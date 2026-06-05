from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _int_value(name: str, default: int, env_file_values: dict[str, str] | None = None) -> int:
    value = _env(name, "", env_file_values)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _bool_value(name: str, default: bool = False, env_file_values: dict[str, str] | None = None) -> bool:
    value = _env(name, "", env_file_values)
    if value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env(name: str, default: str = "", env_file_values: dict[str, str] | None = None) -> str:
    if name in os.environ:
        return os.environ[name]
    if env_file_values and name in env_file_values:
        return env_file_values[name]
    return default


@dataclass(frozen=True)
class Settings:
    repo_root: Path = REPO_ROOT
    env_file_path: Path = Path("/etc/nachhilfe-mentor/goal-agent.env")
    exports_dir: Path = REPO_ROOT / "goal_agent" / "exports"
    db_path: Path = REPO_ROOT / "goal_agent" / "goal_agent.db"
    enabled: bool = False
    mode: str = "dry_run"
    allow_production_writes: bool = False
    allow_page_generation: bool = False
    allow_tracking_changes: bool = False
    allow_toolsmith: bool = False
    allow_blog_agent_context_changes: bool = False
    allow_autonomous_deploy: bool = False
    codex_enabled: bool = False
    codex_bin: str = "codex"
    codex_timeout_seconds: int = 21600
    codex_sandbox_mode: str = "workspace-write"
    codex_create_branch: bool = False
    codex_allow_dirty_worktree: bool = False
    codex_dirty_allowed_paths: tuple[str, ...] = (
        # Blog Agent output — committed independently by the Blog Agent
        "auto-blog.log",
        "blog/",
        "Blog/",
        "sitemap.xml",
        "feed.xml",
        "blog/_pinterest_done.txt",
        "blog/_BLOG_REGISTRY.md",
        # Goal Agent runtime files
        "goal_agent/exports/",
        "goal_agent/queues/",
        "goal_agent/goal_agent.db",
        "goal_agent/goal_agent.db-",
    )
    codex_max_tasks_per_run: int = 1
    max_actions_per_run: int = 10
    emergency_max_generated_pages_per_run: int = 50
    max_toolsmith_changes_per_run: int = 1
    posthog_host: str = "https://eu.posthog.com"
    posthog_project_id: str = ""
    posthog_project_api_key_present: bool = False
    posthog_personal_api_key_present: bool = False
    google_application_credentials: str = ""
    gsc_oauth_credentials: str = ""
    gsc_auth_mode: str = "auto"
    gsc_site_url: str = ""
    gsc_configured: bool = False
    telegram_enabled: bool = False
    telegram_bot_token_present: bool = False
    telegram_chat_id: str = ""
    telegram_timeout_seconds: int = 10

    @property
    def safe_write_mode(self) -> bool:
        return self.mode in {"write_safe", "autonomous_full"} and self.allow_production_writes

    @property
    def page_generation_enabled(self) -> bool:
        return self.safe_write_mode and self.allow_page_generation

    @property
    def tracking_changes_enabled(self) -> bool:
        return self.safe_write_mode and self.allow_tracking_changes

    @property
    def toolsmith_enabled(self) -> bool:
        return self.mode == "autonomous_full" and self.allow_toolsmith

    @property
    def deploy_enabled(self) -> bool:
        return self.mode == "autonomous_full" and self.allow_autonomous_deploy


