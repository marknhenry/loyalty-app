# User Stories — Loyalty App

**Generated:** 2026-06-04  
**Status:** Extracted and organized from backlog issues #1–#14  
**Format:** Standard (As a… I want… So that…) with acceptance criteria  

---

## User Story Classification

This document organizes 14 backlog items into **3 categories**:

1. **User-Facing Stories** — Direct value to members or staff
2. **Technical Enablers** — Required infrastructure (no direct user value, but enables user stories)
3. **Pending Decisions** — Blocked pending product owner approval

---

## Domain 1: Authentication & Access

### Story A.1: Member Login & Session Management
**Epic:** Member Authentication  
**As a** member  
**I want** to log in securely with email and password  
**So that** only I can access my personal account and transaction history  

**Acceptance Criteria:**
- ✅ Login form accepts email and password
- ✅ Valid credentials return a JWT token (15-min access + 7-day refresh)
- ✅ Invalid credentials return clear error ("Email or password incorrect")
- ✅ Token stored securely (httpOnly cookie or localStorage with CSRF protection)
- ✅ Token automatically refreshed on page reload if valid refresh token exists
- ✅ Logout clears token and session
- ✅ Unauthenticated users cannot access /account or /exchange pages

**Enables:** F1 (Member Account View), F2 (Point Exchange), F3 (Redemption)

**Priority:** CRITICAL (MVP Blocker)  
**Assignee:** Donatello (Backend) + Picasso (Frontend)  
**Related Issues:** #1

---

### Story A.2: Admin Access & Role-Based Permissions
**Epic:** Member Authentication  
**As an** admin or loyalty manager  
**I want** role-based access to redemption location management and point adjustments  
**So that** only authorized staff can manage system operations  

**Acceptance Criteria:**
- ✅ Admin users identified by JWT claim (role="admin")
- ✅ Admin endpoints (point adjustments, location CRUD) reject non-admin requests with 403 Forbidden
- ✅ Admin pages show only to users with admin role
- ✅ Audit trail logs all admin actions (who, what, when)

**Enables:** F4 (Redemption Location Management), Admin Operations

**Priority:** HIGH (MVP Phase 1)  
**Assignee:** Donatello (Backend)  
**Related Issues:** #1

---

## Domain 2: Loyalty Points & Ledger

### Story L.1: View Member Account & Point Balance
**Epic:** Member Account Management  
**As a** member  
**I want** to see my current point balance and transaction history  
**So that** I know how many points I have and how I earned/spent them  

**Acceptance Criteria:**
- ✅ Member account page displays current balance (SUM of all non-reversed transactions)
- ✅ Transaction history shows date, type (ingestion/exchange/redemption), amount, source
- ✅ Balance updates in real-time when new transactions occur
- ✅ Member can filter history by date range or transaction type
- ✅ UI clearly distinguishes earned points vs. redeemed points

**Enables:** F1.1 (View Account)

**Priority:** HIGH (MVP Blocker)  
**Assignee:** Picasso (Frontend) + Donatello (Backend)  
**Related Issues:** #2, #3, #13

---

### Story L.2: Ingest Points from Partner Apps
**Epic:** Partner Integration  
**As a** partner app (external system)  
**I want** to send member points via API endpoint  
**So that** members earn points through partner transactions  

**Acceptance Criteria:**
- ✅ POST /api/v1/loyalty/ingest endpoint accepts member_id, amount, source, metadata
- ✅ Request authenticated via API key (external app authentication)
- ✅ Response includes transaction_id, new_balance, timestamp
- ✅ Idempotent: duplicate requests with same Idempotency-Key do not create duplicate transactions
- ✅ Invalid requests (negative points, malformed member_id) rejected with 400 Bad Request
- ✅ API rate-limited to 100 requests/min per external app
- ✅ Failed requests logged with full context for debugging

**Enables:** F1.1 (Point Ingestion)

**Priority:** CRITICAL (MVP Blocker)  
**Assignee:** Donatello (Backend)  
**Related Issues:** #2, #11 (pending decision)

---

