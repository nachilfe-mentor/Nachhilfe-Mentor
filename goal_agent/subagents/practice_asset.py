from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


# ── Format signals ────────────────────────────────────────────────────────────
#
# These are hints, not a whitelist. Any school topic can qualify — but the
# format decision (simulation / trainer / neither) must be defensible:
#
#   Simulation  → topic has a physical, chemical, mathematical, or biological
#                 MODEL that becomes clearer when animated or interacted with.
#                 Ask: "Would moving parts / a diagram / a live graph teach
#                 something a static text cannot?"
#
#   Trainer     → topic is a PROCEDURE with unambiguous right/wrong answers
#                 that can be auto-generated and auto-checked. Ask: "Can I
#                 generate 50 random tasks and check the answer programmatically?"
#
#   Guided writing page
#               → topic is an open writing skill where automatic grading would
#                 be fake. Build only if the page provides a real prompt,
#                 learner writing area, self-check, rubric, model solution and
#                 revision workflow. Never present it as auto-graded.
#
#   Neither     → topic is advice, strategy, tips, or meta-learning. These
#                 belong in blog articles, not interactive tools. A bad
#                 interactive tool is worse than no tool at all.

SIMULATION_SIGNALS = [
    # Naturwissenschaften
    "physik", "chemie", "biologie",
    "elektrizität", "mechanik", "optik", "thermodynamik", "kinematik",
    "atom", "molekül", "reaktion", "elektrolyse", "galvanisch",
    "wellen", "schwingung", "magnetfeld", "stromkreis", "linse", "brechung",
    "osmose", "diffusion", "fotosynthese", "zellbiologie", "genetik",
    "radioaktivität", "kernspaltung", "spektrum",
    # Mathematik mit visuellen Modellen
    "geometrie", "trigonometrie", "vektor", "koordinatensystem",
    "funktionen", "kurvendiskussion", "stochastik", "wahrscheinlichkeit",
    "integral visuali", "ableitung visuali",
]

TRAINER_SIGNALS = [
    # Mathematik: Rechenverfahren mit eindeutigem Ergebnis
    "gleichung lösen", "gleichungen lösen", "gleichung aufstellen",
    "ableitung", "integral", "bruch", "bruchrechnung",
    "potenzen", "wurzeln", "dreisatz", "prozentrechnung",
    "quadratische", "terme vereinfachen", "binomische",
    "textaufgaben", "geometrie aufgaben", "statistik aufgaben",
    # Sprachen: Regelbasierte Verfahren
    "grammatik", "vokabeln", "konjugation", "deklination", "kasus",
    "zeitformen", "irregular verbs",
]

GUIDED_WRITING_SIGNALS = [
    "bildbeschreibung", "bildergeschichte", "tierbeschreibung", "ortsbeschreibung",
    "argumentation", "erörterung", "interpretation", "analyse schreiben",
    "aufsatz", "zusammenfassung", "charakterisierung", "sachtextanalyse",
    "redeanalyse", "karikatur analysieren", "gedichtanalyse",
    "übung mit lösung", "übungen mit lösungen", "musterlösung", "bewertungsraster",
]

# Topics that look educational but are advice/strategy — these belong in blog
# posts, not learning tools. Writing skills are handled separately as guided
# practice pages, not as simulations or auto-graded trainers.
NOT_INTERACTIVE_SIGNALS = [
    # Ratgeber / Tipps-Artikel
    "tipps", "tricks", "ratgeber", "so lernst du", "so meisterst du",
    "lernmethode", "lernstrategie", "lernplan", "motivation",
    "prüfungsangst", "prüfungstag", "konzentration",
    "abitur vorbereitung tipps", "klausur tipps", "abitur tipps",
    "stress", "schlaf", "ernährung",
    # Meta-Lernen
    "wie lerne ich", "besser lernen", "effektiv lernen",
    "gedächtnis", "gehirn", "feynman", "pomodoro",
]

ALWAYS_EVALUATE_TYPES = {"practice_asset_opportunity"}


def _classify(text: str) -> tuple[bool, bool, bool, bool]:
    """Return (is_sim, is_trainer, is_guided_writing, is_not_interactive)."""
    is_not = any(term in text for term in NOT_INTERACTIVE_SIGNALS)
    is_sim = any(term in text for term in SIMULATION_SIGNALS)
    is_trainer = any(term in text for term in TRAINER_SIGNALS)
    is_guided_writing = any(term in text for term in GUIDED_WRITING_SIGNALS)
    return is_sim, is_trainer, is_guided_writing, is_not


