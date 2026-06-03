# Server Audit For SEO Goal Agent

Date: 2026-05-25

This audit describes the current Nachhilfe Mentor website/server state that the future SEO Goal Agent must respect. It is implementation guidance only; no production data should be modified by this document.

## Executive Summary

Nachhilfe Mentor is primarily a static website repository with an autonomous Blog Agent running from `/home/opc/Nachhilfe-Mentor/auto-blog.sh`. The Blog Agent currently publishes active blog posts into `blog/posts/`, updates `blog/index.html`, updates `blog/_BLOG_REGISTRY.md`, regenerates `sitemap.xml` and `feed.xml`, and pushes changes to `main`.

The website has no root package manifest and no web build step. Deployment appears to be static hosting through the `main` branch and `CNAME` for `nachhilfe-mentor.de`.

There is also a separate autonomous social/media engine at `/home/opc/nachhilfe-mentor-engine`. That engine is not the website Blog Agent, but it provides useful patterns for scheduling, SQLite memory, run logs, experiments, and agent orchestration.

The future Goal Agent should be implemented as a separate isolated subsystem, likely under `goal_agent/`, with its own SQLite database, scheduler, logs, locks, tests, and documentation. It should coordinate SEO growth and feed structured tasks to the Blog Agent without becoming a blog writer.

## A. Project Structure

### Main Repository

Repository path:

- `/home/opc/Nachhilfe-Mentor`

Important files and directories:

- `index.html`: main website landing page.
- `styles/modern-tech.css`: main stylesheet.
- `scripts/modern-tech.js`: main frontend behavior.
- `scripts/posthog-tracking.js`: current PostHog client tracking script.
- `blog/`: active blog automation and generated blog content.
- `blog/posts/`: active published blog post HTML.
- `blog/posts/img/`: active blog images.
- `blog/articles/`: JSON article specs consumed by the current publisher.
- `Blog/`: legacy exported blog pages, separate from active lowercase `blog/`.
- `blog-1/`: older PHP blog stubs.
- `.htaccess`: Apache rewrite and redirect rules.
- `robots.txt`: crawler policy and sitemap pointer.
- `sitemap.xml`: generated sitemap.
- `feed.xml`: generated RSS feed.
- `CNAME`: static hosting domain configuration.
- `nachhilfementor2026indexnow.txt`: IndexNow key file.
- `.gitignore`: ignores env files, automation scripts/logs, service account files, and generated caches.

Observed content inventory:

- Total HTML files: about 221.
- Active blog posts in `blog/posts/`: about 159.
- Active JSON article specs in `blog/articles/`: 4.
- Active WebP blog images in `blog/posts/img/`: about 159.
- Legacy uppercase `Blog/` HTML pages: about 39.

### Frameworks And Stack

Current website stack:

- Static HTML/CSS/JavaScript.
- No detected root `package.json`, `requirements.txt`, `pyproject.toml`, or equivalent website build manifest.
- Active blog publishing uses Python scripts and shell automation.
- Legacy uppercase `Blog/` appears to be an exported Astro site, but it is not the active lowercase blog publishing pipeline.

### Package Manager

No package manager is currently required for the website repository itself.

The adjacent social engine uses Python dependencies in `/home/opc/nachhilfe-mentor-engine/requirements.txt`, including APScheduler, OpenAI, Pillow, requests, pytz, and moviepy.

### Database

The website repository has no detected application database for the static site or active Blog Agent.

The adjacent social engine has SQLite persistence under:

- `/home/opc/nachhilfe-mentor-engine/memory/agent.db`
- `/home/opc/nachhilfe-mentor-engine/memory/schema.sql`

The Goal Agent should not reuse the social engine database. It should create its own database, for example:

- `goal_agent/goal_agent.db`
- `goal_agent/migrations/001_init.sql`

### Cron And Scheduler Setup

Observed scheduler state:

- A direct running process exists for `/home/opc/Nachhilfe-Mentor/auto-blog.sh loop`.
- A separate process exists for `/home/opc/nachhilfe-mentor-engine/scheduler.py`.
- User crontab did not show Nachhilfe Blog Agent entries.
- No active tmux session was observed for the Blog Agent, even though setup docs mention tmux.
- No obvious Nachhilfe systemd unit was observed in active systemd units.

Current Blog Agent cadence:

- `auto-blog.sh` uses `INTERVAL_SECONDS=28800`, which is 8 hours.
- This results in roughly 3 Blog Agent cycles per day.

### Deployment Setup

The repository contains `CNAME` for `nachhilfe-mentor.de`. Existing setup documentation says pushing to `main` deploys the website, likely through GitHub Pages or an equivalent static host.

Deployment behavior in `auto-blog.sh`:

- Pull from `origin main`.
- Run Blog Agent.
- Regenerate SEO files.
- Commit changes if needed.
- Push to `origin main`.

