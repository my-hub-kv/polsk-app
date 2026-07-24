# Roles and permissions

**Role list: Confirmed. Permission matrix: Candidate policy. Implementation status: Planned.**

Event-year roles are additive and may change between years. The matrix is a starting policy, not an implementation authority for an unresolved edge case; every eventual permission must be enforced server-side.

| Capability | Participant / teen | Coordinator | Organizer | Administrator | Child profile |
| --- | --- | --- | --- | --- | --- |
| View directory, phones, dietary data | Yes | Yes | Yes | Yes | Via acting adult |
| Create activity, draft chore, public channel, or shopping request | Yes | Yes | Yes | Yes | No independent login |
| Edit own activity or message | Yes | Yes | Yes | Yes | Via acting adult |
| Plan/publish chores | No | Chore coordinator | Yes | Yes | No |
| Create official/private channels | No | No | No | Yes | No |
| Verify inventory, edit list, export CSV | No | Food coordinator | Yes | Yes | No |
| Manage users or delete participant | No | No | No | Yes | No |
| Switch into child profile | Same-household adult only | Same | Same | Explicit/audited | N/A |

Administrator, Event organizer, Chore coordinator, Food coordinator, Adult participant, and Teen participant are roles. Private-channel membership and object ownership are additional checks, not role substitutes.
