# Chore planning

**Product rules: Confirmed. Planner and persistence design: Candidate. Implementation: Planned.**

Every chore has exactly one `A` task-responsible person; `X` is an ordinary adult, `B` a child, and `BA` a dinner-only child-food responsible. Dinner `A` and `BA` differ. A chore occurrence belongs to an event year and has date, exact/approximate time, type, description, minimum total/adult/child counts, optional maximum, optional `BA`, and a draft plan version.

Planning inputs include daily presence/availability, global and daily chore enablement, workload percentage, age group, `A`/`BA` eligibility, preferences/avoids, household, keep-together preference, sticky assignments, and locked assignments.

## Hard constraints

Participants must be present, enabled, available, non-overlapping, and in the same event year. Exactly one eligible `A`, any required eligible `BA`, different dinner `A`/`BA`, minima, optional maximum, sticky/locked assignments, and same-household adult pairing for every child must hold.

## Objectives and lifecycle

Subject to hard constraints, favour fair attendance-adjusted workload, preferences, task spread/variety, household preference, and no needless overstaffing. Every assignment counts as one; there are no hidden responsibility weights.

Validate inputs; apply fixed assignments; assign special roles and child/adult pairs; fill minima; improve with safe swaps; report warnings; save Draft; require human review before Published; later Archive. Normal participants see Published only, and no completion state exists. Deterministic explainable rules or an explainable constraint solver are required; a stored seed remains open.

Validation examples: missing eligible `A`/`BA`, insufficient dinner adult, child without household adult, overlap, workload imbalance, or exceeded maximum. Day responsible for date D is the `A` on dinner D+1, adds no chore count, and has an open final-day edge case.