Important safety note:

- The current git remote configuration embeds an access token in the remote URL. The token value must not be printed, copied, or moved into documentation. This should be remediated in a separate secret-hygiene PR by replacing the URL with a credential helper or deploy key.

### Logging

Website/Blog Agent logs:

- `auto-blog.log`
- `batch-blog.log`

Adjacent social engine logs:

- `/home/opc/nachhilfe-mentor-engine/logs/agent.log`
- `/home/opc/nachhilfe-mentor-engine/logs/scheduler.out`
- `/home/opc/nachhilfe-mentor-engine/state/orchestrator_log.jsonl`
- `/home/opc/nachhilfe-mentor-engine/state/health_report.json`
- `/home/opc/nachhilfe-mentor-engine/state/health_report.jsonl`

Recommended Goal Agent logs:

- `goal_agent/logs/goal_agent.log`
- `goal_agent/logs/decisions.jsonl`
- `goal_agent/logs/actions.jsonl`
- `goal_agent/state/run_summaries/*.md`

### Environment Config

Secret values were not inspected or printed. Only variable names were observed.

Website repository `.env` variable names:

- `OPENAI_API_KEY`

Adjacent social engine `.env` variable names:

- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- `TIKTOK_REDIRECT_URI`
- `OPENAI_API_KEY`
- `POSTIZ_API_KEY`

Ignored sensitive/local files:

- `.env`
- `google-analytics-sa.json`
- automation logs
- generated context cache files

Recommended future Goal Agent environment variable names:

- `POSTHOG_PROJECT_API_KEY`
- `POSTHOG_PERSONAL_API_KEY`
- `POSTHOG_HOST`
- `GA4_PROPERTY_ID`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `GSC_SITE_URL`
- `GOAL_AGENT_DB_PATH`
- `GOAL_AGENT_DRY_RUN`
- `GOAL_AGENT_MAX_DAILY_COST_EUR`
- `GOAL_AGENT_ALLOWED_WRITE_ROOTS`

The Goal Agent must never print values of these variables.

### Queue And Background Job Systems

Current website Blog Agent has no durable queue. It operates by prompt, generated JSON article specs, static files, and git commits.

Adjacent social engine has job state and retry queues in SQLite and JSONL files. The Goal Agent should use a more explicit queue model:

- `blog_tasks` database table.
- `interactive_page_tasks` database table.
- optional export file for Blog Agent consumption: `goal_agent/exports/blog_task_snapshot.md`.
- optional machine-readable queue: `goal_agent/queues/blog_tasks.jsonl`.

## B. Existing Blog Agent

### Location

Primary active Blog Agent:

- `auto-blog.sh`
- `blog/_prepare_blog_context.py`
- `blog/_publish_article.py`
- `blog/_update_seo.py`
- `blog/_fetch-analytics.sh`
- `blog/_generate-image.sh`
- `blog/_BLOG_REGISTRY.md`
- `blog/_BLOG_STRATEGY.md`
- `blog/_BLOG_CONTEXT_COMPACT.md`
- `blog/_BLOG_CONTEXT_NOTES.md`

Legacy/manual batch automation:

- `batch-blog.sh`
- `start-autoblog-after-batch.sh`

### How It Runs

The active process runs:

- `/bin/bash /home/opc/Nachhilfe-Mentor/auto-blog.sh loop`

The loop:

1. Changes into the repository.
2. Pulls `origin main`.
3. Generates compact blog context with `python3 blog/_prepare_blog_context.py`.
4. Runs Claude with a German Blog Manager prompt.
5. Regenerates SEO files with `python3 blog/_update_seo.py`.
6. Commits and pushes `sitemap.xml` and `feed.xml` if needed.
7. Runs Pinterest fallback.
8. Sleeps for 8 hours.

### Frequency

The active loop sleeps for 28,800 seconds, or 8 hours. This is roughly 3 cycles per day.

### Topic Selection

The Blog Agent prompt asks the model to:

- read `blog/_BLOG_CONTEXT_COMPACT.md`;
- fetch analytics with `bash blog/_fetch-analytics.sh`;
- choose one evergreen German education keyword;
- avoid duplicate titles and slugs;
- prefer a topic that fits active strategy clusters and analytics learnings.

Main strategy clusters in the compact context:

- Lernmethoden
- Prüfungsvorbereitung
- KI und Bildung
- Motivation
- Schule/Studium Alltag
- Fachspezifisch
- Digitale Lerntools
- Wissenschaftliches Arbeiten

### Prompt Storage

The active prompt is embedded directly inside `auto-blog.sh`.

Supporting context files:

- `blog/_BLOG_CONTEXT_COMPACT.md`
- `blog/_BLOG_STRATEGY.md`
- `blog/_BLOG_CONTEXT_NOTES.md`
- `blog/_BLOG_REGISTRY.md`

