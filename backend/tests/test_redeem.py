"""Tests for Story L.4 — Redemption Codes (PD.4: 8-char alphanumeric, 15-min expiry)."""

import re
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import LedgerEntry, Location, Member, Offer, RedemptionCode, TransactionType
from app.utils import generate_redemption_code, redemption_expiry
from tests.conftest import member_token


pytestmark = pytest.mark.asyncio

REDEEM_URL = "/api/v1/redeem"
USE_CODE_URL = "/api/v1/redeem/use"
_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_offer(
    db, location_name: str = "Test Cafe", points_cost: int = 50
) -> Offer:
    loc = Location(name=location_name, is_active=True)
    db.add(loc)
    await db.flush()
    offer = Offer(
        location_id=loc.id,
        description="Free coffee",
        points_cost=points_cost,
        is_active=True,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


async def _credit(db, member: Member, amount: int) -> None:
    entry = LedgerEntry(
        member_id=member.id,
        amount=amount,
        transaction_type=TransactionType.ingest,
        source="test_setup",
    )
    db.add(entry)
    await db.commit()


# ---------------------------------------------------------------------------
# Code generation unit tests
# ---------------------------------------------------------------------------


class TestCodeGeneration:
    def test_code_is_8_characters(self):
        code = generate_redemption_code()
        assert len(code) == 8

    def test_code_is_alphanumeric_uppercase(self):
        for _ in range(100):
            code = generate_redemption_code()
            assert _CODE_PATTERN.match(code), f"Bad code: {code}"

    def test_codes_are_unique_across_bulk_generation(self):
        codes = {generate_redemption_code() for _ in range(1000)}
        # Extremely unlikely collision with 36^8 = ~2.8 trillion combos
        assert len(codes) == 1000

    def test_expiry_is_15_minutes_from_now(self):
        before = datetime.now(UTC)
        expiry = redemption_expiry()
        after = datetime.now(UTC)
        assert before + timedelta(minutes=14) < expiry < after + timedelta(minutes=16)


# ---------------------------------------------------------------------------
# Redemption endpoint tests
# ---------------------------------------------------------------------------


class TestRedeemEndpoint:
    async def test_successful_redemption_returns_code_and_expiry(
        self, client, db, member: Member
    ):
        offer = await _setup_offer(db)
        await _credit(db, member, 200)

        token = member_token(member)
        resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": offer.id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert _CODE_PATTERN.match(data["code"])
        assert data["points_deducted"] == 50
        assert "expires_at" in data
        assert "qr_data" in data
        assert data["code"] in data["qr_data"]

    async def test_insufficient_balance_returns_400(self, client, db, member: Member):
        offer = await _setup_offer(db, points_cost=999)
        # member has 0 points

        token = member_token(member)
        resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": offer.id},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INSUFFICIENT_BALANCE"

    async def test_unknown_offer_returns_404(self, client, db, member: Member):
        await _credit(db, member, 500)
        token = member_token(member)
        resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert resp.status_code == 404

    async def test_expired_offer_returns_400(self, client, db, member: Member):
        loc = Location(name="Old Shop", is_active=True)
        db.add(loc)
        await db.flush()
        expired_offer = Offer(
            location_id=loc.id,
            description="Expired deal",
            points_cost=10,
            is_active=True,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db.add(expired_offer)
        await db.commit()

        await _credit(db, member, 100)
        token = member_token(member)
        resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": expired_offer.id},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "OFFER_EXPIRED"

    async def test_redemption_deducts_points_from_ledger(
        self, client, db, member: Member
    ):
        offer = await _setup_offer(db, points_cost=30)
        await _credit(db, member, 100)

        token = member_token(member)
        await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": offer.id},
        )

        # Check ledger has a redemption debit
        result = await db.execute(
            select(LedgerEntry).where(
                LedgerEntry.member_id == member.id,
                LedgerEntry.transaction_type == TransactionType.redemption,
            )
        )
        entry = result.scalars().first()
        assert entry is not None
        assert entry.amount == -30

    async def test_out_of_stock_offer_returns_400(self, client, db, member: Member):
        loc = Location(name="Limited Shop", is_active=True)
        db.add(loc)
        await db.flush()
        limited_offer = Offer(
            location_id=loc.id,
            description="Last one",
            points_cost=5,
            quantity_available=0,
            is_active=True,
        )
        db.add(limited_offer)
        await db.commit()

        await _credit(db, member, 100)
        token = member_token(member)
        resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": limited_offer.id},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "OFFER_UNAVAILABLE"


class TestUseCode:
    async def test_use_valid_code_marks_redeemed(self, client, db, member: Member):
        offer = await _setup_offer(db)
        await _credit(db, member, 200)

        token = member_token(member)
        create_resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": offer.id},
        )
        code = create_resp.json()["code"]

        use_resp = await client.post(
            USE_CODE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code},
        )
        assert use_resp.status_code == 200
        assert "redeemed_at" in use_resp.json()

    async def test_reused_code_returns_400(self, client, db, member: Member):
        offer = await _setup_offer(db)
        await _credit(db, member, 200)

        token = member_token(member)
        create_resp = await client.post(
            REDEEM_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"offer_id": offer.id},
        )
        code = create_resp.json()["code"]

        # Use once
        await client.post(USE_CODE_URL, headers={"Authorization": f"Bearer {token}"}, json={"code": code})

        # Use again — must fail
        resp2 = await client.post(
            USE_CODE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code},
        )
        assert resp2.status_code == 400
        assert resp2.json()["error"]["code"] == "CODE_ALREADY_USED"

    async def test_expired_code_returns_400(self, client, db, member: Member):
        offer = await _setup_offer(db)
        await _credit(db, member, 200)

        # Directly insert an expired redemption code
        rc = RedemptionCode(
            code="EXPIR3D1",
            member_id=member.id,
            offer_id=offer.id,
            points_cost=50,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db.add(rc)
        await db.commit()

        token = member_token(member)
        resp = await client.post(
            USE_CODE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "EXPIR3D1"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "CODE_EXPIRED"

    async def test_unknown_code_returns_404(self, client, member: Member):
        token = member_token(member)
        resp = await client.post(
            USE_CODE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 404
