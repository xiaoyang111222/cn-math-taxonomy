#!/usr/bin/env node
/* 每日一句进度与学习打卡的云同步合并，以及打卡接入点：node tests/test_english_sync.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.join(__dirname, '..');
const S = require(path.join(ROOT, 'assets/sync.js'));
const read = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8');
let passed = 0;
const queue = [];
function test(name, fn) { queue.push({ name, fn }); }
const CTX = { remoteAt: 0, localAt: 0, now: 1 };
const OK = { guess: true, order: true, build: true };
const done = (at) => ({ at, checks: OK });

test('同步数据集清单含 english / activity，键名与存储一致', () => {
  assert.deepStrictEqual({ ...S.DATASETS }, {
    children: 'cnmChildren.v1', records: 'cnmChildren.records.v1', wrongbook: 'cnmWrong.v1', finals: 'cnmFinals.v1',
    english: 'cnmEnglish.v1', activity: 'cnmActivity.v1'
  });
  assert.deepStrictEqual(Array.from(S.NAMES), Object.keys(S.DATASETS));
  const ctx = { window: {}, localStorage: { getItem: () => null, setItem() {} } };
  vm.runInNewContext(read('assets/english.js'), ctx);
  vm.runInNewContext(read('assets/activity.js'), ctx);
  assert.strictEqual(ctx.window.CnmEnglish.KEY, S.DATASETS.english);
  assert.strictEqual(ctx.window.CnmActivity.KEY, S.DATASETS.activity);
  assert.deepStrictEqual(Array.from(ctx.window.CnmEnglish.OFFSETS), Array.from(S.ENGLISH_OFFSETS));
});

test('english：两台设备学了不同的天 → 取并集', () => {
  const a = { c1: { done: { 1: done(1000), 2: done(2000) }, reviews: { 1: { dueOrd: 3, doneOrds: [] }, 2: { dueOrd: 4, doneOrds: [] } } } };
  const b = { c1: { done: { 1: done(1000), 3: done(3000) }, reviews: { 1: { dueOrd: 3, doneOrds: [] }, 3: { dueOrd: 5, doneOrds: [] } } }, c2: { done: { 1: done(5) }, reviews: {} } };
  const m = S.mergeEnglish(a, b, undefined, CTX);
  assert.deepStrictEqual(Object.keys(m.c1.done).sort(), ['1', '2', '3']);
  assert.deepStrictEqual(Object.keys(m.c1.reviews).sort(), ['1', '2', '3']);
  assert.ok(m.c2.done['1']);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeEnglish(b, a, undefined, CTX))), JSON.parse(JSON.stringify(m)), '合并与顺序无关');
});

test('english：同一天两边都学了，取 at 晚者；相同取本地', () => {
  const a = { g: { done: { 1: { at: 1000, checks: OK, mark: 'a' } }, reviews: {} } };
  const b = { g: { done: { 1: { at: 2000, checks: OK, mark: 'b' } }, reviews: {} } };
  assert.strictEqual(S.mergeEnglish(a, b).g.done['1'].mark, 'b');
  assert.strictEqual(S.mergeEnglish(b, a).g.done['1'].mark, 'b');
  const c = { g: { done: { 1: { at: 1000, checks: OK, mark: 'c' } }, reviews: {} } };
  assert.strictEqual(S.mergeEnglish(a, c).g.done['1'].mark, 'a');
});

test('english：reviews 取并集——一台做过第 1 轮、另一台做过前两轮 → 合并后两轮都算做过，下一轮到期序号按 n0 重算', () => {
  const a = { g: { done: { 1: done(1) }, reviews: { 1: { dueOrd: 5, doneOrds: [3] } } } };
  const b = { g: { done: { 1: done(1) }, reviews: { 1: { dueOrd: 8, doneOrds: [3, 5] } } } };
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeEnglish(a, b).g.reviews['1'])), { dueOrd: 8, doneOrds: [3, 5] });
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeEnglish(b, a).g.reviews['1'])), { dueOrd: 8, doneOrds: [3, 5] });
  const full = { g: { done: { 1: done(1) }, reviews: { 1: { dueOrd: null, doneOrds: [3, 5, 8, 16] } } } };
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeEnglish(a, full).g.reviews['1'])), { dueOrd: null, doneOrds: [3, 5, 8, 16] });
});

test('english：没有云端数据时保留本地；两边都空 → null；不改动入参', () => {
  const a = { g: { done: { 1: done(1) }, reviews: { 1: { dueOrd: 3, doneOrds: [] } } } };
  const snap = JSON.stringify(a);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeDataset('english', a, undefined, undefined, CTX))), a);
  assert.strictEqual(S.mergeDataset('english', null, null, undefined, CTX), null);
  assert.strictEqual(JSON.stringify(a), snap);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeDataset('english', null, a, undefined, CTX))), a);
});

test('activity：日期取并集、去重、排序；各桶分开；坏数据被丢掉', () => {
  const a = { c1: ['2026-11-21', '2026-11-23'], guest: ['2026-11-01'] };
  const b = { c1: ['2026-11-22', '2026-11-23', 'bad', 5], c2: ['2026-10-31'] };
  const m = S.mergeActivity(a, b, undefined, CTX);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(m)), { c1: ['2026-11-21', '2026-11-22', '2026-11-23'], guest: ['2026-11-01'], c2: ['2026-10-31'] });
  assert.strictEqual(S.mergeDataset('activity', null, undefined, undefined, CTX), null);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(S.mergeDataset('activity', a, null, undefined, CTX))), a);
});

test('引擎：两台设备的英语进度与打卡经假云端合并后一致', async () => {
  const cloud = new Map();
  let clock = 1000;
  function device(initial) {
    const store = new Map(Object.entries(initial));
    const api = async (method, p, body) => {
      if (method === 'GET') {
        const datasets = {};
        cloud.forEach((v, k) => { datasets[k] = v; });
        return { status: 200, data: { datasets } };
      }
      const name = p.split('/').pop();
      const cur = cloud.get(name);
      if ((cur ? cur.updated_at : null) !== (body.base_updated_at || null)) return { status: 409, data: cur };
      const row = { payload: body.payload, updated_at: ++clock };
      cloud.set(name, row);
      return { status: 200, data: { updated_at: row.updated_at } };
    };
    const engine = S.createEngine({ storage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, v), removeItem: (k) => store.delete(k) }, api, now: () => 5000, setTimer: () => 0, clearTimer: () => {} });
    engine.begin('a@b.c');
    return { engine, store };
  }
  const d1 = device({
    'cnmEnglish.v1': JSON.stringify({ g: { done: { 1: done(1000) }, reviews: { 1: { dueOrd: 3, doneOrds: [] } } } }),
    'cnmActivity.v1': JSON.stringify({ g: ['2026-11-21'] })
  });
  const d2 = device({
    'cnmEnglish.v1': JSON.stringify({ g: { done: { 2: done(2000) }, reviews: { 2: { dueOrd: 4, doneOrds: [] } } } }),
    'cnmActivity.v1': JSON.stringify({ g: ['2026-11-22'] })
  });
  await d1.engine.syncAll();
  await d2.engine.syncAll();
  await d1.engine.syncAll();
  const en1 = JSON.parse(d1.store.get('cnmEnglish.v1'));
  const en2 = JSON.parse(d2.store.get('cnmEnglish.v1'));
  assert.deepStrictEqual(Object.keys(en1.g.done).sort(), ['1', '2']);
  assert.deepStrictEqual(en1, en2);
  assert.deepStrictEqual(JSON.parse(d1.store.get('cnmActivity.v1')).g, ['2026-11-21', '2026-11-22']);
  assert.deepStrictEqual(JSON.parse(d2.store.get('cnmActivity.v1')), JSON.parse(d1.store.get('cnmActivity.v1')));
});

test('打卡接入点：每日一句完成、错题复测通过、诊断结果首次存档，三处都引入 activity.js', () => {
  assert.ok(/updated && passed && window\.CnmActivity[^\n]*mark\(childId/.test(read('wrongbook/wrongbook.js')), '复测通过');
  assert.ok(/CC\.saveRecord\(cur\.id, rec\);\s*if \(firstSave && window\.CnmActivity\) window\.CnmActivity\.mark\(cur\.id\)/.test(read('diagnose/app.js')), '诊断完成');
  assert.ok(/window\.CnmActivity\.mark\(childId, t\)/.test(read('assets/english.js')), '每日一句完成');
  ['english/index.html', 'wrongbook/index.html', 'diagnose/index.html'].forEach((f) => {
    assert.ok(read(f).includes('assets/activity.js'), f);
  });
});

(async () => {
  for (const t of queue) { await t.fn(); passed++; console.log('  ok   ' + t.name); }
  console.log(passed + ' passed');
})().catch((e) => { console.error(e); process.exit(1); });
