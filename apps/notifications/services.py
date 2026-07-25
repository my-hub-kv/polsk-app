"""Notification creation and delivery state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.people.models import EventParticipation
from .models import Notification, NotificationDelivery, NotificationState
from .providers.starti_push import (
    StartiPushError,
    StartiPushUncertainDeliveryError,
    is_configured as starti_push_is_configured,
    send_notification,
)


DELIVERY_LEASE = timedelta(minutes=10)
PUSH_TITLE = "Opdatering i Polsk App"
PUSH_BODY = "Åbn appen for at se nyt."
SYNCHRONOUS_DELIVERY_LIMIT = 1


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryDispatchResult:
    """Safe aggregate outcome from one bounded provider-delivery run."""

    processed: int
    sent: int
    retrying: int
    failed: int


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
            delivery = NotificationDelivery.objects.create(
                notification=notification,
                available_at=timezone.now(),
            )
            if settings.NOTIFICATION_DELIVERY_SYNCHRONOUS:
                transaction.on_commit(
                    lambda: _deliver_notification_synchronously(delivery.pk)
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


def claim_due_deliveries(
    *,
    limit: int = 50,
    event_year_id: int | None = None,
    delivery_id: int | None = None,
) -> list[NotificationDelivery]:
    """Claim a bounded batch for one dispatcher without duplicate processing."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    now = timezone.now()
    with transaction.atomic():
        stale_deliveries = NotificationDelivery.objects.filter(
            status=NotificationDelivery.Status.PROCESSING,
            claimed_at__lte=now - DELIVERY_LEASE,
        )
        due_deliveries = NotificationDelivery.objects.filter(
            status__in=[
                NotificationDelivery.Status.PENDING,
                NotificationDelivery.Status.RETRY,
            ],
            available_at__lte=now,
        )
        if event_year_id is not None:
            stale_deliveries = stale_deliveries.filter(
                notification__event_year_id=event_year_id
            )
            due_deliveries = due_deliveries.filter(
                notification__event_year_id=event_year_id
            )
        if delivery_id is not None:
            stale_deliveries = stale_deliveries.filter(pk=delivery_id)
            due_deliveries = due_deliveries.filter(pk=delivery_id)

        stale_deliveries.update(
            status=NotificationDelivery.Status.RETRY,
            available_at=now,
            claimed_at=None,
            error_code="lease_expired",
        )
        deliveries = list(
            due_deliveries.select_for_update(skip_locked=True)
            .select_related("notification__recipient")
            .order_by("available_at")[:limit]
        )
        for delivery in deliveries:
            delivery.status = NotificationDelivery.Status.PROCESSING
            delivery.attempts += 1
            delivery.claimed_at = now
            delivery.save(update_fields=["status", "attempts", "claimed_at"])
    return deliveries


def deliver_due_notifications(
    *,
    limit: int = 50,
    event_year_id: int | None = None,
    delivery_id: int | None = None,
) -> DeliveryDispatchResult:
    """Deliver a claimed batch outside transactions and return only safe counts."""
    deliveries = claim_due_deliveries(
        limit=limit,
        event_year_id=event_year_id,
        delivery_id=delivery_id,
    )
    sent = 0
    retrying = 0
    failed = 0
    for delivery in deliveries:
        notification = delivery.notification
        try:
            title, body = push_copy()
            send_notification(
                user=notification.recipient,
                title=title,
                body=body,
                open_to_url=notification.destination_path,
                badge_count=unread_count(
                    recipient_id=notification.recipient_id,
                    event_year_id=notification.event_year_id,
                ),
            )
        except StartiPushUncertainDeliveryError as error:
            mark_delivery_uncertain(delivery, str(error))
            failed += 1
        except StartiPushError as error:
            mark_delivery_failed(delivery, str(error))
            delivery.refresh_from_db(fields=["status"])
            if delivery.status == NotificationDelivery.Status.RETRY:
                retrying += 1
            else:
                failed += 1
        else:
            mark_delivery_sent(delivery)
            sent += 1
    return DeliveryDispatchResult(
        processed=len(deliveries),
        sent=sent,
        retrying=retrying,
        failed=failed,
    )


def _deliver_notification_synchronously(delivery_id: int) -> None:
    """Attempt one new delivery after its transaction commits without breaking the request."""
    try:
        deliver_due_notifications(
            limit=SYNCHRONOUS_DELIVERY_LIMIT,
            delivery_id=delivery_id,
        )
    except Exception:
        # This is an external-provider boundary. The durable queue remains available
        # for an administrator or a future scheduler if an unexpected failure occurs.
        logger.exception("synchronous_notification_delivery_failed")


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
