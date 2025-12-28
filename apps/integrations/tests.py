from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch


class TelegramWebhookRoutingTests(TestCase):
    def test_webhook_url_resolves_in_api_namespace(self):
        url = reverse("integrations:telegram-webhook", kwargs={"secret": "s3cr3t"})
        self.assertEqual(url, "/api/integrations/telegram/webhook/s3cr3t/")

    def test_root_level_webhook_path_not_routable(self):
        response = self.client.post("/telegram/webhook/s3cr3t/", data={})
        self.assertEqual(response.status_code, 404)

    @override_settings(TELEGRAM_WEBHOOK_SECRET="s3cr3t")
    @patch("integrations.views.telegram.send_message")
    def test_webhook_view_handles_start_message_at_api_path(self, mock_send_message):
        url = reverse("integrations:telegram-webhook", kwargs={"secret": "s3cr3t"})
        payload = {"message": {"chat": {"id": 1}, "text": "/start"}}

        response = self.client.post(url, data=payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        mock_send_message.assert_called_once()
