from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ..storage import utc_now


TaskType = Literal[
    "practice_page",
    "interactive_asset",
    "blog_brief_generation",
    "internal_linking",
    "seo_tooling",
    "quality_fix",
    "analytics_integration",
    "test_improvement",
    "refactor_safe",
]
TaskMode = Literal["draft_only", "modify_repo", "tests_only"]
PublishPolicy = Literal["never_publish", "draft_noindex_only", "queue_for_review"]
TaskStatus = Literal["queued", "running", "completed", "failed", "blocked_by_safety"]


@dataclass(frozen=True)
class CodingTask:
    id: str
    source_recommendation_id: str
    task_type: TaskType
    title: str
    goal: str
    context_summary: str
    allowed_paths: list[str]
    forbidden_paths: list[str]
    acceptance_criteria: list[str]
    safety_constraints: list[str]
    test_commands: list[str]
    mode: TaskMode
    publish_policy: PublishPolicy
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    status: TaskStatus = "queued"
    result_summary: str | None = None
    changed_files: list[str] = field(default_factory=list)
    priority: int = 50

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.id or not self.id.startswith("coding_task_"):
            problems.append("id must start with coding_task_")
        if not self.title.strip():
            problems.append("title is required")
        if not self.goal.strip():
            problems.append("goal is required")
        if not self.context_summary.strip():
            problems.append("context_summary is required")
        if not self.source_recommendation_id:
            problems.append("source_recommendation_id is required")
        if not self.allowed_paths:
            problems.append("allowed_paths must not be empty")
        if not self.acceptance_criteria:
            problems.append("acceptance_criteria must not be empty")
        if not self.safety_constraints:
            problems.append("safety_constraints must not be empty")
        if not 0 <= self.priority <= 100:
            problems.append("priority must be between 0 and 100")
        if self.publish_policy != "never_publish" and self.task_type not in {"practice_page", "interactive_asset", "internal_linking", "blog_brief_generation"}:
            problems.append("publish_policy must be never_publish for tooling/refactor/test tasks")
        return problems

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


def task_from_row(row: Any) -> CodingTask:
    return CodingTask(
        id=row["id"],
        source_recommendation_id=row["source_recommendation_id"] or "",
        task_type=row["task_type"],
        title=row["title"],
        goal=row["goal"],
        context_summary=row["context_summary"],
        allowed_paths=json.loads(row["target_files_allowed_json"] or "[]"),
        forbidden_paths=json.loads(row["target_files_forbidden_json"] or "[]"),
        acceptance_criteria=json.loads(row["acceptance_criteria_json"] or "[]"),
        safety_constraints=json.loads(row["safety_constraints_json"] or "[]"),
        test_commands=json.loads(row["test_commands_json"] or "[]"),
        mode=row["mode"],
        publish_policy=row["publish_policy"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=row["status"],
        priority=row["priority"],
        result_summary=row["result_summary"] if "result_summary" in row.keys() else None,
        changed_files=json.loads(row["changed_files_json"] or "[]") if "changed_files_json" in row.keys() else [],
    )
