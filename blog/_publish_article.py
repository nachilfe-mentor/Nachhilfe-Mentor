#!/usr/bin/env python3
"""Publish one structured blog article into the existing static site.

Input: blog/articles/<slug>.json

Claude owns the article quality. This script owns deterministic publishing:
rendering the shared template, inserting the blog card, and updating registry
metadata without rereading or rewriting large files manually in Claude.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


REPO_DIR = Path(__file__).resolve().parents[1]
BLOG_DIR = REPO_DIR / "blog"
ARTICLES_DIR = BLOG_DIR / "articles"
POSTS_DIR = BLOG_DIR / "posts"
IMG_DIR = POSTS_DIR / "img"
TEMPLATE = BLOG_DIR / "_template.html"
INDEX = BLOG_DIR / "index.html"
REGISTRY = BLOG_DIR / "_BLOG_REGISTRY.md"

REQUIRED = {
    "slug",
    "title",
    "meta_description",
    "keywords",
    "tag",
    "subtitle",
    "excerpt",
    "image_alt",
    "content_html",
    "registry_summary",
}

MONTHS_DE = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def fail(message: str) -> None:
    print(f"[Publish] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_article(slug: str) -> dict[str, Any]:
    path = ARTICLES_DIR / f"{slug}.json"
    if not path.exists():
        fail(f"Missing article JSON: {path.relative_to(REPO_DIR)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path.relative_to(REPO_DIR)}: {exc}")
    missing = sorted(REQUIRED - set(data))
    if missing:
        fail(f"Missing required field(s): {', '.join(missing)}")
    return data


def normalize_slug(slug: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        fail("slug must be lowercase ASCII words separated by hyphens")
    return slug


def as_text(value: Any, field: str) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item).strip() for item in value if str(item).strip())
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty string")
    return value.strip()


def date_labels(value: Any) -> tuple[str, str]:
    iso = str(value or date.today().isoformat())
    try:
        parsed = datetime.strptime(iso, "%Y-%m-%d").date()
    except ValueError:
        fail("date_iso must use YYYY-MM-DD")
    return iso, f"{parsed.day}. {MONTHS_DE[parsed.month]} {parsed.year}"


def existing_titles(registry: str) -> set[str]:
    titles = set()
    for line in registry.splitlines():
        if not line.startswith("| "):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 4 and parts[0].isdigit():
            titles.add(re.sub(r"\s+", " ", parts[3].lower()))
    return titles


def duplicate_guard(slug: str, title: str) -> None:
    post_path = POSTS_DIR / f"{slug}.html"
    registry = REGISTRY.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")
    title_key = re.sub(r"\s+", " ", title.lower().strip())
    if post_path.exists():
        fail(f"Post already exists: {post_path.relative_to(REPO_DIR)}")
    if f"| {slug} |" in registry or f"/blog/posts/{slug}.html" in index:
        fail(f"Slug already exists in registry or index: {slug}")
    if title_key in existing_titles(registry):
        fail(f"Title already exists in registry: {title}")


def estimate_read_time(content_html: str) -> int:
    words = re.findall(r"\b[\wÄÖÜäöüß-]+\b", re.sub(r"<[^>]+>", " ", content_html))
    return max(3, round(len(words) / 180))


def render_post(data: dict[str, Any]) -> Path:
    slug = normalize_slug(as_text(data["slug"], "slug"))
    title = as_text(data["title"], "title")
    duplicate_guard(slug, title)

    content_html = as_text(data["content_html"], "content_html")
    date_iso, date_de = date_labels(data.get("date_iso"))
    read_time = str(data.get("read_time") or estimate_read_time(content_html))
    image_filename = str(data.get("image_filename") or slug).strip()
    image_path = IMG_DIR / f"{image_filename}.webp"
    if not image_path.exists():
        fail(f"Missing cover image: {image_path.relative_to(REPO_DIR)}")

    replacements = {
        "{{TITLE}}": title,
        "{{META_DESCRIPTION}}": as_text(data["meta_description"], "meta_description"),
        "{{KEYWORDS}}": as_text(data["keywords"], "keywords"),
        "{{IMAGE_FILENAME}}": image_filename,
        "{{SLUG}}": slug,
        "{{TAG}}": html.escape(as_text(data["tag"], "tag")),
        "{{DATE_ISO}}": date_iso,
        "{{DATE_DE}}": date_de,
        "{{READ_TIME}}": read_time,
        "{{H1_TITLE}}": as_text(data.get("h1_title") or title, "h1_title"),
        "{{SUBTITLE}}": as_text(data["subtitle"], "subtitle"),
        "{{IMAGE_ALT}}": as_text(data["image_alt"], "image_alt"),
        "{{CONTENT}}": content_html.strip(),
    }

    html_text = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        html_text = html_text.replace(placeholder, value)
    leftovers = re.findall(r"{{[A-Z0-9_]+}}", html_text)
    if leftovers:
        fail(f"Unfilled template placeholder(s): {', '.join(sorted(set(leftovers)))}")

    out_path = POSTS_DIR / f"{slug}.html"
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


def blog_card(data: dict[str, Any]) -> str:
    slug = as_text(data["slug"], "slug")
    date_iso, date_de = date_labels(data.get("date_iso"))
    image_filename = str(data.get("image_filename") or slug).strip()
    return f'''      <a href="/blog/posts/{slug}.html" class="blog-card animate-up">
        <div class="blog-card-img">
          <img src="/blog/posts/img/{html.escape(image_filename)}.webp" alt="{html.escape(as_text(data["image_alt"], "image_alt"))}" loading="lazy">
        </div>
        <div class="blog-card-body">
          <div class="blog-card-meta">
            <span class="blog-tag">{html.escape(as_text(data["tag"], "tag"))}</span>
            <time datetime="{date_iso}">{date_de}</time>
          </div>
          <h2 class="blog-card-title">{html.escape(as_text(data["title"], "title"))}</h2>
          <p class="blog-card-excerpt">{html.escape(as_text(data["excerpt"], "excerpt"))}</p>
          <span class="blog-read-more">Weiterlesen
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </span>
        </div>
      </a>
'''


def update_index(data: dict[str, Any]) -> None:
    slug = as_text(data["slug"], "slug")
    text = INDEX.read_text(encoding="utf-8")
    if f"/blog/posts/{slug}.html" in text:
        fail(f"Index already contains slug: {slug}")
    marker = "      <!-- Neue Posts werden hier automatisch eingefügt -->"
    if marker not in text:
        fail("Blog index insertion marker not found")
    text = text.replace(marker, marker + "\n\n" + blog_card(data), 1)
    INDEX.write_text(text, encoding="utf-8")


def next_article_number(registry: str) -> int:
    match = re.search(r"- Gesamtzahl Artikel:\s*(\d+)", registry)
    if not match:
        fail("Could not find article count in registry")
    return int(match.group(1)) + 1


def update_registry(data: dict[str, Any]) -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    slug = as_text(data["slug"], "slug")
    if f"| {slug} |" in registry:
        fail(f"Registry already contains slug: {slug}")

    number = next_article_number(registry)
    date_iso, _ = date_labels(data.get("date_iso"))
    keywords = as_text(data["keywords"], "keywords")
    row = (
        f"| {number} | {date_iso} | {slug} | {as_text(data['title'], 'title')} | "
        f"{keywords} | {as_text(data['tag'], 'tag')} | {as_text(data['registry_summary'], 'registry_summary')} |"
    )

    registry = re.sub(r"- Gesamtzahl Artikel:\s*\d+", f"- Gesamtzahl Artikel: {number}", registry, count=1)
    registry = re.sub(r"- Letzte Veröffentlichung:\s*\d{4}-\d{2}-\d{2}", f"- Letzte Veröffentlichung: {date_iso}", registry, count=1)
    header = "|---|-------|------|-------|----------|-----|----------------|\n"
    if header not in registry:
        fail("Registry article table header not found")
    registry = registry.replace(header, header + row + "\n", 1)

    link_lines: list[str] = []
    for key in ("internal_links", "backlinks"):
        for item in data.get(key, []) or []:
            if isinstance(item, str):
                link_lines.append(f"- {item}")
            elif isinstance(item, dict):
                source = item.get("source") or item.get("from") or slug
                target = item.get("target") or item.get("to")
                note = item.get("note") or item.get("anchor") or ""
                if source and target:
                    suffix = f" ({note})" if note else ""
                    link_lines.append(f"- {source} -> {target}{suffix}")
    if link_lines:
        registry = registry.rstrip() + f"\n\n## Interne Verlinkungen (Artikel {number})\n" + "\n".join(link_lines) + "\n"

    REGISTRY.write_text(registry, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--check", action="store_true", help="Validate input without writing output")
    args = parser.parse_args()

    slug = normalize_slug(args.slug)
    data = read_article(slug)
    if normalize_slug(as_text(data["slug"], "slug")) != slug:
        fail("JSON slug does not match CLI slug")

    duplicate_guard(slug, as_text(data["title"], "title"))
    content_html = as_text(data["content_html"], "content_html")
    if len(re.findall(r"\b[\wÄÖÜäöüß-]+\b", re.sub(r"<[^>]+>", " ", content_html))) < 700:
        fail("content_html looks too short; expected at least 700 words")
    if args.check:
        print(f"[Publish] OK: {slug} is valid")
        return

    out = render_post(data)
    update_index(data)
    update_registry(data)
    print(f"[Publish] Created {out.relative_to(REPO_DIR)}")
    print("[Publish] Updated blog/index.html and blog/_BLOG_REGISTRY.md")


if __name__ == "__main__":
    main()
