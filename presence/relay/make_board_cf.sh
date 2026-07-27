#!/usr/bin/env bash
# Create a we.ather board on YOUR OWN Cloudflare account — free tier, no
# credit card, nothing routed through anyone else. The self-hosted twin of
# make_board.sh (Fly). Full guide: docs/self-hosting.md
#
# Prereqs: node (for npx), a free Cloudflare account (wrangler will open a
# browser to log in on first use).
#
# Usage: ./presence/relay/make_board_cf.sh <board-name> <member1> [member2 ...]
# e.g.:  ./presence/relay/make_board_cf.sh studio matt jo
# A board with just yourself is fine — try the weather solo, then invite
# people later from the settings gear (or presence.relay.invite).
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ $# -lt 2 ]; then
  echo "usage: $0 <board-name> <member1> [member2 ...]   (solo is fine)"; exit 1
fi
BOARD="$1"; shift
WORKDIR="presence/relay/worker"
CONFIG="$WORKDIR/wrangler.$BOARD.toml"

sed "s/BOARDNAME/$BOARD/" "$WORKDIR/wrangler.toml" > "$CONFIG"

# Mint one token per member; hashes to the relay secret, tokens to humans.
# Hashes (never tokens) also persist to a local file, so an interrupted run
# can finish the secret upload without re-minting everyone's tokens.
HASHFILE="$WORKDIR/hashes.$BOARD.json"
SECRETS="{"
for MEMBER in "$@"; do
  echo
  OUT=$(.venv/bin/python -m presence.relay.mktoken "$MEMBER")
  echo "$OUT"
  HASH=$(echo "$OUT" | grep 'HASH' | sed 's/.*"\([a-f0-9]*\)"$/\1/')
  SECRETS="$SECRETS\"$MEMBER\": \"$HASH\", "
done
SECRETS="${SECRETS%, }}"
echo "$SECRETS" > "$HASHFILE"
chmod 600 "$HASHFILE"

echo
echo "— deploying board '$BOARD' to your Cloudflare account —"
# tee keeps wrangler's output (and any first-run subdomain prompt) visible
# while we capture the deployed URL for the .env lines below.
if ! DEPLOY_OUT=$(npx wrangler@latest deploy --config "$CONFIG" 2>&1 | tee /dev/stderr); then
  echo
  echo "DEPLOY FAILED (often: first deploy needs a workers.dev subdomain"
  echo "registered — wrangler prompts for it). Your tokens above are still"
  echo "good. To finish WITHOUT re-running this script (which would re-mint"
  echo "them), run these two commands once deploy succeeds:"
  echo "  npx wrangler@latest deploy --config $CONFIG"
  echo "  npx wrangler@latest secret put RELAY_TOKENS --config $CONFIG < $HASHFILE"
  exit 1
fi
URL=$(echo "$DEPLOY_OUT" | grep -o 'https://[a-zA-Z0-9.-]*\.workers\.dev' | head -1)
npx wrangler@latest secret put RELAY_TOKENS --config "$CONFIG" < "$HASHFILE"

if [ -z "$URL" ]; then
  echo
  echo "WARNING: couldn't find a workers.dev URL in wrangler's output above."
  echo "Re-run the deploy to see it (safe, keeps your tokens):"
  echo "  npx wrangler@latest deploy --config $CONFIG"
  URL="https://we-ather-$BOARD.<your-subdomain>.workers.dev"
fi

KEY=$(echo "$BOARD" | tr 'a-z-' 'A-Z_')
echo
echo "board '$BOARD' is live at: $URL"
echo "each member's .env needs (with THEIR token from above):"
echo "  PRESENCE_BOARDS=...existing...,$BOARD"
echo "  RELAY_URL_$KEY=$URL"
echo "  RELAY_TOKEN_$KEY=<their token>"
echo "  PRESENCE_TIER_$KEY=topic"
echo "then RESTART their app, and verify with:"
echo "  .venv/bin/python -m presence.pipeline.selftest"
