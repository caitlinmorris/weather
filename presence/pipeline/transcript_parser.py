"""Narrow interface over Claude Code's on-disk JSONL transcripts.

This is the ONLY module that touches the raw format; everything downstream
consumes TranscriptEvent. Built against the format verified on this machine
2026-07-06; tests/test_canary_format.py fails loudly if a Claude Code update
changes it.

Privacy: TranscriptEvent carries raw text (the behavioral and semantic channels
need it, within the personal boundary), but its repr shows metadata only, so an
accidental print/log/traceback never leaks content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator


@dataclass
class ToolResult:
    """Structured result of one tool call (from the toolUseResult field)."""

    stdout: str = ""
    stderr: str = ""
    interrupted: bool = False

    def __repr__(self) -> str:  # metadata only, never content
        return (
            f"ToolResult(stdout_len={len(self.stdout)}, "
            f"stderr_len={len(self.stderr)}, interrupted={self.interrupted})"
        )


@dataclass
class TranscriptEvent:
    type: str
    uuid: str | None = None
    timestamp: datetime | None = None
    session_id: str | None = None
    cwd: str | None = None
    version: str | None = None
    role: str | None = None
    is_meta: bool = False
    is_sidechain: bool = False
    # Human-typed prompt (user events with string content) or assistant prose
    # (concatenated text blocks; thinking blocks are excluded).
    text: str = ""
    is_human_prompt: bool = False
    tool_names: list[str] = field(default_factory=list)
    tool_result: ToolResult | None = None

    def __repr__(self) -> str:  # metadata only, never content
        return (
            f"TranscriptEvent(type={self.type!r}, role={self.role!r}, "
            f"t={self.timestamp}, text_len={len(self.text)}, "
            f"human_prompt={self.is_human_prompt}, tools={self.tool_names})"
        )


def _parse_timestamp(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_tool_result(raw: object) -> ToolResult | None:
    if isinstance(raw, dict):
        return ToolResult(
            stdout=str(raw.get("stdout") or ""),
            stderr=str(raw.get("stderr") or ""),
            interrupted=bool(raw.get("interrupted", False)),
        )
    if isinstance(raw, str):
        return ToolResult(stdout=raw)
    return None


def _event_from_obj(obj: dict) -> TranscriptEvent:
    event = TranscriptEvent(
        type=str(obj.get("type", "unknown")),
        uuid=obj.get("uuid"),
        timestamp=_parse_timestamp(obj.get("timestamp")),
        session_id=obj.get("sessionId"),
        cwd=obj.get("cwd"),
        version=obj.get("version"),
        is_meta=bool(obj.get("isMeta", False)),
        is_sidechain=bool(obj.get("isSidechain", False)),
        tool_result=_parse_tool_result(obj.get("toolUseResult")),
    )

    message = obj.get("message")
    if not isinstance(message, dict):
        return event

    event.role = message.get("role")
    content = message.get("content")

    if isinstance(content, str):
        event.text = content
        event.is_human_prompt = event.type == "user" and not event.is_meta
    elif isinstance(content, list):
        texts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                texts.append(str(block.get("text") or ""))
            elif block_type == "tool_use":
                event.tool_names.append(str(block.get("name") or "unknown"))
            # thinking and tool_result blocks are intentionally not collected
            # into text: thinking is model-internal, and tool results arrive
            # via the structured toolUseResult field instead.
        event.text = "\n".join(texts)

    return event


def parse_transcript(path: Path) -> Iterator[TranscriptEvent]:
    """Yield events from one transcript file, skipping unparseable lines.

    Skipped-line counts are the canary test's business; day-to-day callers just
    get the events that parsed.
    """
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield _event_from_obj(obj)
