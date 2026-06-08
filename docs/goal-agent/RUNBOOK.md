# Goal Agent Runbook

## Initialize

```bash
python3 -m goal_agent.cli init-db
```

## Dry Run

```bash
GOAL_AGENT_MODE=dry_run python3 -m goal_agent.cli run --cycle daily
```

## Analyze Only

```bash
GOAL_AGENT_MODE=analyze_only python3 -m goal_agent.cli run --cycle daily
```

## Queue Only

```bash
GOAL_AGENT_MODE=queue_only python3 -m goal_agent.cli run --cycle daily
```

## Inspect Status

```bash
python3 -m goal_agent.cli show-status
```

## Inspect Queue

```bash
sed -n '1,120p' goal_agent/queues/blog_tasks.jsonl
sed -n '1,160p' goal_agent/exports/blog_task_snapshot.md
sed -n '1,160p' goal_agent/exports/blog_agent_guardian.md
```

## Disable Instantly

Unset scheduler or set:

```bash
GOAL_AGENT_ENABLED=false
GOAL_AGENT_MODE=dry_run
```

The current implementation does not auto-start unless called by CLI, cron, or scheduler.

## Production Cadence

Use two daily runs:

- `03:17` via systemd timer for overnight SEO/GSC-driven planning.
- `15:17` via user cron for queue continuation.

Keep `GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=2` for the afternoon run. This gives extra throughput without encouraging overlapping long-running Codex work. The repo-level lock file `goal_agent/state/goal_agent_run.lock` makes a second run skip cleanly if another Goal Agent run is still active. Increase frequency only after the daily reports show that Codex tasks complete reliably and stale/blocked tasks stay near zero.

## Blog Agent Guardian

The Goal Agent writes a guardian report to:

```bash
goal_agent/exports/blog_agent_guardian.md
```

Guarded Blog Agent context changes require:

```bash
GOAL_AGENT_MODE=write_safe
GOAL_AGENT_ALLOW_PRODUCTION_WRITES=true
GOAL_AGENT_ALLOW_BLOG_AGENT_CONTEXT_CHANGES=true
```

Script-level Blog Agent edits should still be made through reviewed code changes with tests.

## Blog Agent Queue Integration

`blog/_prepare_blog_context.py` now includes:

- `goal_agent/exports/blog_task_snapshot.md`
- `goal_agent/exports/blog_agent_guardian.md`

The Blog Agent uses these only for topic choice, briefs, internal-link suggestions, and quality guidance. Practice pages and interactive assets remain Goal Agent-owned.

## Sitemap Integration

`blog/_update_seo.py` includes indexable files from `lernmaterialien/*.html`.

It excludes:

- `lernmaterialien/entwuerfe/*.html`
- any page with `<meta name="robots" content="noindex,...">`
