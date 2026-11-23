#!/usr/bin/env node
/* 每周学习周报测试：node tests/test_digest.js（无依赖、不联网）。
 * api/lib.js / api/digest.js 的纯逻辑直接测；Worker 路由与整批发送用 node:sqlite 内存库套一层 D1 外壳，
 * 跑真实的 schema.sql（同 tests/test_api.js 的桩法），sendMail 用桩。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { pathToFileURL } = require('url');

const ROOT = path.join(__dirname, '..');
const API = path.join(ROOT, 'api');
const load = (f) => import(pathToFileURL(path.join(API, f)).href);

let passed = 0;
const queue = [];
function test(name, fn) { queue.push({ name, fn }); }

const DAY = 24 * 60 * 60 * 1000;
const MON = Date.parse('2026-11-23T00:00:00Z');

/* ------------------------------------------------------------ 纯逻辑 */

test('INTERVALS_DAYS 与前端 assets/wrongbook.js 同值；computeDue 与前端 isDue 同规则', async () => {
  const L = await load('lib.js');
  const store = new Map();
  const ctx = { window: {}, localStorage: { getItem: (k) => store.get(k) || null, setItem: (k, v) => store.set(k, v), removeItem: (k) => store.delete(k) } };
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'assets/wrongbook.js'), 'utf8'), ctx);
  const CW = ctx.window.CnmWrong;
  assert.deepStrictEqual(Array.from(L.INTERVALS_DAYS), Array.from(CW.INTERVALS_DAYS));
  assert.deepStrictEqual(Array.from(L.INTERVALS_DAYS), [1, 3, 7, 15]);
  const cases = [
    { ts: MON - DAY },
    { ts: MON - DAY + 1 },
    { ts: MON },
    { ts: MON - 30 * DAY },
    { ts: MON - 30 * DAY, done: true },
    { ts: MON - 30 * DAY, stage: 2, dueAt: MON + DAY },
    { ts: MON - 30 * DAY, stage: 2, dueAt: MON },
    { ts: MON - 30 * DAY, stage: 3, dueAt: MON - 1 },
    { ts: MON - 30 * DAY, stage: 3, done: true },
    { ts: MON - 30 * DAY, dueAt: 0 },
    {}
  ];
  cases.forEach((e, i) => {
    assert.strictEqual(L.computeDue(e, MON), CW.isDue(e, MON), 'case ' + i + ' ' + JSON.stringify(e));
  });
  assert.strictEqual(L.computeDue(null, MON), false);
});

test('computeDue：老条目按 ts + 1 天，新字段按 dueAt，done 不到期', async () => {
  const { computeDue } = await load('lib.js');
  assert.strictEqual(computeDue({ ts: MON - DAY }, MON), true);
  assert.strictEqual(computeDue({ ts: MON - DAY + 1000 }, MON), false);
  assert.strictEqual(computeDue({ ts: MON - 9 * DAY, stage: 1, dueAt: MON + 1 }, MON), false);
  assert.strictEqual(computeDue({ ts: MON - 9 * DAY, stage: 1, dueAt: MON }, MON), true);
  assert.strictEqual(computeDue({ ts: MON - 9 * DAY, done: true }, MON), false);
});

