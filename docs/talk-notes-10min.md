# Talk Notes — "Ambient Social Presence for AI Work" (10 min) — v2

*Restructured 2026-07-06: leads with the higher-level why (social translucency
as a general quality of work), opens the design space explicitly before taking
a stance, shows the built thing as one glimpse rather than an architecture
tour, and closes on what 6–7 remaining weeks can genuinely contribute. Same
day, second pass: slide 2 now centers the glance-outcome spectrum (what is a
glance supposed to* do*? — from café-grade nothing to the licensed opener to
brokered intros), and slide 3 gained the commit-stream contrast (artifact
trails inflating as AI writes the artifacts; narration as the signal that
moved upstream). Format: ~7 moments / ~9 min talking, timings in brackets,
bold = candidate verbatim phrasings. Prior version preserved at
talk-notes-10min-v0.md; the deep technical spine lives there and in the
architecture docs if Q&A wants it.*

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

## 4. What I've built (one week in) [1:45]

*(Demo beat: the live widget, plus the replay if time. Keep it a glimpse, not
an architecture tour.)*

- The pipeline is real and running on me: my last three months of AI-assisted
  work, distilled into small typed state objects — topic, phase, momentum,
  openness — **on my machine; raw chat never leaves it. What crosses the
  boundary is a state vector of the worker, never a summary of the chat.**
- Show the widget: dots, warmth, decay; a weather line; hover for a
  five-word handle of "what" — real examples from my own history:
  *"simplifying participant onboarding," "composing publication figures,"
  "shipping raise to production."* It sits at the corner of my screen now;
  I'm living with my own presence for a week before anyone else's.
- Two honesty mechanisms I'll defend as the interesting engineering:
  - **Every field can be `unknown`, and abstention renders as a dimmer dot.
    "An awareness system that hallucinates your mood is worse than none."**
    I'm hand-labeling my own sessions to publish an actual accuracy number.
  - Two channels cross-check each other: deterministic behavioral signals
    (four failed test runs in a row *is* stuckness) against the semantic
    read — because chat tone lies ("great, let's try it!" on the fourth
    consecutive failure).

## 5. The privacy inversion [1:00]

- The design move I most want reactions to: **"The resolution of the display
  is the privacy policy."** Abstraction isn't an aesthetic; it's the
  mechanism. The blurrier the rendering, the stronger everyone's deniability —
  calm and privacy turn out to be the same design parameter.
- Concretely: every field has a visibility tier (private / aggregate-only /
  ambient / introduction-eligible); sensitive ones like stuckness default to
  aggregate-only — the group's weather can be "a lot of grinding today," and
  no display ever says who. In a cohort of eight, even aggregates can identify
  people, so anything derivable from one person gets suppressed.
- The signal *level* is a visible dial on the widget, not a buried setting —
  **"where people leave the dial is itself a finding."**

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
  I'm logging instances. It's hard to peacock through four dim glyphs.
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

7 moments, ~9:15 talking — trim in rehearsal, not on stage. If running long:
slide 3's first bullet compresses to one sentence inside slide 4's opening
(the commit-stream inversion is the part of slide 3 to protect), and the
replay demo drops in favor of the live widget alone. Protect slide 2 above
everything — the glance-outcome spectrum is the talk's thesis — then slide 5.
Slide 6 is the one a committee remembers.
