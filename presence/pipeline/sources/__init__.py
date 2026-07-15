"""Capture sources: each tool a person works in provides one CaptureSource.

The contract (duck-typed; see claude_code.py for the reference):
    name: str                      — source id, also the Source enum value
    available() -> bool            — is this tool present on this machine?
    segments(min_minutes) -> list[(person_id, Segment)]
    last_activity() -> datetime|None   — allowlist-scoped heartbeat instant

Active sources come from PRESENCE_SOURCES in .env (default: claude_code).
Every source enforces its own allowlist BEFORE reading content — consent
filtering happens at discovery, never after ingestion.
"""

from __future__ import annotations

from presence.pipeline.config import env_value


def active_sources() -> list:
    names = [
        n.strip()
        for n in (env_value("PRESENCE_SOURCES") or "claude_code").split(",")
        if n.strip()
    ]
    out = []
    for name in names:
        if name == "claude_code":
            from presence.pipeline.sources.claude_code import ClaudeCodeSource
            out.append(ClaudeCodeSource())
        elif name == "warp":
            from presence.pipeline.sources.warp import WarpSource
            out.append(WarpSource())
        else:
            print(f"unknown capture source '{name}' — skipping")
    return [s for s in out if s.available()]
