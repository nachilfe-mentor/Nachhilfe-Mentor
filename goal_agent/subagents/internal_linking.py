from __future__ import annotations

from collections import Counter

from .base import Recommendation, Subagent, SubagentResult, rec_id


class InternalLinkingAgent(Subagent):
    agent_name = "internal_linking"

    def run(self, context: dict) -> SubagentResult:
        links = context.get("internal_links", [])
        incoming = Counter(link.target_url if hasattr(link, "target_url") else link.get("target_url") for link in links)
        recs = []
        for row in context.get("content_rows", [])[:120]:
            if row.get("content_type") == "blog_article" and incoming.get(row["url_path"], 0) < 2:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, row["url_path"]),
                    source_agent=self.agent_name,
                    recommendation_type="improve_internal_links",
                    title=f"Improve internal links to {row.get('slug') or row['url_path']}",
                    rationale="Page has weak incoming internal-link support.",
                    priority=55,
                    confidence=0.7,
                    target_topic=row.get("topic_cluster") or "allgemein",
                    target_url=row["url_path"],
                    suggested_publish_decision="hold",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["Suggest editorially useful links only.", "No mass link stuffing.", "Tests pass."],
                    required_context=["internal_link_graph", "content_inventory"],
                ))
        return SubagentResult(self.agent_name, "ok", recs[:10], 0.7, 55)
