# Accounts and households user stories

Product status: Confirmed. Implementation status: Planned.

## ACC-01: Join and manage credentials

As an invited adult, I want to join through an invitation link or QR code and set a username and password, so that I can access the event.

### Acceptance criteria

Invitation email is optional; an administrator can reset credentials; a child can later receive independent credentials without a new profile or lost history.

Participant onboarding leaves the optional credential invitation unchecked for every age group. An administrator may deliberately issue one for a participant in any age group.

### Authorization

Only a valid, unexpired, single-use invitation may create or link access.

### Important edge cases

Duplicate use, expiry, recovery, and existing participant profiles fail safely.

### Out of scope

Social login and public registration.

## ACC-02: Directory and household profile switching

As an adult, I want to view the directory and switch into a child profile in my household, so that I can coordinate appropriately.

### Acceptance criteria

Phone and dietary-information visibility is disclosed before saving; the switched profile is obvious; switching back is easy; administrators can safely delete a participant with impact preview.

### Authorization

Cross-household switching is always denied. Administrators cannot switch into another profile.

### Important edge cases

Future mutable domain records retain focused acting-account and active-participant provenance when history is needed.

### Out of scope

Exact birth-date storage.
