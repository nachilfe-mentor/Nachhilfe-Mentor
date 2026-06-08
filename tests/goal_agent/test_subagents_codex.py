from __future__ import annotations

import subprocess
from pathlib import Path

from goal_agent.codex_agent.codex_cli_runner import CodexCliRunner
from goal_agent.codex_agent.dispatcher import build_and_store_tasks, get_task, run_task
from goal_agent.codex_agent.prompt_builder import build_codex_prompt
from goal_agent.codex_agent.result_parser import parse_result
from goal_agent.codex_agent.safety import validate_task_safety
from goal_agent.codex_agent.safety import dirty_worktree_blockers
from goal_agent.codex_agent.task_builder import build_tasks_from_recommendations, retire_obsolete_coding_tasks, store_coding_tasks
from goal_agent.codex_agent.task_schema import CodingTask
from goal_agent.config import Settings
from goal_agent.storage import Database
from goal_agent.subagents.base import Recommendation
from goal_agent.subagents.orchestrator import GoalOrchestrator
from goal_agent.subagents.practice_asset import PracticeAssetAgent
from goal_agent.subagents.quality_guardian import QualityGuardianAgent


def settings(tmp_path: Path) -> Settings:
    return Settings(repo_root=Path(__file__).resolve().parents[2], db_path=tmp_path / "goal_agent.db", mode="dry_run")


def sample_recommendation(**overrides) -> Recommendation:
    data = {
        "id": "rec_test_practice",
        "source_agent": "practice_asset",
        "recommendation_type": "create_practice_asset",
        "title": "Objektpronomen Französisch Klasse 8 Übung",
        "rationale": "Practice intent is strong and a draft exercise page would help learners.",
        "priority": 80,
        "confidence": 0.8,
        "target_topic": "sprachen",
        "target_url": None,
        "suggested_publish_decision": "draft_noindex",
        "codex_task_allowed": True,
        "safety_risk": "low",
        "acceptance_criteria": ["Draft only", "Includes solutions"],
        "required_context": ["practice rules"],
    }
    data.update(overrides)
    return Recommendation(**data)


def test_recommendation_schema_validates() -> None:
    assert sample_recommendation().validate() == []
    assert sample_recommendation(safety_risk="high").validate()


def test_orchestrator_runs_multiple_subagents(tmp_path: Path) -> None:
    db = Database(settings(tmp_path))
    db.init()
    output = GoalOrchestrator(db).run({
        "repo_root": settings(tmp_path).repo_root,
        "content_rows": [{"content_type": "blog_article", "word_count": 700, "url_path": "/blog/posts/x.html", "topic_cluster": "mathematik"}],
        "internal_links": [],
        "opportunities": [{
            "id": "opp_practice",
            "type": "practice_asset_opportunity",
            "primary_keyword": "mathe übungen mit lösungen",
            "topic_cluster": "mathematik",
            "target_url": "/blog/posts/x.html",
            "expected_value_score": 0.7,
            "confidence_score": 0.7,
        }],
        "data_snapshot": {"gsc_warning": "GSC configured, but service account lacks Search Console property access."},
    })
    assert "seo_intelligence" in output["agents_run"]
    assert "practice_asset" in output["agents_run"]
    assert output["recommendations"]


def test_quality_guardian_blocks_bad_recommendation() -> None:
    bad = sample_recommendation(priority=10, confidence=0.2, codex_task_allowed=False)
    result = QualityGuardianAgent().run({"candidate_recommendations": [bad]})
    assert result.recommendations
    assert result.recommendations[0].recommendation_type == "hold"


def test_quality_guardian_blocks_weak_practice_asset_brief() -> None:
    weak = sample_recommendation()
    result = QualityGuardianAgent().run({"candidate_recommendations": [weak]})
    assert result.recommendations
    assert "learning simulation" in result.recommendations[0].rationale