test('week_key：ISO 周，按 Asia/Shanghai 的日历日算', async () => {
  const { isoWeekKey } = await load('lib.js');
  assert.strictEqual(isoWeekKey(Date.parse('2026-11-23T00:00:00Z')), '2026-W48');
  assert.strictEqual(isoWeekKey(Date.parse('2026-11-29T15:59:59Z')), '2026-W48', '周日 23:59 北京仍是 W48');
  assert.strictEqual(isoWeekKey(Date.parse('2026-11-29T16:00:00Z')), '2026-W49', '周一 00:00 北京进入 W49');
  assert.strictEqual(isoWeekKey(Date.parse('2026-11-22T16:30:00Z')), '2026-W48', 'UTC 还是周日，北京已是周一');
  assert.strictEqual(isoWeekKey(Date.parse('2026-01-01T00:00:00Z')), '2026-W01');
  assert.strictEqual(isoWeekKey(Date.parse('2025-12-29T00:00:00Z')), '2026-W01', '跨年：2025-12-29 属于 2026-W01');
  assert.strictEqual(isoWeekKey(Date.parse('2027-01-03T00:00:00Z')), '2026-W53', '2026 有 53 周');
  assert.strictEqual(isoWeekKey(Date.parse('2027-01-04T00:00:00Z')), '2027-W01');
  assert.strictEqual(isoWeekKey(Date.parse('2024-12-30T00:00:00Z')), '2025-W01');
  assert.strictEqual(isoWeekKey(Date.parse('2021-01-03T00:00:00Z')), '2020-W53');
});

test('邮箱打码与退订 token', async () => {
  const L = await load('lib.js');
  assert.strictEqual(L.maskEmail('abc@qq.com'), 'a***@qq.com');
  assert.strictEqual(L.maskEmail('x@y.com'), 'x***@y.com');
  assert.strictEqual(L.maskEmail('weird'), '***');
  const t = L.generateDigestToken();
  assert.match(t, /^[0-9a-f]{32}$/);
  assert.notStrictEqual(t, L.generateDigestToken());
  assert.ok(L.isDigestToken(t));
  ['', 'abc', 'G'.repeat(32), t.toUpperCase(), t + '0', null].forEach((bad) => assert.ok(!L.isDigestToken(bad), String(bad)));
});

function wrong(qid, ts, extra) { return Object.assign({ qid, ts, count: 1, kind: 'wrong' }, extra || {}); }
function profile(name) { return { v: 1, current: 'c1', children: [{ id: 'c1', name }] }; }

test('summarizeUser：本周新增 / 待复测（含老条目）/ 已毕业 / 本周诊断 / 期末计划', async () => {
  const { summarizeUser } = await load('digest.js');
  const datasets = {
    children: profile('小明'),
    wrongbook: {
      c1: [
        wrong('new-legacy', MON - DAY),
        wrong('old-legacy', MON - 20 * DAY),
        wrong('later', MON - 2 * DAY, { stage: 1, dueAt: MON + 2 * DAY }),
        wrong('grad', MON - 40 * DAY, { stage: 3, done: true }),
        wrong('due-newfield', MON - 30 * DAY, { stage: 2, dueAt: MON - 1000 })
      ],
      guest: [wrong('g1', MON - 3 * DAY)]
    },
    records: { c1: [{ key: 'a', savedAt: new Date(MON - 2 * DAY).toISOString() }, { key: 'b', savedAt: new Date(MON - 8 * DAY).toISOString() }] },
    finals: { subject: 'math', startDate: '2026-11-22', days: [[], [], [], [], [], [], []], done: [] }
  };
  const s = summarizeUser(datasets, MON);
  assert.strictEqual(s.name, '小明');
  assert.strictEqual(s.newWrong, 3, 'new-legacy、later、g1（ts 在近 7 天内）');
  assert.strictEqual(s.due, 4, 'new-legacy、old-legacy、due-newfield、g1');
  assert.strictEqual(s.graduated, 1);
  assert.strictEqual(s.diagnoses, 1);
  assert.deepStrictEqual(s.finals, { endMonth: 11, endDay: 28 });
  assert.strictEqual(s.hasContent, true);
});

