#!/usr/bin/env node
/* 诊断引擎测试：node tests/test_engine.js （无依赖，仅用 assert） */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('../diagnose/engine.js');

let passed = 0;
let failed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log('  ok   ' + name); }
  catch (e) { failed++; console.log('  FAIL ' + name + '\n       ' + (e && e.stack || e).split('\n').slice(0, 4).join('\n       ')); }
}
const sorted = (it) => Array.from(it).sort();

/* ------------------------------------------------------------ 手造小图
 *   X(外部) <- F <- E <- C <---hard--- T
 *              F <- D <---hard--- T
 *              F <- B <---soft--- T
 *   Z 与 T 无关
 * topics 顺序：X F E C D B T Z（同级先修按此顺序出题）
 */
function mk(id, extra) {
  return Object.assign({
    id: id, name: id, external: false,
    diagnostic_question: { question: id + '?', answer: '1' }
  }, extra || {});
}
const smallTopics = [
  mk('X', { external: true, diagnostic_question: undefined }),
  mk('F'), mk('E'), mk('C'), mk('D'), mk('B'), mk('T'), mk('Z')
];
const smallDeps = [
  { topicId: 'F', prerequisiteId: 'X', strength: 'hard' },
  { topicId: 'E', prerequisiteId: 'F', strength: 'hard' },
  { topicId: 'C', prerequisiteId: 'E', strength: 'hard' },
  { topicId: 'D', prerequisiteId: 'F', strength: 'hard' },
  { topicId: 'B', prerequisiteId: 'F', strength: 'hard' },
  { topicId: 'T', prerequisiteId: 'B', strength: 'soft' },   // 故意把 soft 写在 hard 前面
  { topicId: 'T', prerequisiteId: 'D', strength: 'hard' },
  { topicId: 'T', prerequisiteId: 'C', strength: 'hard' }
];
const G = E.buildGraph(smallTopics, smallDeps);

function run(session, script) {
  // script: {id: 'correct'|'wrong'|'skip'} —— 按引擎的出题顺序作答，返回 [会话, 出题顺序]
  const asked = [];
  let s = session;
  for (let guard = 0; guard < 100; guard++) {
    const q = E.nextQuestion(G, s);
    if (!q) break;
    asked.push(q);
    assert.ok(script[q], '脚本里没有 ' + q + ' 的答案');
    s = E.applyAnswer(G, s, q, script[q]);
  }
  return [s, asked];
}

function assertTopological(order, graph) {
  const pos = new Map(order.map((id, i) => [id, i]));
  order.forEach((id) => {
    graph.prereqs[id].forEach((p) => {
      if (pos.has(p.id)) assert.ok(pos.get(p.id) < pos.get(id), p.id + ' 应排在 ' + id + ' 之前');
    });
  });
}

console.log('小型手造图（每个知识点只有一道题——回退模式：答错即薄弱）');

test('祖先子图：目标 + 全部祖先（含外部节点），不含无关点', () => {
  assert.deepStrictEqual(sorted(E.ancestors(G, 'T')), ['B', 'C', 'D', 'E', 'F', 'X']);
  assert.deepStrictEqual(sorted(E.ancestors(G, 'E')), ['F', 'X']);
  assert.deepStrictEqual(sorted(E.ancestors(G, 'X')), []);
  const sub = E.subgraph(G, ['T']);
  assert.deepStrictEqual(sorted(sub.nodes), ['B', 'C', 'D', 'E', 'F', 'T', 'X']);
});

test('拓扑序：每个先修都排在依赖它的点之前', () => {
  const sub = E.subgraph(G, ['T']);
  assertTopological(sub.nodes, G);
  assert.strictEqual(sub.nodes[0], 'X');
  assert.strictEqual(sub.nodes[sub.nodes.length - 1], 'T');
  const multi = E.subgraph(G, ['C', 'D']);
  assertTopological(multi.nodes, G);
  assert.deepStrictEqual(sorted(multi.nodes), ['C', 'D', 'E', 'F', 'X']);
});

test('先修按 hard 优先、再 soft', () => {
  assert.deepStrictEqual(G.prereqs.T.map((p) => p.id + ':' + p.strength), ['C:hard', 'D:hard', 'B:soft']);
});

test('第一题问目标本身', () => {
  const s = E.createSession(G, ['T']);
  assert.strictEqual(E.nextQuestion(G, s), 'T');
});

test('答对：该点及所有祖先（含外部）视为掌握并跳过', () => {
  let s = E.createSession(G, ['T']);
  s = E.applyAnswer(G, s, 'T', 'correct');
  assert.strictEqual(E.nextQuestion(G, s), null);
  ['B', 'C', 'D', 'E', 'F', 'X', 'T'].forEach((id) => assert.strictEqual(E.statusOf(s, id), 'mastered', id));
  assert.strictEqual(s.status.T.src, 'direct');
  assert.strictEqual(s.status.F.src, 'inferred');
  assert.strictEqual(E.statusOf(s, 'Z'), 'unknown');
  const sum = E.summarize(G, s);
  assert.deepStrictEqual(sum.weak, []);
  assert.deepStrictEqual(sum.roots, []);
  assert.deepStrictEqual(sum.path, []);
  assert.strictEqual(sum.asked, 1);
});

test('答错：回溯先修，hard 先于 soft，深度优先', () => {
  const s0 = E.createSession(G, ['T']);
  const [s, asked] = run(s0, { T: 'wrong', C: 'wrong', E: 'correct', D: 'correct', B: 'correct' });
  // T 错 -> 先修 C,D（hard，按文件顺序）再 B（soft）；C 错 -> 先问 C 的先修 E，再回到 D、B
  assert.deepStrictEqual(asked, ['T', 'C', 'E', 'D', 'B']);
  assert.strictEqual(E.nextQuestion(G, s), null);
});

test('答错后首个追问是 hard 先修，soft 排最后', () => {
  let s = E.createSession(G, ['T']);
  s = E.applyAnswer(G, s, 'T', 'wrong');
  assert.strictEqual(E.nextQuestion(G, s), 'C');
  s = E.applyAnswer(G, s, 'C', 'correct'); // C 对 -> E、F、X 掌握
  assert.strictEqual(E.nextQuestion(G, s), 'D');
  s = E.applyAnswer(G, s, 'D', 'correct');
  assert.strictEqual(E.nextQuestion(G, s), 'B');
});

test('「不会」(skip) 与答错等效', () => {
  const [a] = run(E.createSession(G, ['T']), { T: 'skip', C: 'skip', E: 'correct', D: 'correct', B: 'correct' });
  const [b] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'correct', D: 'correct', B: 'correct' });
  assert.deepStrictEqual(a.status, b.status);
});

test('已判定的点不重复问；共享先修只问一次', () => {
  const [, asked] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'wrong', F: 'correct', D: 'wrong', B: 'wrong' });
  assert.strictEqual(new Set(asked).size, asked.length);
  assert.deepStrictEqual(asked, ['T', 'C', 'E', 'F', 'D', 'B']);
});

test('题量上限生效，剩余标为未测', () => {
  const s0 = E.createSession(G, ['T'], { limit: 2 });
  const [s, asked] = run(s0, { T: 'wrong', C: 'wrong' });
  assert.deepStrictEqual(asked, ['T', 'C']);
  assert.strictEqual(E.nextQuestion(G, s), null);
  const sum = E.summarize(G, s);
  assert.strictEqual(sum.asked, 2);
  assert.strictEqual(sum.limitReached, true);
  assert.deepStrictEqual(sorted(sum.untested), ['B', 'D', 'E', 'F', 'X']);
  assert.deepStrictEqual(sorted(sum.weak), ['C', 'T']);
  // 根因 C：它的先修 E 还没测到，要标出来
  assert.deepStrictEqual(sum.roots.map((r) => r.id), ['C']);
  assert.deepStrictEqual(sum.roots[0].pendingPrereqs, ['E']);
});

test('limit 默认 16，limit=1 只问目标', () => {
  assert.strictEqual(E.DEFAULT_LIMIT, 16);
  assert.strictEqual(E.createSession(G, ['T']).limit, 16);
  const s0 = E.createSession(G, ['T'], { limit: 1 });
  const [, asked] = run(s0, { T: 'wrong' });
  assert.deepStrictEqual(asked, ['T']);
});

test('根因：薄弱且先修中没有薄弱点；路径为拓扑序且不含已掌握', () => {
  const [s] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'correct', D: 'correct', B: 'correct' });
  const sum = E.summarize(G, s);
  assert.deepStrictEqual(sorted(sum.weak), ['C', 'T']);
  assert.deepStrictEqual(sum.roots.map((r) => r.id), ['C']);
  assert.deepStrictEqual(sum.path.map((p) => p.id), ['C', 'T']);
  assert.strictEqual(sum.path[0].isRoot, true);
  assert.strictEqual(sum.path[1].isTarget, true);
  assert.deepStrictEqual(sorted(sum.mastered), ['B', 'D', 'E', 'F', 'X']);
  assert.strictEqual(sum.finished, true);
  assert.strictEqual(sum.limitReached, false);
});

test('多个根因：路径含根因到目标之间所有未掌握点，拓扑序', () => {
  // T、C、E、D 薄弱；F 掌握 -> E、D 都是根因；B 掌握
  const [s] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'wrong', F: 'correct', D: 'wrong', B: 'correct' });
  const sum = E.summarize(G, s);
  assert.deepStrictEqual(sorted(sum.roots.map((r) => r.id)), ['D', 'E']);
  assert.deepStrictEqual(sorted(sum.path.map((p) => p.id)), ['C', 'D', 'E', 'T']);
  assertTopological(sum.path.map((p) => p.id), G);
  sum.path.forEach((p) => assert.notStrictEqual(p.status, 'mastered'));
  assert.deepStrictEqual(sum.path.filter((p) => p.isRoot).map((p) => p.id).sort(), ['D', 'E']);
});

test('外部（小学）节点不出题；根因的外部先修单独标出', () => {
  const [s, asked] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'wrong', F: 'wrong', D: 'wrong', B: 'wrong' });
  assert.ok(!asked.includes('X'));
  const sum = E.summarize(G, s);
  assert.deepStrictEqual(sum.roots.map((r) => r.id), ['F']);
  assert.deepStrictEqual(sum.roots[0].externalPrereqs, ['X']);
  assert.deepStrictEqual(sum.roots[0].pendingPrereqs, []);
  assert.deepStrictEqual(sum.untested, ['X']);
});

test('多目标：离目标最近的先问；答对一个即覆盖其余祖先目标', () => {
  const s0 = E.createSession(G, ['C', 'T', 'D']);
  assert.strictEqual(E.nextQuestion(G, s0), 'T');
  const s1 = E.applyAnswer(G, s0, 'T', 'correct');
  assert.strictEqual(E.nextQuestion(G, s1), null);
  assert.deepStrictEqual(E.summarize(G, s1).path, []);
});

test('多目标：互不相关的目标都会被问到', () => {
  const s0 = E.createSession(G, ['T', 'Z']);
  const [, asked] = run(s0, { T: 'correct', Z: 'correct' });
  assert.deepStrictEqual(sorted(asked), ['T', 'Z']);
});

test('直接作答的判定不会被推断覆盖', () => {
  let s = E.createSession(G, ['T']);
  s = E.applyAnswer(G, s, 'E', 'wrong');
  s = E.applyAnswer(G, s, 'T', 'correct');
  assert.strictEqual(E.statusOf(s, 'E'), 'weak');
  assert.strictEqual(E.statusOf(s, 'C'), 'mastered');
});

test('applyAnswer 不修改入参；replay 与逐步作答一致', () => {
  const s0 = E.createSession(G, ['T']);
  const snap = JSON.stringify(s0);
  const s1 = E.applyAnswer(G, s0, 'T', 'wrong');
  assert.strictEqual(JSON.stringify(s0), snap);
  const s2 = E.applyAnswer(G, s1, 'C', 'correct');
  const r = E.replay(G, ['T'], [{ id: 'T', result: 'wrong' }, { id: 'C', result: 'correct' }]);
  assert.deepStrictEqual(r, s2);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(s2)), s2); // 可序列化
  assert.throws(() => E.applyAnswer(G, s0, 'T', 'maybe'));
  assert.throws(() => E.createSession(G, ['nope']));
});

test('路径图布局：先修在上层，边不跨回', () => {
  const [s] = run(E.createSession(G, ['T']), { T: 'wrong', C: 'wrong', E: 'wrong', F: 'correct', D: 'wrong', B: 'correct' });
  const sum = E.summarize(G, s);
  const lay = E.layout(G, s, sum);
  const layer = Object.fromEntries(lay.nodes.map((n) => [n.id, n.layer]));
  lay.edges.forEach((e) => assert.ok(layer[e.from] < layer[e.to], e.from + '->' + e.to));
  assert.ok(lay.nodes.some((n) => n.id === 'T' && n.isTarget));
  assert.ok(lay.nodes.some((n) => n.id === 'E' && n.isRoot));
});


/* ------------------------------------------------------------ 两题判定（手造题库） */
console.log('两题判定');

