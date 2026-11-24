#!/usr/bin/env node
/* 云同步测试：node tests/test_sync.js（无依赖，不碰网络与真实浏览器存储）。
 * 一部分测 assets/sync.js 的纯合并函数，一部分用内存假云端 + 两台「设备」测完整同步流程。 */
'use strict';
const assert = require('assert');
const path = require('path');
const S = require(path.join(__dirname, '../assets/sync.js'));

let passed = 0;
const queue = [];
function test(name, fn) { queue.push({ name, fn }); }

const CTX = { remoteAt: 0, localAt: 0, now: Date.parse('2026-11-22T00:00:00Z') };

function child(id, name, extra) {
  return Object.assign({ id, name, grade: '三年级', textbook: '人教版', createdAt: '2026-10-01T00:00:00.000Z' }, extra || {});
}
function profiles(list, current) { return { v: 1, current: current || (list[0] && list[0].id) || null, children: list }; }
function wrong(qid, ts, extra) {
  return Object.assign({ qid, topicId: 't1', topic: '知识点', subject: 'math', prompt: '题 ' + qid, choices: null, answer: 'A', explanation: '', chosen: 'B', kind: 'wrong', ts, count: 1 }, extra || {});
}
function qids(bucket) { return bucket.map((e) => e.qid).sort(); }

/* ------------------------------------------------------------ 纯合并函数 */

test('错题本：两台设备各加一条错题，合并后两条都在', () => {
  const a = { c1: [wrong('q-a', 1000)] };
  const b = { c1: [wrong('q-b', 2000)] };
  const merged = S.mergeWrongbook(a, b, undefined, CTX);
  assert.deepStrictEqual(qids(merged.c1), ['q-a', 'q-b']);
  assert.deepStrictEqual(qids(S.mergeWrongbook(b, a, undefined, CTX).c1), ['q-a', 'q-b']);
});

test('错题本：同一题两边都有，取 ts 较新的一份', () => {
  const a = { c1: [wrong('q1', 1000, { chosen: 'B', count: 1 })] };
  const b = { c1: [wrong('q1', 3000, { chosen: 'C', count: 2 })] };
  const merged = S.mergeWrongbook(a, b, undefined, CTX);
  assert.strictEqual(merged.c1.length, 1);
  assert.strictEqual(merged.c1[0].chosen, 'C');
  assert.strictEqual(merged.c1[0].count, 2);
  assert.strictEqual(S.mergeWrongbook(b, a, undefined, CTX).c1[0].chosen, 'C');
});

test('错题本：基线里有、本地删了、云端没动 → 删除；云端改过 → 保留云端改动', () => {
  const base = { c1: [wrong('q1', 1000), wrong('q2', 1000)] };
  const local = { c1: [wrong('q2', 1000)] };
  const remoteSame = { c1: [wrong('q1', 1000), wrong('q2', 1000)] };
  assert.deepStrictEqual(qids(S.mergeWrongbook(local, remoteSame, base, CTX).c1), ['q2']);
  const remoteEdited = { c1: [wrong('q1', 5000, { count: 3 }), wrong('q2', 1000)] };
  const kept = S.mergeWrongbook(local, remoteEdited, base, CTX);
  assert.deepStrictEqual(qids(kept.c1), ['q1', 'q2']);
  assert.strictEqual(kept.c1.find((e) => e.qid === 'q1').count, 3);
});

test('错题本：云端删了、本地没动 → 本地也删；没有基线时只做并集', () => {
  const base = { c1: [wrong('q1', 1000), wrong('q2', 1000)] };
  const local = { c1: [wrong('q1', 1000), wrong('q2', 1000)] };
  const remote = { c1: [wrong('q2', 1000)] };
  assert.deepStrictEqual(qids(S.mergeWrongbook(local, remote, base, CTX).c1), ['q2']);
  assert.deepStrictEqual(qids(S.mergeWrongbook(local, remote, undefined, CTX).c1), ['q1', 'q2']);
});

test('错题本：带 deleted 标记的条目优先，且不写进结果', () => {
  const local = { c1: [wrong('q1', 9000)] };
  const remote = { c1: [{ qid: 'q1', deleted: true, ts: 2000 }] };
  assert.deepStrictEqual(S.mergeWrongbook(local, remote, undefined, CTX).c1, []);
});

