# Development setup

Use Python 3.12, Node.js 22, and a virtual environment; Docker is not required. Install the existing `requirements.txt`, run `npm ci` and `npm run build:css` (or `npm run watch:css` during UI work), copy `.env.example` to `.env`, and use a local or developer-owned PostgreSQL configuration through `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`. Set `PGSSLMODE=disable` and `PGCHANNELBINDING=disable` for a local PostgreSQL server without TLS. Never use production credentials. SQLite is supported only as the explicit debug-only `USE_SQLITE=True` fallback and is limited; CI uses PostgreSQL 17.

For Neon, store only its direct hostname in `PGHOST` (without `-pooler`) and keep the password separately in `PGPASSWORD`. Runtime derives the pooled hostname. In Render, create the private `polsk-app-runtime` environment group in the dashboard and link it to the web service. It owns `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, every `PG*` component, `APP_ORIGIN`, all `STARTIAPP_*` values, `NOTIFICATION_DELIVERY_SYNCHRONOUS`, `NOTIFICATION_DELIVERY_REQUEST_TRIGGERED`, and the normally-false `PERFORMANCE_TIMING_LOGGING`; remove service-specific copies so the group is the single source of truth. The Blueprint references that existing group but never defines its values. Confirm the web service is behind a proxy that strips and sets `X-Forwarded-Proto` before relying on Django's proxy SSL setting.

## Production migrations

Render Free does not provide Shell access or pre-deploy commands. The `migrate-production` GitHub Actions job therefore runs only after the `django` job succeeds on a push to `main`. Render's `checksPass` trigger waits for that job, so a failed migration prevents deployment of the corresponding commit.

Configure these GitHub secrets in the `production` environment when available, or as repository secrets when the GitHub plan does not provide private-repository environment secrets: `MIGRATION_DJANGO_SECRET_KEY`, `MIGRATION_PGHOST`, `MIGRATION_PGDATABASE`, `MIGRATION_PGUSER`, `MIGRATION_PGPASSWORD`, and `KEEPALIVE_SECRET`. Configure `APP_BASE_URL` as a GitHub Actions variable. `MIGRATION_PGHOST` is Neon’s direct hostname. The migration job supplies TLS, channel-binding, and direct-connection settings itself. It receives no Starti credentials. Restrict workflow changes and `main` pushes through human review; destructive migrations require explicit review before merge.

Before using its direct connection, the job calls the existing protected keepalive endpoint to wake a suspended Neon database. The deployed web service must already exist for that preflight; initial provisioning remains a human-run operation.

Run `createsuperuser` and `bootstrap_event_admin` only once, manually and with a human-authorised direct Neon connection. They are not deployment jobs.

Apply migrations, run `python manage.py runserver`, run `python manage.py test`, and collect static files where relevant. For a safe isolated check, explicitly set `DJANGO_DEBUG=True`, `USE_SQLITE=True`, and a disposable local `DJANGO_SECRET_KEY`; this prevents a command from using a managed database through `.env`. Use another database only when it has been deliberately configured and authorised.
