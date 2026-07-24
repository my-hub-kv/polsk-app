# Communication user stories

Product status: Confirmed. Implementation status: Planned.

## MSG-01: Use channels

As a participant, I want to create/discover public channels and subscribe or unsubscribe, so that I can coordinate without sharing phone numbers.

### Acceptance criteria

Administrators create official and private channels; official channels cannot be muted; private non-members cannot access or discover a channel; no acknowledgement is required.

### Authorization

Membership governs private visibility; a subscription governs notification only.

### Important edge cases

Channel and message access is event-scoped.

### Out of scope

Direct messaging.

## MSG-02: Own messages

As a participant, I want to post, edit, and delete my messages, so that channel communication remains useful.

### Acceptance criteria

Administrators may delete any message; messages remain historically visible unless deleted.

### Authorization

Owners and administrators have distinct mutation rights.

### Important edge cases

Deleted content and errors must not leak private message bodies.

### Out of scope

Seen receipts.
