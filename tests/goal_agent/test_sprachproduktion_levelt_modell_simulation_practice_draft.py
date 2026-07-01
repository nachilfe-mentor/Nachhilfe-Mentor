"""Tests für die Sprachproduktion-nach-Levelt-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "sprachproduktion-levelt-modell-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "sprachproduktion-levelt-modell-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "sprachproduktion-levelt-modell-simulation-qa.md"


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
        "Asset-Typ",
        "Levelt",
        "Konzeptualisierung",
        "Formulierung",
        "Artikulation",
        "Missverständnisse",
        "Zwei-Stufen-Progression",
        "QA-Checkliste",
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


def test_html_has_canvas_animation() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html
    assert "requestAnimationFrame" in html


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe muss vorhanden sein."""
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
    """Feedback benennt Levelt-Konzepte explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Levelt" in html
    assert "Formulierung" in html
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
    assert "Formulierung" in visible          # Schlüsselwort korrekt
    assert "äußere" in visible               # Umlaut korrekt (äußere Rückkopplung)
    assert "Aussprache" in visible            # Grundwortschatz
    assert "Woerter" not in visible
    assert "Aeusserung" not in visible


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


def test_html_levelt_model_stages_present() -> None:
    """Alle vier Levelt-Stufen müssen im sichtbaren Text vorkommen."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Konzeptualisierung" in visible
    assert "Formulierung" in visible
    assert "Artikulation" in visible
    assert "Monitor" in visible


def test_html_has_feedback_for_wrong_answer() -> None:
    """Feedback für falsche Antworten muss konzeptuell erklären, nicht nur 'falsch' sagen."""
    html = HTML.read_text(encoding="utf-8")
    # wrong-fb class must exist
    assert "wrong-fb" in html
    # The feedback texts must mention the correct stage
    assert "Formulierung" in html


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
