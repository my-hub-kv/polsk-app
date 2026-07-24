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
