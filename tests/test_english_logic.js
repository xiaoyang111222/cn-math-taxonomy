#!/usr/bin/env node
/* 英语每日一句的解锁、复习、打卡判定与周统计：node tests/test_english_logic.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

function load(withActivity) {
  const store = new Map();
  const ctx = { window: {}, localStorage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) } };
  const run = (f) => vm.runInNewContext(fs.readFileSync(path.join(__dirname, '..', f), 'utf8'), ctx);
  if (withActivity) run('assets/activity.js');
  run('assets/english.js');
  return { E: ctx.window.CnmEnglish, A: ctx.window.CnmActivity, store, raw: () => JSON.parse(store.get('cnmEnglish.v1') || '{}') };
}
const plain = (v) => JSON.parse(JSON.stringify(v));
const OK = { guess: true, order: true, build: true };
const at = (m, d, h) => new Date(2026, m - 1, d, h == null ? 10 : h).getTime();
/* 11 月 1 日起每天学一句：learn(E, n) 学完第 1..n 句，第 k 句在 11 月 k 日 */
function learn(E, child, n) {
  for (let k = 1; k <= n; k++) assert.ok(E.completeDay(child, k, OK, at(11, k)).ok, 'day ' + k);
}

test('新孩子：今天学第 1 句，没有复习，没学完', () => {
  const { E } = load();
  const st = E.todayState('c1', at(11, 1));
  assert.strictEqual(st.day, 1);
  assert.strictEqual(st.doneCount, 0);
  assert.strictEqual(st.completedToday, false);
  assert.strictEqual(st.finished, false);
  assert.deepStrictEqual(plain(st.reviews), []);
});

test('解锁按进度：断学多天不跳句，下一句永远是已完成数 + 1', () => {
  const { E } = load();
  learn(E, 'c1', 3);
  const later = E.todayState('c1', at(11, 20));
  assert.strictEqual(later.day, 4);
  assert.strictEqual(later.doneCount, 3);
  assert.strictEqual(later.completedToday, false);
});

test('一天只学一句：学完当天 day 仍是这句、nextDay 是明天的句子；不能再提前完成下一句', () => {
  const { E } = load();
  assert.ok(E.completeDay('c1', 1, OK, at(11, 1, 9)).ok);
  const st = E.todayState('c1', at(11, 1, 21));
  assert.strictEqual(st.completedToday, true);
  assert.strictEqual(st.day, 1);
  assert.strictEqual(st.nextDay, 2);
  assert.strictEqual(E.completeDay('c1', 2, OK, at(11, 1, 22)).error, 'today');
  assert.strictEqual(E.todayState('c1', at(11, 2, 8)).day, 2);
});

test('只能完成「下一句」：跳句和越界被拒绝；重复完成原样返回、不改时间', () => {
  const { E, raw } = load();
  assert.strictEqual(E.completeDay('c1', 3, OK, at(11, 1)).error, 'locked');
  assert.strictEqual(E.completeDay('c1', 0, OK, at(11, 1)).error, 'day');
  assert.strictEqual(E.completeDay('c1', 31, OK, at(11, 1)).error, 'day');
  E.completeDay('c1', 1, OK, at(11, 1));
  const again = E.completeDay('c1', 1, OK, at(11, 5));
  assert.ok(again.ok && again.already);
  assert.strictEqual(raw().c1.done['1'].at, at(11, 1));
});

test('三项打卡判定：猜出意思 + 排序正确 + 完成造句 全满才算完成', () => {
  const { E, raw } = load();
  assert.strictEqual(E.checksComplete(OK), true);
  [{ guess: true, order: true }, { guess: true, order: true, build: false }, { order: true, build: true }, {}, null, 'x'].forEach((c) => {
    assert.strictEqual(E.checksComplete(c), false, JSON.stringify(c));
  });
  assert.strictEqual(E.completeDay('c1', 1, { guess: true, order: true, build: false }, at(11, 1)).error, 'checks');
  assert.strictEqual(E.doneCount('c1'), 0);
  assert.strictEqual(raw().c1, undefined);
  assert.ok(E.completeDay('c1', 1, OK, at(11, 1)).ok);
  assert.deepStrictEqual(raw().c1.done['1'].checks, OK);
});

test('进度按孩子分，游客用 guest 桶', () => {
  const { E } = load();
  E.completeDay('c1', 1, OK, at(11, 1));
  E.completeDay(null, 1, OK, at(11, 1));
  E.completeDay(null, 2, OK, at(11, 2));
  assert.strictEqual(E.doneCount('c1'), 1);
  assert.strictEqual(E.doneCount('guest'), 2);
  assert.strictEqual(E.doneCount('c2'), 0);
  assert.strictEqual(E.hasProgress('c2'), false);
});

test('复习在完成序号 +2 / +4 / +7 / +15 到期：第 1 句在学到第 3、5、8、16 句那天', () => {
  const { E } = load();
  const dueDays = [];
  for (let k = 1; k <= 20; k++) {
    const t = at(11, k, 8);
    const st = E.todayState('c1', t);
    assert.strictEqual(st.day, k);
    const due1 = st.reviews.find((r) => r.day === 1);
    if (due1) {
      dueDays.push(k);
      assert.strictEqual(due1.stage, dueDays.length);
      assert.ok(E.completeReview('c1', 1));
    }
    assert.ok(E.completeDay('c1', k, OK, at(11, k, 9)).ok);
    st.reviews.filter((r) => r.day !== 1).forEach((r) => E.completeReview('c1', r.day));
  }
  assert.deepStrictEqual(dueDays, [3, 5, 8, 16]);
});

