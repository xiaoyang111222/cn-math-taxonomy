#!/usr/bin/env node
/* 数据修补批回归：科学锚定（#42）、cnm_p268_q3（#53）、cnm_h117_q3（#54）、历史诊断题量（#34）。
 * node tests/test_data_patch_batch.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const E = require('../diagnose/engine.js');

const ROOT = path.join(__dirname, '..');
const read = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const topics = read('data/topics.json');
const deps = read('data/dependencies.json');
const questions = read('data/questions.json');
const aliases = read('data/id-aliases.json').aliases;
const byId = new Map(topics.map((t) => [t.id, t]));
const sci = topics.filter((t) => String(t.id).startsWith('cns_'));
const sciIndex = new Map(topics.map((t, i) => [t.id, i]));

let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

console.log('#42 科学子图教材锚定');

const RETIRED = {
  cns_p007: '植物的根、茎、叶', cns_p023: '物体是用什么做的', cns_p029: '动物的身体特征', cns_p037: '牢固的结构',
  cns_p053: '化石是怎样形成的', cns_p058: '磁铁的两极', cns_p060: '磁铁在生活中的应用'
};

test('7 个无教材锚的节点：topics、先修边、题目里都不再出现，名称也不在科学节点里', () => {
  Object.keys(RETIRED).forEach((id) => {
    assert.ok(!byId.has(id), id + ' 仍在 topics');
    assert.ok(!deps.some((e) => e.topicId === id || e.prerequisiteId === id), id + ' 仍在先修边里');
    assert.ok(!questions.some((q) => q.topicId === id), id + ' 仍有题目');
  });
  const names = new Set(sci.map((t) => t.name));
  Object.values(RETIRED).forEach((n) => assert.ok(!names.has(n), n));
});

test('修正落在构建源头：sci_g*.py 不再登记这 7 个 key，旧 ID 也不在 KEY_IDS', () => {
  const py = [
    'import sys', "sys.path.insert(0, 'scripts')",
    'import sci_g1, sci_g2, sci_g3, sci_g4, sci_g5, sci_g6, sci_edges',
    'from sci_lib import TOPICS, HARD, SOFT', 'from sci_ids import KEY_IDS', 'import json',
    "print(json.dumps({'keys': [t['key'] for t in TOPICS], 'unofficial': [t['key'] for t in TOPICS if t['official'] is False],",
    " 'edges': [e[0] for e in HARD + SOFT] + [e[1] for e in HARD + SOFT], 'ids': sorted(KEY_IDS.values())}))"
  ].join('\n');
  const r = spawnSync('python3', ['-c', py], { cwd: ROOT, encoding: 'utf8' });
  assert.strictEqual(r.status, 0, r.stderr);
  const out = JSON.parse(r.stdout);
  const gone = ['g1a_genjing', 'g1b_cailiao', 'g1b_dongwutezheng', 'g2a_jiegou', 'g2b_huashi', 'g2b_jiechu', 'g2b_yongchu'];
  gone.forEach((k) => {
    assert.ok(!out.keys.includes(k), k + ' 仍登记在源脚本');
    assert.ok(!out.edges.includes(k), k + ' 仍被 sci_edges 引用');
  });
  Object.keys(RETIRED).forEach((id) => assert.ok(!out.ids.includes(id), id + ' 仍在 sci_ids'));
  assert.strictEqual(out.keys.length, sci.length, '源脚本与 topics.json 的科学点数一致');
});

test('旧 7 个 ID 有别名，指向仍存在的小学科学知识点', () => {
  Object.keys(RETIRED).forEach((id) => {
    assert.ok(aliases[id] && aliases[id].name === RETIRED[id], id);
    const ids = E.resolveTargets([id], aliases);
    assert.ok(ids.length >= 1);
    ids.forEach((t) => { assert.ok(byId.has(t) && t.startsWith('cns_'), id + ' -> ' + t); });
  });
});

test('科学 262 个、全站 3924 个知识点（含 2026-11-20 补强批新增的高中地理 119、生物 135、历史 120）；每个科学点 4 题；先修都指向更靠前的点', () => {
  assert.strictEqual(sci.length, 262);
  assert.strictEqual(topics.length, 3924);
  sci.forEach((t) => {
    assert.strictEqual(questions.filter((q) => q.topicId === t.id).length, 4, t.id);
  });
  const sciEdges = deps.filter((e) => String(e.topicId).startsWith('cns_'));
  sciEdges.forEach((e) => {
    assert.ok(byId.has(e.prerequisiteId), '先修不存在：' + e.prerequisiteId);
    assert.ok(sciIndex.get(e.prerequisiteId) < sciIndex.get(e.topicId), e.topicId + ' ← ' + e.prerequisiteId);
  });
  const withPre = new Set(sciEdges.map((e) => e.topicId));
  sci.slice(1).forEach((t) => assert.ok(withPre.has(t.id), t.id + ' 没有先修'));
});

test('合并去向：磁极并入「磁极与方向」，化石并入「挖掘恐龙化石」，三角形结构并入「建造小房子」', () => {
  const name = (n) => sci.find((t) => t.name === n);
  const ciji = name('磁极与方向');
  assert.match(ciji.description, /N 极和 S 极两个磁极/);
  assert.ok(questions.filter((q) => q.topicId === ciji.id).some((q) => /两个磁极/.test(q.prompt)));
  const wajue = name('挖掘恐龙「化石」');
  assert.match(wajue.description, /泥沙掩埋/);
  const gudai = name('古代生物的多样性');
  assert.ok(deps.some((e) => e.topicId === gudai.id && e.prerequisiteId === wajue.id && e.strength === 'hard'));
  const jianzao = name('建造小房子');
  assert.match(jianzao.description, /三角形/);
  const tatai = name('建造塔台');
  assert.ok(deps.some((e) => e.topicId === tatai.id && e.prerequisiteId === jianzao.id && e.strength === 'hard'));
  const jingye = name('茎和叶');
  assert.ok(deps.some((e) => e.topicId === jingye.id && e.prerequisiteId === name('观察植物').id && e.strength === 'hard'));
});

test('「动物联欢会」是扮演活动，不是分类', () => {
  const t = sci.find((x) => x.name === '动物联欢会');
  assert.match(t.description, /扮演/);
  assert.ok(!/分类/.test(t.description));
  questions.filter((q) => q.topicId === t.id).forEach((q) => {
    const right = q.choices.find((c) => c.key === q.answer).text;
    assert.ok(!/分类/.test(right), q.id + ' 正确答案不应是分类：' + right);
  });
});

test('「让小车动起来」是磁力隔空驱动加距离影响，不是同极相斥、异极相吸', () => {
  const t = sci.find((x) => x.name === '让小车动起来');
  assert.match(t.description, /不接触小车/);
  assert.match(t.description, /离得越近吸引力越大/);
  const qs = questions.filter((q) => q.topicId === t.id);
  const blob = qs.map((q) => [q.prompt, q.explanation].concat(q.choices.map((c) => c.text)).join(' ')).join(' ');
  assert.ok(!/同极相斥|异极相吸|N 极|S 极/.test(t.description + blob));
  assert.ok(qs.some((q) => /越近/.test(q.prompt) && q.choices.find((c) => c.key === q.answer).text === '越大'));
  assert.ok(!deps.some((e) => e.topicId === t.id && /磁极/.test(byId.get(e.prerequisiteId).name)));
});

test('二下 U2 课序对齐 2024 版，且没有被移出课序的概念点夹在里面', () => {
  const u2 = sci.filter((t) => t.chapter === '二年级下册 第2单元 玩磁铁').map((t) => t.name);
  assert.deepStrictEqual(u2, ['磁铁能吸引什么', '比较力量的大小', '让小车动起来', '隔物吸铁', '设计钓鱼玩具', '我们来钓鱼']);
  const idOf = (n) => sci.find((t) => t.name === n).id;
  for (let i = 1; i < u2.length; i++) {
    assert.ok(deps.some((e) => e.topicId === idOf(u2[i]) && e.prerequisiteId === idOf(u2[i - 1])),
      u2[i - 1] + ' → ' + u2[i] + ' 应有先修边');
  }
});

test('「观察云」在三上 U1 第 6 课，早于「水珠从哪里来」，先修边不再倒挂', () => {
  const u1 = sci.filter((t) => t.chapter === '三年级上册 第1单元 天气').map((t) => t.name);
  assert.strictEqual(u1.indexOf('观察云'), 5);
  const yun = sci.find((t) => t.name === '观察云');
  const zhu = sci.find((t) => t.name === '水珠从哪里来');
  assert.ok(sciIndex.get(yun.id) < sciIndex.get(zhu.id));
  assert.ok(!deps.some((e) => e.topicId === yun.id && e.prerequisiteId === zhu.id), '观察云不应依赖水珠');
  const G = E.buildGraph(topics, deps);
  assert.ok(new Set(E.ancestors(G, zhu.id)).has(yun.id), '水珠应沿课序软边排在观察云之后');
  assert.ok(!new Set(E.ancestors(G, yun.id)).has(zhu.id));
});

console.log('#53 cnm_p268_q3 / #54 cnm_h117_q3');

const qById = new Map(questions.map((q) => [q.id, q]));

test('cnm_p268_q3：一道题两问，答案同时覆盖「每份几个」和「还剩几个」', () => {
  const q = qById.get('cnm_p268_q3');
  assert.strictEqual(q.answer, '6，48');
  assert.match(q.prompt, /依次作答/);
  assert.strictEqual(E.judgeQuestion(q, '6，48').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion(q, '6,48').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion(q, '6 和 48').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion(q, '48').verdict, 'wrong');
  assert.strictEqual(E.judgeQuestion(q, '6').verdict, 'wrong');
  assert.strictEqual(E.judgeQuestion(q, '48，6').verdict, 'wrong');
  assert.match(q.explanation, /6/);
  assert.match(q.explanation, /48/);
});

test('cnm_h117_q3：题干完整，答案与题干自洽', () => {
  const q = qById.get('cnm_h117_q3');
  assert.ok(q.prompt.length >= 30, '题干过短：' + q.prompt);
  assert.match(q.prompt, /平行于平面/);
  assert.match(q.prompt, /交线有几条/);
  assert.strictEqual(q.answer, '1');
  assert.strictEqual(E.judgeQuestion(q, '1').verdict, 'correct');
  assert.strictEqual(E.judgeQuestion(q, '2').verdict, 'wrong');
  const peers = questions.filter((x) => x.topicId === q.topicId);
  assert.strictEqual(peers.length, 4);
  peers.forEach((x) => assert.ok(x.prompt.length >= 10, x.id));
});

test('两道题在 _qbatches 源文件里同步改了（否则下次重建会被覆盖）', () => {
  const b1 = read('data/_qbatches/primary_g2.json').find((q) => q.id === 'cnm_p268_q3');
  const b2 = read('data/_qbatches/high.json').find((q) => q.id === 'cnm_h117_q3');
  assert.deepStrictEqual(b1, qById.get('cnm_p268_q3'));
  assert.deepStrictEqual(b2, qById.get('cnm_h117_q3'));
});

console.log('#34 历史诊断题量');

const graphFor = (subject) => {
  const tp = topics.filter((t) => E.subjectOf(t) === subject);
  const allow = new Set(tp.map((t) => t.id));
  return E.buildGraph(tp,
    deps.filter((d) => allow.has(d.topicId) && allow.has(d.prerequisiteId)),
    questions.filter((q) => allow.has(q.topicId)));
};

function runAll(graph, ids, opts, result) {
  let s = E.createSession(graph, ids, opts);
  let n = 0;
  for (;;) {
    const id = E.nextQuestion(graph, s);
    if (!id) break;
    s = E.applyAnswer(graph, s, id, typeof result === 'function' ? result(id, n) : result);
    n++;
  }
  return { asked: n, session: s };
}

test('历史整体诊断（按年级、全答对）每个年级都跑满 SCREEN_LIMIT 题，和数学、科学一致', () => {
  const H = graphFor('history');
  ['七', '八', '九'].forEach((g) => {
    const scope = E.gradeTargets(H, g + '年级', 'history');
    assert.ok(scope && scope.ids.length >= 20, g + '年级知识点数');
    const r = runAll(H, scope.ids, { mode: 'screen' }, 'correct');
    assert.strictEqual(r.asked, E.SCREEN_LIMIT, g + '年级全答对应跑满 ' + E.SCREEN_LIMIT);
    assert.strictEqual(E.summarize(H, r.session).limitReached, true);
  });
  ['math', 'science', 'chinese'].forEach((subj) => {
    const G = graphFor(subj);
    const scope = E.gradeTargets(G, subj === 'math' ? '七年级' : subj === 'science' ? '三年级' : '三年级', subj);
    assert.strictEqual(runAll(G, scope.ids, { mode: 'screen' }, 'correct').asked, E.SCREEN_LIMIT, subj);
  });
});

test('历史整体诊断（全答错、一半答错）同样跑满，题量上限可调且被遵守', () => {
  const H = graphFor('history');
  const scope = E.gradeTargets(H, '八年级', 'history');
  assert.strictEqual(runAll(H, scope.ids, { mode: 'screen' }, 'wrong').asked, E.SCREEN_LIMIT);
  assert.strictEqual(runAll(H, scope.ids, { mode: 'screen' }, (id, n) => (n % 2 ? 'wrong' : 'correct')).asked, E.SCREEN_LIMIT);
  assert.strictEqual(runAll(H, scope.ids, { mode: 'screen', limit: 60 }, 'correct').asked, 60);
  assert.strictEqual(runAll(H, scope.ids, { mode: 'screen', limit: 20 }, 'correct').asked, 20);
});

test('历史每册也跑满（七上到九下），每个知识点 4 题、满足连对确认', () => {
  const H = graphFor('history');
  ['七上', '七下', '八上', '八下', '九上', '九下'].forEach((v) => {
    const scope = E.gradeTargets(H, v, 'history');
    assert.ok(scope, v);
    assert.strictEqual(runAll(H, scope.ids, { mode: 'screen' }, 'correct').asked, E.SCREEN_LIMIT, v);
  });
  H.topics.filter((t) => !t.external).forEach((t) => assert.strictEqual((H.bank[t.id] || []).length, 4, t.id));
});

test('单个知识点诊断：答对 confirm 题就结束，各学科一致（历史不是特例）', () => {
  ['history', 'geography', 'biology', 'physics', 'chemistry', 'science', 'morality'].forEach((subj) => {
    const G = graphFor(subj);
    const last = G.topics.slice().reverse().find((t) => E.isTestable(G, t.id));
    assert.strictEqual(runAll(G, [last.id], { confirm: 3 }, 'correct').asked, 3, subj);
    assert.strictEqual(runAll(G, [last.id], { confirm: 3 }, 'wrong').asked, E.DEFAULT_LIMIT, subj + ' 全答错回溯到题量上限');
  });
});

test('结果页对「只答了几题就结束」的单点诊断给出整体诊断入口，且只在非筛查、未到上限时出现', () => {
  const src = fs.readFileSync(path.join(ROOT, 'diagnose/app.js'), 'utf8');
  assert.ok(/!screen && !sum\.limitReached && sum\.asked > 0 && sum\.asked < 8/.test(src));
  assert.ok(src.includes("id: 'short-run-hint'"));
});

console.log('\n' + passed + ' passed');
