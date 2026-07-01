"""Tests für die Konzeptuelle-Metapher-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "konzeptuelle-metapher-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "konzeptuelle-metapher-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "konzeptuelle-metapher-simulation-qa.md"


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
        "Lakoff",
        "Johnson",
        "Quellbereich",
        "Zielbereich",
        "Mapping",
        "Highlighting",
        "Hiding",
        "ARGUMENTATION IST KRIEG",
        "ZEIT IST GELD",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker}"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow">' in html


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


def test_html_has_animated_visual_model() -> None:
    """Visuelles Modell: animiertes Mapping-Diagramm (DOM-basiert)."""
    html = HTML.read_text(encoding="utf-8")
    # DOM-basiertes Diagramm mit Transitions
    assert "mapping-diagram" in html
    assert "transition" in html


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible
    assert "option-btn" in html


def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage3" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_feedback_names_concept() -> None:
    """Feedback benennt konzeptuelle Metapher, Highlighting und Hiding."""
    html = HTML.read_text(encoding="utf-8")
    assert "ARGUMENTATION IST KRIEG" in html
    assert "Highlighting" in html
    assert "Hiding" in html
    assert "concept-tag" in html


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ü" in visible or "ö" in visible or "ä" in visible
    # Keine ASCII-Ersetzungen
    assert "Quellbereich" in visible
    assert "Zielbereich" in visible
    assert "Überzeugen" in visible or "berzeugen" in html
    assert "Worterbuche" not in visible
    assert "Woerter" not in visible


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
    """QA-Notiz muss existieren."""
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
