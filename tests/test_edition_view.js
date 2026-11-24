#!/usr/bin/env node
/* 教材版本落点投影测试：node tests/test_edition_view.js（无依赖，纯函数，不启浏览器）。
   用小型夹具锁住 assets/edition.js 的规则，见 docs/hujiao-mapping-plan.md 第 3、5 节。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('../diagnose/engine.js');
const Ed = require('../assets/edition.js');

let passed = 0;
let chain = Promise.resolve();
function test(name, fn) {
  chain = chain.then(fn).then(() => {
    passed++;
    console.log('  ok   ' + name);
  });
}
const clone = (x) => JSON.parse(JSON.stringify(x));

/* 夹具：人教口径下的几个点。
 *  P1  人教三上            -> 沪教三上 单元 U1
 *  P2  人教六上            -> 沪教四下 单元 U2（人教六年级的点被标进小学 1–5 年级）
 *  P3  人教三下            -> 沪教三下 单元 U9
 *  P4  人教三上，没有映射
 *  P5  人教二下，没有映射，是 P1 的先修
 *  P6  人教四上            -> 沪教三上 单元 U0（文件里排在 P1 的单元之后，id 却在前）
 *  P7  人教六下，没有映射
 */
function mk(id, grade, semester, chapter) {
  return {
    id: id, name: id, external: false, grade: grade, semester: semester, chapter: chapter,
    diagnostic_question: { question: id + '?', answer: '1' }
  };
}
const topics = [
  mk('cnm_p001', 3, '上', '三年级上册 第1单元 人教单元甲'),
  mk('cnm_p002', 6, '上', '六年级上册 第2单元 人教单元乙'),
  mk('cnm_p003', 3, '下', '三年级下册 第3单元 人教单元丙'),
  mk('cnm_p004', 3, '上', '三年级上册 第4单元 人教单元丁'),
  mk('cnm_p005', 2, '下', '二年级下册 第5单元 人教单元戊'),
  mk('cnm_p006', 4, '上', '四年级上册 第6单元 人教单元己'),
  mk('cnm_p007', 6, '下', '六年级下册 第7单元 人教单元庚')
];
const deps = [
  { topicId: 'cnm_p001', prerequisiteId: 'cnm_p005', strength: 'hard' },
  { topicId: 'cnm_p002', prerequisiteId: 'cnm_p001', strength: 'hard' }
];
const mapping = {
  version: 'hujiao', subject: 'math', stage: 'primary', label: '夹具', status: 'draft',
  source: 's', contributor: 'c',
  entries: {
    cnm_p006: { grade: 3, term: 1, unit: 'U0 先排的单元', chapter: '第一课' },
    cnm_p001: { grade: 3, term: 1, unit: 'U1 后排的单元' },
    cnm_p002: { grade: 4, term: 2, unit: 'U2 六年级点放四下', note: '人教六上' },
    cnm_p003: { grade: 3, term: 2, unit: 'U9 三下' }
  }
};
const topicsBefore = clone(topics);
const G = E.buildGraph(topics, deps);
const P = Ed.buildPlacement(mapping);

test('有条目的点：落点来自映射，topics 里的原对象仍是人教值', () => {
  const p = Ed.placementOf(P, 'cnm_p002');
  assert.strictEqual(p.grade, 4);
  assert.strictEqual(p.term, 2);
  assert.strictEqual(p.semester, '下');
  assert.strictEqual(p.volume, '四下');
  assert.strictEqual(p.unit, 'U2 六年级点放四下');
  assert.strictEqual(p.stage, 'primary');
  assert.strictEqual(G.byId.cnm_p002.grade, 6);
  assert.strictEqual(G.byId.cnm_p002.semester, '上');
  assert.strictEqual(G.byId.cnm_p002.chapter, '六年级上册 第2单元 人教单元乙');
});

