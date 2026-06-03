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
