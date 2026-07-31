"""CodexSource against synthetic rollout files — structure per the
tester's probe (docs/codex-probes.sh output, 2026-07-30)."""

import json
from pathlib import Path

from presence.pipeline.sources.codex import CodexSource


def rollout_line(kind: str, payload: dict, ts="2026-07-30T12:00:00.000Z"):
    return json.dumps({"timestamp": ts, "type": kind, "payload": payload})


def write_rollout(path: Path, cwd: str, lines: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = rollout_line("session_meta", {"session_id": "s1", "cwd": cwd})
    path.write_text("\n".join([meta] + lines) + "\n")


def message(role: str, text: str, ts: str):
    return rollout_line("response_item", {
        "type": "message", "role": role,
        "content": [{"type": "text", "text": text}],
    }, ts)


def test_allowlist_gates_at_first_line(tmp_path):
    allowed = tmp_path / "sessions" / "2026" / "07" / "rollout-a.jsonl"
    write_rollout(allowed, "/Users/x/proj", [
        message("user", "synthetic prompt about maps", "2026-07-30T12:01:00Z"),
        message("assistant", "synthetic reply", "2026-07-30T12:02:00Z"),
    ])
    denied = tmp_path / "sessions" / "2026" / "07" / "rollout-b.jsonl"
    write_rollout(denied, "/Users/x/secret", [
        message("user", "must never surface", "2026-07-30T12:03:00Z"),
    ])
    src = CodexSource(sessions_root=tmp_path / "sessions",
                      allow_prefixes=["/Users/x/proj"])
    events = src.events()
    assert len(events) == 2
    assert all("secret" not in (e.text or "") and "never surface" not in e.text
               for e in events)
    assert events[0].is_human_prompt and events[0].role == "user"
    assert events[0].cwd == "/Users/x/proj"


def test_prefix_match_is_path_aware(tmp_path):
    # /Users/x/proj must not match /Users/x/project-other
    f = tmp_path / "sessions" / "rollout-c.jsonl"
    write_rollout(f, "/Users/x/project-other", [
        message("user", "synthetic", "2026-07-30T12:00:30Z"),
    ])
    src = CodexSource(sessions_root=tmp_path / "sessions",
                      allow_prefixes=["/Users/x/proj"])
    assert src.events() == []
    assert src.last_activity() is None


def test_non_message_records_are_skipped(tmp_path):
    f = tmp_path / "sessions" / "rollout-d.jsonl"
    write_rollout(f, "/Users/x/proj", [
        rollout_line("event_msg", {"type": "turn_started", "turn_id": "t"}),
        rollout_line("world_state", {"full": True, "state": {}}),
        rollout_line("response_item", {"type": "function_call", "role": None,
                                       "content": []}),
        message("user", "the only real narration", "2026-07-30T12:05:00Z"),
    ])
    src = CodexSource(sessions_root=tmp_path / "sessions",
                      allow_prefixes=["/Users/x/proj"])
    events = src.events()
    assert [e.text for e in events] == ["the only real narration"]


def test_last_activity_scoped_to_allowlist(tmp_path):
    f = tmp_path / "sessions" / "rollout-e.jsonl"
    write_rollout(f, "/Users/x/proj",
                  [message("user", "synthetic", "2026-07-30T12:00:10Z")])
    src = CodexSource(sessions_root=tmp_path / "sessions",
                      allow_prefixes=["/Users/x/proj"])
    assert src.last_activity() is not None
    denied = CodexSource(sessions_root=tmp_path / "sessions",
                         allow_prefixes=["/Users/x/other"])
    assert denied.last_activity() is None