test('投影不写回 topic 对象（深比较）', () => {
  Ed.gradeTargets(G, P, '三年级');
  Ed.groupByUnit(P, topics.map((t) => t.id));
  Ed.filterByProgress(G, P, topics.map((t) => t.id), '上', 3);
  topics.forEach((t) => Ed.chapterText(P, t));
  E.chapterSummary(G, E.createSession(G, ['cnm_p001'], { mode: 'screen' }), Ed.chapterView(P));
  assert.deepStrictEqual(topics, topicsBefore);
  assert.ok(topics.every((t) => !('mappings' in t) && !('placement' in t)));
});

test('无条目的点：covered 为 false，放进沪教三年级池里也找不到它', () => {
  assert.strictEqual(Ed.isCovered(P, 'cnm_p004'), false);
  assert.strictEqual(Ed.placementOf(P, 'cnm_p004'), null);
  const g3 = Ed.gradeTargets(G, P, '三年级');
  assert.ok(g3.ids.indexOf('cnm_p004') < 0);
  assert.deepStrictEqual(g3.ids.slice().sort(), ['cnm_p001', 'cnm_p003', 'cnm_p006']);
  assert.strictEqual(g3.label, '三年级');
  assert.deepStrictEqual(g3.volumes, ['三上', '三下']);
});

test('按册：沪教三上只含落点在三上的点，人教三上里没映射的不在；人教六年级点出现在落点年级', () => {
  assert.deepStrictEqual(Ed.gradeTargets(G, P, '三上').ids, ['cnm_p006', 'cnm_p001']);
  assert.deepStrictEqual(Ed.gradeTargets(G, P, '四下').ids, ['cnm_p002']);
  assert.deepStrictEqual(Ed.gradeTargets(G, P, '四年级').ids, ['cnm_p002']);
});

test('六年级：池为空并带预备年级说明，不去取人教六年级的点', () => {
  ['六年级', '六上', '六下'].forEach((s) => {
    const g = Ed.gradeTargets(G, P, s);
    assert.deepStrictEqual(g.ids, []);
    assert.strictEqual(g.empty, true);
    assert.match(g.reason, /预备年级/);
  });
  assert.strictEqual(Ed.gradeTargets(G, P, '七上'), null);
  assert.strictEqual(Ed.gradeTargets(G, P, '高一'), null);
  assert.strictEqual(Ed.isPrimaryScope('六年级'), true);
  assert.strictEqual(Ed.isPrimaryScope('七上'), false);
});

test('没有对应册的目标池给出空态和说明，而不是 null', () => {
  const g = Ed.gradeTargets(G, P, '一年级');
  assert.deepStrictEqual(g.ids, []);
  assert.strictEqual(g.empty, true);
  assert.match(g.reason, /该版本暂未覆盖/);
});

test('term 为 2、进度为「上」、当前年级等于落点年级：在 deferred 里，不在目标 id 里；进度「下」保留', () => {
  const ids = Ed.gradeTargets(G, P, '三年级').ids;
  const up = Ed.filterByProgress(G, P, ids, '上', 3);
  assert.deepStrictEqual(up.ids, ['cnm_p006', 'cnm_p001']);
  assert.deepStrictEqual(up.deferred, ['cnm_p003']);
  const down = Ed.filterByProgress(G, P, ids, '下', 3);
  assert.deepStrictEqual(down.ids, ids);
  assert.deepStrictEqual(down.deferred, []);
  const whole = Ed.filterByProgress(G, P, ids, '全', 3);
  assert.deepStrictEqual(whole.ids, ids);
});

test('进度过滤读落点而不是人教：落点年级不同则不按人教年级误判', () => {
  const up4 = Ed.filterByProgress(G, P, ['cnm_p002', 'cnm_p003'], '上', 4);
  assert.deepStrictEqual(up4.deferred, ['cnm_p002']);
  assert.deepStrictEqual(up4.ids, ['cnm_p003']);
  const up6 = Ed.filterByProgress(G, P, ['cnm_p002'], '上', 6);
  assert.deepStrictEqual(up6.deferred, []);
  const none = Ed.filterByProgress(G, P, ['cnm_p003', 'cnm_p002'], '上', null);
  assert.deepStrictEqual(none.deferred, ['cnm_p003', 'cnm_p002']);
});