### Story L.3: Exchange Points Between Members (with Configurable Rates)
**Epic:** Point Exchange  
**As a** member  
**I want** to exchange my points for points of another member at an agreed rate  
**So that** I can transfer my points to earn rewards  

**Acceptance Criteria:**
- ✅ Member specifies: recipient, amount to give, exchange rate
- ✅ Exchange validates: sender has enough points, rate is within system limits
- ✅ Exchange creates two offsetting ledger entries (debit sender, credit recipient)
- ✅ Transaction is atomic: both entries succeed together or both fail
- ✅ No race conditions: concurrent exchanges by different members don't cause double-spend
- ✅ Exchange rate is database-driven (ops can adjust without code changes)
- ✅ Exchange history visible in both members' transaction history

**Enables:** F2 (Point Exchange)

**Priority:** HIGH (MVP Phase 1)  
**Assignee:** Donatello (Backend)  
**Related Issues:** #2, #9, #12 (pending decision)

---

### Story L.4: Redeem Points for Offers at Physical Locations
**Epic:** Redemption  
**As a** member  
**I want** to redeem points for an offer at a participating location  
**So that** I can receive rewards in exchange for my points  

**Acceptance Criteria:**
- ✅ Member selects a location and offer (e.g., "Coffee shop: Free drink for 50 points")
- ✅ System validates member has sufficient points
- ✅ System generates 8-digit alphanumeric redemption code
- ✅ Redemption code is valid for 15 minutes
- ✅ Code can be entered at physical location to complete redemption
- ✅ Redemption deducts points and creates ledger entry marked "redeemed"
- ✅ Redemption code cannot be reused

**Enables:** F3 (Point Redemption)

**Priority:** HIGH (MVP Phase 1)  
**Assignee:** Donatello (Backend) + Picasso (Frontend)  
**Related Issues:** #2, #3, #12 (pending decision)

---

### Story L.5: Correct Ledger Entries (Manual Adjustment with Immutable Trail)
**Epic:** Ledger Integrity  
**As an** admin  
**I want** to correct member balances due to system errors or disputes  
**So that** account balances are always accurate  

**Acceptance Criteria:**
- ✅ Admin can create a "correction" transaction linked to original transaction
- ✅ Correction transaction shows in audit trail (e.g., "Reversal of txn_id: 12345")
- ✅ Ledger remains append-only: no UPDATE or DELETE, only new entries
- ✅ Member sees correction in transaction history with reason
- ✅ Balance recalculated correctly after correction
- ✅ All corrections logged with admin user, timestamp, and justification

**Enables:** L4.2 (Error Recovery), Compliance

**Priority:** MEDIUM (MVP Phase 2)  
**Assignee:** Donatello (Backend)  
**Related Issues:** #2, #9, #12 (pending decision)

---

## Domain 3: Redemption Location Management

### Story R.1: Manage Redemption Locations & Offers
**Epic:** Redemption  
**As an** admin  
**I want** to add, update, and remove redemption locations and their offers  
**So that** members have access to current partners and available rewards  

**Acceptance Criteria:**
- ✅ Admin can CRUD locations (name, address, hours, contact)
- ✅ Admin can CRUD offers per location (description, point cost, quantity available, expiry)
- ✅ Location list visible to members (searchable, filterable by offer type)
- ✅ Offers marked unavailable when quantity exhausted
- ✅ Expired offers automatically hidden from member view
- ✅ Location changes audited (who changed what, when)

**Enables:** F3 (Redemption), Partner Onboarding

**Priority:** HIGH (MVP Phase 1)  
**Assignee:** Donatello (Backend) + Picasso (Frontend)  
**Related Issues:** #2, #3

---

## Domain 4: System Resilience & Operations

### Story O.1: System Monitoring & Error Logging
**Epic:** Operational Excellence  
**As an** ops engineer  
**I want** to receive structured logs and error alerts  
**So that** I can quickly diagnose and resolve production issues  

**Acceptance Criteria:**
- ✅ All backend errors logged as JSON with: timestamp, level, request_id, user_id, operation, stack trace
- ✅ Frontend errors caught by error boundary and logged to monitoring service
- ✅ Logs include request correlation IDs for end-to-end tracing
- ✅ Critical errors (ledger inconsistency, auth failures) trigger alerts
- ✅ Logs exportable to ELK/CloudWatch for analysis
- ✅ Error messages to users are clear and actionable (no stack traces)

