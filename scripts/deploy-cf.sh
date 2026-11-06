#!/usr/bin/env bash
# Deploy the static site to Cloudflare Pages project cn-math-taxonomy (math.pansgo.com).
# Requires: CLOUDFLARE_API_TOKEN (and usually CLOUDFLARE_ACCOUNT_ID), npx/wrangler.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${TMPDIR:-/tmp}/cn-math-pages-dist.$$"
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-6799c67ce94928e7fc4136842327a18f}"
export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/xdg-cache}"
mkdir -p "$XDG_CACHE_HOME" "$DIST/data/mappings"

cp "$ROOT/index.html" "$ROOT/sw.js" "$ROOT/manifest.webmanifest" "$DIST/"
[[ -f "$ROOT/.nojekyll" ]] && cp "$ROOT/.nojekyll" "$DIST/"
cp -a "$ROOT/assets" "$DIST/"
cp -a "$ROOT/explore" "$DIST/"
cp -a "$ROOT/diagnose" "$DIST/"
cp -a "$ROOT/children" "$DIST/"
rm -f "$DIST/diagnose/README.md"
cp "$ROOT/data/topics.json" \
   "$ROOT/data/dependencies.json" \
   "$ROOT/data/cn-curriculum-standards.json" \
   "$ROOT/data/questions.json" \
   "$ROOT/data/id-aliases.json" \
   "$DIST/data/"
cp "$ROOT/data/mappings/sujiao_math.json" \
   "$ROOT/data/mappings/hujiao_math.json" \
   "$ROOT/data/mappings/sd54_math.json" \
   "$ROOT/data/mappings/yilin_english.json" \
   "$DIST/data/mappings/"

echo "Deploying $(du -sh "$DIST" | awk '{print $1}') from $DIST ..."
# Upload often succeeds even if wrangler then trips on a local cache path; check exit and pages.dev.
set +e
npx --yes wrangler@4.86.0 pages deploy "$DIST" \
  --project-name cn-math-taxonomy \
  --branch main \
  --commit-dirty=true
rc=$?
set -e
rm -rf "$DIST"
if [[ $rc -ne 0 ]]; then
  echo "wrangler exited $rc — if files uploaded, check https://cn-math-taxonomy.pages.dev/ anyway." >&2
  exit "$rc"
fi
echo "Done. Production: https://math.pansgo.com/  (alias https://cn-math-taxonomy.pages.dev/)"
