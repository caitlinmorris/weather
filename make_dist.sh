#!/usr/bin/env bash
# Build the minimal shareable package: everything needed to install, start
# a board, and invite people — nothing else. Rebuilt from tracked files
# (git archive), so it can never leak .env, data/, or untracked drafts.
#
# Output: dist/we.ather/ and dist/we.ather.zip
# Usage:  ./make_dist.sh
set -euo pipefail
cd "$(dirname "$0")"

OUT="dist/we.ather"

# Refuse to clobber in-place edits (it happened once — 2026-07-27, doc
# edits made inside dist/ were lost to a rebuild). Compare the editable
# files against HEAD; README.md is generated, so it's exempt.
if [ -d "$OUT" ] && [ "${FORCE:-}" != "1" ]; then
  while IFS= read -r f; do
    if git show "HEAD:$f" 2>/dev/null | cmp -s - "$OUT/$f"; then
      continue  # matches current repo version
    fi
    # A dist file that matches ANY committed version is merely stale
    # (built before recent commits) — only never-committed content
    # means someone edited the generated copy by hand.
    stale=0
    for rev in $(git rev-list -8 HEAD); do
      if git show "$rev:$f" 2>/dev/null | cmp -s - "$OUT/$f"; then
        stale=1; break
      fi
    done
    [ "$stale" = "1" ] && continue
    echo "ABORT: $OUT/$f contains changes that exist in no commit —"
    echo "it was edited in place. Port them into the repo copy first"
    echo "(that's the source the package is built from), or rerun with"
    echo "FORCE=1 to discard them."
    exit 1
  done < <(cd "$OUT" && find docs install.sh -type f 2>/dev/null)
fi

rm -rf "$OUT" dist/we.ather.zip
mkdir -p "$OUT"

# Code: the runtime package (minus the dev-only eval/labeling harness),
# installer, deps. Docs: exactly the three that serve a new group —
# host guide, member guide, security model (they cross-reference only
# each other, checked 2026-07-27).
git archive HEAD \
  presence \
  install.sh \
  requirements.txt \
  docs/self-hosting.md \
  docs/pilot-kit.md \
  docs/security-model.md \
  | tar -x -C "$OUT"
rm -rf "$OUT/presence/eval"

cat > "$OUT/README.md" <<'EOF'
# we.ather

Ambient "work weather" for small trusted rooms (2–10 people) working
with AI tools. Only low-resolution state — a work-phase and a few topic
words — ever leaves anyone's machine.

Start where you are:

- **Starting a room (you'll host it):** read `docs/self-hosting.md`.
  ~20 minutes, free Cloudflare account, one terminal command for the
  room itself.
- **Someone invited you:** read `docs/pilot-kit.md`, then run
  `./install.sh` and paste the invite you were sent.
- **"What exactly does this share?"**: `docs/security-model.md` —
  one page, covers what leaves your machine and what a compromised
  relay could and couldn't expose.

Requirements: macOS, Python 3.12+, and your AI working time in
Claude Code and/or Warp. Questions → Caitlin.
EOF

(cd dist && zip -qr we.ather.zip we.ather)
echo "built:"
find "$OUT" -type f | sed "s|$OUT/|  |" | sort
echo
du -h dist/we.ather.zip