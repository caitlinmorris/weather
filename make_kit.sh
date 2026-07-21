#!/usr/bin/env bash
# Build a personalized we.ather kit: a zip with everything pre-configured
# except the recipient's consent choices. Provider mode: the API key you
# bake in is one YOU minted for them (Console -> their own spend-capped
# workspace) — billing is yours, but their extraction traffic goes DIRECT
# to Anthropic, never through you. See docs/self-hosting.md.
#
# Usage: ./make_kit.sh <person> [board-name]
#   - prompts for their API key (minted by you) and, if board-name given,
#     their relay URL + token (from make_board / make_board_cf output).
# Output: dist/we.ather-<person>.zip
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 1 ]; then echo "usage: $0 <person> [board-name]"; exit 1; fi
PERSON="$1"; BOARD="${2:-}"

read -r -s -p "API key you minted for $PERSON (input hidden): " APIKEY; echo
RELAYURL=""; RELAYTOK=""
if [ -n "$BOARD" ]; then
  read -r -p "relay URL for board '$BOARD': " RELAYURL
  read -r -s -p "$PERSON's relay token (input hidden): " RELAYTOK; echo
fi

STAGE=$(mktemp -d)
git archive HEAD | tar -x -C "$STAGE"

{
  echo "ANTHROPIC_API_KEY=$APIKEY"
  echo "PRESENCE_PERSON_ID=$PERSON"
  echo "PRESENCE_GROUP_MODE=person"
  echo "PRESENCE_SOURCES=claude_code"
  echo "# PRESENCE_ALLOWLIST is deliberately absent: the installer asks YOU"
  echo "# which project folders may be observed. That choice is never made"
  echo "# for you."
  if [ -n "$BOARD" ]; then
    KEY=$(echo "$BOARD" | tr 'a-z-' 'A-Z_')
    echo "PRESENCE_BOARDS=$BOARD"
    echo "RELAY_URL_$KEY=$RELAYURL"
    echo "RELAY_TOKEN_$KEY=$RELAYTOK"
    echo "PRESENCE_TIER_$KEY=topic"
  fi
} > "$STAGE/.env"
chmod 600 "$STAGE/.env"

mkdir -p dist
OUT="dist/we.ather-$PERSON.zip"
rm -f "$OUT"
(cd "$STAGE" && zip -qr - .) > "$OUT"
rm -rf "$STAGE"

echo "built $OUT"
echo
echo "send it privately (it contains their API key + relay token)."
echo "their instructions, complete:"
echo "  unzip we.ather-$PERSON.zip -d weather && cd weather"
echo "  ./install.sh          # asks ONE thing: which folders to observe"
echo "  .venv/bin/python -m presence.render.app"
