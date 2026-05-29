from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

from .config import Settings
from .privacy import sanitize_properties, validate_event_definition


STANDARD_EVENTS: dict[str, list[str]] = {
    "seo_page_view": ["page_id", "slug", "topic_cluster", "primary_keyword", "search_intent", "content_type", "template_version", "agent_version", "agent_run_id", "experiment_id", "traffic_source", "device_type"],
    "seo_scroll_depth_reached": ["page_id", "slug", "scroll_depth_percent", "topic_cluster", "content_type"],
    "seo_internal_link_clicked": ["page_id", "slug", "target_slug", "target_content_type", "target_topic_cluster", "link_position", "anchor_category"],
    "seo_cta_clicked": ["page_id", "slug", "cta_type", "cta_location", "cta_variant", "destination_type"],
    "seo_app_store_clicked": ["page_id", "slug", "store", "cta_location", "app_variant"],
    "seo_tool_started": ["page_id", "slug", "tool_type", "tool_id", "difficulty_level", "input_mode"],
    "seo_tool_completed": ["page_id", "slug", "tool_type", "tool_id", "difficulty_level", "completion_status", "duration_bucket", "steps_completed_count"],
    "seo_quiz_started": ["page_id", "slug", "quiz_id", "topic_cluster", "difficulty_level", "question_count_bucket"],
    "seo_quiz_completed": ["page_id", "slug", "quiz_id", "difficulty_level", "score_bucket", "completion_status", "duration_bucket"],
    "seo_answer_checked": ["page_id", "slug", "tool_id", "quiz_id", "question_type", "answer_correct", "attempt_number", "answer_length_bucket"],
    "seo_return_visit": ["page_id", "slug", "return_window", "previous_content_type"],
    "practice_started": ["page_id", "slug", "asset_type", "subject", "grade_level", "exam_type", "difficulty", "interaction_type"],
    "practice_completed": ["page_id", "slug", "asset_type", "subject", "grade_level", "exam_type", "difficulty", "score_bucket", "completion_status"],
    "answer_checked": ["page_id", "slug", "asset_type", "question_type", "answer_correct", "attempt_number", "answer_length_bucket"],
    "solution_revealed": ["page_id", "slug", "asset_type", "solution_mode", "question_type"],
    "mistake_detected": ["page_id", "slug", "asset_type", "mistake_type", "difficulty"],
    "retry_clicked": ["page_id", "slug", "asset_type", "attempt_number"],
    "worksheet_generated": ["page_id", "slug", "asset_type", "subject", "grade_level", "difficulty", "worksheet_type"],
    "app_cta_clicked_from_practice": ["page_id", "slug", "asset_type", "subject", "grade_level", "cta_location"],
}


@dataclass(frozen=True)
class ConnectorResult:
    configured: bool
    ok: bool
    summary: dict[str, Any]
    warning: str = ""


def validate_standard_events() -> list[str]:
    problems: list[str] = []
    for event, props in STANDARD_EVENTS.items():
        problems.extend(validate_event_definition(event, props))
    return problems


