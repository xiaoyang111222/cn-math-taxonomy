#!/usr/bin/env node
/* 沪教版映射文件格式测试：node tests/test_hujiao_mapping.js（无依赖）。
   规则见 docs/hujiao-mapping-plan.md 第 2、5 节。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const FILE = path.join(ROOT, 'data/mappings/hujiao-math.json');
const TOPICS = path.join(ROOT, 'data/topics.json');
const MAP_DIR = path.join(ROOT, 'data/mappings');
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

/* 找出原始 JSON 文本里同一对象内重复出现的键（JSON.parse 会静默留下后者）。 */
function findDuplicateKeys(text) {
  const dups = [];
  let i = 0;
  function ws() { while (i < text.length && /\s/.test(text[i])) i++; }
  function str() {
    const start = i;
    i++;
    while (text[i] !== '"') { if (text[i] === '\\') i++; i++; }
    i++;
    return JSON.parse(text.slice(start, i));
  }
  function value(where) {
    ws();
    const c = text[i];
    if (c === '{') {
      i++;
      const seen = new Set();
      ws();
      if (text[i] === '}') { i++; return; }
      for (;;) {
        ws();
        const k = str();
        if (seen.has(k)) dups.push(where + '/' + k);
        seen.add(k);
        ws();
        i++; // :
        value(where + '/' + k);
        ws();
        if (text[i] === ',') { i++; continue; }
        i++; // }
        return;
      }
    }
    if (c === '[') {
      i++;
      ws();
      if (text[i] === ']') { i++; return; }
      for (;;) {
        value(where + '[]');
        ws();
        if (text[i] === ',') { i++; continue; }
        i++; // ]
        return;
      }
    }
    if (c === '"') { str(); return; }
    while (i < text.length && !/[,\]}\s]/.test(text[i])) i++;
  }
  value('');
  return dups;
}

if (!fs.existsSync(FILE)) {
  console.error('data/mappings/hujiao-math.json 不存在：先提交映射文件骨架，页面才不会去 fetch 一个 404。');
  process.exit(1);
}

const raw = fs.readFileSync(FILE, 'utf8');
const map = JSON.parse(raw);
const topics = JSON.parse(fs.readFileSync(TOPICS, 'utf8'));
const byId = new Map(topics.map((t) => [t.id, t]));
const HEAD_FIELDS = ['version', 'subject', 'stage', 'label', 'status', 'source', 'contributor', 'note', 'entries'];
const ENTRY_FIELDS = ['grade', 'term', 'unit', 'chapter', 'note'];
const nonEmpty = (v) => typeof v === 'string' && v.trim() !== '';

test('findDuplicateKeys 能识别重复键', () => {
  assert.deepEqual(findDuplicateKeys('{"a":{"x":1,"x":2},"b":[{"k":1},{"k":2}]}'), ['/a/x']);
  assert.deepEqual(findDuplicateKeys('{"a":1,"b":{"a":2}}'), []);
  assert.deepEqual(findDuplicateKeys('{"entries":{"cnm_p001":{"grade":1},"cnm_p001":{"grade":2}}}'), ['/entries/cnm_p001']);
});

test('文件 UTF-8 无 BOM，原始文本无重复键', () => {
  assert.notEqual(raw.charCodeAt(0), 0xfeff);
  assert.deepEqual(findDuplicateKeys(raw), []);
});

test('文件头：必填字段齐全，无未知字段', () => {
  assert.ok(map && typeof map === 'object' && !Array.isArray(map));
  for (const k of Object.keys(map)) assert.ok(HEAD_FIELDS.includes(k), '未知顶层字段 ' + k);
  for (const k of ['version', 'subject', 'stage', 'source', 'contributor', 'entries']) {
    assert.ok(k in map, '缺少 ' + k);
  }
  assert.ok(nonEmpty(map.source) && map.source.length <= 2000);
  assert.ok(nonEmpty(map.contributor) && map.contributor.length <= 40);
  for (const k of ['label', 'note']) if (k in map) assert.ok(nonEmpty(map[k]), k);
  assert.ok(map.entries && typeof map.entries === 'object' && !Array.isArray(map.entries));
});

test('version/subject/stage 与文件名一致，一期是 hujiao + math + primary', () => {
  assert.match(map.version, /^[a-z][a-z0-9]*$/);
  assert.equal(map.version, 'hujiao');
  assert.equal(map.subject, 'math');
  assert.equal(map.stage, 'primary');
  assert.equal(path.basename(FILE), map.version + '-' + map.subject + '.json');
});

