#!/usr/bin/env node
/* 首页统计测试：node tests/test_home.js（无依赖，用假 DOM 和可控 fetch 运行 assets/home.js）。 */
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

const flush = async () => { for (let i = 0; i < 10; i++) await new Promise(r => setImmediate(r)); };

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
  { id: 'cne_a', grade: 3, semester: '上' }
];
const deps = [{ topicId: 'cnm_b', prereqId: 'cnm_a' }, { topicId: 'cne_a', prereqId: 'cne_x' }];
const standards = { items: [{ id: 'cms-1' }, { id: 'cms-2' }, { id: 'ces-1' }] };
const questions = [{ topicId: 'cnm_a' }, { topicId: 'cnm_b' }, { topicId: 'cnm_a' }, { topicId: 'cne_a' }];

function load(search) {
  const ids = {};
  ['n-topics', 'n-edges', 'n-questions', 'n-standards', 'load-error', 'grades'].forEach(id => { ids[id] = element(); });
  ids.grades.setAttribute('aria-busy', 'true');
  const calls = [];
  function fetch(url) {
    let resolve, reject;
    const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
    calls.push({ url, resolve, reject });
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
  const call = url => calls.find(c => c.url === url);
  const respond = (url, data, status) => {
    const c = call(url);
    assert.ok(c, 'expected fetch of ' + url);
    const ok = status === undefined || (status >= 200 && status < 300);
    c.resolve({ ok, status: status || 200, json: () => Promise.resolve(data) });
  };
  async function base() {
    respond('data/topics.json', topics);
    respond('data/dependencies.json', deps);
    respond('data/cn-curriculum-standards.json', standards);
    await flush();
  }
  return { ids, calls, call, respond, base, text: id => ids[id].textContent };
}

(async () => {
  await test('initial batch does not wait on questions.json', async () => {
    const h = load();
    assert.deepStrictEqual(h.calls.map(c => c.url), [
      'data/topics.json', 'data/dependencies.json', 'data/cn-curriculum-standards.json'
    ]);
    assert.equal(h.call('data/questions.json'), undefined);
  });

  await test('stats and grade cards render while questions.json is still pending', async () => {
    const h = load();
    await h.base();
    assert.equal(h.text('n-topics'), '2');
    assert.equal(h.text('n-edges'), '1');
    assert.equal(h.text('n-standards'), '2');
    assert.equal(h.text('n-questions'), '…');
    assert.ok(h.call('data/questions.json'), 'questions.json requested after base data');
    assert.ok(h.ids.grades.children.length > 0);
    assert.equal(h.ids.grades.hasAttribute('aria-busy'), false);
    assert.equal(h.ids['load-error'].hidden, true);
  });

  await test('question count is filled in once questions.json arrives (math)', async () => {
    const h = load();
    await h.base();
    h.respond('data/questions.json', questions);
    await flush();
    assert.equal(h.text('n-questions'), '3');
  });

  await test('question count is filtered by subject (english)', async () => {
    const h = load('?subject=english');
    await h.base();
    h.respond('data/questions.json', questions);
    await flush();
    assert.equal(h.text('n-questions'), '1');
    assert.equal(h.text('n-topics'), '1');
  });

  await test('subject with no questions shows 0', async () => {
    const h = load('?subject=chemistry');
    await h.base();
    h.respond('data/questions.json', questions);
    await flush();
    assert.equal(h.text('n-questions'), '0');
  });

  await test('questions.json HTTP error shows — without failing the page', async () => {
    const h = load();
    await h.base();
    h.respond('data/questions.json', null, 404);
    await flush();
    assert.equal(h.text('n-questions'), '—');
    assert.equal(h.ids['load-error'].hidden, true);
    assert.equal(h.text('n-topics'), '2');
    assert.ok(h.ids.grades.children.length > 0);
  });

  await test('non-array questions.json shows —', async () => {
    const h = load();
    await h.base();
    h.respond('data/questions.json', { items: [] });
    await flush();
    assert.equal(h.text('n-questions'), '—');
    assert.equal(h.ids['load-error'].hidden, true);
  });

  await test('questions.json network failure shows —', async () => {
    const h = load();
    await h.base();
    h.call('data/questions.json').reject(new Error('offline'));
    await flush();
    assert.equal(h.text('n-questions'), '—');
    assert.equal(h.ids['load-error'].hidden, true);
  });

  await test('invalid topics still reports a load error and skips questions.json', async () => {
    const h = load();
    h.respond('data/topics.json', { not: 'array' });
    h.respond('data/dependencies.json', deps);
    h.respond('data/cn-curriculum-standards.json', standards);
    await flush();
    assert.equal(h.ids['load-error'].hidden, false);
    assert.ok(h.text('load-error').includes('数据格式无法识别'));
    assert.equal(h.call('data/questions.json'), undefined);
  });

  await test('base data HTTP error reports a load error', async () => {
    const h = load();
    h.respond('data/topics.json', topics);
    h.respond('data/dependencies.json', null, 500);
    h.respond('data/cn-curriculum-standards.json', standards);
    await flush();
    assert.equal(h.ids['load-error'].hidden, false);
    assert.ok(h.text('load-error').includes('HTTP 500'));
  });

  console.log(passed + ' passed');
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
