"""Tests für die Neurolinguistik Broca-Wernicke-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "neurolinguistik-broca-wernicke-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "neurolinguistik-broca-wernicke-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "neurolinguistik-broca-wernicke-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: neurolinguistik-broca-wernicke-simulation-spec.md"


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
        "Broca",
        "Wernicke",
        "Aphasie",
        "Fasciculus arcuatus",
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


# ── SVG-Diagramm / Animation ──────────────────────────────────────────────────

def test_html_has_brain_svg() -> None:
    """SVG-Gehirn-Diagramm mit Broca- und Wernicke-Areal vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "<svg" in html, "SVG-Element fehlt"
    assert "broca-area" in html, "Broca-Areal SVG-Element fehlt"
    assert "wernicke-area" in html, "Wernicke-Areal SVG-Element fehlt"


def test_html_has_animation() -> None:
    """CSS-Animation für Gehirn-Aktivierung vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "animation" in html, "CSS-Animation fehlt"
    assert "pulse" in html or "transition" in html, "Puls-Animation oder Transition fehlt"


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text gefunden"
    assert "option-btn" in html, "option-btn Klasse fehlt"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ──────────────────────────────────────────────────

def test_html_feedback_names_brain_areas() -> None:
    """Feedback benennt Broca- und Wernicke-Areal explizit mit Konzept-Tags."""
    html = HTML.read_text(encoding="utf-8")
    assert "Broca-Areal" in html, "Begriff 'Broca-Areal' fehlt"
    assert "Wernicke-Areal" in html, "Begriff 'Wernicke-Areal' fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_mentions_aphasien() -> None:
    """Simulation erklärt Broca-Aphasie und Wernicke-Aphasie."""
    html = HTML.read_text(encoding="utf-8")
    assert "Broca-Aphasie" in html, "Broca-Aphasie fehlt"
    assert "Wernicke-Aphasie" in html, "Wernicke-Aphasie fehlt"
    assert "Leitungsaphasie" in html, "Leitungsaphasie fehlt"


def test_html_has_fasciculus_arcuatus() -> None:
    """Fasciculus arcuatus (Verbindungsbahn) wird erwähnt."""
    html = HTML.read_text(encoding="utf-8")
    assert "Fasciculus arcuatus" in html or "arcuatus" in html, (
        "Fasciculus arcuatus fehlt"
    )


def test_html_addresses_misconception() -> None:
    """Simulation adressiert Missverständnis (Wernicke-Aphasie ≠ Sprachverlust)."""
    html = HTML.read_text(encoding="utf-8")
    assert any(phrase in html for phrase in [
        "flüssig",
        "bedeutungslos",
        "Jargon",
        "telegraphisch",
    ]), "Differenzierung der Aphasie-Symptome fehlt"


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
    assert "ä" in visible or "ö" in visible or "ü" in visible, (
        "Keine deutschen Umlaute im sichtbaren Text gefunden"
    )
    assert "Broca" in visible, "Schlüsselbegriff 'Broca' fehlt"
    assert "Wernicke" in visible, "Schlüsselbegriff 'Wernicke' fehlt"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: neurolinguistik-broca-wernicke-simulation-qa.md"


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
