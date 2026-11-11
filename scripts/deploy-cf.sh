#!/usr/bin/env bash
# Deploy the static site to Cloudflare Pages project cn-math-taxonomy (math.pansgo.com).
# Requires: CLOUDFLARE_API_TOKEN (and usually CLOUDFLARE_ACCOUNT_ID), npx/wrangler.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${TMPDIR:-/tmp}/cn-math-pages-dist.$$"
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-6799c67ce94928e7fc4136842327a18f}"
export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"
# wrangler 4.86.0 getCacheFolder() reads WRANGLER_CACHE_DIR, then falls back to
# <nearest node_modules>/.cache/wrangler (here that is /node_modules/.cache/wrangler).
# XDG_CACHE_HOME is not consulted for that path.
if [[ -n "${WRANGLER_CACHE_DIR:-}" ]]; then
  if ! mkdir -p "$WRANGLER_CACHE_DIR" 2>/dev/null || [[ ! -w "$WRANGLER_CACHE_DIR" ]]; then
    WRANGLER_CACHE_DIR="${TMPDIR:-/tmp}/cn-math-wrangler-cache"
    mkdir -p "$WRANGLER_CACHE_DIR"
  fi
else
  WRANGLER_CACHE_DIR="${TMPDIR:-/tmp}/cn-math-wrangler-cache"
  mkdir -p "$WRANGLER_CACHE_DIR"
fi
export WRANGLER_CACHE_DIR
mkdir -p "$DIST/data"

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
