#!/usr/bin/env node
/* 错题本存储测试：node tests/test_wrongbook.js（无依赖，不访问真实浏览器存储）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SOURCE = fs.readFileSync(path.join(__dirname, '../assets/wrongbook.js'), 'utf8');
const KEY = 'cnmWrong.v1';
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function load(entries, options = {}) {
  const storage = new Map(Object.entries(entries || {}));
  const context = {
    window: {},
    localStorage: {
      getItem(key) {
        if (options.failRead) throw new Error('Storage access denied');
        return storage.has(key) ? storage.get(key) : null;
      },
      setItem(key, value) {
        if (options.failWrite) throw new Error('QuotaExceededError');
        storage.set(key, value);
      },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(SOURCE, context, { filename: 'assets/wrongbook.js' });
  return { api: context.window.CnmWrong, storage };
}

function entry(qid, extra) {
  return Object.assign({
    childId: 'c1', qid, topicId: 'cnm_001', topic: '加法', subject: 'math',
    prompt: '1+1=?', choices: null, answer: '2', explanation: '', chosen: '3', kind: 'wrong', ts: 1000
  }, extra || {});
}
function saved(storage) { return JSON.parse(storage.get(KEY)); }

test('空库时 list / count 为空', () => {
  const { api } = load();
  assert.equal(api.list('c1').length, 0);
  assert.equal(api.count('c1'), 0);
  assert.equal(api.count(), 0);
});

test('record 新增一条，字段完整且不把 childId 存进条目', () => {
  const { api, storage } = load();
  const ok = api.record(entry('q1', {
    choices: [{ key: 'A', text: '2' }, { key: 'B', text: '3' }], explanation: '一加一', kind: 'skip', chosen: ''
  }));
  assert.equal(ok, true);
  const rows = api.list('c1');
  assert.equal(rows.length, 1);
  const e = rows[0];
  assert.equal(e.qid, 'q1');
  assert.equal(e.topicId, 'cnm_001');
  assert.equal(e.topic, '加法');
  assert.equal(e.subject, 'math');
  assert.equal(e.prompt, '1+1=?');
  assert.equal(e.choices.length, 2);
  assert.equal(e.choices[1].key, 'B');
  assert.equal(e.answer, '2');
  assert.equal(e.explanation, '一加一');
  assert.equal(e.kind, 'skip');
  assert.equal(e.ts, 1000);
  assert.equal(e.count, 1);
  assert.ok(!('childId' in e));
  assert.ok(!('childId' in saved(storage).c1[0]));
});

test('没有 qid 的条目被拒绝；没有 childId 记到 guest', () => {
  const { api } = load();
  assert.equal(api.record({ prompt: 'x' }), false);
  assert.equal(api.record(null), false);
  api.record(entry('q1', { childId: undefined }));
  assert.equal(api.count('guest'), 1);
  assert.equal(api.count(), 1);
  assert.equal(api.count('c1'), 0);
});

test('同一孩子同一 qid 去重：更新 chosen / kind / ts，count + 1', () => {
  const { api } = load();
  api.record(entry('q1', { ts: 1000, chosen: '3', kind: 'wrong' }));
  api.record(entry('q1', { ts: 2000, chosen: '', kind: 'skip' }));
  api.record(entry('q1', { ts: 3000, chosen: '5', kind: 'wrong' }));
  const rows = api.list('c1');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].count, 3);
  assert.equal(rows[0].chosen, '5');
  assert.equal(rows[0].kind, 'wrong');
  assert.equal(rows[0].ts, 3000);
});

test('list 按最近答错倒序', () => {
  const { api } = load();
  api.record(entry('q1', { ts: 1000 }));
  api.record(entry('q2', { ts: 3000 }));
  api.record(entry('q3', { ts: 2000 }));
  assert.equal(api.list('c1').map((e) => e.qid).join(','), 'q2,q3,q1');
  api.record(entry('q1', { ts: 4000 }));
  assert.equal(api.list('c1')[0].qid, 'q1');
});

test('每桶上限 300 条，超了丢最旧', () => {
  const { api } = load();
  for (let i = 1; i <= 305; i++) api.record(entry('q' + i, { ts: i }));
  const rows = api.list('c1');
  assert.equal(rows.length, 300);
  assert.equal(api.count('c1'), 300);
  assert.equal(rows[0].qid, 'q305');
  assert.equal(rows[299].qid, 'q6');
  assert.ok(!rows.some((e) => e.qid === 'q1' || e.qid === 'q5'));
});

test('更新旧条目会让它变新，不被上限淘汰', () => {
  const { api } = load();
  for (let i = 1; i <= 300; i++) api.record(entry('q' + i, { ts: i }));
  api.record(entry('q1', { ts: 1000 }));
  api.record(entry('q301', { ts: 1001 }));
  const ids = api.list('c1').map((e) => e.qid);
  assert.equal(ids.length, 300);
  assert.ok(ids.indexOf('q1') >= 0);
  assert.ok(ids.indexOf('q2') < 0);
});

test('remove 只删指定 qid', () => {
  const { api } = load();
  api.record(entry('q1'));
  api.record(entry('q2'));
  assert.equal(api.remove('c1', 'q1'), true);
  assert.equal(api.list('c1').map((e) => e.qid).join(','), 'q2');
  assert.equal(api.remove('c1', 'nope'), false);
  assert.equal(api.count('c1'), 1);
});

test('clear 只清指定孩子', () => {
  const { api } = load();
  api.record(entry('q1', { childId: 'c1' }));
  api.record(entry('q2', { childId: 'c2' }));
  api.clear('c1');
  assert.equal(api.count('c1'), 0);
  assert.equal(api.count('c2'), 1);
});

test('不同孩子互相隔离，同一 qid 各记各的', () => {
  const { api } = load();
  api.record(entry('q1', { childId: 'c1' }));
  api.record(entry('q1', { childId: 'c1' }));
  api.record(entry('q1', { childId: 'c2' }));
  api.record(entry('q9', { childId: undefined }));
  assert.equal(api.list('c1')[0].count, 2);
  assert.equal(api.list('c2')[0].count, 1);
  assert.equal(api.count('c1'), 1);
  assert.equal(api.count('c2'), 1);
  assert.equal(api.count('guest'), 1);
  api.remove('c2', 'q1');
  assert.equal(api.count('c1'), 1);
});

test('存储损坏时不抛错并返回空结构', () => {
  for (const bad of ['{not json', '[1,2]', '"x"', '123', 'null', '{"c1":"oops"}', '{"c1":[null,5,{"prompt":"no qid"}]}']) {
    const { api } = load({ [KEY]: bad });
    assert.equal(api.list('c1').length, 0, bad);
    assert.equal(api.count('c1'), 0, bad);
    assert.equal(api.remove('c1', 'q1'), false, bad);
    assert.doesNotThrow(() => api.clear('c1'), bad);
    assert.equal(api.record(entry('q1')), true, bad);
    assert.equal(api.count('c1'), 1, bad);
  }
});

test('localStorage 读写抛错时不抛错', () => {
  const r = load({}, { failRead: true });
  assert.equal(r.api.list('c1').length, 0);
  assert.doesNotThrow(() => r.api.record(entry('q1')));
  const w = load({}, { failWrite: true });
  assert.equal(w.api.record(entry('q1')), false);
  assert.equal(w.api.count('c1'), 0);
  assert.doesNotThrow(() => w.api.clear('c1'));
});

console.log('\n' + passed + ' passed');
