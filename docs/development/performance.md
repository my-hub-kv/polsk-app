# Performance and perceived responsiveness

Performance review is required for every feature implementation and every code review. It
includes both server cost and whether a person can tell that an intentional wait is in
progress.

## Database and query discipline

Production uses Neon through transaction pooling. Free-tier latency, connection setup, and
database wake-up can make an otherwise small request noticeably slow. Keep Django connections
non-persistent as configured; do not change pooling settings solely to mask latency.

- Scope every event-owned query first, select related display data deliberately, and avoid
  query work in templates.
- Check list pages for N+1 queries and add `assertNumQueries()` where a stable, important
  query budget is useful.
- Keep mutation transactions short. Provider calls must remain outside the transaction and
  after commit.
- Consider fan-out work, such as notification creation, as proportional to the number of
  recipients and review it before expanding a workflow. For one event-wide notification, validate
  recipients and bulk-create durable records; do not repeat a full database workflow per account.
- In a successful POST/Redirect/Get mutation, do not construct page-shell data that the redirect
  discards. Build navigation, unread counts, and profile menus only when rendering a response.
- Keep participant-input validation local to a form or service where possible. Do not use a broad
  model `full_clean()` merely to revalidate trusted server-derived foreign keys; preserve explicit
  service authorization and database constraints instead. Cross-model validation remains required
  in model/admin workflows where those relations are user-editable.
- Request-triggered notification dispatch is deliberately best effort and drains all due work
  in claims of 50; it keeps provider latency out of the user request but may occupy a web process
  for a large queue. Do not add unbounded provider concurrency merely to shorten that work.

## Perceived responsiveness

Every navigation or mutation that can wait on a database or provider must give immediate,
accessible feedback. The shared shell shows a loading line for same-origin navigation. Forms
that may take noticeable time disable their submit button, replace its label with the current
action, and expose a Danish status message. Do not fake success, hide an error, or rely only on
colour or animation.

When adding a new slow operation, reuse these patterns or provide an equally accessible local
loading state. Preserve ordinary browser validation before disabling a submit control, and make
the action idempotent or safe against repeated submission on the server.

## Local timing diagnostics

For a reproducible local investigation, set `PERFORMANCE_TIMING_LOGGING=True` in the ignored
`.env` file and restart the Django process. The console then writes safe duration and count-only
lines for activity creation, notification fan-out, dispatcher scheduling, and background delivery.
They deliberately exclude titles, descriptions, account identifiers, event identifiers, URLs, and
provider responses. Copy those lines with the matching browser timestamp when diagnosing a delay,
then set the option back to `False` after the investigation.

The diagnostic records the effective delivery-policy booleans, the duration of transaction commit
and post-commit callbacks, and the time spent returning from `Thread.start()`. It also records the
background thread entering and ending. This distinguishes synchronous provider delivery, slow
database commit, and a genuinely asynchronous dispatcher without logging private configuration.

## Review checklist

- Review the query shape, relation loading, transaction duration, and external calls.
- Identify expected free-tier/cold-start waits and verify visible loading feedback manually on
  mobile and desktop.
- Test denied and failed operations still re-enable controls after the server response.
- Record a measured query budget only where it is durable; do not add brittle performance tests
  for incidental implementation details.
