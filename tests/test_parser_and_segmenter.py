from datetime import timedelta

from presence.pipeline.segmenter import segment_events
from presence.pipeline.transcript_parser import parse_transcript

from tests.synthetic import T0, write_synthetic_transcript


def _events(tmp_path):
    f = tmp_path / "session.jsonl"
    write_synthetic_transcript(f)
    return list(parse_transcript(f))


def test_parser_extracts_events(tmp_path):
    events = _events(tmp_path)
    assert len(events) == 7
    human = [e for e in events if e.is_human_prompt]
    assert len(human) == 2
    assert all(e.session_id == "synthetic-session-0001" for e in events)
    assert all(e.timestamp is not None for e in events)


def test_parser_collects_tools_and_results(tmp_path):
    events = _events(tmp_path)
    tool_names = [n for e in events for n in e.tool_names]
    assert tool_names == ["Edit", "Edit", "Bash"]
    results = [e.tool_result for e in events if e.tool_result]
    assert len(results) == 2
    assert results[1].stderr == "1 test failed"


def test_parser_excludes_thinking_from_text(tmp_path):
    events = _events(tmp_path)
    assert not any("internal" in e.text for e in events)


def test_repr_never_shows_content(tmp_path):
    # The privacy guard: printing an event or segment must not leak text.
    events = _events(tmp_path)
    for e in events:
        assert "sorting" not in repr(e) and "refactor" not in repr(e)
    for s in segment_events(events):
        assert "sorting" not in repr(s)


def test_segmenter_splits_on_gap(tmp_path):
    segments = segment_events(_events(tmp_path), gap_minutes=30)
    assert len(segments) == 2
    assert segments[0].t_start == T0
    assert segments[0].human_prompt_count == 1
    assert segments[1].t_start == T0 + timedelta(minutes=48)
    assert len(segments[0].events) + len(segments[1].events) == 7


def test_segmenter_single_segment_when_no_gap(tmp_path):
    segments = segment_events(_events(tmp_path), gap_minutes=60)
    assert len(segments) == 1
    assert segments[0].duration_minutes == 51
