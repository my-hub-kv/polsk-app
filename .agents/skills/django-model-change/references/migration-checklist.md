# Migration checklist

- Ownership and event-year foreign key are clear.
- `on_delete`, nullability, defaults, unique/check constraints, and indexes are intentional.
- Schema and data migrations are separate where that improves safety; data migrations use historical models, are retry-safe where practical, and have a backfill plan.
- Expand/migrate/enforce/contract suitability, reversibility, locks, large-table batching, PostgreSQL 17, custom-user implications, history, and rollback are reviewed.
- Tests cover the change; no hosted database access occurred.
