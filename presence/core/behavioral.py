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

import re as _re

from presence.pipeline.transcript_parser import TranscriptEvent

# Ruling A1: failure = error text / FAILED / nonzero exit — EXCEPT failure
# VOCABULARY appearing as prose/content. Translation (patched 2026-07-21
# after content-word false positives — sessions ABOUT failure detection
# read as failing): structured PATTERNS only, never bare substrings.
# [Flagged as translator refinement #9.]
_FAILURE_PATTERNS = (
    _re.compile(r"^(FAILED|ERROR)\b", _re.M),          # pytest-style lines
    _re.compile(r"\b\d+ (failed|errors?)\b"),          # "1 failed, 55 passed"
    _re.compile(r"Traceback \(most recent call last\)"),
    _re.compile(r"\bexit [1-9]\d*\b"),                 # shell/Warp exits
    _re.compile(r"\bfatal:", _re.I),                    # git-style
    _re.compile(r"\berror:", _re.I),                    # compiler-style (flag #1)
)


def _looks_failed(text: str) -> bool:
    return any(p.search(text) for p in _FAILURE_PATTERNS)



def _is_interrupted(event: TranscriptEvent) -> bool:
    r = event.tool_result
    return r is not None and r.interrupted


def _is_neutral_action(event: TranscriptEvent) -> bool:
    """Ruling B1 says successful OUTCOMES break streaks — a tool that
    completes with no output at all (an Edit landing silently) is an
    ACTION, not an outcome: it neither counts toward error_frequency nor
    resets a streak. [Translator refinement of B1's word 'outcome',
    flagged. Sources whose empty output IS an outcome (Warp's exit 0)
    say so explicitly in stdout.]"""
    r = event.tool_result
    return (r is not None and not r.interrupted
            and not r.stdout.strip() and not r.stderr.strip())


def _is_failure(event: TranscriptEvent) -> bool:
    r = event.tool_result
    if r is None or r.interrupted:  # ruling A2: interrupted is NEITHER
        return False
    if r.stderr.strip():
        # stderr is a failure only in failure SHAPE: structured markers,
        # or the classic all-output-on-stderr pattern. Warnings and
        # notices on stderr are not failures. [refinement #9]
        return _looks_failed(r.stderr) or not r.stdout.strip()
    return _looks_failed(r.stdout[-800:])


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
                 if e.tool_result is not None and not _is_interrupted(e)
                 and not _is_neutral_action(e)]  # ruling B1: outcomes only
    if not countable:
        return None
    return sum(1 for e in countable if _is_failure(e)) / len(countable)


def _failure_signature(event: TranscriptEvent) -> frozenset:
    """Distinctive tokens of a failure's output — 'the same failed tests'
    (ruling B2) recognized by their error text rather than by command
    identity, which stays local."""
    r = event.tool_result
    text = (r.stderr + " " + r.stdout[-400:]).lower()
    tokens = _re.findall(r"[a-z0-9_./:-]{5,}", text)
    distinctive = {t for t in tokens if any(c in t for c in "_./:") or len(t) > 8}
    return frozenset(distinctive or tokens[:12])


def _same_failure(a: frozenset, b: frozenset) -> bool:
    if not a and not b:
        return True
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= 0.3


def failure_streak(events: list[TranscriptEvent]) -> int:
    """Longest recurrence streak of the same failure.

    Rulings B1 + B2, reconciled as: a success PAUSES streaks; a failure
    that matches a paused streak's signature RESUMES it ("returns to the
    same failed tests" — B2); an unrelated failure starts fresh (B1's
    split into streaks of one). Conversation never breaks anything (B1);
    interruptions (A2) and silent actions (B1 'outcomes' refinement) are
    neutral. [Signature matching = translator approximation, flagged.]"""
    streaks: list[dict] = []  # {sig, count}
    for e in events:
        if (e.tool_result is None or _is_interrupted(e)
                or _is_neutral_action(e)):
            continue
        if _is_failure(e):
            sig = _failure_signature(e)
            for s in streaks:
                if _same_failure(s["sig"], sig):
                    s["count"] += 1
                    s["sig"] = s["sig"] | sig
                    break
            else:
                streaks.append({"sig": sig, "count": 1})
        # successes pause (implicitly): they don't reset counts, but a
        # NON-matching later failure starts its own streak — B1's split.
    return max((s["count"] for s in streaks), default=0)


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
    if not parts:
        return "quiet window — nothing to classify"
    # Scope note: keeps mechanical friction from bleeding into PHASE,
    # which should follow the narration. [translator patch, flagged]
    return ("; ".join(parts)
            + " (mechanical friction informs momentum; phase follows the narration)")
