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

    class Meta:
        verbose_name = "deltager"
        verbose_name_plural = "deltagere"

    def __str__(self) -> str:
        return self.display_name


class EventParticipation(models.Model):
    """A participant's membership of one event year."""

    event_year = models.ForeignKey("events.EventYear", on_delete=models.PROTECT)
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "eventdeltagelse"
        verbose_name_plural = "eventdeltagelser"
        constraints = [
            models.UniqueConstraint(
                fields=["event_year", "participant"],
                name="people_participation_unique_event_participant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.participant} — {self.event_year}"


class EventRoleAssignment(models.Model):
    """Additive role assigned to an event participation."""

    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        EVENT_ORGANIZER = "event_organizer", "Eventansvarlig"
        CHORE_COORDINATOR = "chore_coordinator", "Opgaveansvarlig"
        FOOD_COORDINATOR = "food_coordinator", "Madansvarlig"
        ADULT_PARTICIPANT = "adult_participant", "Voksen deltager"
        TEEN_PARTICIPANT = "teen_participant", "Teenagedeltager"

    participation = models.ForeignKey(
        EventParticipation, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role = models.CharField(max_length=32, choices=Role.choices)

    class Meta:
        verbose_name = "eventrolle"
        verbose_name_plural = "eventroller"
        constraints = [
            models.UniqueConstraint(
                fields=["participation", "role"],
                name="people_role_unique_participation_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.participation} — {self.get_role_display()}"


class Household(models.Model):
    """A household as it applies to one event year."""

    event_year = models.ForeignKey("events.EventYear", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name = "husstand"
        verbose_name_plural = "husstande"
        constraints = [
            models.UniqueConstraint(
                fields=["event_year", "name"], name="people_household_unique_event_name"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.event_year}"


class HouseholdMembership(models.Model):
    """Explicit household membership for historical event-year accuracy."""

    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    participation = models.OneToOneField(
        EventParticipation, on_delete=models.CASCADE, related_name="household_membership"
    )

    class Meta:
        verbose_name = "husstandsmedlemskab"
        verbose_name_plural = "husstandsmedlemskaber"

    def clean(self) -> None:
        super().clean()
        if (
            self.household_id
            and self.participation_id
            and self.household.event_year_id != self.participation.event_year_id
        ):
            raise ValidationError("Household and participation must share an event year.")

    def __str__(self) -> str:
        return f"{self.participation} — {self.household}"
