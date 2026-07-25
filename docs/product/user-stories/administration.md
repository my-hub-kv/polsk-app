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

Django Admin remains intentionally unlinked from the participant UI. It uses Django's standard active-staff login and model permissions; it has no event-year or participant-profile scope, so an authorised staff member can inspect all data for each permitted model. Every Polsk model is registered with standard add, change, delete, and bulk-action access for emergency repair, including invitations, throttle state, notification records, and household memberships. Admin deliberately has no Polsk-specific read-only modes, hidden fields, or service-level workflow restrictions. Django's ordinary model-form validation and database constraints remain in effect. Operators must preserve cross-record invariants, including same-event household membership when moving a participation.
