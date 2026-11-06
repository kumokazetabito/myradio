#!/bin/bash
# Build real episode pages and update an existing gh-pages worktree without force-pushing.
# First build and commit source + generated files. This script keeps audio and archives.
# PAGES_PYTHON: Python with tools/requirements-pages.txt installed.
# PAGES_WORKTREE: existing, clean gh-pages worktree (default: sibling github-radio-publish).
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
PAGES_PYTHON=${PAGES_PYTHON:-python3}
PAGES_WORKTREE=${PAGES_WORKTREE:-"$ROOT/../github-radio-publish"}
if [ "$(git -C "$PAGES_WORKTREE" branch --show-current)" != gh-pages ]; then
  echo 'Publication requires an existing gh-pages worktree.' >&2; exit 1
fi
if [ -n "$(git -C "$PAGES_WORKTREE" status --porcelain)" ]; then
  echo 'The gh-pages worktree has unsaved changes; publication stopped.' >&2; exit 1
fi
"$PAGES_PYTHON" "$ROOT/tools/build_pages.py" --root "$ROOT"
if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
  echo 'Commit the source and generated pages before publication.' >&2; exit 1
fi
"$PAGES_PYTHON" "$ROOT/tools/build_pages.py" --root "$ROOT" --publish-dir "$PAGES_WORKTREE"
git -C "$PAGES_WORKTREE" add -A
# main ignores audio; stage only audio referenced by the published episode manifest.
while IFS= read -r -d '' asset; do
  git -C "$PAGES_WORKTREE" add -f -- "$asset"
done < <("$PAGES_PYTHON" - "$ROOT/pages-manifest.json" <<'PYTHON'
import json,sys
for path in json.load(open(sys.argv[1])).get('audio', []):
    sys.stdout.buffer.write(path.encode() + b'\0')
PYTHON
)
if ! git -C "$PAGES_WORKTREE" diff --cached --quiet; then
  git -C "$PAGES_WORKTREE" commit -m 'Publish generated episode pages'
  git -C "$PAGES_WORKTREE" push origin gh-pages
fi
