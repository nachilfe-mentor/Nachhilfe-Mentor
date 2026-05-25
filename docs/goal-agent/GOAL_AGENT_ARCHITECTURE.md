# Goal Agent Architecture

## Purpose

The Goal Agent is an autonomous SEO Growth Governor for `nachhilfe-mentor.de`. It supervises organic growth, analytics, SEO infrastructure, experiments, internal links, topic strategy, and conversion optimization. It does not write normal blog articles.

The existing Blog Agent remains the blogging worker. The Goal Agent feeds it structured, evidence-backed tasks.

Practice-first SEO assets are first-class Goal Agent assets alongside interactive tools. They include exercise pages with solutions, mini tests, quizzes, exam practice pages, grammar drills, formula practice pages, step-by-step calculation exercises, mistake-detection exercises, flashcard sets, worksheet generators, oral exam practice pages, topic diagnosis pages, and typical mistakes practice pages. They are owned by the Goal Agent/interactive asset system, not the Blog Agent.

## Proposed Code Location

Add a new isolated subsystem:

```text
goal_agent/
  __init__.py
  config.py
  cli.py
  scheduler.py
  migrations/
    001_init.sql
  storage/
    db.py
    repositories.py
  core/
    loop.py
    state_machine.py
    scoring.py
    context_builder.py
    locks.py
    safety.py
  connectors/
    posthog.py
    ga4.py
    gsc.py
    content_inventory.py
    sitemap.py
    blog_registry.py
    site_crawler.py
    internal_links.py
  prompts/
    constitution.md
    strategy_snapshot.md
    master_prompt.md
  tools/
    registry.json
    verified/
    experimental/
  queues/
    blog_tasks.jsonl
  exports/
    blog_task_snapshot.md
    daily_seo_report.md
  logs/
    goal_agent.log
    decisions.jsonl
    actions.jsonl
  state/
    goal_agent.pid
    run_summaries/
  tests/
```

V1 should use SQLite at:

```text
goal_agent/goal_agent.db
```

## 1. Goal Agent Core

### Main Loop

The main loop should be implemented in:

- `goal_agent/core/loop.py`

Command:

```bash
python3 -m goal_agent.cli run-once --cycle daily_analysis --dry-run
python3 -m goal_agent.cli run-once --cycle daily_analysis
```

Each run:

1. Acquire a Goal Agent lock.
2. Check whether the Blog Agent working tree is in a safe state.
3. Create `agent_runs` row.
4. Build context from layered context components.
5. Ingest data snapshots.
6. Score opportunities.
7. Create or update ideas, experiments, actions, and blog tasks.
8. Export a Blog Agent task snapshot.
9. Write run log, decision log, and action log.
10. Release lock.

### Scheduler

Use APScheduler, matching the adjacent engine pattern but isolated:

- `goal_agent/scheduler.py`

Recommended timezone:

- `Europe/Berlin`

Recommended jobs:

- Daily analysis: 05:20 Berlin time.
- Blog task export refresh: 05:45 Berlin time.
- Weekly strategy review: Sunday 06:40 Berlin time.
- Monthly technical SEO audit: first day of month 07:30 Berlin time.
- Hourly lightweight health check: optional after V1.

Command:

```bash
python3 -m goal_agent.scheduler
```

### State Machine

File:

- `goal_agent/core/state_machine.py`

States:

- `idle`
- `acquire_lock`
- `ingest_data`
- `crawl_site`
- `update_inventory`
- `score_opportunities`
- `plan_actions`
- `write_safe_changes`
- `validate`
- `export_tasks`
- `log_results`
- `failed`
- `rolled_back`

Each state writes to:

- `agent_runs`
- `decisions`
- `actions`
- `goal_agent/logs/goal_agent.log`

### Decision Cycle

Each decision cycle should answer:

1. What changed in organic traffic, engagement, and conversion?
2. Which pages/clusters gained or decayed?
3. Which opportunities have the highest expected business value?
4. What should the Blog Agent write or refresh?
5. What non-blog SEO asset should be built or improved?
6. What tracking is missing?
7. What experiment should be started, stopped, or evaluated?
8. What risks or blockers prevent action?

### Daily Loop

Daily loop objective:

- update page metrics;
- detect content decay;
- detect rising clusters;
- create high-confidence Blog Agent tasks;
- identify missing internal links;
- produce a daily SEO report.

Allowed daily writes:

- SQLite rows;
- JSONL logs;
- `goal_agent/exports/blog_task_snapshot.md`;
- `goal_agent/queues/blog_tasks.jsonl`;
- small documentation/report files under `goal_agent/exports/`.

### Weekly Loop

Weekly loop objective:

- review cluster performance;
- evaluate experiments;
- adjust scoring weights if evidence is strong;
- propose template/prompt changes;
- prioritize interactive SEO assets.

Allowed weekly writes after tests:

