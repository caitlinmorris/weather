# Capture & Overlay Architecture — Implementation Plan v1

*Extends tech-spec-v0. Resolves the critical decision: where the observed interaction lives, how state is extracted from it at maximum realistic resolution, and where presence is rendered. Verified against current Claude Code docs (hooks, statusline) as of July 2026 — re-verify specifics at build time.*

## The decision, stated once

**Host the interaction nowhere. Claude Code is the interaction; we attach to its edges.**

The system never asks anyone to change how they work. Claude Code already (a) writes complete session transcripts — user prompts, assistant responses, tool calls and results — to local JSONL under `~/.claude/projects/`, and (b) fires lifecycle hooks (`SessionStart`, `UserPromptSubmit`, `Stop`, `SessionEnd`, and others) that receive JSON on stdin including the transcript path. That is a supported, passive, full-resolution capture surface. The Anthropic API's role is *extraction* (the model that reads captured deltas and emits SessionObservations), not hosting.

### Rejected alternatives, for the record

- **Custom API chat client / mock terminal.** Maximum control over fake data. Participants won't relocate real work into it, so it measures performativity, not presence. Also the largest build. Retained only as `simulate/` — a replay harness that feeds historical or synthetic transcripts through the pipeline as pseudo-people (already in the plan for week 4).
- **Browser overlay injected into claude.ai.** Real interaction, worst integration position: no hooks, no realtime transcript access (data exports are batch), so capture means DOM-scraping a UI that changes without notice. High maintenance, gray-zone, worse data than the terminal path yields for free. A browser *tab* rendering GroupState is fine and cheap (it's just our own frontend); browser *injection* is out of scope for the residency.
- **claude.ai chat coverage generally**: accepted gap for v1. Residency work is terminal-heavy; chat-side capture via manual export ingestion (`capture_export.py`) remains as a batch supplement. If a participant is chat-primary, their presence is simply staler — rendered honestly via the staleness field.

## Capture layer (revised pipeline/ design)

### Two channels, deliberately separate

**Channel 1 — behavioral (deterministic, free, instant).** Transcript metadata alone carries real signal before any model call: message timestamps and cadence; tool-call density and mix; *test-run failure streaks*; edit→revert loops; error frequency; prompt length trends. In a coding context, `momentum` is substantially computable: three consecutive failing test runs on the same file is stuckness evidence no LLM needs to infer. Implemented as pure functions over parsed transcript events (`core/behavioral.py` — this is a learning component, and honestly one of the most fun ones).

**Channel 2 — semantic (LLM, incremental).** The extractor reads only the *delta* since the last observation, plus the previous SessionObservation, and emits an updated one. This rolling-update design matters for three reasons: cost (no re-reading whole sessions), latency (small calls), and *temporal fields* — `momentum` and `trajectory_note` are about change, so the prompt should literally receive "here's what we believed 20 minutes ago; here's what happened since; update."

The two channels merge in the extractor: behavioral features are computed first and passed *into* the semantic prompt as structured hints ("test failure streak: 4; edit-revert loops: 2"), and each channel corrects the other's blind spot — in both directions. Chat text is a systematically unreliable witness to momentum (people type "great, let's try it!" on their fourth consecutive failure), so when the semantic verdict says `flowing` against a failure-streak-plus-reverts hint block, confidence drops and the field resolves toward `grinding` or `unknown`. But behavior can't distinguish *stuck and suffering* from *methodically bisecting exactly as planned* — the same four failed runs — while the user narrating "ok, halving the search space again" can. Neither channel is ground truth; that mutual coverage is the reason they stay separate rather than being folded into one prompt. Disagreements get logged; they're eval gold. **See Appendix A for a worked end-to-end example.**

### Hook wiring

Hooks must return fast (a stalled hook stalls the session), so every hook is a thin enqueue — under ~50ms — with all real work in a background worker. This enqueue/worker split is the standard pattern for exactly this use case.

```
~/.claude/settings.json (user level — travels across all projects):
  SessionStart  → presence-enqueue session_open   (person goes "active")
  Stop          → presence-enqueue turn_done      (transcript_path + session_id)
  SessionEnd    → presence-enqueue session_close  (begin staleness decay)

worker (single background process, was scheduler.py):
  - debounce turn_done events (extract at most every N turns or M minutes,
    whichever first; N=5, M=10 to start)
  - read transcript delta since last high-water mark (JSONL offset per session)
  - run behavioral features → run semantic extractor → write SessionObservation
    (private db) → rollup → write PersonState (public db) → push to relay
```

Design rules: transcript JSONL on disk is the source of truth (hooks are triggers, not data carriers — if the worker dies, it catches up from the files); per-session high-water marks make extraction idempotent; the JSONL parser gets built against the *actual* format on my machine day 1, behind a narrow interface, with a canary test that fails loudly if a Claude Code update changes the format.

### Extraction cadence & cost envelope

Presence freshness target: minutes, not seconds — the display changes on the timescale of minutes by principle 5, so capture faster than that is waste.

**The design never re-processes conversation history.** Each extraction reads only the delta past the per-session high-water mark; everything before it enters the call as exactly one object — the previous SessionObservation (~300 tokens), which acts as compressed memory (structurally a Kalman-style state update: the old state summarizes what would otherwise be re-read). Per-call budget:

```
previous SessionObservation      ~300 tokens
behavioral hint block            ~100
delta turns (truncated, capped)  ~2,000–4,000
instructions + schema            ~500
────────────────────────────────────────────
per call                         ~3–5k in, a few hundred out
```

At the debounce above, a heavy workday is 15–40 calls/person — pennies per person per day on a Haiku-class model, and *flat over the day* rather than growing with session length. This is exactly why the runtime extractor is the cheap model (tech-spec-v0's design-high/run-cheap loop).

**Delta truncation rules** (the one place cost could still blow up is a single turn containing a 50k-token test log or file dump):
- Tool *results* in the delta are aggressively truncated (first/last ~200 chars each). The behavioral channel has already consumed them in full, deterministically — that's where failure streaks come from — so the semantic extractor mostly needs the human's prompts and Claude's prose.
- Hard per-call input cap; if a delta exceeds it even after truncation, subsample turns (keep first, last, and human prompts preferentially) rather than paying up.

## Overlay layer (revised render/ design): three concentric rings

**Ring 1 — statusline (in-stream whisper).** Claude Code's statusline runs a user-supplied command and renders its output in the session itself. Ours reads the latest GroupState from the local cache and emits a single compact strip — e.g. one glyph per active colleague, brightness = recency, a cluster mark when ≥2 people share a topic cluster. This is presence *inside the moment of work*, the most literal answer to "as close to the real interaction as possible," and it's nearly free once GroupState exists. Its extreme lowness of resolution is a feature twice over (calm + privacy).

**Ring 2 — ambient TUI pane (the primary deliverable).** A persistent terminal app (Python **Textual** — stays in-stack, async, styleable) living in a tmux split or a second terminal window. Renders the group as a slow field: braille/block-character dots that drift with topic movement, warmth with momentum-weather, dim with staleness; the two-sentence weather line beneath. Character-cell resolution enforces translucence *mechanically* — you cannot leak much through 40×12 cells of dim glyphs. Update loop: poll relay every 60s, animate transitions over minutes. The event layer, when it arrives (week 4+), knocks here as a single distinct line with an approve/ignore keybind — never in Ring 1.

**Ring 3 — browser tab (optional, later).** A local web page rendering the same GroupState JSON for wall-screen demos or chat-primary participants. It's our own frontend fed by our own relay — none of the injection brittleness. Build only if weeks 5–6 have slack; the UMAP scatter stub grows into this naturally.

One GroupState JSON contract feeds all three rings; rings differ only in resolution. That makes "resolution is the privacy policy" an actual line of code — each ring declares the max tier and granularity it renders.

## Multi-person transport (the week-4 decision, now made)

Smallest thing that works: a ~150-line FastAPI relay (single small VPS or Fly.io app) with three endpoints — `POST /state` (client pushes PersonState at consented tiers), `GET /group` (returns GroupState; aggregation and the weather-writer run relay-side), `DELETE /state/{person}` (revocation → immediate "away"). Auth: per-person bearer token, TLS, group is a closed list. The relay stores only current PersonStates plus a short ring buffer for trajectory features — raw chat and SessionObservations never leave laptops, so the relay is a low-value target by construction (the boundary contract holds even if it's compromised). Watcher runs relay-side too, since convergence needs the group's trajectories.

Rejected: synced git repo (janky, slow, leaks history in commits), any realtime websocket infra (minutes-scale freshness needs none of it).

## Participant install (pilot kit target)

One script: writes the three hook entries and statusline command into `~/.claude/settings.json` (merging, not clobbering), installs the worker + TUI, writes relay token, runs a synthetic end-to-end self-test. Uninstall/pause is one command and results in ordinary "away." Under 15 minutes, per the plan.

## Revised build order (weeks 2–3 deltas from tech-spec-v0)

1. Day 1–2: JSONL parser against real local transcripts + canary test; `schema.py`; both stores. *(unchanged plus parser)*
2. Day 2–4: hook enqueue scripts + background worker skeleton with high-water marks. *(replaces generic capture)*
3. Day 4–6: `core/behavioral.py` — hand-built, tested on my real sessions.
4. Day 6–9: incremental semantic extractor (prompt v1 designed with Fable; runs on cheap model); behavioral hints wired in.
5. Day 9–11: hand-label ~30 sessions; eval per field; one schema/prompt revision.
6. Day 11–13: `similarity.py`, embeddings, UMAP scatter. *(unchanged)*
7. Day 13–15: `rollup.py` + trajectory v0 + **statusline Ring 1 against my own solo GroupState** — the first live overlay, two weeks in, on real work.

Relay + Ring 2 TUI land in weeks 4–5 per the main plan.

## Risk register (new items)

- **Transcript format drift** → narrow parser interface + canary test; fix is localized.
- **Hook misconfiguration annoys participants** (worst case: a slow hook stalls their session) → hooks do nothing but enqueue; worker failures are silent to the host session by design; self-test in installer.
- **Behavioral features overfit to coding** (test-failure streaks mean nothing in writing sessions) → features are per-source; chat-side momentum leans on the semantic channel with lower confidence.
- **Extractor sees mixed/sensitive content** (people vent, paste secrets) → extractor prompt includes explicit instructions to omit anything personal/emotional/credential-like from all output fields; this goes in the week-3 eval as its own labeled category, not just an aspiration.
- **Relay availability** → clients cache last GroupState; display degrades to "stale group" not blankness.

---

## Appendix A — One extraction cycle, worked end to end

*The canonical example for explaining the pipeline to collaborators. One 20-minute window of a real-shaped coding session.*

**State at 2:00pm** (previous SessionObservation, ~300 tokens — this is the *only* representation of everything before 2:00 that the next call will see):

```
gist:       "debugging flaky auth-token refresh test"
tags:       [auth, testing, race-condition]
phase:      debugging        momentum: steady (0.7)
stance:     exercising_expertise        openness: heads_down
trajectory: "narrowing from CI config toward token expiry logic"
```

**2:00–2:20:** six turns occur in the Claude Code session. The `Stop` hook enqueues after each; the worker's debounce fires at 2:20.

**Step 1 — behavioral channel** (pure functions over the raw delta events, zero model calls, tool outputs read in full):

```
pytest runs: 4, all failing test_token_refresh
edit→revert cycles on token_manager.py: 2
prompt cadence: accelerating; prompt length: shrinking
```

**Step 2 — semantic channel.** One call to the cheap extractor model containing: the 2:00 observation, the hint block above, and the six delta turns with tool results truncated to stubs. Instruction, in essence: *"Given what we believed at 2:00 and what happened since, emit the updated observation."* What only this channel can catch in those turns:

- User: "ugh — it's not the expiry logic, it's the mock clock." → gist updates; `trajectory_note` becomes *"pivoted from token expiry to clock mocking."* A pivot is behaviorally invisible — the failing tests look identical before and after.
- User: "can you just explain how freezegun actually works?" → `stance` shifts toward `learning`. Metadata sees only another prompt.
- User: "let me step back — should this test even exist?" → `phase` drifts from `debugging` toward `shaping`.

**Step 3 — cross-channel correction.** Suppose the semantic verdict for momentum is `flowing` (the user's chat tone was upbeat throughout). Against a 4-failure streak with reverts, confidence drops and the field resolves to `grinding`. The reverse case: if the user had narrated "ok, halving the search space again," the identical behavioral signature would correctly resolve as methodical `steady` — behavior alone cannot tell bisection from flailing. The disagreement, either way, is logged for the eval set.

**Output at 2:20** (written to the private db; rollup then updates the published PersonState at consented tiers):

```
gist:       "chasing a clock-mocking bug in auth test suite"
tags:       [auth, testing, time-mocking]
phase:      debugging (→shaping, 0.4)     momentum: grinding (0.8)
stance:     learning (0.6)                openness: heads_down
trajectory: "pivoted from token expiry to clock mocking; questioning test's existence"
```

**Why the previous state must be an input rather than re-summarizing recent turns:** `momentum` and `trajectory_note` are derivatives — "pivoted," "circling," "still stuck on the same thing" are claims about *change between two states*. A model shown only the last 20 minutes can describe a position; it cannot describe motion.

**Cost of this cycle:** ~3–5k input tokens, a few hundred out, regardless of whether the session is 20 minutes or 6 hours old.

