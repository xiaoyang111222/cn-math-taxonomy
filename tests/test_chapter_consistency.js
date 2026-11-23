#!/usr/bin/env node
/* 章节数据一致性（Issue #58）：node tests/test_chapter_consistency.js
 * 1. 同一学科、同一册内，同一个编号（第N单元 / 第N章 / 第N课）只能对应一个单元名；
 * 2. 综合与实践点的 chapter 必须是册级格式「X年级X册 综合与实践 活动名」；
 * 3. 九年级综合与实践的册级写法能被 parseChapter 解析，整册诊断、章节汇总、学习进度过滤照常工作。
 */
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
const byId = new Map(topics.map((t) => [t.id, t]));
const G = E.buildGraph(topics, deps, questions);

let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

const PREFIX = { cnm_: 'math', cne_: 'english', cnp_: 'physics', cnc_: 'chinese', cns_: 'science', cnd_: 'morality', cnh_: 'history', cng_: 'geography', cnb_: 'biology', cnk_: 'chemistry', cnz_: 'politics' };
function subjectOf(t) {
  if (t.subject) return t.subject;
  const p = Object.keys(PREFIX).find((k) => t.id.startsWith(k));
  return p ? PREFIX[p] : 'math';
}

/* 七、八年级的综合与实践点仍是章级写法（「七上 第二章 有理数的运算 综合与实践」），Issue #58 没有要求改，
 * 这里只登记现状，不让新的章级综实点混进来。改成册级后可以从这个名单删掉。 */
const LEGACY_CHAPTER_LEVEL = new Set(['cnm_024', 'cnm_061', 'cnm_101', 'cnm_109', 'cnm_119', 'cnm_141', 'cnm_210', 'cnm_218']);

const NUM_ZH = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
const VOLUME_LEVEL = /^([一二三四五六九])年级([上下])册 综合与实践 (\S.*)$/;

test('同一册内同一单元号不对应两个单元名', () => {
  const seen = new Map();
  const conflicts = [];
  topics.forEach((t) => {
    if (t.external) return;
    const c = E.parseChapter(t.chapter);
    if (!c.volume || !/^(第.+(单元|章|课)|预备单元\d)$/.test(c.chapterNo)) return;
    // 高中语文「必修上 第一单元 第1课」只有课名没有单元名，chapterName 是课号，不属于这条规则
    if (subjectOf(t) === 'chinese' && /^(必修|选必)[上中下]$/.test(c.volume)) return;
    const key = [subjectOf(t), c.volume, c.chapterNo].join(' | ');
    if (!seen.has(key)) seen.set(key, new Map());
    const names = seen.get(key);
    if (!names.has(c.chapterName)) names.set(c.chapterName, []);
    names.get(c.chapterName).push(t.id);
  });
  seen.forEach((names, key) => {
    if (names.size > 1) conflicts.push(key + ' -> ' + Array.from(names).map(([n, ids]) => n + '(' + ids.slice(0, 3).join(',') + ')').join(' / '));
  });
  assert.deepStrictEqual(conflicts, []);
});

test('四上条形统计图在第7单元，除数是两位数的除法在第6单元', () => {
  ['cnm_p108', 'cnm_p130'].forEach((id) => assert.strictEqual(byId.get(id).chapter, '四年级上册 第7单元 条形统计图', id));
  ['cnm_p106', 'cnm_p107'].forEach((id) => assert.strictEqual(byId.get(id).chapter, '四年级上册 第6单元 除数是两位数的除法', id));
});

test('综合与实践点的 chapter 是册级格式，且册次与 grade/semester 一致', () => {
  const synth = topics.filter((t) => String(t.chapter).indexOf('综合与实践') >= 0);
  assert.ok(synth.length >= 30, '综合与实践点变少了：' + synth.length);
  const bad = [];
  synth.forEach((t) => {
    if (LEGACY_CHAPTER_LEVEL.has(t.id)) return;
    const m = VOLUME_LEVEL.exec(t.chapter);
    if (!m || NUM_ZH.indexOf(m[1]) !== t.grade || m[2] !== t.semester) bad.push(t.id + ' ' + t.chapter);
  });
  assert.deepStrictEqual(bad, []);
  const stillChapterLevel = synth.filter((t) => !VOLUME_LEVEL.test(t.chapter)).map((t) => t.id).sort();
  assert.deepStrictEqual(stillChapterLevel.filter((id) => !LEGACY_CHAPTER_LEVEL.has(id)), []);
});

const NINTH = {
  cnm_243: ['九年级上册 综合与实践 高铁列车运行中的数量关系', '九上', '高铁列车运行中的数量关系'],
  cnm_267: ['九年级上册 综合与实践 生活中的优化问题', '九上', '生活中的优化问题'],
  cnm_290: ['九年级下册 综合与实践 停车设计问题', '九下', '停车设计问题'],
  cnm_291: ['九年级下册 综合与实践 建筑中的数学', '九下', '建筑中的数学']
};

