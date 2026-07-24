# Chore planning

**Product rules: Confirmed. Planner and persistence design: Candidate. Implementation: Planned.**

Every chore has exactly one `A` task-responsible person; `X` is an ordinary adult, `B` a child, and `BA` a dinner-only child-food responsible. The `A` ensures the chore happens and coordinates help as needed. For dinner, `BA` ensures suitable food is available for children; dinner `A` and `BA` differ. A chore occurrence belongs to an event year and has date, exact/approximate time, type, description, minimum total/adult/child counts, optional maximum, optional `BA`, and a draft plan version.

Planning inputs include daily presence/availability, global and daily chore enablement, workload percentage, age group, `A`/`BA` eligibility, preferences/avoids, household, keep-together preference, sticky assignments, and locked assignments.

## Hard constraints

Participants must be present, enabled, available, non-overlapping, and in the same event year. Exactly one eligible `A`, any required eligible `BA`, different dinner `A`/`BA`, minima, optional maximum, sticky/locked assignments, and same-household adult pairing for every child must hold. One eligible adult may satisfy that pairing for multiple children from the same household on the same chore.

## Objectives and lifecycle

Subject to hard constraints, favour fair attendance-adjusted workload, preferences, task spread/variety, household preference, and no needless overstaffing. Once minimum staffing is satisfied, the planner may add eligible participants above the minimum to improve fairness, up to an optional maximum. Without a maximum, fairness may justify additional assignments, but not unnecessary overstaffing. Every assignment counts as one; there are no hidden responsibility weights.

Validate inputs; apply fixed assignments; assign special roles and child/adult pairs; fill minima; add eligible participants where helpful for fairness; improve with safe swaps; report warnings; save Draft; require human review before Published; later Archive. Normal participants see Published only, and no completion state exists. When the keep-household-together preference is enabled, it applies to every participating member of the household; it is a soft preference unless an approved feature makes it a hard constraint. Deterministic explainable rules or an explainable constraint solver are required; a stored seed remains open.

Validation examples: missing eligible `A`/`BA`, insufficient dinner adult, child without household adult, overlap, workload imbalance, or exceeded maximum. Day responsible for date D is the `A` on dinner D+1 so that person has time to check what must be purchased or prepared; it adds no chore count and has an open final-day edge case. Whether a `BA` must always be an adult remains open.
