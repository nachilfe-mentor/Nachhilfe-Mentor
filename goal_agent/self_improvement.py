from __future__ import annotations

import hashlib
from datetime import date, timedelta

from .storage import Database, json_dumps, utc_now


def store_learning(db: Database, claim: str, evidence: list[dict], confidence: float, affected_clusters: list[str], recommended_policy_change: str, source: str) -> str:
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1")
    learning_id = "learning_" + hashlib.sha1(f"{claim}:{source}".encode("utf-8")).hexdigest()[:16]
    now = utc_now()
    revalidate = (date.today() + timedelta(days=30)).isoformat()
    with db.connect() as conn:
        conn.execute(
            """
            insert into learnings (id, claim, evidence_json, confidence, affected_clusters_json, recommended_policy_change, source, status, created_at, revalidate_after, expires_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (learning_id, claim, json_dumps(evidence), confidence, json_dumps(affected_clusters), recommended_policy_change, source, "active", now, revalidate, None),
        )
    return learning_id


def maybe_update_scoring(db: Database, evidence: list[dict], confidence: float) -> str | None:
    if confidence < 0.8:
        return None
    version = "scoring_" + hashlib.sha1(str(evidence).encode("utf-8")).hexdigest()[:12]
    now = utc_now()
    with db.connect() as conn:
        conn.execute(
            """
            insert into scoring_versions (id, version, weights_json, change_reason, evidence_json, status, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (version, version, json_dumps({}), "High-confidence evidence captured; no automatic weight change without review.", json_dumps(evidence), "proposed", now),
        )
    return version
