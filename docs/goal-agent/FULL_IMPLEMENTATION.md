# Full Implementation

The Goal Agent implementation lives in `goal_agent/` and covers V1-V5 with safe defaults.

## V1

- SQLite storage and migrations.
- Content inventory scanner.
- Sitemap/feed aware scan primitives.
- Blog registry reader.
- Opportunity scoring.
- Blog Agent queue export.
- Daily markdown report.
- CLI commands.

## V2

- Privacy-safe PostHog connector.
- GSC placeholder connector.
- SERP placeholder connector.
- Event schema validation.
- Internal link graph analyzer.
- Content decay built-in tool.
- Blog prompt evaluator.

## V3

- Interactive asset generator.
- Practice-first asset support.
- Quality gate for generated assets.
- Adaptive publishing throttle with publish/index, draft/noindex, and hold decisions.
- Lightweight experiment registry.
- Schema.org generator.
- Rollback-safe generated output folder: `goal-agent-pages/`.

## V4

- Tool registry.
- Built-in verified tools.
- Gated Toolsmith path for generated tools.
- Structured learning storage.
- Scoring version proposal storage.

## V5

- Autonomous loop in `goal_agent/loop.py`.
- Cron-compatible scheduler in `goal_agent/scheduler.py`.
- Blog Agent Guardian monitoring and guarded adjustment recommendations.
- Modes: `dry_run`, `analyze_only`, `queue_only`, `write_safe`, `autonomous_full`.
- Default mode is `dry_run`.
- Production writes, page generation, tracking changes, Toolsmith, and deploys require explicit env flags.