test('错题本：每桶最多 300 条，丢最旧的；guest 桶照常合并', () => {
  const many = [];
  for (let i = 0; i < 250; i++) many.push(wrong('a' + i, 1000 + i));
  const other = [];
  for (let i = 0; i < 250; i++) other.push(wrong('b' + i, 5000 + i));
  const merged = S.mergeWrongbook({ guest: many }, { guest: other }, undefined, CTX);
  assert.strictEqual(merged.guest.length, 300);
  assert.ok(merged.guest.every((e) => e.ts >= 1000 + 200 || e.qid[0] === 'b'));
  assert.ok(!merged.guest.some((e) => e.qid === 'a0'));
});

test('错题本：两边都没有数据 → null；云端不可用（undefined）不丢本地', () => {
  assert.strictEqual(S.mergeWrongbook(null, null, undefined, CTX), null);
  const local = { c1: [wrong('q1', 1)] };
  assert.deepStrictEqual(S.mergeDataset('wrongbook', local, undefined, { c1: [wrong('q1', 1)] }, CTX), local);
});

test('档案：两台设备各加一个孩子 → 都在，current 保持本地', () => {
  const a = profiles([child('ca', '小满')], 'ca');
  const b = profiles([child('cb', '小禾')], 'cb');
  const merged = S.mergeChildren(a, b, undefined, CTX);
  assert.deepStrictEqual(merged.children.map((c) => c.id), ['ca', 'cb']);
  assert.strictEqual(merged.current, 'ca');
  assert.strictEqual(S.mergeChildren(b, a, undefined, CTX).current, 'cb');
});

test('档案：同一孩子按 updatedAt 取较新的一份（含学习进度）', () => {
  const older = child('c1', '小满', { grade: '三年级', updatedAt: '2026-11-01T00:00:00.000Z' });
  const newer = child('c1', '小满', { grade: '四年级', updatedAt: '2026-11-10T00:00:00.000Z', progress: { v: '上', term: '2026-上' } });
  const m1 = S.mergeChildren(profiles([older]), profiles([newer]), undefined, CTX);
  assert.strictEqual(m1.children[0].grade, '四年级');
  assert.deepStrictEqual(m1.children[0].progress, { v: '上', term: '2026-上' });
  const m2 = S.mergeChildren(profiles([newer]), profiles([older]), undefined, CTX);
  assert.strictEqual(m2.children[0].grade, '四年级');
});

test('档案：本地孩子较新且带 editions、云端同 id 较旧且不带时，合并结果保留 editions（反向亦然）', () => {
  const older = child('c1', '小满', { updatedAt: '2026-11-01T00:00:00.000Z' });
  const newer = child('c1', '小满', { updatedAt: '2026-11-10T00:00:00.000Z', editions: { math: 'hujiao' } });
  const m1 = S.mergeChildren(profiles([newer]), profiles([older]), undefined, CTX);
  assert.deepStrictEqual(m1.children[0].editions, { math: 'hujiao' });
  const m2 = S.mergeChildren(profiles([older]), profiles([newer]), undefined, CTX);
  assert.deepStrictEqual(m2.children[0].editions, { math: 'hujiao' });
});

test('档案：editions 随 cnmChildren.v1 同步；本机版本键 cnmEdition.v1 不在同步数据集里', () => {
  assert.strictEqual(S.DATASETS.children, 'cnmChildren.v1');
  assert.ok(!Object.values(S.DATASETS).includes('cnmEdition.v1'));
});

test('档案：没有时间戳的同一孩子按整表较新的一方；平手取本地', () => {
  const l = child('c1', '小满', { grade: '三年级' });
  const r = child('c1', '小满', { grade: '五年级' });
  delete l.createdAt; delete r.createdAt;
  assert.strictEqual(S.mergeChildren(profiles([l]), profiles([r]), undefined, { remoteAt: 500, localAt: 100 }).children[0].grade, '五年级');
  assert.strictEqual(S.mergeChildren(profiles([l]), profiles([r]), undefined, { remoteAt: 100, localAt: 500 }).children[0].grade, '三年级');
  assert.strictEqual(S.mergeChildren(profiles([l]), profiles([r]), undefined, { remoteAt: 100, localAt: 100 }).children[0].grade, '三年级');
});

test('档案：删除孩子靠基线传播；两台设备加了同名孩子 → 较晚的加「（2）」', () => {
  const base = profiles([child('c1', '小满'), child('c2', '小禾')]);
  const local = profiles([child('c2', '小禾')]);
  const remote = profiles([child('c1', '小满'), child('c2', '小禾')]);
  assert.deepStrictEqual(S.mergeChildren(local, remote, base, CTX).children.map((c) => c.id), ['c2']);

  const a = profiles([child('ca', '小明', { createdAt: '2026-10-01T00:00:00.000Z' })]);
  const b = profiles([child('cb', '小明', { createdAt: '2026-10-05T00:00:00.000Z' })]);
  const merged = S.mergeChildren(a, b, undefined, CTX);
  assert.deepStrictEqual(merged.children.map((c) => c.name), ['小明', '小明（2）']);
  assert.ok(merged.children[1].updatedAt);
});