def test_practice_asset_agent_creates_recommendation_from_opportunity() -> None:
    result = PracticeAssetAgent().run({"opportunities": [{
        "id": "opp_1",
        "type": "practice_asset_opportunity",
        "primary_keyword": "französisch übungen klasse 8",
        "topic_cluster": "sprachen",
        "target_url": "/blog/posts/franzoesisch.html",
        "expected_value_score": 0.8,
    }]})
    assert result.recommendations
    assert result.recommendations[0].codex_task_allowed
    criteria = " ".join(result.recommendations[0].acceptance_criteria).lower()
    assert "active answer input" in criteria
    assert "immediate feedback" in criteria
    assert "primary keyword" in criteria
    assert "modern responsive" in criteria


def test_practice_asset_agent_allows_guided_writing_pages() -> None:
    result = PracticeAssetAgent().run({"opportunities": [{
        "id": "opp_bildbeschreibung",
        "type": "practice_asset_opportunity",
        "primary_keyword": "bildbeschreibung übung mit lösung",
        "topic_cluster": "deutsch schreiben",
        "target_url": "/blog/posts/bildbeschreibung-schreiben-tipps.html",
        "expected_value_score": 0.82,
    }]})
    assert result.recommendations
    rec = result.recommendations[0]
    assert "Guided writing" in rec.title
    criteria = " ".join(rec.acceptance_criteria).lower()
    assert "musterlösung" in criteria
    assert "bewertungsraster" in criteria or "rubric" in criteria
    assert "cost" in criteria
    assert "no generic landing-page hero" in criteria


def test_quality_guardian_accepts_strong_guided_writing_brief() -> None:
    rec = sample_recommendation(
        title="Guided writing practice page: bildbeschreibung übung mit lösung",
        rationale=(
            "Guided writing asset with image prompt, textarea writing field, self-check rubric, "
            "Musterlösung, typical mistakes, revision workflow, metadata, license and cost tracking."
        ),
        acceptance_criteria=[
            "Use a concrete image prompt and asset metadata.",
            "Include learner writing textarea and structure scaffold.",
            "Use self-check checklist and Bewertungsraster/rubric, not fake auto-grading.",
            "Include Musterlösung/model solution and typical mistakes.",
            "Add revision/überarbeiten workflow.",
            "Track image metadata, license and cost.",
            "375 px mobile responsive layout with compact hero.",
            "Include keyword, search intent and SEO metadata.",
            "Keep draft noindex.",
        ],
        required_context=["guided writing practice standard", "image asset policy"],
    )
    result = QualityGuardianAgent().run({"candidate_recommendations": [rec]})
    assert result.recommendations == []


def test_task_builder_creates_guided_writing_task() -> None:
    rec = sample_recommendation(
        title="Guided writing practice page: bildbeschreibung übung mit lösung",
        rationale="Build guided writing page with image prompt, Musterlösung, Bewertungsraster and cost metadata.",
        acceptance_criteria=[
            "Include image prompt and asset metadata.",
            "Include writing textarea, self-check, rubric, Musterlösung and revision workflow.",
        ],
        required_context=["guided writing practice standard"],
    )
    task = build_tasks_from_recommendations([rec])[0]
    assert task.task_type == "practice_page"
    assert any(path == "docs/goal-agent/LEARNING_ASSET_PATTERNS.md" for path in task.allowed_paths)
    assert any(path == "lernmaterialien/deutsch/" for path in task.allowed_paths)
    assert any(path == "lernmaterialien/assets/" for path in task.allowed_paths)
    assert "LEARNING_ASSET_PATTERNS.md" in task.goal
    assert "not as rigid templates" in task.goal
    assert "fake AI grader" in task.goal


def test_task_builder_treats_argumentation_as_guided_writing_even_from_old_brief() -> None:
    rec = sample_recommendation(
        title="Draft practice page: argumentation Übungen mit Lösungen",
        rationale="Practice page for open German writing skill.",
        acceptance_criteria=["Include useful exercises with solutions."],
        required_context=["practice rules"],
    )
    task = build_tasks_from_recommendations([rec])[0]
    assert task.title.startswith("Draft guided writing practice page:")
    assert "writing textarea" in task.goal
    assert "Do not pretend to auto-grade open writing" in task.goal


