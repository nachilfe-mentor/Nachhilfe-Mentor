from __future__ import annotations


def detect_decay(metrics: list[dict], threshold: float = 0.25) -> list[dict]:
    decayed = []
    by_url: dict[str, list[dict]] = {}
    for row in metrics:
        by_url.setdefault(row.get("url_path", ""), []).append(row)
    for url, rows in by_url.items():
        ordered = sorted(rows, key=lambda item: item.get("date", ""))
        if len(ordered) < 2:
            continue
        first = float(ordered[0].get("views", 0) or 0)
        last = float(ordered[-1].get("views", 0) or 0)
        if first > 0 and (first - last) / first >= threshold:
            decayed.append({"url_path": url, "drop_rate": round((first - last) / first, 4)})
    return decayed