test('summarizeUser：没有孩子不带名字；四项全 0 且无计划没内容；过期计划不算进行中；坏数据不抛错', async () => {
  const { summarizeUser, digestSubject } = await load('digest.js');
  assert.strictEqual(summarizeUser({}, MON).hasContent, false);
  assert.strictEqual(summarizeUser({ children: { children: [] } }, MON).name, '');
  const expired = { subject: 'math', startDate: '2026-11-10', days: [[], [], [], [], [], [], []], done: [] };
  assert.strictEqual(summarizeUser({ finals: expired }, MON).finals, null);
  assert.strictEqual(summarizeUser({ finals: expired }, MON).hasContent, false);
  const junk = summarizeUser({ children: 5, wrongbook: { c1: 'x', c2: [null, 3, { qid: '' }] }, records: [], finals: { startDate: 'x' } }, MON);
  assert.strictEqual(junk.hasContent, false);
  const named = { name: '小明', due: 3 };
  assert.strictEqual(digestSubject(named), '知识图谱周报：小明有 3 道错题待复测');
  assert.strictEqual(digestSubject({ name: '', due: 3 }), '知识图谱周报：有 3 道错题待复测');
  assert.strictEqual(digestSubject({ name: '小明', due: 0 }), '知识图谱周报：本周学习小结');
});

test('renderDigest：正文双份、数字齐全、按钮与退订链接、转义、不提付费', async () => {
  const { renderDigest } = await load('digest.js');
  const url = 'https://api.math.pansgo.com/digest/unsub?t=' + 'a'.repeat(32);
  const r = renderDigest({ name: '<b>小明</b>', newWrong: 3, due: 4, graduated: 1, diagnoses: 2, finals: { endMonth: 11, endDay: 28 } }, url);
  ['本周新增错题：3 道', '现在待复测：4 道', '已毕业的错题：1 道', '本周诊断：2 次', '期末计划进行中', '11 月 28 日',
    'https://math.pansgo.com/wrongbook/', url, '这是您注册时同意接收的服务邮件'].forEach((s) => assert.ok(r.text.includes(s), 'text 缺 ' + s));
  assert.ok(r.html.includes('href="https://math.pansgo.com/wrongbook/"'));
  assert.ok(r.html.includes('href="' + url + '"'));
  assert.ok(r.html.includes('这是您注册时同意接收的服务邮件'));
  assert.ok(!r.html.includes('<b>小明</b>'), '孩子昵称必须转义');
  assert.ok(r.html.includes('&lt;b&gt;'));
  assert.ok(!/付费|会员|优惠|折扣|购买|VIP|¥|￥/.test(r.text + r.html));
  const plain = renderDigest({ name: '', newWrong: 0, due: 0, graduated: 0, diagnoses: 1, finals: null }, url);
  assert.ok(!plain.text.includes('期末计划'));
  assert.ok(plain.text.startsWith('您好，这是这一周'));
});

test('mailer：extra 的 html / headers 会随 Resend 请求发出，三参数调用不变', async () => {
  const { createMailer } = await load('mail.js');
  let seen;
  const send = createMailer({ RESEND_API_KEY: 'k' }, async (u, init) => { seen = JSON.parse(init.body); return { ok: true }; });
  await send('a@b.com', 's', 't');
  assert.ok(!('html' in seen) && !('headers' in seen));
  await send('a@b.com', 's', 't', { html: '<p>x</p>', headers: { 'List-Unsubscribe': '<u>' } });
  assert.strictEqual(seen.html, '<p>x</p>');
  assert.deepStrictEqual(seen.headers, { 'List-Unsubscribe': '<u>' });
});

/* ------------------------------------------------------------ Worker + 内存 SQLite */

let sqlite = null;
try { sqlite = require('node:sqlite'); } catch (e) { /* Node 太老：跳过集成测试 */ }

function wrapD1(db) {
  return {
    db,
    prepare(sql) {
      const st = db.prepare(sql);
      return {
        bind(...args) {
          return {
            async first() { const r = st.get(...args); return r === undefined ? null : Object.assign({}, r); },
            async all() { return { results: st.all(...args).map((r) => Object.assign({}, r)) }; },
            async run() { const r = st.run(...args); return { meta: { changes: Number(r.changes), last_row_id: Number(r.lastInsertRowid) } }; }
          };
        }
      };
    }
  };
}

