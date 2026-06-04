# Loyalty Platform — Requirements

**Owner:** Mark Henry  
**Lead:** Bond  
**Created:** 2026-06-04  
**Status:** MVP Definition

---

## Executive Summary

The Loyalty Platform aggregates points from multiple external applications into a single ledger, enabling users to exchange points on-platform and redeem them at member locations. This document defines the functional and non-functional requirements, MVP scope, and explicit out-of-scope items.

---

## Functional Requirements

### Core Use Cases

#### 1. Point Ingestion & Aggregation
- **F1.1** Platform accepts point events from external applications via API
- **F1.2** Points are attributed to a member account by `member_id`
- **F1.3** Point ledger maintains chronological record of all deposits (source, amount, timestamp)
- **F1.4** Point balance is calculated as sum of all ledger entries

#### 2. Member Account Management
- **F2.1** Members create or link existing accounts on the platform
- **F2.2** Member profile displays:
  - Current point balance
  - Lifetime points earned
  - Transaction history (last 30 days visible in MVP)
- **F2.3** Members can link external application accounts to their loyalty account

#### 3. Point Exchange (On-Platform)
- **F3.1** Members initiate point exchange (e.g., points from App A → points from App B)
- **F3.2** Exchange is recorded as paired debit/credit transactions in ledger
- **F3.3** Exchange rules are configurable:
  - Conversion rates (e.g., 100 App A points = 50 App B points)
  - Minimum exchange amount
  - Daily/monthly exchange limits per member
- **F3.4** Exchange confirmation is sent to member (email/in-app notification)

#### 4. Point Redemption at Member Locations
- **F4.1** Members browse list of redeemable locations (stores/restaurants)
- **F4.2** Each location displays:
  - Available redemption offers
  - Point cost per offer
  - Redemption mechanics (in-store code, app barcode, etc.)
- **F4.3** Members redeem points at location (staff scans QR code or member enters code)
- **F4.4** Redemption is recorded as ledger debit + audit trail (location, timestamp, code)
- **F4.5** Redemption rules:
  - Minimum point balance required
  - One-time vs. recurring offer redemption limits
  - Expiration policies for offers or redeemed codes

#### 5. Admin Capabilities (MVP Minimal)
- **F5.1** Admin dashboard displays:
  - Total points in circulation
  - Top redemption offers
  - Member transaction volume
- **F5.2** Admin can view detailed ledger for a member (audit trail)
- **F5.3** Admin can manually adjust point balance (with audit reason)

---

## Non-Functional Requirements

### Performance
- **NFR1.1** Point balance query completes in < 200ms (p99)
- **NFR1.2** Ledger transaction write completes in < 500ms (p99)
- **NFR1.3** Dashboard queries return within 2s (p95)

### Scalability
- **NFR2.1** Support 100k+ members
- **NFR2.2** Support 1M+ ledger transactions per day
- **NFR2.3** API can handle 500 requests/sec (exchanges, redemptions, point ingestion)

### Security & Compliance
- **NFR3.1** All API endpoints require authentication (JWT bearer token)
- **NFR3.2** Members can only access their own account data
- **NFR3.3** Sensitive operations (e.g., manual point adjustments) require admin role
- **NFR3.4** Ledger is immutable (no modifications, only new entries for corrections)
- **NFR3.5** All sensitive data at rest is encrypted (DB credentials, JWT secrets)
- **NFR3.6** API traffic is encrypted (TLS 1.3+)
- **NFR3.7** Audit log captures: who, what, when, why for all ledger modifications

### Availability & Reliability
- **NFR4.1** SLA: 99.5% uptime during business hours
- **NFR4.2** Recovery time objective (RTO): 1 hour for unplanned outages
- **NFR4.3** Recovery point objective (RPO): 15 minutes (acceptable data loss on disaster)
- **NFR4.4** Ledger data is replicated (no single point of failure)
- **NFR4.5** Point ingestion from external apps uses retry logic (exponential backoff, 3 attempts)

### Observability
- **NFR5.1** Application logs include: timestamp, level (INFO/WARN/ERROR), request_id, user_id
- **NFR5.2** Metrics tracked: request latency, error rates, ledger transaction volume
- **NFR5.3** Distributed tracing enabled for multi-service flows
- **NFR5.4** Alerting on: error rate > 5%, latency p99 > 1s, failed point ingestion

### Data Integrity
- **NFR6.1** All ledger entries are immutable
- **NFR6.2** Point balance consistency: no race conditions during concurrent updates
- **NFR6.3** Exchange and redemption transactions are atomic (all-or-nothing)

---

## Assumptions

