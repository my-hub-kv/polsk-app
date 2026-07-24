# Polsk App agent instructions

## Purpose and sources of truth

Polsk App is an invitation-only application for one recurring yearly family event, not a platform for unrelated groups. Each event year is stored separately so history can be reviewed. The interface is Danish; technical source, identifiers, comments, tests, commits, and technical documentation are English.

“Polsk” is the event name, unrelated to Poland. Do not use Polish language, national imagery, flags, or colours.

Read [docs/index.md](docs/index.md) before product work. Use this precedence: direct human instructions; confirmed product rules; domain invariants; accepted ADRs; an approved written feature brief when one exists; tests and existing behaviour; then general conventions. Stop and report conflicts or ambiguity; never invent a product decision or commit raw conversations or private reasoning.

## Baseline and boundaries

- Python 3.12, Django 5.2 LTS, PostgreSQL 17 in production and CI.
- Modular Django monolith; templates first, HTMX for useful partial updates, Alpine only for small local interactions, Tailwind for styling.
- No Docker, SPA, separate frontend, microservices, Kubernetes, Redis, Celery, WebSockets, or Channels without an approved ADR.
- Make the smallest complete requested local change. Do not deploy, merge, push to `main`, rotate secrets, or alter live infrastructure.
- Explicit human approval is required for destructive migrations, irreversible transformations, production dependencies, authentication or authorization architecture, deployment architecture, live systems, secrets, or material scope expansion.

## Git and staging boundary

- Never run `git add`, `git restore --staged`, `git reset`, `git commit`, `git stash`, `git merge`, `git rebase`, `git push`, or any other command that changes Git staging, history, or remote state unless the human explicitly asks for that exact action in the current request.
- Never infer permission to stage from wording such as “finish”, “prepare”, “ready to commit”, “review”, or from an existing staged worktree.
- Before staging any file, ask for permission and wait for an explicit yes. This rule applies even when staging appears helpful or necessary to preserve a rename.

## Security and product safety

- Treat committed files as public. Never commit, print, log, or expose secrets, real participant data, hosted-database details, account IDs, dashboard links, production URLs, or recovery procedures.
- Never access a hosted production database or shared hosted development database. Codex uses only isolated local or disposable test databases containing synthetic data; authorised humans perform shared-environment database operations outside Codex.
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

Create schema migrations with `python manage.py makemigrations`; never hand-write schema migration files. Never modify an existing data migration after it has been created or applied—add a new, reviewed migration instead. Use repository scripts when present, plus `python manage.py makemigrations --check --dry-run` and `git diff --check`. Test successful and denied authorization, event-year isolation, profile switching, deletion, constraints, CSV safety, date boundaries, and mocked provider adapters as relevant. CI PostgreSQL 17 is authoritative.

Follow `docs/development/coding-standards.md` and `docs/development/commenting-and-code-documentation.md` for Python, Django, comments, and docstrings.

Documentation status is deliberate: **Confirmed** means product behaviour is approved; **Candidate** means it is a proposal and must not be implemented as settled behaviour; **Planned** means approved behaviour has no implementation yet; **Implemented** means tests and code enforce it. Never promote a Candidate merely because it is convenient to build.

## Review focus

Flag missing event scoping or object authorization; insecure profile switching; acting-account/active-profile confusion; personal data or secrets in any artifact; frontend-only rules; destructive migrations; missing constraints/tests; N+1 list risks; unmocked external calls; non-Danish visible text; undocumented behaviour; unjustified dependencies; and scope expansion.
