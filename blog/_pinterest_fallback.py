#!/usr/bin/env python3
"""
Pinterest Fallback: Pinnt alle Blog-Artikel, die noch keinen Pinterest-Pin haben.
Wird als Safety-Fallback nach jedem Blog-Cycle aufgerufen.

Speichert gepinnte Slugs in blog/_pinterest_done.txt um Doppel-Posts zu vermeiden.
"""

import os
import re
import sys
import json
from pathlib import Path

REPO_DIR = Path("/home/opc/Nachhilfe-Mentor")
POSTS_DIR = REPO_DIR / "blog" / "posts"
DONE_FILE = REPO_DIR / "blog" / "_pinterest_done.txt"
POST_PINTEREST = REPO_DIR / "blog" / "_post_pinterest.py"

# Private/system files that are not blog posts
SKIP_PREFIXES = ("_", "index", "404")


def load_done() -> set:
    if DONE_FILE.exists():
        return set(DONE_FILE.read_text().splitlines())
    return set()


def save_done(done: set):
    DONE_FILE.write_text("\n".join(sorted(done)) + "\n")


def extract_meta(html_path: Path) -> tuple[str, str]:
    """Extrahiert Titel und Meta-Description aus einer HTML-Datei."""
    text = html_path.read_text(encoding="utf-8", errors="replace")

    title_match = re.search(r"<title>([^<]+)</title>", text)
    title = title_match.group(1) if title_match else ""
    # Strip trailing " – Nachhilfe Mentor Blog" suffix
    title = re.sub(r"\s*[–-]\s*Nachhilfe Mentor.*$", "", title).strip()

    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', text)
    description = desc_match.group(1) if desc_match else ""

    return title, description


def main():
    done = load_done()
    pinned_count = 0

    posts = sorted(POSTS_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime)

    for post in posts:
        slug = post.stem

        # Skip system/index files
        if any(slug.startswith(p) for p in SKIP_PREFIXES):
            continue

        if slug in done:
            continue

        title, description = extract_meta(post)

        if not title or not description:
            print(f"[Pinterest-Fallback] Überspringe {slug}: kein Titel/keine Description gefunden.")
            done.add(slug)
            continue

        print(f"[Pinterest-Fallback] Pinne: {slug}")
        print(f"  Titel: {title}")
        print(f"  Desc:  {description[:80]}...")

        import subprocess
        result = subprocess.run(
            [sys.executable, str(POST_PINTEREST), slug, title, description],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode == 0:
            done.add(slug)
            pinned_count += 1
            save_done(done)
            print(f"[Pinterest-Fallback] OK: {slug}")
        else:
            print(f"[Pinterest-Fallback] FEHLER bei {slug}: {result.stderr[:200]}")

    if pinned_count == 0:
        print("[Pinterest-Fallback] Nichts zu pinnen - alle Artikel sind bereits auf Pinterest.")
    else:
        print(f"[Pinterest-Fallback] {pinned_count} neue Pin(s) erstellt.")


if __name__ == "__main__":
    main()
