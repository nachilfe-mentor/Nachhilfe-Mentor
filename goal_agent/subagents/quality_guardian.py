from __future__ import annotations

from .base import Recommendation, Subagent, SubagentResult, rec_id


class QualityGuardianAgent(Subagent):
    agent_name = "quality_guardian"

    def run(self, context: dict) -> SubagentResult:
        recs = []
        for rec in context.get("candidate_recommendations", []):
            if rec.safety_risk == "high" or rec.confidence < 0.35 or rec.priority < 25:
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, rec.id),
                    source_agent=self.agent_name,
                    recommendation_type="hold",
                    title=f"Hold low-quality or risky recommendation: {rec.title}",
                    rationale="Quality First gate blocked this recommendation because risk is too high or confidence/priority too low.",
                    priority=100,
                    confidence=0.9,
                    target_topic=rec.target_topic,
                    target_url=rec.target_url,
                    suggested_publish_decision="hold",
                    codex_task_allowed=False,
                    safety_risk="medium",
                    acceptance_criteria=["Do not execute until quality/risk improves."],
                    required_context=["quality gate"],
                ))
                continue
            if rec.recommendation_type == "create_practice_asset" and not _practice_asset_brief_is_strong(rec):
                recs.append(Recommendation(
                    id=rec_id(self.agent_name, f"weak_practice:{rec.id}"),
                    source_agent=self.agent_name,
                    recommendation_type="hold",
                    title=f"Hold underspecified learning simulation: {rec.title}",
                    rationale=(
                        "Quality First gate blocked this practice asset because the brief does not require a real learning "
                        "simulation with active input, checking, feedback, mistake correction, repetition, design QA and SEO intent."
                    ),
                    priority=100,
                    confidence=0.92,
                    target_topic=rec.target_topic,
                    target_url=rec.target_url,
                    suggested_publish_decision="hold",
                    codex_task_allowed=False,
                    safety_risk="medium",
                    acceptance_criteria=[
                        "Rewrite the brief as a multi-cycle learning simulation spec before execution.",
                        "Require active answer input, answer checking, feedback, mistake correction and repeated practice.",
                        "Keep output noindex until the quality, SEO, design and usefulness gates pass.",
                    ],
                    required_context=["learning simulation quality gate", "Nachhilfe Mentor design standard"],
                ))
        return SubagentResult(self.agent_name, "ok", recs, 0.9, 100, safety_notes=["Quality First is the primary publishing rule."])


def _practice_asset_brief_is_strong(rec: Recommendation) -> bool:
    text = " ".join([rec.rationale, *rec.acceptance_criteria, *rec.required_context]).lower()
    required_groups = [
        # Sichtbare Simulation: animated model muss beschrieben sein
        ("canvas", "animation", "svg", "dom animation", "sichtbar", "visible", "modell", "simulation"),
        # Aktive Aufgabe: Vorhersage oder Eingabe
        ("vorhersage", "prediction", "input", "eingabe", "active task", "active prediction"),
        # Feedback: muss Konzept nennen, nicht nur richtig/falsch
        ("concept", "konzept", "gesetz", "law", "specific feedback", "specific concept"),
        # Fachliche Korrektheit: model muss verifiziert sein
        ("model", "modell", "correct", "korrekt", "verified", "verifiziert", "factually"),
        # Spec-first: kein Build ohne Spec
        ("spec", "entwurf", "research note", "research-first", "no spec"),
        # Progression: mindestens 2 Schritte
        ("progression", "2-step", "two-step", "fortschritt", "next concept", "unlocked"),
        # Mobile
        ("375", "mobile", "responsive", "thumb"),
        # SEO
        ("keyword", "suchintent", "seo"),
    ]
    return all(any(term in text for term in group) for group in required_groups)