1. **External App Integration:** External applications will push point events to the platform via REST API (not polling). Authentication is via API key in Authorization header.
2. **Member Identification:** Member IDs are globally unique strings (e.g., UUIDs or platform-specific IDs provided by external apps).
3. **Single Currency:** All points are fungible across the platform (no separate "App A points" currency—points are exchanged, not aggregated separately).
4. **Transactional Database:** PostgreSQL is available for ledger storage (ACID guarantees required).
5. **Caching Layer:** Redis is used for session/rate-limit caching (optional for MVP but expected in infra).
6. **Admin Users:** Platform has pre-seeded admin accounts; no self-service admin registration in MVP.
7. **Redemption Locations:** Locations are pre-configured by admins; members browse but don't add locations.
8. **Real-Time Sync:** Point balance updates within 5 seconds of a transaction is sufficient for MVP (not sub-second).
9. **No Batch Processing MVP:** Point ingestion is synchronous; batch ingestion (e.g., daily CSV uploads) is out-of-scope.
10. **Regional:** Initial deployment is single-region (US); geo-redundancy is future scope.

---

## MVP Scope

### In Scope
- ✅ Member registration and authentication (email + password)
- ✅ Point balance query and transaction history (read-only view)
- ✅ Manual point ingestion from external apps (via REST API)
- ✅ Point exchange between members (1-to-1 or predefined exchange rates)
- ✅ Basic redemption at locations (code-based: member enters code, location staff marks redeemed)
- ✅ Admin dashboard (summary stats + member search)
- ✅ Ledger audit trail (all transactions logged)
- ✅ Basic JWT authentication
- ✅ PostgreSQL backend + Redis cache (optional for session store)
- ✅ Docker-based local development (docker-compose)

### Out of Scope (Future)
- ❌ Fraud detection / anomaly alerting (v2)
- ❌ Multi-currency support or currency conversion (v2)
- ❌ Scheduled / recurring rewards programs (v2)
- ❌ Social features (points sharing, leaderboards) (v2)
- ❌ Third-party integration marketplace (v2)
- ❌ Mobile app (web-only MVP; mobile responsive, but not native)
- ❌ Batch point ingestion / webhook retry logic (v1.1)
- ❌ Advanced analytics dashboards (v2)
- ❌ Gamification (badges, tiers) (v2)
- ❌ Multi-region / geo-redundancy (v2)
- ❌ Automated refund logic for redemptions (manual admin intervention only in MVP)

---

## Success Criteria (MVP Exit)

1. ✅ Members can register, log in, view balance, and see transaction history
2. ✅ External apps can ingest points via API (health endpoint + test transaction flow)
3. ✅ Members can exchange points with valid exchange rules
4. ✅ Members can redeem points at locations (code generation + member-facing redemption UI)
5. ✅ Admin dashboard displays aggregate stats and member ledger
6. ✅ All ledger transactions are immutable and auditable
7. ✅ Frontend and backend run locally with `npm run dev` and `npm run dev:backend`
8. ✅ No critical security vulnerabilities (JWT properly enforced, no SQL injection, XSS protected)
9. ✅ Basic test coverage (routes, business logic)
10. ✅ Documentation covers API contracts, deployment steps, and incident runbook

---

## Architecture Touchpoints (Scaffold Readiness)

| Component | Current State | MVP Requirement | Notes |
|-----------|---------------|------------------|-------|
| Frontend (React) | ✅ Scaffolded | Auth UI, account page, exchange/redemption UIs | Needs implementation |
| Backend (FastAPI) | ✅ Scaffolded | DB models, auth middleware, point logic | Minimal routes; needs expansion |
| Database | ❌ Not set up | PostgreSQL + schema | .env placeholder only |
| Auth (JWT) | ❌ Not set up | JWT validation middleware | Defined in requirements |
| Caching (Redis) | ❌ Not set up | Optional session cache | .env placeholder only |
| Testing | ⚠️ Placeholder | Test suite with >70% coverage | npm scripts defined but empty |
| Docker | ❌ Not set up | docker-compose for local dev | Infra planning phase |
| CI/CD | ❌ Not set up | GitHub Actions for lint/test/build | Infra planning phase |

---

## Decision Checkpoints

**Resolved:**
- API versioning: `/api/v1/` prefix (frontend and backend aligned)
- Stack: React (frontend), FastAPI (backend), PostgreSQL (data)

**Pending:**
- Exchange rate management: hardcoded vs. database-driven? (recommend: database for flexibility)
- Redemption code format: numeric PIN vs. alphanumeric vs. QR? (recommend: alphanumeric for MVP simplicity)
- Ledger correction workflow: manual adjustment only vs. "reversal" transaction? (recommend: reversal for immutability)

---

## Next Steps (For Squad Handoff)

1. **Backend Lead** → Implement data models (Member, Ledger, ExchangeRule, Location)
2. **Backend Lead** → Build authentication layer (JWT validation, role checks)
3. **Frontend Lead** → Implement auth pages and account view
4. **Frontend + Backend** → Design and validate API contract for point ingestion
5. **DevOps Lead** → Provision PostgreSQL and Redis locally (docker-compose)
6. **QA Lead** → Define test plan for ledger consistency and concurrent transaction safety
