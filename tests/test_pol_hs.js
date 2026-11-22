#!/usr/bin/env node
/* 高中思想政治（cnz_h）：七册、课标、先修与整册诊断。
 * node tests/test_pol_hs.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('../diagnose/engine.js');

const ROOT = path.join(__dirname, '..');
const read = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const topics = read('data/topics.json');
const deps = read('data/dependencies.json');
const questions = read('data/questions.json');
const standards = read('data/cn-curriculum-standards.json');
const byId = new Map(topics.map((t) => [t.id, t]));
const qByTopic = new Map();
questions.forEach((q) => {
  if (!qByTopic.has(q.topicId)) qByTopic.set(q.topicId, []);
  qByTopic.get(q.topicId).push(q);
});

const WORD = {
  10: '必修一', 11: '必修二', 12: '必修三', 13: '必修四',
  14: '选必一', 15: '选必二', 16: '选必三'
};
const COUNTS = { 10: 20, 11: 26, 12: 30, 13: 27, 14: 20, 15: 15, 16: 15 };
const DOMAINS = ['中国特色社会主义', '经济与社会', '政治与法治', '哲学与文化', '当代国际政治与经济', '法律与生活', '逻辑与思维'];
const JUNIOR = [
  ['cnz_h001', 'cnd_j044'],
  ['cnz_h022', 'cnd_j071'],
  ['cnz_h026', 'cnd_j073'],
  ['cnz_h041', 'cnd_j072'],
  ['cnz_h047', 'cnd_j089'],
  ['cnz_h054', 'cnd_j063'],
  ['cnz_h057', 'cnd_j068'],
  ['cnz_h075', 'cnd_j084'],
  ['cnz_h124', 'cnd_j108'],
  ['cnz_h129', 'cnd_j041']
];

let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

const hs = topics.filter((t) => t.id.startsWith('cnz_h'));
const hsIds = new Set(hs.map((t) => t.id));

console.log('高中思想政治');

test('153 点，id 连续，七册数量、grade、semester、章节首词和领域都对', () => {
  assert.strictEqual(hs.length, 153);
  assert.deepStrictEqual(hs.map((t) => t.id), Array.from({ length: 153 }, (_, i) => 'cnz_h' + String(i + 1).padStart(3, '0')));
  const byGrade = {};
  hs.forEach((t, i) => {
    assert.ok(t.grade >= 10 && t.grade <= 16, t.id);
    assert.strictEqual(t.semester, '上', t.id);
    assert.strictEqual(t.chapter.split(' ')[0], WORD[t.grade], t.id + ' ' + t.chapter);
    assert.strictEqual(t.subject, 'politics', t.id);
    assert.ok(DOMAINS.includes(t.domain), t.id + ' ' + t.domain);
    assert.ok(t.description.length >= 40, t.id);
    assert.ok(t.mastery_criteria.length >= 2 && t.mastery_criteria.length <= 3, t.id);
    assert.ok(!('root_reason' in t), t.id + ' 每点都有先修，不单写 root_reason');
    byGrade[t.grade] = (byGrade[t.grade] || 0) + 1;
    if (i) assert.ok(t.grade >= hs[i - 1].grade, t.id);
  });
  assert.deepStrictEqual(byGrade, COUNTS);
});

test('每点 4 题，诊断题与 q1 对齐', () => {
  hs.forEach((t) => {
    const qs = (qByTopic.get(t.id) || []).slice().sort((a, b) => parseInt(a.id.split('_q')[1], 10) - parseInt(b.id.split('_q')[1], 10));
    assert.strictEqual(qs.length, 4, t.id);
    assert.deepStrictEqual(qs.map((q) => q.difficulty), ['basic', 'basic', 'standard', 'challenge'], t.id);
    assert.strictEqual(qs[0].type, 'choice', t.id);
    assert.strictEqual(t.diagnostic_question.question, qs[0].prompt, t.id);
    const right = qs[0].choices.find((c) => c.key === qs[0].answer).text;
    assert.strictEqual(t.diagnostic_question.answer, right, t.id);
  });
});

test('课标 67 条都已核，verbatim 为 false，无待核，且每条都被引用', () => {
  const obj = standards.politics_senior;
  assert.strictEqual(obj.title, '普通高中思想政治课程标准（2017年版2020年修订）');
  assert.strictEqual(obj.year, 2017);
  assert.ok(obj.textbook && obj.note && obj.issuer && obj.stage);
  const items = standards.items.filter((i) => i.id.startsWith('czs-hs-2017:'));
  assert.strictEqual(items.length, 67);
  const cited = new Set();
  hs.forEach((t) => {
    assert.ok(t.standards.length >= 1 && t.standards.length <= 3, t.id);
    t.standards.forEach((s) => {
      assert.ok(s.id.startsWith('czs-hs-2017:'), t.id);
      cited.add(s.id);
    });
  });
  items.forEach((i) => {
    assert.strictEqual(i.verbatim, false, i.id);
    assert.match(i.page_or_ref, /^课标印刷页码 \d+(–\d+)?$/, i.id);
    assert.ok(String(i.text_status).includes('2026-11-22'), i.id);
    assert.ok(!String(i.page_or_ref).includes('待核') && !String(i.text_status).includes('待核'), i.id);
    assert.ok(cited.has(i.id), i.id + ' 没有被引用');
    assert.ok(DOMAINS.includes(i.domain), i.id);
  });
});

test('先修边密度不低于 1.5，跨科只连约定的 10 条初中道德与法治', () => {
  const idx = new Map(topics.map((t, i) => [t.id, i]));
  const edges = deps.filter((e) => hsIds.has(e.topicId));
  const seen = new Set();
  edges.forEach((e) => {
    assert.ok(byId.has(e.prerequisiteId), e.prerequisiteId);
    assert.notStrictEqual(e.topicId, e.prerequisiteId);
    const k = e.topicId + '>' + e.prerequisiteId;
    assert.ok(!seen.has(k), k);
    seen.add(k);
    assert.ok(e.prerequisiteId.startsWith('cnz_h') || e.prerequisiteId.startsWith('cnd_'), k);
    assert.ok(idx.get(e.prerequisiteId) < idx.get(e.topicId), k);
  });
  hs.forEach((t) => assert.ok(edges.some((e) => e.topicId === t.id), t.id));
  assert.ok(edges.length / hs.length >= 1.5, '密度 ' + (edges.length / hs.length).toFixed(2));
  const junior = edges.filter((e) => e.prerequisiteId.startsWith('cnd_'));
  assert.deepStrictEqual(junior.map((e) => [e.topicId, e.prerequisiteId]), JUNIOR);
  junior.forEach((e) => assert.strictEqual(e.strength, 'hard', e.topicId));
  assert.ok(junior.some((e) => e.topicId === 'cnz_h001'));
});

test('学科识别、章节解析和七册诊断范围', () => {
  assert.strictEqual(E.subjectOf({ id: 'cnz_h001' }), 'politics');
  assert.strictEqual(E.subjectOf(hs[0]), 'politics');
  hs.forEach((t) => {
    const c = E.parseChapter(t.chapter);
    assert.strictEqual(c.volume, WORD[t.grade], t.id + ' ' + t.chapter);
    assert.match(c.chapterNo, /^第\S+课$/, t.id + ' ' + c.chapterNo);
  });
  const tp = topics.filter((t) => E.subjectOf(t) === 'politics');
  const allow = new Set(tp.map((t) => t.id));
  const graph = E.buildGraph(tp,
    deps.filter((d) => allow.has(d.topicId) && allow.has(d.prerequisiteId)),
    questions.filter((q) => allow.has(q.topicId)));
  Object.keys(WORD).forEach((g) => {
    const word = WORD[g];
    const expected = hs.filter((t) => t.grade === Number(g)).map((t) => t.id);
    const scope = E.gradeTargets(graph, word, 'politics');
    assert.ok(scope, word);
    assert.deepStrictEqual(scope.ids, expected, word);
    let s = E.createSession(graph, scope.ids, { mode: 'screen' });
    let n = 0;
    for (;;) {
      const id = E.nextQuestion(graph, s);
      if (!id) break;
      s = E.applyAnswer(graph, s, id, 'correct');
      n++;
    }
    assert.ok(n > 0 && n <= E.SCREEN_LIMIT, word + ' ' + n);
  });
});

console.log(passed + ' passed');
