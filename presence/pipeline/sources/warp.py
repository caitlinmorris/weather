"""Warp capture source (spec: docs/multi-tool-capture.md, probes 2026-07-15).

Reads ONLY two tables: ai_queries (the person's typed AI prompts, with
timestamp and working directory) and commands (exit codes — the behavioral
channel). NEVER conversation_data: it contains no dialogue, and the usage/
credit metadata in it is nobody's business but Warp's.

The allowlist (PRESENCE_ALLOWLIST_WARP: comma-separated absolute path
prefixes) is applied IN the SQL WHERE clause — rows from unconsented
directories are never read into memory at all.

Timestamps in warp.sqlite are naive; we treat them as UTC (SQLite
CURRENT_TIMESTAMP convention). VERIFY LIVE at onboarding: run one command,
confirm its stored start_ts is now-in-UTC — the Z-vs-offset lesson.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from presence.pipeline import config
from presence.pipeline.segmenter import Segment, segment_events
from presence.pipeline.transcript_parser import ToolResult, TranscriptEvent

WARP_DB = (Path.home() / "Library/Group Containers/2BBY89MBSN.dev.warp"
           / "Library/Application Support/dev.warp.Warp-Stable/warp.sqlite")


class WarpSource:
    name = "warp"

    def __init__(self, db_path: Path | None = None,
                 allow_prefixes: list[str] | None = None):
        self.db_path = db_path or WARP_DB
        if allow_prefixes is None:
            raw = config.env_value("PRESENCE_ALLOWLIST_WARP") or ""
            allow_prefixes = [p.strip() for p in raw.split(",") if p.strip()]
        self.allow = allow_prefixes

    def available(self) -> bool:
        return self.db_path.is_file() and bool(self.allow)

    # -- internals ---------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        # Read-only open: safe while Warp itself is running.
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def _where(self, column: str) -> tuple[str, list[str]]:
        clause = "(" + " OR ".join(f"{column} LIKE ?" for _ in self.allow) + ")"
        return clause, [p.rstrip("/") + "%" for p in self.allow]

    @staticmethod
    def _ts(raw: str | None) -> datetime | None:
        if not raw:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    # -- CaptureSource contract ---------------------------------------------------

    def events(self) -> list[TranscriptEvent]:
        events: list[TranscriptEvent] = []
        conn = self._conn()
        try:
            where, params = self._where("working_directory")
            for ts, text, wd in conn.execute(
                f"SELECT start_ts, input, working_directory FROM ai_queries"
                f" WHERE start_ts IS NOT NULL AND {where}", params):
                stamp = self._ts(ts)
                if stamp and text:
                    events.append(TranscriptEvent(
                        type="user", is_human_prompt=True, text=text,
                        timestamp=stamp, cwd=wd, session_id="warp",
                    ))
            where, params = self._where("pwd")
            for ts, exit_code, pwd in conn.execute(
                f"SELECT start_ts, exit_code, pwd FROM commands"
                f" WHERE start_ts IS NOT NULL AND {where}", params):
                stamp = self._ts(ts)
                if stamp is None:
                    continue
                failed = exit_code not in (0, None)
                # Command TEXT stays local (secrets risk, and the semantic
                # channel doesn't need it) — only the outcome crosses. A
                # success says "exit 0" explicitly: for Warp, empty output
                # IS an outcome, and the behavioral channel must not read
                # it as a silent action (ruling B1 refinement).
                events.append(TranscriptEvent(
                    type="tool", timestamp=stamp, cwd=pwd, session_id="warp",
                    tool_result=ToolResult(
                        stdout="" if failed else "exit 0",
                        stderr=f"exit {exit_code}" if failed else "",
                    ),
                ))
        finally:
            conn.close()
        events.sort(key=lambda e: e.timestamp)
        return events

    def segments(self, min_minutes: int) -> list[tuple[str, Segment]]:
        person = config.PERSON_ID if config.GROUP_MODE == "person" else "warp"
        pairs = []
        for seg in segment_events(self.events()):
            if seg.duration_minutes >= min_minutes:
                seg.origin = self.name
                pairs.append((person, seg))
        return pairs

    def last_activity(self) -> datetime | None:
        if not self.available():
            return None
        conn = self._conn()
        try:
            wq, pq = self._where("working_directory"), self._where("pwd")
            row = conn.execute(
                f"SELECT MAX(ts) FROM (SELECT MAX(start_ts) AS ts FROM ai_queries"
                f" WHERE {wq[0]} UNION SELECT MAX(start_ts) FROM commands"
                f" WHERE {pq[0]})", wq[1] + pq[1]).fetchone()
            return self._ts(row[0]) if row else None
        finally:
            conn.close()