const DIFFS = { b: 'basic', s: 'standard', a: 'advanced' };
function mq(topicId, n, diff, extra) {
  return Object.assign({
    id: topicId + '_q' + n, topicId: topicId, difficulty: DIFFS[diff] || diff, type: 'numeric',
    prompt: topicId + ' 第 ' + n + ' 题', answer: '1', explanation: '解析'
  }, extra || {});
}
// T 的先修：P1(hard) <- R，P2(hard)；每个知识点 4 题：q1 标准、q2 标准、q3 基础、q4 提高
const bankTopics = ['R', 'P1', 'P2', 'T'].map((id) => mk(id, { diagnostic_question: undefined }));
const bankDeps = [
  { topicId: 'P1', prerequisiteId: 'R', strength: 'hard' },
  { topicId: 'T', prerequisiteId: 'P1', strength: 'hard' },
  { topicId: 'T', prerequisiteId: 'P2', strength: 'hard' }
];
const bankQs = [];
['R', 'P1', 'P2', 'T'].forEach((id) => {
  bankQs.push(mq(id, 1, 's'), mq(id, 2, 's'), mq(id, 3, 'b'), mq(id, 4, 'a'));
});
const G2 = E.buildGraph(bankTopics, bankDeps, bankQs);

/** 按脚本作答：script[id] = [第一题结果, 第二题结果]；返回 [会话, 出过的 (知识点#第几题) 序列]。 */
function run2(session, script) {
  const seq = [];
  let s = session;
  for (let guard = 0; guard < 100; guard++) {
    const it = E.nextItem(G2, s);
    if (!it) break;
    seq.push(it.topicId + '#' + it.attempt);
    const r = script[it.topicId][it.attempt - 1];
    assert.ok(r, '脚本缺少 ' + it.topicId + ' 第 ' + it.attempt + ' 题');
    s = E.applyAnswer(G2, s, it.topicId, r);
  }
  return [s, seq];
}

test('题库：isTestable 看题库；有题库时 hasBank 为 true，回退模式为 false', () => {
  assert.strictEqual(G2.hasBank, true);
  assert.strictEqual(G.hasBank, false);
  assert.strictEqual(G2.bank.T.length, 4);
  assert.strictEqual(G.bank.T[0].type, 'legacy');
});

test('confirm=1：第一题答对 → 掌握，并推断祖先掌握；只问 1 题', () => {
  const [s, seq] = run2(E.createSession(G2, ['T'], { confirm: 1 }), { T: ['correct'] });
  assert.deepStrictEqual(seq, ['T#1']);
  ['T', 'P1', 'P2', 'R'].forEach((id) => assert.strictEqual(E.statusOf(s, id), 'mastered', id));
  assert.strictEqual(s.status.T.src, 'direct');
  assert.strictEqual(s.status.R.src, 'inferred');
});

test('默认 confirm=3：连续答对 3 题才掌握；只对 1 题不算掌握、继续出题', () => {
  let s = E.createSession(G2, ['T']);
  assert.strictEqual(s.confirm, 3);
  assert.strictEqual(E.needConfirm(G2, s, 'T'), 3);
  s = E.applyAnswer(G2, s, 'T', 'correct');
  assert.strictEqual(s.status.T, undefined);
  assert.strictEqual(E.nextQuestion(G2, s), 'T');
  assert.strictEqual(E.nextItem(G2, s).attempt, 2);
  s = E.applyAnswer(G2, s, 'T', 'correct');
  assert.strictEqual(s.status.T, undefined);
  s = E.applyAnswer(G2, s, 'T', 'correct');
  assert.strictEqual(E.statusOf(s, 'T'), 'mastered');
  ['P1', 'P2', 'R'].forEach((id) => assert.strictEqual(E.statusOf(s, id), 'mastered', id));
  assert.strictEqual(E.nextQuestion(G2, s), null);
});

test('confirm=3 但题库只有 2 题：答对 2 题即掌握', () => {
  const topics2 = [mk('M', { diagnostic_question: undefined })];
  const qs2 = [mq('M', 1, 's'), mq('M', 2, 'b')];
  const Gx = E.buildGraph(topics2, [], qs2);
  let s2 = E.createSession(Gx, ['M'], { confirm: 3 });
  assert.strictEqual(E.needConfirm(Gx, s2, 'M'), 2);
  s2 = E.applyAnswer(Gx, s2, 'M', 'correct');
  assert.strictEqual(s2.status.M, undefined);
  s2 = E.applyAnswer(Gx, s2, 'M', 'correct');
  assert.strictEqual(E.statusOf(s2, 'M'), 'mastered');
});

test('confirm 非法值回退到默认 3；可选 2/3/5', () => {
  assert.strictEqual(E.clampConfirm(2), 2);
  assert.strictEqual(E.clampConfirm(5), 5);
  assert.strictEqual(E.clampConfirm(4), 3);
  assert.strictEqual(E.clampConfirm('x'), 3);
  assert.strictEqual(E.createSession(G2, ['T'], { confirm: 5 }).confirm, 5);
});

test('第一题错 → 再出第二题（同一知识点），此时还没有结论、不回溯', () => {
  let s = E.createSession(G2, ['T']);
  s = E.applyAnswer(G2, s, 'T', 'wrong');
  assert.strictEqual(E.nextQuestion(G2, s), 'T');
  const it = E.nextItem(G2, s);
  assert.strictEqual(it.attempt, 2);
  assert.notStrictEqual(it.question.id, s.answers[0].qid);
  assert.strictEqual(s.status.T, undefined);
  assert.strictEqual(E.isUnconfirmed(s, 'T'), true);
});

test('错 + 错 → 薄弱，并向先修回溯（P1、P2 依次，再深入 R）', () => {
  // confirm=1：先修答对一次即掌握，方便检查回溯顺序
  const [s, seq] = run2(E.createSession(G2, ['T'], { confirm: 1 }), {
    T: ['wrong', 'skip'], P1: ['wrong', 'wrong'], R: ['correct'], P2: ['correct']
  });
  assert.deepStrictEqual(seq, ['T#1', 'T#2', 'P1#1', 'P1#2', 'R#1', 'P2#1']);
  assert.strictEqual(E.statusOf(s, 'T'), 'weak');
  assert.strictEqual(E.statusOf(s, 'P1'), 'weak');
  assert.strictEqual(E.statusOf(s, 'R'), 'mastered');
  const sum = E.summarize(G2, s);
  assert.deepStrictEqual(sum.roots.map((r) => r.id), ['P1']);
  assert.deepStrictEqual(sum.shaky, []);
});

test('错 + 对 → 不稳（shaky），且不向先修回溯', () => {
  const [s, seq] = run2(E.createSession(G2, ['T']), { T: ['wrong', 'correct'] });
  assert.deepStrictEqual(seq, ['T#1', 'T#2']);
  assert.strictEqual(E.statusOf(s, 'T'), 'shaky');
  assert.strictEqual(E.nextQuestion(G2, s), null);
  ['P1', 'P2', 'R'].forEach((id) => assert.strictEqual(E.statusOf(s, id), 'unknown', id));
  const sum = E.summarize(G2, s);
  assert.deepStrictEqual(sum.shaky, ['T']);
  assert.deepStrictEqual(sum.weak, []);
  assert.deepStrictEqual(sum.roots, []);
  assert.deepStrictEqual(sorted(sum.untested), ['P1', 'P2', 'R']);
  // 不稳的点要进学习路径
  assert.deepStrictEqual(sum.path.map((p) => [p.id, p.status]), [['T', 'shaky']]);
});

test('不稳的先修若同时被别处判为薄弱，路径含它及其后代', () => {
  const [s] = run2(E.createSession(G2, ['T'], { confirm: 1 }), {
    T: ['wrong', 'wrong'], P1: ['wrong', 'correct'], P2: ['wrong', 'wrong'], R: ['correct']
  });
  assert.strictEqual(E.statusOf(s, 'P1'), 'shaky');
  assert.strictEqual(E.statusOf(s, 'P2'), 'weak');
  const sum = E.summarize(G2, s);
  assert.deepStrictEqual(sum.roots.map((r) => r.id), ['P2']);
  assert.deepStrictEqual(sorted(sum.path.map((p) => p.id)), ['P1', 'P2', 'T']);
  assert.strictEqual(sum.path.find((p) => p.id === 'P1').status, 'shaky');
  assertTopological(sum.path.map((p) => p.id), G2);
});

test('第一题优先 standard；答对再出 challenge；答错再出 basic', () => {
  for (let i = 0; i < 60; i++) {
    const s0 = E.createSession(G2, ['P2'], { seed: 'k' + i });
    const first = E.nextItem(G2, s0).question;
    assert.strictEqual(first.difficulty, 'standard', '有 standard 时第一题应是 standard');
    const sWrong = E.applyAnswer(G2, s0, 'P2', 'wrong');
    assert.strictEqual(E.nextItem(G2, sWrong).question.id, 'P2_q3', '答错后应出唯一的 basic');
    const sRight = E.applyAnswer(G2, s0, 'P2', 'correct');
    assert.strictEqual(E.nextItem(G2, sRight).question.difficulty, 'advanced', '答对后应出拓展档');
  }
  // 没有 standard 时第一题退到 basic（仍不出拓展）
  const topics3 = [mk('M', { diagnostic_question: undefined })];
  const qsB = [mq('M', 1, 'b'), mq('M', 2, 'b'), mq('M', 3, 'a')];
  const GB = E.buildGraph(topics3, [], qsB);
  for (let i = 0; i < 20; i++) {
    const it = E.nextItem(GB, E.createSession(GB, ['M'], { seed: i }));
    assert.strictEqual(it.question.difficulty, 'basic');
  }
  // 没有 basic 时，答错后取同难度 standard
  const qs3 = [mq('M', 1, 's'), mq('M', 2, 's'), mq('M', 3, 's'), mq('M', 4, 'a')];
  const G3 = E.buildGraph(topics3, [], qs3);
  for (let i = 0; i < 20; i++) {
    const s1 = E.applyAnswer(G3, E.createSession(G3, ['M'], { seed: i }), 'M', 'wrong');
    assert.strictEqual(E.nextItem(G3, s1).question.difficulty, 'standard');
  }
  // 只有拓展档时才出拓展
  const qs4 = [mq('M', 1, 'a'), mq('M', 2, 'a')];
  const G4 = E.buildGraph(topics3, [], qs4);
  const s4 = E.applyAnswer(G4, E.createSession(G4, ['M'], { seed: 1 }), 'M', 'wrong');
  assert.strictEqual(E.nextItem(G4, s4).question.difficulty, 'advanced');
});

test('种子固定时选题确定；不同种子能得到不同选题', () => {
  const trace = (seed) => {
    const [s] = run2(E.createSession(G2, ['T'], { seed: seed }), {
      T: ['wrong', 'wrong'], P1: ['wrong', 'wrong'], R: ['wrong', 'wrong'], P2: ['wrong', 'wrong']
    });
    return s.answers.map((a) => a.qid).join(',');
  };
  assert.strictEqual(trace('abc'), trace('abc'));
  assert.strictEqual(trace(42), trace('42'));
  const variants = new Set();
  for (let i = 0; i < 40; i++) variants.add(trace('s' + i));
  assert.ok(variants.size > 5, '不同种子应产生不同的题目序列（得到 ' + variants.size + ' 种）');
  // 重放与逐步作答一致，题号也一致
  const [s2] = run2(E.createSession(G2, ['T'], { seed: 9 }), { T: ['wrong', 'correct'] });
  const r = E.replay(G2, ['T'], s2.answers, { seed: 9 });
  assert.deepStrictEqual(r, s2);
});

test('已出题避让：优先出没出过的题，全出过也不会卡住', () => {
  const avoid = ['T_q1', 'T_q2'];
  for (let i = 0; i < 40; i++) {
    const s0 = E.createSession(G2, ['T'], { seed: i, avoid: avoid });
    const first = E.nextItem(G2, s0).question;
    assert.ok(!avoid.includes(first.id), '第一题应避开出过的题：' + first.id);
  }
  const all = G2.bank.T.map((q) => q.id);
  const s1 = E.createSession(G2, ['T'], { seed: 1, avoid: all });
  const it = E.nextItem(G2, s1);
  assert.ok(it && all.includes(it.question.id));
  // 第二题：basic 优先于“没出过”——q3 是唯一 basic，即使它出过也还是 q3
  let hit = 0;
  for (let i = 0; i < 40; i++) {
    const s0 = E.createSession(G2, ['T'], { seed: i, avoid: ['T_q3'] });
    const a1 = E.nextItem(G2, s0).question;
    if (a1.difficulty !== 'standard') continue;
    const s2 = E.applyAnswer(G2, s0, 'T', 'wrong');
    assert.strictEqual(E.nextItem(G2, s2).question.id, 'T_q3');
    hit++;
  }
  assert.ok(hit > 5);
  // 同一次会话里不会重复出同一道题
  const [s3] = run2(E.createSession(G2, ['T']), { T: ['wrong', 'wrong'], P1: ['wrong', 'wrong'], P2: ['wrong', 'wrong'], R: ['wrong', 'wrong'] });
  const qids = s3.answers.map((a) => a.qid);
  assert.strictEqual(new Set(qids).size, qids.length);
});

test('题量上限按“题”计：2 题一个知识点；只答错第一题就到上限 → 暂按薄弱，标为未复测', () => {
  const [s, seq] = run2(E.createSession(G2, ['T'], { limit: 3 }), {
    T: ['wrong', 'wrong'], P1: ['wrong', 'wrong'], R: ['wrong', 'wrong'], P2: ['wrong', 'wrong']
  });
  assert.deepStrictEqual(seq, ['T#1', 'T#2', 'P1#1']);
  assert.strictEqual(s.answers.length, 3);
  assert.strictEqual(E.nextQuestion(G2, s), null);
  assert.strictEqual(E.statusOf(s, 'P1'), 'weak');
  const sum = E.summarize(G2, s);
  assert.deepStrictEqual(sum.unconfirmed, ['P1']);
  assert.strictEqual(sum.limitReached, true);
  assert.deepStrictEqual(sorted(sum.untested), ['P2', 'R']);
});

