"""Tests for Story L.3 — Point Exchange (atomicity, rates, concurrency safety)."""

import asyncio

import pytest
from sqlalchemy import func, select

from app.models import ExchangeRate, LedgerEntry, Member, TransactionType
from tests.conftest import member_token


pytestmark = pytest.mark.asyncio

EXCHANGE_URL = "/api/v1/exchange"


async def _give_points(db, member: Member, amount: int) -> None:
    entry = LedgerEntry(
        member_id=member.id,
        amount=amount,
        transaction_type=TransactionType.ingest,
        source="test_setup",
    )
    db.add(entry)
    await db.commit()


async def _get_balance(db, member_id: str) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.member_id == member_id
        )
    )
    return int(result.scalar())


class TestExchangeValidation:
    async def test_self_exchange_returns_400(
        self, client, db, member: Member, standard_rate: ExchangeRate
    ):
        await _give_points(db, member, 500)
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": member.id, "amount": 100, "rate_name": "standard"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SELF_EXCHANGE"

    async def test_unknown_recipient_returns_400(
        self, client, db, member: Member, standard_rate: ExchangeRate
    ):
        await _give_points(db, member, 500)
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": "does-not-exist", "amount": 100, "rate_name": "standard"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "RECIPIENT_NOT_FOUND"

    async def test_invalid_rate_name_returns_400(
        self, client, db, member: Member, second_member: Member
    ):
        await _give_points(db, member, 500)
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 100, "rate_name": "nonexistent_rate"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_RATE"

    async def test_insufficient_balance_returns_400(
        self, client, db, member: Member, second_member: Member, standard_rate: ExchangeRate
    ):
        # member has 0 points
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 100, "rate_name": "standard"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INSUFFICIENT_BALANCE"

    async def test_unauthenticated_exchange_returns_401(self, client):
        resp = await client.post(
            EXCHANGE_URL,
            json={"recipient_id": "x", "amount": 100, "rate_name": "standard"},
        )
        assert resp.status_code == 401


class TestExchangeAtomicity:
    async def test_successful_exchange_creates_two_ledger_entries(
        self, client, db, member: Member, second_member: Member, standard_rate: ExchangeRate
    ):
        await _give_points(db, member, 300)

        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 100, "rate_name": "standard"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["amount_sent"] == 100
        assert data["sender_transaction_id"] != data["recipient_transaction_id"]

    async def test_exchange_deducts_from_sender(
        self, client, db, member: Member, second_member: Member, standard_rate: ExchangeRate
    ):
        await _give_points(db, member, 500)
        balance_before = await _get_balance(db, member.id)

        token = member_token(member)
        await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 150, "rate_name": "standard"},
        )

        balance_after = await _get_balance(db, member.id)
        assert balance_after == balance_before - 150

    async def test_exchange_credits_recipient(
        self, client, db, member: Member, second_member: Member, standard_rate: ExchangeRate
    ):
        await _give_points(db, member, 400)
        recipient_before = await _get_balance(db, second_member.id)

        token = member_token(member)
        await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 200, "rate_name": "standard"},
        )

        recipient_after = await _get_balance(db, second_member.id)
        assert recipient_after == recipient_before + 200  # rate=1.0


class TestExchangeRateFromDB:
    async def test_exchange_applies_database_rate(
        self, client, db, member: Member, second_member: Member
    ):
        rate = ExchangeRate(name="premium", rate=1.5, min_amount=1, is_active=True)
        db.add(rate)
        await db.commit()

        await _give_points(db, member, 600)
        recipient_before = await _get_balance(db, second_member.id)

        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 100, "rate_name": "premium"},
        )
        assert resp.status_code == 200
        assert resp.json()["rate_applied"] == 1.5
        assert resp.json()["amount_received"] == 150

    async def test_inactive_rate_is_rejected(
        self, client, db, member: Member, second_member: Member
    ):
        rate = ExchangeRate(name="old_rate", rate=0.5, is_active=False)
        db.add(rate)
        await db.commit()

        await _give_points(db, member, 300)
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 100, "rate_name": "old_rate"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_RATE"

    async def test_exchange_respects_min_amount(
        self, client, db, member: Member, second_member: Member
    ):
        rate = ExchangeRate(name="min_test", rate=1.0, min_amount=50, is_active=True)
        db.add(rate)
        await db.commit()

        await _give_points(db, member, 300)
        token = member_token(member)
        resp = await client.post(
            EXCHANGE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_id": second_member.id, "amount": 10, "rate_name": "min_test"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "AMOUNT_TOO_SMALL"
