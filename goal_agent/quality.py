from __future__ import annotations

import re
from dataclasses import dataclass


SPAM_PATTERNS = [
    r"\bbeste\s+nachhilfe\s+nachhilfe\s+nachhilfe\b",
    r"\bgarantiert\s+platz\s+1\b",
    r"\bkostenlos\s+download\s+download\s+download\b",
]

LOW_VALUE_INTERACTION_PATTERNS = [
    r"\bWähle eine Schwierigkeit und markiere, wie sicher du dich fühlst\b",
    r"\bSicherheit nach dem Lösen\b",
    r"\bLösung anzeigen\b",
    r"\bLern-Check\b",
]

UMLAUT_REPLACEMENT_SUSPECTS = [
    (r"\bSchueler(?:in|innen)?\b", "Schüler"),
    (r"\bSchuelertext(?:e|es)?\b", "Schülertext"),
    (r"\bSchuelerseite(?:n)?\b", "Schülerseite"),
    (r"\bUebung(?:en)?\b", "Übung/Übungen"),
    (r"\bUeberarbeitung(?:en)?\b", "Überarbeitung"),
    (r"\bLoesung(?:en)?\b", "Lösung/Lösungen"),
    (r"\bPruefung(?:en)?\b", "Prüfung/Prüfungen"),
    (r"\bPruef(?:e|en|t|ung|ungen)\b", "prüfe/prüfen/Prüfung"),
    (r"\bmuendlich(?:e|er|es|en)?\b", "mündlich"),
    (r"\bspaeter\b", "später"),
    (r"\bnaechste(?:m|n|r|s)?\b", "nächste/nächster/nächstem"),
    (r"\bwaehle(?:n)?\b", "wähle/wählen"),
    (r"\baehnlich(?:e|er|es|en)?\b", "ähnlich"),
    (r"\bfuer\b", "für"),
    (r"\bkoennen\b", "können"),
    (r"\bueben\b", "üben"),
    (r"\buebst\b", "übst"),
    (r"\bueber\b", "über"),
    (r"\bpruefe(?:n)?\b", "prüfe/prüfen"),
    (r"\bErklaerung(?:en)?\b", "Erklärung/Erklärungen"),
    (r"\bErklaere\b", "Erkläre"),
    (r"\bBegruendung(?:en)?\b", "Begründung/Begründungen"),
    (r"\bWoerter\b", "Wörter"),
    (r"\bSaetze\b", "Sätze"),
    (r"\berfuellt\b", "erfüllt"),
]

COMMON_ASCII_UMLAUT_REPLACEMENTS = [
    (r"\bpruefung(?:en|s|stag|svorbereitung)?\b", "Prüfung/Prüfungsvorbereitung"),
    (r"\buebung(?:en)?\b", "Übung/Übungen"),
    (r"\bloesung(?:en)?\b", "Lösung/Lösungen"),
    (r"\berklaer(?:e|ung|ungen)?\b", "erkläre/Erklärung"),
]


@dataclass(frozen=True)
class QualityResult:
    ok: bool
    problems: list[str]
    score: float = 0.0


def check_interactive_page_quality(title: str, body_html: str, page_type: str) -> QualityResult:
    problems: list[str] = []
    text = re.sub(r"<[^>]+>", " ", body_html)
    words = re.findall(r"\b[\wÄÖÜäöüß-]+\b", text)
    if len(words) < 250:
        problems.append("interactive page body is too thin")
    if not re.search(r"<(button|input|select|textarea)\b", body_html, flags=re.I):
        problems.append("interactive page has no interactive controls")
    if not re.search(r"<(input|textarea)\b", body_html, flags=re.I):
        problems.append("learning asset must require active learner input")
    if not re.search(r"schema.org|application/ld\+json", body_html, flags=re.I):
        problems.append("schema markup is missing")
    if page_type not in {"practice_page", "mini_test", "worksheet", "calculator", "visualizer", "quiz", "exam_simulator", "learning_utility", "interactive_learning_page", "formula_practice", "grammar_drill", "flashcard_set"}:
        problems.append("unsupported page_type")
    if page_type in {"practice_page", "mini_test", "worksheet", "quiz", "exam_simulator", "formula_practice", "grammar_drill"}:
        if not re.search(r"Lösung|solution|Erklärung", body_html, flags=re.I):
            problems.append("practice asset must include clear solutions or explanations")
        if not re.search(r"leicht|mittel|schwer|difficulty|Schwierigkeit", body_html, flags=re.I):
            problems.append("practice asset must include difficulty progression or level metadata")
        if not re.search(r"data-subject|data-grade-level|data-asset-type", body_html, flags=re.I):
            problems.append("practice asset metadata is missing")
        if not re.search(r"answer_checked|checkAnswer|Antwort|Prüfen|Auswerten|feedback|Fehler|Hinweis|Wiederholung", body_html, flags=re.I):
            problems.append("practice asset must actively check learner work and provide feedback")
        if not re.search(r"Fehler|falsch|Noch nicht|Hinweis|Schritt|Erklärung|Wiederholung|erneut|noch einmal", body_html, flags=re.I):
            problems.append("practice asset must teach from mistakes, not just reveal an answer")
        if not re.search(r"Neue Aufgabe|Nächste|Wiederholung|Serie|Fortschritt|Treffer|Quote|Stapel|Fällig", body_html, flags=re.I):
            problems.append("practice asset must support repeated practice or progress tracking")
    haystack = f"{title} {text}".lower()
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, haystack):
            problems.append("spam-like wording detected")
    for pattern in LOW_VALUE_INTERACTION_PATTERNS:
        if re.search(pattern, body_html, flags=re.I):
            problems.append("low-value generic interaction pattern detected")
    visible_text = re.sub(r"<script\b.*?</script>", " ", body_html, flags=re.I | re.S)
    visible_text = re.sub(r"<style\b.*?</style>", " ", visible_text, flags=re.I | re.S)
    visible_text = re.sub(r"<[^>]+>", " ", visible_text)
    for pattern, preferred in [*UMLAUT_REPLACEMENT_SUSPECTS, *COMMON_ASCII_UMLAUT_REPLACEMENTS]:
        if re.search(pattern, visible_text, flags=re.I):
            problems.append(f"visible German text should use umlaut spelling, prefer {preferred}")
            break
    keyword_counts = {}
    for word in [w.lower() for w in words if len(w) > 5]:
        keyword_counts[word] = keyword_counts.get(word, 0) + 1
    if words and any(count / len(words) > 0.08 for count in keyword_counts.values()):
        problems.append("possible keyword stuffing")
    score = 1.0
    score -= 0.25 if len(words) < 250 else 0.0
    score -= 0.20 if not re.search(r"<(button|input|select|textarea)\b", body_html, flags=re.I) else 0.0
    score -= 0.15 if not re.search(r"schema.org|application/ld\+json", body_html, flags=re.I) else 0.0
    score -= min(0.5, 0.08 * len(problems))
    return QualityResult(not problems, problems, round(max(0.0, min(1.0, score)), 4))
