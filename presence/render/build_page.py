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

from presence.pipeline import config
from presence.pipeline.store import PublicStore

OUT = Path(__file__).parent / "ambient.html"
TEMPLATE = Path(__file__).parent / "template.html"
CACHE_FRESH_SECONDS = 15 * 60


def group_cache_data() -> tuple[list[dict], list[str]] | None:
    """Merge every fresh per-board relay cache into the page's data shape.

    The composite exists only in this viewer's eyes: states are tagged with
    their board for hover provenance and per-board weather lines, and a
    person appearing on multiple boards (usually the viewer) dedups by
    timestamp. Boards' data never mixes server-side — this merge is the
    only place they meet, and only for rendering."""
    merged: dict[str, dict] = {}
    boards: list[str] = []
    for cache in sorted(config.DATA_DIR.glob("group_cache*.json")):
        if time.time() - cache.stat().st_mtime > CACHE_FRESH_SECONDS:
            continue  # stale board: fall back rather than lie quietly
        board = cache.stem.replace("group_cache", "").strip("_") or "board"
        boards.append(board)  # an EMPTY board still exists — room, lights on
        group = json.loads(cache.read_text())
        for entry in group.get("per_person", []):
            person = merged.setdefault(
                entry["person_id"], {"person": entry["person_id"], "states": {}}
            )
            for s in entry.get("states", []):
                person["states"].setdefault(s["updated_at"], {
                    "t": s["updated_at"],
                    "gist": s.get("topic_gist", ""),
                    "micro": s.get("topic_micro", ""),
                    "tags": s.get("topic_tags", []),
                    "phase": s.get("phase", "unknown"),
                    "openness": s.get("openness", "unknown"),
                    "last_active": s.get("last_active"),
                    "board": board,
                })
    if not boards:
        return None
    data = [
        {"person": pid, "states": sorted(p["states"].values(), key=lambda s: s["t"])}
        for pid, p in sorted(merged.items()) if p["states"]
    ]
    return (data, boards) if data else None


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


def build(
    store: PublicStore,
    out: Path = OUT,
    allow_cache: bool = True,
    allow_empty: bool = False,
) -> Path:
    boards: list[str] = []
    cached = group_cache_data() if allow_cache else None
    if cached:
        data, boards = cached
    else:
        data = page_data(store)
    if not data and not allow_empty:
        raise SystemExit("public store is empty — run extract_all first")
    data = data or []  # first run: an empty, honest "still air" field
    payload = json.dumps(data).replace("</", "<\\/")
    html = TEMPLATE.read_text().replace("__DATA__", payload)
    html = html.replace("__BOARDS__", json.dumps(boards))
    out.write_text(html)
    return out


def main() -> None:
    store = PublicStore(config.PUBLIC_DB)
    out = build(store)
    people = len(page_data(store))
    store.close()
    print(f"wrote {out} ({people} people)")
    print("open it with:  open " + str(out))


if __name__ == "__main__":
    main()
