# Participants and households

**Product rules: Confirmed. Domain design: Candidate. Implementation: Planned.**

Authentication account, participant profile, event participation, household, household membership, event-year role, active participant, and acting authenticated user are distinct concepts. A session stores active participant separately from the authenticated adult.

Profile switching is: authenticate an adult; choose a same-household child; store active participant; scope participant-facing queries to it; record acting account and active participant for auditable mutations; reject cross-household switching. Exceptional administrator access must be explicit and audited.

Age groups are 0–3, 4–11, 12–18, and adult; exact birthdays are not stored. Directory, optional phone, and dietary visibility follow the confirmed disclosed-all-participants policy. Household membership changes between years must be explicit so history remains understandable.
