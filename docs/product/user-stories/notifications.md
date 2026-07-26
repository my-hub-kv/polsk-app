# Notifications user stories

Product status: Confirmed. Implementation status: Foundation implemented; broader notification
preferences and channels planned.

## NTF-01: Receive relevant notification

As a participant, I want in-app, push-adapter, invitation/credential email, calendar, and transfer notifications, so that I receive useful event updates.

### Acceptance criteria

Public channels default off, official channels cannot be muted, delivery is not duplicated, failures are safely recorded, and draft plan changes do not notify participants.

### Authorization

Recipient selection respects event scope, channel membership, role, and preferences.

### Important edge cases

Provider failure does not corrupt domain state.

### Current implementation

The authenticated event-scoped inbox, unread badge, durable delivery queue, Starti push adapter,
and administrator delivery fallback are implemented. Activity creation creates one notification per
same-event login account. Delivery is idempotent per recipient and event year and is best-effort in
a request-triggered background thread after commit. Channel preferences, official/public channel
rules, invitation/credential email, calendar notifications, and transfer notifications remain
planned.

### Out of scope

Routine email announcements.
