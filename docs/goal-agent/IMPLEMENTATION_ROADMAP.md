# Implementation Roadmap

## V1: Read, Measure, Queue

Goal:

- create a safe read-mostly Goal Agent that understands current Blog Agent setup, analytics, content inventory, and queues structured Blog Agent tasks.

### Work Items

1. Create Goal Agent package skeleton.

Likely files:

- `goal_agent/__init__.py`
- `goal_agent/config.py`
- `goal_agent/cli.py`
- `goal_agent/scheduler.py`
- `goal_agent/core/loop.py`
- `goal_agent/core/locks.py`
- `goal_agent/storage/db.py`
- `goal_agent/migrations/001_init.sql`

Likely command:

```bash
python3 -m goal_agent.cli init-db
python3 -m goal_agent.cli run-once --cycle daily_analysis --dry-run
```

Safety check:

- writes only under `goal_agent/`.

Success metric:

- one dry run creates `agent_runs`, report, and no production file changes.

2. Add database tables.

Likely tables:

- `agent_runs`
- `decisions`
- `actions`
- `failures`
- `ideas`
- `opportunities`
- `blog_tasks`
- `content_inventory`
- `page_metrics`
- `posthog_event_definitions`

Safety check:

- SQLite DB only; no production data mutation.

Success metric:

- migration is repeatable and tested.

3. Build content inventory reader.

Likely file:

- `goal_agent/connectors/content_inventory.py`

Reads:

- `index.html`
- `blog/index.html`
- `blog/posts/*.html`
- `blog/_BLOG_REGISTRY.md`
- `sitemap.xml`

Safety check:

- read-only.

Success metric:

- inventory count matches active blog post count and identifies sitemap inclusion.

4. Build analytics ingestion.

Likely files:

- `goal_agent/connectors/posthog.py`
- `goal_agent/connectors/ga4.py`

PostHog:

- aggregate events only.

GA4:

- reuse logic from `blog/_fetch-analytics.sh` or call the Analytics Data API in Python.

Safety check:

- no secret values printed;
- no personal data stored.

Success metric:

- daily page metrics populate for top pages.

5. Add GSC connector placeholder.

Likely file:

- `goal_agent/connectors/gsc.py`

Behavior:

- if credentials are missing, log integration missing and continue.

Safety check:

- no failure if GSC is not configured.

Success metric:

- run summary clearly reports GSC unavailable or returns aggregate query data.

6. Create Blog Agent task queue.

Likely files:

- `goal_agent/queues/blog_tasks.jsonl`
- `goal_agent/exports/blog_task_snapshot.md`
- `goal_agent/connectors/blog_registry.py`

Safety check:

- do not change `auto-blog.sh` in the first PR unless explicitly included.

Success metric:

- top 3 queued tasks are exported with evidence and success metrics.

7. Create daily analysis report.

Likely file:

- `goal_agent/exports/daily_seo_report.md`

Safety check:

- redact secret-like strings.

Success metric:

- report includes top opportunities, risks, and next actions.

### Recommended First Implementation PR

Scope:

- add `goal_agent/` skeleton;
- add SQLite schema;
- add read-only content inventory;
- add read-only sitemap parser;
- add report generation;
- add blog task queue export;
- no production page changes;
- no Blog Agent prompt changes yet.

## V2: Tracking And SEO Optimization

Goal:

- improve privacy-safe measurement and create optimization workflows.

### Work Items

1. Standardize PostHog event schema.

Likely files:

- `scripts/posthog-tracking.js`
- `blog/_template.html`
- `index.html`

Safety check:

- whitelist properties;
- no raw inputs;
- no personal data.

Success metric:

- 95% of SEO page views include `page_id`, `content_type`, and `topic_cluster`.

2. Add conversion analyzer.

Likely file:

- `goal_agent/tools/verified/posthog_conversion_analyzer.py`

Safety check:

- aggregate data only.

Success metric:

- page and cluster conversion scores populate daily.

3. Add internal link optimizer.

Likely files:

- `goal_agent/connectors/internal_links.py`
- `goal_agent/tools/verified/internal_link_graph_analyzer.py`

Safety check:

