# Testing

Use model/constraint, service, selector/query, form, view, authorization, event-isolation, profile-switch, planner-invariant, transfer-race, CSV, notification-idempotency, adapter-contract, deletion, timezone/date, query-count, and practical accessibility smoke tests as the feature requires.

Fixtures are synthetic, tests deterministic, adapters mocked, and live external services/production databases forbidden. PostgreSQL 17 in CI is authoritative. Add a regression test for each bug and never claim a command passed unless it ran.
