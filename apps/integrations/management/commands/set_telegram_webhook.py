from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from integrations.services import telegram


class Command(BaseCommand):
    help = "Set Telegram bot webhook URL using TELEGRAM_WEBHOOK_URL or SITE_BASE_URL + TELEGRAM_WEBHOOK_SECRET."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            dest="url",
            help="Webhook URL to register (overrides settings.TELEGRAM_WEBHOOK_URL).",
        )

    def handle(self, *args, **options):
        webhook_url = options.get("url") or self._build_webhook_url_from_settings()
        if not webhook_url:
            self.stderr.write(self.style.ERROR("Webhook URL is missing; provide --url or set TELEGRAM_WEBHOOK_URL."))
            return

        ok = telegram.set_webhook(webhook_url)
        if ok:
            self.stdout.write(self.style.SUCCESS(f"Webhook set to: {webhook_url}"))
        else:
            self.stderr.write(self.style.ERROR("Failed to set Telegram webhook. Check logs for details."))

    def _build_webhook_url_from_settings(self) -> str:
        if getattr(settings, "TELEGRAM_WEBHOOK_URL", ""):
            return settings.TELEGRAM_WEBHOOK_URL

        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if not secret:
            self.stderr.write(self.style.WARNING("TELEGRAM_WEBHOOK_SECRET is not set; webhook URL cannot be built."))
            return ""

        base_url = getattr(settings, "SITE_BASE_URL", "") or getattr(settings, "FRONTEND_BASE_URL", "")
        if not base_url:
            self.stderr.write(self.style.WARNING("SITE_BASE_URL/FRONTEND_BASE_URL missing; webhook URL cannot be built."))
            return ""

        path = reverse("integrations:telegram-webhook", kwargs={"secret": secret})
        return f"{base_url.rstrip('/')}{path}"
