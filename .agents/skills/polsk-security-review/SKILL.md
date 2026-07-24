---
name: polsk-security-review
description: Review Polsk App code or a pull-request diff for security, privacy, authorization, event-isolation, profile-switching, personal-data, CSV, messaging, and migration risks. Use before merging authentication, permissions, household switching, messaging, food, shopping, notification, deletion, or admin changes. Do not use as a substitute for human review.
---

# Review Polsk App security

1. Read `AGENTS.md`, authorization/domain documents, and determine protected objects/trust boundaries.
2. Review every query/mutation for event-year scope, object authorization, IDOR, active participant/actor handling, household switching, and private-channel visibility.
3. Review CSRF, sessions, redirects, validation, logs/errors, fixtures/evidence, migrations/deletion, adapters, CSV formula safety, and notification recipient/idempotency.
4. Run relevant tests or explain why not; apply [the security checklist](references/security-checklist.md).
5. Report findings by severity with file/line evidence and concrete remediation.

Do not call provider identity alone a vulnerability; report exposed credentials, insecure configuration, or exploitable behaviour.
