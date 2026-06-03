from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


# Topics where a visual simulation adds genuine insight (priority 1)
SIMULATION_TERMS = [
    "physik", "chemie", "biologie",
    "elektrizität", "mechanik", "optik", "thermodynamik", "kinematik",
    "atom", "molekül", "reaktion", "elektrolyse", "galvanisch",
    "geometrie", "trigonometrie", "vektor",
    "stochastik", "wahrscheinlichkeit",
]

# Topics better served by a procedural step trainer (priority 2)
TRAINER_TERMS = [
    "gleichung", "gleichungen", "ableitung", "integral", "bruch", "bruchrechnung",
    "potenzen", "wurzeln", "dreisatz", "prozentrechnung",
    "quadratische", "übungen", "aufgaben", "trainer", "üben",
    "grammatik", "vokabeln", "konjugation",
    "abi", "abitur", "klassenarbeit", "klausur",
]

PRACTICE_TERMS = SIMULATION_TERMS + TRAINER_TERMS


class PracticeAssetAgent(Subagent):
    agent_name = "practice_asset"

    def run(self, context: dict) -> SubagentResult:
        recs: list[Recommendation] = []
        for opp in context.get("opportunities", [])[:50]:
            text = f"{opp.get('primary_keyword') or ''} {opp.get('target_url') or ''}".lower()
            is_sim = any(term in text for term in SIMULATION_TERMS)
            is_trainer = any(term in text for term in TRAINER_TERMS)
            is_explicit = opp.get("type") == "practice_asset_opportunity"
            if not (is_explicit or is_sim or is_trainer):
                continue

            base_priority = int(opp.get("expected_value_score", 0.5) * 100)
            if is_sim:
                # Simulations get a higher priority boost
                priority = min(100, base_priority + 20)
                title = f"Learning simulation: {opp.get('primary_keyword')}"
                rationale = (
                    "Topic has a visual/physical model worth animating. "
                    "Build an interactive simulation with a visible animated model (canvas/SVG), "
                    "at least one active prediction or observation task, specific concept feedback, and 2-step progression. "
                    "Write a spec first. If no convincing model exists, output a research note instead."
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
