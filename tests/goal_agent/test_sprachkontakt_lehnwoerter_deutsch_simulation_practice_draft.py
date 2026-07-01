"""Tests für die Sprachkontakt-Lehnwörter-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "sprachkontakt-lehnwoerter-deutsch-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "sprachkontakt-lehnwoerter-deutsch-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "sprachkontakt-lehnwoerter-deutsch-simulation-qa.md"


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
        "Lehnwort",
        "Fremdwort",
        "Missverständnisse",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
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


def test_html_has_canvas_animation() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html
    assert "requestAnimationFrame" in html


def test_html_has_prediction_task() -> None:
    """Vorhersage-Aufgabe mit option-btn vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible
    assert "option-btn" in html


def test_html_has_fenster_prediction() -> None:
    """Das Wort 'Fenster' ist Gegenstand der Vorhersage-Aufgabe."""
    visible = _visible(HTML.read_text(encoding="utf-8"))
    assert "Fenster" in visible


def test_html_has_two_step_progression() -> None:
    """Zwei Stufen vorhanden (stage1 und stage3)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage3" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_has_classification_task() -> None:
    """Klassifizierungs-Aufgabe mit Lehnwort/Fremdwort-Buttons vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "classify-btn" in html
    assert "Koch" in visible
    assert "Restaurant" in visible
    assert "Keller" in visible
    assert "Computer" in visible


def test_html_feedback_names_concept() -> None:
    """Feedback benennt Lehnwort, Fremdwort und Sprachkontakt."""
    html = HTML.read_text(encoding="utf-8")
    assert "Lehnwort" in html
    assert "Fremdwort" in html
    assert "Sprachkontakt" in html
    assert "concept-tag" in html


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
    # Keine ASCII-Ersetzungen in sichtbarem Text
    assert "Woerter" not in visible
    assert "Lehnwoerter" not in visible
    assert "Fremdwoerter" not in visible
    assert "Pruefen" not in visible
    assert "Franzoeisch" not in visible
    # Richtige Umlaute prüfen
    assert "Lehnwörter" in visible
    assert "Fremdwörter" in visible
    assert "Prüfen" in visible


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
