"""Tests for Stories R.1 and A.2 — Admin CRUD and Role-Based Access."""

import pytest
from httpx import AsyncClient

from app.models import Location, Member, Offer
from tests.conftest import admin_token, member_token


pytestmark = pytest.mark.asyncio

LOCATIONS_URL = "/api/v1/admin/locations"


class TestAdminRoleGuard:
    async def test_member_cannot_create_location(
        self, client: AsyncClient, member: Member
    ):
        token = member_token(member)
        resp = await client.post(
            LOCATIONS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Shop"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_unauthenticated_cannot_create_location(self, client: AsyncClient):
        resp = await client.post(LOCATIONS_URL, json={"name": "Test Shop"})
        assert resp.status_code == 401

    async def test_admin_can_create_location(
        self, client: AsyncClient, admin_member: Member
    ):
        token = admin_token(admin_member)
        resp = await client.post(
            LOCATIONS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Admin Shop", "address": "123 Main St"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Admin Shop"

    async def test_member_cannot_update_location(
        self, client: AsyncClient, db, member: Member
    ):
        loc = Location(name="Shop A", is_active=True)
        db.add(loc)
        await db.commit()

        token = member_token(member)
        resp = await client.put(
            f"{LOCATIONS_URL}/{loc.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Hacked Name"},
        )
        assert resp.status_code == 403


class TestLocationCRUD:
    async def test_create_location_persists(
        self, client: AsyncClient, admin_member: Member
    ):
        token = admin_token(admin_member)
        resp = await client.post(
            LOCATIONS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Cafe", "address": "10 Park Ave", "hours": "9-5", "contact": "555-1234"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"]
        assert data["is_active"] is True

    async def test_list_locations_returns_active_only(
        self, client: AsyncClient, db, admin_member: Member
    ):
        active = Location(name="Open Shop", is_active=True)
        inactive = Location(name="Closed Shop", is_active=False)
        db.add_all([active, inactive])
        await db.commit()

        resp = await client.get(LOCATIONS_URL)
        assert resp.status_code == 200
        names = [loc["name"] for loc in resp.json()]
        assert "Open Shop" in names
        assert "Closed Shop" not in names

    async def test_update_location(
        self, client: AsyncClient, db, admin_member: Member
    ):
        loc = Location(name="Old Name", is_active=True)
        db.add(loc)
        await db.commit()

        token = admin_token(admin_member)
        resp = await client.put(
            f"{LOCATIONS_URL}/{loc.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_delete_location_deactivates(
        self, client: AsyncClient, db, admin_member: Member
    ):
        loc = Location(name="Closing Shop", is_active=True)
        db.add(loc)
        await db.commit()

        token = admin_token(admin_member)
        resp = await client.delete(
            f"{LOCATIONS_URL}/{loc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Should not appear in public list
        list_resp = await client.get(LOCATIONS_URL)
        names = [l["name"] for l in list_resp.json()]
        assert "Closing Shop" not in names

    async def test_update_nonexistent_location_returns_404(
        self, client: AsyncClient, admin_member: Member
    ):
        token = admin_token(admin_member)
        resp = await client.put(
            f"{LOCATIONS_URL}/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404


class TestOfferCRUD:
    async def test_create_offer_for_location(
        self, client: AsyncClient, db, admin_member: Member
    ):
        loc = Location(name="Offer Shop", is_active=True)
        db.add(loc)
        await db.commit()

        token = admin_token(admin_member)
        resp = await client.post(
            f"{LOCATIONS_URL}/{loc.id}/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Free tea", "points_cost": 25},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "Free tea"
        assert data["points_cost"] == 25

    async def test_create_offer_for_unknown_location_returns_404(
        self, client: AsyncClient, admin_member: Member
    ):
        token = admin_token(admin_member)
        resp = await client.post(
            f"{LOCATIONS_URL}/no-such-location/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Ghost offer", "points_cost": 10},
        )
        assert resp.status_code == 404

    async def test_update_offer(self, client: AsyncClient, db, admin_member: Member):
        loc = Location(name="Update Shop", is_active=True)
        db.add(loc)
        await db.flush()
        offer = Offer(
            location_id=loc.id,
            description="Old desc",
            points_cost=100,
            is_active=True,
        )
        db.add(offer)
        await db.commit()

        token = admin_token(admin_member)
        resp = await client.put(
            f"/api/v1/admin/offers/{offer.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "New desc", "points_cost": 80},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "New desc"

    async def test_offer_quantity_exhaustion_marks_unavailable(
        self, client: AsyncClient, db, admin_member: Member
    ):
        loc = Location(name="Limited Shop", is_active=True)
        db.add(loc)
        await db.flush()
        offer = Offer(
            location_id=loc.id,
            description="Last one",
            points_cost=10,
            quantity_available=0,
            is_active=False,
        )
        db.add(offer)
        await db.commit()

        # Public list should not show inactive offer
        list_resp = await client.get(LOCATIONS_URL)
        for location_data in list_resp.json():
            if location_data["id"] == loc.id:
                active_offers = [o for o in location_data.get("offers", []) if o["is_active"]]
                assert all(o["id"] != offer.id for o in active_offers)


class TestAuditTrail:
    async def test_admin_action_creates_audit_entry(
        self, client: AsyncClient, db, admin_member: Member
    ):
        from app.models import AuditLog
        from sqlalchemy import select

        token = admin_token(admin_member)
        await client.post(
            LOCATIONS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Audited Shop"},
        )

        result = await db.execute(
            select(AuditLog).where(
                AuditLog.admin_id == admin_member.id,
                AuditLog.action == "create_location",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.resource_type == "location"
