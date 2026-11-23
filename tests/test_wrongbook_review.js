#!/usr/bin/env node
/* 错题到期复测测试：node tests/test_wrongbook_review.js（无依赖，不访问真实浏览器存储）。
 * 覆盖 assets/wrongbook.js 的到期规则与 review，assets/sync.js 合并时保住复测进度，以及诊断页 childBar 判空。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'assets/wrongbook.js'), 'utf8');
const S = require(path.join(ROOT, 'assets/sync.js'));
const KEY = 'cnmWrong.v1';
const DAY = 24 * 60 * 60 * 1000;
const T0 = Date.parse('2026-11-23T08:00:00Z');
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function load(initial) {
  const storage = new Map();
  if (initial) storage.set(KEY, JSON.stringify(initial));
  const context = {
    window: {},
    localStorage: {
      getItem: (k) => (storage.has(k) ? storage.get(k) : null),
      setItem: (k, v) => { storage.set(k, v); },
      removeItem: (k) => { storage.delete(k); }
    }
  };
  vm.runInNewContext(SOURCE, context, { filename: 'assets/wrongbook.js' });
  return { api: context.window.CnmWrong, storage };
}

function entry(qid, extra) {
  return Object.assign({
    childId: 'c1', qid, topicId: 'cnm_001', topic: '加法', subject: 'math',
    prompt: '1+1=?', choices: null, answer: '2', explanation: '', chosen: '3', kind: 'wrong', ts: T0
  }, extra || {});
}
function legacy(qid, ts, extra) {
  return Object.assign({
    qid, topicId: 'cnm_001', topic: '加法', subject: 'math', prompt: 'p', choices: null,
    answer: '2', explanation: '', chosen: '3', kind: 'wrong', ts, count: 1
  }, extra || {});
}
function saved(storage) { return JSON.parse(storage.get(KEY)); }

test('复测间隔常量为 1 / 3 / 7 / 15 天（与 api/lib.js 的一致性由 test_digest.js 核对）', () => {
  const { api } = load();
  assert.deepStrictEqual(Array.from(api.INTERVALS_DAYS), [1, 3, 7, 15]);
});

test('新条目：stage 0、dueAt = ts + 1 天、done false；明天到期，今天不到期', () => {
  const { api, storage } = load();
  api.record(entry('q1'));
  const row = saved(storage).c1[0];
  assert.strictEqual(row.stage, 0);
  assert.strictEqual(row.dueAt, T0 + DAY);
  assert.strictEqual(row.done, false);
  assert.deepStrictEqual(Array.from(api.dueList('c1', T0 + DAY - 1).map((e) => e.qid)), []);
  assert.deepStrictEqual(Array.from(api.dueList('c1', T0 + DAY).map((e) => e.qid)), ['q1']);
  assert.deepStrictEqual(Array.from(api.dueList('c1', T0).map((e) => e.qid)), []);
  assert.strictEqual(api.dueTotal(T0 + DAY), 1);
  assert.strictEqual(api.dueTotal(T0), 0);
});

test('老条目（无 stage / dueAt / done）按 ts + 1 天到期，并按 dueAt 升序', () => {
  const { api } = load({ c1: [legacy('q-new', T0), legacy('q-old', T0 - 10 * DAY)] });
  assert.deepStrictEqual(Array.from(api.dueList('c1', T0).map((e) => e.qid)), ['q-old']);
  assert.deepStrictEqual(Array.from(api.dueList('c1', T0 + DAY).map((e) => e.qid)), ['q-old', 'q-new']);
});

test('通过一次推进一轮：间隔依次 3 → 7 → 15 天', () => {
  const { api } = load();
  api.record(entry('q1'));
  let now = T0 + DAY;
  let e = api.review('c1', 'q1', true, now);
  assert.strictEqual(e.stage, 1);
  assert.strictEqual(e.dueAt, now + 3 * DAY);
  assert.strictEqual(e.done, false);
  now = e.dueAt;
  e = api.review('c1', 'q1', true, now);
  assert.strictEqual(e.stage, 2);
  assert.strictEqual(e.dueAt, now + 7 * DAY);
  now = e.dueAt;
  e = api.review('c1', 'q1', true, now);
  assert.strictEqual(e.stage, 3);
  assert.strictEqual(e.dueAt, now + 15 * DAY);
  assert.strictEqual(e.done, false);
  assert.strictEqual(api.dueList('c1', now + 15 * DAY - 1).length, 0);
  assert.strictEqual(api.dueList('c1', now + 15 * DAY).length, 1);
});

test('老条目通过后同样走 stage 0 → 1', () => {
  const { api } = load({ c1: [legacy('q1', T0)] });
  const e = api.review('c1', 'q1', true, T0 + DAY);
  assert.strictEqual(e.stage, 1);
  assert.strictEqual(e.dueAt, T0 + DAY + 3 * DAY);
});

test('stage 3 通过后毕业：done、清除到期、不再到期，条目仍在列表里', () => {
  const { api, storage } = load();
  api.record(entry('q1'));
  api.review('c1', 'q1', true, T0 + DAY);
  api.review('c1', 'q1', true, T0 + 5 * DAY);
  api.review('c1', 'q1', true, T0 + 13 * DAY);
  const e = api.review('c1', 'q1', true, T0 + 30 * DAY);
  assert.strictEqual(e.done, true);
  assert.strictEqual(e.stage, 3);
  assert.ok(!('dueAt' in e));
  assert.strictEqual(api.dueList('c1', T0 + 3650 * DAY).length, 0);
  assert.strictEqual(api.dueTotal(T0 + 3650 * DAY), 0);
  assert.strictEqual(saved(storage).c1.length, 1);
  assert.strictEqual(api.list('c1').length, 1);
  assert.strictEqual(api.reviewLabel(e, T0 + 31 * DAY), '已毕业 ✓');
});

test('未过：stage 不变，dueAt = now + 1 天', () => {
  const { api } = load();
  api.record(entry('q1'));
  api.review('c1', 'q1', true, T0 + DAY);
  const mid = api.review('c1', 'q1', true, T0 + 5 * DAY);
  assert.strictEqual(mid.stage, 2);
  const now = T0 + 12 * DAY;
  const e = api.review('c1', 'q1', false, now);
  assert.strictEqual(e.stage, 2);
  assert.strictEqual(e.dueAt, now + DAY);
  assert.strictEqual(e.done, false);
});

test('再次答错：stage 回 0、dueAt = 新 ts + 1 天、done 清掉、count + 1', () => {
  const { api } = load();
  api.record(entry('q1'));
  api.review('c1', 'q1', true, T0 + DAY);
  api.review('c1', 'q1', true, T0 + 5 * DAY);
  api.review('c1', 'q1', true, T0 + 13 * DAY);
  api.review('c1', 'q1', true, T0 + 30 * DAY);
  assert.strictEqual(api.list('c1')[0].done, true);
  const again = T0 + 40 * DAY;
  api.record(entry('q1', { ts: again, chosen: '5' }));
  const e = api.list('c1')[0];
  assert.strictEqual(e.stage, 0);
  assert.strictEqual(e.dueAt, again + DAY);
  assert.strictEqual(e.done, false);
  assert.strictEqual(e.count, 2);
  assert.strictEqual(e.ts, again);
  assert.strictEqual(api.dueList('c1', again + DAY).length, 1);
});

test('review 找不到条目返回 null；已毕业条目不被改动；不同孩子互不影响', () => {
  const { api } = load();
  assert.strictEqual(api.review('c1', 'nope', true, T0), null);
  api.record(entry('q1'));
  api.record(entry('q1', { childId: 'c2' }));
  api.review('c1', 'q1', true, T0 + DAY);
  assert.strictEqual(api.list('c1')[0].stage, 1);
  assert.strictEqual(api.list('c2')[0].stage, 0);
  assert.strictEqual(api.review('c3', 'q1', true, T0), null);
  api.review('c2', 'q1', true, T0 + DAY);
  api.review('c2', 'q1', true, T0 + 5 * DAY);
  api.review('c2', 'q1', true, T0 + 13 * DAY);
  api.review('c2', 'q1', true, T0 + 30 * DAY);
  const g = api.review('c2', 'q1', false, T0 + 40 * DAY);
  assert.strictEqual(g.done, true);
  assert.strictEqual(g.stage, 3);
  assert.ok(!('dueAt' in g));
});

test('reviewLabel：已到期 / 下次复测日期 / 已毕业', () => {
  const { api } = load();
  api.record(entry('q1'));
  const e0 = api.list('c1')[0];
  assert.strictEqual(api.reviewLabel(e0, T0 + DAY), '第 1 轮 · 已到期');
  const e1 = api.review('c1', 'q1', true, T0 + DAY);
  const d = new Date(e1.dueAt);
  assert.strictEqual(api.reviewLabel(e1, T0 + DAY), '下次复测 ' + (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日');
  assert.strictEqual(api.reviewLabel(e1, e1.dueAt), '第 2 轮 · 已到期');
});

test('answerKey 取选择题答案里的选项 key', () => {
  const { api } = load();
  assert.strictEqual(api.answerKey({ answer: 'B. 3.5' }), 'B');
  assert.strictEqual(api.answerKey({ answer: '12' }), '12');
});

/* ------------------------------------------------------------ 同步合并 */

