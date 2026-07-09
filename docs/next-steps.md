# Next Steps — Staged Plan with Model Directives

*Written 2026-07-06 at the end of the V0.1 build sprint with Fable. This is the
working reference for continuing WITHOUT Fable as a daily build partner. Each
stage names its model, its owner, its exit criteria, and what escalates.
Supersedes the week-by-week pacing in research-plan.md where they differ; the
principles doc still governs everything.*

## Where we actually are (vs. the original plans)

Built and verified, ahead of the original weeks 2–3 scope:

- Capture: JSONL parser + canary test, 30-min segmenter, allowlist config.
- Extraction: prompt v2 (micro_gist, hard word caps), rolling-update harness,
  deterministic guards (confidence floor, enum fallback, word truncation).
- Stores: private/public SQLite split; rollup.py is the sole publisher
  (grep-enforced by tests). 20 real observations extracted.
- Rendering: browser widget (replay + #live modes), hover-reveal signal dial,
  activity-warped playback. Sticky desktop app via pywebview + polling watch loop.
- 30 passing tests including privacy-boundary and repr-leak guards.

Not built, deliberately — this is the queue below: hand-rewritten core
(learning debt), eval numbers, behavioral.py, embeddings/similarity, real
hooks, relay/multi-person, event watcher, TUI.

## Model allocation (the operating rule)

| Role | Model | Where |
|---|---|---|
| Build partner (default) | **Opus** | Claude Code, this repo |
| Mechanical batches: test scaffolds, renames, doc formatting, spec'd-out plumbing | **Sonnet** (`/model sonnet`, switch back after) | Claude Code |
| Runtime extractor | **Haiku** (already wired) | pipeline |
| Design forks, prompt failure analysis, core/ code review & tutoring | **Fable, async** — batch questions for when access exists; interim: Opus in plan mode + a written decision memo in `docs/decisions/` | chat / Claude Code |

Escalation triggers (from tech-spec-v0, still right): Claude argues two designs
about equally → stop, write the fork up in `docs/decisions/`, don't coin-flip.
A bug survives two fix attempts → same. Extractor being *wrong* (not just
sloppy) on real sessions → collect examples for a Fable failure-analysis pass.

## Check-in ritual (every stage, every session)

1. **Open**: tell Claude Code which stage you're on; it reads this file and
   states a 3–6 bullet plan before touching code (CLAUDE.md enforces).
2. **During**: small diffs; run tests after pipeline changes; anything
   surprising goes in the lab notebook immediately, not at the end.
3. **Close**: check the stage's exit criteria; one lab-notebook entry (what
   changed, what the data contradicted, one decision + rationale); commit.

---

## Re-sequencing (2026-07-08) — the road to the residency cohort

Reality since this plan was written: Stage 6 landed early (relay live at
we-ather-relay.fly.dev; N=2 pilot with Daniel starting), the field view
replaced dots, and the topology doc exists. The question "is a more
shareable version next?" was answered **no**: install ergonomics are not
the bottleneck; trust-grade extraction and board topology are. Sequence:

**STATUS 2026-07-09:** N=2 live; "2 making weather" achieved 2026-07-08
(details + lessons in friend-pilot-plan.md). Operational hardening landed
along the way: rolling delta extraction (flat latency/cost), heartbeat
presence, debug mode, single-relay-machine, allowlist review tooling.
Phase A's remaining core is unchanged and now unblocked: the eval, the
lab-notebook habit, and letting the N=2 instruments run. A 3rd *trusted
friend* extends N=2 under the distilled flow in friend-pilot-plan.md;
the cohort still waits for Phase C gates.