test('同一知识点只有一道题时：答错直接薄弱（无第二题）', () => {
  const G5 = E.buildGraph(bankTopics, bankDeps, [mq('T', 1, 's'), mq('P1', 1, 's'), mq('P2', 1, 's'), mq('R', 1, 's')]);
  let s = E.applyAnswer(G5, E.createSession(G5, ['T']), 'T', 'wrong');
  assert.strictEqual(E.statusOf(s, 'T'), 'weak');
  assert.strictEqual(E.nextQuestion(G5, s), 'P1');
});

test('applyAnswer 不修改入参（含 attempts）；答题记录带 qid 与用户答案', () => {
  const s0 = E.createSession(G2, ['T'], { seed: 5 });
  const snap = JSON.stringify(s0);
  const s1 = E.applyAnswer(G2, s0, 'T', 'wrong', { text: '42' });
  assert.strictEqual(JSON.stringify(s0), snap);
  assert.strictEqual(s1.answers[0].text, '42');
  assert.ok(/^T_q\d$/.test(s1.answers[0].qid));
  const snap1 = JSON.stringify(s1);
  E.applyAnswer(G2, s1, 'T', 'correct');
  assert.strictEqual(JSON.stringify(s1), snap1);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(s1)), s1);
});

test('判题（按题型）：choice 比字母，也接受选项文字；numeric 数值等价；short 精确匹配 + accept；self 自评', () => {
  const ch = { type: 'choice', answer: 'B', choices: [{ key: 'A', text: '1/2' }, { key: 'B', text: '-3' }, { key: 'C', text: '相切' }] };
  const j = (q, u) => E.judgeQuestion(q, u).verdict;
  assert.strictEqual(j(ch, 'B'), 'correct');
  assert.strictEqual(j(ch, ' b '), 'correct');
  assert.strictEqual(j(ch, '(B)'), 'correct');
  assert.strictEqual(j(ch, 'B.'), 'correct');
  assert.strictEqual(j(ch, 'A'), 'wrong');
  assert.strictEqual(j(ch, '-3'), 'correct');
  assert.strictEqual(j(ch, '－３'), 'correct');
  assert.strictEqual(j(ch, '1/2'), 'wrong');
  assert.strictEqual(j(ch, '相切'), 'wrong');
  assert.strictEqual(j(ch, 'E'), 'manual');
  assert.strictEqual(j(ch, '随便写'), 'manual');
  assert.strictEqual(j(ch, ''), 'manual');
  const num = { type: 'numeric', answer: '-1/2' };
  assert.strictEqual(j(num, '-0.5'), 'correct');
  assert.strictEqual(j(num, '－１/２'), 'correct');
  assert.strictEqual(j(num, '1/2'), 'wrong');
  const ord = { type: 'numeric', answer: '3，-2' };
  assert.strictEqual(j(ord, '3，-2'), 'correct');
  assert.strictEqual(j(ord, '3, -2'), 'correct');
  assert.strictEqual(j(ord, '-2，3'), 'wrong');       // 有序：顺序错
  assert.strictEqual(j(ord, '3'), 'wrong');
  const unord = { type: 'numeric', answer: '3，-2', unordered: true };
  assert.strictEqual(j(unord, '-2，3'), 'correct');
  assert.strictEqual(j(unord, '-2 和 3'), 'correct');
  assert.strictEqual(j(unord, '-2，4'), 'wrong');
  const sh = { type: 'short', answer: 'y=2x+1', accept: ['2x+1', 'f(x)=2x+1'] };
  assert.strictEqual(j(sh, 'y = 2x + 1'), 'correct');
  assert.strictEqual(j(sh, 'Y＝2X+1'), 'correct');
  assert.strictEqual(j(sh, 'f(x)=2x+1'), 'correct');
  assert.strictEqual(j(sh, 'y=1+2x'), 'manual');       // 等价写法无法可靠判断，交给自评
  const quad = { type: 'short', answer: '第三象限' };
  assert.strictEqual(j(quad, '第三象限'), 'correct');
  assert.strictEqual(j(quad, '第二象限'), 'manual');
  assert.strictEqual(j({ type: 'self', answer: '略' }, '略'), 'manual');
  assert.strictEqual(j({ type: 'legacy', answer: '3' }, '3.0'), 'correct');
});

test('PRNG：mulberry32 相同种子相同序列，输出在 [0,1)', () => {
  const a = E.mulberry32(123), b = E.mulberry32(123);
  for (let i = 0; i < 100; i++) { const x = a(); assert.strictEqual(x, b()); assert.ok(x >= 0 && x < 1); }
});

/* ------------------------------------------------------------ 答案规范化与判题 */
console.log('答案规范化与判题');

function verdict(user, ref) { return E.judgeAnswer(user, ref).verdict; }

test('规范化：全角转半角、去空格、中文标点、度', () => {
  assert.strictEqual(E.normalizeText('　１／２ '), '1/2');
  assert.strictEqual(E.normalizeText('90 度'), '90°');
  assert.strictEqual(E.normalizeText('－３，（２）'), '-3,(2)');
  assert.strictEqual(E.normalizeText('x²'), 'x^2');
  assert.strictEqual(E.normalizeText('A、B；C'), 'a,b;c');
  assert.strictEqual(E.normalizeText('答：60°。'), '60°');
});

test('分数与小数等价："１/２" vs "0.5"', () => {
  assert.strictEqual(verdict('１/２', '0.5'), 'correct');
  assert.strictEqual(verdict('0.5', '1/2'), 'correct');
  assert.strictEqual(verdict('2/4', '1/2'), 'correct');
  assert.strictEqual(verdict('-1/2', '-0.5'), 'correct');
  assert.strictEqual(verdict('－１／２', '-(1/2)'), 'correct');
  assert.strictEqual(verdict('1/3', '0.333'), 'wrong');
  assert.strictEqual(verdict('1又1/2', '3/2'), 'correct');
  assert.strictEqual(verdict('1 1/2', '1.5'), 'correct');
  assert.strictEqual(verdict('50%', '1/2'), 'correct');
  assert.strictEqual(verdict('3/5', '3/5'), 'correct');
  assert.strictEqual(verdict('3/5', '5/3'), 'wrong');
});

test('角度："90 度" vs "90°"', () => {
  assert.strictEqual(verdict('90 度', '90°'), 'correct');
  assert.strictEqual(verdict('90', '90°'), 'correct');
  assert.strictEqual(verdict('６０°', '60度'), 'correct');
  assert.strictEqual(verdict('50°', '60°'), 'wrong');
});

test('多个答案顺序无关："-3 和 -1/2" vs "-1/2，-3"', () => {
  assert.strictEqual(verdict('-3 和 -1/2', '-1/2，-3'), 'correct');
  assert.strictEqual(verdict('-1/2、-3', '-3 和 -1/2'), 'correct');
  assert.strictEqual(verdict('-3', '-3 和 -1/2'), 'wrong');
  assert.strictEqual(verdict('-3，-1/2，0', '-3 和 -1/2'), 'wrong');
  assert.strictEqual(verdict('x=3 或 x=2', 'x=2 或 x=3'), 'correct');
  assert.strictEqual(verdict('2,3', 'x=2 或 x=3'), 'correct');
  assert.strictEqual(verdict('3；3', '3；3'), 'correct');
});

test('带变量名的答案：x=… 可省略变量名，但 x、y 不能互换', () => {
  assert.strictEqual(verdict('3', 'x=3'), 'correct');
  assert.strictEqual(verdict('x=3', '3'), 'correct');
  assert.strictEqual(verdict('y=2，x=3', 'x=3，y=2'), 'correct');
  assert.strictEqual(verdict('3，2', 'x=3，y=2'), 'correct');
  assert.strictEqual(verdict('x=2，y=3', 'x=3，y=2'), 'wrong');
  assert.strictEqual(verdict('2，3', 'x=3，y=2'), 'wrong');
});

test('单位：别名等价，缺省单位放行，不同单位判错', () => {
  assert.strictEqual(verdict('12米', '12 m'), 'correct');
  assert.strictEqual(verdict('12', '12 m'), 'correct');
  assert.strictEqual(verdict('12 cm', '12 m'), 'wrong');
  assert.strictEqual(verdict('25 平方米', '25 m²'), 'correct');
  assert.strictEqual(verdict('1,000', '1000'), 'correct');
});

test('坐标等有括号的多值答案', () => {
  assert.strictEqual(verdict('（１，２）', '(1,2)'), 'correct');
  assert.strictEqual(verdict('(1, 2)', '(1,2)'), 'correct');
  assert.strictEqual(verdict('(2,1)', '(1,2)'), 'wrong');
  assert.strictEqual(verdict('(0.5,2)', '(1/2,2)'), 'correct');
});

test('无法可靠解析的答案（文字、代数式）：只在完全相同时判对，否则交给用户自评', () => {
  assert.strictEqual(verdict('相切', '相切'), 'correct');
  assert.strictEqual(verdict('相离', '相切'), 'manual');
  assert.strictEqual(verdict('y=2x+3', 'y=2x+3'), 'correct');
  assert.strictEqual(verdict('2x+3', 'y=2x+3'), 'correct');
  assert.strictEqual(verdict('y=3x+2', 'y=2x+3'), 'manual');
  assert.strictEqual(verdict('(x-2)^2-1', 'y=(x-2)²-1'), 'correct');
  assert.strictEqual(verdict('共 11 种', '共 11 种，每种有 6 个正方形'), 'manual');
  assert.strictEqual(verdict('', '3'), 'manual');
  assert.strictEqual(verdict('不知道', '3'), 'manual');
});

test('判题不抛异常：奇怪输入', () => {
  ['', ' ', '(', ')))', '1/0', '/', '--1', '1/2/3', '％', '😀', null, undefined, '１２３４５６７８９０１２３４５６７８９０/３'].forEach((u) => {
    ['3', '1/2', '相切', 'x=2 或 x=3', '', '(1,2)'].forEach((r) => {
      const v = E.judgeAnswer(u, r).verdict;
      assert.ok(['correct', 'wrong', 'manual'].includes(v));
    });
  });
});

/* ------------------------------------------------------------ 真实数据 */
console.log('真实数据');

const dataDir = path.join(__dirname, '..', 'data');
const topics = JSON.parse(fs.readFileSync(path.join(dataDir, 'topics.json'), 'utf8'));
const deps = JSON.parse(fs.readFileSync(path.join(dataDir, 'dependencies.json'), 'utf8'));
const stdFile = JSON.parse(fs.readFileSync(path.join(dataDir, 'cn-curriculum-standards.json'), 'utf8'));
const RG = E.buildGraph(topics, deps);
const formal = topics.filter((t) => !t.external);

function bfsAncestors(id) {
  const pre = new Map();
  deps.forEach((d) => { (pre.get(d.topicId) || pre.set(d.topicId, []).get(d.topicId)).push(d.prerequisiteId); });
  const seen = new Set();
  const q = [id];
  while (q.length) { (pre.get(q.shift()) || []).forEach((p) => { if (!seen.has(p)) { seen.add(p); q.push(p); } }); }
  return seen;
}

test('数据可加载：小学 284 + 初中 315 + 高中必修 143 + 选择性必修 128，没有外部节点；课标含第一学段', () => {
  const mathTopics = topics.filter((t) => String(t.id).startsWith('cnm_'));
  const mathDeps = deps.filter((d) => String(d.topicId).startsWith('cnm_'));
  assert.strictEqual(mathTopics.length, 870);
  assert.strictEqual(mathDeps.length, 1459);
  assert.strictEqual(topics.filter((t) => t.external).length, 0);
  assert.strictEqual(mathTopics.filter((t) => t.grade <= 6).length, 284);
  assert.strictEqual(mathTopics.filter((t) => t.grade >= 7 && t.grade <= 9).length, 315);
  assert.strictEqual(mathTopics.filter((t) => t.grade === 10 || t.grade === 11).length, 143);
  assert.strictEqual(mathTopics.filter((t) => t.grade >= 12).length, 128);
  assert.strictEqual(mathTopics.filter((t) => t.grade >= 10).length, 271);
  assert.ok(mathTopics.filter((t) => t.grade >= 10).every((t) => /^cnm_h\d{3,}$/.test(t.id)));
  assert.ok(formal.every((t) => E.isTestable(RG, t.id)));
  assert.ok(stdFile.items.length > 200);
  assert.ok(stdFile.items[0].id.indexOf('cms-2022:1.') === 0);
  assert.deepStrictEqual(mathTopics.map((t) => t.id + '\t' + t.name), topics.filter((t) => String(t.id).startsWith('cnm_')).map((t) => t.id + '\t' + t.name));
});

