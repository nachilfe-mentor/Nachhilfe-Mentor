from __future__ import annotations

import os
from pathlib import Path

from goal_agent.analytics import GSCConnector, PostHogConnector, parse_gsc_rows, validate_standard_events
from goal_agent.config import Settings
from goal_agent.draft_promotion import promote_drafts
from goal_agent.interactive import render_interactive_page
from goal_agent.loop import run_cycle
from goal_agent.notifications import TelegramNotifier, build_daily_update
from goal_agent.publishing import AdaptivePublishingThrottle
from goal_agent.quality import check_interactive_page_quality
from goal_agent.queue import validate_blog_task
from goal_agent.scanners import scan_content
from goal_agent.scoring import build_opportunities_from_inventory, score_opportunity
from goal_agent.self_improvement import store_learning
from goal_agent.storage import Database
from goal_agent.toolsmith import ToolRegistry


def settings(tmp_path: Path) -> Settings:
    return Settings(
        repo_root=Path(__file__).resolve().parents[2],
        db_path=tmp_path / "goal_agent.db",
        mode="dry_run",
    )


def test_db_initialization(tmp_path: Path) -> None:
    db = Database(settings(tmp_path))
    db.init()
    rows = db.query("select name from sqlite_master where type='table' and name='agent_runs'")
    assert rows


def test_content_scanner_finds_blog_posts(tmp_path: Path) -> None:
    rows = scan_content(settings(tmp_path).repo_root)
    assert any(row["content_type"] == "blog_article" for row in rows)
    assert any(row["url_path"] == "/" for row in rows)


def test_queue_schema_validation() -> None:
    task = {
        "task_id": "blog_task_test",
        "task_type": "article_refresh",
        "priority": 50,
        "topic": "lernplan",
        "primary_keyword": "lernplan erstellen",
        "search_intent": "informational",
        "topic_cluster": "lernmethoden",
        "recommended_angle": "Refresh with practical examples.",
        "evidence": [],
        "expected_metric": "CTA clicks after 28 days",
        "source_agent_run_id": "run_test",
        "status": "queued",
    }
    assert validate_blog_task(task) == []


def test_opportunity_scoring_and_practice_boost() -> None:
    score = score_opportunity({"search_demand": 1, "posthog_conversion_potential": 1, "confidence": 1})
    assert 0 <= score.expected_value_score <= 1
    rows = [{
        "content_type": "blog_article",
        "word_count": 900,
        "internal_link_count": 6,
        "schema_types": [],
        "title": "Mathe Übungen mit Lösungen",
        "primary_keyword": "mathe übungen mit lösungen",
        "topic_cluster": "mathematik",
        "search_intent": "informational",
        "url_path": "/blog/posts/mathe-uebungen.html",
    }]
    opps = build_opportunities_from_inventory(rows)
    assert opps[0]["type"] == "practice_asset_opportunity"
    assert opps[0]["asset_type"] == "practice_page"


def test_posthog_skip_without_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("POSTHOG_PROJECT_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_PERSONAL_API_KEY", raising=False)
    result = PostHogConnector(settings(tmp_path)).analyze()
    assert result.ok
    assert not result.configured
    assert "POSTHOG" not in result.warning


def test_posthog_requires_project_id_and_personal_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", "placeholder-not-used")
    monkeypatch.delenv("POSTHOG_PROJECT_ID", raising=False)
    assert not PostHogConnector(settings(tmp_path)).configured
    cfg = Settings(
        repo_root=Path(__file__).resolve().parents[2],
        db_path=tmp_path / "goal_agent.db",
        mode="dry_run",
        posthog_project_id="119071",
    )
    assert PostHogConnector(cfg).configured


def test_gsc_connector_skip_and_parse_shape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    result = GSCConnector(settings(tmp_path)).analyze()
    assert result.ok
    assert not result.configured
    rows = parse_gsc_rows({
        "rows": [
            {"keys": ["mathe übungen", "https://nachhilfe-mentor.de/"], "clicks": 2, "impressions": 10, "ctr": 0.2, "position": 4.5}
        ]
    })
    assert rows == [{
        "query": "mathe übungen",
        "page": "https://nachhilfe-mentor.de/",
        "clicks": 2,
        "impressions": 10,
        "ctr": 0.2,
        "position": 4.5,
    }]


