"""Pipeline configuration.

The allowlist is a hard privacy boundary (see CLAUDE.md): only transcripts from
projects listed here are ever read. Widening it is a human decision, not a code
change to make casually.
"""

from pathlib import Path

PROJECTS_ROOT = Path.home() / ".claude" / "projects"

# Claude Code encodes a project's working directory into its folder name by
# replacing "/" with "-". Prefix match, so all MIT/SocialAI-Designs projects
# are covered by one entry. Decided 2026-07-06 (docs/v0.1-plan.md).
ALLOWED_PROJECT_PREFIXES = [
    "-Users-caitlinmorris-Documents-Translucency",
    "-Users-caitlinmorris-Documents-MIT-SocialAI-Designs",
]

SESSION_GAP_MINUTES = 30

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PRIVATE_DB = DATA_DIR / "private.db"
PUBLIC_DB = DATA_DIR / "public.db"


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