**Enables:** Production Support, Compliance Audits

**Priority:** MEDIUM (MVP Phase 1)  
**Assignee:** Donatello (Backend) + Picasso (Frontend)  
**Related Issues:** #14

---

### Story O.2: API Rate Limiting & Abuse Prevention
**Epic:** Operational Excellence  
**As a** system operator  
**I want** API endpoints rate-limited and throttled  
**So that** malicious or accidental abuse doesn't overwhelm the system  

**Acceptance Criteria:**
- ✅ External app ingestion API rate-limited to 100 requests/min per API key
- ✅ Member redemption requests limited to 10/hour per member
- ✅ Frontend input debounced (exchange amount field updates every 500ms, not on each keystroke)
- ✅ Rate limit exceeded returns 429 Too Many Requests with Retry-After header
- ✅ Rate limits enforced in Redis or database for consistency across nodes

**Enables:** System Stability, Security

**Priority:** MEDIUM (MVP Phase 1)  
**Assignee:** Donatello (Backend) + Picasso (Frontend)  
**Related Issues:** #10

---

## Technical Enablers (Non-User-Facing, Required for Stories)

These are infrastructure and framework stories — no direct user value, but required to deliver user stories.

| Tech Story | Purpose | Relates To | Status |
|--|--|--|--|
| **TE.1: Database Models & PostgreSQL** | Store members, ledger, locations, redemption codes | All L.* stories | CRITICAL |
| **TE.2: Frontend API Integration** | Connect React UI to backend | All A.*, L.*, R.* stories | CRITICAL |
| **TE.3: Data Validation & Error Handling** | Validate all inputs, return consistent errors | All stories | HIGH |
| **TE.4: React State Management** | Store auth state, member data | A.1, L.1, R.1 | HIGH |
| **TE.5: Backend Testing (pytest)** | Ensure ledger logic is correct | All L.* stories | HIGH |
| **TE.6: Frontend Testing (Vitest)** | Ensure UI works correctly | All A.*, L.*, R.* stories | HIGH |
| **TE.7: docker-compose Setup** | Local dev environment | All stories | HIGH |
| **TE.8: CI/CD Pipeline (GitHub Actions)** | Automated quality gates | All stories | HIGH |

---

## Pending Decisions (Blocking Implementation)

### PD.1: Point Ingestion API Contract Approval
**Issue:** #11  
**Question:** Do we approve the proposed request/response schema and authentication strategy?
- Request: `{ "member_id", "amount", "source", "metadata" }`
- Response: `{ "transaction_id", "balance_after", "timestamp" }`
- Authentication: API key header for external apps
- Idempotency: Idempotency-Key header

**Impact:** Blocks Story L.2 (Partner Ingestion)  
**Owner:** Mark Henry (Product Owner)  
**Decision Needed By:** Before Donatello starts backend API implementation

---

### PD.2: Ledger Correction Workflow Decision
**Issue:** #12  
**Question:** Approve ledger correction approach?
- Option: Only reversal transactions (create new debit entry to offset original)
- Recommendation: Reversal for immutability + audit trail

**Impact:** Affects Story L.5 (Correct Ledger) and system auditing approach  
**Owner:** Mark Henry (Product Owner)  
**Decision Needed By:** Before Donatello implements correction logic

---

### PD.3: Exchange Rate Configuration
**Issue:** #12  
**Question:** Should exchange rates be database-driven or hardcoded?
- Option: Database-driven (ops can change without code changes)
- Recommendation: Database-driven for flexibility

**Impact:** Affects Story L.3 (Point Exchange), scalability, and ops workflows  
**Owner:** Mark Henry (Product Owner)  
**Decision Needed By:** Before backend schema design

---

### PD.4: Redemption Code Format
**Issue:** #12  
**Question:** What format for redemption codes?
- Options: Numeric PIN (4–6 digits), alphanumeric (8 chars), QR code
- Recommendation: 8-digit alphanumeric (easy in-store entry, non-guessable)

