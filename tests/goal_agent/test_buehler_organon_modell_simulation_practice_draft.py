"""Tests für die Bühler-Organon-Modell-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "buehler-organon-modell-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "buehler-organon-modell-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "buehler-organon-modell-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: buehler-organon-modell-simulation-spec.md"


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
        "Search intent",
        "Bühler",
        "Darstellungsfunktion",
        "Ausdrucksfunktion",
        "Appellfunktion",
        "Organon",
        "Missverständnis",
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


# ── SVG-Animation ──────────────────────────────────────────────────────────────

def test_html_has_svg_animation() -> None:
    """SVG-Dreieck als visuelles Modell vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "<svg" in html, "SVG-Element fehlt"
    assert "transition" in html, "CSS-Transition für Animation fehlt"
    assert "edge" in html, "Kanten-Elemente (edge) für Dreieck-Animation fehlen"


def test_html_has_triangle_model() -> None:
    """Bühlers Dreieck mit allen drei Polen vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Sachverhalt" in visible, "Dreieck-Pol 'Sachverhalt' fehlt"
    assert "Sender" in visible, "Dreieck-Pol 'Sender' fehlt"
    assert "Empfänger" in visible, "Dreieck-Pol 'Empfänger' fehlt"


# ── Vorhersage-Aufgabe ─────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible or "vorhersage" in visible.lower(), (
        "Vorhersage-Aufgabe nicht im sichtbaren Text gefunden"
    )
    assert "option-btn" in html, "option-btn Klasse fehlt"


def test_html_has_rot_example() -> None:
    """Bühlers klassisches 'Rot!'-Beispiel ist enthalten."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Rot!" in visible or "\u201eRot!\u201c" in html, (
        "Bühlers Schlüsselbeispiel 'Rot!' fehlt im sichtbaren Text"
    )


# ── Zwei-Stufen-Progression ────────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ───────────────────────────────────────────────────

def test_html_feedback_names_buhler_concepts() -> None:
    """Feedback benennt alle drei Sprachfunktionen explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Darstellungsfunktion" in html, "Begriff 'Darstellungsfunktion' fehlt"
    assert "Ausdrucksfunktion" in html, "Begriff 'Ausdrucksfunktion' fehlt"
    assert "Appellfunktion" in html, "Begriff 'Appellfunktion' fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_mentions_buehler_symbols() -> None:
    """Bühlers Symbolnamen (Symbol, Symptom, Signal) sind enthalten."""
    html = HTML.read_text(encoding="utf-8")
    assert "Symbol" in html, "Bühlers Bezeichnung 'Symbol' fehlt"
    assert "Symptom" in html, "Bühlers Bezeichnung 'Symptom' fehlt"
    assert "Signal" in html, "Bühlers Bezeichnung 'Signal' fehlt"


def test_html_addresses_misconception() -> None:
    """Simulation adressiert das Missverständnis 'eine Äußerung – eine Funktion'."""
    html = HTML.read_text(encoding="utf-8")
    assert any(phrase in html for phrase in [
        "gleichzeitig",
        "immer gleichzeitig",
        "alle drei",
        "dominiert",
    ]), "Missverständnis-Adressierung (gleichzeitig aktiv) fehlt"


def test_html_mentions_sprechakttheorie() -> None:
    """Simulation grenzt Organon-Modell von der Sprechakttheorie ab."""
    html = HTML.read_text(encoding="utf-8")
    assert "Sprechakttheorie" in html or "Sprechakt" in html, (
        "Abgrenzung zur Sprechakttheorie fehlt"
    )
    assert "Austin" in html or "Searle" in html or "Illokution" in html, (
        "Verweis auf Austin/Searle/Illokution fehlt"
    )


# ── Tracking ───────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "data-asset-type" in html, "data-asset-type fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster fehlt"


# ── Deutsche Rechtschreibung ───────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "ü" in visible or "ö" in visible or "ä" in visible, (
        "Keine deutschen Umlaute im sichtbaren Text gefunden"
    )
    assert "Bühler" in visible or "B\u00fchler" in visible, (
        "Schlüsselbegriff 'Bühler' fehlt im sichtbaren Text"
    )


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ───────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: buehler-organon-modell-simulation-qa.md"


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