const CTX = { remoteAt: 0, localAt: 0, now: T0 };
const merge = (a, b) => S.mergeWrongbook(a, b, undefined, CTX).c1[0];

test('mergeWrongbook：已毕业不被旧副本覆盖（两个方向）', () => {
  const grad = legacy('q1', T0, { stage: 3, done: true });
  const stale = legacy('q1', T0 + 1000, { stage: 0, dueAt: T0 + DAY + 1000, done: false });
  [merge({ c1: [grad] }, { c1: [stale] }), merge({ c1: [stale] }, { c1: [grad] })].forEach((m) => {
    assert.strictEqual(m.done, true);
    assert.strictEqual(m.stage, 3);
    assert.ok(!('dueAt' in m));
    assert.strictEqual(m.ts, T0 + 1000, 'ts 沿用较新者');
  });
});

test('mergeWrongbook：stage 高者胜，不被较新 ts 的低 stage 副本冲掉', () => {
  const high = legacy('q1', T0, { stage: 2, dueAt: T0 + 9 * DAY, done: false });
  const low = legacy('q1', T0 + 5000, { stage: 1, dueAt: T0 + 20 * DAY, done: false });
  [merge({ c1: [high] }, { c1: [low] }), merge({ c1: [low] }, { c1: [high] })].forEach((m) => {
    assert.strictEqual(m.stage, 2);
    assert.strictEqual(m.dueAt, T0 + 9 * DAY);
    assert.strictEqual(m.ts, T0 + 5000);
  });
});

