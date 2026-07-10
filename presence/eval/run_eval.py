"""Phase 1/3 eval runner (docs/schema-v1-spec.md).

Usage:
    python -m presence.eval.run_eval             # labels vs extractor
    python -m presence.eval.run_eval baseline    # entropy over ALL observations
    python -m presence.eval.run_eval consistency [N]  # re-extract N segments
                                                 #   twice; self-agreement
                                                 #   (costs ~2N Haiku calls)
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

from presence.pipeline.config import PRIVATE_DB
from presence.pipeline.store import PrivateStore

LABELS_FILE = Path(__file__).parent / "labels" / "raw" / "labels.jsonl"
FIELDS = ("phase", "momentum", "stance", "openness")
CONF_BINS = ((0.0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.01))


# --- metrics (hand-rolled; these are learning-component adjacent) ---------------


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Agreement corrected for chance. pairs = (human, extractor)."""
    if len(pairs) < 2:
        return None
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ha, ea = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ha[v] / n) * (ea[v] / n) for v in set(ha) | set(ea))
    if pe == 1.0:
        return None  # degenerate: everyone always says the same thing
    return (po - pe) / (1 - pe)


def entropy(values: list[str]) -> float:
    n = len(values)
    if not n:
        return 0.0
    return -sum(
        (c / n) * math.log2(c / n) for c in Counter(values).values()
    )


# --- labels vs extractor ------------------------------------------------------------


def eval_labels() -> None:
    rows = [
        json.loads(l) for l in LABELS_FILE.read_text().splitlines() if l
    ] if LABELS_FILE.is_file() else []
    rows = [r for r in rows if not r.get("skipped")]
    if not rows:
        print("no labels yet — run the label tool first")
        return

    print(f"labeled segments: {len(rows)}\n")
    print(f"{'field':<10} {'n':>3} {'agree':>6} {'kappa':>6} "
          f"{'you=unk':>8} {'ext=unk':>8}  top confusion")
    for field in FIELDS:
        pairs = [
            (r["labels"][field], r["extractor"][field])
            for r in rows if r["labels"].get(field) is not None
        ]
        if not pairs:
            print(f"{field:<10}   0      —      —        —        —")
            continue
        agree = sum(1 for a, b in pairs if a == b) / len(pairs)
        kappa = cohen_kappa(pairs)
        you_unk = sum(1 for a, _ in pairs if a == "unknown") / len(pairs)
        ext_unk = sum(1 for _, b in pairs if b == "unknown") / len(pairs)
        confusions = Counter((a, b) for a, b in pairs if a != b)
        top = (f"{confusions.most_common(1)[0][0][0]}->"
               f"{confusions.most_common(1)[0][0][1]}"
               f" x{confusions.most_common(1)[0][1]}") if confusions else "—"
        kappa_s = f"{kappa:.2f}" if kappa is not None else "degen"
        print(f"{field:<10} {len(pairs):>3} {agree:>6.0%} {kappa_s:>6} "
              f"{you_unk:>8.0%} {ext_unk:>8.0%}  {top}")

    print("\ncalibration (extractor confidence -> was it right):")
    for field in FIELDS:
        parts = []
        for lo, hi in CONF_BINS:
            binned = [
                r for r in rows
                if r["labels"].get(field) is not None
                and lo <= float(r.get("extractor_confidence", {}).get(field, 0)) < hi
            ]
            if binned:
                acc = sum(
                    1 for r in binned if r["labels"][field] == r["extractor"][field]
                ) / len(binned)
                parts.append(f"[{lo:.2f}-{min(hi, 1):.2f}) {acc:.0%} (n={len(binned)})")
        print(f"  {field:<10} " + ("  ".join(parts) if parts else "—"))

    flags = sum(1 for r in rows if r.get("overshares"))
    gist_bad = sum(1 for r in rows if not r.get("gist_ok", True))
    shaped = Counter(f for r in rows for f in r.get("wrong_shaped", []))
    print(f"\ndiscretion flags: {flags}/{len(rows)} · gist not colleague-ok: "
          f"{gist_bad}/{len(rows)}")
    if shaped:
        print("wrong-shaped complaints:", dict(shaped))


# --- baseline: distributions over everything ---------------------------------------


def baseline() -> None:
    store = PrivateStore(PRIVATE_DB)
    obs = store.all_observations()
    store.close()
    print(f"observations: {len(obs)}\n")
    print(f"{'field':<10} {'entropy':>7} {'unknown':>8}  distribution")
    for field in FIELDS:
        values = [getattr(o, field).value for o in obs]
        unk = values.count("unknown") / len(values) if values else 0
        dist = ", ".join(
            f"{v}:{c}" for v, c in Counter(values).most_common()
        )
        print(f"{field:<10} {entropy(values):>7.2f} {unk:>8.0%}  {dist}")
    print("\n(entropy near 0 = the field is a constant, not a signal;"
          "\n max for a 6-value field is ~2.6)")


# --- self-consistency probe ---------------------------------------------------------


def consistency(n: int) -> None:
    from presence.extract.extractor import Extractor
    from presence.pipeline.sample_extract import find_segment

    store = PrivateStore(PRIVATE_DB)
    obs = [o for o in store.all_observations()
           if (o.t_end - o.t_start).total_seconds() >= 600][-n:]
    store.close()
    extractor = Extractor()
    print(f"re-extracting {len(obs)} segments twice each "
          f"(~{2 * len(obs)} Haiku calls)…")
    matches: dict[str, list[bool]] = {f: [] for f in FIELDS}
    for o in obs:
        seg = find_segment(o.person_id, o.t_start.isoformat(), o.t_end.isoformat(),
                           min_minutes=10)
        if seg is None:
            continue
        a = extractor.extract_segment(seg, person_id="probe")
        b = extractor.extract_segment(seg, person_id="probe")
        for f in FIELDS:
            matches[f].append(getattr(a, f) == getattr(b, f))
    print(f"\n{'field':<10} self-agreement")
    for f in FIELDS:
        m = matches[f]
        print(f"{f:<10} {sum(m) / len(m):>6.0%} (n={len(m)})" if m else f"{f:<10}      —")
    print("\n(a field that disagrees with itself can't agree with you)")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "labels"
    if cmd == "baseline":
        baseline()
    elif cmd == "consistency":
        consistency(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    else:
        eval_labels()


if __name__ == "__main__":
    main()
