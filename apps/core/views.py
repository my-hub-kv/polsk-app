from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from functools import wraps
import hmac
import json
import logging
import os
from typing import Literal
from uuid import UUID

from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.models import Invitation
from apps.accounts.services import create_invitation, purge_expired_throttle_state
from apps.events.forms import ActivityForm
from apps.events.selectors import activities_for_event_year, activity_for_event_year
from apps.events.services import can_edit_activity, create_activity, update_activity
from apps.notifications.models import Notification
from apps.notifications.providers.starti_push import starti_user_id_for_user
from apps.notifications.services import (
    deliver_due_notifications,
    mark_notification_center_opened,
    unread_count,
)
from apps.people.forms import ParticipantOnboardingForm
from apps.people.models import EventParticipation
from apps.people.services import (
    active_context_for_request,
    event_administrator,
    onboard_participant,
    switch_active_participant,
    switchable_participants,
)


logger = logging.getLogger(__name__)

MAX_CLIENT_ERROR_BODY_BYTES = 4_096
MAX_CLIENT_ERROR_MESSAGE_LENGTH = 300
MAX_CLIENT_ERROR_SOURCE_LENGTH = 200
ADMIN_NOTIFICATION_DELIVERY_LIMIT = 10

@dataclass(frozen=True)
class FeatureDefinition:
    """Describe one reviewable participant feature release."""

    key: str
    title: str
    route_name: str
    icon: str
    placement: Literal["primary", "more"]
    published: bool
    description: str = ""


# This registry deliberately controls only released participant navigation and pages.
# Domain authorization continues to be enforced by the individual views and services.
FEATURE_REGISTRY = (
    FeatureDefinition("agenda", "Agenda", "core:home", "calendar", "primary", True),
    FeatureDefinition("chores", "Opgaver", "core:chores", "checklist", "primary", False),
    FeatureDefinition("messages", "Beskeder", "core:messages", "messages", "primary", False),
    FeatureDefinition("food", "Mad", "core:food", "basket", "primary", False),
    FeatureDefinition("more", "Mere", "core:more", "more", "primary", True),
    FeatureDefinition(
        "activities",
        "Aktiviteter",
        "core:activities",
        "calendar",
        "more",
        True,
        "Planlagte aktiviteter under eventet.",
    ),
    FeatureDefinition(
        "directory",
        "Deltagere",
        "core:directory",
        "more",
        "more",
        True,
        "Se eventets deltageroversigt.",
    ),
    FeatureDefinition(
        "notifications",
        "Notifikationer",
        "core:notifications",
        "more",
        "more",
        True,
        "Se relevante opdateringer.",
    ),
    FeatureDefinition(
        "profile",
        "Min profil",
        "core:profile",
        "more",
        "more",
        False,
        "Se dine kommende profilindstillinger.",
    ),
    FeatureDefinition(
        "shopping",
        "Indkøb",
        "core:shopping",
        "basket",
        "more",
        False,
        "Se indkøbsønsker og lister.",
    ),
    FeatureDefinition(
        "history",
        "Tidligere år",
        "core:history",
        "more",
        "more",
        False,
        "Gå på opdagelse i eventets historik.",
    ),
    FeatureDefinition(
        "weather",
        "Vejr",
        "core:weather",
        "more",
        "more",
        False,
        "Se vejr som støtte til planlægningen.",
    ),
)
FEATURES_BY_KEY: dict[str, FeatureDefinition] = {
    feature.key: feature for feature in FEATURE_REGISTRY
}

PLACEHOLDER_PAGES = {
    "chores": ("Opgaver", "Her kommer dine og fællesskabets opgaver."),
    "messages": ("Beskeder", "Her kommer eventets fælles beskeder og kanaler."),
    "directory": ("Deltagere", "Her kommer deltageroversigten."),
    "notifications": ("Notifikationer", "Her kommer dine notifikationer."),
    "profile": ("Min profil", "Her kommer indstillinger for din profil."),
    "history": ("Tidligere år", "Her kommer eventets historik."),
    "weather": ("Vejr", "Her kommer vejr som støtte til planlægningen."),
    "food": ("Mad", "Her kommer overblik over tilgængelig og reserveret mad."),
    "shopping": ("Indkøb", "Her kommer indkøbsønsker og lister."),
}