function makeD1() {
  const db = new sqlite.DatabaseSync(':memory:');
  db.exec(fs.readFileSync(path.join(API, 'schema.sql'), 'utf8'));
  return wrapD1(db);
}

let nextUser = 1;
function addUser(d1, email, flags, data) {
  const f = Object.assign({ mail: 1, mkt: 0, optOut: 0 }, flags || {});
  const id = nextUser++;
  d1.db.prepare('INSERT INTO users (id, email, created_at, mail_consent, mkt_consent, digest_opt_out) VALUES (?, ?, ?, ?, ?, ?)')
    .run(id, email, MON - 90 * DAY, f.mail, f.mkt, f.optOut);
  Object.keys(data || {}).forEach((name) => {
    d1.db.prepare('INSERT INTO sync_data (user_id, dataset, payload, updated_at) VALUES (?, ?, ?, ?)')
      .run(id, name, JSON.stringify({ v: 1, at: MON - DAY, data: data[name] }), MON - DAY);
  });
  return id;
}

const RICH = () => ({
  children: profile('小明'),
  wrongbook: { c1: [wrong('q1', MON - DAY), wrong('q2', MON - 20 * DAY), wrong('q3', MON - 40 * DAY, { stage: 3, done: true })] },
  records: { c1: [{ key: 'k', savedAt: new Date(MON - 2 * DAY).toISOString() }] }
});
const EMPTY_DONE_ONLY = () => ({ wrongbook: { c1: [wrong('old', MON - 60 * DAY, { stage: 3, done: true })] } });

async function makeWorld(envExtra) {
  const { createHandler, runScheduled } = await load('worker.js');
  const { sendWeeklyDigests } = await load('digest.js');
  nextUser = 1;
  const d1 = makeD1();
  const world = { now: MON, mails: [], d1, failFor: new Set(), mailDryRun: false };
  const env = Object.assign({ DB: d1, MAIL_DRY_RUN: '0', DIGEST_DRY_RUN: '0', ALLOWED_ORIGINS: 'https://math.pansgo.com' }, envExtra || {});
  world.env = env;
  world.sendMail = async (to, subject, text, extra) => {
    if (world.failFor.has(to)) throw new Error('mail_failed_500');
    world.mails.push({ to, subject, text, extra });
    return { dryRun: world.mailDryRun };
  };
  const handler = createHandler({ now: () => world.now, sendMail: world.sendMail });
  world.call = async (method, route, opts) => {
    const o = opts || {};
    const headers = {};
    if (o.key !== undefined) headers['X-Admin-Key'] = o.key;
    if (o.token) headers.Authorization = 'Bearer ' + o.token;
    const res = await handler(new Request('https://api.test' + route, { method, headers }), env);
    const text = await res.text();
    let data = null;
    try { data = JSON.parse(text); } catch (e) { /* html */ }
    return { status: res.status, data, text, headers: res.headers };
  };
  world.run = (opts) => sendWeeklyDigests(env, Object.assign({ now: world.now, sendMail: world.sendMail }, opts || {}));
  world.cron = () => runScheduled(env, world.sendMail, world.now);
  world.logRows = () => d1.db.prepare('SELECT user_id, week_key FROM digest_log ORDER BY user_id, week_key').all().map((r) => Object.assign({}, r));
  return world;
}

function worldTest(name, fn, envExtra) {
  test(name, async () => {
    if (!sqlite) { console.log('  skip ' + name + '（需要 node:sqlite，Node ≥ 22.13）'); passed--; return; }
    await fn(await makeWorld(envExtra));
  });
}

