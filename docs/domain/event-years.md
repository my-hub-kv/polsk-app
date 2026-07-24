# Event years

**Product rules: Confirmed. Domain design: Candidate. Implementation: Planned.**

One event series has separate event-year records with year-specific dates, venue/address, coordinates, timezone, roles, and attendance. Useful lifecycle states are Draft, Active, Completed, and Archived. Selected templates can be copied to a new year; live records and historical quantities are never blindly copied. There is no multi-tenant organisation model.

> An object owned by one event year must never be accessible through another event year’s URL, selector, service, or permission check.

Every query, service, URL, and permission check must preserve this isolation. Previous-year comparisons are read-only historical context unless an explicit copying workflow is approved.
