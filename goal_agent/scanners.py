from __future__ import annotations

import hashlib
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import REPO_ROOT


SITE_URL = "https://nachhilfe-mentor.de"


def _read(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text if limit is None else text[:limit]


def _strip_tags(value: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _match(pattern: str, text: str, flags: int = re.I | re.S) -> str:
    found = re.search(pattern, text, flags)
    return html.unescape(found.group(1).strip()) if found else ""


def _url_path_for_file(repo_root: Path, path: Path) -> str:
    rel = path.relative_to(repo_root).as_posix()
    if rel == "index.html":
        return "/"
    return "/" + rel


def _content_type(path: Path) -> str:
    parts = path.parts
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel == "index.html":
        return "landing_page"
    if rel == "blog/index.html":
        return "blog_index"
    if "/blog/posts/" in "/" + rel:
        return "blog_article"
    if rel.startswith("lernmaterialien/"):
        return "interactive_tool"
    if "datenschutz" in rel or "impressum" in rel or "nutzungsbedingungen" in rel:
        return "legal"
    if rel.startswith("Blog/"):
        return "legacy_blog"
    return "static_page"


def infer_topic_cluster(title: str, path: str) -> str:
    text = f"{title} {path}".lower()
    checks = [
        ("schreibaufgaben", ["schreiben", "analyse", "interpretation", "aufsatz", "argumentation", "erörterung", "eroerterung"]),
        ("mathematik", ["mathe", "ableitung", "integral", "stochastik", "gleichung", "vektor", "bruch"]),
        ("pruefungsvorbereitung", ["abitur", "prüfung", "pruefung", "klausur", "klassenarbeit"]),
        ("lernmethoden", ["lernen", "lernplan", "pomodoro", "karteikarten", "spaced", "feynman"]),
        ("ki-und-bildung", ["ki", "chatgpt"]),
        ("motivation", ["motivation", "prokrastination", "disziplin", "lernblockade"]),
        ("sprachen", ["englisch", "französisch", "franzoesisch", "spanisch", "latein"]),
    ]
    for cluster, needles in checks:
        if any(needle in text for needle in needles):
            return cluster
    return "allgemein"


def read_sitemap(repo_root: Path = REPO_ROOT) -> set[str]:
    path = repo_root / "sitemap.xml"
    if not path.exists():
        return set()
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return set()
    urls = set()
    for loc in root.findall(".//{*}loc"):
        if not loc.text:
            continue
        parsed = urlparse(loc.text.strip())
        urls.add(parsed.path or "/")
    return urls


def read_feed(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    path = repo_root / "feed.xml"
    if not path.exists():
        return []
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return []
    items = []
    for item in root.findall(".//item"):
        items.append({
            "title": item.findtext("title", default=""),
            "link": item.findtext("link", default=""),
            "pubDate": item.findtext("pubDate", default=""),
        })
    return items


def scan_content(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    sitemap_paths = read_sitemap(repo_root)
    generated_pages = sorted((repo_root / "lernmaterialien").glob("*.html")) if (repo_root / "lernmaterialien").exists() else []
    html_files = [
        repo_root / "index.html",
        repo_root / "blog" / "index.html",
        *sorted((repo_root / "blog" / "posts").glob("*.html")),
        *[repo_root / name for name in (
            "impressum.html",
            "datenschutzerklaerung.html",
            "nutzungsbedingungen.html",
            "apps-privacy.html",
            "loesche-deinen-account.html",
        )],
        *generated_pages,
    ]
    rows = []
    for path in html_files:
        if not path.exists() or not path.is_file():
            continue
        text = _read(path)
        head = text[:12000]
        url_path = _url_path_for_file(repo_root, path)
        title = _match(r"<title[^>]*>(.*?)</title>", head)
        meta = _match(r'<meta\s+(?:name|property)=["\']description["\']\s+content=["\'](.*?)["\']', head)
        if not meta:
            meta = _match(r'content=["\'](.*?)["\']\s+(?:name|property)=["\']description["\']', head)
        canonical = _match(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', head)
        h1 = _match(r"<h1[^>]*>(.*?)</h1>", text)
        links = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"']", text, flags=re.I)
        internal_links = [link for link in links if link.startswith("/") or link.startswith("https://nachhilfe-mentor.de")]
        external_links = [link for link in links if link.startswith("http") and "nachhilfe-mentor.de" not in link]
        schema_types = re.findall(r'"@type"\s*:\s*"([^"]+)"', text)
        body_text = _strip_tags(text)
        words = re.findall(r"\b[\wÄÖÜäöüß-]+\b", body_text)
        slug = path.stem if path.parent.name == "posts" else ("" if url_path == "/" else path.stem)
        cluster = infer_topic_cluster(title or h1, url_path)
        rows.append({
            "id": hashlib.sha1(url_path.encode("utf-8")).hexdigest(),
            "url_path": url_path,
            "canonical_url": canonical,
            "source_file": path.relative_to(repo_root).as_posix(),
            "content_type": _content_type(path),
            "slug": slug,
            "title": title,
            "meta_description": meta,
            "h1": h1,
            "topic_cluster": cluster,
            "primary_keyword": re.sub(r"\s*[|–—-]\s*Nachhilfe Mentor.*$", "", title).strip().lower()[:120],
            "search_intent": "informational" if "blog/posts" in url_path else "mixed",
            "word_count": len(words),
            "schema_types": sorted(set(schema_types)),
            "internal_link_count": len(internal_links),
            "external_link_count": len(external_links),
            "image_count": len(re.findall(r"<img\b", text, flags=re.I)),
            "is_in_sitemap": url_path in sitemap_paths,
            "lastmod": str(path.stat().st_mtime_ns),
        })
    return rows


def read_blog_registry(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    path = repo_root / "blog" / "_BLOG_REGISTRY.md"
    if not path.exists():
        return {"exists": False, "article_count": 0, "slugs": []}
    text = path.read_text(encoding="utf-8", errors="ignore")
    count_match = re.search(r"Gesamtzahl Artikel:\s*(\d+)", text)
    slugs = re.findall(r"\|\s*\d+\s*\|[^|]*\|\s*([a-z0-9-]+)\s*\|", text)
    return {
        "exists": True,
        "article_count": int(count_match.group(1)) if count_match else len(slugs),
        "slugs": slugs,
        "path": str(path),
    }


@dataclass
class LinkRecord:
    source_url: str
    target_url: str
    anchor_category: str
    link_position: str
    same_cluster: bool
    is_broken: bool


def build_internal_link_graph(content_rows: list[dict[str, Any]], repo_root: Path = REPO_ROOT) -> list[LinkRecord]:
    by_path = {row["url_path"]: row for row in content_rows}
    records: list[LinkRecord] = []
    for row in content_rows:
        source_file = row.get("source_file")
        if not source_file:
            continue
        path = repo_root / source_file
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, match in enumerate(re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, flags=re.I | re.S)):
            href = match.group(1)
            if href.startswith("http") and "nachhilfe-mentor.de" not in href:
                continue
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            target_path = urlparse(href).path if href.startswith("http") else href.split("#", 1)[0]
            if not target_path.startswith("/"):
                base = "/" + str(Path(row["url_path"]).parent / target_path).replace("\\", "/")
                target_path = re.sub(r"/+", "/", base)
            anchor = _strip_tags(match.group(2)).lower()
            category = "cta" if any(x in anchor for x in ["app", "download", "testen"]) else "contextual"
            target = by_path.get(target_path)
            records.append(LinkRecord(
                source_url=row["url_path"],
                target_url=target_path,
                anchor_category=category,
                link_position="early" if idx < 3 else "body",
                same_cluster=bool(target and target.get("topic_cluster") == row.get("topic_cluster")),
                is_broken=target_path not in by_path and target_path != "/",
            ))
    return records
