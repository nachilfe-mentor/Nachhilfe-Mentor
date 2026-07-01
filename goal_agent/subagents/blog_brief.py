from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class BlogBriefAgent(Subagent):
    agent_name = "blog_brief"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        data_snapshot = context.get("data_snapshot", {})

        # Build GSC signal lookup for enriching briefs with real evidence
        gsc_by_query: dict[str, dict] = {}
        for row in data_snapshot.get("gsc", {}).get("queries", []):
            q = (row.get("query") or "").lower()
            if q and q not in gsc_by_query:
                gsc_by_query[q] = row

        for opp in context.get("opportunities", [])[:10]:
            if opp.get("type") == "practice_asset_opportunity":
                continue

            keyword = (opp.get("primary_keyword") or "").lower()
            gsc_signal = gsc_by_query.get(keyword, {})
            impressions = int(gsc_signal.get("impressions") or 0)
            position = float(gsc_signal.get("position") or 0)
            ctr = float(gsc_signal.get("ctr") or 0)
            gap_type = opp.get("gap_type", "")

            # Build a concrete, evidence-backed brief description
            if impressions > 0:
                gsc_context = (
                    f"GSC: {impressions} Impressionen, Pos. {position:.1f}, CTR {ctr:.1%}. "
                )
            else:
                gsc_context = ""

            if gap_type == "ctr_gap":
                angle = (
                    f"{gsc_context}Artikel existiert, wird aber kaum geklickt. "
                    f"Neuen Titel testen: klarer Mehrwert, Zielgruppe explizit nennen, ggf. Zahl/Jahr ergänzen."
                )
                brief_type = "article_refresh"
                priority = min(88, int(opp.get("expected_value_score", 0.5) * 100) + 10)
            elif gap_type == "position_gap":
                angle = (
                    f"{gsc_context}Kein dedizierter Artikel. "
                    f"Fokussierter Artikel nötig: ein klares Keyword, echte Beispiele, Schema-Markup."
                )
                brief_type = "new_topic"
                priority = min(82, int(opp.get("expected_value_score", 0.5) * 100))
            elif gap_type == "homepage_gap":
                angle = (
                    f"{gsc_context}Suchanfrage landet auf Homepage. "
                    f"Dedizierte Seite oder Landing Page erstellen."
                )
                brief_type = "new_topic"
                priority = min(78, int(opp.get("expected_value_score", 0.5) * 100))
            else:
                angle = (
                    f"{gsc_context}Thema '{keyword}' hat Optimierungspotenzial. "
                    f"Blog Agent sollte echte Beispiele, Übungsaufgaben oder Schema-Markup ergänzen."
                )
                brief_type = "article_refresh"
                priority = min(72, int(opp.get("expected_value_score", 0.5) * 100))

            recs.append(Recommendation(
                id=rec_id(self.agent_name, opp["id"]),
                source_agent=self.agent_name,
                recommendation_type="create_blog_brief",
                title=f"Blog brief ({brief_type}): {keyword}",
                rationale=angle,
                priority=priority,
                confidence=opp.get("confidence_score", 0.65),
                target_topic=opp.get("topic_cluster") or "allgemein",
                target_url=opp.get("target_url"),
                suggested_publish_decision="hold",
                codex_task_allowed=False,
                safety_risk="low",
                acceptance_criteria=[
                    "Brief only — no article writing by Goal Agent.",
                    "No Blog Agent script change.",
                    "Queue entry structured with evidence and angle.",
                ],
                required_context=["opportunity", "gsc_signal", "blog_task_queue"],
            ))

        return SubagentResult(self.agent_name, "ok", recs[:5], 0.74, 68)
