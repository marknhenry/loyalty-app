"""Account & balance routes (Story L.1)."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import LedgerEntry, Member, TransactionType
from app.schemas import AccountResponse, BalanceResponse, MemberOut, TransactionOut

logger = logging.getLogger("loyalty_app")
router = APIRouter(prefix="/account", tags=["account"])


async def _get_member_or_404(member_id: str, db: AsyncSession) -> Member:
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found"},
        )
    return member


async def _get_balance(member_id: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.member_id == member_id
        )
    )
    return int(result.scalar())


@router.get("/me", response_model=AccountResponse)
async def get_my_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    from_date: datetime | None = Query(None, description="Filter transactions from this date"),
    to_date: datetime | None = Query(None, description="Filter transactions up to this date"),
    tx_type: TransactionType | None = Query(None, description="Filter by transaction type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AccountResponse:
    member_id = current_user["sub"]
    member = await _get_member_or_404(member_id, db)
    balance = await _get_balance(member_id, db)

    query = select(LedgerEntry).where(LedgerEntry.member_id == member_id)
    if from_date:
        query = query.where(LedgerEntry.created_at >= from_date)
    if to_date:
        query = query.where(LedgerEntry.created_at <= to_date)
    if tx_type:
        query = query.where(LedgerEntry.transaction_type == tx_type)

    query = query.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    entries = result.scalars().all()

    return AccountResponse(
        member=MemberOut.model_validate(member),
        balance=balance,
        transactions=[TransactionOut.model_validate(e) for e in entries],
    )


@router.get("/{member_id}/balance", response_model=BalanceResponse)
async def get_member_balance(
    member_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BalanceResponse:
    """Admin or self can view a member's balance."""
    caller_id = current_user["sub"]
    caller_role = current_user.get("role", "member")

    if caller_id != member_id and caller_role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot view another member's balance"},
        )

    await _get_member_or_404(member_id, db)
    balance = await _get_balance(member_id, db)
    return BalanceResponse(member_id=member_id, balance=balance)
