"""Tests für die Aktionsarten-Simulation (Vendler-Klassifikation) – Draft/noindex."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "aktionsarten-lexikalischer-aspekt-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "aktionsarten-lexikalischer-aspekt-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "aktionsarten-lexikalischer-aspekt-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    assert SPEC.exists(), "Spec-Datei fehlt"


def test_spec_older_than_html() -> None:
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, "Spec muss älter sein als HTML"


def test_spec_contains_required_sections() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Vendler",
        "Telizität",
        "Missverständnis",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt: {marker!r}"


# ── HTML Grundstruktur ─────────────────────────────────────────────────────────

def test_html_exists() -> None:
    assert HTML.exists(), "HTML-Datei fehlt"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'content="noindex,nofollow"' in html, "noindex-Meta-Tag fehlt"


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html, "lang=de fehlt"


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html


# ── Canvas-Animation ──────────────────────────────────────────────────────────

def test_html_has_canvas_animation() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html, "Canvas-Element fehlt"
    assert "requestAnimationFrame" in html, "requestAnimationFrame fehlt – keine Animation"


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe fehlt"
    assert "option-btn" in html, "Auswahlknöpfe (option-btn) fehlen"


def test_html_has_two_step_progression() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe ──────────────────────────────────────────────────────────────

def test_html_names_all_four_aktionsarten() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "Zustand" in html,        "Begriff 'Zustand' fehlt"
    assert "Aktivität" in html,      "Begriff 'Aktivität' fehlt"
    assert "Accomplishment" in html, "Begriff 'Accomplishment' fehlt"
    assert "Achievement" in html,    "Begriff 'Achievement' fehlt"


def test_html_feedback_names_concepts() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "concept-tag" in html,   "concept-tag im Feedback fehlt"
    assert "Telizität" in html or "telisch" in html, "Telizitätsbegriff fehlt"
    assert "Progressiv" in html,    "Progressiv-Test fehlt"
    assert "atelisch" in html,      "Begriff 'atelisch' fehlt"


def test_html_addresses_misconception() -> None:
    html = HTML.read_text(encoding="utf-8")
    # Simulation muss das Missverständnis mental=Zustand adressieren
    assert any(phrase in html for phrase in [
        "Denken", "mental", "Nachdenken", "kognitiv",
    ]), "Missverständnis (mental ≠ Zustand) nicht adressiert"


# ── Tracking ──────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "data-asset-type" in html,  "data-asset-type fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster fehlt"


# ── Deutsche Rechtschreibung ──────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ä" in visible or "ö" in visible or "ü" in visible, "Keine deutschen Umlaute gefunden"
    # Prüfe, dass echte Umlaute vorhanden sind (keine ASCII-Ersetzungen)
    assert "Prüfen" in visible or "Übung" in visible or "Vorhersage" in visible
    # Verbotene ASCII-Ersetzungen in sichtbarem Text
    forbidden = ["Vorhersaege", "Pruefen", "Uebung", "Zustaende", "Aktivitaet"]
    for bad in forbidden:
        assert bad not in visible, f"ASCII-Umlaut-Ersetzung '{bad}' gefunden"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible,     "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible,     "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

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
