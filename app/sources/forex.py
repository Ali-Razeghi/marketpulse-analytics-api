"""Foreign-exchange source backed by the Frankfurter API (ECB reference rates).

Keyless time-series endpoint::

    GET /{start}..{end}?base=USD&symbols=EUR

Response shape::

    {"base": "USD", "rates": {"2026-01-02": {"EUR": 0.95}, ...}}
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions import UpstreamError
from app.schemas.datapoint import NormalizedPoint
from app.sources.base import HttpDataSource


class ForexParams(BaseModel):
    """Validated parameters for the forex source."""

    base: str = Field(default="USD", min_length=3, max_length=3)
    symbol: str = Field(default="EUR", min_length=3, max_length=3)
    days: int = Field(default=30, ge=1, le=365)

    @model_validator(mode="after")
    def _base_differs_from_symbol(self) -> ForexParams:
        if self.base.upper() == self.symbol.upper():
            raise ValueError("`base` and `symbol` must differ.")
        return self


class FrankfurterSource(HttpDataSource[ForexParams]):
    name = "forex"
    params_model = ForexParams

    async def collect(self, params: ForexParams) -> list[NormalizedPoint]:
        base = params.base.upper()
        symbol = params.symbol.upper()
        end = date.today()
        start = end - timedelta(days=params.days)

        payload = await self._get_json(
            f"{start.isoformat()}..{end.isoformat()}",
            {"base": base, "symbols": symbol},
        )
        if not isinstance(payload, dict) or "rates" not in payload:
            raise UpstreamError("Unexpected Frankfurter payload shape.")

        series_key = f"{base}/{symbol}".lower()
        points: list[NormalizedPoint] = []
        for day_str, rates in payload["rates"].items():
            if not isinstance(rates, dict) or symbol not in rates:
                continue
            try:
                ts = datetime.combine(date.fromisoformat(day_str), time.min, tzinfo=UTC)
                value = float(rates[symbol])
            except (TypeError, ValueError):
                continue
            points.append(
                NormalizedPoint(
                    series_key=series_key,
                    ts=ts,
                    value=value,
                    unit=symbol,
                    meta={"base": base},
                )
            )
        points.sort(key=lambda p: p.ts)
        return points