def _safe_client_error_text(value: object, maximum_length: int) -> str:
    """Return bounded single-line text suitable for an application error log."""
    if not isinstance(value, str):
        return ""

    return " ".join(value.split())[:maximum_length]


def _can_review_unpublished_features(request: HttpRequest) -> bool:
    """Return whether this account may review unreleased participant pages."""
    return bool(
        request.user.is_authenticated
        and (request.user.is_staff or request.user.is_superuser)
    )


def _feature_is_available(request: HttpRequest, feature_key: str) -> bool:
    """Return release availability without granting feature-specific permissions."""
    feature = FEATURES_BY_KEY.get(feature_key)
    return bool(
        feature and (feature.published or _can_review_unpublished_features(request))
    )


def _feature_items(
    request: HttpRequest,
    placement: Literal["primary", "more"],
    active_page: str,
) -> list[dict[str, object]]:
    """Return visible registry items for a participant shell placement."""
    return [
        {
            "key": feature.key,
            "title": feature.title,
            "url": reverse(feature.route_name),
            "icon": feature.icon,
            "active": feature.key == active_page,
            "published": feature.published,
            "description": feature.description,
        }
        for feature in FEATURE_REGISTRY
        if feature.placement == placement and _feature_is_available(request, feature.key)
    ]


def _shell_context(request: HttpRequest, active_page: str, page_title: str) -> dict[str, object]:
    """Return shared shell context and release metadata without granting permissions."""
    context: dict[str, object] = {
        "navigation_items": _feature_items(request, "primary", active_page),
        "feature_availability": [
            {
                "key": feature.key,
                "published": feature.published,
                "visible": _feature_is_available(request, feature.key),
            }
            for feature in FEATURE_REGISTRY
        ],
        "page_title": page_title,
    }
    active_context = active_context_for_request(request)
    if active_context:
        event_year = active_context.event_participation.event_year
        context["active_participant"] = active_context.event_participation.participant
        context["active_event_year"] = event_year
        context["notification_count"] = unread_count(
            recipient_id=request.user.pk, event_year_id=event_year.pk
        )
        context["switchable_participants"] = switchable_participants(request)
    if settings.STARTIAPP_BRAND_NAME:
        context["startiapp_brand_name"] = settings.STARTIAPP_BRAND_NAME
        context["startiapp_user_id"] = starti_user_id_for_user(request.user)
        context["startiapp_complete_biometric_save"] = bool(
            request.session.get("startiapp_credential_capture_armed")
        )
    return context


def _released_feature(
    feature_key: str,
) -> Callable[[Callable[[HttpRequest], HttpResponse]], Callable[[HttpRequest], HttpResponse]]:
    """Redirect normal participants away from a feature not in their release."""

    def decorator(
        view: Callable[[HttpRequest], HttpResponse],
    ) -> Callable[[HttpRequest], HttpResponse]:
        @wraps(view)
        def wrapped(
            request: HttpRequest,
            *args: object,
            **kwargs: object,
        ) -> HttpResponse:
            if not _feature_is_available(request, feature_key):
                return redirect("core:home")
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def _placeholder_view(
    page_key: str,
    active_page: str,
) -> Callable[[HttpRequest], HttpResponse]:
    """Build an authenticated placeholder view for a planned product area."""

    @login_required
    @ensure_csrf_cookie
    def view(request: HttpRequest) -> HttpResponse:
        if not _feature_is_available(request, page_key):
            return redirect("core:home")
        page = PLACEHOLDER_PAGES.get(page_key)
        if page is None:
            return HttpResponseNotFound()

        title, description = page
        context = _shell_context(request, active_page, title)
        context.update({"placeholder_title": title, "placeholder_description": description})
        return render(request, "core/placeholder.html", context)

    return view


