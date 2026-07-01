"""Tests für die Sprachfamilien-Simulation (Draft/noindex) – Keyword: sprachen."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "sprachfamilien-indoeuropaeisch-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "sprachfamilien-indoeuropaeisch-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "sprachfamilien-indoeuropaeisch-simulation-qa.md"


def _visible(html: str) -> str:
    """Sichtbaren Text aus HTML extrahieren (ohne Script- und Style-Blöcke)."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",   " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


# ── Spec ───────────────────────────────────────────────────────────────────────

def test_spec_exists() -> None:
    """Spec-Datei muss vorhanden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt: sprachfamilien-indoeuropaeisch-simulation-spec.md"


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
        "sprachen",
        "Swadesh",
        "Kognat",
        "Indo-Europäisch",
        "Ural",
        "lexikalische Distanz",
        "Fehlvorstellung",
        "Stufe 1",
        "Stufe 2",
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

def test_html_has_svg_tree() -> None:
    """SVG-Stammbaum vorhanden und mit Animation."""
    html = HTML.read_text(encoding="utf-8")
    assert 'id="tree-svg"' in html, "tree-svg Element fehlt"
    assert "Proto-Indo-Europäisch" in html, "PIE-Bezeichnung fehlt"
    assert "setTimeout" in html, "setTimeout (Animation) fehlt"


def test_html_tree_shows_language_families() -> None:
    """Alle Hauptsprachfamilien im Baum vertreten."""
    html = HTML.read_text(encoding="utf-8")
    for family in ("Germanisch", "Romanisch", "Slawisch"):
        assert family in html, f"Sprachfamilie '{family}' fehlt im Baum"


def test_html_tree_shows_non_ie_group() -> None:
    """Nicht-IE-Gruppe (Ural) klar außerhalb des Stammbaums dargestellt."""
    html = HTML.read_text(encoding="utf-8")
    assert "Ural" in html, "Ural-Sprachfamilien fehlen"
    assert "Finnisch" in html, "Finnisch als Ural-Beispiel fehlt"
    assert "Nicht IE" in html or "Nicht-IE" in html or "nicht indoeuropäisch" in html.lower(), (
        "Nicht-IE-Kennzeichnung fehlt"
    )


# ── Vorhersage / Rangfolge-Aufgabe ────────────────────────────────────────────

def test_html_has_ranking_task() -> None:
    """Rangfolge-Vorhersage-Aufgabe vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert 'id="rank-pool"' in html, "rank-pool fehlt"
    assert "lang-card" in html, "lang-card Klasse fehlt"
    assert 'onclick="rankSelect(' in html, "rankSelect-Handler fehlt"


def test_html_has_five_language_cards() -> None:
    """Genau 5 Sprachkarten im Ranking."""
    html = HTML.read_text(encoding="utf-8")
    for lang in ("nl", "sv", "ru", "fr", "fi"):
        assert f'data-lang="{lang}"' in html, f"Sprachkarte für '{lang}' fehlt"


def test_html_has_submit_button() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'onclick="submitRanking()"' in html, "submitRanking-Handler fehlt"


# ── Kognaten-Detektiv ─────────────────────────────────────────────────────────

def test_html_has_detective_rounds() -> None:
    """Zwei Kognaten-Detektiv-Runden vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "word-chip" in html, "word-chip Klasse fehlt"
    assert "option-btn" in html, "option-btn Klasse fehlt"
    assert 'id="options-a"' in html, "Runde A (options-a) fehlt"
    assert 'id="options-b"' in html, "Runde B (options-b) fehlt"


def test_html_detective_round_a_has_dutch_words() -> None:
    """Runde A enthält niederländische Swadesh-Wörter."""
    html = HTML.read_text(encoding="utf-8")
    for word in ("water", "moeder", "nacht", "twee"):
        assert word in html, f"Niederländisches Wort '{word}' fehlt in Runde A"


def test_html_detective_round_b_has_spanish_words() -> None:
    """Runde B enthält spanische Swadesh-Wörter."""
    html = HTML.read_text(encoding="utf-8")
    for word in ("agua", "madre", "noche", "dos"):
        assert word in html, f"Spanisches Wort '{word}' fehlt in Runde B"


# ── Zwei-Stufen-Progression ───────────────────────────────────────────────────

def test_html_has_three_step_sections() -> None:
    """Drei Stufen-Sektionen plus Abschluss vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert 'id="step-0"' in html, "step-0 fehlt"
    assert 'id="step-1"' in html, "step-1 fehlt"
    assert 'id="step-2"' in html, "step-2 fehlt"
    assert 'id="step-complete"' in html, "step-complete fehlt"


