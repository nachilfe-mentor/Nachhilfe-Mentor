from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class BlogBriefAgent(Subagent):
    agent_name = "blog_brief"

    def run(self, context: dict) -> SubagentResult:
        recs = []
        for opp in context.get("opportunities", [])[:10]:
            if opp.get("type") != "practice_asset_opportunity":
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, opp["id"]),
                    source_agent=self.agent_name,
                    recommendation_type="create_blog_brief",
                    title=f"Create better Blog Agent brief: {opp.get('primary_keyword')}",
                    rationale="The Blog Agent should receive evidence-backed briefs while remaining a pure blog writer.",
                    priority=min(90, int(opp.get("expected_value_score", 0.5) * 100)),
                    confidence=0.72,
                    target_topic=opp.get("topic_cluster") or "allgemein",
                    target_url=opp.get("target_url"),
                    suggested_publish_decision="hold",
                    codex_task_allowed=False,
                    safety_risk="low",
                    acceptance_criteria=["Brief only, no article writing.", "No Blog Agent script change.", "Queue remains structured."],
                    required_context=["opportunity", "blog_task_queue"],
                ))
        return SubagentResult(self.agent_name, "ok", recs[:5], 0.72, 65)
