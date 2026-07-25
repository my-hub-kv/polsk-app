# Participants and households

**Product rules: Confirmed. Domain design: Candidate. Implementation: Foundation implemented.**

Authentication account, participant profile, event participation, household, household membership, event-year role, active participant, and acting authenticated user are distinct concepts. A session stores active participant separately from the authenticated adult.

Profile switching is: authenticate an adult; choose a same-household child; store active participant; scope participant-facing queries to it; and reject cross-household switching. Administrators cannot switch into another profile.

Implementation: `accounts.User` is the credential account and `people.Participant` is the durable profile. Event participation and household membership are explicit event-year records. There is no generic audit model; future mutable domain records add focused provenance when needed.

`people.services.assign_household_membership()` is the write boundary for household membership and validates that both records belong to the same event year. Django Admin deliberately exposes existing memberships read-only, so it cannot bypass this boundary. Profile-switch tests cover same-household success and cross-household denial.

Age groups are 0–3, 4–11, 12–18, and adult; exact birthdays are not stored. Directory, optional phone, and dietary visibility follow the confirmed disclosed-all-participants policy. Household membership changes between years must be explicit so history remains understandable.
