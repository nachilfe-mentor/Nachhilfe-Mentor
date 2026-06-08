# Learning Asset Patterns

This file is the design and implementation reference for Goal Agent-owned learning assets. It is not a rigid copy/paste template. The agent should build pages that fit the topic, but every page must satisfy the relevant pattern contract.

## Decision

Use pattern contracts, not fixed page templates.

Why:

- Fixed templates improve consistency but tend to produce generic, repetitive pages.
- Learning assets need different structures: simulations, math trainers, and German writing practice pages have different interaction models.
- Pattern contracts preserve quality while still forcing the agent to think through the learning design.

The agent may reuse CSS/components from existing assets, but it must not blindly clone a layout when the topic needs a different workflow.

## Shared Design Rules

Every learning asset must:

- look like a Nachhilfe Mentor learning tool, not a landing page;
- show the learning activity quickly in the first viewport;
- avoid large empty hero areas;
- use stable responsive dimensions and no horizontal scroll at 375 px;
- use root favicon assets;
- use correct German umlauts in visible text;
- render formatted text with real line breaks and spacing, never visible escape sequences such as `\n`, `\t`, `&bsol;n` or JSON artifacts;
- include `noindex,nofollow` until promoted by the quality gate;
- include metadata, schema plan, internal-link plan and privacy-safe tracking plan in the spec;
- avoid fake interactivity and dead controls.

## Guided Writing Practice Pattern

Use for open German writing skills such as:

- Bildbeschreibung
- Argumentation
- Interpretation
- Erörterung
- Charakterisierung
- Sachtextanalyse
- Redeanalyse

Do not use simulations or fake auto-graders for these topics.

Required first-cycle output:

1. Spec under `/lernmaterialien/entwuerfe/<slug>-spec.md`.
2. Noindex prototype under `/lernmaterialien/deutsch/` or `/lernmaterialien/entwuerfe/`.
3. Asset metadata and cost log when images are generated.

Required page sections:

- compact task header with grade level and learning outcome;
- prompt or image impulse visible near the top;
- task instructions with 2-4 clear subtasks;
- local writing textarea;
- structure scaffold;
- word bank;
- self-check checklist;
- rubric / Bewertungsraster;
- Musterlösung / model solution;
- typical mistakes;
- revision guidance.

Forbidden:

- automatic grading claims for open writing;
- copied random internet images;
- publishing without image rights metadata;
- generic checklist pages without a concrete prompt;
- large empty hero sections.
- visible raw formatting artifacts such as `\n` instead of actual line breaks.

Reference prototypes:

- `/lernmaterialien/deutsch/bildbeschreibung-uebung-schulhof.html`
- `/lernmaterialien/deutsch/bildbeschreibung-uebung-bahnhof.html`
- `/lernmaterialien/deutsch/bildbeschreibung-uebungen.css`
- `/lernmaterialien/deutsch/bildbeschreibung-uebungen.js`

Use these as quality references, not as mandatory final templates. Improve them when a better layout is needed.

## Image Asset Policy

Preferred order:

1. Existing curated local learning asset with metadata.
2. AI-generated image tailored to the learning task, only when generation is explicitly enabled and budgeted.
3. Curated licensed image with source, license and retrieval date.
4. No image if the task does not need one.

Paid image generation is disabled unless `GOAL_AGENT_IMAGE_GENERATION_ENABLED=true` and `GOAL_AGENT_IMAGE_GENERATION_MONTHLY_BUDGET_CENTS` is greater than zero. If disabled, the agent must write an asset-needed note or use existing/curated assets instead of calling an image API.

Generated image metadata must include:

- model;
- quality;
- size;
- prompt;
- generated count;
- estimated cost;
- remaining configured budget;
- alt text;
- QA status;
- intended page;
- rights note.

Keep image count low. A prototype should usually use 1-2 images.

## Step Trainer Pattern

Use for procedural topics with checkable answers:

- Bruchrechnung
- Gleichungen lösen
- Ableitungsregeln
- Prozentrechnung
- Grammatik rules with unambiguous answers

Required:

- generated or varied tasks, not hardcoded single examples;
- active input;
- immediate checking;
- step-by-step solution after mistakes;
- named misconception per level;
- repeated practice and progress;
- at least 3 difficulty levels when appropriate.

## Simulation Pattern

Use for visual models:

- physics experiments;
- chemistry systems;
- biological processes;
- mathematical visual models.

Required:

- research/spec first;
- visible animated or interactive model;
- prediction or input task;
- feedback tied to the model;
- factual correctness checks;
- at least 2-step progression.

## Promotion Rule

Pattern-compliant prototypes are not automatically publishable.

Promotion to indexable `/lernmaterialien/` requires:

- quality gate pass;
- mobile/desktop QA;
- noindex removed intentionally;
- canonical fixed;
- schema added;
- internal links added;
- sitemap update;
- tests pass;
- autonomous deploy gate enabled.
