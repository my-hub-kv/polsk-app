"""Deliver a finite batch of queued notifications."""

from django.core.management.base import BaseCommand

from apps.notifications.services import deliver_due_notifications


class Command(BaseCommand):
    help = "Deliver a bounded batch of queued Starti notifications."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        result = deliver_due_notifications(limit=options["limit"])
        self.stdout.write(f"Processed {result.processed} notification deliveries.")
