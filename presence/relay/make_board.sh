#!/usr/bin/env bash
# Create a new we.ather board: its own relay app on the host's Fly account.
# (Boards are hosted by a member of the room — operator disclosure belongs
# in the room's consent conversation. See docs/social-topology.md.)
#
# Usage: ./presence/relay/make_board.sh <board-name> <member1> <member2> [...]
# e.g.:  ./presence/relay/make_board.sh vee caitlin vee
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ $# -lt 3 ]; then
  echo "usage: $0 <board-name> <member1> <member2> [...]"; exit 1
fi
BOARD="$1"; shift
APP="we-ather-$BOARD"

echo "— creating board '$BOARD' as app $APP —"
fly apps create "$APP"

# Per-board fly config (fly.toml pins the first board's app name).
sed "s/^app = .*/app = '$APP'/" fly.toml > "fly.$BOARD.toml"

# Mint one token per member; hashes go to the relay, tokens to the humans.
SECRETS="{"
for MEMBER in "$@"; do
  echo
  OUT=$(.venv/bin/python -m presence.relay.mktoken "$MEMBER")
  echo "$OUT"
  HASH=$(echo "$OUT" | grep 'HASH' | sed 's/.*"\([a-f0-9]*\)"$/\1/')
  SECRETS="$SECRETS\"$MEMBER\": \"$HASH\", "
done
SECRETS="${SECRETS%, }}"

fly secrets set -a "$APP" "RELAY_TOKENS=$SECRETS" --stage
fly deploy -c "fly.$BOARD.toml"

echo
echo "board '$BOARD' live at https://$APP.fly.dev"
echo "IMPORTANT: run 'fly scale count 1 -a $APP -y' if machines > 1"
echo
echo "each member's .env needs (with THEIR token from above):"
echo "  PRESENCE_BOARDS=...existing...,$BOARD"
echo "  RELAY_URL_$(echo "$BOARD" | tr 'a-z-' 'A-Z_')=https://$APP.fly.dev"
echo "  RELAY_TOKEN_$(echo "$BOARD" | tr 'a-z-' 'A-Z_')=<their token>"
echo "  PRESENCE_TIER_$(echo "$BOARD" | tr 'a-z-' 'A-Z_')=topic"
echo "then RESTART their app."
