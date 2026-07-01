"""Tests für die Sprachliche-Universalien-Greenberg-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "sprachliche-universalien-greenberg-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "sprachliche-universalien-greenberg-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "sprachliche-universalien-greenberg-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: sprachliche-universalien-greenberg-simulation-spec.md"


def test_spec_older_than_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein (Spec-first-Regel)."""
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss älter sein als HTML (Spec-first-Regel)"
    )


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte und Fachbegriffe."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Greenberg",
        "Implikationsuniversalien",
        "Absolute Universalien",
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


# ── DOM-Animation ──────────────────────────────────────────────────────────────

def test_html_has_dom_animation() -> None:
    """DOM-basierte Sprachen-Radar-Animation vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "lang-node" in html, "lang-node Elemente (Sprachen-Radar) fehlen"
    assert "transition" in html or "animation" in html, (
        "CSS-Transition oder -Animation fehlt"
    )


def test_html_has_language_nodes() -> None:
    """Mindestens sechs verschiedene Sprachen im Radar."""
    html = HTML.read_text(encoding="utf-8")
    assert "node-de" in html, "Deutsch-Knoten (node-de) fehlt"
    assert "node-ja" in html, "Japanisch-Knoten (node-ja) fehlt"
    assert "node-ar" in html, "Arabisch-Knoten (node-ar) fehlt"
    assert "node-tr" in html, "Türkisch-Knoten (node-tr) fehlt"
    assert "node-zh" in html, "Mandarin-Knoten (node-zh) fehlt"
    assert "node-sw" in html, "Swahili-Knoten (node-sw) fehlt"


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text gefunden"
    assert "option-btn" in html, "option-btn Klasse fehlt"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "stage3" in html, "Zusammenfassung (stage3) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ──────────────────────────────────────────────────

def test_html_feedback_names_greenberg_concepts() -> None:
    """Feedback benennt Greenbergs Universalien-Konzepte explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Greenberg" in html, "Begriff 'Greenberg' fehlt"
    assert "Universalien" in html or "Universale" in html, (
        "Begriff 'Universalien'/'Universale' fehlt"
    )
    assert "Implikationsuniversalien" in html or "Implikationsuniversale" in html, (
        "Begriff 'Implikationsuniversalien' fehlt"
    )
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_names_absolute_and_statistical_universals() -> None:
    """Simulation unterscheidet absolute und statistische Universalien."""
    html = HTML.read_text(encoding="utf-8")
    assert "Absolutes Universale" in html or "Absolute Universalien" in html, (
        "'Absolutes Universale' oder 'Absolute Universalien' fehlt"
    )
    assert "Statistisches Universale" in html or "Statistische Universalien" in html, (
        "'Statistisches Universale' fehlt"
    )


# ── Missverständnisse ─────────────────────────────────────────────────────────

def test_html_addresses_misconception_genus() -> None:
    """Simulation adressiert das Missverständnis 'Genus ist universell'."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Genus" in visible or "grammatisches" in visible, (
        "Genus-Missverständnis nicht adressiert"
    )


def test_html_addresses_misconception_tone_languages() -> None:
    """Simulation adressiert das Missverständnis 'Tonsprachen sind selten'."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Tonsprachen" in visible or "Tonsprache" in visible, (
        "Tonsprachen-Missverständnis nicht erwähnt"
    )


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
    # Schlüsselbegriffe mit korrekten Umlauten
    assert "Universalien" in visible, "Schlüsselbegriff 'Universalien' fehlt"
    assert "Türkisch" in visible or "türkisch" in visible.lower(), (
        "'Türkisch' mit Umlaut fehlt"
    )
    # Keine ASCII-Ersetzungen im sichtbaren Text
    assert "Tuerken" not in visible, "ASCII-Ersatz 'Tuerken' statt Umlauts gefunden"
    assert "Universalitaet" not in visible, "ASCII-Ersatz gefunden"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: sprachliche-universalien-greenberg-simulation-qa.md"


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
