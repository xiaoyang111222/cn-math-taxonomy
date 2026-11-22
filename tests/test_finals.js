#!/usr/bin/env node
/* 期末补漏计划：node tests/test_finals.js（无依赖，用真实 topics / dependencies 数据，假 localStorage）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const F = require('../finals/finals.js');

const ROOT = path.join(__dirname, '..');
const topics = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/topics.json'), 'utf8'));
const deps = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/dependencies.json'), 'utf8'));
const byId = Object.fromEntries(topics.map(t => [t.id, t]));
const NOW = new Date(2026, 10, 19, 15, 30);
let passed = 0;

function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }
function build(extra) { return F.buildPlan(Object.assign({ topics, deps, subject: 'math', grade: 5, now: NOW }, extra)); }
function flat(plan) { return plan.days.reduce((a, d) => a.concat(d), []); }
function storage() {
  const m = new Map();
  return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, v), removeItem: k => m.delete(k), m };
}

test('每个学科每个年级：有足够知识点时 21–28 个点、前 6 天各 3–5 个、第 7 天为空、不重复', () => {
  const seen = new Set();
  topics.filter(t => !t.external).forEach(t => seen.add(F.subjectOf(t) + '|' + t.grade));
  assert.ok(seen.size > 50);
  seen.forEach(k => {
    const [subject, grade] = k.split('|');
    const g = Number(grade);
    /* 补齐只向本年级和更低年级取。某册不足 21 且前面没有同学科点时，计划就是这一册的全部。 */
    const pool = topics.filter(t => !t.external && F.subjectOf(t) === subject && t.grade <= g).length;
    const plan = build({ subject, grade: g });
    const ids = flat(plan);
    const lo = Math.min(21, pool);
    assert.ok(ids.length >= lo && ids.length <= 28, k + ' 共 ' + ids.length + '，可用 ' + pool);
    assert.equal(plan.days.length, 7);
    assert.equal(plan.days[6].length, 0);
    if (ids.length >= 18) {
      plan.days.slice(0, 6).forEach((d, i) => assert.ok(d.length >= 3 && d.length <= 5, k + ' 第 ' + (i + 1) + ' 天 ' + d.length));
    }
    assert.equal(new Set(ids).size, ids.length, k + ' 有重复');
    ids.forEach(id => {
      assert.ok(byId[id] && !byId[id].external && F.subjectOf(byId[id]) === subject, k + ' ' + id);
      assert.ok(byId[id].grade <= g, k + ' ' + id + ' 年级更高');
    });
  });
});

test('排序遵守先修：先修点不会排在后面', () => {
  const plan = build({ subject: 'math', grade: 8 });
  const pos = {};
  flat(plan).forEach((id, i) => { pos[id] = i; });
  let checked = 0;
  deps.forEach(e => {
    if (e.prerequisiteId in pos && e.topicId in pos) {
      assert.ok(pos[e.prerequisiteId] < pos[e.topicId], e.prerequisiteId + ' 应在 ' + e.topicId + ' 前');
      checked++;
    }
  });
  assert.ok(checked > 0);
});

test('错题本知识点优先，错题多的先入选；其他学科的错题不进来', () => {
  const g5 = topics.filter(t => F.subjectOf(t) === 'math' && t.grade === 5).map(t => t.id);
  const g9 = topics.filter(t => F.subjectOf(t) === 'math' && t.grade === 9 && !t.external).map(t => t.id);
  const eng = topics.find(t => F.subjectOf(t) === 'english').id;
  const rows = [
    { topicId: g9[0], ts: 1 }, { topicId: g9[1], ts: 2 }, { topicId: g9[1], ts: 3 }, { topicId: g9[1], ts: 4 },
    { topicId: eng, ts: 5 }, { topicId: 'nope', ts: 6 }
  ];
  const plan = build({ wrongRows: rows });
  const ids = flat(plan);
  assert.ok(ids.includes(g9[0]) && ids.includes(g9[1]), '跨年级的错题知识点也要排进来');
  assert.ok(!ids.includes(eng));
  assert.ok(g5.some(id => ids.includes(id)), '不够的用该年级补齐');
});

