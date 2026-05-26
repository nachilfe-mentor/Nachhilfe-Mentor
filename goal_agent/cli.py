from __future__ import annotations

import argparse
import json

from .config import load_settings
from .codex_agent.dispatcher import build_and_store_tasks, get_task, list_tasks, run_next, run_task
from .codex_agent.prompt_builder import build_codex_prompt
from .draft_promotion import promote_drafts
from .loop import run_cycle
from .notifications import TelegramNotifier, build_daily_update
from .queue import export_blog_tasks
from .reports import generate_daily_report
from .scanners import scan_content
from .scoring import build_opportunities_from_inventory
from .storage import Database, write_migration_file
from .subagents.orchestrator import GoalOrchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="goal-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    sub.add_parser("scan-content")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--cycle", default="daily", choices=["daily", "weekly", "monthly"])
    run_parser.add_argument("--queue-codex-tasks", action="store_true")
    sub.add_parser("generate-report")
    promote_parser = sub.add_parser("promote-drafts")
    promote_parser.add_argument("--limit", type=int)
    sub.add_parser("export-blog-tasks")
    sub.add_parser("show-status")
    subagents_parser = sub.add_parser("subagents")
    subagents_sub = subagents_parser.add_subparsers(dest="subagents_command", required=True)
    subagents_run = subagents_sub.add_parser("run")
    subagents_run.add_argument("--cycle", default="daily")
    subagents_run.add_argument("--dry-run", action="store_true")
    codex_parser = sub.add_parser("codex-tasks")
    codex_sub = codex_parser.add_subparsers(dest="codex_command", required=True)
    codex_build = codex_sub.add_parser("build")
    codex_build.add_argument("--cycle", default="daily")
    codex_build.add_argument("--limit", type=int, default=10)
    codex_list = codex_sub.add_parser("list")
    codex_list.add_argument("--status")
    codex_show = codex_sub.add_parser("show")
    codex_show.add_argument("--task-id", required=True)
    codex_run = codex_sub.add_parser("run")
    codex_run.add_argument("--task-id", required=True)
    codex_run.add_argument("--allow-dirty-worktree", action="store_true")
    codex_run.add_argument("--force-enabled", action="store_true")
    codex_run_next = codex_sub.add_parser("run-next")
    codex_run_next.add_argument("--allow-dirty-worktree", action="store_true")
    codex_run_next.add_argument("--force-enabled", action="store_true")
    codex_dry = codex_sub.add_parser("dry-run")
    codex_dry.add_argument("--task-id", required=True)
    telegram_parser = sub.add_parser("telegram")
    telegram_sub = telegram_parser.add_subparsers(dest="telegram_command", required=True)
    telegram_sub.add_parser("status")
    telegram_sub.add_parser("discover-chat")
    telegram_sub.add_parser("test-message")
    args = parser.parse_args(argv)
    settings = load_settings()
    db = Database(settings)
    if args.command == "init-db":
        db.init()
        path = write_migration_file()
        print(json.dumps({"ok": True, "db_path": str(db.path), "migration": str(path)}))
        return 0
    if args.command == "scan-content":
        db.init()
        rows = scan_content(settings.repo_root)
        db.upsert_content(rows)
        print(json.dumps({"ok": True, "count": len(rows)}))
        return 0
    if args.command == "run":
        print(json.dumps(run_cycle(args.cycle, settings, queue_codex_tasks=args.queue_codex_tasks), ensure_ascii=False))
        return 0
    if args.command == "generate-report":
        db.init()
        path = generate_daily_report(db, settings, "manual")
        print(json.dumps({"ok": True, "path": str(path)}))
        return 0
    if args.command == "promote-drafts":
        results = promote_drafts(settings, args.limit)
        print(json.dumps({
            "ok": True,
            "promoted": [str(result.published_path) for result in results if result.status == "promoted" and result.published_path],
            "held": [
                {
                    "draft": str(result.draft_path),
                    "quality_score": result.quality.score,
                    "reasons": result.reasons,
                }
                for result in results
                if result.status != "promoted"
            ],
        }, ensure_ascii=False))
        return 0
    if args.command == "export-blog-tasks":
        db.init()
        jsonl, md = export_blog_tasks(db, settings.repo_root)
        print(json.dumps({"ok": True, "jsonl": str(jsonl), "markdown": str(md)}))
        return 0
    if args.command == "show-status":
        db.init()
        runs = db.query("select id, cycle_type, status, started_at, summary from agent_runs order by started_at desc limit 5")
        tasks = db.query("select count(*) as c from blog_tasks where status='queued'")[0]["c"]
        codex_tasks = db.query("select count(*) as c from coding_tasks where status='queued'")[0]["c"]
        print(json.dumps({"mode": settings.mode, "enabled": settings.enabled, "queued_blog_tasks": tasks, "queued_codex_tasks": codex_tasks, "codex_enabled": settings.codex_enabled, "recent_runs": [dict(row) for row in runs]}, ensure_ascii=False))
        return 0
    if args.command == "subagents":
        db.init()
        if args.subagents_command == "run":
            rows = scan_content(settings.repo_root)
            opportunities = build_opportunities_from_inventory(rows)
            context = {
                "repo_root": settings.repo_root,
                "content_rows": rows,
                "internal_links": [],
                "opportunities": opportunities,
                "data_snapshot": {"gsc_warning": "", "posthog_warning": ""},
            }
            output = GoalOrchestrator(db).run(context, persist=not args.dry_run)
            print(json.dumps({
                "agents_run": output["agents_run"],
                "recommendations_created": len(output["recommendations"]),
                "blocked_recommendations": len(output["blocked_recommendations"]),
                "top_recommendations": [rec.to_dict() for rec in output["recommendations"][:5]],
                "dry_run": args.dry_run,
            }, ensure_ascii=False))
            return 0
    if args.command == "codex-tasks":
        db.init()
        if args.codex_command == "build":
            rows = scan_content(settings.repo_root)
            opportunities = build_opportunities_from_inventory(rows)
            GoalOrchestrator(db).run({
                "repo_root": settings.repo_root,
                "content_rows": rows,
                "internal_links": [],
                "opportunities": opportunities,
                "data_snapshot": {"gsc_warning": "", "posthog_warning": ""},
            })
            count = build_and_store_tasks(db, args.limit)
            print(json.dumps({"ok": True, "created_or_updated": count}))
            return 0
        if args.codex_command == "list":
            tasks = list_tasks(db, args.status)
            print(json.dumps({"tasks": [task.to_dict() for task in tasks]}, ensure_ascii=False))
            return 0
        if args.codex_command == "show":
            task = get_task(db, args.task_id)
            if task is None:
                print(json.dumps({"ok": False, "error": "unknown task"}))
                return 2
            print(json.dumps(task.to_dict(), ensure_ascii=False))
            return 0
        if args.codex_command == "dry-run":
            task = get_task(db, args.task_id)
            if task is None:
                print(json.dumps({"ok": False, "error": "unknown task"}))
                return 2
            print(json.dumps({"ok": True, "task_id": task.id, "prompt_preview": build_codex_prompt(task)[:3000]}, ensure_ascii=False))
            return 0
        if args.codex_command == "run":
            result = run_task(db, settings, args.task_id, allow_dirty_worktree=args.allow_dirty_worktree, force_enabled=args.force_enabled)
            print(json.dumps(result.__dict__, ensure_ascii=False))
            return 0 if result.status == "completed" else 1
        if args.codex_command == "run-next":
            result = run_next(db, settings, allow_dirty_worktree=args.allow_dirty_worktree, force_enabled=args.force_enabled)
            if result is None:
                print(json.dumps({"ok": True, "message": "no queued coding tasks"}))
                return 0
            print(json.dumps(result.__dict__, ensure_ascii=False))
            return 0 if result.status == "completed" else 1
        return 0
    if args.command == "telegram":
        db.init()
        notifier = TelegramNotifier(settings)
        if args.telegram_command == "status":
            print(json.dumps({
                "enabled": settings.telegram_enabled,
                "token_present": settings.telegram_bot_token_present,
                "chat_id_configured": bool(settings.telegram_chat_id),
                "configured": notifier.configured,
            }))
            return 0
        if args.telegram_command == "discover-chat":
            result = notifier.discover_chat_ids()
            print(json.dumps(result.__dict__, ensure_ascii=False))
            return 0 if result.ok else 1
        if args.telegram_command == "test-message":
            recent = db.query("select id, summary from agent_runs order by started_at desc limit 1")
            run_id = recent[0]["id"] if recent else "manual"
            summary = recent[0]["summary"] if recent else "Manual Telegram test."
            result = notifier.send_text(build_daily_update(db, settings, run_id, summary))
            print(json.dumps(result.__dict__, ensure_ascii=False))
            return 0 if result.ok else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
