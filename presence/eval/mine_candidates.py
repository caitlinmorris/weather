"""Phase 3 candidate mining (docs/schema-v1-spec.md): what dimensions vary
in the observed work that the schema doesn't capture? PROPOSALS ONLY —
admission happens in the Phase 4 redesign session, by a human, against the
five criteria.

Reads gists/trajectory/evidence (T0) from the local private db; output goes
to eval/labels/raw/ (gitignored — it quotes evidence strings).

Usage: python -m presence.eval.mine_candidates
"""

from __future__ import annotations

import json
from pathlib import Path

from presence.extract.extractor import load_api_key
from presence.pipeline.config import PRIVATE_DB
from presence.pipeline.store import PrivateStore

MODEL = "claude-haiku-4-5-20251001"
BATCH = 30
OUT = Path(__file__).parent / "labels" / "raw" / "candidates.md"

SCHEMA_NOTE = (
    "The current schema captures: topic (tags + gist), phase (exploring/"
    "shaping/building/debugging/polishing/writing), momentum (flowing/"
    "steady/grinding/stuck), stance (learning/mixed/exercising_expertise)."
)


def _parse_array(raw: str) -> list:
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        parsed = json.loads(raw[start:end + 1])
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def main() -> None:
    import anthropic

    store = PrivateStore(PRIVATE_DB)
    observations = store.all_observations()
    store.close()

    corpus = []
    for o in observations:
        bits = [f"gist: {o.topic.gist}"]
        if o.trajectory_note:
            bits.append(f"trajectory: {o.trajectory_note}")
        bits += [f"{k}-evidence: {v}" for k, v in o.evidence.items()]
        corpus.append(" | ".join(bits))
    print(f"mining {len(corpus)} observations…")

    client = anthropic.Anthropic(api_key=load_api_key())

    def ask(prompt: str) -> str:
        r = client.messages.create(model=MODEL, max_tokens=2000,
                                   messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if b.type == "text")

    proposals = []
    for i in range(0, len(corpus), BATCH):
        batch = corpus[i:i + BATCH]
        listing = "\n".join(f"{n+1}. {row}" for n, row in enumerate(batch))
        raw = ask(
            f"Below are {len(batch)} descriptions of one person's AI-assisted "
            f"work sessions. {SCHEMA_NOTE}\n\nQuestion: what dimensions VARY "
            "across these descriptions that the schema does NOT capture? Only "
            "dimensions with real variation in THIS data — no speculation. "
            "Return a JSON array only: [{\"dimension\": short-name, "
            "\"description\": one sentence, \"example_phrases\": [2-3 short "
            "quotes from the data], \"possible_values\": [3-5 enum values]}]"
            f"\n\n{listing}"
        )
        proposals += _parse_array(raw)

    merged_raw = ask(
        "Merge these candidate schema dimensions: combine duplicates/near-"
        "duplicates, rank by how much distinct supporting evidence each has, "
        "keep at most 8. Same JSON shape, plus \"support\": int (count of "
        "distinct supporting examples).\n\n" + json.dumps(proposals)
    )
    merged = _parse_array(merged_raw)

    lines = ["# Candidate dimensions (mined — proposals only)\n"]
    for c in merged:
        lines.append(f"## {c.get('dimension')}  (support: {c.get('support', '?')})")
        lines.append(c.get("description", ""))
        lines.append("values: " + ", ".join(c.get("possible_values", [])))
        for q in c.get("example_phrases", []):
            lines.append(f"  > {q}")
        lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nsaved to {OUT}")


if __name__ == "__main__":
    main()