test('档案：current 指向被删的孩子时回落到第一个', () => {
  const merged = S.mergeChildren(profiles([child('c1', 'A')], 'zzz'), profiles([child('c2', 'B')], 'yyy'), undefined, CTX);
  assert.strictEqual(merged.current, 'c1');
});

test('诊断记录：按记录 key 逐条合并，两台设备的诊断都保留，按 savedAt 倒序', () => {
  const r = (key, saved, extra) => Object.assign({ key, savedAt: saved, updatedAt: saved, label: key }, extra || {});
  const local = { c1: [r('k1', '2026-11-01T00:00:00.000Z')] };
  const remote = { c1: [r('k2', '2026-11-05T00:00:00.000Z'), r('k1', '2026-11-01T00:00:00.000Z', { updatedAt: '2026-11-02T00:00:00.000Z', label: 'k1-new' })], c2: [r('k3', '2026-11-03T00:00:00.000Z')] };
  const merged = S.mergeRecords(local, remote, undefined, CTX);
  assert.deepStrictEqual(merged.c1.map((x) => x.key), ['k2', 'k1']);
  assert.strictEqual(merged.c1[1].label, 'k1-new');
  assert.deepStrictEqual(merged.c2.map((x) => x.key), ['k3']);
});

test('诊断记录：本地删了孩子的记录，云端没动 → 一并删除', () => {
  const rec = { key: 'k1', savedAt: '2026-11-01T00:00:00.000Z' };
  const base = { c1: [rec] };
  const merged = S.mergeRecords({}, { c1: [rec] }, base, CTX);
  assert.deepStrictEqual(merged, {});
});

test('期末计划：取较新的一份；本地没了而云端没动 → 删除；云端清空而本地没动 → 删除', () => {
  const p = (updatedAt, done) => ({ subject: 'math', grade: 5, startDate: '2026-11-20', days: [[], [], [], [], [], [], []], done, createdAt: 1000, updatedAt });
  const l = p(2000, [true, false, false, false, false, false, false]);
  const r = p(3000, [true, true, false, false, false, false, false]);
  assert.strictEqual(S.mergeWhole(l, r, undefined, CTX).done[1], true);
  assert.strictEqual(S.mergeWhole(r, l, undefined, CTX).done[1], true);
  assert.strictEqual(S.mergeWhole(null, r, r, CTX), null);
  assert.deepStrictEqual(S.mergeWhole(null, r, l, CTX), r);
  assert.strictEqual(S.mergeWhole(l, null, l, CTX), null);
  assert.deepStrictEqual(S.mergeWhole(l, undefined, l, CTX), l);
  assert.deepStrictEqual(S.mergeWhole(l, null, undefined, CTX), l);
});

test('合并函数不改动入参', () => {
  const a = { c1: [wrong('q-a', 1000)] };
  const b = { c1: [wrong('q-b', 2000)] };
  const copyA = JSON.parse(JSON.stringify(a)), copyB = JSON.parse(JSON.stringify(b));
  S.mergeWrongbook(a, b, undefined, CTX);
  assert.deepStrictEqual(a, copyA);
  assert.deepStrictEqual(b, copyB);
});

/* ------------------------------------------------------------ 引擎 + 假云端 */

function makeServer() {
  const rows = {}; // dataset -> { payload, updated_at }
  let clock = 1000;
  const server = {
    rows, calls: [], tokens: { good: true },
    handle(token, method, url, body) {
      server.calls.push(method + ' ' + url);
      if (!server.tokens[token]) return { status: 401, data: { error: 'unauthorized' } };
      if (method === 'GET' && url === '/sync') return { status: 200, data: { datasets: JSON.parse(JSON.stringify(rows)) } };
      const m = /^\/sync\/(\w+)$/.exec(url);
      if (method === 'PUT' && m) {
        const cur = rows[m[1]];
        const base = body.base_updated_at;
        if ((cur ? cur.updated_at : null) !== (base == null ? null : base)) {
          return { status: 409, data: { error: 'conflict', payload: cur ? cur.payload : null, updated_at: cur ? cur.updated_at : null } };
        }
        clock += 10;
        rows[m[1]] = { payload: body.payload, updated_at: clock };
        return { status: 200, data: { ok: true, updated_at: clock } };
      }
      return { status: 404, data: null };
    }
  };
  return server;
}

