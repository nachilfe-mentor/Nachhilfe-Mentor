from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import Settings, load_settings


SCHEMA = """
pragma journal_mode=WAL;

create table if not exists agent_runs (
  id text primary key,
  cycle_type text not null,
  status text not null,
  started_at text not null,
  finished_at text,
  agent_version text not null,
  git_commit_before text,
  git_commit_after text,
  dry_run integer not null default 1,
  summary text,
  error_type text,
  error_message_redacted text,
  cost_estimate_eur real default 0,
  created_at text not null
);

create table if not exists decisions (
  id text primary key,
  agent_run_id text not null,
  decision_type text not null,
  title text not null,
  rationale text not null,
  evidence_json text not null,
  alternatives_json text,
  confidence real not null,
  risk_score real not null,
  status text not null,
  created_at text not null
);

create table if not exists actions (
  id text primary key,
  agent_run_id text not null,
  decision_id text,
  action_type text not null,
  target_type text not null,
  target_id text,
  status text not null,
  files_changed_json text,
  command text,
  safety_checks_json text not null,
  success_metric text,
  rollback_plan text,
  created_at text not null,
  completed_at text
);

create table if not exists failures (
  id text primary key,
  agent_run_id text,
  action_id text,
  failure_type text not null,
  message_redacted text not null,
  stack_redacted text,
  retryable integer not null default 0,
  resolved integer not null default 0,
  created_at text not null
);

create table if not exists opportunities (
  id text primary key,
  type text not null,
  topic_cluster text,
  primary_keyword text,
  intent text,
  target_url text,
  evidence_json text not null,
  expected_value_score real not null,
  money_potential_score real not null,
  traffic_potential_score real not null,
  search_demand_score real not null,
  serp_weakness_score real not null,
  topical_authority_fit_score real not null,
  posthog_conversion_potential_score real not null,
  internal_link_value_score real not null,
  interactivity_advantage_score real not null,
  execution_complexity_score real not null,
  privacy_risk_score real not null,
  seo_risk_score real not null,
  confidence_score real not null,
  status text not null,
  next_action text,
  created_by text not null,
  created_at text not null,
  updated_at text not null
);

create table if not exists ideas (
  id text primary key,
  type text not null,
  topic_cluster text,
  primary_keyword text,
  intent text,
  evidence_json text not null,
  confidence real not null,
  expected_value_score real not null,
  money_potential_score real not null,
  traffic_potential_score real not null,
  execution_complexity real not null,
  risk_score real not null,
  status text not null,
  next_action text,
  related_pages_json text not null default '[]',
  related_experiments_json text not null default '[]',
  created_by text not null,
  dedupe_key text not null unique,
  created_at text not null,
  updated_at text not null
);

create table if not exists experiments (
  id text primary key,
  name text not null,
  hypothesis text not null,
  topic_cluster text,
  target_pages_json text not null,
  primary_metric text not null,
  secondary_metrics_json text not null,
  start_date text,
  end_date text,
  status text not null,
  baseline_json text,
  results_json text,
  decision_id text,
  created_at text not null,
  updated_at text not null
);

create table if not exists learnings (
  id text primary key,
  claim text not null,
  evidence_json text not null,
  confidence real not null,
  affected_clusters_json text not null,
  recommended_policy_change text,
  source text not null,
  status text not null,
  created_at text not null,
  revalidate_after text,
  expires_at text
);

create table if not exists blog_tasks (
  id text primary key,
  task_type text not null,
  status text not null,
  priority integer not null,
  topic text,
  topic_cluster text,
  primary_keyword text,
  secondary_keywords_json text not null default '[]',
  search_intent text,
  target_slug text,
  title_hint text,
  recommended_angle text,
  template_version text,
  required_internal_links_json text not null default '[]',
  recommended_cta text,
  evidence_json text not null default '[]',
  expected_metric text,
  due_window text,
  source_agent_run_id text,
  created_by text not null,
  accepted_at text,
  completed_at text,
  result_url text,
  created_at text not null,
  updated_at text not null
);

create table if not exists interactive_page_tasks (
  id text primary key,
  status text not null,
  asset_type text not null default 'interactive_learning_page',
  page_type text not null,
  subject text,
  grade_level text,
  exam_type text,
  difficulty text,
  solution_mode text,
  interaction_type text,
  expected_learning_outcome text,
  topic_cluster text not null,
  primary_keyword text,
  search_intent text,
  target_slug text not null,
  spec_markdown text not null,
  tracking_requirements_json text not null,
  schema_requirements_json text not null,
  privacy_review_status text not null,
  seo_risk_score real not null,
  expected_value_score real not null,
  agent_run_id text,
  created_at text not null,
  updated_at text not null
);

create table if not exists tools (
  id text primary key,
  name text not null unique,
  purpose text not null,
  status text not null,
  current_version_id text,
  allowed_inputs_json text not null,
  allowed_outputs_json text not null,
  risk_level text not null,
  created_at text not null,
  updated_at text not null
);

create table if not exists tool_versions (
  id text primary key,
  tool_id text not null,
  version text not null,
  file_path text not null,
  sha256 text not null,
  spec_markdown text not null,
  test_command text not null,
  test_result_json text,
  status text not null,
  created_at text not null
);

create table if not exists tool_runs (
  id text primary key,
  tool_name text not null,
  agent_run_id text,
  status text not null,
  input_summary text,
  output_summary text,
  error_message_redacted text,
  created_at text not null
);

create table if not exists coding_tasks (
  id text primary key,
  source_recommendation_id text,
  task_type text not null,
  title text not null,
  goal text not null,
  context_summary text not null,
  target_files_allowed_json text not null,
  target_files_forbidden_json text not null,
  acceptance_criteria_json text not null,
  safety_constraints_json text not null,
  test_commands_json text not null,
  mode text not null,
  publish_policy text not null,
  created_at text not null,
  updated_at text not null,
  status text not null,
  result_summary text,
  changed_files_json text not null default '[]',
  priority integer not null default 50,
  legacy_source_refs_json text not null default '[]'
);

create table if not exists subagent_runs (
  id text primary key,
  agent_name text not null,
  status text not null,
  confidence real not null,
  priority integer not null,
  risks_json text not null default '[]',
  safety_notes_json text not null default '[]',
  recommendation_count integer not null default 0,
  created_at text not null
);

create table if not exists subagent_recommendations (
  id text primary key,
  source_agent text not null,
  recommendation_type text not null,
  title text not null,
  rationale text not null,
  priority integer not null,
  confidence real not null,
  target_topic text,
  target_url text,
  suggested_publish_decision text not null,
  codex_task_allowed integer not null default 0,
  safety_risk text not null,
  acceptance_criteria_json text not null,
  required_context_json text not null,
  created_at text not null,
  status text not null default 'queued'
);

create table if not exists coding_task_runs (
  id text primary key,
  task_id text not null,
  status text not null,
  started_at text not null,
  finished_at text,
  exit_code integer,
  stdout_summary text,
  stderr_summary text,
  changed_files_json text not null default '[]',
  git_diff_stat text,
  git_status_short text,
  tests_run_json text not null default '[]',
  failure_reason text,
  safety_blocked integer not null default 0,
  prompt_summary text,
  created_at text not null
);

create table if not exists posthog_event_definitions (
  event_name text primary key,
  description text not null,
  allowed_properties_json text not null,
  blocked_properties_json text not null,
  privacy_level text not null,
  first_seen_at text,
  last_seen_at text,
  status text not null,
  created_at text not null,
  updated_at text not null
);

create table if not exists content_inventory (
  id text primary key,
  url_path text not null unique,
  canonical_url text,
  source_file text,
  content_type text not null,
  slug text,
  title text,
  meta_description text,
  h1 text,
  topic_cluster text,
  primary_keyword text,
  search_intent text,
  word_count integer,
  schema_types_json text not null default '[]',
  internal_link_count integer default 0,
  external_link_count integer default 0,
  image_count integer default 0,
  is_in_sitemap integer not null default 0,
  lastmod text,
  first_seen_at text not null,
  last_scanned_at text not null
);

create table if not exists page_metrics (
  id text primary key,
  url_path text not null,
  date text not null,
  source text not null,
  views integer default 0,
  sessions integer default 0,
  users integer default 0,
  engaged_sessions integer default 0,
  avg_engagement_seconds real,
  scroll_90_count integer default 0,
  internal_link_clicks integer default 0,
  cta_clicks integer default 0,
  app_store_clicks integer default 0,
  tool_starts integer default 0,
  tool_completions integer default 0,
  quiz_starts integer default 0,
  quiz_completions integer default 0,
  gsc_clicks integer default 0,
  gsc_impressions integer default 0,
  gsc_ctr real,
  gsc_avg_position real,
  created_at text not null,
  unique(url_path, date, source)
);

create table if not exists topic_graph_nodes (
  id text primary key,
  node_type text not null,
  name text not null,
  slug text,
  parent_id text,
  authority_score real default 0,
  conversion_score real default 0,
  created_at text not null,
  updated_at text not null
);

create table if not exists topic_graph_edges (
  id text primary key,
  source_node_id text not null,
  target_node_id text not null,
  edge_type text not null,
  weight real not null default 1,
  evidence_json text not null default '{}',
  created_at text not null
);

create table if not exists internal_link_graph (
  id text primary key,
  source_url text not null,
  target_url text not null,
  anchor_category text,
  link_position text,
  same_cluster integer not null default 0,
  is_broken integer not null default 0,
  first_seen_at text not null,
  last_seen_at text not null
);

create table if not exists prompt_versions (
  id text primary key,
  prompt_name text not null,
  version text not null,
  file_path text not null,
  sha256 text not null,
  status text not null,
  change_reason text,
  created_by text not null,
  created_at text not null
);

create table if not exists scoring_versions (
  id text primary key,
  version text not null,
  weights_json text not null,
  change_reason text not null,
  evidence_json text not null,
  status text not null,
  created_at text not null
);

create table if not exists context_snapshots (
  id text primary key,
  agent_run_id text not null,
  context_type text not null,
  content_sha256 text not null,
  file_path text,
  summary text,
  created_at text not null
);

create table if not exists data_snapshots (
  id text primary key,
  agent_run_id text not null,
  source text not null,
  period_start text,
  period_end text,
  record_count integer not null,
  summary_json text not null,
  created_at text not null
);

create index if not exists idx_agent_runs_started_at on agent_runs(started_at);
create index if not exists idx_ideas_status_score on ideas(status, expected_value_score desc);
create index if not exists idx_blog_tasks_status_priority on blog_tasks(status, priority desc);
create index if not exists idx_content_inventory_cluster on content_inventory(topic_cluster);
create index if not exists idx_page_metrics_url_date on page_metrics(url_path, date);
create index if not exists idx_internal_link_source on internal_link_graph(source_url);
create index if not exists idx_internal_link_target on internal_link_graph(target_url);
create index if not exists idx_coding_tasks_status_priority on coding_tasks(status, priority desc);
create index if not exists idx_subagent_recommendations_priority on subagent_recommendations(status, priority desc);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Database:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.path = self.settings.db_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._ensure_compat_columns(conn)

    def _ensure_compat_columns(self, conn: sqlite3.Connection) -> None:
        tables = {row["name"] for row in conn.execute("select name from sqlite_master where type='table'")}
        if "coding_tasks" in tables:
            columns = {row["name"] for row in conn.execute("pragma table_info(coding_tasks)")}
            additions = {
                "source_recommendation_id": "text",
                "result_summary": "text",
                "changed_files_json": "text not null default '[]'",
                "legacy_source_refs_json": "text not null default '[]'",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    conn.execute(f"alter table coding_tasks add column {name} {ddl}")

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.connect() as conn:
            conn.execute(sql, params)

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute(sql, params))

    def upsert_content(self, rows: list[dict[str, Any]]) -> None:
        now = utc_now()
        with self.connect() as conn:
            for row in rows:
                conn.execute(
                    """
                    insert into content_inventory (
                      id, url_path, canonical_url, source_file, content_type, slug,
                      title, meta_description, h1, topic_cluster, primary_keyword,
                      search_intent, word_count, schema_types_json, internal_link_count,
                      external_link_count, image_count, is_in_sitemap, lastmod,
                      first_seen_at, last_scanned_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(url_path) do update set
                      canonical_url=excluded.canonical_url,
                      source_file=excluded.source_file,
                      content_type=excluded.content_type,
                      slug=excluded.slug,
                      title=excluded.title,
                      meta_description=excluded.meta_description,
                      h1=excluded.h1,
                      topic_cluster=excluded.topic_cluster,
                      primary_keyword=excluded.primary_keyword,
                      search_intent=excluded.search_intent,
                      word_count=excluded.word_count,
                      schema_types_json=excluded.schema_types_json,
                      internal_link_count=excluded.internal_link_count,
                      external_link_count=excluded.external_link_count,
                      image_count=excluded.image_count,
                      is_in_sitemap=excluded.is_in_sitemap,
                      lastmod=excluded.lastmod,
                      last_scanned_at=excluded.last_scanned_at
                    """,
                    (
                        row["id"],
                        row["url_path"],
                        row.get("canonical_url"),
                        row.get("source_file"),
                        row["content_type"],
                        row.get("slug"),
                        row.get("title"),
                        row.get("meta_description"),
                        row.get("h1"),
                        row.get("topic_cluster"),
                        row.get("primary_keyword"),
                        row.get("search_intent"),
                        row.get("word_count", 0),
                        json_dumps(row.get("schema_types", [])),
                        row.get("internal_link_count", 0),
                        row.get("external_link_count", 0),
                        row.get("image_count", 0),
                        1 if row.get("is_in_sitemap") else 0,
                        row.get("lastmod"),
                        now,
                        now,
                    ),
                )


def write_migration_file() -> Path:
    path = Path(__file__).resolve().parent / "migrations" / "001_init.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or "Canonical migration content is generated" in path.read_text(encoding="utf-8", errors="ignore"):
        path.write_text(SCHEMA, encoding="utf-8")
    return path
