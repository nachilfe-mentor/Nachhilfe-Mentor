from __future__ import annotations

from collections import Counter


def analyze_links(records: list[dict]) -> dict:
    incoming = Counter(record["target_url"] for record in records if not record.get("is_broken"))
    broken = [record for record in records if record.get("is_broken")]
    weak_targets = [url for url, count in incoming.items() if count < 2]
    return {"broken_count": len(broken), "weak_targets": weak_targets[:50], "incoming_counts": dict(incoming)}
