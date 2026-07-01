"""Tests für die Prototypentheorie-Simulation (Draft/noindex).

Prüft: Spec-First-Regel, Grundstruktur, Canvas-Animation, Vorhersage-Aufgabe,
Zwei-Stufen-Progression, fachspezifisches Feedback, Tracking, Rechtschreibung.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "prototypentheorie-kognitive-semantik-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "prototypentheorie-kognitive-semantik-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "prototypentheorie-kognitive-semantik-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: prototypentheorie-kognitive-semantik-simulation-spec.md"


def test_spec_older_than_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein."""
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss älter sein als HTML (Spec-first-Regel)"
    )


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Prototypentheorie",
        "Rosch",
        "Vogel",
        "Möbel",
        "Typikalität",
        "Familienähnlichkeit",
        "Missverständnis",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker!r}"


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
    """Vorhersage-Aufgabe muss im sichtbaren Text vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text"
    # Mindestens eine der Vogel-Optionen im HTML (als choice-btn)
    assert "Rotkehlchen" in html, "Rotkehlchen als Option fehlt"
    assert "Pinguin" in html, "Pinguin als Option fehlt"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ──────────────────────────────────────────────────

def test_html_feedback_names_prototypeneffekt() -> None:
    """Feedback benennt Prototypeneffekt und Rosch explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Prototypeneffekt" in html, "Begriff 'Prototypeneffekt' fehlt"
    assert "Rosch" in html, "Verweis auf Rosch fehlt"


def test_html_feedback_names_gradierte_mitgliedschaft() -> None:
    """Feedback benennt gradierte Kategorienmitgliedschaft."""
    html = HTML.read_text(encoding="utf-8")
    assert "gradierte" in html or "Gradiert" in html, (
        "Begriff 'gradierte Kategorienmitgliedschaft' fehlt"
    )


def test_html_addresses_misconception() -> None:
    """Simulation adressiert Missverständnis klassische vs. Prototypentheorie."""
    html = HTML.read_text(encoding="utf-8")
    has_classical = any(phrase in html for phrase in [
        "klassisch",
        "aristotelisch",
        "Aristoteles",
        "binär",
        "Binär",
        "notwendige",
    ])
    assert has_classical, (
        "Missverständnis 'klassische Kategorientheorie' nicht adressiert"
    )


def test_html_has_moebelranking() -> None:
    """Möbel-Ranking (Stufe 2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "Stuhl" in html, "Möbel-Item 'Stuhl' fehlt"
    assert "Sofa" in html, "Möbel-Item 'Sofa' fehlt"
    assert "Lampe" in html, "Möbel-Item 'Lampe' fehlt"


# ── Tracking ──────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "data-asset-type" in html, "data-asset-type fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster fehlt"


# ── Deutsche Rechtschreibung ──────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute vorhanden
    assert "ä" in visible or "ö" in visible or "ü" in visible, (
        "Keine deutschen Umlaute im sichtbaren Text gefunden"
    )
    # ASCII-Umlaut-Ersetzungen dürfen nicht im sichtbaren Text vorkommen
    forbidden = ["Voegl", "Moebelst", "Familienaehnlichkeit", "Prototypentheorie".replace("o", "oe")]
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
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: prototypentheorie-kognitive-semantik-simulation-qa.md"


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
