"""Event-year boundary for all participant data."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class EventYear(models.Model):
    """A separately scoped annual Polsk event."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Kladde"
        ACTIVE = "active", "Aktiv"
        COMPLETED = "completed", "Afsluttet"
        ARCHIVED = "archived", "Arkiveret"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=80)
    year = models.PositiveSmallIntegerField(unique=True)
    starts_on = models.DateField()
    ends_on = models.DateField()
    timezone = models.CharField(max_length=64, default="Europe/Copenhagen")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        verbose_name = "eventår"
        verbose_name_plural = "eventår"
        constraints = [models.CheckConstraint(condition=models.Q(ends_on__gte=models.F("starts_on")), name="events_eventyear_dates_ordered")]
        ordering = ["-year"]

    def __str__(self) -> str:
        return self.name


class Activity(models.Model):
    """One shared scheduled activity within a single event year."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_year = models.ForeignKey(EventYear, on_delete=models.PROTECT)
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=2_000)
    activity_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    is_time_approximate = models.BooleanField(default=False)
    owner_participation = models.ForeignKey(
        "people.EventParticipation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_activities",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_activities",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "aktivitet"
        verbose_name_plural = "aktiviteter"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__isnull=True)
                | models.Q(end_time__gt=models.F("start_time")),
                name="events_activity_end_time_after_start_time",
            )
        ]
        indexes = [models.Index(fields=["event_year", "activity_date", "start_time"])]
        ordering = ["activity_date", "start_time", "pk"]

    def clean(self) -> None:
        """Validate event-year consistency not expressible as database constraints."""
        super().clean()
        if self.event_year_id and self.owner_participation_id:
            from apps.people.models import EventParticipation

            if not EventParticipation.objects.filter(
                pk=self.owner_participation_id,
                event_year_id=self.event_year_id,
            ).exists():
                raise ValidationError(
                    {"owner_participation": "Ejeren skal deltage i det samme eventår."}
                )

    def __str__(self) -> str:
        return f"{self.title} — {self.event_year}"