test('英语：小学 197、初中 180–260、高中 220–320，不与数学连边，非起点都有先修；整册按学科分开', () => {
  const enTopics = topics.filter((t) => String(t.id).startsWith('cne_'));
  const primary = enTopics.filter((t) => String(t.id).startsWith('cne_p'));
  const junior = enTopics.filter((t) => String(t.id).startsWith('cne_j'));
  const seniorEn = enTopics.filter((t) => String(t.id).startsWith('cne_h'));
  assert.strictEqual(primary.length, 275);
  assert.ok(junior.length >= 180 && junior.length <= 260, '初中英语知识点 ' + junior.length);
  assert.ok(seniorEn.length >= 220 && seniorEn.length <= 320, '高中英语知识点 ' + seniorEn.length);
  assert.strictEqual(enTopics.length, primary.length + junior.length + seniorEn.length);
  assert.ok(primary.every((t) => t.subject === 'english' && t.grade >= 3 && t.grade <= 6 && !t.external && (t.semester === '上' || t.semester === '下')));
  assert.ok(junior.every((t) => t.subject === 'english' && t.grade >= 7 && t.grade <= 9 && !t.external));
  assert.ok(junior.every((t) => (t.grade === 9 ? t.semester === '上' || t.semester === '全' : t.semester === '上' || t.semester === '下')));
  assert.ok(seniorEn.every((t) => t.subject === 'english' && t.grade >= 10 && t.grade <= 16 && t.semester === '上' && !t.external));
  assert.ok(seniorEn.some((t) => t.name === '虚拟语气'));
  assert.ok(enTopics.every((t) => ['语音', '词汇', '语法', '日常表达', '读写'].includes(t.domain)));
  const enDeps = deps.filter((d) => String(d.topicId).startsWith('cne_'));
  assert.ok(deps.every((d) => String(d.topicId).startsWith('cne_') === String(d.prerequisiteId).startsWith('cne_')));
  const cross = enDeps.filter((d) => String(d.topicId).startsWith('cne_j') && String(d.prerequisiteId).startsWith('cne_p'));
  assert.ok(cross.length >= 1, '初中英语应链到小学英语');
  assert.ok(!cross.some((d) => String(d.prerequisiteId).startsWith('cnm_')));
  const crossH = enDeps.filter((d) => String(d.topicId).startsWith('cne_h') && String(d.prerequisiteId).startsWith('cne_j'));
  assert.ok(crossH.length >= 8, '高中英语应链到初中英语');
  assert.ok(enDeps.filter((d) => String(d.topicId).startsWith('cne_h')).every((d) => String(d.prerequisiteId).startsWith('cne_')));
  const pre = new Map();
  enDeps.forEach((d) => { (pre.get(d.topicId) || pre.set(d.topicId, []).get(d.topicId)).push(d); });
  enTopics.forEach((t) => {
    if (t.id === 'cne_p001') {
      assert.ok(t.root_reason);
      return;
    }
    assert.ok(pre.get(t.id) && pre.get(t.id).length >= 1, t.id + ' 没有先修');
    pre.get(t.id).forEach((d) => {
      const src = RG.byId[t.id];
      const dst = RG.byId[d.prerequisiteId];
      const ra = src.grade * 2 + (src.semester === '下' ? 1 : 0);
      const rb = dst.grade * 2 + (dst.semester === '下' ? 1 : 0);
      assert.ok(rb <= ra, t.id + ' 的先修更晚 ' + d.prerequisiteId);
    });
  });
  const math4 = E.gradeTargets(RG, '四上');
  const en4 = E.gradeTargets(RG, '四上', 'english');
  assert.ok(math4.ids.length > 0 && math4.ids.every((id) => id.startsWith('cnm_') && RG.byId[id].grade === 4 && RG.byId[id].semester === '上'));
  assert.ok(en4.ids.length > 0 && en4.ids.every((id) => id.startsWith('cne_p') && RG.byId[id].grade === 4 && RG.byId[id].semester === '上'));
  assert.deepStrictEqual(E.gradeTargets(RG, '四上').ids, E.gradeTargets(RG, '四上', 'math').ids);
  const en8 = E.gradeTargets(RG, '八上', 'english');
  assert.strictEqual(en8.label, '八年级上册');
  assert.ok(en8.ids.length > 0 && en8.ids.every((id) => id.startsWith('cne_j') && RG.byId[id].grade === 8 && RG.byId[id].semester === '上'));
  assert.ok(E.gradeTargets(RG, '八上').ids.every((id) => id.startsWith('cnm_')));
  const en9 = E.gradeTargets(RG, '九全', 'english');
  assert.strictEqual(en9.label, '九年级全一册');
  assert.ok(en9.ids.length > 0 && en9.ids.every((id) => id.startsWith('cne_j') && RG.byId[id].grade === 9 && RG.byId[id].semester === '全'));
  const enGrade9 = E.gradeTargets(RG, '九年级', 'english');
  assert.ok(enGrade9.volumes.indexOf('九全') >= 0 && enGrade9.ids.every((id) => id.startsWith('cne_')));
  const mathGrade9 = E.gradeTargets(RG, '九年级');
  assert.ok(mathGrade9.ids.length > 0 && mathGrade9.ids.every((id) => id.startsWith('cnm_') && RG.byId[id].semester !== '全'));
  assert.deepStrictEqual(
    E.parseChapter('八年级下册 第8单元 Have you read Treasure Island yet'),
    { volume: '八下', chapterNo: '第8单元', chapterName: 'Have you read Treasure Island yet', section: '' }
  );
  assert.deepStrictEqual(
    E.parseChapter('必修第一册 欢迎单元 Welcome Unit'),
    { volume: '必修一', chapterNo: '欢迎单元', chapterName: 'Welcome Unit', section: '' }
  );
  assert.deepStrictEqual(
    E.parseChapter('必修第一册 第1单元 Teenage Life'),
    { volume: '必修一', chapterNo: '第1单元', chapterName: 'Teenage Life', section: '' }
  );
  assert.deepStrictEqual(
    E.parseChapter('选择性必修第一册 第1单元 People of Achievement'),
    { volume: '选必一', chapterNo: '第1单元', chapterName: 'People of Achievement', section: '' }
  );
  assert.strictEqual(E.gradeTargets(RG, '必修一'), null);
  assert.strictEqual(E.gradeTargets(RG, '选择性必修第四册'), null);
  const enB1 = E.gradeTargets(RG, '必修一', 'english');
  assert.strictEqual(enB1.label, '必修一（必修第一册）');
  assert.ok(enB1.ids.length > 0 && enB1.ids.every((id) => id.startsWith('cne_h') && RG.byId[id].grade === 10));
  const enS1 = E.gradeTargets(RG, '选必一', 'english');
  assert.strictEqual(enS1.label, '选必一（选择性必修第一册）');
  assert.ok(enS1.ids.length > 0 && enS1.ids.every((id) => id.startsWith('cne_h') && RG.byId[id].grade === 13));
  assert.ok(E.gradeTargets(RG, '选必一').ids.every((id) => id.startsWith('cnm_')));
  assert.ok(E.gradeTargets(RG, '选择性必修第一册').ids.every((id) => id.startsWith('cnm_')));
  const enS4 = E.gradeTargets(RG, '选必四', 'english');
  assert.strictEqual(enS4.label, '选必四（选择性必修第四册）');
  assert.ok(enS4.ids.every((id) => id.startsWith('cne_h') && RG.byId[id].grade === 16));
  assert.strictEqual(E.subjectOf(enTopics[0]), 'english');
  assert.strictEqual(E.subjectOf(topics.find((t) => t.id === 'cnm_p001')), 'math');
  const ces = stdFile.items.filter((it) => String(it.id).startsWith('ces-2022:'));
  const ces3 = ces.filter((it) => String(it.id).indexOf('ces-2022:3.') === 0);
  assert.ok(ces.length >= 20 && ces3.length >= 20, '三级课标 ' + ces3.length);
  assert.ok(ces.every((it) => it.verbatim === false && it.page_or_ref === '待核'));
  const cesH = stdFile.items.filter((it) => String(it.id).startsWith('ces-2017:H.'));
  assert.ok(cesH.length >= 20, '高中英语课标 ' + cesH.length);
  assert.ok(cesH.every((it) => it.verbatim === false && it.page_or_ref === '待核'));
  assert.ok(cesH.some((it) => String(it.id).indexOf('ces-2017:H.B.') === 0));
  assert.ok(cesH.some((it) => String(it.id).indexOf('ces-2017:H.S.') === 0));
  assert.strictEqual(stdFile.english.senior.year, 2025);
});

test('真实数据：祖先集合与独立 BFS 一致（全部知识点）', () => {
  topics.forEach((t) => {
    assert.deepStrictEqual(sorted(E.ancestors(RG, t.id)), sorted(bfsAncestors(t.id)), t.id);
  });
});

test('真实数据：先修子图不含外部节点，初中目标能回到小学，拓扑序合法', () => {
  let sawPrimary = false;
  formal.forEach((t) => {
    const sub = E.subgraph(RG, [t.id]);
    assert.strictEqual(sub.nodes[sub.nodes.length - 1], t.id);
    assertTopological(sub.nodes, RG);
    assert.ok(sub.nodes.every((id) => !RG.byId[id].external));
    if (t.grade >= 7 && sub.nodes.some((id) => RG.byId[id].grade <= 6)) sawPrimary = true;
  });
  assert.ok(sawPrimary, '至少有一个初中或高中知识点的祖先里有小学知识点');
  const senior = formal.filter((t) => t.grade >= 10 && String(t.id).startsWith('cnm_'));
  assert.ok(senior.length === 271);
  assert.ok(senior.every((t) => E.subgraph(RG, [t.id]).nodes.length > 1), '高中知识点都有先修');
  assert.ok(senior.some((t) => E.subgraph(RG, [t.id]).nodes.some((id) => RG.byId[id].grade >= 7 && RG.byId[id].grade <= 9)),
    '至少有一个高中知识点的祖先里有初中知识点');
});

test('旧 id 别名：cnm_ext_* 已不在图中，resolveTargets 跳到小学正式知识点', () => {
  const aliases = JSON.parse(fs.readFileSync(path.join(dataDir, 'id-aliases.json'), 'utf8')).aliases;
  assert.strictEqual(Object.keys(aliases).length, 18);
  for (let i = 1; i <= 18; i++) {
    const key = 'cnm_ext_' + String(i).padStart(3, '0');
    assert.ok(!RG.byId[key], key + ' 不应再作为知识点');
    assert.ok(aliases[key] && aliases[key].name && aliases[key].targets.length);
    const ids = E.resolveTargets([key], aliases);
    assert.ok(ids.length >= 1 && ids.length === new Set(ids).size, key);
    ids.forEach((id) => {
      const t = RG.byId[id];
      assert.ok(t && t.grade <= 6 && !t.external, key + ' -> ' + id);
    });
    const s = E.createSession(RG, ids, { limit: 2 });
    assert.ok(ids.indexOf(E.nextQuestion(RG, s)) >= 0, key);
  }
  const mixed = E.resolveTargets(['cnm_ext_002', 'cnm_001'], aliases);
  assert.ok(mixed.indexOf('cnm_001') >= 0);
  assert.ok(mixed.some((id) => RG.byId[id].grade <= 6));
  assert.deepStrictEqual(E.resolveTargets(['nope'], aliases), ['nope']);
  assert.deepStrictEqual(E.resolveTargets(['cnm_221'], null), ['cnm_221']);
});

test('真实数据：cnm_221（配方法）——首问目标；答错后 hard 先修在前', () => {
  let s = E.createSession(RG, ['cnm_221']);
  assert.strictEqual(E.nextQuestion(RG, s), 'cnm_221');
  s = E.applyAnswer(RG, s, 'cnm_221', 'wrong');
  const prereqs = RG.prereqs.cnm_221;
  const firstHard = prereqs.find((p) => p.strength === 'hard').id;
  assert.strictEqual(E.nextQuestion(RG, s), firstHard);
});

test('真实数据：答对目标即跳过全部祖先', () => {
  const s = E.applyAnswer(RG, E.createSession(RG, ['cnm_221']), 'cnm_221', 'correct');
  assert.strictEqual(E.nextQuestion(RG, s), null);
  const anc = bfsAncestors('cnm_221');
  assert.ok(anc.size > 30);
  anc.forEach((id) => assert.strictEqual(E.statusOf(s, id), 'mastered', id));
});

// 简单可复现的伪随机数
function rng(seed) { let x = seed >>> 0; return () => { x = (Math.imul(x, 1664525) + 1013904223) >>> 0; return x / 4294967296; }; }

/** 一致的“学生”：已掌握集合对祖先封闭。 */
function makeStudent(rand, p) {
  const known = new Set();
  topics.forEach((t) => {
    if (rand() < p) { known.add(t.id); bfsAncestorsCached(t.id).forEach((a) => known.add(a)); }
  });
  return known;
}
const ancCache = new Map();
function bfsAncestorsCached(id) { if (!ancCache.has(id)) ancCache.set(id, bfsAncestors(id)); return ancCache.get(id); }

function simulate(targets, known, limit) {
  let s = E.createSession(RG, targets, { limit: limit });
  const asked = [];
  for (let guard = 0; guard < 500; guard++) {
    const q = E.nextQuestion(RG, s);
    if (!q) break;
    asked.push(q);
    s = E.applyAnswer(RG, s, q, known.has(q) ? 'correct' : 'wrong');
  }
  return { s: s, asked: asked };
}

test('真实数据：一致的学生 + 无限题量 => 薄弱集合与根因精确还原', () => {
  const rand = rng(20261017);
  let cases = 0;
  for (let round = 0; round < 3; round++) {
    const known = makeStudent(rand, [0.04, 0.12, 0.3][round]);
    formal.forEach((t) => {
      const { s, asked } = simulate([t.id], known, 9999);
      cases++;
      assert.strictEqual(new Set(asked).size, asked.length, '不应重复出题 ' + t.id);
      assert.ok(asked.every((id) => !RG.byId[id].external));
      const sum = E.summarize(RG, s);
      const sub = E.subgraph(RG, [t.id]);
      const unknown = sub.nodes.filter((id) => E.isTestable(RG, id) && !known.has(id));
      assert.deepStrictEqual(sorted(sum.weak), sorted(unknown), '薄弱集合 ' + t.id);
      sum.mastered.forEach((id) => assert.ok(known.has(id), id + ' 被判掌握但学生不会'));
      const expectRoots = unknown.filter((id) => RG.prereqs[id].every((p) => !unknown.includes(p.id)));
      assert.deepStrictEqual(sorted(sum.roots.map((r) => r.id)), sorted(expectRoots), '根因 ' + t.id);
      // 路径：拓扑序、不含已掌握、覆盖所有薄弱点、含全部根因
      const pathIds = sum.path.map((p) => p.id);
      assertTopological(pathIds, RG);
      sum.path.forEach((p) => assert.notStrictEqual(p.status, 'mastered'));
      sum.weak.forEach((id) => assert.ok(pathIds.includes(id), '薄弱点应在路径中 ' + id));
      sum.roots.forEach((r) => assert.ok(pathIds.includes(r.id)));
      if (unknown.length) assert.strictEqual(pathIds[pathIds.length - 1], t.id);
      // 要么全对（1 题），要么 hard/soft 回溯
      if (known.has(t.id)) assert.strictEqual(asked.length, 1);
      assert.strictEqual(sum.finished, true);
      assert.strictEqual(sum.limitReached, false);
    });
  }
  assert.ok(cases >= 900);
});

