#!/usr/bin/env python3
"""
SEO-Automatisierung fuer nachhilfe-mentor.de
=============================================
Generiert sitemap.xml und feed.xml aus den vorhandenen HTML-Dateien,
submitted dann an IndexNow (Bing, Yandex, etc.).

Nutzung:
  python3 blog/_update_seo.py                # Alles: Sitemap + Feed + IndexNow
  python3 blog/_update_seo.py --no-ping      # Nur generieren, nicht submitten

Wird automatisch vom Blog-Agent nach jedem neuen Post aufgerufen.
"""

import os
import re
import sys
import glob
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

SITE_URL = "https://nachhilfe-mentor.de"
SITE_DIR = "/home/opc/Nachhilfe-Mentor"
SITEMAP_PATH = os.path.join(SITE_DIR, "sitemap.xml")
FEED_PATH = os.path.join(SITE_DIR, "feed.xml")
INDEXNOW_KEY = "nachhilfementor2026indexnow"


def get_lastmod(filepath):
    """Gibt das Aenderungsdatum einer Datei als YYYY-MM-DD zurueck."""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def get_rfc822_date(filepath):
    """Gibt das Aenderungsdatum als RFC 822 fuer RSS zurueck."""
    mtime = os.path.getmtime(filepath)
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def extract_meta(filepath, attr_name):
    """Extrahiert einen meta-Tag Wert aus dem HTML Head."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(8000)
        # name="..." content="..."
        pattern = rf'<meta\s+(?:name|property)="{re.escape(attr_name)}"\s+content="([^"]*)"'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        # content="..." name="..."
        pattern = rf'content="([^"]*)"\s+(?:name|property)="{re.escape(attr_name)}"'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return ""


def extract_title(filepath):
    """Extrahiert den <title> Tag."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4000)
        match = re.search(r"<title>([^<]+)</title>", content)
        if match:
            title = match.group(1)
            title = re.sub(r"\s*[\u2013\u2014–—]\s*Nachhilfe Mentor.*$", "", title)
            return title.strip()
    except Exception:
        pass
    return ""


def extract_category(filepath):
    """Extrahiert Kategorie aus blog-tag span."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(10000)
        match = re.search(r'class="blog-tag[^"]*">([^<]+)<', content)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return "Lerntipps"


def has_noindex(filepath):
    """Prueft ob eine Seite ein noindex-Tag hat."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            head = f.read(3000)
        return bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', head))
    except Exception:
        return False


def scan_pages():
    """Scannt alle HTML-Seiten und kategorisiert sie."""
    pages = {
        "main": [],
        "blog_index": None,
        "blog_posts": [],
        "legal": [],
    }

    # Hauptseite
    index = os.path.join(SITE_DIR, "index.html")
    if os.path.exists(index):
        pages["main"].append(("", index, 1.0, "weekly"))

    # Blog-Index
    blog_index = os.path.join(SITE_DIR, "blog", "index.html")
    if os.path.exists(blog_index):
        pages["blog_index"] = ("blog/", blog_index, 0.9, "daily")

    # Blog-Artikel in blog/posts/
    posts_dir = os.path.join(SITE_DIR, "blog", "posts")
    if os.path.isdir(posts_dir):
        for f in sorted(glob.glob(os.path.join(posts_dir, "*.html"))):
            basename = os.path.basename(f)
            path = f"blog/posts/{basename}"
            pages["blog_posts"].append((path, f, 0.7, "monthly"))

    # Legal-Seiten (nur wenn KEIN noindex-Tag)
    legal_pages = [
        "impressum.html",
        "datenschutzerklaerung.html",
        "nutzungsbedingungen.html",
        "apps-privacy.html",
        "loesche-deinen-account.html",
        "plantscan-legal.html",
        "plantscan-terms.html",
    ]
    for name in legal_pages:
        f = os.path.join(SITE_DIR, name)
        if os.path.exists(f) and not has_noindex(f):
            pages["legal"].append((name, f, 0.3, "yearly"))

    return pages


