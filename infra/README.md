# Infrastructure Notes

This folder contains platform-level guidance for running the loyalty app stack locally and a placeholder for future deployment assets.

## Local development flow

From the repository root:

1. Install root helper dependencies:
   - `npm install`
2. Install frontend + backend dependencies:
   - `npm run setup`
3. Start both apps in one terminal:
   - `npm run dev`

You can also run each service separately:

- Frontend only: `npm run dev:frontend`
- Backend only: `npm run dev:backend`

## Environment setup

1. Copy `.env.example` to `.env` (or service-specific env files if each app expects its own).
2. Update DB/auth/integration placeholders with your local values.
3. Keep frontend and backend ports aligned with `FRONTEND_PORT`, `BACKEND_PORT`, and `API_BASE_URL`.

## Validation helpers

- `npm run lint` — frontend lint + backend placeholder
- `npm run test` — frontend tests + backend placeholder
- `npm run build` — frontend build + backend placeholder

> Backend lint/test/build commands are intentionally placeholders until dedicated tooling is introduced in `backend/`.

## Future deployment placeholders

Planned additions (as delivery progresses):

- IaC definitions (Terraform/Bicep) for cloud resources
- CI/CD deployment workflow templates
- Environment matrix (dev/stage/prod) and secrets contract
- Operational runbooks (rollout, rollback, incident checks)
