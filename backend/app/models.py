import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MemberRole(str, enum.Enum):
    member = "member"
    admin = "admin"
    manager = "manager"


class TransactionType(str, enum.Enum):
    ingest = "ingest"
    exchange_out = "exchange_out"
    exchange_in = "exchange_in"
    redemption = "redemption"
    reversal = "reversal"
    correction = "correction"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Member(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, native_enum=False), default=MemberRole.member, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="member", foreign_keys="LedgerEntry.member_id"
    )
    redemption_codes: Mapped[list["RedemptionCode"]] = relationship(
        "RedemptionCode", back_populates="member"
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class LedgerEntry(Base):
    """Append-only financial ledger — never UPDATE or DELETE rows."""

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("members.id"), nullable=False
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # positive=credit, negative=debit
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False), nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Idempotency key — unique per partner submission; NULL allowed for system entries
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    # Link to the original entry this entry corrects/reverses
    related_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ledger_entries.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    member: Mapped["Member"] = relationship(
        "Member", back_populates="ledger_entries", foreign_keys=[member_id]
    )
    related_entry: Mapped["LedgerEntry | None"] = relationship(
        "LedgerEntry", remote_side="LedgerEntry.id", foreign_keys=[related_entry_id]
    )


class ExchangeRate(Base):
    """Database-driven exchange rates — ops can update without code changes (PD.3)."""

    __tablename__ = "exchange_rates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    rate: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    min_amount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offers: Mapped[list["Offer"]] = relationship("Offer", back_populates="location")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_available: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # None = unlimited
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    location: Mapped["Location"] = relationship("Location", back_populates="offers")
    redemption_codes: Mapped[list["RedemptionCode"]] = relationship(
        "RedemptionCode", back_populates="offer"
    )


class RedemptionCode(Base):
    """8-char alphanumeric code (PD.4), valid for 15 minutes."""

    __tablename__ = "redemption_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("members.id"), nullable=False
    )
    offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("offers.id"), nullable=False
    )
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ledger_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ledger_entries.id"), nullable=True
    )

    member: Mapped["Member"] = relationship("Member", back_populates="redemption_codes")
    offer: Mapped["Offer"] = relationship("Offer", back_populates="redemption_codes")


class AuditLog(Base):
    """Immutable audit trail for all admin actions (Story A.2)."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    admin_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
