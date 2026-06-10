from __future__ import annotations

import hashlib

from ..storage import Database, json_dumps, utc_now
from ..subagents.base import Recommendation
from .task_schema import CodingTask


COMMON_SAFETY = [
    "Do not deploy, push, or publish live from this coding task; final promotion/push is handled only by the Goal Agent publishing gate.",
    "Do not read, print, or commit secrets.",
    "Do not modify .env, /etc/nachhilfe-mentor, or service account JSON files.",
    "Do not modify production data.",
    "Run listed tests or explain why they could not run.",
]


GUIDED_WRITING_TERMS = (
    "bildbeschreibung",
    "bildergeschichte",
    "argumentation",
    "erörterung",
    "eroerterung",
    "interpretation",
    "aufsatz",
    "zusammenfassung",
    "charakterisierung",
    "sachtextanalyse",
    "redeanalyse",
    "gedichtanalyse",
    "musterlösung",
    "musterloesung",
    "bewertungsraster",
)


def _task_id(seed: str) -> str:
    return "coding_task_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def task_from_recommendation(rec: Recommendation) -> CodingTask | None:
    if not rec.codex_task_allowed or rec.safety_risk == "high":
        return None
    if rec.recommendation_type == "create_practice_asset":
        rec_text = " ".join([rec.title, rec.rationale, *rec.acceptance_criteria, *rec.required_context]).lower()
        if "guided writing" in rec_text or any(term in rec_text for term in GUIDED_WRITING_TERMS):
            return CodingTask(
                id=_task_id(rec.id),
                source_recommendation_id=rec.id,
                task_type="practice_page",
                title=f"Draft guided writing practice page: {rec.title}",
                goal=(
                    "Build a high-quality guided German writing practice page. "
                    "Follow these steps in order — do NOT skip step 1:\n\n"
                    "STEP 1 — LEARNING DESIGN SPEC (mandatory before any code):\n"
                    "  Read docs/goal-agent/LEARNING_ASSET_PATTERNS.md before writing the spec.\n"
                    "  Treat existing prototypes as quality references, not as rigid templates.\n"
                    "  Write a spec file to lernmaterialien/entwuerfe/<slug>-spec.md containing:\n"
                    "  - Primary keyword, search intent, target learner and learning outcome\n"
                    "  - Prompt concept and why it helps the writing skill\n"
                    "  - Asset plan: existing curated local asset, AI-generated asset only if explicitly enabled/budgeted, or licensed image/text source; include metadata, alt text, and cost tracking if generated\n"
                    "  - Writing workflow: scaffold, learner input, self-check, revision step, model solution and rubric\n"
                    "  - Typical mistakes and how the page helps learners correct them\n"
                    "  - QA checklist for mobile, desktop, German copy, rights safety and usefulness\n"
                    "  If you cannot write a convincing spec, STOP. Save a research note to goal_agent/exports/<slug>-research-needed.md.\n\n"
                    "STEP 2 — BUILD (only after a solid spec exists):\n"
                    "  Build a noindex guided practice page under lernmaterialien/entwuerfe/ or lernmaterialien/deutsch/.\n"
                    "  Do not call paid image-generation APIs unless GOAL_AGENT_IMAGE_GENERATION_ENABLED=true and the configured budget is stated in the spec.\n"
                    "  The first viewport must be compact and exercise-first: prompt/image plus task context, not a large empty landing hero.\n"
                    "  The page MUST include: writing textarea, structure scaffold, word bank, self-check checklist, rubric, model solution, "
                    "  typical mistakes and revision guidance. Do not pretend to auto-grade open writing.\n\n"
                    "STEP 3 — SELF-CHECK:\n"
                    "  Verify: (a) no horizontal scroll at 375 px, (b) no text clipping, (c) all German text uses correct umlauts, "
                    "  (d) no visible escaped formatting artifacts such as literal \\\\n in rendered text or textareas, "
                    "  (e) noindex is set, (f) image metadata/cost log exists for generated assets, (g) tests pass.\n\n"
                    "STEP 4 — QUALITY PASS (mandatory before finishing):\n"
                    "  Do one explicit improvement pass after the first working draft. Tighten the learning task, wording, layout density, "
                    "  mobile behavior, and usefulness. Then write lernmaterialien/entwuerfe/<slug>-qa.md with:\n"
                    "  - usefulness score and what the page teaches better than a blog article\n"
                    "  - interaction checks performed, including one happy path and one mistake path\n"
                    "  - mobile/desktop layout notes, including 375 px result\n"
                    "  - copy QA for umlauts, visible escape artifacts, and no fake auto-grading\n"
                    "  - promotion recommendation: promote, hold, or rewrite, with concrete reasons\n"
                    "  If the page is only minimally acceptable, mark it hold/rewrite in the QA note instead of presenting it as done.\n\n"
                    "IMPORTANT: A good guided writing page helps students compare and revise their own text. "
                    "A fake AI grader, generic checklist, or copied internet image fails the task."
                ),
                context_summary=f"{rec.rationale}\nTarget topic: {rec.target_topic}\nTarget URL: {rec.target_url or ''}",
                allowed_paths=[
                    "docs/goal-agent/LEARNING_ASSET_PATTERNS.md",
                    "lernmaterialien/entwuerfe/",
                    "lernmaterialien/deutsch/",
                    "lernmaterialien/assets/",
                    "goal_agent/exports/",
                    "tests/goal_agent/",
                ],
                forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
                acceptance_criteria=[
                    *rec.acceptance_criteria,
                    "A spec file must exist in lernmaterialien/entwuerfe/ before the HTML page is created.",
                    "Generated or referenced images must have metadata, alt text and rights/cost notes; paid generation requires GOAL_AGENT_IMAGE_GENERATION_ENABLED=true and a configured budget.",
                    "Open writing is not auto-graded; use self-check and rubric comparison.",
                    "The first viewport is compact and exercise-first, with no large empty hero space.",
                    "After the first working draft, perform one explicit improvement pass before finishing.",
                    "A QA note must exist in lernmaterialien/entwuerfe/ with usefulness, interaction, mobile, copy and promotion assessment.",
                    "All user-facing German copy must use correct umlauts; ASCII replacements are forbidden in visible text.",
                    "Rendered page text and textarea presets must not show raw escape sequences such as literal \\\\n; use real line breaks.",
                    "noindex is set; sitemap inclusion only after promotion gates pass.",
                ],
                safety_constraints=COMMON_SAFETY,
                test_commands=["python3 -m pytest tests/goal_agent -q"],
                mode="draft_only",
                publish_policy="draft_noindex_only",
                priority=rec.priority,
            )
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="practice_page",
            title=f"Draft learning simulation: {rec.title}",
            goal=(
                "Build a high-quality interactive learning simulation. "
                "Follow these steps in order — do NOT skip step 1:\n\n"
                    "STEP 1 — RESEARCH & SPEC (mandatory before any code):\n"
                    "  Read docs/goal-agent/LEARNING_ASSET_PATTERNS.md before writing the spec.\n"
                    "  Treat existing assets as quality references, not as rigid templates.\n"
                    "  Research the topic thoroughly. Write a spec file to lernmaterialien/entwuerfe/<slug>-spec.md containing:\n"
                "  - The exact physical, chemical, or mathematical model (with formula or rule)\n"
                "  - What the learner will see and interact with (describe the animation/diagram)\n"
                "  - The active tasks (predictions, inputs) and what correct/incorrect looks like\n"
                "  - The misconception(s) the simulation addresses\n"
                "  - Why this is better than a plain article for this keyword\n"
                "  If you cannot write a convincing spec, STOP. Save a research note to goal_agent/exports/<slug>-research-needed.md "
                "  explaining what information is missing. Do not build a simulation without a solid spec.\n\n"
                "STEP 2 — BUILD (only after a solid spec exists):\n"
                "  Build the simulation as a single self-contained HTML file in lernmaterialien/lernsimulationen/.\n"
                "  The simulation MUST have: a visible animated model (canvas or DOM), at least one prediction/input task, "
                "  feedback that names the specific concept or law, and a 2-step progression.\n"
                "  The underlying model must be factually correct — cross-check against your spec.\n\n"
                "STEP 3 — SELF-CHECK:\n"
                "  Before finishing, verify: (a) the simulation is factually correct, (b) it works at 375 px width, "
                "  (c) all German text uses correct umlauts, (d) no visible escaped formatting artifacts such as literal \\\\n, "
                "  (e) noindex is set, (f) tests pass.\n\n"
                "STEP 4 — QUALITY PASS (mandatory before finishing):\n"
                "  Do one explicit improvement pass after the first working prototype. Tighten the model, feedback, task progression, "
                "  layout density, mobile behavior, and educational usefulness. Then write lernmaterialien/entwuerfe/<slug>-qa.md with:\n"
                "  - usefulness score and what the simulation teaches better than a blog article\n"
                "  - model/factual checks performed\n"
                "  - interaction checks, including one correct and one incorrect path\n"
                "  - mobile/desktop layout notes, including 375 px result\n"
                "  - promotion recommendation: promote, hold, or rewrite, with concrete reasons\n"
                "  If the simulation is only minimally acceptable, mark it hold/rewrite in the QA note instead of presenting it as done.\n\n"
                "IMPORTANT: producing something thin, static, or factually wrong is worse than producing nothing. "
                "If the simulation would not genuinely help a student understand the concept better than reading the blog post, do not publish it."
            ),
            context_summary=f"{rec.rationale}\nTarget topic: {rec.target_topic}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["docs/goal-agent/LEARNING_ASSET_PATTERNS.md", "lernmaterialien/entwuerfe/", "lernmaterialien/lernsimulationen/", "goal_agent/exports/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[
                *rec.acceptance_criteria,
                "A spec file must exist in lernmaterialien/entwuerfe/ before the simulation HTML is created.",
                "If no convincing spec could be written, a research-needed note must exist in goal_agent/exports/ and no simulation HTML is created.",
                "The simulation shows a visible animated model — canvas animation, SVG, or DOM-based diagram.",
                "The learner makes at least one active prediction or input before seeing the result.",
                "Feedback names the specific concept or physical/chemical law, not just 'richtig' or 'falsch'.",
                "At least 2-step progression is present.",
                "The underlying model is factually correct (verified in spec).",
                "Generated asset uses: lernmaterialien/entwuerfe/ (spec), lernmaterialien/lernsimulationen/ (prototype).",
                "All user-facing German copy must use correct umlauts; ASCII replacements are forbidden in visible text.",
                "Rendered page text must not show raw escape sequences such as literal \\\\n; use real line breaks.",
                "After the first working prototype, perform one explicit improvement pass before finishing.",
                "A QA note must exist in lernmaterialien/entwuerfe/ with usefulness, model, interaction, mobile and promotion assessment.",
                "Do not ship a weak one-cycle result; always write the spec first and leave the simulation noindex until the quality gate passes.",
                "noindex is set; no push or deploy; sitemap inclusion only after promotion gates pass.",
            ],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="draft_noindex_only",
            priority=rec.priority,
        )
    if rec.recommendation_type == "improve_internal_links":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="internal_linking",
            title=f"Draft internal-link improvement: {rec.title}",
            goal="Create a safe internal-link improvement spec or queue item. Do not mass-edit production blog posts.",
            context_summary=f"{rec.rationale}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["goal_agent/exports/", "goal_agent/queues/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[*rec.acceptance_criteria, "No keyword stuffing.", "No mass link insertion."],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="queue_for_review",
            priority=rec.priority,
        )
    if rec.recommendation_type == "update_existing_content":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="quality_fix",
            title=f"Draft content quality fix: {rec.title}",
            goal="Create a review/spec for improving existing content quality. Do not rewrite articles directly.",
            context_summary=f"{rec.rationale}\nTarget URL: {rec.target_url or ''}",
            allowed_paths=["goal_agent/exports/", "goal_agent/queues/", "tests/goal_agent/"],
            forbidden_paths=["auto-blog.sh", "blog/posts/", "blog/articles/", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=[*rec.acceptance_criteria, "Blog Agent remains the article writer."],
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="draft_only",
            publish_policy="queue_for_review",
            priority=rec.priority,
        )
    if rec.recommendation_type == "quality_fix":
        return CodingTask(
            id=_task_id(rec.id),
            source_recommendation_id=rec.id,
            task_type="quality_fix",
            title=f"Quality fix: {rec.title}",
            goal="Implement a safe quality or test improvement if it does not touch forbidden files.",
            context_summary=f"{rec.rationale}\nTarget topic: {rec.target_topic}",
            allowed_paths=["goal_agent/", "tests/goal_agent/", "docs/goal-agent/"],
            forbidden_paths=["auto-blog.sh", ".env", "/etc/nachhilfe-mentor", "*service-account*.json", ".git/"],
            acceptance_criteria=rec.acceptance_criteria,
            safety_constraints=COMMON_SAFETY,
            test_commands=["python3 -m pytest tests/goal_agent -q"],
            mode="modify_repo",
            publish_policy="never_publish",
            priority=rec.priority,
        )
    return None


