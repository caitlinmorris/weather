# Talk Notes — "Ambient Social Presence for AI Work" (10 min)

*Format: ~7 slides / ~9 minutes talking + buffer. Timings in brackets. Bolded lines are candidate verbatim phrasings; everything else is talking-point shorthand. The three-layer framing (person state → shared element → rendering) is the spine — every slide locates itself on it.*

---

## 1. The problem [1:30]

- Open concrete, not abstract: describe yesterday — hours of deep, productive work, entirely inside a chat with an AI. Genuinely good work. And *nobody on earth had any idea it was happening.*
- **"AI-assisted work might be the most productive siloed work in history — and the most siloed productive work in history."**
- What we lost when work went screen-shaped: the ambient substrate of shared space. Overhearing. Glancing. Sensing the room's mood. Knowing without asking that now is a bad time to interrupt someone. Collaboration used to *emerge* from that substrate; we replaced the substrate with search boxes and standups.
- This project: rebuild a small piece of that substrate, using the very thing that siloed us.

## 2. The lineage + the new ingredient [1:30]

- This is an old dream with a 25-year literature: **social translucence** (Erickson & Kellogg) — visibility → awareness → accountability, with deliberate blur. Show/describe the Babble "social proxy": a circle, dots drift toward center when people are active. Calm technology (Weiser & Brown): systems that live in the periphery and reward attention without demanding it.
- Why revisit it now: every prior awareness system was starved for signal — video snapshots, typing indicators, calendar state. **"For the first time, there's a rich semantic trace of what a person is actually working on and how it's going — because they're narrating it to an AI all day."**
- The bet: point modern signal at the old framework.

## 3. Architecture in one picture [1:30]

*(One diagram slide: chat → PersonState → GroupState → two consumers. Walk it left to right. This is the three-layer spine.)*

- **Layer 1 — person state.** Each person's AI sessions are distilled — locally, on their machine — into a small typed object: topic gist, work phase (exploring/building/debugging/polishing), momentum, openness to interruption, trajectory. Not a summary of the chat; a *state vector of the worker*.
- **Layer 2 — the shared element.** Only that typed state crosses the personal boundary, and it aggregates into a group state: who's active, what themes are alive, the collective "weather."
- **Layer 3 — rendering + events.** Group state feeds two consumers: an always-on **ambient display** (the main event), and a deliberately quiet **watcher** that maybe once a week says "you two are converging on the same problem — want an intro?" with mutual consent on both sides.
- **"Presence is the architecture; matchmaking is a rare side effect — the same ratio a good shared office has."**

## 4. Layer 1 technically: extraction [1:30]

- Where the data comes from: no new tools, no behavior change. Claude Code already writes complete session transcripts locally and fires lifecycle hooks. **"The system never asks you to work differently; it attaches to the edges of the tool you already use."**
- Two extraction channels, and this is the part I find most fun:
  - *Behavioral* — free, deterministic: timing cadence, tool-call patterns. In a coding session, four failed test runs in a row on the same file *is* stuckness; no model needed.
  - *Semantic* — a small cheap LLM call per work chunk, incremental: "here's what we believed 20 min ago, here's what happened since — update the state." Behavioral features feed in as hints and as a lie detector.
- Honesty mechanism: every field can be `unknown`, and I'm hand-labeling my own sessions to publish an actual extraction-accuracy number. **"An awareness system that hallucinates your mood is worse than none."**

## 5. Layer 2 technically: what crosses the boundary [1:30]

- This is where the privacy design lives, and the design move I most want reactions to: **every field has a visibility tier** — private / aggregate-only / ambient / introduction-eligible. Raw chat is tier-zero forever; it never leaves your laptop (enforced structurally: private and public state live in separate stores; one function may write to public).
- Sensitive example: *stuckness*. Exists in the model because "she solved this last Tuesday" is the most valuable connection the system can make — but it defaults to aggregate-only. The group's weather can be "a lot of grinding today"; no dashboard ever says who.
- **"The resolution of the display is the privacy policy."** The blurrier the rendering, the stronger everyone's deniability — calmness and privacy are the same design parameter here. Corollary I'm designing for explicitly: in a group of eight, aggregate stats can still identify people, so anything derivable from one person gets suppressed.
- Anti-goals, said out loud: not a productivity monitor, not a manager dashboard, nothing rankable.

## 6. Layer 3: what it looks like [1:00]

- Terminal-native, because that's where this crowd actually works. Three rings, one data contract, increasing size:
  - a one-line **statusline strip** inside Claude Code itself — a few glyphs, presence inside the moment of work;
  - the primary artifact: a persistent **ambient TUI pane** — colleagues as drifting character-cell dots, warmth, decay, a two-sentence weather line. Changes on the timescale of minutes; glanceable in under a second; meaningless to a passerby;
  - optionally a browser/wall rendering of the same state.
- **"The display never addresses you. It's a window, not an agent — no notifications, no suggestions, no Clippy."** Only the rare introduction event may knock, in its own channel.

## 7. Deliverables, evaluation, and the ask [1:30]

- Concrete deliverables, mapped to the three layers: **(1)** the person/group state schema + open-source extraction pipeline *with measured accuracy*; **(2)** the presence relay + watcher; **(3)** the ambient terminal display, live, fed by real work — plus pilot findings.
- The evaluation trick I'm most committed to: ambient systems fail by becoming wallpaper, invisibly. So besides daily two-question experience sampling and counting introductions (offered/accepted/conversations started), **week 8 includes a deprivation test — I turn it off without announcement and see who notices and who minds.** "People missed it when it was gone" is the strongest evidence an ambient system can produce.
- The ask (soft, no commitment sought today): I'll pilot on myself first; in a few weeks I'll be looking for 3–6 people willing to run a small daemon and glance at a pane. Opt-in at three separate layers, revocable instantly and invisibly. **"If the idea of your workday having weather appeals to you, come talk to me."**

---

## Anticipated Q&A (30-second answers)

- **"Isn't this surveillance with mood lighting?"** The design question I take most seriously. Three structural answers: raw content never leaves your machine; every shared field has a consent tier you control; and the rendering is deliberately too low-resolution to reconstruct anything. Also: no managers exist in this deployment, and the schema contains nothing rankable — that's a design test I apply to every field.
- **"Why not just better matchmaking?"** Matching replicates the *output* of shared space (introductions) without the substrate. Presence rebuilds the substrate; introductions fall out as a side effect, at roughly the rate they do in a real office. Also matchmaking has been prototyped to death; AI-derived *presence* hasn't, because the signal didn't exist until now.
- **"Won't people perform for the display?"** Maybe — that's a finding, not just a bug, and I'm logging instances. The low resolution helps: it's hard to peacock through four dim glyphs.
- **"What about people who work in browser chat, not the terminal?"** Batch import path exists; their dot is just staler, and the display renders staleness honestly. Full realtime chat capture is out of scope for eight weeks.
- **"Does the extractor see everything I type to Claude?"** Locally, yes — same trust boundary as Claude Code itself, running under your account on your machine. What *leaves* is only the typed state at your consented tier. And the extractor is explicitly instructed and evaluated on omitting personal/emotional/credential content from even the private fields.

## Slide count sanity check

7 content moments in ~9:00 talking. If running long, compress slide 2 into slide 1's last beat (the lineage can be one sentence) — protect slides 4–5, which are what makes this audience trust the build.
