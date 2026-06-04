# Frontend Deployment Guide

## Overview

The frontend (React + TypeScript + Vite) is deployed to **GitHub Pages** via a manual GitHub Actions workflow.
Deployment is **on-demand** — Mark Henry triggers it from the GitHub Actions UI whenever a new version is ready.

---

## Triggering a Deployment

1. Go to the repository on GitHub: **[marknhenry/loyalty-app](https://github.com/marknhenry/loyalty-app)**
2. Click the **Actions** tab.
3. In the left sidebar, select **"Deploy Frontend to GitHub Pages"**.
4. Click the **"Run workflow"** button (top-right of the workflow list).
5. Leave the environment field as `production` (or enter a label for your own reference).
6. Click **"Run workflow"** to confirm.

The workflow will appear in the list within a few seconds. Click it to watch live logs.

---

## What the Workflow Does

| Step | Description |
|------|-------------|
| **Checkout** | Clones the repository at the triggered commit |
| **Setup Node 20** | Installs Node.js with npm cache keyed to `frontend/package-lock.json` |
| **Install deps** | Runs `npm ci` inside `frontend/` for a clean, reproducible install |
| **Build** | Runs `npm run build` (`tsc -b && vite build`) — output lands in `frontend/dist/` |
| **Upload artifact** | Packages `frontend/dist/` as a GitHub Pages artifact |
| **Deploy** | Publishes the artifact to GitHub Pages via the official `actions/deploy-pages@v4` action |

The Vite config already sets `base: '/loyalty-app/'` so all asset paths resolve correctly under the Pages sub-path.

---

## Expected Output

- **Deployed URL:** `https://marknhenry.github.io/loyalty-app/`
- **Typical duration:** 2–4 minutes end-to-end
- **Post-deploy:** The live URL appears in the workflow summary and in **Settings → Pages** on the repository.

---

## One-Time Repository Setup (first deployment only)

GitHub Pages must be configured to accept deployments from GitHub Actions:

1. Go to **Settings → Pages** in the repository.
2. Under **Source**, select **"GitHub Actions"** (not a branch).
3. Save. The workflow will handle all future deployments automatically.

---

## Concurrency Policy

Only one deployment runs at a time. If a second run is triggered while one is already in progress, the in-progress run is cancelled and the new one takes over — ensuring the latest code is always what lands in production.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `pages` permission denied | Pages not configured to use Actions | Set Source to **GitHub Actions** in Settings → Pages |
| 404 on deployed site | Wrong `base` path in `vite.config.ts` | Ensure `base: '/loyalty-app/'` is set |
| Build fails on `tsc` errors | TypeScript type errors in source | Fix errors locally (`npm run build` in `frontend/`) before re-triggering |
| Old content served | Browser/CDN cache | Hard-refresh (`Ctrl+Shift+R`) or wait a few minutes |
