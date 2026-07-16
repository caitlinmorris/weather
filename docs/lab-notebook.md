# Lab Notebook — we.ather

*The process journal the research plan mandated: what changed, what the
data contradicted, one decision + rationale per entry. Chronological;
append at the bottom. This file is the writeup's spine — entries stay
short and honest; the polish happens later, elsewhere. Media shot-list at
the end.*

---

## 2026-07-06 — V0.1 sprint (with Fable)

Built: repo, JSONL parser + canary, segmenter, two-store privacy split,
extractor prompt v1 + harness, replay demo. **Decision:** replay-before-
live — test extraction on months of existing history before building
capture. **Data check that shaped everything:** 27 real transcripts
already on disk; the "sensor" existed before the project did. First
extraction outputs accurate but verbose (word caps ignored) → v2.

## 2026-07-08 — the long day: pilot live, and three structural lessons

(One ~20-hour day; some docs mis-dated 07-09/-10/-11 and were corrected.)

- **Dot→field pivot.** One day of living with my own dot: "I had rebuilt
  the Slack presence indicator. The data was private; the form wasn't."
  Anonymous pixel weather replaces identity×status. (Memo: field-vs-dots.)
- **N=2 live with dan; "2 making weather" achieved.** Every onboarding
  failure traced to humans typing identity strings — including a literal
  `<friend>` placeholder registered as a token identity. D2 (invite flow)
  validated three times over before being built once.
- **What the data contradicted:** (1) presence ≠ extraction — the display
  felt broken because aliveness rode the slow semantic path; split into a
  timestamps-only heartbeat. (2) Latency "accumulating" all day wasn't
  perception: whole-session re-extraction grew O(session) per cycle;
  the architecture doc's rolling-delta design existed on paper only.
  Implemented for real. (3) Two Fly machines split-brained the in-memory
  ring — membership flapped between realities. One machine, forever.
- **Transitions-hoverable rule** (memo): changes are legible; ongoing
  states are just weather. Tried hover-anywhere for one hour; it read as
  surveillance; reverted.

## 2026-07-08 (later) — re-sequencing

"Is a shareable version next?" → no. Bottleneck analysis: install
ergonomics are not the barrier; trust-grade extraction (eval as safety
gate) and board topology are. Packaging parked. Boards-not-follows
decided in social-topology.md; audience-loud/activity-quiet principle
named.

## 2026-07-10 — schema v1.0 process designed; instrument built

Spec: derive the taxonomy, don't redesign it (five criteria: extractable/
informative/consumed/safe/honest). Labeling + eval tools built. **Baseline
before any labeling, pre-registered:** stance a constant (entropy 0.00),
momentum 87% flowing, zero abstention anywhere. Web labeling UI replaced
the terminal after plaintext fatigue — reading experience IS the
instrument.

## 2026-07-15 — boards multiply; Warp becomes a sensor

- Lara (Warp user) forces D1/D3/D4. **Decision: host-per-board** — the
  trust boundary tracks the social structure; nobody operates a room
  they're not in. Pilot simplification: I host all boards, disclosed
  ("operator disclosure" now a consent rule). Composite = blend + hover
  provenance; weather lines never aggregate across boards.
- Warp adapter built same day as the probes returned. Best surprise:
  consent filtering lives IN the SQL (unconsented rows never read into
  memory), and `conversation_data` holds no dialogue — so the adapter
  reads less than feared. Command text never leaves the machine; only
  exit outcomes.
- Second placeholder-identity incident: my invented "V" propagated into
  docs as if it were Lara's name. Identity-by-string fails even at the
  documentation layer.

## 2026-07-16 — the eval versus its maker: schema v1.0

27 segments hand-labeled blind. **The instrument failed informatively and
safely:** discretion 27/27 clean (the cohort-gate property passed whole);
judgment quality poor everywhere else. All four pre-registered predictions
confirmed. Momentum anti-calibrated (κ=−0.09, every error →flowing) — the
extractor's own evidence contained the friction it ignored. Stance
degenerate; labeler notes + candidate mining independently discovered the
missing mode (directing). Openness construct-invalid — the labeler
couldn't answer her own question ("open to the AI or to people?").
**Decisions (person-model-spec-v1.md):** openness killed; stance reshaped
to learning/collaborating/directing; momentum repaired via
evidence-first extraction + behavioral channel (now critical path); unit
of analysis fixed to extraction windows; confidence demoted to
diagnostics; zero of eight mined candidates admitted. **v1.0 is smaller
than v0.1.** Prompt v4 authored same day with falsifiable predictions.

## 2026-07-16 (later) — v1.0 ships; v4 graded honestly: partial fail

Migration landed in one push: openness deleted end-to-end (relay accepts-
and-ignores it for un-pulled clients), stance re-axed, observations became
appended extraction windows (no more replace; no mass re-extraction of
history — old versions stand), 47 stance values migrated in place, both
relays redeployed. Then the graded exam: re-extracted all 27 labeled
segments at v4. **What the data contradicted:** evidence-before-verdict —
the strongest prompt-level abstention structure — produced ZERO unknowns;
Haiku will not abstain by being asked. Momentum moved the right direction
(flowing 87→70%, monodirectionality broken) but sits at chance without
the behavioral channel — the two-channel design claim, now measured twice.
**Decision:** no v4.1 prompt-tinkering; abstention becomes a harness
mechanism (disagreement-derived) when queued, and momentum waits for
behavioral.py (Stage 3, mine to write). Failing predictions in public
beats passing vibes in private.

---

## Media shot-list (manual captures, ongoing)

Grab when convenient; store outside the repo or in a gitignored media/
folder. ⚠ = contains real content — review before any publication use.

- [ ] Sticky widget, field view, live with 2 people ("via dan" hover) ⚠
- [ ] The weather line at "2 making weather" (the thesis in four words)
- [ ] Multi-board weather line: "dan: … · lara: still air" (room, lights on)
- [ ] View toggle: same data as dots vs as field (the pivot, visually)
- [ ] Web labeling UI mid-session, blind stage + reveal stage ⚠
- [ ] run_eval output table (the κ numbers that killed openness)
- [ ] Baseline entropy report (stance's 0.00 — a constant, not a signal)
- [ ] Replay mode scrubbing months of history ⚠
- [ ] selftest all-green with two boards
- [ ] Signal dial cycling presence/topic/topic+ (resolution as a dial)
- [ ] Lara's first clouds arriving (when it happens — the Warp milestone)

## Standing habit

Stage closes and surprises get an entry the same day. Media beats memory:
screenshot the moment, caption it here with one line.