test('完成一次复习后当天不再到期；四轮完成后永不再到期', () => {
  const { E, raw } = load();
  learn(E, 'c1', 2);
  let st = E.todayState('c1', at(11, 3, 8));
  assert.deepStrictEqual(plain(st.reviews.map((r) => [r.day, r.stage])), [[1, 1]]);
  assert.ok(E.completeReview('c1', 1));
  assert.deepStrictEqual(raw().c1.reviews['1'], { dueOrd: 5, doneOrds: [3] });
  assert.strictEqual(E.todayState('c1', at(11, 3, 8)).reviews.length, 0);
  assert.ok(E.completeDay('c1', 3, OK, at(11, 3, 9)).ok);
  assert.strictEqual(E.todayState('c1', at(11, 3, 20)).reviews.some((r) => r.day === 1), false, '学完第 3 句当天也不会再冒出第 1 句');
  for (let k = 4; k <= 16; k++) assert.ok(E.completeDay('c1', k, OK, at(11, k)).ok);
  const clearOthers = () => {
    for (let guard = 0; guard < 200; guard++) {
      const others = E.todayState('c1', at(11, 17)).reviews.filter((x) => x.day !== 1);
      if (!others.length) return;
      others.forEach((x) => E.completeReview('c1', x.day));
    }
  };
  [5, 8, 16].forEach((due) => {
    clearOthers();
    const r = E.todayState('c1', at(11, 17)).reviews.find((x) => x.day === 1);
    assert.ok(r && r.dueOrd === due, 'dueOrd ' + due);
    assert.ok(E.completeReview('c1', 1));
  });
  assert.deepStrictEqual(raw().c1.reviews['1'], { dueOrd: null, doneOrds: [3, 5, 8, 16] });
  clearOthers();
  assert.strictEqual(E.todayState('c1', at(11, 17)).reviews.some((r) => r.day === 1), false);
  assert.strictEqual(E.completeReview('c1', 1), false);
  assert.strictEqual(E.completeReview('c1', 99), false);
});

test('复习不占新句名额，一天最多列 5 条', () => {
  const { E } = load();
  learn(E, 'c1', 14);
  const st = E.todayState('c1', at(12, 1));
  assert.strictEqual(st.day, 15);
  assert.strictEqual(st.reviews.length, 5);
  assert.ok(st.reviewTotal > 5);
  const ords = plain(st.reviews.map((r) => r.dueOrd));
  assert.deepStrictEqual(ords, ords.slice().sort((a, b) => a - b));
});

test('30 句学完：显示完成态，没有新句；复习仍可做', () => {
  const { E } = load();
  learn(E, 'c1', 30);
  const st = E.todayState('c1', at(12, 5));
  assert.strictEqual(st.finished, true);
  assert.strictEqual(st.day, null);
  assert.strictEqual(st.doneCount, 30);
  assert.strictEqual(E.completeDay('c1', 31, OK, at(12, 5)).error, 'day');
  assert.ok(st.reviews.length > 0);
});

test('weekStats：最近 7 天完成的新句数，不含更早的', () => {
  const { E } = load();
  learn(E, 'c1', 10);
  assert.deepStrictEqual({ ...E.weekStats('c1', at(11, 10, 12)) }, { days: 7, total: 10 });
  assert.deepStrictEqual({ ...E.weekStats('c1', at(11, 30)) }, { days: 0, total: 10 });
  assert.deepStrictEqual({ ...E.weekStats('nobody', at(11, 10)) }, { days: 0, total: 0 });
});

test('完成新句时记活动打卡；没有活动脚本也不影响进度；复习不打卡', () => {
  const a = load(true);
  a.E.completeDay('c1', 1, OK, at(11, 1));
  assert.deepStrictEqual(plain(a.A.dates('c1')), ['2026-11-01']);
  a.E.completeReview('c1', 1);
  assert.deepStrictEqual(plain(a.A.dates('c1')), ['2026-11-01']);
  assert.strictEqual(a.E.completeDay('c1', 2, { guess: true }, at(11, 2)).ok, false);
  assert.deepStrictEqual(plain(a.A.dates('c1')), ['2026-11-01'], '未完成不打卡');
  const b = load(false);
  assert.ok(b.E.completeDay('c1', 1, OK, at(11, 1)).ok);
});

test('存储损坏时不抛错，按没有进度处理', () => {
  const { E, store } = load();
  store.set('cnmEnglish.v1', '{坏');
  assert.strictEqual(E.todayState('c1', at(11, 1)).day, 1);
  store.set('cnmEnglish.v1', JSON.stringify({ c1: { done: { 1: 'x', 2: { at: 1 } }, reviews: 5 } }));
  assert.strictEqual(E.doneCount('c1'), 1);
});

console.log(passed + ' passed');
