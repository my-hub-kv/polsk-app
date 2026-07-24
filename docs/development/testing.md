# Testing

Tests are executable documentation of implemented behaviour. Use synthetic data only, keep tests deterministic, mock external adapters, and never call live external services or hosted databases. PostgreSQL 17 in CI is authoritative. Add a regression test for every bug and never claim a command passed unless it ran.

## Test layers

Use the layers relevant to the change:

- Model and database-constraint tests.
- Service/state-transition tests.
- QuerySet or selector tests, including event-year isolation.
- Form validation and view tests, including denied authorization.
- Household profile-switch and acting-account/active-participant tests.
- Planner-invariant and transfer race-condition tests.
- CSV formula-safety and export tests.
- Notification idempotency and provider-adapter contract tests.
- Deletion, timezone/date-boundary, and important-list query-count tests.
- Practical accessibility smoke checks for participant-facing templates.

## Django test rules

- Use `TestCase` by default. Use `TransactionTestCase` only when a test needs real commit behaviour, transaction visibility, locking, or `on_commit()` execution; it is slower because Django flushes the database between tests.
- Start with the narrowest meaningful test and broaden coverage when the change crosses domains. Test public behaviour and important invariants, not private implementation details. Mock only a boundary you do not own, such as an external provider or clock.
- Do not add negative assertions merely to prove a short-lived branch change or removed field is absent. Keep tests focused on final intended behaviour and real regression risks.
- Use `assertNumQueries()` for important lists when query count is part of the requirement. Test both successful and rejected mutations.
- Set up only the data a test needs. Name tests after the scenario and expected outcome, for example `test_non_member_cannot_view_private_channel`.
- Keep fixtures/factories readable and local to the domain. Do not build a global fixture with unrelated defaults.
- When changing imports in models, admin, shared utilities, template tags, or other startup-sensitive modules, run at least one command or test that executes Django setup; syntax-only checks cannot catch many import cycles.
