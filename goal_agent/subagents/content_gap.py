from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class ContentGapAgent(Subagent):
    agent_name = "content_gap"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        for row in context.get("content_rows", [])[:80]:
            if row.get("content_type") == "blog_article" and int(row.get("word_count") or 0) < 800:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, row["url_path"]),
                    source_agent=self.agent_name,
                    recommendation_type="update_existing_content",
                    title=f"Improve thin content: {row.get('title') or row['url_path']}",
                    rationale="Page is relatively thin and may need examples, exercises, or clearer structure.",
                    priority=60,
                    confidence=0.65,
                    target_topic=row.get("topic_cluster") or "allgemein",
                    target_url=row["url_path"],
                    suggested_publish_decision="hold",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["No article rewrite by Goal Agent.", "Create a review/spec or safe improvement task.", "Tests pass."],
                    required_context=["content_inventory"],
                ))
        return SubagentResult(self.agent_name, "ok", recs[:10], 0.65, 60)
