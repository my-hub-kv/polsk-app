# Administration user stories

Product status: Confirmed. Implementation status: Emergency-backend foundation implemented; broader administration workflow planned.

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

High-impact actions are limited, server-authorized, and use focused provenance where future domain history requires it.

### Important edge cases

Shared history survives participant deletion.

### Out of scope

Unreviewed bulk destructive actions.

## Current emergency backend

Django Admin remains intentionally unlinked from the participant UI. It provides searchable, event-scoped lists for event years, participants, memberships, households, roles, accounts, invitations, notifications, and delivery state. Invitations, throttle fingerprints, notifications, notification read state, delivery queue records, and household membership records are inspection-only so that Admin cannot bypass their services or invariants. Ordinary account, event, participant, participation, role, and household changes remain available only to Django superusers for emergency recovery.
