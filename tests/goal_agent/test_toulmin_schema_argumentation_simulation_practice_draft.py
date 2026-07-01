"""Tests für die Toulmin-Schema-Argumentationsanalyse-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "toulmin-schema-argumentation-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "toulmin-schema-argumentation-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "toulmin-schema-argumentation-simulation-qa.md"


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
        "Schlussregel",
        "Missverständnisse",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
        "Datum",
        "These",
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
    """Mindestens eine Vorhersage-Aufgabe mit option-btn vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Kein 'Vorhersage'-Text im sichtbaren Inhalt"
    assert "option-btn" in html, "Keine option-btn Buttons"


def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen vorhanden (stage1, stage2, stage3)."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "stage1" in html
    assert "stage2" in html
    assert "stage3" in html
    assert "Stufe 1" in visible, "'Stufe 1' fehlt im sichtbaren Text"
    assert "Stufe 2" in visible, "'Stufe 2' fehlt im sichtbaren Text"


def test_html_feedback_names_toulmin_elements() -> None:
    """Feedback benennt konkrete Toulmin-Elemente als concept-tag."""
    html = HTML.read_text(encoding="utf-8")
    assert "concept-tag" in html
    assert "Schlussregel" in html
    assert "Datum" in html
    assert "These" in html
    assert "Stützung" in html
    assert "Modaloperator" in html
    assert "Ausnahme" in html


def test_html_has_toulmin_term() -> None:
    """Der Name 'Toulmin' muss im sichtbaren Text erscheinen."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Toulmin" in visible


def test_html_addresses_datum_vs_schlussregel_misconception() -> None:
    """Das Misskonzept Datum ≠ Schlussregel muss explizit adressiert werden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Beide Begriffe müssen vorkommen und der Unterschied erklärt werden
    assert "Datum" in visible
    assert "Schlussregel" in visible
    # Mindestens ein Hinweis auf "implizit" (Schlussregel oft implizit)
    assert "implizit" in visible.lower() or "implizit" in html.lower()


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute vorhanden
    assert any(c in visible for c in "äöüÄÖÜß"), "Keine korrekten Umlaute im sichtbaren Text"
    # Keine ASCII-Ersetzungen der Kernbegriffe
    assert "Stuetzung" not in visible, "ASCII-Umlaut-Ersetzung 'Stuetzung' gefunden"
    assert "Schlussregel" in visible  # muss korrekt sein
    # Korrekt: Stützung mit ü
    assert "Stützung" in visible


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Sichtbares '\\n' gefunden"
    assert "\\t" not in visible, "Sichtbares '\\t' gefunden"
    assert "&bsol;n" not in visible, "Sichtbares '&bsol;n' gefunden"


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html


def test_html_has_klimaschutz_example() -> None:
    """Das Klimaschutz-Beispiel in Stufe 2 muss enthalten sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "CO" in html  # CO₂
    assert "Klimaerwärmung" in html or "Klimarw" in html or "Klima" in html
    assert "IPCC" in html


def test_html_has_stage4_result() -> None:
    """Ergebnisseite (stage4) muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage4" in html
    visible = _visible(html)
    assert "Lösungsübersicht" in visible or "Ergebnis" in visible


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
