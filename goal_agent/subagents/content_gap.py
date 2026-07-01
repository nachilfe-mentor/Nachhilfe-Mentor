from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class ContentGapAgent(Subagent):
    agent_name = "content_gap"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        content_rows = context.get("content_rows", [])
        data_snapshot = context.get("data_snapshot", {})

        # Build a map of GSC impressions per URL path for priority weighting
        gsc_impressions: dict[str, int] = {}
        for row in data_snapshot.get("gsc", {}).get("queries", []):
            from urllib.parse import urlparse
            path = urlparse(row.get("page") or "").path or "/"
            gsc_impressions[path] = gsc_impressions.get(path, 0) + int(row.get("impressions") or 0)

        for row in content_rows[:100]:
            if row.get("content_type") != "blog_article":
                continue

            url_path = row.get("url_path") or ""
            word_count = int(row.get("word_count") or 0)
            schema_count = len(row.get("schema_types") or [])
            link_count = int(row.get("internal_link_count") or 0)
            impressions = gsc_impressions.get(url_path, 0)
            title = row.get("title") or url_path

            # Thin content — especially bad if the page gets real traffic
            if word_count < 800:
                traffic_note = f", gets {impressions} GSC impressions" if impressions > 20 else ""
                priority = min(85, 55 + int(impressions / 20))  # traffic boosts priority
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, f"thin:{url_path}"),
                    source_agent=self.agent_name,
                    recommendation_type="update_existing_content",
                    title=f"Thin content ({word_count} words){traffic_note}: {title}",
                    rationale=f"Page at {url_path} has only {word_count} words{traffic_note}. Add examples, exercises, or clearer structure.",
                    priority=priority,
                    confidence=0.70,
                    target_topic=row.get("topic_cluster") or "allgemein",
                    target_url=url_path,
                    suggested_publish_decision="hold",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["No article rewrite by Goal Agent.", "Create a review/spec or safe improvement task.", "Tests pass."],
                    required_context=["content_inventory"],
                ))

            # Missing schema on pages with real traffic — SEO low-hanging fruit
            elif schema_count == 0 and impressions > 50:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, f"no_schema:{url_path}"),
                    source_agent=self.agent_name,
                    recommendation_type="update_existing_content",
                    title=f"Missing schema markup ({impressions} impressions): {title}",
                    rationale=f"Page at {url_path} gets {impressions} GSC impressions but has no structured data schema. Adding Article/LearningResource schema can improve CTR.",
                    priority=65,
                    confidence=0.80,
                    target_topic=row.get("topic_cluster") or "allgemein",
                    target_url=url_path,
                    suggested_publish_decision="hold",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["Schema markup added (Article or LearningResource).", "No content rewrite.", "Tests pass."],
                    required_context=["content_inventory", "GSC impressions"],
                ))

            # Orphan pages — good content but no internal links pointing to them
            elif link_count == 0 and impressions > 30:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, f"orphan:{url_path}"),
                    source_agent=self.agent_name,
                    recommendation_type="improve_internal_links",
                    title=f"Orphan page with traffic ({impressions} impressions): {title}",
                    rationale=f"Page at {url_path} gets {impressions} impressions but has no incoming internal links. Link equity is lost.",
                    priority=60,
                    confidence=0.75,
                    target_topic=row.get("topic_cluster") or "allgemein",
                    target_url=url_path,
                    suggested_publish_decision="hold",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=["At least 2 relevant internal links added pointing to this page.", "No keyword stuffing."],
                    required_context=["internal link graph", "content_inventory"],
                ))

        # Sort by priority and cap output
        recs.sort(key=lambda r: r.priority, reverse=True)
        return SubagentResult(self.agent_name, "ok", recs[:12], 0.70, 65)
