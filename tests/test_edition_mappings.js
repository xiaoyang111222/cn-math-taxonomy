#!/usr/bin/env node
/* 知识图谱「其他教材版本」测试：node tests/test_edition_mappings.js（无依赖，不起浏览器）。
 * 从 explore/app.js 取出 mappingTermLabel / loadMappings 在沙箱里跑，fetch 用假的；
 * 另外核对 sw.js、scripts/deploy-cf.sh 与对照表文件清单一致。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const APP = fs.readFileSync(path.join(ROOT, 'explore/app.js'), 'utf8');
const SW = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
const DEPLOY = fs.readFileSync(path.join(ROOT, 'scripts/deploy-cf.sh'), 'utf8');
let passed = 0;

async function test(name, fn) {
  await fn();
  passed++;
  console.log('  ok   ' + name);
}

function pick(re, label) {
  const m = APP.match(re);
  assert.ok(m, 'explore/app.js 里找不到 ' + label);
  return m[0];
}

const CN_SRC = pick(/var CN = \[[^\]]*\];/, 'CN');
const FILES_SRC = pick(/var MAPPING_FILES = \[[^\]]*\];/, 'MAPPING_FILES');
const LABEL_SRC = pick(/function mappingTermLabel\(m\) \{[\s\S]*?\n  \}\n/, 'mappingTermLabel');
const LOAD_SRC = pick(/async function loadMappings\(\) \{[\s\S]*?\n  \}\n/, 'loadMappings');
const MAPPING_FILES = vm.runInNewContext(FILES_SRC + ' MAPPING_FILES;');

function sandbox(responses) {
  const requested = [];
  const context = {
    fetch(url) {
      requested.push(url);
      const name = url.replace('../data/mappings/', '').replace(/\.json$/, '');
      const r = responses[name];
      if (r instanceof Error) return Promise.reject(r);
      if (r === undefined) return Promise.resolve({ ok: false, json: () => Promise.reject(new Error('404')) });
      return Promise.resolve({ ok: true, json: () => (typeof r === 'function' ? r() : Promise.resolve(JSON.parse(JSON.stringify(r)))) });
    }
  };
  vm.runInNewContext(CN_SRC + FILES_SRC + 'var mappingsByTopic = new Map();' + LABEL_SRC + LOAD_SRC, context);
  context.requested = requested;
  context.result = () => {
    const out = {};
    context.mappingsByTopic.forEach((v, k) => { out[k] = JSON.parse(JSON.stringify(v)); });
    return out;
  };
  return context;
}

const sujiao = {
  edition: 'sujiao_math', label: '苏教版（江苏凤凰教育出版社）数学', status: 'draft',
  entries: [
    { topicId: 'cnm_p001', grade: 1, term: '上', unit: '一 0～5的认识和加减法' },
    { topicId: 'cnm_p003', grade: 1, term: '上', unit: '一 0～5的认识和加减法', chapter: '几和第几', note: '**重点**看例2' }
  ]
};
const sd54 = {
  edition: 'sd54_math', label: '山东五四制·数学（青岛出版社）', status: 'reviewed',
  entries: [{ topicId: 'cnm_p001', grade: 2, term: '下' }]
};

(async () => {
  await test('MAPPING_FILES 只列四个真实对照表，不含示例文件', () => {
    assert.deepStrictEqual(Array.from(MAPPING_FILES), ['sujiao_math', 'hujiao_math', 'sd54_math', 'yilin_english']);
    MAPPING_FILES.forEach(name => assert.ok(!/example/.test(name)));
  });

  await test('mappingTermLabel：上 / 下册显示「三上」，全年显示「三年级」', () => {
    const ctx = sandbox({});
    assert.equal(ctx.mappingTermLabel({ grade: 3, term: '上' }), '三上');
    assert.equal(ctx.mappingTermLabel({ grade: 9, term: '下' }), '九下');
    assert.equal(ctx.mappingTermLabel({ grade: 7, term: '全' }), '七年级');
  });

  await test('mappingTermLabel：年级超出 CN 表时退回数字', () => {
    const ctx = sandbox({});
    assert.equal(ctx.mappingTermLabel({ grade: 10, term: '上' }), '10上');
    assert.equal(ctx.mappingTermLabel({ grade: 12, term: '全' }), '12年级');
  });

  await test('loadMappings 从 ../data/mappings/ 请求每个文件各一次', async () => {
    const ctx = sandbox({});
    await ctx.loadMappings();
    assert.deepStrictEqual(ctx.requested.slice().sort(),
      Array.from(MAPPING_FILES, n => '../data/mappings/' + n + '.json').sort());
  });

  await test('loadMappings 按知识点归集，多个版本落在同一个知识点下', async () => {
    const ctx = sandbox({ sujiao_math: sujiao, sd54_math: sd54 });
    await ctx.loadMappings();
    const got = ctx.result();
    assert.deepStrictEqual(Object.keys(got).sort(), ['cnm_p001', 'cnm_p003']);
    assert.equal(got.cnm_p001.length, 2);
    assert.deepStrictEqual(got.cnm_p001.map(m => m.label).sort(), ['山东五四制', '苏教版'].sort());
    assert.deepStrictEqual(got.cnm_p003, [{
      label: '苏教版', grade: 1, term: '上', unit: '一 0～5的认识和加减法',
      chapter: '几和第几', note: '**重点**看例2', status: 'draft'
    }]);
  });

  await test('loadMappings：版本名截到括号或「·」之前，缺字段补空串，状态取文件的', async () => {
    const ctx = sandbox({ sd54_math: sd54, yilin_english: { label: '译林版(译林出版社)英语', entries: [{ topicId: 'cne_p001', grade: 3, term: '全' }] } });
    await ctx.loadMappings();
    const got = ctx.result();
    assert.deepStrictEqual(got.cnm_p001[0], { label: '山东五四制', grade: 2, term: '下', unit: '', chapter: '', note: '', status: 'reviewed' });
    assert.equal(got.cne_p001[0].label, '译林版');
    assert.equal(got.cne_p001[0].status, 'draft');
  });

  await test('loadMappings：没有 label 时用 edition', async () => {
    const ctx = sandbox({ hujiao_math: { edition: 'hujiao_math', entries: [{ topicId: 'cnm_p010', grade: 1, term: '下' }] } });
    await ctx.loadMappings();
    assert.equal(ctx.result().cnm_p010[0].label, 'hujiao_math');
  });

  await test('loadMappings 跳过 status 为 example 的文件', async () => {
    const example = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/mappings/hujiao_math.example.json'), 'utf8'));
    const ctx = sandbox({ hujiao_math: example, sujiao_math: sujiao });
    await ctx.loadMappings();
    const got = ctx.result();
    Object.values(got).forEach(list => list.forEach(m => assert.notEqual(m.label, '沪教版')));
    assert.ok(!got.cnm_p029 && !got.cnm_p188);
  });

  await test('loadMappings：404、网络错误、坏 JSON 都跳过，不影响其他文件', async () => {
    const ctx = sandbox({
      sujiao_math: sujiao,
      hujiao_math: new Error('offline'),
      sd54_math: () => Promise.reject(new SyntaxError('bad json'))
    });
    await ctx.loadMappings();
    const got = ctx.result();
    assert.deepStrictEqual(Object.keys(got).sort(), ['cnm_p001', 'cnm_p003']);
    assert.equal(got.cnm_p001.length, 1);
  });

  await test('loadMappings：entries 不是数组、条目缺 topicId 或为空都忽略', async () => {
    const ctx = sandbox({
      sujiao_math: { label: '苏教版', entries: 'oops' },
      hujiao_math: { label: '沪教版', entries: [null, {}, { grade: 1, term: '上' }, { topicId: 'cnm_p050', grade: 2, term: '上' }] },
      sd54_math: {}
    });
    await ctx.loadMappings();
    const got = ctx.result();
    assert.deepStrictEqual(Object.keys(got), ['cnm_p050']);
  });

  await test('loadMappings 每次重建，不累积上一次的结果', async () => {
    const ctx = sandbox({ sujiao_math: sujiao });
    await ctx.loadMappings();
    await ctx.loadMappings();
    assert.equal(ctx.result().cnm_p001.length, 1);
  });

  await test('真实对照表能被读进来，每条都有知识点和合法的年级册次', async () => {
    const real = {};
    MAPPING_FILES.forEach(name => {
      const file = path.join(ROOT, 'data/mappings', name + '.json');
      assert.ok(fs.existsSync(file), name + '.json 不存在');
      real[name] = JSON.parse(fs.readFileSync(file, 'utf8'));
      assert.notEqual(real[name].status, 'example');
      assert.ok(Array.isArray(real[name].entries) && real[name].entries.length > 0);
    });
    const ctx = sandbox(real);
    await ctx.loadMappings();
    const got = ctx.result();
    const total = MAPPING_FILES.reduce((n, name) => n + real[name].entries.filter(e => e && e.topicId).length, 0);
    assert.equal(Object.values(got).reduce((n, l) => n + l.length, 0), total);
    Object.values(got).forEach(list => list.forEach(m => {
      assert.ok(m.label && !/[（(·]/.test(m.label), '版本名没截干净：' + m.label);
      assert.ok(['上', '下', '全'].includes(m.term), '册次不合法：' + m.term);
      assert.ok(!/undefined/.test(ctx.mappingTermLabel(m)));
    }));
    assert.ok(got.cnm_p001.some(m => m.label === '苏教版'));
  });

  await test('知识点数据加载后同时读题库和对照表', () => {
    assert.ok(/Promise\.all\(\[loadQuestions\(\), loadMappings\(\)\]\)/.test(APP));
  });

  await test('sw.js 预缓存四个对照表、不缓存示例文件，VERSION 已升到 v9', () => {
    MAPPING_FILES.forEach(name => assert.ok(SW.includes("'data/mappings/" + name + ".json'"), 'sw.js 缺 ' + name));
    assert.ok(!/example\.json/.test(SW));
    assert.ok(/var VERSION = 'v9';/.test(SW));
  });

  await test('deploy-cf.sh 建 data/mappings 目录并复制四个对照表', () => {
    assert.ok(DEPLOY.includes('"$DIST/data/mappings"'));
    MAPPING_FILES.forEach(name => assert.ok(DEPLOY.includes('"$ROOT/data/mappings/' + name + '.json"'), 'deploy 缺 ' + name));
    assert.ok(DEPLOY.includes('"$DIST/data/mappings/"'));
    assert.ok(!/example\.json/.test(DEPLOY));
  });

  console.log(passed + ' passed');
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
