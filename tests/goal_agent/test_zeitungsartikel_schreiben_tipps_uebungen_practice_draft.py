from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SLUG = "zeitungsartikel-schreiben-tipps-uebungen"
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / f"{SLUG}-spec.md"
HTML = ROOT / "lernmaterialien" / "entwuerfe" / f"{SLUG}.html"
QA = ROOT / "lernmaterialien" / "entwuerfe" / f"{SLUG}-qa.md"


def _visible_text(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_zeitungsartikel_tipps_spec_exists_before_draft() -> None:
    assert SPEC.exists(), f"Spec-Datei fehlt: {SPEC}"
    assert HTML.exists(), f"HTML-Draft fehlt: {HTML}"
    assert QA.exists(), f"QA-Notiz fehlt: {QA}"
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime, (
        "Spec muss vor oder gleichzeitig mit HTML erstellt worden sein"
    )

    spec = SPEC.read_text(encoding="utf-8")
    required_sections = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Schreibworkflow",
        "Typische Fehler",
        "QA-Checkliste",
        "Tracking",
        "Zwei-Stufen-Progression",
    ]
    for marker in required_sections:
        assert marker in spec, f"Pflichtabschnitt fehlt in Spec: {marker!r}"


def test_zeitungsartikel_tipps_draft_contract() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible_text(html)

    # Sicherheit: noindex
    assert '<meta name="robots" content="noindex,nofollow">' in html

    # Schema und Tracking
    assert "schema.org" in html
    assert "window.dataLayer.push" in html

    # Aktive Eingabe
    assert "<textarea" in html

    # Pflichtabschnitte sichtbar
    assert "Struktur-Scaffold" in visible
    assert "Wortbank" in visible
    assert "Selbstcheck" in visible
    assert "Bewertungsraster" in visible
    assert "Musterlösung" in visible
    assert "Typische Fehler" in visible
    assert "Revision" in visible
    assert "Schwierigkeitsprogression" in visible

    # Animiertes Modell
    assert "model-stage" in html
    assert "@keyframes travel" in html

    # Vorhersage-Interaktion
    assert "Vorhersage" in visible
    assert "Prüfen" in visible
    assert "predictionChecked && words >= 40" in html

    # Keine Fake-Bewertung
    assert "automatische Bewertung" in visible
    assert "automatisch benotet" not in visible.lower()

    # Maschinenlesbare Metadaten
    assert 'data-subject="Deutsch"' in html
    assert 'data-grade-level="7-10"' in html
    assert 'data-asset-type="guided-writing-practice"' in html
    assert 'data-topic-cluster="schreibaufgaben-zeitungsartikel"' in html
    assert 'data-primary-keyword="schreibaufgaben"' in html

    # Fortschrittsanzeige
    assert "Fortschritt" in visible
    assert "0 von 4 Arbeitsschritten" in visible
    assert "progressBar.style.width" in html

    # Interner Link zum Blog-Artikel
    assert "/blog/posts/zeitungsartikel-schreiben-tipps.html" in html


def test_zeitungsartikel_tipps_german_copy_and_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible_text(html)

    # Keine sichtbaren Escape-Artefakte
    assert "\\n" not in visible
    assert "\\t" not in visible

    # Keine ASCII-Umlaut-Ersetzungen
    assert "Musterloesung" not in visible
    assert "Pruefen" not in visible
    assert "Uebung" not in visible
    assert "ueberarbeite" not in visible

    # Korrekte Umlaute vorhanden
    assert "üben" in visible
    assert "Prüfen" in visible
    assert "Musterlösung" in visible
    assert "Überarbeitung" in visible or "überarbeiten" in visible


def test_zeitungsartikel_tipps_qa_note_exists() -> None:
    qa = QA.read_text(encoding="utf-8")
    required = [
        "Nützlichkeit",
        "Interaktionschecks",
        "Layoutchecks",
        "Copy- und Safety-QA",
        "noindex",
        "automatische Bewertung",
    ]
    for section in required:
        assert section in qa, f"Pflichtabschnitt fehlt in QA-Notiz: {section!r}"
