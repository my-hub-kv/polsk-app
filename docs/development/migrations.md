# Migrations

Review every migration. Prefer additive steps and expand/migrate/contract for risky work; separate schema/data migrations where useful and keep data migrations reversible where practical. Destructive work requires explicit human approval. Test PostgreSQL behaviour; never access production from Codex.

Review historical nullable references, `on_delete`, constraints, indexes, defaults, locking, and rollback. The initial Django migrations already exist, so authentication-model changes need a deliberate approved plan. Do not casually edit applied migrations. Run `python manage.py makemigrations --check --dry-run`; test representative prior schemas when risk warrants it.
