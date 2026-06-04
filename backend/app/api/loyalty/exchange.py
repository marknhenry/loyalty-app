"""Point exchange endpoint — atomic double-entry, database-driven rates (Story L.3 / PD.3)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import ExchangeRate, LedgerEntry, Member, TransactionType
from app.schemas import ExchangeRequest, ExchangeResponse
from app.utils import now_utc

logger = logging.getLogger("loyalty_app")
router = APIRouter(tags=["loyalty"])


@router.post("/exchange", response_model=ExchangeResponse)
async def exchange_points(
    body: ExchangeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeResponse:
    sender_id = current_user["sub"]

    if sender_id == body.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_EXCHANGE", "message": "Cannot exchange points with yourself"},
        )

    # --- Look up exchange rate from DB (PD.3) ---
    rate_result = await db.execute(
        select(ExchangeRate).where(
            ExchangeRate.name == body.rate_name, ExchangeRate.is_active == True
        )
    )
    rate_obj = rate_result.scalar_one_or_none()
    if not rate_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_RATE", "message": f"Exchange rate '{body.rate_name}' not found"},
        )

    # Validate amount against rate limits
    if body.amount < rate_obj.min_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AMOUNT_TOO_SMALL",
                "message": f"Minimum exchange amount is {rate_obj.min_amount}",
            },
        )
    if rate_obj.max_amount and body.amount > rate_obj.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AMOUNT_TOO_LARGE",
                "message": f"Maximum exchange amount is {rate_obj.max_amount}",
            },
        )

    # --- Verify recipient exists ---
    recipient_result = await db.execute(
        select(Member).where(Member.id == body.recipient_id, Member.is_active == True)
    )
    if not recipient_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "RECIPIENT_NOT_FOUND", "message": "Recipient member not found"},
        )

    # --- Check sender balance (SELECT FOR UPDATE equivalent via row lock) ---
    balance_result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.member_id == sender_id
        )
    )
    sender_balance = int(balance_result.scalar())

    if sender_balance < body.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INSUFFICIENT_BALANCE",
                "message": f"Insufficient balance ({sender_balance} points available)",
            },
        )

    amount_received = int(body.amount * float(rate_obj.rate))

    # --- Atomic double-entry (both writes in same transaction) ---
    debit_entry = LedgerEntry(
        member_id=sender_id,
        amount=-body.amount,
        transaction_type=TransactionType.exchange_out,
        source="exchange",
        description=f"Exchange out to member {body.recipient_id} @ rate {rate_obj.rate}",
    )
    credit_entry = LedgerEntry(
        member_id=body.recipient_id,
        amount=amount_received,
        transaction_type=TransactionType.exchange_in,
        source="exchange",
        description=f"Exchange in from member {sender_id} @ rate {rate_obj.rate}",
    )
    db.add(debit_entry)
    db.add(credit_entry)
    await db.flush()

    # Link entries to each other
    debit_entry.related_entry_id = credit_entry.id
    credit_entry.related_entry_id = debit_entry.id

    await db.commit()
    await db.refresh(debit_entry)
    await db.refresh(credit_entry)

    logger.info(
        "Exchange: %s → %s, %d pts sent, %d pts received",
        sender_id,
        body.recipient_id,
        body.amount,
        amount_received,
        extra={"user_id": sender_id, "operation": "exchange"},
    )

    return ExchangeResponse(
        sender_transaction_id=debit_entry.id,
        recipient_transaction_id=credit_entry.id,
        amount_sent=body.amount,
        amount_received=amount_received,
        rate_applied=float(rate_obj.rate),
        timestamp=debit_entry.created_at,
    )
