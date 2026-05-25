from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .task_schema import CodingTask


BLOCKED_PROMPT_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bdeploy\b",
    r"\bdeployment\b",
    r"\brm\s+-rf\s+/",
    r"\breset\s+--hard\b",
    r"\bcheckout\s+--\s+\.",
    r"\bIndexNow\b.*\bsubmit\b",
    r"\bprint\s+.*secret",
    r"\bcat\s+.*\.env\b",
    r"\bcat\s+.*service-account.*\.json\b",
]

DEFAULT_FORBIDDEN = [
    ".env",
    "*.env",
    "google-analytics-sa.json",
    "*service-account*.json",
    ".git/",
    "auto-blog.sh",
]


def validate_task_safety(task: CodingTask) -> list[str]:
    problems = task.validate()
    haystack = "\n".join([
        task.title,
        task.goal,
        task.context_summary,
        "\n".join(task.test_commands),
    ])
    for pattern in BLOCKED_PROMPT_PATTERNS:
        if re.search(pattern, haystack, flags=re.I):
            problems.append(f"blocked risky instruction: {pattern}")
    if task.publish_policy == "draft_noindex_only" and task.mode == "modify_repo":
        if not any("draft" in allowed or "goal-agent-pages" in allowed for allowed in task.allowed_paths):
            problems.append("draft_noindex tasks must be limited to draft/generated asset paths")
    if task.task_type != "blog_brief_generation" and any(path == "auto-blog.sh" for path in task.allowed_paths):
        problems.append("auto-blog.sh may only be allowed for explicit blog_agent_improvement tasks")
    return problems


def git_status_short(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "status", "--short"], cwd=repo_root, text=True)
    except Exception:  # noqa: BLE001
        return ""


def dirty_worktree_blockers(repo_root: Path) -> list[str]:
    status = git_status_short(repo_root).strip()
    return ["dirty worktree"] if status else []


def sanitize_for_log(text: str, max_chars: int = 4000) -> str:
    redacted = re.sub(r"(?i)(phx_|ghp_|github_pat|sk-|BEGIN PRIVATE KEY).*", "[redacted]", text)
    redacted = re.sub(r"(?i)(private_key|client_secret|api_key)\s*[:=].*", r"\1=[redacted]", redacted)
    return redacted[:max_chars]
