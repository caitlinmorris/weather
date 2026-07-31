#!/usr/bin/env bash
# we.ather participant installer (macOS). Interactive; ~5 minutes.
# Safe to rerun — it never overwrites an existing .env without asking.
set -euo pipefail
cd "$(dirname "$0")"

echo "— we.ather setup —"
echo

# 1. Python 3.12+
PY=""
for candidate in python3.13 python3.12 /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
  echo "Python 3.12+ not found. Install with:  brew install python@3.13"
  exit 1
fi
echo "using $($PY --version)"

# 2. venv + deps
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
.venv/bin/pip install -q -r requirements.txt
echo "dependencies installed"

# 3. .env
if [ -f .env ] && grep -q '^PRESENCE_ALLOWLIST=..*\|^PRESENCE_ALLOWLIST_WARP=..*' .env; then
  echo
  echo ".env already exists — keeping it. (Edit it by hand to change settings,"
  echo "then RESTART the we.ather app — settings are read at launch.)"
elif [ -f .env ]; then
  # A pre-configured kit: everything is set EXCEPT consent, which is
  # always the recipient's own choice, asked here.
  echo
  echo "Pre-configured kit detected. One question remains — yours alone:"
  echo "which project folders may we.ather observe? Only sessions in the"
  echo "folders you pick are ever read."
  SOURCES=$(grep '^PRESENCE_SOURCES=' .env | cut -d= -f2)
  SOURCES=${SOURCES:-claude_code}
  ALLOW=""
  if [[ "$SOURCES" == *claude_code* ]]; then
    PROJECTS_DIR="$HOME/.claude/projects"
    if [ ! -d "$PROJECTS_DIR" ]; then
      echo "No Claude Code projects found at $PROJECTS_DIR — run Claude Code once first."
      exit 1
    fi
    i=0; declare -a NAMES
    for d in "$PROJECTS_DIR"/*/; do
      name="$(basename "$d")"
      i=$((i+1)); NAMES[$i]="$name"
      echo "  [$i] $name"
    done
    read -r -p "numbers to include (space-separated, e.g. 1 3 4): " PICKS
    for n in $PICKS; do
      ALLOW="${ALLOW:+$ALLOW,}${NAMES[$n]}"
    done
    printf 'PRESENCE_ALLOWLIST=%s\n' "$ALLOW" >> .env
  fi
  if [[ "$SOURCES" == *warp* ]]; then
    read -r -p "Warp folders to observe (absolute paths, comma-separated): " WARP_ALLOW
    printf 'PRESENCE_ALLOWLIST_WARP=%s\n' "$WARP_ALLOW" >> .env
  fi
  if [[ "$SOURCES" == *codex* ]]; then
    read -r -p "Codex folders to observe (absolute paths, comma-separated): " CODEX_ALLOW
    printf 'PRESENCE_ALLOWLIST_CODEX=%s\n' "$CODEX_ALLOW" >> .env
  fi
  printf 'PRESENCE_START=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%S+00:00)" >> .env
  chmod 600 .env
  echo "consent recorded in .env"
else
  echo
  echo "Your short name identifies you in your rooms."
  echo "- Joining a board someone invited you to? It must EXACTLY match the"
  echo "  name your token was registered under (ask your host if unsure)."
  echo "- About to create your own board? Choose the name you'll register"
  echo "  for yourself in the next step."
  read -r -p "your short name (lowercase, e.g. dan): " PERSON

  echo
  echo "How should the small AI model that summarizes your work be billed?"
  echo "  1) my Anthropic API key (works for everyone; pennies per workday)"
  echo "  2) my Claude subscription — uses your existing Claude Code login"
  echo "     (needs Claude Code installed + a Pro/Max plan; no API key)"
  read -r -p "choice [1/2] (default 1): " BILLING
  BILLING=${BILLING:-1}
  APIKEY=""
  EXTRACTOR=""
  if [ "$BILLING" = "2" ]; then
    EXTRACTOR="claude_cli"
    command -v claude >/dev/null 2>&1 \
      || echo "note: no 'claude' CLI found on PATH — install Claude Code" \
              "before first run, or switch to an API key in settings later."
  else
    read -r -p "Anthropic API key (starts sk-ant-, from whoever sent you this): " APIKEY
  fi
  read -r -p "relay URL (https://..., or leave empty for local-only): " RELAYURL
  RELAYTOK=""
  BOARDNAME=""
  if [ -n "$RELAYURL" ]; then
    read -r -p "room (board) name, from your invite: " BOARDNAME
    read -r -p "your relay token (from your board's host): " RELAYTOK
  fi

  echo
  read -r -p "capture sources [claude_code / warp / codex — comma-separate] (default claude_code): " SOURCES
  SOURCES=${SOURCES:-claude_code}

  ALLOW=""
  if [[ "$SOURCES" == *claude_code* ]]; then
    echo
    echo "Which Claude Code projects may we.ather observe? (Consent layer (a) —"
    echo "only sessions in the folders you pick are ever read.)"
    PROJECTS_DIR="$HOME/.claude/projects"
    if [ ! -d "$PROJECTS_DIR" ]; then
      echo "No Claude Code projects found at $PROJECTS_DIR — run Claude Code once first."
      exit 1
    fi
    i=0; declare -a NAMES
    for d in "$PROJECTS_DIR"/*/; do
      name="$(basename "$d")"
      i=$((i+1)); NAMES[$i]="$name"
      echo "  [$i] $name"
    done
    read -r -p "numbers to include (space-separated, e.g. 1 3 4): " PICKS
    for n in $PICKS; do
      ALLOW="${ALLOW:+$ALLOW,}${NAMES[$n]}"
    done
  fi

  WARP_ALLOW=""
  if [[ "$SOURCES" == *warp* ]]; then
    echo
    echo "Which folders may we.ather observe in Warp? (Absolute paths,"
    echo "comma-separated — e.g. /Users/you/code/mapsproj,/Users/you/thesis)"
    read -r -p "warp folders: " WARP_ALLOW
  fi

  CODEX_ALLOW=""
  if [[ "$SOURCES" == *codex* ]]; then
    echo
    echo "Which folders may we.ather observe in Codex? (Absolute paths,"
    echo "comma-separated — sessions started outside them are never read)"
    read -r -p "codex folders: " CODEX_ALLOW
  fi

  cat > .env <<EOF
