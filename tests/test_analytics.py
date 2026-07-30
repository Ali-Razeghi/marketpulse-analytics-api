"""Integration tests for ingestion + analytics over the synthetic source."""

from __future__ import annotations

import math

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import AnalyticsService
from app.services.ingestion_service import IngestionService


async def _ingest_synthetic(session: AsyncSession, days: int = 20) -> str:
    resp = await IngestionService(session).ingest(
        "synthetic", {"series_key": "demo/index", "days": days}
    )
    assert resp.points_ingested == days
    return "demo/index"


async def test_summary_stats(session: AsyncSession) -> None:
    series_key = await _ingest_synthetic(session, days=20)
    summary = await AnalyticsService(session).summary("synthetic", series_key)

    assert summary.count == 20
    assert summary.min_value is not None and summary.max_value is not None
    assert summary.min_value <= summary.mean_value <= summary.max_value
    # Synthetic series trends upward overall.
    assert summary.pct_change is not None and summary.pct_change > 0


async def test_moving_average_window(session: AsyncSession) -> None:
    series_key = await _ingest_synthetic(session, days=20)
    result = await AnalyticsService(session).moving_average(
        "synthetic", series_key, window=5
    )
    # First (window-1) entries have no moving average yet.
    assert result.points[3].moving_average is None
    assert result.points[4].moving_average is not None

    # Verify the rolling mean matches a manual computation for one window.
    first_five = [p.value for p in result.points[:5]]
    expected = sum(first_five) / 5
    assert math.isclose(result.points[4].moving_average, expected, rel_tol=1e-9)


async def test_correlation_of_series_with_itself(session: AsyncSession) -> None:
    series_key = await _ingest_synthetic(session, days=20)
    result = await AnalyticsService(session).correlation(
        "synthetic", series_key, "synthetic", series_key
    )
    assert result.overlapping_points == 20
    assert result.correlation is not None
    assert math.isclose(result.correlation, 1.0, rel_tol=1e-9)


async def test_analytics_endpoint_end_to_end(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    ingest = await client.post(
        "/api/v1/ingest/synthetic",
        json={"series_key": "demo/index", "days": 15},
        headers=auth_headers,
    )
    assert ingest.status_code == 200

    summary = await client.get(
        "/api/v1/analytics/summary",
        params={"source": "synthetic", "series_key": "demo/index"},
        headers=auth_headers,
    )
    assert summary.status_code == 200
    assert summary.json()["count"] == 15
