from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def normalize_currency(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("₹", "").replace(",", "").replace("Crore", "").replace("crore", "").replace("Cr", "").replace("cr", "")
    text = text.replace("Lakh", "").replace("lakh", "").replace("Lakhs", "").replace("lakhs", "")
    text = text.replace("₹", "").replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None


def normalize_percentage(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def normalize_date(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    text = str(raw).strip()
    for pattern in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text if re.match(r"^\d{4}-\d{2}-\d{2}$", text) else None


def normalize_value(field_name: str, raw: Any) -> Any:
    key = field_name.lower()
    if "cost" in key or "expenditure" in key:
        return normalize_currency(raw)
    if "progress" in key or "percent" in key or "risk" in key:
        return normalize_percentage(raw)
    if "date" in key:
        return normalize_date(raw)
    return raw
