# Talk Notes — "Ambient Social Presence for AI Work" (10 min) — v3

*v2 (2026-07-06): leads with the higher-level why, opens the design space
(connection / coordination / companionship + the glance-outcome spectrum)
before taking a stance, adds the commit-stream contrast (artifact trails
inflating as AI writes the artifacts). v3 (2026-07-10): the design decisions
became content. Slide 4 now carries the lived dot→weather pivot (surveillance
grammar, discovered by self-dogfooding, demoed via the view toggle); slide 5
generalizes it — "form is policy" — folding the privacy inversion together
with boards-vs-follows and the audience-loud/activity-quiet rule from
docs/social-topology.md. Format: ~7 moments, timings in brackets, bold =
candidate verbatim phrasings. Prior versions: talk-notes-10min-v0.md; deep
technical spine lives in the architecture docs if Q&A wants it.*

---

## 1. The why, from the top [1:30]

- Open concrete: yesterday I did hours of genuinely good work — and it happened
  entirely inside a private chat with an AI. **"AI-assisted work might be the
  most productive siloed work in history — and the most siloed productive work
  in history."**
- Zoom out from AI: this is the latest step in a longer loss. When work became
  screen-shaped we lost the ambient substrate of shared space — overhearing,
  glancing, sensing the room's mood, knowing without asking that now is a bad
  time. Collaboration, companionship, and culture used to *emerge* from that
  substrate. We replaced it with search boxes, standups, and status emoji.
- The old name for the fix is **social translucence** (Erickson & Kellogg,
  25 years ago): make people's activity visible enough for awareness and
  accountability, with deliberate blur. Babble's dots. Calm technology.
  **"It's an old dream. Every previous attempt starved for signal — typing
  indicators, calendar state, webcam thumbnails. The dream was never wrong;
  the sensor was missing."**

## 2. What is the visibility actually *for*? The design space [2:15]

*(The intellectual heart of the talk — two questions I keep adjudicating
micro-decisions against: whose relationships the value lives in, and what a
glance is allowed to cause.)*

- Three readings of the same substrate, one line each:
  - **Connection** — finding the right stranger (the matchmaking reading;
    most-prototyped, least mysterious).
  - **Coordination** — making *existing* collaborators legible: when to
    interrupt, when to sync, when to leave alone.
  - **Companionship** — knowing other humans are out there working,
    regardless of the specifics. **"Nobody in a café knows what you're
    writing. The room still helps."**
- The sharper question underneath: **what is a glance supposed to *do*?**
  A spectrum of intended outcomes:
  - **Nothing, ever** — and that is still worth building. Café-grade
    ambience; the isolation antidote with no actionable payload.
  - **It quietly updates your model of your people** — you come to know what
    your friends are into lately. Nothing happens *now*; the next
    conversation starts warmer and truer.
  - **It licenses a conversation that wouldn't have happened.** Co-presence
    used to license the opener — "what are you working on?" is a normal
    thing to ask across a desk and a strange thing to ask cold over chat.
    **"Remote work lost the license, not the interest."** Maybe the ideal
    output of this whole system is one human-typed sentence: *"hey — saw
    you're deep in map overlays. Tell me more?"*
  - **The system brokers the conversation** — the watcher's rare, mutually
    consented introduction. The far end, deliberately rare.
- Different people will genuinely want different points on this spectrum —
  so, like everything else here, it's **instrumented rather than assumed**:
  the pilot's daily two-question sample asks what a glance changed (felt
  different / thought of someone / reached out), which places each person's
  actual value on the spectrum.
- Anti-goals said out loud, every time: not a productivity monitor, not a
  manager dashboard, nothing rankable.

## 3. The new ingredient — and the old signal inflating [1:15]

- Why revisit the old dream now: **"For the first time there's a rich semantic
  trace of what a person is actually working on and how it's going — because
  they're narrating it to an AI all day."** The sensor the field never had.
  And it attaches at the edges of tools people already use (local transcripts,
  lifecycle hooks) — nobody is asked to work differently.
- The counterpoint that makes this urgent rather than just possible: we
  already *have* work visibility — commit streams, green squares, and now
  platforms adding public views of commits. Those are **artifact trails**:
  past tense, countable, performative. And increasingly **AI-generated** —
  which quietly breaks them: **"As AI writes more of the artifacts, the
  artifacts say less and less about the person. The narration is where the
  person went."** A commit stream is starting to measure toolchain
  throughput; presence built on narration measures the human — present
  tense: exploring, stuck, open. **"Someone who's stuck has no commit to
  show — the moment a conversation would help most is exactly the moment
  with no artifact."** The same shift that devalued the old signal created
  the new one.

## 4. What I've built — and what living with it taught me [2:00]

*(Demo beat: the live widget, using the view toggle to show BOTH grammars.
Keep it a glimpse, not an architecture tour.)*

- The pipeline is real and running on me: months of AI-assisted work
  distilled into small typed state objects — topic, phase, openness — **on
  my machine; raw chat never leaves it. What crosses the boundary is a
  state vector of the worker, never a summary of the chat.** Hover phrases
  from my real history: *"simplifying participant onboarding," "composing
  publication figures," "shipping raise to production."*
- **The pivot the prototype forced.** v1 rendered each person as a glowing
  dot — faithful to the Babble lineage. After one day of living with it:
  **"I had rebuilt the Slack presence indicator. The data was private; the
  *form* wasn't."** Identity × current-status is a loaded grammar — twenty
  years of chat apps taught everyone, including managers, to read it as
  "is this person at their desk."
- The replacement (toggle to it live): an anonymous **weather field** —
  right edge is now, the last hours trail off left, hue is the kind of
  work, recurring topics recur at the same height, and nothing is
  attributed to anyone. **"Position encodes *when*, not *who* — 'is she
  working right now' stops being a question the display can answer."**
  Fresh events crystallize as outlined blocks you can hover for a
  five-word phrase; whether a *name* ever appears is a setting each person
  controls.
