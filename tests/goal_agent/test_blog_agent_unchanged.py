from __future__ import annotations

from pathlib import Path

from goal_agent.blog_guardian import monitor_blog_agent, recommend_blog_agent_adjustments


def test_blog_agent_entrypoints_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "auto-blog.sh").exists()
    assert (root / "blog" / "_publish_article.py").exists()
    assert (root / "blog" / "_update_seo.py").exists()
    assert (root / "blog" / "_prepare_blog_context.py").exists()


def test_goal_agent_does_not_patch_blog_agent_prompt() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "auto-blog.sh").read_text(encoding="utf-8")
    assert "Du bist der autonome Blog-Manager" in text
    assert "goal_agent/queues/blog_tasks.jsonl" not in text


def test_blog_context_reads_goal_agent_exports_without_changing_blog_role() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "blog" / "_prepare_blog_context.py").read_text(encoding="utf-8")
    assert "GOAL_AGENT_TASKS" in text
    assert "GOAL_AGENT_GUARDIAN" in text
    assert "Practice-/Tool-Seiten" in text


def test_sitemap_includes_only_indexable_goal_agent_pages() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "blog" / "_update_seo.py").read_text(encoding="utf-8")
    assert "goal-agent-pages" in text
    assert "has_noindex(f)" in text
    assert "goal_agent_pages" in text


def test_blog_guardian_monitors_without_script_changes() -> None:
    root = Path(__file__).resolve().parents[2]
    status = monitor_blog_agent(root)
    assert status["entrypoints"]["auto_blog"]
    recs = recommend_blog_agent_adjustments({"missing": ["seo_cta_clicked"]}, [{"topic_cluster": "lernmethoden"}])
    assert recs
