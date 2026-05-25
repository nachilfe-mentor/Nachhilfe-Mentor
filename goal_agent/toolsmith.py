from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, Settings
from .storage import Database, json_dumps, utc_now


BUILTIN_TOOLS = {
    "posthog_conversion_analyzer": "goal_agent.tools.builtin.posthog_conversion_analyzer",
    "gsc_query_clusterer": "goal_agent.tools.builtin.gsc_query_clusterer",
    "content_decay_detector": "goal_agent.tools.builtin.content_decay_detector",
    "internal_link_graph_analyzer": "goal_agent.tools.builtin.internal_link_graph_analyzer",
    "serp_gap_scanner": "goal_agent.tools.builtin.serp_gap_scanner",
    "topic_graph_builder": "goal_agent.tools.builtin.topic_graph_builder",
    "blog_prompt_evaluator": "goal_agent.tools.builtin.blog_prompt_evaluator",
    "interactive_page_generator": "goal_agent.tools.builtin.interactive_page_generator",
    "sitemap_diff_checker": "goal_agent.tools.builtin.sitemap_diff_checker",
    "schema_markup_generator": "goal_agent.tools.builtin.schema_markup_generator",
    "cannibalization_detector": "goal_agent.tools.builtin.cannibalization_detector",
    "ranking_anomaly_detector": "goal_agent.tools.builtin.ranking_anomaly_detector",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ToolRegistry:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self.registry_path = REPO_ROOT / "goal_agent" / "tools" / "registry.json"

    def register_builtin_tools(self) -> None:
        now = utc_now()
        registry = []
        with self.db.connect() as conn:
            for name, module_path in BUILTIN_TOOLS.items():
                module = importlib.import_module(module_path)
                file_path = Path(module.__file__ or "")
                digest = sha256_file(file_path)
                tool_id = "tool_" + name
                version_id = f"{tool_id}_v1"
                conn.execute(
                    """
                    insert into tools (id, name, purpose, status, current_version_id, allowed_inputs_json, allowed_outputs_json, risk_level, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(name) do update set current_version_id=excluded.current_version_id, status=excluded.status, updated_at=excluded.updated_at
                    """,
                    (tool_id, name, f"Built-in {name}", "verified", version_id, "{}", "{}", "low", now, now),
                )
                conn.execute(
                    """
                    insert into tool_versions (id, tool_id, version, file_path, sha256, spec_markdown, test_command, test_result_json, status, created_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(id) do nothing
                    """,
                    (version_id, tool_id, "1", str(file_path.relative_to(REPO_ROOT)), digest, f"# {name}\nBuilt-in verified tool.", "python3 -m pytest tests/goal_agent", json_dumps({"builtin": True}), "verified", now),
                )
                registry.append({"name": name, "module": module_path, "status": "verified", "sha256": digest})
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps({"tools": registry}, indent=2, sort_keys=True), encoding="utf-8")

    def is_verified(self, name: str) -> bool:
        rows = self.db.query("select status from tools where name=?", (name,))
        return bool(rows and rows[0]["status"] == "verified")


class Toolsmith:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self.generated_dir = REPO_ROOT / "goal_agent" / "generated_tools"

    def propose_tool_spec(self, name: str, purpose: str, bottleneck: str) -> Path | None:
        if not self.settings.toolsmith_enabled:
            return None
        safe_name = name.replace("/", "_").replace("..", "_")
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        path = self.generated_dir / f"{safe_name}.spec.md"
        spec = f"""# {safe_name}

Purpose: {purpose}

Bottleneck: {bottleneck}

Inputs: JSON-compatible structured data only.
Outputs: JSON-compatible structured data only.
Blocked: secrets, destructive commands, production writes, personal data.
Tests: required before activation.
"""
        path.write_text(spec, encoding="utf-8")
        return path

    def activate_generated_tool(self, name: str) -> bool:
        # Generated tools cannot be activated automatically in this implementation.
        # They must be reviewed and tested first.
        return False
