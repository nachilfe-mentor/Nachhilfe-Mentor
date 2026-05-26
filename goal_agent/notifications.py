from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .analytics import GSCConnector
from .config import Settings
from .storage import Database


@dataclass(frozen=True)
class NotificationResult:
    ok: bool
    configured: bool
    channel: str
    message: str


class TelegramNotifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.telegram_enabled and self.settings.telegram_bot_token_present and bool(self.settings.telegram_chat_id)

    def send_text(self, text: str) -> NotificationResult:
        if not self.settings.telegram_enabled:
            return NotificationResult(True, False, "telegram", "Telegram notifications disabled.")
        if not self.settings.telegram_bot_token_present:
            return NotificationResult(False, False, "telegram", "Telegram bot token missing.")
        token = _secret_env("GOAL_AGENT_TELEGRAM_BOT_TOKEN", self.settings)
        if not token:
            return NotificationResult(False, False, "telegram", "Telegram bot token missing.")
        chat_id = self.settings.telegram_chat_id
        if not chat_id:
            try:
                discovered = self._discover_chat_ids(token)
            except RuntimeError as exc:
                return NotificationResult(False, True, "telegram", str(exc))
            if len(discovered) == 1:
                chat_id = discovered[0]
            elif not discovered:
                return NotificationResult(False, False, "telegram", "Telegram chat id missing. Send /start to the bot or configure GOAL_AGENT_TELEGRAM_CHAT_ID.")
            else:
                return NotificationResult(False, False, "telegram", "Multiple Telegram chat ids found. Configure GOAL_AGENT_TELEGRAM_CHAT_ID explicitly.")
        payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text[:3900],
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        try:
            with urllib.request.urlopen(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=payload,
                timeout=self.settings.telegram_timeout_seconds,
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
            if body.get("ok"):
                return NotificationResult(True, True, "telegram", "sent")
            return NotificationResult(False, True, "telegram", "Telegram API rejected message.")
        except Exception as exc:  # noqa: BLE001
            return NotificationResult(False, True, "telegram", f"Telegram send failed: {exc.__class__.__name__}")

    def discover_chat_ids(self) -> NotificationResult:
        if not self.settings.telegram_enabled or not self.settings.telegram_bot_token_present:
            return NotificationResult(False, False, "telegram", "Telegram token not configured.")
        token = _secret_env("GOAL_AGENT_TELEGRAM_BOT_TOKEN", self.settings)
        if not token:
            return NotificationResult(False, False, "telegram", "Telegram bot token missing.")
        try:
            chat_ids = self._discover_chat_ids(token)
        except RuntimeError as exc:
            return NotificationResult(False, True, "telegram", str(exc))
        if not chat_ids:
            return NotificationResult(False, True, "telegram", "No Telegram chat id found. Send /start to the bot first.")
        return NotificationResult(True, True, "telegram", "chat_ids=" + ",".join(chat_ids))

    def _discover_chat_ids(self, token: str) -> list[str]:
        try:
            with urllib.request.urlopen(
                f"https://api.telegram.org/bot{token}/getUpdates",
                timeout=self.settings.telegram_timeout_seconds,
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Telegram getUpdates failed: {exc.__class__.__name__}") from exc
        chat_ids: list[str] = []
        for update in body.get("result", []):
            message = update.get("message") or update.get("channel_post") or {}
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is not None and str(chat_id) not in chat_ids:
                chat_ids.append(str(chat_id))
        return chat_ids


def build_daily_update(db: Database, settings: Settings, run_id: str, summary: str) -> str:
    rows = db.query("select count(*) as c from coding_tasks where status='queued'")
    queued_codex = rows[0]["c"] if rows else 0
    blog_rows = db.query("select count(*) as c from blog_tasks where status='queued'")
    queued_blog = blog_rows[0]["c"] if blog_rows else 0
    blocked_rows = db.query("select count(*) as c from coding_task_runs where safety_blocked=1")
    safety_blocks = blocked_rows[0]["c"] if blocked_rows else 0
    gsc = GSCConnector(settings).analyze()
    if gsc.ok and gsc.configured:
        gsc_status = f"ok ({gsc.summary.get('row_count', 0)} rows)"
    elif gsc.warning:
        gsc_status = gsc.warning
    else:
        gsc_status = "not configured"
    return "\n".join([
        "Nachhilfe Mentor Goal Agent Update",
        f"Run: {run_id}",
        f"Mode: {settings.mode}",
        f"Status: {summary}",
        f"Queued Blog Tasks: {queued_blog}",
        f"Queued Codex Tasks: {queued_codex}",
        f"Codex enabled: {settings.codex_enabled}",
        f"Safety blocks: {safety_blocks}",
        f"GSC: {gsc_status}",
        "Deploy: blocked",
    ])


def notify_daily_update(db: Database, settings: Settings, run_id: str, summary: str) -> NotificationResult:
    return TelegramNotifier(settings).send_text(build_daily_update(db, settings, run_id, summary))


def _secret_env(name: str, settings: Settings | None = None) -> str:
    # Token values are intentionally read at send time and never stored in Settings,
    # reports, database rows, or logs.
    import os

    if name in os.environ:
        return os.environ[name]
    if settings and settings.env_file_path.exists():
        for line in settings.env_file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    return ""
