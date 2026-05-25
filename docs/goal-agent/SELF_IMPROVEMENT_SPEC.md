# Self-Improvement Spec

## Purpose

The Goal Agent should improve its SEO strategy over time, but only through measured, reversible changes. It must store learnings explicitly and avoid silent prompt drift.

## Learning Object

Each learning must contain:

- `id`
- `claim`
- `evidence`
- `confidence`
- `affected_clusters`
- `recommended_policy_change`
- `date`
- `source`
- `status`
- `expiry_or_revalidation_date`

Example:

```json
{
  "id": "learning_2026_06_15_001",
  "claim": "Planning-related articles convert better than generic motivation articles.",
  "evidence": [
    {
      "source": "posthog",
      "summary": "Planning cluster app CTA click rate was 2.1x site blog average over 28 days."
    },
    {
      "source": "gsc",
      "summary": "Planning queries grew 38% impressions over the same period."
    }
  ],
  "confidence": 0.78,
  "affected_clusters": ["lernmethoden", "schule-alltag"],
  "recommended_policy_change": "Increase money_potential_score weight for planning and execution topics by 10%.",
  "date": "2026-06-15",
  "source": "weekly_strategy_review",
  "status": "active",
  "expiry_or_revalidation_date": "2026-07-15"
}
```

## Learning Sources

Allowed sources:

- PostHog aggregate events;
- GA4 aggregate metrics;
- Google Search Console query/page metrics;
- content inventory;
- site crawl;
- internal link graph;
- sitemap audit;
- experiment results;
- Blog Agent output evaluation.

Blocked sources:

- raw personal data;
- raw student answers;
- emails or names;
- anecdotal single-session behavior without aggregation;
- external outreach results.

## Policy Update Rules

A learning may change scoring, prompts, or templates only if:

- confidence is at least `0.70`;
- evidence covers enough traffic or enough repeated observations;
- the change is reversible;
- the expected metric is defined before the change;
- the learning has a revalidation date.

Low-confidence learnings may create ideas, not policy changes.

## Scoring Weight Updates

Scoring changes are stored in:

- `scoring_versions`

Required fields:

- previous weights;
- new weights;
- evidence;
- expected impact;
- rollback condition;
- review date.

Example rollback condition:

- revert if app CTA clicks per organic SEO page view decline by more than 15% for the affected clusters after 28 days.

## Prompt Improvements

Prompt changes are stored in:

- `prompt_versions`

Prompt improvement types:

- Blog Agent task brief format improvements;
- Goal Agent decision format improvements;
- context compression improvements;
- safety wording improvements.

Rules:

- do not mutate the active Blog Agent prompt automatically in V1;
- create a `prompt_template_change_recommendation` Blog Agent task or implementation ticket;
- include before/after prompt text in a docs or review file, not in an untracked shell edit.

## Template Selection

The Goal Agent may learn that certain page formats perform better:

- checklist;
- calculator;
- quiz;
- visualizer;
- simulator;
- comparison guide;
- refresh article;
- internal link hub.

Template changes require:

- tracking coverage;
- schema validation;
- mobile layout check;
- privacy check;
- rollback plan.

## Stop Rules

The Goal Agent should stop or downgrade a strategy when:

- affected pages lose meaningful conversions for two evaluation windows;
- engagement drops and traffic quality worsens;
- SEO risk increases;
- duplicate/cannibalization risk rises;
- privacy review fails;
- implementation cost exceeds expected value.

## Evaluation Windows

Suggested windows:

- PostHog engagement: 7, 14, 28 days.
- Conversion effects: 28 days minimum.
- SEO ranking/click effects: 28 to 90 days.
- Technical fixes: 1 to 7 days.
- Indexing changes: 7 to 30 days.

## Self-Improvement Outputs

Daily:

- new or updated ideas;
- short run summary;
- no broad policy changes.

Weekly:

- learning candidates;
- experiment evaluations;
- scoring adjustment proposals.

Monthly:

- strategy snapshot rewrite;
- archived/revived idea list;
- technical SEO risk review.
