from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .storage import Database, json_dumps, utc_now


REQUIRED_TASK_FIELDS = {
    "task_id",
    "task_type",
    "priority",
    "topic",
    "primary_keyword",
    "search_intent",
    "topic_cluster",
    "recommended_angle",
    "evidence",
    "expected_metric",
    "source_agent_run_id",
    "status",
}


def validate_blog_task(task: dict[str, Any]) -> list[str]:
    problems = [f"missing {field}" for field in sorted(REQUIRED_TASK_FIELDS - set(task))]
    if task.get("task_type") not in {"new_topic", "article_refresh", "cluster_expansion", "internal_link_insertion_request", "prompt_template_change_recommendation"}:
        problems.append("invalid task_type")
    priority = task.get("priority")
    if not isinstance(priority, int) or not 0 <= priority <= 100:
        problems.append("priority must be integer 0..100")
    return problems


def task_from_opportunity(opportunity: dict[str, Any], run_id: str) -> dict[str, Any]:
    opp_type = opportunity["type"]
    if opp_type == "content_refresh":
        task_type = "article_refresh"
    elif opp_type == "practice_asset_opportunity":
        task_type = "cluster_expansion"
    elif opp_type == "new_blog_article":
        task_type = "new_topic"
    elif opp_type == "ctr_gap":
        task_type = "article_refresh"
    else:
        task_type = "internal_link_insertion_request"
    slug = (opportunity.get("target_url") or "").rsplit("/", 1)[-1].replace(".html", "")
    angle = opportunity.get("recommended_angle") or "Refresh or link this page based on current SEO evidence; keep the Blog Agent responsible for article writing."
    return {
        "task_id": "blog_task_" + opportunity["id"].replace("opp_", ""),
        "task_type": task_type,
        "priority": int(round(opportunity["expected_value_score"] * 100)),
        "topic": opportunity.get("primary_keyword") or slug,
        "primary_keyword": opportunity.get("primary_keyword") or slug,
        "secondary_keywords": [],
        "search_intent": opportunity.get("intent") or "informational",
        "topic_cluster": opportunity.get("topic_cluster") or "allgemein",
        "recommended_angle": angle,
        "template_version": "blog-task-v1",
        "required_internal_links": [],
        "recommended_cta": "Natural single mention of Nachhilfe Mentor app when useful.",
        "evidence": opportunity.get("evidence", []),
        "expected_metric": "Organic entrances and app CTA clicks after 28 days.",
        "due_window": "next_7_days",
        "source_agent_run_id": run_id,
        "status": "queued",
        "target_slug": slug,
    }


def tasks_from_subagent_recs(db: Database, run_id: str) -> list[dict[str, Any]]:
    """Convert actionable subagent recommendations into blog tasks.

    Subagents like ContentGapAgent produce content_refresh and similar recs
    that were previously stored in the DB but never forwarded to the Blog Agent.
    This bridges that gap for non-Codex recommendation types.
    """
    ELIGIBLE_TYPES = ("content_refresh", "update_existing_content", "create_blog_brief")
    rows = db.query(
        """
        select * from subagent_recommendations
        where status = 'queued'
          and recommendation_type in ('content_refresh', 'update_existing_content', 'create_blog_brief')
          and safety_risk != 'high'
          and priority >= 40
        order by priority desc
        limit 5
        """,
    )
    tasks: list[dict[str, Any]] = []
    for row in rows:
        rec_type = row["recommendation_type"]
        task_type = "article_refresh" if rec_type in {"content_refresh", "update_existing_content"} else "new_topic"
        slug = (row["target_url"] or "").rsplit("/", 1)[-1].replace(".html", "")
        task_id = "blog_task_sa_" + row["id"].replace("rec_", "")[:24]
        tasks.append({
            "task_id": task_id,
            "task_type": task_type,
            "priority": min(100, int(row["priority"])),
            "topic": row["target_topic"] or slug or "allgemein",
            "primary_keyword": row["target_topic"] or slug or "",
            "secondary_keywords": [],
            "search_intent": "informational",
            "topic_cluster": row["target_topic"] or "allgemein",
            "recommended_angle": row["rationale"] or "",
            "template_version": "blog-task-v1",
            "required_internal_links": [],
            "recommended_cta": "Natural single mention of Nachhilfe Mentor app when useful.",
            "evidence": [{"source": f"subagent:{row['source_agent']}", "summary": row["title"]}],
            "expected_metric": "Organic entrances and app CTA clicks after 28 days.",
            "due_window": "next_7_days",
            "source_agent_run_id": run_id,
            "status": "queued",
            "target_slug": slug,
        })
    return tasks