### Article Generation

The current preferred flow is JSON-first:

1. Generate a WebP image using `blog/_generate-image.sh`.
2. Create `blog/articles/<slug>.json`.
3. Validate uniqueness and required fields via `blog/_publish_article.py`.
4. Publish HTML from `blog/_template.html`.

The JSON article schema includes fields such as:

- `slug`
- `title`
- `meta_description`
- `keywords`
- `tag`
- `subtitle`
- `excerpt`
- `image_filename`
- `image_alt`
- `content_html`
- `registry_summary`

### Publishing

`blog/_publish_article.py`:

- reads one JSON spec from `blog/articles/`;
- validates required fields;
- rejects duplicate post paths, slugs, and titles;
- requires a matching WebP image;
- renders the post from `blog/_template.html`;
- inserts a card into `blog/index.html`;
- updates `blog/_BLOG_REGISTRY.md`.

### Outputs

Blog Agent outputs:

- `blog/articles/<slug>.json`
- `blog/posts/<slug>.html`
- `blog/posts/img/<image>.webp`
- updated `blog/index.html`
- updated `blog/_BLOG_REGISTRY.md`
- updated `sitemap.xml`
- updated `feed.xml`
- git commit and push

### Failure Handling

Current failure handling is mostly shell-level:

- logs success/failure to `auto-blog.log`;
- continues loop after sleeping;
- may still attempt SEO updates after the Claude run;
- has duplicate guards in the publisher.

The system lacks:

- explicit job table;
- retry categorization;
- structured failure records;
- cost budgets;
- global locks between autonomous processes;
- CI checks before deployment.

### What Must Not Be Changed

Do not stop, rewrite, or merge the Blog Agent into the Goal Agent.

The Blog Agent must remain responsible for:

- writing blog articles;
- generating blog article JSON specs;
- generating blog images;
- publishing active blog HTML posts;
- maintaining the active blog registry and blog index through its current publisher.

The Goal Agent may only steer the Blog Agent through:

- structured task queues;
- topic priorities;
- refresh requests;
- internal link insertion requests;
- template or prompt change recommendations;
- evidence-backed briefs.

## C. Existing SEO Pipeline

### Sitemap Generation

`blog/_update_seo.py` generates:

- `sitemap.xml`
- `feed.xml`

It scans:

- `index.html`
- `blog/index.html`
- `blog/posts/*.html`
- selected legal pages

It does not currently include all static pages, old `Blog/` pages, or all subproject pages.

It also submits recent URLs to IndexNow unless run with `--no-ping`.

Recommended Goal Agent integration:

- call `python3 blog/_update_seo.py --no-ping` in tests/dry runs;
- propose sitemap logic changes through a tested PR;
- avoid direct IndexNow submission during analysis runs.

### Robots.txt

`robots.txt`:

- allows all crawlers;
- disallows `/blog/draft/`;
- points to `https://nachhilfe-mentor.de/sitemap.xml`.

### Schema.org

Active lowercase blog pages do not appear to have robust article JSON-LD in the current template.

Legacy uppercase `Blog/` pages include JSON-LD such as `WebSite`, `Organization`, `Article`, and `BreadcrumbList`. Those legacy pages should be treated as reference material only, not as the active pipeline.

Recommended Goal Agent work:

- add tested schema generation to `blog/_template.html`;
- add `Article`, `BreadcrumbList`, and `Organization` markup;
- add `SoftwareApplication` or `LearningResource` schema for interactive pages where appropriate.

### Internal Linking

Current internal links are mostly model-generated in article HTML and tracked narratively in `blog/_BLOG_REGISTRY.md`.

There is no dedicated internal link graph table or analyzer.

Recommended Goal Agent work:

- create a content inventory scanner;
- create an internal link graph builder;
- create safe link insertion requests for the Blog Agent;
- avoid automatic mass link insertion until tests and duplicate checks exist.

### Slugs And Metadata

Active blog posts are static HTML in `blog/posts/<slug>.html`.

Metadata comes from `blog/_template.html` and JSON article fields.

Risk:

- manual changes to generated posts can drift from template updates.
- future template changes must either regenerate posts safely or inject only shared external scripts/styles.

### Content Inventory

There is no structured content inventory table. The active registry is Markdown:

- `blog/_BLOG_REGISTRY.md`

Recommended Goal Agent work:

- parse active files and registry into `content_inventory`;
- store canonical URL, slug, title, meta description, heading structure, word count, cluster, template version, first seen, last modified, and source.

### Indexing-Related Code

Current indexing hooks:

- `robots.txt`
- `sitemap.xml`
- `feed.xml`
- IndexNow in `blog/_update_seo.py`
- canonical URLs in HTML templates

No Google Search Console connector was found.

### Article Update Mechanisms