class PostHogConnector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.host = settings.posthog_host.rstrip("/")
        self.project_id = settings.posthog_project_id
        self.project_key = _secret_from_env_or_file("POSTHOG_PROJECT_API_KEY", settings.env_file_path)
        self.personal_key = _secret_from_env_or_file("POSTHOG_PERSONAL_API_KEY", settings.env_file_path)

    @property
    def configured(self) -> bool:
        return bool(self.project_id and self.personal_key)

    def analyze(self, days: int = 30) -> ConnectorResult:
        if not self.configured:
            return ConnectorResult(False, True, {"events": {}, "missing": sorted(STANDARD_EVENTS)}, "analytics credentials are not configured")
        # Query Events API with an event list only. Never print or return tokens.
        event_counts: dict[str, int] = {}
        for event_name in STANDARD_EVENTS:
            try:
                count = self._count_event(event_name, days)
            except Exception as exc:  # noqa: BLE001 - redacted connector boundary
                detail = str(exc) if str(exc).startswith("http_") else exc.__class__.__name__
                return ConnectorResult(True, False, {"events": event_counts}, f"PostHog query failed: {detail}")
            event_counts[event_name] = count
        missing = [name for name, count in event_counts.items() if count == 0]
        return ConnectorResult(True, True, {"events": event_counts, "missing": missing})

    def _count_event(self, event_name: str, days: int) -> int:
        # HogQL endpoint shape; if API changes, caller receives a redacted failure.
        safe_event = "'" + event_name.replace("\\", "\\\\").replace("'", "\\'") + "'"
        safe_days = max(1, min(int(days), 365))
        payload = {
            "query": {
                "kind": "HogQLQuery",
                "query": f"select count() from events where event = {safe_event} and timestamp >= now() - interval {safe_days} day",
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/projects/{self.project_id}/query/",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.personal_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - configured host only
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"http_{exc.code}") from exc
        results = body.get("results") or [[0]]
        return int(results[0][0] or 0)


def _secret_from_env_or_file(name: str, env_file_path) -> str:
    if os.environ.get(name):
        return os.environ[name]
    try:
        for line in env_file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    except Exception:
        return ""
    return ""


class GSCConnector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyze(self) -> ConnectorResult:
        if not self.settings.gsc_configured:
            return ConnectorResult(False, True, {"queries": [], "missing_env": ["GOOGLE_APPLICATION_CREDENTIALS or GSC_OAUTH_CREDENTIALS", "GSC_SITE_URL"]}, "GSC not configured")
        try:
            rows = self._query_search_analytics()
        except FileNotFoundError:
            return ConnectorResult(True, False, {"queries": []}, "GSC credentials file not found")
        except PermissionError:
            return ConnectorResult(True, False, {"queries": []}, "GSC credentials file is not readable")
        except Exception as exc:  # noqa: BLE001 - connector boundary, no secret details
            detail = str(exc) if str(exc).startswith("http_") else exc.__class__.__name__
            if detail == "http_403":
                return ConnectorResult(True, False, {"queries": []}, "GSC configured, but service account lacks Search Console property access.")
            return ConnectorResult(True, False, {"queries": []}, f"GSC query failed: {detail}")
        return ConnectorResult(True, True, {"queries": rows, "row_count": len(rows)})

    def _query_search_analytics(self, days: int = 28, row_limit: int = 250) -> list[dict[str, Any]]:
        credentials = self._load_credentials()
        credentials.refresh(self._google_request())
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=days)
        payload = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
            "startRow": 0,
        }
        data = json.dumps(payload).encode("utf-8")
        site = quote(self.settings.gsc_site_url, safe="")
        req = urllib.request.Request(
            f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 - Google API endpoint
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"http_{exc.code}") from exc
        return parse_gsc_rows(body)

    def _load_credentials(self):
        mode = self.settings.gsc_auth_mode
        if mode in {"auto", "oauth"} and self.settings.gsc_oauth_credentials:
            try:
                from google.oauth2.credentials import Credentials
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("google_auth_missing") from exc
            return Credentials.from_authorized_user_file(
                self.settings.gsc_oauth_credentials,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
        if mode in {"auto", "service_account"} and self.settings.google_application_credentials:
            try:
                from google.oauth2 import service_account
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("google_auth_missing") from exc
            return service_account.Credentials.from_service_account_file(
                self.settings.google_application_credentials,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
        raise FileNotFoundError("No GSC credentials configured")

    @staticmethod
    def _google_request():
        try:
            from google.auth.transport.requests import Request
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("google_auth_missing") from exc
        return Request()


class SerpConnector:
    def analyze(self) -> ConnectorResult:
        return ConnectorResult(False, True, {"provider": None, "queries": []}, "No SERP provider configured; aggressive scraping is blocked")


def page_conversion_scores(posthog_summary: dict[str, Any]) -> dict[str, Any]:
    # Placeholder until page-level PostHog properties are populated. Sanitized
    # shape keeps the scoring layer independent of raw events.
    return sanitize_properties({"sitewide_conversion_score": 0.35, **posthog_summary})


def parse_gsc_rows(body: dict[str, Any]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for row in body.get("rows", []) or []:
        keys = row.get("keys", []) or []
        parsed.append({
            "query": keys[0] if len(keys) > 0 else "",
            "page": keys[1] if len(keys) > 1 else "",
            "clicks": int(row.get("clicks", 0) or 0),
            "impressions": int(row.get("impressions", 0) or 0),
            "ctr": float(row.get("ctr", 0.0) or 0.0),
            "position": float(row.get("position", 0.0) or 0.0),
        })
    return parsed
