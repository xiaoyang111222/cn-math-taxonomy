#!/usr/bin/env node
/* 道德与法治初中入口：首页行为 + 图谱/诊断源码门槛。不读全仓。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
let passed = 0;

function test(name, fn) {
  return Promise.resolve(fn()).then(function () {
    passed++;
    console.log('  ok   ' + name);
  });
}

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

function loadHome(search) {
  const ids = {};
  ['n-topics', 'n-edges', 'n-questions', 'n-standards', 'load-error', 'grades'].forEach(function (id) {
    ids[id] = element();
  });
  const eyebrow = element();
  eyebrow.className = 'eyebrow';
  const calls = [];
  function fetch(url) {
    let resolve;
    let reject;
    const promise = new Promise(function (res, rej) { resolve = res; reject = rej; });
    calls.push({ url: url, resolve: resolve, reject: reject });
    return promise;
  }
  const context = {
    window: {},
    location: { hash: '', search: search || '' },
    URLSearchParams: URLSearchParams,
    fetch: fetch,
    document: {
      title: '',
      body: { classList: { toggle() {} } },
      querySelector(sel) { return sel === '.eyebrow' ? eyebrow : null; },
      querySelectorAll() { return []; },
      getElementById(id) { return ids[id] || null; },
      createElement() { return element(); }
    }
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'assets/home.js'), 'utf8'), context, { filename: 'assets/home.js' });
  return { ids: ids, eyebrow: eyebrow, calls: calls, document: context.document };
}

(async function () {
  await test('首页道法画出已有初中年级，空年级不画高中卡', async function () {
    const home = loadHome('?subject=morality');
    const topics = [
      { id: 'cnd_p001', subject: 'morality', grade: 1, semester: '上' },
      { id: 'cnd_j701', subject: 'morality', grade: 7, semester: '上' },
      { id: 'cnd_j702', subject: 'morality', grade: 7, semester: '下' },
      { id: 'cnd_j801', subject: 'morality', grade: 8, semester: '上' },
      { id: 'cnd_j802', subject: 'morality', grade: 8, semester: '下' }
    ];
    const byUrl = {};
    home.calls.forEach(function (call) { byUrl[call.url] = call; });
    assert.ok(byUrl['data/topics.json']);
    byUrl['data/topics.json'].resolve({ ok: true, status: 200, json: function () { return Promise.resolve(topics); } });
    byUrl['data/dependencies.json'].resolve({ ok: true, status: 200, json: function () { return Promise.resolve([]); } });
    byUrl['data/cn-curriculum-standards.json'].resolve({
      ok: true, status: 200, json: function () { return Promise.resolve({ items: [{ id: 'cds-2022:4.JK.01' }] }); }
    });
    for (let i = 0; i < 12; i++) await new Promise(function (r) { setImmediate(r); });
    const titles = home.ids.grades.children.map(function (card) {
      return card.children[1].textContent;
    });
    assert.deepStrictEqual(titles, ['一年级', '七年级', '八年级']);
    assert.ok(titles.indexOf('九年级') < 0);
    const splits = home.ids.grades.children.map(function (card) {
      return card.children[3].textContent;
    });
    assert.deepStrictEqual(splits, ['上 1', '上 1 · 下 1', '上 1 · 下 1']);
    assert.ok(home.ids.grades.children[0].className.indexOf('is-primary') >= 0);
    assert.ok(home.ids.grades.children.every(function (card) { return card.className.indexOf('is-senior') < 0; }));
    assert.strictEqual(home.document.title, '道德与法治 · 中小学·高中知识图谱');
    assert.ok(home.eyebrow.textContent.indexOf('初中现含七上、七下、八上、八下') >= 0);
    assert.ok(home.eyebrow.textContent.indexOf('九年级未录入') >= 0);
    assert.ok(home.eyebrow.textContent.indexOf('全初中') < 0);
    assert.strictEqual(home.ids['n-topics'].textContent, '5');
    assert.strictEqual(home.ids['n-standards'].textContent, '1');
  });

  await test('图谱年级含七至九且无高中学段', function () {
    const source = fs.readFileSync(path.join(root, 'explore/app.js'), 'utf8');
    assert.ok(source.indexOf('function fillMoralityGrades()') >= 0);
    assert.ok(source.indexOf('[1, 2, 3, 4, 5, 6, 7, 8, 9]') >= 0);
    assert.ok(source.indexOf("subject === 'chinese' || subject === 'morality'") >= 0);
    assert.ok(source.indexOf("button.hidden = button.getAttribute('data-stage') === 'h'") >= 0);
    assert.ok(source.indexOf('fillMoralityGrades();') >= 0);
  });

  await test('诊断道法学段含小学和初中', function () {
    const source = fs.readFileSync(path.join(root, 'diagnose/app.js'), 'utf8');
    const gate = "subject === 'chinese' || subject === 'morality' ? [stageButton('', '全部'), stageButton('p', '小学'), stageButton('j', '初中')]";
    assert.ok(source.indexOf(gate) >= 0);
    assert.ok(source.indexOf("subject === 'morality'") >= 0);
    assert.ok(source.indexOf("'一二三四五六七八九'") >= 0);
  });

  console.log('test_jmor_frontend ok ' + passed);
})().catch(function (err) {
  console.error(err);
  process.exit(1);
});
