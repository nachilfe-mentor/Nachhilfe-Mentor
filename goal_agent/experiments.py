from __future__ import annotations

import hashlib
from typing import Any

from .storage import Database, json_dumps, utc_now


EXPERIMENT_TYPES = {
    "cta_copy_test",
    "cta_placement_test",
    "tool_first_vs_explanation_first",
    "quiz_placement_test",
    "template_version_test",
}


def create_experiment(db: Database, name: str, experiment_type: str, target_pages: list[str], hypothesis: str, topic_cluster: str = "allgemein") -> str:
    if experiment_type not in EXPERIMENT_TYPES:
        raise ValueError("invalid experiment type")
    now = utc_now()
    exp_id = "exp_" + hashlib.sha1(f"{name}:{experiment_type}:{target_pages}".encode("utf-8")).hexdigest()[:16]
    with db.connect() as conn:
        conn.execute(
            """
            insert into experiments (
              id, name, hypothesis, topic_cluster, target_pages_json, primary_metric,
              secondary_metrics_json, status, baseline_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set updated_at=excluded.updated_at
            """,
            (
                exp_id,
                name,
                hypothesis,
                topic_cluster,
                json_dumps(target_pages),
                "seo_cta_clicked_per_seo_page_view",
                json_dumps(["seo_scroll_depth_reached", "seo_internal_link_clicked"]),
                "planned",
                json_dumps({}),
                now,
                now,
            ),
        )
    return exp_id


def config_flags() -> dict[str, Any]:
    return {
        "feature_flags": {
            "cta_copy_test": "config_only",
            "cta_placement_test": "config_only",
            "tool_first_vs_explanation_first": "config_only",
            "quiz_placement_test": "config_only",
            "template_version_test": "config_only",
        }
    }
