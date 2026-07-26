"""Explicit state changes for event activities."""

from datetime import date, time
import logging
from time import perf_counter
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.notifications.services import enqueue_notifications
from apps.people.models import EventParticipation, EventRoleAssignment

from .models import Activity

if TYPE_CHECKING:
    from apps.accounts.models import User


performance_logger = logging.getLogger("apps.performance")


def create_activity(
    *,
    event_participation: EventParticipation,
    acting_user: "User",
    title: str,
    description: str,
    activity_date: date,
    start_time: time,
    end_time: time | None,
    is_time_approximate: bool,
) -> Activity:
    """Create an activity and enqueue event-wide notifications after commit."""
    started_at = perf_counter()
    _require_acting_account(
        event_participation=event_participation,
        acting_user=acting_user,
    )
    authorization_completed_at = perf_counter()
    with transaction.atomic():
        activity = Activity(
            event_year_id=event_participation.event_year_id,
            title=title,
            description=description,
            activity_date=activity_date,
            start_time=start_time,
            end_time=end_time,
            is_time_approximate=is_time_approximate,
            owner_participation=event_participation,
            created_by=acting_user,
            updated_by=acting_user,
        )
        _validate_activity_fields(activity)
        validation_completed_at = perf_counter()
        activity.save()
        save_completed_at = perf_counter()

        recipient_ids = list(
            EventParticipation.objects.filter(
                event_year_id=event_participation.event_year_id,
                participant__login_account__isnull=False,
            )
            .values_list("participant__login_account_id", flat=True)
            .distinct()
        )
        recipient_query_completed_at = perf_counter()
        notifications = enqueue_notifications(
            event_year_id=event_participation.event_year_id,
            recipient_ids=recipient_ids,
            title=f"Ny aktivitet: {activity.title}",
            body="Der er tilføjet en aktivitet til programmet.",
            destination_path=f"/aktiviteter/{activity.public_id}/",
            idempotency_key=f"activity-created-{activity.public_id}",
        )
        notification_enqueue_completed_at = perf_counter()
    transaction_completed_at = perf_counter()

    if settings.PERFORMANCE_TIMING_LOGGING:
        performance_logger.info(
            "performance_activity_create total_ms=%d authorization_ms=%d "
            "validation_ms=%d save_ms=%d recipient_query_ms=%d "
            "notification_enqueue_ms=%d transaction_finish_ms=%d "
            "recipients=%d notifications=%d",
            int((perf_counter() - started_at) * 1_000),
            int((authorization_completed_at - started_at) * 1_000),
            int((validation_completed_at - authorization_completed_at) * 1_000),
            int((save_completed_at - validation_completed_at) * 1_000),
            int((recipient_query_completed_at - save_completed_at) * 1_000),
            int((notification_enqueue_completed_at - recipient_query_completed_at) * 1_000),
            int((transaction_completed_at - notification_enqueue_completed_at) * 1_000),
            len(recipient_ids),
            len(notifications),
        )
    return activity


def _validate_activity_fields(activity: Activity) -> None:
    """Validate local fields while trusted service state supplies all relations."""
    activity.clean_fields(
        exclude={
            "event_year",
            "owner_participation",
            "created_by",
            "updated_by",
        }
    )
    if activity.end_time and activity.end_time <= activity.start_time:
        raise ValidationError(
            {"end_time": "Sluttidspunktet skal ligge efter starttidspunktet."}
        )


def update_activity(
    *,
    activity: Activity,
    event_participation: EventParticipation,
    acting_user: "User",
    title: str,
    description: str,
    activity_date: date,
    start_time: time,
    end_time: time | None,
    is_time_approximate: bool,
) -> Activity:
    """Update an activity only for its owner or an event administrator."""
    _require_acting_account(
        event_participation=event_participation,
        acting_user=acting_user,
    )
    if activity.event_year_id != event_participation.event_year_id or not can_edit_activity(
        activity=activity,
        event_participation=event_participation,
    ):
        raise PermissionDenied

    activity.title = title
    activity.description = description
    activity.activity_date = activity_date
    activity.start_time = start_time
    activity.end_time = end_time
    activity.is_time_approximate = is_time_approximate
    activity.updated_by = acting_user
    _validate_activity_fields(activity)
    activity.save()
    return activity


def can_edit_activity(
    *, activity: Activity, event_participation: EventParticipation
) -> bool:
    """Return whether the active profile owns the activity or administers its event."""
    return bool(
        activity.owner_participation_id == event_participation.pk
        or EventRoleAssignment.objects.filter(
            participation=event_participation,
            role=EventRoleAssignment.Role.ADMINISTRATOR,
        ).exists()
    )


def _require_acting_account(
    *, event_participation: EventParticipation, acting_user: "User"
) -> None:
    """Reject service calls that do not originate from an account in this event year."""
    if not acting_user.is_authenticated or not EventParticipation.objects.filter(
        event_year_id=event_participation.event_year_id,
        participant__login_account=acting_user,
    ).exists():
        raise PermissionDenied
