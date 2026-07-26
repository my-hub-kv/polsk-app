# Authorization model

Authentication account and active participant are distinct. Every protected query scopes to event-year membership and object ownership/membership before rendering or mutation. Roles grant capabilities, but channel membership, household switching, and object-level checks remain necessary. Templates may hide unavailable controls but never enforce security.

Use safe defaults, scoped QuerySets/selectors, explicit mutation authorization, CSRF-protected sessions, safe redirects, and explicit administrator overrides where future domain rules allow them. Derive event year, acting account, active participant, and permissions from trusted server-side state; hidden fields, URL/query values, JSON IDs, and form choices must be scoped and authorized before use. Deletion has separate authorization and impact rules. Implement login/invitation rate limiting when those flows are built.

The versioned participant feature registry controls release visibility only. Normal participants are redirected from unpublished feature pages, while staff and superusers may review those pages. That review override is not a role or permission grant: every view, service, event scope, household rule, and administrator operation continues to enforce its own server-side authorization. Administration is deliberately outside the feature registry and remains available only to the active event administrator.

## Review checklist

- Is every lookup event-year scoped and IDOR-resistant?
- Is active participant valid for the acting account and household?
- Are channel/private-object membership, role, and ownership checked server-side?
- Are mutations CSRF-protected, audited where needed, and safely rejected?
- Are every related-object ID and every form choice restricted to the current event year and authorized before use?
