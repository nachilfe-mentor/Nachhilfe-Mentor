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
    ]
    OUT.write_text("\n".join(part for part in parts if part is not None), encoding="utf-8")
    print(f"[Context] Wrote {OUT.relative_to(REPO_DIR)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
