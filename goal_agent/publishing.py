from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PublishingDecision:
    opportunity_id: str
    action: str
    indexable: bool
    reasons: list[str]
    quality_adjusted_score: float


class AdaptivePublishingThrottle:
    """Quality-first adaptive publishing gate.

    This is not a fixed daily publishing quota. It allows higher output when
    quality, uniqueness, indexing, engagement, and conversion signals are good.
    It slows output to draft/noindex or hold when risk rises. The emergency cap
    exists only as a runaway-process fallback.
    """

    def __init__(self, emergency_cap: int = 50):
        self.emergency_cap = max(1, emergency_cap)

    def decide(
        self,
        opportunities: list[dict[str, Any]],
        content_rows: list[dict[str, Any]],
        site_signals: dict[str, Any] | None = None,
    ) -> list[PublishingDecision]:
        site_signals = site_signals or {}
        cluster_counts = Counter(row.get("topic_cluster") or "allgemein" for row in content_rows)
        keyword_counts = Counter((row.get("primary_keyword") or "").lower().strip() for row in content_rows if row.get("primary_keyword"))
        decisions: list[PublishingDecision] = []
        for opp in opportunities:
            reasons: list[str] = []
            expected = float(opp.get("expected_value_score", 0.0) or 0.0)
            privacy_risk = float(opp.get("privacy_risk_score", 1.0) or 1.0)
            seo_risk = float(opp.get("seo_risk_score", 1.0) or 1.0)
            confidence = float(opp.get("confidence_score", 0.0) or 0.0)
            keyword = (opp.get("primary_keyword") or "").lower().strip()
            cluster = opp.get("topic_cluster") or "allgemein"
            intent = opp.get("intent") or ""
            duplicate_score = min(1.0, keyword_counts.get(keyword, 0) / 3.0)
            cluster_saturation = min(1.0, cluster_counts.get(cluster, 0) / 80.0)
            indexing_health = float(site_signals.get("indexing_health", 0.7))
            engagement_health = float(site_signals.get("engagement_health", 0.7))
            conversion_health = float(site_signals.get("conversion_health", 0.7))
            quality_adjusted = expected
            quality_adjusted += 0.12 * confidence
            quality_adjusted += 0.10 * conversion_health
            quality_adjusted += 0.05 * engagement_health
            quality_adjusted += 0.05 * indexing_health
            quality_adjusted -= 0.25 * duplicate_score
            quality_adjusted -= 0.15 * cluster_saturation
            quality_adjusted -= 0.30 * seo_risk
            quality_adjusted -= 0.30 * privacy_risk
            if not intent:
                reasons.append("missing clear search intent")
            if duplicate_score > 0.5:
                reasons.append("duplicate intent or cannibalization risk")
            if seo_risk > 0.25:
                reasons.append("seo risk too high")
            if privacy_risk > 0.2:
                reasons.append("privacy risk too high")
            if quality_adjusted >= 0.45 and not reasons:
                action = "publish_indexable"
                indexable = True
                reasons.append("quality-adjusted signals support indexing")
            elif quality_adjusted >= 0.25 and privacy_risk <= 0.2 and seo_risk <= 0.35:
                action = "draft_noindex"
                indexable = False
                reasons.append("needs stronger uniqueness, indexing, engagement, or conversion evidence")
            else:
                action = "hold"
                indexable = False
                reasons.append("quality-adjusted score too low")
            decisions.append(PublishingDecision(opp["id"], action, indexable, reasons, round(max(0.0, min(1.0, quality_adjusted)), 4)))

        active_count = 0
        capped: list[PublishingDecision] = []
        for decision in decisions:
            if decision.action in {"publish_indexable", "draft_noindex"}:
                active_count += 1
            if active_count > self.emergency_cap:
                capped.append(PublishingDecision(decision.opportunity_id, "hold", False, ["emergency runaway cap reached"], decision.quality_adjusted_score))
            else:
                capped.append(decision)
        return capped
