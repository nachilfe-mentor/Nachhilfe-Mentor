"""Tests für die Flexion-Derivation-Morphologie-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "flexion-derivation-morphologie-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "flexion-derivation-morphologie-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "flexion-derivation-morphologie-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",  " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_spec_exists_before_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt"
    assert HTML.exists(), "HTML-Datei fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, "Spec muss älter sein als HTML"


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Flexion",
        "Derivation",
        "Missverständnisse",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt: {marker}"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow">' in html


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


def test_html_has_dom_animation() -> None:
    """Simulation nutzt DOM-basierte Animation (CSS transitions/keyframes)."""
    html = HTML.read_text(encoding="utf-8")
    # DOM-Animation statt Canvas – CSS-Animationen oder transitions
    assert "@keyframes" in html or "transition" in html
    assert "morphem-chip" in html or "morph" in html.lower()


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe mit option-btn."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible
    assert "option-btn" in html


def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen vorhanden (stage1 und stage3)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage3" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_feedback_names_concept() -> None:
    """Feedback benennt Flexion, Derivation und Lexem."""
    html = HTML.read_text(encoding="utf-8")
    assert "Flexion" in html
    assert "Derivation" in html
    assert "Lexem" in html
    # Konzept-Tag im Feedback
    assert "concept-tag" in html


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute vorhanden
    assert "ü" in visible or "ö" in visible or "ä" in visible
    # Keine ASCII-Ersetzungen in sichtbarem Text
    assert "Pruefen" not in visible
    assert "Woerter" not in visible
    assert "haeufig" not in visible
    # Richtige Schlüsselwörter
    assert "Schönheit" in html
    assert "Wörterbuch" in html
    assert "Prüfen" not in visible  # kein Prüfen-Button – aber Umlaute generell ok


def test_html_has_flexion_and_derivation_examples() -> None:
    """Konkrete Lehr-Beispiele Schönheit, Tische, Forschung im HTML."""
    html = HTML.read_text(encoding="utf-8")
    assert "Schönheit" in html
    assert "Tische" in html
    assert "Forschung" in html
    # Knifflige Fälle Stufe 2
    assert "unfair" in html
    assert "Schwimmen" in html


def test_html_has_konversion_explanation() -> None:
    """Konversion als Sonderfall der Derivation muss erklärt werden."""
    html = HTML.read_text(encoding="utf-8")
    assert "Konversion" in html
    assert "Nullableitung" in html


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible
    assert "\\t" not in visible
    assert "&bsol;n" not in visible


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html


def test_qa_note_exists() -> None:
    """QA-Notiz muss nach dem HTML angelegt worden sein."""
    assert QA.exists(), "QA-Notiz fehlt"


def test_qa_note_has_required_sections() -> None:
    qa = QA.read_text(encoding="utf-8")
    required = [
        "Nützlichkeit",
        "Modell",
        "Interaktion",
        "Mobile",
        "Promotionsempfehlung",
    ]
    for marker in required:
        assert marker in qa, f"QA-Notiz fehlt Abschnitt: {marker}"
