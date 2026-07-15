"""Structural privacy checks: cheap greps that make the boundary contract
(docs/person-model-spec-v0.md) mechanically auditable."""

from pathlib import Path

PRESENCE = Path(__file__).resolve().parents[1] / "presence"

# Only rollup may open the public store for writing.
PUBLISH_ALLOWED = {PRESENCE / "core" / "rollup.py"}


def test_only_rollup_opens_public_store_as_writer():
    violations = []
    for py in PRESENCE.rglob("*.py"):
        if py in PUBLISH_ALLOWED or py.name == "store.py":
            continue
        if "writer=True" in py.read_text():
            violations.append(str(py))
    assert not violations, f"public-store write access outside rollup: {violations}"


def test_only_pipeline_reads_raw_transcripts():
    # Raw-content entry points (transcript parsing, source databases) live in
    # the pipeline subtree only; core/ and render/ consume TranscriptEvent/
    # Segment objects handed to them, never open files or databases.
    violations = []
    for py in PRESENCE.rglob("*.py"):
        if "pipeline" in py.parts:
            continue
        text = py.read_text()
        if ("parse_transcript" in text or ".claude/projects" in text
                or "warp.sqlite" in text):
            violations.append(str(py))
    assert not violations, f"raw capture access outside pipeline: {violations}"
