# Notifications

**Architecture status: Implemented foundation.**

```text
Domain transaction -> durable notification/delivery record -> request-triggered dispatcher
    -> in-app inbox -> push adapter
```

Domain state and the authenticated inbox commit independently of provider success. Idempotency is
scoped to event year and recipient. `NotificationDelivery` is created in the same database
transaction only when the optional Starti brand, API key, and app origin are configured. The
recipient/event/idempotency unique constraint is the final cross-process idempotency boundary:
batch inserts use a conflict-safe no-op update and delivery inserts ignore their own duplicate
constraint, so concurrent enqueue attempts leave one durable notification and delivery intent.

By default, `NOTIFICATION_DELIVERY_SYNCHRONOUS=False` and
`NOTIFICATION_DELIVERY_REQUEST_TRIGGERED=True`. After a committed request creates delivery work,
one best-effort daemon thread per web process drains all currently due records in safe claims of
up to 50. Requests do not wait for provider calls. Work that arrives while the dispatcher runs is
coalesced into a following pass. The thread is an opportunistic wake-up, not a durable worker:
deployments, restarts, suspension, or no notification-producing traffic can leave records pending.

The queue remains authoritative. An authenticated event administrator can process a bounded due
batch for their active event year, and a future scheduler may run alongside the request-triggered
dispatcher. Claim locking and delivery uniqueness prevent duplicate processing. A lease reclaims
work left in `processing` by an interrupted dispatcher. Retryable failures remain due at their
scheduled retry time; ambiguous transport failures are failed without retry because Starti has no
verified provider-side idempotency contract. Push copy is generic and lock-screen-safe; complete
content remains in the authenticated inbox. Never log secrets or notification bodies.

The initial activity schedule creates one in-app notification for each login account in the same
event year when an activity is created. The fan-out validates recipients and bulk-creates the
inbox and delivery records rather than issuing one database workflow per account. Saving succeeds
once the activity and inbox notifications are durable; push is delivered in the background.
Activity edits do not currently notify.