**Impact:** Affects Story L.4 (Redemption), POS integration, and UX  
**Owner:** Mark Henry (Product Owner)  
**Decision Needed By:** Before Picasso designs redemption flow

---

## Backlog Organization by Feature

### Phase 1 (MVP Critical Path)

| Priority | Story | Dependency | Assignee |
|--|--|--|--|
| 🔴 CRITICAL | A.1: Member Login | TE.1, TE.2 | Donatello + Picasso |
| 🔴 CRITICAL | L.2: Ingest Points | TE.1, PD.1 (decision needed) | Donatello |
| 🟠 HIGH | L.1: View Account & Balance | TE.1, TE.2, TE.4, TE.5 | Picasso + Donatello |
| 🟠 HIGH | L.3: Exchange Points | TE.1, L.1, PD.3 (decision needed) | Donatello |
| 🟠 HIGH | L.4: Redeem Points | TE.1, TE.2, PD.4 (decision needed) | Donatello + Picasso |
| 🟠 HIGH | R.1: Manage Locations | TE.1, TE.2 | Donatello + Picasso |
| 🟠 HIGH | A.2: Admin Access | TE.1, A.1 | Donatello |
| 🟡 MEDIUM | O.1: Monitoring & Logging | TE.3 | Donatello + Picasso |
| 🟡 MEDIUM | O.2: Rate Limiting | TE.1, TE.3 | Donatello + Picasso |

**Technical Enablers (must start immediately):**
- TE.1: Database Models & PostgreSQL
- TE.2: Frontend API Integration
- TE.3: Data Validation
- TE.4: React State Management
- TE.7: docker-compose Setup

### Phase 2 (Post-MVP)

| Priority | Story | Dependency |
|--|--|--|
| 🟢 MEDIUM | L.5: Correct Ledger | TE.1, TE.5, PD.2 (decision needed) |
| 🟡 MEDIUM | TE.5: Backend Testing | TE.1 |
| 🟡 MEDIUM | TE.6: Frontend Testing | TE.4, TE.2 |
| 🟡 MEDIUM | TE.8: CI/CD Pipeline | TE.5, TE.6 |

---

## Acceptance Criteria Summary by Feature

### F1: Member Account View
- ✅ Secure login (Story A.1)
- ✅ View balance and transaction history (Story L.1)

### F2: Point Exchange
- ✅ Database exchange rate configuration (Story L.3, requires PD.3 decision)
- ✅ Atomic ledger updates (Story L.3, requires TE.1)
- ✅ Concurrent safety (Story L.3, requires TE.5 testing)

### F3: Redemption
- ✅ Generate time-limited redemption codes (Story L.4, requires PD.4 decision)
- ✅ Manage locations and offers (Story R.1)
- ✅ Deduct points atomically (Story L.4, requires TE.1)

### F4: Admin Operations
- ✅ Role-based access (Story A.2)
- ✅ Correct ledger with immutable trail (Story L.5, requires PD.2 decision)
- ✅ Manage redemption locations (Story R.1)

---

## Organization Format & Notes

This document uses **standard user story format**: "As a [role], I want [capability], so that [business value]."

**Grouping Strategy:**
- Stories organized by **domain** (Authentication, Ledger, Locations, Operations)
- Technical enablers separated from user-facing stories for clarity
- Pending decisions highlighted to unblock implementation

**Prioritization:**
- 🔴 CRITICAL: MVP blockers; must complete before release
- 🟠 HIGH: Essential features; required for feature completeness
- 🟡 MEDIUM: Quality/ops; can defer to Phase 2 if needed
- 🟢 FUTURE: Post-MVP enhancements

**Next Steps for Mark Henry:**
1. ✅ Review and approve all user stories above (confirm wording and acceptance criteria match intent)
2. ✅ Make decisions on PD.1–PD.4 (pending items) to unblock backend work
3. ✅ Confirm Phase 1 vs. Phase 2 prioritization
4. ✅ Assign any stories not yet assigned to squad members

---

**Generated By:** Bond (Lead)  
**Last Updated:** 2026-06-04  
**Status:** Ready for Product Owner Review
