#!/usr/bin/env node
/* 本机盲区汇总测试：node tests/test_blindspots.js（无依赖，不访问真实浏览器存储）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SOURCE = fs.readFileSync(path.join(__dirname, '../assets/blindspots.js'), 'utf8');
const KEY = 'cnmBlind.local.v1';
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function load(entries) {
  const storage = new Map(Object.entries(entries || {}));
  const context = {
    window: {},
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(SOURCE, context, { filename: 'assets/blindspots.js' });
  return { api: context.window.CnmBlind, storage };
}

test('空库时 list 为空', () => {
  const { api } = load();
  assert.equal(api.list().length, 0);
  assert.equal(api.count(), 0);
});

test('noteResult 写入薄弱 / 不稳，并累计答错次数', () => {
  const { api, storage } = load();
  api.noteResult({
    subject: 'math', key: 'math|s1|t', label: '配方法',
    weak: ['cnm_221'], shaky: ['cnm_100'], mastered: ['cnm_050'],
    roots: ['cnm_221'],
    answers: [
      { id: 'cnm_221', result: 'wrong' },
      { id: 'cnm_221', result: 'wrong' },
      { id: 'cnm_100', result: 'wrong' },
      { id: 'cnm_100', result: 'correct' },
      { id: 'cnm_050', result: 'correct' }
    ]
  });
  const rows = api.list();
  assert.equal(rows.length, 2);
  assert.equal(rows[0].id, 'cnm_221');
  assert.equal(rows[0].status, 'weak');
  assert.equal(rows[0].root, true);
  assert.equal(rows[0].wrongs, 2);
  assert.equal(rows[1].id, 'cnm_100');
  assert.equal(rows[1].status, 'shaky');
  assert.equal(rows[1].wrongs, 1);
  const raw = JSON.parse(storage.get(KEY));
  assert.equal(raw.byId.cnm_050.status, 'mastered');
  assert.ok(!rows.some(r => r.id === 'cnm_050'));
});

test('再次掌握后从盲区列表消失（以最近一次为准）', () => {
  const { api } = load();
  api.noteResult({
    subject: 'math', key: 'a', label: '一', weak: ['cnm_221'], shaky: [], mastered: [], roots: ['cnm_221'],
    answers: [{ id: 'cnm_221', result: 'wrong' }]
  });
  assert.equal(api.count(), 1);
  api.noteResult({
    subject: 'math', key: 'b', label: '二', weak: [], shaky: [], mastered: ['cnm_221'], roots: [],
    answers: [{ id: 'cnm_221', result: 'correct' }]
  });
  assert.equal(api.count(), 0);
});

test('diagnoseHref 带学科参数', () => {
  const { api } = load();
  assert.equal(api.diagnoseHref(['cne_p001'], 'english', '../diagnose/'),
    '../diagnose/?subject=english&target=cne_p001');
  assert.equal(api.diagnoseHref(['cnm_221'], 'math', './'), './?target=cnm_221');
  assert.equal(api.diagnoseHref(['cnd_p001', 'cnd_p002']),
    'diagnose/?subject=morality&target=cnd_p001,cnd_p002');
  assert.equal(api.diagnoseHref(['cnh_j001']),
    'diagnose/?subject=history&target=cnh_j001');
  assert.equal(api.diagnoseHref(['cng_j001']),
    'diagnose/?subject=geography&target=cng_j001');
  assert.equal(api.diagnoseHref(['cnb_j001']),
    'diagnose/?subject=biology&target=cnb_j001');
  assert.equal(api.diagnoseHref(['cnk_j001']),
    'diagnose/?subject=chemistry&target=cnk_j001');
  assert.equal(api.diagnoseHref(['cnc_j001']),
    'diagnose/?subject=chinese&target=cnc_j001');
  assert.equal(api.diagnoseHref(['cnc_p001', 'cnc_j002']),
    'diagnose/?subject=chinese&target=cnc_p001,cnc_j002');
  assert.equal(api.subjectOfId('cnc_j001'), 'chinese');
  assert.equal(api.subjectOfId('cnc_p001'), 'chinese');
});

test('初中语文未完成会话仍归语文，并与小学会话共用 cncDiagnose.session.v2', () => {
  const { api } = load({
    'cncDiagnose.session.v2': JSON.stringify({
      label: '七上 春', savedAt: '2026-11-06T01:00:00.000Z',
      answers: [
        { id: 'cnc_j001', result: 'wrong' },
        { id: 'cnc_p001', result: 'wrong' },
        { id: 'cnc_j002', result: 'correct' }
      ]
    })
  });
  const rows = api.list({ subject: 'chinese' });
  const ids = [];
  rows.forEach((r) => ids.push(String(r.id)));
  ids.sort();
  assert.deepStrictEqual(ids, ['cnc_j001', 'cnc_p001']);
  rows.forEach((r) => {
    assert.equal(r.subject, 'chinese');
    assert.equal(r.source, 'session');
  });
});

test('subject 过滤与未完成会话答错合并', () => {
  const { api } = load({
    'cneDiagnose.session.v2': JSON.stringify({
      label: '四上 Unit1', savedAt: '2026-10-30T01:00:00.000Z',
      answers: [
        { id: 'cne_p010', result: 'wrong' },
        { id: 'cne_p011', result: 'correct' }
      ]
    })
  });
  api.noteResult({
    subject: 'math', key: 'm', label: '数学', weak: ['cnm_221'], shaky: [], mastered: [], roots: ['cnm_221'],
    answers: [{ id: 'cnm_221', result: 'wrong' }]
  });
  const en = api.list({ subject: 'english' });
  assert.equal(en.length, 1);
  assert.equal(en[0].id, 'cne_p010');
  assert.equal(en[0].source, 'session');
  assert.equal(en[0].wrongs, 1);
  assert.equal(api.list({ subject: 'math' }).length, 1);
});

test('demo 标记不写入', () => {
  const { api } = load();
  api.noteResult({
    demo: true, subject: 'math', weak: ['cnm_221'], shaky: [], mastered: [], roots: ['cnm_221'],
    answers: [{ id: 'cnm_221', result: 'wrong' }]
  });
  assert.equal(api.count(), 0);
});

test('孩子档案 latestStatus 可并入列表', () => {
  const { api } = load();
  const contextWindow = { CnmChildren: {
    current() { return { id: 'c1', name: '小禾' }; },
    latestStatus() {
      return {
        cnm_300: { status: 'weak', root: true, at: '2026-10-30T08:00:00.000Z', label: '整体', subject: 'math' },
        cnm_301: { status: 'mastered', at: '2026-10-30T08:00:00.000Z', subject: 'math' }
      };
    }
  }};
  // reload with CnmChildren present
  const storage = new Map();
  const ctx = {
    window: contextWindow,
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(SOURCE, ctx, { filename: 'assets/blindspots.js' });
  const rows = ctx.window.CnmBlind.list({ subject: 'math' });
  assert.equal(rows.length, 1);
  assert.equal(rows[0].id, 'cnm_300');
  assert.equal(rows[0].source, 'child');
});

console.log('\n' + passed + ' passed');
