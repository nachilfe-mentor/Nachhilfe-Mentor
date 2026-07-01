from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


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

GSC_PRACTICE_MODIFIERS = [
    "übung",
    "übungen",
    "aufgabe",
    "aufgaben",
    "beispiel",
    "beispiele",
    "lösung",
    "lösungen",
    "aufbau",
    "schreiben",
    "analyse",
    "argumentation",
    "beschreiben",
    "beschreibung",
    "bildbeschreibung",
    "interpretation",
    "zeitungsartikel",
]

PRACTICE_KEYWORD_FILLERS = [
    "übungen",
    "übung",
    "uebungen",
    "uebung",
    "aufgaben",
    "aufgabe",
    "mit lösungen",
    "mit lösung",
    "mit loesungen",
    "mit loesung",
    "lösungen",
    "lösung",
    "loesungen",
    "loesung",
    "beispiele",
    "beispiel",
    "arbeitsblatt",
    "klausur",
    "test",
]

PRACTICE_KEYWORD_SYNONYMS = {
    "bild beschreiben": "bildbeschreibung",
    "bilder beschreiben": "bildbeschreibung",
    "bildbeschreibung schreiben": "bildbeschreibung",
    "ableitungen": "ableitung",
    "vokabel": "vokabeln",
    "vokabeltraining": "vokabeln",
}

HOMEPAGE_PATHS: frozenset[str] = frozenset({"/", "/index.html", ""})

TOPIC_STOPWORDS: frozenset[str] = frozenset({
    "und", "oder", "für", "mit", "ohne", "der", "die", "das", "ein", "eine", "einen",
    "wie", "was", "warum", "wann", "wer", "wozu", "ist", "sind", "kann", "können",
    "app", "kostenlos", "online", "gratis", "im", "in", "auf", "bei", "von", "zu",
    "auch", "noch", "schon", "nur", "mehr", "zum", "zur", "am", "dem", "den",
})


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


