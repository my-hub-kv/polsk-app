"""Notification creation and delivery state transitions."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.people.models import EventParticipation
from .models import Notification, NotificationDelivery, NotificationState
from .providers.starti_push import is_configured as starti_push_is_configured


DELIVERY_LEASE = timedelta(minutes=10)
PUSH_TITLE = "Opdatering i Polsk App"
PUSH_BODY = "Åbn appen for at se nyt."


def enqueue_notification(
    *,
    event_year_id: int,
    recipient_id: int,
    title: str,
    body: str,
    destination_path: str,
    idempotency_key: str,
) -> Notification:
    """Persist an in-app notification and its delivery intent atomically."""
    if not EventParticipation.objects.filter(
        event_year_id=event_year_id,
        participant__login_account_id=recipient_id,
    ).exists():
        raise ValueError("The recipient is not a participant in this event year.")
    candidate = Notification(
        event_year_id=event_year_id,
        recipient_id=recipient_id,
        title=title,
        body=body,
        destination_path=destination_path,
        idempotency_key=idempotency_key,
    )
    candidate.full_clean(validate_unique=False, validate_constraints=False)
    with transaction.atomic():
        notification, created = Notification.objects.get_or_create(
            event_year_id=event_year_id,
            recipient_id=recipient_id,
            idempotency_key=idempotency_key,
            defaults={
                "title": title,
                "body": body,
                "destination_path": destination_path,
            },
        )
        if created and starti_push_is_configured():
            NotificationDelivery.objects.create(
                notification=notification,
                available_at=timezone.now(),
            )
        return notification


def unread_count(*, recipient_id: int, event_year_id: int) -> int:
    """Count notifications after the recipient last opened the inbox."""
    state = NotificationState.objects.filter(
        recipient_id=recipient_id, event_year_id=event_year_id
    ).first()
    queryset = Notification.objects.filter(
        recipient_id=recipient_id, event_year_id=event_year_id
    )
    if state and state.last_opened_at:
        queryset = queryset.filter(created_at__gt=state.last_opened_at)
    return queryset.count()


def mark_notification_center_opened(*, recipient_id: int, event_year_id: int) -> None:
    """Advance the recipient's notification read boundary after explicit opening."""
    NotificationState.objects.update_or_create(
        recipient_id=recipient_id,
        event_year_id=event_year_id,
        defaults={"last_opened_at": timezone.now()},
    )


def claim_due_deliveries(limit: int = 50) -> list[NotificationDelivery]:
    """Claim a bounded batch for one dispatcher without duplicate processing."""
    now = timezone.now()
    with transaction.atomic():
        NotificationDelivery.objects.filter(
            status=NotificationDelivery.Status.PROCESSING,
            claimed_at__lte=now - DELIVERY_LEASE,
        ).update(
            status=NotificationDelivery.Status.RETRY,
            available_at=now,
            claimed_at=None,
            error_code="lease_expired",
        )
        deliveries = list(
            NotificationDelivery.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=[
                    NotificationDelivery.Status.PENDING,
                    NotificationDelivery.Status.RETRY,
                ],
                available_at__lte=now,
            )
            .select_related("notification__recipient")
            .order_by("available_at")[:limit]
        )
        for delivery in deliveries:
            delivery.status = NotificationDelivery.Status.PROCESSING
            delivery.attempts += 1
            delivery.claimed_at = now
            delivery.save(update_fields=["status", "attempts", "claimed_at"])
    return deliveries


def mark_delivery_sent(delivery: NotificationDelivery) -> None:
    """Mark a provider delivery successful."""
    delivery.status = NotificationDelivery.Status.SENT
    delivery.sent_at = timezone.now()
    delivery.claimed_at = None
    delivery.error_code = ""
    delivery.save(update_fields=["status", "sent_at", "claimed_at", "error_code"])


def mark_delivery_failed(delivery: NotificationDelivery, error_code: str) -> None:
    """Schedule bounded retry without storing provider payload or response text."""
    if delivery.attempts >= 5:
        delivery.status = NotificationDelivery.Status.FAILED
        delivery.claimed_at = None
        delivery.error_code = error_code[:80]
        delivery.save(update_fields=["status", "claimed_at", "error_code"])
        return
    delay_minutes = min(2 ** delivery.attempts, 60)
    delivery.status = NotificationDelivery.Status.RETRY
    delivery.available_at = timezone.now() + timedelta(minutes=delay_minutes)
    delivery.claimed_at = None
    delivery.error_code = error_code[:80]
    delivery.save(update_fields=["status", "available_at", "claimed_at", "error_code"])


def mark_delivery_uncertain(delivery: NotificationDelivery, error_code: str) -> None:
    """Stop retrying an ambiguous provider attempt to avoid duplicate pushes."""
    delivery.status = NotificationDelivery.Status.FAILED
    delivery.claimed_at = None
    delivery.error_code = error_code[:80]
    delivery.save(update_fields=["status", "claimed_at", "error_code"])


def push_copy() -> tuple[str, str]:
    """Return lock-screen-safe copy without domain or participant information."""
    return PUSH_TITLE, PUSH_BODY
