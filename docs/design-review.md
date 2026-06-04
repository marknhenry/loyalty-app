# Loyalty Platform — Design Review

**Conducted by:** Bond (Lead)  
**Date:** 2026-06-04  
**Participants:** TBD (squad handoff)  
**Status:** Architecture review complete; implementation planning phase

---

## Scope

This design review covers the monorepo scaffold, technology choices, and high-level architecture in relation to MVP requirements (see `docs/requirements.md`).

---

## Strengths

### 1. **Smart Monorepo Structure**
✅ **Verdict:** Strengths outweigh complexity for this team size.

- Clear separation: `frontend/`, `backend/`, `infra/`, `docs/`
- Shared root npm tasks enable parallel development (frontend and backend can run simultaneously)
- .squad directory co-locates team coordination artifacts (decisions, ceremonies, agents)
- Single git repo simplifies dependency management and shared versioning

**Recommendation:** Keep structure; codify team coordination workflows in `.squad/ceremonies.md`.

---

### 2. **Pragmatic Tech Stack**
✅ **Verdict:** Right tooling for MVP velocity and scalability.

- **Frontend:** React 19 + TypeScript + Vite
  - TypeScript catches bugs early (especially critical for financial transactions)
  - Vite provides fast dev/build cycles
  - React ecosystem is mature for this UI complexity
  
- **Backend:** FastAPI + Uvicorn
  - Built-in OpenAPI documentation (auto-generated API contracts)
  - Native async/await support (scales well for I/O-bound point ingestion)
  - Type hints enforce API contract correctness
  - Lightweight; no Django overhead
  
- **Environment:** npm task orchestration + concurrently (backend + frontend in parallel)
  - Simplifies local dev (single `npm run dev` command)
  - Matches infra automation patterns

**Recommendation:** This stack is locked in; no concerns.

---

### 3. **API Versioning & Contract Clarity**
✅ **Verdict:** Forward-thinking.

- `/api/v1/` prefix already baked into backend scaffold
- FastAPI's OpenAPI integration provides self-documenting API
- Health check endpoint establishes baseline ops pattern

**Recommendation:** Leverage FastAPI's auto-generated Swagger UI for frontend developer onboarding.

---

## Risks

### 1. **Missing Authentication & Authorization** 🔴 CRITICAL

**Issue:** No JWT validation middleware in backend. Routes are currently unauthenticated.

**Impact:**
- Any API client can call `/api/v1/loyalty/accounts/{member_id}` and access any member's data (security breach)
- Admin operations (point adjustments, location management) have no role checks
- Frontend has no login UI; cannot be tested end-to-end

**Mitigation (MVP Blocker):**
- Implement JWT middleware in FastAPI (validate Authorization header, extract subject/role)
- Add `@requires_role("member")` and `@requires_role("admin")` decorators to routes
- Create login endpoint (`POST /api/v1/auth/login`) and token refresh logic
- Frontend implements auth pages (login, registration) + token storage (secure httpOnly cookie or localStorage with CSRF protection)

**Owner:** Backend Lead  
**Priority:** Block all other backend work; start immediately

---

### 2. **No Data Layer (Database, ORM, Models)** 🔴 CRITICAL

**Issue:** Backend routes return hardcoded responses; no database integration planned.

**Impact:**
- Cannot persist member accounts, transactions, or redemption locations
- Ledger logic (point balance calculation, immutability) cannot be implemented
- No state persists between service restarts
- Cannot validate exchange rules or rate-limit requests

**Mitigation (MVP Blocker):**
- Define SQLAlchemy ORM models: `Member`, `PointLedger`, `ExchangeRule`, `RedemptionLocation`, `RedemptionCode`
- Set up PostgreSQL connection pooling (async sqlalchemy or asyncpg)
- Implement database schema migrations (Alembic)
- Add database setup to `docker-compose.yml` (local dev)

**Owner:** Backend Lead  
**Priority:** Start after auth middleware; critical path item

---

### 3. **Frontend API Integration Missing** 🔴 CRITICAL

**Issue:** Frontend scaffold has no HTTP client or integration with backend API.

**Impact:**
- No way to test frontend + backend handshake locally
- Member login/account UI cannot be developed
- Exchange and redemption features cannot be built

