# Migration checklist

- Ownership and event-year foreign key are clear.
- `on_delete`, nullability, defaults, unique/check constraints, and indexes are intentional.
- Data migration, reversibility, locks, large-table assumptions, PostgreSQL 17, custom-user implications, history, and rollback are reviewed.
- Tests cover the change; no production access occurred.
