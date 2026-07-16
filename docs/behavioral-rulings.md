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

> _your ruling:_

**A2.** You cancel/interrupt a command halfway. Failure, success, or
neither?

> _your ruling:_

**A3.** Name this measurement. (The starter code called the ratio of
failed runs "error_density" — what would YOU call "how much of what I
tried went wrong"?)

> _your name:_

## B. What is a losing streak?

The strongest stuckness signal: failures in a row.

**B1.** Tests fail. You talk with the AI about why. Tests fail again.
One streak of 2, or two streaks of 1? (Does conversation between
failures break the streak, or is it all one grind?)

> _your ruling:_

**B2.** Tests fail three times; then a DIFFERENT kind of command (say,
just listing files) succeeds; then tests fail again. Did the streak
break at the unrelated success?

> _your ruling:_

**B3.** How many in a row starts to MEAN something to you? (Two fails is
Tuesday; is four a grind? Where's your line, if you have one?)

> _your ruling:_

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

> _your ruling:_

**C2.** How many prompts before a rhythm claim is honest? (Below that:
"we don't know.")

> _your ruling:_

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

> _your ruling:_

## E. When do we say "we don't know"?

**E1.** A window with almost no mechanical activity (you were reading,
thinking, whiteboarding). What should this channel report — and should
"quiet window" itself be a hint, given the sensor-limits lesson that
contemplation is invisible?

> _your ruling:_

**E2.** Anything above you want measured that wasn't asked? (This is the
wish-list question again — it found "directing" last time.)

> _your ruling:_

---

*When you've answered: hand this doc back. Translation returns as (a)
code where every branch cites a ruling number, (b) your scenarios from
B1/B2/etc. as tests using your expected answers, (c) a list of anything
the translator had to decide alone, flagged for your ruling — never
silently chosen.*
