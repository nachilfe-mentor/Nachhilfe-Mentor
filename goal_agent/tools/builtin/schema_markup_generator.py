from __future__ import annotations

from ...interactive import schema_markup


def generate_learning_resource(title: str, description: str, page_type: str = "learning_utility") -> str:
    return schema_markup(title, description, page_type)