test('人教路径不传取值函数时，filterByProgress 仍按 topic.semester 排除下册', () => {
  const all = topics.map((t) => t.id);
  const f = E.filterByProgress(G, all, '上', 3);
  assert.deepStrictEqual(f.deferred, ['cnm_p003']);
  const f2 = E.filterByProgress(G, all, '上', 6);
  assert.deepStrictEqual(f2.deferred, ['cnm_p007']);
  assert.deepStrictEqual(E.filterByProgress(G, all, '下', 6).ids, all);
});

test('先修：目标点有落点、先修点没有落点时，graph.prereqs 仍包含该先修；册次文案是「该版本暂未覆盖」', () => {
  assert.ok(Ed.isCovered(P, 'cnm_p001'));
  assert.ok(!Ed.isCovered(P, 'cnm_p005'));
  assert.ok(G.prereqs.cnm_p001.some((e) => e.id === 'cnm_p005'));
  const s = E.createSession(G, ['cnm_p001'], { limit: 40, confirm: 1 });
  assert.ok(s.order.indexOf('cnm_p005') >= 0, '回溯范围含没有落点的先修');
  const text = Ed.chapterText(P, G.byId.cnm_p005);
  assert.strictEqual(text, '该版本暂未覆盖');
  assert.ok(text.indexOf('人教单元戊') < 0 && text.indexOf('二年级') < 0, '不能带出人教 chapter 原文');
});

test('章节文案：有落点写单元名，有节名再接节名；人教（不传落点表）原样返回 chapter', () => {
  assert.strictEqual(Ed.chapterText(P, G.byId.cnm_p001), 'U1 后排的单元');
  assert.strictEqual(Ed.chapterText(P, G.byId.cnm_p006), 'U0 先排的单元 · 第一课');
  assert.strictEqual(Ed.chapterText(null, G.byId.cnm_p001), '三年级上册 第1单元 人教单元甲');
});

test('排序：同一年级学期下，单元顺序是文件里的首次出现顺序，而不是 id 顺序', () => {
  const grouped = Ed.groupByUnit(P, ['cnm_p001', 'cnm_p006', 'cnm_p003']);
  assert.deepStrictEqual(grouped.volumes.map((v) => v.volume), ['三上', '三下']);
  assert.deepStrictEqual(grouped.volumes[0].units.map((u) => u.unit), ['U0 先排的单元', 'U1 后排的单元']);
  assert.deepStrictEqual(grouped.volumes[0].units.map((u) => u.ids), [['cnm_p006'], ['cnm_p001']]);
  assert.strictEqual(grouped.volumes[0].title, '三年级上册');
  assert.deepStrictEqual(grouped.uncovered, []);
});

test('同单元内按文件里的顺序，不按 id 字母序', () => {
  const m = clone(mapping);
  m.entries = {
    cnm_p009: { grade: 1, term: 1, unit: 'A' },
    cnm_p002: { grade: 1, term: 1, unit: 'B' },
    cnm_p005: { grade: 1, term: 1, unit: 'A' },
    cnm_p001: { grade: 1, term: 1, unit: 'A' }
  };
  const Q = Ed.buildPlacement(m);
  const g = Ed.groupByUnit(Q, ['cnm_p001', 'cnm_p002', 'cnm_p005', 'cnm_p009']);
  assert.deepStrictEqual(g.volumes[0].units.map((u) => u.unit), ['A', 'B']);
  assert.deepStrictEqual(g.volumes[0].units[0].ids, ['cnm_p009', 'cnm_p005', 'cnm_p001']);
});

test('groupByUnit：没有落点的点单独放 uncovered，不进任何册', () => {
  const g = Ed.groupByUnit(P, ['cnm_p004', 'cnm_p001', 'cnm_p007', 'cnm_p005']);
  assert.deepStrictEqual(g.uncovered, ['cnm_p004', 'cnm_p007', 'cnm_p005']);
  assert.deepStrictEqual(g.volumes.map((v) => v.volume), ['三上']);
});

