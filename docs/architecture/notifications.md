# Notifications

**Architecture status: Candidate design. Implementation: Planned.**

```text
Domain transaction -> durable notification/outbox record -> delivery dispatcher
    -> in-app delivery -> push adapter -> email adapter
```

Domain state commits independently of provider success. Delivery records support idempotency, retry, failure state, recipient preferences, official-channel rules, transfer notifications, and approximate calendar reminders. Draft-plan changes create no participant notifications. Never log secrets or message bodies unless a specific safe policy approves it. Provider implementations remain outside domain apps behind adapters.