def _is_interactive_topic(opp: dict) -> bool:
    """
    Return True only for topics where an interactive tool genuinely helps.
    Topics that are purely advice, tips, or open writing skills return False —
    those belong in blog articles, not interactive tools.
    """
    keyword = (opp.get("primary_keyword") or "").lower()
    cluster = (opp.get("topic_cluster") or "").lower()
    url = (opp.get("target_url") or "").lower()
    text = f"{keyword} {cluster} {url}"

    is_sim, is_trainer, is_guided_writing, is_not = _classify(text)

    if is_guided_writing:
        return True

    # Hard exclusion: tips/advice/writing topics are never interactive tools
    if is_not and not (is_sim or is_trainer):
        return False

    # Explicit classification from scanner
    if opp.get("type") in ALWAYS_EVALUATE_TYPES:
        return not is_not

    # Include school subjects that have a concrete procedural or model-based angle
    school_signals = [
        "mathe", "mathematik", "physik", "chemie", "biologie",
        "englisch", "latein", "informatik",
        "gleichung", "funktion", "integral", "ableitung", "bruch",
        "übungen", "aufgaben", "trainer", "simulation", "lernmaterial",
        "rechnen", "berechnen",
    ]
    has_school = any(s in text for s in school_signals)
    return has_school and not is_not


