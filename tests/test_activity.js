#!/usr/bin/env node
/* 学习打卡：node tests/test_activity.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

function load() {
  const store = new Map();
  const ctx = { window: {}, localStorage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/activity.js'), 'utf8'), ctx);
  return { A: ctx.window.CnmActivity, store };
}
const plain = (v) => JSON.parse(JSON.stringify(v));
const at = (y, m, d, h) => new Date(y, m - 1, d, h == null ? 12 : h).getTime();

test('mark 记本地日期、同一天去重、结果排序', () => {
  const { A, store } = load();
  A.mark('c1', at(2026, 11, 23, 8));
  A.mark('c1', at(2026, 11, 23, 22));
  A.mark('c1', at(2026, 11, 21));
  assert.deepStrictEqual(JSON.parse(store.get('cnmActivity.v1')).c1, ['2026-11-21', '2026-11-23']);
  assert.deepStrictEqual(plain(A.dates('c1')), ['2026-11-21', '2026-11-23']);
});

test('没有孩子 id 记到 guest；各孩子互不影响', () => {
  const { A } = load();
  A.mark(null, at(2026, 11, 23));
  A.mark('c2', at(2026, 11, 22));
  assert.deepStrictEqual(plain(A.dates('guest')), ['2026-11-23']);
  assert.deepStrictEqual(plain(A.dates(undefined)), ['2026-11-23']);
  assert.deepStrictEqual(plain(A.dates('c2')), ['2026-11-22']);
  assert.strictEqual(A.hasAny('c3'), false);
  assert.strictEqual(A.hasAny('guest'), true);
});

test('streak：今天学了就从今天数，连续多天', () => {
  const { A } = load();
  [21, 22, 23].forEach((d) => A.mark('c1', at(2026, 11, d)));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23, 20)), 3);
});

test('streak：昨天学过、今天还没学，仍保链', () => {
  const { A } = load();
  [21, 22].forEach((d) => A.mark('c1', at(2026, 11, d)));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23, 9)), 2);
});

test('streak：断一天就重置（前天学过、昨天没学 → 0；断后重新开始只算新的一段）', () => {
  const { A } = load();
  A.mark('c1', at(2026, 11, 21));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 0);
  A.mark('c1', at(2026, 11, 23));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 1);
  [18, 19, 20].forEach((d) => A.mark('c1', at(2026, 11, d)));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 1, '19–21 连着但 22 断了');
});

test('streak：跨月、跨年都连得上', () => {
  const { A } = load();
  [[2026, 10, 30], [2026, 10, 31], [2026, 11, 1], [2026, 11, 2]].forEach(([y, m, d]) => A.mark('c1', at(y, m, d)));
  assert.strictEqual(A.streak('c1', at(2026, 11, 2)), 4);
  const b = load().A;
  [[2026, 12, 30], [2026, 12, 31], [2027, 1, 1]].forEach(([y, m, d]) => b.mark('c1', at(y, m, d)));
  assert.strictEqual(b.streak('c1', at(2027, 1, 1)), 3);
  const c = load().A;
  [[2028, 2, 28], [2028, 2, 29], [2028, 3, 1]].forEach(([y, m, d]) => c.mark('c1', at(y, m, d)));
  assert.strictEqual(c.streak('c1', at(2028, 3, 1)), 3, '闰日');
});

test('没有数据 / 数据损坏时 streak 为 0 且不抛错', () => {
  const { A, store } = load();
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 0);
  store.set('cnmActivity.v1', '{坏');
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 0);
  store.set('cnmActivity.v1', JSON.stringify({ c1: ['bad', 5, '2026-11-23'] }));
  assert.strictEqual(A.streak('c1', at(2026, 11, 23)), 1);
});

console.log(passed + ' passed');
