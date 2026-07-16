# Decision memo — judgment-authorship replaces code-authorship for core/

**Trigger:** Stage 3 (behavioral.py) stalled on a translation gap: the
builder-researcher owns the *judgments* (what counts as a failure, what a
losing streak is) but not the vocabulary or appetite for expressing them
as Python. The original "hand-written core" rule conflated two kinds of
ownership.

**Decision:** For core/ components, the human-authored artifact is a
**rulings document** — plain-language decisions with rationale, including
scenario-style test cases in prose. Code is a translation with strict
traceability:

1. Every branch/threshold in the code cites the ruling it implements
   (`# ruling B2`).
2. Anything the translator had to decide alone is flagged back as an open
   question in the rulings doc — never silently chosen.
3. Function and feature NAMES follow the human's language, not
   engineering convention.
4. Verification is behavioral: the human's prose scenarios become tests;
   acceptance = scenarios pass + the pre-registered eval target moves.
   Reading the code is optional; reading the rulings is not.

**Why this is truer to principle 9 (inspectable over clever):** a rulings
doc makes the load-bearing judgments MORE inspectable than hand-written
Python would — they're legible to pilot participants, committee members,
and future collaborators, not just to programmers. The judgments remain
falsifiable and owned; only the typing is delegated.

**Applies to:** behavioral.py now (worksheet: docs/behavioral-rulings.md);
retroactively legitimizes the schema-v1.0 process (which already worked
this way: her labels/notes/verdicts, machine translation); Stage 1's
"rewrite core by hand" is superseded — its replacement is authoring
rulings docs for schema.py and rollup.py if and when their judgments need
revisiting.
