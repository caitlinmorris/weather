#!/usr/bin/env bash
# Create a we.ather board on YOUR OWN Cloudflare account — free tier, no
# credit card, nothing routed through anyone else. The self-hosted twin of
# make_board.sh (Fly). Full guide: docs/self-hosting.md
#
# Prereqs: node (for npx), a free Cloudflare account (wrangler will open a
# browser to log in on first use).
#
# Usage: ./presence/relay/make_board_cf.sh <board-name> <member1> <member2> [...]
# e.g.:  ./presence/relay/make_board_cf.sh studio matt jo
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ $# -lt 3 ]; then
  echo "usage: $0 <board-name> <member1> <member2> [...]"; exit 1
fi
BOARD="$1"; shift
WORKDIR="presence/relay/worker"
CONFIG="$WORKDIR/wrangler.$BOARD.toml"

sed "s/BOARDNAME/$BOARD/" "$WORKDIR/wrangler.toml" > "$CONFIG"

# Mint one token per member; hashes to the relay secret, tokens to humans.
SECRETS="{"
for MEMBER in "$@"; do
  echo
  OUT=$(.venv/bin/python -m presence.relay.mktoken "$MEMBER")
  echo "$OUT"
  HASH=$(echo "$OUT" | grep 'HASH' | sed 's/.*"\([a-f0-9]*\)"$/\1/')
  SECRETS="$SECRETS\"$MEMBER\": \"$HASH\", "
done
SECRETS="${SECRETS%, }}"

echo
echo "— deploying board '$BOARD' to your Cloudflare account —"
npx wrangler@latest deploy --config "$CONFIG"
echo "$SECRETS" | npx wrangler@latest secret put RELAY_TOKENS --config "$CONFIG"

KEY=$(echo "$BOARD" | tr 'a-z-' 'A-Z_')
echo
echo "board '$BOARD' is live at the workers.dev URL printed above."
echo "each member's .env needs (with THEIR token from above):"
echo "  PRESENCE_BOARDS=...existing...,$BOARD"
echo "  RELAY_URL_$KEY=https://we-ather-$BOARD.<your-subdomain>.workers.dev"
echo "  RELAY_TOKEN_$KEY=<their token>"
echo "  PRESENCE_TIER_$KEY=topic"
echo "then RESTART their app, and verify with:"
echo "  .venv/bin/python -m presence.pipeline.selftest"
