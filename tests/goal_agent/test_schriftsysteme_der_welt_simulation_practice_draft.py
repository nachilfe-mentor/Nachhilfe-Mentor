"""Tests für die Schriftsysteme-der-Welt-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "schriftsysteme-der-welt-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "schriftsysteme-der-welt-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "schriftsysteme-der-welt-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: schriftsysteme-der-welt-simulation-spec.md"


def test_spec_older_than_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein (Spec-first-Regel)."""
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss älter sein als HTML (Spec-first-Regel)"
    )


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Logographie",
        "Syllabarie",
        "Abjad",
        "Abugida",
        "Alphabet",
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
    assert "schema.org" in html, "schema.org fehlt"
    assert "LearningResource" in html, "LearningResource fehlt"


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html, "/favicon.ico fehlt"


# ── DOM-Animation / SVG ───────────────────────────────────────────────────────

def test_html_has_svg_animation() -> None:
    """SVG-Schriftrad vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "<svg" in html, "SVG-Element fehlt"
    assert "transition" in html or "animation" in html, (
        "CSS-Transition oder -Animation fehlt"
    )


def test_html_has_flip_card() -> None:
    """Flip-Karten-Animation vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "flip-card" in html, "flip-card Klasse fehlt"
    assert "flipped" in html, "flipped-Klasse fehlt"


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "vorhersage" in visible.lower() or "Vorhersage" in visible, (
        "Vorhersage-Aufgabe nicht im sichtbaren Text gefunden"
    )
    assert "option-btn" in html, "option-btn Klasse fehlt"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ──────────────────────────────────────────────────

def test_html_feedback_names_all_five_types() -> None:
    """Feedback benennt alle 5 Schrifttypen explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Logographie" in html, "Begriff 'Logographie' fehlt"
    assert "Syllabarie" in html, "Begriff 'Syllabarie' fehlt"
    assert "Alphabet" in html, "Begriff 'Alphabet' fehlt"
    assert "Abjad" in html, "Begriff 'Abjad' fehlt"
    assert "Abugida" in html, "Begriff 'Abugida' fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_shows_real_script_examples() -> None:
    """Simulation enthält echte Unicode-Schriftzeichen."""
    html = HTML.read_text(encoding="utf-8")
    # Chinesisch, Hiragana, Arabisch, Devanagari, Latein
    assert "水" in html, "Chinesisches Zeichen 水 fehlt"
    assert "み" in html, "Hiragana-Zeichen み fehlt"
    assert "ب" in html, "Arabisches Zeichen ب fehlt"
    assert "क" in html, "Devanagari-Zeichen क fehlt"


def test_html_addresses_misconception() -> None:
    """Simulation adressiert das Missverständnis 'alle Schriften = Alphabet'."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert any(phrase in visible for phrase in [
        "nicht für einen Laut",
        "keine direkte Lautentsprechung",
        "Bedeutungseinheit",
        "primitiv",
        "primitiver",
    ]), "Missverständnis-Adressierung fehlt im sichtbaren Text"


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
    assert "ü" in visible or "ä" in visible or "ö" in visible, (
        "Keine deutschen Umlaute im sichtbaren Text gefunden"
    )
    assert "Schriftsysteme" in visible, "Schlüsselbegriff 'Schriftsysteme' fehlt"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: schriftsysteme-der-welt-simulation-qa.md"


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
