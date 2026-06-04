"""Pydantic schemas for all request/response models (TE.3)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth schemas (Story A.1)
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class MemberOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Ledger / Account schemas (Story L.1)
# ---------------------------------------------------------------------------


class TransactionOut(BaseModel):
    id: str
    amount: int
    transaction_type: str
    source: str | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    member: MemberOut
    balance: int
    transactions: list[TransactionOut]


class BalanceResponse(BaseModel):
    member_id: str
    balance: int


# ---------------------------------------------------------------------------
# Point ingestion schemas (Story L.2 / PD.1)
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    member_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0, description="Must be a positive integer")
    source: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None

    @field_validator("member_id")
    @classmethod
    def member_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("member_id cannot be blank")
        return v


class IngestResponse(BaseModel):
    transaction_id: str
    balance_after: int
    timestamp: datetime


# ---------------------------------------------------------------------------
# Exchange schemas (Story L.3)
# ---------------------------------------------------------------------------


class ExchangeRequest(BaseModel):
    recipient_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0, description="Points to give (positive integer)")
    rate_name: str = Field(default="standard", description="Exchange rate key from DB")


class ExchangeResponse(BaseModel):
    sender_transaction_id: str
    recipient_transaction_id: str
    amount_sent: int
    amount_received: int
    rate_applied: float
    timestamp: datetime


# ---------------------------------------------------------------------------
# Redemption schemas (Story L.4)
# ---------------------------------------------------------------------------


class RedeemRequest(BaseModel):
    offer_id: str = Field(..., min_length=1)


class RedeemResponse(BaseModel):
    redemption_id: str
    code: str  # 8-char alphanumeric (PD.4)
    offer_id: str
    points_deducted: int
    expires_at: datetime
    qr_data: str  # URL-safe string for QR generation


class UseCodeRequest(BaseModel):
    code: str = Field(..., min_length=8, max_length=8)


class UseCodeResponse(BaseModel):
    redemption_id: str
    member_id: str
    offer_id: str
    redeemed_at: datetime


# ---------------------------------------------------------------------------
# Admin — Location schemas (Story R.1)
# ---------------------------------------------------------------------------


class LocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str | None = None
    hours: str | None = None
    contact: str | None = None


class LocationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    address: str | None = None
    hours: str | None = None
    contact: str | None = None
    is_active: bool | None = None


class LocationOut(BaseModel):
    id: str
    name: str
    address: str | None
    hours: str | None
    contact: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Admin — Offer schemas (Story R.1)
# ---------------------------------------------------------------------------


class OfferCreate(BaseModel):
    description: str = Field(..., min_length=1)
    points_cost: int = Field(..., gt=0)
    quantity_available: int | None = Field(None, ge=0)
    expires_at: datetime | None = None


class OfferUpdate(BaseModel):
    description: str | None = None
    points_cost: int | None = Field(None, gt=0)
    quantity_available: int | None = Field(None, ge=0)
    expires_at: datetime | None = None
    is_active: bool | None = None


class OfferOut(BaseModel):
    id: str
    location_id: str
    description: str
    points_cost: int
    quantity_available: int | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LocationWithOffersOut(LocationOut):
    offers: list[OfferOut] = []


# ---------------------------------------------------------------------------
# Admin — Ledger correction (Story L.5 / PD.2)
# ---------------------------------------------------------------------------


class CorrectionRequest(BaseModel):
    member_id: str
    amount: int  # positive=credit back, negative=additional debit
    related_entry_id: str
    description: str = Field(..., min_length=1)


class CorrectionResponse(BaseModel):
    transaction_id: str
    member_id: str
    amount: int
    related_entry_id: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Shared error response (TE.2 — consistent error shape)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str | None = None
