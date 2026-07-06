# Design Principles — Ambient Social Presence for AI Work

*A working constitution for the residency project. Every later design decision should be adjudicated against these. Revise deliberately, not casually.*

## The premise

AI chat gives us a semantic signal about what people are working on and how it's going — a signal no prior awareness system ever had. The project points that signal at the classic CSCW goal of social translucence: rebuilding, for screen-facing and siloed work, the ambient substrate (overhearing, glancing, sensing the room) from which collaboration naturally emerges in physical space.

## 1. Presence is the architecture; matching is an occasional event

The system continuously maintains a group-state model and renders it ambiently. A separate, deliberately conservative watcher process may occasionally emit high-confidence "introduction" events, surfaced through a mutual-consent flow. The presence layer is expressive and always-on; the event layer is quiet and rare (order of one candidate introduction per person per week, not a stream). The rarity of events is what keeps the ambient layer from feeling like surveillance with a pretty face.

**Test:** If a proposed feature makes the system address the user more often, it is probably wrong.

## 2. Translucence, not transparency

Following Erickson & Kellogg: the goal is visibility sufficient for awareness and accountability, not full disclosure. Deliberate blur is a feature. We never render raw chat content, verbatim excerpts, or anything a colleague could quote back.

**Test:** Could an outsider glancing at someone's display learn anything specific about a third person's work? If yes, the resolution is too high.

## 3. Resolution is the privacy policy

Abstraction is the primary privacy mechanism, not an aesthetic afterthought. The lower the resolution of the rendered representation, the stronger the plausible deniability for everyone represented in it. Privacy decisions are therefore made at the rendering layer as much as at the data layer, and the two must be designed together.

Corollary for small groups: k-anonymity collapses fast in a cohort of ~8. "Someone is frustrated about embeddings" identifies a person. Any group-level signal must be checked against the question "in a group this size, is this actually individual-level information?"

## 4. Consent is layered and revocable

Three distinct consent boundaries, each opt-in and separately revocable at any time: (a) whether one's chats are modeled at all, (b) whether one's derived state contributes to the group presence rendering, (c) whether one is eligible for introduction events. Turning any layer off must be instant, unremarkable, and invisible to others (absence from the display should be indistinguishable from inactivity). No raw chat ever leaves the individual's boundary; only structured, derived state does.

## 5. The display never addresses you

It is a window, not an agent. It issues no notifications, asks no questions, offers no suggestions. Changes are noticeable on the timescale of minutes, glanceable in under a second, and calm in the Weiser & Brown sense: it lives in the periphery and rewards attention without demanding it. Only the (rare) event layer may knock, and it does so through a distinct, unmistakable channel so the ambient layer stays unimpeachably passive.

## 6. Model states, not verdicts

The person-model produces structured, typed state — topic facets, work phase, trajectory, openness — not evaluations. Nothing in the schema should support ranking people, measuring productivity, or comparing output. Sensitive dimensions (e.g., stuckness) exist to enable *complementarity* ("she solved this last Tuesday"), and are rendered at low resolution or aggregated, never itemized on a dashboard.

**Test:** Could a manager repurpose this field for performance review? If yes, redesign or drop it.

## 7. Trajectories over snapshots

Represent people as short sequences of states, not points. Convergence, divergence, and orbit are the interesting phenomena — for the matcher (two people converging on a problem from different directions beats two people statically nearby) and for the renderer (motion is more legible ambiently than position).

## 8. Complementarity beats similarity

"You're stuck on X; he solved X last week" is worth more than "you're both working on X." The person-model and event-watcher should privilege phase-offset, stance-offset, and history matches, not just topic proximity.

## 9. Inspectable over clever

Structured extraction first; embeddings only for fuzzy similarity within that structure. Every introduction event must come with a human-readable reason derived from typed facets. The builder (me) hand-implements the conceptually core components — the state model, the matching math — and delegates plumbing. No load-bearing black boxes.

## 10. Evaluate presence on presence's terms

Clicks and matches undercount an ambient system's value; wallpaper-ification is its invisible failure mode. Evaluation plan: glance behavior and lightweight experience sampling with the cohort, plus a scheduled deprivation test (turn it off, see who notices and minds). "People missed it when it was gone" is the strongest evidence an ambient system can produce. The event layer additionally provides countable outcomes (introductions offered / accepted / conversations started) for a legible demo-day story.

## Anti-goals

Not a productivity monitor. Not a manager dashboard. Not a notification engine. Not a matchmaking app with mood lighting. Not a replacement for talking to people — every successful outcome ends with humans contacting each other on their own channels.
