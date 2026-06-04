# Project Context

- **Owner:** Mark Henry
- **Project:** loyalty-app
- **Stack:** TBD
- **Created:** 2026-06-04

## Learnings

- Architecture focus: unify points from multiple external apps into one exchange and redemption platform.
- Completed initial architecture documentation set (2026-06-04): system context, container/component, sequence flows, and deployment view — all as Mermaid-in-Markdown under `docs/architecture/`.
- Identified five core containers: React SPA, FastAPI API, Celery Worker, PostgreSQL, Redis.
- Established double-entry ledger as the foundational pattern for point movements (debit+credit pairs, zero-sum invariant).
- Partner ingestion model is push-based (webhooks), processed asynchronously via a task queue to isolate user-facing latency.
- Deployment topology: SPA on CDN, stateless API/workers behind a gateway, managed database with read replicas for query isolation.
- Open decisions deferred: async framework choice, cloud provider, webhook auth scheme.

## Work Log

### 2026-06-04 — Architecture Documentation Consolidation
- **What:** Architecture review merged into squad decision registry with cross-team sync
- **Deliverables:**
  - 4-view baseline architecture documentation (system context, container/component, sequence, deployment)
  - Identified 6 key architectural principles: event-driven ingestion, double-entry ledger, Celery async worker, PostgreSQL + Redis, CDN + gateway topology, stateless compute
  - Deferred decisions: Celery vs. ARQ/Dramatiq, cloud provider choice, partner webhook auth scheme (HMAC vs. mTLS)
- **File Updates:**
  - Architecture decisions merged into `.squad/decisions.md` with Bond's design review
  - Referenced in orchestration log: `.squad/orchestration-log/design-review-2026-06-04.md`
  - Referenced in session log: `.squad/log/design-review-session-2026-06-04.md`
- **Placement:** Architecture diagrams ready for placement under `docs/architecture/` (Mermaid format)
- **Status:** ✅ Consolidated and registry-ready for ceremony handoff
