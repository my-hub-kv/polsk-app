# Agenda and calendar user stories

Product status: Confirmed. Implementation status: Initial activity schedule implemented; broader agenda work planned.

## AGN-01: Use the agenda

As a participant, I want an agenda positioned near today with Mine, Household, and All views, so that I immediately understand the event.

### Acceptance criteria

Today is highlighted, “Gå til i dag” works, day responsibility is visible, exact/approximate times render clearly, and archived event years remain browsable.

### Authorization

Views are restricted to the active participant’s allowed event year.

### Current implementation

Agenda lists all activities in the active event year chronologically. It has an honest empty
state, shows exact or approximate times, and opens an event-scoped activity detail page.
Today positioning, filters, day responsibility, chores, and historical browsing remain planned.

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

### Current implementation

An authenticated active participant can create an activity with title, description, date,
start time, optional end time, and an approximate-time flag. The active profile owns the
activity; that owner and event administrators may edit it. Creation immediately makes the
activity visible to every participant in the event year and creates one in-app notification
for each participating login account. Editing does not notify. Activity audiences/groups,
reminders, cancellation, deletion, and history remain planned.

### Important edge cases

Post-publication editing rules require conservative implementation and documentation.

### Out of scope

Automatic parental reminders.
