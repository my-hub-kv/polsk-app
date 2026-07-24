# Agenda and calendar user stories

Status: Confirmed

## AGN-01: Use the agenda

As a participant, I want an agenda positioned near today with Mine, Household, and All views, so that I immediately understand the event.

### Acceptance criteria

Today is highlighted, “Gå til i dag” works, day responsibility is visible, exact/approximate times render clearly, and archived event years remain browsable.

### Authorization

Views are restricted to the active participant’s allowed event year.

### Important edge cases

Empty days, approximate periods, and unavailable activities have designed states.

### Out of scope

External calendar synchronisation.

## AGN-02: Manage activities

As a participant, I want to create and edit my activity, while administrators can manage activities, so that the agenda stays useful.

### Acceptance criteria

Activities open in detail and generate an approximate 15-minute reminder when applicable.

### Authorization

Owners edit their own activity; administrators manage any activity.

### Important edge cases

Post-publication editing rules require conservative implementation and documentation.

### Out of scope

Automatic parental reminders.
