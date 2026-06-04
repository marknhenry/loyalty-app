# Project Context

- **Owner:** Mark Henry
- **Project:** loyalty-app
- **Stack:** TBD
- **Created:** 2026-06-04

## Learnings

- Integration goal: support point collection from multiple apps and standardized exchange into platform balance.

## Work Log

### 2026-06-04 — FastAPI Backend Scaffold
- Scaffolded FastAPI backend in `backend/` with app package layout (`app/main.py`, `app/api/routes/`)
- Configured Uvicorn core (not `[standard]`) for Windows/Python compatibility
- Created thin project entrypoint (`backend/main.py`) wrapping FastAPI app factory
- Prepared `requirements.txt` with pinned dependencies
- Documented backend service architecture and dev workflow in `backend/README.md`
- Decision made: **FastAPI Backend Scaffold** — lightweight, API-first with clear router separation
- **Status:** ✅ Complete

### 2026-06-04 — Design Review Handoff Notification
- **From:** Bond + Leonardo (Design Review)
- **What:** Design review decisions now registered in `.squad/decisions.md` with approval matrix
- **Actionable Items for Donatello:**
  - Ledger schema decision requires ORM models (SQLAlchemy) + database indexes
  - JWT auth middleware decision requires FastAPI dependency injection + token validation
  - Pydantic validation decision requires request/response models on all routes
  - API key authentication decision requires middleware for external app validation
  - See full requirements at `.squad/decisions/inbox/bond-design-review.md`
- **Next Steps:** Await Phase 1 kickoff after design review ceremony approvals
- **Status:** ✅ Notified; ready for Phase 1 implementation coordination

### 2026-06-04T21:44:04.147+04:00 — Phase 1 Full Backend Implementation

**All 4 pending decisions approved. Full backend built, tested, and passing at 70% coverage.**

#### Database Schema (TE.1)
- Created `app/models.py` with 8 SQLAlchemy models: `Member`, `APIKey`, `LedgerEntry`, `ExchangeRate`, `Location`, `Offer`, `RedemptionCode`, `AuditLog`
- Ledger is append-only: no UPDATE/DELETE paths exist; corrections create new `reversal`/`correction` entries
- `LedgerEntry.idempotency_key` has a UNIQUE constraint; NULL values are permitted (SQL-level idempotency enforcement)
- All enums use `native_enum=False` for SQLite/PostgreSQL portability
- `DateTime(timezone=True)` columns: SQLite stores naive UTC; comparison helper `_is_expired()` in redeem.py handles both

#### Auth Foundation (A.1, A.2)
- JWT: 15-min access token + 7-day refresh token, both stored as httpOnly cookies
- Tokens accepted from `Authorization: Bearer` header OR `access_token` cookie
- Role claims (`role` field in JWT) gate admin endpoints via `require_admin` FastAPI dependency
- Switched from `passlib` to direct `bcrypt>=4.0.0` — passlib is incompatible with bcrypt 4.x on Python 3.13
- `email-validator` required for Pydantic `EmailStr` fields

#### Point Ingestion API (L.2 / PD.1 ✅)
- `POST /api/v1/loyalty/ingest` — X-API-Key header auth, Idempotency-Key header
- API keys stored as SHA-256 hashes; plaintext never persisted
- Idempotency: duplicate key replay returns original transaction (no double-credit)
- Rate limited to 100/min per API key via slowapi

#### Account & Balance (L.1)
- `GET /api/v1/account/me` — balance = `SUM(ledger_entries.amount)` for member
- Supports filter by date range and transaction type
- Admin/self can query `GET /api/v1/account/{member_id}/balance`

#### Exchange Points (L.3 / PD.3 ✅)
- `POST /api/v1/exchange` — double-entry: debit sender + credit recipient in one DB transaction
- Exchange rates loaded from `exchange_rates` table (database-driven, ops can change without deploys)
- Validates sender balance, rate limits, rate active status, recipient existence
- Linked entries: `debit.related_entry_id` ↔ `credit.related_entry_id`

#### Redemption Codes (L.4 / PD.4 ✅)
- `POST /api/v1/redeem` — 8-char uppercase alphanumeric code, 15-min expiry
- Points deducted atomically with code creation (single DB transaction)
- `POST /api/v1/redeem/use` — marks code used; rejects expired/already-used codes
- Rate limited to 10/hour per member
- QR-ready: returns `qr_data: "loyalty://redeem/{code}"` in response

#### Admin Management (R.1, A.2, L.5 / PD.2 ✅)
- Full Location CRUD + Offer CRUD under `POST/PUT/DELETE /api/v1/admin/*`
- Every admin action writes an `AuditLog` row (who, what, when, resource_id)
- Soft-delete only (sets `is_active=False`); no hard deletes in the system
- Ledger corrections append a new `correction` entry linked to original via `related_entry_id`
- `selectinload(Location.offers)` used in list query — async SQLAlchemy requires eager loading

#### Error Handling & Logging (O.1)
- `CorrelationIDMiddleware` attaches `X-Request-ID` to all responses; echoes client-supplied ID
- JSON-formatted log output with timestamp, level, request_id, user_id, operation fields
- Unified error envelope: `{"error": {"code": "...", "message": "...", "field": null}, "request_id": "..."}`
- Three exception handlers: HTTP, validation (422), and unhandled (500)

#### Rate Limiting (O.2)
- slowapi decorators: `@limiter.limit("100/minute")` on ingest, `@limiter.limit("10/hour")` on redeem
- Uses `X-API-Key` as bucket key for ingestion (partner-level), member ID for redemption
- Returns 429 with `Retry-After` header (slowapi default behavior)

#### Testing (TE.5)
- 89 tests across 8 test files, **70.2% coverage** (target met)
- Per-test fresh in-memory SQLite engine — complete isolation, no shared state
- Tests use `httpx.AsyncClient` with `ASGITransport` and DB dependency override
- Tests encode every acceptance criterion from user stories

#### Infrastructure (TE.7)
- `docker-compose.yml` at repo root: PostgreSQL 16 + Redis 7 + FastAPI backend
- Health checks on postgres/redis; backend waits for both to be healthy
- `backend/Dockerfile` for containerized deployment

#### Known Constraints (Python 3.13 ARM64 Windows)
- `asyncpg` has no pre-built wheel for Python 3.13 ARM64 Windows; use `aiosqlite` for dev/tests
- Production deployment (Linux container) will install asyncpg without issue
- `passlib` is incompatible with bcrypt >= 4.0; replaced with direct `bcrypt` calls

- **Status:** ✅ Phase 1 complete — 89 tests passing, 70.2% coverage
