from __future__ import annotations

from pathlib import Path


def test_science_simulation_prototypes_are_local_noindex_and_interactive() -> None:
    root = Path(__file__).resolve().parents[2]
    simulation_dir = root / "lernmaterialien" / "lernsimulationen"
    files = [
        simulation_dir / "rutherford-streuversuch-simulation.html",
        simulation_dir / "galvanische-zelle-simulator.html",
        simulation_dir / "teilchenbewegung-temperatur-simulation.html",
    ]

    for path in files:
        html = path.read_text(encoding="utf-8")
        assert '<meta name="robots" content="noindex,follow">' in html
        assert "/favicon.ico" in html
        assert "<canvas" in html or "cell" in html
        assert "addEventListener" in html
        assert "Prüfen" in html
        assert "Vorhersage" in html
        assert "feedback" in html
