# Development setup

Use Python 3.12 and a virtual environment; Docker is not required. Install the existing `requirements.txt`, copy `.env.example` to `.env`, and use a local or developer-owned PostgreSQL `DATABASE_URL`. Never use production credentials. SQLite is supported only as the explicit debug-only `USE_SQLITE=True` fallback and is limited; CI uses PostgreSQL 17.

Apply migrations, run `python manage.py runserver`, run tests, and collect static files where relevant. The repository scripts are [check.sh](../../scripts/check.sh), [test.sh](../../scripts/test.sh), and [codex-setup.sh](../../scripts/codex-setup.sh). They do not replace understanding the configuration they run against.
