from __future__ import annotations

from collections import defaultdict


def detect(content_rows: list[dict]) -> list[dict]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in content_rows:
        keyword = (row.get("primary_keyword") or "").lower().strip()
        if keyword:
            groups[keyword].append(row["url_path"])
    return [{"keyword": key, "urls": urls, "risk": "medium"} for key, urls in groups.items() if len(urls) > 1]
