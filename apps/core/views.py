import hmac
import os

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse


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
          </body>
        </html>
        """
    )


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


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