- scoring config update;
- prompt version proposal;
- verified tool output reports;
- Blog Agent prompt recommendation task.

### Monthly Loop

Monthly loop objective:

- crawl full site;
- audit sitemap, robots, schema, duplicate pages, canonicals, broken links;
- review risk budget and cost;
- archive stale ideas;
- revive previously low-confidence ideas if new evidence exists.

### Failure Handling

On failure:

- mark `agent_runs.status='failed'`;
- write `failures` row;
- write structured error without secrets;
- do not retry destructive writes automatically;
- do not push git changes;
- leave Blog Agent untouched.

Rollback behavior:

- only rollback files changed by the current Goal Agent run;
- never run `git reset --hard`;
- record backup path and restored files in `actions`;
- require human review for migrations or broad content rewrites.

## 2. Data Ingestion Layer

### PostHog Connector

File:

- `goal_agent/connectors/posthog.py`

Purpose:

- query aggregate event data;
- fetch page-level conversion and engagement metrics;
- detect event schema gaps;
- never fetch or store raw person profiles unless explicitly approved.

Inputs:

- `POSTHOG_HOST`
- `POSTHOG_PROJECT_API_KEY`
- `POSTHOG_PERSONAL_API_KEY`

Outputs:

- `page_metrics`
- `data_snapshots`
- `posthog_event_definitions`
- evidence rows linked to ideas/opportunities.

Safety check:

- redact any property matching email/name/free-text patterns before persistence.

### GA4 Connector

File:

- `goal_agent/connectors/ga4.py`

Purpose:

- reuse the current GA4 historical signal from `blog/_fetch-analytics.sh` or a Python equivalent;
- provide continuity while PostHog accumulates data.

Integration point:

- existing service account file path already used by `blog/_fetch-analytics.sh`;
- do not print its contents.

### Google Search Console Connector

File:

- `goal_agent/connectors/gsc.py`

No existing GSC connector was found.

Recommended env:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GSC_SITE_URL=https://nachhilfe-mentor.de/`

Metrics:

- query;
- page;
- clicks;
- impressions;
- CTR;
- average position;
- country;
- device;
- date.

Safety check:

- aggregate query data only;
- do not store user identifiers.

### Ranking/SERP Connector

File:

- `goal_agent/connectors/serp.py`

V1 can skip paid SERP APIs. V2/V3 may add an opt-in connector with a strict cost cap.

Metrics:

- SERP weakness;
- competitor page type;
- rich result presence;
- interactive-tool opportunity;
- cannibalization risk.

### Content Inventory Connector

File:

- `goal_agent/connectors/content_inventory.py`

Scans:

- `index.html`
- `blog/index.html`
- `blog/posts/*.html`
- selected static pages;
- future `tools/` or `learn/` interactive pages.

Extracts:

- canonical URL;
- title;
- meta description;
- H1/H2;
- word count;
- internal links;
- image count;
- schema presence;
- last modified git timestamp;
- template/script version hints.

### Site Crawler

File:

- `goal_agent/connectors/site_crawler.py`

V1 local crawl:

- parse local files and generated sitemap.

V2 live crawl:

- fetch live URLs with rate limits;
- compare status codes, canonicals, and indexability.

Safety:

- no aggressive crawling;
- user-agent identifies Nachhilfe Mentor internal SEO audit;
- respect `robots.txt`.

### Blog Output Reader

File:

- `goal_agent/connectors/blog_registry.py`

Reads:

- `blog/_BLOG_REGISTRY.md`
- `blog/_BLOG_CONTEXT_COMPACT.md`
- `blog/posts/*.html`
- `blog/articles/*.json`

Produces:

- cluster inventory;
- duplicate title/slug checks;
- link notes;
- content freshness;
- Blog Agent task context.

### Internal Link Graph Reader

File:

- `goal_agent/connectors/internal_links.py`

Builds:

- source URL;
- target URL;
- anchor text category;
- link position;
- same-cluster flag;
- broken-link status;
- orphan-page score.

### Sitemap Reader

File:

- `goal_agent/connectors/sitemap.py`

Reads:

- `sitemap.xml`

Checks:

- URLs exist locally;
- canonical matches;
- active pages are included;
- excluded pages are intentional;
- lastmod is reasonable.

## 3. Storage

See `DATABASE_SCHEMA.md` for exact table recommendations.

V1 storage should be SQLite because:

- the current website stack is static;
- there is no existing application DB;
- autonomous process count is low;
- SQLite is easy to back up and inspect.

## 4. Idea Management

Ideas are persisted business/SEO hypotheses. They are not tasks by themselves.

Idea lifecycle:

- `new`
- `scored`
- `queued`
- `in_progress`
- `experimenting`
- `validated`
- `rejected`
- `archived`
- `revived`

Deduplication keys:

- normalized primary keyword;
- topic cluster;
- target page slug;
- intent;
- idea type.

