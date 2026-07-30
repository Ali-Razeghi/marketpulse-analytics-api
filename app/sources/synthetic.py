"""A deterministic, offline data source.

This exists for two practical reasons:

1. The whole platform can be demonstrated (``docker compose up`` -> ingest ->
   analyse) with **zero external dependencies or API keys**, which reviewers
   value.
2. It proves the abstraction is not HTTP-specific: a source need not talk to a
   network at all -- it only has to emit ``NormalizedPoint`` objects.

The series is fully reproducible (closed-form generator), so tests can assert
exact values.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from app.schemas.datapoint import NormalizedPoint
from app.sources.base import DataSource


class SyntheticParams(BaseModel):
    """Validated parameters for the synthetic source."""

    series_key: str = Field(default="demo/index", min_length=1, max_length=128)
    days: int = Field(default=30, ge=1, le=365)
    base_value: float = Field(default=100.0, gt=0, le=1_000_000)


class SyntheticMarketSource(DataSource[SyntheticParams]):
    name = "synthetic"
    params_model = SyntheticParams

    async def collect(self, params: SyntheticParams) -> list[NormalizedPoint]:
        now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        points: list[NormalizedPoint] = []
        for offset in range(params.days):
            ts = now - timedelta(days=params.days - 1 - offset)
            # Gentle upward trend + deterministic seasonal oscillation.
            trend = params.base_value * (1 + 0.002 * offset)
            seasonal = 5.0 * math.sin(offset / 3.0)
            value = round(trend + seasonal, 4)
            points.append(
                NormalizedPoint(
                    series_key=params.series_key,
                    ts=ts,
                    value=value,
                    unit="index",
                    meta={"generator": "synthetic"},
                )
            )
        return points
