# Project: ambient social presence for AI work

Read docs/design-principles.md and docs/person-model-spec-v0.md before structural
work. **docs/next-steps.md is the current staged plan — at session start, ask
which stage is active, read that stage, and state a 3-6 bullet plan before
touching code.** docs/v0.1-plan.md is the (completed) V0.1 plan.

## Model use

- Default build partner: Opus. For mechanical batches (test scaffolds, renames,
  spec'd-out plumbing) suggest the user switch to Sonnet via /model, and say
  when to switch back.
- If two designs seem about equally right, or a bug survives two fix attempts:
  STOP. Write the fork as a short memo in docs/decisions/ for an async Fable
  review instead of picking one.
- The runtime extractor stays on Haiku; prompt changes require rerunning eval
  (once run_eval.py exists) before deployment.

## Division of labor

- core/ and extract/prompts/ are conceptually HUMAN-OWNED (learning components).
- **V0.1 relaxation (in effect now, per docs/v0.1-plan.md decision 2):** Claude
  may draft first versions of core/ and prompts to reach the replay demo.
  Caitlin rewrites them by hand afterward; drafts are reference implementations.
  When V0.1 ships, the strict rule returns: never create or modify core/ or
  extract/prompts/; review, suggest tests, and ask Socratic questions only.
- Everything else (pipeline/, eval/, render/, tests) Claude may build freely.

## Working style

- Before implementing anything new or structural: state the plan in 3–6 bullets,
  name the alternatives you rejected and why, wait for approval.
- Small diffs. One concern per change. Explain design decisions as you go.
- No new dependencies without asking. Approved: pydantic, numpy, anthropic,
  pytest, pywebview.
- If you'd argue for two designs about equally, stop and say so — that decision
  escalates to a design conversation, not a coin flip.

## Hard privacy rules

- Never log, print, commit, or copy raw conversation content. This includes test
  output, debug prints, and error messages. Test fixtures use synthetic data only.
- The canary test may read real transcripts but asserts structure only.
- Only the pipeline may read transcripts under the allowlist in
  presence/pipeline/config.py; never widen the allowlist without asking.
- Nothing outside rollup.py writes to the public store. Flag any violation.

## Verification

- Every component gets a test using synthetic fixtures before wiring to real data.
- After touching pipeline/, run the test suite and report the numbers.