worldTest('收件人过滤：mail_consent=1 且未退订才发；营销同意与否无关', async (w) => {
  addUser(w.d1, 'yes@qq.com', {}, RICH());
  addUser(w.d1, 'no-consent@qq.com', { mail: 0 }, RICH());
  addUser(w.d1, 'opted-out@qq.com', { optOut: 1 }, RICH());
  addUser(w.d1, 'mkt-only@qq.com', { mail: 1, mkt: 1 }, RICH());
  const r = await w.run();
  assert.strictEqual(r.candidates, 2);
  assert.strictEqual(r.sent, 2);
  assert.deepStrictEqual(w.mails.map((m) => m.to).sort(), ['mkt-only@qq.com', 'yes@qq.com']);
});

worldTest('没内容不发：没有同步数据、四项全 0 且无计划都跳过', async (w) => {
  addUser(w.d1, 'nodata@qq.com');
  addUser(w.d1, 'zero@qq.com', {}, { children: profile('小红'), wrongbook: {}, records: {} });
  addUser(w.d1, 'gradonly@qq.com', {}, EMPTY_DONE_ONLY());
  const r = await w.run();
  assert.strictEqual(r.candidates, 3);
  assert.strictEqual(r.skipped.no_content, 2, '只有已毕业总数 > 0 的那位有内容');
  assert.strictEqual(r.sent, 1);
  assert.strictEqual(w.mails[0].to, 'gradonly@qq.com');
  assert.ok(w.mails[0].text.includes('已毕业的错题：1 道'));
});

worldTest('只有期末计划也发；邮件主题、正文数字、退订头', async (w) => {
  addUser(w.d1, 'finals@qq.com', {}, { finals: { subject: 'math', startDate: '2026-11-22', days: [[], [], [], [], [], [], []], done: [] } });
  const r = await w.run();
  assert.strictEqual(r.sent, 1);
  assert.strictEqual(w.mails[0].subject, '知识图谱周报：本周学习小结');
  assert.ok(w.mails[0].text.includes('期末计划进行中'));
  assert.ok(w.mails[0].text.includes('11 月 28 日'));
});

worldTest('待复测数含老条目规则；主题带孩子名与待复测数；正文与退订链接', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  const r = await w.run();
  assert.strictEqual(r.sent, 1);
  const m = w.mails[0];
  assert.strictEqual(m.subject, '知识图谱周报：小明有 2 道错题待复测', 'q1（ts+1天=今天）与 q2 都到期，q3 已毕业');
  ['本周新增错题：1 道', '现在待复测：2 道', '已毕业的错题：1 道', '本周诊断：1 次', 'https://math.pansgo.com/wrongbook/'].forEach((s) => assert.ok(m.text.includes(s), s));
  assert.ok(m.extra.html.includes('小明'));
  const token = w.d1.db.prepare('SELECT digest_token FROM users WHERE email = ?').get('p@qq.com').digest_token;
  assert.match(token, /^[0-9a-f]{32}$/);
  assert.ok(m.text.includes('https://api.math.pansgo.com/digest/unsub?t=' + token));
  assert.strictEqual(m.extra.headers['List-Unsubscribe'], '<https://api.math.pansgo.com/digest/unsub?t=' + token + '>');
  assert.deepStrictEqual(r.items[0], { to: 'p***@qq.com', new_wrong: 1, due: 2, graduated: 1, diagnoses: 1, finals: false, status: 'sent' });
});

worldTest('digest_token 已有就沿用，不重新生成', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  w.d1.db.prepare('UPDATE users SET digest_token = ? WHERE email = ?').run('f'.repeat(32), 'p@qq.com');
  await w.run();
  assert.ok(w.mails[0].text.includes('t=' + 'f'.repeat(32)));
});

