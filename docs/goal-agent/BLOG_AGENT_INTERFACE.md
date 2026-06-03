# Blog Agent Interface

## Relationship

The existing Blog Agent is the only normal blog article writer and publisher.

The Goal Agent may steer the Blog Agent, but it must not replace it. The Goal Agent creates structured tasks with evidence, priorities, and briefs. The Blog Agent decides how to write and publish the article through the existing JSON and publisher flow.

## Current Blog Agent Integration Points

Active files:

- `auto-blog.sh`
- `blog/_prepare_blog_context.py`
- `blog/_publish_article.py`
- `blog/_BLOG_CONTEXT_COMPACT.md`
- `blog/_BLOG_REGISTRY.md`
- `blog/_BLOG_STRATEGY.md`
- `blog/_fetch-analytics.sh`

Recommended V1 integration:

1. Goal Agent writes queued tasks to `goal_agent/queues/blog_tasks.jsonl`.
2. Goal Agent writes a compact human-readable export to `goal_agent/exports/blog_task_snapshot.md`.
3. `blog/_prepare_blog_context.py` reads the export and adds the top tasks to `blog/_BLOG_CONTEXT_COMPACT.md`.
4. `auto-blog.sh` prompt is updated to prefer high-priority Goal Agent tasks when one fits the current Blog Agent cycle.

Do not make the Blog Agent query the Goal Agent database directly.

## Task Status Lifecycle

Allowed statuses:

- `queued`
- `accepted`
- `in_progress`
- `completed`
- `rejected`
- `stale`
- `blocked`

The Blog Agent can initially be read-only against the queue. Later, a small callback script can update status:

```bash
python3 -m goal_agent.cli mark-blog-task-complete --task-id <id> --url <url>
```

## Blog Task JSON Schema

```json
{
  "id": "blog_task_2026_05_25_001",
  "task_type": "new_topic",
  "status": "queued",
  "priority": 90,
  "topic_cluster": "lernmethoden",
  "primary_keyword": "lernplan erstellen",
  "search_intent": "informational_to_conversion",
  "target_slug": "lernplan-erstellen",
  "title_hint": "Lernplan erstellen: einfache Vorlage für Schüler",
  "brief_markdown": "Write a German evergreen article for students and parents. Focus on practical planning steps, common mistakes, and a natural CTA to the app. Do not keyword-stuff.",
  "required_internal_links": [
    {
      "url": "/blog/posts/lernblockade-ueberwinden.html",
      "reason": "Related motivation and execution problem."
    }
  ],
  "avoid_slugs": [
    "lernplan-mit-ki-erstellen"
  ],
  "evidence_refs": [
    {
      "source": "gsc",
      "summary": "Rising impressions for lernplan terms."
    },
    {
      "source": "posthog",
      "summary": "Planning-related pages show above-average app CTA click rate."
    }
  ],
  "success_metric": "Organic entrances and app CTA clicks from the article after 28 days.",
  "deadline": "2026-05-29",
  "created_by": "goal_agent",
  "agent_run_id": "run_2026_05_25_0520",
  "created_at": "2026-05-25T05:20:00+02:00",
  "updated_at": "2026-05-25T05:20:00+02:00"
}
```

## Allowed Task Types

### `new_topic`

Purpose:

- ask the Blog Agent to write one new evergreen article.

Required fields:

- `topic_cluster`
- `primary_keyword`
- `search_intent`
- `brief_markdown`
- `evidence_refs`
- `success_metric`

### `article_refresh`

Purpose:

- ask the Blog Agent to update or rewrite an existing article because of content decay, weak engagement, or outdated information.

Required fields:

- `target_slug`
- `refresh_reason`
- `evidence_refs`
- `specific_sections_to_improve`
- `success_metric`

### `cluster_expansion`

Purpose:

- ask for one article that fills a topic graph gap.

Required fields:

- `topic_cluster`
- `parent_topic`
- `missing_subtopic`
- `required_internal_links`
- `evidence_refs`

### `internal_link_insertion_request`

Purpose:

- ask the Blog Agent to add one or more editorial internal links during its normal publishing/update process.

Required fields:

- `source_slug`
- `target_slug`
- `anchor_guidance`
- `reason`
- `risk_check`

The Goal Agent should not mass-edit blog content directly in V1.

### `prompt_template_change_recommendation`

Purpose:

- recommend a Blog Agent prompt or template improvement.

Required fields:

- `change_summary`
- `evidence_refs`
- `expected_effect`
- `risk_check`
- `rollback_plan`

This task requires human or explicit implementation review before changing `auto-blog.sh` or `blog/_template.html`.

## Blog Task Export Format

File:

- `goal_agent/exports/blog_task_snapshot.md`

Recommended format:

```markdown
# Goal Agent Blog Task Snapshot

Generated: 2026-05-25T05:45:00+02:00

## Top Queued Tasks

### 1. blog_task_2026_05_25_001

Type: new_topic
Priority: 90
Cluster: lernmethoden
Keyword: lernplan erstellen
Intent: informational_to_conversion
Title hint: Lernplan erstellen: einfache Vorlage für Schüler

Brief:
...

Required internal links:
- /blog/posts/lernblockade-ueberwinden.html

Avoid:
- lernplan-mit-ki-erstellen

Success metric:
Organic entrances and app CTA clicks after 28 days.
```

## Safety Rules

The Goal Agent must not:

- tell the Blog Agent to publish spam, doorway pages, or keyword-stuffed content;
- create duplicate topics without a clear differentiation;
- include secret values in briefs;
- include raw PostHog user data;
- include raw student answers;
- include names or emails;
- make the Blog Agent responsible for analytics engineering.

## Success Metrics

V1 success:

- Blog Agent context includes top 3 Goal Agent tasks.
- At least one Blog Agent article per week is chosen from a Goal Agent task.
- Task completion can be linked to resulting URL.
- 28-day post-publication metrics are stored in `page_metrics`.
