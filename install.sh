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
if [ -f .env ]; then
  echo
  echo ".env already exists — keeping it. (Edit it by hand to change settings.)"
else
  echo
  read -r -p "your short name (lowercase, e.g. dan): " PERSON
  read -r -p "Anthropic API key (starts sk-ant-, from the study owner): " APIKEY
  read -r -p "relay URL (https://..., or leave empty for local-only): " RELAYURL
  RELAYTOK=""
  if [ -n "$RELAYURL" ]; then
    read -r -p "your relay token (from the study owner): " RELAYTOK
  fi

  echo
  echo "Which projects may we.ather observe? (This is consent layer (a) —"
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
  ALLOW=""
  for n in $PICKS; do
    ALLOW="${ALLOW:+$ALLOW,}${NAMES[$n]}"
  done

  cat > .env <<EOF
ANTHROPIC_API_KEY=$APIKEY
PRESENCE_PERSON_ID=$PERSON
PRESENCE_GROUP_MODE=person
PRESENCE_ALLOWLIST=$ALLOW
RELAY_URL=$RELAYURL
RELAY_TOKEN=$RELAYTOK
EOF
  chmod 600 .env
  echo ".env written (permissions 600)"
fi

# 4. self-test
echo
.venv/bin/python -m presence.pipeline.selftest

echo
echo "Done. Daily driver:   .venv/bin/python -m presence.render.app"
echo "Step away anytime:    .venv/bin/python -m presence.pipeline.pause"
echo "What leaves your machine: docs/security-model.md (one page, read it)"
