# Deployment

The Goal Agent pushes to `main` only when the explicit autonomous deploy gate is enabled.

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
- `GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=2` is the recommended autonomous value;
- no push, deploy, or live publish.

Recommended production cadence:

- Keep the existing systemd morning run at `03:17`.
- Add one user-cron afternoon run at `15:17` with `GOAL_AGENT_CODEX_MAX_TASKS_PER_RUN=2`.
- The repo-level run lock at `goal_agent/state/goal_agent_run.lock` prevents the afternoon run from overlapping a long morning run.
- Do not increase beyond twice daily until recent runs show completed Codex tasks, low failure rate, and no stale blocked-task backlog.
- More frequent starts are less useful than better context, current pattern contracts, stale-task retirement, and passing QA gates.

Do not enable autonomous deploy until manual review has validated generated pages, tracking, and rollback.
