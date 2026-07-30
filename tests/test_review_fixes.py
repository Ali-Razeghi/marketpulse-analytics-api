"""Tests for behaviours added after review: idempotent ingestion, parameter
validation, unknown sources, invalid tokens, admin RBAC, and the health probe.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.services.analytics_service import AnalyticsService
from app.services.ingestion_service import IngestionService


async def test_health_endpoint(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_reingestion_is_idempotent(session: AsyncSession) -> None:
    svc = IngestionService(session)
    await svc.ingest("synthetic", {"series_key": "demo/index", "days": 15})
    await svc.ingest("synthetic", {"series_key": "demo/index", "days": 15})

    summary = await AnalyticsService(session).summary("synthetic", "demo/index")
    # Without idempotency this would be 30; the unique series must stay 15.
    assert summary.count == 15


async def test_ingest_unknown_source(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/ingest/does-not-exist", json={}, headers=auth_headers
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


async def test_ingest_invalid_params(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/ingest/synthetic",
        json={"days": -3},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_invalid_jwt_is_rejected(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


async def _make_admin(session: AsyncSession) -> None:
    session.add(
        User(
            email="admin@example.com",
            hashed_password=hash_password("adminpass1"),
            role=UserRole.ADMIN,
        )
    )
    await session.commit()


async def test_admin_route_forbidden_for_regular_user(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_admin_route_allowed_for_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _make_admin(session)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    )
    token = login.json()["access_token"]
    resp = await client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert any(u["email"] == "admin@example.com" for u in resp.json())


async def test_empty_csv_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_sources_endpoint_lists_known_sources(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/sources")
    assert resp.status_code == 200
    assert resp.json() == {"sources": ["crypto", "forex", "synthetic"]}


async def test_empty_source_result_is_rejected(
    session: AsyncSession, monkeypatch
) -> None:
    from pydantic import BaseModel

    import app.services.ingestion_service as ingestion_module
    from app.core.exceptions import NoDataError
    from app.sources.base import DataSource

    class EmptyParams(BaseModel):
        pass

    class EmptySource(DataSource[EmptyParams]):
        name = "empty"
        params_model = EmptyParams

        async def collect(self, params: EmptyParams):
            return []

    def _get_empty_source(name, client):
        return EmptySource()

    monkeypatch.setattr(ingestion_module, "get_source", _get_empty_source)

    svc = IngestionService(session)
    try:
        await svc.ingest("empty", {})
    except NoDataError as exc:
        assert exc.code == "NO_DATA_RETURNED"
    else:
        raise AssertionError("Expected NO_DATA_RETURNED")
