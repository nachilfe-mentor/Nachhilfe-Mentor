from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Settings


ALLOWED_PUBLISH_PATHS = (
    "lernmaterialien/",
    "goal_agent/generated_tools/",
    "sitemap.xml",
    "feed.xml",
)


@dataclass(frozen=True)
class AutoPublishResult:
    ok: bool
    status: str
    changed_files: list[str]
    pushed: bool
    message: str


def _run(args: list[str], repo_root: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _changed_files(repo_root: Path) -> list[str]:
    proc = _run(["git", "status", "--short"], repo_root)
    files: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path)
    return files


def _publishable_changes(repo_root: Path) -> list[str]:
    changed = _changed_files(repo_root)
    return [
        path
        for path in changed
        if path in {"sitemap.xml", "feed.xml"} or path.startswith("lernmaterialien/") or path.startswith("goal_agent/generated_tools/")
    ]


def auto_publish(settings: Settings, commit_message: str = "chore: publish goal agent SEO assets") -> AutoPublishResult:
    if not settings.deploy_enabled:
        return AutoPublishResult(True, "skipped", [], False, "autonomous deploy disabled")

    repo_root = settings.repo_root
    seo = _run(["python3", "blog/_update_seo.py", "--no-ping"], repo_root, timeout=300)
    if seo.returncode != 0:
        return AutoPublishResult(False, "failed", [], False, "SEO update failed")

    publishable = _publishable_changes(repo_root)
    if not publishable:
        return AutoPublishResult(True, "skipped", [], False, "no publishable changes")

    add = _run(["git", "add", "--", *ALLOWED_PUBLISH_PATHS], repo_root)
    if add.returncode != 0:
        return AutoPublishResult(False, "failed", publishable, False, "git add failed")

    diff = _run(["git", "diff", "--cached", "--name-only"], repo_root)
    staged = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    staged = [
        path
        for path in staged
        if path in {"sitemap.xml", "feed.xml"} or path.startswith("lernmaterialien/") or path.startswith("goal_agent/generated_tools/")
    ]
    if not staged:
        return AutoPublishResult(True, "skipped", [], False, "no allowed staged changes")

    tests = _run(["python3", "-m", "pytest", "-q"], repo_root, timeout=max(300, settings.codex_timeout_seconds))
    if tests.returncode != 0:
        return AutoPublishResult(False, "failed", staged, False, "tests failed; publish aborted")

    commit = _run(["git", "commit", "-m", commit_message], repo_root)
    if commit.returncode != 0:
        return AutoPublishResult(False, "failed", staged, False, "git commit failed")

    push = _run(["git", "push", "origin", "main"], repo_root, timeout=600)
    if push.returncode != 0:
        return AutoPublishResult(False, "failed", staged, False, "git push failed")

    return AutoPublishResult(True, "published", staged, True, "pushed to origin/main")
