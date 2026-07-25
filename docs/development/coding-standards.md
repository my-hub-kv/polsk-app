# Python and Django coding standards

Use this page with [commenting and code documentation](commenting-and-code-documentation.md). Source identifiers, code comments, tests, commit messages, and technical documentation are English; user-visible text is Danish.

## Standard hierarchy and external references

This page, relevant product/domain documents, accepted ADRs, and the repository configuration are the project standard. They take precedence over external guidance. Use [PEP 8](https://peps.python.org/pep-0008/) as the Python baseline and the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) as a supplementary reference for readable imports, type annotations, docstrings, and error handling. Follow Djangoâ€™s documented APIs and the projectâ€™s supported versions rather than copying compatibility patterns from projects that support multiple Django or Python releases.

The project uses an 88-character line-length target, except for unavoidable URLs, paths, generated migration code, and deliberately unbroken strings. Wrap readable expressions using parentheses; never use a backslash solely for line continuation. Do not introduce automated formatters, linters, type checkers, or pre-commit hooks as part of feature work: tooling changes need their own approved, documented change with pinned development dependencies and CI coverage.

## Python

- Follow PEP 8 naming: `CapWords` classes, `snake_case` functions/variables, and `UPPER_CASE` constants. Use descriptive domain names rather than abbreviations.
- Group imports as standard library, third-party, Django, then local application imports. Do not use wildcard imports.
- Add type hints to public functions, service functions, selectors, and non-trivial helpers. Prefer precise domain types over `Any` or unstructured dictionaries when a stable type is known.
- On Python 3.12, prefer built-in generic types and `X | None` where they make the contract clearer. Use `from __future__ import annotations` only when it avoids a real forward-reference or import-cycle problem; do not add it mechanically.
- Keep functions focused. Prefer early returns for invalid preconditions and do not silently ignore invalid states.
- Use the standard library and Django before adding a dependency. A dependency needs explicit approval and a written purpose.
- Catch only expected exceptions. Do not catch broad `Exception` unless the boundary, safe logging, and recovery behaviour are explicit.
- Use `pathlib` for filesystem paths, timezone-aware datetimes, enums/Django choices for stable state, and constants close to the domain that owns them.

## Django design

- Keep views responsible for HTTP concerns: input, authorization, delegation, response, and presentation. Use explicit forms or serializers-equivalent validation for user input; never mutate data on `GET`.
- Use Post/Redirect/Get after successful browser form mutations. Restrict unsafe endpoints to the intended HTTP methods and enforce authentication and object-level authorization in server-side code.
- Put multi-model state changes in explicit service functions. Use `transaction.atomic()` for a state transition that must succeed or fail together; keep transactions short and register external side effects only after commit.
- Put reusable read patterns in QuerySets, managers, or clearly named selectors. Scope every event-owned query to its event year before object lookup, and use `select_related()`/`prefetch_related()` deliberately for lists.
- Treat a model's default manager as part of the product contract. When ordinary product access must exclude internal or system-managed rows, use an explicit full-access manager such as `all_objects`, audit admin/related-manager/migration behaviour, and test both visibility paths. Do not hide rows by default without checking those consequences.
- Use database constraints for invariants that must hold under concurrent requests. Model/form validation improves feedback but is not a substitute for an important database constraint.
- Keep templates presentational. Do not put business rules, authorization decisions, writes, or query-heavy loops in templates.
- Do not use `Model.save()`, signals, middleware, or generic utility modules as hidden primary business workflows. Do not make network calls from models or migrations.
- Keep lower-level modules independent of views, templates, template tags, and other UI-layer imports. If shared logic would create a Django startup cycle, extract a lower-level helper rather than importing a UI module.
- Generate schema migrations with `python manage.py makemigrations`; never hand-write schema migration files or change an existing data migration.

## Errors, logging, and security

- Return actionable, user-safe errors in Danish. Keep technical detail in safe server-side logs where needed.
- Never log credentials, tokens, headers, cookies, phone numbers, dietary information, message bodies, or other personal data.
- Preserve Django template autoescaping. Do not use `mark_safe()` or raw HTML from untrusted data without a documented, reviewed sanitisation boundary.
- Validate redirect destinations, use Django CSRF protection for browser session requests, and treat external adapters as fallible boundaries.

## Django Admin

Django Admin is an unlinked internal emergency backend, not a participant-facing workflow. Every persisted Polsk model is registered so authorised staff can inspect operational data when needed. Access uses Django's standard active-staff login and model-permission checks; Admin has no active-event or participant-profile scope, so a staff account permitted to view a model can view all of that model's event years and records.

- Give every registered model a concise, stable, human-readable `__str__()` value. It must not expose passwords, tokens, digests, session identifiers, message bodies, or unnecessary personal data.
- Configure each changelist deliberately with useful `list_display`, `search_fields`, `list_filter`, deterministic ordering, and `list_select_related` or `prefetch_related` for every relation used by columns or string representations.
- Use `autocomplete_fields` for editable dynamic `ForeignKey` and `ManyToManyField` relations. The related admin must provide useful `search_fields` and a useful `__str__()` value. Standard selects remain appropriate for genuinely small, fixed choices.
- Do not add Polsk-specific read-only modes, hidden fields, CRUD permission overrides, disabled bulk actions, event scopes, or participant-profile scopes. The emergency backend uses Django's standard model forms and normal staff model permissions.
- Direct emergency edits and Django's built-in bulk actions are permitted when staff need to repair data. Admin does not infer or enforce an active event scope; the operator must preserve cross-record invariants, including keeping a participation and its household membership in the same event year.
- Django's ordinary field and model-form validation, plus actual database constraints, remain in effect. They are framework integrity checks rather than participant-workflow rules.

## Change quality

- Prefer small, cohesive, reviewable changes. Update tests and relevant documentation in the same change.
- Write tests for normal behaviour, denied access, event-year isolation, and meaningful edge cases. Use synthetic data only.
- Before handoff, run the relevant Django checks, tests, migration check, and `git diff --check` with an explicitly authorised local database configuration. Do not claim style, type, security, coverage, or dependency checks ran unless the repository actually configures and ran them.
