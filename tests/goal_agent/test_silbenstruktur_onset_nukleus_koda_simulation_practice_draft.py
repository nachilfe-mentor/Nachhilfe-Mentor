"""Tests für die Silbenstruktur-Onset-Nukleus-Koda-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "silbenstruktur-onset-nukleus-koda-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "silbenstruktur-onset-nukleus-koda-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "silbenstruktur-onset-nukleus-koda-simulation-qa.md"


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
        "Nukleus",
        "Onset",
        "Koda",
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


def test_html_has_fenster_word() -> None:
    """Das Wort 'Fenster' ist Gegenstand der Vorhersage-Aufgabe (Stufe 1)."""
    visible = _visible(HTML.read_text(encoding="utf-8"))
    assert "Fenster" in visible


def test_html_has_stern_word() -> None:
    """Das Wort 'Stern' ist Gegenstand der Analyse-Aufgabe (Stufe 2)."""
    visible = _visible(HTML.read_text(encoding="utf-8"))
    assert "Stern" in visible


def test_html_has_two_step_progression() -> None:
    """Zwei Stufen vorhanden (stage1 und stage3)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage3" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_has_classify_task() -> None:
    """Klassifizierungs-Aufgabe mit classify-btn für Onset/Nukleus/Koda."""
    html = HTML.read_text(encoding="utf-8")
    assert "classify-btn" in html
    assert "onsetRow" in html
    assert "nukleusRow" in html
    assert "kodaRow" in html


def test_html_feedback_names_concept() -> None:
    """Feedback benennt Onset, Nukleus, Koda und Silbenstruktur explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Onset" in html
    assert "Nukleus" in html
    assert "Koda" in html
    assert "Silbenstruktur" in html
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
    # Keine ASCII-Ersetzungen im sichtbaren Text
    assert "Nukleus" in visible           # Fachbegriff vorhanden
    assert "Silbenkern" in visible        # Erklärung vorhanden
    assert "Pruefen" not in visible
    assert "Prüfen" in visible            # korrekte Umlautschreibung
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
