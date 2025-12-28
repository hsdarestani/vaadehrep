from typing import Dict, List, Tuple

from catalog.models import Product


NO_OPTION_ITEM_NAMES = {"بدون سس", "بدون نوشیدنی", "بدون نوشابه"}


def build_option_group_payload(product: Product) -> List[dict]:
    links = (
        product.product_option_groups.filter(is_active=True, group__is_active=True)
        .select_related("group")
        .prefetch_related("group__items")
        .order_by("sort_order", "group__sort_order", "id")
    )
    payload = []
    for link in links:
        group = link.group
        items = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price_delta_amount": item.price_delta_amount,
                "sort_order": item.sort_order,
            }
            for item in group.items.filter(is_active=True).order_by("sort_order", "id")
        ]
        payload.append(
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "is_required": link.is_required if link.is_required is not None else group.is_required,
                "min_select": link.min_select if link.min_select is not None else group.min_select,
                "max_select": link.max_select if link.max_select is not None else group.max_select,
                "sort_order": link.sort_order,
                "items": items,
            }
        )
    return payload


def normalize_modifiers(product: Product, modifiers_payload) -> Tuple[List[dict], int]:
    if modifiers_payload in (None, ""):
        modifiers_payload = []
    if not isinstance(modifiers_payload, list):
        raise ValueError("فرمت سفارشی‌سازی‌ها نامعتبر است.")

    option_groups = build_option_group_payload(product)
    group_config: Dict[int, dict] = {group["id"]: group for group in option_groups}

    normalized: List[dict] = []
    modifier_unit_total = 0
    seen_groups = set()
    selections: Dict[int, int] = {}

    for group_entry in modifiers_payload:
        if not isinstance(group_entry, dict):
            raise ValueError("فرمت سفارشی‌سازی‌ها نامعتبر است.")
        group_id = group_entry.get("group_id") or group_entry.get("group")
        if not group_id or group_id not in group_config:
            raise ValueError("گروه گزینه‌ها معتبر نیست.")
        if group_id in seen_groups:
            raise ValueError("گروه گزینه‌ها تکراری است.")
        group = group_config[group_id]
        items_payload = group_entry.get("items") or []
        if not isinstance(items_payload, list):
            raise ValueError("فرمت آیتم‌های سفارشی‌سازی نامعتبر است.")

        normalized_items: List[dict] = []
        total_qty = 0
        has_no_option = False
        available_items = {item["id"]: item for item in group["items"]}
        for item_entry in items_payload:
            if not isinstance(item_entry, dict):
                raise ValueError("فرمت آیتم‌های سفارشی‌سازی نامعتبر است.")
            item_id = item_entry.get("id") or item_entry.get("item_id") or item_entry.get("item")
            if not item_id or item_id not in available_items:
                raise ValueError("آیتم گزینه معتبر نیست.")
            quantity = int(item_entry.get("quantity") or 1)
            if quantity < 1:
                raise ValueError("تعداد گزینه‌ها معتبر نیست.")
            option_item = available_items[item_id]
            if option_item["name"] in NO_OPTION_ITEM_NAMES:
                has_no_option = True
            normalized_items.append(
                {
                    "id": option_item["id"],
                    "name": option_item["name"],
                    "price_delta_amount": option_item["price_delta_amount"],
                    "quantity": quantity,
                }
            )
            total_qty += quantity
            modifier_unit_total += option_item["price_delta_amount"] * quantity

        if has_no_option and len(normalized_items) > 1:
            raise ValueError("گزینه بدون سس یا بدون نوشیدنی باید به‌تنهایی انتخاب شود.")

        selections[group_id] = total_qty
        normalized.append(
            {
                "group_id": group_id,
                "group_name": group["name"],
                "items": normalized_items,
            }
        )
        seen_groups.add(group_id)

    for group_id, group in group_config.items():
        count = selections.get(group_id, 0)
        min_select = group["min_select"] or 0
        max_select = group["max_select"]
        is_required = group["is_required"]
        required_min = min_select if min_select > 0 else (1 if is_required else 0)
        if required_min and count < required_min:
            raise ValueError(f"انتخاب {group['name']} الزامی است.")
        if max_select and count > max_select:
            raise ValueError(f"حداکثر تعداد برای {group['name']} {max_select} است.")

    return normalized, modifier_unit_total
