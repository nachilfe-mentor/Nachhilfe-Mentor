from __future__ import annotations

import hashlib

from ..storage import Database, json_dumps, utc_now
from ..subagents.base import Recommendation
from .task_schema import CodingTask


COMMON_SAFETY = [
    "Do not deploy, push, or publish live.",
    "Do not read, print, or commit secrets.",
    "Do not modify .env, /etc/nachhilfe-mentor, or service account JSON files.",
    "Do not modify production data.",
    "Run listed tests or explain why they could not run.",
]


def _task_id(seed: str) -> str:
    return "coding_task_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def task_from_recommendation(rec: Recommendation) -> CodingTask | None:
    if not rec.codex_task_allowed or rec.safety_risk == "high":
        return None
    if rec.recommendation_type == "create_practice_asset":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="practice_page",
            title=f"Draft practice asset: {rec.title}",
            goal="Create a high-quality draft/noindex practice asset spec or page draft. Do not publish it indexable.",
            context_summary=f"{rec.rationale}\nTarget topic: {rec.target_topic}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["goal-agent-pages/drafts/", "goal_agent/exports/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[
                *rec.acceptance_criteria,
                "Generated asset is draft/noindex or spec only.",
                "No live publish, push, deploy, or sitemap indexable inclusion.",
            ],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="draft_noindex_only",
            priority=rec.priority,
        )
    if rec.recommendation_type == "improve_internal_links":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="internal_linking",
            title=f"Draft internal-link improvement: {rec.title}",
            goal="Create a safe internal-link improvement spec or queue item. Do not mass-edit production blog posts.",
            context_summary=f"{rec.rationale}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["goal_agent/exports/", "goal_agent/queues/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[*rec.acceptance_criteria, "No keyword stuffing.", "No mass link insertion."],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="queue_for_review",
            priority=rec.priority,
        )
    if rec.recommendation_type == "update_existing_content":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="quality_fix",
            title=f"Draft content quality fix: {rec.title}",
            goal="Create a review/spec for improving existing content quality. Do not rewrite articles directly.",
            context_summary=f"{rec.rationale}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["goal_agent/exports/", "goal_agent/queues/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[*rec.acceptance_criteria, "Blog Agent remains the article writer."],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="queue_for_review",
            priority=rec.priority,
        )
    if rec.recommendation_type == "quality_fix":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="quality_fix",
            title=f"Quality fix: {rec.title}",
            goal="Implement a safe quality or test improvement if it does not touch forbidden files.",
            context_summary=f"{rec.rationale}\nTarget topic: {rec.target_topic}",
            allowed_paths=["goal_agent/", "tests/goal_agent/", "docs/goal-agent/"],
            forbidden_paths=["auto-blog.sh", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=rec.acceptance_criteria,
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="modify_repo",
            publish_policy="never_publish",
            priority=rec.priority,
        )
    return None


def build_tasks_from_recommendations(recommendations: list[Recommendation], limit: int = 10) -> list[CodingTask]:
    tasks = [task for rec in recommendations for task in [task_from_recommendation(rec)] if task is not None]
    return sorted(tasks, key=lambda task: task.priority, reverse=True)[:limit]


def build_tasks_from_state(db: Database, limit: int = 10) -> list[CodingTask]:
    from ..subagents.base import Recommendation

    rows = db.query("select * from subagent_recommendations where status='queued' and codex_task_allowed=1 and safety_risk != 'high' order by priority desc limit ?", (limit,))
    recs = [
        Recommendation(
            id=row["id"],
            source_agent=row["source_agent"],
            recommendation_type=row["recommendation_type"],
            title=row["title"],
            rationale=row["rationale"],
            priority=row["priority"],
            confidence=row["confidence"],
            target_topic=row["target_topic"] or "",
            target_url=row["target_url"],
            suggested_publish_decision=row["suggested_publish_decision"],
            codex_task_allowed=bool(row["codex_task_allowed"]),
            safety_risk=row["safety_risk"],
            acceptance_criteria=__import__("json").loads(row["acceptance_criteria_json"] or "[]"),
            required_context=__import__("json").loads(row["required_context_json"] or "[]"),
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return build_tasks_from_recommendations(recs, limit)


def store_coding_tasks(db: Database, tasks: list[CodingTask]) -> int:
    now = utc_now()
    count = 0
    with db.connect() as conn:
        for task in tasks:
            problems = task.validate()
            if problems:
                continue
            existing = conn.execute("select status from coding_tasks where id=?", (task.id,)).fetchone()
            status = task.status
            if existing:
                status = existing["status"]
                latest = conn.execute(
                    """
                    select status, failure_reason from coding_task_runs
                    where task_id=?
                    order by created_at desc
                    limit 1
                    """,
                    (task.id,),
                ).fetchone()
                if latest and latest["status"] == "completed":
                    status = "completed"
                elif existing["status"] in {"blocked_by_safety", "failed"}:
                    reason = (latest["failure_reason"] if latest else "") or ""
                    retryable_reasons = (
                        "dirty worktree",
                        "Codex execution disabled",
                        "Codex binary not found",
                        "timeout",
                    )
                    if any(marker in reason for marker in retryable_reasons):
                        status = "queued"
            conn.execute(
                """
                insert into coding_tasks (
                  id, source_recommendation_id, task_type, title, goal, context_summary,
                  target_files_allowed_json, target_files_forbidden_json,
                  acceptance_criteria_json, safety_constraints_json, test_commands_json,
                  mode, publish_policy, created_at, updated_at, status,
                  result_summary, changed_files_json, priority
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                  title=excluded.title,
                  goal=excluded.goal,
                  context_summary=excluded.context_summary,
                  priority=excluded.priority,
                  updated_at=excluded.updated_at,
                  status=excluded.status
                """,
                (
                    task.id,
                    task.source_recommendation_id,
                    task.task_type,
                    task.title,
                    task.goal,
                    task.context_summary,
                    json_dumps(task.allowed_paths),
                    json_dumps(task.forbidden_paths),
                    json_dumps(task.acceptance_criteria),
                    json_dumps(task.safety_constraints),
                    json_dumps(task.test_commands),
                    task.mode,
                    task.publish_policy,
                    task.created_at,
                    now,
                    status,
                    task.result_summary,
                    json_dumps(task.changed_files),
                    task.priority,
                ),
            )
            count += 1
    return count
