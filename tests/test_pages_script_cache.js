#!/usr/bin/env node
/* 页面发布脚本的本地缓存目录与退出码：隔离 PATH，用假 npx，不触达远端。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const SCRIPT = path.join(ROOT, 'scripts/deploy-cf.sh');
const FORBIDDEN = [
  '.english-g7-research',
  '.english-g8-research',
  '.english-g9-research',
  '.moral-g78-research',
  '.moral-g9-research',
  '.science42-research',
  'grok-phases'
];
const REQUIRED = [
  './index.html',
  './sw.js',
  './manifest.webmanifest',
  './assets',
  './explore',
  './diagnose',
  './children',
  './data/topics.json',
  './data/dependencies.json',
  './data/cn-curriculum-standards.json',
  './data/questions.json',
  './data/id-aliases.json'
];
const FAKE_TOKEN = 'test-token-not-for-live';
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function parseKv(text) {
  const out = {};
  for (const line of String(text || '').split(/\r?\n/)) {
    const i = line.indexOf('=');
    if (i <= 0) continue;
    out[line.slice(0, i)] = line.slice(i + 1);
  }
  return out;
}

function leftoverUploadDirs(tmpdir) {
  if (!fs.existsSync(tmpdir)) return [];
  return fs.readdirSync(tmpdir).filter((n) => n.startsWith('cn-math-pages-dist.'));
}

function writeStub(stubDir) {
  const body = `#!/usr/bin/env bash
set -u
log="\${PAGES_STUB_LOG:-}"
if [[ -z "$log" ]]; then
  echo "pages stub missing PAGES_STUB_LOG" >&2
  exit 90
fi
{
  echo "stub=pages-script-cache"
  echo "argv0=$0"
  i=0
  for a in "$@"; do
    i=$((i+1))
    printf 'arg%d=%s\\n' "$i" "$a"
  done
  printf 'WRANGLER_CACHE_DIR=%s\\n' "\${WRANGLER_CACHE_DIR-}"
  printf 'XDG_CACHE_HOME=%s\\n' "\${XDG_CACHE_HOME-}"
} > "$log"
dist=""
prev=""
for a in "$@"; do
  if [[ "$prev" == "deploy" ]]; then
    dist="$a"
    break
  fi
  prev="$a"
done
printf 'dist=%s\\n' "$dist" >> "$log"
if [[ -z "\${WRANGLER_CACHE_DIR:-}" ]]; then
  echo "stub: cache dir unset" >&2
  exit 91
fi
if [[ ! -d "\$WRANGLER_CACHE_DIR" ]]; then
  echo "stub: cache dir missing" >&2
  exit 92
fi
if [[ ! -w "\$WRANGLER_CACHE_DIR" ]]; then
  echo "stub: cache dir not writable" >&2
  exit 93
fi
if [[ -n "$dist" && -d "$dist" ]]; then
  (cd "$dist" && find . | sort) > "\${log}.tree"
fi
exit "\${PAGES_STUB_EXIT:-0}"
`;
  fs.mkdirSync(stubDir, { recursive: true });
  const stub = path.join(stubDir, 'npx');
  fs.writeFileSync(stub, body, { mode: 0o755 });
  return stub;
}

function runScript(extraEnv) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-script-cache-'));
  const stubDir = path.join(tmp, 'bin');
  const log = path.join(tmp, 'stub.log');
  const workTmp = extraEnv && extraEnv.TMPDIR ? extraEnv.TMPDIR : path.join(tmp, 'tmp');
  writeStub(stubDir);
  fs.mkdirSync(workTmp, { recursive: true });
  const env = {
    ...process.env,
    PATH: stubDir + path.delimiter + '/usr/bin:/bin',
    PAGES_STUB_LOG: log,
    PAGES_STUB_EXIT: '0',
    TMPDIR: workTmp,
    CLOUDFLARE_API_TOKEN: FAKE_TOKEN,
    CLOUDFLARE_ACCOUNT_ID: 'test-account-id'
  };
  delete env.WRANGLER_CACHE_DIR;
  Object.assign(env, extraEnv || {});
  if (env.TMPDIR) fs.mkdirSync(env.TMPDIR, { recursive: true });
  const result = spawnSync('bash', [SCRIPT], {
    env,
    encoding: 'utf8',
    timeout: 120000
  });
  const logText = fs.existsSync(log) ? fs.readFileSync(log, 'utf8') : '';
  const treeText = fs.existsSync(log + '.tree') ? fs.readFileSync(log + '.tree', 'utf8') : '';
  return {
    tmp,
    env,
    result,
    logText,
    kv: parseKv(logText),
    tree: treeText.split(/\r?\n/).filter(Boolean),
    leftover: leftoverUploadDirs(env.TMPDIR)
  };
}

function cleanupRun(run) {
  fs.rmSync(run.tmp, { recursive: true, force: true });
  if (run.env.WRANGLER_CACHE_DIR && String(run.env.WRANGLER_CACHE_DIR).startsWith(run.tmp)) {
    fs.rmSync(run.env.WRANGLER_CACHE_DIR, { recursive: true, force: true });
  }
}

test('bash -n 通过', () => {
  const r = spawnSync('bash', ['-n', SCRIPT], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
});

test('脚本设置 4.86.0 支持的可写缓存变量，且不 sudo / chmod 777', () => {
  const src = fs.readFileSync(SCRIPT, 'utf8');
  assert.match(src, /WRANGLER_CACHE_DIR/);
  assert.match(src, /wrangler@4\.86\.0/);
  assert.match(src, /pages deploy/);
  assert.doesNotMatch(src, /\bsudo\b/);
  assert.doesNotMatch(src, /chmod\s+777/);
  assert.doesNotMatch(src, /export XDG_CACHE_HOME/);
});

test('正常路径：假发布退出 0，脚本退出 0，缓存目录可写', () => {
  const run = runScript({ PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.equal(run.kv.stub, 'pages-script-cache');
    assert.equal(run.kv.arg1, '--yes');
    assert.equal(run.kv.arg2, 'wrangler@4.86.0');
    assert.equal(run.kv.arg3, 'pages');
    assert.equal(run.kv.arg4, 'deploy');
    const cacheDir = run.kv.WRANGLER_CACHE_DIR;
    assert.ok(cacheDir, '未设置 WRANGLER_CACHE_DIR');
    assert.ok(fs.existsSync(cacheDir), cacheDir);
    assert.ok(fs.statSync(cacheDir).isDirectory());
    fs.accessSync(cacheDir, fs.constants.W_OK);
    assert.equal(run.leftover.length, 0, String(run.leftover));
    assert.doesNotMatch(run.result.stdout + run.result.stderr, new RegExp(FAKE_TOKEN));
  } finally {
    cleanupRun(run);
  }
});

test('失败退出码原样返回（2），不当成成功', () => {
  const run = runScript({ PAGES_STUB_EXIT: '2' });
  try {
    assert.equal(run.result.status, 2, run.result.stderr);
    assert.equal(run.kv.stub, 'pages-script-cache');
    assert.ok(run.kv.WRANGLER_CACHE_DIR);
    assert.equal(run.leftover.length, 0, String(run.leftover));
  } finally {
    cleanupRun(run);
  }
});

test('失败退出码原样返回（3），并清理临时上传目录', () => {
  const run = runScript({ PAGES_STUB_EXIT: '3' });
  try {
    assert.equal(run.result.status, 3, run.result.stderr);
    assert.equal(run.leftover.length, 0, String(run.leftover));
    assert.ok(run.kv.dist, '假发布未收到上传目录');
    assert.ok(!fs.existsSync(run.kv.dist), run.kv.dist);
  } finally {
    cleanupRun(run);
  }
});

test('成功后临时上传目录已删除', () => {
  const run = runScript({ PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.ok(run.kv.dist);
    assert.ok(!fs.existsSync(run.kv.dist), run.kv.dist);
    assert.equal(run.leftover.length, 0, String(run.leftover));
  } finally {
    cleanupRun(run);
  }
});

test('调用方已设置可写缓存目录时沿用', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-script-cache-'));
  const custom = path.join(tmp, 'custom-cache');
  fs.mkdirSync(custom);
  const run = runScript({ WRANGLER_CACHE_DIR: custom, PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.equal(run.kv.WRANGLER_CACHE_DIR, custom);
  } finally {
    cleanupRun(run);
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('调用方缓存路径不可写时改用可写目录', () => {
  const run = runScript({
    WRANGLER_CACHE_DIR: '/node_modules/.cache/wrangler',
    PAGES_STUB_EXIT: '0'
  });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.notEqual(run.kv.WRANGLER_CACHE_DIR, '/node_modules/.cache/wrangler');
    fs.accessSync(run.kv.WRANGLER_CACHE_DIR, fs.constants.W_OK);
  } finally {
    cleanupRun(run);
  }
});

test('TMPDIR 含空格时缓存与上传路径仍正确', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-script-cache-'));
  const spaced = path.join(tmp, 'tmp dir');
  fs.mkdirSync(spaced);
  const run = runScript({ TMPDIR: spaced, PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.ok(run.kv.WRANGLER_CACHE_DIR.indexOf(' ') >= 0);
    fs.accessSync(run.kv.WRANGLER_CACHE_DIR, fs.constants.W_OK);
    assert.ok(run.kv.dist.indexOf(' ') >= 0);
    assert.ok(!fs.existsSync(run.kv.dist));
    assert.equal(run.leftover.length, 0);
  } finally {
    cleanupRun(run);
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('缓存目录路径含空格时仍沿用该路径', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-script-cache-'));
  const custom = path.join(tmp, 'cache dir');
  fs.mkdirSync(custom);
  const run = runScript({ WRANGLER_CACHE_DIR: custom, PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.equal(run.kv.WRANGLER_CACHE_DIR, custom);
    fs.accessSync(custom, fs.constants.W_OK);
  } finally {
    cleanupRun(run);
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('只打包白名单，不把研究目录拷进上传目录', () => {
  const run = runScript({ PAGES_STUB_EXIT: '0' });
  try {
    assert.equal(run.result.status, 0, run.result.stderr);
    assert.ok(run.tree.length > 0, '假发布未看到上传目录内容');
    const set = new Set(run.tree);
    for (const rel of REQUIRED) {
      assert.ok(set.has(rel), '缺少 ' + rel);
    }
    assert.ok(!set.has('./diagnose/README.md'));
    for (const name of FORBIDDEN) {
      const hit = run.tree.some((p) => p === './' + name || p.startsWith('./' + name + '/'));
      assert.ok(!hit, '不应上传 ' + name);
    }
    const src = fs.readFileSync(SCRIPT, 'utf8');
    for (const name of FORBIDDEN) {
      assert.doesNotMatch(src, new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    }
  } finally {
    cleanupRun(run);
  }
});

console.log('\n' + passed + ' passed');
