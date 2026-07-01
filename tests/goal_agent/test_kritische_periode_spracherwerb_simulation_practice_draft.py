"""Tests für die Kritische-Periode-Spracherwerb-Simulation (Draft/noindex).

Task ID: coding_task_0c0b91f639e8e668
Thema: sprachen / Sensitive Periode im Spracherwerb (AoA-Modell)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "kritische-periode-spracherwerb-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "kritische-periode-spracherwerb-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "kritische-periode-spracherwerb-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",  " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ─── Schritt 1: Spec-Existenz ────────────────────────────────────────────────

def test_spec_exists_before_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt"
    assert HTML.exists(), "HTML-Datei fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, "Spec muss älter oder gleich alt wie HTML sein"


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte laut LEARNING_ASSET_PATTERNS."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Sensitive Periode",
        "Missverständnisse",
        "Zwei-Stufen-Progression",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker!r}"


# ─── Schritt 2: HTML-Grundanforderungen ──────────────────────────────────────

def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow">' in html


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


# ─── Schritt 3: Canvas-Animation ─────────────────────────────────────────────

def test_html_has_canvas_animation() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html, "Canvas-Element fehlt"
    assert "requestAnimationFrame" in html, "Animation (requestAnimationFrame) fehlt"


def test_html_has_two_canvases() -> None:
    """Stufe 1 und Stufe 2 haben je ein eigenes Canvas."""
    html = HTML.read_text(encoding="utf-8")
    assert "canvas-1" in html
    assert "canvas-2" in html


# ─── Schritt 4: Interaktion und Vorhersage-Aufgabe ───────────────────────────

def test_html_has_option_buttons() -> None:
    """Auswahlbuttons (opt-btn) für beide Stufen vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "opt-btn" in html


def test_html_stage1_has_luisa_jonas() -> None:
    """Stufe 1 fragt nach Luisa vs. Jonas – die Schlüsselpersonen der AoA-Vorhersage."""
    visible = _visible(HTML.read_text(encoding="utf-8"))
    assert "Luisa" in visible, "Luisa (AoA 5) fehlt in Stufe 1"
    assert "Jonas" in visible, "Jonas (AoA 14) fehlt in Stufe 1"


def test_html_stage2_has_emma() -> None:
    """Stufe 2 fragt nach Emma (AoA 20) – Grammatik vs. Aussprache."""
    visible = _visible(HTML.read_text(encoding="utf-8"))
    assert "Emma" in visible


# ─── Schritt 5: 2-Stufen-Progression ─────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "stage-1" in html, "Stufe-1-Element (id=stage-1) fehlt"
    assert "stage-2" in html, "Stufe-2-Element (id=stage-2) fehlt"
    visible = _visible(html)
    assert "Stufe 1" in visible
    assert "Stufe 2" in visible


# ─── Schritt 6: Feedback benennt Konzept ─────────────────────────────────────

def test_html_feedback_names_concept() -> None:
    """Feedback muss die Sensitive Periode und das AoA-Konzept benennen."""
    html = HTML.read_text(encoding="utf-8")
    assert "Sensitive Periode" in html or "Sensitiven Periode" in html
    assert "AoA" in html or "Age of Acquisition" in html
    assert "Grammatik" in html
    assert "Aussprache" in html


def test_html_feedback_names_research() -> None:
    """Quellenangabe in der Simulation vorhanden (Johnson & Newport oder Flege)."""
    html = HTML.read_text(encoding="utf-8")
    assert "Johnson" in html or "Newport" in html
    assert "Flege" in html


# ─── Schritt 7: Tracking ─────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html


# ─── Schritt 8: Deutsche Umlaute korrekt ─────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute müssen vorhanden sein
    assert "ü" in visible or "ö" in visible or "ä" in visible, "Keine deutschen Umlaute gefunden"
    # Keine ASCII-Ersetzungen
    assert "Aussprache" in visible, "Kernbegriff 'Aussprache' fehlt"
    assert "Akzentfrei" in visible or "akzentfrei" in visible or "Akzent" in visible
    assert "Grammatik" in visible
    assert "Spracherwerb" in visible


def test_html_no_ascii_umlaut_replacements() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Spracherwerb" in visible
    # Keine ASCII-Ersetzungen im sichtbaren Text
    assert "Pruefen" not in visible
    assert "Ueberarbeitung" not in visible


# ─── Schritt 9: Keine Escape-Artefakte ───────────────────────────────────────

def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text gefunden"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text gefunden"
    assert "&bsol;n" not in visible


# ─── Schritt 10: Faktisches Modell ───────────────────────────────────────────

def test_html_model_functions_present() -> None:
    """Die mathematischen Modellfunktionen (pronScore, gramScore) sind im Script vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "pronScore" in html, "Aussprache-Scoring-Funktion pronScore fehlt"
    assert "gramScore" in html, "Grammatik-Scoring-Funktion gramScore fehlt"


def test_html_seeded_rng() -> None:
    """Deterministischer Seed-RNG vorhanden – reproduzierbare Animation."""
    html = HTML.read_text(encoding="utf-8")
    # LCG-Seed oder ähnliches Muster
    assert "mkRng" in html or "seed" in html.lower()


# ─── Schritt 11: QA-Notiz ────────────────────────────────────────────────────

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


# ─── Schritt 12: Kein horizontaler Scroll bei 375 px (CSS-Check) ─────────────

def test_html_mobile_responsive() -> None:
    """Media-Query für schmale Bildschirme und max-width auf canvas vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "max-width: 900px" in html or "max-width:900px" in html, (
        "Media-Query für mobile Darstellung fehlt"
    )
    # Canvas sollte responsive sein
    assert "width: 100%" in html or "width:100%" in html, (
        "Canvas ist nicht fluid (width: 100% fehlt)"
    )
