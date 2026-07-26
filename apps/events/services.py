"""Explicit state changes for event activities."""

from datetime import date, time
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.notifications.services import enqueue_notification
from apps.people.models import EventParticipation, EventRoleAssignment

from .models import Activity

if TYPE_CHECKING:
    from apps.accounts.models import User


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
    """Create an activity and notify every account in its event year after commit."""
    _require_acting_account(
        event_participation=event_participation,
        acting_user=acting_user,
    )
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
        activity.full_clean()
        activity.save()

        recipient_ids = EventParticipation.objects.filter(
            event_year_id=event_participation.event_year_id,
            participant__login_account__isnull=False,
        ).values_list("participant__login_account_id", flat=True).distinct()
        for recipient_id in recipient_ids:
            enqueue_notification(
                event_year_id=event_participation.event_year_id,
                recipient_id=recipient_id,
                title=f"Ny aktivitet: {activity.title}",
                body="Der er tilføjet en aktivitet til programmet.",
                destination_path=f"/aktiviteter/{activity.public_id}/",
                idempotency_key=f"activity-created-{activity.public_id}",
            )
    return activity


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
    activity.full_clean()
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
