"""Tests for Story O.1 — Error handling, response format, and correlation IDs."""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestErrorResponseShape:
    async def test_404_not_found_has_error_envelope(self, client: AsyncClient):
        resp = await client.get("/api/v1/nonexistent-path")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    async def test_validation_error_has_field_info(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "x"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"]

    async def test_validation_error_includes_request_id(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={})
        body = resp.json()
        # request_id may be None in test but key must be present
        assert "request_id" in body

    async def test_401_error_has_consistent_shape(self, client: AsyncClient):
        resp = await client.get("/api/v1/account/me")
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"]
        assert body["error"]["message"]

    async def test_403_error_has_consistent_shape(self, client: AsyncClient):
        from app.models import Member
        from app.utils import hash_password, create_access_token
        from app.db import async_session_factory
        # Use a regular member trying admin endpoint
        from app.models import MemberRole
        from sqlalchemy.ext.asyncio import AsyncSession

        # Hit an admin endpoint with a member token
        from app.utils import create_access_token
        import uuid
        fake_token = create_access_token(subject=str(uuid.uuid4()), role="member")
        resp = await client.post(
            "/api/v1/admin/locations",
            headers={"Authorization": f"Bearer {fake_token}"},
            json={"name": "x"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "FORBIDDEN"


class TestCorrelationID:
    async def test_response_includes_x_request_id_header(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers

    async def test_custom_request_id_is_echoed(self, client: AsyncClient):
        custom_id = "my-trace-id-12345"
        resp = await client.get(
            "/api/v1/health",
            headers={"X-Request-ID": custom_id},
        )
        assert resp.headers.get("X-Request-ID") == custom_id

    async def test_request_id_is_unique_per_request(self, client: AsyncClient):
        resp1 = await client.get("/api/v1/health")
        resp2 = await client.get("/api/v1/health")
        id1 = resp1.headers.get("X-Request-ID")
        id2 = resp2.headers.get("X-Request-ID")
        assert id1 != id2


class TestHealthCheck:
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
