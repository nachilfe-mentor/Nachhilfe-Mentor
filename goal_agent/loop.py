from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from . import __version__
from .analytics import GSCConnector, PostHogConnector, SerpConnector, page_conversion_scores, validate_standard_events
from .autopublish import auto_publish
from .blog_guardian import maybe_apply_blog_context_note, monitor_blog_agent, recommend_blog_agent_adjustments, write_guardian_report
from .codex_agent.dispatcher import build_and_store_tasks, run_next
from .config import REPO_ROOT, Settings, load_settings
from .context_builder import build_context
from .draft_promotion import promote_drafts
from .experiments import create_experiment
from .notifications import notify_daily_update
from .queue import export_blog_tasks, store_blog_tasks, task_from_opportunity
from .publishing import AdaptivePublishingThrottle
from .reports import generate_daily_report
from .scanners import build_internal_link_graph, read_blog_registry, scan_content
from .scoring import build_gsc_practice_opportunities, build_opportunities_from_inventory, dedupe_opportunities
from .self_improvement import maybe_update_scoring, store_learning
from .storage import Database, json_dumps, utc_now, write_migration_file
from .subagents.orchestrator import GoalOrchestrator
from .toolsmith import ToolRegistry, Toolsmith


def _run_id(cycle_type: str) -> str:
    return "run_" + hashlib.sha1(f"{cycle_type}:{utc_now()}".encode("utf-8")).hexdigest()[:16]


