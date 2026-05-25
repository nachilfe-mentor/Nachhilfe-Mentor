# Toolsmith Spec

## Purpose

The Toolsmith system lets the Goal Agent create small helper tools safely. It must not become an unrestricted self-modifying system.

## Controlled Location

Experimental tools:

```text
goal_agent/tools/experimental/
```

Verified tools:

```text
goal_agent/tools/verified/
```

Tool registry:

```text
goal_agent/tools/registry.json
```

Tests:

```text
goal_agent/tests/
```

## Lifecycle

### 1. Identify Repeated Bottleneck

The Goal Agent may propose a tool only when a bottleneck recurs in at least two runs or blocks a high-value workflow.

Required decision log fields:

- bottleneck;
- repeated evidence;
- expected time/cost reduction;
- privacy risk;
- SEO risk;
- failure impact.

### 2. Write Tool Spec

Create a spec in:

```text
goal_agent/tools/experimental/<tool_name>.spec.md
```

Required sections:

- purpose;
- inputs;
- outputs;
- allowed files;
- blocked files;
- external network usage;
- privacy constraints;
- failure behavior;
- tests;
- success metric.

### 3. Implement In Controlled Folder

Implementation path:

```text
goal_agent/tools/experimental/<tool_name>.py
```

Rules:

- no secret printing;
- no destructive filesystem operations;
- no production data mutation;
- no external writes unless explicitly listed in the spec;
- no imports from unverified local scripts unless reviewed;
- deterministic output where possible.

### 4. Write Tests

Test path:

```text
goal_agent/tests/test_<tool_name>.py
```

Minimum tests:

- valid input;
- missing input;
- malformed input;
- privacy redaction;
- dry-run behavior;
- no writes outside allowed paths.

### 5. Run Tests

Command:

```bash
python3 -m pytest goal_agent/tests/test_<tool_name>.py
```

If no test framework exists yet, V1 should add a minimal `pytest` dependency for `goal_agent/` only.

### 6. Document Inputs And Outputs

Each verified tool must document:

- function/class entry point;
- CLI command if any;
- input schema;
- output schema;
- examples;
- known limitations.

### 7. Register Tool

Add to:

```text
goal_agent/tools/registry.json
```

Required fields:

- `name`
- `version`
- `status`
- `file_path`
- `spec_path`
- `test_command`
- `last_test_result`
- `sha256`
- `allowed_inputs`
- `allowed_outputs`
- `risk_level`
- `created_by`
- `verified_at`

Status must be `verified` before use.

### 8. Use Only After Tests Pass

The Goal Agent can invoke only tools with:

- `status=verified`;
- matching file hash;
- passing latest test result;
- allowed input type for the current action.

## Likely First Tools

### `posthog_conversion_analyzer`

Purpose:

- aggregate PostHog SEO events into page and cluster conversion metrics.

Metric:

- app CTA clicks per organic SEO page view.

### `gsc_query_clusterer`

Purpose:

- group Search Console queries into topic clusters.

Metric:

- cluster-level impressions, clicks, CTR, position, and opportunity score.

### `content_decay_detector`

Purpose:

- find pages with declining clicks, impressions, engagement, or conversions.

Metric:

- decay severity and refresh priority.

### `internal_link_graph_analyzer`

Purpose:

- detect orphan pages, weak cluster links, broken links, and high-value link insertion opportunities.

Metric:

- internal link value score and affected pages.

### `serp_gap_scanner`

Purpose:

- evaluate whether a query deserves an article, tool, calculator, visualizer, or simulator.

Metric:

- SERP weakness and interactivity advantage.

### `topic_graph_builder`

Purpose:

- create and update a topic graph from content inventory, GSC queries, and analytics.

Metric:

- topical authority fit score.

### `blog_prompt_evaluator`

Purpose:

- compare Blog Agent output quality by prompt version.

Metric:

- duplicate risk, structure quality, internal link quality, conversion alignment.

### `interactive_page_generator`

Purpose:

- generate non-blog interactive page scaffolds from approved specs.

Metric:

- pages pass tests, schema validation, tracking validation, and privacy checks.

### `sitemap_diff_checker`

Purpose:

- compare expected indexable URLs with `sitemap.xml`.

Metric:

- missing URLs, stale URLs, excluded URLs, invalid lastmod.

### `schema_markup_generator`

Purpose:

- create JSON-LD for blog articles and interactive pages.

Metric:

- valid schema output and no misleading markup.

### `cannibalization_detector`

Purpose:

- detect multiple pages competing for the same query without a clear role.

Metric:

- cannibalization risk and recommended canonical/internal-link action.

### `ranking_anomaly_detector`

Purpose:

- detect sudden search performance changes.

Metric:

- anomaly score and likely cause.

## Blocked Tool Behaviors

Tools must not:

- send outreach;
- buy links;
- scrape search results aggressively;
- collect personal data;
- modify authentication, payment, or subscription logic;
- delete production content without backup;
- make irreversible migrations;
- bypass robots.txt;
- print secret environment values.

## Safety Metric

A Toolsmith release is acceptable only when:

- all tests pass;
- registry hash matches file hash;
- no blocked behavior is detected;
- a rollback plan exists;
- the tool's output can be explained from its inputs.
