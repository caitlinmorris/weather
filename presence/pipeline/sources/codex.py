"""Codex CLI capture source (structure from a tester's probe output,
docs/codex-probes.sh, 2026-07-30).

Codex stores sessions as JSONL "rollout" files under ~/.codex/sessions/,
one line per record: {timestamp, type, payload}. We read only two types:

- session_meta  — payload.cwd, the session's working directory: the
  consent gate. If it doesn't match PRESENCE_ALLOWLIST_CODEX (absolute
  path prefixes), the REST OF THE FILE IS NEVER PARSED — the allowlist
  applies at the first line, before any content is read.
- response_item — payload.role + payload.content: the person's typed
  prompts (role=user -> human prompt) and the assistant's prose
  (role=assistant). Other payload types (function calls, reasoning,
  world_state, event_msg, ...) are skipped: the semantic channel needs
  narration, and Codex's tool internals stay local.

Known v1 limits: a session that *changes* into an allowlisted directory
mid-way is skipped (gate is the session's starting cwd); no command exit
codes are read yet, so the behavioral channel is quieter for Codex than
for Warp.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from presence.pipeline import config
from presence.pipeline.segmenter import Segment, segment_events
from presence.pipeline.transcript_parser import TranscriptEvent

CODEX_SESSIONS = Path.home() / ".codex" / "sessions"


def _ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _content_text(content) -> str:
    """Defensive text extraction: content is a list of typed items whose
    exact shapes the probe truncated — take any dict's 'text' str, join."""
    parts = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
    elif isinstance(content, str):
        parts.append(content)
    return "\n".join(p for p in parts if p.strip())


class CodexSource:
    name = "codex"

    def __init__(self, sessions_root: Path | None = None,
                 allow_prefixes: list[str] | None = None):
        self.root = sessions_root or CODEX_SESSIONS
        if allow_prefixes is None:
            raw = config.env_value("PRESENCE_ALLOWLIST_CODEX") or ""
            allow_prefixes = [p.strip() for p in raw.split(",") if p.strip()]
        self.allow = allow_prefixes

    def available(self) -> bool:
        return self.root.is_dir() and bool(self.allow)

    # -- internals ---------------------------------------------------------------

    def _allowed_cwd(self, cwd: str | None) -> bool:
        if not cwd:
            return False
        return any(cwd == p.rstrip("/") or cwd.startswith(p.rstrip("/") + "/")
                   for p in self.allow)

    def _rollouts(self) -> list[Path]:
        return sorted(self.root.rglob("rollout-*.jsonl"),
                      key=lambda p: p.stat().st_mtime)

    def _session_cwd(self, path: Path) -> str | None:
        """First line only — the consent check reads nothing else."""
        try:
            with path.open() as fh:
                first = json.loads(fh.readline())
        except (OSError, ValueError):
            return None
        if first.get("type") != "session_meta":
            return None
        return (first.get("payload") or {}).get("cwd")

    def _file_events(self, path: Path) -> list[TranscriptEvent]:
        events: list[TranscriptEvent] = []
        cwd = None
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                payload = rec.get("payload") or {}
                kind = rec.get("type")
                if kind == "session_meta":
                    cwd = payload.get("cwd")
                    continue
                if kind == "turn_context":
                    cwd = payload.get("cwd") or cwd
                    continue
                if kind != "response_item":
                    continue
                role = payload.get("role")
                if role not in ("user", "assistant"):
                    continue
                stamp = _ts(rec.get("timestamp"))
                text = _content_text(payload.get("content"))
                if stamp is None or not text:
                    continue
                events.append(TranscriptEvent(
                    type=role, role=role, text=text, timestamp=stamp,
                    cwd=cwd, session_id="codex",
                    is_human_prompt=(role == "user"),
                ))
        return events

    # -- CaptureSource contract ---------------------------------------------------

    def events(self) -> list[TranscriptEvent]:
        events: list[TranscriptEvent] = []
        for path in self._rollouts():
            if self._allowed_cwd(self._session_cwd(path)):
                events.extend(self._file_events(path))
        events.sort(key=lambda e: e.timestamp)
        return events

    def segments(self, min_minutes: int) -> list[tuple[str, Segment]]:
        person = config.PERSON_ID if config.GROUP_MODE == "person" else "codex"
        pairs = []
        for seg in segment_events(self.events()):
            if seg.duration_minutes >= min_minutes:
                seg.origin = self.name
                pairs.append((person, seg))
        return pairs

    def last_activity(self) -> datetime | None:
        from datetime import timezone

        mtimes = [p.stat().st_mtime for p in self._rollouts()
                  if self._allowed_cwd(self._session_cwd(p))]
        if not mtimes:
            return None
        return datetime.fromtimestamp(max(mtimes), tz=timezone.utc)
