"""Create the first event and bind an existing superuser to it."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.events.models import EventYear
from apps.people.models import EventParticipation, EventRoleAssignment, Participant


class Command(BaseCommand):
    help = "Bind an existing superuser to the initial Polsk event as administrator."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--year", required=True, type=int)
        parser.add_argument("--starts-on", required=True)
        parser.add_argument("--ends-on", required=True)
        parser.add_argument("--display-name", required=True)

    def handle(self, *args, **options):
        user = get_user_model().objects.filter(username=options["username"], is_superuser=True).first()
        if user is None:
            raise CommandError("The supplied username is not an existing superuser.")
        with transaction.atomic():
            event = EventYear.objects.create(
                name=options["name"],
                year=options["year"],
                starts_on=options["starts_on"],
                ends_on=options["ends_on"],
                status=EventYear.Status.ACTIVE,
            )
            participant = Participant.objects.create(
                display_name=options["display_name"],
                age_group=Participant.AgeGroup.ADULT,
                login_account=user,
            )
            participation = EventParticipation.objects.create(event_year=event, participant=participant)
            EventRoleAssignment.objects.create(
                participation=participation,
                role=EventRoleAssignment.Role.ADMINISTRATOR,
            )
        self.stdout.write(self.style.SUCCESS("Initial event administrator created."))
