#!/usr/bin/env node
/* 诊断页「这道题有错？报错」链接测试：node tests/test_report_link.js（无依赖，不启动浏览器）。
 * 从 diagnose/app.js 截取 h / append / answerText / reportUrl / feedbackBlock，在最小 DOM 桩上运行。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const APP = fs.readFileSync(path.join(ROOT, 'diagnose/app.js'), 'utf8');
const TEMPLATE = fs.readFileSync(path.join(ROOT, '.github/ISSUE_TEMPLATE/question-fix.yml'), 'utf8');
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function slice(src, startMarker, endMarker) {
  const a = src.indexOf(startMarker);
  assert.ok(a >= 0, '找不到 ' + startMarker);
  const b = src.indexOf(endMarker, a);
  assert.ok(b > a, '找不到 ' + endMarker);
  return src.slice(a, b);
}

class FakeNode {
  constructor(tag) { this.tagName = tag; this.attrs = {}; this.children = []; this.className = ''; this.listeners = {}; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  addEventListener(t, fn) { this.listeners[t] = fn; }
  append(c) { this.children.push(c); }
  get nodeType() { return 1; }
  get textContent() { return this._text != null ? this._text : this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this._text = String(v); }
  find(pred) {
    if (pred(this)) return this;
    for (const c of this.children) { if (c instanceof FakeNode) { const r = c.find(pred); if (r) return r; } }
    return null;
  }
}
class FakeText {
  constructor(t) { this.textContent = t; }
  get nodeType() { return 3; }
}

function load() {
  const code = slice(APP, '  function h(tag, attrs) {', '  function figureEl(') +
    slice(APP, '  function answerText(q) {', '  function renderQuestion(') +
    '\nthis.api = { reportUrl: reportUrl, feedbackBlock: feedbackBlock, ISSUE_NEW_URL: ISSUE_NEW_URL };';
  const context = {
    document: { createElement: tag => new FakeNode(tag), createTextNode: t => new FakeText(t) }
  };
  vm.runInNewContext(code, context, { filename: 'diagnose/app.js' });
  return context.api;
}

const api = load();
const byId = (root, id) => root.find(n => n.getAttribute('id') === id);
const byClass = (root, cls) => root.find(n => (' ' + n.className + ' ').indexOf(' ' + cls + ' ') >= 0);

test('reportUrl 指向本仓库的 new issue 并选用 question-fix.yml 模板', () => {
  const u = new URL(api.reportUrl({ id: 'cnm_221_q3' }));
  assert.equal(u.origin + u.pathname, 'https://github.com/xiaoyang111222/cn-math-taxonomy/issues/new');
  assert.equal(u.searchParams.get('template'), 'question-fix.yml');
});

test('reportUrl 预填标题「[题目] <id>」和题目 ID', () => {
  const u = new URL(api.reportUrl({ id: 'cnm_p001_q1' }));
  assert.equal(u.searchParams.get('title'), '[题目] cnm_p001_q1');
  assert.equal(u.searchParams.get('question_id'), 'cnm_p001_q1');
});

test('reportUrl 对中文和特殊字符做 URL 编码', () => {
  const raw = api.reportUrl({ id: 'a&b=c #d' });
  assert.ok(raw.indexOf('%5B%E9%A2%98%E7%9B%AE%5D') >= 0, '标题中的「[题目]」应被编码');
  assert.ok(raw.indexOf(' ') < 0 && raw.indexOf('#') < 0, '空格和 # 不能原样出现');
  const u = new URL(raw);
  assert.equal(u.searchParams.get('question_id'), 'a&b=c #d');
  assert.equal(u.searchParams.get('title'), '[题目] a&b=c #d');
  assert.deepStrictEqual([...u.searchParams.keys()], ['template', 'title', 'question_id']);
});

test('URL 里的 question_id 与模板中的字段 id 一致，标题前缀与模板一致', () => {
  assert.ok(/^\s+id:\s*question_id\s*$/m.test(TEMPLATE), '模板缺少 question_id 字段');
  assert.ok(/^title:\s*"\[题目\] "\s*$/m.test(TEMPLATE), '模板标题前缀应为「[题目] 」');
  assert.ok(fs.existsSync(path.join(ROOT, '.github/ISSUE_TEMPLATE', new URL(api.reportUrl({ id: 'x' })).searchParams.get('template'))));
});

test('有 id 的题目在反馈块里显示报错链接，新窗口打开且不泄露 opener', () => {
  const q = { id: 'cnm_221_q3', type: 'numeric', answer: '-2', explanation: '配方。' };
  const block = api.feedbackBlock(q);
  const a = byId(block, 'report-q');
  assert.ok(a, '应有 #report-q 链接');
  assert.equal(a.tagName, 'a');
  assert.equal(a.getAttribute('href'), api.reportUrl(q));
  assert.equal(a.getAttribute('target'), '_blank');
  assert.equal(a.getAttribute('rel'), 'noopener noreferrer');
  assert.equal(a.textContent, '这道题有错？报错');
});

test('报错链接包在 .report-link.no-print 中，位于参考答案和解析之后', () => {
  const block = api.feedbackBlock({ id: 'cnm_221_q3', type: 'numeric', answer: '-2', explanation: '配方。' });
  const wrap = byClass(block, 'report-link');
  assert.ok(wrap, '应有 .report-link');
  assert.ok(/\bno-print\b/.test(wrap.className), '打印时应隐藏');
  const kinds = block.children.map(c => c.className);
  assert.deepStrictEqual(kinds, ['refans', 'explain', 'report-link no-print']);
});

test('没有解析时报错链接仍紧跟参考答案', () => {
  const block = api.feedbackBlock({ id: 'cnm_100_q2', type: 'numeric', answer: '4' });
  assert.deepStrictEqual(block.children.map(c => c.className), ['refans', 'report-link no-print']);
  assert.ok(byId(block, 'report-q'));
});

test('题目没有 id 时不显示报错链接', () => {
  for (const id of [undefined, null, '']) {
    const block = api.feedbackBlock({ id, type: 'numeric', answer: '4', explanation: 'x' });
    assert.equal(byId(block, 'report-q'), null);
    assert.equal(byClass(block, 'report-link'), null);
  }
});

test('选择题的参考答案显示不受报错链接影响', () => {
  const q = { id: 'cnm_p001_q4', type: 'choice', answer: 'B', choices: [{ key: 'A', text: '3' }, { key: 'B', text: '5' }] };
  const block = api.feedbackBlock(q);
  assert.equal(byClass(block, 'refans').textContent, '参考答案：B. 5');
  assert.equal(new URL(byId(block, 'report-q').getAttribute('href')).searchParams.get('question_id'), 'cnm_p001_q4');
});

test('模板说明的题目 ID 格式为 <知识点id>_q<N>，占位符为 cnm_xxx_qN', () => {
  assert.ok(/^\s+placeholder:\s*cnm_xxx_qN\s*$/m.test(TEMPLATE));
  assert.ok(TEMPLATE.indexOf('<知识点id>_q<N>') >= 0);
  assert.ok(TEMPLATE.indexOf('q_cnm_') < 0, '旧格式 q_cnm_xxx 不应再出现');
});

test('题库里的题目 id 确实是 <知识点id>_q<N> 格式', () => {
  const qs = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/questions.json'), 'utf8'));
  assert.ok(qs.length > 0);
  const bad = qs.filter(q => q.id && q.topicId && !new RegExp('^' + q.topicId + '_q\\d+$').test(q.id));
  assert.deepStrictEqual(bad.slice(0, 5).map(q => q.id), []);
});

test('样式表定义了 .report-link', () => {
  const css = fs.readFileSync(path.join(ROOT, 'diagnose/style.css'), 'utf8');
  assert.ok(/\.report-link\s*\{[^}]*text-align:\s*right/.test(css));
});

console.log(passed + ' passed');
