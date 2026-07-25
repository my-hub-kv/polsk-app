"""Explicit credential-flow services with no raw secret persistence."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from .models import Invitation, InvitationThrottle, LoginThrottle

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=5)
LOGIN_ACCOUNT_ATTEMPT_LIMIT = 10
THROTTLE_RETENTION = timedelta(days=1)
INVITATION_ATTEMPT_LIMIT = 5
INVITATION_ATTEMPT_WINDOW = timedelta(minutes=10)


def _digest(value: str) -> str:
    return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode()).hexdigest()


def _connection_source(request: HttpRequest) -> str:
    """Return only the direct connection address; never trust forwarded headers here."""
    return request.META.get("REMOTE_ADDR", "")


def _login_throttle_digests(request: HttpRequest, username: str) -> tuple[str, str]:
    """Return account-wide and direct-source-plus-account fingerprints."""
    normalized_username = username.strip().casefold()
    account_digest = _digest(f"login-account:{normalized_username}")
    source_digest = _digest(
        f"login-source:{_connection_source(request)}:{normalized_username}"
    )
    return account_digest, source_digest


def _invitation_throttle_digest(request: HttpRequest, raw_token: str) -> str:
    """Return a source-bound fingerprint without retaining a usable token."""
    token_digest = hashlib.sha256(raw_token.encode()).hexdigest()
    return _digest(f"invitation:{_connection_source(request)}:{token_digest}")


def _is_limited(
    model: type[LoginThrottle] | type[InvitationThrottle], digest: str
) -> bool:
    state = model.objects.filter(key_digest=digest).first()
    return bool(state and state.locked_until and state.locked_until > timezone.now())


def _record_failure(
    model: type[LoginThrottle] | type[InvitationThrottle],
    digest: str,
    *,
    limit: int,
    window: timedelta,
) -> None:
    """Atomically record a failed credential attempt using an irreversible key."""
    now = timezone.now()
    with transaction.atomic():
        model.objects.filter(updated_at__lt=now - THROTTLE_RETENTION).delete()
        state, created = model.objects.get_or_create(
            key_digest=digest,
            defaults={"window_started_at": now, "failures": 1},
        )
        if created:
            return
        state = model.objects.select_for_update().get(pk=state.pk)
        if state.window_started_at + window <= now:
            state.window_started_at = now
            state.failures = 1
            state.locked_until = None
        else:
            state.failures += 1
            if state.failures >= limit:
                state.locked_until = now + window
        state.save(
            update_fields=["window_started_at", "failures", "locked_until", "updated_at"]
        )


def _clear_failures(
    model: type[LoginThrottle] | type[InvitationThrottle], digests: tuple[str, ...]
) -> None:
    model.objects.filter(key_digest__in=digests).delete()


def _throttle_digest(request: HttpRequest, username: str) -> str:
    """Return the source-bound login digest retained for compatibility and diagnostics."""
    return _login_throttle_digests(request, username)[1]


def login_is_limited(request: HttpRequest, username: str) -> bool:
    """Return whether the supplied credential source is temporarily locked."""
    return any(
        _is_limited(LoginThrottle, digest)
        for digest in _login_throttle_digests(request, username)
    )


def record_login_failure(request: HttpRequest, username: str) -> None:
    """Atomically record a failed credential attempt without storing its input."""
    account_digest, source_digest = _login_throttle_digests(request, username)
    _record_failure(
        LoginThrottle,
        account_digest,
        limit=LOGIN_ACCOUNT_ATTEMPT_LIMIT,
        window=LOGIN_ATTEMPT_WINDOW,
    )
    _record_failure(
        LoginThrottle,
        source_digest,
        limit=LOGIN_ATTEMPT_LIMIT,
        window=LOGIN_ATTEMPT_WINDOW,
    )


def clear_login_failures(request: HttpRequest, username: str) -> None:
    """Remove ephemeral throttle state after a successful login."""
    _clear_failures(LoginThrottle, _login_throttle_digests(request, username))


def invitation_is_limited(request: HttpRequest, raw_token: str) -> bool:
    """Return whether repeated attempts against this invitation are temporarily locked."""
    return _is_limited(
        InvitationThrottle, _invitation_throttle_digest(request, raw_token)
    )


def record_invitation_failure(request: HttpRequest, raw_token: str) -> None:
    """Record a failed invitation redemption without keeping the raw token."""
    _record_failure(
        InvitationThrottle,
        _invitation_throttle_digest(request, raw_token),
        limit=INVITATION_ATTEMPT_LIMIT,
        window=INVITATION_ATTEMPT_WINDOW,
    )


def clear_invitation_failures(request: HttpRequest, raw_token: str) -> None:
    """Delete temporary invitation throttle state after successful redemption."""
    _clear_failures(InvitationThrottle, (_invitation_throttle_digest(request, raw_token),))


def purge_expired_throttle_state(*, now: datetime | None = None) -> int:
    """Delete privacy-preserving throttle fingerprints past their retention period."""
    cutoff = (now or timezone.now()) - THROTTLE_RETENTION
    deleted_login, _ = LoginThrottle.objects.filter(updated_at__lt=cutoff).delete()
    deleted_invitation, _ = InvitationThrottle.objects.filter(
        updated_at__lt=cutoff
    ).delete()
    return deleted_login + deleted_invitation


def create_invitation(
    participation_id: int,
    purpose: str,
    expires_at: timezone.datetime,
) -> tuple[Invitation, str]:
    """Create a one-time credential link and return its only raw-token copy."""
    raw_token = secrets.token_urlsafe(32)
    with transaction.atomic():
        Invitation.objects.filter(
            participation_id=participation_id,
            purpose=purpose,
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        invitation = Invitation.objects.create(
            participation_id=participation_id,
            purpose=purpose,
            token_digest=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=expires_at,
        )
    return invitation, raw_token


def redeem_invitation(
    raw_token: str,
    username: str,
    password: str,
    email: str | None = None,
) -> object | None:
    """Consume a valid invitation atomically and create or reset an account."""
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        invitation = (
            Invitation.objects.select_for_update()
            .select_related("participation__participant__login_account")
            .filter(
                token_digest=digest,
                used_at__isnull=True,
                revoked_at__isnull=True,
                expires_at__gt=now,
            )
            .first()
        )
        if invitation is None:
            return None

        participant = invitation.participation.participant
        user_model = get_user_model()
        if invitation.purpose == Invitation.Purpose.CREATE_ACCOUNT:
            if participant.login_account_id:
                return None
            account = user_model.objects.create_user(
                username=username, password=password, email=email
            )
            participant.login_account = account
            participant.save(update_fields=["login_account"])
        else:
            account = participant.login_account
            if account is None:
                return None
            account.set_password(password)
            if email:
                account.email = email
            account.full_clean()
            account.save()

        invitation.used_at = now
        invitation.save(update_fields=["used_at"])
        return account
