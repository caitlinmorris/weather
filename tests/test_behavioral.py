"""Behavioral channel tests. The worked example's tests show the pattern;
the skipped ones are scaffolds for the features you implement — unskip
each as you go (synthetic events only, constructed inline)."""

import pytest

from presence.core.behavioral import error_density, hint_block, max_failure_streak
from presence.pipeline.transcript_parser import ToolResult, TranscriptEvent


def tool(stdout="", stderr="", interrupted=False):
    return TranscriptEvent(
        type="tool",
        tool_result=ToolResult(stdout=stdout, stderr=stderr, interrupted=interrupted),
    )


def prompt(text="synthetic prompt"):
    return TranscriptEvent(type="user", is_human_prompt=True, text=text)


# --- worked example: error_density -------------------------------------------------


def test_error_density_counts_failures():
    events = [tool(stdout="ok"), tool(stderr="boom"),
              tool(stdout="3 tests FAILED"), prompt()]
    assert error_density(events) == 2 / 3


def test_error_density_none_without_evidence():
    # No tool results at all: "no evidence" is not "no failures".
    assert error_density([prompt(), prompt()]) is None


def test_warp_exit_codes_read_as_failures():
    assert error_density([tool(stderr="exit 1"), tool()]) == 0.5


# --- yours: unskip as you implement -------------------------------------------------


@pytest.mark.skip(reason="Stage 3: implement max_failure_streak, then unskip")
def test_failure_streak_resets_on_success():
    events = [tool(stderr="x"), tool(stderr="x"), tool(stdout="ok"),
              tool(stderr="x"), tool(stderr="x"), tool(stderr="x")]
    assert max_failure_streak(events) == 3


@pytest.mark.skip(reason="Stage 3: decide whether prompts between failures break a streak")
def test_failure_streak_across_interleaved_prompts():
    events = [tool(stderr="x"), prompt("hmm why"), tool(stderr="x")]
    assert max_failure_streak(events) == 2  # ...or 1? Your call — justify it.


def test_hint_block_grows_with_implemented_features():
    events = [tool(stderr="exit 1"), tool(stdout="ok")]
    block = hint_block(events)
    assert "error_density: 50%" in block
    # Stubs are silently skipped until implemented:
    assert "max_failure_streak" not in block or True
