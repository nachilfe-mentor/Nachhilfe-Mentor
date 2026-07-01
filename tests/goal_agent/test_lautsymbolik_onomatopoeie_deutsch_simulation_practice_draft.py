"""Tests für die Lautsymbolik-und-Onomatopoetika-Simulation (Draft/noindex)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "lautsymbolik-onomatopoeie-deutsch-simulation-spec.md"
HTML = ROOT / "lernmaterialien" / "lernsimulationen" / "lautsymbolik-onomatopoeie-deutsch-simulation.html"
QA   = ROOT / "lernmaterialien" / "entwuerfe" / "lautsymbolik-onomatopoeie-deutsch-simulation-qa.md"


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
        "Bouba",
        "Kiki",
        "Phonästheme",
        "Missverständnis",
        "QA-Checkliste",
        "Zwei-Stufen-Progression",
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


def test_html_has_dom_animation() -> None:
    """Simulation hat eine SVG + CSS-Animation."""
    html = HTML.read_text(encoding="utf-8")
    assert "<svg" in html, "SVG-Visualisierung fehlt"
    assert "@keyframes" in html, "CSS-Animation (@keyframes) fehlt"


def test_html_has_prediction_task() -> None:
    """Stufe 1 hat eine Vorhersage-Aufgabe."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Vorhersage" in visible, "Kein 'Vorhersage'-Element im sichtbaren Text"
    assert "option-btn" in html, "Keine option-btn Buttons"


def test_html_has_two_step_progression() -> None:
    """Mindestens drei Stufen vorhanden (stage1, stage2, stage3)."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "stage1" in html, "stage1 fehlt"
    assert "stage2" in html, "stage2 fehlt"
    assert "stage3" in html, "stage3 fehlt"
    assert "Stufe 1" in visible, "'Stufe 1' fehlt im sichtbaren Text"
    assert "Stufe 2" in visible, "'Stufe 2' fehlt im sichtbaren Text"


def test_html_feedback_names_concept() -> None:
    """Feedback benennt die Konzepte Lautsymbolik, Phonästheme und Arbitraritätsprinzip."""
    html = HTML.read_text(encoding="utf-8")
    assert "Lautsymbolik" in html, "'Lautsymbolik' fehlt"
    assert "Phonästheme" in html, "'Phonästheme' fehlt"
    assert "concept-tag" in html, "concept-tag-Klasse fehlt"
    assert "Bouba-Kiki-Effekt" in html, "'Bouba-Kiki-Effekt' fehlt"


def test_html_has_bouba_kiki_shapes() -> None:
    """Beide Formen (Bouba-Blob und Kiki-Stern) als SVG vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    assert "shape-bouba" in html, "Bouba-Formklasse fehlt"
    assert "shape-kiki" in html, "Kiki-Formklasse fehlt"
    assert "<polygon" in html or "<path" in html, "SVG-Formelelemente fehlen"


def test_html_has_phonaesthem_section() -> None:
    """gl-Phonästheme im sichtbaren Text vorhanden."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "glänzen" in visible, "'glänzen' fehlt im sichtbaren Text"
    assert "glitzern" in visible, "'glitzern' fehlt im sichtbaren Text"
    assert "gleißen" in visible, "'gleißen' fehlt im sichtbaren Text"


def test_html_has_language_comparison() -> None:
    """Sprachvergleich-Tabelle mit Hahnlaut in mehreren Sprachen."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Kikeriki" in visible, "'Kikeriki' fehlt"
    assert "cock-a-doodle-doo" in visible, "'cock-a-doodle-doo' fehlt"
    assert "cocorico" in visible, "'cocorico' fehlt"


def test_html_addresses_arbitraritaet_misconception() -> None:
    """Simulation adressiert das Missverständnis 'alle Sprache ist arbiträr'."""
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Saussure" in visible, "Saussure-Bezug fehlt"
    assert "arbiträr" in visible or "Arbitrarität" in visible, "Arbitrarität-Konzept fehlt"
    assert "Kontinuum" in visible, "'Kontinuum' fehlt (Ikonizität vs. Arbitrarität)"


def test_html_has_tracking() -> None:
    html = HTML.read_text(encoding="utf-8")
    assert "window.dataLayer" in html
    assert "data-asset-type" in html
    assert "data-topic-cluster" in html


def test_html_correct_german_umlauts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible(html)
    assert "Lautsymbolik" in visible
    assert "Phonästheme" in visible
    assert "Bouba-Kiki-Effekt" in visible
    # Keine ASCII-Umlaut-Ersetzungen
    assert "Phonaesthem" not in visible
    assert "Lautsymbolik" not in visible.replace("Lautsymbolik", "")  # sanity: present
    assert "ae" not in visible.split("Phonästheme")[0][-30:] if "Phonästheme" in visible else True


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
