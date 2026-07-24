# Development setup

Use Python 3.12 and a virtual environment; Docker is not required. Install the existing `requirements.txt`, copy `.env.example` to `.env`, and use a local or developer-owned PostgreSQL `DATABASE_URL`. Never use production credentials. SQLite is supported only as the explicit debug-only `USE_SQLITE=True` fallback and is limited; CI uses PostgreSQL 17.

Apply migrations, run `python manage.py runserver`, run `python manage.py test`, and collect static files where relevant. For a safe isolated check, explicitly set `DJANGO_DEBUG=True`, `USE_SQLITE=True`, and a disposable local `DJANGO_SECRET_KEY`; this prevents a command from using a managed database through `.env`. Use another database only when it has been deliberately configured and authorised.
