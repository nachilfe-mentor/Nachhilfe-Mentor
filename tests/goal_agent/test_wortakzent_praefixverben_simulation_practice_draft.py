"""Tests für die Wortakzent-Präfixverben-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "wortakzent-praefixverben-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "wortakzent-praefixverben-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "wortakzent-praefixverben-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec-First ────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: wortakzent-praefixverben-simulation-spec.md"


def test_spec_older_than_html() -> None:
    """Spec muss vor der HTML-Datei angelegt worden sein (Spec-First-Regel)."""
    assert SPEC.exists() and HTML.exists(), "Spec oder HTML fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss älter sein als HTML (Spec-first-Regel)"
    )


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Wortakzent",
        "trennbar",
        "untrennbar",
        "Präfixverben",
        "Primary keyword",
        "Asset-Plan",
        "Missverständnisse",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
        "übersetzen",
        "umfahren",
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
    assert "/favicon.ico" in html, "/favicon.ico fehlt"


# ── Canvas-Animation ──────────────────────────────────────────────────────────

def test_html_has_canvas_animation() -> None:
    """Canvas-Element und requestAnimationFrame müssen vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "<canvas" in html, "Canvas-Element fehlt"
    assert "requestAnimationFrame" in html, "requestAnimationFrame fehlt – keine Animation"


# ── Vorhersage-Aufgabe ────────────────────────────────────────────────────────

def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Vorhersage-Aufgabe nicht im sichtbaren Text"
    assert "option-btn" in html, "option-btn Klasse fehlt (Auswahlknöpfe)"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_two_step_progression() -> None:
    """Mindestens zwei Stufen (stage1 und stage2) vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html, "stage1 fehlt"
    assert "stage2" in html, "stage2 fehlt"
    assert "Stufe 1" in html, "'Stufe 1' Text fehlt"
    assert "Stufe 2" in html, "'Stufe 2' Text fehlt"


# ── Fachbegriffe im Feedback ──────────────────────────────────────────────────

def test_html_feedback_names_concepts() -> None:
    """Feedback benennt Fachbegriffe Wortakzent, trennbar, untrennbar."""
    html = HTML.read_text(encoding="utf-8")
    assert "Wortakzent" in html, "Begriff 'Wortakzent' fehlt"
    assert "trennbar" in html.lower(), "Begriff 'trennbar' fehlt"
    assert "untrennbar" in html.lower(), "Begriff 'untrennbar' fehlt"
    assert "concept-tag" in html, "concept-tag Klasse fehlt (Konzept-Feedback)"
    assert "Präfixverb" in html, "Begriff 'Präfixverb' fehlt"


def test_html_addresses_misconception() -> None:
    """Simulation adressiert das Missverständnis zu homographen Präfixverben."""
    html = HTML.read_text(encoding="utf-8")
    assert any(phrase in html for phrase in [
        "Missverständnis",
        "Häufiges Missverständnis",
        "häufiges Missverständnis",
        "Irrtum",
        "grundverschieden",
        "eine Bedeutung",
    ]), "Missverständnis-Adressierung fehlt"


# ── Verb-Beispiele ────────────────────────────────────────────────────────────

def test_html_contains_canonical_verb_pairs() -> None:
    """Die kanonischen Beispielverbpaare müssen im HTML vorkommen."""
    html = HTML.read_text(encoding="utf-8")
    assert "umfahren" in html.lower(), "Verbpaar 'umfahren' fehlt"
    assert "übersetzen" in html.lower(), "Verbpaar 'übersetzen' fehlt"
    assert "wiederholen" in html.lower(), "Verbpaar 'wiederholen' fehlt"


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
        "Keine deutschen Umlaute im sichtbaren Text"
    )
    # Keine ASCII-Ersetzungen
    forbidden = ["Praefixverben", "Prafix", "Woerter", "trennbares Verb ohne Umlaut"]
    for bad in forbidden:
        assert bad not in visible, f"ASCII-Umlaut-Ersetzung '{bad}' gefunden"
    # Korrekte Umlaute prüfen
    assert "Präfix" in visible or "Präfixverb" in visible, "Korrekte Umlaut-Schreibung 'Präfix' fehlt"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible,    "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible,    "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: wortakzent-praefixverben-simulation-qa.md"


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
