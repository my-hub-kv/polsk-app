from datetime import timedelta
from urllib.error import URLError
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.events.models import EventYear
from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.providers.starti_push import (
    StartiPushError,
    StartiPushUncertainDeliveryError,
    send_notification,
)
from apps.notifications.services import DELIVERY_LEASE, claim_due_deliveries, enqueue_notification
from apps.people.models import EventParticipation, Participant


@override_settings(
    STARTIAPP_BRAND_NAME="test-brand",
    STARTIAPP_API_KEY="test-key",
    APP_ORIGIN="https://example.test",
)
class DeliveryTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="recipient", password="safe-test-password")
        self.event = EventYear.objects.create(name="Polsk 2026", year=2026, starts_on="2026-07-01", ends_on="2026-07-05")
        participant = Participant.objects.create(
            display_name="Recipient",
            age_group=Participant.AgeGroup.ADULT,
            login_account=self.user,
        )
        EventParticipation.objects.create(event_year=self.event, participant=participant)

    @patch("apps.notifications.management.commands.deliver_notifications.send_notification")
    def test_delivery_is_idempotent(self, send_notification) -> None:
        notification = enqueue_notification(event_year_id=self.event.pk, recipient_id=self.user.pk, title="Nyt", body="Indhold", destination_path="/", idempotency_key="unique")
        enqueue_notification(event_year_id=self.event.pk, recipient_id=self.user.pk, title="Nyt", body="Indhold", destination_path="/", idempotency_key="unique")
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        call_command("deliver_notifications")
        self.assertEqual(send_notification.call_count, 1)
        self.assertEqual(notification.deliveries.get().status, NotificationDelivery.Status.SENT)
        self.assertEqual(send_notification.call_args.kwargs["title"], "Opdatering i Polsk App")

    def test_idempotency_key_is_scoped_to_recipient_and_event_year(self) -> None:
        second_user = get_user_model().objects.create_user(
            username="second-recipient", password="safe-test-password"
        )
        second_participant = Participant.objects.create(
            display_name="Second recipient",
            age_group=Participant.AgeGroup.ADULT,
            login_account=second_user,
        )
        EventParticipation.objects.create(
            event_year=self.event,
            participant=second_participant,
        )

        first = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=self.user.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key="same-domain-key",
        )
        second = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=second_user.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key="same-domain-key",
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Notification.objects.count(), 2)

    @patch("apps.notifications.management.commands.deliver_notifications.send_notification")
    def test_uncertain_delivery_is_not_retried(self, send_notification) -> None:
        notification = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=self.user.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key="uncertain-transport",
        )
        send_notification.side_effect = StartiPushUncertainDeliveryError(
            "transport_uncertain"
        )

        call_command("deliver_notifications")

        delivery = notification.deliveries.get()
        self.assertEqual(delivery.status, NotificationDelivery.Status.FAILED)
        self.assertEqual(delivery.attempts, 1)

    @override_settings(STARTIAPP_API_KEY="test-key", APP_ORIGIN="https://example.test")
    @patch("apps.notifications.providers.starti_push.urlopen", side_effect=URLError("offline"))
    def test_starti_transport_failure_is_classified_as_uncertain(self, urlopen) -> None:
        with self.assertRaises(StartiPushUncertainDeliveryError):
            send_notification(
                user=self.user,
                title="Opdatering i Polsk App",
                body="Åbn appen for at se nyt.",
                open_to_url="/notifikationer/",
                badge_count=0,
            )

    def test_stale_processing_delivery_is_reclaimed(self) -> None:
        notification = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=self.user.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key="stale",
        )
        delivery = notification.deliveries.get()
        delivery.status = NotificationDelivery.Status.PROCESSING
        delivery.claimed_at = timezone.now() - DELIVERY_LEASE - timedelta(minutes=1)
        delivery.attempts = 1
        delivery.save(update_fields=["status", "claimed_at", "attempts"])
        claimed = claim_due_deliveries()
        self.assertEqual([item.pk for item in claimed], [delivery.pk])
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, NotificationDelivery.Status.PROCESSING)
        self.assertEqual(delivery.attempts, 2)

    @override_settings(STARTIAPP_BRAND_NAME="")
    def test_in_app_notification_does_not_queue_push_without_starti(self) -> None:
        notification = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=self.user.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key="browser-only",
        )
        self.assertEqual(NotificationDelivery.objects.count(), 0)
        self.assertEqual(notification.recipient, self.user)

    @override_settings(STARTIAPP_API_KEY="test-key", APP_ORIGIN="https://example.test")
    @patch("apps.notifications.providers.starti_push.urlopen")
    def test_starti_adapter_uses_internal_url_and_timeout(self, urlopen) -> None:
        response = MagicMock(status=202)
        urlopen.return_value.__enter__.return_value = response
        send_notification(
            user=self.user,
            title="Opdatering i Polsk App",
            body="Åbn appen for at se nyt.",
            open_to_url="/notifikationer/",
            badge_count=3,
        )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.starti.app/v1/push-notifications/send")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)
        self.assertNotIn("test-key", request.data.decode())

    @override_settings(STARTIAPP_API_KEY="test-key", APP_ORIGIN="https://example.test")
    def test_starti_adapter_rejects_non_internal_destination(self) -> None:
        with self.assertRaises(StartiPushError):
            send_notification(
                user=self.user,
                title="Title",
                body="Body",
                open_to_url="https://other.test/",
                badge_count=0,
            )
