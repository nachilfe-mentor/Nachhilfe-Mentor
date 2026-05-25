# Configuration

Defaults are safe.

## Core Flags

- `GOAL_AGENT_ENABLED=false`
- `GOAL_AGENT_MODE=dry_run`
- `GOAL_AGENT_ALLOW_PRODUCTION_WRITES=false`
- `GOAL_AGENT_ALLOW_PAGE_GENERATION=false`
- `GOAL_AGENT_ALLOW_TRACKING_CHANGES=false`
- `GOAL_AGENT_ALLOW_TOOLSMITH=false`
- `GOAL_AGENT_ALLOW_AUTONOMOUS_DEPLOY=false`
- `GOAL_AGENT_MAX_ACTIONS_PER_RUN=10`
- `GOAL_AGENT_EMERGENCY_MAX_GENERATED_PAGES_PER_RUN=50`
- `GOAL_AGENT_MAX_TOOLSMITH_CHANGES_PER_RUN=1`
- `GOAL_AGENT_ALLOW_BLOG_AGENT_CONTEXT_CHANGES=false`

## Modes

- `dry_run`: scan, score, queue, report.
- `analyze_only`: analyze without queue expansion.
- `queue_only`: update Blog Agent queue and reports.
- `write_safe`: allow explicitly gated safe writes.
- `autonomous_full`: enables full loop only when separate allow flags are also true.

Generated SEO/practice/interactive pages do not use a normal fixed daily publishing limit. The emergency max is only a runaway safety fallback. Normal publishing is controlled by quality-adjusted adaptive gates.

## Analytics

PostHog:

- `POSTHOG_HOST`
- `POSTHOG_PROJECT_ID`
- `POSTHOG_PROJECT_API_KEY`
- `POSTHOG_PERSONAL_API_KEY`

GSC:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GSC_SITE_URL`

Secret values must never be printed or committed.
