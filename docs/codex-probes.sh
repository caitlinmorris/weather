#!/usr/bin/env bash
# we.ather — Codex structure probe. Prints STRUCTURE only: event types,
# key names, one timestamp's format, and where the working-directory key
# lives. No prompt content, no counts, no date ranges, no paths' values —
# we ask only what parsing strictly requires.
# Run:  bash codex-probes.sh   and send back everything it prints.
set -euo pipefail

python3 - <<'PY'
import json
from pathlib import Path

root = Path.home() / ".codex" / "sessions"
files = sorted(root.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime)
if not files:
    print(f"no rollout files under {root}")
    raise SystemExit(0)
newest = files[-1]
print(f"newest rollout file name pattern: {newest.name[:8]}…jsonl")

def shape(x, depth=0):
    if depth > 2:
        return "..."
    if isinstance(x, dict):
        return {k: shape(v, depth + 1) for k, v in x.items()}
    if isinstance(x, list):
        return [shape(x[0], depth + 1), f"...x{len(x)}"] if x else []
    return type(x).__name__

seen_types = {}
ts_sample = None
cwd_key_path = None

def find_key(obj, needles, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if any(n in k.lower() for n in needles):
                return p
            hit = find_key(v, needles, p)
            if hit:
                return hit
    return None

with open(newest) as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = obj.get("type") or obj.get("record_type") or "?" + "/".join(sorted(obj)[:3])
        if t not in seen_types:
            seen_types[t] = shape(obj)
        if ts_sample is None:
            hit = find_key(obj, ("timestamp", "_ts", "time"))
            if hit:
                val = obj
                for part in hit.split("."):
                    val = val[part]
                if isinstance(val, (str, int, float)):
                    ts_sample = (hit, val)
        if cwd_key_path is None:
            cwd_key_path = find_key(obj, ("cwd", "working_dir", "workdir"))

print(f"\ndistinct line types in this session: {sorted(seen_types)}")
for t, s in seen_types.items():
    print(f"\n== shape of first '{t}' line (key names only) ==")
    print(json.dumps(s, indent=1))
print(f"\ntimestamp sample (format only): {ts_sample}")
print(f"working-directory key found at: {cwd_key_path or 'NOT FOUND in this file'}")
PY
