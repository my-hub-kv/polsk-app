# Migrations

**Implementation status: Planned policy.** Every persisted-model change needs a reviewed migration. Create schema migrations with `python manage.py makemigrations`, inspect the generated result, and run `python manage.py makemigrations --check --dry-run` before handoff. Never hand-write a schema migration file.

Never modify an existing data migration after it has been created or applied. If its intended behaviour must change, create a new reviewed migration that moves the data forward safely. Likewise, do not casually edit applied migrations.

## Separate schema from data

Schema migrations define tables, fields, indexes, and constraints. Data migrations transform existing rows. Keep them separate whenever that makes deployment, rollback, or review safer. A data migration must use Django’s historical models through `apps.get_model()`, be safe to retry where practical, and avoid importing current model code.

For risky changes, prefer **expand → migrate/backfill → enforce → contract**:

1. Add a backwards-compatible field, table, or index.
2. Backfill in a deliberate, observable, and resumable operation.
3. Add validation or a database constraint only after data satisfies it.
4. Remove obsolete schema in a later approved change.

## PostgreSQL review

Assess nullability, defaults, `on_delete`, uniqueness/check constraints, indexes, locks, long-running operations, and rollback. Large-table backfills should be batched; a concurrent index or non-atomic migration needs an explicit PostgreSQL plan. Test PostgreSQL 17 behaviour in CI and use a representative prior schema when risk warrants it.

Use nullable historical references or explicit anonymisation when shared history must survive participant deletion. Destructive or irreversible work requires explicit human approval and a recovery plan. Never access a hosted database from Codex.

The repository already has initial Django migrations. Introducing or changing the authentication model after real identity data exists is a deliberate migration project, not a routine refactor.
