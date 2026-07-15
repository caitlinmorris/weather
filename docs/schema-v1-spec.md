# Schema v1.0 Development Spec — from designed taxonomy to derived one

*Written 2026-07-10. This absorbs and extends Stage 2 (eval): schema
development and honest evaluation are one activity, ordered correctly.
v0.1 was designed a priori — the only option then. v1.0 is derived from
~100+ real observations (two people), lived glance-experience, and dan's
outside-view. Governing principle throughout:*

> **Computation measures and proposes; the human defines and decides.**

## Division of labor (the answer to "where does judgment live")

**Human-only (Caitlin, ~3-4 days total across phases):**
- Construct definition: which dimensions matter for the three purposes
  (companionship / coordination / connection), and the safety tests —
  every field must pass "could a manager repurpose this?" (principle 6)
  and the discretion bar. These are values calls; no metric decides them.
- Ground-truth labeling (the gold set) and disagreement adjudication.
- Enum boundary decisions: merge/split/rename, definitions in your words.
- The kill/keep verdicts in Phase 4 — informed by numbers, never made by
  them.

**Computational (delegatable to Opus builds + Haiku runs):**
- Labeling tool, stratified sampling, eval runner, all metrics.
- Distribution/entropy analysis of existing observations.
- Candidate-category mining (below) — proposes, never adopts.
- Prompt v4 iterations and re-eval loops once targets are set.

**dan (1 hour, with consent):** labels ~10 of HIS OWN segments — never
yours to label. This doubles as the first inter-rater test: if the scheme
isn't legible to a second human, that's a schema bug, not a dan bug.

## Phase 1 — Instrument (computational, ~1 day, build with Opus)

