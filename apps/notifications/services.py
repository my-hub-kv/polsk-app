"""Notification creation and delivery state transitions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
import logging
from threading import Lock, Thread
from time import perf_counter

from django.conf import settings
from django.db import close_old_connections, transaction
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
REQUEST_TRIGGERED_DELIVERY_CLAIM_LIMIT = 50


logger = logging.getLogger(__name__)
performance_logger = logging.getLogger("apps.performance")

_request_dispatch_state_lock = Lock()
_request_dispatch_running = False
_request_dispatch_requested = False


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
    candidate.clean_fields(exclude={"event_year", "recipient"})
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
            elif settings.NOTIFICATION_DELIVERY_REQUEST_TRIGGERED:
                transaction.on_commit(request_notification_delivery_dispatch)
        return notification


def enqueue_notifications(
    *,
    event_year_id: int,
    recipient_ids: Iterable[int],
    title: str,
    body: str,
    destination_path: str,
    idempotency_key: str,
) -> list[Notification]:
    """Persist validated per-recipient notifications with bounded database round trips."""
    started_at = perf_counter()
    unique_recipient_ids = list(dict.fromkeys(recipient_ids))
    if not unique_recipient_ids:
        _log_performance("notification_batch_enqueue", started_at, recipients=0)
        return []

    candidate = Notification(
        event_year_id=event_year_id,
        recipient_id=unique_recipient_ids[0],
        title=title,
        body=body,
        destination_path=destination_path,
        idempotency_key=idempotency_key,
    )
    candidate.clean_fields(exclude={"event_year", "recipient"})
    validation_completed_at = perf_counter()

    with transaction.atomic():
        eligible_recipient_ids = set(
            EventParticipation.objects.filter(
                event_year_id=event_year_id,
                participant__login_account_id__in=unique_recipient_ids,
            )
            .values_list("participant__login_account_id", flat=True)
            .distinct()
        )
        recipient_validation_completed_at = perf_counter()
        requested_recipient_ids = set(unique_recipient_ids)
        if eligible_recipient_ids != requested_recipient_ids:
            raise ValueError("Every recipient must participate in the event year.")

        existing_recipient_ids = set(
            Notification.objects.filter(
                event_year_id=event_year_id,
                recipient_id__in=unique_recipient_ids,
                idempotency_key=idempotency_key,
            ).values_list("recipient_id", flat=True)
        )
        existing_lookup_completed_at = perf_counter()
        notifications = [
            Notification(
                event_year_id=event_year_id,
                recipient_id=recipient_id,
                title=title,
                body=body,
                destination_path=destination_path,
                idempotency_key=idempotency_key,
            )
            for recipient_id in unique_recipient_ids
            if recipient_id not in existing_recipient_ids
        ]
        if not notifications:
            _log_performance(
                "notification_batch_enqueue",
                started_at,
                recipients=len(unique_recipient_ids),
                notifications=0,
            )
            return []

        # The unique constraint is the final idempotency boundary across requests and
        # web processes. Updating the identical key is a no-op that lets PostgreSQL
        # return primary keys for both newly inserted and raced rows.
        Notification.objects.bulk_create(
            notifications,
            update_conflicts=True,
            update_fields=["idempotency_key"],
            unique_fields=["event_year", "recipient", "idempotency_key"],
        )
        notification_insert_completed_at = perf_counter()
        delivery_count = 0
        starti_push_configured = starti_push_is_configured()
        if starti_push_configured:
            NotificationDelivery.objects.bulk_create(
                [
                    NotificationDelivery(
                        notification=notification,
                        available_at=timezone.now(),
                    )
                    for notification in notifications
                ],
                ignore_conflicts=True,
            )
            delivery_count = len(notifications)
            if settings.NOTIFICATION_DELIVERY_SYNCHRONOUS:
                transaction.on_commit(
                    lambda: _deliver_notifications_synchronously(notifications)
                )
            elif settings.NOTIFICATION_DELIVERY_REQUEST_TRIGGERED:
                transaction.on_commit(request_notification_delivery_dispatch)
        delivery_insert_completed_at = perf_counter()

    _log_performance(
        "notification_batch_enqueue",
        started_at,
        recipients=len(unique_recipient_ids),
        notifications=len(notifications),
        deliveries=delivery_count,
        starti_push_configured=int(starti_push_configured),
        delivery_synchronous=int(settings.NOTIFICATION_DELIVERY_SYNCHRONOUS),
        delivery_request_triggered=int(
            settings.NOTIFICATION_DELIVERY_REQUEST_TRIGGERED
        ),
        validation_ms=int((validation_completed_at - started_at) * 1_000),
        recipient_validation_ms=int(
            (recipient_validation_completed_at - validation_completed_at) * 1_000
        ),
        existing_lookup_ms=int(
            (existing_lookup_completed_at - recipient_validation_completed_at) * 1_000
        ),
        notification_insert_ms=int(
            (notification_insert_completed_at - existing_lookup_completed_at) * 1_000
        ),
        delivery_insert_ms=int(
            (delivery_insert_completed_at - notification_insert_completed_at) * 1_000
        ),
    )
    return notifications


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


def _deliver_notifications_synchronously(notifications: list[Notification]) -> None:
    """Attempt each newly queued delivery after commit in explicit synchronous mode."""
    started_at = perf_counter()
    _log_performance(
        "notification_synchronous_delivery_started",
        started_at,
        deliveries=len(notifications),
    )
    for notification in notifications:
        delivery = notification.deliveries.get()
        _deliver_notification_synchronously(delivery.pk)
    _log_performance(
        "notification_synchronous_delivery_finished",
        started_at,
        deliveries=len(notifications),
    )


def request_notification_delivery_dispatch() -> None:
    """Start or coalesce one best-effort dispatcher after a request has committed."""
    global _request_dispatch_requested, _request_dispatch_running

    started_at = perf_counter()
    _log_performance(
        "notification_dispatch_callback_entered",
        started_at,
        delivery_synchronous=int(settings.NOTIFICATION_DELIVERY_SYNCHRONOUS),
        delivery_request_triggered=int(
            settings.NOTIFICATION_DELIVERY_REQUEST_TRIGGERED
        ),
    )
    with _request_dispatch_state_lock:
        _request_dispatch_requested = True
        if _request_dispatch_running:
            _log_performance("notification_dispatch_request", started_at, started=0)
            return
        _request_dispatch_running = True
        dispatcher = Thread(
            target=_run_request_triggered_delivery_dispatcher,
            name="polsk-notification-dispatch",
            daemon=True,
        )
        try:
            thread_start_started_at = perf_counter()
            dispatcher.start()
            _log_performance(
                "notification_dispatch_request",
                started_at,
                started=1,
                thread_start_ms=int(
                    (perf_counter() - thread_start_started_at) * 1_000
                ),
            )
        except RuntimeError:
            _request_dispatch_running = False
            logger.exception("request_triggered_notification_dispatcher_start_failed")


def _run_request_triggered_delivery_dispatcher() -> None:
    """Drain due delivery batches without keeping request-thread database connections."""
    global _request_dispatch_requested, _request_dispatch_running

    started_at = perf_counter()
    batches = 0
    processed = 0
    sent = 0
    retrying = 0
    failed = 0
    try:
        _log_performance("notification_dispatcher_thread_entered", started_at)
        close_old_connections()
        while True:
            with _request_dispatch_state_lock:
                _request_dispatch_requested = False

            while True:
                result = deliver_due_notifications(
                    limit=REQUEST_TRIGGERED_DELIVERY_CLAIM_LIMIT
                )
                if result.processed:
                    batches += 1
                    processed += result.processed
                    sent += result.sent
                    retrying += result.retrying
                    failed += result.failed
                if result.processed == 0:
                    break

            with _request_dispatch_state_lock:
                if not _request_dispatch_requested:
                    _request_dispatch_running = False
                    return
    except Exception:
        logger.exception("request_triggered_notification_dispatcher_failed")
        with _request_dispatch_state_lock:
            _request_dispatch_running = False
    finally:
        close_old_connections()
        _log_performance(
            "notification_dispatcher",
            started_at,
            batches=batches,
            processed=processed,
            sent=sent,
            retrying=retrying,
            failed=failed,
        )


def _log_performance(event: str, started_at: float, **counts: int) -> None:
    """Write opt-in, safe timing diagnostics without user or notification content."""
    if not settings.PERFORMANCE_TIMING_LOGGING:
        return
    count_fields = " ".join(f"{name}={value}" for name, value in counts.items())
    performance_logger.info(
        "performance_%s total_ms=%d %s",
        event,
        int((perf_counter() - started_at) * 1_000),
        count_fields,
    )


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
