#!/usr/bin/env python3
"""
Pinterest Pin fuer einen neuen Blogartikel erstellen.
=====================================================
Nutzt die Postiz-API (gleicher Mechanismus wie der Elternkanal-Agent)
um das Blog-Headerbild als Pin zu posten mit Link zum Artikel.

Nutzung:
  python3 blog/_post_pinterest.py <SLUG> "<TITEL>" "<BESCHREIBUNG>"

Beispiel:
  python3 blog/_post_pinterest.py pomodoro-technik-lernen \
    "Pomodoro-Technik: Mit dem Tomaten-Timer fokussiert lernen" \
    "Erfahre, wie die Pomodoro-Technik funktioniert."

Wird automatisch vom auto-blog.sh Agent nach jedem neuen Artikel aufgerufen.
"""

import sys
import json
import os
from datetime import datetime, timezone

import requests

POSTIZ_API_KEY = "0e2a2a6b9fca79305409ccdfabb17ea5c631b762416a64fd2ebb02e21bf7c22e"
POSTIZ_BASE_URL = "https://api.postiz.com/public/v1"
PINTEREST_ID = "cmng2dk8p04p2pn0ygk520i1p"
SITE_URL = "https://nachhilfe-mentor.de"
BLOG_DIR = "/home/opc/Nachhilfe-Mentor/blog/posts"

# Pinterest Board ID — kann leer bleiben, Postiz nutzt dann das Default-Board
PINTEREST_BOARD = "1088534241125391299"

MIME_TYPES = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def auth_headers(extra=None):
    h = {"Authorization": POSTIZ_API_KEY}
    if extra:
        h.update(extra)
    return h


def upload_image(file_path):
    """Laedt ein Bild zur Postiz-API hoch (multipart/form-data)."""
    ext = os.path.splitext(file_path)[1].lower()
    mime = MIME_TYPES.get(ext, "image/png")
    filename = os.path.basename(file_path)

    print(f"[Pinterest] Uploading {filename} ({mime})...")
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{POSTIZ_BASE_URL}/upload",
            headers={"Authorization": POSTIZ_API_KEY},
            files={"file": (filename, f, mime)},
            timeout=60,
        )

    if resp.status_code not in (200, 201):
        print(f"[Pinterest] Upload-Fehler: {resp.status_code} {resp.text[:300]}")
        return None

    result = resp.json()
    print(f"[Pinterest] Upload OK: id={result.get('id')}")
    return result


def create_pin(image_ref, title, description, link):
    """Erstellt einen Pinterest-Pin (exakt gleiches Format wie Elternkanal-Agent)."""
    settings = {
        "__type": "pinterest",
        "title": title[:100],
    }
    if link:
        settings["link"] = link
    if PINTEREST_BOARD:
        settings["board"] = PINTEREST_BOARD

    post_entry = {
        "integration": {"id": PINTEREST_ID},
        "value": [{"content": description, "image": [image_ref]}],
        "settings": settings,
    }

    payload = {
        "type": "now",
        "date": datetime.now(timezone.utc).isoformat(),
        "shortLink": False,
        "tags": [],
        "posts": [post_entry],
    }

    resp = requests.post(
        f"{POSTIZ_BASE_URL}/posts",
        headers=auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        print(f"[Pinterest] Post-Fehler: {resp.status_code} {resp.text[:300]}")
        return None

    result = resp.json()
    if isinstance(result, list) and len(result) > 0:
        post_id = result[0].get("id", "?")
    elif isinstance(result, dict):
        post_id = result.get("id", "?")
    else:
        post_id = str(result)[:50]
    print(f"[Pinterest] Pin erstellt! Post-ID: {post_id}")
    return post_id


def main():
    if len(sys.argv) < 4:
        print('Nutzung: python3 _post_pinterest.py <SLUG> "<TITEL>" "<BESCHREIBUNG>"')
        sys.exit(1)

    slug = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]

    # Bild finden
    image_path = None
    for ext in ["webp", "png", "jpg"]:
        candidate = os.path.join(BLOG_DIR, "img", f"{slug}.{ext}")
        if os.path.exists(candidate):
            image_path = candidate
            break

    if not image_path:
        print(f"[Pinterest] Kein Bild gefunden fuer Slug: {slug}")
        print(f"[Pinterest] Gesucht in: {BLOG_DIR}/img/{slug}.[webp|png|jpg]")
        sys.exit(1)

    link = f"{SITE_URL}/blog/posts/{slug}.html"

    print(f"[Pinterest] Erstelle Pin fuer: {title}")
    print(f"[Pinterest] Bild: {image_path}")
    print(f"[Pinterest] Link: {link}")

    # 1. Bild hochladen
    upload_result = upload_image(image_path)
    if not upload_result or "id" not in upload_result:
        print("[Pinterest] Bild-Upload fehlgeschlagen, breche ab.")
        sys.exit(1)

    image_ref = {"id": upload_result["id"], "path": upload_result["path"]}

    # 2. Pin erstellen mit SEO-Beschreibung
    pin_description = (
        f"{description}\n\n"
        f"Jetzt lesen auf nachhilfe-mentor.de\n\n"
        f"#Lerntipps #Schule #Studium #NachhilfeMentor #Lernen #Lernmethoden"
    )

    post_id = create_pin(image_ref, title, pin_description, link)
    if post_id:
        print(f"[Pinterest] Erfolgreich! Pin-ID: {post_id}")
    else:
        print("[Pinterest] Pin-Erstellung fehlgeschlagen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
