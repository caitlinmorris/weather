"""Phase 1 labeling tool (docs/schema-v1-spec.md).

Blind-label your own segments, then see the extractor's answer. Collects
per-field labels plus the two annotations v0.1 never had: a DISCRETION flag
(gist/evidence over-shares) and a WRONG-SHAPED complaint (`!` — "no right
answer exists for this field here").

Usage:
    python -m presence.eval.label_tool sample [N]   # pick stratified sample (~35)
    python -m presence.eval.label_tool              # label next unlabeled
    python -m presence.eval.label_tool status

Labels live in presence/eval/labels/raw/ (gitignored — notes may quote
content). Answer keys: number = value · u = unknown · ! = wrong-shaped ·
s = skip field · q = quit (progress saved).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from presence.core.schema import Momentum, Openness, Phase, Stance
from presence.extract.extractor import _middle_truncate
from presence.pipeline.config import PERSON_ID, PRIVATE_DB
from presence.pipeline.sample_extract import find_segment
from presence.pipeline.store import PrivateStore

LABELS_DIR = Path(__file__).parent / "labels" / "raw"
SAMPLE_FILE = LABELS_DIR / "sample.jsonl"
LABELS_FILE = LABELS_DIR / "labels.jsonl"
DISPLAY_LINE_CAP = 150

FIELDS = {
    "phase": Phase,
    "momentum": Momentum,
    "stance": Stance,
    "openness": Openness,
}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _append_jsonl(path: Path, row: dict) -> None:
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(row) + "\n")


# --- sampling --------------------------------------------------------------------


def sample(n: int) -> None:
    store = PrivateStore(PRIVATE_DB)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    candidates = [
        o for o in store.all_observations()
        if o.person_id == PERSON_ID
        and (o.t_end - o.t_start) >= timedelta(minutes=10)
        and o.t_end < cutoff  # still-growing segments make unstable samples
    ]
    store.close()
    if not candidates:
        print("no eligible observations (>=10 min, older than 24h)")
        return

    # Stratify by (month, extractor phase): round-robin across buckets so the
    # sample covers time and the extractor's own claimed variety.
    buckets: dict[tuple, list] = {}
    for o in candidates:
        buckets.setdefault((o.t_start.strftime("%Y-%m"), o.phase.value), []).append(o)
    for b in buckets.values():
        b.sort(key=lambda o: o.t_start)

    picked, keys = [], sorted(buckets)
    while len(picked) < min(n, len(candidates)):
        progressed = False
        for k in keys:
            if buckets[k]:
                picked.append(buckets[k].pop(0))
                progressed = True
                if len(picked) >= n:
                    break
        if not progressed:
            break

    SAMPLE_FILE.unlink(missing_ok=True)
    for o in picked:
        _append_jsonl(SAMPLE_FILE, json.loads(o.model_dump_json()))
    summary = {}
    for o in picked:
        summary[o.phase.value] = summary.get(o.phase.value, 0) + 1
    print(f"sampled {len(picked)} observations -> {SAMPLE_FILE}")
    print("by extractor phase:", dict(sorted(summary.items())))


# --- labeling ---------------------------------------------------------------------


def _labeling_lines(events) -> list[str]:
    """The HUMAN's view of a segment — unlike the extractor's diet, this
    keeps only the conversation: your prompts, and assistant text that is
    human-facing (substantial prose, or a question to you). Tool churn
    collapses into count markers so the CADENCE stays visible (that's
    momentum evidence) without the noise."""
    lines: list[str] = []
    omitted = 0

    def flush() -> None:
        nonlocal omitted
        if omitted:
            lines.append(f"        ⋯ {omitted} assistant/tool steps ⋯")
            omitted = 0

    for e in events:
        stamp = f"[{e.timestamp:%H:%M}]" if e.timestamp else "[--:--]"
        if e.is_human_prompt:
            flush()
            lines.append("")
            lines.append(f"{stamp} YOU: {_middle_truncate(e.text, 2000)}")
        elif (e.type == "assistant" and e.text
              and (len(e.text) >= 200 or "?" in e.text[-300:])):
            flush()
            lines.append(f"{stamp} ASSISTANT: {_middle_truncate(e.text, 1200)}")
        elif not e.is_meta and not e.is_sidechain and e.type in ("user", "assistant"):
            omitted += 1
    flush()
    return lines


def _show_segment(obs: dict) -> bool:
    seg = find_segment(obs["person_id"], obs["t_start"], obs["t_end"])
    if seg is None:
        print("  (segment no longer matches on disk — skipping)")
        return False
    lines = _labeling_lines(seg.events)
    if len(lines) > DISPLAY_LINE_CAP:
        half = DISPLAY_LINE_CAP // 2
        lines = lines[:half] + [f"  …[{len(lines) - DISPLAY_LINE_CAP} lines omitted]…"] + lines[-half:]
    print("\n".join(lines))
    return True


def _ask_enum(field: str, enum_cls) -> dict:
    values = [v.value for v in enum_cls if v.value != "unknown"]
    options = "  ".join(f"{i + 1}={v}" for i, v in enumerate(values))
    while True:
        raw = input(f"  {field:<10} [{options}  u=unknown  !=wrong-shaped  s=skip] > ").strip().lower()
        if raw == "q":
            raise KeyboardInterrupt
        if raw == "s":
            return {"label": None}
        if raw == "u":
            return {"label": "unknown"}
        if raw == "!":
            return {"label": None, "wrong_shaped": True}
        if raw.isdigit() and 1 <= int(raw) <= len(values):
            return {"label": values[int(raw) - 1]}
        print("    ?")


def _ask_yn(prompt: str) -> bool:
    return input(f"  {prompt} [y/N] > ").strip().lower() == "y"


def label_next() -> None:
    samples = _load_jsonl(SAMPLE_FILE)
    done = {r["observation_id"] for r in _load_jsonl(LABELS_FILE)}
    todo = [s for s in samples if s["observation_id"] not in done]
    if not samples:
        print("no sample yet — run: python -m presence.eval.label_tool sample")
        return
    if not todo:
        print(f"all {len(samples)} labeled — run run_eval for the numbers")
        return

    print(f"{len(done)}/{len(samples)} labeled · q at any prompt saves and quits\n")
    try:
        for obs in todo:
            print("=" * 72)
            print(f"segment {obs['t_start'][:16]} -> {obs['t_end'][:16]}")
            print("=" * 72)
            if not _show_segment(obs):
                _append_jsonl(LABELS_FILE, {
                    "observation_id": obs["observation_id"], "skipped": True,
                })
                continue

            print("\nYour labels (blind — extractor's answer comes after):")
            row = {
                "observation_id": obs["observation_id"],
                "labels": {}, "wrong_shaped": [],
                "extractor": {f: obs[f] for f in FIELDS},
                "extractor_confidence": obs.get("confidence", {}),
                "gist": obs["topic"]["gist"],
                "labeled_at": datetime.now(timezone.utc).isoformat(),
            }
            for field, enum_cls in FIELDS.items():
                answer = _ask_enum(field, enum_cls)
                if answer.get("wrong_shaped"):
                    row["wrong_shaped"].append(field)
                row["labels"][field] = answer.get("label")

            print("\n  extractor said: " + "  ".join(
                f"{f}={obs[f]}" for f in FIELDS))
            print(f"  gist: \"{obs['topic']['gist']}\"")
            row["gist_ok"] = _ask_yn("gist colleague-appropriate?")
            row["overshares"] = _ask_yn("anything over-shared (gist/evidence)? [discretion flag]")
            note = input("  note (enter to skip) > ").strip()
            if note:
                row["note"] = note
            _append_jsonl(LABELS_FILE, row)
            print()
    except (KeyboardInterrupt, EOFError):
        print("\nprogress saved")


def status() -> None:
    samples, labels = _load_jsonl(SAMPLE_FILE), _load_jsonl(LABELS_FILE)
    real = [r for r in labels if not r.get("skipped")]
    print(f"sample: {len(samples)} · labeled: {len(real)} · skipped: {len(labels) - len(real)}")
    flags = sum(1 for r in real if r.get("overshares"))
    shaped = sum(len(r.get("wrong_shaped", [])) for r in real)
    print(f"discretion flags: {flags} · wrong-shaped complaints: {shaped}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "label"
    if cmd == "sample":
        sample(int(sys.argv[2]) if len(sys.argv) > 2 else 35)
    elif cmd == "status":
        status()
    else:
        label_next()


if __name__ == "__main__":
    main()
