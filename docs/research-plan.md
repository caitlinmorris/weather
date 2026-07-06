# 8-Week Research Plan — Ambient Social Presence for AI Work

*Architecture: a continuously updated person/group-state model feeding two consumers — an always-on ambient presence renderer, and a quiet, conservative introduction-event watcher reusing the prior prototype's mutual-consent flow.*

## Standing threads (all eight weeks)

**Dogfooding pipeline.** From week 1, my own Claude chats are the first dataset; other participants' (residents or remote friends) join later, once instrumentation is solid and the recruitment ask feels natural. Real data reshapes the person-model faster than theorizing.

**Learning components vs. delegated components.** Hand-implemented with Claude Code as reviewer/tutor: state schema and extraction prompts, embedding + similarity math, trajectory/convergence detection, aggregation logic. Delegated to Claude Code: capture plumbing, storage, consent UI scaffolding, renderer boilerplate. The repo's CLAUDE.md instructs: explain design decisions before implementing, prefer simple readable implementations, pause at architectural forks.

**Lab notebook.** A short weekly entry: what changed in the model, what the data contradicted, one design decision and its rationale. This becomes the spine of the final writeup at near-zero marginal cost.

---

## Week 1 — Foundations: literature, principles, spec, consent

- Literature pass (2–3 days, synthesis notes not summaries): Erickson & Kellogg on social translucence and the Babble social proxy; Dourish & Bellotti on awareness; Portholes; Weiser & Brown on calm technology; a sampling of interruptibility work (Fogarty, Hudson, Horvitz). Output: a 2-page "what the field already knows" memo with implications for this design.
- Finalize the design-principles document; circulate to residency mentors/peers for early reaction.
- Draft v0 spec for the person-model layer only: the typed state schema (topic facets, phase, trajectory note, stance, openness), update cadence, and the boundary contract (what derived state crosses the individual boundary; raw chat never does).
- **Design the consent architecture** (the three layers, what data flows where, revocation mechanics) as part of the spec — but defer any recruitment ask. The pilot pool decision (residents, remote friends, or a mix) waits until relationships have formed; informal conversations about the idea can happen naturally as the cohort gels.

**Milestone:** principles final, person-model spec v0.

## Weeks 2–3 — Instrumentation and the state extractor

- Build chat capture for my own Claude usage (export/API/logging — whichever is least invasive to my actual workflow, since distorted usage produces distorted data).
- Hand-build the LLM state extractor against the v0 schema. Iterate prompts against my real transcripts; the schema will be wrong in instructive ways — revise it and log why.
- Small honest evaluation: label ~30 of my own sessions by hand (phase, stuckness, openness); measure extractor agreement. This number goes in the writeup either way.
- Learning module: implement embedding of topic facets and cosine similarity from scratch; visualize my own week of work with UMAP. (This visualization doubles as a first sketch of the presence display.)
- Begin trajectory representation: person as a short sequence of state objects; define and detect convergence/divergence/orbit on toy and real data.

**Milestone:** end of week 3 — a pipeline that turns my live chats into an evolving structured state, with a measured extraction-quality number.

## Week 4 — Aggregation, the event watcher, and the group model

- Group-state model: aggregate N person-states into a renderable group object. Prototype two aggregation styles and compare: (a) clustering/statistical, (b) LLM-written "weather report" of the collective. Check every group signal against the small-group re-identification test (principle 3).
- Event watcher v0: conservative convergence detector over trajectories, privileging complementarity (phase-offset, stance-offset, solved-it-before) per principle 8. Every candidate event must carry a human-readable reason. Wire to the prior prototype's mutual-consent flow. Tune thresholds toward silence: false negatives are cheap, false positives spend trust.
- Simulate: replay my own historical data as 2–3 pseudo-people to shake out the pipeline before real users touch it.

**Milestone:** end-to-end pipeline (chat → state → group model → renderer stub + event watcher) running on simulated multi-person data.

## Weeks 5–6 — The ambient front-end

- Week 5: breadth. Paper/Figma-level sketches of 3–4 rendering directions along the safe→weird axis: social-proxy descendant (dots, drift, warmth in a menu-bar widget), weather-system metaphor, slow generative landscape (always-on secondary surface), and optionally ambient sound. Evaluate each against principles 2, 3, and 5 (translucence, resolution-as-privacy, never-addresses-you) and against glanceability: legible in <1s, changes on the timescale of minutes, meaningless to an onlooker.
- Mid-week 5: pick one primary direction (plus one cheap secondary if it shares a rendering substrate). Depth over breadth from here.
- Week 6: build it for real, fed by live group state. Get it onto my own desktop early in the week and live with it — self-dogfooding the *display*, not just the pipeline. Tune the change-rate and resolution by feel and against the principles tests.
- Prepare the pilot kit: one-page participant explainer, consent-layer toggles that actually work (instant, invisible-to-others revocation), setup script a resident can run in <15 minutes.

**Milestone:** the ambient display running live on my machine off real data; pilot kit ready.

## Week 7 — Pilot (residents, remote friends, or a mix)

- Onboard 3–6 participants from whichever pool has gelled — fellow residents if the relationships and interest are there by mid-residency, remote friends otherwise. (Remote friends are arguably the *truer* test population for the siloed-work premise anyway.) Days 1–2: presence layer only. Mid-week: enable the event watcher for those who opted into layer (c).
- Evaluation instruments, per principle 10:
  - Daily 2-question experience sample ("Did you glance at it today? Did it change anything you did or felt?").
  - Event-layer counts: candidates generated, offered, mutually accepted, conversations actually started.
  - Ad-hoc log of unprompted reactions (the qualitative gold).
- Rapid iteration on display legibility and event thresholds mid-pilot; log every change.

**Milestone:** ≥5 days of live multi-person data; first accepted introduction (stretch goal).

## Week 8 — Deprivation test, analysis, writeup

- Days 1–2: **deprivation test** — turn the display off without fanfare; note who notices, who asks, who says they miss it. Then short exit interviews (15 min each): what it felt like, privacy comfort, what they'd want at higher/lower resolution.
- Analyze: extraction quality trend, event-layer funnel, experience-sample trajectories, deprivation results.
- Writeup structured by the lab notebook: premise → principles → architecture → what the data contradicted → pilot findings → what a v2 would change. Demo-day story pairs the ambient display (the artifact) with the event-funnel numbers and deprivation quotes (the evidence).
- Explicitly park a "v2 / open questions" list: larger groups, longer timescales, non-chat signals, sound.

**Milestone:** final writeup + live demo + honest evaluation numbers.

---

## Risks and pre-committed mitigations

- **Wallpaper-ification is invisible** → deprivation test is scheduled now, not decided later; experience sampling runs daily from pilot day 1.
- **Cohort consent falls through** → weeks 2–6 are designed to run entirely on self-data and simulated pseudo-people; the pilot shrinks gracefully to N=2.
- **Extractor quality is poor** → the hand-labeled evaluation in week 3 catches this early; fallback is a coarser schema (fewer, more reliable facets) rather than a broken rich one.
- **Small-group re-identification** → every group-level signal passes the principle-3 test before rendering; when in doubt, lower the resolution.
- **Collaborator plans change scope** → the person-model layer is consumer-agnostic by design (principle 1 + architecture); new consumers attach without rework.
