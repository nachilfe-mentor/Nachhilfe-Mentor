from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class QualityGuardianAgent(Subagent):
    agent_name = "quality_guardian"

    def run(self, context: dict) -> SubagentResult:
        recs = []
        for rec in context.get("candidate_recommendations", []):
            if rec.safety_risk == "high" or rec.confidence < 0.35 or rec.priority < 25:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, rec.id),
                    source_agent=self.agent_name,
                    recommendation_type="hold",
                    title=f"Hold low-quality or risky recommendation: {rec.title}",
                    rationale="Quality First gate blocked this recommendation because risk is too high or confidence/priority too low.",
                    priority=100,
                    confidence=0.9,
                    target_topic=rec.target_topic,
                    target_url=rec.target_url,
                    suggested_publish_decision="hold",
                    codex_task_allowed=False,
                    safety_risk="medium",
                    acceptance_criteria=["Do not execute until quality/risk improves."],
                    required_context=["quality gate"],
                ))
        return SubagentResult(self.agent_name, "ok", recs, 0.9, 100, safety_notes=["Quality First is the primary publishing rule."])
