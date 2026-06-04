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
