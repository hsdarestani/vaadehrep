from typing import Optional

from vendors.models import VendorStaff


def get_active_vendor_staff(user) -> Optional[VendorStaff]:
    """
    برمی‌گرداند اولین نقش فعال VendorStaff برای کاربر احراز هویت‌شده.
    Only active vendors that are visible are considered.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return None

    return (
        VendorStaff.objects.select_related("vendor")
        .filter(user=user, is_active=True, vendor__is_active=True, vendor__is_visible=True)
        .order_by("-created_at")
        .first()
    )
