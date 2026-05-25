from __future__ import annotations


def cluster_queries(queries: list[dict]) -> dict[str, list[dict]]:
    clusters: dict[str, list[dict]] = {}
    for row in queries:
        query = str(row.get("query", "")).lower()
        if any(x in query for x in ["mathe", "gleichung", "ableitung"]):
            key = "mathematik"
        elif any(x in query for x in ["aufsatz", "analyse", "schreiben"]):
            key = "schreibaufgaben"
        elif any(x in query for x in ["abitur", "klausur", "prüfung", "pruefung"]):
            key = "pruefungsvorbereitung"
        else:
            key = "allgemein"
        clusters.setdefault(key, []).append(row)
    return clusters