**Phase A — now, ~1–2 weeks (Caitlin's irreplaceable work):**
- Run the N=2 pilot and bank its lessons (bugs, glance-outcome pings,
  bad-gist screenshots) before scaling.
- **Stage 2 eval, promoted to safety gate.** Waived consciously for one
  trusted friend; cannot be waived for a cohort — an over-sharing gist has
  real social cost with semi-colleagues, and discretion must become a
  measured category, not an instruction. Hand-labeling ~25–30 sessions IS
  the person-state deep dive; expect it to expose schema weaknesses
  (predictions on record: stance is mushier than it looks; openness is
  mostly noise).
- Stage 1 core rewrite interleaves as the learning track.
- **Residency design feedback WITHOUT onboarding**: talk + replay demo +
  the live widget. Separate "get feedback" from "get users" — the first is
  available this week.

**Phase B — parallel/next (delegatable to Opus once decisions are made):**
- The social plumbing from docs/social-topology.md §6 (now a decision
  docket): board topology, invite redemption, composite view, per-board
  tiers. Decisions are Caitlin's, made in the docket; the builds are
  written specs after that.
- Explicitly parked: packaging (pipx, one-line installers, .app). Revisit
  only if install friction is what an actual participant stumbles on.

**Phase C — cohort onboarding (~2–3 weeks out):** lands on the original
week-7 pilot timing, but with a measured extractor, an invite flow that
deletes the manual token dance, and a board topology that respects the
partner/builders/colleagues reality. Gates: eval numbers exist; N=2 ran
≥1 week; the residency board's default tier is a deliberate decision.

## Stage 0 — Live with it (now → ~3 days). No building.

Run `python -m presence.render.app` daily. Watch your own status while working.
- Log in the notebook: Is the 3h half-life right? Do micro-gists stay accurate
  mid-session? Which dial level do you actually leave it on? Does glancing
  change anything you do?
- Allowed changes: constants only (decay, colors, intervals) — **Sonnet**.
- **Exit:** 3 days of notes; a felt answer to "would I miss this?"

## Stage 1 — Hand-rewrite the core (the learning debt) — ~3-4 days

The V0.1 relaxation ends here. Rewrite by hand, using Claude's drafts as
reference to study against, not to copy: `schema.py`, `rollup.py`, then delete
the drafts. Claude Code (**Opus**) reviews, poses edge cases, quizzes — never
edits core/. Then flip CLAUDE.md's division-of-labor section back to strict.
- **Exit:** your implementations pass the existing 30 tests unmodified; you can
  explain tier filtering and the recency-weighted mode from memory; CLAUDE.md
  strict rule reinstated.

## Stage 2 — Honest eval — ~2-3 days

- Hand-label ~25-30 of your real segments (phase, momentum, stance, openness,
  gist quality y/n). Labels in `presence/eval/labels/` (synthetic-ify before
  any commit).
- Claude Code (**Opus**) builds `run_eval.py`: per-field agreement + a
  calibration read on the confidence floor (is 0.5 the right cut?).
- One prompt revision (v3) from what the labels teach; re-run; log both numbers
  — the before/after is writeup material. Include the "omits sensitive
  content" check as its own labeled category.
- **Exit:** agreement numbers per field in the notebook; v3 deployed or v2
  affirmed.

## Stage 3 — behavioral.py, the real channel — ~2-3 days (yours to write)

Failure streaks, edit→revert loops, cadence trends over parsed events — pure
functions, hand-built (no draft exists; this one is yours from scratch).
Claude Code (**Opus**) reviews + wires the features into the extractor's hint
block, replacing the shallow counts. Re-run eval: does momentum agreement move?
That number is the two-channel argument made empirical.
- **Exit:** hints wired; eval delta logged; momentum disagreements between
  channels logged as eval gold.

## Stage 4 — similarity.py + embeddings (yours) — ~2-3 days

Cosine + nearest-neighbor by hand; embeddings behind one function with
model/version recorded; UMAP scatter of your history. Then the payoff: widget
dot positions become semantic (topic-similar people drift near) — the fake-2D
problem from the design reviews, finally resolved honestly.
- **Exit:** you can whiteboard-explain the math; positions in the widget mean
  something; UMAP figure saved for the writeup.

## Stage 5 — Hooks + statusline (Ring 1) — ~2 days, mostly delegated

Replace the polling watch loop with real SessionStart/Stop/SessionEnd hooks
(thin enqueue <50ms, background worker, per-session high-water marks — spec in
capture-overlay-architecture-v1). Add the statusline strip. **Opus**; the
architecture doc is the plan, follow it.
- **Exit:** kill the poller; presence updates within minutes of real work with
  no manual process; canary + self-test still green.

## Stage 6 — Relay + second person — frontloadable

Full plan in **docs/friend-pilot-plan.md** (transport, build list, onboarding
script, go/no-go gates, N=2 risks). Headlines: the FastAPI relay per the
architecture doc; the hidden prerequisite is the person-identity refactor
(person ≠ project); the friend gets a scoped, spend-capped API key. **Opus.**
- Can run in parallel with Stages 3–5 once its gates are met (Stage 2 eval
  numbers + a clean week of self-watching + cold-tested installer). It does
  NOT need to wait for behavioral.py or embeddings.
- **Exit:** two real people on one display for ≥1 week; revocation renders as
  ordinary absence within minutes; debrief notes + licensed-opener count in
  the lab notebook.

Parked beyond these: event watcher + mutual-consent flow, TUI pane (Ring 2),
weather-writer LLM, vocabulary consolidation. Don't start them mid-stage.
