# Notifications

**Architecture status: Implemented foundation.**

```text
Domain transaction -> durable notification/outbox record -> delivery dispatcher
    -> in-app delivery -> push adapter -> email adapter
```

Domain state commits independently of provider success. Every notification is available in the authenticated inbox. Idempotency is scoped to its event year and recipient. `NotificationDelivery` is created in the same database transaction only when the optional Starti brand, API key, and app origin are configured. By default, `NOTIFICATION_DELIVERY_SYNCHRONOUS=True` dispatches that one delivery after the originating transaction commits, so the initiating request waits without risking a domain rollback. Setting it to `False` preserves the durable queue for a future scheduler. The authenticated administrator page can process a bounded due batch only for its active event year and can prune expired privacy-preserving throttle fingerprints; it never resends deliveries already marked sent. A lease reclaims work left in `processing` by an interrupted worker. A confirmed provider failure may be retried, but an ambiguous transport failure is recorded as failed without retry because Starti has no verified provider-side idempotency contract; the in-app inbox remains authoritative. The current notification center clears its badge when opened. Starti owns device-token storage; Polsk stores only its derived account identifier. Push copy is intentionally generic and lock-screen-safe; full notification content remains in the authenticated inbox. Draft-plan changes create no participant notifications. Never log secrets or message bodies. Provider implementations remain outside domain apps behind adapters.
