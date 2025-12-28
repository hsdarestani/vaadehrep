from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import TelegramUser, User, UserDevice
from addresses.models import Address
from core.utils import normalize_phone
from orders.models import Order
from vendors.models import VendorStaff


class Command(BaseCommand):
    help = "Normalize stored phone numbers and merge duplicate users based on the canonical phone."

    def handle(self, *args, **options):
        with transaction.atomic():
            canonical_map = {}
            duplicates = []

            for user in User.objects.order_by("created_at", "id"):
                normalized = normalize_phone(user.phone)
                if not normalized:
                    continue

                primary = canonical_map.get(normalized)
                if primary:
                    duplicates.append((user, primary))
                else:
                    canonical_map[normalized] = user

            # Update primaries to the normalized format
            for normalized, primary in canonical_map.items():
                if primary.phone != normalized:
                    primary.phone = normalized
                    primary.save(update_fields=["phone"])

            merged = 0
            for duplicate, primary in duplicates:
                Address.objects.filter(user=duplicate).update(user=primary)
                Order.objects.filter(user=duplicate).update(user=primary)

                for device in UserDevice.objects.filter(user=duplicate):
                    existing = UserDevice.objects.filter(user=primary, device_id=device.device_id).first()
                    if existing:
                        updated_fields = []
                        if not existing.title and device.title:
                            existing.title = device.title
                            updated_fields.append("title")
                        if device.last_seen_at and (not existing.last_seen_at or device.last_seen_at > existing.last_seen_at):
                            existing.last_seen_at = device.last_seen_at
                            updated_fields.append("last_seen_at")
                        if device.ip and not existing.ip:
                            existing.ip = device.ip
                            updated_fields.append("ip")
                        if device.user_agent and not existing.user_agent:
                            existing.user_agent = device.user_agent
                            updated_fields.append("user_agent")
                        if device.refresh_hash and not existing.refresh_hash:
                            existing.refresh_hash = device.refresh_hash
                            updated_fields.append("refresh_hash")
                        if updated_fields:
                            existing.save(update_fields=updated_fields)
                        device.delete()
                    else:
                        device.user = primary
                        device.save(update_fields=["user"])

                for staff in VendorStaff.objects.filter(user=duplicate):
                    if not VendorStaff.objects.filter(vendor=staff.vendor, user=primary).exists():
                        staff.user = primary
                        staff.save(update_fields=["user"])
                    else:
                        staff.delete()

                for tg in TelegramUser.objects.filter(user=duplicate):
                    if not TelegramUser.objects.filter(user=primary).exists():
                        tg.user = primary
                        tg.save(update_fields=["user"])
                    else:
                        tg.delete()

                duplicate.delete()
                merged += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Normalized {len(canonical_map)} phone(s); merged {merged} duplicate user(s) based on phone."
            )
        )
