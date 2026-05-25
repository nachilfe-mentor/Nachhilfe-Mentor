# Operations

## Reports

- `goal_agent/exports/daily_seo_report.md`
- `goal_agent/exports/blog_task_snapshot.md`

## Queue

- `goal_agent/queues/blog_tasks.jsonl`

The Blog Agent is not modified to read the queue automatically yet.

## Database

Default DB:

- `goal_agent/goal_agent.db`

Inspect:

```bash
sqlite3 goal_agent/goal_agent.db '.tables'
sqlite3 goal_agent/goal_agent.db 'select id,status,summary from agent_runs order by started_at desc limit 5;'
```

## Rollback Generated Pages

Generated pages live in:

- `goal-agent-pages/`

Rollback by removing only generated files from the current action and marking related actions/experiments stopped in the DB.
