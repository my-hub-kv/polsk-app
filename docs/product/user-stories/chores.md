# Chores user stories

Product status: Confirmed. Implementation status: Planned.

## CHR-01: Plan and publish chores

As a coordinator, I want to configure attendance, workload, preferences, availability, sticky assignments, and chore types, so that I can generate, validate, adjust, and publish a fair draft plan.

### Acceptance criteria

Drafts show validation problems, remain hidden from participants, preserve sticky assignments, and publish only after human review. Once staffing minima are met, the planner may add eligible participants to improve fairness without exceeding an optional maximum. Day responsibility is derived.

### Authorization

Only authorised coordinators plan or publish.

### Important edge cases

Disabled participants/days, role eligibility, child/adult pairing, overlaps, and final-day responsibility are handled or reported.

### Out of scope

Completion controls and spreadsheet-grid participant UI.

## CHR-02: View chores

As a participant, I want to see my, household, and all published chores with their team, so that I know my responsibilities.

### Acceptance criteria

Published plans have no done, proof, photo, or approval controls.

### Authorization

Draft data never reaches normal participants.

### Important edge cases

Event-year isolation applies to every list and detail view.

### Out of scope

Household-level assignment.

## CHR-03: Suggest or create a chore

As a participant, I want to create a draft chore, so that I can suggest work that should be planned without publishing an assignment myself.

### Acceptance criteria

Any participant can create a draft chore for the current event year. Creating it does not publish assignments or notify participants.

### Authorization

Participants may create drafts; authorised coordinators decide whether to edit, schedule, configure, or include a draft in a published plan.

### Important edge cases

The draft is event-year scoped and does not expose unpublished planning data to normal participants.

### Out of scope

Participant-led publication or direct assignment of other participants.
