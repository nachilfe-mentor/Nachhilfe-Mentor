from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "zeitungsartikel-schreibaufgaben-uebung-spec.md"
HTML = ROOT / "lernmaterialien" / "entwuerfe" / "zeitungsartikel-schreibaufgaben-uebung.html"
QA = ROOT / "lernmaterialien" / "entwuerfe" / "zeitungsartikel-schreibaufgaben-uebung-qa.md"


def _visible_text(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_zeitungsartikel_spec_exists_before_draft() -> None:
    assert SPEC.exists()
    assert HTML.exists()
    assert QA.exists()
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime

    spec = SPEC.read_text(encoding="utf-8")
    qa = QA.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Topic cluster",
        "Asset-Plan",
        "Schreibworkflow",
        "Typische Fehler",
        "QA-Checkliste",
        "Tracking",
        "Musterlösung",
    ]
    for marker in required:
        assert marker in spec

    assert "coding_task_a30ea554751d5830" in spec
    assert "coding_task_a30ea554751d5830" in qa
    assert "Vorher-Nachher-Revision" in qa


def test_zeitungsartikel_practice_draft_contract() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible_text(html)

    assert '<meta name="robots" content="noindex,nofollow">' in html
    assert "schema.org" in html
    assert "window.dataLayer.push" in html
    assert "Freitext" not in html
    assert "<textarea" in html
    assert "Recherchezettel" in visible
    assert "Struktur-Scaffold" in visible
    assert "Wortbank" in visible
    assert "Selbstcheck" in visible
    assert "Bewertungsraster" in visible
    assert "Musterlösung" in visible
    assert "Typische Fehler" in visible
    assert "Revision" in visible
    assert "Schwierigkeitsprogression" in visible
    assert "Vorher: Formulierung" in visible
    assert "Nachher: sachlicher" in visible
    assert "practice_revision_log_started" in html
    assert "revisionLogged" in html

    assert "model-stage" in html
    assert "Vorhersage" in visible
    assert "Prüfen" in visible
    assert "predictionChecked && words >= 40" in html
    assert "automatische Bewertung" in visible
    assert "automatisch bewertet" in visible
    assert "automatisch benotet" not in visible.lower()
    assert "/blog/posts/zeitungsartikel-schreiben-tipps.html" in html


def test_zeitungsartikel_german_copy_and_artifacts() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible_text(html)

    assert "\\n" not in visible
    assert "\\t" not in visible
    assert "Musterloesung" not in visible
    assert "Pruefen" not in visible
    assert "Uebung" not in visible
    assert "ueberarbeite" not in visible
    assert "üben" in visible
    assert "Prüfen" in visible
    assert "Musterlösung" in visible
    assert "Überarbeitung" in visible or "überarbeiten" in visible
