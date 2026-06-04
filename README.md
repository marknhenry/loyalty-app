# Loyalty Platform

Top-level monorepo scaffold for a loyalty platform with a React frontend and Python backend.

## Project Structure

```text
loyalty-app/
├─ frontend/   # React application (implemented separately)
├─ backend/    # Python API/services (implemented separately)
├─ infra/      # Infrastructure, deployment, and environment config
├─ docs/       # Product and technical documentation
└─ .squad/     # Team coordination artifacts
```

## Architecture Overview

- **Frontend (`frontend/`)**: React UI for customer/member experiences.
- **Backend (`backend/`)**: Python services for loyalty accounts, point ingestion, exchange, and redemption workflows.
- **Infra (`infra/`)**: Environment provisioning, deployment assets, and operations configs.
- **Docs (`docs/`)**: Architecture notes, API contracts, and runbooks.

## Local Development (Planned Workflow)

Frontend and backend internals are scaffolded by dedicated streams.

Expected workflow once those are in place:

1. Start backend service from `backend/`.
2. Start frontend app from `frontend/`.
3. Use shared configuration and environment references from `infra/`.
4. Keep design decisions and onboarding materials in `docs/`.

## Ownership

- **Requested by:** Mark Henry
- **Lead:** Bond