worldTest('同一周第二次运行发送数为 0；下一周可以再发', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  const first = await w.run();
  assert.strictEqual(first.sent, 1);
  assert.deepStrictEqual(w.logRows(), [{ user_id: 1, week_key: '2026-W48' }]);
  const second = await w.run();
  assert.strictEqual(second.sent, 0);
  assert.strictEqual(second.will_send, 0);
  assert.strictEqual(second.skipped.already_sent, 1);
  assert.strictEqual(w.mails.length, 1);
  w.now = MON + 7 * DAY;
  const next = await w.run();
  assert.strictEqual(next.sent, 1);
  assert.strictEqual(w.mails.length, 2);
  assert.deepStrictEqual(w.logRows().map((r) => r.week_key), ['2026-W48', '2026-W49']);
});

worldTest('退订：点链接置 digest_opt_out，之后不再发；重复点仍成功；坏 token 404', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  addUser(w.d1, 'q@qq.com', {}, RICH());
  await w.run();
  const token = w.d1.db.prepare('SELECT digest_token FROM users WHERE email = ?').get('p@qq.com').digest_token;
  const res = await w.call('GET', '/digest/unsub?t=' + token);
  assert.strictEqual(res.status, 200);
  assert.ok(/text\/html/.test(res.headers.get('Content-Type')));
  assert.ok(res.text.includes('已退订'));
  assert.strictEqual(w.d1.db.prepare('SELECT digest_opt_out AS o FROM users WHERE email = ?').get('p@qq.com').o, 1);
  assert.strictEqual(w.d1.db.prepare('SELECT digest_opt_out AS o FROM users WHERE email = ?').get('q@qq.com').o, 0, '只退订自己');
  assert.strictEqual((await w.call('GET', '/digest/unsub?t=' + token)).status, 200);
  w.now = MON + 7 * DAY;
  const next = await w.run();
  assert.deepStrictEqual(w.mails.slice(2).map((m) => m.to), ['q@qq.com']);
  assert.strictEqual(next.candidates, 1);
  assert.strictEqual((await w.call('GET', '/digest/unsub?t=' + 'e'.repeat(32))).status, 404);
  assert.strictEqual((await w.call('GET', '/digest/unsub?t=nope')).status, 404);
  assert.strictEqual((await w.call('GET', '/digest/unsub')).status, 404);
});

worldTest('退订 token 只管退订：不能当会话令牌用', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  await w.run();
  const token = w.d1.db.prepare('SELECT digest_token FROM users WHERE email = ?').get('p@qq.com').digest_token;
  assert.strictEqual((await w.call('GET', '/auth/me', { token })).status, 401);
  assert.strictEqual((await w.call('GET', '/sync', { token })).status, 401);
});

worldTest('单个用户发送失败不中断整批，失败的不写日志，下次还能补发', async (w) => {
  addUser(w.d1, 'a@qq.com', {}, RICH());
  addUser(w.d1, 'bad@qq.com', {}, RICH());
  addUser(w.d1, 'c@qq.com', {}, RICH());
  w.failFor.add('bad@qq.com');
  const errors = [];
  const orig = console.error;
  console.error = (m) => errors.push(String(m));
  let r;
  try { r = await w.run(); } finally { console.error = orig; }
  assert.strictEqual(r.sent, 2);
  assert.strictEqual(r.failed, 1);
  assert.deepStrictEqual(w.mails.map((m) => m.to), ['a@qq.com', 'c@qq.com']);
  assert.deepStrictEqual(w.logRows().map((x) => x.user_id), [1, 3]);
  assert.ok(errors.some((e) => e.includes('user 2')), errors.join('|'));
  assert.strictEqual(r.items.find((i) => i.to === 'b***@qq.com').status, 'failed');
  w.failFor.clear();
  const again = await w.run();
  assert.strictEqual(again.sent, 1);
  assert.strictEqual(w.mails[w.mails.length - 1].to, 'bad@qq.com');
});

worldTest('MAIL_DRY_RUN 下邮件没真发，不写 digest_log', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  w.mailDryRun = true;
  const r = await w.run();
  assert.strictEqual(r.sent, 0);
  assert.strictEqual(r.items[0].status, 'mail_dry_run');
  assert.deepStrictEqual(w.logRows(), []);
});

