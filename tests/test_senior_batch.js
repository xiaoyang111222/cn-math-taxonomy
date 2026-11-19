#!/usr/bin/env node
/* 薄弱科目补强批回归：高中地理、生物、历史（cng_h / cnb_h / cnh_h）和初中历史先修边。
 * node tests/test_senior_batch.js */
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
questions.forEach((q) => { if (!qByTopic.has(q.topicId)) qByTopic.set(q.topicId, []); qByTopic.get(q.topicId).push(q); });
const stdIds = new Set(standards.items.map((i) => i.id));

let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

const SUBJECTS = {
  geography: { hs: 'cng_h', jr: 'cng_j', std: 'cgs-hs-2017:', obj: 'geography_senior', range: [90, 120], domains: ['自然地理基础', '人文地理基础', '区域发展', '资源环境与国家安全'] },
  biology: { hs: 'cnb_h', jr: 'cnb_j', std: 'cbs-hs-2017:', obj: 'biology_senior', range: [110, 140], domains: ['分子与细胞', '遗传与进化', '稳态与调节', '生物与环境', '生物技术与工程'] },
  history: { hs: 'cnh_h', jr: 'cnh_j', std: 'chs-hs-2017:', obj: 'history_senior', range: [100, 130], domains: ['中国古代史', '中国近代史', '中国现代史', '世界古代史', '世界近代史', '世界现代史', '国家制度与社会治理', '经济与社会生活', '文化交流与传播'] }
};
const WORD = { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' };

console.log('高中地理、生物、历史');

Object.keys(SUBJECTS).forEach((subj) => {
  const cfg = SUBJECTS[subj];
  const hs = topics.filter((t) => t.id.startsWith(cfg.hs));
  const jr = topics.filter((t) => t.id.startsWith(cfg.jr));
  const hsIds = new Set(hs.map((t) => t.id));

  test(subj + '：高中点数在目标范围内，id 连续，五册都有，grade 10–14、semester 上、章节首词是册名', () => {
    assert.ok(hs.length >= cfg.range[0] && hs.length <= cfg.range[1], subj + ' 高中点数 ' + hs.length);
    hs.forEach((t, i) => {
      assert.strictEqual(t.id, cfg.hs + String(i + 1).padStart(3, '0'));
      assert.ok(t.grade >= 10 && t.grade <= 14, t.id);
      assert.strictEqual(t.semester, '上', t.id);
      assert.strictEqual(t.chapter.split(' ')[0], WORD[t.grade], t.id + ' ' + t.chapter);
      assert.strictEqual(t.subject, subj, t.id);
      assert.ok(cfg.domains.includes(t.domain), t.id + ' ' + t.domain);
      assert.ok(t.description.length >= 40, t.id + ' 讲解太短');
      assert.ok(t.mastery_criteria.length >= 2 && t.mastery_criteria.length <= 3, t.id);
    });
    [10, 11, 12, 13, 14].forEach((g) => assert.ok(hs.some((t) => t.grade === g), subj + ' 缺 grade ' + g));
    for (let i = 1; i < hs.length; i++) assert.ok(hs[i].grade >= hs[i - 1].grade, '册序不降 ' + hs[i].id);
  });

  test(subj + '：每个高中点 4 题（basic、basic、standard、challenge），q1 是 basic 选择题，诊断题与 q1 对齐', () => {
    hs.forEach((t) => {
      const qs = (qByTopic.get(t.id) || []).slice().sort((a, b) => parseInt(a.id.split('_q')[1], 10) - parseInt(b.id.split('_q')[1], 10));
      assert.strictEqual(qs.length, 4, t.id + ' 题数');
      assert.deepStrictEqual(qs.map((q) => q.difficulty), ['basic', 'basic', 'standard', 'challenge'], t.id);
      assert.strictEqual(qs[0].id, t.id + '_q1');
      assert.strictEqual(qs[0].type, 'choice', t.id);
      assert.strictEqual(t.diagnostic_question.question, qs[0].prompt, t.id + ' 诊断题题干');
      const right = qs[0].choices.find((c) => c.key === qs[0].answer).text;
      assert.strictEqual(t.diagnostic_question.answer, right, t.id + ' 诊断题答案');
      qs.forEach((q) => {
        assert.ok(q.explanation && q.explanation.length > 5, q.id);
        assert.ok(q.verify, q.id + ' 缺 verify');
        if (q.type === 'choice') {
          assert.strictEqual(q.choices.length, 4, q.id);
          assert.strictEqual(new Set(q.choices.map((c) => c.text)).size, 4, q.id + ' 选项重复');
        }
      });
    });
  });

  test(subj + '：课标引用都指向本科高中课标，课标对象与条目齐全且每条都被引用', () => {
    assert.ok(standards[cfg.obj] && standards[cfg.obj].title && standards[cfg.obj].textbook, cfg.obj);
    const items = standards.items.filter((i) => i.id.startsWith(cfg.std));
    assert.ok(items.length >= 25, subj + ' 课标条数 ' + items.length);
    const cited = new Set();
    hs.forEach((t) => {
      assert.ok(t.standards.length >= 1 && t.standards.length <= 3, t.id);
      t.standards.forEach((s) => { assert.ok(s.id.startsWith(cfg.std) && stdIds.has(s.id), t.id + ' ' + s.id); cited.add(s.id); });
    });
    items.forEach((i) => {
      assert.strictEqual(i.verbatim, false);
      assert.strictEqual(i.page_or_ref, '待核');
      assert.ok(cited.has(i.id), i.id + ' 没有被引用');
    });
    jr.forEach((t) => t.standards.forEach((s) => assert.ok(!s.id.includes('-hs-'), t.id + ' 初中点不能引用高中课标')));
  });

  test(subj + '：高中边无悬空、无重复、无自环；先修都排在后续点之前；连到初中点的边只来自高中点；每点至少 1 条先修', () => {
    const idx = new Map(topics.map((t, i) => [t.id, i]));
    const seen = new Set();
    const edges = deps.filter((e) => hsIds.has(e.topicId));
    edges.forEach((e) => {
      assert.ok(byId.has(e.prerequisiteId), '悬空 ' + e.prerequisiteId);
      assert.notStrictEqual(e.topicId, e.prerequisiteId);
      const k = e.topicId + '>' + e.prerequisiteId;
      assert.ok(!seen.has(k), '重复 ' + k);
      seen.add(k);
      assert.ok(e.prerequisiteId.startsWith(cfg.hs) || e.prerequisiteId.startsWith(cfg.jr), '跨学科 ' + k);
      assert.ok(['hard', 'soft'].includes(e.strength));
      assert.ok(e.reason && e.reason.length >= 8, k + ' 缺理由');
      assert.ok(idx.get(e.prerequisiteId) < idx.get(e.topicId), '先修排在后面 ' + k);
      if (e.prerequisiteId.startsWith(cfg.hs)) assert.ok(byId.get(e.prerequisiteId).grade <= byId.get(e.topicId).grade, '册次倒挂 ' + k);
    });
    hs.forEach((t) => assert.ok(edges.some((e) => e.topicId === t.id), t.id + ' 没有先修'));
    assert.ok(deps.filter((e) => jr.some((j) => j.id === e.topicId)).every((e) => !hsIds.has(e.prerequisiteId)), '初中点不能依赖高中点');
    const toJunior = edges.filter((e) => e.prerequisiteId.startsWith(cfg.jr));
    assert.ok(toJunior.length >= 15, subj + ' 连到初中的边 ' + toJunior.length);
    assert.ok(toJunior.some((e) => e.topicId === hs[0].id && e.strength === 'hard'), '第一个高中点必须硬连初中点');
  });

  test(subj + '：高中边密度（条/点）不低于同科初中段，且不低于 1.5', () => {
    const hsEdges = deps.filter((e) => hsIds.has(e.topicId)).length;
    const jrEdges = deps.filter((e) => e.topicId.startsWith(cfg.jr)).length;
    assert.ok(hsEdges / hs.length >= 1.5, subj + ' 高中边密度 ' + (hsEdges / hs.length).toFixed(2));
    assert.ok(hsEdges / hs.length >= jrEdges / jr.length, subj + ' 高中 ' + (hsEdges / hs.length).toFixed(2) + ' < 初中 ' + (jrEdges / jr.length).toFixed(2));
  });

  test(subj + '：整册诊断范围按必修一至选必三取到高中点，不混进初中点；全答对的整册诊断能跑满题量上限', () => {
    const tp = topics.filter((t) => E.subjectOf(t) === subj);
    const allow = new Set(tp.map((t) => t.id));
    const graph = E.buildGraph(tp,
      deps.filter((d) => allow.has(d.topicId) && allow.has(d.prerequisiteId)),
      questions.filter((q) => allow.has(q.topicId)));
    Object.keys(WORD).forEach((g) => {
      const word = WORD[g];
      const expected = hs.filter((t) => t.grade === Number(g)).map((t) => t.id);
      const scope = E.gradeTargets(graph, word, subj);
      assert.ok(scope, subj + ' ' + word + ' 没有范围');
      assert.deepStrictEqual(scope.ids, expected, subj + ' ' + word);
      assert.ok(scope.ids.every((id) => id.startsWith(cfg.hs)));
      let s = E.createSession(graph, scope.ids, { mode: 'screen' });
      let n = 0;
      for (;;) {
        const id = E.nextQuestion(graph, s);
        if (!id) break;
        s = E.applyAnswer(graph, s, id, 'correct');
        n++;
      }
      assert.ok(n > 0 && n <= E.SCREEN_LIMIT, subj + ' ' + word + ' 题量 ' + n);
    });
    const chapters = new Set();
    hs.forEach((t) => {
      const c = E.parseChapter ? E.parseChapter(t.chapter) : null;
      if (c) { assert.strictEqual(c.volume, WORD[t.grade], t.id + ' ' + t.chapter); assert.ok(c.chapterNo, t.id + ' 章号'); chapters.add(c.volume + c.chapterNo); }
    });
  });
});

console.log('初中历史先修边');

test('初中历史边密度至少 1.4 条/点，补边都是真实存在、不重复、不成环的边', () => {
  const jr = topics.filter((t) => t.id.startsWith('cnh_j'));
  assert.strictEqual(jr.length, 134);
  const edges = deps.filter((e) => e.topicId.startsWith('cnh_j'));
  assert.ok(edges.length / jr.length >= 1.4, '密度 ' + (edges.length / jr.length).toFixed(3));
  const seen = new Set();
  edges.forEach((e) => {
    assert.ok(e.prerequisiteId.startsWith('cnh_j'));
    const k = e.topicId + '>' + e.prerequisiteId;
    assert.ok(!seen.has(k), '重复 ' + k);
    seen.add(k);
    assert.ok(e.prerequisiteId < e.topicId, '先修不在前面 ' + k);
  });
  assert.ok(edges.length >= 188);
});

test('全站先修图无环', () => {
  const adj = new Map();
  deps.forEach((e) => { if (!adj.has(e.topicId)) adj.set(e.topicId, []); adj.get(e.topicId).push(e.prerequisiteId); });
  const color = new Map();
  for (const start of adj.keys()) {
    if (color.get(start)) continue;
    const stack = [[start, 0]];
    color.set(start, 1);
    while (stack.length) {
      const top = stack[stack.length - 1];
      const list = adj.get(top[0]) || [];
      if (top[1] >= list.length) { color.set(top[0], 2); stack.pop(); continue; }
      const next = list[top[1]++];
      const c = color.get(next) || 0;
      assert.notStrictEqual(c, 1, '成环 ' + top[0] + ' -> ' + next);
      if (c === 0) { color.set(next, 1); stack.push([next, 0]); }
    }
  }
});

console.log('\n' + passed + ' passed');
