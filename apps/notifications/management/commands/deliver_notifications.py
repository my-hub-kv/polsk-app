"""Deliver a finite batch of queued notifications."""

from django.core.management.base import BaseCommand

from apps.notifications.providers.starti_push import (
    StartiPushError,
    StartiPushUncertainDeliveryError,
    send_notification,
)
from apps.notifications.services import (
    claim_due_deliveries,
    mark_delivery_uncertain,
    mark_delivery_failed,
    mark_delivery_sent,
    push_copy,
    unread_count,
)


class Command(BaseCommand):
    help = "Deliver a bounded batch of queued Starti notifications."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        deliveries = claim_due_deliveries(limit=options["limit"])
        for delivery in deliveries:
            notification = delivery.notification
            try:
                title, body = push_copy()
                send_notification(
                    user=notification.recipient,
                    title=title,
                    body=body,
                    open_to_url=notification.destination_path,
                    badge_count=unread_count(
                        recipient_id=notification.recipient_id,
                        event_year_id=notification.event_year_id,
                    ),
                )
            except StartiPushUncertainDeliveryError as error:
                mark_delivery_uncertain(delivery, str(error))
            except StartiPushError as error:
                mark_delivery_failed(delivery, str(error))
            else:
                mark_delivery_sent(delivery)
        self.stdout.write(f"Processed {len(deliveries)} notification deliveries.")