worldTest('dry-run：只算不发，不写 digest_log，不生成 token；DIGEST_DRY_RUN 非 "0" 一律 dry-run', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  const r = await w.run({ dryRun: true });
  assert.strictEqual(r.dry_run, true);
  assert.strictEqual(r.will_send, 1);
  assert.strictEqual(r.sent, 0);
  assert.strictEqual(w.mails.length, 0);
  assert.deepStrictEqual(w.logRows(), []);
  assert.strictEqual(w.d1.db.prepare('SELECT digest_token AS t FROM users').get().t, null);
  assert.strictEqual(r.items[0].status, 'dry_run');
  for (const v of ['1', undefined, '', 'true']) {
    w.env.DIGEST_DRY_RUN = v;
    const viaEnv = await w.run({ dryRun: undefined });
    assert.strictEqual(viaEnv.dry_run, true, String(v));
    const viaCron = await w.cron();
    assert.strictEqual(viaCron.dry_run, true, 'cron ' + String(v));
  }
  assert.strictEqual(w.mails.length, 0);
  w.env.DIGEST_DRY_RUN = '0';
  assert.strictEqual((await w.cron()).sent, 1, 'DIGEST_DRY_RUN=0 时 cron 真发');
});

worldTest('管理端点：ADMIN_KEY 未设一律 404；密钥错 401；GET 405', async (w) => {
  addUser(w.d1, 'p@qq.com', {}, RICH());
  assert.strictEqual((await w.call('POST', '/admin/digest/run', { key: 'x' })).status, 404);
  assert.strictEqual((await w.call('GET', '/admin/digest/run')).status, 404);
  w.env.ADMIN_KEY = 'secret-key';
  assert.strictEqual((await w.call('POST', '/admin/digest/run')).status, 401);
  assert.strictEqual((await w.call('POST', '/admin/digest/run', { key: 'wrong' })).status, 401);
  assert.strictEqual((await w.call('GET', '/admin/digest/run', { key: 'secret-key' })).status, 405);
  assert.strictEqual(w.mails.length, 0);
});

worldTest('管理端点 ?dry=1：强制 dry-run，返回汇总、打码邮箱与关键计数，不发不写日志', async (w) => {
  addUser(w.d1, 'alice@qq.com', {}, RICH());
  addUser(w.d1, 'nodata@163.com');
  w.env.ADMIN_KEY = 'secret-key';
  w.env.DIGEST_DRY_RUN = '0';
  const res = await w.call('POST', '/admin/digest/run?dry=1', { key: 'secret-key' });
  assert.strictEqual(res.status, 200);
  const d = res.data;
  assert.strictEqual(d.dry_run, true);
  assert.strictEqual(d.week_key, '2026-W48');
  assert.strictEqual(d.candidates, 2);
  assert.strictEqual(d.will_send, 1);
  assert.strictEqual(d.sent, 0);
  assert.deepStrictEqual(d.skipped, { already_sent: 0, no_content: 1 });
  assert.deepStrictEqual(d.items, [{ to: 'a***@qq.com', new_wrong: 1, due: 2, graduated: 1, diagnoses: 1, finals: false, status: 'dry_run' }]);
  assert.ok(!JSON.stringify(d).includes('alice'), '汇总里不能出现完整邮箱');
  assert.strictEqual(w.mails.length, 0);
  assert.deepStrictEqual(w.logRows(), []);
});

