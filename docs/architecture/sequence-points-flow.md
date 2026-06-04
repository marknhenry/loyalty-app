# Core Sequence: Points Ingestion → Exchange → Redemption

End-to-end flow showing how points enter the system, get exchanged between programs, and are redeemed for rewards.

## 1. Points Ingestion

```mermaid
sequenceDiagram
    participant Partner as Partner App
    participant API as Backend API
    participant Queue as Redis Queue
    participant Worker as Event Worker
    participant DB as PostgreSQL

    Partner->>API: POST /api/v1/loyalty/ingest {event_type, member_id, points, source}
    API->>API: Validate webhook signature & payload
    API->>Queue: Enqueue ingestion task
    API-->>Partner: 202 Accepted

    Worker->>Queue: Dequeue task
    Worker->>DB: BEGIN transaction
    Worker->>DB: INSERT into points_ledger (credit)
    Worker->>DB: UPDATE account balance
    Worker->>DB: COMMIT
    Worker->>Worker: Emit "points.credited" domain event
```

## 2. Points Exchange (Cross-Program Conversion)

```mermaid
sequenceDiagram
    participant Member as Member (SPA)
    participant API as Backend API
    participant DB as PostgreSQL

    Member->>API: POST /api/v1/loyalty/exchange {from_program, to_program, amount}
    API->>API: Authenticate (JWT) & authorize
    API->>DB: SELECT balance WHERE program = from_program
    DB-->>API: current_balance

    alt Insufficient balance
        API-->>Member: 400 Insufficient points
    else Sufficient balance
        API->>DB: BEGIN transaction
        API->>DB: INSERT ledger entry (debit from_program)
        API->>DB: INSERT ledger entry (credit to_program, apply exchange rate)
        API->>DB: UPDATE account balances
        API->>DB: COMMIT
        API-->>Member: 200 {new_balances}
    end
```

## 3. Reward Redemption

```mermaid
sequenceDiagram
    participant Member as Member (SPA)
    participant API as Backend API
    participant DB as PostgreSQL
    participant Notif as Notification Service

    Member->>API: POST /api/v1/loyalty/redeem {reward_id, points_amount}
    API->>API: Authenticate (JWT) & authorize
    API->>DB: SELECT balance, reward catalog entry
    DB-->>API: balance, reward details

    alt Insufficient points or reward unavailable
        API-->>Member: 400 Cannot redeem
    else Valid redemption
        API->>DB: BEGIN transaction
        API->>DB: INSERT ledger entry (debit)
        API->>DB: INSERT redemption record (status: pending)
        API->>DB: UPDATE account balance
        API->>DB: COMMIT
        API-->>Member: 200 {redemption_id, status: pending}
        API->>Notif: POST notification (redemption confirmation)
    end
```

## Invariants

1. **Double-entry ledger** — every point movement is a debit+credit pair; total system points are zero-sum.
2. **Idempotency** — ingestion events carry a unique `event_id`; duplicates are detected and ignored.
3. **Atomicity** — balance updates and ledger writes are always in the same DB transaction.
4. **Exchange rates** — stored in a program-rules table; changes apply only to future exchanges.
