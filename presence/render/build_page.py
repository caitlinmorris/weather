"""Generate render/ambient.html from the public store.

Reads the PUBLIC side only (read-only): this module sees exactly what a
colleague's renderer would see, nothing more — running it is itself a check
that the boundary holds. The page is fully self-contained (data embedded, no
network), so it can be opened as a file or projected for a demo.

Usage: python -m presence.render.build_page
"""

from __future__ import annotations

import json
from pathlib import Path

from presence.pipeline.config import PUBLIC_DB
from presence.pipeline.store import PublicStore

OUT = Path(__file__).parent / "ambient.html"
TEMPLATE = Path(__file__).parent / "template.html"


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


def build(store: PublicStore, out: Path = OUT) -> Path:
    data = page_data(store)
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
