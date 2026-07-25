"""Trusted active-participant session context and profile switching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.accounts.models import Invitation
from apps.accounts.services import create_invitation
from .models import (
    EventParticipation,
    EventRoleAssignment,
    Household,
    HouseholdMembership,
    Participant,
)

ACTIVE_EVENT_SESSION_KEY = "polsk_active_event_id"
ACTIVE_PARTICIPANT_SESSION_KEY = "polsk_active_participant_id"


@dataclass(frozen=True)
class ActiveContext:
    event_participation: EventParticipation


def active_context_for_request(request: HttpRequest) -> ActiveContext | None:
    """Resolve session context only when it remains valid for the account."""
    if not request.user.is_authenticated:
        return None
    participation_id = request.session.get(ACTIVE_PARTICIPANT_SESSION_KEY)
    queryset = EventParticipation.objects.select_related("event_year", "participant")
    if participation_id:
        participation = queryset.filter(
            pk=participation_id,
            event_year_id=request.session.get(ACTIVE_EVENT_SESSION_KEY),
        ).first()
        if participation and _is_available_to_account(request.user, participation):
            return ActiveContext(participation)

    participation = queryset.filter(
        participant__login_account=request.user,
        event_year__status="active",
    ).order_by("-event_year__year").first()
    if participation:
        return ActiveContext(participation)
    return None


def initialize_active_context(request: HttpRequest) -> None:
    """Store the authenticated account's default active event after login only."""
    if not request.user.is_authenticated:
        return
    participation = (
        EventParticipation.objects.select_related("event_year", "participant")
        .filter(
            participant__login_account=request.user,
            event_year__status="active",
        )
        .order_by("-event_year__year")
        .first()
    )
    if participation:
        _store_context(request, participation)


def switch_active_participant(request: HttpRequest, participant_public_id: str) -> ActiveContext:
    """Switch an adult account only to its own or same-household child profile."""
    current = active_context_for_request(request)
    if current is None:
        raise PermissionDenied
    target = (
        EventParticipation.objects.select_related("participant", "event_year")
        .filter(event_year=current.event_participation.event_year, participant__public_id=participant_public_id)
        .first()
    )
    if target is None or not _is_available_to_account(request.user, target):
        raise PermissionDenied
    _store_context(request, target)
    return ActiveContext(target)


def switchable_participants(request: HttpRequest) -> list[Participant]:
    """Return only child profiles the authenticated adult may select."""
    current = active_context_for_request(request)
    if current is None:
        return []
    own = EventParticipation.objects.select_related("participant").filter(
        event_year=current.event_participation.event_year,
        participant__login_account=request.user,
    ).first()
    if own is None or own.participant.age_group != Participant.AgeGroup.ADULT:
        return []
    household_id = (
        type(own).objects.filter(pk=own.pk)
        .values_list("household_membership__household_id", flat=True)
        .first()
    )
    if household_id is None:
        return []
    return list(
        Participant.objects.filter(
            eventparticipation__event_year=own.event_year,
            eventparticipation__household_membership__household_id=household_id,
            age_group__in=[Participant.AgeGroup.TODDLER, Participant.AgeGroup.CHILD],
        ).order_by("display_name")
    )


def _is_available_to_account(account: AbstractBaseUser, target: EventParticipation) -> bool:
    own = EventParticipation.objects.select_related("participant").filter(
        event_year=target.event_year, participant__login_account=account
    ).first()
    if own is None:
        return False
    if own.pk == target.pk:
        return True
    if own.participant.age_group != Participant.AgeGroup.ADULT:
        return False
    if target.participant.age_group not in {Participant.AgeGroup.TODDLER, Participant.AgeGroup.CHILD}:
        return False
    own_household_id = (
        EventParticipation.objects.filter(pk=own.pk)
        .values_list("household_membership__household_id", flat=True)
        .first()
    )
    target_household_id = (
        EventParticipation.objects.filter(pk=target.pk)
        .values_list("household_membership__household_id", flat=True)
        .first()
    )
    return own_household_id is not None and own_household_id == target_household_id


def _store_context(request: HttpRequest, participation: EventParticipation) -> None:
    request.session[ACTIVE_EVENT_SESSION_KEY] = participation.event_year_id
    request.session[ACTIVE_PARTICIPANT_SESSION_KEY] = participation.pk


def event_administrator(participation: EventParticipation) -> bool:
    """Return whether this event participation holds the administrator role."""
    return participation.role_assignments.filter(role="administrator").exists()


def onboard_participant(
    *,
    event_year_id: int,
    display_name: str,
    age_group: str,
    household_name: str,
    create_credentials: bool,
) -> tuple[Participant, str | None]:
    """Create event-scoped person data and optionally one invitation link."""
    with transaction.atomic():
        participant = Participant.objects.create(
            display_name=display_name,
            age_group=age_group,
        )
        participation = EventParticipation.objects.create(
            event_year_id=event_year_id,
            participant=participant,
        )
        household, _ = Household.objects.get_or_create(
            event_year_id=event_year_id,
            name=household_name,
        )
        assign_household_membership(household=household, participation=participation)
        role = (
            EventRoleAssignment.Role.ADULT_PARTICIPANT
            if age_group == Participant.AgeGroup.ADULT
            else EventRoleAssignment.Role.TEEN_PARTICIPANT
        )
        EventRoleAssignment.objects.create(participation=participation, role=role)
        if not create_credentials:
            return participant, None
        _, token = create_invitation(
            participation.pk,
            Invitation.Purpose.CREATE_ACCOUNT,
            timezone.now() + timedelta(days=7),
        )
    return participant, token


def assign_household_membership(
    *, household: Household, participation: EventParticipation
) -> HouseholdMembership:
    """Create one event-consistent household membership through the domain boundary."""
    membership = HouseholdMembership(household=household, participation=participation)
    membership.full_clean()
    membership.save()
    return membership
