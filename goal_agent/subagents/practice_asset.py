from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


# Terms that strongly suggest a visual simulation is the right format.
# These are signals, not a whitelist — any educational topic can qualify.
SIMULATION_SIGNALS = [
    "physik", "chemie", "biologie",
    "elektrizität", "mechanik", "optik", "thermodynamik", "kinematik",
    "atom", "molekül", "reaktion", "elektrolyse", "galvanisch",
    "geometrie", "trigonometrie", "vektor",
    "stochastik", "wahrscheinlichkeit",
    "wellen", "schwingung", "magnetfeld", "stromkreis", "linse",
    "osmose", "diffusion", "fotosynthese", "zellbiologie",
    "koordinatensystem", "funktionen", "kurvendiskussion",
]

# Terms that suggest a step-by-step procedural trainer fits better.
# Use trainer only when a visual model would add no real insight.
TRAINER_SIGNALS = [
    "gleichung", "gleichungen", "ableitung", "integral", "bruch", "bruchrechnung",
    "potenzen", "wurzeln", "dreisatz", "prozentrechnung",
    "quadratische", "terme", "binomische formeln",
    "übungen", "aufgaben", "trainer", "üben", "rechnen",
    "grammatik", "vokabeln", "konjugation", "deklination",
    "abi", "abitur", "klassenarbeit", "klausur",
    "textaufgaben", "geometrie aufgaben", "statistik aufgaben",
]

# Topics that should be evaluated as practice assets regardless of keyword match.
# Used as an escape hatch for opportunities the scanner already classified.
ALWAYS_EVALUATE_TYPES = {"practice_asset_opportunity"}


def _classify(text: str) -> tuple[bool, bool]:
    """Return (is_sim_signal, is_trainer_signal) based on keyword overlap."""
    is_sim = any(term in text for term in SIMULATION_SIGNALS)
    is_trainer = any(term in text for term in TRAINER_SIGNALS)
    return is_sim, is_trainer


def _is_educational(opp: dict) -> bool:
    """
    Return True for any opportunity worth evaluating as a practice asset.
    The lists above are signals for format choice, not a whitelist.
    We evaluate everything in the school/education domain; the spec step
    will decide whether a simulation or trainer is the right format.
    """
    if opp.get("type") in ALWAYS_EVALUATE_TYPES:
        return True
    cluster = (opp.get("topic_cluster") or "").lower()
    keyword = (opp.get("primary_keyword") or "").lower()
    # Exclude pure editorial/news/opinion opportunities
    if any(x in cluster for x in ("news", "meinung", "kommentar", "aktuell")):
        return False
    # Include anything with a school-subject or learning signal
    school_signals = [
        "mathe", "mathematik", "physik", "chemie", "biologie", "deutsch",
        "englisch", "latein", "geschichte", "erdkunde", "geographie",
        "informatik", "wirtschaft", "politik", "musik", "kunst",
        "lernen", "schule", "nachhilfe", "abitur", "klausur", "übung",
        "aufgaben", "trainer", "simulation", "lernmaterial",
    ]
    text = f"{keyword} {cluster} {opp.get('target_url') or ''}".lower()
    return any(s in text for s in school_signals) or bool(_classify(text)[0] or _classify(text)[1])


class PracticeAssetAgent(Subagent):
    agent_name = "practice_asset"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        for opp in context.get("opportunities", [])[:50]:
            if not _is_educational(opp):
                continue

            text = f"{opp.get('primary_keyword') or ''} {opp.get('target_url') or ''}".lower()
            is_sim, is_trainer = _classify(text)
            # When neither signal fires, default to simulation-first:
            # the spec step will decide; trainer only if simulation is unsuitable.
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
