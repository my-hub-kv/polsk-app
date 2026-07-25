from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.services import LOGIN_ATTEMPT_LIMIT
from apps.events.models import EventYear
from apps.notifications.models import Notification, NotificationState
from apps.people.models import EventParticipation, Household, HouseholdMembership, Participant
from apps.people.services import ACTIVE_EVENT_SESSION_KEY, ACTIVE_PARTICIPANT_SESSION_KEY


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

    @override_settings(STARTIAPP_BRAND_NAME="")
    def test_browser_login_omits_optional_starti_assets(self) -> None:
        response = self.client.get(reverse("core:login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "cdn.starti.app")

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
