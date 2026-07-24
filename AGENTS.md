# Polsk App agent instructions

## Purpose and sources of truth

Polsk App is an invitation-only application for one recurring yearly family event, not a platform for unrelated groups. Each event year is stored separately so history can be reviewed. The interface is Danish; technical source, identifiers, comments, tests, commits, and technical documentation are English.

“Polsk” is the event name, unrelated to Poland. Do not use Polish language, national imagery, flags, or colours.

Read [docs/index.md](docs/index.md) before product work. Use this precedence: direct human instructions; confirmed product rules; domain invariants; accepted ADRs; approved active specifications; tests and existing behaviour; then general conventions. Stop and report conflicts or ambiguity; never invent a product decision or commit raw conversations or private reasoning.

## Baseline and boundaries

- Python 3.12, Django 5.2 LTS, PostgreSQL 17 in production and CI.
- Modular Django monolith; templates first, HTMX for useful partial updates, Alpine only for small local interactions, Tailwind for styling.
- No Docker, SPA, separate frontend, microservices, Kubernetes, Redis, Celery, WebSockets, or Channels without an approved ADR.
- Make the smallest complete requested local change. Do not deploy, merge, push to `main`, rotate secrets, or alter live infrastructure.
- Explicit human approval is required for destructive migrations, irreversible transformations, production dependencies, authentication or authorization architecture, deployment architecture, live systems, secrets, or material scope expansion.

## Security and product safety

- Treat committed files as public. Never commit, print, log, or expose secrets, real participant data, hosted-database details, account IDs, dashboard links, production URLs, or recovery procedures.
- Never access hosted development or production databases without explicit authorization. Use synthetic fixtures, examples, and screenshots.
- Enforce authorization on the server. Scope every event-owned object to its event year and prevent IDOR; hidden UI is never authorization.
- Do not weaken authentication, CSRF, secure cookies, HTTPS, or production failure handling. Do not expose secrets to untrusted pull-request workflows.
- Participant profiles and login credentials are separate. An adult may act as a child only within the same household; record both acting account and active participant for auditable actions.
- Do not store exact birth dates or years. Age groups are 0–3, 4–11, 12–18, and adult. Phone numbers and dietary information are visible to all participants only with clear disclosure before saving.
- Participant deletion removes sensitive personal data while preserving shared history through explicit nullable references or anonymisation. Never cascade-delete shared history.

## Implementation and Django rules

1. Read the issue/specification and relevant documentation; identify unresolved questions.
2. Inspect existing code and tests, add focused tests where practical, then implement the smallest vertical slice.
3. Keep views thin, validate input explicitly, use services for multi-model workflows, selectors/QuerySets for reusable reads, transactions for state changes, and database constraints for important invariants.
4. Avoid primary-workflow signals, hidden cross-app effects, generic `utils.py` modules, premature abstractions, and unreviewed dependencies.
5. Use timezone-aware datetimes, deliberate related-object loading, type hints for public/non-trivial functions, semantic accessible mobile-first HTML, and Danish visible text.
6. Update affected documentation and honestly summarize behaviour, authorization, security, migrations, tests, and open questions.

Use repository scripts when present, plus `python manage.py makemigrations --check --dry-run` and `git diff --check`. Test successful and denied authorization, event-year isolation, profile switching, deletion, constraints, CSV safety, date boundaries, and mocked provider adapters as relevant. CI PostgreSQL 17 is authoritative.

## Review focus

Flag missing event scoping or object authorization; insecure profile switching; acting-account/active-profile confusion; personal data or secrets in any artifact; frontend-only rules; destructive migrations; missing constraints/tests; N+1 list risks; unmocked external calls; non-Danish visible text; undocumented behaviour; unjustified dependencies; and scope expansion.
