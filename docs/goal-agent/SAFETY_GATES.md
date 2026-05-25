# Safety Gates

Active gates:

- default `dry_run`;
- production writes disabled;
- page generation disabled;
- tracking changes disabled;
- Toolsmith disabled;
- autonomous deploy disabled;
- no Blog Agent source modification;
- no git push;
- no external outreach;
- no SERP scraping;
- PostHog skips safely without credentials;
- generated practice assets require quality checks.

Practice asset gates:

- must include solutions;
- must include difficulty metadata;
- must include interaction controls;
- must include tracking metadata;
- must not be thin;
- must not be doorway/spam content.
- visible German text must use correct umlauts; `ue`, `oe`, and `ae` replacements are blocked unless linguistically correct or technically required.

Adaptive publishing gates:

- no fixed daily publishing limit for normal operation;
- publish/index only when quality-adjusted score is high;
- draft/noindex when quality is promising but uniqueness, indexing, engagement, or conversion evidence is weak;
- hold when duplicate intent, cannibalization, SEO risk, privacy risk, or thinness is too high;
- emergency max exists only to stop runaway loops, not to set growth pace.

Blog Agent Guardian gates:

- the Goal Agent monitors the Blog Agent process, entrypoints, logs, and analytics fit;
- it may recommend Blog Agent topic/prompt/context adjustments;
- direct Blog Agent context writes require `GOAL_AGENT_ALLOW_BLOG_AGENT_CONTEXT_CHANGES=true` plus write-safe mode;
- direct script edits remain blocked unless handled by an explicit implementation change with tests.

Blocked always:

- buying backlinks;
- link spam;
- cloaking;
- doorway pages;
- keyword stuffing;
- sensitive personal data collection;
- raw answer telemetry;
- payment/subscription/auth changes.
