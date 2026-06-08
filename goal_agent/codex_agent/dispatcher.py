from __future__ import annotations

from ..config import Settings
from ..storage import Database
from .codex_cli_runner import CodexCliRunner, CodexRunResult
from .task_builder import build_tasks_from_state, retire_obsolete_coding_tasks, store_coding_tasks
from .task_schema import CodingTask, task_from_row


def build_and_store_tasks(db: Database, limit: int = 10) -> int:
    retire_obsolete_coding_tasks(db)
    stored = store_coding_tasks(db, build_tasks_from_state(db, limit))
    retire_obsolete_coding_tasks(db)
    return stored


def list_tasks(db: Database, status: str | None = None) -> list[CodingTask]:
    if status:
        rows = db.query("select * from coding_tasks where status=? order by priority desc, created_at desc", (status,))
    else:
        rows = db.query("select * from coding_tasks order by priority desc, created_at desc")
    return [task_from_row(row) for row in rows]


def get_task(db: Database, task_id: str) -> CodingTask | None:
    rows = db.query("select * from coding_tasks where id=?", (task_id,))
    return task_from_row(rows[0]) if rows else None


def run_task(db: Database, settings: Settings, task_id: str, allow_dirty_worktree: bool = False, force_enabled: bool = False, dry_run: bool = False) -> CodexRunResult:
    task = get_task(db, task_id)
    if task is None:
        raise ValueError(f"unknown coding task: {task_id}")
    return CodexCliRunner(db, settings).run_task(task, allow_dirty_worktree=allow_dirty_worktree, force_enabled=force_enabled, dry_run=dry_run)


def run_next(db: Database, settings: Settings, allow_dirty_worktree: bool = False, force_enabled: bool = False) -> CodexRunResult | None:
    tasks = list_tasks(db, "queued")
    if not tasks:
        return None
    return CodexCliRunner(db, settings).run_task(tasks[0], allow_dirty_worktree=allow_dirty_worktree, force_enabled=force_enabled)
