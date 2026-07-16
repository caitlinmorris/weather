# Person-Model Spec v1.0 — decided 2026-07-16 (Phase 4 session)

*Derived, not designed: from 27 hand-labeled segments (eval numbers in the
lab record), the labeler's notes, and mined candidates — adjudicated against
the five criteria (extractable / informative / consumed / safe / honest).
v0 spec remains for history; this records the deltas and the field table.*

## The verdicts

| Field | v1.0 status | Why |
|---|---|---|
| topic (tags, gist ≤15w, micro ≤5w, domain) | **unchanged** | 27/27 discretion-clean, 27/27 colleague-appropriate — the shareability layer passed whole |
| phase (exploring/shaping/building/debugging/polishing/writing) | **categories kept; UNIT fixed** | κ=0.20 with diffuse confusion + four "segment too long for one label" notes → the segment was the wrong unit, not the taxonomy |
| momentum (flowing/steady/grinding/stuck) | **kept; extraction repaired** | κ=−0.09, all errors →flowing. The extractor's own evidence contained the friction ("three failed attempts") while the enum said flowing — v4 must derive the enum FROM friction evidence; behavioral.py (Stage 3, now critical path) supplies ground-truth failure signals |
| stance | **reshaped: learning / collaborating / directing / unknown** | Old axis degenerate (κ=0.00, 100% exercising_expertise). The labeler's "functional" note and mined decision_autonomy independently identify the missing mode: DIRECTING — delegating known steps to the AI. Relationship-to-AI replaces human-expertise axis. Stays T1 |
| openness | **KILLED** | Construct invalid: labeler couldn't answer it ("open to the AI or to people?"), κ=−0.10, anti-calibrated, and its disambiguated form (AI-facing) has no colleague-display consumer. Renderer loses the openness ring; heartbeat already carries ambient availability. If interruptibility returns: user-set or behavioral, never LLM-inferred |
| confidence | **T0 diagnostic only** | Self-reported confidence is theater (0.85+ bucket: 37–58% accurate). Floors recalibrated per-field at v4 re-eval; abstention must be structurally easy in v4, not more strongly requested |
| presence, last_active, staleness, trajectory | unchanged | |

## Unit of analysis (the biggest change)

**An observation = one extraction window, appended** — not one
observation-per-segment, replaced as the segment grows. Long sessions
become *sequences* of observations; segments remain only as gap-defined
containers. Consequences: phase labels attach to coherent stretches;
private history gains real trajectory grain; the eval's unit matches the
extraction's unit. (Pipeline: extract_all's delta path appends
window-bounded observations instead of delete-and-replace.)

## Mined candidates: none admitted

decision_autonomy → absorbed into stance's reshape. iteration_friction →
absorbed into momentum's repair. session_continuity → deterministic;
belongs to behavioral.py. collaboration_openness → fails the consumer
criterion even disambiguated; supports the openness kill.
domain_context → duplicates topic.domain. artifact_scope, output_maturity,
discovery_vs_execution → parked (archaeology-fork material; nothing in the
ambient display consumes them). **v1.0 is smaller than v0.1.**

## v4 re-eval targets (falsifiability)

- phase: κ ≥ 0.5 at window grain, else the categories themselves go back
  on trial.
- momentum: κ ≥ 0.4 *after* behavioral hints land; errors must stop being
  monodirectional (→flowing).
- stance: κ ≥ 0.5 on the new axis; distribution non-degenerate.
- discretion: stays 100% — any single over-share flag blocks deployment.
- extractor unknown-rate: must be > 0 somewhere, or abstention still
  isn't real.

## v4 re-eval RESULTS (2026-07-16, whole-segment comparability check)

Graded honestly per the preamble's commitment: **partial failure.**
momentum flowing-share 87%→70% (target <50%; direction right, magnitude
missed); →flowing errors 92%→54% of errors (passed); momentum κ −0.09→0.09
(still ~chance — the semantic channel's ceiling, measured twice: the rest
of the fix is behavioral.py); stance non-degenerate (21 directing /
6 collaborating) but κ=−0.25 vs MAPPED old-vocabulary labels (soft number;
needs a fresh-vocabulary labeling round); **abstention still zero — Haiku
will not abstain by being asked, in any prompt structure.** v1.0 abstention
must be harness-derived (e.g., double-extraction disagreement → unknown) —
queued as a mechanism decision. Phase untestable at segment grain by
design; awaits window-grain labels.

## Migration notes (for the Phase 5 build)

Wire compatibility: `openness` leaves the schema but the relay must
ACCEPT-and-ignore it for one transition window (deploy relay first; old
clients — dan's — still send it until they pull). Renderer: ring removed;
legacy states with openness values render without them. Prompt: v4, with
the v3 discretion sections carried whole.
