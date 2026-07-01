"""Tests für die Tonsprachen-Simulation: Lexikalischer Ton (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "tonsprachen-lexikalischer-ton-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "tonsprachen-lexikalischer-ton-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "tonsprachen-lexikalischer-ton-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",  " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_spec_exists_before_html() -> None:
    """Spec-Datei muss existieren und älter als HTML sein."""
    assert SPEC.exists(), "Spec-Datei fehlt"
    assert HTML.exists(), "HTML-Datei fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, "Spec muss älter sein als HTML"


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "lexikalischer Ton",
        "Chao",
        "Missverständnis",
        "Zwei-Stufen-Progression",
        "QA-Checkliste",
        "Mandarin",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker!r}"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow">' in html


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


def test_html_has_canvas_animation() -> None:
    """Simulation enthält Canvas und requestAnimationFrame-Animation."""
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html
    assert "requestAnimationFrame" in html


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Kein sichtbarer Vorhersage-Text"
    assert "option-btn" in html, "Keine Option-Buttons gefunden"


def test_html_has_two_step_progression() -> None:
    """Zwei-Stufen-Progression: stage1 und stage2 müssen vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html
    assert "stage2" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_feedback_names_lexikalischer_ton() -> None:
    """Feedback benennt explizit den Begriff 'lexikalischer Ton'."""
    html = HTML.read_text(encoding="utf-8")
    assert "lexikalischer Ton" in html
    assert "concept-tag" in html


def test_html_has_chao_numbers() -> None:
    """Die Chao-Tonenummerierung (55, 35, 214, 51) muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "55" in html
    assert "35" in html
    assert "214" in html
    assert "51" in html


def test_html_names_mandarin_tones() -> None:
    """Alle vier Mandarin-Beispielwörter (mā, má, mǎ, mà) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "mā" in html or "mā" in html
    assert "Mutter" in html
    assert "Pferd" in html
    assert "schimpfen" in html or "schelten" in html


def test_html_addresses_misconception() -> None:
    """Die Simulation adressiert das Missverständnis Ton vs. Intonation."""
    html = HTML.read_text(encoding="utf-8")
    assert "Intonation" in html
    assert "Missverständnis" in html or "Ton ≠ Intonation" in html


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
    assert "Woerter" not in visible
    assert "Toene" not in visible
    # Korrekte Begriffe
    assert "Bedeutung" in visible
    assert "Tonsprachen" in visible or "Tonsprache" in visible


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


def test_html_names_chao_source() -> None:
    """Die Simulation benennt das Chao-Tonsystem als Quelle."""
    html = HTML.read_text(encoding="utf-8")
    assert "Chao" in html
    # Chao (1930) oder ähnlich muss irgendwo erscheinen
    assert "1930" in html


def test_html_global_tone_statistics() -> None:
    """Die globale Verbreitung von Tonsprachen (~70 %) muss erwähnt sein."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "70" in visible


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
        assert marker in qa, f"QA-Notiz fehlt Abschnitt: {marker!r}"
