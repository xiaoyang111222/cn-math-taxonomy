#!/usr/bin/env node
/* CI 工作流测试：node tests/test_ci_workflow.js（无依赖，只读取 .github/workflows/ci.yml）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const WORKFLOW = path.join(ROOT, '.github/workflows/ci.yml');
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function unquote(value) {
  const v = value.trim();
  if (/^".*"$/.test(v) || /^'.*'$/.test(v)) return v.slice(1, -1);
  return v;
}

function indentOf(line) { return line.match(/^ */)[0].length; }

function readSource() { return fs.readFileSync(WORKFLOW, 'utf8'); }

/* 解析 steps 列表：每个步骤收集 name / uses / run / continue-on-error / env / with。 */
function parseSteps(source) {
  const lines = source.split(/\r?\n/);
  const start = lines.findIndex((l) => /^\s+steps:\s*$/.test(l));
  assert.ok(start >= 0, 'steps: 未找到');
  const base = indentOf(lines[start]);
  const steps = [];
  let current = null;
  let itemIndent = -1;
  let section = null;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim() || line.trim().startsWith('#')) continue;
    const ind = indentOf(line);
    if (ind <= base) break;
    const body = line.trim();
    if (body.startsWith('- ')) {
      current = { env: {}, with: {} };
      steps.push(current);
      itemIndent = ind + 2;
      section = null;
      const m = body.slice(2).match(/^([\w-]+):\s*(.*)$/);
      if (m) current[m[1]] = unquote(m[2]);
      continue;
    }
    if (!current) continue;
    const m = body.match(/^([\w-]+):\s*(.*)$/);
    if (!m) continue;
    if (ind === itemIndent) {
      if (m[2] === '') { section = m[1]; current[m[1]] = current[m[1]] || {}; }
      else { section = null; current[m[1]] = unquote(m[2]); }
    } else if (section && ind > itemIndent) {
      current[section][m[1]] = unquote(m[2]);
    }
  }
  return steps;
}

function runSteps() { return parseSteps(readSource()).filter((s) => typeof s.run === 'string'); }

test('工作流文件存在', () => {
  assert.ok(fs.existsSync(WORKFLOW));
});

test('推送与 PR 到 main 时触发', () => {
  const src = readSource();
  assert.match(src, /^on:\s*$/m);
  assert.match(src, /^\s+push:\s*\n\s+branches:\s*\[\s*main\s*\]/m);
  assert.match(src, /^\s+pull_request:\s*\n\s+branches:\s*\[\s*main\s*\]/m);
});

test('权限仅为 contents: read', () => {
  const src = readSource();
  assert.match(src, /^permissions:\s*\n\s+contents:\s*read\s*$/m);
  assert.doesNotMatch(src, /:\s*write\b/);
});

test('在 ubuntu-latest 上运行', () => {
  assert.match(readSource(), /runs-on:\s*ubuntu-latest/);
});

test('先检出代码，再安装 Python 与 Node 22', () => {
  const steps = parseSteps(readSource());
  assert.equal(steps[0].uses, 'actions/checkout@v4');
  const py = steps.find((s) => /^actions\/setup-python@/.test(s.uses || ''));
  const node = steps.find((s) => /^actions\/setup-node@/.test(s.uses || ''));
  assert.ok(py, '缺少 setup-python');
  assert.ok(node, '缺少 setup-node');
  assert.equal(py.with['python-version'], '3.x');
  assert.equal(node.with['node-version'], '22');
  const firstRun = steps.findIndex((s) => s.run);
  assert.ok(steps.indexOf(py) < firstRun && steps.indexOf(node) < firstRun);
});

test('所有 action 均固定主版本号', () => {
  for (const s of parseSteps(readSource())) {
    if (s.uses) assert.match(s.uses, /^[\w.-]+\/[\w.-]+@v\d+$/, s.uses);
  }
});

test('每个 run 步骤都有名称', () => {
  for (const s of runSteps()) assert.ok(s.name && s.name.length > 0, s.run);
});

test('run 命令引用的脚本都存在于仓库中', () => {
  const steps = runSteps();
  assert.ok(steps.length >= 6);
  for (const s of steps) {
    const m = s.run.match(/^(python3|node)\s+(\S+)$/);
    assert.ok(m, '不支持的命令：' + s.run);
    assert.ok(fs.existsSync(path.join(ROOT, m[2])), '文件不存在：' + m[2]);
  }
});

test('数据校验为强制步骤（不允许失败）', () => {
  const strict = runSteps().filter((s) => s.run === 'python3 scripts/validate.py');
  const required = strict.filter((s) => s['continue-on-error'] !== 'true');
  assert.equal(required.length, 1);
  assert.equal(required[0].env.STRICT_STANDARDS, undefined);
});

test('课标严格模式只报告，不阻断构建', () => {
  const step = runSteps().find((s) => s.env.STRICT_STANDARDS !== undefined);
  assert.ok(step, '缺少 STRICT_STANDARDS 步骤');
  assert.equal(step.env.STRICT_STANDARDS, '1');
  assert.equal(step['continue-on-error'], 'true');
  assert.equal(step.run, 'python3 scripts/validate.py');
});

test('validate.py 读取 STRICT_STANDARDS=1 环境变量', () => {
  const py = fs.readFileSync(path.join(ROOT, 'scripts/validate.py'), 'utf8');
  assert.match(py, /os\.environ\.get\(\s*["']STRICT_STANDARDS["']\s*\)\s*==\s*["']1["']/);
});

test('除严格模式外，其余步骤均不允许失败', () => {
  for (const s of runSteps()) {
    if (s.env.STRICT_STANDARDS !== undefined) continue;
    assert.notEqual(s['continue-on-error'], 'true', s.name);
  }
});

test('运行题库答案核验', () => {
  assert.ok(runSteps().some((s) => s.run === 'python3 scripts/verify_questions.py'));
});

test('覆盖全部无浏览器依赖的 Node 测试', () => {
  const runs = new Set(runSteps().map((s) => s.run));
  const self = path.basename(__filename);
  const files = fs.readdirSync(path.join(ROOT, 'tests'))
    .filter((f) => /^test_.*\.js$/.test(f) && !/_browser\.js$/.test(f) && f !== self);
  assert.ok(files.length >= 3);
  for (const f of files) assert.ok(runs.has('node tests/' + f), '未在 CI 中运行：' + f);
});

test('不运行需要真实浏览器的测试', () => {
  for (const s of runSteps()) assert.doesNotMatch(s.run, /_browser\.js/);
});

test('parseSteps 能识别 env 与 continue-on-error', () => {
  const steps = parseSteps([
    'jobs:', '  x:', '    steps:',
    '      - name: a', '        continue-on-error: true', '        env:', '          K: "1"', '        run: echo',
    '      - uses: foo/bar@v1'
  ].join('\n'));
  assert.equal(steps.length, 2);
  assert.equal(steps[0].env.K, '1');
  assert.equal(steps[0]['continue-on-error'], 'true');
  assert.equal(steps[1].uses, 'foo/bar@v1');
});

console.log('\n' + passed + ' passed');
