from __future__ import annotations

import hashlib

from ..storage import Database, json_dumps, utc_now
from .base import Recommendation, SubagentResult
from .blog_brief import BlogBriefAgent
from .content_gap import ContentGapAgent
from .internal_linking import InternalLinkingAgent
from .practice_asset import PracticeAssetAgent
from .quality_guardian import QualityGuardianAgent
from .review_agent import ReviewAgent
from .seo_intelligence import SEOIntelligenceAgent


DEFAULT_SUBAGENTS = [
    SEOIntelligenceAgent(),
    ContentGapAgent(),
    PracticeAssetAgent(),
    InternalLinkingAgent(),
    BlogBriefAgent(),
    ReviewAgent(),
]


class GoalOrchestrator:
    def __init__(self, db: Database):
        self.db = db

    def run(self, context: dict, persist: bool = True) -> dict:
        results: list[SubagentResult] = []
        recommendations: list[Recommendation] = []
        for agent in DEFAULT_SUBAGENTS:
            result = agent.run(context)
            results.append(result)
            recommendations.extend(result.recommendations)
        guardian_context = dict(context)
        guardian_context["candidate_recommendations"] = recommendations
        guardian_result = QualityGuardianAgent().run(guardian_context)
        results.append(guardian_result)
        recommendations.extend(guardian_result.recommendations)
        if persist:
            self._store_results(results)
        top = sorted(recommendations, key=lambda rec: (rec.priority, rec.confidence), reverse=True)
        return {
            "agents_run": [result.agent_name for result in results],
            "recommendations": top,
            "blocked_recommendations": [rec for rec in top if rec.recommendation_type == "hold"],
            "quality_guardian_decisions": guardian_result.recommendations,
        }

    def _store_results(self, results: list[SubagentResult]) -> None:
        now = utc_now()
        with self.db.connect() as conn:
            for result in results:
                run_id = "subagent_run_" + hashlib.sha1(f"{result.agent_name}:{now}".encode("utf-8")).hexdigest()[:16]
                conn.execute(
                    """
                    insert into subagent_runs (id, agent_name, status, confidence, priority, risks_json, safety_notes_json, recommendation_count, created_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, result.agent_name, result.status, result.confidence, result.priority, json_dumps(result.risks), json_dumps(result.safety_notes), len(result.recommendations), now),
                )
                for rec in result.recommendations:
                    conn.execute(
                        """
                        insert into subagent_recommendations (
                          id, source_agent, recommendation_type, title, rationale, priority,
                          confidence, target_topic, target_url, suggested_publish_decision,
                          codex_task_allowed, safety_risk, acceptance_criteria_json,
                          required_context_json, created_at, status
                        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        on conflict(id) do update set
                          priority=excluded.priority,
                          confidence=excluded.confidence,
                          status=excluded.status
                        """,
                        (
                            rec.id,
                            rec.source_agent,
                            rec.recommendation_type,
                            rec.title,
                            rec.rationale,
                            rec.priority,
                            rec.confidence,
                            rec.target_topic,
                            rec.target_url,
                            rec.suggested_publish_decision,
                            1 if rec.codex_task_allowed else 0,
                            rec.safety_risk,
                            json_dumps(rec.acceptance_criteria),
                            json_dumps(rec.required_context),
                            rec.created_at,
                            "queued",
                        ),
                    )
