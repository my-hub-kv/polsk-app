# Security checklist

- Authentication, Django password/session/reset use, invitation/recovery token generation, hashed storage where practical, expiry, single use, enumeration-safe errors, CSRF, HTTPS/cookies, rate limits, and safe errors.
- Event scope, IDOR, roles, household switching, actor/profile audit, private channels, message ownership, and admin permissions.
- Every related object ID supplied in a form, URL, JSON body, export, or mutation is event-scoped and authorized; form choice querysets do not expose out-of-scope objects.
- Shopping/export permissions and CSV formula injection; XSS, SQL injection, redirects, logs, personal data, secrets, external adapters, deletion, and migration impact.
- Audit events contain only minimal safe metadata and audit-read access is protected. Adapters have configured destinations, timeouts, bounded retries, no network calls inside models/migrations/transactions, and mocked tests.
- Dependency and workflow changes have least-privilege permissions, no secret exposure to untrusted code, and a documented vulnerability-audit/update path.
- Error reports and logs contain only approved safe context; client reports are bounded, same-origin, CSRF-protected, and cannot become a log-amplification or data-exfiltration endpoint.
- Relevant denied-access and regression tests.
