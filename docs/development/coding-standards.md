# Python and Django coding standards

Use this page with [commenting and code documentation](commenting-and-code-documentation.md). Source identifiers, code comments, tests, commit messages, and technical documentation are English; user-visible text is Danish.

## Python

- Follow PEP 8 naming: `CapWords` classes, `snake_case` functions/variables, and `UPPER_CASE` constants. Use descriptive domain names rather than abbreviations.
- Group imports as standard library, third-party, Django, then local application imports. Do not use wildcard imports.
- Add type hints to public functions, service functions, selectors, and non-trivial helpers. Prefer precise domain types over `Any` or unstructured dictionaries when a stable type is known.
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

## Change quality

- Prefer small, cohesive, reviewable changes. Update tests and relevant documentation in the same change.
- Write tests for normal behaviour, denied access, event-year isolation, and meaningful edge cases. Use synthetic data only.
- Before handoff, run the relevant Django checks, tests, migration check, and `git diff --check` with an explicitly authorised local database configuration.
