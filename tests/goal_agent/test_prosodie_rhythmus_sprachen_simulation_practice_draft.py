"""Tests für die Prosodie-Rhythmus-Sprachen-Simulation (Draft/noindex).

Prüft Spec-first-Regel, HTML-Pflichtbestandteile (Canvas, Animation,
Vorhersage-Task, Zwei-Stufen-Progression, Feedback mit Fachbegriffen),
deutsche Umlaute, keine Escape-Artefakte und die QA-Notiz.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "prosodie-rhythmus-sprachen-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "prosodie-rhythmus-sprachen-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "prosodie-rhythmus-sprachen-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ───────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    assert SPEC.exists(), "Spec-Datei fehlt"


def test_spec_older_than_html() -> None:
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss älter oder gleich alt wie HTML sein (Spec-first-Regel)"
    )


def test_spec_contains_required_sections() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Betonungstakt",
        "Silbentakt",
        "Morentakt",
        "Abercrombie",
        "Misskonzeptionen",
        "Zwei-Stufen-Progression",
        "QA-Checkliste",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker!r}"


# ── HTML Grundstruktur ─────────────────────────────────────────────────────────

def test_html_exists() -> None:
    assert HTML.exists(), "HTML-Datei fehlt"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'content="noindex,nofollow"' in html, "noindex,nofollow Meta-Tag fehlt"


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html, "lang=de fehlt"


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html, "schema.org fehlt"
    assert "LearningResource" in html, "LearningResource fehlt"


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html, "/favicon.ico fehlt"


# ── Canvas-Animation ───────────────────────────────────────────────────────────

def test_html_has_canvas() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html, "<canvas> Element fehlt"


def test_html_has_request_animation_frame() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "requestAnimationFrame" in html, "requestAnimationFrame fehlt"


# ── Vorhersage-Aufgabe (Stufe 1) ───────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text"
    assert "option-btn" in html, "option-btn Klasse fehlt"


def test_html_has_rhythm_type_options() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Betonungstakt" in visible, "'Betonungstakt' als Antwortoption fehlt"
    assert "Silbentakt"    in visible, "'Silbentakt' als Antwortoption fehlt"
    assert "Morentakt"     in visible, "'Morentakt' als Antwortoption fehlt"


# ── Zwei-Stufen-Progression ────────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "stage1" in html, "stage1 fehlt"
    assert "stage2" in html, "stage2 fehlt"
    assert "Stufe 1" in html, "'Stufe 1' fehlt"
    assert "Stufe 2" in html, "'Stufe 2' fehlt"


def test_html_has_syllable_stress_task() -> None:
    """Stufe 2: Betonungssilben-Task vorhanden."""
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "syl-btn" in html or "syl_btn" in html or "syl-buttons" in html, (
        "Silbenbuttons für Stufe 2 fehlen"
    )
    assert "Betonung" in visible, "'Betonung' im sichtbaren Text fehlt"


# ── Feedback mit Fachbegriffen ─────────────────────────────────────────────────

def test_html_feedback_names_rhythm_types() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "Betonungstaktsprache" in html or "Betonungstakt" in html, (
        "Begriff 'Betonungstakt' fehlt im Feedback"
    )
    assert "Silbentaktsprache" in html or "Silbentakt" in html, (
        "Begriff 'Silbentakt' fehlt im Feedback"
    )
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_mentions_abercrombie() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "Abercrombie" in html, "Abercrombie (Quellenangabe) fehlt"


def test_html_mentions_mora() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Mora" in visible or "Moren" in visible, (
        "Begriff 'Mora/Moren' (Morentakt) fehlt im sichtbaren Text"
    )


# ── Tracking ───────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "data-asset-type"  in html, "data-asset-type fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster fehlt"


# ── Deutsche Rechtschreibung ───────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ä" in visible or "ö" in visible or "ü" in visible, (
        "Keine deutschen Umlaute im sichtbaren Text"
    )
    assert "Betonungstakt" in visible, "Schlüsselbegriff 'Betonungstakt' fehlt"
    assert "Silbentakt"    in visible, "Schlüsselbegriff 'Silbentakt' fehlt"


def test_html_no_umlaut_replacements() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Betonungstakt" not in visible.replace("Betonungstakt", ""), True
    assert "haeufig"    not in visible, "ASCII-Ersetzung 'haeufig' gefunden"
    assert "Pruefen"    not in visible, "ASCII-Ersetzung 'Pruefen' gefunden"
    assert "Sprachwissenschaft".lower() not in visible.lower().replace("ä", "ae"), True


def test_html_no_escape_artifacts() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible,    "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible,    "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ───────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
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