test('真实数据：题量上限（8/12/20）永远不被突破，且仍满足根因/路径定义', () => {
  const rand = rng(7);
  [8, 12, 20].forEach((limit) => {
    const known = makeStudent(rand, 0.02);
    let capped = 0;
    formal.forEach((t) => {
      const { s, asked } = simulate([t.id], known, limit);
      assert.ok(asked.length <= limit);
      if (asked.length === limit) capped++;
      const sum = E.summarize(RG, s);
      assert.strictEqual(sum.asked, asked.length);
      sum.roots.forEach((r) => {
        assert.strictEqual(E.statusOf(s, r.id), 'weak');
        RG.prereqs[r.id].forEach((p) => assert.notStrictEqual(E.statusOf(s, p.id), 'weak'));
      });
      const pathIds = sum.path.map((p) => p.id);
      assertTopological(pathIds, RG);
      sum.path.forEach((p) => assert.notStrictEqual(p.status, 'mastered'));
      if (sum.limitReached) assert.ok(sum.untested.length > 0);
      const all = new Set(sum.mastered.concat(sum.weak, sum.untested));
      assert.strictEqual(all.size, s.order.length);
    });
    if (limit === 8) assert.ok(capped > 0, '应有触发上限的目标');
  });
});

test('真实数据：什么都不会的学生，在上限处停下，未测节点被标出', () => {
  const none = new Set();
  const { s, asked } = simulate(['cnm_221'], none, 12);
  assert.strictEqual(asked.length, 12);
  const sum = E.summarize(RG, s);
  assert.strictEqual(sum.limitReached, true);
  assert.ok(sum.untested.length > 0);
  assert.ok(sum.roots.length >= 1);
});

test('真实数据：整章作为目标——会的学生只需问“最末端”的目标', () => {
  const chapter = formal.filter((t) => t.chapter.startsWith('七上 第一章 '));
  const ids = chapter.map((t) => t.id);
  assert.ok(ids.length >= 5);
  const known = new Set(topics.map((t) => t.id));
  const { s, asked } = simulate(ids, known, 12);
  const idSet = new Set(ids);
  const maximal = ids.filter((id) => !ids.some((o) => o !== id && bfsAncestorsCached(o).has(id) && idSet.has(o)));
  assert.strictEqual(asked.length, maximal.length);
  ids.forEach((id) => assert.strictEqual(E.statusOf(s, id), 'mastered'));
  // 什么都不会：每个目标都会被问到或被标未测，不会漏
  const r = simulate(ids, new Set(), 20);
  const sum = E.summarize(RG, r.s);
  ids.forEach((id) => assert.ok(sum.weak.includes(id) || sum.untested.includes(id), id));
});

test('真实数据：replay 与 JSON 往返得到相同会话', () => {
  const known = makeStudent(rng(3), 0.1);
  const { s } = simulate(['cnm_232'], known, 12);
  const r = E.replay(RG, ['cnm_232'], s.answers, { limit: 12 });
  assert.deepStrictEqual(r, s);
  assert.deepStrictEqual(E.replay(RG, JSON.parse(JSON.stringify(s.targets)), JSON.parse(JSON.stringify(s.answers)), { limit: 12 }), s);
});

test('真实数据：路径图布局——所有边方向一致，节点不丢', () => {
  const { s } = simulate(['cnm_232'], new Set(), 12);
  const sum = E.summarize(RG, s);
  const lay = E.layout(RG, s, sum);
  const layer = Object.fromEntries(lay.nodes.map((n) => [n.id, n.layer]));
  lay.edges.forEach((e) => assert.ok(layer[e.from] < layer[e.to]));
  sum.path.forEach((p) => assert.ok(layer[p.id] !== undefined));
  assert.ok(layer.cnm_232 === lay.layers - 1);
});

test('真实数据：诊断题答案能被自己的判题器接受（判对率检查）', () => {
  let bad = [];
  formal.forEach((t) => {
    const a = t.diagnostic_question.answer;
    if (E.judgeAnswer(a, a).verdict !== 'correct') bad.push(t.id);
  });
  assert.deepStrictEqual(bad, []);
});

test('真实数据：章节名可解析', () => {
  formal.forEach((t) => {
    const c = E.parseChapter(t.chapter);
    assert.ok(c.volume && c.chapterNo && c.chapterName, t.chapter);
  });
});

/* ------------------------------------------------------------ 题库数据（data/questions.json） */
console.log('题库数据');

const questions = JSON.parse(fs.readFileSync(path.join(dataDir, 'questions.json'), 'utf8'));
const RGQ = E.buildGraph(topics, deps, questions);
const qByTopic = {};
questions.forEach((q) => { (qByTopic[q.topicId] = qByTopic[q.topicId] || []).push(q); });
const NUM_RE = /^-?\d+(\.\d+)?(\/\d+(\.\d+)?)?$/;

test('题库：每个正式知识点至少 3 题；id 唯一且格式正确；外部节点无题；含 basic 与 standard', () => {
  const ids = new Set();
  questions.forEach((q) => {
    assert.ok(!ids.has(q.id), '重复 id ' + q.id);
    ids.add(q.id);
    assert.ok(new RegExp('^' + q.topicId + '_q[1-9]\\d*$').test(q.id), q.id);
    assert.ok(RG.byId[q.topicId] && !RG.byId[q.topicId].external, q.id + ' 的 topicId 无效');
  });
  formal.forEach((t) => {
    const qs = qByTopic[t.id] || [];
    assert.ok(qs.length >= 3, t.id + ' 只有 ' + qs.length + ' 题');
    const ds = new Set(qs.map((q) => q.difficulty));
    assert.ok(ds.has('basic') && ds.has('standard'), t.id + ' 缺少 basic 或 standard');
    if (t.grade >= 1 && t.grade <= 6 && String(t.id).startsWith('cnm_p')) {
      assert.ok(ds.has('challenge'), t.id + ' 缺少 challenge');
    }
    assert.ok(qs.some((q) => q.id === t.id + '_q1'), t.id + ' 缺 q1');
    assert.ok(qs.filter((q) => q.id !== t.id + '_q1').some((q) => q.difficulty === 'basic'), t.id + ' 除 q1 外没有 basic');
  });
});

test('题库：type / difficulty 合法；必填字段非空；numeric + choice 占 60% 以上', () => {
  let auto = 0;
  questions.forEach((q) => {
    assert.ok(['numeric', 'choice', 'short', 'self'].includes(q.type), q.id);
    assert.ok(['basic', 'standard', 'challenge', 'advanced'].includes(q.difficulty), q.id);
    ['prompt', 'answer', 'explanation'].forEach((f) => assert.ok(typeof q[f] === 'string' && q[f].trim(), q.id + ' ' + f));
    if (q.type === 'numeric' || q.type === 'choice') auto++;
  });
  assert.ok(auto / questions.length >= 0.6, 'numeric+choice 占比 ' + (auto / questions.length));
});

