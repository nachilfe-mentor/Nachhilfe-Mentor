#!/usr/bin/env python3
"""Build a compact context file for the autonomous blog writer.

Claude should not reread the full registry and strategy on every run. This
script extracts only the parts needed for safe topic selection and quality.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
BLOG_DIR = REPO_DIR / "blog"
REGISTRY = BLOG_DIR / "_BLOG_REGISTRY.md"
STRATEGY = BLOG_DIR / "_BLOG_STRATEGY.md"
OUT = BLOG_DIR / "_BLOG_CONTEXT_COMPACT.md"
NOTES = BLOG_DIR / "_BLOG_CONTEXT_NOTES.md"
GOAL_AGENT_TASKS = REPO_DIR / "goal_agent" / "exports" / "blog_task_snapshot.md"
GOAL_AGENT_GUARDIAN = REPO_DIR / "goal_agent" / "exports" / "blog_agent_guardian.md"
CONTENT_REGISTRY = REPO_DIR / "goal_agent" / "exports" / "content_registry_compact.md"


def section(text: str, heading: str) -> str:
    pattern = rf"(^## {re.escape(heading)}\n.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def latest_article_rows(registry: str, limit: int = 45) -> list[str]:
    rows = []
    in_table = False
    for line in registry.splitlines():
        if line.startswith("| # | Datum | Slug |"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            if not line.startswith("|"):
                break
            rows.append(line)
            if len(rows) >= limit:
                break
    return rows


def all_slugs(registry: str) -> list[str]:
    slugs: list[str] = []
    for line in registry.splitlines():
        if not line.startswith("| "):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 4 and parts[0].isdigit() and re.match(r"^[a-z0-9-]+$", parts[2]):
            slugs.append(parts[2])
    return slugs


def latest_analytics(strategy: str, limit: int = 7) -> list[str]:
    learnings = section(strategy, "Learnings / Analytics")
    bullets = [line for line in learnings.splitlines() if line.startswith("- Stand ")]
    return bullets[-limit:]


def lernmaterialien_section(registry_path: Path) -> str:
    """Extract just the live-simulations section from the content registry for the blog agent."""
    if not registry_path.exists():
        return "- Keine Lernmaterialien-Daten vorhanden. Führe blog/_update_content_registry.py aus."
    text = registry_path.read_text(encoding="utf-8", errors="ignore")
    # Extract only the "Live & indexiert" block — skip the rest (blog post list is already in compact context)
    start = text.find("### Live & indexiert")
    end = text.find("### Noch nicht indexiert")
    if start == -1:
        return "- Keine Live-Lernmaterialien vorhanden."
    snippet = text[start: end if end != -1 else start + 4000].strip()
    # Also append the "Lücken" section if present (blog agent should know what to write next)
    luecken_start = text.find("## Lücken")
    if luecken_start != -1:
        snippet += "\n\n" + text[luecken_start:luecken_start + 1500].strip()
    return snippet


def compact_goal_agent_file(path: Path, max_chars: int = 5000) -> str:
    if not path.exists():
        return "- Keine Goal-Agent-Daten vorhanden."
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return "- Goal-Agent-Datei ist leer."
    return text[:max_chars]


def main() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    strategy = STRATEGY.read_text(encoding="utf-8")
    slugs = all_slugs(registry)

    parts = [
        "# Kompakter Blog-Kontext",
        "",
        "Diese Datei ist automatisch generiert. Lies diese Datei statt der vollständigen Registry/Strategie.",
        "",
        "## Statistik",
        section(registry, "Statistik").replace("## Statistik\n", "").strip(),
        f"- Bekannte Slugs: {len(slugs)}",
        "",
        "## Aktuelle Strategie",
        section(strategy, "Ziel").replace("## Ziel\n", "").strip(),
        "",
        section(strategy, "Content-Richtlinien").strip(),
        "",
        section(strategy, "Themen-Strategie").strip(),
        "",
        "## Letzte Analytics-Learnings",
        *latest_analytics(strategy),
        "",
        "## Goal-Agent-Steuerung",
        "Nutze diese Hinweise nur fuer Themenwahl, Briefing, interne Links und Qualitaet. Der Blog-Agent bleibt reiner Blog-Autor und schreibt keine Practice-/Tool-Seiten.",
        "",
        compact_goal_agent_file(GOAL_AGENT_TASKS),
        "",
        "## Goal-Agent-Guardian",
        compact_goal_agent_file(GOAL_AGENT_GUARDIAN, max_chars=2500),
        "",
        "## Zusatznotizen",
        NOTES.read_text(encoding="utf-8").strip() if NOTES.exists() else "",
        "",
        "## Letzte Artikel",
        "| # | Datum | Slug | Titel | Keywords | Tag | Zusammenfassung |",
        "|---|-------|------|-------|----------|-----|----------------|",
        *latest_article_rows(registry),
        "",
        "## Keyword-Pool",
        section(registry, "Keyword-Pool (noch nicht verwendet)").strip(),
        "",
        "## Bereits verwendete Slugs",
        ", ".join(slugs),
        "",
        "## Image-Prompt-Style",
        section(strategy, "Image-Prompt-Style").strip(),
        "",
        "## Lernmaterialien — vorhandene Simulationen & Trainer",
        "Wenn du einen Artikel zu einem dieser Themen schreibst, verlinke die passende Simulation im Fließtext.",
        "Nutze immer die absolute URL (z.B. `/lernmaterialien/bruchrechnung-trainer.html`).",
        "Schreibe KEINE neuen Simulations-Seiten — das ist Aufgabe des Goal-Agenten.",
        "",
        lernmaterialien_section(CONTENT_REGISTRY),
        "",
    ]
    OUT.write_text("\n".join(part for part in parts if part is not None), encoding="utf-8")
    print(f"[Context] Wrote {OUT.relative_to(REPO_DIR)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
