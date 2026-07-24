# Weather user stories

Status: Confirmed

## WTH-01: Use weather context

As a coordinator, I want to configure an event-year location and view retained forecasts and observed weather, so that I can interpret planning and historical purchases.

### Acceptance criteria

Forecast snapshots and observed weather are separate; suggestions use weather context; provider failures do not prevent manual planning.

### Authorization

Only authorised event administrators configure location or imports.

### Important edge cases

Unavailable weather is displayed honestly.

### Out of scope

Weather-driven ordering.
