"""Tests for ledger immutability, balance calculation, and Story L.1."""

import pytest
from sqlalchemy import select

from app.models import LedgerEntry, Member, TransactionType
from app.utils import calculate_balance, hash_password
from tests.conftest import member_token


pytestmark = pytest.mark.asyncio


class TestLedgerImmutability:
    async def test_ledger_entries_are_never_deleted(
        self, db, member: Member
    ):
        """Entries must persist — no DELETE allowed by convention."""
        entry = LedgerEntry(
            member_id=member.id,
            amount=100,
            transaction_type=TransactionType.ingest,
            source="test",
        )
        db.add(entry)
        await db.commit()

        # Verify it exists
        result = await db.execute(select(LedgerEntry).where(LedgerEntry.id == entry.id))
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.amount == 100

    async def test_reversal_creates_new_entry_not_update(
        self, db, member: Member
    ):
        """Corrections append a new row; original amount is unchanged."""
        original = LedgerEntry(
            member_id=member.id,
            amount=200,
            transaction_type=TransactionType.ingest,
            source="test",
        )
        db.add(original)
        await db.commit()
        await db.refresh(original)

        reversal = LedgerEntry(
            member_id=member.id,
            amount=-200,
            transaction_type=TransactionType.reversal,
            source="admin",
            related_entry_id=original.id,
            description=f"Reversal of txn_id: {original.id}",
        )
        db.add(reversal)
        await db.commit()

        # Original is untouched
        result = await db.execute(select(LedgerEntry).where(LedgerEntry.id == original.id))
        unchanged = result.scalar_one()
        assert unchanged.amount == 200  # original preserved

    async def test_balance_after_reversal_is_zero(
        self, db, member: Member
    ):
        entries = [
            LedgerEntry(member_id=member.id, amount=300, transaction_type=TransactionType.ingest),
            LedgerEntry(member_id=member.id, amount=-300, transaction_type=TransactionType.reversal),
        ]
        db.add_all(entries)
        await db.commit()

        balance = calculate_balance(entries)
        assert balance == 0


class TestBalanceCalculation:
    async def test_empty_ledger_balance_is_zero(self, db, second_member: Member):
        result = await db.execute(
            select(LedgerEntry).where(LedgerEntry.member_id == second_member.id)
        )
        entries = result.scalars().all()
        assert calculate_balance(entries) == 0

    async def test_balance_sums_all_entries(self, db, member: Member):
        entries = [
            LedgerEntry(member_id=member.id, amount=500, transaction_type=TransactionType.ingest),
            LedgerEntry(member_id=member.id, amount=200, transaction_type=TransactionType.ingest),
            LedgerEntry(member_id=member.id, amount=-100, transaction_type=TransactionType.redemption),
        ]
        db.add_all(entries)
        await db.commit()

        balance = calculate_balance(entries)
        assert balance == 600

    async def test_balance_includes_exchange_entries(self, db, member: Member):
        entries = [
            LedgerEntry(member_id=member.id, amount=1000, transaction_type=TransactionType.ingest),
            LedgerEntry(member_id=member.id, amount=-250, transaction_type=TransactionType.exchange_out),
        ]
        db.add_all(entries)
        await db.commit()
        assert calculate_balance(entries) == 750

    async def test_idempotency_key_prevents_duplicates(self, db, member: Member):
        """Two entries with the same idempotency_key should raise a DB-level error."""
        e1 = LedgerEntry(
            member_id=member.id,
            amount=100,
            transaction_type=TransactionType.ingest,
            idempotency_key="idem-test-001",
        )
        db.add(e1)
        await db.commit()

        e2 = LedgerEntry(
            member_id=member.id,
            amount=100,
            transaction_type=TransactionType.ingest,
            idempotency_key="idem-test-001",  # same key
        )
        db.add(e2)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


class TestAccountEndpoint:
    async def test_get_my_account_returns_balance_and_transactions(
        self, client, db, member: Member
    ):
        entry = LedgerEntry(
            member_id=member.id,
            amount=150,
            transaction_type=TransactionType.ingest,
            source="partner_x",
        )
        db.add(entry)
        await db.commit()

        token = member_token(member)
        resp = await client.get(
            "/api/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] >= 150
        assert len(data["transactions"]) >= 1
        assert data["member"]["email"] == "alice@example.com"

    async def test_filter_by_transaction_type(self, client, db, member: Member):
        entries = [
            LedgerEntry(member_id=member.id, amount=100, transaction_type=TransactionType.ingest),
            LedgerEntry(member_id=member.id, amount=-50, transaction_type=TransactionType.redemption),
        ]
        db.add_all(entries)
        await db.commit()

        token = member_token(member)
        resp = await client.get(
            "/api/v1/account/me?tx_type=redemption",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        txns = resp.json()["transactions"]
        assert all(t["transaction_type"] == "redemption" for t in txns)

    async def test_unauthenticated_account_access_returns_401(self, client):
        resp = await client.get("/api/v1/account/me")
        assert resp.status_code == 401