def generate_sitemap(pages):
    """Generiert sitemap.xml."""
    urls = []

    all_pages = pages["main"][:]
    if pages["blog_index"]:
        all_pages.append(pages["blog_index"])
    all_pages.extend(pages["blog_posts"])
    all_pages.extend(pages["legal"])

    for path, filepath, priority, changefreq in all_pages:
        loc = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
        lastmod = get_lastmod(filepath)
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"[SEO] sitemap.xml generiert: {len(urls)} URLs")
    return len(urls)


def generate_feed(pages):
    """Generiert feed.xml (RSS 2.0) aus den Blog-Artikeln."""
    now = datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    blog_pages = sorted(
        pages["blog_posts"],
        key=lambda p: os.path.getmtime(p[1]),
        reverse=True,
    )

    for path, filepath, _, _ in blog_pages[:20]:
        title = extract_title(filepath)
        description = extract_meta(filepath, "description")
        category = extract_category(filepath)
        pub_date = get_rfc822_date(filepath)
        link = f"{SITE_URL}/{path}"

        # XML-Escape
        title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        description = description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        items.append(
            f"    <item>\n"
            f"      <title>{title}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid>{link}</guid>\n"
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"      <description>{description}</description>\n"
            f"      <category>{category}</category>\n"
            f"    </item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>Nachhilfe Mentor Blog</title>\n"
        f"    <link>{SITE_URL}/blog/</link>\n"
        "    <description>Lerntipps, Lernmethoden und Strategien fuer Schueler und Studenten</description>\n"
        "    <language>de-de</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(items)
        + "\n  </channel>\n"
        "</rss>\n"
    )

    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"[SEO] feed.xml generiert: {len(items)} Artikel")
    return len(items)


def submit_indexnow(changed_urls):
    """Submitted URLs an IndexNow (Bing, Yandex, etc.)."""
    if not changed_urls:
        print("[SEO] IndexNow: Keine URLs zum Submitten")
        return True

    key_file = os.path.join(SITE_DIR, f"{INDEXNOW_KEY}.txt")
    if not os.path.exists(key_file):
        with open(key_file, "w") as f:
            f.write(INDEXNOW_KEY)
        print(f"[SEO] IndexNow Key-Datei erstellt: {INDEXNOW_KEY}.txt")

    payload = json.dumps({
        "host": "nachhilfe-mentor.de",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": changed_urls[:10000],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=payload,
            method="POST",
        )
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("User-Agent", "NachhilfeMentor-SEO-Bot/1.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            print(f"[SEO] IndexNow: HTTP {status} - {len(changed_urls)} URLs submitted")
            return status in (200, 202)
    except urllib.error.HTTPError as e:
        print(f"[SEO] IndexNow HTTP-Fehler: {e.code} {e.reason}")
        return False
    except Exception as e:
        print(f"[SEO] IndexNow fehlgeschlagen: {e}")
        return False


def main():
    no_ping = "--no-ping" in sys.argv

    print(f"[SEO] Starte SEO-Update fuer {SITE_URL}")
    print(f"[SEO] Scanne {SITE_DIR}...")

    pages = scan_pages()
    url_count = generate_sitemap(pages)
    article_count = generate_feed(pages)

    if not no_ping:
        all_urls = [f"{SITE_URL}/{p[0]}" for p in pages["blog_posts"]]
        all_urls.append(f"{SITE_URL}/")
        if pages["blog_index"]:
            all_urls.append(f"{SITE_URL}/blog/")
        print(f"[SEO] Submitte {len(all_urls)} URLs an IndexNow (Bing, Yandex, etc.)...")
        submit_indexnow(all_urls)
        print("[SEO] Google erkennt Aenderungen automatisch ueber sitemap.xml + robots.txt")
    else:
        print("[SEO] IndexNow-Submit uebersprungen (--no-ping)")

    print(f"[SEO] Fertig! {url_count} URLs in Sitemap, {article_count} Artikel im Feed.")


if __name__ == "__main__":
    main()