def build_tasks_from_recommendations(recommendations: list[Recommendation], limit: int = 10) -> list[CodingTask]:
    tasks = [task for rec in recommendations for task in [task_from_recommendation(rec)] if task is not None]
    return sorted(tasks, key=lambda task: task.priority, reverse=True)[:limit]


def build_tasks_from_state(db: Database, limit: int = 10) -> list[CodingTask]:
    from ..subagents.base import Recommendation

    rows = db.query("select * from subagent_recommendations where status='queued' and codex_task_allowed=1 and safety_risk != 'high' order by priority desc limit ?", (limit,))
    recs = [
        Recommendation(
            id=row["id"],
            source_agent=row["source_agent"],
            recommendation_type=row["recommendation_type"],
            title=row["title"],
            rationale=row["rationale"],
            priority=row["priority"],
            confidence=row["confidence"],
            target_topic=row["target_topic"] or "",
            target_url=row["target_url"],
            suggested_publish_decision=row["suggested_publish_decision"],
            codex_task_allowed=bool(row["codex_task_allowed"]),
            safety_risk=row["safety_risk"],
            acceptance_criteria=__import__("json").loads(row["acceptance_criteria_json"] or "[]"),
            required_context=__import__("json").loads(row["required_context_json"] or "[]"),
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return build_tasks_from_recommendations(recs, limit)


def retire_obsolete_coding_tasks(db: Database) -> int:
    """
    Retire queued/blocked tasks created with older learning-asset prompts.

    These tasks are not useful to rerun after the asset policy changed: they
    either ask for "learning simulations" around open writing skills or broad
    exam-advice topics that now belong to guided writing specs or Blog Agent
    work. Retiring them prevents autonomous runs from spending Codex time on
    stale prompts while keeping the audit trail in the DB.
    """
    stale_title_markers = [
        "Draft learning simulation: Draft practice page:",
        "Draft practice asset: Draft practice page:",
        "Create practice-first asset for bildbeschreibung",
    ]
    stale_topic_markers = [
        "prüfung: so meisterst du",
        "prüfungstag",
        "klausur letzte nacht",
        "ki hausaufgaben hilfe",
        "abitur vorbereitung: so meisterst du",
    ]
    now = utc_now()
    retired = 0
    with db.connect() as conn:
        rows = conn.execute(
            """
            select id, title from coding_tasks
            where status in ('queued', 'blocked_by_safety', 'failed')
            """
        ).fetchall()
        for row in rows:
            title = (row["title"] or "").lower()
            is_stale = any(marker.lower() in title for marker in stale_title_markers)
            is_stale = is_stale or any(marker in title for marker in stale_topic_markers)
            if not is_stale:
                continue
            conn.execute(
                """
                update coding_tasks
                set status='retired',
                    updated_at=?,
                    result_summary='retired by learning-asset policy upgrade; regenerate from current Pattern Library'
                where id=?
                """,
                (now, row["id"]),
            )
            retired += 1
    return retired


def store_coding_tasks(db: Database, tasks: list[CodingTask]) -> int:
    now = utc_now()
    count = 0
    with db.connect() as conn:
        for task in tasks:
            problems = task.validate()
            if problems:
                continue
            existing = conn.execute("select status from coding_tasks where id=?", (task.id,)).fetchone()
            status = task.status
            if existing:
                status = existing["status"]
                if existing["status"] == "retired" and task.title.lower().startswith("draft guided writing practice page:"):
                    status = task.status
                latest = conn.execute(
                    """
                    select status, failure_reason, changed_files_json from coding_task_runs
                    where task_id=?
                    order by created_at desc
                    limit 1
                    """,
                    (task.id,),
                ).fetchone()
                if latest and latest["status"] == "completed":
                    changed_files = latest["changed_files_json"] or "[]"
                    if task.title.lower().startswith("draft guided writing practice page:") and "lernmaterialien/" not in changed_files:
                        status = task.status
                    else:
                        status = "completed"
                elif existing["status"] in {"blocked_by_safety", "failed"}:
                    reason = (latest["failure_reason"] if latest else "") or ""
                    retryable_reasons = (
                        "dirty worktree",
                        "Codex execution disabled",
                        "Codex binary not found",
                        "timeout",
                    )
                    if any(marker in reason for marker in retryable_reasons):
                        status = "queued"
            conn.execute(
                """
                insert into coding_tasks (
                  id, source_recommendation_id, task_type, title, goal, context_summary,
                  target_files_allowed_json, target_files_forbidden_json,
                  acceptance_criteria_json, safety_constraints_json, test_commands_json,
                  mode, publish_policy, created_at, updated_at, status,
                  result_summary, changed_files_json, priority
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                  title=excluded.title,
                  goal=excluded.goal,
                  context_summary=excluded.context_summary,
                  priority=excluded.priority,
                  updated_at=excluded.updated_at,
                  status=excluded.status
                """,
                (
                    task.id,
                    task.source_recommendation_id,
                    task.task_type,
                    task.title,
                    task.goal,
                    task.context_summary,
                    json_dumps(task.allowed_paths),
                    json_dumps(task.forbidden_paths),
                    json_dumps(task.acceptance_criteria),
                    json_dumps(task.safety_constraints),
                    json_dumps(task.test_commands),
                    task.mode,
                    task.publish_policy,
                    task.created_at,
                    now,
                    status,
                    task.result_summary,
                    json_dumps(task.changed_files),
                    task.priority,
                ),
            )
            count += 1
    return count
