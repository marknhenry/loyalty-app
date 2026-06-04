"""Utility helpers — JWT, password hashing, code generation, audit logging."""

import hashlib
import json
import random
import string
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ---------------------------------------------------------------------------
# API key hashing (SHA-256 — never store plaintext keys)
# ---------------------------------------------------------------------------


def hash_api_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure 40-char API key."""
    alphabet = string.ascii_letters + string.digits
    return "lp_" + "".join(random.SystemRandom().choices(alphabet, k=37))


# ---------------------------------------------------------------------------
# Redemption code generation (PD.4 — 8-char alphanumeric)
# ---------------------------------------------------------------------------

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_redemption_code() -> str:
    """Generate a non-guessable 8-character alphanumeric code."""
    return "".join(random.SystemRandom().choices(_CODE_ALPHABET, k=8))


# ---------------------------------------------------------------------------
# Audit log serialization helper
# ---------------------------------------------------------------------------


def audit_details(**kwargs) -> str:
    """Serialize arbitrary kwargs to a JSON string for AuditLog.details."""
    return json.dumps(kwargs, default=str)


# ---------------------------------------------------------------------------
# Balance calculation (pure function — testable without DB)
# ---------------------------------------------------------------------------


def calculate_balance(entries: list) -> int:
    """Sum all ledger entry amounts. Positive = credit, negative = debit."""
    return sum(e.amount for e in entries)


# ---------------------------------------------------------------------------
# Datetime helpers
# ---------------------------------------------------------------------------


def now_utc() -> datetime:
    return datetime.now(UTC)


def redemption_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=15)
