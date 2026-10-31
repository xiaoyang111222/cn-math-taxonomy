#!/usr/bin/env node
/* 跨设备同步测试：node tests/test_sync.js （无依赖，仅用 assert）
 * 覆盖：首次上传、双端合并、空档案不覆盖、删除不复活、诊断记录合并、刷新防循环。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'assets', 'children.js'), 'utf8');
const KEY = 'cnmChildren.v1';
const REC_KEY = 'cnmChildren.records.v1';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function makeStorage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => { m.set(k, String(v)); },
    removeItem: (k) => { m.delete(k); }
  };
}

/* 每个用例一份干净环境；env 自带网络桩，测试里随时 net({...}) 换路由都不会踩空 */
function env() {
  global.window = {};
  global.localStorage = makeStorage();
  global.sessionStorage = makeStorage();
  global.location = { count: 0, reload() { this.count++; } };
  puts.length = 0;
  net({});
  (0, eval)(SRC);
  return global.window.CnmChildren;
}

/* routes: { '/store/children.json': <对象> }；没配的路径一律 404，PUT 记进常驻的 puts 里 */
let ROUTES = {};
const puts = [];
function net(routes) {
  ROUTES = routes;
  global.fetch = (url, opts) => {
    const o = opts || {};
    if (o.method === 'PUT') {
      puts.push({ url, body: JSON.parse(o.body) });
      return Promise.resolve({ status: 201, ok: true });
    }
    if (!(url in ROUTES)) return Promise.resolve({ status: 404, ok: false });
    return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve(ROUTES[url]) });
  };
  return puts;
}

const kid = (id, name, extra) => Object.assign(
  { id, name, grade: '三年级', textbook: '人教版', createdAt: '2026-01-01T00:00:00.000Z' }, extra || {});
const rec = (key, at, extra) => Object.assign(
  { key, savedAt: at, updatedAt: at, mastered: [], shaky: [], weak: ['cnm_1'], roots: [], label: key }, extra || {});

const tests = [];
const t = (name, fn) => tests.push([name, fn]);

t('本地有档案、服务端还没有 → 首次上传（手机把数据推上云）', async () => {
  const CC = env();
  global.localStorage.setItem(KEY, JSON.stringify({ v: 1, current: 'c1', children: [kid('c1', '小明')] }));
  const puts = net({});
  const changed = await CC.sync();
  assert.strictEqual(changed, false, '服务端没有数据，本地不该被判为「有变化」');
  const up = puts.find((p) => p.url === '/store/children.json');
  assert.ok(up, '应该把 children.json 推上去');
  assert.strictEqual(up.body.children[0].name, '小明');
  assert.strictEqual(puts.filter((p) => p.url === '/store/records.json').length, 0, '空记录不上传');
});

t('电脑和手机各有一个孩子 → 合并后两边都在', async () => {
  const CC = env();
  global.localStorage.setItem(KEY, JSON.stringify({ v: 1, current: 'phone', children: [kid('phone', '手机加的')] }));
  net({ '/store/children.json': { v: 1, current: 'pc', children: [kid('pc', '电脑加的')] } });
  const changed = await CC.sync();
  assert.strictEqual(changed, true);
  const names = CC.list().map((c) => c.name);
  assert.deepStrictEqual(names.sort(), ['电脑加的', '手机加的'].sort());
});

t('本地是空的 → 直接采用服务端数据，且绝不上传空档案', async () => {
  const CC = env();
  const puts = net({ '/store/children.json': { v: 1, current: 'c1', children: [kid('c1', '小明')] } });
  const changed = await CC.sync();
  assert.strictEqual(changed, true);
  assert.strictEqual(CC.list().length, 1, '空本地要吃到服务端的档案');
  assert.strictEqual(puts.length, 0, '空档案一旦上传就会把家人的数据清空');
});

t('这边删掉的孩子不会被那边复活', async () => {
  const CC = env();
  global.localStorage.setItem(KEY, JSON.stringify({
    v: 1, current: null, children: [], deleted: { gone: '2026-02-01T00:00:00.000Z' }
  }));
  net({ '/store/children.json': { v: 1, current: 'gone', children: [kid('gone', '已删除')] } });
  await CC.sync();
  assert.strictEqual(CC.list().length, 0, '墓碑要挡住另一端的旧数据');
});

t('两边各自的诊断记录都保留', async () => {
  const CC = env();
  global.localStorage.setItem(REC_KEY, JSON.stringify({ c1: [rec('a', '2026-03-01T00:00:00.000Z')] }));
  net({ '/store/records.json': { c1: [rec('b', '2026-03-02T00:00:00.000Z')] } });
  await CC.sync();
  const keys = CC.recordsOf('c1').map((r) => r.key).sort();
  assert.deepStrictEqual(keys, ['a', 'b'], '孩子的测试记录两边要合成一份');
});

t('同一条记录两边都改过 → 取 updatedAt 新的那份', async () => {
  const CC = env();
  global.localStorage.setItem(REC_KEY, JSON.stringify(
    { c1: [rec('same', '2026-03-01T00:00:00.000Z', { updatedAt: '2026-03-05T00:00:00.000Z' })] }));
  net({ '/store/records.json': { c1: [rec('same', '2026-03-01T00:00:00.000Z', { updatedAt: '2026-03-06T00:00:00.000Z' })] } });
  await CC.sync();
  const all = JSON.parse(global.localStorage.getItem(REC_KEY));
  assert.strictEqual(all.c1[0].updatedAt, '2026-03-06T00:00:00.000Z');
});

