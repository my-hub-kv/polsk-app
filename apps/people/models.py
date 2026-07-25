"""People and households, all scoped to an event year."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Participant(models.Model):
    """Durable person profile, which may exist without login credentials."""

    class AgeGroup(models.TextChoices):
        TODDLER = "0_3", "0-3"
        CHILD = "4_11", "4-11"
        TEEN = "12_18", "12-18"
        ADULT = "adult", "Adult"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    display_name = models.CharField(max_length=120)
    age_group = models.CharField(max_length=16, choices=AgeGroup.choices)
    login_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="participant_profile",
    )


class EventParticipation(models.Model):
    """A participant's membership of one event year."""

    event_year = models.ForeignKey("events.EventYear", on_delete=models.PROTECT)
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_year", "participant"],
                name="people_participation_unique_event_participant",
            )
        ]


class EventRoleAssignment(models.Model):
    """Additive role assigned to an event participation."""

    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        EVENT_ORGANIZER = "event_organizer", "Event organizer"
        CHORE_COORDINATOR = "chore_coordinator", "Chore coordinator"
        FOOD_COORDINATOR = "food_coordinator", "Food coordinator"
        ADULT_PARTICIPANT = "adult_participant", "Adult participant"
        TEEN_PARTICIPANT = "teen_participant", "Teen participant"

    participation = models.ForeignKey(
        EventParticipation, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role = models.CharField(max_length=32, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participation", "role"],
                name="people_role_unique_participation_role",
            )
        ]


class Household(models.Model):
    """A household as it applies to one event year."""

    event_year = models.ForeignKey("events.EventYear", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_year", "name"], name="people_household_unique_event_name"
            )
        ]


class HouseholdMembership(models.Model):
    """Explicit household membership for historical event-year accuracy."""

    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    participation = models.OneToOneField(
        EventParticipation, on_delete=models.CASCADE, related_name="household_membership"
    )

    def clean(self) -> None:
        super().clean()
        if (
            self.household_id
            and self.participation_id
            and self.household.event_year_id != self.participation.event_year_id
        ):
            raise ValidationError("Household and participation must share an event year.")
