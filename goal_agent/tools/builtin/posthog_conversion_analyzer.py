from __future__ import annotations

from typing import Any


def analyze(summary: dict[str, Any]) -> dict[str, Any]:
    events = summary.get("events", {})
    page_views = max(1, int(events.get("seo_page_view", 0) or 0))
    ctas = int(events.get("seo_cta_clicked", 0) or 0) + int(events.get("seo_app_store_clicked", 0) or 0)
    return {"page_views": page_views, "cta_clicks": ctas, "conversion_rate": round(ctas / page_views, 4)}
