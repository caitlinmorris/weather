"""Allowlist review: notice new project folders, include them deliberately.

The allowlist is consent layer (a) — this tool NEVER widens it automatically.
It diffs what exists on disk against what's allowed and what you've already
reviewed (a local "seen" ledger), and asks. Folders you decline stay quiet
forever unless you rerun the review.

Usage:
    python -m presence.pipeline.projects          # review NEW folders only
    python -m presence.pipeline.projects all      # revisit everything,
                                                  #   including past declines
    python -m presence.pipeline.projects status   # list only, change nothing

After any change: restart the we.ather app (settings load at launch).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from presence.pipeline.config import (
    ALLOWED_PROJECT_PREFIXES,
    DATA_DIR,
    PROJECTS_ROOT,
    REPO_ROOT,
)

SEEN_LEDGER = DATA_DIR / "projects_seen.json"


def all_project_dirs() -> list[str]:
    if not PROJECTS_ROOT.is_dir():
        return []
    return sorted(p.name for p in PROJECTS_ROOT.iterdir() if p.is_dir())


def is_allowed(name: str) -> bool:
    return any(name.startswith(pre) for pre in ALLOWED_PROJECT_PREFIXES)


def load_seen() -> set[str]:
    if SEEN_LEDGER.is_file():
        return set(json.loads(SEEN_LEDGER.read_text()))
    return set()


def save_seen(seen: set[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_LEDGER.write_text(json.dumps(sorted(seen)))


def unreviewed() -> list[str]:
    """Folders that are neither allowed nor previously reviewed — the ones
    worth a quiet launch-time notice."""
    seen = load_seen()
    return [n for n in all_project_dirs() if not is_allowed(n) and n not in seen]


def rewrite_allowlist(env_path: Path, prefixes: list[str]) -> None:
    """Persist the allowlist to .env, replacing the existing line in place."""
    line = "PRESENCE_ALLOWLIST=" + ",".join(prefixes)
    lines = env_path.read_text().splitlines() if env_path.is_file() else []
    replaced = False
    for i, existing in enumerate(lines):
        if existing.startswith("PRESENCE_ALLOWLIST="):
            lines[i] = line
            replaced = True
            break
    if not replaced:
        lines.append(line)
    env_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "new"
    dirs = all_project_dirs()
    if not dirs:
        print(f"no project folders found under {PROJECTS_ROOT}")
        return

    new = unreviewed()
    excluded = [n for n in dirs if not is_allowed(n) and n not in new]

    print(f"allowed prefixes: {len(ALLOWED_PROJECT_PREFIXES)}")
    for n in dirs:
        if is_allowed(n):
            print(f"  [observed] {n}")
    for n in excluded:
        print(f"  [excluded] {n}")
    for n in new:
        print(f"  [NEW]      {n}")

    pool = new + excluded if mode == "all" else new
    if mode == "status" or not pool:
        if not pool:
            print("nothing to review" + ("" if mode == "all" else
                  " (past declines: rerun with 'all')"))
        return

    if not sys.stdin.isatty():
        print(f"\n{len(pool)} folder(s) to review; rerun interactively")
        return

    prefixes = list(ALLOWED_PROJECT_PREFIXES)
    seen = load_seen()
    added = 0
    print("\nReview folders (y = observe it, N = leave it private):")
    for n in pool:
        answer = input(f"  include {n}? [y/N] ").strip().lower()
        seen.add(n)
        if answer == "y":
            prefixes.append(n)
            added += 1
    save_seen(seen)
    if added:
        rewrite_allowlist(REPO_ROOT / ".env", prefixes)
        print(f"\nadded {added} folder(s) to .env — RESTART the app to apply")
    else:
        print("\nno changes; these folders won't be mentioned again")


if __name__ == "__main__":
    main()
