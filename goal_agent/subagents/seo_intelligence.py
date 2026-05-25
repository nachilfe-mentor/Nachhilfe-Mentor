from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class SEOIntelligenceAgent(Subagent):
    agent_name = "seo_intelligence"

    def run(self, context: dict) -> SubagentResult:
        data = context.get("data_snapshot", {})
        gsc_warning = data.get("gsc_warning", "")
        recommendations: list[Recommendation] = []
        if "lacks Search Console property access" in gsc_warning or "http_403" in gsc_warning:
            recommendations.append(Recommendation(
                id=rec_id(self.agent_name, "gsc_access"),
                source_agent=self.agent_name,
                recommendation_type="quality_fix",
                title="Fix Google Search Console service-account access",
                rationale="GSC configured, but service account lacks Search Console property access.",
                priority=85,
                confidence=0.95,
                target_topic="gsc",
                target_url=None,
                suggested_publish_decision="hold",
                codex_task_allowed=False,
                safety_risk="medium",
                acceptance_criteria=["Service account is added to the Search Console property.", "Connector returns aggregate rows without 403."],
                required_context=["GSC_SITE_URL", "service account email"],
            ))
        for opp in context.get("opportunities", [])[:5]:
            if opp.get("type") == "practice_asset_opportunity":
                recommendations.append(Recommendation(
                    id=rec_id(self.agent_name, opp["id"]),
                    source_agent=self.agent_name,
                    recommendation_type="create_practice_asset",
                    title=f"Create practice-first asset for {opp.get('primary_keyword')}",
                    rationale="Practice intent plus SEO opportunity indicates a useful non-blog asset.",
                    priority=int(opp.get("expected_value_score", 0.5) * 100),
                    confidence=opp.get("confidence_score", 0.6),
                    target_topic=opp.get("topic_cluster") or "allgemein",
                    target_url=opp.get("target_url"),
                    suggested_publish_decision="draft_noindex",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["Draft/noindex only.", "Real exercises and solutions.", "Quality gate passes."],
                    required_context=["content inventory", "opportunity score"],
                ))
        return SubagentResult(self.agent_name, "ok", recommendations, 0.8, 80, safety_notes=["GSC failures are non-fatal."])
