# Polsk App

Polsk App is an invitation-only coordination application for one recurring annual family event. It helps participants understand today’s agenda, their responsibilities, and the practical information needed during the event.

The participant experience is Danish, mobile-first, and designed to be calm and low-friction. Polsk is the event name; it has no connection to Poland.

> **Project status:** early development. The repository currently contains the Django foundation and the approved product/design direction. Most product capabilities are planned, not yet implemented.

## What we are building

The planned product supports:

- A shared agenda that combines activities and chores.
- Fair, explainable chore planning and approved chore transfers.
- Participant, household, and event-year coordination.
- Channel-based communication without requiring everyone to exchange phone numbers.
- Food availability, reservations, shopping requests, safe vendor exports, and weather context.
- Historical event-year information, with privacy-conscious deletion behaviour.

Polsk App is for this one recurring event. It is not a multi-tenant platform for unrelated groups.

## Start here

| If you are… | Read… |
| --- | --- |
| A business or product collaborator | [Product vision](docs/product/vision.md), [confirmed decisions](docs/product/confirmed-decisions.md), and [user stories](docs/product/user-stories/) |
| Deciding whether a behaviour is settled | [Open questions](docs/product/open-questions.md) and the [documentation status conventions](docs/index.md#status-conventions) |
| A developer implementing a feature | [Documentation index](docs/index.md), [agent instructions](AGENTS.md), the relevant domain document, and [development setup](docs/development/setup.md) |
| Changing models or data | [Conceptual data model](docs/architecture/conceptual-data-model.md) and [migration guidance](docs/development/migrations.md) |
| Reviewing authorization or privacy | [Roles and permissions](docs/product/roles-and-permissions.md), [authorization model](docs/architecture/authorization-model.md), and [security guidance](docs/development/security.md) |
| Reviewing a pull request | [Pull-request process](docs/development/pull-request-process.md), [coding standards](docs/development/coding-standards.md), and [testing guidance](docs/development/testing.md) |
| Looking for a technical decision | [Architecture decision records](docs/architecture/decisions/) |

## Technology

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 17 for normal development, CI, and production
- Django templates and a modular Django monolith
- Server-rendered, mobile-first interface; HTMX and Alpine.js only where they add value

There is no separate SPA, frontend repository, microservice architecture, or Docker requirement in the current baseline.

## Local development

Use Python 3.12 and a virtual environment. The normal development path uses a deliberately configured development PostgreSQL database; never use production credentials.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env` with safe local development PostgreSQL components (`PGHOST`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`), then run:

```powershell
python manage.py migrate
python manage.py runserver
```

For a limited, isolated SQLite check, explicitly set `DJANGO_DEBUG=True`, `USE_SQLITE=True`, and a disposable local `DJANGO_SECRET_KEY`. Full setup details and safety notes are in [development setup](docs/development/setup.md).

### Verification

Run the checks relevant to your change:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

CI validates PostgreSQL 17 compatibility. Do not claim a check passed unless you ran it successfully.

## Contributing and review

Work from a bounded issue, use a non-`main` branch, keep changes focused, and update tests and documentation with behaviour changes. Human review is required before merge.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md), [Python and Django standards](docs/development/coding-standards.md), and [commenting guidance](docs/development/commenting-and-code-documentation.md) before changing code. Schema migrations are generated through Django; never hand-write them or modify an existing data migration.

Deployment, provider-account configuration, backups, and recovery procedures are intentionally maintained outside this public repository.

## Privacy and security

Treat every committed file as public. Never commit credentials, connection strings, real participant information, private messages, dietary information, screenshots containing personal data, or private operational details.

Report security vulnerabilities privately; see [SECURITY.md](SECURITY.md). The detailed security rules are in [development security guidance](docs/development/security.md).

## License

Polsk App is licensed under the [GNU Affero General Public License v3.0](LICENSE).
