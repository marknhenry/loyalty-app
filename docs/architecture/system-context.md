# System Context Diagram

Shows the loyalty platform in relation to its users and external systems.

```mermaid
C4Context
    title System Context — Loyalty Platform

    Person(member, "Member", "End-user earning and redeeming loyalty points")
    Person(admin, "Platform Admin", "Manages program rules, monitors analytics")

    System(loyalty, "Loyalty Platform", "Points ingestion, exchange, balance, and redemption")

    System_Ext(partnerA, "Partner App A", "Retail POS / e-commerce — emits purchase events")
    System_Ext(partnerB, "Partner App B", "Travel booking — emits booking events")
    System_Ext(partnerC, "Partner App C", "Financial services — emits transaction events")
    System_Ext(idp, "Identity Provider", "OAuth2/OIDC — authenticates members & admins")
    System_Ext(email, "Notification Service", "Sends transactional emails & push notifications")

    Rel(member, loyalty, "Views balance, redeems rewards", "HTTPS")
    Rel(admin, loyalty, "Configures programs, views reports", "HTTPS")
    Rel(partnerA, loyalty, "Sends point-earning events", "Webhook / REST")
    Rel(partnerB, loyalty, "Sends point-earning events", "Webhook / REST")
    Rel(partnerC, loyalty, "Sends point-earning events", "Webhook / REST")
    Rel(loyalty, idp, "Validates tokens", "OIDC")
    Rel(loyalty, email, "Triggers notifications", "REST / SMTP")
```

## Key Observations

| Aspect | Decision |
|--------|----------|
| Ingestion model | Partner apps push events via webhook; platform does not poll |
| Auth | Delegated to an external IdP (JWT-based) |
| Notifications | Decoupled — platform emits events, notification service delivers |
