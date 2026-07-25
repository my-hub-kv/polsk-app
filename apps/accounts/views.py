"""Django session authentication and invitation redemption views."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import InvitationCredentialForm
from .services import (
    clear_invitation_failures,
    clear_login_failures,
    invitation_is_limited,
    login_is_limited,
    record_invitation_failure,
    record_login_failure,
    redeem_invitation,
)
from apps.people.services import initialize_active_context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RateLimitedLoginView(LoginView):
    """Standard Django login with persistent brute-force throttling."""

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if login_is_limited(request, request.POST.get("username", "")):
            form = self.get_form()
            form.add_error(None, "For mange forsøg. Prøv igen om få minutter.")
            context = self.get_context_data(form=form)
            context["login_rate_limited"] = True
            return self.render_to_response(context, status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form: object) -> HttpResponse:
        record_login_failure(self.request, self.request.POST.get("username", ""))
        return super().form_invalid(form)

    def form_valid(self, form: object) -> HttpResponse:
        clear_login_failures(self.request, self.request.POST.get("username", ""))
        if self.request.POST.get("startiapp_credential_capture_armed") == "1":
            self.request.session["startiapp_credential_capture_armed"] = True
        response = super().form_valid(form)
        initialize_active_context(self.request)
        return response

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["startiapp_brand_name"] = settings.STARTIAPP_BRAND_NAME
        return context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class PolskLogoutView(LogoutView):
    """Render client cleanup after Django has invalidated the session."""

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["startiapp_brand_name"] = settings.STARTIAPP_BRAND_NAME
        return context


@require_POST
def startiapp_biometric_save_completed(request: HttpRequest) -> JsonResponse:
    """Acknowledge only the optional device-side credential-save completion."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False}, status=403)
    armed = request.session.pop("startiapp_credential_capture_armed", False)
    return JsonResponse({"ok": bool(armed)})


def redeem(request: HttpRequest, token: str) -> HttpResponse:
    """Redeem an invitation without revealing token validity details."""
    if request.method == "POST":
        form = InvitationCredentialForm(request.POST)
        if invitation_is_limited(request, token):
            form.add_error(None, "Linket kan ikke bruges. Bed om en ny invitation.")
        elif form.is_valid():
            try:
                account = redeem_invitation(
                    token,
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                    form.cleaned_data.get("email"),
                )
            except IntegrityError:
                account = None
            if account is not None:
                clear_invitation_failures(request, token)
                return redirect(reverse("core:login"))
            record_invitation_failure(request, token)
        else:
            record_invitation_failure(request, token)
        form.add_error(None, "Linket kan ikke bruges. Bed om en ny invitation.")
    else:
        form = InvitationCredentialForm()
    response = render(request, "accounts/redeem.html", {"form": form})
    response["Referrer-Policy"] = "no-referrer"
    return response
