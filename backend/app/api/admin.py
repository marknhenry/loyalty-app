"""Admin routes — Location & Offer CRUD, Ledger corrections (Stories R.1, A.2, L.5)."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.auth import require_admin
from app.models import AuditLog, LedgerEntry, Location, Member, Offer, TransactionType
from app.schemas import (
    CorrectionRequest,
    CorrectionResponse,
    LocationCreate,
    LocationOut,
    LocationUpdate,
    LocationWithOffersOut,
    OfferCreate,
    OfferOut,
    OfferUpdate,
)
from app.utils import audit_details, now_utc

logger = logging.getLogger("loyalty_app")
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------


async def _audit(
    db: AsyncSession,
    admin_id: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    **details,
) -> None:
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=audit_details(**details),
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# Location CRUD
# ---------------------------------------------------------------------------


@router.get("/locations", response_model=list[LocationWithOffersOut])
async def list_locations(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[LocationWithOffersOut]:
    """Public-readable endpoint — no auth required for member browsing."""
    query = select(Location).options(selectinload(Location.offers))
    if not include_inactive:
        query = query.where(Location.is_active == True)
    result = await db.execute(query.order_by(Location.name))
    locations = result.scalars().all()
    return [LocationWithOffersOut.model_validate(loc) for loc in locations]


@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LocationOut:
    loc = Location(**body.model_dump())
    db.add(loc)
    await db.flush()
    await _audit(db, current_user["sub"], "create_location", "location", loc.id, name=body.name)
    await db.commit()
    await db.refresh(loc)
    logger.info("Admin %s created location %s", current_user["sub"], loc.id)
    return LocationOut.model_validate(loc)


@router.put("/locations/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: str,
    body: LocationUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LocationOut:
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Location not found"})

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(loc, field, value)
    loc.updated_at = now_utc()

    await _audit(db, current_user["sub"], "update_location", "location", location_id, changes=update_data)
    await db.commit()
    await db.refresh(loc)
    return LocationOut.model_validate(loc)


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Location not found"})

    loc.is_active = False
    loc.updated_at = now_utc()
    await _audit(db, current_user["sub"], "delete_location", "location", location_id)
    await db.commit()


# ---------------------------------------------------------------------------
# Offer CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/locations/{location_id}/offers",
    response_model=OfferOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    location_id: str,
    body: OfferCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> OfferOut:
    result = await db.execute(select(Location).where(Location.id == location_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Location not found"})

    offer = Offer(location_id=location_id, **body.model_dump())
    db.add(offer)
    await db.flush()
    await _audit(db, current_user["sub"], "create_offer", "offer", offer.id, location_id=location_id)
    await db.commit()
    await db.refresh(offer)
    return OfferOut.model_validate(offer)


@router.put("/offers/{offer_id}", response_model=OfferOut)
async def update_offer(
    offer_id: str,
    body: OfferUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> OfferOut:
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Offer not found"})

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(offer, field, value)
    offer.updated_at = now_utc()

    await _audit(db, current_user["sub"], "update_offer", "offer", offer_id, changes=update_data)
    await db.commit()
    await db.refresh(offer)
    return OfferOut.model_validate(offer)


@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Offer not found"})

    offer.is_active = False
    offer.updated_at = now_utc()
    await _audit(db, current_user["sub"], "delete_offer", "offer", offer_id)
    await db.commit()


# ---------------------------------------------------------------------------
# Ledger correction (Story L.5 / PD.2 — reversal, append-only)
# ---------------------------------------------------------------------------


@router.post("/corrections", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
async def correct_ledger(
    body: CorrectionRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CorrectionResponse:
    """Create a reversal/correction entry. Never modifies existing rows (PD.2)."""
    # Verify original entry exists
    orig_result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.id == body.related_entry_id)
    )
    original = orig_result.scalar_one_or_none()
    if not original:
        raise HTTPException(
            status_code=404,
            detail={"code": "ENTRY_NOT_FOUND", "message": "Original ledger entry not found"},
        )

    # Verify member exists
    member_result = await db.execute(select(Member).where(Member.id == body.member_id))
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Member not found"})

    entry = LedgerEntry(
        member_id=body.member_id,
        amount=body.amount,
        transaction_type=TransactionType.correction,
        source="admin_correction",
        related_entry_id=body.related_entry_id,
        description=f"Correction by admin {current_user['sub']}: {body.description}",
    )
    db.add(entry)
    await db.flush()

    await _audit(
        db,
        current_user["sub"],
        "ledger_correction",
        "ledger_entry",
        entry.id,
        member_id=body.member_id,
        amount=body.amount,
        related_entry_id=body.related_entry_id,
        reason=body.description,
    )

    await db.commit()
    await db.refresh(entry)

    logger.info(
        "Admin %s corrected ledger for member %s: %d pts (related=%s)",
        current_user["sub"],
        body.member_id,
        body.amount,
        body.related_entry_id,
        extra={"user_id": current_user["sub"], "operation": "correction"},
    )

    return CorrectionResponse(
        transaction_id=entry.id,
        member_id=body.member_id,
        amount=body.amount,
        related_entry_id=body.related_entry_id,
        timestamp=entry.created_at,
    )
