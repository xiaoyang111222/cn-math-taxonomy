#!/usr/bin/env node
/* 首页题库异步：假 DOM + 可控 fetch。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/home.js'), 'utf8');
let passed = 0;

async function test(name, fn) {
  await fn();
  passed++;
  console.log('  ok   ' + name);
}

const flush = async () => { for (let i = 0; i < 12; i++) await new Promise(r => setImmediate(r)); };

function element() {
  const attrs = {};
  const el = {
    textContent: '', hidden: true, children: [], className: '', href: '',
    classList: { toggle() {}, add() {}, remove() {} },
    setAttribute(k, v) { attrs[k] = String(v); },
    getAttribute(k) { return k in attrs ? attrs[k] : null; },
    removeAttribute(k) { delete attrs[k]; },
    hasAttribute(k) { return k in attrs; },
    replaceChildren() { el.children = []; },
    append(...nodes) { el.children.push(...nodes); },
    appendChild(node) { el.children.push(node); return node; }
  };
  return el;
}

const topics = [
  { id: 'cnm_a', grade: 1, semester: '上' },
  { id: 'cnm_b', grade: 7, semester: '下' },
  { id: 'cne_a', grade: 3, semester: '上' },
  { id: 'cnp_a', grade: 8, semester: '上' }
];
const deps = [{ topicId: 'cnm_b', prerequisiteId: 'cnm_a' }];
const standards = { items: [{ id: 'cms-1' }, { id: 'ces-1' }, { id: 'cps-1' }] };
const questions = [
  { topicId: 'cnm_a' }, { topicId: 'cnm_b' }, { topicId: 'cnm_a' },
  { topicId: 'cne_a' }, { topicId: 'cnp_a' }
];

function load(search) {
  const ids = {};
  ['n-topics', 'n-edges', 'n-questions', 'n-standards', 'load-error', 'grades'].forEach(id => { ids[id] = element(); });
  ids.grades.setAttribute('aria-busy', 'true');
  const calls = [];
  function fetch(url) {
    let resolve, reject;
    const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
    calls.push({ url, resolve, reject, promise });
    return promise;
  }
  const context = {
    window: {},
    location: { hash: '', search: search || '' },
    URLSearchParams,
    fetch,
    document: {
      title: '',
      body: { classList: { toggle() {} } },
      querySelector() { return null; },
      querySelectorAll() { return []; },
      getElementById(id) { return ids[id] || null; },
      createElement() { return element(); }
    }
  };
  vm.runInNewContext(source, context, { filename: 'assets/home.js' });
  const all = url => calls.filter(c => c.url === url);
  const call = url => all(url)[0];
  const respond = (url, data, status) => {
    const c = call(url);
    assert.ok(c, 'expected fetch of ' + url);
    const ok = status === undefined || (status >= 200 && status < 300);
    c.resolve({ ok, status: status || 200, json: () => Promise.resolve(data) });
  };
  const failNet = (url) => {
    const c = call(url);
    assert.ok(c, 'expected fetch of ' + url);
    c.reject(new Error('network'));
  };
  async function baseMeta() {
    respond('data/topics.json', topics);
    respond('data/dependencies.json', deps);
    respond('data/cn-curriculum-standards.json', standards);
    await flush();
  }
  return { ids, calls, all, call, respond, failNet, baseMeta };
}

(async () => {
  await test('元数据到后可渲染，题库先显示 …', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    assert.strictEqual(ids['n-topics'].textContent, '2');
    assert.strictEqual(ids['n-questions'].textContent, '…');
    assert.ok(ids.grades.children.length > 0, 'grade cards rendered');
    respond('data/questions.json', questions);
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '3');
  });

  await test('题库 404 显示 — 且不整页 fail', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    respond('data/questions.json', null, 404);
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '—');
    assert.strictEqual(ids['load-error'].hidden, true);
  });

  await test('题库非数组显示 —', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    respond('data/questions.json', { nope: true });
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '—');
  });

  await test('题库网络错误会重试至多 2 次', async () => {
    const { ids, all, baseMeta, failNet, respond } = load('');
    await baseMeta();
    assert.strictEqual(all('data/questions.json').length, 1);
    failNet('data/questions.json');
    await flush();
    assert.ok(all('data/questions.json').length >= 2, 'retried');
    // second attempt succeeds
    const second = all('data/questions.json')[1];
    second.resolve({ ok: true, status: 200, json: () => Promise.resolve(questions) });
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '3');
  });

  await test('进行中 Promise 去重', async () => {
    assert.ok(source.includes('fetchInflight'), 'inflight map present');
    assert.ok(source.includes('fetchJsonWithRetry'), 'retry helper present');
  });

  await test('topics 无效仍 fail', async () => {
    const { ids, respond } = load('');
    respond('data/topics.json', { bad: true });
    respond('data/dependencies.json', deps);
    respond('data/cn-curriculum-standards.json', standards);
    await flush();
    assert.strictEqual(ids['load-error'].hidden, false);
  });

  await test('英语学科计数过滤', async () => {
    const { ids, baseMeta, respond } = load('?subject=english');
    await baseMeta();
    respond('data/questions.json', questions);
    await flush();
    assert.strictEqual(ids['n-topics'].textContent, '1');
    assert.strictEqual(ids['n-questions'].textContent, '1');
  });

  console.log(passed + ' passed');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