def test_html_has_progress_dots() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "step-dot" in html, "step-dot Klasse (Fortschritts-Punkte) fehlt"
    assert "Stufe 1 von 3" in html, "'Stufe 1 von 3' fehlt"


# ── Feedback benennt Fachkonzepte ─────────────────────────────────────────────

def test_html_feedback_names_cognates() -> None:
    """Feedback benennt Kognaten explizit als linguistisches Konzept."""
    html = HTML.read_text(encoding="utf-8")
    assert "Kognat" in html, "'Kognat' fehlt im Feedback"
    assert "Swadesh" in html, "'Swadesh' fehlt im Feedback"


def test_html_feedback_names_language_families() -> None:
    """Feedback nennt konkrete Sprachfamilienbezeichnungen."""
    html = HTML.read_text(encoding="utf-8")
    assert "westgermanisch" in html.lower(), "Westgermanisch im Feedback fehlt"
    assert "Ural-Sprachfamilie" in html or "Ural-Sprachen" in html, (
        "Ural-Sprachfamilie im Feedback fehlt"
    )


def test_html_addresses_misconception_geography() -> None:
    """Fehlvorstellung Geografie ≠ Sprachverwandtschaft explizit adressiert."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Geograf" in visible or "geograph" in visible.lower(), (
        "Geografie-Fehlvorstellung nicht adressiert"
    )


# ── Tracking ──────────────────────────────────────────────────────────────────

def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html, "window.dataLayer fehlt"
    assert "trackSim" in html, "trackSim-Funktion fehlt"
    assert "data-asset-type" in html, "data-asset-type Attribut fehlt"
    assert "data-topic-cluster" in html, "data-topic-cluster Attribut fehlt"


# ── Deutsche Rechtschreibung ──────────────────────────────────────────────────

def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Niederländisch" in visible, "'Niederländisch' mit Umlaut fehlt"
    assert "Verwandtschaft" in visible, "'Verwandtschaft' fehlt"
    assert "Überraschung" in visible or "überraschung" in visible.lower() or "Finnisch" in visible, (
        "Wichtige Umlaute fehlen im sichtbaren Text"
    )
    # Keine ASCII-Ersetzungen
    assert "Niederlandisch" not in visible, "ASCII-Ersatz 'Niederlandisch' gefunden"
    assert "Verwandschaft" not in visible, "Falsche Schreibweise 'Verwandschaft' gefunden"


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible, "Literal \\n im sichtbaren Text"
    assert "\\t" not in visible, "Literal \\t im sichtbaren Text"
    assert "&bsol;n" not in visible, "&bsol;n im sichtbaren Text"


# ── Summary-Tabelle ───────────────────────────────────────────────────────────

def test_html_has_summary_table() -> None:
    """Abschluss-Tabelle mit Kognat-Scores vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "summary-table" in html, "summary-table Klasse fehlt"
    assert "90 %" in html, "Kognat-Score 90% für Niederländisch fehlt"
    assert "10 %" in html, "Kognat-Score 10% für Finnisch fehlt"


# ── QA-Notiz ──────────────────────────────────────────────────────────────────

def test_qa_note_exists() -> None:
    """QA-Notiz muss existieren."""
    assert QA.exists(), "QA-Notiz fehlt: sprachfamilien-indoeuropaeisch-simulation-qa.md"


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
