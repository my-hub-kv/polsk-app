# Polsk App documentation

This documentation is the durable, reviewable product memory for humans and Codex. Read the product, domain, architecture, and active specification documents relevant to a change before implementing it. Confirmed product rules and accepted ADRs are authoritative; unresolved choices belong in [product/open-questions.md](product/open-questions.md).

Private deployment, recovery, and provider-account procedures stay outside this public repository. Raw conversations and private reasoning are not source-of-truth documents.

| Need | Read |
| --- | --- |
| Understand the product | [Product vision](product/vision.md) and [confirmed decisions](product/confirmed-decisions.md) |
| Implement a feature | Relevant [user story](product/user-stories/), domain document, and active specification |
| Change models | [Conceptual model](architecture/conceptual-data-model.md), domain document, and [migration guide](development/migrations.md) |
| Change permissions | [Roles and permissions](product/roles-and-permissions.md) and [authorization model](architecture/authorization-model.md) |
| Understand a technical decision | [ADRs](architecture/decisions/) |
| Review security | [Development security](development/security.md) and the repository security skill |
| Contribute | [Contributing](../CONTRIBUTING.md) and [pull-request process](development/pull-request-process.md) |

## Areas

- **Product:** [vision](product/vision.md), [confirmed decisions](product/confirmed-decisions.md), [non-goals](product/non-goals.md), [open questions](product/open-questions.md), [roles](product/roles-and-permissions.md), [experience](product/user-experience.md), [glossary](product/glossary.md), and user stories for [accounts](product/user-stories/accounts-and-households.md), [agenda](product/user-stories/agenda-and-calendar.md), [chores](product/user-stories/chores.md), [communication](product/user-stories/communication.md), [food/shopping](product/user-stories/food-and-shopping.md), [weather](product/user-stories/weather.md), [notifications](product/user-stories/notifications.md), and [administration](product/user-stories/administration.md).
- **Domain:** [event years](domain/event-years.md), [participants and households](domain/participants-and-households.md), [chore planning](domain/chore-planning.md), [transfers](domain/chore-transfers.md), [channels](domain/channels-and-messages.md), [inventory](domain/inventory-and-reservations.md), [shopping](domain/shopping-lists.md), [weather](domain/weather-history.md), and [deletion](domain/deletion-and-history.md).
- **Architecture:** [overview](architecture/overview.md), [boundaries](architecture/application-boundaries.md), [conceptual model](architecture/conceptual-data-model.md), [authorization](architecture/authorization-model.md), [notifications](architecture/notifications.md), and ADRs for [monolith](architecture/decisions/0001-modular-django-monolith.md), [frontend](architecture/decisions/0002-server-rendered-frontend.md), [identity](architecture/decisions/0003-person-and-login-separation.md), [configuration](architecture/decisions/0004-provider-neutral-configuration.md), [services](architecture/decisions/0005-explicit-domain-services.md), and [planning](architecture/decisions/0006-explainable-planning-rules.md).
- **Development:** [setup](development/setup.md), [standards](development/coding-standards.md), [testing](development/testing.md), [migrations](development/migrations.md), [security](development/security.md), and [pull requests](development/pull-request-process.md).
- **Specifications:** [specification process](specifications/README.md), [active](specifications/active/), and [completed](specifications/completed/).
