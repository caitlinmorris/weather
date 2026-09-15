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

## 2026-07-21 — rulings translated; momentum's failure diagnosed to two humans

Lara clarification: she uses Codex-the-model INSIDE Warp — she's a Warp
user; the built adapter is right; Codex paused (no direct test subject).
Behavioral rulings (hers) translated under the judgment-authorship
contract: every branch cites a ruling, her scenarios are the tests, five
translator decisions flagged back. Two translation bugs found by LOOKING
at testimony on her grind segments: silent Edit results counted as
streak-resetting successes (her B1 word "outcomes" fixed it); B2's
"returns to the same failed tests" needed failure-SIGNATURE matching,
not tool-kind proxies. **Result: testimony now honest (grinds 11-33%
error frequency, flows 0-6%) but κ target failed (0.06). Diagnosis is
human-shaped, not mysterious: (1) B4 unruled — machine-grind/felt-flow
bisection segments now "correctly" disagree with her labels; (2) her
grinding is mostly SEMANTIC (few mechanical failures, calm rhythm — the
person-dependence she predicted in C1). Also: run-to-run extraction
variance exceeds the effects chased at n=27 (stance κ swung −0.25→+0.14
on identical inputs) — consistency probe promoted.** Decision: stop
iterating; B4 + C1-personalization go back to the rulings doc; variance
gets measured before any further κ-chasing.

---

## 2026-07-21 (later) — fresh-folder walkthrough earns its keep; invites go GUI

Caitlin ran the full self-hosting path (fresh clone, own Cloudflare
account) while the settings GUI (Tier 0, shipped today) was built in
parallel. The walkthrough surfaced three real bugs, each fixed at
source the same hour: docs never said to leave the relay prompt empty
during host install; make_board_cf never surfaced the deployed URL; and
the big one — a deploy aborted at the subdomain prompt strands the
RELAY_TOKENS secret, so the worker 401s everything (fix: hashes persist
to a local file, failed deploys print two-command recovery). End state:
CF worker passes the full selftest contract — relay sovereignty is real.

Decision + a corrected instinct: invites become one GUI click (mint
token, register on relay, show send-this-privately message once). I had
argued for keeping token-minting in the terminal on "audience-loud"
grounds; Caitlin pushed back — the principle governs displays, not host
tooling, and the human step (privately sending the token) survives the
button. She's right that the barrier was taste, not security: the GUI
subprocess uses the same wrangler/fly login already on disk. Goal
restated plainly: 10–15 real users giving feedback; friction in the
host's path is friction in the study of the *social* questions.

---

## 2026-07-21 (evening) — the orange bias: quoted failure is not felt failure

Caitlin: clouds skew debugging-orange even on planning/docs topics.
Data: 50% of today's states are phase=debugging vs 0–35% on every prior
day. Today's sessions were saturated with PASTED error output — the CF
walkthrough's 401s, selftest FAILs, the dead-widget report — much of it
quoted into conversations whose actual activity was planning, docs, or
tool-fixing. Hypothesis: Haiku reads quoted error text as evidence of
debugging phase — the phase-level cousin of the behavioral channel's
substring false-positives (fixed there with structured patterns; no
mechanical fix exists for narration-level judgment). Checked en route:
momentum/stance 100%-unknown in the public store is NOT a bug — the T1
tier rule in core/schema.py, deliberate.

