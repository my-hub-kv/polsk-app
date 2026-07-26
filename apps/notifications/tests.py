from datetime import timedelta
from queue import Queue
from threading import Barrier, Thread
from urllib.error import URLError
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from apps.events.models import EventYear
from apps.notifications.models import Notification, NotificationDelivery
from apps.notifications.providers.starti_push import (
    StartiPushError,
    StartiPushUncertainDeliveryError,
    send_notification,
)
from apps.notifications import services
from apps.notifications.services import (
    DELIVERY_LEASE,
    DeliveryDispatchResult,
    claim_due_deliveries,
    enqueue_notification,
    enqueue_notifications,
)
from apps.people.models import EventParticipation, Participant


@override_settings(
    STARTIAPP_BRAND_NAME="test-brand",
    STARTIAPP_API_KEY="test-key",
    APP_ORIGIN="https://example.test",
    NOTIFICATION_DELIVERY_SYNCHRONOUS=True,
    NOTIFICATION_DELIVERY_REQUEST_TRIGGERED=False,
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

    @patch("apps.notifications.services.send_notification")
    def test_delivery_is_idempotent(self, send_notification) -> None:
        notification = enqueue_notification(event_year_id=self.event.pk, recipient_id=self.user.pk, title="Nyt", body="Indhold", destination_path="/", idempotency_key="unique")
        enqueue_notification(event_year_id=self.event.pk, recipient_id=self.user.pk, title="Nyt", body="Indhold", destination_path="/", idempotency_key="unique")
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        call_command("deliver_notifications")
        self.assertEqual(send_notification.call_count, 1)
        self.assertEqual(notification.deliveries.get().status, NotificationDelivery.Status.SENT)
        self.assertEqual(send_notification.call_args.kwargs["title"], "Opdatering i Polsk App")

    @patch("apps.notifications.services.send_notification")
    def test_new_delivery_is_sent_after_the_transaction_commits(self, send_notification) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            notification = enqueue_notification(
                event_year_id=self.event.pk,
                recipient_id=self.user.pk,
                title="Nyt",
                body="Indhold",
                destination_path="/",
                idempotency_key="synchronous",
            )

        delivery = notification.deliveries.get()
        self.assertEqual(send_notification.call_count, 1)
        self.assertEqual(delivery.status, NotificationDelivery.Status.SENT)

    @override_settings(
        NOTIFICATION_DELIVERY_SYNCHRONOUS=False,
        NOTIFICATION_DELIVERY_REQUEST_TRIGGERED=False,
    )
    @patch("apps.notifications.services.send_notification")
    def test_synchronous_delivery_can_be_disabled_for_a_future_dispatcher(
        self, send_notification
    ) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            notification = enqueue_notification(
                event_year_id=self.event.pk,
                recipient_id=self.user.pk,
                title="Nyt",
                body="Indhold",
                destination_path="/",
                idempotency_key="scheduled",
            )

        self.assertEqual(send_notification.call_count, 0)
        self.assertEqual(notification.deliveries.get().status, NotificationDelivery.Status.PENDING)

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

    @patch("apps.notifications.services.send_notification")
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


@override_settings(
    STARTIAPP_BRAND_NAME="test-brand",
    STARTIAPP_API_KEY="test-key",
    APP_ORIGIN="https://example.test",
    NOTIFICATION_DELIVERY_SYNCHRONOUS=False,
    NOTIFICATION_DELIVERY_REQUEST_TRIGGERED=True,
)
class RequestTriggeredDeliveryTests(TestCase):
    def setUp(self) -> None:
        self.event = EventYear.objects.create(
            name="Polsk 2026",
            year=2026,
            starts_on="2026-07-01",
            ends_on="2026-07-05",
        )
        self.user = self._create_recipient(0)
        self._reset_dispatcher_state()

    def tearDown(self) -> None:
        self._reset_dispatcher_state()

    def _reset_dispatcher_state(self) -> None:
        with services._request_dispatch_state_lock:
            services._request_dispatch_running = False
            services._request_dispatch_requested = False

    def _create_recipient(self, number: int):
        user = get_user_model().objects.create(username=f"recipient-{number}")
        participant = Participant.objects.create(
            display_name=f"Recipient {number}",
            age_group=Participant.AgeGroup.ADULT,
            login_account=user,
        )
        EventParticipation.objects.create(event_year=self.event, participant=participant)
        return user

    def _enqueue(self, *, recipient, key: str) -> Notification:
        return enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=recipient.pk,
            title="Nyt",
            body="Indhold",
            destination_path="/",
            idempotency_key=key,
        )

    @patch("apps.notifications.services.Thread")
    @patch("apps.notifications.services.send_notification")
    def test_committed_delivery_starts_background_dispatch_without_push_in_request(
        self,
        send_notification,
        thread,
    ) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            self._enqueue(recipient=self.user, key="request-triggered")

        thread.assert_called_once()
        thread.return_value.start.assert_called_once()
        send_notification.assert_not_called()

    @override_settings(STARTIAPP_BRAND_NAME="")
    @patch("apps.notifications.services.Thread")
    def test_browser_only_notification_does_not_start_background_dispatch(self, thread) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            self._enqueue(recipient=self.user, key="browser-only")

        thread.assert_not_called()
        self.assertEqual(NotificationDelivery.objects.count(), 0)

    @patch("apps.notifications.services.Thread")
    def test_batch_enqueue_creates_45_notifications_and_one_dispatch_trigger(
        self,
        thread,
    ) -> None:
        recipients = [self.user] + [
            self._create_recipient(number) for number in range(1, 45)
        ]

        with self.captureOnCommitCallbacks(execute=True):
            notifications = enqueue_notifications(
                event_year_id=self.event.pk,
                recipient_ids=[recipient.pk for recipient in recipients],
                title="Fælles opdatering",
                body="Indhold",
                destination_path="/",
                idempotency_key="batch-45",
            )

        self.assertEqual(len(notifications), 45)
        self.assertEqual(Notification.objects.count(), 45)
        self.assertEqual(NotificationDelivery.objects.count(), 45)
        thread.assert_called_once()

    def test_batch_enqueue_rejects_recipient_from_another_event_year(self) -> None:
        other_event = EventYear.objects.create(
            name="Polsk 2027",
            year=2027,
            starts_on="2027-07-01",
            ends_on="2027-07-05",
        )
        other_user = get_user_model().objects.create(username="other-event-user")
        other_participant = Participant.objects.create(
            display_name="Other event",
            age_group=Participant.AgeGroup.ADULT,
            login_account=other_user,
        )
        EventParticipation.objects.create(
            event_year=other_event,
            participant=other_participant,
        )

        with self.assertRaises(ValueError):
            enqueue_notifications(
                event_year_id=self.event.pk,
                recipient_ids=[self.user.pk, other_user.pk],
                title="Fælles opdatering",
                body="Indhold",
                destination_path="/",
                idempotency_key="wrong-event",
            )

    @patch("apps.notifications.services.Thread")
    def test_batch_enqueue_is_idempotent(self, thread) -> None:
        kwargs = {
            "event_year_id": self.event.pk,
            "recipient_ids": [self.user.pk],
            "title": "Fælles opdatering",
            "body": "Indhold",
            "destination_path": "/",
            "idempotency_key": "batch-idempotent",
        }

        with self.captureOnCommitCallbacks(execute=True):
            created = enqueue_notifications(**kwargs)
        with self.captureOnCommitCallbacks(execute=True):
            repeated = enqueue_notifications(**kwargs)

        self.assertEqual(len(created), 1)
        self.assertEqual(repeated, [])
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        thread.assert_called_once()

    @patch("apps.notifications.services.send_notification")
    def test_dispatcher_drains_all_45_due_deliveries(self, send_notification) -> None:
        recipients = [self.user] + [
            self._create_recipient(number) for number in range(1, 45)
        ]
        for number, recipient in enumerate(recipients):
            self._enqueue(recipient=recipient, key=f"forty-five-{number}")

        services._run_request_triggered_delivery_dispatcher()

        self.assertEqual(send_notification.call_count, 45)
        self.assertEqual(
            NotificationDelivery.objects.filter(
                status=NotificationDelivery.Status.SENT
            ).count(),
            45,
        )

    @patch("apps.notifications.services.send_notification")
    def test_dispatcher_drains_more_than_one_claim_batch(self, send_notification) -> None:
        recipients = [self.user] + [
            self._create_recipient(number) for number in range(1, 51)
        ]
        for number, recipient in enumerate(recipients):
            self._enqueue(recipient=recipient, key=f"multi-batch-{number}")

        services._run_request_triggered_delivery_dispatcher()

        self.assertEqual(send_notification.call_count, 51)
        self.assertEqual(
            NotificationDelivery.objects.filter(
                status=NotificationDelivery.Status.SENT
            ).count(),
            51,
        )

    @patch("apps.notifications.services.Thread")
    def test_active_dispatcher_coalesces_another_request_into_a_follow_up_pass(
        self,
        thread,
    ) -> None:
        with services._request_dispatch_state_lock:
            services._request_dispatch_running = True
        calls = 0

        def request_again_then_return_empty(
            **kwargs: object,
        ) -> DeliveryDispatchResult:
            nonlocal calls
            calls += 1
            if calls == 1:
                services.request_notification_delivery_dispatch()
            return DeliveryDispatchResult(processed=0, sent=0, retrying=0, failed=0)

        with patch(
            "apps.notifications.services.deliver_due_notifications",
            side_effect=request_again_then_return_empty,
        ) as deliver_due_notifications:
            services._run_request_triggered_delivery_dispatcher()

        thread.assert_not_called()
        self.assertEqual(deliver_due_notifications.call_count, 2)

    @patch("apps.notifications.services.logger")
    @patch(
        "apps.notifications.services.deliver_due_notifications",
        side_effect=RuntimeError("dispatcher failure"),
    )
    def test_dispatcher_failure_releases_local_dispatch_state(
        self,
        deliver_due_notifications,
        logger,
    ) -> None:
        with services._request_dispatch_state_lock:
            services._request_dispatch_running = True

        services._run_request_triggered_delivery_dispatcher()

        logger.exception.assert_called_once_with(
            "request_triggered_notification_dispatcher_failed"
        )
        with services._request_dispatch_state_lock:
            self.assertFalse(services._request_dispatch_running)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row-conflict handling")
