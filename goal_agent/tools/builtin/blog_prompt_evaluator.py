from __future__ import annotations


def evaluate_prompt_text(prompt: str) -> dict:
    checks = {
        "keeps_blog_agent_pure": "Artikel" in prompt and "Goal Agent" not in prompt,
        "has_duplicate_guard": "Doppelcontent" in prompt or "duplicate" in prompt.lower(),
        "uses_publisher": "_publish_article.py" in prompt,
        "blocks_analytics_code_in_article": "Analytics-Code" in prompt,
    }
    return {"checks": checks, "score": sum(1 for ok in checks.values() if ok) / len(checks)}
