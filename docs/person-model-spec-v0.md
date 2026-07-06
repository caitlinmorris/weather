# Person-Model Spec v0

*The typed state layer everything else consumes. Consumers: (1) ambient presence renderer, (2) introduction-event watcher. Design principles doc governs; principles 3 (resolution = privacy), 6 (states not verdicts), and 7 (trajectories over snapshots) bind hardest here.*

## Architecture: two tiers

**Tier A — SessionObservation (private).** Extracted per work session (or ~30-minute segment of a long session) by an LLM extractor running *within the person's boundary*. Never crosses to anyone else. This is where richness and messiness live.

**Tier B — PersonState (published).** A rolling roll-up of recent observations (default window: last 4 working hours, with staleness decay). This is the only object that crosses the personal boundary, and only the fields at the person's consented visibility tier.

Rationale: extraction wants fine granularity to be accurate; sharing wants coarse granularity to be safe. Separating the two lets each be tuned independently, and makes the boundary contract auditable — you can point at exactly one object type and say "only this leaves."

## Visibility tiers (per field, not per person)

Every published field carries one of four tiers. Consent layer (b)/(c) from the principles doc maps onto these.

- **T0 — private.** Never leaves the personal boundary. (All raw chat, all evidence notes, all low-confidence extractions.)
- **T1 — aggregate-only.** Contributes to group-level statistics or the LLM weather report; never rendered attributably. Subject to the k≥2 rule: any group statement derivable from a single person is suppressed.
- **T2 — ambient.** Renderable per-person in the presence display, at the renderer's (low) resolution.
- **T3 — event-eligible.** May appear in an introduction rationale shown to a potential match, gated by the mutual-consent flow.

Defaults are conservative; individuals can opt fields *up* a tier but the system never does so automatically.

## SessionObservation schema

```
SessionObservation {
  observation_id: uuid
  person_id: uuid
  t_start, t_end: timestamps
  source: claude_chat | claude_code | other
  extractor_version: string        # prompts + model, for eval traceability

  topic {
    tags: [3–7 short noun phrases]         # semi-controlled vocabulary, grows over time
    gist: string ≤ 15 words                # WRITTEN TO BE SHARED — the extractor is
                                           # instructed to produce a colleague-appropriate
                                           # one-liner, not a summary of the raw chat
    domain: string                          # coarse: e.g. "ML systems", "writing", "design"
  }

  phase: exploring | shaping | building | debugging | polishing | writing_up | unknown
  momentum: flowing | steady | grinding | stuck | unknown
  stance: learning | mixed | exercising_expertise | unknown
  openness: heads_down | neutral | open | seeking_input | unknown

  trajectory_note: string ≤ 20 words       # direction of movement, not position
                                           # ("moving from schema design toward eval harness")

  confidence: {field → 0–1}                # per enum field; low-confidence → unknown
  evidence: {field → string}               # extractor's justification. T0 forever.
                                           # exists for MY debugging, never for display

  embedding: float[]                        # over gist + tags, model/version recorded
}
```

Design notes:

- **Every enum includes `unknown`, and the extractor is rewarded for using it.** An awareness system that hallucinates states is worse than one that abstains; abstention also renders naturally (a dimmer dot).
- **The gist is authored for its audience.** This is the single most important prompt-design decision: the extractor writes the gist *as the person's own colleague-friendly status line*, which builds translucence into generation instead of bolting redaction on afterward.
- **`momentum` is the sensitive field.** It exists because complementarity (principle 8) needs it, not because anyone should see a stuckness dashboard. See tier defaults below.
- **`evidence` never ships.** It exists so extraction failures can be debugged and the eval set labeled; treating it as T0-forever removes the temptation to render "why we think Dana is stuck."

## PersonState schema (published)

```
PersonState {
  person_id, updated_at
  presence: active | recently_active | away        # T2. Derived from activity timestamps
                                                   # only — never from content. "Away" is
                                                   # deliberately identical for opted-out,
                                                   # revoked, and actually-away (principle 4).

  topic_gist: string                               # T2 default, T3 eligible
  topic_tags: [strings]                            # T2
  phase: enum (mode over window)                   # T2
  stance: enum                                     # T1 default, T3 eligible
  openness: enum                                   # T2 — this is the interruptibility signal
  momentum: enum                                   # T1 default (aggregate/weather only).
                                                   # Person may opt up to T2; system never does.
  trajectory: [last k (topic embedding, phase, t)] # T0 as raw sequence; the WATCHER may
                                                   # consume it, but only its conclusions
                                                   # (a candidate event + rationale) surface, at T3
  staleness: hours since last observation          # T2, drives visual decay
}
```

Roll-up rules v0 (deliberately dumb, revise with data): enums by recency-weighted mode; gist from the most recent observation unless the last three share a topic cluster, in which case the extractor writes a window-level gist; embedding as recency-weighted mean.

## Trajectory & derived features (watcher-internal, T0 → T3 via events only)

- Drift vector: direction of topic-embedding movement over the window.
- Convergence(A, B): decreasing topic distance across ≥3 consecutive states, plus complementarity bonuses — phase offset (one building what the other is exploring), stance offset (learner ↔ expert), history match (B previously dwelt where A is now stuck).
- Dwell/stuckness duration: consecutive `grinding|stuck` observations on a stable topic. Consumed only by the watcher and by T1 aggregates.

## GroupState (for the renderer)

```
GroupState {
  active_count, recently_active_count
  weather: string ≤ 2 sentences        # LLM-written from T1+T2 fields ONLY, with an
                                       # explicit k≥2 instruction and a post-check:
                                       # regenerate if any clause is attributable to
                                       # one person in a group this size
  clusters: [{label, member_count}]    # only clusters of size ≥ 2 are rendered
  per_person: [PersonState @ T2 fields]
}
```

## Boundary contract (the auditable sentence)

Raw conversation content, SessionObservations, evidence strings, and raw trajectories never leave the individual boundary. The only cross-boundary objects are (1) PersonState fields at their consented tier and (2) watcher-emitted introduction events, which contain a human-readable rationale built solely from T3-eligible fields and are gated by mutual consent. Revocation at any layer takes effect at the next roll-up (≤ minutes) and renders as ordinary absence.

## Known open questions (park, revisit with data)

1. **Session segmentation** — what's "a session" in continuous Claude Code use? Start with 30-min activity-gap splitting; wrong answers here mostly cost extraction quality, not safety.
2. **Multi-thread people** — someone juggling two projects breaks the single-gist assumption. Possible v1: PersonState carries 1–2 "threads." Deferred.
3. **Performativity** — once people know their chats feed a display, do they write for the display? This is a real finding either way; note instances in the lab notebook rather than designing around it prematurely.
4. **Decay curves** — how fast should a stale state fade? Tune by feel during self-dogfooding (week 6, living with the display).
5. **Vocabulary drift** — topic tags need occasional consolidation; an LLM pass every few days can merge synonyms. Low stakes.
