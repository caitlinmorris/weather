"""Canary: parse the newest REAL transcript on this machine and assert the
structure the pipeline depends on still holds. Fails loudly on format drift
after a Claude Code update; localizes the fix to transcript_parser.py.

Privacy: asserts structure and counts only. No assertion message, print, or
fixture in this file may include event text.
"""

import pytest

from presence.pipeline.config import allowed_transcripts
from presence.pipeline.transcript_parser import parse_transcript

transcripts = allowed_transcripts()

pytestmark = pytest.mark.skipif(
    not transcripts, reason="no real transcripts on this machine"
)


def _newest_events():
    newest = max(transcripts, key=lambda p: p.stat().st_mtime)
    return list(parse_transcript(newest))


def test_real_transcript_yields_conversation_events():
    events = _newest_events()
    assert len(events) > 0, "transcript parsed to zero events: format drift?"
    types = {e.type for e in events}
    assert "user" in types and "assistant" in types, f"missing core types: {types}"


def test_real_events_carry_required_metadata():
    events = _newest_events()
    conversation = [e for e in events if e.type in ("user", "assistant")]
    timestamped = sum(1 for e in conversation if e.timestamp is not None)
    with_session = sum(1 for e in conversation if e.session_id)
    assert timestamped / len(conversation) > 0.9, "timestamps missing: format drift?"
    assert with_session / len(conversation) > 0.9, "sessionId missing: format drift?"


def test_real_transcript_has_signal_for_both_channels():
    events = _newest_events()
    has_human_prompt = any(e.is_human_prompt for e in events)
    has_tool_activity = any(e.tool_names or e.tool_result for e in events)
    assert has_human_prompt, "no human prompts detected: content shape drifted?"
    assert has_tool_activity, "no tool activity detected: content shape drifted?"
