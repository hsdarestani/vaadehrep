from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order, OrderStatusHistory
from orders.services import handle_order_status_change


class Command(BaseCommand):
    help = "Cancel unpaid orders that have been pending payment for more than 10 minutes."

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(minutes=10)
        candidates = Order.objects.filter(
            status="PENDING_PAYMENT", payment_status="UNPAID", placed_at__lte=threshold
        )

        cancelled_count = 0
        for order in candidates:
            previous_status = order.status
            order.status = "CANCELLED"
            order.payment_status = "FAILED"
            order.cancelled_at = timezone.now()
            order.save(update_fields=["status", "payment_status", "cancelled_at"])

            OrderStatusHistory.objects.create(
                order=order,
                from_status=previous_status,
                to_status=order.status,
                changed_by_type="SYSTEM",
            )
            handle_order_status_change(order)
            cancelled_count += 1

        self.stdout.write(self.style.SUCCESS(f"Cancelled {cancelled_count} unpaid orders."))
