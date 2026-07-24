# Notifications user stories

Product status: Confirmed. Implementation status: Planned.

## NTF-01: Receive relevant notification

As a participant, I want in-app, push-adapter, invitation/credential email, calendar, and transfer notifications, so that I receive useful event updates.

### Acceptance criteria

Public channels default off, official channels cannot be muted, delivery is not duplicated, failures are safely recorded, and draft plan changes do not notify participants.

### Authorization

Recipient selection respects event scope, channel membership, role, and preferences.

### Important edge cases

Provider failure does not corrupt domain state.

### Out of scope

Routine email announcements.
