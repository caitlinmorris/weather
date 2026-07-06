# Tech Spec v0 — First Functional Components

*Scope: weeks 2–3 of the research plan. Goal: a running pipeline from my own live Claude usage → SessionObservations → PersonState, with a measured extraction-quality number. Renderer and watcher get stubs only.*

## Stack decisions (bias: boring, local, inspectable)

- **Python 3.12+**, minimal dependencies (sqlite3, pydantic for schema types, numpy for vector math, anthropic SDK for the extractor). No framework until the renderer forces one.
- **SQLite** single file, local. Tables mirror the spec's object types 1:1 so the boundary contract is visible in the schema itself: `session_observations` and `evidence` in a *separate database file* from `person_states` — the boundary is literally a file boundary. Publishing = writing to the public db.
- **Local-first everything.** No server until the multi-person pilot forces one; at that point the smallest thing that works (a tiny shared endpoint or synced store) — decide in week 4, not now.
- **Embeddings**: whatever is cheapest/easiest to call, wrapped behind one function with model+version recorded per vector. Similarity math is hand-written (learning component), not a vector-db dependency.

## Repo layout

```
presence/
  core/            # LEARNING COMPONENTS — I write these, Claude Code reviews
    schema.py          # pydantic types straight from the person-model spec
    similarity.py      # cosine, nearest-neighbor, hand-rolled
    trajectory.py      # drift, dwell, convergence detection
    rollup.py          # SessionObservations → PersonState rules
  extract/         # LEARNING (prompts) + DELEGATED (harness)
    prompts/           # versioned extractor prompts, one file per version
    extractor.py       # calls model, validates against schema, writes obs
  pipeline/        # DELEGATED — Claude Code builds
    capture_claude_code.py   # watch ~/.claude/projects/**/*.jsonl transcripts
    capture_export.py        # ingest claude.ai data-export files
    segmenter.py             # 30-min-gap session splitting
    scheduler.py             # cron-ish loop: capture → segment → extract → rollup
    store.py                 # the two sqlite files + boundary enforcement
  group/           # week 4 — stubs only for now
    aggregate.py, watcher.py
  render/          # weeks 5–6 — stub: dump GroupState as JSON + a UMAP scatter
  eval/
    labels/            # my ~30 hand-labeled sessions (synthetic-ified before commit)
    run_eval.py        # extractor-vs-labels agreement, per field
  CLAUDE.md
  docs/            # principles, specs, lab notebook
```

## Capture sources, v0

1. **Claude Code transcripts** (primary — this is where residency work happens): local JSONL session logs, read-only tail. Verify the current on-disk format at build time rather than trusting recall.
2. **claude.ai exports** (secondary, batch): manual export ingestion for chat-side work.
3. Everything behind a `CaptureSource` interface so a future realtime source slots in.

Privacy rule to enforce in code review: capture reads raw chat but writes only into the *private* db; nothing under `pipeline/` may import the public store's write path except `rollup.py`.

## Build order (maps to plan weeks 2–3)

1. `schema.py` + both sqlite stores + fixtures from synthetic data. *(Day 1–2)*
2. `capture_claude_code.py` + `segmenter.py` running on my real logs. *(Day 2–4)*
3. Extractor harness + prompt v1; iterate on my own transcripts. *(Day 4–8)*
4. Hand-label ~30 sessions; `run_eval.py`; get the number; revise schema/prompts once. *(Day 8–11)*
5. `similarity.py` + embeddings + UMAP scatter of my week. *(Day 11–13)*
6. `trajectory.py` v0 + `rollup.py`; scheduler ties it together end-to-end. *(Day 13–15)*

Definition of done: `scheduler.py` runs in the background all day; by evening, `person_states` contains a plausible history of my day, and the eval number exists.

## Model allocation

Three roles, chosen by what each model's marginal capability is worth per call:

**Fable (this chat, in the residency Project) — design and review. Low volume, high leverage.**
- Schema and architecture evolution; adjudicating decisions against the principles doc.
- Extraction-prompt design and, especially, *failure analysis* — reading transcripts where the extractor was wrong and diagnosing why. This is subtle judgment work and the highest-leverage use of the strongest model.
- Code review + tutoring for `core/`: I paste my similarity/trajectory implementations, Fable reviews, poses edge cases, and quizzes me until I can explain the math unaided.
- Weekly plan check-ins against the lab notebook.

**Opus (Claude Code) — implementation volume, governed by CLAUDE.md.**
- Builds everything under `pipeline/`, the extractor harness, stores, eval runner, stubs, tests.
- Constraint profile (see CLAUDE.md below): plan-before-code on anything structural, small diffs, explain decisions, hands off `core/`.

**Sonnet or Haiku (runtime) — the extractor itself.**
- Runs on every session forever, so cost and latency dominate; the labeled eval set is the referee for whether Haiku suffices or Sonnet is needed per field (plausibly: Haiku for tags/phase, Sonnet if `momentum`/`stance` prove subtle).
- Prompts are *designed* with Fable, *deployed* on the cheap model, and every prompt or model change reruns `run_eval.py`. This design-high/run-cheap loop is a pattern worth internalizing.

Escalation rule of thumb: when Opus-in-Claude-Code proposes two architectures and argues both sides plausibly, or when a bug survives two fix attempts, that's a Fable conversation, not a third attempt.

## CLAUDE.md (draft — lives at repo root)

```markdown
# Project: ambient social presence for AI work
Read docs/design-principles.md and docs/person-model-spec-v0.md before structural work.

## Division of labor
- core/ is HUMAN-WRITTEN. Never create or modify files in core/. You may read,
  review, suggest tests for, and ask Socratic questions about core/ code when asked.
- extract/prompts/ is human-written. Propose changes as comments, never edits.
- Everything else (pipeline/, eval/, group/, render/, tests) you may build.

## Working style
- Before implementing anything new or structural: state the plan in 3–6 bullets,
  name the alternatives you rejected and why, wait for approval.
- Small diffs. One concern per change. Explain design decisions as you go.
- No new dependencies without asking. Prefer stdlib + sqlite + numpy.
- If you'd argue for two designs about equally, stop and say so — that decision
  escalates to a design conversation, not a coin flip.

## Hard privacy rules
- Never log, print, commit, or copy raw conversation content. Test fixtures use
  synthetic data only. eval/labels/ content must be synthetic-ified before commit.
- Nothing outside rollup.py writes to the public store. Flag any violation you notice.

## Verification
- Every component gets a test using synthetic fixtures before wiring to real data.
- After touching pipeline/, run eval/run_eval.py and report the numbers.
```

## Deferred decisions (deliberately)

- Renderer technology (menu-bar widget vs. web canvas vs. wallpaper) — week 5, after living with the JSON/UMAP stub.
- Multi-person transport (server vs. synced store) — week 4, sized to the actual pilot pool.
- Realtime claude.ai capture — only if exports prove too laggy for dogfooding.
