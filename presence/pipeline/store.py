"""The two SQLite stores. The privacy boundary is literally a file boundary:
SessionObservations live in private.db; PersonStates live in public.db, and
"publishing" means writing there.

Write access to the public store requires writer=True, which only core/rollup.py
may pass — enforced by tests/test_boundary.py, which greps for violations.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from presence.core.schema import PersonState, SessionObservation


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


class PrivateStore:
    """SessionObservations. Never leaves this machine."""

    def __init__(self, path: Path):
        self.conn = _connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS session_observations (
                observation_id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                t_start TEXT NOT NULL,
                t_end TEXT NOT NULL,
                source TEXT NOT NULL,
                json TEXT NOT NULL
            )"""
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_obs_person_time"
            " ON session_observations (person_id, t_end)"
        )
        self.conn.commit()

    def add(self, obs: SessionObservation) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO session_observations VALUES (?, ?, ?, ?, ?, ?)",
            (
                obs.observation_id,
                obs.person_id,
                obs.t_start.isoformat(),
                obs.t_end.isoformat(),
                obs.source.value,
                obs.model_dump_json(),
            ),
        )
        self.conn.commit()

    def latest(self, person_id: str) -> SessionObservation | None:
        row = self.conn.execute(
            "SELECT json FROM session_observations WHERE person_id = ?"
            " ORDER BY t_end DESC LIMIT 1",
            (person_id,),
        ).fetchone()
        return SessionObservation.model_validate_json(row[0]) if row else None

    def get_span(
        self, person_id: str, t_start: str, t_end: str
    ) -> SessionObservation | None:
        row = self.conn.execute(
            "SELECT json FROM session_observations"
            " WHERE person_id = ? AND t_start = ? AND t_end = ?",
            (person_id, t_start, t_end),
        ).fetchone()
        return SessionObservation.model_validate_json(row[0]) if row else None

    def spans(self) -> dict[tuple[str, str, str], str]:
        """(person_id, t_start, t_end) -> extractor_version for every stored
        observation. Batch extraction skips spans already done at the current
        version and re-extracts spans done at an older one."""
        rows = self.conn.execute(
            "SELECT person_id, t_start, t_end,"
            " json_extract(json, '$.extractor_version')"
            " FROM session_observations"
        ).fetchall()
        return {(p, a, b): v for p, a, b, v in rows}

    def delete_span(self, person_id: str, t_start: str, t_end: str) -> None:
        self.conn.execute(
            "DELETE FROM session_observations"
            " WHERE person_id = ? AND t_start = ? AND t_end = ?",
            (person_id, t_start, t_end),
        )
        self.conn.commit()

    def migrate_person_ids(self, old_ids: list[str], new_id: str) -> int:
        """One-time migration when GROUP_MODE flips projects -> person:
        re-keys existing observations instead of re-extracting them."""
        total = 0
        for old in old_ids:
            cur = self.conn.execute(
                "UPDATE session_observations SET person_id = ?,"
                " json = json_set(json, '$.person_id', ?) WHERE person_id = ?",
                (new_id, new_id, old),
            )
            total += cur.rowcount
        self.conn.commit()
        return total

    def all_observations(self) -> list[SessionObservation]:
        rows = self.conn.execute(
            "SELECT json FROM session_observations ORDER BY t_end"
        ).fetchall()
        return [SessionObservation.model_validate_json(r[0]) for r in rows]

    def window(
        self, person_id: str, since: datetime
    ) -> list[SessionObservation]:
        rows = self.conn.execute(
            "SELECT json FROM session_observations"
            " WHERE person_id = ? AND t_end >= ? ORDER BY t_end",
            (person_id, since.isoformat()),
        ).fetchall()
        return [SessionObservation.model_validate_json(r[0]) for r in rows]

    def close(self) -> None:
        self.conn.close()


class PublicStore:
    """PersonStates: the published side of the boundary.

    History is kept (not just latest) because the replay demo and trajectory
    features both need the time series.
    """

    def __init__(self, path: Path, writer: bool = False):
        self.writer = writer
        self.conn = _connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS person_states (
                person_id TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                json TEXT NOT NULL,
                PRIMARY KEY (person_id, updated_at)
            )"""
        )
        self.conn.commit()

    def publish(self, state: PersonState) -> None:
        if not self.writer:
            raise PermissionError(
                "PublicStore opened read-only; only rollup may publish"
            )
        self.conn.execute(
            "INSERT OR REPLACE INTO person_states VALUES (?, ?, ?)",
            (state.person_id, state.updated_at.isoformat(), state.model_dump_json()),
        )
        self.conn.commit()

    def latest(self, person_id: str) -> PersonState | None:
        row = self.conn.execute(
            "SELECT json FROM person_states WHERE person_id = ?"
            " ORDER BY updated_at DESC LIMIT 1",
            (person_id,),
        ).fetchone()
        return PersonState.model_validate_json(row[0]) if row else None

    def all_latest(self) -> list[PersonState]:
        rows = self.conn.execute(
            """SELECT json FROM person_states p
               WHERE updated_at = (SELECT MAX(updated_at) FROM person_states
                                   WHERE person_id = p.person_id)"""
        ).fetchall()
        return [PersonState.model_validate_json(r[0]) for r in rows]

    def history(self, person_id: str) -> list[PersonState]:
        rows = self.conn.execute(
            "SELECT json FROM person_states WHERE person_id = ? ORDER BY updated_at",
            (person_id,),
        ).fetchall()
        return [PersonState.model_validate_json(r[0]) for r in rows]

    def close(self) -> None:
        self.conn.close()
