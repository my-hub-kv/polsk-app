from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, InvitationThrottle, LoginThrottle
from apps.accounts.services import (
    INVITATION_ATTEMPT_LIMIT,
    THROTTLE_RETENTION,
    create_invitation,
)
from apps.events.models import EventYear
from apps.people.models import EventParticipation, Participant


class InvitationTests(TestCase):
    def setUp(self) -> None:
        event = EventYear.objects.create(
            name="Polsk 2026", year=2026, starts_on="2026-07-01", ends_on="2026-07-05"
        )
        participant = Participant.objects.create(
            display_name="Barn", age_group=Participant.AgeGroup.CHILD
        )
        self.participation = EventParticipation.objects.create(event_year=event, participant=participant)

    def test_valid_invitation_creates_account_once(self) -> None:
        invitation, token = create_invitation(
            self.participation.pk,
            Invitation.Purpose.CREATE_ACCOUNT,
            timezone.now() + timedelta(hours=1),
        )
        response = self.client.post(
            reverse("accounts:redeem", args=[token]),
            {"username": "new-user", "password": "safe-test-password", "password_confirmation": "safe-test-password"},
        )
        self.assertRedirects(response, reverse("core:login"))
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.used_at)
        self.participation.participant.refresh_from_db()
        self.assertIsNotNone(self.participation.participant.login_account)

    def test_used_or_unknown_invitation_has_generic_failure(self) -> None:
        response = self.client.post(
            reverse("accounts:redeem", args=["unknown"]),
            {"username": "new-user", "password": "safe-test-password", "password_confirmation": "safe-test-password"},
        )
        self.assertContains(response, "Linket kan ikke bruges")

    def test_replacement_invitation_revokes_without_marking_original_as_used(self) -> None:
        invitation, _ = create_invitation(
            self.participation.pk,
            Invitation.Purpose.CREATE_ACCOUNT,
            timezone.now() + timedelta(hours=1),
        )
        replacement, _ = create_invitation(
            self.participation.pk,
            Invitation.Purpose.CREATE_ACCOUNT,
            timezone.now() + timedelta(hours=1),
        )
        invitation.refresh_from_db()
        self.assertIsNone(invitation.used_at)
        self.assertIsNotNone(invitation.revoked_at)
        self.assertIsNone(replacement.revoked_at)

    def test_invalid_invitation_attempts_are_rate_limited(self) -> None:
        url = reverse("accounts:redeem", args=["unknown"])
        payload = {
            "username": "new-user",
            "password": "safe-test-password",
            "password_confirmation": "safe-test-password",
        }
        for _ in range(INVITATION_ATTEMPT_LIMIT):
            self.assertEqual(self.client.post(url, payload).status_code, 200)
        self.assertEqual(self.client.post(url, payload).status_code, 200)
        state = InvitationThrottle.objects.get()
        self.assertEqual(state.failures, INVITATION_ATTEMPT_LIMIT)
        self.assertIsNotNone(state.locked_until)

    def test_redemption_response_disables_referrer_forwarding(self) -> None:
        response = self.client.get(reverse("accounts:redeem", args=["unknown"]))
        self.assertEqual(response["Referrer-Policy"], "no-referrer")

    def test_cleanup_command_removes_only_expired_throttle_fingerprints(self) -> None:
        expired_login = LoginThrottle.objects.create(
            key_digest="expired-login",
            window_started_at=timezone.now(),
        )
        expired_invitation = InvitationThrottle.objects.create(
            key_digest="expired-invitation",
            window_started_at=timezone.now(),
        )
        fresh_login = LoginThrottle.objects.create(
            key_digest="fresh-login",
            window_started_at=timezone.now(),
        )
        expired_at = timezone.now() - THROTTLE_RETENTION - timedelta(seconds=1)
        LoginThrottle.objects.filter(pk=expired_login.pk).update(updated_at=expired_at)
        InvitationThrottle.objects.filter(pk=expired_invitation.pk).update(
            updated_at=expired_at
        )

        from django.core.management import call_command

        call_command("cleanup_throttle_state")

        self.assertFalse(LoginThrottle.objects.filter(pk=expired_login.pk).exists())
        self.assertFalse(
            InvitationThrottle.objects.filter(pk=expired_invitation.pk).exists()
        )
        self.assertTrue(LoginThrottle.objects.filter(pk=fresh_login.pk).exists())


class UserManagerTests(TestCase):
    def test_multiple_accounts_can_omit_email(self) -> None:
        user_model = get_user_model()
        first = user_model.objects.create_user(
            username="without-email-one",
            password="safe-test-password",
        )
        second = user_model.objects.create_user(
            username="without-email-two",
            password="safe-test-password",
        )

        self.assertIsNone(first.email)
        self.assertIsNone(second.email)
