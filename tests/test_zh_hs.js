#!/usr/bin/env node
/* 高中语文：144 点、册名、先修、课标待核、界面册次标签。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('../diagnose/engine.js');

const ROOT = path.resolve(__dirname, '..');
const read = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const src = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');

let passed = 0;
function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

const topics = read('data/topics.json');
const deps = read('data/dependencies.json');
const questions = read('data/questions.json');
const standards = read('data/cn-curriculum-standards.json');
const byId = new Map(topics.map((t) => [t.id, t]));
const hs = topics.filter((t) => String(t.id).startsWith('cnc_h'));
const BOOK = { 10: '必修上', 11: '必修下', 12: '选必上', 13: '选必中', 14: '选必下' };
const CHAPTER = /^(必修上|必修下|选必上|选必中|选必下) (?:第[一二三四五六七八]单元 \S+|古诗词诵读 \S+)$/;

test('高中语文 144 点，id 连续，年级与册名对齐', () => {
  assert.strictEqual(hs.length, 144);
  hs.forEach((t, i) => {
    const id = 'cnc_h' + String(i + 1).padStart(3, '0');
    assert.strictEqual(t.id, id);
    assert.strictEqual(t.subject, 'chinese');
    assert.strictEqual(t.semester, '上');
    assert.ok(BOOK[t.grade], t.id);
    assert.match(t.chapter, CHAPTER, t.id + ' ' + t.chapter);
    assert.ok(t.chapter.startsWith(BOOK[t.grade] + ' '), t.id);
  });
  const counts = { 10: 0, 11: 0, 12: 0, 13: 0, 14: 0 };
  hs.forEach((t) => { counts[t.grade]++; });
  assert.deepStrictEqual(counts, { 10: 39, 11: 31, 12: 21, 13: 26, 14: 27 });
});

test('每点 4 道选择题，诊断题与第 1 题一致', () => {
  const qBy = new Map();
  questions.forEach((q) => {
    if (!String(q.topicId).startsWith('cnc_h')) return;
    if (!qBy.has(q.topicId)) qBy.set(q.topicId, []);
    qBy.get(q.topicId).push(q);
  });
  const ids = new Set();
  hs.forEach((t) => {
    const qs = qBy.get(t.id) || [];
    assert.strictEqual(qs.length, 4, t.id);
    qs.forEach((q, n) => {
      assert.strictEqual(q.id, t.id + '_q' + (n + 1));
      assert.strictEqual(q.type, 'choice');
      assert.ok(!ids.has(q.id));
      ids.add(q.id);
      const right = q.choices.find((c) => c.key === q.answer);
      assert.ok(right, q.id);
      assert.strictEqual(q.verify, JSON.stringify(right.text));
    });
    assert.strictEqual(qs[0].difficulty, 'basic');
    assert.strictEqual(t.diagnostic_question.question, qs[0].prompt);
    const right = qs[0].choices.find((c) => c.key === qs[0].answer);
    assert.strictEqual(t.diagnostic_question.answer, right.text);
  });
});

test('先修只连语文，高中点指向更早的点，且无环', () => {
  const hsEdges = deps.filter((e) => String(e.topicId).startsWith('cnc_h'));
  assert.ok(hsEdges.length > 144);
  hsEdges.forEach((e) => {
    assert.match(e.prerequisiteId, /^cnc_[pjh]/, e.topicId + ' -> ' + e.prerequisiteId);
    assert.ok(byId.has(e.prerequisiteId));
    if (String(e.prerequisiteId).startsWith('cnc_h')) {
      assert.ok(e.prerequisiteId < e.topicId, e.topicId + ' -> ' + e.prerequisiteId);
    }
  });
  const adj = new Map();
  deps.forEach((e) => {
    if (!adj.has(e.topicId)) adj.set(e.topicId, []);
    adj.get(e.topicId).push(e.prerequisiteId);
  });
  const color = new Map();
  function dfs(n) {
    color.set(n, 1);
    for (const p of adj.get(n) || []) {
      const c = color.get(p) || 0;
      if (c === 1) return true;
      if (c === 0 && dfs(p)) return true;
    }
    color.set(n, 2);
    return false;
  }
  for (const n of adj.keys()) {
    if ((color.get(n) || 0) === 0) assert.ok(!dfs(n), '先修有环');
  }
  const first = hsEdges.filter((e) => e.topicId === 'cnc_h001');
  assert.ok(first.some((e) => e.prerequisiteId === 'cnc_j127' && e.strength === 'hard'));
  const lunyu = hs.find((t) => t.name.indexOf('《论语》十二章') >= 0);
  assert.ok(lunyu, '缺少《论语》十二章');
  assert.ok(hsEdges.some((e) => e.topicId === lunyu.id && e.prerequisiteId === 'cnc_j013'));
  assert.strictEqual(byId.get('cnc_j013').name.indexOf('论语') >= 0, true);
});

test('高中语文课标已对照课标 PDF，未对应的仍待核，小学初中不引用它', () => {
  const items = standards.items.filter((it) => String(it.id).startsWith('ccs-hs-2017:'));
  assert.strictEqual(items.length, 20);
  items.forEach((it) => {
    assert.strictEqual(it.verbatim, false);
    assert.ok(it.page_or_ref === '待核' || /^课标印刷页码 \d+([–、]\d+)*$/.test(it.page_or_ref), it.id + ' ' + it.page_or_ref);
    assert.match(it.text_status, /2026-11-22/);
  });
  const meta = standards.chinese_senior;
  assert.strictEqual(meta.title, '普通高中语文课程标准（2017年版）');
  assert.strictEqual(meta.year, 2017);
  assert.ok(!String(meta.title).includes('2022'));
  hs.forEach((t) => {
    assert.ok(t.standards && t.standards.length);
    t.standards.forEach((s) => {
      assert.ok(String(s.id).startsWith('ccs-hs-2017:'));
      assert.strictEqual(s.confidence, 'inferred');
      assert.match(s.note, /待核/);
    });
  });
  topics.filter((t) => /^cnc_[pj]/.test(t.id)).forEach((t) => {
    (t.standards || []).forEach((s) => assert.ok(!String(s.id).startsWith('ccs-hs-2017:')));
  });
});

test('初中小学与地理生物历史高中点数不变', () => {
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cnc_j')).length, 189);
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cnc_p')).length, 494);
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cng_h')).length, 119);
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cnb_h')).length, 135);
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cnh_h')).length, 120);
  assert.strictEqual(topics.filter((t) => String(t.id).startsWith('cnz_h')).length, 153);
  assert.strictEqual(topics.length, 4221);
  assert.strictEqual(questions.length, 17031);
});

test('界面册次不用高一或必修一', () => {
  const explore = src('explore/app.js');
  const home = src('assets/home.js');
  const diagnose = src('diagnose/app.js');
  const kp = src('scripts/gen-kp-pages.mjs');
  assert.match(explore, /\[\[10, '必修上'\], \[11, '必修下'\], \[12, '选必上'\], \[13, '选必中'\], \[14, '选必下'\]\]/);
  assert.match(home, /高中语文/);
  assert.match(home, /10: '必修上'/);
  assert.match(diagnose, /'必修上', '必修上'/);
  assert.match(kp, /10: '必修上', 11: '必修下', 12: '选必上', 13: '选必中', 14: '选必下'/);
  assert.doesNotMatch(home, /语文、道德与法治到九年级且无高中/);
  const b1 = E.gradeTargets({ topics: hs, byId }, '必修上', 'chinese');
  assert.strictEqual(b1.label, '必修上');
  assert.strictEqual(b1.ids.length, 39);
  assert.strictEqual(E.gradeTargets({ topics: hs, byId }, '必修上'), null);
});

test('目录锁定的篇目在，旧转载多出来的篇目不在', () => {
  const names = hs.map((t) => t.name).join('\n');
  assert.match(names, /插秧歌/);
  assert.match(names, /榜样——焦裕禄/);
  assert.doesNotMatch(names, /好榜样/);
  assert.match(names, /一个消逝了的山村/);
  assert.doesNotMatch(names, /风景谈/);
  assert.match(names, /天文学上的旷世之争/);
  assert.doesNotMatch(names, /机遇偏爱有准备的头脑/);
  assert.match(names, /江城子·乙卯正月二十日夜记梦/);
});

console.log(passed + ' passed');
