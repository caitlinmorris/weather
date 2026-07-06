"""Synthetic transcript fixtures. All content here is invented; per CLAUDE.md,
no real conversation content may ever appear in tests or fixtures."""

import json
from datetime import datetime, timedelta, timezone

T0 = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)
SESSION_ID = "synthetic-session-0001"


def _base(event_type: str, t: datetime) -> dict:
    return {
        "type": event_type,
        "uuid": f"uuid-{t.timestamp():.0f}",
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "sessionId": SESSION_ID,
        "cwd": "/home/synthetic/project",
        "version": "synthetic-1.0",
        "isSidechain": False,
    }


def user_prompt(t: datetime, text: str) -> dict:
    return {**_base("user", t), "message": {"role": "user", "content": text}}


def assistant_turn(t: datetime, text: str, tools: list[str] = ()) -> dict:
    content = [{"type": "thinking", "thinking": "internal"}]
    if text:
        content.append({"type": "text", "text": text})
    for name in tools:
        content.append({"type": "tool_use", "name": name, "id": "tu-1", "input": {}})
    return {**_base("assistant", t), "message": {"role": "assistant", "content": content}}


def tool_result(t: datetime, stdout: str = "", stderr: str = "") -> dict:
    return {
        **_base("user", t),
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "tu-1", "content": stdout}],
        },
        "toolUseResult": {"stdout": stdout, "stderr": stderr, "interrupted": False},
    }


def synthetic_transcript_lines() -> list[str]:
    """A small fake session: two work bursts separated by a 45-minute gap."""
    events = [
        user_prompt(T0, "add a sorting function to utils"),
        assistant_turn(T0 + timedelta(minutes=1), "Adding it now.", ["Edit"]),
        tool_result(T0 + timedelta(minutes=2), stdout="ok"),
        assistant_turn(T0 + timedelta(minutes=3), "Done, tests pass."),
        # 45-minute gap: the segmenter should split here.
        user_prompt(T0 + timedelta(minutes=48), "now refactor the config loader"),
        assistant_turn(T0 + timedelta(minutes=50), "Refactoring.", ["Edit", "Bash"]),
        tool_result(T0 + timedelta(minutes=51), stdout="", stderr="1 test failed"),
    ]
    return [json.dumps(e) for e in events]


def write_synthetic_transcript(path) -> None:
    path.write_text("\n".join(synthetic_transcript_lines()) + "\n")
