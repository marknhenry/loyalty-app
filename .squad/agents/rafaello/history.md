# Project Context

- **Owner:** Mark Henry
- **Project:** loyalty-app
- **Stack:** TBD
- **Created:** 2026-06-04

## Learnings

- Platform reliability is critical because loyalty balances and redemption flows must be consistent across member locations.

## Work Log

### 2026-06-04 — Root Workflow & Platform Orchestration
- Created root `package.json` as unified task runner for full-stack development
- Implemented npm wrappers for frontend and Python wrappers for backend services
- Set up `concurrently`-based dual-service startup (`npm run dev`)
- Prepared `.env.example` template with service configuration variables
- Documented platform operations, local dev workflow, and deployment patterns in `infra/README.md`
- Decision made: **Root Workflow Package & Platform Stack** — one-command orchestration from repository root
- **Note:** Backend placeholder validation steps to be replaced with real commands once toolchain is finalized
- **Status:** ✅ Complete

### 2026-06-04 — Design Review Handoff Notification
- **From:** Bond + Leonardo (Design Review)
- **What:** Design review decisions now registered in `.squad/decisions.md` with approval matrix
- **Actionable Items for Rafaello:**
  - docker-compose decision: Production-mirror architecture for local dev (PostgreSQL, Redis, backend, frontend with hot reload)
  - .env configuration decision: Secrets management via .env.local (not hardcoded)
  - Platform workflow: Root package.json wrappers finalized once backend/frontend commands are known
  - Infrastructure setup: Pre-commit hooks to prevent .env commits; env-file injection in docker-compose
  - See full requirements at `.squad/decisions/inbox/bond-design-review.md`
- **Next Steps:** Await Phase 1 kickoff after design review ceremony approvals; docker-compose is critical blocker
- **Status:** ✅ Notified; ready for Phase 1 infrastructure setup coordination

### 2026-06-04T21:54:26.273+04:00 — GitHub Pages Deployment Workflow
- **Trigger:** Created `.github/workflows/deploy-frontend-pages.yml` — manual dispatch only (`workflow_dispatch`)
- **Build:** Runs `npm ci` then `npm run build` (`tsc -b && vite build`) inside `frontend/`
- **Artifact:** Uploads `frontend/dist/` via `actions/upload-pages-artifact@v3`
- **Deploy:** Publishes to GitHub Pages via `actions/deploy-pages@v4` (official GitHub action)
- **Permissions:** Minimum-scoped (`contents: read`, `pages: write`, `id-token: write`)
- **Concurrency:** Single-slot group `pages-deploy`; new run cancels any in-progress run
- **Base path:** `vite.config.ts` already has `base: '/loyalty-app/'` — no config change needed
- **Target URL:** `https://marknhenry.github.io/loyalty-app/`
- **One-time setup required:** Repo Settings → Pages → Source must be set to **"GitHub Actions"**
- **Documentation:** `.github/DEPLOYMENT.md` covers trigger steps, expected output, and troubleshooting
- **Decision filed:** `.squad/decisions/inbox/rafaello-frontend-deployment.md`
- **Status:** ✅ Complete