ANTHROPIC_API_KEY=$APIKEY
PRESENCE_PERSON_ID=$PERSON
PRESENCE_GROUP_MODE=person
PRESENCE_SOURCES=$SOURCES
PRESENCE_ALLOWLIST=$ALLOW
PRESENCE_ALLOWLIST_WARP=$WARP_ALLOW
PRESENCE_ALLOWLIST_CODEX=$CODEX_ALLOW
PRESENCE_START=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
EOF
  if [ -n "$BOARDNAME" ]; then
    # Canonical per-board form (PRESENCE_BOARDS roster + suffixed keys) —
    # same dialect the board script and invites speak.
    KEY=$(echo "$BOARDNAME" | tr 'a-z-' 'A-Z_')
    {
      printf 'PRESENCE_BOARDS=%s\n' "$BOARDNAME"
      printf 'RELAY_URL_%s=%s\n' "$KEY" "$RELAYURL"
      printf 'RELAY_TOKEN_%s=%s\n' "$KEY" "$RELAYTOK"
      printf 'PRESENCE_TIER_%s=topic\n' "$KEY"
    } >> .env
  fi
  if [ -n "$EXTRACTOR" ]; then
    printf 'PRESENCE_EXTRACTOR=%s\n' "$EXTRACTOR" >> .env
  fi
  chmod 600 .env
  echo ".env written (permissions 600)"
fi

# 4. self-test
echo
.venv/bin/python -m presence.pipeline.selftest

echo
echo "Done. Daily driver:   ./weather"
echo "Step away anytime:    ./weather pause"
echo "What leaves your machine: docs/security-model.md (one page, read it)"
echo
echo "Hosting your own board? That's the next step:"
echo "  ./presence/relay/make_board_cf.sh <board-name> <you> [friends...]"
echo "  (just yourself is fine — invite people later from the settings gear;"
echo "   full guide: docs/self-hosting.md)"
