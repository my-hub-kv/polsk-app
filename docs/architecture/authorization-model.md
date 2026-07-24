# Authorization model

Authentication account and active participant are distinct. Every protected query scopes to event-year membership and object ownership/membership before rendering or mutation. Roles grant capabilities, but channel membership, household switching, and object-level checks remain necessary. Templates may hide unavailable controls but never enforce security.

Use safe defaults, scoped QuerySets/selectors, explicit mutation authorization, CSRF-protected sessions, safe redirects, and explicit/audited administrator overrides. Deletion has separate authorization and impact rules. Implement login/invitation rate limiting when those flows are built.

## Review checklist

- Is every lookup event-year scoped and IDOR-resistant?
- Is active participant valid for the acting account and household?
- Are channel/private-object membership, role, and ownership checked server-side?
- Are mutations CSRF-protected, audited where needed, and safely rejected?
