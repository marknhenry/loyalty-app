"""Tests for Story L.2 — Point Ingestion from Partner Apps."""

import pytest
from httpx import AsyncClient

from app.models import APIKey, Member
from tests.conftest import member_token


pytestmark = pytest.mark.asyncio

INGEST_URL = "/api/v1/loyalty/ingest"


class TestAPIKeyAuth:
    async def test_missing_api_key_returns_401(
        self, client: AsyncClient, member: Member
    ):
        resp = await client.post(
            INGEST_URL,
            json={"member_id": member.id, "amount": 100, "source": "shop"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "MISSING_API_KEY"

    async def test_invalid_api_key_returns_401(
        self, client: AsyncClient, member: Member
    ):
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": "lp_invalid_key_xyz"},
            json={"member_id": member.id, "amount": 100, "source": "shop"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_API_KEY"

    async def test_valid_api_key_is_accepted(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": 50, "source": "shop"},
        )
        assert resp.status_code == 200


class TestIngestValidation:
    async def test_negative_amount_returns_400(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": -50, "source": "shop"},
        )
        assert resp.status_code == 422

    async def test_zero_amount_returns_422(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": 0, "source": "shop"},
        )
        assert resp.status_code == 422

    async def test_unknown_member_returns_400(
        self, client: AsyncClient, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": "nonexistent-uuid", "amount": 100, "source": "shop"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "MEMBER_NOT_FOUND"

    async def test_missing_source_returns_422(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": 100},
        )
        assert resp.status_code == 422


class TestIngestResponse:
    async def test_successful_ingest_returns_transaction_details(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        resp = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": 200, "source": "partner_app"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "transaction_id" in data
        assert data["balance_after"] >= 200
        assert "timestamp" in data

    async def test_ingest_increases_member_balance(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key

        # First get current balance
        token = member_token(member)
        before = await client.get(
            "/api/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        balance_before = before.json()["balance"]

        await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key},
            json={"member_id": member.id, "amount": 75, "source": "shop"},
        )

        after = await client.get(
            "/api/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after.json()["balance"] == balance_before + 75


class TestIdempotency:
    async def test_duplicate_idempotency_key_returns_same_transaction(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        headers = {"X-API-Key": plain_key, "Idempotency-Key": "idem-key-abc-001"}
        payload = {"member_id": member.id, "amount": 100, "source": "shop"}

        resp1 = await client.post(INGEST_URL, headers=headers, json=payload)
        resp2 = await client.post(INGEST_URL, headers=headers, json=payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["transaction_id"] == resp2.json()["transaction_id"]

    async def test_duplicate_idempotency_key_does_not_double_credit(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        idem_key = "idem-no-double-002"
        headers = {"X-API-Key": plain_key, "Idempotency-Key": idem_key}
        payload = {"member_id": member.id, "amount": 50, "source": "shop"}

        await client.post(INGEST_URL, headers=headers, json=payload)
        r2 = await client.post(INGEST_URL, headers=headers, json=payload)
        await client.post(INGEST_URL, headers=headers, json=payload)

        # Balance from first call should equal third call (no double-credit)
        assert r2.json()["balance_after"] == (await client.post(INGEST_URL, headers=headers, json=payload)).json()["balance_after"]

    async def test_different_idempotency_keys_create_separate_transactions(
        self, client: AsyncClient, member: Member, api_key
    ):
        plain_key, _ = api_key
        payload = {"member_id": member.id, "amount": 30, "source": "shop"}

        r1 = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key, "Idempotency-Key": "key-A"},
            json=payload,
        )
        r2 = await client.post(
            INGEST_URL,
            headers={"X-API-Key": plain_key, "Idempotency-Key": "key-B"},
            json=payload,
        )

        assert r1.json()["transaction_id"] != r2.json()["transaction_id"]