test('mergeWrongbook：同 stage 取 dueAt 晚者；带进度的一方胜过缺省字段的老副本', () => {
  const a = legacy('q1', T0, { stage: 1, dueAt: T0 + 3 * DAY, done: false });
  const b = legacy('q1', T0, { stage: 1, dueAt: T0 + 4 * DAY, done: false });
  assert.strictEqual(merge({ c1: [a] }, { c1: [b] }).dueAt, T0 + 4 * DAY);
  assert.strictEqual(merge({ c1: [b] }, { c1: [a] }).dueAt, T0 + 4 * DAY);
  const old = legacy('q1', T0 + 9000);
  const m = merge({ c1: [old] }, { c1: [a] });
  assert.strictEqual(m.stage, 1);
  assert.strictEqual(m.dueAt, T0 + 3 * DAY);
  assert.strictEqual(S.mergeWrongbook({ c1: [a] }, { c1: [old] }, undefined, CTX).c1[0].stage, 1);
});

test('mergeWrongbook：两边都没有复测字段时保持原样，不凭空加字段', () => {
  const a = legacy('q1', T0);
  const b = legacy('q1', T0 + 1000, { chosen: 'C', count: 2 });
  const m = merge({ c1: [a] }, { c1: [b] });
  assert.strictEqual(m.chosen, 'C');
  assert.strictEqual(m.count, 2);
  assert.ok(!('stage' in m) && !('dueAt' in m) && !('done' in m));
});

test('mergeWrongbook：两边一致时原样返回', () => {
  const a = legacy('q1', T0, { stage: 2, dueAt: T0 + 7 * DAY, done: false });
  assert.deepStrictEqual(merge({ c1: [a] }, { c1: [Object.assign({}, a)] }), a);
});

test('dueBuckets：只数有到期题的桶；dueTotal 是各桶之和', () => {
  const { api } = load();
  api.record(entry('q1'));
  api.record(entry('q2'));
  api.record(entry('q1', { childId: 'c2' }));
  api.record(entry('q9', { childId: 'c3', ts: T0 + 10 * DAY }));
  assert.strictEqual(api.dueTotal(T0 + DAY), 3);
  assert.strictEqual(api.dueBuckets(T0 + DAY), 2);
  assert.strictEqual(api.dueBuckets(T0), 0);
  assert.strictEqual(api.dueBuckets(T0 + 11 * DAY), 3);
});

/* ------------------------------------------------------------ reviewedAt：谁的复测进度更新 */

test('record / review 都会更新 reviewedAt（再次答错取新 ts，复测取 now，已毕业的不动）', () => {
  const { api } = load();
  api.record(entry('q1'));
  assert.strictEqual(api.list('c1')[0].reviewedAt, T0);
  assert.strictEqual(api.review('c1', 'q1', true, T0 + DAY).reviewedAt, T0 + DAY);
  assert.strictEqual(api.review('c1', 'q1', false, T0 + 5 * DAY).reviewedAt, T0 + 5 * DAY, '未过也算一次复测');
  api.record(entry('q1', { ts: T0 + 6 * DAY }));
  assert.strictEqual(api.list('c1')[0].reviewedAt, T0 + 6 * DAY);
  [T0 + 7 * DAY, T0 + 9 * DAY, T0 + 13 * DAY, T0 + 30 * DAY].forEach((t) => api.review('c1', 'q1', true, t));
  const g = api.review('c1', 'q1', true, T0 + 99 * DAY);
  assert.strictEqual(g.done, true);
  assert.strictEqual(g.reviewedAt, T0 + 30 * DAY, '已毕业再点不改动');
});