def normalize_practice_keyword(keyword: str | None) -> str:
    normalized = (keyword or "").strip().lower()
    normalized = normalized.replace("ß", "ss")
    for phrase, replacement in sorted(PRACTICE_KEYWORD_SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", replacement, normalized)
    for filler in sorted(PRACTICE_KEYWORD_FILLERS, key=len, reverse=True):
        normalized = re.sub(rf"\b{re.escape(filler)}\b", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def dedupe_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    passthrough: list[dict[str, Any]] = []
    for opportunity in opportunities:
        if opportunity.get("type") != "practice_asset_opportunity":
            passthrough.append(opportunity)
            continue
        key = (
            opportunity.get("type") or "",
            opportunity.get("target_url") or "",
            normalize_practice_keyword(opportunity.get("primary_keyword")),
        )
        current = best_by_key.get(key)
        if not current or opportunity.get("expected_value_score", 0) > current.get("expected_value_score", 0):
            best_by_key[key] = opportunity
    return sorted([*passthrough, *best_by_key.values()], key=lambda item: item["expected_value_score"], reverse=True)


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
    return dedupe_opportunities(opportunities)


def _normalize_topic(query: str) -> str:
    """Normalize query to a base topic for clustering similar queries."""
    words = [w for w in re.split(r"\s+", query.lower().strip()) if w and w not in TOPIC_STOPWORDS and len(w) > 2]
    return " ".join(words[:3])


def _infer_topic_cluster(query: str) -> str:
    q = query.lower()
    if any(t in q for t in ["mathe", "mathematik", "gleichung", "rechnen", "geometrie", "algebra", "bruch", "ableitung", "kurvendiskussion", "integral"]):
        return "mathematik"
    if any(t in q for t in ["englisch", "english", "vokabel"]):
        return "englisch"
    if any(t in q for t in ["biologie", "zelle", "evolution", "genetik", "ökologie", "ökosystem"]):
        return "biologie"
    if any(t in q for t in ["physik", "chemie", "atom", "reaktion", "optik", "mechanik"]):
        return "naturwissenschaften"
    if any(t in q for t in ["geschichte", "historisch", "krieg", "revolution", "weimarer", "ns-", "nazi"]):
        return "geschichte"
    if any(t in q for t in ["latein", "französisch", "spanisch", "italienisch", "chinesisch"]):
        return "sprachen"
    return "deutsch"


def build_gsc_keyword_gap_opportunities(
    gsc_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find keyword gaps: queries with real demand but weak/missing content.

    Three gap types:
    - ctr_gap: ranks but almost nobody clicks → title/meta mismatch → article_refresh
    - position_gap: shows up but ranks poorly → new focused article → new_topic
    - homepage_gap: query lands on root without dedicated content → new_topic
    """
    inventory_paths: frozenset[str] = frozenset(row.get("url_path") or "" for row in inventory_rows)
    # Normalized primary keywords of existing content — used for cannibalization check
    existing_keywords: set[str] = {
        normalize_practice_keyword(row.get("primary_keyword") or "")
        for row in inventory_rows
        if row.get("primary_keyword")
    }

    # First pass: classify all candidates
    candidates: list[dict[str, Any]] = []
    for row in gsc_rows:
        query = (row.get("query") or "").strip().lower()
        if not query:
            continue
        impressions = int(row.get("impressions") or 0)
        ctr = float(row.get("ctr") or 0.0)
        position = float(row.get("position") or 0.0)
        path = urlparse(row.get("page") or "").path or "/"

        # Skip practice-modifier queries (handled by build_gsc_practice_opportunities)
        if any(term in query for term in GSC_PRACTICE_MODIFIERS):
            continue
        # Minimum evidence threshold
        if impressions < 25:
            continue
        # Skip already well-performing queries
        if position <= 4 and ctr >= 0.05:
            continue

        on_homepage = path in HOMEPAGE_PATHS
        on_unknown_page = path not in inventory_paths and not on_homepage
        is_ctr_gap = position <= 12 and ctr < 0.015 and impressions >= 50
        is_position_gap = 12 < position <= 35

        if not (on_homepage or is_ctr_gap or is_position_gap):
            continue
        # on_unknown_page (not homepage, not in inventory) is low confidence - skip
        if on_unknown_page and not is_ctr_gap and not is_position_gap:
            continue

        if on_homepage:
            gap_type = "homepage_gap"
            opp_type = "new_blog_article"
        elif is_ctr_gap:
            gap_type = "ctr_gap"
            opp_type = "ctr_gap"
        else:
            gap_type = "position_gap"
            opp_type = "new_blog_article"

        candidates.append({
            "query": query, "impressions": impressions, "ctr": ctr,
            "position": position, "path": path,
            "gap_type": gap_type, "opp_type": opp_type,
            "topic_key": _normalize_topic(query),
        })

    # Second pass: per topic cluster keep only the highest-impression representative
    best_by_topic: dict[str, dict[str, Any]] = {}
    for c in candidates:
        key = c["topic_key"]
        if key not in best_by_topic or c["impressions"] > best_by_topic[key]["impressions"]:
            best_by_topic[key] = c

    # Third pass: build scored opportunities
    opportunities: list[dict[str, Any]] = []
    for c in best_by_topic.values():
        query = c["query"]
        impressions = c["impressions"]
        ctr = c["ctr"]
        position = c["position"]
        path = c["path"]
        gap_type = c["gap_type"]
        opp_type = c["opp_type"]
        topic_cluster = _infer_topic_cluster(query)

        # Cannibalization check: skip new_blog_article if we already have well-matching content
        if opp_type == "new_blog_article":
            norm_query = normalize_practice_keyword(query)
            if any(
                norm_query and existing and (norm_query in existing or existing in norm_query)
                for existing in existing_keywords
            ):
                continue

        if gap_type == "homepage_gap":
            is_brand = any(t in query for t in ["nachhilfe", "mentor", "app", "lernapp"])
            angle = (
                f"Erstelle {'Landing Page' if is_brand else 'Blog-Artikel'} für '{query}' — "
                f"{impressions} Impressionen landen auf der Homepage ohne gezielten Content."
            )
            suggested_intent = "navigational" if is_brand else "informational"
        elif gap_type == "ctr_gap":
            angle = (
                f"Optimiere Titel und Meta Description für '{query}' "
                f"(Pos. {position:.0f}, CTR {ctr:.1%}, {impressions} Impressionen) — "
                f"starkes Ranking ohne Klicks zeigt einen Snippet-Mismatch."
            )
            suggested_intent = "informational"
        else:
            angle = (
                f"Erstelle fokussierten Artikel zu '{query}' — "
                f"Position {position:.0f} mit {impressions} Impressionen zeigt echte Nachfrage ohne starkes Ranking."
            )
            suggested_intent = "informational"

        search_demand = clamp(impressions / 400)
        position_weakness = clamp((position - 3) / 22)
        ctr_weakness = clamp((0.05 - ctr) / 0.05) if ctr < 0.05 else 0.0
        serp_weakness = max(position_weakness, ctr_weakness)
        confidence = 0.75 if impressions >= 100 else (0.62 if impressions >= 50 else 0.50)

        # Intent-adjusted signals: navigational queries convert differently than informational
        if suggested_intent == "navigational":
            conversion_potential = 0.65  # brand/app queries → high conversion if page exists
            interactivity = 0.10         # navigation, not learning
            internal_link = 0.40
        elif gap_type == "ctr_gap":
            conversion_potential = 0.50  # already ranking → fix snippet → conversion improves
            interactivity = 0.25
            internal_link = 0.60
        else:
            conversion_potential = 0.45
            interactivity = 0.20
            internal_link = 0.55

        score = score_opportunity({
            "search_demand": max(0.35, search_demand),
            "serp_weakness": max(0.45, serp_weakness),
            "topical_authority_fit": 0.70 if topic_cluster == "deutsch" else 0.55,
            "posthog_conversion_potential": conversion_potential,
            "internal_link_value": internal_link,
            "interactivity_advantage": interactivity,
            "execution_complexity": 0.45,
            "privacy_risk": 0.05,
            "seo_risk": 0.10 if gap_type == "ctr_gap" else 0.15,
            "confidence": confidence,
        })

        opp_id = "opp_gap_" + hashlib.sha1(f"{gap_type}:{query}".encode("utf-8")).hexdigest()[:16]
        opportunities.append({
            "id": opp_id,
            "type": opp_type,
            "gap_type": gap_type,
            "asset_type": "blog_article",
            "topic_cluster": topic_cluster,
            "primary_keyword": query,
            "intent": suggested_intent,
            "target_url": path if path not in HOMEPAGE_PATHS else None,
            "evidence": [{
                "source": "gsc_keyword_gap",
                "summary": (
                    f"gap_type={gap_type}, impressions={impressions}, "
                    f"ctr={ctr:.4f}, position={position:.1f}, page={path}"
                ),
            }],
            **score.__dict__,
            "status": "scored",
            "next_action": "queue_blog_task",
            "created_by": "goal_agent_gsc_gap",
            "recommended_angle": angle,
        })

    return sorted(opportunities, key=lambda x: x["expected_value_score"], reverse=True)


def build_gsc_practice_opportunities(gsc_rows: list[dict[str, Any]], inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory_by_path = {row.get("url_path"): row for row in inventory_rows}
    opportunities: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in gsc_rows:
        query = (row.get("query") or "").strip().lower()
        if not query:
            continue
        impressions = int(row.get("impressions") or 0)
        ctr = float(row.get("ctr") or 0.0)
        position = float(row.get("position") or 0.0)
        if impressions < 20 or position < 3 or position > 18 or ctr > 0.04:
            continue
        if not any(term in query for term in GSC_PRACTICE_MODIFIERS):
            continue
        path = urlparse(row.get("page") or "").path or "/"
        inventory = inventory_by_path.get(path)
        if not inventory:
            continue
        practice_keyword = query
        if not any(term in query for term in ["übung", "übungen", "aufgabe", "aufgaben", "lösung", "lösungen", "test"]):
            practice_keyword = f"{query} Übungen mit Lösungen"
        key = (normalize_practice_keyword(practice_keyword), path)
        if key in seen:
            continue
        seen.add(key)
        search_demand = clamp(min(1.0, impressions / 1000))
        ctr_gap = clamp((0.04 - ctr) / 0.04)
        position_fit = clamp(1 - abs(position - 8) / 12)
        score = score_opportunity({
            "search_demand": max(0.45, search_demand),
            "serp_weakness": max(0.55, ctr_gap),
            "topical_authority_fit": 0.75,
            "posthog_conversion_potential": 0.6,
            "internal_link_value": 0.7,
            "interactivity_advantage": 0.95,
            "execution_complexity": 0.4,
            "privacy_risk": 0.1,
            "seo_risk": 0.12,
            "confidence": max(0.6, position_fit),
        })
        opp_id = "opp_gsc_" + hashlib.sha1(f"{query}:{path}".encode("utf-8")).hexdigest()[:16]
        opportunities.append({
            "id": opp_id,
            "type": "practice_asset_opportunity",
            "asset_type": "practice_page",
            "topic_cluster": inventory.get("topic_cluster") or "deutsch",
            "primary_keyword": practice_keyword,
            "intent": "practice",
            "target_url": path,
            "evidence": [{
                "source": "gsc",
                "summary": f"query={query}, impressions={impressions}, ctr={ctr:.4f}, position={position:.2f}",
            }],
            **score.__dict__,
            "status": "scored",
            "next_action": "queue_practice_asset",
            "created_by": "goal_agent_gsc",
        })
    return dedupe_opportunities(opportunities)