def load_settings() -> Settings:
    env_file = Path(os.environ.get("GOAL_AGENT_ENV_FILE", "/etc/nachhilfe-mentor/goal-agent.env"))
    env_file_values = _read_env_file(env_file)
    mode = _env("GOAL_AGENT_MODE", "dry_run", env_file_values).strip() or "dry_run"
    if mode not in {"dry_run", "analyze_only", "queue_only", "write_safe", "autonomous_full"}:
        mode = "dry_run"
    db_path = Path(_env("GOAL_AGENT_DB_PATH", str(REPO_ROOT / "goal_agent" / "goal_agent.db"), env_file_values))
    exports_dir = Path(_env("GOAL_AGENT_EXPORTS_DIR", str(REPO_ROOT / "goal_agent" / "exports"), env_file_values))
    google_application_credentials = _env("GOOGLE_APPLICATION_CREDENTIALS", "", env_file_values)
    gsc_oauth_credentials = _env("GSC_OAUTH_CREDENTIALS", "", env_file_values)
    gsc_auth_mode = _env("GSC_AUTH_MODE", "auto", env_file_values).strip().lower() or "auto"
    if gsc_auth_mode not in {"auto", "service_account", "oauth"}:
        gsc_auth_mode = "auto"
    gsc_site_url = _env("GSC_SITE_URL", "", env_file_values)
    dirty_allowed = tuple(
        item.strip()
        for item in _env(
            "GOAL_AGENT_CODEX_DIRTY_ALLOWED_PATHS",
            "auto-blog.log,blog/_pinterest_done.txt,goal_agent/exports/,goal_agent/queues/,goal_agent/goal_agent.db,goal_agent/goal_agent.db-",
            env_file_values,
        ).split(",")
        if item.strip()
    )
    return Settings(
        env_file_path=env_file,
        exports_dir=exports_dir,
        db_path=db_path,
        enabled=_env("GOAL_AGENT_ENABLED", "false", env_file_values).strip().lower() in {"1", "true", "yes", "on"},
        mode=mode,
        allow_production_writes=_bool_value("GOAL_AGENT_ALLOW_PRODUCTION_WRITES", False, env_file_values),
        allow_page_generation=_bool_value("GOAL_AGENT_ALLOW_PAGE_GENERATION", False, env_file_values),
        allow_tracking_changes=_bool_value("GOAL_AGENT_ALLOW_TRACKING_CHANGES", False, env_file_values),
        allow_toolsmith=_bool_value("GOAL_AGENT_ALLOW_TOOLSMITH", False, env_file_values),
        allow_blog_agent_context_changes=_bool_value("GOAL_AGENT_ALLOW_BLOG_AGENT_CONTEXT_CHANGES", False, env_file_values),
        allow_autonomous_deploy=_bool_value("GOAL_AGENT_ALLOW_AUTONOMOUS_DEPLOY", False, env_file_values),
        codex_enabled=_env("GOAL_AGENT_CODEX_ENABLED", "false", env_file_values).strip().lower() in {"1", "true", "yes", "on"},
        codex_bin=_env("GOAL_AGENT_CODEX_BIN", "codex", env_file_values),
        codex_timeout_seconds=_int_value("GOAL_AGENT_CODEX_TIMEOUT_SECONDS", 21600, env_file_values),
        codex_sandbox_mode=_env("GOAL_AGENT_CODEX_SANDBOX_MODE", "workspace-write", env_file_values),
        codex_create_branch=_env("GOAL_AGENT_CODEX_CREATE_BRANCH", "false", env_file_values).strip().lower() in {"1", "true", "yes", "on"},
        codex_allow_dirty_worktree=_env("GOAL_AGENT_CODEX_ALLOW_DIRTY_WORKTREE", "false", env_file_values).strip().lower() in {"1", "true", "yes", "on"},
        codex_dirty_allowed_paths=dirty_allowed,
        codex_max_tasks_per_run=_int_value("GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN", 1, env_file_values),
        max_actions_per_run=_int_value("GOAL_AGENT_MAX_ACTIONS_PER_RUN", 10, env_file_values),
        emergency_max_generated_pages_per_run=_int_value(
            "GOAL_AGENT_EMERGENCY_MAX_GENERATED_PAGES_PER_RUN",
            _int_value("GOAL_AGENT_MAX_GENERATED_PAGES_PER_RUN", 50, env_file_values),
            env_file_values,
        ),
        max_toolsmith_changes_per_run=_int_value("GOAL_AGENT_MAX_TOOLSMITH_CHANGES_PER_RUN", 1, env_file_values),
        posthog_host=_env("POSTHOG_HOST", "https://eu.posthog.com", env_file_values).rstrip("/"),
        posthog_project_id=_env("POSTHOG_PROJECT_ID", "", env_file_values).strip(),
        posthog_project_api_key_present=bool(_env("POSTHOG_PROJECT_API_KEY", "", env_file_values)),
        posthog_personal_api_key_present=bool(_env("POSTHOG_PERSONAL_API_KEY", "", env_file_values)),
        google_application_credentials=google_application_credentials,
        gsc_oauth_credentials=gsc_oauth_credentials,
        gsc_auth_mode=gsc_auth_mode,
        gsc_site_url=gsc_site_url,
        gsc_configured=bool(gsc_site_url and (google_application_credentials or gsc_oauth_credentials)),
        telegram_enabled=_bool_value("GOAL_AGENT_TELEGRAM_ENABLED", False, env_file_values),
        telegram_bot_token_present=bool(_env("GOAL_AGENT_TELEGRAM_BOT_TOKEN", "", env_file_values)),
        telegram_chat_id=_env("GOAL_AGENT_TELEGRAM_CHAT_ID", "", env_file_values).strip(),
        telegram_timeout_seconds=_int_value("GOAL_AGENT_TELEGRAM_TIMEOUT_SECONDS", 10, env_file_values),
    )


BLOCKED_ACTIONS = {
    "external_outreach",
    "buy_backlinks",
    "link_spam",
    "cloaking",
    "doorway_pages",
    "keyword_stuffing",
    "collect_sensitive_personal_data",
    "print_secrets",
    "delete_production_content_without_backup",
    "irreversible_migration_without_backup",
    "payment_change",
    "subscription_change",
    "auth_change",
    "autonomous_push_main",
}
