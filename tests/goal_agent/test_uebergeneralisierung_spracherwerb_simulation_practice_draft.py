"""Tests für die Übergeneralisierung-Spracherwerb-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "uebergeneralisierung-spracherwerb-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "uebergeneralisierung-spracherwerb-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "uebergeneralisierung-spracherwerb-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",  " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_spec_exists_before_html() -> None:
    """Spec-Datei muss vor der HTML-Datei angelegt worden sein."""
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
        "Übergeneralisierung",
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
    """Simulation hat eine DOM-basierte oder CSS-Animation."""
    html = HTML.read_text(encoding="utf-8")
    has_css_animation   = "@keyframes" in html
    has_css_transition  = "transition" in html
    has_raf             = "requestAnimationFrame" in html
    has_canvas          = "<canvas" in html
    assert has_css_animation or has_css_transition or has_raf or has_canvas, \
        "Keine animierte Visualisierung gefunden (kein @keyframes, transition, requestAnimationFrame oder canvas)"


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Kein 'Vorhersage'-Element im sichtbaren Text"
    assert "choice-btn" in html or "option-btn" in html or "stage-opt" in html, \
        "Keine Auswahl-Buttons für Interaktion gefunden"


def test_html_has_two_step_progression() -> None:
    """Mindestens drei Stufen vorhanden (stage1, stage2 und stage3)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "stage1 fehlt"
    assert "stage2" in html, "stage2 fehlt"
    assert "stage3" in html, "stage3 fehlt"
    visible = _visible(html)
    assert "Stufe 1" in visible, "'Stufe 1' fehlt im sichtbaren Text"
    assert "Stufe 2" in visible, "'Stufe 2' fehlt im sichtbaren Text"


def test_html_feedback_names_concept() -> None:
    """Feedback benennt die Konzepte Übergeneralisierung, Regelbildung und Behaviorismus."""
    html = HTML.read_text(encoding="utf-8")
    assert "Übergeneralisierung" in html, "'Übergeneralisierung' fehlt"
    assert "Regelbildung" in html, "'Regelbildung' fehlt"
    assert "Behaviorismus" in html, "'Behaviorismus' fehlt"
    assert "concept-tag" in html, "concept-tag-Klasse fehlt"


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute müssen vorhanden sein
    assert "ü" in visible or "ö" in visible or "ä" in visible
    # Schlüsselbegriffe mit Umlauten
    assert "Übergeneralisierung" in visible
    assert "Regelbildung" in visible
    # Keine ASCII-Umlaut-Ersetzungen im sichtbaren Text
    assert "Uebergeneralisierung" not in visible
    assert "Regelbildnung" not in visible


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


def test_html_has_u_curve_svg() -> None:
    """Die U-Kurven-Visualisierung ist als SVG vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "<svg" in html, "SVG-Diagramm fehlt"
    assert "stroke-dashoffset" in html, "SVG-Animation (stroke-dashoffset) fehlt"


def test_html_has_speech_bubbles() -> None:
    """Mindestens drei Sprechblasen mit Kindäußerungen vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ging" in visible, "Kindäußerung 'ging' fehlt"
    assert "gingte" in visible or "gehte" in visible, "Übergeneralisierte Form fehlt"
    assert "speech-bubble" in html, "speech-bubble-Element fehlt"


def test_qa_note_exists() -> None:
    """QA-Notiz muss vorhanden sein."""
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
