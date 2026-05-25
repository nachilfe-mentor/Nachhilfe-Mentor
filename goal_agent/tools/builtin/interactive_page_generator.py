from __future__ import annotations

from ...config import load_settings
from ...interactive import generate_page


def generate(spec: dict):
    settings = load_settings()
    return generate_page(
        settings,
        spec["title"],
        spec["description"],
        spec.get("page_type", "learning_utility"),
        spec.get("topic_cluster", "allgemein"),
        spec.get("primary_keyword", spec["title"].lower()),
    )
