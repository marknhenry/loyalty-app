# Container / Component Architecture

Shows the major runtime containers and their responsibilities within the loyalty platform boundary.

```mermaid
C4Container
    title Container Diagram — Loyalty Platform

    Person(member, "Member")
    Person(admin, "Admin")

    System_Boundary(platform, "Loyalty Platform") {
        Container(spa, "Frontend SPA", "React + TypeScript + Vite", "Member & admin UI for balances, redemptions, program config")
        Container(api, "Backend API", "Python / FastAPI", "REST API — accounts, points, exchange, redemption logic")
        Container(worker, "Event Worker", "Python / Celery (planned)", "Async processing of ingestion events and notifications")
        ContainerDb(pg, "PostgreSQL", "Relational DB", "Loyalty ledger, accounts, program rules")
        ContainerDb(redis, "Redis", "Cache / Queue", "Session cache, task queue, rate-limit counters")
    }

    System_Ext(partners, "Partner Apps", "External point-earning sources")
    System_Ext(idp, "Identity Provider", "OIDC auth")
    System_Ext(notif, "Notification Service", "Email/push delivery")

    Rel(member, spa, "Uses", "HTTPS")
    Rel(admin, spa, "Uses", "HTTPS")
    Rel(spa, api, "Calls", "REST / JSON")
    Rel(api, pg, "Reads/Writes", "SQL")
    Rel(api, redis, "Caches / Enqueues", "Redis protocol")
    Rel(worker, redis, "Consumes tasks", "Redis protocol")
    Rel(worker, pg, "Writes ledger entries", "SQL")
    Rel(partners, api, "Push events", "Webhook POST")
    Rel(api, idp, "Validates JWT", "OIDC")
    Rel(worker, notif, "Triggers notifications", "REST")
```

## Component Breakdown (Backend API)

```mermaid
graph TD
    subgraph "FastAPI Backend /api/v1"
        HEALTH["/health — readiness probe"]
        ACCOUNTS["/loyalty/accounts — member balances"]
        INGEST["/loyalty/ingest — partner event intake"]
        EXCHANGE["/loyalty/exchange — cross-program point conversion"]
        REDEEM["/loyalty/redeem — reward redemption"]
    end

    ACCOUNTS --> LEDGER["Ledger Service"]
    INGEST --> INGESTION["Ingestion Service"]
    EXCHANGE --> EXCHANGE_SVC["Exchange Engine"]
    REDEEM --> REDEEM_SVC["Redemption Service"]

    LEDGER --> PG[(PostgreSQL)]
    INGESTION --> QUEUE[(Redis Queue)]
    EXCHANGE_SVC --> PG
    REDEEM_SVC --> PG
    REDEEM_SVC --> NOTIF[Notification Service]
```

## Design Rationale

| Decision | Rationale |
|----------|-----------|
| Single FastAPI process for all REST routes | Simplicity at current scale; split later by domain if load requires |
| Celery worker for async ingestion | Partner event spikes shouldn't block user-facing latency |
| Redis as both cache and broker | Reduces infra surface; revisit if queue depth exceeds Redis capacity |
| PostgreSQL for ledger | ACID guarantees are non-negotiable for financial-grade point balances |
