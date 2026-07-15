#!/usr/bin/env bash
# we.ather — Warp structure probes (round 2, after the schema dump).
# Prints STRUCTURE only: JSON key names, one timestamp's format, the
# status vocabulary. No conversation content, no counts, no date ranges,
# no model names — we ask only what parsing strictly requires.
# Run:  bash warp-probes.sh   and send back everything it prints.
set -euo pipefail

DB="$HOME/Library/Group Containers/2BBY89MBSN.dev.warp/Library/Application Support/dev.warp.Warp-Stable/warp.sqlite"

echo "== probe 1: shape of conversation_data (JSON key names only) =="
sqlite3 -readonly "$DB" \
  "SELECT conversation_data FROM agent_conversations
   ORDER BY last_modified_at DESC LIMIT 1;" | python3 -c "
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception as e:
    print('not JSON:', type(e).__name__, '- first bytes look like:', repr(raw[:20]))
    sys.exit(0)
def probe(x, depth=0):
    if depth > 3: return '...'
    if isinstance(x, dict): return {k: probe(v, depth + 1) for k, v in x.items()}
    if isinstance(x, list):
        return [probe(x[0], depth + 1), f'...x{len(x)}'] if x else []
    return type(x).__name__
print(json.dumps(probe(d), indent=1))"

echo
echo "== probe 2: timestamp format + status vocabulary =="
sqlite3 -readonly "$DB" \
  "SELECT start_ts, output_status FROM ai_queries LIMIT 3;
   SELECT DISTINCT output_status FROM ai_queries;"