**Mitigation (MVP Blocker):**
- Add `axios` or `fetch` API client library to frontend package.json
- Create API service module (e.g., `src/services/api.ts`) with methods for:
  - `login(email, password)` → returns JWT token
  - `getMemberAccount(memberId)` → returns balance + history
  - `initiateExchange(fromMemberId, toMemberId, points, rate)` → records exchange
  - `redeemPoints(memberId, locationId, offer, points)` → returns redemption code
- Wire up Vite proxy (`vite.config.ts`) to route `/api/` calls to `http://localhost:4000/api/`
- Implement token management (storage, refresh, expiry)

**Owner:** Frontend Lead  
**Priority:** Start in parallel with backend auth; enables e2e testing

---

### 4. **No Data Validation & Error Handling** 🟡 HIGH

**Issue:** Pydantic models not in use; no input validation on loyalty routes. Error responses are inconsistent.

**Impact:**
- Invalid requests (negative points, malformed member_id) are accepted silently
- Frontend cannot reliably handle error cases
- Debugging production issues is difficult (no error context)

**Mitigation (MVP):**
- Define Pydantic request/response models for all endpoints
- Add global exception handler in FastAPI (return consistent error format: `{"error": "...", "code": "...", "details": {...}}`)
- Validate business logic (e.g., point balance >= redemption cost)
- Return appropriate HTTP status codes (400 for bad request, 403 for forbidden, 409 for conflict)

**Owner:** Backend Lead  
**Timeline:** Implement during auth/data layer work

---

### 5. **Testing Infrastructure is Placeholder** 🟡 HIGH

**Issue:** Both `npm run test` and `npm run test:backend` are stubs.

**Impact:**
- No CI/CD gates (untested code can merge)
- Ledger consistency bugs won't be caught (critical for financial correctness)
- Frontend state management won't be tested
- Concurrent transaction safety cannot be verified

**Mitigation (MVP):**
- **Backend:** Set up pytest + conftest.py (database fixtures, auth mocking)
  - Write unit tests: auth middleware, ledger math, exchange logic
  - Write integration tests: full flow (login → ingest points → exchange → redeem)
  - Aim for >70% coverage on business logic
  
- **Frontend:** Set up Vitest (or Jest) + React Testing Library
  - Test auth pages (login form, token storage)
  - Test account page (balance display, transaction history)
  - Aim for >60% coverage on UI logic (can supplement with e2e Cypress tests later)

**Owner:** QA Lead (or Backend/Frontend Leads)  
**Timeline:** Implement in parallel with feature work (not a blocker, but needed before MVP sign-off)

---

### 6. **Deployment & Infrastructure Undefined** 🟡 HIGH

**Issue:** `infra/` folder contains only README placeholders; no docker-compose, no cloud IaC, no CI/CD.

**Impact:**
- Cannot run services locally without manual setup (Database, Redis)
- No clear path to staging/production deployment
- Ops team has no runbooks (incident response, rollback procedures)

**Mitigation (MVP):**
- Create `infra/docker-compose.yml` with services: frontend, backend, postgres, redis
  - Mount volumes for code (hot reload)
  - Configure networks for inter-service communication
  - Environment file injection from `.env`
  
- Create `infra/local-setup.md` with steps:
  - `docker-compose up` to start all services
  - `npm run setup` to install dependencies
  - `npm run migrate` to initialize database schema
  
- GitHub Actions workflow (`.github/workflows/ci.yml`):
  - Run frontend lint/test/build on PR
  - Run backend lint/test/build on PR
  - Deploy to staging on merge to `main` (placeholder for now)

**Owner:** DevOps Lead (or Backend Lead)  
**Timeline:** Complete before MVP handoff (needed for squad validation)

---

### 7. **Ledger Immutability & Concurrency Model Unclear** 🟡 HIGH

**Issue:** No documented strategy for ledger writes, conflict resolution, or race condition prevention.

**Impact:**
- Two concurrent exchanges might double-spend points
- Point balance calculation could be incorrect if ledger is mutated
- Audit trail loses integrity if corrections bypass proper channels

**Mitigation (MVP):**
- **Design Decision:** Ledger table is append-only (INSERT only; no UPDATE/DELETE)
  - Corrections are recorded as new entries (e.g., debit entry marked "correction for txn_id: X")
  - Point balance is SUM of all non-reversed entries
  
- **Concurrency Safety:**
  - Use database row-level locking or SELECT ... FOR UPDATE when reading current balance before debit
  - Wrap exchange/redeem operations in database transactions (SERIALIZABLE isolation level or advisory locks)
  - Test with concurrent load (e.g., 10 members exchanging simultaneously)
  
