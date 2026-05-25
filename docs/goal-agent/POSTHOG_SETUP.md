# PostHog Setup

The Goal Agent can query PostHog aggregates if configured.

Required env vars:

```bash
POSTHOG_HOST=https://eu.posthog.com
POSTHOG_PROJECT_ID=119071
POSTHOG_PROJECT_API_KEY=...
POSTHOG_PERSONAL_API_KEY=...
```

Do not print or commit values.

Practice-first events:

- `practice_started`
- `practice_completed`
- `answer_checked`
- `solution_revealed`
- `mistake_detected`
- `retry_clicked`
- `worksheet_generated`
- `app_cta_clicked_from_practice`

Blocked event properties:

- names;
- emails;
- raw student answers;
- free text;
- school identity;
- sensitive learning data.
