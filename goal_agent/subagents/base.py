from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ..storage import utc_now


RecommendationType = Literal[
    "create_practice_asset",
    "create_blog_brief",
    "improve_internal_links",
    "update_existing_content",
    "create_tool_spec",
    "quality_fix",
    "hold",
]
PublishDecision = Literal["publish_indexable", "draft_noindex", "hold"]
SafetyRisk = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Recommendation:
    id: str
    source_agent: str
    recommendation_type: RecommendationType
    title: str
    rationale: str
    priority: int
    confidence: float
    target_topic: str
    target_url: str | None
    suggested_publish_decision: PublishDecision
    codex_task_allowed: bool
    safety_risk: SafetyRisk
    acceptance_criteria: list[str]
    required_context: list[str]
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.id:
            problems.append("id is required")
        if not 0 <= self.priority <= 100:
            problems.append("priority must be 0..100")
        if not 0 <= self.confidence <= 1:
            problems.append("confidence must be 0..1")
        if self.safety_risk == "high" and self.codex_task_allowed:
            problems.append("high-risk recommendations cannot allow Codex tasks by default")
        if not self.acceptance_criteria:
            problems.append("acceptance_criteria required")
        return problems

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubagentResult:
    agent_name: str
    status: str
    recommendations: list[Recommendation]
    confidence: float
    priority: int
    risks: list[str] = field(default_factory=list)
    suggested_tasks: list[str] = field(default_factory=list)
    suggested_codex_tasks: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recommendations"] = [rec.to_dict() for rec in self.recommendations]
        return data


class Subagent:
    agent_name = "base"

    def run(self, context: dict[str, Any]) -> SubagentResult:
        raise NotImplementedError


def rec_id(source_agent: str, seed: str) -> str:
    return "rec_" + hashlib.sha1(f"{source_agent}:{seed}".encode("utf-8")).hexdigest()[:16]