t('两边数据一模一样 → 不改本地、不多余回写', async () => {
  const CC = env();
  const same = { v: 1, current: 'c1', children: [kid('c1', '小明')] };
  global.localStorage.setItem(KEY, JSON.stringify(same));
  const puts = net({ '/store/children.json': same });
  await sleep(20);      // 等 setup 阶段的推送（含去抖后的补推）全部落地
  puts.length = 0;      // 只看这次 sync 会不会白回写
  const changed = await CC.sync();
  assert.strictEqual(changed, false, '内容一致就不该判为有变化');
  assert.strictEqual(puts.length, 0, '一致还回写就是白折腾一次网络');
});

t('诊断页自己写的会话存档也会推上去（模拟它的 lsSet）', async () => {
  const CC = env();
  const puts = net({});
  global.localStorage.setItem('cnmDiagnose.session.v2', JSON.stringify({
    v: 2, mode: 'target', targets: ['cnm_221'], limit: 8, answers: [], seed: 'abc', savedAt: '2026-03-01T00:00:00.000Z'
  }));
  await sleep(20);
  const up = puts.find((p) => p.url === '/store/session-math.json');
  assert.ok(up, '钩子要替诊断页把会话推上去');
  assert.deepStrictEqual(up.body.targets, ['cnm_221']);
  assert.ok(CC);
});

t('服务端的会话更新 → 本地换成新的', async () => {
  const CC = env();
  const s = (at, n) => ({ v: 2, mode: 'target', targets: ['cnm_221'], limit: 8, answers: new Array(n).fill(1), seed: 'abc', savedAt: at });
  global.localStorage.setItem('cnmDiagnose.session.v2', JSON.stringify(s('2026-03-01T00:00:00.000Z', 1)));
  net({ '/store/session-math.json': s('2026-03-02T00:00:00.000Z', 5) });
  await CC.sync();
  const got = JSON.parse(global.localStorage.getItem('cnmDiagnose.session.v2'));
  assert.strictEqual(got.answers.length, 5, '要换成答得更多的那份');
});

t('放弃的诊断存档不会被另一台设备带回来', async () => {
  const CC = env();
  global.localStorage.removeItem('cnmDiagnose.session.v2'); // 诊断页的「放弃存档」就是这么写的
  assert.ok(JSON.parse(global.localStorage.getItem('cnmDiagnose.session.v2')).deletedAt, '放弃要留墓碑');
  const stale = { v: 2, mode: 'target', targets: ['cnm_221'], limit: 8, answers: [], seed: 'abc', savedAt: '2026-03-01T00:00:00.000Z' };
  net({ '/store/session-math.json': stale });
  await CC.sync();
  const got = JSON.parse(global.localStorage.getItem('cnmDiagnose.session.v2'));
  assert.ok(got.deletedAt, '墓碑要挡住旧存档');
  assert.strictEqual(got.targets, undefined, '不能把放弃的存档复活');
});

t('已出过的题两边取并集', async () => {
  const CC = env();
  global.localStorage.setItem('cnmDiagnose.seen.v1', JSON.stringify(['q1', 'q2']));
  net({ '/store/seen.json': ['q2', 'q3'] });
  await CC.sync();
  assert.deepStrictEqual(JSON.parse(global.localStorage.getItem('cnmDiagnose.seen.v1')).sort(), ['q1', 'q2', 'q3']);
});

t('拉到新数据刷新一次，且刷新后不再刷（防死循环）', async () => {
  const server = { '/store/children.json': { v: 1, current: 'c1', children: [kid('c1', '小明')] } };
  // 第一次打开：本地空，服务端有 → 应该刷一次
  global.window = { fetch: () => {} };
  global.localStorage = makeStorage();
  global.sessionStorage = makeStorage();
  global.location = { count: 0, reload() { this.count++; } };
  net(server);
  (0, eval)(SRC);
  await sleep(20);
  assert.strictEqual(global.location.count, 1, '要刷新一次让页面显示新数据');

  // 模拟刷新之后再跑一遍：带着标记，不能再刷
  global.window = { fetch: () => {} };
  global.localStorage = makeStorage();
  global.sessionStorage = makeStorage();
  global.sessionStorage.setItem('cnmSync.reloaded', '1');
  global.location = { count: 0, reload() { this.count++; } };
  net(server);
  (0, eval)(SRC);
  await sleep(20);
  assert.strictEqual(global.location.count, 0, '第二次不能再刷，否则无限循环');
});

(async () => {
  let failed = 0;
  for (const [name, fn] of tests) {
    try {
      await fn();
      console.log('  ok   ' + name);
    } catch (e) {
      failed++;
      console.log('  FAIL ' + name + '\n       ' + ((e && e.stack) || e).split('\n').slice(0, 4).join('\n       '));
    }
  }
  console.log('\n' + (tests.length - failed) + ' passed, ' + failed + ' failed');
  process.exit(failed ? 1 : 0);
})();
