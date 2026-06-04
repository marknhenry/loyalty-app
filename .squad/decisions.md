# Squad Decisions

## Active Decisions

### 2026-06-04T19:35:16.745+04:00: Custom squad roster initialized
**By:** Mark Henry (via Copilot)
**What:** Team names set explicitly to Bond (Lead), Leonardo (Architect), Donatello (Integration Engineer), Rafaello (Platform Engineer), Picasso (Frontend Developer), Scribe (Session Logger), and Moneypenny (Work Monitor).
**Why:** Establish a fixed, user-defined operating roster for loyalty-app execution.

### 2026-06-04T19:40:10.226+04:00: Root Project Structure
**By:** Bond
**What:** Adopt a top-level monorepo layout with dedicated root folders: `frontend/`, `backend/`, `infra/`, `docs/`.
**Why:** This separates concerns between user experience, service logic, operations, and documentation so parallel agent work can proceed without file overlap.
**Impact:** Frontend and backend streams can scaffold internals independently. Infrastructure and documentation have explicit homes from day one. Root onboarding and ignores now align with a React + Python stack.

### 2026-06-04T19:40:10.226+04:00: FastAPI Backend Scaffold
**By:** Donatello
**What:** Scaffold backend service with FastAPI and Uvicorn using an app package layout (`app/main.py`, `app/api/routes/*`) and a thin project entrypoint (`backend/main.py`).
**Why:** FastAPI is lightweight, API-first, and enables quick evolution from placeholder routes to production-ready service modules with clear router separation. Use `uvicorn` core package for broader Python/Windows compatibility without requiring local C++ build tools.
**Outcome:** Ready for rapid route expansion and integration with external loyalty point APIs.

### 2026-06-04T19:40:10.226+04:00: React + TypeScript + Vite Frontend Scaffold
**By:** Picasso
**What:** Use a Vite + React + TypeScript scaffold in `frontend/` as the baseline UI foundation.
**Why:** Keeps setup modern and minimal, with fast iteration (`vite`), type safety (`typescript`), and built-in lint tooling suited for future loyalty feature work.
**Outcome:** Frontend-ready for loyalty point collection, exchange, and redemption flows.

### 2026-06-04T19:40:10.226+04:00: Root Workflow Package & Platform Stack
**By:** Rafaello
**What:** Adopt a root `package.json` as a lightweight task runner with frontend npm wrappers and backend Python wrappers, using `concurrently` for dual-service startup.
**Why:** Keeps local platform workflow simple, avoids touching service internals, and provides one-command setup/dev entry points from repository root.
**Related:** `package.json`, `.env.example`, `infra/README.md`.
**Follow-up:** Replace backend placeholder validation steps with real commands once backend toolchain is finalized.

### 2026-06-04T19:46:50.800+04:00: Design Review Decisions — Phase 1 Critical Path
**By:** Bond (Lead)  
**Status:** ✅ APPROVED

**Scope:** 11 architectural and operational decisions covering ledger model, authentication, API key management, exchange rates, redemption codes, frontend state, docker-compose setup, error responses, validation, testing, and environment configuration.

**Key Decisions (All Approved):**
- **Ledger append-only** (immutable transactions for financial audit trail) ✅
- **JWT auth** with 15-min access token + 7-day refresh token (httpOnly cookie) ✅
- **API key authentication** for external apps (scalable to OAuth2 in v2) ✅
- **Exchange rates** in database, not hardcoded (ops-driven flexibility) ✅
- **8-digit alphanumeric redemption codes** (easy in-store entry; non-guessable) ✅
- **React Context API** for MVP state management (upgrade to Zustand if needed) ✅
- **docker-compose** for local dev (PostgreSQL + Redis + services) ✅
- **Consistent error responses** with structured schema ✅
- **Pydantic validation** on all routes (type-safe API boundary) ✅
- **70% test coverage** target on business logic ✅
- **.env configuration** for secrets management (not hardcoded) ✅

**Impact:** Establishes critical baseline for backend data models, security posture, and developer experience before Phase 1 implementation begins.

**Owner:** Bond (Lead) — Approved by Mark Henry on 2026-06-04T21:44:04.147+04:00

**Reference:** Full design review details in `decisions/inbox/bond-design-review.md` (now merged).

---

### 2026-06-04T19:46:50.800+04:00: Architecture Documentation — Four-View Baseline
**By:** Leonardo (Architect)  
**Status:** Accepted

**Scope:** Created baseline architecture documentation set (`docs/architecture/`) covering:
1. System Context — platform boundary, external actors
2. Container/Component — internal topology and API routes
3. Core Sequence — end-to-end points flow (ingestion → exchange → redemption)
4. Deployment/Runtime — local dev and cloud topology

**Key Architectural Principles:**
- Event-driven ingestion (partner webhooks, not polling)
- Double-entry ledger (financial audit trail + zero-sum invariant)
- Async worker (Celery) for spike handling
- PostgreSQL (ledger) + Redis (cache/queue)
- Stateless compute (horizontal scaling)

**Consequences:** Team has shared visual reference; clear integration points for future domain services.

**Deferred Questions:** Celery vs. ARQ, cloud provider choice, partner webhook auth scheme (HMAC vs. mTLS).

**Reference:** Full architecture review in `decisions/inbox/leonardo-architecture-review.md` (now merged).

---

### 2026-06-04T19:56:55.410+04:00: Issue Triage — Design Review + Requirements → Backlog
**By:** Bond (Lead)  
**Status:** ✅ UNBLOCKED FOR PHASE 1

**What:** Extracted all actionable risks, open items, pending tasks, and follow-up actions from design review and requirements into formal Issue Register (`docs/backlog-issues.md`).

**Key Findings:**
- **3 CRITICAL blockers:** JWT auth middleware, database models + PostgreSQL, frontend API integration
- **6 HIGH priority:** Validation, test infrastructure, docker-compose, CI/CD, ledger safety, concurrency
- **2 MEDIUM priority:** Rate limiting, structured logging
- **2 Pending decisions:** Point ingestion API design ✅ APPROVED, ledger correction workflow ✅ APPROVED

**Routing Summary:**
- Donatello (Backend): 7 issues
- Picasso (Frontend): 3 issues (working with Mark Henry on UI mockup)
- Rafaello (Platform): 2 issues
- Mark Henry (Product): 2 issues (UI direction)
- **Total: 14 actionable items — READY FOR PHASE 1 KICKOFF**

**Outcome:** All design decisions approved by Mark Henry. Phase 1 implementation can begin immediately.

---

### 2026-06-04T21:44:04.147+04:00: Phase 1 Pending Decisions — APPROVED
**By:** Mark Henry (Product Owner)  
**Status:** ✅ APPROVED

**Decisions:**
1. **PD.1: Point Ingestion API** — API key auth + Idempotency-Key header ✅
2. **PD.2: Ledger Correction Workflow** — Reversal transactions (immutable); members see corrections in UI ✅
3. **PD.3: Exchange Rate Configuration** — Database-driven rates (ops flexibility) ✅
4. **PD.4: Redemption Code Format** — 8-digit alphanumeric (easy in-store entry) ✅

**Impact:** Unblocks all Phase 1 backend implementation (Stories L.2, L.3, L.4, L.5).

**Reference:** User stories with full acceptance criteria in `docs/user-stories.md`

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
