# Deployment / Runtime View

Shows the physical runtime topology for local development and the target cloud deployment.

## Local Development Topology

```mermaid
graph LR
    subgraph "Developer Machine"
        SPA["React SPA<br/>localhost:3000<br/>(Vite dev server)"]
        API["FastAPI<br/>localhost:4000<br/>(uvicorn --reload)"]
        PG["PostgreSQL<br/>localhost:5432"]
        REDIS["Redis<br/>localhost:6379"]
    end

    SPA -->|REST JSON| API
    API -->|SQL| PG
    API -->|Cache / Queue| REDIS
```

## Target Cloud Deployment

```mermaid
graph TB
    subgraph "CDN / Edge"
        CDN["Static CDN<br/>(React SPA bundle)"]
    end

    subgraph "Compute Tier"
        LB["Load Balancer / API Gateway"]
        API1["API Instance 1<br/>FastAPI"]
        API2["API Instance 2<br/>FastAPI"]
        WORKER1["Worker 1<br/>Celery"]
        WORKER2["Worker 2<br/>Celery"]
    end

    subgraph "Data Tier"
        PG_PRIMARY["PostgreSQL Primary"]
        PG_REPLICA["PostgreSQL Read Replica"]
        REDIS_CLUSTER["Redis Cluster<br/>(cache + queue)"]
    end

    subgraph "External"
        IDP["Identity Provider"]
        PARTNERS["Partner Apps"]
        NOTIF["Notification Service"]
    end

    CDN -->|API calls| LB
    LB --> API1
    LB --> API2
    API1 --> PG_PRIMARY
    API2 --> PG_PRIMARY
    API1 --> PG_REPLICA
    API2 --> PG_REPLICA
    API1 --> REDIS_CLUSTER
    API2 --> REDIS_CLUSTER
    WORKER1 --> REDIS_CLUSTER
    WORKER2 --> REDIS_CLUSTER
    WORKER1 --> PG_PRIMARY
    WORKER2 --> PG_PRIMARY
    WORKER1 --> NOTIF
    PARTNERS -->|Webhooks| LB
    API1 --> IDP
    API2 --> IDP
```

## Environment Matrix

| Environment | Frontend | Backend | Database | Redis | Notes |
|-------------|----------|---------|----------|-------|-------|
| Local | Vite dev server :3000 | uvicorn :4000 | Docker postgres :5432 | Docker redis :6379 | Single-process, hot-reload |
| Staging | CDN (preview URL) | 1 API + 1 Worker | Managed PG (small) | Managed Redis (single) | Mirrors prod topology |
| Production | CDN (custom domain) | 2+ API + 2+ Workers | Managed PG (HA) | Redis Cluster | Auto-scaling, read replicas |

## Infrastructure Decisions

| Decision | Rationale |
|----------|-----------|
| SPA served from CDN, not from API | Independent deploy cadence; zero backend load for static assets |
| API Gateway in front of API instances | Centralized rate-limiting, auth pre-check, TLS termination |
| Read replica for query-heavy paths | Isolate analytics/reporting queries from write path |
| Workers scale independently | Ingestion spikes don't require scaling user-facing API |
