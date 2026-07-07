#!/usr/bin/env bash
# Usage: ./_fetch-gsc-signals.sh
# Fetches Google Search Console data and outputs a structured signal report:
#   1) Kannibalisierung: eigene Themen, bei denen mehrere Seiten um dieselbe
#      Query konkurrieren (Warnsignal fuer Doppelcontent).
#   2) CTR-Schwachstellen: Seiten mit hohen Impressions aber ungewoehnlich
#      niedriger Klickrate fuer ihre Position (Title/Meta-Problem).
#   3) Content-Gaps: Queries mit hohen Impressions aber schwacher Position,
#      die auf fehlenden oder zu schwachen Content hindeuten.
#
# Der Blog-Agent liest diesen Report VOR der Themenwahl und MUSS ihn
# gegenueber neuem Content priorisieren (siehe auto-blog.sh Schritt 2).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SA_KEY="$REPO_DIR/gsc-sa.json"
SITE_URL="https://nachhilfe-mentor.de/"

python3 << PYEOF
import json, urllib.request
from datetime import date, timedelta
from urllib.parse import quote
from collections import defaultdict

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
except ImportError:
    print("FEHLER: google-auth nicht installiert. Bitte: pip3 install google-auth")
    raise SystemExit(1)

SITE = "$SITE_URL"
try:
    creds = service_account.Credentials.from_service_account_file(
        "$SA_KEY", scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    creds.refresh(Request())
except Exception as exc:
    print(f"(GSC nicht verfuegbar: {exc.__class__.__name__}. Ueberspringe GSC-Signale.)")
    raise SystemExit(0)

def query(payload):
    site = quote(SITE, safe="")
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {creds.token}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())

end = date.today() - timedelta(days=2)
start = end - timedelta(days=90)

print("=" * 70)
print(f"GSC SIGNAL REPORT — {date.today().isoformat()} (Datenbasis: {start} .. {end})")
print("=" * 70)

body = query({"startDate": start.isoformat(), "endDate": end.isoformat(),
              "dimensions": ["query", "page"], "rowLimit": 5000})
rows = body.get("rows", [])

if not rows:
    print("\n(Keine GSC-Daten im Zeitraum. Ueberspringe Signal-Analyse.)")
    raise SystemExit(0)

by_query = defaultdict(list)
for r in rows:
    q, p = r["keys"]
    by_query[q].append((p, r["impressions"], r["clicks"], r["position"]))

# ─── 1. Kannibalisierung ─────────────────────────────────────────────────────
print("\n## 1. KANNIBALISIERUNGS-WARNUNGEN")
print("(Eigene Seiten, die um dieselbe Query konkurrieren — WICHTIG vor jeder Themenwahl pruefen)\n")
found_cannibalization = False
for q, plist in sorted(by_query.items(), key=lambda kv: -sum(x[1] for x in kv[1])):
    pages = {p for p, impr, clk, pos in plist}
    total_impr = sum(x[1] for x in plist)
    if len(pages) >= 2 and total_impr >= 30:
        found_cannibalization = True
        detail = "; ".join(f"{p.rsplit('/',1)[-1]} (pos {pos:.0f}, impr {impr})" for p, impr, clk, pos in plist)
        print(f"- \"{q}\" (impr={total_impr}): {detail}")
if not found_cannibalization:
    print("(Keine relevanten Kannibalisierungsfaelle gefunden.)")

# ─── 2. CTR-Schwachstellen ───────────────────────────────────────────────────
print("\n## 2. CTR-SCHWACHSTELLEN")
print("(Hohe Impressions, aber CTR deutlich unter Erwartung fuer die Position — Title/Meta ueberarbeiten statt neuen Artikel schreiben)\n")
by_page = defaultdict(lambda: {"impr": 0, "clicks": 0, "pos_sum": 0.0, "n": 0})
for r in rows:
    p = r["keys"][1]
    d = by_page[p]
    d["impr"] += r["impressions"]
    d["clicks"] += r["clicks"]
    d["pos_sum"] += r["position"] * r["impressions"]
    d["n"] += 1

def expected_ctr(pos):
    if pos <= 3: return 0.08
    if pos <= 6: return 0.04
    if pos <= 10: return 0.02
    return 0.01

weak = []
for p, d in by_page.items():
    if d["impr"] < 100:
        continue
    avg_pos = d["pos_sum"] / d["impr"]
    ctr = d["clicks"] / d["impr"]
    exp = expected_ctr(avg_pos)
    if ctr < exp * 0.5:
        weak.append((p, d["impr"], d["clicks"], avg_pos, ctr, exp))

weak.sort(key=lambda x: -x[1])
if weak:
    for p, impr, clicks, pos, ctr, exp in weak[:15]:
        print(f"- {p.rsplit('/',1)[-1]:<50} impr={impr:>6} clicks={clicks:>4} pos={pos:.1f} ctr={ctr*100:.2f}% (erwartet ~{exp*100:.0f}%)")
else:
    print("(Keine auffaelligen CTR-Schwachstellen gefunden.)")

# ─── 3. Content-Gaps ──────────────────────────────────────────────────────────
print("\n## 3. CONTENT-GAP-KANDIDATEN")
print("(Hohe Impressions, aber schwache Position — moeglicher fehlender oder zu duenner Content. Vor neuem Artikel gegen Registry pruefen, ob das Thema bereits ANDERS abgedeckt ist.)\n")
gaps = []
for q, plist in by_query.items():
    total_impr = sum(x[1] for x in plist)
    best_pos = min(x[3] for x in plist)
    if total_impr >= 60 and best_pos > 12:
        gaps.append((q, total_impr, best_pos))
gaps.sort(key=lambda x: -x[1])
if gaps:
    for q, impr, pos in gaps[:20]:
        print(f"- {q:<45} impr={impr:>6} best_pos={pos:.1f}")
else:
    print("(Keine klaren Content-Gaps gefunden. Bevorzuge Konsolidierung bestehender Top-Seiten statt neuer Artikel.)")

print("\n" + "=" * 70)
PYEOF
