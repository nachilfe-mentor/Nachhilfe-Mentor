#!/usr/bin/env python3
"""
Content Registry — builds a bidirectional index of blog posts and learning tools.

Run after every blog cycle and after every simulation creation.
Output: goal_agent/exports/content_registry_compact.md

Both the Blog Agent and the Goal Agent read this file to find cross-link targets.
Blog Agent: gets a list of available simulations to link from blog articles.
Goal Agent: gets a list of existing blog posts to link from new simulations.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOG_ARTICLES = REPO_ROOT / "blog" / "articles"
LERNMATERIALIEN = REPO_ROOT / "lernmaterialien"
OUT = REPO_ROOT / "goal_agent" / "exports" / "content_registry_compact.md"
BASE_URL = "https://nachhilfe-mentor.de"

# Words too generic to be useful for topic matching
_STOPWORDS = {
    # Verben/Tätigkeiten — zu generisch
    "schreiben", "lernen", "ueben", "üben", "analysieren", "bestimmen", "loesen",
    "lösen", "interpretieren", "beschreiben", "erstellen", "üben", "erkennen",
    "verstehen", "erklären", "erklaeren", "nutzen", "finden", "machen",
    # Substantive — zu generisch
    "tipps", "aufbau", "aufgaben", "aufgabe", "uebung", "übung", "übungen", "uebungen",
    "anleitung", "beispiel", "beispiele", "vorlage", "muster", "fehler", "fehler",
    "schule", "klasse", "schüler", "schueler", "nachhilfe", "mentor", "unterricht",
    "tricks", "hilfe", "guide", "kurs",
    # Adjektive — zu generisch
    "interaktiv", "interaktiver", "interaktive", "kostenlos", "online", "gratis",
    "einfach", "schnell", "automatisch", "vollständig",
    # Artikel/Präpositionen/Konjunktionen
    "und", "die", "der", "das", "ein", "eine", "auf", "ist", "im", "von", "zu",
    "wie", "was", "fuer", "für", "mit", "zum", "zur", "an", "in", "bei", "nach",
    "oder", "als", "auch", "noch", "alle", "alle", "sehr", "nur",
    # Jede einzelne Ziffer und Klassen-Nummern
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
    # Marketing-Floskeln in Titeln
    "nachhilfe mentor", "trainer", "simulator", "simulation", "tool",
}


def _topic_words(text: str) -> set[str]:
    # Nur Buchstaben und Umlaute, keine Ziffern (Klasse 5/6/7 etc. zu unspezifisch)
    cleaned = re.sub(r"[^a-züäöß\s]", " ", text.lower())
    words = set(cleaned.split())
    # Auch einzelne Buchstaben entfernen
    words = {w for w in words if len(w) > 2}
    return words - _STOPWORDS


def load_blog_posts() -> list[dict]:
    posts = []
    for f in sorted(BLOG_ARTICLES.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = data.get("slug", f.stem)
            title = data.get("title", "")
            keywords = data.get("keywords") or []
            date = data.get("date", "")
            words = _topic_words(slug + " " + title + " " + " ".join(keywords))
            posts.append({
                "slug": slug,
                "title": title,
                "url": f"{BASE_URL}/blog/posts/{slug}.html",
                "keywords": keywords,
                "words": words,
                "date": date,
            })
        except Exception:
            pass
    return posts


def _html_meta(html: str) -> dict:
    def _find(pattern: str) -> str:
        m = re.search(pattern, html, re.I | re.S)
        return m.group(1).strip() if m else ""

    return {
        "title": _find(r"<title[^>]*>(.*?)</title>"),
        "description": _find(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']'),
        "robots": _find(r'<meta\s+name=["\']robots["\']\s+content=["\'](.*?)["\']') or "index,follow",
        "canonical": _find(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']'),
        "keywords_raw": _find(r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']'),
    }


def load_simulations() -> list[dict]:
    seen = set()
    sims = []

    scan_dirs = [
        LERNMATERIALIEN,
        LERNMATERIALIEN / "lernsimulationen",
        LERNMATERIALIEN / "deutsch",
        LERNMATERIALIEN / "entwuerfe",
    ]

    for d in scan_dirs:
        if not d.exists():
            continue
        for html_file in sorted(d.glob("*.html")):
            if html_file.name in ("index.html",):
                continue
            slug = html_file.stem
            if slug in seen:
                continue
            seen.add(slug)

            try:
                html = html_file.read_text(encoding="utf-8", errors="replace")
                meta = _html_meta(html)
                is_indexed = "noindex" not in meta["robots"].lower()

                try:
                    rel = html_file.relative_to(REPO_ROOT)
                    url = f"{BASE_URL}/{rel}"
                except ValueError:
                    url = f"{BASE_URL}/lernmaterialien/{html_file.name}"

                words = _topic_words(
                    slug + " " + meta["title"] + " " + meta["description"] + " " + meta["keywords_raw"]
                )

                if "entwuerfe" in str(html_file):
                    status = "Entwurf"
                elif "lernsimulationen" in str(html_file):
                    status = "Prototyp (noindex)" if not is_indexed else "Prototyp"
                elif is_indexed:
                    status = "live"
                else:
                    status = "noindex"

                sims.append({
                    "slug": slug,
                    "title": meta["title"] or slug,
                    "description": meta["description"][:120],
                    "url": url,
                    "path": str(html_file.relative_to(REPO_ROOT)),
                    "words": words,
                    "status": status,
                    "is_indexed": is_indexed,
                })
            except Exception:
                pass

    return sims


def _related(words: set[str], pool: list[dict], max_results: int = 4) -> list[dict]:
    scored = []
    for item in pool:
        overlap = len(words & item["words"])
        if overlap > 0:
            scored.append((overlap, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_results]]


def build_registry_md(blog_posts: list[dict], simulations: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    live_sims = [s for s in simulations if s["is_indexed"]]
    draft_sims = [s for s in simulations if not s["is_indexed"]]

    lines: list[str] = [
        "# Content Registry — nachhilfe-mentor.de",
        f"Stand: {now} UTC | Autogeneriert von blog/_update_content_registry.py",
        "",
        "## Verwendung",
        "- **Blog-Agent**: Wenn du einen Artikel zu einem Thema schreibst und eine passende Simulation existiert,",
        "  verlinke sie im Fließtext (URL direkt aus dieser Liste nutzen). Z.B. für Bruchrechnung:",
        "  `<a href=\"/lernmaterialien/bruchrechnung-trainer.html\">interaktiver Bruchrechnung-Trainer</a>`",
        "- **Goal-Agent / Coding-Tasks**: Wenn du eine neue Simulation baust, prüfe ob ein passender Blog-Artikel",
        "  existiert und verlinke ihn unter 'Weiterführende Artikel'. Wenn kein Artikel existiert:",
        "  erstelle einen Blog-Task in `goal_agent/exports/blog_task_snapshot.md`.",
        "",
    ]

    # === SIMULATIONS ===
    lines.append(f"## Lernmaterialien ({len(live_sims)} live, {len(draft_sims)} Entwürfe/Prototypen)")
    lines.append("")

    if live_sims:
        lines.append("### Live & indexiert — für interne Links nutzbar")
        lines.append("")
        for sim in live_sims:
            related = _related(sim["words"], blog_posts)
            lines.append(f"#### {sim['title']}")
            lines.append(f"- URL: `{sim['url']}`")
            lines.append(f"- Pfad: `{sim['path']}`")
            if related:
                lines.append(f"- Passende Blog-Artikel: " + ", ".join(f"`{p['slug']}`" for p in related))
            else:
                lines.append("- Passende Blog-Artikel: **KEINER GEFUNDEN** — Blog-Agent sollte Artikel zu diesem Thema erstellen")
            lines.append("")

    if draft_sims:
        lines.append("### Noch nicht indexiert (Entwürfe / Prototypen)")
        for sim in draft_sims:
            lines.append(f"- `{sim['path']}` — {sim['status']} — {sim['title'][:60]}")
        lines.append("")

    # === BLOG POSTS grouped by topic ===
    lines.append(f"## Blog-Artikel ({len(blog_posts)} gesamt)")
    lines.append("")
    lines.append("Alle verfügbaren Slugs für interne Links — nach Themenbereich:")
    lines.append("")

    clusters = {
        "Mathe": {"mathe", "mathematik", "gleichung", "bruch", "geometrie", "algebra", "rechnen", "zahlen"},
        "Informatik/Python": {"python", "informatik", "programmieren", "coding"},
        "Naturwissenschaften": {"chemie", "physik", "biologie", "galvanisch", "teilchen", "atom"},
        "Deutsch — Schreiben": {"erzaehlung", "aufsatz", "gedicht", "brief", "bericht", "geschichte", "text"},
        "Deutsch — Analyse": {"analyse", "interpretation", "karikatur", "sachtextanalyse", "filmanalyse"},
        "Abitur-Vorbereitung": {"abitur"},
        "Sprachen": {"englisch", "franzoesisch", "spanisch", "latein", "japanisch", "vokabel"},
    }

    used_slugs: set[str] = set()
    for cluster_name, cluster_words in clusters.items():
        matches = [p for p in blog_posts if cluster_words & p["words"] and p["slug"] not in used_slugs]
        if matches:
            lines.append(f"**{cluster_name}:**")
            lines.append(", ".join(f"`{p['slug']}`" for p in matches))
            lines.append("")
            for p in matches:
                used_slugs.add(p["slug"])

    rest = [p for p in blog_posts if p["slug"] not in used_slugs]
    if rest:
        lines.append("**Sonstige:**")
        lines.append(", ".join(f"`{p['slug']}`" for p in rest))
        lines.append("")

    # === LÜCKEN / MISSING ===
    missing_blog = [s for s in live_sims if not _related(s["words"], blog_posts)]
    missing_sims_for = []
    # Simulations topics that could be built (topics with blog posts but no sim)
    # (intentionally light — just flags obvious Mathe/Natur gaps)

    if missing_blog:
        lines.append("## Lücken — fehlende Blog-Artikel zu vorhandenen Simulationen")
        lines.append("")
        lines.append("Diese Simulationen haben keinen passenden Blog-Artikel. Blog-Agent: Artikel zu diesen Themen erstellen.")
        for sim in missing_blog:
            lines.append(f"- Simulation: `{sim['path']}` → Artikel fehlt für Thema: {sim['slug'].replace('-', ' ')}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    blog_posts = load_blog_posts()
    simulations = load_simulations()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    md = build_registry_md(blog_posts, simulations)
    OUT.write_text(md, encoding="utf-8")

    live = sum(1 for s in simulations if s["is_indexed"])
    print(f"[Registry] {len(blog_posts)} Blog-Artikel, {len(simulations)} Simulationen ({live} live) → {OUT.relative_to(REPO_ROOT)} ({OUT.stat().st_size} Bytes)")


if __name__ == "__main__":
    main()
