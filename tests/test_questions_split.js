#!/usr/bin/env node
/* 题库按学科拆分：对账（总数、不丢不重、归属）、索引、前端和 sw 不再引用整包。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const readJson = (p) => JSON.parse(read(p));
const SUBJECTS = ['math', 'chinese', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'morality', 'science'];
const PREFIX = { cnm_: 'math', cne_: 'english', cnp_: 'physics', cnc_: 'chinese', cns_: 'science', cnd_: 'morality', cnh_: 'history', cng_: 'geography', cnb_: 'biology', cnk_: 'chemistry' };
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

const all = readJson('data/questions.json');
const topics = readJson('data/topics.json');
const index = readJson('data/questions/index.json');
const subjectOfTopic = {};
topics.forEach((t) => {
  const byPrefix = Object.keys(PREFIX).find((p) => t.id.startsWith(p));
  subjectOfTopic[t.id] = SUBJECTS.includes(t.subject) ? t.subject : PREFIX[byPrefix];
});
const parts = {};
SUBJECTS.forEach((s) => { parts[s] = readJson('data/questions/' + s + '.json'); });

test('恰好 10 个学科文件加 index.json', () => {
  const names = fs.readdirSync(path.join(ROOT, 'data/questions')).sort();
  assert.deepStrictEqual(names, SUBJECTS.map((s) => s + '.json').concat(['index.json']).sort());
});

test('拆分前后总数一致，且不丢不重', () => {
  const sum = SUBJECTS.reduce((n, s) => n + parts[s].length, 0);
  assert.strictEqual(sum, all.length);
  const ids = [].concat(...SUBJECTS.map((s) => parts[s].map((q) => q.id)));
  assert.strictEqual(new Set(ids).size, ids.length, '题 id 重复');
  assert.deepStrictEqual(new Set(ids), new Set(all.map((q) => q.id)));
});

test('每道题落在其知识点所属学科的文件里，内容与原题逐字相同', () => {
  const byId = new Map(all.map((q) => [q.id, q]));
  SUBJECTS.forEach((s) => {
    parts[s].forEach((q) => {
      assert.strictEqual(subjectOfTopic[q.topicId], s, q.id + ' 放错学科：' + s);
      assert.deepStrictEqual(q, byId.get(q.id), q.id + ' 内容变了');
    });
  });
});

test('index.json 的题数和各科文件、总数一致', () => {
  assert.strictEqual(index.total, all.length);
  assert.deepStrictEqual(Object.keys(index.subjects).sort(), SUBJECTS.slice().sort());
  SUBJECTS.forEach((s) => {
    assert.strictEqual(index.subjects[s].file, s + '.json');
    assert.strictEqual(index.subjects[s].count, parts[s].length, s);
  });
});

test('拆分文件与 questions.json 同步（改题后须重跑 scripts/split_questions.py）', () => {
  const { spawnSync } = require('child_process');
  const r = spawnSync('python3', [path.join(ROOT, 'scripts/split_questions.py'), '--check'], { encoding: 'utf8' });
  assert.strictEqual(r.status, 0, (r.stderr || '') + (r.stdout || ''));
});

test('页面和 sw 不再请求整包 questions.json', () => {
  ['diagnose/app.js', 'explore/app.js', 'assets/home.js'].forEach((p) => {
    assert.ok(!/questions\.json/.test(read(p)), p + ' 仍引用 questions.json');
  });
  const sw = read('sw.js');
  assert.ok(!/'data\/questions\.json'/.test(sw), 'sw 仍缓存整包');
  assert.ok(sw.includes("'data/questions/index.json'"));
  assert.ok(!/'data\/questions\/(?!index|math)\w+\.json'/.test(sw), 'sw 不应预缓存非默认学科题库');
});

test('诊断页和图谱页按当前学科取文件', () => {
  assert.ok(read('diagnose/app.js').includes("'../data/questions/' + subject + '.json'"));
  assert.ok(read('explore/app.js').includes("'../data/questions/' + subject + '.json'"));
});

test('sw 版本已升到 v35', () => {
  assert.ok(/var VERSION = 'v35';/.test(read('sw.js')));
});

console.log(passed + ' passed');
