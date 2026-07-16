"""Harness tests with a fake API client — no network, synthetic content only."""

import json
from datetime import timedelta

import pytest

from presence.core.schema import Momentum, Phase, SessionObservation, Stance
from presence.extract.extractor import (
    ExtractionError,
    Extractor,
    format_event,
    load_system_prompt,
)
from presence.pipeline.segmenter import segment_events
from presence.pipeline.transcript_parser import parse_transcript

from tests.synthetic import T0, write_synthetic_transcript

VALID_RESPONSE = json.dumps(
    {
        "topic": {"tags": ["utilities", "refactoring"], "gist": "tidying utility code", "micro_gist": "tidying utilities", "domain": "tooling"},
        "phase": "building",
        "momentum": "steady",
        "stance": "directing",
        "trajectory_note": "moved from sorting helper to config loader",
        "confidence": {"phase": 0.8, "momentum": 0.7, "stance": 0.2},
        "evidence": {"phase": "adding and refactoring code", "momentum": "few reversals"},
    }
)


class FakeBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class FakeClient:
    """Returns queued responses; records every request for inspection."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return type("R", (), {"content": [FakeBlock(self.responses.pop(0))]})()


def _segment(tmp_path):
    f = tmp_path / "session.jsonl"
    write_synthetic_transcript(f)
    return segment_events(list(parse_transcript(f)), gap_minutes=60)[0]


def test_extraction_builds_valid_observation(tmp_path):
    client = FakeClient([VALID_RESPONSE])
    obs = Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    assert isinstance(obs, SessionObservation)
    assert obs.phase == Phase.BUILDING
    assert obs.momentum == Momentum.STEADY
    assert obs.stance == Stance.UNKNOWN  # 0.2 confidence floors to unknown
    assert obs.topic.gist == "tidying utility code"
    assert obs.topic.micro_gist == "tidying utilities"
    assert obs.t_start == T0  # segment bounds, not extraction time
    assert obs.t_end == T0 + timedelta(minutes=51)
    assert obs.extractor_version.startswith("v4+")


def test_word_caps_enforced_mechanically(tmp_path):
    fields = json.loads(VALID_RESPONSE)
    fields["topic"]["gist"] = " ".join(["word"] * 30)
    fields["topic"]["micro_gist"] = "one two three four five six seven"
    fields["trajectory_note"] = " ".join(["note"] * 40)
    client = FakeClient([json.dumps(fields)])
    obs = Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    assert len(obs.topic.gist.split()) == 15 and obs.topic.gist.endswith("…")
    assert len(obs.topic.micro_gist.split()) == 5 and obs.topic.micro_gist.endswith("…")
    assert len(obs.trajectory_note.split()) == 20 and obs.trajectory_note.endswith("…")


def test_confidence_floor_forces_unknown(tmp_path):
    # stance confidence 0.2 in VALID_RESPONSE -> harness overrides to unknown.
    client = FakeClient([VALID_RESPONSE])
    obs = Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    assert obs.stance == Stance.UNKNOWN
    assert obs.confidence["stance"] == 0.2  # recorded, not erased


def test_unrecognized_enum_resolves_to_unknown(tmp_path):
    fields = json.loads(VALID_RESPONSE)
    fields["phase"] = "vibing"
    client = FakeClient([json.dumps(fields)])
    obs = Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    assert obs.phase == Phase.UNKNOWN


def test_retry_once_on_unparseable_response(tmp_path):
    client = FakeClient(["sorry, here you go:", VALID_RESPONSE])
    obs = Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    assert obs.phase == Phase.BUILDING
    assert len(client.requests) == 2
    assert "Note" in client.requests[1]["messages"][0]["content"]


def test_second_parse_failure_raises(tmp_path):
    client = FakeClient(["nope", "still nope"])
    with pytest.raises(ValueError):
        Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")


def test_prompt_contains_prior_hints_and_delta(tmp_path):
    client = FakeClient([VALID_RESPONSE])
    Extractor(client=client).extract_segment(_segment(tmp_path), person_id="p1")
    user_message = client.requests[0]["messages"][0]["content"]
    assert "first observation" in user_message  # no prior yet
    assert "Behavioral hints" in user_message
    assert "PERSON: add a sorting function to utils" in user_message
    assert "stderr" in user_message  # failure signal reached the prompt


def test_long_tool_results_are_middle_truncated():
    from presence.pipeline.transcript_parser import ToolResult, TranscriptEvent

    event = TranscriptEvent(type="user", tool_result=ToolResult(stdout="x" * 5000))
    line = format_event(event)
    assert len(line) < 600
    assert "chars omitted" in line


def test_delta_events_limit_what_the_model_sees(tmp_path):
    # Rolling update: with an events override, only the tail reaches the
    # prompt — the session's earlier content must NOT be re-read.
    seg = _segment(tmp_path)
    delta = [e for e in seg.events
             if e.timestamp and e.timestamp >= T0 + timedelta(minutes=48)]
    client = FakeClient([VALID_RESPONSE])
    obs = Extractor(client=client).extract_segment(seg, "p1", events=delta)
    message = client.requests[0]["messages"][0]["content"]
    assert "refactor the config loader" in message
    assert "sorting function" not in message
    assert obs.t_start == seg.t_start  # bounds still cover the whole segment
    assert obs.t_end == seg.t_end


def test_chunking_rolls_observation_forward(tmp_path):
    responses = [VALID_RESPONSE] * 3
    client = FakeClient(responses)
    extractor = Extractor(client=client)
    seg = _segment(tmp_path)
    # Shrink the budget so the synthetic segment needs multiple calls.
    lines = [l for l in map(format_event, seg.events) if l]
    chunks = extractor._chunk(lines, budget=80)
    assert len(chunks) > 1
    assert "\n".join(chunks).count("PERSON") == 2  # nothing dropped


def test_system_prompt_preamble_stripped():
    for version in ("v1", "v2", "v3", "v4"):
        system = load_system_prompt(version)
        assert "state extractor" in system
        assert "unknown is a good answer" in system.lower()
    assert "micro_gist" in load_system_prompt("v4")
    assert "openness" not in load_system_prompt("v4").lower()
    assert "directing" in load_system_prompt("v4")


def test_sidechain_and_meta_events_excluded():
    from presence.pipeline.transcript_parser import TranscriptEvent

    assert format_event(TranscriptEvent(type="user", is_sidechain=True, text="hi")) is None
    assert format_event(TranscriptEvent(type="user", is_meta=True, text="hi")) is None


def test_no_key_raises_cleanly(tmp_path, monkeypatch):
    import presence.extract.extractor as ex

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(ex, "REPO_ROOT", tmp_path)  # no .env here
    with pytest.raises(ExtractionError):
        Extractor()
