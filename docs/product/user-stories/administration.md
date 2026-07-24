# Administration user stories

Product status: Confirmed. Implementation status: Planned.

## ADM-01: Manage an event year

As an administrator, I want to create an event year from selected prior-year information, configure roles, households, attendance, and archive state, so that each year remains independently manageable.

### Acceptance criteria

Copying is selective; quantities are not blindly copied; historical years remain browsable.

### Authorization

Administrative event-year actions require administrator authority.

### Important edge cases

Year boundaries prevent cross-year mutation or access.

### Out of scope

Multi-tenant organisation administration.

## ADM-02: Use emergency administration

As an administrator, I want safe administrative tools for channels, inventory corrections, shopping exports, and participant deletion, so that operational exceptions are manageable.

### Acceptance criteria

Django admin remains an emergency backend; deletion previews impact where practical.

### Authorization

High-impact actions are limited and audited.

### Important edge cases

Shared history survives participant deletion.

### Out of scope

Unreviewed bulk destructive actions.