test('筛查按章汇总：沪教按落点单元分章，没有落点的一章排在最后', () => {
  let s = E.createSession(G, ['cnm_p001', 'cnm_p003', 'cnm_p004', 'cnm_p006'], { mode: 'screen', limit: 40, confirm: 1 });
  for (let i = 0; i < 30 && E.nextQuestion(G, s); i++) s = E.applyAnswer(G, s, E.nextQuestion(G, s), 'correct');
  const chs = E.chapterSummary(G, s, Ed.chapterView(P));
  assert.deepStrictEqual(chs.map((c) => c.label), [
    '三上 U0 先排的单元', '三上 U1 后排的单元', '三下 U9 三下', '该版本暂未覆盖'
  ]);
  const last = chs[chs.length - 1];
  assert.ok(last.total >= 1);
  chs.forEach((c) => assert.ok(c.label.indexOf('人教') < 0));
  const plain = E.chapterSummary(G, s);
  assert.ok(plain.some((c) => c.label.indexOf('人教单元甲') >= 0), '不传 view 仍是人教章名');
});

test('buildPlacement 保留 note 与 chapter，缺省为空串；status 缺省当 draft', () => {
  assert.strictEqual(Ed.placementOf(P, 'cnm_p002').note, '人教六上');
  assert.strictEqual(Ed.placementOf(P, 'cnm_p001').chapter, '');
  assert.strictEqual(Ed.buildPlacement({ version: 'hujiao', subject: 'math', stage: 'primary', entries: {} }).status, 'draft');
  assert.strictEqual(Ed.draftNote(P), '册次依据为草稿');
  assert.strictEqual(Ed.draftNote(Ed.buildPlacement(Object.assign(clone(mapping), { status: 'reviewed' }))), '');
  assert.strictEqual(Ed.draftNote(null), '');
  assert.throws(() => Ed.buildPlacement(null));
  assert.throws(() => Ed.buildPlacement({ entries: [] }));
});

test('load：只拼小学映射的路径，junior 一期拒绝', async () => {
  assert.strictEqual(Ed.mappingPath('hujiao', 'math', 'primary'), 'data/mappings/hujiao-math.json');
  assert.strictEqual(Ed.mappingPath('hujiao', 'math', 'junior'), 'data/mappings/hujiao-math-junior.json');
  const urls = [];
  const fake = (u) => { urls.push(u); return Promise.resolve({ ok: true, json: () => Promise.resolve(clone(mapping)) }); };
  const Q = await Ed.load({ fetch: fake, base: '../', version: 'hujiao', subject: 'math', stage: 'primary' });
  assert.deepStrictEqual(urls, ['../data/mappings/hujiao-math.json']);
  assert.strictEqual(Q.count, 4);
  await assert.rejects(Ed.load({ fetch: fake, stage: 'junior' }));
  assert.strictEqual(urls.length, 1, 'junior 不发请求');
  await assert.rejects(Ed.load({ fetch: () => Promise.resolve({ ok: false, status: 404 }), stage: 'primary' }));
});

test('仓库里的真实映射文件能建出落点表，且不动 topics.json 里的对象', () => {
  const real = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data/mappings/hujiao-math.json'), 'utf8'));
  const all = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data/topics.json'), 'utf8'));
  const before = JSON.stringify(all);
  const R = Ed.buildPlacement(real);
  const RG = E.buildGraph(all, []);
  const g = Ed.gradeTargets(RG, R, '三年级');
  assert.ok(g && Array.isArray(g.ids));
  Object.keys(R.byId).forEach((id) => assert.ok(RG.byId[id], id + ' 不在 topics'));
  assert.strictEqual(JSON.stringify(all), before);
});

chain.then(() => console.log('\n' + passed + ' passed'), (e) => {
  console.error('FAIL ' + (e && e.stack || e));
  process.exit(1);
});
