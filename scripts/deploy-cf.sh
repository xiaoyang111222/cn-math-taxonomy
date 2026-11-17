#!/usr/bin/env bash
# Deploy the static site to Cloudflare Pages project cn-math-taxonomy (math.pansgo.com).
# Requires: CLOUDFLARE_API_TOKEN (and usually CLOUDFLARE_ACCOUNT_ID), npx/wrangler.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${TMPDIR:-/tmp}/cn-math-pages-dist.$$"
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-6799c67ce94928e7fc4136842327a18f}"
export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/xdg-cache}"
mkdir -p "$XDG_CACHE_HOME" "$DIST/data"

# 题库学科分片：每次部署前从 questions.json 重新生成
python3 "$ROOT/scripts/split_questions.py"

cp "$ROOT/index.html" "$ROOT/sw.js" "$ROOT/manifest.webmanifest" "$DIST/"
[[ -f "$ROOT/.nojekyll" ]] && cp "$ROOT/.nojekyll" "$DIST/"
cp -a "$ROOT/assets" "$DIST/"
cp -a "$ROOT/explore" "$DIST/"
cp -a "$ROOT/diagnose" "$DIST/"
cp -a "$ROOT/children" "$DIST/"
cp -a "$ROOT/practice" "$DIST/"
rm -f "$DIST/diagnose/README.md"
cp "$ROOT/data/topics.json" \
   "$ROOT/data/dependencies.json" \
   "$ROOT/data/cn-curriculum-standards.json" \
   "$ROOT/data/questions.json" \
   "$ROOT/data/questions-math.json" \
   "$ROOT/data/questions-english.json" \
   "$ROOT/data/questions-physics.json" \
   "$ROOT/data/id-aliases.json" \
   "$ROOT/data/question-templates.json" \
   "$DIST/data/"

# 教材版本对照表（示例文件 *.example.json 前端不读，不部署）
mkdir -p "$DIST/data/mappings"
for f in "$ROOT"/data/mappings/*.json; do
  [[ -e "$f" && "$f" != *.example.json ]] && cp "$f" "$DIST/data/mappings/"
done

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
