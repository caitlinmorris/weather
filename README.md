# we.ather

**Ambient social presence for AI-era work.** A small always-on-top widget
that lets rooms of 2–12 trusted people share low-resolution "work
weather" while they work with AI tools — the hum of working *near*
people, without sharing what anyone is actually saying or doing.

<!-- screenshot: field view, two rooms stacked, "2 making weather" -->
<!-- ![we.ather field view](docs/media/field.png) -->

Your AI coding tools (Claude Code, Warp) already keep session logs on
your machine. we.ather reads only the project folders you explicitly
allow, distills them **locally** into a few words of state — a work
phase, a short topic phrase — and shares *only that* with your room,
through a tiny relay one member hosts on their own free Cloudflare
account. Color = kind of work, position = time. Hovering a fresh cloud
shows who it is and five words of what they're into. Everything else is
just weather.

No accounts, no central server, no feed, no metrics. Nothing from
before you install is ever analyzed — your weather starts when your
consent does.

## Try it

- **Join or start a room** → download the latest package from
  [Releases](../../releases) and read the
  [Member Guide](docs/pilot-kit.md). Setup is ~10 minutes; a board of
  just yourself is fine to start.
- **Host your own board** (free, ~20 minutes, nothing routed through
  anyone) → [Self-Hosting Guide](docs/self-hosting.md).
- **"What exactly leaves my machine?"** →
  [Security Model](docs/security-model.md) — one page, and if the code
  and that page ever disagree, that's a bug: tell me.

Currently macOS + Claude Code and/or Warp. Extraction runs on your own
Anthropic API key (~pennies/workday) or your existing Claude
subscription — your choice at install.

## Status

Early beta, developed live during a residency at
[Stochastic Labs](https://stochasticlabs.org). A small pilot has been
running for weeks; a wider circle of testers is starting now. Interested?
Open an issue or reach out — [caitlinmorris.net](https://caitlinmorris.net).

The narrative version — why ambient presence matters, what my research
on workplace visibility found, and how this design answers it — is on
[Substack](https://caitlinmaking.substack.com/p/weather-ambient-social-visibility).

## Research context

we.ather extends my work on calibrated social visibility in
collaboration (InquiryBits, CSCW) into AI-era work: people consistently
want *more* visibility to support connection and collaboration — and
firmly want it limited to small trusted groups. The design premise here
is that those aren't in tension; they're a spec. Design principles,
decision memos, and an honest lab notebook (including the constructs
that failed) live in [docs/](docs/).

## License

[MIT](LICENSE).
