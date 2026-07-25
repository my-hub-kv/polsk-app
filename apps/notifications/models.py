"""Durable in-app notifications and delivery queue."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator
from django.db import models


safe_internal_path = RegexValidator(r"^/[a-z0-9/_-]*$", "Use an internal path.")


class Notification(models.Model):
    """A controlled notification visible only to its account recipient."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_year = models.ForeignKey("events.EventYear", on_delete=models.PROTECT)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=280)
    destination_path = models.CharField(max_length=200, validators=[safe_internal_path])
    idempotency_key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "notifikation"
        verbose_name_plural = "notifikationer"
        constraints = [
            models.UniqueConstraint(
                fields=["event_year", "recipient", "idempotency_key"],
                name="notifications_unique_recipient_event_idempotency",
            )
        ]
        indexes = [models.Index(fields=["recipient", "event_year", "created_at"])]
        ordering = ["-created_at"]

    def clean(self) -> None:
        super().clean()
        if not self.event_year_id or not self.recipient_id:
            return
        try:
            participant = self.recipient.participant_profile
        except ObjectDoesNotExist:
            raise ValidationError("Notification recipient must participate in the event year.")
        if not participant.eventparticipation_set.filter(
            event_year_id=self.event_year_id
        ).exists():
            raise ValidationError("Notification recipient must participate in the event year.")

    def __str__(self) -> str:
        return f"{self.title} — {self.recipient}"


class NotificationState(models.Model):
    """Read boundary for one account in one event year."""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_year = models.ForeignKey("events.EventYear", on_delete=models.CASCADE)
    last_opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "notifikationsstatus"
        verbose_name_plural = "notifikationsstatusser"
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_year"],
                name="notifications_state_unique_recipient_event",
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipient} — {self.event_year}"


class NotificationDelivery(models.Model):
    """Provider delivery queue with retry-safe state."""

    class Status(models.TextChoices):
        PENDING = "pending", "Afventer"
        PROCESSING = "processing", "Behandles"
        SENT = "sent", "Sendt"
        RETRY = "retry", "Prøv igen"
        FAILED = "failed", "Mislykkedes"

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="deliveries"
    )
    provider = models.CharField(max_length=32, default="starti")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField()
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "notifikationslevering"
        verbose_name_plural = "notifikationsleveringer"
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "provider"],
                name="notifications_delivery_unique_notification_provider",
            )
        ]
        indexes = [models.Index(fields=["status", "available_at"])]

    def __str__(self) -> str:
        return f"{self.notification} — {self.get_status_display()}"
