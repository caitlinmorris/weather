"""The behavioral channel: deterministic features over transcript events.

HUMAN-WRITTEN territory (Stage 3). This is a STARTER: `error_density` is
fully worked as the pattern to follow; the remaining features are specs
with edge-case questions — implementing them is the learning content, and
`max_failure_streak` is the one the eval is waiting for (momentum κ ≥ 0.4
is the pre-registered target in person-model-spec-v1.md).

Doctrine (capture-overlay-architecture-v1): this channel is deterministic,
free, and reads tool results IN FULL — it sees exactly the friction the
semantic channel is structurally blind to. Neither channel is ground
truth: behavior can't tell methodical bisection from flailing; narration
can't be trusted about whether things are working. They correct each
other, which is why both exist.

Everything here is pure functions: list[TranscriptEvent] in, typed value
out, no I/O, no model calls, no clocks.
"""

from __future__ import annotations

from presence.pipeline.transcript_parser import TranscriptEvent

# Words in a tool result that indicate failure even when the tool doesn't
# use stderr (e.g. pytest failures arrive on stdout). Tune against real
# sessions; keep lowercase.
FAILURE_MARKERS = ("error", "failed", "failure", "traceback", "exit 1",
                   "exit 2", "fatal")


def _is_failure(event: TranscriptEvent) -> bool:
    """A tool-result event that looks like something went wrong."""
    r = event.tool_result
    if r is None:
        return False
    if r.stderr.strip():
        return True
    tail = r.stdout[-400:].lower()
    return any(marker in tail for marker in FAILURE_MARKERS)


def _is_success(event: TranscriptEvent) -> bool:
    return event.tool_result is not None and not _is_failure(event)


# ---------------------------------------------------------------------------
# WORKED EXAMPLE — the pattern: tiny spec, pure function, edge cases in tests.
# ---------------------------------------------------------------------------


def error_density(events: list[TranscriptEvent]) -> float | None:
    """Share of tool results that look like failures, 0.0–1.0.

    None (not 0.0) when there are no tool results at all: "no evidence"
    and "no failures" are different claims — the unknown-honesty rule
    applies to features too."""
    results = [e for e in events if e.tool_result is not None]
    if not results:
        return None
    return sum(1 for e in results if _is_failure(e)) / len(results)


# ---------------------------------------------------------------------------
# YOURS TO IMPLEMENT — specs and questions below. Delete each
# NotImplementedError as you go; hint_block() picks features up
# automatically once they stop raising.
# ---------------------------------------------------------------------------


def max_failure_streak(events: list[TranscriptEvent]) -> int:
    """THE momentum feature. Longest run of consecutive failing tool
    results, where a success resets the streak.

    Design questions to answer before writing (worth notes in the lab
    notebook):
    - Does a non-tool event (a human prompt, an assistant message) between
      two failures break the streak? (Consider: four failing test runs
      with discussion in between is still one grind.)
    - Does an *interrupted* tool result (r.interrupted) count as failure,
      success, or neither?
    - Should the streak be global to the window, or per-ish "activity"?
      (v1: keep it simple; note what you punted.)
    """
    raise NotImplementedError("Stage 3: yours to write")


def cadence_trend(events: list[TranscriptEvent]) -> str:
    """Trend of the person's prompting rhythm across the window:
    'accelerating' | 'steady' | 'sparse' | 'unknown'.

    Appendix A's agitation signature is accelerating gaps + shrinking
    prompts. Questions: how many prompts is enough to claim a trend
    (fewer than 3 is surely 'unknown')? Compare first-half vs second-half
    mean gaps, or fit something fancier? (Simple wins; this feeds a hint,
    not a verdict.) Events without timestamps exist — decide their fate.
    """
    raise NotImplementedError("Stage 3: yours to write")


def edit_oscillation(events: list[TranscriptEvent]) -> int:
    """Approximate rework loops: count Edit->failure->Edit oscillations.

    Honest constraint: events currently carry no file paths (the parser
    drops tool inputs), so true same-file revert detection is impossible
    today. Decide: approximate with tool-sequence patterns, or request the
    parser extension (pipeline work, requestable) and do it properly.
    Either answer is defensible; write down why you chose yours.
    """
    raise NotImplementedError("Stage 3: yours to write")


# ---------------------------------------------------------------------------
# Assembly — already wired-ready: implemented features appear, stubs are
# skipped, so the hint block grows as you work.
# ---------------------------------------------------------------------------


def hint_block(events: list[TranscriptEvent]) -> str:
    """Behavioral hints for the semantic extractor's prompt. Deterministic
    facts only — the semantic channel judges; this channel testifies."""
    parts: list[str] = []
    for name, fn in (
        ("error_density", error_density),
        ("max_failure_streak", max_failure_streak),
        ("cadence", cadence_trend),
        ("edit_oscillations", edit_oscillation),
    ):
        try:
            value = fn(events)
        except NotImplementedError:
            continue
        if value is not None:
            if isinstance(value, float):
                value = f"{value:.0%}"
            parts.append(f"{name}: {value}")
    return "; ".join(parts) if parts else "no behavioral evidence in window"
