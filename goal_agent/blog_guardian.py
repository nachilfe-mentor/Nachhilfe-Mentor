from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, Settings
from .storage import utc_now


def monitor_blog_agent(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    try:
        output = subprocess.check_output(["ps", "-eo", "pid,args"], text=True)
    except Exception:  # noqa: BLE001
        output = ""
    running_lines = [line.strip() for line in output.splitlines() if "auto-blog.sh loop" in line and "grep" not in line]
    entrypoints = {
        "auto_blog": (repo_root / "auto-blog.sh").exists(),
        "publisher": (repo_root / "blog" / "_publish_article.py").exists(),
        "seo_updater": (repo_root / "blog" / "_update_seo.py").exists(),
        "context_builder": (repo_root / "blog" / "_prepare_blog_context.py").exists(),
    }
    log_path = repo_root / "auto-blog.log"
    recent_log_tail = ""
    if log_path.exists():
        recent_log_tail = "\n".join(log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:])
    return {
        "running": bool(running_lines),
        "process_count": len(running_lines),
        "entrypoints": entrypoints,
        "recent_failures_hint": "failed" in recent_log_tail.lower() or "error" in recent_log_tail.lower(),
        "checked_at": utc_now(),
    }


def recommend_blog_agent_adjustments(posthog_summary: dict[str, Any], opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    missing_events = set(posthog_summary.get("missing", []) or [])
    if "seo_cta_clicked" in missing_events or "seo_app_store_clicked" in missing_events:
        recommendations.append({
            "type": "tracking_context_recommendation",
            "title": "Prefer briefs with explicit CTA measurement expectation",
            "reason": "PostHog conversion events are missing or sparse, so Blog Agent briefs should include measurable CTA hypotheses.",
            "risk": "low",
        })
    high_clusters = [opp.get("topic_cluster") for opp in opportunities[:10] if opp.get("topic_cluster")]
    if high_clusters:
        recommendations.append({
            "type": "topic_priority_recommendation",
            "title": f"Prioritize cluster: {high_clusters[0]}",
            "reason": "Top scored opportunities indicate this cluster currently has the strongest quality-adjusted potential.",
            "risk": "low",
        })
    return recommendations


def write_guardian_report(status: dict[str, Any], recommendations: list[dict[str, Any]], repo_root: Path = REPO_ROOT) -> Path:
    path = repo_root / "goal_agent" / "exports" / "blog_agent_guardian.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Blog Agent Guardian",
        "",
        f"Checked: {status.get('checked_at')}",
        f"Running: {status.get('running')}",
        f"Process count: {status.get('process_count')}",
        f"Recent failure hint: {status.get('recent_failures_hint')}",
        "",
        "## Entrypoints",
        "",
    ]
    for key, exists in (status.get("entrypoints") or {}).items():
        lines.append(f"- {key}: {'ok' if exists else 'missing'}")
    lines.extend(["", "## Recommendations", ""])
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec['title']}: {rec['reason']} (risk: {rec['risk']})")
    else:
        lines.append("- No adjustment recommended.")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def maybe_apply_blog_context_note(settings: Settings, recommendations: list[dict[str, Any]], repo_root: Path = REPO_ROOT) -> Path | None:
    if not (settings.safe_write_mode and settings.allow_blog_agent_context_changes and recommendations):
        return None
    path = repo_root / "blog" / "_BLOG_CONTEXT_NOTES.md"
    if not path.exists():
        return None
    note = "\n".join(
        [
            "",
            f"## Goal Agent Guardian {utc_now()}",
            *[f"- {rec['title']}: {rec['reason']}" for rec in recommendations[:3]],
        ]
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(note + "\n")
    return path
