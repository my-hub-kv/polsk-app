import os
from unittest.mock import patch

from django.test import Client, SimpleTestCase
from django.urls import reverse


class CoreViewsTests(SimpleTestCase):
    def test_home_page(self):
        response = self.client.get(
            reverse("core:home"),
            secure=True,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Polsk App")

    def test_health_endpoint(self):
        response = self.client.get(
            reverse("core:health"),
            secure=True,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class DatabaseKeepaliveTests(SimpleTestCase):
    url = "/internal/database-keepalive/"

    @patch.dict(os.environ, {"KEEPALIVE_SECRET": "test-secret"})
    @patch("apps.core.views.connection")
    def test_bearer_authenticated_request_is_not_rejected_by_csrf_middleware(
        self, mock_connection
    ):
        csrf_enforcing_client = Client(enforce_csrf_checks=True)

        response = csrf_enforcing_client.post(
            self.url,
            secure=True,
            HTTP_AUTHORIZATION="Bearer test-secret",
            HTTP_HOST="localhost",
        )

        mock_connection.cursor.assert_called_once_with()
        self.assertEqual(response.status_code, 200)

    @patch.dict(os.environ, {"KEEPALIVE_SECRET": "test-secret"})
    @patch("apps.core.views.connection")
    def test_authorized_request_queries_the_database(self, mock_connection):
        response = self.client.post(
            self.url,
            secure=True,
            HTTP_AUTHORIZATION="Bearer test-secret",
            HTTP_HOST="localhost",
        )

        cursor = mock_connection.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once_with("SELECT 1")
        cursor.fetchone.assert_called_once_with()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})
        self.assertEqual(response["Cache-Control"], "no-store")

    @patch.dict(os.environ, {"KEEPALIVE_SECRET": "test-secret"})
    @patch("apps.core.views.connection")
    def test_rejects_an_invalid_secret(self, mock_connection):
        csrf_enforcing_client = Client(enforce_csrf_checks=True)

        response = csrf_enforcing_client.post(
            self.url,
            secure=True,
            HTTP_AUTHORIZATION="Bearer incorrect-secret",
            HTTP_HOST="localhost",
        )

        mock_connection.cursor.assert_not_called()
        self.assertEqual(response.status_code, 401)

    @patch.dict(os.environ, {"KEEPALIVE_SECRET": ""})
    def test_returns_service_unavailable_when_not_configured(self):
        response = self.client.post(
            self.url,
            secure=True,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 503)


class ClientErrorTests(SimpleTestCase):
    url = "/internal/client-errors/"

    def test_client_error_requires_csrf_protection(self):
        csrf_enforcing_client = Client(enforce_csrf_checks=True)

        response = csrf_enforcing_client.post(
            self.url,
            data='{"kind": "error", "message": "Broken"}',
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 403)

    @patch("apps.core.views.logger")
    def test_client_error_logs_valid_bounded_report(self, mock_logger):
        csrf_enforcing_client = Client(enforce_csrf_checks=True)
        csrf_enforcing_client.get("/", secure=True, HTTP_HOST="localhost")
        csrf_token = csrf_enforcing_client.cookies["csrftoken"].value

        response = csrf_enforcing_client.post(
            self.url,
            data=(
                '{"kind": "error", "message": "Broken client action", '
                '"source": "/static/core/app.js", "line": 12, '
                '"column": 4, "page": "/agenda/"}'
            ),
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ORIGIN="https://localhost",
            HTTP_X_CSRFTOKEN=csrf_token,
            HTTP_RNDR_ID="test-request-id",
        )

        self.assertEqual(response.status_code, 204)
        mock_logger.error.assert_called_once()

    def test_client_error_rejects_unknown_or_malformed_payloads(self):
        csrf_enforcing_client = Client(enforce_csrf_checks=True)
        csrf_enforcing_client.get("/", secure=True, HTTP_HOST="localhost")
        csrf_token = csrf_enforcing_client.cookies["csrftoken"].value

        response = csrf_enforcing_client.post(
            self.url,
            data='{"kind": "custom", "message": "Broken"}',
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ORIGIN="https://localhost",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 400)