Open ruling (Caitlin's): does discussing/quoting failures while doing X
count as debugging, or does phase follow the human's activity? Any
prompt change is gated on the eval rerun rule. Variance caveat stands:
single-window classifications are noisy; 50%-vs-baseline is a day-level
signal, not proof for any one cloud.

## 2026-07-22 — ruling deployed; a purge lesson about granularity

Caitlin ruled (easy call, eval-gate consciously waived): quoted/discussed
failure while building or documenting is NOT debugging; phase follows the
activity. Translated into v4.md's debugging definition, cited in place.
Verification by purge + re-extract of the polluted day surfaced a
METHOD lesson: rolling windows are an artifact of live extraction —
re-extracting yesterday after a purge collapses ~74 incremental windows
into ~2 segment-sized ones (covered_until was empty, so each segment
extracted as one big window). Granularity cannot be recreated after the
fact; purges trade resolution for correctness. The 2 coarse re-labels:
1 shaping, 1 debugging (the day genuinely contained real debugging — the
dead widget, the 401s — so orange surviving is honest). The live signal
under the new prompt: today's rolling windows so far are 75% building /
12% shaping / 12% debugging while sessions still quote yesterday's
errors. Real verdict accumulates over the next error-quoting workdays.

## 2026-07-27 — the wire now matches the writing: "verbose" tier

Prep for wider distribution surfaced a docs-vs-wire gap: the dial's
topic+ level looked like the overshare, but the dial is display-only —
tier "topic" was already transmitting the full 15-word gist to every
room, while the writeups promise "a five-word gist." Ruling (Caitlin):
fix at the wire. Tier "topic" now sends micro+tags only; a new
per-board tier — her name: **verbose** — carries the full gist.
Surfacing is membership-gated (the invite's tier line unlocks the dial
level and dropdown option), so dist users who never join a verbose room
never see it, and no forked build exists. Her boards flipped to verbose
to preserve the close-friends pilot. Also shipped: subscription-billed
extraction via the claude CLI (install-time + GUI choice), the minimal
dist package (make_dist.sh, ~100KB), and a guard after a real loss:
generated dist copies got hand-edited, a rebuild ate the edits — the
script now refuses to clobber never-committed content.

## 2026-07-27 (later) — consent starts the clock

Caitlin, watching her own weeks-old chats populate a fresh install: "it
feels a little odd to include things from prior to the consent state."
Ruling: no pre-install history is ever analyzed. The backfill was V0.1
replay-first heritage — the live field's 4h window never needed it, and
its only dist-user value (earlier-today) wasn't worth analyzing
pre-consent sessions at cost during the exact moment trust is being
decided. PRESENCE_START stamped at install; epoch_clamp in extract_all;
first launch now opens honest still air. Bonus: kills the slowest, most
expensive step of onboarding. Open edge (flagged, not decided): a
folder allowlisted LATER still extracts back to the global epoch —
per-folder consent timestamps would close it if it matters.

## 2026-07-28 — dist v1 ready: the walkthrough method's tally

Three days of fresh-folder walkthroughs on the real artifact (download
link included) before sharing: ten shipped fixes, every one found by
being a new user rather than imagining one — solo boards, one .env
dialect, tests-in-dist, host-aware installer, ./weather launcher,
consent-starts-the-clock, Gatekeeper guidance, Dock-app repoint guard,
roster memory through relay amnesia, member-flow install. Verified live
today: three people on the dan board (incl. a duplicate-Caitlin member
install), labels stable through a Fly ring wipe. Known-untested at
ship: CF invite path (simpler twin of the tested Fly one) and a full
subscription-billing workday. we.ather.zip: 132K. Distribution is a
download link + a friend's invite message — nothing routed through
anyone.

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

## 2026-09-14 — the window bounds the drawing, not the reading

Dan widened his allowlist from four projects to two whole folders and
relaunched. Expectation: the app looks at the last four hours. Data: the
first cycle ran 20+ minutes and summarized ~217 sessions going back to
July, roughly $2.50 of Haiku, before he killed it. His .env predates the
consent-starts-the-clock stamp (installs before 07-27 "behave as
before"), so nothing floored the backfill — exactly the open edge the
07-27 entry flagged, hit by an old install instead of a late folder.
The 4h window lived only in the template and the relay push; the scanner
had no notion of time at all. Decision: extraction gets a rolling floor,
the later of PRESENCE_START and now − BACKFILL_HOURS, fed through the
existing epoch_clamp (straddling sessions extract only events past the
edge, so a long-running current session still appears). One constant in
config for relay push and extraction; the template keeps its own 4 by
hand — wiring it through build_page is a separate change. Rejected
24h (six times the cold-start cost, and the relay never ships more than
4h anyway) and an mtime prefilter (an optimization, not a rule; can't
express straddlers). What can't be drawn is never summarized. Dry run
on Dan's data after the change: 2 segments to extract, 348 skipped.

## Standing habit

Stage closes and surprises get an entry the same day. Media beats memory:
screenshot the moment, caption it here with one line.
