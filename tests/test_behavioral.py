"""Behavioral channel tests — her ruling scenarios, verbatim where possible.
Each test cites the ruling it verifies. Synthetic events only."""

from presence.core.behavioral import (
    agitation,
    error_frequency,
    failure_streak,
    hint_block,
)
from presence.pipeline.transcript_parser import ToolResult, TranscriptEvent


def tool(stdout="", stderr="", interrupted=False, via=None):
    events = []
    if via:
        events.append(TranscriptEvent(type="assistant", tool_names=[via]))
    events.append(TranscriptEvent(
        type="tool",
        tool_result=ToolResult(stdout=stdout, stderr=stderr, interrupted=interrupted),
    ))
    return events


def prompt(text="synthetic prompt"):
    return [TranscriptEvent(type="user", is_human_prompt=True, text=text)]


def flat(*groups):
    return [e for g in groups for e in g]


# --- ruling A1: structured failure signals only ------------------------------------


def test_a1_prose_error_is_not_failure():
    ok = flat(tool(stdout="the error handling chapter looks good"))
    bad = flat(tool(stdout="build FAILED"), tool(stderr="exit 1"))
    assert error_frequency(ok) == 0.0
    assert error_frequency(flat(ok, bad)) == 2 / 3


# --- ruling A2: interrupted is neither ----------------------------------------------


def test_a2_interrupted_excluded_from_both_sides():
    events = flat(tool(stderr="x"), tool(interrupted=True), tool(stdout="ok"))
    assert error_frequency(events) == 0.5  # denominator is 2, not 3
    # And an interruption neither breaks nor extends a streak:
    streaky = flat(tool(stderr="x"), tool(interrupted=True), tool(stderr="x"))
    assert failure_streak(streaky) == 2


# --- ruling B1: chat doesn't break a streak; success does ---------------------------


def test_b1_conversation_between_failures_is_one_grind():
    events = flat(tool(stderr="FAILED"), prompt("why though"),
                  tool(stderr="FAILED"))
    assert failure_streak(events) == 2


def test_b1_success_splits_into_two_streaks_of_one():
    events = flat(tool(stderr="x"), tool(stdout="ok", via="Bash"),
                  tool(stderr="x"))
    assert failure_streak(events) == 1


# --- ruling B2: unrelated read-only success does not break the streak ---------------


def test_b2_listing_files_does_not_break_the_streak():
    events = flat(
        tool(stderr="FAILED", via="Bash"),
        tool(stderr="FAILED", via="Bash"),
        tool(stderr="FAILED", via="Bash"),
        tool(stdout="16 files", via="Read"),   # unrelated success
        tool(stderr="FAILED", via="Bash"),
    )
    assert failure_streak(events) == 4


# --- ruling C1: shorter + repeated prompts read as agitation ------------------------


def test_c1_repeated_shrinking_prompts_read_agitated():
    events = flat(
        prompt("could you take a look at why the auth token refresh fails"),
        prompt("hmm, still failing with the same message about the token"),
        prompt("no, that still didn't work"),
        prompt("still didn't work"),
    )
    assert agitation(events) == "agitated"


def test_c2_provisional_floor_returns_none_below_four_prompts():
    events = flat(prompt("a"), prompt("b"), prompt("c"))
    assert agitation(events) is None  # C2 flagged: provisional floor of 4


# --- ruling B3 thresholds + E1 quiet, via the hint block ----------------------------


def test_b3_thresholds_appear_in_hints():
    grind = flat(tool(stderr="x"), tool(stderr="x"), tool(stderr="x"))
    assert "failure_streak: 3 (grind-level)" in hint_block(grind)
    two = flat(tool(stderr="x"), tool(stderr="x"))
    assert "(downgrade from flowing)" in hint_block(two)


def test_e1_quiet_window():
    assert hint_block([]) == "quiet window — nothing to classify"
    only_assistant = [TranscriptEvent(type="assistant", text="long monologue")]
    assert "quiet window" in hint_block(only_assistant)