def _git_commit(repo_root: Path = REPO_ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def _insert_run(db: Database, run_id: str, cycle_type: str, settings: Settings) -> None:
    now = utc_now()
    with db.connect() as conn:
        conn.execute(
            """
            insert into agent_runs (id, cycle_type, status, started_at, agent_version, git_commit_before, dry_run, created_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, cycle_type, "running", now, __version__, _git_commit(), 1 if settings.mode in {"dry_run", "analyze_only", "queue_only"} else 0, now),
        )


def _finish_run(db: Database, run_id: str, status: str, summary: str, error: str | None = None) -> None:
    with db.connect() as conn:
        conn.execute(
            "update agent_runs set status=?, finished_at=?, git_commit_after=?, summary=?, error_message_redacted=? where id=?",
            (status, utc_now(), _git_commit(), summary, error, run_id),
        )


def _log_decision(db: Database, run_id: str, decision_type: str, title: str, rationale: str, evidence: list[dict], confidence: float, risk: float) -> str:
    decision_id = "decision_" + hashlib.sha1(f"{run_id}:{title}".encode("utf-8")).hexdigest()[:16]
    with db.connect() as conn:
        conn.execute(
            """
            insert into decisions (id, agent_run_id, decision_type, title, rationale, evidence_json, alternatives_json, confidence, risk_score, status, created_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (decision_id, run_id, decision_type, title, rationale, json_dumps(evidence), "[]", confidence, risk, "accepted", utc_now()),
        )
    return decision_id


def _log_action(db: Database, run_id: str, decision_id: str | None, action_type: str, target_type: str, target_id: str | None, status: str, files: list[str], safety: list[str]) -> None:
    action_id = "action_" + hashlib.sha1(f"{run_id}:{action_type}:{target_id}".encode("utf-8")).hexdigest()[:16]
    with db.connect() as conn:
        conn.execute(
            """
            insert into actions (id, agent_run_id, decision_id, action_type, target_type, target_id, status, files_changed_json, safety_checks_json, rollback_plan, created_at, completed_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (action_id, run_id, decision_id, action_type, target_type, target_id, status, json_dumps(files), json_dumps(safety), "Remove generated Goal Agent output or mark task stale.", utc_now(), utc_now()),
        )


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _learning_simulation_shape(keyword: str, topic_cluster: str) -> str:
    text = f"{keyword} {topic_cluster}".lower()
    if any(term in text for term in ["ableitung", "funktion", "gleichung", "bruch", "mathe", "kurvendiskussion"]):
        return "Mathe-Trainer mit generierten Aufgaben, Antwortprüfung, Rechenweg-Hinweisen, Fehlertypen und adaptiver Wiederholung."
    if any(term in text for term in ["vokabel", "englisch", "französisch", "spanisch", "latein"]):
        return "Vokabel- oder Grammatiktrainer mit Eingabe, Abfrage-Runden, Selbstkorrektur, Wiederholung und Fortschritt im Browser."
    if any(term in text for term in ["bildbeschreibung", "argumentation", "interpretation", "analyse", "aufsatz", "text"]):
        return "Deutsch-Trainer mit strukturierter Eingabe, Kriterienprüfung, Beispielbausteinen, Feedback und gezielten Korrekturaufgaben."
    return "Fokussierte Lernsimulation mit aktiver Eingabe, Prüfung, Feedback, Fehlerkorrektur, Wiederholung und sichtbarem Lernfortschritt."


def _interactive_task_spec(opportunity: dict[str, Any]) -> str:
    keyword = opportunity.get("primary_keyword") or "lernen üben"
    topic_cluster = opportunity.get("topic_cluster") or "allgemein"
    target_url = opportunity.get("target_url") or ""
    shape = _learning_simulation_shape(keyword, topic_cluster)
    return "\n".join([
        f"# Lernsimulation: {keyword}",
        "",
        f"- Primäres Keyword: {keyword}",
        f"- Suchintent: {opportunity.get('intent') or 'practice'}",
        f"- Themencluster: {topic_cluster}",
        f"- Ausgangsseite für interne Links: {target_url or 'noch festlegen'}",
        f"- Empfohlene Asset-Form: {shape}",
        "",
        "Arbeite in mehreren Zyklen, wenn das Ergebnis sonst nur dünn oder generisch würde:",
        "1. Research/Spec: Zielgruppe, konkretes Lernproblem, Keyword-Variante, Suchintent und Lernziel festlegen.",
        "2. Prototyp: unter /lernmaterialien/lernsimulationen/ oder /lernmaterialien/entwuerfe/ als noindex bauen.",
        "3. QA: mobile Layouts, echte Interaktion, Antwortprüfung, Feedback, Fehlerbehandlung, Wiederholung und korrekte Umlaute prüfen.",
        "4. Promotion: erst nach Qualitätsgate indexierbar nach /lernmaterialien/ verschieben, mit Canonical, Schema, internen Links und Sitemap.",
        "",
        "Mindestanforderungen:",
        "- Lernende müssen eine eigene Antwort eingeben oder eine echte Entscheidung treffen; reine Lösungskarten reichen nicht.",
        "- Nach Fehlern muss die Seite erklären, welcher Schritt falsch war und eine passende Wiederholungsaufgabe geben.",
        "- Das Design muss modern, responsive und passend zu Nachhilfe Mentor sein; keine verschachtelten Karten und keine wackeligen Controls.",
        "- Sichtbarer deutscher Text muss ä, ö, ü, Ä, Ö, Ü und ß korrekt nutzen.",
        "- Tracking bleibt privacy-safe und erfasst keine Freitextantworten.",
        "- SEO ist strategisch: ein klares Hauptkeyword, hilfreicher Titel, Meta Description, LearningResource/Quiz-Schema und interne Links.",
    ])


def _store_interactive_task(db: Database, run_id: str, opportunity: dict[str, Any]) -> str:
    task_id = "practice_task_" + opportunity["id"].replace("opp_", "")
    now = utc_now()
    with db.connect() as conn:
        conn.execute(
            """
            insert into interactive_page_tasks (
              id, status, asset_type, page_type, subject, grade_level, exam_type,
              difficulty, solution_mode, interaction_type, expected_learning_outcome,
              topic_cluster, primary_keyword, search_intent, target_slug,
              spec_markdown, tracking_requirements_json, schema_requirements_json,
              privacy_review_status, seo_risk_score, expected_value_score,
              agent_run_id, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
              expected_value_score=excluded.expected_value_score,
              updated_at=excluded.updated_at
            """,
            (
                task_id,
                "queued",
                "practice_page",
                "practice_page",
                opportunity.get("topic_cluster") or "allgemein",
                "mixed",
                "practice",
                "mixed",
                "step_by_step",
                "self_check",
                "Learner can solve a representative exercise and understand the solution path.",
                opportunity.get("topic_cluster") or "allgemein",
                opportunity.get("primary_keyword"),
                opportunity.get("intent") or "informational",
                (opportunity.get("target_url") or "practice").rsplit("/", 1)[-1].replace(".html", "") + "-uebungen",
                _interactive_task_spec(opportunity),
                json_dumps(["practice_started", "practice_completed", "answer_checked", "solution_revealed", "retry_clicked", "app_cta_clicked_from_practice"]),
                json_dumps(["LearningResource", "Quiz"]),
                "passed_static_rules",
                opportunity.get("seo_risk_score", 0.1),
                opportunity.get("expected_value_score", 0.0),
                run_id,
                now,
                now,
            ),
        )
    return task_id


def run_cycle(cycle_type: str = "daily", settings: Settings | None = None, queue_codex_tasks: bool = False) -> dict[str, Any]:
    settings = settings or load_settings()
    db = Database(settings)
    db.init()
    write_migration_file()
    run_id = _run_id(cycle_type)
    _insert_run(db, run_id, cycle_type, settings)
    try:
        event_problems = validate_standard_events()
        content_rows = scan_content(settings.repo_root)
        db.upsert_content(content_rows)
        link_records = build_internal_link_graph(content_rows, settings.repo_root)
        with db.connect() as conn:
            for record in link_records:
                link_id = "link_" + hashlib.sha1(f"{record.source_url}:{record.target_url}:{record.link_position}".encode("utf-8")).hexdigest()[:16]
                conn.execute(
                    """
                    insert into internal_link_graph (id, source_url, target_url, anchor_category, link_position, same_cluster, is_broken, first_seen_at, last_seen_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(id) do nothing
                    """,
                    (link_id, record.source_url, record.target_url, record.anchor_category, record.link_position, int(record.same_cluster), int(record.is_broken), utc_now(), utc_now()),
                )
        posthog = PostHogConnector(settings).analyze()
        gsc = GSCConnector(settings).analyze()
        serp = SerpConnector().analyze()
        metrics = page_conversion_scores(posthog.summary)
        inventory_opportunities = build_opportunities_from_inventory(content_rows, metrics={})
        gsc_opportunities = build_gsc_practice_opportunities(gsc.summary.get("queries", []), content_rows) if gsc.ok else []
        opportunities_by_id = {opp["id"]: opp for opp in [*inventory_opportunities, *gsc_opportunities]}
        opportunities = dedupe_opportunities(list(opportunities_by_id.values()))
        publishing_decisions = {
            item.opportunity_id: item
            for item in AdaptivePublishingThrottle(settings.emergency_max_generated_pages_per_run).decide(
                opportunities,
                content_rows,
                site_signals={
                    "indexing_health": 0.7,
                    "engagement_health": 0.7,
                    "conversion_health": metrics.get("sitewide_conversion_score", 0.35),
                },
            )
        }
        now = utc_now()
        with db.connect() as conn:
            for opp in opportunities[:50]:
                conn.execute(
                    """
                    insert into opportunities (
                      id, type, topic_cluster, primary_keyword, intent, target_url, evidence_json,
                      expected_value_score, money_potential_score, traffic_potential_score,
                      search_demand_score, serp_weakness_score, topical_authority_fit_score,
                      posthog_conversion_potential_score, internal_link_value_score,
                      interactivity_advantage_score, execution_complexity_score, privacy_risk_score,
                      seo_risk_score, confidence_score, status, next_action, created_by, created_at, updated_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(id) do update set expected_value_score=excluded.expected_value_score, updated_at=excluded.updated_at
                    """,
                    (
                        opp["id"], opp["type"], opp.get("topic_cluster"), opp.get("primary_keyword"), opp.get("intent"), opp.get("target_url"), json_dumps(opp.get("evidence", [])),
                        opp["expected_value_score"], opp["money_potential_score"], opp["traffic_potential_score"],
                        opp["search_demand_score"], opp["serp_weakness_score"], opp["topical_authority_fit_score"],
                        opp["posthog_conversion_potential_score"], opp["internal_link_value_score"],
                        opp["interactivity_advantage_score"], opp["execution_complexity_score"], opp["privacy_risk_score"],
                        opp["seo_risk_score"], opp["confidence_score"], opp["status"], opp["next_action"], opp["created_by"], now, now,
                    ),
                )
                idea_id = "idea_" + opp["id"].replace("opp_", "")
                conn.execute(
                    """
                    insert into ideas (id, type, topic_cluster, primary_keyword, intent, evidence_json, confidence, expected_value_score, money_potential_score, traffic_potential_score, execution_complexity, risk_score, status, next_action, created_by, dedupe_key, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(id) do update set expected_value_score=excluded.expected_value_score, updated_at=excluded.updated_at
                    """,
                    (
                        idea_id, opp["type"], opp.get("topic_cluster"), opp.get("primary_keyword"), opp.get("intent"), json_dumps(opp.get("evidence", [])),
                        opp["confidence_score"], opp["expected_value_score"], opp["money_potential_score"], opp["traffic_potential_score"],
                        opp["execution_complexity_score"], max(opp["privacy_risk_score"], opp["seo_risk_score"]), "scored", opp["next_action"], "goal_agent",
                        f"{opp['type']}:{opp.get('topic_cluster')}:{opp.get('primary_keyword')}:{opp.get('target_url')}", now, now,
                    ),
                )
        practice_opportunities = [opp for opp in opportunities if opp["type"] == "practice_asset_opportunity"]
        blog_opportunities = [opp for opp in opportunities if opp["type"] != "practice_asset_opportunity"]
        top_tasks = [
            task_from_opportunity(opp, run_id)
            for opp in blog_opportunities[: min(5, settings.max_actions_per_run)]
            if opp["expected_value_score"] >= 0.25
        ]
        if settings.mode in {"dry_run", "queue_only", "write_safe", "autonomous_full"}:
            store_blog_tasks(db, top_tasks)
            jsonl_path, md_path = export_blog_tasks(db, settings.repo_root)
            decision_id = _log_decision(db, run_id, "queue_blog_tasks", "Export Blog Agent task suggestions", "Structured queue keeps Blog Agent pure while improving priorities.", [{"source": "opportunity_scoring", "count": len(top_tasks)}], 0.8, 0.1)
            _log_action(db, run_id, decision_id, "export_blog_tasks", "queue", None, "completed", [str(jsonl_path.relative_to(settings.repo_root)), str(md_path.relative_to(settings.repo_root))], ["No blog source files modified", "No secrets included"])
            created_practice = []
            for opp in practice_opportunities:
                decision = publishing_decisions.get(opp["id"])
                if decision and decision.action in {"publish_indexable", "draft_noindex"}:
                    created_practice.append(_store_interactive_task(db, run_id, opp))
            if created_practice:
                practice_decision_id = _log_decision(db, run_id, "queue_practice_assets", "Queue practice-first SEO assets", "Practice pages are Goal Agent-owned non-blog assets and must not be assigned to the Blog Agent.", [{"source": "practice_intent_scoring", "count": len(created_practice)}], 0.78, 0.12)
                _log_action(db, run_id, practice_decision_id, "queue_interactive_page_tasks", "interactive_page_tasks", ",".join(created_practice), "completed", [], ["Practice assets kept out of Blog Agent queue", "Quality requirements attached to task"])
        codex_tasks_created = 0
        if opportunities:
            create_experiment(db, "CTA quality baseline", "cta_copy_test", [opportunities[0]["target_url"]], "CTA wording should improve app-relevant clicks without hurting engagement.", opportunities[0].get("topic_cluster") or "allgemein")
        publishable = [opp for opp in opportunities if publishing_decisions.get(opp["id"]) and publishing_decisions[opp["id"]].action in {"publish_indexable", "draft_noindex"}]
        if settings.page_generation_enabled and publishable:
            top = publishable[0]
            publishing_decision = publishing_decisions[top["id"]]
            _log_action(
                db,
                run_id,
                None,
                "defer_learning_material_generation",
                "interactive_page",
                top["id"],
                "skipped",
                [],
                [
                    "Direct one-cycle HTML generation disabled for learning materials",
                    f"Adaptive publishing candidate: {publishing_decision.action}",
                    "Use queued spec/prototype/QA/promotion cycle instead",
                    *publishing_decision.reasons,
                ],
            )
        promotion_results = promote_drafts(settings)
        promoted_files = [
            str(result.published_path.relative_to(settings.repo_root))
            for result in promotion_results
            if result.status == "promoted" and result.published_path
        ]
        held_count = len([result for result in promotion_results if result.status != "promoted"])
        if promotion_results:
            _log_action(
                db,
                run_id,
                None,
                "promote_quality_approved_drafts",
                "interactive_page",
                ",".join(promoted_files) if promoted_files else None,
                "completed" if promoted_files else "skipped",
                promoted_files,
                [
                    "Draft-first promotion gate",
                    f"Promoted: {len(promoted_files)}",
                    f"Held: {held_count}",
                    "Only quality-approved drafts are made indexable",
                ],
            )
        guardian_status = monitor_blog_agent(settings.repo_root)
        guardian_recommendations = recommend_blog_agent_adjustments(posthog.summary, opportunities)
        guardian_report = write_guardian_report(guardian_status, guardian_recommendations, settings.repo_root)
        changed_context = maybe_apply_blog_context_note(settings, guardian_recommendations, settings.repo_root)
        _log_action(
            db,
            run_id,
            None,
            "monitor_blog_agent",
            "blog_agent",
            "auto-blog.sh",
            "completed",
            [str(guardian_report.relative_to(settings.repo_root)), str(changed_context.relative_to(settings.repo_root))] if changed_context else [str(guardian_report.relative_to(settings.repo_root))],
            ["Blog Agent process checked", "No direct Blog Agent script changes", "Context notes changed only if explicit flag enabled"],
        )
        subagent_context = {
            "repo_root": settings.repo_root,
            "content_rows": content_rows,
            "internal_links": link_records,
            "opportunities": opportunities,
            "data_snapshot": {
                "posthog": posthog.summary,
                "posthog_warning": posthog.warning,
                "gsc": gsc.summary,
                "gsc_warning": gsc.warning,
                "serp": serp.summary,
            },
        }
        subagent_output = GoalOrchestrator(db).run(subagent_context)
        _log_action(
            db,
            run_id,
            None,
            "run_subagents",
            "subagents",
            None,
            "completed",
            [],
            [f"Agents run: {len(subagent_output['agents_run'])}", f"Recommendations: {len(subagent_output['recommendations'])}"],
        )
        if queue_codex_tasks or settings.mode == "autonomous_full":
            codex_tasks_created = build_and_store_tasks(db, limit=settings.max_actions_per_run)
            _log_action(db, run_id, None, "queue_codex_coding_tasks", "coding_tasks", None, "completed", [], ["Codex tasks queued only", "Codex execution remains separately gated"],)
            if settings.mode == "autonomous_full" and settings.codex_enabled:
                executed = 0
                for _ in range(max(0, settings.codex_max_tasks_per_run)):
                    result = run_next(db, settings)
                    if result is None:
                        break
                    executed += 1
                    _log_action(
                        db,
                        run_id,
                        None,
                        "run_codex_coding_task",
                        "coding_tasks",
                        None,
                        result.status,
                        result.changed_files,
                        [
                            "Codex CLI execution explicitly enabled",
                            f"Exit code: {result.exit_code}",
                            f"Safety blocked: {result.safety_blocked}",
                            f"Failure: {result.failure_reason}",
                        ],
                    )
                    if result.status != "completed":
                        break
                if executed == 0:
                    _log_action(db, run_id, None, "run_codex_coding_task", "coding_tasks", None, "skipped", [], ["No queued Codex task available"])
        ToolRegistry(db, settings).register_builtin_tools()
        Toolsmith(db, settings).propose_tool_spec("example_bottleneck_tool", "Demonstrate gated toolsmith path", "Toolsmith disabled unless autonomous_full and flag set")
        store_learning(db, "Read-mostly queueing is the safest first integration with the Blog Agent.", [{"source": "safety_policy", "summary": "Blog Agent remains unchanged"}], 0.75, ["allgemein"], "Keep queue interface separate from Blog Agent execution.", "daily")
        maybe_update_scoring(db, [{"source": "run", "summary": "No high-confidence scoring change yet"}], 0.4)
        context = build_context(db, run_id, {
            "cycle_type": cycle_type,
            "mode": settings.mode,
            "data_snapshot": {
                "content_rows": len(content_rows),
                "blog_registry": read_blog_registry(settings.repo_root),
                "posthog": posthog.summary,
                "posthog_warning": posthog.warning,
                "gsc": gsc.summary,
                "gsc_warning": gsc.warning,
                "serp": serp.summary,
                "event_schema_problems": event_problems,
                "adaptive_publishing": {key: value.__dict__ for key, value in list(publishing_decisions.items())[:20]},
                "blog_guardian": guardian_status,
                "codex_tasks_created": codex_tasks_created,
                "subagents": {
                    "agents_run": subagent_output["agents_run"],
                    "recommendations_created": len(subagent_output["recommendations"]),
                    "blocked_recommendations": len(subagent_output["blocked_recommendations"]),
                },
            },
        })
        report = generate_daily_report(db, settings, run_id, settings.repo_root)
        _log_action(db, run_id, None, "generate_report", "report", str(report), "completed", [_display_path(report, settings.repo_root)], ["Report contains no secret values"])
        publish_result = auto_publish(settings)
        _log_action(
            db,
            run_id,
            None,
            "auto_publish_goal_agent_changes",
            "git",
            "origin/main",
            publish_result.status if publish_result.ok else "failed",
            publish_result.changed_files,
            [
                publish_result.message,
                f"Pushed: {publish_result.pushed}",
                "Allowed paths only: lernmaterialien, goal_agent/generated_tools, sitemap.xml, feed.xml",
            ],
        )
        summary = f"Scanned {len(content_rows)} pages, scored {len(opportunities)} opportunities, exported {len(top_tasks)} blog tasks, queued {codex_tasks_created} Codex tasks."
        _finish_run(db, run_id, "completed", summary)
        notification = notify_daily_update(db, settings, run_id, summary)
        _log_action(db, run_id, None, "send_daily_notification", "telegram", None, "completed" if notification.ok else "skipped", [], [notification.message])
        return {"run_id": run_id, "summary": summary, "context_keys": sorted(context.keys()), "report": str(report)}
    except Exception as exc:  # noqa: BLE001
        _finish_run(db, run_id, "failed", "Run failed", exc.__class__.__name__)
        notify_daily_update(db, settings, run_id, f"Run failed: {exc.__class__.__name__}")
        raise
