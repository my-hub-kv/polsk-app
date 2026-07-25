"""Narrow Starti REST adapter that never persists device tokens."""

from __future__ import annotations

import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class StartiPushError(Exception):
    """Safe provider failure category for delivery retry decisions."""


class StartiPushUncertainDeliveryError(StartiPushError):
    """The provider might have accepted a request before transport failed."""


def is_configured() -> bool:
    """Return whether the optional native push integration is fully configured."""
    return bool(
        settings.STARTIAPP_BRAND_NAME
        and settings.STARTIAPP_API_KEY
        and settings.APP_ORIGIN
    )


def starti_user_id_for_user(user: object) -> str:
    """Return a non-sequential, environment-separated provider identity."""
    return f"polsk-{settings.STARTIAPP_ENVIRONMENT_TAG}-account-{user.public_id}"


def send_notification(*, user: object, title: str, body: str, open_to_url: str, badge_count: int) -> None:
    """Send controlled notification data to Starti with a strict timeout."""
    if not is_configured():
        raise StartiPushError("not_configured")
    if not re.fullmatch(r"/[a-z0-9/_-]*", open_to_url):
        raise StartiPushError("invalid_destination")
    payload = json.dumps(
        [
            {
                "userIds": [starti_user_id_for_user(user)],
                "title": title,
                "body": body,
                "openToUrl": f"{settings.APP_ORIGIN.rstrip('/')}{open_to_url}",
                "badgeCount": badge_count,
            }
        ]
    ).encode()
    request = Request(
        "https://api.starti.app/v1/push-notifications/send",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": settings.STARTIAPP_API_KEY,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            if not 200 <= response.status < 300:
                raise StartiPushError("unexpected_status")
    except HTTPError as error:
        raise StartiPushError(f"http_{error.code}") from error
    except (TimeoutError, socket.timeout, URLError) as error:
        # Without a provider idempotency contract, retrying an interrupted request
        # could show the same lock-screen notification more than once.
        raise StartiPushUncertainDeliveryError("transport_uncertain") from error
