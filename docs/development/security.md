# Development security

Public source is attacker-readable; secrets remain external and provider identity is not a control. Use safe authentication/password handling, server-side authorization, event scoping and IDOR prevention, CSRF, secure sessions/cookies/HTTPS, `DEBUG=False` production configuration that fails closed, and rate limiting for login/invitation flows when implemented.

Invitation tokens must expire and be single use. Audit profile switching; isolate private channels; escape CSV formula values; rely on template autoescaping; validate redirects; and plan upload safety before adding uploads. Review dependencies and secrets, log no sensitive data, never use production data in development, implement secure deletion, and require human review for sensitive changes.
