"""Read queries for the event activity schedule."""

from uuid import UUID

from django.db.models import QuerySet

from .models import Activity


def activities_for_event_year(*, event_year_id: int) -> QuerySet[Activity]:
    """Return chronological activities for one event year with display relations."""
    return Activity.objects.filter(event_year_id=event_year_id).select_related(
        "event_year",
        "owner_participation__participant",
    )


def activity_for_event_year(*, event_year_id: int, public_id: UUID) -> Activity | None:
    """Return one activity only when it belongs to the requested event year."""
    return activities_for_event_year(event_year_id=event_year_id).filter(
        public_id=public_id
    ).first()
