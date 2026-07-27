"""Semantic extraction harness: Segment -> SessionObservation.

Implements the rolling-update design from docs/capture-overlay-architecture-v1:
the model sees the previous observation (compressed memory), shallow behavioral
hints, and a bounded delta of new events — never whole-session re-reads. Long
segments are processed as sequential chunks, threading the observation through.

The prompt (prompts/v1.md) does the judgment; this file does plumbing:
truncation, chunking, JSON parsing/validation, and deterministic enforcement of
the confidence floor (low-confidence enum -> unknown happens HERE, in code,
so abstention doesn't depend on the model following instructions).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from presence.core.schema import (
    Momentum,
    Phase,
    SessionObservation,
    Source,
    Stance,
    Topic,
)
from presence.pipeline.segmenter import Segment
from presence.pipeline.transcript_parser import TranscriptEvent

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = Path(__file__).parent / "prompts"

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_DELTA_CHARS = 16_000  # ~4k tokens; per-call cap from the architecture doc
HUMAN_PROMPT_KEEP = 2_000  # human prompts are kept most generously
ASSISTANT_KEEP = 1_200
TOOL_RESULT_KEEP = 400  # first/last 200 chars; behavioral channel reads them in full
CONFIDENCE_FLOOR = 0.5
DEFAULT_PROMPT_VERSION = "v4"

# Spec word limits, enforced mechanically (the model is told they're hard).
WORD_CAPS = {"gist": 15, "micro_gist": 5, "trajectory_note": 20}

ENUM_FIELDS = {
    "phase": Phase,
    "momentum": Momentum,
    "stance": Stance,
}


def extraction_backend() -> str:
    """'api' (default: Anthropic API on the person's key) or 'claude_cli'
    (bills to their Claude subscription via the local claude CLI)."""
    from presence.pipeline.config import env_value

    return env_value("PRESENCE_EXTRACTOR") or "api"


def load_api_key() -> str | None:
    """ANTHROPIC_API_KEY from the environment, else from repo-root .env."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_file = REPO_ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


def load_system_prompt(version: str) -> str:
    """The prompt file's preamble (title + rationale, above the first ---) is
    documentation for humans; only what follows is sent to the model."""
    text = (PROMPTS_DIR / f"{version}.md").read_text()
    _, _, body = text.partition("\n---\n")
    return body.strip() if body else text


def _middle_truncate(text: str, keep: int) -> str:
    if len(text) <= keep:
        return text
    half = keep // 2
    return f"{text[:half]} …[{len(text) - keep} chars omitted]… {text[-half:]}"


def format_event(event: TranscriptEvent) -> str | None:
    """One delta line per event; None for events with no semantic signal.
    Sidechain (subagent) traffic is excluded: it's tool-internal, not the
    person working."""
    if event.is_sidechain or event.is_meta:
        return None
    t = f"[{event.timestamp:%H:%M}]" if event.timestamp else "[--:--]"

    if event.is_human_prompt:
        return f"{t} PERSON: {_middle_truncate(event.text, HUMAN_PROMPT_KEEP)}"

    if event.type == "assistant":
        parts = []
        if event.text:
            parts.append(_middle_truncate(event.text, ASSISTANT_KEEP))
        if event.tool_names:
            parts.append(f"(ran tools: {', '.join(event.tool_names)})")
        return f"{t} ASSISTANT: {' '.join(parts)}" if parts else None

    if event.tool_result is not None:
        r = event.tool_result
        parts = [f"stdout {len(r.stdout)} chars"]
        if r.stdout:
            parts.append(_middle_truncate(r.stdout, TOOL_RESULT_KEEP))
        if r.stderr:
            parts.append(f"| stderr: {_middle_truncate(r.stderr, TOOL_RESULT_KEEP)}")
        return f"{t} TOOL_RESULT: {' '.join(parts)}"

    return None


def shallow_hints(segment: Segment) -> str:
    """Window-shape context that accompanies the behavioral testimony."""
    return (
        f"segment duration: {segment.duration_minutes:.0f} min; "
        f"human prompts: {segment.human_prompt_count}"
    )


class ExtractionError(Exception):
    pass


class Extractor:
    def __init__(
        self,
        client=None,
        model: str = DEFAULT_MODEL,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ):
        if client is None:
            if extraction_backend() == "claude_cli":
                from presence.extract.cli_client import ClaudeCliClient

                client = ClaudeCliClient()
            else:
                import anthropic

                key = load_api_key()
                if not key:
                    raise ExtractionError(
                        "No ANTHROPIC_API_KEY found in environment or .env at repo root"
                    )
                client = anthropic.Anthropic(api_key=key)
        self.client = client
        self.model = model
        self.system_prompt = load_system_prompt(prompt_version)
        self.extractor_version = f"{prompt_version}+{model}"

    # -- public entry point ----------------------------------------------------

    def extract_segment(
        self,
        segment: Segment,
        person_id: str,
        previous: SessionObservation | None = None,
        events: list[TranscriptEvent] | None = None,
    ) -> SessionObservation:
        """Roll the observation through the segment, one bounded chunk at a
        time. Pass `events` to extract only a delta (the rolling-update
        design: previous observation as compressed memory + new events only —
        never re-reading the whole session)."""
        window_events = events if events is not None else segment.events
        lines = [l for l in (format_event(e) for e in window_events) if l]
        obs = previous
        # The behavioral channel testifies over exactly the events the
        # semantic channel will read (docs/behavioral-rulings.md).
        from presence.core.behavioral import hint_block

        hints = shallow_hints(segment) + "; " + hint_block(window_events)
        for chunk in self._chunk(lines):
            obs = self._update(obs, chunk, hints, person_id)
        if obs is None:
            raise ExtractionError("segment contained no extractable events")
        obs.t_start = segment.t_start
        obs.t_end = segment.t_end
        try:
            obs.source = Source(segment.origin)
        except ValueError:
            obs.source = Source.OTHER
        return obs

    # -- internals ---------------------------------------------------------------

    @staticmethod
    def _chunk(lines: list[str], budget: int = MAX_DELTA_CHARS) -> list[str]:
        chunks, current, size = [], [], 0
        for line in lines:
            if current and size + len(line) > budget:
                chunks.append("\n".join(current))
                current, size = [], 0
            current.append(line)
            size += len(line)
        if current:
            chunks.append("\n".join(current))
        return chunks

    def _update(
        self,
        previous: SessionObservation | None,
        delta: str,
        hints: str,
        person_id: str,
    ) -> SessionObservation:
        prev_block = (
            _observation_for_prompt(previous) if previous else "none — first observation"
        )
        user_message = (
            f"## Previous observation\n{prev_block}\n\n"
            f"## Behavioral hints\n{hints}\n\n"
            f"## Delta (new events since previous observation)\n{delta}"
        )
        raw = self._call(user_message)
        try:
            fields = _parse_json(raw)
        except ValueError as first_error:
            raw = self._call(
                user_message
                + "\n\n## Note\nYour previous reply was not parseable as a single "
                f"JSON object ({first_error}). Return ONLY the JSON object."
            )
            fields = _parse_json(raw)  # second failure propagates
        return _build_observation(fields, person_id, self.extractor_version)

    def _call(self, user_message: str) -> str:
        import time

        last_error = None
        for attempt in range(3):  # transient 5xx/overload resilience
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                return "".join(b.text for b in response.content if b.type == "text")
            except Exception as e:
                status = getattr(e, "status_code", None)
                if status is not None and status >= 500 and attempt < 2:
                    last_error = e
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        raise last_error


# -- response handling ------------------------------------------------------------


def _observation_for_prompt(obs: SessionObservation) -> str:
    """Compact prior-state block (~300 tokens): judgment fields only."""
    return json.dumps(
        {
            "topic": obs.topic.model_dump(),
            "phase": obs.phase.value,
            "momentum": obs.momentum.value,
            "stance": obs.stance.value,
            "trajectory_note": obs.trajectory_note,
        }
    )


def _parse_json(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in response")
    try:
        obj = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON is not an object")
    return obj


def _cap_words(text: str, cap: int) -> str:
    words = text.split()
    return " ".join(words[:cap]) + ("…" if len(words) > cap else "")


def _build_observation(
    fields: dict, person_id: str, extractor_version: str
) -> SessionObservation:
    """Validate model output into the schema. Deterministic guards live here:
    unrecognized enum values and sub-floor confidence resolve to unknown, and
    word limits are enforced by truncation rather than trust."""
    topic_raw = fields.get("topic") or {}
    confidence = {
        k: float(v)
        for k, v in (fields.get("confidence") or {}).items()
        if isinstance(v, (int, float))
    }

    def enum_value(name: str, enum_cls):
        raw_value = str(fields.get(name, "unknown")).lower()
        try:
            value = enum_cls(raw_value)
        except ValueError:
            return enum_cls.UNKNOWN
        if confidence.get(name, 0.0) < CONFIDENCE_FLOOR:
            return enum_cls.UNKNOWN
        return value

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return SessionObservation(
        person_id=person_id,
        t_start=now,  # overwritten with segment bounds by extract_segment
        t_end=now,
        source=Source.CLAUDE_CODE,
        extractor_version=extractor_version,
        topic=Topic(
            tags=[str(t) for t in (topic_raw.get("tags") or [])][:7],
            gist=_cap_words(str(topic_raw.get("gist") or ""), WORD_CAPS["gist"]),
            micro_gist=_cap_words(
                str(topic_raw.get("micro_gist") or ""), WORD_CAPS["micro_gist"]
            ),
            domain=str(topic_raw.get("domain") or ""),
        ),
        phase=enum_value("phase", Phase),
        momentum=enum_value("momentum", Momentum),
        stance=enum_value("stance", Stance),
        trajectory_note=_cap_words(
            str(fields.get("trajectory_note") or ""), WORD_CAPS["trajectory_note"]
        ),
        confidence=confidence,
        evidence={
            k: str(v) for k, v in (fields.get("evidence") or {}).items()
        },
    )
