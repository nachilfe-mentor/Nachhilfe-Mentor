from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .safety import sanitize_for_log


@dataclass(frozen=True)
class ParsedResult:
    stdout_summary: str
    stderr_summary: str
    changed_files: list[str]
    git_diff_stat: str
    git_status_short: str
    safety_blocked: bool
    failure_reason: str


def _run_git(repo_root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:  # noqa: BLE001
        return f"git command failed: {exc.__class__.__name__}"


def parse_result(repo_root: Path, stdout: str, stderr: str, exit_code: int | None, timed_out: bool = False) -> ParsedResult:
    status = _run_git(repo_root, ["status", "--short"])
    diff_stat = _run_git(repo_root, ["diff", "--stat"])
    changed = []
    for line in status.splitlines():
        if not line.strip():
            continue
        changed.append(line[3:] if len(line) > 3 else line.strip())
    combined = f"{stdout}\n{stderr}".lower()
    safety_blocked = "safety gate" in combined or "blocked_by_safety" in combined or "blocked by safety" in combined
    failure = ""
    if timed_out:
        failure = "timeout"
    elif exit_code not in (0, None):
        failure = f"exit_{exit_code}"
    return ParsedResult(
        stdout_summary=sanitize_for_log(stdout),
        stderr_summary=sanitize_for_log(stderr),
        changed_files=changed[:200],
        git_diff_stat=sanitize_for_log(diff_stat),
        git_status_short=sanitize_for_log(status),
        safety_blocked=safety_blocked,
        failure_reason=failure,
    )
