"""Point ingestion endpoint for partner apps (Story L.2 / PD.1).

Authentication: X-API-Key header
Idempotency:    Idempotency-Key header
Rate limiting:  100 req/min per API key (Story O.2)
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.rate_limit import limiter
from app.models import APIKey, LedgerEntry, Member, TransactionType
from app.schemas import IngestRequest, IngestResponse
from app.utils import hash_api_key

logger = logging.getLogger("loyalty_app")
router = APIRouter(tags=["loyalty"])


async def _verify_api_key(
    x_api_key: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """Validate X-API-Key header against hashed keys in the database."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_API_KEY", "message": "X-API-Key header required"},
        )

    key_hash = hash_api_key(x_api_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        logger.warning("Invalid API key attempt (hash=%s...)", key_hash[:8])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_API_KEY", "message": "Invalid or inactive API key"},
        )

    # Stamp last_used_at without a full ORM update (append-friendly)
    api_key_obj.last_used_at = datetime.now(UTC)
    await db.commit()
    return api_key_obj


@router.post("/loyalty/ingest", response_model=IngestResponse)
@limiter.limit("100/minute")
async def ingest_points(
    request: Request,
    body: IngestRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    api_key_obj: APIKey = Depends(_verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    # --- Validate member exists ---
    result = await db.execute(select(Member).where(Member.id == body.member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member ID not found"},
        )

    # --- Idempotency check (PD.1) ---
    if idempotency_key:
        existing = await db.execute(
            select(LedgerEntry).where(
                LedgerEntry.idempotency_key == idempotency_key
            )
        )
        existing_entry = existing.scalar_one_or_none()
        if existing_entry:
            logger.info(
                "Idempotent replay for key %s (txn=%s)", idempotency_key, existing_entry.id
            )
            balance_result = await db.execute(
                select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                    LedgerEntry.member_id == body.member_id
                )
            )
            balance = int(balance_result.scalar())
            return IngestResponse(
                transaction_id=existing_entry.id,
                balance_after=balance,
                timestamp=existing_entry.created_at,
            )

    # --- Create ledger entry ---
    description_parts = [f"Ingest from {api_key_obj.partner_name}"]
    if body.source:
        description_parts.append(f"via {body.source}")

    entry = LedgerEntry(
        member_id=body.member_id,
        amount=body.amount,
        transaction_type=TransactionType.ingest,
        source=body.source,
        idempotency_key=idempotency_key,
        description=" | ".join(description_parts),
    )
    db.add(entry)
    await db.flush()  # get entry.id + created_at before balance query

    # --- Calculate new balance ---
    balance_result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.member_id == body.member_id
        )
    )
    balance = int(balance_result.scalar())

    await db.commit()
    await db.refresh(entry)

    logger.info(
        "Ingested %d points for member %s (txn=%s)",
        body.amount,
        body.member_id,
        entry.id,
        extra={"user_id": body.member_id, "operation": "ingest"},
    )

    return IngestResponse(
        transaction_id=entry.id,
        balance_after=balance,
        timestamp=entry.created_at,
    )