@override_settings(
    STARTIAPP_BRAND_NAME="test-brand",
    STARTIAPP_API_KEY="test-key",
    APP_ORIGIN="https://example.test",
    NOTIFICATION_DELIVERY_SYNCHRONOUS=False,
    NOTIFICATION_DELIVERY_REQUEST_TRIGGERED=False,
)
class NotificationBatchConcurrencyTests(TransactionTestCase):
    """Prove batch idempotency when two database connections race."""

    def setUp(self) -> None:
        self.event = EventYear.objects.create(
            name="Polsk 2026",
            year=2026,
            starts_on="2026-07-01",
            ends_on="2026-07-05",
        )
        self.user = get_user_model().objects.create(username="race-recipient")
        participant = Participant.objects.create(
            display_name="Race recipient",
            age_group=Participant.AgeGroup.ADULT,
            login_account=self.user,
        )
        EventParticipation.objects.create(event_year=self.event, participant=participant)

    def test_concurrent_batch_enqueue_keeps_one_notification(self) -> None:
        insert_barrier = Barrier(2)
        outcomes: Queue[object] = Queue()
        original_bulk_create = Notification.objects.bulk_create

        def synchronize_notification_insert(*args: object, **kwargs: object):
            insert_barrier.wait(timeout=10)
            return original_bulk_create(*args, **kwargs)

        def enqueue() -> None:
            close_old_connections()
            try:
                enqueue_notifications(
                    event_year_id=self.event.pk,
                    recipient_ids=[self.user.pk],
                    title="Samtidig opdatering",
                    body="Indhold",
                    destination_path="/",
                    idempotency_key="concurrent-batch",
                )
            except Exception as error:  # Report thread failures to the test process.
                outcomes.put(error)
            else:
                outcomes.put("ok")
            finally:
                close_old_connections()

        with patch.object(
            Notification.objects,
            "bulk_create",
            side_effect=synchronize_notification_insert,
        ):
            first = Thread(target=enqueue)
            second = Thread(target=enqueue)
            first.start()
            second.start()
            first.join(timeout=15)
            second.join(timeout=15)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual([outcomes.get_nowait(), outcomes.get_nowait()], ["ok", "ok"])
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)