test('错题超过 28 个时截断到 28，按错题数降序取', () => {
  const pool = topics.filter(t => F.subjectOf(t) === 'math' && !t.external).slice(0, 40);
  const rows = [];
  pool.forEach((t, i) => { for (let k = 0; k <= i; k++) rows.push({ topicId: t.id, ts: i }); });
  const ids = flat(build({ wrongRows: rows }));
  assert.equal(ids.length, 28);
  pool.slice(12).forEach(t => assert.ok(ids.includes(t.id)));
  assert.ok(!ids.includes(pool[0].id));
});

test('诊断薄弱 / 不稳进计划，待复测和已掌握不进', () => {
  const pool = topics.filter(t => F.subjectOf(t) === 'math' && t.grade === 9 && !t.external);
  const plan = build({ blindRows: [
    { id: pool[0].id, status: 'weak' }, { id: pool[1].id, status: 'shaky' },
    { id: pool[2].id, status: 'retest' }, { id: pool[3].id, status: 'mastered' }
  ] });
  const ids = flat(plan);
  assert.ok(ids.includes(pool[0].id) && ids.includes(pool[1].id));
  assert.ok(!ids.includes(pool[2].id) && !ids.includes(pool[3].id));
});

test('补齐优先本年级，年级点不够时往低年级取；开始日期取本机今天', () => {
  const plan = F.buildPlan({ topics, deps, subject: 'chemistry', grade: 10, now: NOW });
  const ids = flat(plan);
  assert.ok(ids.length >= 21);
  assert.ok(ids.some(id => byId[id].grade === 10) && ids.some(id => byId[id].grade === 9));
  assert.equal(plan.startDate, '2026-11-19');
  assert.deepEqual(plan.done, [false, false, false, false, false, false, false]);
  assert.equal(plan.createdAt, NOW.getTime());
  assert.deepEqual(Object.keys(plan).sort(), ['createdAt', 'days', 'done', 'grade', 'startDate', 'subject']);
});

test('日期：每天日期、跨月、过期与今天是第几天', () => {
  const plan = build();
  assert.equal(F.fmtDate(F.dayDate(plan.startDate, 6)), '2026-11-25');
  assert.equal(F.fmtDate(F.dayDate('2026-11-28', 3)), '2026-12-01');
  assert.equal(F.todayIndex(plan, NOW), 0);
  assert.equal(F.todayIndex(plan, new Date(2026, 10, 22, 8)), 3);
  assert.equal(F.todayIndex(plan, new Date(2026, 10, 26)), -1);
  assert.equal(F.isExpired(plan, new Date(2026, 10, 25, 23, 59)), false);
  assert.equal(F.isExpired(plan, new Date(2026, 10, 26, 0, 1)), true);
});

test('存取：cnmFinals.v1 往返；坏数据当作没有；清除', () => {
  const s = storage();
  assert.equal(F.KEY, 'cnmFinals.v1');
  assert.equal(F.loadPlan(s), null);
  const plan = build();
  assert.equal(F.savePlan(s, plan), true);
  assert.deepEqual(F.loadPlan(s), plan);
  s.setItem(F.KEY, '{"subject":"math"}');
  assert.equal(F.loadPlan(s), null);
  s.setItem(F.KEY, 'not json');
  assert.equal(F.loadPlan(s), null);
  F.savePlan(s, plan);
  F.clearPlan(s);
  assert.equal(F.loadPlan(s), null);
  assert.equal(F.savePlan({ setItem() { throw new Error('quota'); } }, plan), false);
});

test('链接：练题沿用诊断 target 入口，非数学带 subject；复测带全部知识点', () => {
  assert.equal(F.practiceHref('cnm_p001', 'math'), '../diagnose/?target=cnm_p001');
  assert.equal(F.practiceHref('cne_x', 'english'), '../diagnose/?subject=english&target=cne_x');
  const plan = build();
  const ids = flat(plan);
  assert.equal(F.retestHref(plan), '../diagnose/?target=' + ids.join(','));
  assert.ok(F.retestHref(Object.assign({}, plan, { subject: 'physics' })).startsWith('../diagnose/?subject=physics&target='));
});

console.log(passed + ' passed');
