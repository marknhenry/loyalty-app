# Project Context

- **Owner:** Mark Henry
- **Project:** loyalty-app
- **Stack:** TBD
- **Created:** 2026-06-04

## Learnings

- Frontend mission: make point collection, exchange, and redemption clear across many partner sources and locations.
- CSS Modules used for all component/page styles — scoped, colocated, no Tailwind dependency.
- Mock data lives in `frontend/src/data/mockData.ts`; all types in `frontend/src/types/index.ts`.
- `AccountContext` holds the live account state and exposes `exchangePoints` + `generateRedemption` mutators — components never directly mutate state.
- Exchange and redemption flows use a multi-step local state machine (`select → preview/confirm → success/code`) — no router changes between steps, cleaner UX.
- QR code is a deterministic SVG built from the redemption code string — no external library needed, visually convincing mockup.
- Redemption codes: 8-char alphanumeric from charset excluding ambiguous chars (0/O, 1/I).
- Partner `exchangeRate` is stored on each partner object so previews are self-contained in the frontend without API calls.
- `react-router-dom` added as a production dependency; `@types/react-router-dom` is a devDependency.

## Work Log

### 2026-06-04 — React + TypeScript + Vite Scaffold
- Initialized Vite + React + TypeScript project in `frontend/` directory
- Built app shell with React Router foundation ready for loyalty flows
- Configured TypeScript for strict type safety
- Enabled ESLint and Prettier for code quality and linting
- Prepared component scaffolds for point collection, exchange, and redemption UIs
- Documented frontend architecture and component guidelines in `frontend/README.md`
- Decision made: **React + TypeScript + Vite Frontend Scaffold** — modern, minimal setup with fast iteration
- **Status:** ✅ Complete

### 2026-06-04 — Design Review Handoff Notification
- **From:** Bond + Leonardo (Design Review)
- **What:** Design review decisions now registered in `.squad/decisions.md` with approval matrix
- **Actionable Items for Picasso:**
  - State management decision: React Context API for MVP (auth + account context)
  - API client requirements: Error response handling for consistent error schema
  - Authentication flow: Login/logout via JWT + refresh token (httpOnly cookie)
  - Component approach: useAuth() + useAccount() hooks for token/state access
  - See full requirements at `.squad/decisions/inbox/bond-design-review.md`
- **Next Steps:** Await Phase 1 kickoff after design review ceremony approvals
- **Status:** ✅ Notified; ready for Phase 1 auth context + component work

### 2026-06-04T21:22:55.147+04:00 — Working UI Mockup (Phase 1 Deliverable)
- Built full working UI mockup across three core flows: Dashboard, Exchange, Redemption
- **Dashboard:** hero balance cards (platform + partner totals), partner balance grid with exchange rates, recent activity feed
- **Exchange:** two-step flow (partner selection + amount → preview with rate calculation → success confirmation); live context mutation updates nav balance in real time
- **Redemption:** two-step flow (location selection with affordability check → confirm deduction preview → generated QR code + 8-digit code display with 30-min expiry)
- **Navigation:** fixed dark sidebar with NavLink active states, live balance counter at bottom
- **Components created:** `Nav`, `TransactionList`, `QRCode` (SVG-based, no external lib)
- **Pages created:** `DashboardPage`, `ExchangePage`, `RedemptionPage`
- **Context:** `AccountContext` with `exchangePoints` + `generateRedemption` mutators
- **QR code:** deterministic SVG pattern seeded from code string; includes finder patterns and timing rows for visual authenticity
- **Build:** zero TypeScript errors; `npm run build` passes clean; `npm run dev` from `frontend/` is ready
- **Status:** ✅ Complete — runnable locally via `npm run dev` in `frontend/`
