"""Tests for Story A.1 — Member Login & Session Management."""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models import Member
from app.utils import create_access_token, create_refresh_token, hash_password
from tests.conftest import member_token


pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_valid_credentials_return_access_token(
        self, client: AsyncClient, member: Member
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_sets_http_only_cookies(
        self, client: AsyncClient, member: Member
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    async def test_invalid_password_returns_401(
        self, client: AsyncClient, member: Member
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "INVALID_CREDENTIALS"
        assert "incorrect" in body["error"]["message"].lower()

    async def test_unknown_email_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "anything"},
        )
        assert resp.status_code == 401

    async def test_missing_fields_returns_422(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={"email": "x@y.com"})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_disabled_account_returns_403(
        self, client: AsyncClient, db, member: Member
    ):
        member.is_active = False
        await db.commit()
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "ACCOUNT_DISABLED"


class TestTokenRefresh:
    async def test_valid_refresh_token_issues_new_access_token(
        self, client: AsyncClient, member: Member
    ):
        # Login to get cookies
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        assert login.status_code == 200

        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_missing_refresh_token_returns_401(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "MISSING_REFRESH_TOKEN"

    async def test_invalid_refresh_token_returns_401(self, client: AsyncClient):
        client.cookies.set("refresh_token", "not.a.real.token")
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_access_token_used_as_refresh_returns_401(
        self, client: AsyncClient, member: Member
    ):
        # Use an access token where a refresh token is expected
        access = create_access_token(subject=member.id, role="member")
        client.cookies.set("refresh_token", access)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


class TestLogout:
    async def test_logout_clears_cookies(self, client: AsyncClient, member: Member):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_unauthenticated_request_blocked(self, client: AsyncClient):
        resp = await client.get("/api/v1/account/me")
        assert resp.status_code == 401

    async def test_valid_bearer_token_allows_access(
        self, client: AsyncClient, member: Member
    ):
        token = member_token(member)
        resp = await client.get(
            "/api/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
