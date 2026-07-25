import hmac
import json
import logging
import os

from django.db import connection
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)

MAX_CLIENT_ERROR_BODY_BYTES = 4_096
MAX_CLIENT_ERROR_MESSAGE_LENGTH = 300
MAX_CLIENT_ERROR_SOURCE_LENGTH = 200


def _safe_client_error_text(value: object, maximum_length: int) -> str:
    """Return bounded single-line text suitable for an application error log."""
    if not isinstance(value, str):
        return ""

    return " ".join(value.split())[:maximum_length]


@ensure_csrf_cookie
def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        """
        <!doctype html>
        <html lang="da">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Polsk App</title>
            <style>
              body {
                font-family: system-ui, sans-serif;
                max-width: 720px;
                margin: 0 auto;
                padding: 4rem 1.5rem;
                line-height: 1.5;
              }

              h1 {
                font-size: 3rem;
                margin-bottom: 0.5rem;
              }
            </style>
          </head>
          <body>
            <h1>Polsk App</h1>
            <p>Automatisk deployment virker.</p>
            <script src="/static/core/client-error-reporting.js" defer></script>
          </body>
        </html>
        """
    )


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