function makeDevice(server, initial, opts) {
  const o = opts || {};
  const store = new Map(Object.entries(initial || {}).map(([k, v]) => [k, JSON.stringify(v)]));
  const storage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => { store.set(k, String(v)); },
    removeItem: (k) => { store.delete(k); }
  };
  const timers = [];
  const events = [];
  let unauthorized = 0;
  let t = 5000;
  const engine = S.createEngine({
    storage,
    api: async (method, url, body) => server.handle(o.token || 'good', method, url, body && JSON.parse(JSON.stringify(body))),
    now: () => (t += 1),
    setTimer: (fn, ms) => { const h = { fn, ms, off: false }; timers.push(h); return h; },
    clearTimer: (h) => { h.off = true; },
    emit: (s) => events.push(s.state),
    onUnauthorized: () => { unauthorized++; },
    confirmSwitch: o.confirmSwitch
  });
  return {
    engine, store, timers, events, get unauthorized() { return unauthorized; },
    read: (k) => (store.has(k) ? JSON.parse(store.get(k)) : null),
    write: (k, v) => { storage.setItem(k, JSON.stringify(v)); },
    fire() { const live = timers.filter((x) => !x.off); live.forEach((x) => { x.off = true; }); return Promise.all(live.map((x) => x.fn())); }
  };
}

const WRONG = 'cnmWrong.v1';
const CHILDREN = 'cnmChildren.v1';
const FINALS = 'cnmFinals.v1';

function cloudWrong(server) {
  return JSON.parse(server.rows.wrongbook.payload).data;
}

test('引擎：未登录（没调用 begin）时完全静默，不请求网络、不起定时器', async () => {
  const server = makeServer();
  const d = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  d.engine.notifyLocalChange();
  await d.engine.syncAll();
  await d.engine.pushChanged();
  assert.deepStrictEqual(server.calls, []);
  assert.strictEqual(d.timers.length, 0);
  assert.deepStrictEqual(d.events, []);
});

test('引擎：两台设备各加一条错题 → 登录同步后两边都有两条', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q-a', 1000)] } });
  const B = makeDevice(server, { [WRONG]: { c1: [wrong('q-b', 2000)] } });
  assert.ok(A.engine.begin('mom@example.com'));
  await A.engine.syncAll();
  assert.ok(B.engine.begin('mom@example.com'));
  await B.engine.syncAll();
  assert.deepStrictEqual(qids(B.read(WRONG).c1), ['q-a', 'q-b']);
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q-a', 'q-b']);
  await A.engine.syncAll();
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q-a', 'q-b']);
  assert.ok(A.events.includes('applied'));
});

test('引擎：登录后本地改动防抖 5 秒自动上传，连改只传一次', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  A.engine.begin('mom@example.com');
  await A.engine.syncAll();
  const puts = () => server.calls.filter((c) => c.startsWith('PUT')).length;
  const before = puts();
  A.write(WRONG, { c1: [wrong('q1', 1), wrong('q2', 2)] });
  A.engine.notifyLocalChange();
  A.write(WRONG, { c1: [wrong('q1', 1), wrong('q2', 2), wrong('q3', 3)] });
  A.engine.notifyLocalChange();
  const live = A.timers.filter((x) => !x.off);
  assert.strictEqual(live.length, 1);
  assert.strictEqual(live[0].ms, 5000);
  await A.fire();
  assert.strictEqual(puts(), before + 1);
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q1', 'q2', 'q3']);
});

test('引擎：PUT 遇 409 → 重新拉取合并后再 PUT，不丢另一台设备的改动', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q0', 1)] } });
  const B = makeDevice(server, {});
  A.engine.begin('mom@example.com'); B.engine.begin('mom@example.com');
  await A.engine.syncAll();
  await B.engine.syncAll();
  B.write(WRONG, { c1: [wrong('q0', 1), wrong('q-b', 2000)] });
  await B.engine.pushChanged();
  A.write(WRONG, { c1: [wrong('q0', 1), wrong('q-a', 3000)] });
  const before = server.calls.length;
  await A.engine.pushChanged();
  const sent = server.calls.slice(before);
  assert.strictEqual(sent.filter((c) => c.startsWith('PUT')).length, 2, sent.join(' | '));
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q-a', 'q-b', 'q0']);
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q-a', 'q-b', 'q0']);
});

test('引擎：一台设备删了错题，同步后另一台也删，不会「复活」', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1), wrong('q2', 2)] } });
  const B = makeDevice(server, {});
  A.engine.begin('mom@example.com'); B.engine.begin('mom@example.com');
  await A.engine.syncAll();
  await B.engine.syncAll();
  assert.deepStrictEqual(qids(B.read(WRONG).c1), ['q1', 'q2']);
  A.write(WRONG, { c1: [wrong('q2', 2)] });
  await A.engine.pushChanged();
  await B.engine.syncAll();
  assert.deepStrictEqual(qids(B.read(WRONG).c1), ['q2']);
  await A.engine.syncAll();
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q2']);
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q2']);
});