@login_required
@ensure_csrf_cookie
@_released_feature("agenda")
def home(request: HttpRequest) -> HttpResponse:
    """Render the active event year's shared activity schedule."""
    context = _shell_context(request, "agenda", "Agenda")
    active_context = active_context_for_request(request)
    context["activities"] = (
        activities_for_event_year(
            event_year_id=active_context.event_participation.event_year_id
        )
        if active_context
        else []
    )
    return render(request, "core/agenda.html", context)


chores = _placeholder_view("chores", "chores")
messages = _placeholder_view("messages", "messages")
profile = _placeholder_view("profile", "more")
history = _placeholder_view("history", "more")
weather = _placeholder_view("weather", "more")
food = _placeholder_view("food", "food")
shopping = _placeholder_view("shopping", "more")


@login_required
@ensure_csrf_cookie
@_released_feature("activities")
@require_http_methods(["GET", "POST"])
def activities(request: HttpRequest) -> HttpResponse:
    """List all active-event activities and allow authenticated participants to add one."""
    context = _shell_context(request, "more", "Aktiviteter")
    active_context = active_context_for_request(request)
    if active_context is None:
        context.update({"activities": [], "form": None})
        return render(request, "core/activities.html", context)

    participation = active_context.event_participation
    if request.method == "POST":
        form = ActivityForm(request.POST)
        if form.is_valid():
            try:
                activity = create_activity(
                    event_participation=participation,
                    acting_user=request.user,
                    **form.cleaned_data,
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                django_messages.success(request, "Aktiviteten er oprettet.")
                return redirect("core:activity_detail", activity_public_id=activity.public_id)
    else:
        form = ActivityForm()

    context.update(
        {
            "activities": activities_for_event_year(
                event_year_id=participation.event_year_id
            ),
            "form": form,
        }
    )
    return render(request, "core/activities.html", context)


@login_required
@ensure_csrf_cookie
@_released_feature("activities")
@require_http_methods(["GET", "POST"])
def activity_detail(
    request: HttpRequest,
    activity_public_id: UUID,
) -> HttpResponse:
    """Show one event-scoped activity and allow only its owner or an admin to edit it."""
    active_context = active_context_for_request(request)
    if active_context is None:
        return HttpResponseNotFound()
    participation = active_context.event_participation
    activity = activity_for_event_year(
        event_year_id=participation.event_year_id,
        public_id=activity_public_id,
    )
    if activity is None:
        return HttpResponseNotFound()

    can_edit = can_edit_activity(
        activity=activity,
        event_participation=participation,
    )
    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied
        form = ActivityForm(
            request.POST,
            instance=activity,
        )
        if form.is_valid():
            try:
                activity = update_activity(
                    activity=activity,
                    event_participation=participation,
                    acting_user=request.user,
                    **form.cleaned_data,
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                django_messages.success(request, "Aktiviteten er opdateret.")
                return redirect("core:activity_detail", activity_public_id=activity.public_id)
    else:
        form = (
            ActivityForm(instance=activity)
            if can_edit
            else None
        )

    context = _shell_context(request, "more", activity.title)
    context.update({"activity": activity, "form": form, "can_edit_activity": can_edit})
    return render(request, "core/activity_detail.html", context)


@login_required
def food_and_shopping(request: HttpRequest) -> HttpResponse:
    """Redirect the former combined food route to the primary food section."""
    if not _feature_is_available(request, "food"):
        return redirect("core:home")
    return redirect("core:food")


@login_required
@ensure_csrf_cookie
@_released_feature("more")
def more(request: HttpRequest) -> HttpResponse:
    """Render the released secondary navigation for participant areas."""
    context = _shell_context(request, "more", "Mere")
    context["more_items"] = _feature_items(request, "more", "more")
    active_context = active_context_for_request(request)
    if active_context and event_administrator(active_context.event_participation):
        context["more_items"].append(
            {
                "key": "administration",
                "title": "Administration",
                "description": "Behandl notifikationer og ryd udløbet loginbeskyttelse.",
                "url": reverse("core:administration"),
            }
        )
    return render(request, "core/more.html", context)


def _active_event_administrator(request: HttpRequest):
    """Return the active event membership only for a server-authorized administrator."""
    active_context = active_context_for_request(request)
    if active_context is None or not event_administrator(
        active_context.event_participation
    ):
        raise PermissionDenied
    return active_context.event_participation


@login_required
@ensure_csrf_cookie
@require_GET
def administration(request: HttpRequest) -> HttpResponse:
    """Render restricted operational controls for the active event administrator."""
    _active_event_administrator(request)
    context = _shell_context(request, "more", "Administration")
    context["notification_delivery_limit"] = ADMIN_NOTIFICATION_DELIVERY_LIMIT
    return render(request, "core/administration.html", context)


@login_required
@require_POST
def process_notifications(request: HttpRequest) -> HttpResponse:
    """Process a bounded due delivery batch within the administrator's event year."""
    participation = _active_event_administrator(request)
    result = deliver_due_notifications(
        limit=ADMIN_NOTIFICATION_DELIVERY_LIMIT,
        event_year_id=participation.event_year_id,
    )
    if result.processed == 0:
        django_messages.info(request, "Der er ingen afventende notifikationer.")
    else:
        django_messages.success(
            request,
            (
                f"Behandlede {result.processed} notifikationer: {result.sent} sendt, "
                f"{result.retrying} afventer nyt forsøg og {result.failed} kunne ikke sendes."
            ),
        )
    return redirect("core:administration")


@login_required
@require_POST
def cleanup_login_protection(request: HttpRequest) -> HttpResponse:
    """Delete expired throttle fingerprints after server-side administrator authorization."""
    _active_event_administrator(request)
    deleted = purge_expired_throttle_state()
    django_messages.success(request, f"Ryddede {deleted} udløbne loginbeskyttelser.")
    return redirect("core:administration")


@login_required
@ensure_csrf_cookie
@_released_feature("notifications")
def notifications(request: HttpRequest) -> HttpResponse:
    """Render the authenticated event inbox without mutating read state."""
    context = _shell_context(request, "more", "Notifikationer")
    active_context = active_context_for_request(request)
    if active_context is None:
        context["notifications"] = []
        return render(request, "core/notifications.html", context)

    event_year = active_context.event_participation.event_year
    context["notifications"] = Notification.objects.filter(
        recipient=request.user, event_year=event_year
    )
    return render(request, "core/notifications.html", context)


@login_required
@require_POST
def mark_notifications_opened(request: HttpRequest) -> JsonResponse:
    """Advance the read boundary after the notification center has opened."""
    active_context = active_context_for_request(request)
    if active_context is None:
        return JsonResponse({"ok": False}, status=403)
    mark_notification_center_opened(
        recipient_id=request.user.pk,
        event_year_id=active_context.event_participation.event_year_id,
    )
    return JsonResponse({"ok": True})


@login_required
@ensure_csrf_cookie
@_released_feature("directory")
def directory(request: HttpRequest) -> HttpResponse:
    """Show the active event directory and limited administrator onboarding."""
    context = _shell_context(request, "more", "Deltagere")
    active_context = active_context_for_request(request)
    if active_context is None:
        context.update({"participants": [], "form": None, "can_manage_participants": False})
        return render(request, "core/directory.html", context)
    participation = active_context.event_participation
    can_manage = event_administrator(participation)
    invitation_url = None
    if request.method == "POST":
        if not can_manage:
            return HttpResponse(status=403)
        form = ParticipantOnboardingForm(request.POST)
        if form.is_valid():
            _, token = onboard_participant(
                event_year_id=participation.event_year_id,
                **form.cleaned_data,
            )
            if token:
                invitation_url = request.build_absolute_uri(
                    reverse("accounts:redeem", args=[token])
                )
            form = ParticipantOnboardingForm()
    else:
        form = ParticipantOnboardingForm() if can_manage else None
    context.update(
        {
            "participants": EventParticipation.objects.filter(
                event_year=participation.event_year
            ).select_related("participant").order_by("participant__display_name"),
            "form": form,
            "can_manage_participants": can_manage,
            "invitation_url": invitation_url,
        }
    )
    return render(request, "core/directory.html", context)


@login_required
@require_POST
def reset_credentials(request: HttpRequest, participant_public_id: str) -> HttpResponse:
    """Issue one reset link for an account in the administrator's event year."""
    active_context = active_context_for_request(request)
    if active_context is None or not event_administrator(active_context.event_participation):
        return HttpResponse(status=403)
    participation = EventParticipation.objects.select_related("participant").filter(
        event_year=active_context.event_participation.event_year,
        participant__public_id=participant_public_id,
        participant__login_account__isnull=False,
    ).first()
    if participation is None:
        return HttpResponse(status=404)
    _, token = create_invitation(
        participation.pk,
        Invitation.Purpose.RESET_CREDENTIALS,
        timezone.now() + timedelta(days=1),
    )
    return render(
        request,
        "core/invitation_created.html",
        {"invitation_url": request.build_absolute_uri(reverse("accounts:redeem", args=[token]))},
    )


@login_required
@require_POST
def switch_profile(request: HttpRequest) -> HttpResponse:
    """Switch only to a server-authorized household child profile."""
    switch_active_participant(request, request.POST.get("participant", ""))
    return redirect("core:home")


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_POST
def client_error(request: HttpRequest) -> HttpResponse:
    """Log a bounded, CSRF-protected browser error without persisting client data."""
    if request.content_type != "application/json":
        return HttpResponseBadRequest("Invalid error report.")

    content_length = request.headers.get("Content-Length")
    if content_length:
        try:
            body_size = int(content_length)
        except ValueError:
            return HttpResponseBadRequest("Invalid error report.")

        if body_size < 0 or body_size > MAX_CLIENT_ERROR_BODY_BYTES:
            return HttpResponse(status=413)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid error report.")

    if not isinstance(payload, dict):
        return HttpResponseBadRequest("Invalid error report.")

    kind = payload.get("kind")
    if kind not in {"error", "unhandledrejection"}:
        return HttpResponseBadRequest("Invalid error report.")

    message = _safe_client_error_text(
        payload.get("message"),
        MAX_CLIENT_ERROR_MESSAGE_LENGTH,
    )
    source = _safe_client_error_text(
        payload.get("source"),
        MAX_CLIENT_ERROR_SOURCE_LENGTH,
    )
    page = _safe_client_error_text(
        payload.get("page"),
        MAX_CLIENT_ERROR_SOURCE_LENGTH,
    )

    if not message:
        return HttpResponseBadRequest("Invalid error report.")

    line = payload.get("line")
    column = payload.get("column")
    if not isinstance(line, int) or line < 0:
        line = 0
    if not isinstance(column, int) or column < 0:
        column = 0

    request_id = _safe_client_error_text(
        request.headers.get("Rndr-Id"),
        MAX_CLIENT_ERROR_SOURCE_LENGTH,
    )
    logger.error(
        "client_error kind=%s message=%r source=%r line=%d column=%d "
        "page=%r request_id=%r",
        kind,
        message,
        source,
        line,
        column,
        page,
        request_id,
    )
    return HttpResponse(status=204)


# This non-browser endpoint authenticates with a bearer secret, not a session cookie.
# CSRF protection therefore cannot validate its scheduled request; bearer authentication
# remains mandatory for every request.
@csrf_exempt
def database_keepalive(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    expected = os.getenv("KEEPALIVE_SECRET")
    supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")

    if not expected:
        return JsonResponse({"error": "Keepalive is unavailable"}, status=503)

    if not hmac.compare_digest(supplied, expected):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    response = JsonResponse({"status": "ok", "database": "connected"})
    response["Cache-Control"] = "no-store"
    return response
