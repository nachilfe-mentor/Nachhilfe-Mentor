"""Tests für die Greenberg-Sprachuniversalien-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "sprachuniversalien-greenberg-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "sprachuniversalien-greenberg-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "sprachuniversalien-greenberg-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ──────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: sprachuniversalien-greenberg-simulation-spec.md"


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
        "Greenberg",
        "Universal",
        "SOV",
        "VSO",
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

def test_html_has_animated_word_order_diagram() -> None:
    """DOM-basiertes Wortstellungsdiagramm mit Animation vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "card" in html, "card-Elemente fehlen"
    assert "transition" in html or "animation" in html, (
        "CSS-Transition oder -Animation fehlt"
    )
    assert "wo-block" in html or "wo-box" in html, (
        "Wortstellungs-Diagram-Elemente (wo-block/wo-box) fehlen"
    )


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe mit option-btn vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text"
    assert "option-btn" in html, "option-btn Klasse fehlt"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "Stufe 1 (stage1) fehlt"
    assert "stage2" in html, "Stufe 2 (stage2) fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Greenberg-Konzepte im Feedback ───────────────────────────────────────────

def test_html_feedback_names_greenberg_universals() -> None:
    """Feedback benennt Greenbergs Universalien explizit."""
    html = HTML.read_text(encoding="utf-8")
    assert "Universal 3" in html, "Greenbergs Universal 3 fehlt"
    assert "Universal 4" in html, "Greenbergs Universal 4 fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt"


def test_html_mentions_wortstellungstypen() -> None:
    """Simulation referenziert SOV, SVO und VSO."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "SOV" in visible, "SOV fehlt im sichtbaren Text"
    assert "SVO" in visible, "SVO fehlt im sichtbaren Text"
    assert "VSO" in visible, "VSO fehlt im sichtbaren Text"


def test_html_mentions_adposition_types() -> None:
    """Simulation erklärt Prä- und Postpositionen."""
    html = HTML.read_text(encoding="utf-8")
    assert "Postposition" in html, "Postposition fehlt"
    assert "Pr\u00e4position" in html or "Präposition" in html, "Präposition fehlt"


def test_html_has_language_examples() -> None:
    """Simulation enthält konkrete Sprachbeispiele (Türkisch, Walisisch)."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Türkisch" in visible or "T\u00fcrkisch" in visible, (
        "Türkisch-Beispiel fehlt"
    )
    assert "Walisisch" in visible, "Walisisch-Beispiel fehlt"


def test_html_addresses_misconception() -> None:
    """Simulation adressiert das Missverständnis 'Sprachmerkmale sind zufällig'."""
    html = HTML.read_text(encoding="utf-8")
    assert any(phrase in html for phrase in [
        "zuf\u00e4llig",
        "zufällig",
        "korrelieren",
        "Missverst\u00e4ndnis",
        "Missverständnis",
    ]), "Missverständnis-Adressierung fehlt"


# ── Tracking ──────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "data-asset-type" in html, "data-asset-type fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster fehlt"
    assert "sprachen" in html, "topic-cluster 'sprachen' fehlt"


# ── Deutsche Rechtschreibung ──────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert any(c in visible for c in "äöüÄÖÜß"), (
        "Keine deutschen Umlaute im sichtbaren Text gefunden"
    )
    assert "Greenberg" in visible, "Schlüsselbegriff 'Greenberg' fehlt im sichtbaren Text"
    # Keine ASCII-Ersetzungen für Umlaute
    assert "Praeposition" not in visible, "ASCII-Ersatz 'Praeposition' gefunden"
    assert "Wortstellung" in visible, "Schlüsselbegriff 'Wortstellung' fehlt"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: sprachuniversalien-greenberg-simulation-qa.md"


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
