from __future__ import annotations

import subprocess

from .base import Recommendation, Subagent, SubagentResult, rec_id


class ReviewAgent(Subagent):
    agent_name = "review_agent"

    def run(self, context: dict) -> SubagentResult:
        repo_root = context.get("repo_root")
        recs = []
        if repo_root:
            try:
                status = subprocess.check_output(["git", "status", "--short"], cwd=repo_root, text=True)
            except Exception:  # noqa: BLE001
                status = ""
            if "auto-blog.sh" in status:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, "auto_blog_dirty"),
                    source_agent=self.agent_name,
                    recommendation_type="quality_fix",
                    title="Review unexpected auto-blog.sh changes",
                    rationale="Blog Agent execution script is sensitive and should not change without explicit review.",
                    priority=95,
                    confidence=0.9,
                    target_topic="blog_agent",
                    target_url=None,
                    suggested_publish_decision="hold",
                    codex_task_allowed=False,
                    safety_risk="high",
                    acceptance_criteria=["Confirm no unsafe Blog Agent script changes."],
                    required_context=["git status"],
                ))
        return SubagentResult(self.agent_name, "ok", recs, 0.8, 90)
