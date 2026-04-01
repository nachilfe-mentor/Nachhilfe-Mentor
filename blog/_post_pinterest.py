#!/usr/bin/env python3
"""
Pinterest Pin fuer einen neuen Blogartikel erstellen.
=====================================================
Nutzt die Postiz-API um das Blog-Headerbild als Pin zu posten
mit SEO-optimierter Beschreibung und Link zum Artikel.

Nutzung:
  python3 blog/_post_pinterest.py <SLUG> "<TITEL>" "<BESCHREIBUNG>"

Beispiel:
  python3 blog/_post_pinterest.py pomodoro-technik-lernen \
    "Pomodoro-Technik: Mit dem Tomaten-Timer endlich fokussiert lernen" \
    "Erfahre, wie die Pomodoro-Technik funktioniert und warum 25-Minuten-Bloecke deine Konzentration steigern."

Wird automatisch vom auto-blog.sh Agent nach jedem neuen Artikel aufgerufen.
"""

import sys
import json
import os
import mimetypes
import urllib.request
import urllib.error

POSTIZ_API_KEY = "0e2a2a6b9fca79305409ccdfabb17ea5c631b762416a64fd2ebb02e21bf7c22e"
POSTIZ_BASE_URL = "https://api.postiz.com/public/v1"
PINTEREST_ID = "cmng2dk8p04p2pn0ygk520i1p"
SITE_URL = "https://nachhilfe-mentor.de"
BLOG_DIR = "/home/opc/Nachhilfe-Mentor/blog/posts"


def postiz_request(method, endpoint, data=None, headers=None):
    """Sendet einen Request an die Postiz-API."""
    url = f"{POSTIZ_BASE_URL}{endpoint}"
    h = {"Authorization": POSTIZ_API_KEY}
    if headers:
        h.update(headers)

    if data and isinstance(data, dict):
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    elif data:
        body = data
    else:
        body = None

    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[Pinterest] API-Fehler: {e.code} {e.reason} - {error_body}")
        return None
    except Exception as e:
        print(f"[Pinterest] Request fehlgeschlagen: {e}")
        return None


def upload_image(file_path):
    """Laedt ein Bild zur Postiz-API hoch und gibt die Media-URL zurueck."""
    if not os.path.exists(file_path):
        print(f"[Pinterest] Bild nicht gefunden: {file_path}")
        return None

    mime_type = mimetypes.guess_type(file_path)[0] or "image/png"
    filename = os.path.basename(file_path)

    # Multipart form-data erstellen
    boundary = "----PinterestUploadBoundary2026"
    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{POSTIZ_BASE_URL}/media/upload-simple"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", POSTIZ_API_KEY)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            # Postiz gibt verschiedene Formate zurueck
            if isinstance(result, dict):
                return result.get("url") or result.get("path") or result.get("id")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[Pinterest] Upload-Fehler: {e.code} {e.reason} - {error_body}")
        return None
    except Exception as e:
        print(f"[Pinterest] Upload fehlgeschlagen: {e}")
        return None


def create_pin(image_url, title, description, link):
    """Erstellt einen Pinterest-Pin ueber die Postiz-API."""
    payload = {
        "type": "social",
        "integrationId": [PINTEREST_ID],
        "content": description,
        "title": title[:100],  # Pinterest max 100 Zeichen Titel
        "image": [image_url] if image_url else [],
        "settings": {
            "pinterest": {
                "link": link,
            }
        },
    }

    result = postiz_request("POST", "/posts", data=payload)
    if result:
        post_id = result.get("id", "?")
        print(f"[Pinterest] Pin erstellt! Post-ID: {post_id}")
        return post_id
    return None


def main():
    if len(sys.argv) < 4:
        print("Nutzung: python3 _post_pinterest.py <SLUG> \"<TITEL>\" \"<BESCHREIBUNG>\"")
        sys.exit(1)

    slug = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]

    # Bild finden (webp oder png)
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
    print("[Pinterest] Lade Bild hoch...")
    image_url = upload_image(image_path)
    if not image_url:
        print("[Pinterest] Bild-Upload fehlgeschlagen, breche ab.")
        sys.exit(1)
    print(f"[Pinterest] Bild hochgeladen: {image_url}")

    # 2. Pin erstellen
    print("[Pinterest] Erstelle Pin...")
    # Pinterest-Beschreibung: SEO-optimiert, 2-3 Saetze + Hashtags
    pin_description = (
        f"{description}\n\n"
        f"Jetzt lesen: {link}\n\n"
        f"#Lerntipps #Schule #Studium #NachhilfeMentor #Lernen #Lernmethoden"
    )

    post_id = create_pin(image_url, title, pin_description, link)
    if post_id:
        print(f"[Pinterest] Erfolgreich! Pin-ID: {post_id}")
    else:
        print("[Pinterest] Pin-Erstellung fehlgeschlagen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