- V2 should create link insertion requests first, not mass-edit blog posts.

Success metric:

- orphan pages and high-value link opportunities are detected.

4. Add content decay detector.

Likely file:

- `goal_agent/tools/verified/content_decay_detector.py`

Safety check:

- refresh tasks only; no automatic rewriting.

Success metric:

- decayed pages create evidence-backed `article_refresh` tasks.

5. Article refresh queue.

Likely table:

- `blog_tasks` with `task_type='article_refresh'`.

Integration point:

- `blog/_prepare_blog_context.py` reads Goal Agent task export.

Safety check:

- Blog Agent remains the article writer.

Success metric:

- refreshed articles show recovery in 28 to 90 days.

## V3: Interactive SEO Assets And Experiments

Goal:

- build non-blog SEO infrastructure that creates value beyond articles.

### Work Items

1. Interactive page builder.

Likely files:

- `goal_agent/tools/verified/interactive_page_generator.py`
- `tools/` or `lernen/` static page directory chosen by implementation PR.

Allowed assets:

- calculators;
- visualizers;
- quizzes;
- exam simulators;
- interactive learning pages.

Safety check:

- no raw answer tracking;
- mobile layout verified;
- schema valid;
- sitemap updated in dry run first.

Success metric:

- tool starts, completions, and CTA clicks are tracked.

2. Experiment engine.

Likely files:

- `goal_agent/core/experiments.py`
- `goal_agent/connectors/posthog.py`

Tables:

- `experiments`
- `page_metrics`
- `decisions`

Safety check:

- no dark patterns;
- no personal data;
- experiments are reversible.

Success metric:

- at least one experiment reaches a clear keep/stop decision.

3. Schema markup generator.

Likely file:

- `goal_agent/tools/verified/schema_markup_generator.py`

Integration points:

- `blog/_template.html`;
- future interactive templates.

Safety check:

- markup must match visible content.

Success metric:

- active blog and interactive pages have valid relevant JSON-LD.

## V4: Toolsmith And Self-Improvement

Goal:

- allow constrained tool creation and evidence-backed scoring/prompt improvements.

### Work Items

1. Toolsmith lifecycle.

Likely files:

- `goal_agent/tools/registry.json`
- `goal_agent/core/toolsmith.py`
- `goal_agent/tests/`

Safety check:

- generated tools start in `experimental`;
- cannot be used until tests pass and registry status is `verified`.

Success metric:

- first self-created helper tool passes tests and is registered.

2. Prompt version evaluation.

Likely tables:

- `prompt_versions`
- `experiments`
- `learnings`

Integration:

- create recommendations for Blog Agent prompt changes, not direct broad rewrites.

Safety check:

- human review for active Blog Agent prompt changes.

Success metric:

- prompt variants are linked to output quality and performance.

3. Scoring weight self-improvement.

Likely files:

- `goal_agent/core/scoring.py`
- `goal_agent/config/scoring_weights.json`

Safety check:

- every change has rollback condition and revalidation date.

Success metric:

- scoring changes improve conversion-weighted outcomes.

## V5: Full Autonomous SEO Growth Governor

Goal:

- continuous safe SEO growth system with automatic analysis, tasking, implementation, validation, rollback, and learning.

### Capabilities

- continuous scheduled operation;
- PostHog and GSC feedback loops;
- content decay recovery;
- internal link optimization;
- interactive SEO asset creation;
- experiment engine;
- safe Toolsmith;
- strategy self-improvement;
- cost tracking;
- daily/weekly/monthly reports;
- rollback strategy;
- action audit log.

### Safety Gate

Before V5, require:

- stable V1-V4 runs for at least 30 days;
- no privacy incidents;
- no broken Blog Agent cycles caused by Goal Agent;
- tests for all write-capable tools;
- documented rollback procedures;
- cost cap enforcement;
- clear human review path for high-risk actions.

### Success Metric

The Goal Agent is successful when:

- organic app-relevant conversions increase;
- useful pages and tools grow without spam patterns;
- Blog Agent receives better tasks and briefs;
- technical SEO gaps decline;
- decisions are auditable;
- failed actions are safely contained;
- learnings improve future prioritization.