No dedicated article refresh/update queue was found.

The Blog Agent can be directed by prompt, but there is no structured refresh task system yet.

## D. Existing Analytics

### GA4

Active site and blog template use GA4.

The Blog Agent has `blog/_fetch-analytics.sh`, which:

- uses a Google Analytics service account file if available;
- queries GA4;
- reports top pages, sources, landing pages, devices, and summaries;
- focuses on `/blog` and `/`.

This is currently the Blog Agent's strongest historical feedback signal.

### PostHog

Current PostHog integration:

- client-side script: `scripts/posthog-tracking.js`;
- configured for EU host;
- cookieless mode;
- pageview and pageleave capture;
- autocapture enabled;
- identified-only person profiles;
- input masking for session recording settings.

Current custom events include:

- `website_page_ready`
- `landing_page_view`
- `blog_post_view`
- `app_download_click`
- `blog_card_click`
- `nav_click`
- `contact_click`
- `outbound_link_click`
- `anchor_click`
- `scroll_depth`
- `blog_read_complete`
- `image_view`
- `page_engagement_summary`

Current PostHog data is new and will not yet be enough for long-term SEO decisions. V1 should combine GA4 history with PostHog conversion and engagement data until PostHog has enough volume.

### Missing Analytics For Goal Agent

Missing or incomplete:

- stable `page_id`;
- `slug`;
- `topic_cluster`;
- `primary_keyword`;
- `search_intent`;
- `content_type`;
- `template_version`;
- `agent_version`;
- `agent_run_id`;
- `experiment_id`;
- normalized CTA types;
- normalized tool/quiz event lifecycle;
- internal link destination metadata;
- privacy-safe answer checking events without raw answer text.

### Client-Side Vs Server-Side

Current tracking is client-side.

Recommended V1:

- keep website tracking client-side and privacy-safe;
- add server-side PostHog query connector for analysis only;
- do not send server-side user events until a clear need exists.

## E. Existing Data Persistence

### Website Repository

Current persistence is file-based:

- static HTML;
- Markdown registry and strategy files;
- JSON article specs;
- logs;
- sitemap and feed XML.

### Adjacent Social Engine

The adjacent engine uses:

- SQLite memory DB;
- JSONL orchestrator logs;
- state snapshots;
- retry queues;
- experiment files;
- health reports.

Useful table patterns in the social engine:

- `learnings`
- `strategy_history`
- `orchestrator_cycles`
- `experiments`
- `job_runs`
- `strategy_decisions`
- `retry_jobs`
- `experiment_queue`

The Goal Agent should implement similar concepts but not share that DB.

### Vector Databases

No vector database was found for the website Blog Agent.

V1 does not require a vector DB. It can use SQLite FTS5 or deterministic retrieval over structured tables and compact Markdown summaries.

## F. Current Risks

### Production Safety Risks

- The active Blog Agent runs with broad permissions through Claude.
- It pulls and pushes directly on `main`.
- There is no CI or test gate before static deployment.
- Autonomous systems can dirty the working tree while another agent is inspecting or editing.
- Git conflicts are possible if the Goal Agent also writes files without a lock.
- Remote git credentials are embedded in the remote URL and must not be exposed.

### Privacy Risks

- Future interactive tools and quizzes could accidentally collect free text, student answers, names, emails, or school details.
- Current tracking should be tightened around normalized metadata rather than free-form labels where possible.
- PostHog configuration should remain cookieless unless there is explicit legal review.

### SEO Spam Risks

- The site already publishes at high cadence.
- Creating many thin programmatic pages would create doorway/thin-content risk.
- The Goal Agent must optimize for usefulness, conversions, and durable organic growth, not raw page count.

### Duplicate Content Risks

- Active lowercase `blog/`, legacy uppercase `Blog/`, and old `blog-1/` coexist.
- Sitemaps include only active lowercase blog pages and selected static pages.
- Canonicals and redirects should be audited before expanding SEO infrastructure.

### Agent Runaway Risks

- Existing automation lacks global budget caps.
- Existing automation lacks a central action audit log.
- Existing automation lacks explicit approvals for high-risk changes.
- The future Toolsmith system must be constrained by tests, registry status, and write-root restrictions.

### Deployment Risks

- No build step means generated static files are production artifacts.
- Template changes may not affect old posts unless posts are regenerated or shared scripts are externalized.
- Direct edits to generated posts can be overwritten by future publishing flows.

### Cost Risks

- Blog images use external image generation.
- Claude runs autonomously several times per day.
- Adding SERP APIs, crawl jobs, or LLM analysis could increase recurring cost.

### Context Management Risks

- The Blog Agent already relies on compact generated context.
- A Goal Agent with one giant prompt would become brittle.
- The future system needs explicit context layers, memory retrieval, data snapshots, and run summaries.