def test_gsc_oauth_credentials_mark_connector_configured(tmp_path: Path) -> None:
    cfg = Settings(
        repo_root=Path(__file__).resolve().parents[2],
        db_path=tmp_path / "goal_agent.db",
        mode="dry_run",
        gsc_site_url="https://nachhilfe-mentor.de/",
        gsc_oauth_credentials=str(tmp_path / "gsc-oauth.json"),
        gsc_auth_mode="oauth",
        gsc_configured=True,
    )
    assert GSCConnector(cfg).settings.gsc_configured


def test_gsc_oauth_credentials_are_preferred_in_auto_mode(tmp_path: Path, monkeypatch) -> None:
    oauth_file = tmp_path / "gsc-oauth.json"
    oauth_file.write_text("{}", encoding="utf-8")
    cfg = Settings(
        repo_root=Path(__file__).resolve().parents[2],
        db_path=tmp_path / "goal_agent.db",
        mode="dry_run",
        google_application_credentials="/missing-service-account.json",
        gsc_oauth_credentials=str(oauth_file),
        gsc_site_url="https://nachhilfe-mentor.de/",
        gsc_auth_mode="auto",
        gsc_configured=True,
    )
    called = {}

    class FakeCredentials:
        @staticmethod
        def from_authorized_user_file(path, scopes):
            called["path"] = path
            called["scopes"] = scopes
            return "oauth-credentials"

    monkeypatch.setattr("google.oauth2.credentials.Credentials", FakeCredentials)
    assert GSCConnector(cfg)._load_credentials() == "oauth-credentials"
    assert called["path"] == str(oauth_file)


def test_event_schema_has_no_blocked_properties() -> None:
    assert validate_standard_events() == []


def test_practice_page_quality_gate() -> None:
    html = render_interactive_page(
        "Mathe Übungen mit Lösungen",
        "Trainiere eine Aufgabe mit Lösung.",
        "practice_page",
        "mathematik",
        "mathe übungen",
        subject="mathematik",
        grade_level="klasse_8",
    )
    result = check_interactive_page_quality("Mathe Übungen mit Lösungen", html, "practice_page")
    assert result.ok, result.problems
    assert "practice_completed" in html
    assert "solution_revealed" in html


def test_quality_gate_rejects_visible_umlaut_replacements() -> None:
    html = render_interactive_page(
        "Mathe Uebungen mit Loesungen",
        "Trainiere eine Aufgabe mit Loesung.",
        "practice_page",
        "mathematik",
        "mathe uebungen",
        subject="mathematik",
        grade_level="klasse_8",
    )
    result = check_interactive_page_quality("Mathe Uebungen mit Loesungen", html, "practice_page")
    assert not result.ok
    assert any("umlaut" in problem for problem in result.problems)