test('题库：带 figure 的题是可解析的内联 SVG，不引用外网；图形选项不把名称写进图', () => {
  let n = 0;
  questions.forEach((q) => {
    const blobs = [];
    if (q.figure != null) blobs.push(['题干', q.figure]);
    (q.choices || []).forEach((c) => { if (c.figure != null) blobs.push(['选项' + c.key, c.figure]); });
    if (!blobs.length && q.hideChoiceText == null) return;
    n++;
    if (q.hideChoiceText != null) {
      assert.strictEqual(q.hideChoiceText, true, q.id);
      assert.strictEqual(q.type, 'choice', q.id);
      q.choices.forEach((c) => {
        assert.ok(c.figure, q.id + ' 选项 ' + c.key + ' 缺少图');
        assert.ok(!c.text || c.figure.indexOf(c.text) < 0, q.id + ' 图中写出了名称 ' + c.text);
      });
    }
    blobs.forEach((pair) => {
      const svg = pair[1];
      assert.strictEqual(typeof svg, 'string', q.id + pair[0]);
      assert.ok(svg.indexOf('<svg') === 0 && svg.indexOf('viewBox=') > 0, q.id + ' ' + pair[0] + ' 不是带 viewBox 的 svg');
      assert.ok(!/<\s*script|foreignObject|<\s*image\b/i.test(svg), q.id + ' 图含不允许的标签');
      const probe = svg.replace('xmlns="http://www.w3.org/2000/svg"', '');
      assert.ok(!/https?:\/\//i.test(probe), q.id + ' 图引用了外网');
      assert.ok(!/url\(\s*(?!#)/i.test(svg), q.id + ' 图有外部 url()');
    });
  });
  assert.ok(n >= 80, '带图的题太少：' + n);
});

test('题库：初中生物有内联结构示意图', () => {
  const bio = questions.filter((q) => String(q.topicId || '').startsWith('cnb_') && q.figure);
  assert.ok(bio.length >= 35 && bio.length <= 50, '生物配图题数 ' + bio.length);
  ['cnb_j003_q1', 'cnb_j004_q1', 'cnb_j050_q3'].forEach((id) => {
    const q = questions.find((item) => item.id === id);
    assert.ok(q && q.figure && q.figure.indexOf('currentColor') > 0, id);
    assert.ok(q.figure.indexOf('viewBox=') > 0, id);
  });
});

test('题库：初中地理有内联示意图', () => {
  const geo = questions.filter((q) => String(q.topicId || '').startsWith('cng_') && q.figure);
  assert.ok(geo.length >= 35 && geo.length <= 50, '地理配图题数 ' + geo.length);
  ['cng_j001_q3', 'cng_j005_q3', 'cng_j034_q1'].forEach((id) => {
    const q = questions.find((item) => item.id === id);
    assert.ok(q && q.figure && q.figure.indexOf('currentColor') > 0, id);
    assert.ok(q.figure.indexOf('viewBox=') > 0, id);
  });
});

test('题库：choice 题有 3–4 个选项、key 不重复、answer 是某个选项的 key', () => {
  let n = 0;
  questions.filter((q) => q.type === 'choice').forEach((q) => {
    n++;
    assert.ok(Array.isArray(q.choices) && q.choices.length >= 3 && q.choices.length <= 4, q.id);
    const keys = q.choices.map((c) => c.key);
    assert.strictEqual(new Set(keys).size, keys.length, q.id + ' key 重复');
    assert.ok(keys.includes(q.answer), q.id + ' answer 不在选项里');
    assert.strictEqual(new Set(q.choices.map((c) => c.text.trim())).size, keys.length, q.id + ' 选项文字重复');
  });
  assert.ok(n > 100);
});

test('题库：numeric 题的 answer 能被解析为数（整数/小数/分数/负数，多个答案用「，」分隔）', () => {
  let n = 0;
  questions.filter((q) => q.type === 'numeric').forEach((q) => {
    n++;
    const parts = q.answer.split(/[，,]/).map((x) => x.replace(/\s/g, ''));
    parts.forEach((x) => assert.ok(NUM_RE.test(x), q.id + ' answer=' + q.answer));
    if (q.unordered) assert.ok(parts.length > 1, q.id + ' unordered 但只有一个答案');
  });
  assert.ok(n > 500);
});

test('英语题：自包含、不引用课标或上一题，答案能被判对', () => {
  const enQs = questions.filter((q) => String(q.topicId).startsWith('cne_'));
  const juniorTopics = topics.filter((t) => String(t.id).startsWith('cne_j')).length;
  assert.ok(enQs.length >= 197 * 4 + juniorTopics * 3, '英语题 ' + enQs.length);
  enQs.forEach((q) => {
    assert.ok(!/^(同一|上题|该题|同上)/.test(String(q.prompt).trim()), q.id);
    assert.ok(!/本知识点|课标|是否要求/.test(q.prompt), q.id);
    assert.ok(q.type === 'numeric' || q.type === 'choice', q.id);
    const verdict = E.judgeQuestion(q, q.type === 'choice' ? q.answer : q.answer).verdict;
    assert.strictEqual(verdict, 'correct', q.id);
  });
});

test('物理：人教版八上 28、八下 24、九全 40，只在物理内部连边，mathLinks 指向数学，整册按学科分开', () => {
  const phy = topics.filter((t) => /^cnp_\d/.test(String(t.id)));
  const count = (g, s) => phy.filter((t) => t.grade === g && t.semester === s).length;
  assert.strictEqual(phy.length, 92);
  assert.strictEqual(count(8, '上'), 28);
  assert.strictEqual(count(8, '下'), 24);
  assert.strictEqual(count(9, '全'), 40);
  assert.ok(phy.every((t) => t.subject === 'physics' && E.subjectOf(t) === 'physics' && !t.external));
  assert.ok(phy.every((t) => ['物质', '运动和相互作用', '能量', '跨学科实践'].includes(t.domain)));
  assert.ok(phy.every((t) => E.parseChapter(t.chapter).section && /^(八上|八下|九全)$/.test(E.parseChapter(t.chapter).volume)));
  assert.ok(phy.every((t) => (t.standards || []).length >= 1 && t.standards.every((s) => s.id.startsWith('cps-2022:'))));
  const order = new Map(phy.map((t, i) => [t.id, i]));
  const phyDeps = deps.filter((d) => /^cnp_\d/.test(String(d.topicId)));
  assert.ok(phyDeps.length >= 92);
  phyDeps.forEach((d) => {
    assert.ok(/^cnp_\d/.test(String(d.prerequisiteId)), '初中物理的先修必须也是初中物理 ' + d.topicId);
    assert.ok(order.get(d.prerequisiteId) < order.get(d.topicId), d.topicId + ' 的先修不在教材前面');
  });
  const links = phy.flatMap((t) => t.mathLinks || []);
  assert.ok(links.length >= 20);
  assert.ok(links.every((l) => String(l.id).startsWith('cnm_') && RG.byId[l.id] && l.reason));
  const p8 = E.gradeTargets(RG, '八上', 'physics');
  assert.strictEqual(p8.ids.length, 28);
  assert.ok(E.gradeTargets(RG, '八上').ids.every((id) => id.startsWith('cnm_')));
  assert.strictEqual(E.gradeTargets(RG, '九年级', 'physics').ids.length, 40);
  assert.strictEqual(E.gradeTargets(RG, '九全', 'physics').label, '九年级全一册');
  assert.strictEqual(stdFile.items.filter((it) => String(it.id).startsWith('cps-2022:')).length, 89);
  assert.ok(stdFile.physics && /2025/.test(stdFile.physics.title));
});

test('高中物理：必修一 27、必修二 25、必修三 37、选必一 28、选必二 26、选必三 34，先修只连物理且不指向更晚的册，整册按学科分开', () => {
  const sen = topics.filter((t) => /^cnp_h\d/.test(String(t.id)));
  const vols = ['必修一', '必修二', '必修三', '选必一', '选必二', '选必三'];
  const want = [27, 25, 37, 28, 26, 34];
  assert.strictEqual(sen.length, 177);
  sen.forEach((t) => {
    assert.ok(t.subject === 'physics' && E.subjectOf(t) === 'physics' && !t.external && t.semester === '上', t.id);
    assert.ok(t.grade >= 10 && t.grade <= 15, t.id);
    assert.ok(vols[t.grade - 10] === E.parseChapter(t.chapter).volume && E.parseChapter(t.chapter).section, t.id + ' 章节');
    assert.ok(['物质', '运动和相互作用', '能量', '跨学科实践'].includes(t.domain), t.id);
    assert.ok((t.standards || []).length >= 1 && t.standards.every((x) => x.id.startsWith('cps-hs-2017:')), t.id + ' 课标');
  });
  vols.forEach((v, i) => {
    assert.strictEqual(sen.filter((t) => t.grade === 10 + i).length, want[i], v);
    const g = E.gradeTargets(RG, v, 'physics');
    assert.strictEqual(g.ids.length, want[i], v + ' 整册');
    assert.ok(E.gradeTargets(RG, v, 'english') === null || E.gradeTargets(RG, v, 'english').ids.every((id) => id.startsWith('cne_')));
  });
  assert.strictEqual(E.gradeTargets(RG, '必修一', 'physics').label, '必修一（必修第一册）');
  assert.strictEqual(E.gradeTargets(RG, '选必三', 'physics').ids.length, 34);
  assert.ok(E.gradeTargets(RG, '八上', 'physics').ids.every((id) => /^cnp_\d/.test(id)));
  const rank = new Map(topics.filter((t) => String(t.id).startsWith('cnp_')).map((t) => [t.id, /^cnp_h/.test(t.id) ? 100 + t.grade : t.grade]));
  const order = new Map(sen.map((t, i) => [t.id, i]));
  const senDeps = deps.filter((d) => /^cnp_h\d/.test(String(d.topicId)));
  assert.ok(senDeps.length >= 400);
  senDeps.forEach((d) => {
    assert.ok(String(d.prerequisiteId).startsWith('cnp_'), '跨学科边 ' + d.topicId);
    assert.ok(rank.get(d.prerequisiteId) <= rank.get(d.topicId), d.topicId + ' 的先修在更晚的册');
    if (/^cnp_h/.test(d.prerequisiteId)) assert.ok(order.get(d.prerequisiteId) < order.get(d.topicId), d.topicId + ' 的先修不在教材前面');
  });
  assert.ok(deps.filter((d) => /^cnp_\d/.test(String(d.topicId))).every((d) => /^cnp_\d/.test(String(d.prerequisiteId))), '初中物理不能依赖高中');
  assert.ok(senDeps.some((d) => /^cnp_\d/.test(String(d.prerequisiteId))), '高中应连回初中物理');
  const links = sen.flatMap((t) => t.mathLinks || []);
  assert.ok(links.length >= 40 && links.every((l) => String(l.id).startsWith('cnm_') && RG.byId[l.id] && l.reason));
  const hs = stdFile.items.filter((it) => String(it.id).startsWith('cps-hs-2017:'));
  assert.strictEqual(hs.length, 108);
  assert.ok(hs.every((it) => it.verbatim === false && it.page_or_ref === '待核'));
  assert.ok(stdFile.physics_senior && /2020/.test(stdFile.physics_senior.title) && /2019/.test(stdFile.physics_senior.textbook));
  const sq = questions.filter((q) => /^cnp_h\d/.test(String(q.topicId)));
  assert.strictEqual(sq.length, 177 * 4);
  sq.forEach((q) => assert.ok(q.verify && !/免费|AI ?初稿/.test(q.prompt + q.explanation), q.id));
});

test('物理题：每个知识点 4 题，带单位的数值题只填数值，答案能被判对', () => {
  const phyAll = topics.filter((t) => String(t.id).startsWith('cnp_'));
  const pq = questions.filter((q) => String(q.topicId).startsWith('cnp_'));
  assert.strictEqual(pq.length, phyAll.length * 4);
  pq.forEach((q) => {
    assert.ok(q.type === 'numeric' || q.type === 'choice', q.id);
    assert.ok(q.verify, q.id + ' 没有 verify');
    if (q.type === 'numeric') assert.ok(/只填数值/.test(q.prompt), q.id + ' 题干要说明只填数值');
    assert.strictEqual(E.judgeQuestion(q, q.answer).verdict, 'correct', q.id);
  });
  const speedQ = { id: 'x', type: 'numeric', answer: '20', prompt: '' };
  assert.strictEqual(E.judgeQuestion(speedQ, '20 m/s').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion(speedQ, '20m/s').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion({ id: 'y', type: 'numeric', answer: '15000', prompt: '' }, '15000Pa').verdict, 'correct');
});

test('百分数题：percent 题接受 50 和 50%，不接受 0.5；不带 percent 的题行为不变', () => {
  const pq = questions.filter((q) => q.percent === true);
  assert.ok(pq.length >= 2, 'percent 题 ' + pq.length);
  pq.forEach((q) => {
    assert.ok(String(q.topicId).startsWith('cnp_') && q.type === 'numeric' && /百分之多少|百分比|%/.test(q.prompt), q.id);
    const a = q.answer;
    assert.strictEqual(E.judgeQuestion(q, a).verdict, 'correct', q.id + ' ' + a);
    assert.strictEqual(E.judgeQuestion(q, a + '%').verdict, 'correct', q.id + ' ' + a + '%');
    assert.strictEqual(E.judgeQuestion(q, a + ' %').verdict, 'correct', q.id + ' ' + a + ' %');
    assert.strictEqual(E.judgeQuestion(q, a + '％').verdict, 'correct', q.id + ' 全角');
    assert.strictEqual(E.judgeQuestion(q, String(Number(a) / 100)).verdict, 'wrong', q.id + ' 小数');
    assert.strictEqual(E.judgeQuestion(q, String(Number(a) + 1) + '%').verdict, 'wrong', q.id + ' 错值');
  });
  assert.ok(questions.every((q) => q.percent !== true || String(q.topicId).startsWith('cnp_')));
  const plain = { id: 'm', type: 'numeric', answer: '0.5', prompt: '' };
  assert.strictEqual(E.judgeQuestion(plain, '50%').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion({ id: 'n', type: 'numeric', answer: '50', prompt: '' }, '50%').verdict, 'wrong');
});

test('题库：q1 由 diagnostic_question 迁移（题干以原题开头，或标注了 fixed_from_source）', () => {
  formal.forEach((t) => {
    const q1 = qByTopic[t.id].find((q) => q.id === t.id + '_q1');
    assert.ok(q1.prompt.startsWith(t.diagnostic_question.question) || q1.fixed_from_source, t.id);
  });
});

test('题库：判题器接受每道题自己的参考答案（self 一律自评）', () => {
  const bad = [];
  questions.forEach((q) => {
    const v = E.judgeQuestion(q, q.type === 'choice' ? q.answer : q.answer).verdict;
    const want = q.type === 'self' ? 'manual' : 'correct';
    if (v !== want) bad.push(q.id + ':' + v);
    if (q.type === 'choice') {
      const text = q.choices.find((c) => c.key === q.answer).text;
      // 选项文字本身是单个字母（如 x、D）时和选项字母无法区分，按字母处理；界面里选择题是点选项，不受影响
      if (!/^[A-Za-z]$/.test(text.trim()) && E.judgeQuestion(q, text).verdict !== 'correct') bad.push(q.id + ':text');
      q.choices.filter((c) => c.key !== q.answer).forEach((c) => {
        if (E.judgeQuestion(q, c.key).verdict !== 'wrong') bad.push(q.id + ':wrong-' + c.key);
      });
    }
    if (q.type === 'numeric' && !q.unordered && E.judgeQuestion(q, '999999').verdict === 'correct') bad.push(q.id + ':999999');
  });
  assert.deepStrictEqual(bad.slice(0, 20), []);
});

test('带题库的图：每个正式知识点可测、外部节点不可测；hasBank 为 true', () => {
  assert.strictEqual(RGQ.hasBank, true);
  assert.ok(formal.every((t) => E.isTestable(RGQ, t.id)));
  assert.ok(topics.filter((t) => t.external).every((t) => !E.isTestable(RGQ, t.id)));
});

console.log('带题库的真实诊断');

/** 学生：known 一次答对；flaky 第一题错第二题对；其余两题都错 */
function simulateBank(targets, known, flaky, limit, seed, confirm) {
  let s = E.createSession(RGQ, targets, {
    limit: limit, seed: seed == null ? 'sim' : seed,
    confirm: confirm == null ? E.DEFAULT_CONFIRM : confirm
  });
  const asked = [];
  for (let guard = 0; guard < 2000; guard++) {
    const it = E.nextItem(RGQ, s);
    if (!it) break;
    asked.push(it.topicId + '#' + it.attempt);
    let r = 'wrong';
    if (known.has(it.topicId)) r = 'correct';
    else if (flaky.has(it.topicId)) r = it.attempt === 1 ? 'wrong' : 'correct';
    s = E.applyAnswer(RGQ, s, it.topicId, r);
  }
  return { s: s, asked: asked };
}

test('小学回溯：答错初中「正数与负数」会问到小学，学习路径按年级从低到高', () => {
  const { s, asked } = simulateBank(['cnm_001'], new Set(), new Set(), 80, 'primary');
  const ids = asked.map((x) => x.split('#')[0]);
  assert.ok(ids.indexOf('cnm_001') >= 0);
  assert.ok(ids.filter((id) => id === 'cnm_001').length <= 2);
  assert.ok(ids.some((id) => RGQ.byId[id].grade === 6), '应问到六年级');
  assert.ok(ids.some((id) => RGQ.byId[id].grade === 1), '应继续问到一年级');
  const per = {};
  ids.forEach((id) => { per[id] = (per[id] || 0) + 1; });
  Object.keys(per).forEach((id) => assert.ok(per[id] <= 2, id + ' 超过 2 题'));
  const sum = E.summarize(RGQ, s);
  const ranks = sum.path.map((p) => E.gradeRank(RGQ, p.id));
  for (let i = 1; i < ranks.length; i++) {
    assert.ok(ranks[i] >= ranks[i - 1], '路径应按年级从低到高：' + sum.path[i - 1].id + ' -> ' + sum.path[i].id);
  }
  assert.ok(sum.path.some((p) => RGQ.byId[p.id].grade <= 6));
  assert.strictEqual(sum.path[sum.path.length - 1].id, 'cnm_001');
  assertTopological(sum.path.map((p) => p.id), RGQ);
});

test('带题库：一致的学生 + 无限题量 => 薄弱集合与根因精确还原；会的 confirm 题、不会的 2 题', () => {
  const rand = rng(20261018);
  let cases = 0;
  const conf = E.DEFAULT_CONFIRM;
  for (let round = 0; round < 3; round++) {
    const known = makeStudent(rand, [0.04, 0.12, 0.3][round]);
    formal.forEach((t) => {
      const { s, asked } = simulateBank([t.id], known, new Set(), 9999);
      cases++;
      const sum = E.summarize(RGQ, s);
      const sub = E.subgraph(RGQ, [t.id]);
      const unknown = sub.nodes.filter((id) => E.isTestable(RGQ, id) && !known.has(id));
      assert.deepStrictEqual(sorted(sum.weak), sorted(unknown), '薄弱集合 ' + t.id);
      assert.deepStrictEqual(sum.shaky, []);
      assert.deepStrictEqual(sum.unconfirmed, []);
      sum.mastered.forEach((id) => assert.ok(known.has(id), id + ' 被判掌握但学生不会'));
      const expectRoots = unknown.filter((id) => RGQ.prereqs[id].every((p) => !unknown.includes(p.id)));
      assert.deepStrictEqual(sorted(sum.roots.map((r) => r.id)), sorted(expectRoots), '根因 ' + t.id);
      const perTopic = {};
      asked.forEach((a) => { const id = a.split('#')[0]; perTopic[id] = (perTopic[id] || 0) + 1; });
      Object.keys(perTopic).forEach((id) => {
        const want = known.has(id) ? E.needConfirm(RGQ, s, id) : 2;
        assert.strictEqual(perTopic[id], want, id);
      });
      const pathIds = sum.path.map((p) => p.id);
      assertTopological(pathIds, RGQ);
      sum.weak.forEach((id) => assert.ok(pathIds.includes(id), '薄弱点应在路径中 ' + id));
      assert.strictEqual(sum.finished, true);
    });
  }
  assert.ok(cases >= 900);
  assert.strictEqual(conf, 3);
});

test('带题库：任何一个知识点“第一题错、第二题对” => 不稳、只问 2 题、不回溯先修、进学习路径', () => {
  let withPrereq = 0;
  formal.forEach((t) => {
    const { s, asked } = simulateBank([t.id], new Set(), new Set([t.id]), 9999);
    assert.deepStrictEqual(asked, [t.id + '#1', t.id + '#2'], t.id);
    assert.strictEqual(E.statusOf(s, t.id), 'shaky');
    const sum = E.summarize(RGQ, s);
    assert.deepStrictEqual(sum.shaky, [t.id]);
    assert.deepStrictEqual(sum.weak, []);
    assert.deepStrictEqual(sum.roots, []);
    assert.deepStrictEqual(sum.path.map((p) => p.id), [t.id]);
    assert.strictEqual(sum.path[0].status, 'shaky');
    if (RGQ.prereqs[t.id].length) withPrereq++;
  });
  assert.ok(withPrereq > 200);
});

test('带题库：混合学生（会 / 不稳 / 不会）——会的点最多 confirm 题，其余最多 2 题；状态与学生一致', () => {
  const rand = rng(99);
  const known = makeStudent(rand, 0.1);
  const flaky = new Set(topics.filter((t) => !t.external && !known.has(t.id) && rand() < 0.3).map((t) => t.id));
  formal.forEach((t) => {
    const { s, asked } = simulateBank([t.id], known, flaky, 9999);
    const cnt = {};
    asked.forEach((a) => { const id = a.split('#')[0]; cnt[id] = (cnt[id] || 0) + 1; });
    Object.keys(cnt).forEach((id) => {
      const maxN = known.has(id) ? E.needConfirm(RGQ, s, id) : 2;
      assert.ok(cnt[id] <= maxN, id + ' ' + cnt[id] + ' > ' + maxN);
    });
    Object.keys(s.status).forEach((id) => {
      const st = s.status[id];
      if (st.src !== 'direct') { assert.strictEqual(st.s, 'mastered'); return; }
      const want = known.has(id) ? 'mastered' : flaky.has(id) ? 'shaky' : 'weak';
      assert.strictEqual(st.s, want, id);
    });
    const sum = E.summarize(RGQ, s);
    sum.shaky.forEach((id) => assert.ok(sum.path.some((p) => p.id === id), '不稳的点应在路径里 ' + id));
    const all = new Set(sum.mastered.concat(sum.shaky, sum.weak, sum.untested));
    assert.strictEqual(all.size, s.order.length);
    assert.strictEqual(sum.mastered.length + sum.shaky.length + sum.weak.length + sum.untested.length, s.order.length);
  });
});

test('带题库：题量上限（8/16/30）按题计、永不突破；未复测的点标出', () => {
  const rand = rng(11);
  [8, 16, 30].forEach((limit) => {
    const known = makeStudent(rand, 0.02);
    let capped = 0;
    formal.forEach((t) => {
      const { s, asked } = simulateBank([t.id], known, new Set(), limit);
      assert.ok(asked.length <= limit, t.id);
      if (asked.length === limit) capped++;
      const sum = E.summarize(RGQ, s);
      assert.strictEqual(sum.asked, asked.length);
      sum.unconfirmed.forEach((id) => assert.ok(sum.weak.includes(id)));
      const all = new Set(sum.mastered.concat(sum.shaky, sum.weak, sum.untested));
      assert.strictEqual(all.size, s.order.length);
    });
    if (limit === 8) assert.ok(capped > 0, '应有触发上限的目标');
  });
});

test('带题库：种子固定 => 整个诊断的出题序列确定；换种子序列会变；重放一致', () => {
  const known = new Set(); // 什么都不会：两题都错，序列最长，选题的随机性最明显
  const a = simulateBank(['cnm_232'], known, new Set(), 16, 'fixed');
  const b = simulateBank(['cnm_232'], known, new Set(), 16, 'fixed');
  assert.deepStrictEqual(a.s.answers.map((x) => x.qid), b.s.answers.map((x) => x.qid));
  const qs = new Set();
  for (let i = 0; i < 30; i++) qs.add(simulateBank(['cnm_232'], known, new Set(), 16, 'seed' + i).s.answers.map((x) => x.qid).join());
  assert.ok(qs.size > 3);
  const r = E.replay(RGQ, ['cnm_232'], a.s.answers, { limit: 16, seed: 'fixed' });
  assert.deepStrictEqual(r, a.s);
});

test('带题库：重测时避开已出过的题（avoid 里的题尽量不再出）', () => {
  const known = makeStudent(rng(8), 0.1);
  const first = simulateBank(['cnm_232'], known, new Set(), 16, 'one');
  const seen = first.s.answers.map((x) => x.qid);
  let s = E.createSession(RGQ, ['cnm_232'], { limit: 16, seed: 'two', avoid: seen });
  let repeats = 0, total = 0;
  for (let guard = 0; guard < 100; guard++) {
    const it = E.nextItem(RGQ, s);
    if (!it) break;
    total++;
    if (it.attempt === 1 && seen.includes(it.question.id)) {
      // 只有当该知识点的非 advanced 题全都出过时才可能重复
      const fresh = RGQ.bank[it.topicId].filter((q) => !seen.includes(q.id) && q.difficulty !== 'advanced' && q.difficulty !== 'challenge');
      assert.strictEqual(fresh.length, 0, it.topicId + ' 还有没出过的题却重复了');
      repeats++;
    }
    s = E.applyAnswer(RGQ, s, it.topicId, known.has(it.topicId) ? 'correct' : 'wrong');
  }
  assert.ok(total > 0);
});

console.log('整年级 / 整册筛查');

function screenRun(spec, student, limit, seed, confirm) {
  let s = E.createSession(RGQ, spec.ids, {
    mode: 'screen', limit: limit, seed: seed == null ? 'scr' : seed,
    confirm: confirm == null ? E.DEFAULT_CONFIRM : confirm
  });
  for (let guard = 0; guard < 2000; guard++) {
    const it = E.nextItem(RGQ, s);
    if (!it) break;
    s = E.applyAnswer(RGQ, s, it.topicId, student(it.topicId, it.attempt));
  }
  return s;
}
const allWrong = () => 'wrong';
const allRight = () => 'correct';
const indexStudent = (id, attempt) => {
  const i = RGQ.index[id];
  if (i % 6 === 0) return 'wrong';
  if (i % 6 === 3) return attempt === 1 ? 'wrong' : 'correct';
  return 'correct';
};

test('gradeTargets：一年级 = 一上 + 一下，七上只含七上；写法不对返回 null', () => {
  const g1 = E.gradeTargets(RGQ, '一年级');
  const up = E.gradeTargets(RGQ, '一上');
  const down = E.gradeTargets(RGQ, '一下');
  assert.deepStrictEqual(g1.volumes, ['一上', '一下']);
  assert.strictEqual(g1.ids.length, up.ids.length + down.ids.length);
  assert.deepStrictEqual(sorted(g1.ids), sorted(up.ids.concat(down.ids)));
  const want = formal.filter((t) => t.grade === 1 && E.subjectOf(t) === 'math').length;
  assert.strictEqual(g1.ids.length, want);
  const g1zh = E.gradeTargets(RGQ, '一年级', 'chinese');
  assert.strictEqual(g1zh.ids.length, 79); // 一上 41 + 一下 38
  assert.ok(g1zh.ids.every((id) => id.startsWith('cnc_')));
  const g1sci = E.gradeTargets(RGQ, '一年级', 'science');
  assert.strictEqual(g1sci.ids.length, 30); // 一上 15 + 一下 15
  assert.ok(g1sci.ids.every((id) => id.startsWith('cns_')));
  const g6sci = E.gradeTargets(RGQ, '六下', 'science');
  assert.ok(g6sci.ids.length >= 15 && g6sci.ids.every((id) => RGQ.byId[id].grade === 6 && RGQ.byId[id].semester === '下'));
  const g1mor = E.gradeTargets(RGQ, '一年级', 'morality');
  assert.strictEqual(g1mor.ids.length, 32); // 一上 16 + 一下 16
  assert.ok(g1mor.ids.every((id) => id.startsWith('cnd_')));
  const g6mor = E.gradeTargets(RGQ, '六下', 'morality');
  assert.ok(g6mor.ids.length >= 10 && g6mor.ids.every((id) => RGQ.byId[id].grade === 6 && RGQ.byId[id].semester === '下'));
  const g7his = E.gradeTargets(RGQ, '七上', 'history');
  assert.strictEqual(g7his.ids.length, 21);
  assert.ok(g7his.ids.every((id) => id.startsWith('cnh_')));
  const g9his = E.gradeTargets(RGQ, '九下', 'history');
  assert.strictEqual(g9his.ids.length, 23);
  assert.ok(g9his.ids.every((id) => id.startsWith('cnh_') && RGQ.byId[id].grade === 9 && RGQ.byId[id].semester === '下'));
  const g7geo = E.gradeTargets(RGQ, '七上', 'geography');
  assert.strictEqual(g7geo.ids.length, 17);
  assert.ok(g7geo.ids.every((id) => id.startsWith('cng_')));
  const g8geo = E.gradeTargets(RGQ, '八下', 'geography');
  assert.strictEqual(g8geo.ids.length, 14);
  assert.ok(g8geo.ids.every((id) => id.startsWith('cng_') && RGQ.byId[id].grade === 8 && RGQ.byId[id].semester === '下'));
  assert.strictEqual(E.gradeTargets(RGQ, '九上', 'geography'), null);
  const g7bio = E.gradeTargets(RGQ, '七上', 'biology');
  assert.strictEqual(g7bio.ids.length, 22);
  assert.ok(g7bio.ids.every((id) => id.startsWith('cnb_')));
  const g8bio = E.gradeTargets(RGQ, '八下', 'biology');
  assert.strictEqual(g8bio.ids.length, 13);
  assert.ok(g8bio.ids.every((id) => id.startsWith('cnb_') && RGQ.byId[id].grade === 8 && RGQ.byId[id].semester === '下'));
  assert.strictEqual(E.gradeTargets(RGQ, '九上', 'biology'), null);
  const g7bioYear = E.gradeTargets(RGQ, '七年级', 'biology');
  assert.strictEqual(g7bioYear.ids.length, 40);
  assert.ok(g7bioYear.ids.every((id) => id.startsWith('cnb_') && RGQ.byId[id].grade === 7));
  assert.strictEqual(E.subjectOf(RGQ.byId[g7bio.ids[0]]), 'biology');
  const g9chem = E.gradeTargets(RGQ, '九上', 'chemistry');
  assert.strictEqual(g9chem.ids.length, 27);
  assert.ok(g9chem.ids.every((id) => id.startsWith('cnk_')));
  const g9chemDown = E.gradeTargets(RGQ, '九下', 'chemistry');
  assert.strictEqual(g9chemDown.ids.length, 18);
  assert.ok(g9chemDown.ids.every((id) => id.startsWith('cnk_') && RGQ.byId[id].grade === 9 && RGQ.byId[id].semester === '下'));
  assert.strictEqual(E.gradeTargets(RGQ, '八上', 'chemistry'), null);
  assert.strictEqual(E.gradeTargets(RGQ, '七上', 'chemistry'), null);
  const g9chemYear = E.gradeTargets(RGQ, '九年级', 'chemistry');
  assert.strictEqual(g9chemYear.ids.length, 45);
  assert.ok(g9chemYear.ids.every((id) => id.startsWith('cnk_') && RGQ.byId[id].grade === 9));
  assert.strictEqual(E.subjectOf(RGQ.byId[g9chem.ids[0]]), 'chemistry');
  assert.ok(E.gradeTargets(RGQ, '九上').ids.every((id) => id.startsWith('cnm_')));
  const g7 = E.gradeTargets(RGQ, '七年级');
  assert.strictEqual(g7.ids.length, formal.filter((t) => t.grade === 7 && String(t.id).startsWith('cnm_')).length);
  assert.ok(g7.ids.every((id) => id.startsWith('cnm_')));
  E.gradeTargets(RGQ, '七上').ids.forEach((id) => {
    const t = RGQ.byId[id];
    assert.ok(id.startsWith('cnm_') && t.grade === 7 && t.semester === '上' && !t.external, id);
  });
  assert.strictEqual(E.gradeTargets(RGQ, '十年级'), null);
  assert.strictEqual(E.gradeTargets(RGQ, '七'), null);
  assert.strictEqual(E.gradeTargets(RGQ, ''), null);
  const g10 = E.gradeTargets(RGQ, '高一');
  assert.strictEqual(g10.label, '高一（必修第一册）');
  assert.deepStrictEqual(g10.volumes, ['高一']);
  assert.strictEqual(g10.ids.length, 78);
  g10.ids.forEach((id) => assert.strictEqual(RGQ.byId[id].grade, 10));
  const g11 = E.gradeTargets(RGQ, '高二必修');
  assert.strictEqual(g11.label, '高二（必修第二册）');
  assert.strictEqual(g11.ids.length, 65);
  g11.ids.forEach((id) => assert.strictEqual(RGQ.byId[id].grade, 11));
  assert.deepStrictEqual(E.parseChapter('高一 第一章 集合与常用逻辑用语 1.1'), {
    volume: '高一', chapterNo: '第一章', chapterName: '集合与常用逻辑用语', section: '1.1'
  });
  assert.deepStrictEqual(E.parseChapter('高二 数学探究 用向量研究三角形'), {
    volume: '高二', chapterNo: '数学探究', chapterName: '用向量研究三角形', section: ''
  });
  const g12 = E.gradeTargets(RGQ, '选必一');
  assert.strictEqual(g12.label, '选必一（选择性必修第一册）');
  assert.deepStrictEqual(g12.volumes, ['选必一']);
  assert.strictEqual(g12.ids.length, 53);
  g12.ids.forEach((id) => assert.strictEqual(RGQ.byId[id].grade, 12));
  const g13 = E.gradeTargets(RGQ, '选择性必修第二册');
  assert.strictEqual(g13.label, '选必二（选择性必修第二册）');
  assert.strictEqual(g13.ids.length, 33);
  g13.ids.forEach((id) => assert.strictEqual(RGQ.byId[id].grade, 13));
  const g14 = E.gradeTargets(RGQ, '选必三');
  assert.strictEqual(g14.label, '选必三（选择性必修第三册）');
  assert.strictEqual(g14.ids.length, 42);
  g14.ids.forEach((id) => assert.strictEqual(RGQ.byId[id].grade, 14));
  assert.deepStrictEqual(E.parseChapter('选必二 第五章 一元函数的导数及其应用 5.1'), {
    volume: '选必二', chapterNo: '第五章', chapterName: '一元函数的导数及其应用', section: '5.1'
  });
  assert.deepStrictEqual(E.parseChapter('选必三 数学探究 杨辉三角的性质与应用'), {
    volume: '选必三', chapterNo: '数学探究', chapterName: '杨辉三角的性质与应用', section: ''
  });
  assert.deepStrictEqual(E.parseChapter('选必三 数学建模 建立统计模型进行预测'), {
    volume: '选必三', chapterNo: '数学建模', chapterName: '建立统计模型进行预测', section: ''
  });
  const pre = new Map();
  deps.forEach((d) => { (pre.get(d.topicId) || pre.set(d.topicId, []).get(d.topicId)).push(d.prerequisiteId); });
  topics.filter((t) => /^cnm_h(\d+)$/.test(t.id) && Number(t.id.slice(5)) >= 144).forEach((t) => {
    assert.ok(pre.get(t.id) && pre.get(t.id).length >= 1, t.id + ' 应至少有一条先修');
  });
  assert.strictEqual(RGQ.byId.cnm_h001.name, '集合的含义');
  assert.strictEqual(RGQ.byId.cnm_h143.name, '用频率估计概率');
  assert.strictEqual(RGQ.byId.cnm_h217.name, '导数的概念');
});

test('筛查会话：范围 = 目标本身，默认题量上限 SCREEN_LIMIT；普通会话不受影响', () => {
  const g = E.gradeTargets(RGQ, '七年级');
  const s = E.createSession(RGQ, g.ids, { mode: 'screen' });
  assert.strictEqual(s.limit, E.SCREEN_LIMIT);
  assert.ok(E.SCREEN_LIMIT > E.DEFAULT_LIMIT);
  assert.deepStrictEqual(sorted(s.order), sorted(g.ids));
  assert.strictEqual(s.mode, 'screen');
  const n = E.createSession(RGQ, g.ids);
  assert.strictEqual(n.limit, E.DEFAULT_LIMIT);
  assert.strictEqual(n.mode, 'target');
  assert.strictEqual(n.scope, null);
  assert.ok(n.order.length > s.order.length, '普通会话的子图包含更早年级的先修');
  assert.strictEqual(E.createSession(RGQ, g.ids, { mode: 'screen', limit: 60 }).limit, 60);
});

test('筛查：题量不超过上限（一年级 / 七年级 / 七上；全错、全对、混合的学生）', () => {
  ['一年级', '七年级', '七上'].forEach((scope) => {
    const g = E.gradeTargets(RGQ, scope);
    [[allWrong, 40], [allRight, 40], [indexStudent, 40], [indexStudent, 25], [indexStudent, 60]].forEach(([stu, limit]) => {
      const s = screenRun(g, stu, limit);
      assert.ok(s.answers.length <= limit, scope + ' ' + s.answers.length + ' > ' + limit);
      const ids = new Set(g.ids);
      s.answers.forEach((a) => assert.ok(ids.has(a.id), '问到了范围之外的知识点 ' + a.id));
      const sum = E.summarize(RGQ, s);
      assert.strictEqual(sum.mastered.length + sum.shaky.length + sum.weak.length + sum.untested.length, g.ids.length);
      assert.strictEqual(sum.asked, s.answers.length);
    });
  });
});

test('筛查：全对的学生只需很少几题（答对即推断先修）；一年级默认上限内能问完', () => {
  // confirm=1：验证「答对即推断先修」仍能把整年级压到很少题
  const g7 = E.gradeTargets(RGQ, '七年级');
  const s = screenRun(g7, allRight, 40, 'scr', 1);
  const sum = E.summarize(RGQ, s);
  assert.ok(sum.asked < g7.ids.length / 2, '全对却问了 ' + sum.asked);
  assert.strictEqual(sum.mastered.length, g7.ids.length);
  // 默认 confirm=3：题量够时仍能问完一年级（indexStudent）
  const g1 = E.gradeTargets(RGQ, '一年级');
  const s1 = screenRun(g1, indexStudent, Math.max(E.SCREEN_LIMIT, g1.ids.length * E.DEFAULT_CONFIRM));
  assert.strictEqual(E.summarize(RGQ, s1).finished, true);
  assert.strictEqual(E.summarize(RGQ, s1).untested.length, 0);
  // 默认 confirm=3 + 上限 40：七年级全对无法在一题掌握的旧意义上问完，但 asked 仍 < 知识点数×confirm
  const s3 = screenRun(g7, allRight, 40);
  const sum3 = E.summarize(RGQ, s3);
  assert.ok(sum3.asked <= 40);
  assert.ok(sum3.mastered.length > 0);
});

test('筛查：到上限没测到的点标「未测」，且题量 = 上限', () => {
  const g = E.gradeTargets(RGQ, '七年级');
  const s = screenRun(g, allWrong, 20);
  const sum = E.summarize(RGQ, s);
  assert.strictEqual(sum.asked, 20);
  assert.strictEqual(sum.limitReached, true);
  assert.ok(sum.untested.length > 0);
});

test('筛查：回溯只在本范围内——薄弱点范围外的先修不被问，且列在 outOfScopePrereqs', () => {
  const g = E.gradeTargets(RGQ, '七上');
  const s = screenRun(g, allWrong, 60);
  const inScope = new Set(g.ids);
  assert.ok(s.answers.every((a) => inScope.has(a.id)));
  const sum = E.summarize(RGQ, s);
  assert.ok(sum.roots.length > 0);
  const outside = new Set();
  sum.roots.forEach((r) => {
    r.pendingPrereqs.forEach((p) => assert.ok(inScope.has(p)));
    r.outOfScopePrereqs.forEach((p) => { assert.ok(!inScope.has(p)); outside.add(p); });
  });
  assert.ok(outside.size > 0, '七上的根因应该有七年级之前的先修');
  // 范围外的点不会出现在汇总里
  sum.mastered.concat(sum.shaky, sum.weak, sum.untested).forEach((id) => assert.ok(inScope.has(id)));
  assert.ok(sum.path.every((p) => inScope.has(p.id) && p.isTarget === false));
});

test('筛查：一致的学生、题量不限 => 薄弱集合恰好等于他不会的点（范围内）', () => {
  const g = E.gradeTargets(RGQ, '七上');
  const inScope = new Set(g.ids);
  [0.3, 0.6, 0.9].forEach((p, k) => {
    const known = makeStudent(rng(100 + k), p);
    const s = screenRun(g, (id) => (known.has(id) ? 'correct' : 'wrong'), 1000);
    const sum = E.summarize(RGQ, s);
    assert.deepStrictEqual(sorted(sum.weak), sorted(g.ids.filter((id) => !known.has(id))));
    assert.strictEqual(sum.untested.length, 0);
    // 根因 = 自己不会、范围内先修都会（范围外的先修不判）
    const wantRoots = g.ids.filter((id) => !known.has(id) &&
      !RGQ.prereqs[id].some((x) => inScope.has(x.id) && !known.has(x.id)));
    assert.deepStrictEqual(sorted(sum.roots.map((r) => r.id)), sorted(wantRoots));
  });
});

test('筛查：同一种子 => 出题序列完全相同；replay 重建一致；换种子序列会变', () => {
  const g = E.gradeTargets(RGQ, '七年级');
  const a = screenRun(g, indexStudent, 40, 'fixed');
  const b = screenRun(g, indexStudent, 40, 'fixed');
  assert.deepStrictEqual(a.answers.map((x) => x.qid), b.answers.map((x) => x.qid));
  const r = E.replay(RGQ, g.ids, a.answers, { mode: 'screen', limit: 40, seed: 'fixed' });
  assert.deepStrictEqual(r, a);
  const c = screenRun(g, indexStudent, 40, 'other');
  assert.notDeepStrictEqual(a.answers.map((x) => x.qid), c.answers.map((x) => x.qid));
  // 会话可 JSON 往返
  assert.deepStrictEqual(JSON.parse(JSON.stringify(a)), a);
});

test('按章汇总：分组正确、数量与汇总一致、薄弱章在前、可复现', () => {
  ['一年级', '七年级', '八上'].forEach((scope) => {
    const g = E.gradeTargets(RGQ, scope);
    const s = screenRun(g, indexStudent, 40);
    const sum = E.summarize(RGQ, s);
    const chs = E.chapterSummary(RGQ, s);
    // 每个知识点恰好在一章里，章总数 = 范围内知识点数
    assert.strictEqual(chs.reduce((n, c) => n + c.total, 0), g.ids.length);
    const seen = new Set();
    chs.forEach((c) => {
      assert.strictEqual(c.mastered + c.shaky + c.weak + c.untested, c.total, c.label);
      assert.strictEqual(c.weakIds.length, c.weak);
      assert.strictEqual(c.shakyIds.length, c.shaky);
      c.weakIds.concat(c.shakyIds, c.untestedIds).forEach((id) => {
        assert.ok(!seen.has(id)); seen.add(id);
        const p = E.parseChapter(RGQ.byId[id].chapter);
        assert.strictEqual(c.volume + ' ' + c.chapterNo + ' ' + c.chapterName, p.volume + ' ' + p.chapterNo + ' ' + p.chapterName);
        assert.ok(g.volumes.includes(p.volume));
      });
      c.weakIds.forEach((id) => assert.strictEqual(E.statusOf(s, id), 'weak'));
      c.shakyIds.forEach((id) => assert.strictEqual(E.statusOf(s, id), 'shaky'));
    });
    assert.strictEqual(chs.reduce((n, c) => n + c.weak, 0), sum.weak.length);
    assert.strictEqual(chs.reduce((n, c) => n + c.shaky, 0), sum.shaky.length);
    assert.strictEqual(chs.reduce((n, c) => n + c.mastered, 0), sum.mastered.length);
    assert.strictEqual(chs.reduce((n, c) => n + c.untested, 0), sum.untested.length);
    for (let i = 1; i < chs.length; i++) {
      const a = chs[i - 1], b = chs[i];
      assert.ok(a.weak > b.weak || (a.weak === b.weak && a.shaky >= b.shaky), '排序：' + a.label + ' / ' + b.label);
    }
    assert.ok(chs[0].weak >= 1, scope + ' 最前面的章应有薄弱点');
    assert.deepStrictEqual(chs, E.chapterSummary(RGQ, screenRun(g, indexStudent, 40)));
  });
});

test('按章汇总：七上共 6 章；还没作答的会话所有点都算未测，章按教材顺序', () => {
  const g = E.gradeTargets(RGQ, '七上');
  const s = screenRun(g, allWrong, 60);
  const chs = E.chapterSummary(RGQ, s);
  assert.strictEqual(chs.length, 6);
  const tiny = E.chapterSummary(RGQ, E.createSession(RGQ, g.ids, { mode: 'screen' }));
  assert.ok(tiny.every((c) => c.untested === c.total && c.weak === 0));
  assert.deepStrictEqual(tiny.map((c) => c.label).slice(0, 2), ['七上 第一章 有理数', '七上 第二章 有理数的运算']);
});

test('筛查：路径图只画有问题的点（不把整个年级都画上）', () => {
  const g = E.gradeTargets(RGQ, '七年级');
  const s = screenRun(g, indexStudent, 40);
  const sum = E.summarize(RGQ, s);
  const lay = E.layout(RGQ, s, sum);
  assert.ok(lay.nodes.length < g.ids.length);
  assert.ok(lay.nodes.every((n) => n.isTarget === false));
  const allOk = E.summarize(RGQ, screenRun(g, allRight, 40));
  assert.strictEqual(allOk.path.length, 0);
});

test('普通整章 / 单点诊断不受影响：不带 mode 的会话仍回溯到小学', () => {
  const s = E.createSession(RGQ, ['cnm_232'], { limit: 16 });
  assert.strictEqual(s.mode, 'target');
  assert.ok(s.order.length > 1);
  const sum = E.summarize(RGQ, s);
  assert.strictEqual(sum.mode, 'target');
  sum.roots.forEach((r) => assert.deepStrictEqual(r.outOfScopePrereqs, []));
});

console.log('\n' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