Revival rules:

- revive archived ideas if new GSC impressions, PostHog conversions, or SERP weakness evidence changes expected value by at least 25%.

## 5. Opportunity Scoring

File:

- `goal_agent/core/scoring.py`

Default score:

```text
expected_value_score =
  0.20 * search_demand_score +
  0.15 * serp_weakness_score +
  0.15 * topical_authority_fit_score +
  0.20 * posthog_conversion_potential_score +
  0.10 * internal_link_value_score +
  0.10 * interactivity_advantage_score +
  0.10 * confidence_score
  - 0.10 * execution_complexity_score
  - 0.15 * privacy_risk_score
  - 0.15 * seo_risk_score
```

Money-relevant organic growth is prioritized over traffic. A topic with lower traffic but stronger trial/app-download intent can outrank a high-volume informational topic.

## 6. Blog Agent Integration

The Goal Agent should create structured tasks and export a compact task snapshot.

Preferred integration files:

- DB table: `blog_tasks`
- JSONL export: `goal_agent/queues/blog_tasks.jsonl`
- Markdown export: `goal_agent/exports/blog_task_snapshot.md`

Blog Agent integration PR:

1. Update `blog/_prepare_blog_context.py` to include the top active Goal Agent tasks in `blog/_BLOG_CONTEXT_COMPACT.md`.
2. Update the prompt in `auto-blog.sh` to prefer queued Goal Agent tasks when suitable.
3. Keep `blog/_publish_article.py` unchanged unless the Blog Agent needs task status callbacks.

The Blog Agent should never be asked to run the Goal Agent or inspect the Goal Agent database directly.

## 7. PostHog Tracking Plan

See `POSTHOG_EVENT_SCHEMA.md`.

Implementation point:

- `scripts/posthog-tracking.js`
- `blog/_template.html` for page metadata attributes;
- future interactive page templates.

The tracking plan must remain privacy-safe and avoid personal data, raw answers, and sensitive learning data.

## 8. Self-Improvement System

The Goal Agent learns through structured learnings, not prompt drift.

Learning storage:

- `learnings`
- `scoring_versions`
- `prompt_versions`
- `experiments`
- `decisions`

A learning can update policy only when:

- evidence is linked;
- confidence is above threshold;
- the change is reversible;
- the effect can be measured.

See `SELF_IMPROVEMENT_SPEC.md`.

## 9. Toolsmith System

The Goal Agent may create helper tools only through a controlled lifecycle:

1. identify repeated bottleneck;
2. write tool spec;
3. implement in `goal_agent/tools/experimental/`;
4. write tests in `goal_agent/tests/`;
5. run tests;
6. document inputs/outputs;
7. register as verified in `goal_agent/tools/registry.json`;
8. use only after verification.

See `TOOLSMITH_SPEC.md`.

## 10. Context Management

The Goal Agent must not rely on one giant prompt.

Context layers:

- `constitution.md`: stable mission, safety, permissions.
- `strategy_snapshot.md`: current SEO strategy, refreshed weekly.
- retrieved memory: top relevant ideas, learnings, decisions, experiments.
- current data snapshot: PostHog, GA4, GSC, inventory, crawl, sitemap.
- current task brief: one cycle's objective and constraints.
- tool registry: verified tools only.
- run history summary: recent actions and outcomes.

Regeneration cadence:

- constitution: rarely, human-reviewed.
- strategy snapshot: weekly or after major validated learning.
- memory retrieval: every run.
- data snapshot: every run.
- task brief: every run.
- tool registry: whenever tests verify a tool.
- run summary: every run.

## 11. Execution Permissions

Allowed automatically if tests pass:

- create/update internal SEO tools;
- create non-blog interactive pages;
- add privacy-safe tracking events;
- improve internal links;
- update schema.org;
- update sitemap logic;
- create Blog Agent task briefs;
- create experiments;
- update scoring config;
- create new helper tools.

Blocked:

- external outreach;
- buying backlinks;
- collecting sensitive personal data;
- printing secrets;
- deleting production content without backup;
- large irreversible migrations;
- cloaking, doorway pages, or spam SEO;
- changing payment/subscription logic;
- changing authentication without explicit human review.

## 12. Observability

Required logs:

- `agent_runs` table;
- `decisions` table;
- `actions` table;
- `failures` table;
- `goal_agent/logs/goal_agent.log`;
- `goal_agent/logs/decisions.jsonl`;
- `goal_agent/logs/actions.jsonl`.

Dashboards:

- PostHog SEO dashboard;
- daily Goal Agent summary;
- weekly cluster scorecard;
- experiment scorecard;
- cost and action audit report.

Rollback:

- all file writes must record affected files;
- before mutation, save a local backup or rely on git diff if no concurrent changes;
- rollback only files from the current run;
- never remove user or Blog Agent changes.
