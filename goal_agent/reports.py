from __future__ import annotations

from pathlib import Path

from .config import REPO_ROOT, Settings
from .storage import Database, utc_now


def generate_daily_report(db: Database, settings: Settings, run_id: str, repo_root: Path = REPO_ROOT) -> Path:
    exports = settings.exports_dir
    exports.mkdir(parents=True, exist_ok=True)
    path = exports / "daily_seo_report.md"
    content_count = db.query("select count(*) as c from content_inventory")[0]["c"]
    task_count = db.query("select count(*) as c from blog_tasks where status='queued'")[0]["c"]
    practice_task_count = db.query("select count(*) as c from interactive_page_tasks where status='queued'")[0]["c"]
    opportunities = db.query(
        "select * from opportunities order by expected_value_score desc limit 10"
    )
    codex_task_count = db.query("select count(*) as c from coding_tasks")[0]["c"]
    runnable_codex_count = db.query("select count(*) as c from coding_tasks where status='queued'")[0]["c"]
    blocked_codex_count = db.query("select count(*) as c from coding_task_runs where safety_blocked=1")[0]["c"]
    last_codex_runs = db.query("select * from coding_task_runs order by created_at desc limit 1")
    last_codex = last_codex_runs[0] if last_codex_runs else None
    subagent_runs = db.query("select agent_name, status, recommendation_count from subagent_runs order by created_at desc limit 8")
    top_recs = db.query("select title, source_agent, priority, suggested_publish_decision, safety_risk from subagent_recommendations order by priority desc limit 5")
    blocked_recs = db.query("select count(*) as c from subagent_recommendations where recommendation_type='hold' or safety_risk='high'")[0]["c"]
    gsc_access_rows = db.query(
        "select rationale from subagent_recommendations where rationale=? order by created_at desc limit 1",
        ("GSC configured, but service account lacks Search Console property access.",),
    )
    gsc_status = gsc_access_rows[0]["rationale"] if gsc_access_rows else ("configured" if settings.gsc_configured else "not configured")
    lines = [
        "# Goal Agent Daily SEO Report",
        "",
        f"Generated: {utc_now()}",
        f"Run ID: {run_id}",
        f"Mode: {settings.mode}",
        "",
        "## Safety State",
        "",
        f"- Enabled: {settings.enabled}",
        f"- Production writes allowed: {settings.allow_production_writes}",
        f"- Page generation allowed: {settings.allow_page_generation}",
        f"- Tracking changes allowed: {settings.allow_tracking_changes}",
        f"- Toolsmith allowed: {settings.allow_toolsmith}",
        f"- Blog Agent context changes allowed: {settings.allow_blog_agent_context_changes}",
        f"- Autonomous deploy allowed: {settings.allow_autonomous_deploy}",
        "",
        "## Inventory",
        "",
        f"- Content rows: {content_count}",
        f"- Queued Blog Agent tasks: {task_count}",
        f"- Queued interactive/practice tasks: {practice_task_count}",
        "",
        "## GSC",
        "",
        f"- Status: {gsc_status}",
        "",
        "## Top Opportunities",
        "",
    ]
    for row in opportunities:
        lines.append(f"- {row['type']} `{row['target_url']}` score={row['expected_value_score']:.2f} cluster={row['topic_cluster']}")
    if not opportunities:
        lines.append("- No opportunities scored yet.")
    lines.extend([
        "",
        "## Notes",
        "",
        "- Existing Blog Agent was not modified by this run.",
        "- Practice-first SEO assets are owned by the Goal Agent, not the Blog Agent.",
        "- External outreach, autonomous deploys, and production writes remain blocked unless explicitly enabled.",
        "",
        "## Subagents",
        "",
        f"- Agents run: {', '.join(row['agent_name'] for row in subagent_runs) if subagent_runs else ''}",
        f"- Recommendations created: {sum(row['recommendation_count'] for row in subagent_runs) if subagent_runs else 0}",
        f"- Blocked recommendations: {blocked_recs}",
        "",
        "Top recommendations:",
        *[f"- {row['title']} ({row['source_agent']}, priority={row['priority']}, decision={row['suggested_publish_decision']}, risk={row['safety_risk']})" for row in top_recs],
        "",
        "## Codex Coding Agent",
        "",
        f"- Enabled: {settings.codex_enabled}",
        f"- Codex bin: {settings.codex_bin}",
        f"- Sandbox mode: {settings.codex_sandbox_mode}",
        f"- Tasks created: {codex_task_count}",
        f"- Tasks runnable: {runnable_codex_count}",
        f"- Safety blocks: {blocked_codex_count}",
        f"- Last exit code: {last_codex['exit_code'] if last_codex else ''}",
        f"- Last changed files: {last_codex['changed_files_json'] if last_codex else '[]'}",
        f"- Last failure reason: {last_codex['failure_reason'] if last_codex else ''}",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
