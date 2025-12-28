from __future__ import annotations


def normalize_phone(raw: str) -> str:
    """
    Normalize phone numbers to a canonical local format.

    Examples:
        "+989121234567" -> "09121234567"
        "00989121234567" -> "09121234567"
        "989121234567" -> "09121234567"
        "9121234567" -> "09121234567"
    """
    if not raw:
        return ""

    phone = str(raw).strip()
    digits_only = "".join(ch for ch in phone if ch.isdigit())
    if not digits_only:
        return ""

    if digits_only.startswith("0098"):
        digits_only = digits_only[4:]
    elif digits_only.startswith("98"):
        digits_only = digits_only[2:]

    if digits_only and not digits_only.startswith("0"):
        digits_only = f"0{digits_only}"

    return digits_only
