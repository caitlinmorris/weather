"""Pipeline configuration. Per-machine settings live in .env (written by
install.sh); this module only supplies mechanics and defaults.

The allowlist is a hard privacy boundary (see CLAUDE.md): only transcripts
from projects listed in PRESENCE_ALLOWLIST are ever read. The person
installing chooses it — widening it is a human decision, never a default.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_ROOT = Path.home() / ".claude" / "projects"
SESSION_GAP_MINUTES = 30


def env_value(name: str) -> str | None:
    """Read a setting from the environment, falling back to repo-root .env."""
    import os

    value = os.environ.get(name)
    if value:
        return value
    env_file = REPO_ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


# Claude Code encodes a project's working directory into its folder name by
# replacing "/" with "-"; entries here are prefix-matched against those names.
# Comma-separated in .env: PRESENCE_ALLOWLIST=-Users-x-proj1,-Users-x-proj2
_raw_allowlist = env_value("PRESENCE_ALLOWLIST") or ""
ALLOWED_PROJECT_PREFIXES = [p.strip() for p in _raw_allowlist.split(",") if p.strip()]

# --- identity -----------------------------------------------------------------
# GROUP_MODE "projects": each project renders as a pseudo-person (the replay /
# demo trick). GROUP_MODE "person": all allowlisted projects roll up into one
# human — PERSON_ID — required for a real multi-person pilot. Flip via .env,
# then run: python -m presence.pipeline.migrate_identity
GROUP_MODE = env_value("PRESENCE_GROUP_MODE") or "projects"
PERSON_ID = env_value("PRESENCE_PERSON_ID") or "me"


def person_for_project(project_dir_name: str) -> str:
    if GROUP_MODE == "person":
        return PERSON_ID
    return project_dir_name.rsplit("-", 1)[-1]


DATA_DIR = REPO_ROOT / "data"
PRIVATE_DB = DATA_DIR / "private.db"
PUBLIC_DB = DATA_DIR / "public.db"
GROUP_CACHE = DATA_DIR / "group_cache.json"
PAUSE_FLAG = DATA_DIR / "paused"


def allowed_project_dirs() -> list[Path]:
    """Project folders under PROJECTS_ROOT that match the allowlist."""
    if not PROJECTS_ROOT.is_dir():
        return []
    return sorted(
        p
        for p in PROJECTS_ROOT.iterdir()
        if p.is_dir() and any(p.name.startswith(pre) for pre in ALLOWED_PROJECT_PREFIXES)
    )


def allowed_transcripts() -> list[Path]:
    """All transcript files the pipeline is permitted to read."""
    return sorted(f for d in allowed_project_dirs() for f in d.glob("*.jsonl"))