test('mergeWrongbook：一台已毕业、另一台之后又答错回炉，回炉不被毕业盖掉（两个方向）', () => {
  const grad = legacy('q1', T0, { stage: 3, done: true, reviewedAt: T0 + 20 * DAY });
  const relapse = legacy('q1', T0 + 25 * DAY, { count: 2, stage: 0, dueAt: T0 + 26 * DAY, done: false, reviewedAt: T0 + 25 * DAY });
  [merge({ c1: [grad] }, { c1: [relapse] }), merge({ c1: [relapse] }, { c1: [grad] })].forEach((m) => {
    assert.strictEqual(m.done, false);
    assert.strictEqual(m.stage, 0);
    assert.strictEqual(m.dueAt, T0 + 26 * DAY);
    assert.strictEqual(m.reviewedAt, T0 + 25 * DAY);
    assert.strictEqual(m.count, 2);
  });
});

test('mergeWrongbook：旧副本不覆盖新进度，即使旧副本 stage 更高或已毕业（两个方向）', () => {
  const fresh = legacy('q1', T0, { stage: 1, dueAt: T0 + 40 * DAY, done: false, reviewedAt: T0 + 37 * DAY });
  const staleHigh = legacy('q1', T0, { stage: 2, dueAt: T0 + 50 * DAY, done: false, reviewedAt: T0 + 30 * DAY });
  const staleGrad = legacy('q1', T0, { stage: 3, done: true, reviewedAt: T0 + 30 * DAY });
  [staleHigh, staleGrad].forEach((stale) => {
    [merge({ c1: [fresh] }, { c1: [stale] }), merge({ c1: [stale] }, { c1: [fresh] })].forEach((m) => {
      assert.strictEqual(m.stage, 1);
      assert.strictEqual(m.done, false);
      assert.strictEqual(m.dueAt, T0 + 40 * DAY);
      assert.strictEqual(m.reviewedAt, T0 + 37 * DAY);
    });
  });
});

test('mergeWrongbook：较新的一次「没过」复测不被另一台 dueAt 更晚的旧进度盖掉', () => {
  const passed = legacy('q1', T0, { stage: 1, dueAt: T0 + 13 * DAY, done: false, reviewedAt: T0 + 10 * DAY });
  const failed = legacy('q1', T0, { stage: 1, dueAt: T0 + 12 * DAY, done: false, reviewedAt: T0 + 11 * DAY });
  [merge({ c1: [passed] }, { c1: [failed] }), merge({ c1: [failed] }, { c1: [passed] })].forEach((m) => {
    assert.strictEqual(m.dueAt, T0 + 12 * DAY);
    assert.strictEqual(m.reviewedAt, T0 + 11 * DAY);
  });
});

test('mergeWrongbook：没有 reviewedAt 的老副本仍按 done > stage > dueAt 比较，且一边有一边没有时同样', () => {
  const withAt = legacy('q1', T0, { stage: 1, dueAt: T0 + 3 * DAY, done: false, reviewedAt: T0 + DAY });
  const without = legacy('q1', T0, { stage: 2, dueAt: T0 + 9 * DAY, done: false });
  assert.strictEqual(merge({ c1: [withAt] }, { c1: [without] }).stage, 2);
  assert.strictEqual(merge({ c1: [without] }, { c1: [withAt] }).stage, 2);
});

/* ------------------------------------------------------------ 顺手修的 bug */

test('诊断页：childBar 在演示模式返回 null，三处调用都不能直接 append(null)', () => {
  const src = fs.readFileSync(path.join(ROOT, 'diagnose/app.js'), 'utf8');
  assert.ok(/function childBar\(mode\) \{\s*if \(demo\) return null;/.test(src), 'childBar 演示模式仍返回 null');
  assert.ok(!/append\(childBar\(/.test(src), '不能把 childBar() 直接 append');
  ['start', 'question', 'result'].forEach((mode) => {
    const re = new RegExp("const bar = childBar\\('" + mode + "'\\);\\s*if \\(bar\\) page\\.append\\(bar\\);");
    assert.ok(re.test(src), 'childBar(' + mode + ') 需要判空');
  });
});

console.log(passed + ' passed');
