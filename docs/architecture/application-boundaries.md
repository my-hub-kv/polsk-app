# Application boundaries

Conceptual future Django apps are `core` (presentation/health), `accounts` (auth/invitations), `events`, `people`, `schedule`, `chores`, `messaging`, `food`, `shopping`, `weather`, `notifications`, and `audit`. They are not immediate scaffolding requirements.

Views call their own domain services; cross-domain mutation is not performed directly from views. Illustrative services include `people.services.switch_active_participant`, `chores.services.generate_draft_plan`, `chores.services.publish_plan`, `chores.services.request_transfer`, `chores.services.accept_transfer`, `food.services.report_item_missing`, `food.services.verify_stock`, `shopping.services.build_suggestions`, `shopping.services.export_list_csv`, and `notifications.services.enqueue_notification`.

Dependencies flow from presentation to domain operations and persistence; external adapters sit behind domain-facing interfaces. Avoid circular imports and generic shared business utilities.
