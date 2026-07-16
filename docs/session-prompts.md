# Session Prompts — pasteable kickoffs for the next computational tasks

*Written 2026-07-14. Each entry: which model, when to trigger it, and the
prompt to paste verbatim (edit the [BRACKETED] slots first). Fable = design
judgment, failure analysis, prompt authoring. Opus = builds against written
specs. Per CLAUDE.md, any session that finds a genuine design fork STOPS
and writes a memo to docs/decisions/ instead of coin-flipping.*

| # | Task | Model | Trigger |
|---|------|-------|---------|
| 1 | ~~Eval failure analysis~~ | — | DONE 2026-07-16 in-session |
| 2 | ~~Candidate mining~~ | — | DONE 2026-07-16 (mine_candidates.py; none admitted) |
| 3 | ~~Phase 4 redesign~~ | — | DONE 2026-07-16 -> docs/person-model-spec-v1.md |
| 4 | ~~Prompt v4 authoring~~ | — | DONE 2026-07-16 (prompts/v4.md; deploys with #5) |
| 5 | ~~v4 migration + re-eval~~ | — | DONE 2026-07-16: v1.0 live; v4 graded PARTIAL FAIL (results in spec-v1) |
| 6 | ~~CaptureSource + tool adapter~~ | — | DONE 2026-07-15 in-session (Warp): sources/ pkg + warp.py, 62 tests |
| 7 | Invite redemption (D2) build | Opus | after D1+D2 decisions recorded |
| 8 | Stage 1 Socratic review | Opus | whenever core rewrite begins |

---

## 1. Eval failure analysis — FABLE

> I've finished hand-labeling for the schema v1.0 process. Read
> docs/schema-v1-spec.md (esp. Phase 3-4 and the appendix's baseline
> findings). Below I'm pasting: (a) the full `run_eval` output, (b) my
> wish-list memo from labeling, (c) [N] disagreement cases where I want
> your read (my label, extractor's label, and the segment's gist/evidence).
>
> Do failure analysis, not summary: for each weak field, diagnose WHY —
> prompt wording, wrong-shaped category, genuinely hard inference, or my
> labeling inconsistency (say so if you suspect it). Interpret the
> calibration table: are the confidence numbers meaningful, and is the 0.5
> floor right? End with a pre-brief for my Phase 4 session: per field, the
> evidence-backed case for keep / kill / merge / demote, applying the five
> criteria. Where you'd argue both sides equally, say exactly that.
>
> [PASTE run_eval OUTPUT] [PASTE WISH-LIST] [PASTE CASES]

## 2. Candidate mining — OPUS (build + run)

> We're on Phase 3 of docs/schema-v1-spec.md — read it plus
> docs/design-principles.md first. Build `presence/eval/mine_candidates.py`:
> batch all SessionObservation evidence strings + gists from the private db
> (T0, stays local; output file goes in eval/labels/raw/, gitignored)
> through Haiku with one question: "across these work-session descriptions,
> what dimensions VARY that the current schema (phase, momentum, stance,
> openness, topic) does not capture?" Then a second pass to cluster and
> dedupe the answers. Output: ranked candidate list, each with 2-3
> supporting quotes from evidence strings and a first-guess enum shape.
> Proposals only — mark clearly that nothing is adopted here. Constraints:
> no new dependencies; plan in 3-6 bullets before code; run it and give me
> the ranked list plus cost. State what you'd ask a human before trusting
> each candidate.

## 3. Phase 4 redesign sparring — FABLE

> This is the schema v1.0 redesign session (docs/schema-v1-spec.md Phase 4).
> I decide; your job is adversarial quality control. Inputs pasted below:
> eval numbers, failure-analysis pre-brief, candidate mining output, my
> wish-list. For every field I propose to KEEP: argue the cheapest way it
> still fails (rankability test, unknown-rate, consumer check — name its
> actual consumer or it goes). For every field I propose to ADD: attack it
> with the five criteria, especially "could a manager repurpose this" and
> "who consumes it on day one." For every KILL: steelman one round of
> defense, then let it die if the defense is weak. Output: the v1.0 field
> table (name, type, values, consumer, tier default, eval threshold it must
> meet) ready to paste into person-model-spec v1.
>
> [PASTE INPUTS]

## 4. Prompt v4 authoring — FABLE

> Read presence/extract/prompts/v3.md, the v1.0 field table (pasted below),
> and the failure analysis. Author prompts/v4.md in the same file format
> (human preamble above ---, system prompt below). Requirements: every v3
> lesson that still applies survives; new/changed fields get definitions
> with the same care as v3's writing/micro_gist entries; specifically fix
> the measured failures — [E.G.: momentum's flowing-bias; zero abstention
> despite instructions — consider making abstention structurally easier
> rather than more instructed]. Also we will re-run eval right after: state
> which numbers you expect to move and in which direction, so v4 is a
> falsifiable change, not a vibe.
>
> [PASTE v1.0 FIELD TABLE + FAILURE ANALYSIS]

## 5. v4 migration + re-eval — OPUS

> Read docs/schema-v1-spec.md Phase 5 and the new prompts/v4.md. Implement
> the v1.0 schema migration: schema.py changes per the field table below,
> extractor DEFAULT_PROMPT_VERSION=v4 with deterministic guards for any new
> fields, db migration for renamed/removed fields (follow the v2->v3
> pattern: in-place json rewrite + version-bump re-extraction), relay
> WireState update IF any shared-tier field changed (deploy relay BEFORE
> clients; optional-field compatibility like last_active), template updates
> for renamed values, tests updated not deleted. Then re-run
> eval/run_eval.py against my existing labels where fields are comparable
> and report before/after per field. Small diffs, plan first, run the full
> suite, remind me to restart the app and tell dan to pull.
>
> [PASTE v1.0 FIELD TABLE]

## 6. CaptureSource + second-tool adapter — OPUS

> Read docs/multi-tool-capture.md and presence/pipeline/transcript_parser.py.
> Step 1: formalize the CaptureSource interface exactly as the memo
> sketches (discover/events, per-source config+allowlist, per-source canary,
> heartbeat from per-source file mtimes), moving the Claude Code parser
> behind it with zero behavior change — full test suite green before step 2.
> Step 2: build the [Warp|Codex] adapter from the schema/sample pasted
> below. Behavioral-channel features are per-source (see the risk register
> note); mark which ones this source can't support rather than faking them.
> Consent nuance from the memo applies — surface the "new third party"
> sentence in the pilot-kit diff. A broken adapter must render as staleness,
> never corruption. Plan first; the interface refactor and the adapter are
> separate commits.
>
> [PASTE SCHEMA DUMP / SAMPLE LINES]

## 7. Invite redemption build (D2) — OPUS

> Read docs/social-topology.md §3 and the D1+D2 decisions in docs/decisions/
> [DECISION MEMO FILENAME]. Build the invite flow: relay gains
> POST /join (single-use expiring codes carrying identity; joiner's machine
> generates its token locally, sends only the hash; response includes the
> member list for the consent screen) and whatever D1 decided about board
> scoping. Installer drops the name prompt entirely — identity comes from
> the code (delete the failure class, don't improve the warning). The
> audience-loud rule: open invites and joins appear as quiet caption lines
> in the widget, never notifications. mktoken stays for the owner
> bootstrap. Update security-model.md and pilot-kit.md in the same commit —
> the docs and relay tests must keep asserting each other.

## 8. Stage 1 Socratic review — OPUS (recurring, short sessions)

> I'm hand-rewriting [schema.py|rollup.py|behavioral.py] for Stage 1
> (docs/next-steps.md). The strict rule applies to you: read, review, quiz —
> never edit core/ or write the implementation for me. My draft is below /
> at [PATH]. First: find real defects (be specific, cite lines). Second:
> pose 3 edge cases as questions, not answers, and let me respond before
> revealing your take. Third: quiz me — tier filtering, recency-weighted
> mode, why unknown must never win a mode when known values exist — until
> I explain them unaided. Run the existing tests against my version and
> hold me to green without modifying the tests.

---

*Maintenance: when a task completes, strike its row and add the outcome
one-liner. If a session's model argues two designs equally — memo to
docs/decisions/, not a coin flip. That rule outranks these prompts.*
