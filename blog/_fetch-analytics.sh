#!/usr/bin/env bash
# Usage: ./_fetch-analytics.sh
# Fetches Google Analytics data for the blog and outputs a structured report.
# The agent reads this output to inform its content strategy.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SA_KEY="$REPO_DIR/google-analytics-sa.json"
PROPERTY_ID="530491605"

export GOOGLE_APPLICATION_CREDENTIALS="$SA_KEY"

python3 << 'PYEOF'
import os, json, sys
from datetime import datetime

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension, OrderBy
except ImportError:
    print("FEHLER: google-analytics-data nicht installiert. Bitte: pip3 install google-analytics-data")
    sys.exit(1)

PROPERTY = "properties/530491605"
client = BetaAnalyticsDataClient()

print("=" * 70)
print(f"BLOG ANALYTICS REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)

# ─── 1. Top-Seiten letzte 30 Tage ────────────────────────────────────────────
print("\n## TOP-SEITEN (letzte 30 Tage)\n")
response = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    dimensions=[Dimension(name="pagePath")],
    metrics=[
        Metric(name="screenPageViews"),
        Metric(name="sessions"),
        Metric(name="averageSessionDuration"),
        Metric(name="bounceRate"),
    ],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
    limit=30
))

print(f"{'Seite':<65} {'Views':>6} {'Sess.':>6} {'Dauer':>7} {'Bounce':>7}")
print("-" * 95)
for row in response.rows:
    page = row.dimension_values[0].value
    if not page.startswith("/blog") and page != "/":
        continue
    views = row.metric_values[0].value
    sessions = row.metric_values[1].value
    duration = f"{float(row.metric_values[2].value):.0f}s"
    bounce = f"{float(row.metric_values[3].value)*100:.0f}%"
    print(f"{page:<65} {views:>6} {sessions:>6} {duration:>7} {bounce:>7}")

# ─── 2. Top-Seiten letzte 7 Tage ─────────────────────────────────────────────
print("\n## TOP-SEITEN (letzte 7 Tage)\n")
response7 = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    dimensions=[Dimension(name="pagePath")],
    metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
    limit=20
))

print(f"{'Seite':<65} {'Views':>6} {'Sess.':>6}")
print("-" * 80)
for row in response7.rows:
    page = row.dimension_values[0].value
    if not page.startswith("/blog") and page != "/":
        continue
    views = row.metric_values[0].value
    sessions = row.metric_values[1].value
    print(f"{page:<65} {views:>6} {sessions:>6}")

# ─── 3. Traffic-Quellen ──────────────────────────────────────────────────────
print("\n## TRAFFIC-QUELLEN (letzte 30 Tage)\n")
src_response = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    dimensions=[Dimension(name="sessionSource")],
    metrics=[Metric(name="sessions")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
    limit=10
))

print(f"{'Quelle':<40} {'Sessions':>8}")
print("-" * 50)
for row in src_response.rows:
    source = row.dimension_values[0].value or "(direct)"
    sessions = row.metric_values[0].value
    print(f"{source:<40} {sessions:>8}")

# ─── 4. Suchbegriffe (falls vorhanden) ───────────────────────────────────────
print("\n## SUCHBEGRIFFE / LANDING PAGES (letzte 30 Tage)\n")
try:
    search_response = client.run_report(RunReportRequest(
        property=PROPERTY,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimensions=[Dimension(name="landingPagePlusQueryString")],
        metrics=[Metric(name="sessions"), Metric(name="screenPageViews")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=15
    ))

    print(f"{'Landing Page':<65} {'Sess.':>6} {'Views':>6}")
    print("-" * 80)
    for row in search_response.rows:
        page = row.dimension_values[0].value
        if not page.startswith("/blog") and page != "/":
            continue
        sessions = row.metric_values[0].value
        views = row.metric_values[1].value
        print(f"{page:<65} {sessions:>6} {views:>6}")
except Exception as e:
    print(f"(Keine Daten verfügbar: {e})")

# ─── 5. Geräte ───────────────────────────────────────────────────────────────
print("\n## GERÄTETYPEN (letzte 30 Tage)\n")
dev_response = client.run_report(RunReportRequest(
    property=PROPERTY,
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    dimensions=[Dimension(name="deviceCategory")],
    metrics=[Metric(name="sessions")],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
))

for row in dev_response.rows:
    device = row.dimension_values[0].value
    sessions = row.metric_values[0].value
    print(f"  {device}: {sessions} Sessions")

# ─── 6. Zusammenfassung für den Agenten ──────────────────────────────────────
print("\n## ZUSAMMENFASSUNG FÜR STRATEGIE-ENTSCHEIDUNGEN\n")

total_views = sum(int(r.metric_values[0].value) for r in response.rows)
blog_views = sum(int(r.metric_values[0].value) for r in response.rows if r.dimension_values[0].value.startswith("/blog"))

print(f"- Gesamt-Pageviews (30 Tage): {total_views}")
print(f"- Blog-Pageviews (30 Tage): {blog_views}")

if response.rows:
    top_page = next((r for r in response.rows if r.dimension_values[0].value.startswith("/blog/posts/")), None)
    if top_page:
        print(f"- Bester Blogartikel: {top_page.dimension_values[0].value} ({top_page.metric_values[0].value} Views)")

print(f"\nHinweis: Wenn es weniger als 50 Gesamt-Views gibt, sind die Daten noch nicht aussagekräftig.")
print(f"In diesem Fall sollte der Agent KEINE strategischen Entscheidungen auf Basis dieser Daten treffen,")
print(f"sondern weiterhin den Keyword-Pool und die Themen-Strategie aus _BLOG_STRATEGY.md nutzen.")

print("\n" + "=" * 70)
PYEOF
