# Architecture Documentation

This folder contains the architectural views for the Loyalty Platform, maintained as Mermaid-in-Markdown diagrams.

## Diagram Index

| # | Diagram | File | Description |
|---|---------|------|-------------|
| 1 | [System Context](./system-context.md) | `system-context.md` | C4 Level 1 — platform in relation to users and external systems |
| 2 | [Container / Component Architecture](./container-architecture.md) | `container-architecture.md` | C4 Level 2 — internal containers, plus component breakdown of the API |
| 3 | [Points Flow Sequence](./sequence-points-flow.md) | `sequence-points-flow.md` | Core domain sequence: ingestion → exchange → redemption |
| 4 | [Deployment / Runtime View](./deployment-view.md) | `deployment-view.md` | Local dev topology + target cloud deployment + environment matrix |

## How to View

- **GitHub** — Mermaid diagrams render natively in `.md` files on GitHub.
- **VS Code** — Install the "Markdown Preview Mermaid Support" extension.
- **CLI** — Use `mmdc` (Mermaid CLI) to export SVG/PNG if needed.

## Architecture Principles

1. **Event-driven ingestion** — Partner apps push; we never poll.
2. **Double-entry ledger** — Every point movement is a debit+credit pair for auditability.
3. **Separation of read/write paths** — Async workers handle ingestion; API serves user queries.
4. **Stateless compute** — API and workers hold no local state; all state lives in PostgreSQL + Redis.
5. **Independent deployability** — Frontend, API, and workers deploy on separate cadences.

## Conventions

- Diagrams use [C4 model](https://c4model.com/) terminology where applicable.
- Sequence diagrams focus on the happy path; error/alt paths shown as `alt` blocks.
- Keep diagrams up to date when domain boundaries or integrations change.
