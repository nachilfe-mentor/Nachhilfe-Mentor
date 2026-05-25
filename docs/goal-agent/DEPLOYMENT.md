# Deployment

The Goal Agent does not push to `main` by default.

Recommended deployment:

1. Run tests.
2. Run `GOAL_AGENT_MODE=dry_run python3 -m goal_agent.cli run --cycle daily`.
3. Inspect `goal_agent/exports/daily_seo_report.md`.
4. Inspect `goal_agent/queues/blog_tasks.jsonl`.
5. Add cron/systemd only after repeated clean dry runs.

Cron-compatible command:

```bash
cd /home/opc/Nachhilfe-Mentor && GOAL_AGENT_MODE=dry_run python3 -m goal_agent.cli run --cycle daily
```

Systemd-compatible autonomous command:

```bash
cd /home/opc/Nachhilfe-Mentor && python3 -m goal_agent.cli run --cycle daily --queue-codex-tasks
```

Autonomous deploys are blocked unless:

- `GOAL_AGENT_MODE=autonomous_full`;
- `GOAL_AGENT_ALLOW_AUTONOMOUS_DEPLOY=true`;
- tests pass;
- production-write gates pass.

Codex Coding Agent execution is separately gated:

- `GOAL_AGENT_CODEX_ENABLED=true`;
- clean git worktree unless `GOAL_AGENT_CODEX_ALLOW_DIRTY_WORKTREE=true`;
- `GOAL_AGENT_CODEX_TIMEOUT_SECONDS=21600` by default for real Coding Agent work;
- `GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=1` by default;
- no push, deploy, or live publish.

Do not enable autonomous deploy until manual review has validated generated pages, tracking, and rollback.
