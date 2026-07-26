from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import LoginThrottle
from apps.accounts.services import LOGIN_ATTEMPT_LIMIT, THROTTLE_RETENTION
from apps.events.models import EventYear
from apps.notifications.models import Notification, NotificationDelivery, NotificationState
from apps.notifications.services import enqueue_notification
from apps.people.models import (
    EventParticipation,
    EventRoleAssignment,
    Household,
    Participant,
)
from apps.people.services import ACTIVE_EVENT_SESSION_KEY, ACTIVE_PARTICIPANT_SESSION_KEY
from django.utils import timezone


class AuthenticationShellTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="participant", password="safe-test-password"
        )

    def test_shell_routes_require_login(self) -> None:
        response = self.client.get(reverse("core:home"))
        self.assertRedirects(response, f"{reverse('core:login')}?next={reverse('core:home')}")

    def test_standard_login_redirects_to_agenda(self) -> None:
        response = self.client.post(
            reverse("core:login"),
            {"username": "participant", "password": "safe-test-password"},
        )
        self.assertRedirects(response, reverse("core:home"))

    def test_normal_participant_sees_only_published_navigation(self) -> None:
        self.client.force_login(self.user)

        agenda_response = self.client.get(reverse("core:home"))
        self.assertEqual(
            [item["key"] for item in agenda_response.context["navigation_items"]],
            ["agenda", "more"],
        )
        self.assertEqual(
            [item["key"] for item in agenda_response.context["navigation_items"] if item["active"]],
            ["agenda"],
        )

        more_response = self.client.get(reverse("core:more"))
        self.assertEqual(
            [item["key"] for item in more_response.context["more_items"]],
            ["directory", "notifications"],
        )

    def test_agenda_has_a_real_empty_state(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Der er endnu ingen aktiviteter i programmet.")
        self.assertNotContains(response, "Denne del er under opbygning.")

    def test_normal_participant_is_redirected_from_unpublished_feature_pages(self) -> None:
        self.client.force_login(self.user)

        for route_name in (
            "chores",
            "messages",
            "food",
            "food_and_shopping",
            "activities",
            "profile",
            "shopping",
            "history",
            "weather",
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"core:{route_name}"))
                self.assertRedirects(response, reverse("core:home"))

    def test_staff_and_superusers_can_review_without_event_administrator_access(
        self,
    ) -> None:
        staff_user = get_user_model().objects.create_user(
            username="staff-reviewer", password="safe-test-password", is_staff=True
        )
        superuser = get_user_model().objects.create_superuser(
            username="superuser-reviewer", password="safe-test-password"
        )

        for reviewer in (staff_user, superuser):
            with self.subTest(reviewer=reviewer.username):
                self.client.force_login(reviewer)

                agenda_response = self.client.get(reverse("core:home"))
                self.assertEqual(
                    [item["key"] for item in agenda_response.context["navigation_items"]],
                    ["agenda", "chores", "messages", "food", "more"],
                )
                more_response = self.client.get(reverse("core:more"))
                self.assertEqual(
                    [item["key"] for item in more_response.context["more_items"]],
                    [
                        "activities",
                        "directory",
                        "notifications",
                        "profile",
                        "shopping",
                        "history",
                        "weather",
                    ],
                )
                for route_name in (
                    "chores",
                    "messages",
                    "food",
                    "activities",
                    "profile",
                    "shopping",
                    "history",
                    "weather",
                ):
                    with self.subTest(route_name=route_name):
                        response = self.client.get(reverse(f"core:{route_name}"))
                        self.assertEqual(response.status_code, 200)

                self.assertRedirects(
                    self.client.get(reverse("core:food_and_shopping")),
                    reverse("core:food"),
                )
                self.assertEqual(
                    self.client.get(reverse("core:administration")).status_code,
                    403,
                )
                self.assertEqual(
                    self.client.post(reverse("core:process_notifications")).status_code,
                    403,
                )

    @override_settings(STARTIAPP_BRAND_NAME="")
    def test_browser_login_omits_optional_starti_assets(self) -> None:
        response = self.client.get(reverse("core:login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "cdn.starti.app")

    @override_settings(STARTIAPP_BRAND_NAME="test-brand")
    def test_authenticated_shell_includes_starti_credit_link(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, 'href="https://starti.app/"')
        self.assertContains(response, "data-startiapp-credit")
        self.assertContains(response, "hidden")
        self.assertContains(response, "Powered by")

    @override_settings(STARTIAPP_BRAND_NAME="")
    def test_authenticated_shell_omits_starti_credit_without_starti(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(reverse("core:home"))

        self.assertNotContains(response, "startiapp-credit")

    def test_login_normalizes_username_case(self) -> None:
        response = self.client.post(
            reverse("core:login"),
            {"username": "PARTICIPANT", "password": "safe-test-password"},
        )
        self.assertRedirects(response, reverse("core:home"))

    def test_repeated_failed_logins_are_rate_limited_in_database(self) -> None:
        for _ in range(LOGIN_ATTEMPT_LIMIT):
            response = self.client.post(
                reverse("core:login"),
                {"username": "participant", "password": "incorrect-password"},
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("core:login"),
            {"username": "participant", "password": "incorrect-password"},
        )
        self.assertEqual(response.status_code, 429)

    def test_logout_requires_post_and_renders_cleanup_page(self) -> None:
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("core:logout")).status_code, 405)
        response = self.client.post(reverse("core:logout"))
        self.assertContains(response, "Du er logget ud")
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(SECURE_HSTS_SECONDS=31_536_000)
    def test_secure_response_includes_hsts_header(self) -> None:
        response = self.client.get(reverse("core:login"), secure=True)
        self.assertEqual(response["Strict-Transport-Security"], "max-age=31536000")


class NotificationViewTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="adult", password="safe-test-password"
        )
        self.event = EventYear.objects.create(
            name="Polsk 2026", year=2026, starts_on="2026-07-01", ends_on="2026-07-05", status="active"
        )
        participant = Participant.objects.create(
            display_name="Adult", age_group=Participant.AgeGroup.ADULT, login_account=self.user
        )
        EventParticipation.objects.create(event_year=self.event, participant=participant)

    def test_login_initializes_active_context_without_get_mutation(self) -> None:
        response = self.client.post(
            reverse("core:login"),
            {"username": "adult", "password": "safe-test-password"},
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertIn(ACTIVE_EVENT_SESSION_KEY, self.client.session)
        self.assertIn(ACTIVE_PARTICIPANT_SESSION_KEY, self.client.session)

        session = self.client.session
        session.pop(ACTIVE_EVENT_SESSION_KEY)
        session.pop(ACTIVE_PARTICIPANT_SESSION_KEY)
        session.save()
        self.client.get(reverse("core:home"))

        self.assertNotIn(ACTIVE_EVENT_SESSION_KEY, self.client.session)
        self.assertNotIn(ACTIVE_PARTICIPANT_SESSION_KEY, self.client.session)

    def test_opening_notification_center_marks_notifications_read_via_post(self) -> None:
        Notification.objects.create(
            event_year=self.event,
            recipient=self.user,
            title="Opdatering",
            body="Der er nyt.",
            destination_path="/",
            idempotency_key="notification-1",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:notifications"))
        self.assertContains(response, "Opdatering")
        self.assertFalse(NotificationState.objects.filter(recipient=self.user, event_year=self.event).exists())
        response = self.client.post(reverse("core:mark_notifications_opened"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(NotificationState.objects.get(recipient=self.user, event_year=self.event).last_opened_at)

    @override_settings(STARTIAPP_BRAND_NAME="test-brand")
    def test_push_control_is_hidden_until_the_native_bridge_confirms_the_app(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(reverse("core:notifications"))

        self.assertContains(response, "data-startiapp-push-control")
        self.assertContains(response, "data-startiapp-push-control hidden")


class ClientErrorTests(TestCase):
    @patch("apps.core.views.logger")
    def test_client_error_is_csrf_protected_and_logs_safe_report(self, logger) -> None:
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("core:login"))
        response = client.post(
            reverse("core:client_error"),
            data='{"kind":"error","message":"Broken","source":"/app.js","line":1,"column":1,"page":"/"}',
            content_type="application/json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 204)
        logger.error.assert_called_once()


@override_settings(
    STARTIAPP_BRAND_NAME="test-brand",
    STARTIAPP_API_KEY="test-key",
    APP_ORIGIN="https://example.test",
    NOTIFICATION_DELIVERY_SYNCHRONOUS=False,
)
class AdministrationTests(TestCase):
    def setUp(self) -> None:
        self.administrator = get_user_model().objects.create_user(
            username="administrator", password="safe-test-password"
        )
        self.event = EventYear.objects.create(
            name="Polsk 2026",
            year=2026,
            starts_on="2026-07-01",
            ends_on="2026-07-05",
            status="active",
        )
        participant = Participant.objects.create(
            display_name="Administrator",
            age_group=Participant.AgeGroup.ADULT,
            login_account=self.administrator,
        )
        self.participation = EventParticipation.objects.create(
            event_year=self.event,
            participant=participant,
        )
        EventRoleAssignment.objects.create(
            participation=self.participation,
            role=EventRoleAssignment.Role.ADMINISTRATOR,
        )

    @patch("apps.notifications.services.send_notification")
    def test_administrator_processes_only_active_event_notifications(
        self, send_notification
    ) -> None:
        active_notification = enqueue_notification(
            event_year_id=self.event.pk,
            recipient_id=self.administrator.pk,
            title="Aktiv",
            body="Indhold",
            destination_path="/",
            idempotency_key="active",
        )
        other_user = get_user_model().objects.create_user(
            username="other-recipient", password="safe-test-password"
        )
        other_event = EventYear.objects.create(
            name="Polsk 2027",
            year=2027,
            starts_on="2027-07-01",
            ends_on="2027-07-05",
            status="active",
        )
        other_participant = Participant.objects.create(
            display_name="Other recipient",
            age_group=Participant.AgeGroup.ADULT,
            login_account=other_user,
        )
        EventParticipation.objects.create(
            event_year=other_event,
            participant=other_participant,
        )
        other_notification = enqueue_notification(
            event_year_id=other_event.pk,
            recipient_id=other_user.pk,
            title="Andet år",
            body="Indhold",
            destination_path="/",
            idempotency_key="other-event",
        )

        self.client.force_login(self.administrator)
        response = self.client.get(reverse("core:more"))
        self.assertContains(response, "Administration")
        response = self.client.get(reverse("core:administration"))
        self.assertContains(response, "Behandl afventende notifikationer")
        response = self.client.post(reverse("core:process_notifications"))

        self.assertRedirects(response, reverse("core:administration"))
        self.assertEqual(send_notification.call_count, 1)
        self.assertEqual(
            active_notification.deliveries.get().status,
            NotificationDelivery.Status.SENT,
        )
        self.assertEqual(
            other_notification.deliveries.get().status,
            NotificationDelivery.Status.PENDING,
        )

    @patch("apps.notifications.services.send_notification")
    def test_administrator_notification_run_is_limited_to_ten(self, send_notification) -> None:
        notifications = [
            enqueue_notification(
                event_year_id=self.event.pk,
                recipient_id=self.administrator.pk,
                title="Aktiv",
                body="Indhold",
                destination_path="/",
                idempotency_key=f"batch-{index}",
            )
            for index in range(11)
        ]

        self.client.force_login(self.administrator)
        response = self.client.post(reverse("core:process_notifications"))

        self.assertRedirects(response, reverse("core:administration"))
        self.assertEqual(send_notification.call_count, 10)
        self.assertEqual(
            NotificationDelivery.objects.filter(
                notification__in=notifications,
                status=NotificationDelivery.Status.PENDING,
            ).count(),
            1,
        )

    def test_administration_denies_non_administrators_and_requires_post(self) -> None:
        non_administrator = get_user_model().objects.create_user(
            username="participant", password="safe-test-password"
        )
        participant = Participant.objects.create(
            display_name="Participant",
            age_group=Participant.AgeGroup.ADULT,
            login_account=non_administrator,
        )
        EventParticipation.objects.create(event_year=self.event, participant=participant)

        self.client.force_login(non_administrator)
        response = self.client.get(reverse("core:more"))
        self.assertNotContains(response, "Administration")
        self.assertEqual(self.client.get(reverse("core:administration")).status_code, 403)
        self.assertEqual(
            self.client.post(reverse("core:process_notifications")).status_code,
            403,
        )
        self.client.force_login(self.administrator)
        self.assertEqual(
            self.client.get(reverse("core:process_notifications")).status_code,
            405,
        )

    def test_administrator_can_remove_only_expired_throttle_state(self) -> None:
        expired = LoginThrottle.objects.create(
            key_digest="expired",
            window_started_at=timezone.now(),
        )
        fresh = LoginThrottle.objects.create(
            key_digest="fresh",
            window_started_at=timezone.now(),
        )
        LoginThrottle.objects.filter(pk=expired.pk).update(
            updated_at=timezone.now() - THROTTLE_RETENTION - timedelta(seconds=1)
        )

        self.client.force_login(self.administrator)
        response = self.client.post(reverse("core:cleanup_login_protection"))

        self.assertRedirects(response, reverse("core:administration"))
        self.assertFalse(LoginThrottle.objects.filter(pk=expired.pk).exists())
        self.assertTrue(LoginThrottle.objects.filter(pk=fresh.pk).exists())

    def test_administrator_actions_require_csrf(self) -> None:
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.administrator)
        client.get(reverse("core:administration"))

        response = client.post(reverse("core:process_notifications"))

        self.assertEqual(response.status_code, 403)
