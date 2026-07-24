# Security checklist

- Authentication, password/invitation/session handling, CSRF, HTTPS/cookies, rate limits, and safe errors.
- Event scope, IDOR, roles, household switching, actor/profile audit, private channels, message ownership, and admin permissions.
- Every related object ID supplied in a form, URL, JSON body, export, or mutation is event-scoped and authorized; form choice querysets do not expose out-of-scope objects.
- Shopping/export permissions and CSV formula injection; XSS, SQL injection, redirects, logs, personal data, secrets, external adapters, deletion, and migration impact.
- Relevant denied-access and regression tests.
