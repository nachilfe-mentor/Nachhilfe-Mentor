"""Tests für die Phonologische-Assimilation-Simulation (Draft/noindex).

Prüft Spec-first-Regel, HTML-Pflichtbestandteile (Canvas, Animation,
Vorhersage-Task, Zwei-Stufen-Progression, Feedback mit Fachbegriffen),
deutsche Umlaute, keine Escape-Artefakte und die QA-Notiz.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "phonologische-assimilation-deutsch-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "phonologische-assimilation-deutsch-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "phonologische-assimilation-deutsch-simulation-qa.md"


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
        "Nasalassimilation",
        "regressive",
        "labial",
        "velar",
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


def test_html_has_nasal_phoneme_options() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Die drei Phonem-Optionen müssen sichtbar sein
    assert "[m]" in visible, "[m] als Antwortoption fehlt im sichtbaren Text"
    assert "[n]" in visible, "[n] als Antwortoption fehlt im sichtbaren Text"
    # [ŋ] als Unicode-Zeichen (U+014B)
    assert "ŋ" in visible, "[ŋ] (velarer Nasal) fehlt im sichtbaren Text"


# ── Zwei-Stufen-Progression ────────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "stage1" in html, "stage1 fehlt"
    assert "stage2" in html, "stage2 fehlt"
    assert "Stufe 1" in html, "'Stufe 1' fehlt"
    assert "Stufe 2" in html, "'Stufe 2' fehlt"


def test_html_has_application_word_task() -> None:
    """Stufe 2: Wort-Karten mit syl-btn vorhanden."""
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "syl-btn" in html, "syl-btn Klasse (Stufe 2 Wort-Buttons) fehlt"
    assert "Wort 1" in visible or "word-card" in html, "Wort-Karten fehlen in Stufe 2"


# ── Feedback mit Fachbegriffen ─────────────────────────────────────────────────

def test_html_feedback_names_assimilation_types() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "labiale Nasalassimilation" in html, "Begriff 'labiale Nasalassimilation' fehlt"
    assert "velare Nasalassimilation" in html, "Begriff 'velare Nasalassimilation' fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_mentions_regressive() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "regressive" in visible or "Regressive" in visible, (
        "Begriff 'regressive Assimilation' fehlt im sichtbaren Text"
    )


def test_html_mentions_place_features() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "labial" in visible.lower(), "'labial' (Artikulationsort) fehlt"
    assert "velar"  in visible.lower(), "'velar' (Artikulationsort) fehlt"
    assert "alveolar" in visible.lower(), "'alveolar' (Artikulationsort) fehlt"


def test_html_mentions_source() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "Wiese" in html or "Hall" in html, "Quellenangabe (Wiese / Hall) fehlt"


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
    has_umlaut = any(c in visible for c in "äöüÄÖÜß")
    assert has_umlaut, "Keine deutschen Umlaute im sichtbaren Text"
    assert "Artikulationsort" in visible, "Schlüsselbegriff 'Artikulationsort' fehlt"


def test_html_no_umlaut_replacements() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "haeufig"   not in visible, "ASCII-Ersetzung 'haeufig' gefunden"
    assert "Pruefen"   not in visible, "ASCII-Ersetzung 'Pruefen' gefunden"
    assert "Ueberblick" not in visible, "ASCII-Ersetzung 'Ueberblick' gefunden"


def test_html_no_escape_artifacts() -> None:
    html    = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible,     "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible,     "Literal \\t im sichtbaren Text"
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
