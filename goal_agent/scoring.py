from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


DEFAULT_WEIGHTS = {
    "search_demand": 0.20,
    "serp_weakness": 0.15,
    "topical_authority_fit": 0.15,
    "posthog_conversion_potential": 0.20,
    "internal_link_value": 0.10,
    "interactivity_advantage": 0.10,
    "confidence": 0.10,
    "execution_complexity": -0.10,
    "privacy_risk": -0.15,
    "seo_risk": -0.15,
}

PRACTICE_INTENT_TERMS = [
    "übungen",
    "uebungen",
    "mit lösungen",
    "mit loesungen",
    "aufgaben",
    "test",
    "klausur",
    "abi",
    "abitur",
    "arbeitsblatt",
]


@dataclass(frozen=True)
class OpportunityScore:
    expected_value_score: float
    money_potential_score: float
    traffic_potential_score: float
    search_demand_score: float
    serp_weakness_score: float
    topical_authority_fit_score: float
    posthog_conversion_potential_score: float
    internal_link_value_score: float
    interactivity_advantage_score: float
    execution_complexity_score: float
    privacy_risk_score: float
    seo_risk_score: float
    confidence_score: float


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_opportunity(signals: dict[str, float]) -> OpportunityScore:
    search = clamp(signals.get("search_demand", 0.4))
    serp = clamp(signals.get("serp_weakness", 0.3))
    authority = clamp(signals.get("topical_authority_fit", 0.5))
    conversion = clamp(signals.get("posthog_conversion_potential", 0.4))
    links = clamp(signals.get("internal_link_value", 0.4))
    interactive = clamp(signals.get("interactivity_advantage", 0.2))
    complexity = clamp(signals.get("execution_complexity", 0.4))
    privacy = clamp(signals.get("privacy_risk", 0.1))
    seo = clamp(signals.get("seo_risk", 0.1))
    confidence = clamp(signals.get("confidence", 0.5))
    expected = (
        DEFAULT_WEIGHTS["search_demand"] * search
        + DEFAULT_WEIGHTS["serp_weakness"] * serp
        + DEFAULT_WEIGHTS["topical_authority_fit"] * authority
        + DEFAULT_WEIGHTS["posthog_conversion_potential"] * conversion
        + DEFAULT_WEIGHTS["internal_link_value"] * links
        + DEFAULT_WEIGHTS["interactivity_advantage"] * interactive
        + DEFAULT_WEIGHTS["confidence"] * confidence
        + DEFAULT_WEIGHTS["execution_complexity"] * complexity
        + DEFAULT_WEIGHTS["privacy_risk"] * privacy
        + DEFAULT_WEIGHTS["seo_risk"] * seo
    )
    return OpportunityScore(
        expected_value_score=round(clamp(expected), 4),
        money_potential_score=round(conversion, 4),
        traffic_potential_score=round(search, 4),
        search_demand_score=search,
        serp_weakness_score=serp,
        topical_authority_fit_score=authority,
        posthog_conversion_potential_score=conversion,
        internal_link_value_score=links,
        interactivity_advantage_score=interactive,
        execution_complexity_score=complexity,
        privacy_risk_score=privacy,
        seo_risk_score=seo,
        confidence_score=confidence,
    )


def build_opportunities_from_inventory(rows: list[dict[str, Any]], metrics: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    metrics = metrics or {}
    opportunities: list[dict[str, Any]] = []
    for row in rows:
        if row.get("content_type") not in {"blog_article", "landing_page", "interactive_tool"}:
            continue
        word_count = int(row.get("word_count") or 0)
        links = int(row.get("internal_link_count") or 0)
        schema_count = len(row.get("schema_types") or [])
        conversion_signal = float(metrics.get(row["url_path"], {}).get("conversion_score", 0.35))
        title_text = f"{row.get('title') or ''} {row.get('primary_keyword') or ''}".lower()
        practice_intent = any(term in title_text for term in PRACTICE_INTENT_TERMS)
        signals = {
            "search_demand": 0.55 if row.get("content_type") == "blog_article" else 0.45,
            "serp_weakness": 0.65 if practice_intent and schema_count == 0 else (0.4 if schema_count == 0 else 0.2),
            "topical_authority_fit": 0.65 if row.get("topic_cluster") != "allgemein" else 0.35,
            "posthog_conversion_potential": max(conversion_signal, 0.55 if practice_intent else conversion_signal),
            "internal_link_value": 0.7 if links < 5 else 0.35,
            "interactivity_advantage": 0.9 if practice_intent else (0.75 if any(k in (row.get("title") or "").lower() for k in ["rechner", "test", "plan", "check"]) else 0.3),
            "execution_complexity": 0.35 if row.get("content_type") == "blog_article" else 0.55,
            "privacy_risk": 0.1,
            "seo_risk": 0.2 if word_count < 500 else 0.1,
            "confidence": 0.55,
        }
        score = score_opportunity(signals)
        kind = "practice_asset_opportunity" if practice_intent else ("content_refresh" if word_count < 700 or links < 3 else "internal_link_improvement")
        if row.get("content_type") == "landing_page":
            kind = "conversion_optimization"
        opp_id = "opp_" + hashlib.sha1(f"{kind}:{row['url_path']}".encode("utf-8")).hexdigest()[:16]
        opportunities.append({
            "id": opp_id,
            "type": kind,
            "asset_type": "practice_page" if practice_intent else None,
            "topic_cluster": row.get("topic_cluster"),
            "primary_keyword": row.get("primary_keyword"),
            "intent": row.get("search_intent"),
            "target_url": row.get("url_path"),
            "evidence": [{"source": "content_inventory", "summary": f"word_count={word_count}, internal_links={links}, schema={schema_count}"}],
            **score.__dict__,
            "status": "scored",
            "next_action": "queue_blog_task" if kind == "content_refresh" else "review_internal_links",
            "created_by": "goal_agent",
        })
    return sorted(opportunities, key=lambda item: item["expected_value_score"], reverse=True)
