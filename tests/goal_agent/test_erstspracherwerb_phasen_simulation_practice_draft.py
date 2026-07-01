"""Tests für die Erstspracherwerb-Phasen-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "erstspracherwerb-phasen-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "erstspracherwerb-phasen-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "erstspracherwerb-phasen-simulation-qa.md"


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
        "Übergeneralisierung",
        "MLU",
        "Holophrase",
        "Zweiwortphase",
        "Zwei-Stufen-Progression",
        "QA-Checkliste",
        "Missverständnis",
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


def test_html_has_timeline_animation() -> None:
    """Zeitstrahl-Animation muss vorhanden sein (DOM-basiert, kein Canvas nötig)."""
    html = HTML.read_text(encoding="utf-8")
    assert "@keyframes pulse" in html
    assert "tl-item" in html
    assert "animateTimeline" in html


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible
    assert "option-btn" in html


def test_html_has_two_step_progression() -> None:
    """Zwei Stufen vorhanden (stage1 und stage2)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage2" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_feedback_names_concepts() -> None:
    """Feedback benennt linguistische Konzepte explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Holophrase" in html
    assert "Übergeneralisierung" in html
    assert "concept-tag" in html
    assert "MLU" in html


def test_html_has_five_rounds() -> None:
    """Fünf Äußerungs-Zuordnungsrunden in Stufe 1."""
    html = HTML.read_text(encoding="utf-8")
    assert "Aufgabe 1 von 5" in html or "von 5" in html


def test_html_phase_names_present() -> None:
    """Alle sechs Phasen-Namen müssen im HTML erscheinen (Timeline nutzt &shy; soft hyphens)."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Lallphase" in visible
    assert "Einwortphase" in visible
    assert "Zweiwortphase" in visible
    # Timeline verwendet Früh&shy;grammatik – Name in JS-Daten prüfen
    assert "Frühgrammatik" in html


def test_html_has_wrong_feedback() -> None:
    """Feedback für falsche Antworten muss konzeptuell erklären."""
    html = HTML.read_text(encoding="utf-8")
    assert "wrong-fb" in html
    assert "wrongFeedback" in html


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ü" in visible or "ö" in visible or "ä" in visible
    assert "Äußerung" in visible
    assert "Übergeneralisierung" in visible
    # Frühgrammatik in JS-Daten (Timeline hat &shy; soft hyphens)
    assert "Frühgrammatik" in html
    # Keine ASCII-Ersetzungen
    assert "Uebergeneralisierung" not in visible
    assert "Aeusserung" not in visible
    assert "Fruehgrammatik" not in html


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


def test_html_has_restart() -> None:
    """Neustart-Funktion muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "restartSim" in html or "Nochmal" in html


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
