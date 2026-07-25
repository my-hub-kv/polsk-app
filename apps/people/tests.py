from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.events.models import EventYear
from apps.people.forms import ParticipantOnboardingForm
from apps.people.models import EventParticipation, Household, HouseholdMembership, Participant
from apps.people.services import assign_household_membership


class ProfileSwitchingTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="adult", password="safe-test-password")
        self.event = EventYear.objects.create(name="Polsk 2026", year=2026, starts_on="2026-07-01", ends_on="2026-07-05", status="active")
        adult = Participant.objects.create(display_name="Adult", age_group=Participant.AgeGroup.ADULT, login_account=self.user)
        self.adult_participation = EventParticipation.objects.create(event_year=self.event, participant=adult)
        household = Household.objects.create(event_year=self.event, name="Family")
        HouseholdMembership.objects.create(household=household, participation=self.adult_participation)
        self.child = Participant.objects.create(display_name="Child", age_group=Participant.AgeGroup.CHILD)
        child_participation = EventParticipation.objects.create(event_year=self.event, participant=self.child)
        HouseholdMembership.objects.create(household=household, participation=child_participation)
        other = Participant.objects.create(display_name="Other", age_group=Participant.AgeGroup.CHILD)
        self.other_participation = EventParticipation.objects.create(event_year=self.event, participant=other)

    def test_adult_can_switch_to_same_household_child(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(reverse("core:switch_profile"), {"participant": str(self.child.public_id)})
        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(self.client.session["polsk_active_participant_id"], self.child.eventparticipation_set.get().pk)

    def test_cross_household_switch_is_denied(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(reverse("core:switch_profile"), {"participant": str(self.other_participation.participant.public_id)})
        self.assertEqual(response.status_code, 403)

    def test_household_membership_service_rejects_another_event_year(self) -> None:
        other_event = EventYear.objects.create(
            name="Polsk 2027", year=2027, starts_on="2027-07-01", ends_on="2027-07-05"
        )
        other_household = Household.objects.create(event_year=other_event, name="Other family")
        with self.assertRaises(ValidationError):
            assign_household_membership(
                household=other_household,
                participation=self.adult_participation,
            )


class ParticipantOnboardingFormTests(TestCase):
    def test_young_participant_credentials_are_an_explicit_opt_in(self) -> None:
        form = ParticipantOnboardingForm()
        self.assertFalse(form.fields["create_credentials"].initial)
        for age_group in (Participant.AgeGroup.TODDLER, Participant.AgeGroup.CHILD):
            with self.subTest(age_group=age_group):
                form = ParticipantOnboardingForm(
                    {
                        "display_name": "Barn",
                        "age_group": age_group,
                        "household_name": "Familie",
                        "create_credentials": "on",
                    }
                )
                self.assertTrue(form.is_valid())
