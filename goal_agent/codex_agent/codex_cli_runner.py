from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..config import Settings
from ..storage import Database, json_dumps, utc_now
from .prompt_builder import build_codex_prompt
from .result_parser import parse_result
from .safety import dirty_worktree_blockers, git_status_short, validate_task_safety
from .task_schema import CodingTask


@dataclass(frozen=True)
class CodexRunResult:
    status: str
    exit_code: int | None
    stdout_summary: str
    stderr_summary: str
    changed_files: list[str]
    failure_reason: str
    safety_blocked: bool


class CodexCliRunner:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def run_task(self, task: CodingTask, allow_dirty_worktree: bool = False, force_enabled: bool = False, dry_run: bool = False) -> CodexRunResult:
        problems = validate_task_safety(task)
        if problems:
            return self._record_blocked(task, "; ".join(problems))
        if not (self.settings.codex_enabled or force_enabled) and not dry_run:
            return self._record_blocked(task, "Codex execution disabled. Set GOAL_AGENT_CODEX_ENABLED=true or use explicit CLI flag.")
        if shutil.which(self.settings.codex_bin) is None:
            return self._record_blocked(task, f"Codex binary not found: {self.settings.codex_bin}")
        if not (allow_dirty_worktree or self.settings.codex_allow_dirty_worktree):
            blockers = dirty_worktree_blockers(self.settings.repo_root)
            if blockers:
                return self._record_blocked(task, "; ".join(blockers))
        prompt = build_codex_prompt(task)
        if dry_run:
            return self._record_run(task, "completed", None, prompt[:1200], "", [], "", False, prompt_summary=prompt[:1200])
        if self.settings.codex_create_branch:
            subprocess.run(["git", "switch", "-c", f"goal-agent/codex-task-{task.id}"], cwd=self.settings.repo_root, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cmd = [
            self.settings.codex_bin,
            "exec",
            "--cd",
            str(self.settings.repo_root),
            "--sandbox",
            self.settings.codex_sandbox_mode,
            "--json",
            "-",
        ]
        started = utc_now()
        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                cwd=self.settings.repo_root,
                capture_output=True,
                timeout=self.settings.codex_timeout_seconds,
                check=False,
            )
            parsed = parse_result(self.settings.repo_root, proc.stdout, proc.stderr, proc.returncode)
            status = "completed" if proc.returncode == 0 and not parsed.failure_reason else "failed"
            safety_blocked = parsed.safety_blocked if status != "completed" else False
            return self._record_run(task, status, proc.returncode, parsed.stdout_summary, parsed.stderr_summary, parsed.changed_files, parsed.failure_reason, safety_blocked, started)
        except subprocess.TimeoutExpired as exc:
            parsed = parse_result(self.settings.repo_root, exc.stdout or "", exc.stderr or "", None, timed_out=True)
            return self._record_run(task, "failed", None, parsed.stdout_summary, parsed.stderr_summary, parsed.changed_files, "timeout", parsed.safety_blocked, started)

    def _record_blocked(self, task: CodingTask, reason: str) -> CodexRunResult:
        return self._record_run(task, "blocked_by_safety", None, "", "", [], reason, True)

    def _record_run(
        self,
        task: CodingTask,
        status: str,
        exit_code: int | None,
        stdout: str,
        stderr: str,
        changed_files: list[str],
        failure_reason: str,
        safety_blocked: bool,
        started_at: str | None = None,
        prompt_summary: str = "",
    ) -> CodexRunResult:
        run_id = "coding_run_" + hashlib.sha1(f"{task.id}:{utc_now()}".encode("utf-8")).hexdigest()[:16]
        status_short = git_status_short(self.settings.repo_root)
        try:
            diff_stat = subprocess.check_output(["git", "diff", "--stat"], cwd=self.settings.repo_root, text=True)
        except Exception:  # noqa: BLE001
            diff_stat = ""
        with self.db.connect() as conn:
            conn.execute(
                """
                insert into coding_task_runs (
                  id, task_id, status, started_at, finished_at, exit_code,
                  stdout_summary, stderr_summary, changed_files_json, git_diff_stat,
                  git_status_short, tests_run_json, failure_reason, safety_blocked,
                  prompt_summary, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    task.id,
                    status,
                    started_at or utc_now(),
                    utc_now(),
                    exit_code,
                    stdout,
                    stderr,
                    json_dumps(changed_files),
                    diff_stat,
                    status_short,
                    json.dumps(task.test_commands, ensure_ascii=False),
                    failure_reason,
                    1 if safety_blocked else 0,
                    prompt_summary[:1200],
                    utc_now(),
                ),
            )
            conn.execute("update coding_tasks set status=?, updated_at=? where id=?", (status if status in {"completed", "failed", "blocked_by_safety"} else "running", utc_now(), task.id))
            if changed_files:
                conn.execute("update coding_tasks set changed_files_json=?, result_summary=? where id=?", (json_dumps(changed_files), failure_reason or status, task.id))
        return CodexRunResult(status, exit_code, stdout, stderr, changed_files, failure_reason, safety_blocked)
