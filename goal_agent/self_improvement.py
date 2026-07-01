from __future__ import annotations

import hashlib
import json
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


def _compute_weight_proposals(db: Database) -> dict:
    """Derive scoring weight adjustments from historical opportunity data.

    Looks at which opportunity types have been acted upon (turned into blog
    tasks or coding tasks) vs. just scored and ignored. Types that dominate
    the scored set without being actioned suggest their weights are inflated.
    """
    from .scoring import DEFAULT_WEIGHTS

    scored = db.query(
        """
        select type, count(*) as total, avg(expected_value_score) as avg_score
        from opportunities
        where created_at >= datetime('now', '-90 days')
        group by type
        """
    )
    if not scored:
        return {}

    actioned = db.query(
        "select count(*) as n from blog_tasks where created_at >= datetime('now', '-90 days') and status != 'stale'"
    )
    actioned_count = actioned[0]["n"] if actioned else 0
    total_scored = sum(row["total"] for row in scored)

    if total_scored == 0 or actioned_count == 0:
        return {}

    action_rate = min(1.0, actioned_count / max(1, total_scored))
    type_data = {row["type"]: row for row in scored}
    adjusted = dict(DEFAULT_WEIGHTS)
    reasons: list[str] = []

    # If practice opportunities dominate but action rate is low, boost gap/blog signals
    if action_rate < 0.20 and "practice_asset_opportunity" in type_data:
        practice_share = type_data["practice_asset_opportunity"]["total"] / max(1, total_scored)
        if practice_share > 0.6:
            adjusted["search_demand"] = round(min(0.30, adjusted["search_demand"] + 0.02), 4)
            adjusted["serp_weakness"] = round(min(0.20, adjusted["serp_weakness"] + 0.02), 4)
            reasons.append(f"practice dominates ({practice_share:.0%}); nudging search_demand+serp_weakness to surface blog gaps")

    # If ctr_gap opportunities appear, they are high-value; boost conversion signal
    if "ctr_gap" in type_data and type_data["ctr_gap"]["total"] >= 3:
        adjusted["posthog_conversion_potential"] = round(min(0.28, adjusted["posthog_conversion_potential"] + 0.02), 4)
        reasons.append("ctr_gap opportunities present; boosting conversion_potential weight")

    return {
        "weights": adjusted,
        "action_rate": round(action_rate, 4),
        "total_scored": total_scored,
        "actioned": actioned_count,
        "reason": " | ".join(reasons) if reasons else "no adjustment needed based on current distribution",
    }


def maybe_update_scoring(db: Database, evidence: list[dict], confidence: float) -> str | None:
    if confidence < 0.8:
        return None
    proposals = _compute_weight_proposals(db)
    version = "scoring_" + hashlib.sha1(str(evidence).encode("utf-8")).hexdigest()[:12]
    now = utc_now()
    weights = proposals.get("weights", {})
    reason = proposals.get("reason") or "High-confidence evidence captured; weights derived from historical opportunity distribution."
    with db.connect() as conn:
        conn.execute(
            """
            insert into scoring_versions (id, version, weights_json, change_reason, evidence_json, status, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
              weights_json=excluded.weights_json,
              change_reason=excluded.change_reason,
              status='proposed',
              created_at=excluded.created_at
            """,
            (version, version, json_dumps(weights), reason, json_dumps(evidence), "proposed", now),
        )
    return version


def load_active_scoring_weights(db: Database) -> dict | None:
    """Return the most recently approved scoring weights, or None to use defaults."""
    rows = db.query(
        "select weights_json from scoring_versions where status = 'approved' order by created_at desc limit 1"
    )
    if not rows:
        return None
    try:
        weights = json.loads(rows[0]["weights_json"] or "{}")
        return weights if weights else None
    except Exception:
        return None
