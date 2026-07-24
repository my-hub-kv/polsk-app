---
name: implement-user-story
description: Implement a bounded, approved Polsk App GitHub issue or active feature specification end-to-end. Use for feature work with explicit acceptance criteria that requires code, tests, authorization checks, documentation updates, and a reviewable delivery summary. Do not use for open-ended product discovery or unresolved requirements.
---

# Implement a Polsk App user story

1. Read root `AGENTS.md`, the issue/specification, and every referenced product, domain, architecture, and ADR document.
2. Inspect existing code/tests; stop and report unresolved conflicts instead of inventing behaviour; state the implementation scope.
3. Add/update tests where practical, implement the smallest complete slice, enforce event-year/object authorization server-side, use services and transactions for state transitions, and update documentation.
4. Run `./scripts/check.sh`, `./scripts/test.sh`, focused tests, and `git diff --check`.
5. Review with [the delivery checklist](references/delivery-checklist.md), then summarize behaviour, changed files, authorization, security/privacy, migrations, tests/results, documentation, and remaining risks.

Never deploy, merge, access production, add secrets, or expand beyond the approved issue.