test('九年级综合与实践：parseChapter 解析为册 + 综合与实践 + 活动名', () => {
  Object.keys(NINTH).forEach((id) => {
    const [chapter, volume, name] = NINTH[id];
    assert.strictEqual(byId.get(id).chapter, chapter, id);
    assert.deepStrictEqual(E.parseChapter(chapter), { volume: volume, chapterNo: '综合与实践', chapterName: name, section: '' }, id);
  });
  // 小学写法不受影响，七、八年级的章级写法仍按章解析
  assert.deepStrictEqual(E.parseChapter('一年级上册 综合与实践 数学游戏'), { volume: '一上', chapterNo: '综合与实践', chapterName: '数学游戏', section: '' });
  assert.deepStrictEqual(E.parseChapter('七上 第二章 有理数的运算 综合与实践'), { volume: '七上', chapterNo: '第二章', chapterName: '有理数的运算', section: '综合与实践' });
});

test('整册诊断：九上含 243/267 不含 290/291，九下反之，九年级整体含四个', () => {
  const up = E.gradeTargets(G, '九上', 'math').ids;
  const down = E.gradeTargets(G, '九下', 'math').ids;
  const all = E.gradeTargets(G, '九年级', 'math').ids;
  ['cnm_243', 'cnm_267'].forEach((id) => { assert.ok(up.includes(id), id + ' 在九上'); assert.ok(!down.includes(id), id + ' 不在九下'); });
  ['cnm_290', 'cnm_291'].forEach((id) => { assert.ok(down.includes(id), id + ' 在九下'); assert.ok(!up.includes(id), id + ' 不在九上'); });
  Object.keys(NINTH).forEach((id) => assert.ok(all.includes(id), id + ' 在九年级'));
  // 改格式前后，九上、九下的知识点集合应当只靠 volume 划分：不丢点、不串册
  assert.strictEqual(up.length, topics.filter((t) => !t.external && t.grade === 9 && t.semester === '上' && subjectOf(t) === 'math').length);
  assert.strictEqual(down.length, topics.filter((t) => !t.external && t.grade === 9 && t.semester === '下' && subjectOf(t) === 'math').length);
});

test('学期 / 进度过滤：九上上学期保留 243/267，延后 290/291（按 semester，不依赖 chapter 文字）', () => {
  const ids = Object.keys(NINTH);
  const f = E.filterByProgress(G, ids, '上', 9);
  assert.deepStrictEqual(f.ids.sort(), ['cnm_243', 'cnm_267']);
  assert.deepStrictEqual(f.deferred.sort(), ['cnm_290', 'cnm_291']);
  assert.deepStrictEqual(E.filterByProgress(G, ids, '下', 9).ids.sort(), ids.slice().sort());
});

test('章节汇总：九年级综合与实践各成一章，章名带活动名，原章（反比例函数等）仍在', () => {
  const s = E.createSession(G, E.gradeTargets(G, '九年级', 'math').ids, { limit: 12 });
  const sum = E.chapterSummary(G, s);
  const keys = sum.map((c) => c.key);
  Object.keys(NINTH).forEach((id) => {
    const [, volume, name] = NINTH[id];
    const hit = sum.filter((c) => c.key === volume + ' 综合与实践 ' + name);
    assert.strictEqual(hit.length, 1, id);
    assert.strictEqual(hit[0].total, 1, id);
    assert.ok(hit[0].untestedIds.includes(id) || hit[0].weakIds.includes(id) || hit[0].shakyIds.includes(id) || hit[0].mastered === 1, id);
  });
  ['九上 第二十七章 反比例函数', '九上 第三十章 直线与圆的位置关系', '九下 第三十二章 锐角三角函数', '九下 第三十三章 投影与视图'].forEach((k) => {
    const hit = sum.filter((c) => c.key === k);
    assert.strictEqual(hit.length, 1, k);
    assert.ok(hit[0].total >= 1, k);
  });
  assert.strictEqual(new Set(keys).size, keys.length, '章节汇总出现重复的章');
});

test('章节浏览器：按 app.js 的 buildTree 同样的分组，九上/九下各多出综合与实践章，且不重复', () => {
  const tree = {};
  topics.forEach((t) => {
    if (t.external) return;
    const c = E.parseChapter(t.chapter);
    const v = tree[c.volume] || (tree[c.volume] = { chapters: [], byKey: {} });
    const nameParts = [c.chapterNo, c.chapterName].filter(Boolean);
    const key = nameParts.join(' ');
    let ch = v.byKey[key];
    if (!ch) { ch = v.byKey[key] = { key: c.volume + ' ' + c.chapterNo, label: key, topics: [] }; v.chapters.push(ch); }
    ch.topics.push({ t: t, section: c.section });
  });
  const labels = (vol) => tree[vol].chapters.map((c) => c.label);
  assert.ok(labels('九上').includes('综合与实践 高铁列车运行中的数量关系'));
  assert.ok(labels('九上').includes('综合与实践 生活中的优化问题'));
  assert.ok(labels('九下').includes('综合与实践 停车设计问题'));
  assert.ok(labels('九下').includes('综合与实践 建筑中的数学'));
  assert.ok(labels('九上').includes('第二十七章 反比例函数'));
  assert.ok(!labels('九上').some((l) => /综合与实践$/.test(l)), '九上不应再有「章名 + 综合与实践」小节挂在原章下的写法');
});

console.log('\n' + passed + ' passed');
