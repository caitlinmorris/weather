"""One-time flip from projects (pseudo-people) mode to person mode.

Prerequisite: set PRESENCE_GROUP_MODE=person in .env first. Then this
re-keys all existing private observations to PERSON_ID (no re-extraction
cost), clears the old pseudo-person entries from the public store, and
republishes a single unified timeline.

Usage: python -m presence.pipeline.migrate_identity
"""

from __future__ import annotations

import sys

from presence.core import rollup
from presence.pipeline.config import GROUP_MODE, PERSON_ID, PRIVATE_DB, PUBLIC_DB
from presence.pipeline.store import PrivateStore


def main() -> None:
    if GROUP_MODE != "person":
        print("Set PRESENCE_GROUP_MODE=person in .env first, then rerun.")
        sys.exit(1)

    private = PrivateStore(PRIVATE_DB)
    old_ids = sorted(
        row[0]
        for row in private.conn.execute(
            "SELECT DISTINCT person_id FROM session_observations"
        ).fetchall()
        if row[0] != PERSON_ID
    )
    moved = private.migrate_person_ids(old_ids, PERSON_ID)
    print(f"re-keyed {moved} observations from {old_ids or 'nothing'} -> {PERSON_ID}")

    public = rollup.open_public_writer(PUBLIC_DB)
    for old in old_ids:
        public.conn.execute("DELETE FROM person_states WHERE person_id = ?", (old,))
    public.conn.commit()
    n = rollup.publish_history(private, public, PERSON_ID)
    print(f"republished {n} states for {PERSON_ID}")
    public.close()
    private.close()


if __name__ == "__main__":
    main()