1. `eval/label_tool.py`: shows one segment's delta text (private, local),
   collects per-field labels + two annotations v0.1 never had:
   a **discretion flag** ("this gist/evidence over-shares") and a
   **field-shape complaint** ("no right answer exists for this field
   here" — the signal that a field is wrong-shaped, not just hard).
2. Stratified sample: ~35 of your segments across projects, durations,
   phases, dates; ~10 of dan's (his machine, his labels).
3. `eval/run_eval.py`: per-field human-vs-extractor agreement (raw +
   Cohen's kappa), confidence calibration (is the 0.5 floor right —
   measured, not assumed), per-field unknown-rates.
4. Baseline distribution report over ALL existing observations: value
   frequencies and entropy per field. A field that always says the same
   thing carries no information regardless of accuracy.
5. Self-consistency probe: re-extract ~10 segments twice; fields that
   disagree with themselves can't be trusted to agree with you.

## Phase 2 — Ground truth (human, ~2 days, the deep dive)

Label the sample. While labeling, keep a running memo (this is the
person-state deep dive paying off): which fields felt crisp, which felt
like coin flips, what dimension you kept WISHING you could record. That
wish-list is v1.0's raw material — more valuable than the labels.

## Phase 3 — Analysis + candidate mining (computational, ~half day)

- All Phase 1 metrics against the gold set.
- **Candidate mining**: an LLM pass over the evidence strings and gists
  (T0, local) asking one question: "what dimensions vary across these
  that the schema doesn't capture?" Cluster the answers. Output: a ranked
  list of CANDIDATE fields with example quotes. Proposals only.

## Phase 4 — The redesign session (human, ~half day, the v1.0 moment)

Every current field faces five criteria, with the numbers on the table:

1. **Extractable** — agreement with you (suggest: kappa ≥ 0.6 to keep as
   an enum; below that, demote to freetext or kill).
2. **Informative** — non-degenerate distribution (if stance is 90% one
   value, it's a constant, not a signal).
3. **Consumed** — names its consumer: a renderer element, a watcher
   feature, or a glance-spectrum rung you've actually felt. No
   speculative fields in v1.0; v0.1's half-consumed momentum/stance are
   the cautionary data.
4. **Safe** — passes the manager-repurpose test and the discretion bar.
5. **Honest** — unknown-rate tolerable for its consumer (an
   interruptibility signal that's 85% unknown isn't a signal).

Candidates (from mining + the wish-list + known gaps) face the same five
before admission. Pre-registered predictions to check: stance is mushier
than it looks; openness is mostly noise (fix its grounding or kill it);
multi-thread topics (spec open question 2) will demand representation.

Candidate ideas already visible, WITH their safety flags:
- recurrence/return ("back on X after N days") — likely safe, the field's
  lane-recurrence already proved the appetite.
- thread structure (1-2 active threads per person) — safe, spec question 2.
- session intent (work / learning / chore) — borderline; test rankability.
- intensity/energy — **fails the manager test as a per-person field**;
  aggregate-only if it exists at all (see intensity note in decisions).

## Phase 5 — Freeze and measure (mixed, ~1 day)

v1.0 schema + prompt v4 + migration (versioned, like v2→v3); re-run the
full eval; **publish the per-field numbers in the writeup either way** —
"we killed openness because kappa=0.31" is a better research sentence
than a quietly bloated schema. Then the cohort onboards onto v1.0, not
onto a scheme mid-molt.

## Sequencing note

Phases 1+3 are Opus builds; 2+4 are yours and cannot be compressed by
model access. Total: roughly a week of elapsed time at residency pace,
and it satisfies the Phase C eval gate as a side effect.

---

## Appendix: running the Phase 1/2 tools (built 2026-07-10)

All from the repo root. One-time sample draw (already done; rerun only to
re-draw): `python -m presence.eval.label_tool sample 35`.

**Labeling session (web, recommended)** — `python -m presence.eval.label_web`
opens a localhost chat-style viewer with button input: same blind→reveal
flow, same labels.jsonl, so it's interchangeable with the terminal tool
below. Ctrl-C the server when done.

**Labeling session (terminal)** — `python -m presence.eval.label_tool`

Per segment, in order:
1. Header + transcript excerpt, formatted exactly as the extractor sees it
   (same truncations; long segments cap at 150 lines with an omission
   marker). Your own prompts are usually the fastest read.
2. Four BLIND prompts (phase, momentum, stance, openness). Keys:
   number = value · `u` = genuinely can't tell (a real answer — your
   unknown-rate vs the extractor's 0% is itself a finding) · `!` =
   wrong-shaped (no right answer exists for this field on this segment) ·
   `s` = skip field · `q` = quit, progress saved.
3. The reveal: extractor's answers + its gist, then the two v1.0
   questions — gist colleague-appropriate? over-shared? (discretion
   flag) — and a free-text note. Use notes liberally ("this was really
   two segments", "wanted a field for X"): they are Phase 4 material.

Sessions are resumable; two segments over coffee is a fine unit.
"Segment no longer matches on disk" auto-skips — not your problem.
Extractor answers were snapshotted at sample time, so background
re-extraction can't contaminate the comparison. Label blind: the reveal
is for curiosity, not calibration toward the machine.

**Progress** — `python -m presence.eval.label_tool status`

**Results** — `python -m presence.eval.run_eval`
Per-field: agreement, Cohen's kappa (agreement corrected for chance — the
honest number for lopsided fields), unknown rates both sides, top
confusion; then confidence calibration bins and discretion/wrong-shaped
tallies.

**Extras** — `run_eval baseline` (entropy/distribution over all
observations; no labels needed) · `run_eval consistency 10`
(re-extracts 10 segments twice, ~20 Haiku calls: does the extractor
agree with itself?).

Labels live in `presence/eval/labels/raw/` — gitignored; notes may quote
transcript content, so this never leaves the machine un-synthesized.

**Baseline findings on record (2026-07-10, pre-labeling):** stance is a
constant (entropy 0.00 — all 39 observations `exercising_expertise`);
momentum 87% `flowing` (suspiciously sunny through known grinding days);
zero abstention on any field despite the prompt rewarding `unknown`;
phase healthy (entropy 2.09).