worldTest('管理端点不带 dry：DIGEST_DRY_RUN=1 时仍是 dry-run；=0 时真发并写日志', async (w) => {
  addUser(w.d1, 'alice@qq.com', {}, RICH());
  w.env.ADMIN_KEY = 'secret-key';
  w.env.DIGEST_DRY_RUN = '1';
  assert.strictEqual((await w.call('POST', '/admin/digest/run', { key: 'secret-key' })).data.dry_run, true);
  assert.strictEqual(w.mails.length, 0);
  w.env.DIGEST_DRY_RUN = '0';
  const live = await w.call('POST', '/admin/digest/run', { key: 'secret-key' });
  assert.strictEqual(live.data.dry_run, false);
  assert.strictEqual(live.data.sent, 1);
  assert.strictEqual(w.mails.length, 1);
  assert.strictEqual(w.logRows().length, 1);
  const again = await w.call('POST', '/admin/digest/run', { key: 'secret-key' });
  assert.strictEqual(again.data.sent, 0);
  assert.strictEqual(again.data.skipped.already_sent, 1);
});

worldTest('超过一页（50 人）的候选人也能发完；坏载荷当没数据', async (w) => {
  for (let i = 0; i < 120; i++) addUser(w.d1, 'u' + i + '@qq.com', {}, RICH());
  const bad = addUser(w.d1, 'bad-json@qq.com');
  w.d1.db.prepare('INSERT INTO sync_data (user_id, dataset, payload, updated_at) VALUES (?, ?, ?, ?)').run(bad, 'wrongbook', '{not json', 1);
  const r = await w.run();
  assert.strictEqual(r.candidates, 121);
  assert.strictEqual(r.sent, 120);
  assert.strictEqual(r.skipped.no_content, 1);
  assert.strictEqual(w.logRows().length, 120);
});

test('schema.sql 与迁移：旧库跑 0001_digest.sql 后列和表齐全；wrangler.toml 的 cron 与开关', async () => {
  if (!sqlite) { console.log('  skip 迁移（需要 node:sqlite）'); passed--; return; }
  const db = new sqlite.DatabaseSync(':memory:');
  db.exec('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL, mail_consent INTEGER NOT NULL DEFAULT 0, mkt_consent INTEGER NOT NULL DEFAULT 0, mail_consent_at INTEGER, mkt_consent_at INTEGER);');
  db.prepare('INSERT INTO users (email, created_at, mail_consent) VALUES (?, ?, 1)').run('old@qq.com', 1);
  db.exec(fs.readFileSync(path.join(API, 'migrations/0001_digest.sql'), 'utf8'));
  const row = db.prepare('SELECT digest_opt_out AS o, digest_token AS t FROM users').get();
  assert.strictEqual(row.o, 0);
  assert.strictEqual(row.t, null);
  db.prepare('INSERT INTO digest_log (user_id, week_key, sent_at) VALUES (1, ?, 1)').run('2026-W48');
  assert.throws(() => db.prepare('INSERT INTO digest_log (user_id, week_key, sent_at) VALUES (1, ?, 2)').run('2026-W48'), /UNIQUE|constraint/i);
  const toml = fs.readFileSync(path.join(API, 'wrangler.toml'), 'utf8');
  assert.ok(/\[triggers\]\s*(#[^\n]*\n\s*)*crons\s*=\s*\["0 0 \* \* 1"\]/.test(toml), 'cron 0 0 * * 1');
  assert.ok(/^DIGEST_DRY_RUN\s*=\s*"1"/m.test(toml), 'DIGEST_DRY_RUN 先设 "1"');
  assert.ok(/^MAIL_DRY_RUN\s*=\s*"0"/m.test(toml));
  const worker = fs.readFileSync(path.join(API, 'worker.js'), 'utf8');
  assert.ok(/scheduled\(event, env, ctx\)/.test(worker));
  const fresh = new sqlite.DatabaseSync(':memory:');
  fresh.exec(fs.readFileSync(path.join(API, 'schema.sql'), 'utf8'));
  fresh.exec(fs.readFileSync(path.join(API, 'schema.sql'), 'utf8'));
});

(async () => {
  for (const t of queue) {
    await t.fn();
    passed++;
    console.log('  ok   ' + t.name);
  }
  console.log(passed + ' passed');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
