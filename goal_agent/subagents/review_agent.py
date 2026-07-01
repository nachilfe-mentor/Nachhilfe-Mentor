from __future__ import annotations

import subprocess
from pathlib import Path

from .base import Recommendation, Subagent, SubagentResult, rec_id


class ReviewAgent(Subagent):
    agent_name = "review_agent"

    def run(self, context: dict) -> SubagentResult:
        repo_root = context.get("repo_root")
        recs: list[Recommendation] = []

        if not repo_root:
            return SubagentResult(self.agent_name, "ok", recs, 0.8, 90)

        # 1. Guard: detect unexpected changes to sensitive scripts
        try:
            status = subprocess.check_output(["git", "status", "--short"], cwd=repo_root, text=True)
        except Exception:
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

        # 2. Detect drafts stuck in noindex for > 21 days without promotion
        entwuerfe = Path(repo_root) / "lernmaterialien" / "entwuerfe"
        if entwuerfe.exists():
            import time
            now = time.time()
            for html in entwuerfe.glob("*.html"):
                age_days = (now - html.stat().st_mtime) / 86400
                if age_days > 21:
                    recs.append(Recommendation(
                        id=rec_id(self.agent_name, f"stale_draft:{html.name}"),
                        source_agent=self.agent_name,
                        recommendation_type="quality_fix",
                        title=f"Stale draft: {html.name} ({int(age_days)}d in noindex)",
                        rationale=f"Draft has been in lernmaterialien/entwuerfe/ for {int(age_days)} days without promotion. Either fix quality issues and promote, or delete.",
                        priority=70,
                        confidence=0.85,
                        target_topic="draft_quality",
                        target_url=f"lernmaterialien/entwuerfe/{html.name}",
                        suggested_publish_decision="hold",
                        codex_task_allowed=True,
                        safety_risk="low",
                        acceptance_criteria=[
                            "Either the draft passes the quality gate and is promoted, or it is deleted with a reason logged.",
                            "No file stays in entwuerfe/ beyond 30 days without a decision.",
                        ],
                        required_context=["draft path", "promotion quality gate"],
                    ))

        # 3. Detect topic cluster imbalance from content inventory
        content_rows = context.get("content_rows", [])
        cluster_counts: dict[str, int] = {}
        for row in content_rows:
            if row.get("content_type") == "blog_article":
                cluster = row.get("topic_cluster") or "allgemein"
                cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1
        if cluster_counts:
            max_count = max(cluster_counts.values())
            for cluster, count in cluster_counts.items():
                if cluster != "allgemein" and count < 3 and max_count >= 10:
                    recs.append(Recommendation(
                        id=rec_id(self.agent_name, f"thin_cluster:{cluster}"),
                        source_agent=self.agent_name,
                        recommendation_type="create_blog_brief",
                        title=f"Thin topic cluster: {cluster} ({count} article{'s' if count != 1 else ''})",
                        rationale=f"Cluster '{cluster}' has only {count} article(s) vs. {max_count} in the dominant cluster. Topical authority requires breadth.",
                        priority=55,
                        confidence=0.75,
                        target_topic=cluster,
                        target_url=None,
                        suggested_publish_decision="hold",
                        codex_task_allowed=False,
                        safety_risk="low",
                        acceptance_criteria=[f"At least one new article queued for '{cluster}' cluster."],
                        required_context=["blog registry", "topic_cluster distribution"],
                    ))

        return SubagentResult(self.agent_name, "ok", recs[:8], 0.82, 85)