def store_blog_tasks(db: Database, tasks: list[dict[str, Any]]) -> None:
    now = utc_now()
    with db.connect() as conn:
        for task in tasks:
            problems = validate_blog_task(task)
            if problems:
                raise ValueError("; ".join(problems))
            conn.execute(
                """
                insert into blog_tasks (
                  id, task_type, status, priority, topic, topic_cluster, primary_keyword,
                  secondary_keywords_json, search_intent, target_slug, title_hint,
                  recommended_angle, template_version, required_internal_links_json,
                  recommended_cta, evidence_json, expected_metric, due_window,
                  source_agent_run_id, created_by, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                  status=excluded.status,
                  priority=excluded.priority,
                  evidence_json=excluded.evidence_json,
                  updated_at=excluded.updated_at
                """,
                (
                    task["task_id"],
                    task["task_type"],
                    task["status"],
                    task["priority"],
                    task["topic"],
                    task["topic_cluster"],
                    task["primary_keyword"],
                    json_dumps(task.get("secondary_keywords", [])),
                    task["search_intent"],
                    task.get("target_slug"),
                    task.get("title_hint"),
                    task["recommended_angle"],
                    task.get("template_version"),
                    json_dumps(task.get("required_internal_links", [])),
                    task.get("recommended_cta"),
                    json_dumps(task["evidence"]),
                    task["expected_metric"],
                    task.get("due_window"),
                    task["source_agent_run_id"],
                    "goal_agent",
                    now,
                    now,
                ),
            )


def export_blog_tasks(db: Database, repo_root: Path = REPO_ROOT, limit: int = 10) -> tuple[Path, Path]:
    rows = db.query(
        "select * from blog_tasks where status='queued' order by priority desc, created_at desc limit ?",
        (limit,),
    )
    queue_dir = repo_root / "goal_agent" / "queues"
    exports_dir = repo_root / "goal_agent" / "exports"
    queue_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = queue_dir / "blog_tasks.jsonl"
    md_path = exports_dir / "blog_task_snapshot.md"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            payload = {
                "task_id": row["id"],
                "task_type": row["task_type"],
                "priority": row["priority"],
                "topic": row["topic"],
                "primary_keyword": row["primary_keyword"],
                "secondary_keywords": json.loads(row["secondary_keywords_json"] or "[]"),
                "search_intent": row["search_intent"],
                "topic_cluster": row["topic_cluster"],
                "recommended_angle": row["recommended_angle"],
                "template_version": row["template_version"],
                "required_internal_links": json.loads(row["required_internal_links_json"] or "[]"),
                "recommended_cta": row["recommended_cta"],
                "evidence": json.loads(row["evidence_json"] or "[]"),
                "expected_metric": row["expected_metric"],
                "due_window": row["due_window"],
                "source_agent_run_id": row["source_agent_run_id"],
                "status": row["status"],
                "target_slug": row["target_slug"],
            }
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    lines = ["# Goal Agent Blog Task Snapshot", "", f"Generated: {utc_now()}", ""]
    for idx, row in enumerate(rows, 1):
        lines.extend([
            f"## {idx}. {row['id']}",
            "",
            f"- Type: {row['task_type']}",
            f"- Priority: {row['priority']}",
            f"- Cluster: {row['topic_cluster']}",
            f"- Keyword: {row['primary_keyword']}",
            f"- Intent: {row['search_intent']}",
            f"- Target slug: {row['target_slug'] or ''}",
            "",
            row["recommended_angle"] or "",
            "",
            f"Success metric: {row['expected_metric']}",
            "",
        ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return jsonl_path, md_path
