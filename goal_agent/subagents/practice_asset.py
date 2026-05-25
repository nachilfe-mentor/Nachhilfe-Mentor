from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


PRACTICE_TERMS = ["übungen", "aufgaben", "lösungen", "test", "klausur", "arbeitsblatt", "abi"]


class PracticeAssetAgent(Subagent):
    agent_name = "practice_asset"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        for opp in context.get("opportunities", [])[:50]:
            text = f"{opp.get('primary_keyword') or ''} {opp.get('target_url') or ''}".lower()
            if opp.get("type") == "practice_asset_opportunity" or any(term in text for term in PRACTICE_TERMS):
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, opp["id"]),
                    source_agent=self.agent_name,
                    recommendation_type="create_practice_asset",
                    title=f"Draft practice page: {opp.get('primary_keyword')}",
                    rationale="Query intent suggests exercises, tests, worksheets, or solutions. A practice-first asset can provide stronger learning value than another article.",
                    priority=min(100, int(opp.get("expected_value_score", 0.5) * 100) + 10),
                    confidence=0.75,
                    target_topic=opp.get("topic_cluster") or "allgemein",
                    target_url=opp.get("target_url"),
                    suggested_publish_decision="draft_noindex",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=[
                        "Draft/noindex only.",
                        "Visible German text uses correct umlauts.",
                        "Includes exercises, solutions, difficulty progression, internal links, schema and tracking.",
                    ],
                    required_context=["opportunity", "quality rules", "practice-first rules"],
                ))
        return SubagentResult(self.agent_name, "ok", recs[:10], 0.75, 75)
