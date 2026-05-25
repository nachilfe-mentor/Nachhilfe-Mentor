from __future__ import annotations

import re
from typing import Any


BLOCKED_PROPERTY_NAMES = {
    "email",
    "e_mail",
    "mail",
    "name",
    "full_name",
    "phone",
    "telefon",
    "answer",
    "raw_answer",
    "student_answer",
    "free_text",
    "school",
    "schule",
}

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
SECRET_RE = re.compile(r"(sk-|ghp_|github_pat|phx_|AIza|BEGIN PRIVATE KEY)", re.I)


def looks_sensitive(value: Any) -> bool:
    if value is None:
        return False
    text = str(value)
    return bool(EMAIL_RE.search(text) or SECRET_RE.search(text))


def sanitize_properties(properties: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in properties.items():
        normalized = key.lower().strip()
        if normalized in BLOCKED_PROPERTY_NAMES:
            continue
        if looks_sensitive(value):
            clean[key] = "[redacted]"
            continue
        if isinstance(value, str):
            clean[key] = value[:200]
        elif isinstance(value, (int, float, bool)) or value is None:
            clean[key] = value
        else:
            clean[key] = str(value)[:200]
    return clean


def validate_event_definition(event_name: str, properties: list[str]) -> list[str]:
    problems = []
    for prop in properties:
        if prop.lower().strip() in BLOCKED_PROPERTY_NAMES:
            problems.append(f"{event_name}: blocked property {prop}")
    return problems
