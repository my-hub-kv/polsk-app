# Development security

Public source is attacker-readable; secrets remain external and provider identity is not a control. Use safe authentication/password handling, server-side authorization, event scoping and IDOR prevention, CSRF, secure sessions/cookies/HTTPS, `DEBUG=False` production configuration that fails closed, and rate limiting for login/invitation flows when implemented.

Invitation tokens must expire and be single use. Audit profile switching; isolate private channels; escape CSV formula values; rely on template autoescaping; validate redirects; and plan upload safety before adding uploads. Review dependencies and secrets, log no sensitive data, never use production data in development, implement secure deletion, and require human review for sensitive changes.

Before a production deployment, run Django’s deployment checks with production-safe configuration. HSTS should be enabled only after every intended public hostname is permanently HTTPS-capable; choose its duration deliberately and do not enable broad subdomain policy without reviewing every subdomain.

## Identity, tokens, and sessions

Use Django's established password hashing, session, authentication, password-reset, and CSRF facilities instead of custom cryptography or token formats. Generate invitation or recovery secrets with a cryptographically secure source, retain only a hash when the workflow permits it, enforce expiry and single use atomically, and revoke them on deletion or credential reset. Login, invitation, recovery, and account-linking failures must not reveal whether an account, participant, email address, or invitation exists. Apply proportionate rate limits and safe audit events to those flows when they are implemented.

## Authorization and audit boundaries

Derive event year, acting account, active participant, and permissions from trusted server-side state. A URL, hidden field, form choice, query parameter, or JSON object ID never grants scope or permission: restrict choice querysets, scope related-object lookups to the current event year, and authorize every read and mutation before using it. Use the privacy-preserving response appropriate to the object; private channels must not disclose ordinary existence to a non-member.

Record sensitive mutations and administrator overrides with the acting account, active participant where relevant, event-year scope, action, time, and a minimal safe target reference. Audit records must not copy passwords, tokens, session identifiers, private-message bodies, dietary details, phone numbers, or deleted personal attributes. Audit-read access is itself privileged and event-scoped.

## External and supply-chain boundaries

Keep provider credentials and destinations in trusted configuration, never user-controlled URLs. Provider adapters need explicit timeouts, bounded retries, safe failure handling, and mocked tests; they must not make network calls from models, migrations, or open transactions. Review every new dependency for maintenance, licensing, supported Python/Django versions, and its security impact before approval. CI workflow changes need least-privilege permissions, no secret exposure to untrusted code, and human review; dependency vulnerability auditing and automated update proposals should be added as a dedicated supply-chain hardening change.
