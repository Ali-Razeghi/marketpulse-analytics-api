"""Data-source discovery and ingestion endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.openapi.models import Example
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.datapoint import IngestResponse
from app.services.ingestion_service import IngestionService
from app.sources.registry import available_source_names

router = APIRouter(tags=["data-sources"])

# Concrete, per-source examples surfaced in Swagger so callers see the exact
# body shape each source expects. Parameters are still validated server-side
# against each source's Pydantic model.
_INGEST_EXAMPLES: dict[str, Example] = {
    "crypto": Example(
        summary="Crypto (CoinGecko)",
        value={"coin_id": "bitcoin", "vs_currency": "usd", "days": 30},
    ),
    "forex": Example(
        summary="Forex (Frankfurter)",
        value={"base": "USD", "symbol": "EUR", "days": 30},
    ),
    "synthetic": Example(
        summary="Synthetic (offline)",
        value={"series_key": "demo/index", "days": 30, "base_value": 100.0},
    ),
}


@router.get("/sources", summary="List available data sources")
async def list_sources() -> dict[str, list[str]]:
    return {"sources": available_source_names()}


@router.post(
    "/ingest/{source_name}",
    response_model=IngestResponse,
    summary="Fetch from a source and store the results",
)
async def ingest(
    source_name: str,
    params: dict[str, Any] = Body(
        default_factory=dict, openapi_examples=_INGEST_EXAMPLES
    ),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngestResponse:
    # Market sources are public data, so points are stored globally. Ingestion
    # is idempotent per series (re-ingesting replaces prior points).
    return await IngestionService(session).ingest(source_name, params)
