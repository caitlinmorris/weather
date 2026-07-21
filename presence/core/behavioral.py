"""The behavioral channel — a cited translation of docs/behavioral-rulings.md.

The rulings document is the human-written artifact; this file implements it
under the judgment-authorship contract (docs/decisions/2026-07-16-judgment-
authorship.md): every branch cites its ruling; anything the translator had
to decide alone is flagged at the bottom of the rulings doc, not silently
chosen; names follow Caitlin's vocabulary (A3: "error_frequency").

Pure functions: list[TranscriptEvent] in, typed value out. No I/O, no
model calls, no clocks.
"""

from __future__ import annotations

from presence.pipeline.transcript_parser import TranscriptEvent

# Ruling A1: failure = error text / FAILED / nonzero exit — EXCEPT the bare
# word "error" appearing in prose without an error signal. Translation:
# structured markers only; "error:" (compiler-style, with colon) kept as
# structured, bare "error" dropped. [Colon distinction = translator choice,
# flagged.]
FAILURE_MARKERS = ("error:", "failed", "failure", "traceback",
                   "exit 1", "exit 2", "fatal")

# Read-only tool names (Claude Code): their successes are "unrelated
# commands" in the sense of ruling B2 and do not break a failure streak.
# [Tool-kind approximation for B2's "same tests" = translator choice, flagged.]
READ_ONLY_TOOLS = {"read", "grep", "glob", "ls", "websearch", "webfetch",
                   "toolsearch"}


def _is_interrupted(event: TranscriptEvent) -> bool:
    r = event.tool_result
    return r is not None and r.interrupted


def _is_failure(event: TranscriptEvent) -> bool:
    r = event.tool_result
    if r is None or r.interrupted:  # ruling A2: interrupted is NEITHER
        return False
    if r.stderr.strip():
        return True
    tail = r.stdout[-400:].lower()
    return any(marker in tail for marker in FAILURE_MARKERS)


def _is_success(event: TranscriptEvent) -> bool:
    r = event.tool_result
    if r is None or r.interrupted:  # ruling A2
        return False
    return not _is_failure(event)


# ---------------------------------------------------------------------------


def error_frequency(events: list[TranscriptEvent]) -> float | None:
    """Ruling A3 (her name). Share of tool runs that went wrong, 0.0-1.0.
    Interrupted runs are excluded from both sides (ruling A2). None when
    there are no countable runs: "no evidence" is not "no failures"."""
    countable = [e for e in events
                 if e.tool_result is not None and not _is_interrupted(e)]
    if not countable:
        return None
    return sum(1 for e in countable if _is_failure(e)) / len(countable)


def failure_streak(events: list[TranscriptEvent]) -> int:
    """Longest run of consecutive failures.

    Ruling B1: conversation between failures does NOT break a streak
    ("just discussing the why doesn't mean it's working"); a success does.
    Ruling B2: an unrelated success (read-only tool) does NOT break it —
    only a substantive (execution-type) success resets.
    Ruling A2: interrupted runs are neutral — they neither extend nor
    break."""
    longest = current = 0
    # Track the tool kind that produced each result: results follow the
    # assistant event that invoked the tool.
    last_tools: list[str] = []
    for e in events:
        if e.tool_names:
            last_tools = [t.lower() for t in e.tool_names]
        if e.tool_result is None or _is_interrupted(e):
            continue  # prompts/assistant text: ruling B1; interrupted: A2
        if _is_failure(e):
            current += 1
            longest = max(longest, current)
        else:
            substantive = not last_tools or any(
                t not in READ_ONLY_TOOLS for t in last_tools
            )
            if substantive:  # ruling B1: a real success splits the streak
                current = 0
            # else: ruling B2 — unrelated read-only success, streak holds
    return longest


def agitation(events: list[TranscriptEvent]) -> str | None:
    """Ruling C1: the stuck signature she stands behind — SHORTER and
    REPEATED prompts (all-caps as a strong marker; noted person-dependent).
    Returns 'agitated' | 'calm' | None (insufficient evidence).

    Ruling C2 was 'unsure' about the minimum prompt count; translator's
    provisional floor is 4, FLAGGED for her ruling."""
    prompts = [e.text for e in events if e.is_human_prompt and e.text.strip()]
    if len(prompts) < 4:  # provisional per C2 flag
        return None
    half = len(prompts) // 2
    early = sum(len(p) for p in prompts[:half]) / half
    late = sum(len(p) for p in prompts[half:]) / (len(prompts) - half)
    shrinking = late < early * 0.6
    caps = any(p.isupper() and len(p) > 8 for p in prompts)  # C1: all-caps
    repeats = 0
    for a, b in zip(prompts, prompts[1:]):
        wa, wb = set(a.lower().split()), set(b.lower().split())
        if wa and wb and len(wa & wb) / len(wa | wb) >= 0.5:
            repeats += 1  # C1: "no, that still didn't work" repetition
    if caps or (shrinking and repeats >= 1) or repeats >= 2:
        return "agitated"
    return "calm"


# Rework (section D): D1 unanswered — NOT BUILT, per the contract (nothing
# is guessed). D2 ruled: no filenames enter the record. When D1 is ruled,
# the approximate-pattern translation goes here.


def hint_block(events: list[TranscriptEvent]) -> str:
    """Deterministic testimony for the semantic extractor. Includes her
    interpretive thresholds (ruling B3) so the language channel receives
    the ruling, not just the number. Ruling B4 (does bisection get
    distinguished?) is unanswered — until ruled, the streak is reported
    plainly and the language channel may overrule, which matches the
    two-channel doctrine anyway."""
    prompts = any(e.is_human_prompt for e in events)
    results = any(e.tool_result is not None for e in events)
    if not prompts and not results:
        return "quiet window — nothing to classify"  # ruling E1

    parts: list[str] = []
    freq = error_frequency(events)
    if freq is not None:
        parts.append(f"error_frequency: {freq:.0%}")
    streak = failure_streak(events)
    if streak >= 3:  # ruling B3: three or more is a grind
        parts.append(f"failure_streak: {streak} (grind-level)")
    elif streak == 2:  # ruling B3: two downgrades from flowing
        parts.append("failure_streak: 2 (downgrade from flowing)")
    elif streak == 1:
        parts.append("failure_streak: 1")
    mood = agitation(events)
    if mood is not None:
        parts.append(f"prompt_rhythm: {mood}")
    return "; ".join(parts) if parts else "quiet window — nothing to classify"
