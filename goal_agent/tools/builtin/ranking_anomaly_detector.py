from __future__ import annotations


def detect_anomalies(metrics: list[dict], threshold: float = 0.5) -> list[dict]:
    anomalies = []
    for row in metrics:
        impressions = float(row.get("gsc_impressions", 0) or 0)
        clicks = float(row.get("gsc_clicks", 0) or 0)
        if impressions >= 100 and clicks / impressions < threshold * 0.01:
            anomalies.append({"url_path": row.get("url_path"), "reason": "low_ctr_for_impressions"})
    return anomalies