def test_tool_registry_and_learning_storage(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    ToolRegistry(db, cfg).register_builtin_tools()
    assert ToolRegistry(db, cfg).is_verified("content_decay_detector")
    learning_id = store_learning(db, "Quality gates matter", [{"source": "test"}], 0.8, ["allgemein"], "Keep gates strict.", "test")
    assert learning_id.startswith("learning_")


def test_autonomous_loop_dry_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GOAL_AGENT_DB_PATH", str(tmp_path / "goal_agent.db"))
    monkeypatch.setenv("GOAL_AGENT_EXPORTS_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("GOAL_AGENT_MODE", "dry_run")
    monkeypatch.setenv("GOAL_AGENT_ENV_FILE", str(tmp_path / "missing-goal-agent.env"))
    result = run_cycle("daily")
    assert "Scanned" in result["summary"]
    assert Path(result["report"]).exists()
    assert str(result["report"]).startswith(str(tmp_path))
    assert Path("goal_agent/queues/blog_tasks.jsonl").exists()


def test_adaptive_publishing_allows_quality_without_daily_quota() -> None:
    opportunities = [
        {
            "id": f"opp_quality_{idx}",
            "expected_value_score": 0.8,
            "privacy_risk_score": 0.05,
            "seo_risk_score": 0.05,
            "confidence_score": 0.8,
            "primary_keyword": f"mathe übung {idx}",
            "topic_cluster": "mathematik",
            "intent": "informational",
        }
        for idx in range(12)
    ]
    decisions = AdaptivePublishingThrottle(emergency_cap=50).decide(opportunities, [], {"indexing_health": 0.9, "engagement_health": 0.9, "conversion_health": 0.9})
    assert len([item for item in decisions if item.action == "publish_indexable"]) == 12


def test_adaptive_publishing_slows_duplicate_or_risky_assets() -> None:
    opportunities = [
        {
            "id": "opp_risky",
            "expected_value_score": 0.8,
            "privacy_risk_score": 0.05,
            "seo_risk_score": 0.6,
            "confidence_score": 0.8,
            "primary_keyword": "mathe übungen",
            "topic_cluster": "mathematik",
            "intent": "informational",
        }
    ]
    rows = [{"primary_keyword": "mathe übungen", "topic_cluster": "mathematik"} for _ in range(5)]
    decisions = AdaptivePublishingThrottle(emergency_cap=50).decide(opportunities, rows)
    assert decisions[0].action in {"draft_noindex", "hold"}
    assert not decisions[0].indexable


def test_telegram_notifier_disabled_is_non_fatal(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    result = TelegramNotifier(cfg).send_text("test")
    assert result.ok
    assert not result.configured


def test_draft_promotion_promotes_only_quality_approved_noindex_drafts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    drafts = repo / "goal-agent-pages" / "drafts"
    drafts.mkdir(parents=True)
    html = render_interactive_page(
        "Mathe Übungen mit Lösungen",
        "Übungsseite mit Lösungen, Schwierigkeitsprogression und interaktivem Selbstcheck.",
        "practice_page",
        "mathematik",
        "mathe übungen",
        indexable=False,
    ).replace(
        "</main>",
        '<p><strong>Draft/noindex:</strong> Diese Übungsseite ist ein nicht indexierbarer Entwurf.</p>'
        '<p><a href="/blog/posts/binomische-formeln-lernen.html">Binomische Formeln üben</a></p></main>',
    )
    (drafts / "mathe-uebungen-practice-draft.html").write_text(html, encoding="utf-8")
    cfg = Settings(
        repo_root=repo,
        mode="autonomous_full",
        allow_production_writes=True,
        allow_page_generation=True,
    )
    results = promote_drafts(cfg)
    promoted = [result for result in results if result.status == "promoted"]
    assert len(promoted) == 1
    published = repo / "goal-agent-pages" / "mathe-uebungen.html"
    assert published.exists()
    published_html = published.read_text(encoding="utf-8")
    assert "noindex" not in published_html
    assert "nicht indexierbarer Entwurf" not in published_html
    assert "rel=\"canonical\"" in published_html


def test_telegram_notifier_requires_chat_id(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "goal-agent.env"
    env_file.write_text("GOAL_AGENT_TELEGRAM_BOT_TOKEN=redacted\n", encoding="utf-8")
    cfg = Settings(
        repo_root=settings(tmp_path).repo_root,
        env_file_path=env_file,
        db_path=tmp_path / "goal_agent.db",
        telegram_enabled=True,
        telegram_bot_token_present=True,
    )
    notifier = TelegramNotifier(cfg)
    monkeypatch.setattr(notifier, "_discover_chat_ids", lambda token: [])
    result = notifier.send_text("test")
    assert not result.ok
    assert "chat id missing" in result.message.lower()


def test_daily_update_message_contains_no_secret_values(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    message = build_daily_update(db, cfg, "run_test", "Scanned 1 page")
    assert "Scanned 1 page" in message
    assert "token" not in message.lower()