class PracticeAssetAgent(Subagent):
    agent_name = "practice_asset"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        for opp in context.get("opportunities", [])[:50]:
            if not _is_interactive_topic(opp):
                continue

            text = f"{opp.get('primary_keyword') or ''} {opp.get('target_url') or ''}".lower()
            is_sim, is_trainer, is_guided_writing, _ = _classify(text)
            if is_guided_writing:
                base_priority = int(opp.get("expected_value_score", 0.5) * 100)
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, opp["id"]),
                    source_agent=self.agent_name,
                    recommendation_type="create_practice_asset",
                    title=f"Guided writing practice page: {opp.get('primary_keyword')}",
                    rationale=(
                        "Topic is an open German writing skill. Do not build a fake simulation or auto-grader. "
                        "Build a guided practice page with a strong image/text prompt, learner writing area, "
                        "word bank, self-check checklist, model solution, rubric, typical mistakes and a revision workflow. "
                        "For Bildbeschreibung-style pages, use AI-generated or licensed image prompts with metadata; "
                        "never copy random internet images. Prefer the curated local asset set unless image generation is explicitly enabled and budgeted."
                    ),
                    priority=min(100, base_priority + 15),
                    confidence=0.78,
                    target_topic=opp.get("topic_cluster") or "deutsch schreiben",
                    target_url=opp.get("target_url"),
                    suggested_publish_decision="draft_noindex",
                    codex_task_allowed=True,
                    safety_risk="low",
                    acceptance_criteria=[
                        "FIRST: write a learning-design spec to /lernmaterialien/entwuerfe/ with keyword, target learner, prompt concept, rubric, model solution strategy, image/asset plan and QA checklist.",
                        "If an image is needed, create or reference only rights-safe assets: existing curated local assets, AI-generated assets with metadata, or licensed sources with source/license/date. Do not copy random internet images.",
                        "Do not call paid image-generation APIs unless GOAL_AGENT_IMAGE_GENERATION_ENABLED=true and a monthly budget is configured.",
                        "Track every generated image in a JSON cost/asset log with model, quality, size, prompt, count, estimated cost and remaining budget.",
                        "Use no more than the minimum necessary image count; prefer 1-2 images per prototype unless the spec justifies more.",
                        "Build a real learning workflow: prompt, writing textarea, word bank, structure scaffold, self-check checklist, Bewertungsraster/rubric, Musterlösung/model solution, typical mistakes and revision guidance.",
                        "Do not claim automatic grading for open writing. Use self-check or rubric comparison only.",
                        "The page must be useful without logging or sending student text anywhere; no raw answer tracking.",
                        "No generic landing-page hero: the first viewport must show the exercise prompt and image compactly.",
                        "Layout must work at 375 px width with no horizontal scroll, no text clipping and no oversized empty hero space.",
                        "Visible German text uses correct umlauts (ä, ö, ü, Ä, Ö, Ü, ß).",
                        "Start as draft/noindex under /lernmaterialien/entwuerfe/ or /lernmaterialien/deutsch/ until quality gate review.",
                        "Include primary keyword, search intent, topic cluster, learning outcome, internal links, LearningResource schema and privacy-safe tracking plan.",
                    ],
                    required_context=[
                        "guided writing practice standard",
                        "image asset policy",
                        "rubric and model solution standard",
                        "Nachhilfe Mentor design standard",
                        "quality rules",
                    ],
                ))
                continue
            # Simulation-first: only choose trainer when clear procedural signals
            # fire and no simulation signal fires. For everything else the spec
            # step will decide — if no model exists, it must write a research note.
            prefer_sim = is_sim or (not is_trainer)

            base_priority = int(opp.get("expected_value_score", 0.5) * 100)
            if prefer_sim:
                # Simulations get a higher priority boost
                priority = min(100, base_priority + 20)
                title = f"Learning simulation: {opp.get('primary_keyword')}"
                rationale = (
                    "Simulation is the default format for any educational topic with a physical, "
                    "chemical, mathematical, or biological model worth exploring visually. "
                    "Write a spec first — if a convincing animated model exists, build the simulation. "
                    "If the topic is purely procedural and a visual model adds no insight, "
                    "switch to a step trainer and document the decision in the spec. "
                    "If no solid idea exists at all, write a research note and stop."
                )
                criteria = [
                    "FIRST: write a spec to /lernmaterialien/entwuerfe/ with: topic, model, what the learner sees, active tasks, misconceptions, keyword. No spec → no build.",
                    "If no convincing simulation model exists, save a research note to goal_agent/exports/ and stop.",
                    "The simulation must show a visible animated model (canvas, SVG, or DOM animation) — not just sliders and numbers.",
                    "Build a real learning interaction: active answer input, answer checking, immediate feedback on every response, hints after mistakes, and repeated practice across multiple tasks.",
                    "Feedback must name the specific concept or law, not just say 'richtig' or 'falsch'.",
                    "At least 2-step progression: first concept confirmed, then next concept or deeper question.",
                    "The underlying model must be factually correct — verify in the spec.",
                    "Layout must work at 375 px width with no horizontal scroll and thumb-reachable controls.",
                    "Visible German text uses correct umlauts (ä, ö, ü, Ä, Ö, Ü, ß).",
                    "Start as draft/noindex in /lernmaterialien/lernsimulationen/; do not promote without quality gate review.",
                    "Use modern responsive Nachhilfe Mentor design (dark canvas, light panel, Inter font, correct favicon links).",
                    "Include primary keyword, search intent, topic cluster, learning outcome, internal links, schema and privacy-safe tracking.",
                ]
                required = ["opportunity", "keyword strategy", "quality rules",
                            "learning simulation standards", "practice-first rules",
                            "simulation spec template", "research-first rule"]
            else:
                # Trainer: lower priority boost, different criteria
                priority = min(100, base_priority + 8)
                title = f"Step trainer: {opp.get('primary_keyword')}"
                rationale = (
                    "Topic is a calculation or language procedure. A visual simulation adds no real insight here. "
                    "Build a step-by-step exercise trainer: programmatically generated tasks, active input, "
                    "full written solution path on every mistake, and explicit misconception warnings per level. "
                    "No hardcoded example tasks — all tasks must be generated with random parameters and integer/exact results."
                )
                criteria = [
                    "FIRST: write a spec to /lernmaterialien/entwuerfe/ explaining why a trainer fits better than a simulation for this topic.",
                    "All tasks must be generated programmatically — no hardcoded example tasks.",
                    "Build a real learning interaction: active answer input, answer checking, immediate feedback on every response, hints after mistakes, and repeated practice across multiple tasks.",
                    "On every wrong answer: show the full step-by-step solution and name at least one specific misconception for this level.",
                    "Feedback must name the specific concept or law, not just say 'richtig' or 'falsch'.",
                    "At least 3 difficulty levels with automatic progression; 3+ tasks per level.",
                    "Layout must work at 375 px width with no horizontal scroll and thumb-reachable controls.",
                    "Visible German text uses correct umlauts (ä, ö, ü, Ä, Ö, Ü, ß).",
                    "Start as draft/noindex in /lernmaterialien/lernsimulationen/; do not promote without quality gate review.",
                    "Use modern responsive Nachhilfe Mentor design (light panel, Inter font, correct favicon links).",
                    "Include primary keyword, search intent, topic cluster, learning outcome, internal links, schema and privacy-safe tracking.",
                ]
                required = ["opportunity", "keyword strategy", "quality rules",
                            "step trainer standards", "practice-first rules", "research-first rule"]

            recs.append(Recommendation(
                id=rec_id(self.agent_name, opp["id"]),
                source_agent=self.agent_name,
                recommendation_type="create_practice_asset",
                title=title,
                rationale=rationale,
                priority=priority,
                confidence=0.75,
                target_topic=opp.get("topic_cluster") or "allgemein",
                target_url=opp.get("target_url"),
                suggested_publish_decision="draft_noindex",
                codex_task_allowed=True,
                safety_risk="low",
                acceptance_criteria=criteria,
                required_context=required,
            ))
        return SubagentResult(self.agent_name, "ok", recs[:10], 0.75, 75)
