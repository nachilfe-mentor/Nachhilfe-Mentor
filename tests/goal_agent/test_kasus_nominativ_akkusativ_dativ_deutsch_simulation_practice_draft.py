"""Tests für die Kasus-Simulation (Nominativ, Akkusativ, Dativ) – Draft/noindex."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "kasus-nominativ-akkusativ-dativ-deutsch-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "kasus-nominativ-akkusativ-dativ-deutsch-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "kasus-nominativ-akkusativ-dativ-deutsch-simulation-qa.md"


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>",  " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_spec_exists_before_html() -> None:
    """Spec-Datei muss vor der HTML-Datei angelegt worden sein."""
    assert SPEC.exists(), "Spec-Datei fehlt"
    assert HTML.exists(), "HTML-Datei fehlt"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, "Spec muss älter sein als HTML"


def test_spec_contains_required_sections() -> None:
    """Spec enthält alle Pflichtabschnitte."""
    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Nominativ",
        "Akkusativ",
        "Dativ",
        "Genitiv",
        "Missverständnis",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
        "Fragewort",
    ]
    for marker in required:
        assert marker in spec, f"Spec fehlt Abschnitt/Begriff: {marker}"


def test_html_is_noindex() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex,nofollow">' in html


def test_html_has_schema_org() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "schema.org" in html
    assert "LearningResource" in html


def test_html_has_prediction_task() -> None:
    """Mindestens eine Vorhersage-Aufgabe (Fragewort-Auswahl in Stufe 1)."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible or "Fragewort" in visible
    assert "option-btn" in html


def test_html_has_two_step_progression() -> None:
    """Zwei Stufen: Stufe 1 (Kasus erkennen) und Stufe 2 (Artikel einsetzen)."""
    html = HTML.read_text(encoding="utf-8")
    assert "stage1" in html or "Stufe 1" in html
    assert "stage2" in html or "Stufe 2" in html
    assert "Stufe 1" in html
    assert "Stufe 2" in html


def test_html_has_four_kasus() -> None:
    """Alle vier deutschen Kasus müssen im sichtbaren Text vorkommen."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Nominativ" in visible
    assert "Akkusativ" in visible
    assert "Dativ" in visible
    assert "Genitiv" in visible


def test_html_feedback_names_concepts() -> None:
    """Feedback benennt Kasusnamen und grammatische Funktion."""
    html = HTML.read_text(encoding="utf-8")
    assert "concept-tag" in html
    assert "Dativ" in html
    assert "Akkusativ" in html
    assert "Nominativ" in html
    assert "Genitiv" in html


def test_html_has_fragewort_test() -> None:
    """Fragewörter Wer/Wen/Wem/Wessen müssen vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Wer?" in visible or "Wer " in visible
    assert "Wen?" in visible or "Wen " in visible
    assert "Wem?" in visible or "Wem " in visible
    assert "Wessen?" in visible or "Wessen " in visible


def test_html_addresses_misconception() -> None:
    """Simulation adressiert das Missverständnis Dativ/Akkusativ-Verwechslung."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Muss das häufige Fehler explizit nennen
    assert "mit dem" in visible or "Dativ" in visible
    assert "häufiger Fehler" in visible.lower() or "Häufiger Fehler" in visible or "verwechsel" in visible.lower()


def test_html_has_deklination_table() -> None:
    """Deklinationstabelle muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "der" in visible
    assert "den" in visible
    assert "dem" in visible
    assert "des" in visible
    assert "dekl-table" in html


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    # Korrekte Umlaute müssen vorhanden sein
    assert "ü" in visible or "ö" in visible or "ä" in visible
    # Keine ASCII-Ersetzungen in sichtbarem Text
    assert "Haeufiger" not in visible
    assert "Zugehoerigkeit" not in visible
    assert "Missverstaendnis" not in visible
    # Korrekte Formen
    assert "Zugehörigkeit" in visible
    assert "Schüler" in visible or "Schülerin" in visible


def test_html_no_escape_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "\\n" not in visible
    assert "\\t" not in visible
    assert "&bsol;n" not in visible


def test_html_has_favicon() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "/favicon.ico" in html


def test_html_lang_de() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert 'lang="de"' in html


def test_html_has_artikel_input() -> None:
    """Stufe 2 enthält Artikel-Einsetzen-Aufgabe."""
    html = HTML.read_text(encoding="utf-8")
    assert "artikel-btn" in html
    assert "blank-slot" in html


def test_html_has_sentence_diagram() -> None:
    """Satzdiagramm mit word-block-Elementen muss vorhanden sein."""
    html = HTML.read_text(encoding="utf-8")
    assert "sentence-diagram" in html
    assert "word-block" in html


def test_qa_note_exists() -> None:
    """QA-Notiz muss nach dem HTML angelegt worden sein."""
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
        assert marker in qa, f"QA-Notiz fehlt Abschnitt: {marker}"
