# Behavioral Rulings — Caitlin's decisions, in her words

*This document IS the human-written behavioral channel; the Python in
core/behavioral.py is its cited translation. Answer inline under each
question — prose, not code. Where you're torn, say so and say why; "we
can't know this" is a complete answer. Rename anything: the code will
follow your words.*

*Context: these rules read the mechanical record of a work session (tool
runs and their outputs, timestamps, your prompts) to produce honest hints
about friction and rhythm — the facts the AI's cheerful narration can't
be trusted to report. The single number waiting on these rulings:
momentum agreement is at chance (κ=0.09); target is ≥ 0.4.*

---

## A. What does "something went wrong" look like?

The record shows each tool/command run and its output. We need your rule
for reading one run as a failure.

**A1.** Obvious cases: error text, "FAILED", a nonzero exit code. Anything
you'd EXCLUDE — outputs that look alarming but shouldn't count? (e.g., a
search returning nothing; a linter's warnings; output that merely
CONTAINS the word "error" in prose?)

> _your ruling:_  Generally, failure. Exception: output that contains the word "error" in prose but is not associated with an error exit code. 

**A2.** You cancel/interrupt a command halfway. Failure, success, or
neither?

> _your ruling:_ Neither. Dependent on next command - if semantically something like "no, don't..." then failure. If just a new idea or different approach, neutral.

**A3.** Name this measurement. (The starter code called the ratio of
failed runs "error_density" — what would YOU call "how much of what I
tried went wrong"?)

> _your name:_Error_frequency

## B. What is a losing streak?

The strongest stuckness signal: failures in a row.

**B1.** Tests fail. You talk with the AI about why. Tests fail again.
One streak of 2, or two streaks of 1? (Does conversation between
failures break the streak, or is it all one grind?)

> _your ruling:_ If there are more failures than there are successful outcomes in a row, that's a consistent losing streak. Just discussing the "why" doesn't mean it's working. If there is a failure and then a success and then another failure, that success would break it into two streaks of 1. 

**B2.** Tests fail three times; then a DIFFERENT kind of command (say,
just listing files) succeeds; then tests fail again. Did the streak
break at the unrelated success?

> _your ruling:_ No, if the user returns to trying to run the same failed tests, that feels like a continued fail streak.

**B3.** How many in a row starts to MEAN something to you? (Two fails is
Tuesday; is four a grind? Where's your line, if you have one?)

> _your ruling:_ Three or more starts to feel like a grind. Two fails should downgrade from flow if the previous classification was flow state.

**B4.** Your own bisection note from the eval: four deliberate failing
runs while methodically narrowing is not suffering. Should this channel
even try to tell the difference, or report the streak plainly and let
the language channel (which can hear "ok, halving the search space")
overrule? 

> _your ruling:_ 

## C. What does rushing / agitation look like?

**C1.** In your own experience of being stuck: what changes about HOW you
prompt? (Faster? Shorter? More repetitive? Something else entirely —
long silences while you stare?) Describe the signature you believe in;
we'll only encode what you'd stand behind.

> _your ruling:_ Often: shorter, repeated prompts ("no, that still didn't work."). If it really gets frustrating, all caps. This will be person dependent though.

**C2.** How many prompts before a rhythm claim is honest? (Below that:
"we don't know.")

> _your ruling:_ Unsure

## D. What is rework?

**D1.** Describe rework/thrash as YOU experience it in a session (e.g.,
"change something, run it, it breaks, change it back, try again"). What
sequence in the mechanical record would convince you that was happening?

> _your ruling:_ 

**D2.** Constraint, honestly stated: the record currently does NOT say
WHICH file each edit touched, so "edited X, reverted X" can't be detected
literally — only patterns like edit→fail→edit→fail. Is the approximate
pattern worth reporting, or should we extend the record to include file
names (a small privacy question: filenames stay local, but they'd now be
read by this channel)?

> _your ruling:_ Do not include file names.

## E. When do we say "we don't know"?

**E1.** A window with almost no mechanical activity (you were reading,
thinking, whiteboarding). What should this channel report — and should
"quiet window" itself be a hint, given the sensor-limits lesson that
contemplation is invisible?

> _your ruling:_ If there's nothing to report, it should just be classed as quiet; that is, there should be nothing to classify.

**E2.** Anything above you want measured that wasn't asked? (This is the
wish-list question again — it found "directing" last time.)

> _your ruling:_

---

---

## Translator's returned flags (2026-07-21) — yours to rule when ready

Translated: A1, A2, A3 (error_frequency), B1, B2, B3, C1, E1 — code in
core/behavioral.py cites each; your scenarios are tests/test_behavioral.py.
Decided alone and FLAGGED:

1. **(from A1)** "error:" with a colon (compiler-style) counts as a
   failure marker; bare "error" in prose does not. Confirm or adjust.
2. **(from A2)** The "depends what the next prompt says" half of your
   interruption ruling is cross-channel (behavioral event + semantic
   reading) — the behavioral side marks interruptions neutral; the
   semantic overrule isn't built. Fine as-is, or want it queued?
3. **(from B2)** "Returns to the same failed tests" is approximated as:
   only successes from execution-type tools break a streak; read-only
   tool successes (Read/Grep/ls) don't. True same-command matching would
   need command text, which currently stays local-only.
4. **(from C2)** You said "unsure" — provisional floor: 4 prompts before
   any rhythm claim. Adjust when you have a feel.
5. **NOT BUILT:** rework (D1 unanswered — nothing guessed); B4 bisection
   (unruled — streaks report plainly and the language channel may
   overrule, which matches the two-channel doctrine); E2 open.
