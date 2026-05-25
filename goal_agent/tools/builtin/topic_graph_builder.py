from __future__ import annotations

from collections import Counter


def build_topic_summary(content_rows: list[dict]) -> dict:
    counts = Counter(row.get("topic_cluster") or "allgemein" for row in content_rows)
    return {"clusters": dict(counts), "total_pages": len(content_rows)}