test('status 缺省或为 draft/reviewed；reviewed 时至少一条', () => {
  const status = map.status === undefined ? 'draft' : map.status;
  assert.ok(['draft', 'reviewed'].includes(status));
  if (status === 'reviewed') assert.ok(Object.keys(map.entries).length >= 1);
});

test('条目：topicId 是小学数学正式点，字段与取值合法', () => {
  for (const [id, e] of Object.entries(map.entries)) {
    const t = byId.get(id);
    assert.ok(t, id + ' 不在 topics.json');
    assert.ok(!t.external, id + ' 是 external');
    assert.match(id, /^cnm_p\d+$/, id);
    assert.ok(e && typeof e === 'object' && !Array.isArray(e), id);
    for (const k of Object.keys(e)) assert.ok(ENTRY_FIELDS.includes(k), id + ' 未知字段 ' + k);
    assert.ok(Number.isInteger(e.grade) && e.grade >= 1 && e.grade <= 5, id + ' grade ' + e.grade);
    assert.ok(e.term === 1 || e.term === 2, id + ' term ' + e.term);
    assert.ok(nonEmpty(e.unit), id + ' unit');
    for (const k of ['chapter', 'note']) if (k in e) assert.ok(nonEmpty(e[k]), id + ' ' + k);
  }
});

test('unit/chapter/note 不含「示例」「占位」', () => {
  for (const [id, e] of Object.entries(map.entries)) {
    for (const k of ['unit', 'chapter', 'note']) {
      if (typeof e[k] === 'string') assert.ok(!/示例|占位/.test(e[k]), id + ' ' + k);
    }
  }
  for (const k of ['label', 'note', 'source', 'contributor']) {
    if (typeof map[k] === 'string') assert.ok(!/示例|占位/.test(map[k]), '文件头 ' + k);
  }
});

test('topics.json 不含任何 mappings 字段', () => {
  const withMappings = topics.filter((t) => Object.prototype.hasOwnProperty.call(t, 'mappings'));
  assert.equal(withMappings.length, 0);
});

test('旧的下划线对照文件仍在，且不被新文件取代', () => {
  for (const fn of ['hujiao_math.json', 'hujiao_math.example.json', 'sujiao_math.json', 'sd54_math.json', 'yilin_english.json']) {
    const d = JSON.parse(fs.readFileSync(path.join(MAP_DIR, fn), 'utf8'));
    assert.ok(Array.isArray(d.entries) && d.entries.length > 0, fn);
    assert.ok(typeof d.edition === 'string', fn);
  }
});

test('sw.js：壳含 edition.js，预缓存数据含映射文件，路径与页面请求的是同一个 URL', () => {
  const sw = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
  const list = (name) => {
    const m = new RegExp('var ' + name + ' = \\[([\\s\\S]*?)\\];').exec(sw);
    assert.ok(m, name);
    return m[1].split(',').map((x) => x.trim().replace(/^'|'$/g, '')).filter(Boolean);
  };
  assert.ok(list('SHELL').includes('assets/edition.js'));
  assert.ok(list('DATA').includes('data/mappings/hujiao-math.json'));
  const Ed = require('../assets/edition.js');
  assert.strictEqual(Ed.mappingPath(map.version, map.subject, map.stage), 'data/mappings/hujiao-math.json');
  ['diagnose/index.html', 'explore/index.html', 'children/history.html'].forEach((page) => {
    const html = fs.readFileSync(path.join(ROOT, page), 'utf8');
    assert.ok(html.includes('<script src="../assets/edition.js"></script>'), page + ' 没有引入 edition.js');
  });
});

test('覆盖率（只打印，不设最低线）', () => {
  const denom = topics.filter((t) => /^cnm_p\d+$/.test(t.id) && !t.external);
  const numer = denom.filter((t) => Object.prototype.hasOwnProperty.call(map.entries, t.id));
  const g6 = denom.filter((t) => t.grade === 6);
  const g6cov = g6.filter((t) => Object.prototype.hasOwnProperty.call(map.entries, t.id));
  const n = Object.keys(map.entries).length;
  assert.ok(numer.length <= denom.length);
  assert.equal(numer.length, n, '条目里有不属于小学数学正式点的 id');
  console.log('       覆盖率 %d/%d；entries %d 条；人教六年级点 %d 个，其中已有落点 %d 个',
    numer.length, denom.length, n, g6.length, g6cov.length);
});

console.log('\n' + passed + ' passed');
