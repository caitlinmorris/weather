"""Generate render/ambient.html from the freshest group view available:
the relay's group cache when it exists and is recent (multi-person mode),
else the local public store. Either way this module reads only published
state — running it is itself a check that the boundary holds.

Usage: python -m presence.render.build_page
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from presence.pipeline.config import GROUP_CACHE, PUBLIC_DB
from presence.pipeline.store import PublicStore

OUT = Path(__file__).parent / "ambient.html"
TEMPLATE = Path(__file__).parent / "template.html"
CACHE_FRESH_SECONDS = 15 * 60


def group_cache_data() -> list[dict] | None:
    """Adapt a fresh relay group cache to the page's data shape, or None."""
    if not GROUP_CACHE.is_file():
        return None
    if time.time() - GROUP_CACHE.stat().st_mtime > CACHE_FRESH_SECONDS:
        return None  # stale cache: fall back to local rather than lie quietly
    group = json.loads(GROUP_CACHE.read_text())
    data = []
    for entry in group.get("per_person", []):
        states = [
            {
                "t": s["updated_at"],
                "gist": s.get("topic_gist", ""),
                "micro": s.get("topic_micro", ""),
                "tags": s.get("topic_tags", []),
                "phase": s.get("phase", "unknown"),
                "openness": s.get("openness", "unknown"),
            }
            for s in entry.get("states", [])
        ]
        if states:
            data.append({"person": entry["person_id"], "states": states})
    return data or None


def page_data(store: PublicStore) -> list[dict]:
    people = sorted({s.person_id for s in store.all_latest()})
    data = []
    for person in people:
        states = [
            {
                "t": s.updated_at.isoformat(),
                "gist": s.topic_gist,
                "micro": s.topic_micro,
                "tags": s.topic_tags,
                "phase": s.phase.value,
                "openness": s.openness.value,
            }
            for s in store.history(person)
        ]
        data.append({"person": person, "states": states})
    return data


def build(store: PublicStore, out: Path = OUT, allow_cache: bool = True) -> Path:
    data = (group_cache_data() if allow_cache else None) or page_data(store)
    if not data:
        raise SystemExit("public store is empty — run extract_all first")
    payload = json.dumps(data).replace("</", "<\\/")
    out.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    return out


def main() -> None:
    store = PublicStore(PUBLIC_DB)
    out = build(store)
    people = len(page_data(store))
    store.close()
    print(f"wrote {out} ({people} people)")
    print("open it with:  open " + str(out))


if __name__ == "__main__":
    main()
