# PostHog Event Schema

## Principles

Tracking must be useful for SEO and conversion decisions while remaining privacy-safe.

Do collect:

- page identifiers;
- content taxonomy;
- normalized CTA/tool/quiz events;
- aggregate engagement signals;
- experiment identifiers;
- device and traffic source categories.

Do not collect:

- personal names;
- emails;
- phone numbers;
- raw student answers;
- free-text learning input;
- school identity unless intentionally and legally collected elsewhere;
- sensitive learning data;
- unnecessary identifiers.

## Current Integration Point

Current script:

- `scripts/posthog-tracking.js`

Recommended future metadata sources:

- `data-page-id`
- `data-slug`
- `data-topic-cluster`
- `data-primary-keyword`
- `data-search-intent`
- `data-content-type`
- `data-template-version`
- `data-agent-version`
- `data-agent-run-id`
- `data-experiment-id`

These can be added to `<body>` or a top-level `<main>` in:

- `index.html`
- `blog/_template.html`
- future interactive page templates.

## Standard Event Names

### `seo_page_view`

Captured when an SEO-relevant page is viewed.

Properties:

- `page_id`
- `slug`
- `canonical_url`
- `topic_cluster`
- `primary_keyword`
- `search_intent`
- `content_type`
- `template_version`
- `agent_version`
- `agent_run_id`
- `experiment_id`
- `traffic_source`
- `device_type`

### `seo_scroll_depth_reached`

Captured at 25, 50, 75, and 90 percent.

Properties:

- all common page properties;
- `scroll_depth_percent`.

### `seo_internal_link_clicked`

Captured when a user clicks an internal link.

Properties:

- all common page properties;
- `target_slug`;
- `target_content_type`;
- `target_topic_cluster`;
- `link_position`;
- `anchor_category`.

Avoid raw anchor text if it could contain user-provided text. For normal static nav/blog links, raw text is low risk, but normalized categories are preferred.

### `seo_cta_clicked`

Captured when a user clicks a money-relevant CTA.

Properties:

- all common page properties;
- `cta_type`;
- `cta_location`;
- `cta_variant`;
- `destination_type`.

Allowed `cta_type` examples:

- `app_download`
- `app_store`
- `play_store`
- `contact`
- `newsletter`
- `tool_start`
- `quiz_start`

### `seo_app_store_clicked`

Captured when the user clicks an app-store destination.

Properties:

- all common page properties;
- `store`;
- `cta_location`;
- `app_variant`.

Allowed `store`:

- `apple_app_store`
- `google_play`
- `unknown`

### `seo_tool_started`

Captured when an interactive SEO tool starts.

Properties:

- all common page properties;
- `tool_type`;
- `tool_id`;
- `difficulty_level`;
- `input_mode`.

Do not send raw input.

### `seo_tool_completed`

Captured when an interactive SEO tool completes.

Properties:

- all common page properties;
- `tool_type`;
- `tool_id`;
- `difficulty_level`;
- `completion_status`;
- `duration_bucket`;
- `steps_completed_count`.

Do not send raw generated output or raw user input.

### `seo_quiz_started`

Captured when a quiz starts.

Properties:

- all common page properties;
- `quiz_id`;
- `topic_cluster`;
- `difficulty_level`;
- `question_count_bucket`.

### `seo_quiz_completed`

Captured when a quiz completes.

Properties:

- all common page properties;
- `quiz_id`;
- `difficulty_level`;
- `score_bucket`;
- `completion_status`;
- `duration_bucket`.

Do not send question text, raw answers, or student identifiers.

### `seo_answer_checked`

Captured when a single answer is checked in an interactive tool or quiz.

Properties:

- all common page properties;
- `tool_id` or `quiz_id`;
- `question_type`;
- `answer_correct`;
- `attempt_number`;
- `answer_length_bucket`.

Never send raw answer text.

### `seo_return_visit`

Captured when a returning anonymous browser revisits an SEO page under cookieless/session-safe configuration.

Properties:

- all common page properties;
- `return_window`;
- `previous_content_type`;

## Practice-First Events

Practice-first assets also use:

- `practice_started`
- `practice_completed`
- `answer_checked`
- `solution_revealed`
- `mistake_detected`
- `retry_clicked`
- `worksheet_generated`
- `app_cta_clicked_from_practice`

Practice properties:

- `asset_type`
- `subject`
- `grade_level`
- `exam_type`
- `difficulty`
- `solution_mode`
- `interaction_type`
- `expected_learning_outcome`

These events must not include raw student answers. `answer_checked` may include `answer_correct`, `attempt_number`, `answer_length_bucket`, and `question_type`.

## Common Property Definitions

| Property | Type | Example | Notes |
| --- | --- | --- | --- |
| `page_id` | string | `blog:lernplan-erstellen` | Stable internal ID. |
| `slug` | string | `lernplan-erstellen` | No personal data. |
| `canonical_url` | string | `/blog/posts/lernplan-erstellen.html` | Prefer path over full URL if enough. |
| `topic_cluster` | enum | `lernmethoden` | Normalized. |
| `primary_keyword` | string | `lernplan erstellen` | Keyword only, no user text. |
| `search_intent` | enum | `informational` | `informational`, `commercial`, `transactional`, `navigational`, `mixed`. |
| `content_type` | enum | `blog_article` | `landing_page`, `blog_article`, `interactive_tool`, `quiz`, `calculator`, `visualizer`, `exam_simulator`. |
| `template_version` | string | `blog-template-v2` | From template or page metadata. |
| `agent_version` | string | `goal-agent-v1` | Creator/version. |
| `agent_run_id` | string | `run_2026_05_25_0520` | Optional, no secrets. |
| `experiment_id` | string | `exp_internal_links_001` | Optional. |
| `traffic_source` | enum | `organic_google` | Derived client-side only when reliable; server analysis can enrich. |
| `device_type` | enum | `mobile` | `mobile`, `tablet`, `desktop`, `unknown`. |
| `cta_type` | enum | `app_download` | Normalized. |
| `tool_type` | enum | `calculator` | Normalized. |
| `difficulty_level` | enum | `klasse_8` | Avoid school identity. |

## Current-To-Future Event Mapping

| Current event | Future standard |
| --- | --- |
| `landing_page_view` | `seo_page_view` with `content_type=landing_page` |
| `blog_post_view` | `seo_page_view` with `content_type=blog_article` |
| `scroll_depth` | `seo_scroll_depth_reached` |
| `blog_card_click` | `seo_internal_link_clicked` |
| `nav_click` | `seo_internal_link_clicked` or `seo_cta_clicked` |
| `app_download_click` | `seo_app_store_clicked` and/or `seo_cta_clicked` |
| `anchor_click` | `seo_internal_link_clicked` |
| `blog_read_complete` | derived completion event or `seo_scroll_depth_reached=90` |
| `page_engagement_summary` | keep as diagnostic, not primary scoring event |

## Implementation Plan

V1 files:

- update `scripts/posthog-tracking.js` to emit standard `seo_*` events;
- update `blog/_template.html` with normalized data attributes;
- update `index.html` with normalized data attributes;
- update future interactive templates with tool/quiz metadata.

Safety checks:

- block capture of input values;
- ignore textareas and free-text inputs;
- hash nothing personal because hashing personal data is still personal data risk;
- cap property lengths;
- whitelist allowed property keys.

Success metrics:

- 95% of SEO page views include `page_id`, `content_type`, and `topic_cluster`.
- 90% of CTA clicks include `cta_type` and `cta_location`.
- Zero events include email-like strings, raw answers, or names from form fields.
