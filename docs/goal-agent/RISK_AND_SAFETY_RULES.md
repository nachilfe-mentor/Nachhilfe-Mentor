# Risk And Safety Rules

## Non-Negotiable Rules

The Goal Agent must not:

- stop or break the existing Blog Agent;
- become a normal blog article writer;
- expose, copy, or print secrets;
- modify production data directly;
- send emails or external outreach;
- buy backlinks;
- create link spam;
- create doorway pages;
- cloak content;
- keyword-stuff pages;
- collect personal data that is not needed;
- collect raw student answers;
- collect sensitive learning data;
- change payment, subscription, or authentication logic without explicit human review.

## Secret Handling

Allowed:

- inspect environment variable names;
- check whether required variables are present;
- report missing variable names.

Blocked:

- printing secret values;
- writing secret values into docs;
- embedding tokens in git remotes;
- storing credentials in logs;
- sending secret values to analytics.

Known issue:

- the current git remote URL embeds an access token. Do not print the token. Remediate separately with a credential helper or deploy key.

## Blog Agent Safety

The Blog Agent currently runs continuously. The Goal Agent must coordinate around it.

Rules:

- do not kill the Blog Agent process;
- do not edit Blog Agent generated files while it is mid-run unless a lock exists;
- do not rewrite `auto-blog.sh` without a tested implementation PR;
- do not bypass `blog/_publish_article.py`;
- do not make Blog Agent read secrets or raw analytics data from Goal Agent logs.

## Git And Deployment Safety

Required before file writes:

- record current branch and commit;
- check dirty files;
- identify files the Goal Agent intends to modify;
- avoid unrelated dirty files;
- acquire a lock.

Blocked commands:

- `git reset --hard`
- destructive checkout of user/agent changes;
- force push;
- broad deletion of generated production content.

Deployment rule:

- V1 should generate reports and queues first.
- Code changes should land through small reviewed PRs with tests.

## Privacy Safety

PostHog and analytics rules:

- use cookieless/client-safe tracking unless explicitly reviewed;
- do not identify users;
- do not send emails, names, raw answers, or free text;
- whitelist event properties;
- cap string lengths;
- redact suspicious values before storing analysis snapshots.

Interactive page rules:

- compute answer checks in browser when possible;
- send only normalized outcome events;
- no raw answer telemetry;
- no unnecessary persistence.

## SEO Quality Rules

Allowed:

- useful interactive learning pages;
- calculators;
- visualizers;
- quizzes;
- exam simulators;
- schema markup;
- sitemap improvements;
- internal link improvements;
- content refreshes;
- topic graph improvements.

Blocked:

- doorway pages;
- spun content;
- thin keyword pages;
- mass-generated pages with no unique value;
- misleading schema;
- hidden text;
- cloaking;
- artificial link schemes.

Quality bar:

- every created page must have a clear learner or parent use case;
- every SEO page must have a measurable business or education value hypothesis;
- every page must be internally linked naturally;
- every page must be mobile-safe and indexable only if useful.

## Cost Controls

Required controls:

- daily cost estimate in `agent_runs`;
- max daily budget config;
- no paid SERP API without explicit config;
- image or LLM generation budgets;
- stop nonessential runs when budget is exceeded.

## Runaway Prevention

Required:

- lock file;
- one run at a time;
- action count cap per run;
- file change cap per run;
- task creation cap per run;
- rollback plan for every write action;
- human review gate for high-risk categories.

Suggested caps for V1:

- max 10 new ideas per daily run;
- max 5 Blog Agent tasks per daily run;
- max 0 production page writes by default;
- max 1 non-blog page scaffold per implementation PR.

## Approval Gates

Automatic if tests pass:

- write Goal Agent reports;
- write Goal Agent queue exports;
- update Goal Agent DB;
- create low-risk Blog Agent task briefs.

Requires tests and small implementation PR:

- PostHog event schema code changes;
- sitemap logic changes;
- schema markup changes;
- internal link optimizer;
- interactive page scaffolds.

Requires explicit human review:

- large migrations;
- deleting or redirecting production pages;
- changing authentication;
- changing payments/subscriptions;
- external network integrations with cost;
- changing Blog Agent execution cadence;
- replacing Blog Agent prompt wholesale.

## Rollback Rules

Before mutation:

- record file list;
- record diff summary;
- create backup or rely on reversible git patch;
- define rollback command.

On rollback:

- revert only files changed by current Goal Agent action;
- do not revert unrelated dirty files;
- log rollback in `actions`;
- mark affected experiments paused.
