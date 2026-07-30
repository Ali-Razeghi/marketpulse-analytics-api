"""Registry mapping source names to constructed instances.

Centralising construction here means the API and service layers refer to
sources by their string ``name`` only. Adding a source is a one-line change in
:func:`build_sources` -- callers are untouched.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.sources.base import DataSource
from app.sources.crypto import CoinGeckoSource
from app.sources.forex import FrankfurterSource
from app.sources.synthetic import SyntheticMarketSource

# Sources are parameterised by different params models, so the registry is
# heterogeneous and typed as ``DataSource[Any]``.
AnySource = DataSource[Any]

SOURCE_NAMES: tuple[str, ...] = (
    CoinGeckoSource.name,
    FrankfurterSource.name,
    SyntheticMarketSource.name,
)


def build_sources(client: httpx.AsyncClient) -> dict[str, AnySource]:
    """Instantiate every known source, wiring in the shared HTTP client."""
    sources: list[AnySource] = [
        CoinGeckoSource(client, settings.coingecko_base_url),
        FrankfurterSource(client, settings.frankfurter_base_url),
        SyntheticMarketSource(),
    ]
    return {s.name: s for s in sources}


def get_source(name: str, client: httpx.AsyncClient) -> AnySource:
    """Resolve a single source by name or raise ``NotFoundError``."""
    sources = build_sources(client)
    try:
        return sources[name]
    except KeyError as exc:
        raise NotFoundError(
            f"Unknown data source '{name}'.",
            details={"available": sorted(sources)},
        ) from exc


def available_source_names() -> list[str]:
    """Return provider names without constructing HTTP clients or adapters."""
    return sorted(SOURCE_NAMES)
