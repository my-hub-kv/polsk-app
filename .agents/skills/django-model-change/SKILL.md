---
name: django-model-change
description: Design, implement, and review Django model, constraint, index, or migration changes for Polsk App. Use whenever a task changes persistent schema, relationships, deletion behaviour, event scoping, or historical data. Do not use for documentation-only or view-only changes.
---

# Change the Django data model safely

1. Read `AGENTS.md`, relevant domain documentation/conceptual model, and `docs/development/migrations.md`.
2. Inspect models, migrations, constraints, tests, and query usage; confirm event-year ownership and deletion semantics.
3. Identify additive, destructive, or data-transforming work; stop for explicit approval before destructive/irreversible changes.
4. Prefer constraints and nullable historical references where appropriate; add migration/model tests and inspect generated operations when risk warrants.
5. Run migration checks and the relevant full suite; review [the migration checklist](references/migration-checklist.md) and summarize schema, risks, rollback, tests, and compatibility.

Never access a hosted database or use real data.
