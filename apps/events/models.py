"""Event-year boundary for all participant data."""

from __future__ import annotations

import uuid

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