- **Validation:**
  - Balance check: `SUM(ledger) >= redemption_cost` before recording debit
  - Atomic transaction: point debit + audit entry recorded together or not at all

**Owner:** Backend Lead + QA Lead  
**Timeline:** Document in `docs/architecture.md` (new); implement during point logic work

---

### 8. **No Rate Limiting or DDoS Protection** 🟡 MEDIUM

**Issue:** No rate limiting on API endpoints; external apps can flood point ingestion API.

**Impact:**
- Malicious/accidental point ingestion spike could overwhelm database
- Members can spam redemption requests
- Frontend could hammer API with every keystroke

**Mitigation (MVP):**
- Add rate limiting middleware (e.g., `slowapi` Python package or Redis-backed counter)
  - Per-IP or per-API-key rate limit (e.g., 100 requests/min for external app ingestion)
  - Per-member rate limit for redemptions (e.g., 10 redemptions/hour)
  
- Frontend: Debounce/throttle input (e.g., exchange amount field only updates ledger every 500ms)

**Owner:** Backend Lead  
**Timeline:** Implement during auth/middleware setup

---

## Missing Pieces

### 1. **API Contract Documentation** 📄

Current: Health and loyalty endpoints exist but lack formal definition.

**Needed (MVP):**
- OpenAPI spec auto-generated by FastAPI
- Swagger UI available at `/docs` endpoint
- Example requests/responses for all endpoints
- Error code catalog (e.g., `INSUFFICIENT_BALANCE`, `INVALID_MEMBER_ID`)

**Recommendation:** Leverage FastAPI's built-in Swagger; reference in `docs/api-contract.md` with examples.

---

### 2. **Database Schema & Migrations** 📊

Current: Only PostgreSQL URL in `.env.example`.

**Needed (MVP):**
- SQL schema file or Alembic migrations
- Indexes on: member_id, created_at (for ledger query performance)
- Constraints: non-negative point balance, immutable ledger entries
- Reference documentation in `docs/data-model.md`

**Recommendation:** Use Alembic; document schema in `docs/data-model.md` with ERD diagram.

---

### 3. **Point Ingestion API Design** 📤

Current: Route exists but is a placeholder.

**Needed (MVP):**
- Define request schema: `{ "member_id", "amount", "source", "metadata" }`
- Define response: `{ "transaction_id", "balance_after", "timestamp" }`
- Define authentication: API key header or OAuth2 bearer token for external apps
- Document idempotency key handling (prevent duplicate ingestion if request retried)

**Recommendation:** Design and document in `docs/api-contract.md` → Point Ingestion section. Get sign-off from backend lead before implementation.

---

### 4. **Frontend State Management** 🎯

Current: No state management library added to package.json.

**Needed (MVP):**
- Choice: Context API (simple) vs. Redux (scalable) vs. Zustand (lightweight)
- Recommendation: Context API for MVP; upgrade to Zustand if complexity grows
- Global state: authenticated user, member account, exchange history
- Token refresh logic on page reload or token expiry

**Recommendation:** Implement with Context API + useReducer; document in `frontend/src/README.md`.

---

### 5. **Error Handling & Logging Strategy** 🛠️

Current: No logging library configured; error responses are ad-hoc.

**Needed (MVP):**
- Backend: Structured logging (JSON format for ELK/CloudWatch)
  - Log level: DEBUG, INFO, WARN, ERROR
  - Include: timestamp, level, request_id, user_id, operation, error details
  - Use Python logging with structured format (e.g., `python-json-logger`)
  
- Frontend: Error boundary + error tracking (optional: Sentry integration)
  - Log client-side errors to monitoring service
  - Display user-friendly error messages (not stack traces)

**Recommendation:** Add logging in backend auth/data layer; wire up frontend error boundary in auth pages.

---

### 6. **Exchange Rate & Redemption Offer Management** 🤝

Current: No admin UI or configuration layer.

**Needed (MVP):**
- Backend endpoints:
  - `POST /api/v1/admin/exchange-rules` — define rate (e.g., 1:1, 2:3)
  - `GET /api/v1/admin/exchange-rules` — list active rules
  - `POST /api/v1/admin/locations` — register redemption location
  - `POST /api/v1/admin/offers` — create redeemable offers (e.g., "$10 gift card for 1000 points")

