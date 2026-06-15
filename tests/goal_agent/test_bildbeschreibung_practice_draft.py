from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "lernmaterialien" / "entwuerfe" / "bildbeschreibung-schreibaufgaben-uebung-spec.md"
HTML = ROOT / "lernmaterialien" / "entwuerfe" / "bildbeschreibung-schreibaufgaben-uebung.html"


def _visible_text(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def test_bildbeschreibung_practice_spec_exists_before_draft() -> None:
    assert SPEC.exists()
    assert HTML.exists()
    assert SPEC.stat().st_mtime <= HTML.stat().st_mtime

    spec = SPEC.read_text(encoding="utf-8")
    required = [
        "Primary keyword",
        "Search intent",
        "Asset-Plan",
        "Schreibworkflow",
        "Typische Fehler",
        "QA-Checkliste",
        "Tracking",
        "Schwierigkeit",
    ]
    for marker in required:
        assert marker in spec


def test_bildbeschreibung_practice_draft_contract() -> None:
    html = HTML.read_text(encoding="utf-8")
    visible = _visible_text(html)

    assert '<meta name="robots" content="noindex,nofollow">' in html
    assert "schema.org" in html
    assert "window.dataLayer.push" in html
    assert "<textarea" in html
    assert "Struktur-Scaffold" in visible
    assert "Wortbank" in visible
    assert "Selbstcheck" in visible
    assert "Bewertungsraster" in visible
    assert "Musterlösung" in visible
    assert "Typische Fehler" in visible
    assert "Revision" in visible
    assert "Schwierigkeitsprogression" in visible

    assert "model-stage" in html
    assert "@keyframes travel" in html
    assert "Vorhersage" in visible
    assert "Prüfen" in visible
    assert "predictionChecked && words >= 20" in html
    assert "automatische Bewertung" in visible
    assert "automatisch benotet" not in visible.lower()


def test_bildbeschreibung_practice_german_copy_and_artifacts() -> None:
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