def test_retire_obsolete_coding_tasks_marks_pre_pattern_tasks(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    stale = build_tasks_from_recommendations([sample_recommendation(
        id="rec_stale",
        title="Draft practice page: prüfungstag Übungen mit Lösungen",
        rationale="Old pre-pattern task.",
        acceptance_criteria=["Draft only"],
        required_context=["practice rules"],
    )])[0]
    fresh = build_tasks_from_recommendations([sample_recommendation(
        id="rec_fresh",
        title="Guided writing practice page: bildbeschreibung übung mit lösung",
        rationale="Build guided writing page with image prompt, Musterlösung, Bewertungsraster and cost metadata.",
        acceptance_criteria=["Include writing textarea, self-check, rubric, Musterlösung and revision workflow."],
        required_context=["guided writing practice standard"],
    )])[0]
    store_coding_tasks(db, [stale, fresh])
    retired = retire_obsolete_coding_tasks(db)
    assert retired == 1
    rows = {row["id"]: row["status"] for row in db.query("select id,status from coding_tasks")}
    assert rows[stale.id] == "retired"
    assert rows[fresh.id] == "queued"


def test_store_coding_tasks_revives_retired_guided_writing_policy_upgrade(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    rec = sample_recommendation(
        id="rec_upgrade",
        title="Draft practice page: argumentation Übungen mit Lösungen",
        rationale="Practice page for open German writing skill.",
        acceptance_criteria=["Include useful exercises with solutions."],
        required_context=["practice rules"],
    )
    task = build_tasks_from_recommendations([rec])[0]
    store_coding_tasks(db, [task])
    with db.connect() as conn:
        conn.execute("update coding_tasks set status='retired' where id=?", (task.id,))
    store_coding_tasks(db, [task])
    row = db.query("select status from coding_tasks where id=?", (task.id,))[0]
    assert row["status"] == "queued"


def test_store_coding_tasks_ignores_old_guided_writing_completion_without_asset(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    rec = sample_recommendation(
        id="rec_empty_completion",
        title="Draft practice page: aufbau interpretation Übungen mit Lösungen",
        rationale="Practice page for open German writing skill.",
        acceptance_criteria=["Include useful exercises with solutions."],
        required_context=["practice rules"],
    )
    task = build_tasks_from_recommendations([rec])[0]
    store_coding_tasks(db, [task])
    with db.connect() as conn:
        conn.execute("update coding_tasks set status='completed' where id=?", (task.id,))
        conn.execute(
            """
            insert into coding_task_runs (
              id, task_id, status, started_at, finished_at, exit_code,
              stdout_summary, stderr_summary, changed_files_json, git_diff_stat,
              git_status_short, tests_run_json, failure_reason, safety_blocked,
              prompt_summary, created_at
            ) values (
              'run_empty_completion', ?, 'completed', '2026-06-08T00:00:00+00:00',
              '2026-06-08T00:00:01+00:00', 0, '', '', '[]', '', '', '[]', '', 0, '', '2026-06-08T00:00:01+00:00'
            )
            """,
            (task.id,),
        )
    store_coding_tasks(db, [task])
    row = db.query("select status from coding_tasks where id=?", (task.id,))[0]
    assert row["status"] == "queued"


def test_task_builder_creates_codex_task_and_blocks_high_risk() -> None:
    tasks = build_tasks_from_recommendations([sample_recommendation()])
    assert tasks
    assert tasks[0].task_type == "practice_page"
    assert tasks[0].publish_policy == "draft_noindex_only"
    assert any("correct umlauts" in criterion for criterion in tasks[0].acceptance_criteria)
    assert any("lernmaterialien/lernsimulationen" in path for path in tasks[0].allowed_paths)
    assert any("weak one-cycle" in criterion for criterion in tasks[0].acceptance_criteria)
    assert not build_tasks_from_recommendations([sample_recommendation(safety_risk="high")])


def test_prompt_builder_contains_safety_sections() -> None:
    task = build_tasks_from_recommendations([sample_recommendation()])[0]
    prompt = build_codex_prompt(task)
    assert "Du bist ein Coding Agent" in prompt
    assert "Kein Deploy" in prompt
    assert "Verbotene Dateien" in prompt


def test_codex_disabled_blocks_execution(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    task = build_tasks_from_recommendations([sample_recommendation()])[0]
    store_coding_tasks(db, [task])
    result = CodexCliRunner(db, cfg).run_task(task, allow_dirty_worktree=True)
    assert result.status == "blocked_by_safety"
    assert "disabled" in result.failure_reason.lower()


def test_codex_binary_missing_message(tmp_path: Path) -> None:
    cfg = Settings(repo_root=settings(tmp_path).repo_root, db_path=tmp_path / "goal_agent.db", codex_enabled=True, codex_bin="definitely-missing-codex")
    db = Database(cfg)
    db.init()
    task = build_tasks_from_recommendations([sample_recommendation()])[0]
    result = CodexCliRunner(db, cfg).run_task(task, allow_dirty_worktree=True)
    assert result.status == "blocked_by_safety"
    assert "not found" in result.failure_reason


def test_codex_timeout_is_recorded(tmp_path: Path, monkeypatch) -> None:
    cfg = Settings(repo_root=settings(tmp_path).repo_root, db_path=tmp_path / "goal_agent.db", codex_enabled=True, codex_bin="codex")
    db = Database(cfg)
    db.init()
    task = build_tasks_from_recommendations([sample_recommendation()])[0]

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="codex", timeout=1)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr("subprocess.run", fake_run)
    result = CodexCliRunner(db, cfg).run_task(task, allow_dirty_worktree=True)
    assert result.status == "failed"
    assert result.failure_reason == "timeout"


def test_dirty_worktree_blocks_by_default(tmp_path: Path, monkeypatch) -> None:
    cfg = Settings(repo_root=settings(tmp_path).repo_root, db_path=tmp_path / "goal_agent.db", codex_enabled=True)
    db = Database(cfg)
    db.init()
    task = build_tasks_from_recommendations([sample_recommendation()])[0]
    monkeypatch.setattr(
        "goal_agent.codex_agent.codex_cli_runner.dirty_worktree_blockers",
        lambda repo_root, allowed_paths=(): ["dirty worktree: goal_agent/example.py"],
    )
    result = CodexCliRunner(db, cfg).run_task(task)
    assert result.status == "blocked_by_safety"
    assert "dirty worktree" in result.failure_reason


def test_dirty_worktree_allows_configured_runtime_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "goal_agent.codex_agent.safety.git_status_short",
        lambda repo_root: " M auto-blog.log\n M blog/_pinterest_done.txt\n",
    )
    assert dirty_worktree_blockers(tmp_path, ("auto-blog.log", "blog/_pinterest_done.txt")) == []


def test_dirty_worktree_still_blocks_source_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "goal_agent.codex_agent.safety.git_status_short",
        lambda repo_root: " M auto-blog.log\n M goal_agent/config.py\n",
    )
    blockers = dirty_worktree_blockers(tmp_path, ("auto-blog.log",))
    assert blockers
    assert "goal_agent/config.py" in blockers[0]


def test_safety_blocks_push_deploy_publish_commands() -> None:
    task = CodingTask(
        id="coding_task_bad",
        source_recommendation_id="rec_bad",
        task_type="refactor_safe",
        title="Bad",
        goal="Run git push and deploy",
        context_summary="Bad",
        allowed_paths=["goal_agent/"],
        forbidden_paths=[".env"],
        acceptance_criteria=["No"],
        safety_constraints=["No"],
        test_commands=[],
        mode="modify_repo",
        publish_policy="never_publish",
    )
    problems = validate_task_safety(task)
    assert any("blocked risky instruction" in problem for problem in problems)


def test_result_parser_captures_git_state(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    (repo / "a.txt").write_text("x", encoding="utf-8")
    parsed = parse_result(repo, "summary", "", 0)
    assert "a.txt" in parsed.git_status_short


def test_codex_task_cli_storage_roundtrip(tmp_path: Path) -> None:
    cfg = settings(tmp_path)
    db = Database(cfg)
    db.init()
    count = store_coding_tasks(db, build_tasks_from_recommendations([sample_recommendation()]))
    assert count == 1
    task = get_task(db, "coding_task_" + __import__("hashlib").sha1("rec_test_practice".encode("utf-8")).hexdigest()[:16])
    assert task is not None
    assert task.source_recommendation_id == "rec_test_practice"
