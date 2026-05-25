from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .storage import Database, json_dumps, utc_now


CONTEXT_DIR = REPO_ROOT / "goal_agent" / "context"


def _read(name: str) -> str:
    path = CONTEXT_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def retrieve_memory(db: Database, topic: str = "") -> dict[str, Any]:
    pattern = f"%{topic}%" if topic else "%"
    ideas = db.query(
        "select id, type, topic_cluster, primary_keyword, expected_value_score, status from ideas where primary_keyword like ? or topic_cluster like ? order by expected_value_score desc limit 10",
        (pattern, pattern),
    )
    learnings = db.query(
        "select id, claim, confidence, status from learnings where status='active' order by confidence desc limit 10"
    )
    runs = db.query(
        "select id, cycle_type, status, started_at, summary from agent_runs order by started_at desc limit 5"
    )
    return {
        "ideas": [dict(row) for row in ideas],
        "learnings": [dict(row) for row in learnings],
        "recent_runs": [dict(row) for row in runs],
    }


def build_context(db: Database, run_id: str, task_context: dict[str, Any]) -> dict[str, Any]:
    context = {
        "constitution": _read("constitution.md"),
        "strategy_snapshot": _read("strategy_snapshot.md"),
        "retrieved_memory": retrieve_memory(db, task_context.get("topic", "")),
        "data_snapshot": task_context.get("data_snapshot", {}),
        "task_context": task_context,
        "tool_registry": _read("../tools/registry.json"),
        "run_history_summary": retrieve_memory(db).get("recent_runs", []),
    }
    digest = hashlib.sha256(json_dumps(context).encode("utf-8")).hexdigest()
    with db.connect() as conn:
        conn.execute(
            "insert into context_snapshots (id, agent_run_id, context_type, content_sha256, summary, created_at) values (?, ?, ?, ?, ?, ?)",
            (f"ctx_{digest[:16]}", run_id, "full_structured_context", digest, "Structured context assembled without one giant runtime prompt.", utc_now()),
        )
    return context
