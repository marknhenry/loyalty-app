"""Redemption code endpoints (Story L.4 / PD.4).

Codes: 8-char alphanumeric, 15-min expiry, single-use.
Rate limited: 10 redemptions/hour per member (Story O.2).
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import limiter
from app.models import LedgerEntry, Offer, RedemptionCode, TransactionType
from app.schemas import RedeemRequest, RedeemResponse, UseCodeRequest, UseCodeResponse
from app.utils import generate_redemption_code, now_utc, redemption_expiry


def _is_expired(dt) -> bool:
    """Compare datetimes safely regardless of timezone-awareness (SQLite vs Postgres)."""
    now = now_utc()
    if dt.tzinfo is None:
        now = now.replace(tzinfo=None)
    return dt < now

logger = logging.getLogger("loyalty_app")
router = APIRouter(tags=["loyalty"])

_MAX_CODE_GEN_ATTEMPTS = 10


@router.post("/redeem", response_model=RedeemResponse)
@limiter.limit("10/hour")
async def create_redemption(
    request: Request,
    body: RedeemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedeemResponse:
    member_id = current_user["sub"]
    request.state.member_id = member_id  # for rate limiter key

    # --- Validate offer ---
    offer_result = await db.execute(
        select(Offer).where(Offer.id == body.offer_id, Offer.is_active == True)
    )
    offer = offer_result.scalar_one_or_none()
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OFFER_NOT_FOUND", "message": "Offer not found or unavailable"},
        )

    if offer.expires_at and _is_expired(offer.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OFFER_EXPIRED", "message": "Offer has expired"},
        )

    if offer.quantity_available is not None and offer.quantity_available <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OFFER_UNAVAILABLE", "message": "Offer is no longer available"},
        )

    # --- Check member balance ---
    balance_result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.member_id == member_id
        )
    )
    balance = int(balance_result.scalar())

    if balance < offer.points_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INSUFFICIENT_BALANCE",
                "message": f"Insufficient balance. Need {offer.points_cost}, have {balance}",
            },
        )

    # --- Generate unique 8-char code (PD.4) ---
    code = None
    for _ in range(_MAX_CODE_GEN_ATTEMPTS):
        candidate = generate_redemption_code()
        existing = await db.execute(
            select(RedemptionCode).where(RedemptionCode.code == candidate)
        )
        if not existing.scalar_one_or_none():
            code = candidate
            break

    if not code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CODE_GENERATION_FAILED", "message": "Could not generate unique code"},
        )

    expires_at = redemption_expiry()

    # --- Atomic: deduct points + create code ---
    ledger_entry = LedgerEntry(
        member_id=member_id,
        amount=-offer.points_cost,
        transaction_type=TransactionType.redemption,
        source=f"offer:{offer.id}",
        description=f"Redemption: {offer.description}",
    )
    db.add(ledger_entry)
    await db.flush()

    redemption = RedemptionCode(
        code=code,
        member_id=member_id,
        offer_id=offer.id,
        points_cost=offer.points_cost,
        expires_at=expires_at,
        ledger_entry_id=ledger_entry.id,
    )
    db.add(redemption)

    # Decrement quantity if limited
    if offer.quantity_available is not None:
        offer.quantity_available -= 1
        if offer.quantity_available <= 0:
            offer.is_active = False

    await db.commit()
    await db.refresh(redemption)

    logger.info(
        "Redemption code %s created for member %s (offer=%s, cost=%d)",
        code,
        member_id,
        offer.id,
        offer.points_cost,
        extra={"user_id": member_id, "operation": "redeem"},
    )

    return RedeemResponse(
        redemption_id=redemption.id,
        code=code,
        offer_id=offer.id,
        points_deducted=offer.points_cost,
        expires_at=expires_at,
        qr_data=f"loyalty://redeem/{code}",
    )


@router.post("/redeem/use", response_model=UseCodeResponse)
async def use_redemption_code(
    body: UseCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UseCodeResponse:
    """Mark a redemption code as used (called by location staff / POS)."""
    result = await db.execute(
        select(RedemptionCode).where(RedemptionCode.code == body.code)
    )
    redemption = result.scalar_one_or_none()

    if not redemption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CODE_NOT_FOUND", "message": "Redemption code not found"},
        )

    if redemption.redeemed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CODE_ALREADY_USED", "message": "Code has already been redeemed"},
        )

    if _is_expired(redemption.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CODE_EXPIRED", "message": "Code has expired"},
        )

    redemption.redeemed_at = now_utc()
    await db.commit()
    await db.refresh(redemption)

    return UseCodeResponse(
        redemption_id=redemption.id,
        member_id=redemption.member_id,
        offer_id=redemption.offer_id,
        redeemed_at=redemption.redeemed_at,
    )