- Frontend admin dashboard: form to create/edit rules, locations, offers

**Recommendation:** Implement after core ledger logic; start with hardcoded rules for MVP. Upgrade to admin UI in v1.1.

---

## Architecture Diagram (High-Level)

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  React Frontend (Vite)                                   │ │
│  │  - Login / Account Views                                 │ │
│  │  - Exchange / Redemption UI                              │ │
│  │  - Admin Dashboard (future)                              │ │
│  └──────────────────┬──────────────────────────────────────┘ │
└─────────────────────┼────────────────────────────────────────┘
                      │ HTTPS (JWT token in Authorization header)
                      │
         ┌────────────▼─────────────────┐
         │   FastAPI Backend            │
         │   - /api/v1/auth/login       │
         │   - /api/v1/loyalty/accounts │
         │   - /api/v1/loyalty/exchange │
         │   - /api/v1/loyalty/redeem   │
         │   - /api/v1/admin/*          │
         └────────────┬──────────────────┘
                      │
        ┌─────────────┼──────────────────┐
        │             │                  │
   ┌────▼───┐  ┌─────▼─────┐  ┌────────▼────┐
   │PostgreSQL│  │   Redis   │  │ External    │
   │          │  │   Cache   │  │ App APIs    │
   │ Ledger   │  │ (sessions)│  │ (webhooks)  │
   │ Members  │  │           │  │             │
   │ Offers   │  │           │  │             │
   └──────────┘  └───────────┘  └─────────────┘
```

---

## Next Implementation Priorities

### Phase 1: Foundation (Weeks 1–2)
**Blocker for all other work:**
1. Backend: JWT auth middleware + login endpoint
2. Backend: ORM models + database schema (Alembic)
3. Frontend: API client + token management
4. Backend + Frontend: docker-compose setup

### Phase 2: Ledger & Core Flows (Weeks 2–3)
5. Backend: Point ledger CRUD + balance calculation
6. Backend: Point ingestion endpoint (external apps)
7. Backend: Exchange endpoint + validation
8. Backend: Redemption endpoint + code generation

### Phase 3: UI & Testing (Weeks 3–4)
9. Frontend: Account page (balance, history)
10. Frontend: Exchange UI (form, confirmation)
11. Frontend: Redemption UI (location browser, code display)
12. Frontend + Backend: Test suite (>70% coverage)

### Phase 4: Polish & Deployment (Week 5)
13. Error handling + logging on both sides
14. Admin dashboard (stats, member search)
15. CI/CD pipeline (GitHub Actions)
16. Local + staging deployment docs

---

## Design Review Sign-Off

| Role | Name | Notes |
|------|------|-------|
| Lead (Bond) | ✅ | Approval pending Squad handoff |
| Backend Lead | ⏳ | Signature needed |
| Frontend Lead | ⏳ | Signature needed |
| DevOps Lead | ⏳ | Signature needed |

**Required Actions Before Implementation:**
- [ ] Squad reviews and approves requirements.md
- [ ] Squad reviews and approves this design-review.md
- [ ] Backend Lead confirms Phase 1 workstreams and estimates
- [ ] Frontend Lead confirms Phase 1 workstreams and estimates
- [ ] DevOps Lead confirms docker-compose and CI/CD timeline

---

## Appendix: Scaffold Assessment

| Item | Status | Comment |
|------|--------|---------|
| React scaffold | ✅ Ready | TypeScript + Vite configured correctly |
| FastAPI scaffold | ✅ Ready | Routes exist; auth layer missing |
| Root npm tasks | ✅ Ready | Can run both services; backend not set up for actual DB |
| Type checking | ✅ Ready | TypeScript strict mode enforced |
| Linting | ⚠️ ESLint only | Backend needs flake8 + black |
| Testing | ❌ Placeholder | Both frontend and backend need test frameworks |
| Database | ❌ Missing | PostgreSQL connection + models needed |
| Docker | ❌ Missing | docker-compose needed for local dev |
| CI/CD | ❌ Missing | GitHub Actions workflow needed |
| Docs | ⚠️ Minimal | README files exist; architecture docs are new |

---

## References

- `docs/requirements.md` — MVP scope and functional requirements
- `backend/README.md` — Local backend setup
- `frontend/README.md` — Local frontend setup
- `.env.example` — Environment placeholder (to be filled in by infra)
