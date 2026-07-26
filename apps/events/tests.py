from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.notifications.models import Notification
from apps.people.models import (
    EventParticipation,
    EventRoleAssignment,
    Household,
    HouseholdMembership,
    Participant,
)

from .models import Activity, EventYear
from .services import create_activity, update_activity


@override_settings(STARTIAPP_BRAND_NAME="")
class ActivityScheduleTests(TestCase):
    def setUp(self) -> None:
        self.owner_user = get_user_model().objects.create_user(
            username="owner", password="safe-test-password"
        )
        self.other_user = get_user_model().objects.create_user(
            username="other", password="safe-test-password"
        )
        self.other_event_user = get_user_model().objects.create_user(
            username="other-event", password="safe-test-password"
        )
        self.event = EventYear.objects.create(
            name="Polsk 2026",
            year=2026,
            starts_on=date(2026, 7, 1),
            ends_on=date(2026, 7, 5),
            status=EventYear.Status.ACTIVE,
        )
        self.other_event = EventYear.objects.create(
            name="Polsk 2027",
            year=2027,
            starts_on=date(2027, 7, 1),
            ends_on=date(2027, 7, 5),
            status=EventYear.Status.ACTIVE,
        )
        self.owner_participation = self._participation(
            event_year=self.event,
            user=self.owner_user,
            display_name="Owner",
        )
        self.other_participation = self._participation(
            event_year=self.event,
            user=self.other_user,
            display_name="Other",
        )
        self._participation(
            event_year=self.other_event,
            user=self.other_event_user,
            display_name="Other event",
        )

    def _participation(
        self, *, event_year: EventYear, user, display_name: str
    ) -> EventParticipation:
        participant = Participant.objects.create(
            display_name=display_name,
            age_group=Participant.AgeGroup.ADULT,
            login_account=user,
        )
        return EventParticipation.objects.create(
            event_year=event_year,
            participant=participant,
        )

    def _activity_payload(self, **overrides: str) -> dict[str, str]:
        payload = {
            "title": "Polsk Mester 2026",
            "description": "En fælles konkurrence for alle deltagere.",
            "activity_date": "2026-07-02",
            "start_time": "10:00",
            "end_time": "11:00",
            "is_time_approximate": "on",
        }
        payload.update(overrides)
        return payload

    def test_participant_creates_activity_visible_in_same_event_agendas(self) -> None:
        self.client.force_login(self.owner_user)
        response = self.client.post(reverse("core:activities"), self._activity_payload())

        activity = Activity.objects.get()
        self.assertRedirects(
            response,
            reverse("core:activity_detail", args=[activity.public_id]),
        )
        self.assertEqual(activity.owner_participation, self.owner_participation)
        self.assertEqual(activity.created_by, self.owner_user)
        self.assertEqual(activity.updated_by, self.owner_user)

        activities_page = self.client.get(reverse("core:activities"))
        self.assertContains(activities_page, "data-submit-feedback")
        self.assertContains(activities_page, "Opretter aktivitet")

        self.client.force_login(self.other_user)
        agenda = self.client.get(reverse("core:home"))
        self.assertContains(agenda, "Polsk Mester 2026")
        activities = self.client.get(reverse("core:activities"))
        self.assertContains(activities, "Polsk Mester 2026")

        self.client.force_login(self.other_event_user)
        foreign_agenda = self.client.get(reverse("core:home"))
        self.assertNotContains(foreign_agenda, "Polsk Mester 2026")

    def test_planning_date_outside_event_period_is_allowed(self) -> None:
        self.client.force_login(self.owner_user)

        response = self.client.post(
            reverse("core:activities"),
            self._activity_payload(activity_date="2026-06-20"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Activity.objects.get().activity_date, date(2026, 6, 20))

    def test_creation_notifies_each_same_event_account_once(self) -> None:
        self.client.force_login(self.owner_user)
        self.client.post(reverse("core:activities"), self._activity_payload())

        notifications = Notification.objects.filter(event_year=self.event)
        self.assertEqual(notifications.count(), 2)
        self.assertSetEqual(
            set(notifications.values_list("recipient_id", flat=True)),
            {self.owner_user.pk, self.other_user.pk},
        )
        self.assertTrue(
            all(item.destination_path.startswith("/aktiviteter/") for item in notifications)
        )

    def test_adult_acting_as_household_child_creates_for_the_child_profile(self) -> None:
        household = Household.objects.create(event_year=self.event, name="Familie")
        HouseholdMembership.objects.create(
            household=household,
            participation=self.owner_participation,
        )
        child = Participant.objects.create(
            display_name="Barn",
            age_group=Participant.AgeGroup.CHILD,
        )
        child_participation = EventParticipation.objects.create(
            event_year=self.event,
            participant=child,
        )
        HouseholdMembership.objects.create(
            household=household,
            participation=child_participation,
        )
        self.client.force_login(self.owner_user)
        self.client.post(
            reverse("core:switch_profile"),
            {"participant": str(child.public_id)},
        )

        response = self.client.post(reverse("core:activities"), self._activity_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Activity.objects.get().owner_participation, child_participation)
        self.assertEqual(Activity.objects.get().created_by, self.owner_user)

    def test_owner_can_edit_without_creating_another_notification(self) -> None:
        activity = create_activity(
            event_participation=self.owner_participation,
            acting_user=self.owner_user,
            title="Første titel",
            description="Første beskrivelse",
            activity_date=date(2026, 7, 2),
            start_time=time(10, 0),
            end_time=None,
            is_time_approximate=False,
        )
        self.assertEqual(Notification.objects.count(), 2)
        self.client.force_login(self.owner_user)

        response = self.client.post(
            reverse("core:activity_detail", args=[activity.public_id]),
            self._activity_payload(title="Opdateret titel", end_time=""),
        )

        self.assertRedirects(
            response,
            reverse("core:activity_detail", args=[activity.public_id]),
        )
        activity.refresh_from_db()
        self.assertEqual(activity.title, "Opdateret titel")
        self.assertEqual(activity.updated_by, self.owner_user)
        self.assertEqual(Notification.objects.count(), 2)

    def test_edit_form_renders_existing_date_in_html_date_format(self) -> None:
        activity = create_activity(
            event_participation=self.owner_participation,
            acting_user=self.owner_user,
            title="Datoformat",
            description="Beskrivelse",
            activity_date=date(2026, 7, 2),
            start_time=time(10, 0),
            end_time=None,
            is_time_approximate=False,
        )
        self.client.force_login(self.owner_user)

        response = self.client.get(
            reverse("core:activity_detail", args=[activity.public_id])
        )

        self.assertContains(response, 'name="activity_date" value="2026-07-02"')

    def test_form_rejects_an_end_time_before_the_start_time(self) -> None:
        self.client.force_login(self.owner_user)

        response = self.client.post(
            reverse("core:activities"),
            self._activity_payload(start_time="11:00", end_time="10:00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sluttidspunktet skal ligge efter starttidspunktet.")
        self.assertEqual(Activity.objects.count(), 0)

    def test_non_owner_cannot_edit_and_other_event_cannot_open_activity(self) -> None:
        activity = create_activity(
            event_participation=self.owner_participation,
            acting_user=self.owner_user,
            title="Beskyttet aktivitet",
            description="Beskrivelse",
            activity_date=date(2026, 7, 2),
            start_time=time(10, 0),
            end_time=None,
            is_time_approximate=False,
        )
        self.client.force_login(self.other_user)
        denied = self.client.post(
            reverse("core:activity_detail", args=[activity.public_id]),
            self._activity_payload(),
        )
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.other_event_user)
        hidden = self.client.get(reverse("core:activity_detail", args=[activity.public_id]))
        self.assertEqual(hidden.status_code, 404)

    def test_event_administrator_can_edit_any_activity(self) -> None:
        EventRoleAssignment.objects.create(
            participation=self.other_participation,
            role=EventRoleAssignment.Role.ADMINISTRATOR,
        )
        activity = create_activity(
            event_participation=self.owner_participation,
            acting_user=self.owner_user,
            title="Admin kan ændre",
            description="Beskrivelse",
            activity_date=date(2026, 7, 2),
            start_time=time(10, 0),
            end_time=None,
            is_time_approximate=False,
        )

        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse("core:activity_detail", args=[activity.public_id]),
            self._activity_payload(title="Ændret af administrator", end_time=""),
        )

        self.assertEqual(response.status_code, 302)
        activity.refresh_from_db()
        self.assertEqual(activity.title, "Ændret af administrator")
        self.assertEqual(activity.updated_by, self.other_user)

    def test_model_rejects_invalid_times(self) -> None:
        invalid_time = Activity(
            event_year=self.event,
            title="Ugyldig tid",
            description="Beskrivelse",
            activity_date=date(2026, 7, 2),
            start_time=time(11, 0),
            end_time=time(10, 0),
            owner_participation=self.owner_participation,
        )
        with self.assertRaises(ValidationError):
            invalid_time.full_clean()

    def test_service_requires_an_acting_account_in_the_event_year(self) -> None:
        with self.assertRaises(PermissionDenied):
            update_activity(
                activity=Activity(
                    event_year=self.event,
                    title="Ikke gemt",
                    description="Beskrivelse",
                    activity_date=date(2026, 7, 2),
                    start_time=time(10, 0),
                    owner_participation=self.owner_participation,
                ),
                event_participation=self.owner_participation,
                acting_user=self.other_event_user,
                title="Ikke gemt",
                description="Beskrivelse",
                activity_date=date(2026, 7, 2),
                start_time=time(10, 0),
                end_time=None,
                is_time_approximate=False,
            )
