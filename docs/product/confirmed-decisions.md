# Confirmed decisions

## Scope and identity

- Polsk App serves one recurring event only; it is not multi-tenant SaaS. Event years are separate, browsable historical records and selected templates may be copied forward without blindly copying quantities.
- Access is invitation-only, production data is private, and the source is AGPL-3.0. The UI is Danish; technical material is English. Polsk is unrelated to Poland and must not use Polish national imagery.
- Polsk uses its supplied campfire artwork as the product mark. Its participant UI has an accessible, blue-led light and dark theme with a warm orange accent; browser preference is the default and a participant may choose a presentation-only override. The mark is not national imagery.

## Participants, roles, and history

- Every adult and child has a historical participant profile; login credentials are separate, use username/password, and email is optional for invitation or recovery. Administrators can issue single-use credential-reset links; public registration is unavailable.
- Adults may act as children in the same household only. Administrators cannot switch into other participant profiles. Exact birth dates/years are not stored; age groups are 0–3, 4–11, 12–18, and adult.
- The participant directory is visible to participants. Optional phone numbers and dietary/allergy information are visible to all participants after a clear visibility warning.
- Initial roles are Administrator, Event organizer, Chore coordinator, Food coordinator, Adult participant, and Teen participant; people may hold multiple event-year roles.
- Event years have their own dates, venue/address, coordinates, and timezone. Historical records remain available; deleting a participant removes sensitive profile data while preserving necessary shared history with explicit anonymisation or nullable references.

## Agenda and chores

- The agenda is the default screen: vertically scrollable, near today on opening, with a go-to-today action, day-responsible person, and Mine/Household/All filters. It combines activities and published chores; exact and approximate periods are supported.
- All participants may create activities; administrators manage all activities. Activity dates may be before or after the event period for planning. The implemented first slice shares every new activity with the active event year immediately, records its active-profile owner and acting account, and sends one in-app notification per participating login account on creation only. External calendar export is not required. Calendar reminders are approximately 15 minutes before an activity and remain planned.
- Chores are assigned to individuals, have exactly one `A` task-responsible person, and use `X` adult, `B` child, and dinner-only `BA` child-food-responsible roles. `A` ensures the chore happens and coordinates help; `BA` ensures suitable food is available for children. Dinner `A` and `BA` must differ. Each assignment counts as one chore; there is no completion workflow.
- Planning preserves sticky/locked assignments, respects attendance, daily availability, workload, eligibility, and household child/adult pairing. After minimum staffing is satisfied, the planner may add eligible participants above the minimum to improve fairness, up to an optional maximum; it must still avoid unnecessary overstaffing. Plans are Draft, Published, or Archived; participants see only Published plans. Day responsibility is derived from the next day’s dinner `A` and does not add a chore count.
- A transfer requires recipient acceptance, is revalidated server-side, is auditable, and notifies only relevant people. Administrators may override assignments.

## Communication, food, shopping, and weather

- Communication is channel-based: public channels are discoverable and opt-in for notifications; official channels are administrator-designated, all participants are subscribed by default, and participants cannot mute them; private channels are administrator-created and member-only. Every active event year has at least one official all-participants channel. No direct messages or read acknowledgements in v1.
- Messages can be edited/deleted by their owner; administrators may delete any message. Historical messages remain unless deleted by policy.
- Food distinguishes basic generally available stock from dinner/purpose-reserved food. Missing reports are visible immediately and coordinators can verify, correct, or reverse them. Exact consumption logging and automatic ordering are out of scope.
- Any participant may request shopping; a coordinator may add a request to a list, dismiss it, edit its text, quantity, or unit, and merge duplicates. Shopping is planned per delivery day or delivery period so each purchase covers the next period rather than the entire event. Explainable, editable suggestions use stock, reservations, attendance, historical context, and weather. When observations are available, suggestions may consider how verified or estimated stock changed over earlier days of the current event; this remains approximate and never requires recording every use. Lists have operational states and safe CSV exports with history/change-after-export indication.
- Forecast snapshots and observed weather are stored separately per event-year location. Weather informs planning but never makes an ordering decision.

## Notifications and retention

- In-app notifications and provider-neutral push are supported. The notification badge clears when a participant opens the notification center. Public-channel notifications default off; official channels cannot be muted; draft chore-plan changes never notify participants. In-app enqueueing is idempotent per recipient and event year; push delivery is best-effort after commit in a request-triggered background thread by default, while the inbox remains authoritative. The thread drains all due work in safe claims, can be interrupted by the web process, and may later run alongside a scheduler. Administrators have event-scoped in-app controls for pending notification delivery and expired throttle cleanup. Ambiguous external push transport failures are not retried.
- Event history is retained. Participant deletion removes credentials, contact and dietary data, preferences, subscriptions, and household access without broadly cascading shared operational history.
