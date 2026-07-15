# Multi-Tool Capture — Platform-Agnosticism Assessment

*Written 2026-07-07 in answer to: "is this architecture dependent on everyone
using Claude Code?" Short answer: the coupling is one module deep by design,
the polling watcher accidentally removed the hardest dependency, and the
verified per-tool overhead is 0.5–2 days per adapter. The real ongoing cost is
format drift across N undocumented third-party formats.*

## Where the Claude Code coupling actually lives

Exactly two places:

1. `pipeline/transcript_parser.py` + the paths in `config.py` — reads Claude
   Code's JSONL from `~/.claude/projects/`.
2. The *planned* Stage-5 hook wiring (SessionStart/Stop/SessionEnd) — not yet
   built.

Everything downstream is already source-neutral: TranscriptEvent → Segment →
extractor → SessionObservation → rollup → PersonState → relay → renderer.
The schema has carried a `source` field since v0, and tech-spec-v0 already
promised a `CaptureSource` interface — this memo is that promise coming due.

## The accidental architectural win

Because we frontloaded the **polling watcher** instead of hooks, capture
requires nothing from the host tool except a readable local trace. No plugin
API, no hook support, no cooperation. Hooks (Stage 5) are a latency
optimization for Claude Code specifically; every other tool can live on
polling indefinitely. This is what makes agnosticism cheap.

## Per-tool reality (verified 2026-07-07, re-verify at build time)

| Tool | Local trace | Adapter effort | Risk |
|---|---|---|---|
| **Claude Code** | JSONL, documented-ish, hooks available | built | canary in place |
| **Codex CLI** | Full JSONL transcripts (prompts, tool calls, results, timestamps) at `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | ~0.5–1 day — nearest analog to the existing parser | format undocumented; needs own canary |
| **Hermes (Nous)** | SQLite `~/.hermes/state.db`, **documented schema** (sessions + messages tables: role, content, tool_calls, tool_name), open source | ~0.5 day — possibly the easiest of all | low; schema is documented |
| **Warp** | Local SQLite (`warp.sqlite`); schema + structure probes complete 2026-07-15 (docs/warp-schema.txt). **Fully specified**: semantic channel = `ai_queries` (user input, start_ts, working_directory — allowlist filtering IN the SQL, cleanest consent geometry of any tool); behavioral = `commands`/`blocks` (exit codes, `is_agent_executed`; `Failed`/`Cancelled` query statuses as extra signal). `conversation_data` holds NO dialogue (usage metadata only; text is server-side per `server_conversation_token`) — adapter never reads it, so no assistant text ever, and no credits/usage read either. Heartbeat from MAX(start_ts) within allowlist, NOT db mtime (UI activity touches the file). Timestamps naive — assume UTC, verify live at onboarding (the Z-vs-offset lesson). | **~1 day**, green-lit; person-prompts-only extraction matches existing doctrine | drift risk remains (closed source); read-only open while Warp runs |
| **claude.ai chat** | Batch data export | already planned (`capture_export.py`) | staleness rendered honestly |
| **Anything else** | Fallback ladder below | — | — |

Fallback ladder for unsupported tools: (1) batch export ingestion if the tool
exports anything; (2) `presence status "debugging auth tests"` — a manual
one-line self-report CLI. The latter violates the no-behavior-change principle
and would exist only as pilot filler so a friend on an unsupported tool can
participate at low fidelity; if used, label it a violation in the writeup, not
a feature.

## One-time framework work (~1 day, Opus)

- Formalize `CaptureSource` protocol: `discover() -> sessions`,
  `events(session) -> Iterator[TranscriptEvent]`; move the Claude Code parser
  behind it unchanged.
- Per-source config blocks (paths + allowlist per source) replacing the single
  global allowlist.
- Per-source canary test, one per adapter — a broken adapter must fail loudly
  in CI but degrade gracefully in production: **capture failure renders as
  staleness, never as corruption**. The dot dims; nothing lies.
- Per-source behavioral features (already in the risk register: test-failure
  streaks mean nothing outside coding tools; features declare their source).

## The consent nuance agnosticism creates

Platform-agnostic *capture* is not platform-agnostic *extraction*: the
semantic extractor still sends transcript deltas to the Anthropic API. For a
Claude Code user that party already sees everything; for a Codex or Warp user
it is a **new third party reading their work narration**. Consent language for
non-Claude participants must say so explicitly ("read locally; excerpts sent
to Anthropic for state extraction under the study's API key"). A local-model
extractor would dissolve this asymmetry — parked as a v2 note, not a pilot
blocker.

## Recommendation

1. Formalize `CaptureSource` during the friend-pilot build (it touches the
   same files as the person-identity refactor; do them together).
2. Build adapters **demand-driven** — one per actual participant, starting
   with whatever tool the first friend uses. Never speculatively; each adapter
   is an ongoing drift liability, and an adapter nobody uses is pure cost.
3. Sequence preference if choice exists: Hermes (documented schema), then
   Codex (rich JSONL), then Warp (reverse-engineering budget).
4. Claude Code keeps hooks and stays the reference implementation; everyone
   else polls.