- One honesty mechanism, said briefly: every field can be `unknown` and
  renders as abstention — **"an awareness system that hallucinates your
  mood is worse than none"** — with a measured accuracy number to come.

## 5. Form is policy — the structural choices where tone lives [1:30]

*(The meta-lesson of slide 4, generalized: the surveillance question is
decided by shapes, not by features or checkboxes.)*

- **Resolution is the privacy policy.** Abstraction is the mechanism, not an
  aesthetic: every field has a visibility tier; sensitive ones (stuckness)
  default to aggregate-only — weather can say "a lot of grinding today,"
  never who. The sharing level is a visible dial on the widget, and it's
  becoming *per-audience*: more with a partner, less with colleagues.
  **"Where people leave the dial is itself a finding."**
- **Boards, not follows.** The social unit is a *place* you're invited
  into, never a contact you add: everyone on a board sees the same weather
  and the same member list, so visibility is reciprocal by construction —
  **"if I can see your weather, you can see mine, and we both know it."**
  A feed only I compose, of people I chose, is a dashboard of my people —
  surveillance wearing a friendly UI. No search, no discovery, no
  "people you may know," ever.
- The membership rule that falls out, my favorite sentence in the design:
  **"Who can see you is always loud; whether you're working is always
  quiet."** Joining and leaving a board are visible to everyone; pausing,
  lunch, and quitting for the day are indistinguishable from not working.
- **"In every fork so far, the safer design wasn't a feature we added — it
  was a shape we chose."**

## 6. What 6–7 weeks can contribute [1:30]

Three contributions I think are worth having, each testable in the time:

1. **A new sensor, characterized.** An open schema + extraction pipeline for
   turning AI work-narration into honest, shareable state — with a measured
   accuracy number, not a vibe. Useful to anyone building on this signal.
2. **A working answer to the privacy question.** Tiered publication +
   resolution-as-privacy, operational in code — plus dial-position data on
   what level people actually choose to share at.
3. **Evidence about which quality matters — and where on the glance-outcome
   spectrum value actually shows up.** Small pilot (3–6 people, opt-in at
   three separately revocable layers): daily two-question experience sampling
   (mapped to the spectrum: felt different / thought of someone / reached
   out), introduction counts, and in the final week a **deprivation test —
   turn it off unannounced, see who notices and who minds. "Being missed when
   it's gone is the strongest evidence an ambient system can produce."**

## 7. The ask [0:30]

- Soft, no commitment: it runs on my desk today; in a few weeks I'll want 3–6
  people willing to run a small daemon and glance at a widget. Opt-in at every
  layer, revocable instantly and invisibly.
- **"If the idea of your workday having weather appeals to you, come talk
  to me."**

---

## Anticipated Q&A (30-second answers)

- **"Isn't this surveillance with mood lighting?"** The question I take most
  seriously. Structural answers: raw content never leaves your machine; every
  shared field has a consent tier you control; the rendering is deliberately
  too low-resolution to reconstruct anything; and the schema contains nothing
  rankable — a design test applied to every field ("could a manager repurpose
  this?").
- **"Isn't ambient companionship just coworking streams / Discord?"** Those
  share *attention* — a camera, a channel, a performance. This shares blurred
  *state* with no camera and no addressee; it never asks to be watched. The
  difference between a study-with-me stream and hearing typing through a wall.
- **"Why not just watch each other's commit streams?"** Four differences,
  in escalating order: *tense* — artifacts are past, state is present, and
  stuck has no commit; *audience* — broadcast performance for an unbounded
  public vs. blurred state for a closed consented group; *rankability* —
  commit counts became manager metrics precisely because artifacts are
  countable, and this schema is deliberately not; *authorship* — AI
  increasingly writes the commits, so the stream measures the toolchain.
  The inversion worth saying plainly: AI devalued the artifact signal and
  created the narration signal in the same stroke.
- **"Why not just matchmaking?"** Matching replicates the *output* of shared
  space without the substrate, and it's been prototyped to death. Presence
  rebuilds the substrate; introductions fall out at office rates. Also the
  slide-2 answer: I'd rather instrument the question than assume it.
- **"Won't people perform for the display?"** Maybe — that's a finding, and
  I'm logging instances. It's hard to peacock through anonymous weather.
- **"Why can't I just follow people I find interesting?"** Because a follow
  is asymmetric attention, and asymmetric attention to someone's work state
  is the definition of monitoring. Boards make visibility reciprocal by
  construction, and everyone shares one referent — a room, not n private
  dashboards. Also the k-anonymity of the weather collapses if every viewer
  composes their own set.
- **"What does the extractor see?"** Locally, everything — same trust boundary
  as the AI tool itself. What leaves is typed state at your consented tier,
  and the extractor is instructed and evaluated on omitting personal,
  emotional, and credential content from every field.
- **"What would success look like in seven weeks?"** The three contributions
  on slide 6 — a characterized sensor, an operational privacy design, and
  deprivation-test evidence for (or against!) the companionship hypothesis.
  A null result on one quality with a real result on another is a good paper,
  not a failure.

## Slide count sanity check

7 moments, ~9:45 talking — over budget on paper; trim in rehearsal, not on
stage. Cut order if running long: slide 3's first bullet compresses into
slide 4's opening (protect the commit-stream inversion); slide 1's lineage
beat becomes one sentence; slide 6's contribution wording tightens. Protect
slides 2, 4, and 5 above everything — the glance-outcome spectrum is the
thesis, and the dot→weather story plus "form is policy" are what make this
audience trust the designer. Slide 6 is the one a committee remembers.
