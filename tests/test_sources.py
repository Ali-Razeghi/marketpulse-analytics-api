"""Tests for the data-source layer.

External HTTP sources are tested against mocked responses (respx) so the suite
is deterministic and offline. The synthetic source is tested for exact output,
and parameter validation is tested at the model level.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from pydantic import ValidationError

from app.core.exceptions import UpstreamError
from app.sources.crypto import CoinGeckoSource, CryptoParams
from app.sources.forex import ForexParams, FrankfurterSource
from app.sources.synthetic import SyntheticMarketSource, SyntheticParams


async def test_synthetic_source_is_deterministic() -> None:
    source = SyntheticMarketSource()
    params = SyntheticParams(days=10)
    first = await source.collect(params)
    second = await source.collect(params)
    assert len(first) == 10
    assert [p.value for p in first] == [p.value for p in second]
    assert all(a.ts < b.ts for a, b in zip(first, first[1:], strict=False))


@respx.mock
async def test_coingecko_normalisation() -> None:
    respx.get(url__regex=r".*/coins/bitcoin/market_chart").mock(
        return_value=httpx.Response(
            200,
            json={
                "prices": [
                    [1_700_000_000_000, 35000.5],
                    [1_700_086_400_000, 36000.0],
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        source = CoinGeckoSource(client, "https://api.coingecko.com/api/v3")
        points = await source.collect(
            CryptoParams(coin_id="bitcoin", vs_currency="usd", days=2)
        )

    assert len(points) == 2
    assert points[0].series_key == "bitcoin/usd"
    assert points[0].value == 35000.5
    assert points[0].unit == "USD"


@respx.mock
async def test_frankfurter_normalisation() -> None:
    respx.get(url__regex=r".*/\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}").mock(
        return_value=httpx.Response(
            200,
            json={
                "base": "USD",
                "rates": {"2026-01-02": {"EUR": 0.95}, "2026-01-03": {"EUR": 0.96}},
            },
        )
    )
    async with httpx.AsyncClient() as client:
        source = FrankfurterSource(client, "https://api.frankfurter.dev/v1")
        points = await source.collect(ForexParams(base="USD", symbol="EUR", days=2))

    assert [p.value for p in points] == [0.95, 0.96]
    assert points[0].series_key == "usd/eur"


@respx.mock
async def test_upstream_error_on_http_failure() -> None:
    respx.get(url__regex=r".*/coins/.*").mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as client:
        source = CoinGeckoSource(client, "https://api.coingecko.com/api/v3")
        with pytest.raises(UpstreamError):
            await source.collect(CryptoParams(coin_id="bitcoin"))


@respx.mock
async def test_upstream_error_on_invalid_json() -> None:
    # A 200 response whose body is not JSON must still become an UpstreamError.
    respx.get(url__regex=r".*/coins/.*").mock(
        return_value=httpx.Response(200, text="<html>not json</html>")
    )
    async with httpx.AsyncClient() as client:
        source = CoinGeckoSource(client, "https://api.coingecko.com/api/v3")
        with pytest.raises(UpstreamError):
            await source.collect(CryptoParams(coin_id="bitcoin"))


def test_param_validation_rejects_bad_days() -> None:
    with pytest.raises(ValidationError):
        CryptoParams(days=-5)
    with pytest.raises(ValidationError):
        CryptoParams(days=10_000)


def test_forex_rejects_base_equal_symbol() -> None:
    with pytest.raises(ValidationError):
        ForexParams(base="USD", symbol="USD")
