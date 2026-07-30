"""Crypto price source backed by CoinGecko's keyless public API.

Endpoint (no API key required)::

    GET /coins/{id}/market_chart?vs_currency=usd&days=30&interval=daily

The response contains ``prices`` as ``[[epoch_ms, price], ...]``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.core.exceptions import UpstreamError
from app.schemas.datapoint import NormalizedPoint
from app.sources.base import HttpDataSource


class CryptoParams(BaseModel):
    """Validated parameters for the crypto source."""

    coin_id: str = Field(default="bitcoin", min_length=1, max_length=64)
    vs_currency: str = Field(default="usd", min_length=1, max_length=8)
    days: int = Field(default=30, ge=1, le=365)


class CoinGeckoSource(HttpDataSource[CryptoParams]):
    name = "crypto"
    params_model = CryptoParams

    async def collect(self, params: CryptoParams) -> list[NormalizedPoint]:
        payload = await self._get_json(
            f"coins/{params.coin_id}/market_chart",
            {
                "vs_currency": params.vs_currency,
                "days": params.days,
                "interval": "daily",
            },
        )
        if not isinstance(payload, dict) or "prices" not in payload:
            raise UpstreamError("Unexpected CoinGecko payload shape.")

        series_key = f"{params.coin_id}/{params.vs_currency}".lower()
        points: list[NormalizedPoint] = []
        for entry in payload["prices"]:
            # Defensive parsing: skip malformed rows rather than failing.
            if not isinstance(entry, list) or len(entry) != 2:
                continue
            try:
                epoch_ms, price = entry
                ts = datetime.fromtimestamp(epoch_ms / 1000, tz=UTC)
                value = float(price)
            except (TypeError, ValueError, OSError):
                continue
            points.append(
                NormalizedPoint(
                    series_key=series_key,
                    ts=ts,
                    value=value,
                    unit=params.vs_currency.upper(),
                    meta={"coin_id": params.coin_id},
                )
            )
        return points