test('引擎：云端被清空（没有这一行）时不会把本地数据当成「已删除」', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  A.engine.begin('mom@example.com');
  await A.engine.syncAll();
  for (const k of Object.keys(server.rows)) delete server.rows[k];
  await A.engine.syncAll();
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q1']);
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q1']);
});

test('引擎：档案与期末计划一起同步；新设备拉到云端数据', async () => {
  const server = makeServer();
  const plan = { subject: 'math', grade: 5, startDate: '2026-11-20', days: [[], [], [], [], [], [], []], done: [false, false, false, false, false, false, false], createdAt: 1000, updatedAt: 1000 };
  const A = makeDevice(server, { [CHILDREN]: profiles([child('c1', '小满')]), [FINALS]: plan });
  const B = makeDevice(server, {});
  A.engine.begin('mom@example.com'); B.engine.begin('mom@example.com');
  await A.engine.syncAll();
  await B.engine.syncAll();
  assert.deepStrictEqual(B.read(CHILDREN).children.map((c) => c.name), ['小满']);
  assert.deepStrictEqual(B.read(FINALS), plan);
  assert.ok(B.events.includes('applied'));
  assert.strictEqual(B.read('cnmWrong.v1'), null);
});

test('引擎：本地没有变化时不上传；同步后再同步是空操作', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  A.engine.begin('mom@example.com');
  await A.engine.syncAll();
  const before = server.calls.length;
  await A.engine.pushChanged();
  assert.strictEqual(server.calls.length, before);
  await A.engine.syncAll();
  assert.strictEqual(server.calls.slice(before).filter((c) => c.startsWith('PUT')).length, 0);
});

test('引擎：会话失效（401）→ 停止同步并通知调用方，本地数据不动', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } }, { token: 'stale' });
  A.engine.begin('mom@example.com');
  await A.engine.syncAll();
  assert.strictEqual(A.unauthorized, 1);
  assert.ok(A.events.includes('signedout'));
  assert.strictEqual(A.engine.isActive(), false);
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q1']);
});

test('引擎：网络出错只报 error，不抛、不改本地；之后可以重试', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  const realHandle = server.handle;
  let down = true;
  const store = A.store;
  const flaky = S.createEngine({
    storage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) },
    api: async (m, u, b) => { if (down) throw new Error('offline'); return realHandle.call(server, 'good', m, u, b); },
    emit: (s) => A.events.push(s.state)
  });
  flaky.begin('mom@example.com');
  const r = await flaky.syncAll();
  assert.ok(r.error);
  assert.ok(A.events.includes('error'));
  assert.deepStrictEqual(qids(A.read(WRONG).c1), ['q1']);
  down = false;
  await flaky.syncAll();
  assert.deepStrictEqual(qids(cloudWrong(server).c1), ['q1']);
});

test('引擎：这台设备同步过另一个账号 → 要确认才合并，拒绝则不开始', async () => {
  const server = makeServer();
  let asked = null;
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } }, { confirmSwitch: (o, n) => { asked = [o, n]; return false; } });
  assert.ok(A.engine.begin('mom@example.com'));
  await A.engine.syncAll();
  A.engine.stop();
  assert.strictEqual(A.engine.begin('dad@example.com'), false);
  assert.deepStrictEqual(asked, ['mom@example.com', 'dad@example.com']);
  assert.strictEqual(A.engine.isActive(), false);

  const B = makeDevice(server, {}, { confirmSwitch: () => true });
  B.engine.begin('mom@example.com');
  B.engine.stop();
  assert.ok(B.engine.begin('dad@example.com'));
});

test('引擎：stop() 之后不再上传，未触发的定时器被取消', async () => {
  const server = makeServer();
  const A = makeDevice(server, { [WRONG]: { c1: [wrong('q1', 1)] } });
  A.engine.begin('mom@example.com');
  await A.engine.syncAll();
  A.engine.notifyLocalChange();
  A.engine.stop();
  assert.ok(A.timers.every((x) => x.off));
  const before = server.calls.length;
  await A.engine.pushChanged();
  assert.strictEqual(server.calls.length, before);
});

(async () => {
  for (const { name, fn } of queue) {
    await fn();
    passed++;
    console.log('  ok   ' + name);
  }
  console.log('\n' + passed + ' passed');
})().catch((e) => { console.error(e); process.exit(1); });
