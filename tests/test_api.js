#!/usr/bin/env node
/* 账号与同步 Worker 测试：node tests/test_api.js（无依赖、不联网）。
 * api/lib.js 的纯逻辑直接测；api/worker.js 用 node:sqlite 内存库套一层 D1 外壳，跑真实的 schema.sql 与真实的路由。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const API = path.join(__dirname, '../api');
const load = (f) => import(pathToFileURL(path.join(API, f)).href);

let passed = 0;
const queue = [];
function test(name, fn) { queue.push({ name, fn }); }

/* ------------------------------------------------------------ 纯逻辑 */

test('邮箱规范化：小写去空白，不合法返回 null', async () => {
  const L = await load('lib.js');
  assert.strictEqual(L.normalizeEmail('  Mom@Example.COM '), 'mom@example.com');
  ['', 'a@b', 'a b@c.com', '@c.com', 'a@@c.com', 'a@c.com,b@d.com', '<a>@c.com', null, 123, 'x'.repeat(260) + '@a.com'].forEach((bad) => {
    assert.strictEqual(L.normalizeEmail(bad), null, String(bad));
  });
});

test('验证码：6 位数字、拒绝采样去偏、哈希绑定邮箱', async () => {
  const L = await load('lib.js');
  for (let i = 0; i < 200; i++) assert.match(L.generateOtp(), /^\d{6}$/);
  const feed = [0xffffffff, 0xfffffff0, 4000000123];
  let n = 0;
  const code = L.generateOtp((arr) => { arr[0] = feed[Math.min(n++, feed.length - 1)]; });
  assert.strictEqual(code, String(4000000123 % 1000000).padStart(6, '0'));
  assert.ok(n >= 3, '大于等于 limit 的随机数应被丢弃');
  assert.strictEqual(L.generateOtp((arr) => { arr[0] = 7; }), '000007');

  const h1 = await L.hashOtp('a@b.com', '123456', 'p');
  assert.match(h1, /^[0-9a-f]{64}$/);
  assert.strictEqual(h1, await L.hashOtp('a@b.com', '123456', 'p'));
  assert.notStrictEqual(h1, await L.hashOtp('c@b.com', '123456', 'p'));
  assert.notStrictEqual(h1, await L.hashOtp('a@b.com', '123456', 'q'));
  assert.notStrictEqual(h1, await L.hashOtp('a@b.com', '123457', 'p'));
  assert.ok(!h1.includes('123456'));
  assert.ok(L.timingSafeEqual(h1, h1));
  assert.ok(!L.timingSafeEqual(h1, h1.slice(0, -1) + (h1.endsWith('0') ? '1' : '0')));
  assert.ok(!L.timingSafeEqual(h1, 'short'));
});

test('验证码可用性：已用 / 过期 / 试满 5 次', async () => {
  const L = await load('lib.js');
  const row = (extra) => Object.assign({ used: 0, attempts: 0, expires_at: 10000 }, extra);
  assert.strictEqual(L.otpUsable(row(), 5000), 'ok');
  assert.strictEqual(L.otpUsable(row({ attempts: 4 }), 5000), 'ok');
  assert.strictEqual(L.otpUsable(row({ attempts: 5 }), 5000), 'locked');
  assert.strictEqual(L.otpUsable(row({ used: 1 }), 5000), 'used');
  assert.strictEqual(L.otpUsable(row(), 10000), 'expired');
  assert.strictEqual(L.otpUsable(null, 1), 'used');
});

test('限流：同邮箱 60 秒冷却、每小时 5 次，同 IP 每小时 20 次', async () => {
  const L = await load('lib.js');
  const base = { now: 100000, lastEmailAt: null, emailCount: 0, ipCount: 0 };
  assert.deepStrictEqual(L.rateLimit(base), { ok: true });
  const cool = L.rateLimit(Object.assign({}, base, { lastEmailAt: 100000 - 20000, emailCount: 1 }));
  assert.strictEqual(cool.ok, false);
  assert.strictEqual(cool.code, 'cooldown');
  assert.strictEqual(cool.retryAfterSec, 40);
  assert.strictEqual(L.rateLimit(Object.assign({}, base, { lastEmailAt: 100000 - 60000, emailCount: 4 })).ok, true);
  assert.strictEqual(L.rateLimit(Object.assign({}, base, { lastEmailAt: 1000, emailCount: 5 })).code, 'email_hourly');
  assert.strictEqual(L.rateLimit(Object.assign({}, base, { ipCount: 19 })).ok, true);
  assert.strictEqual(L.rateLimit(Object.assign({}, base, { ipCount: 20 })).code, 'ip_hourly');
});

test('会话令牌：32 字节随机、只存哈希、Bearer 解析', async () => {
  const L = await load('lib.js');
  const a = L.generateToken(), b = L.generateToken();
  assert.notStrictEqual(a, b);
  assert.match(a, /^[A-Za-z0-9_-]{43}$/);
  const hash = await L.hashToken(a);
  assert.match(hash, /^[0-9a-f]{64}$/);
  assert.notStrictEqual(hash, a);
  assert.strictEqual(L.parseBearer('Bearer ' + a), a);
  ['', 'Bearer', 'Bearer x', 'Basic ' + a, 'Bearer ' + a + ' extra', null].forEach((bad) => assert.strictEqual(L.parseBearer(bad), null));
});

test('CORS 来源：精确匹配 + 单级子域通配，不被前缀 / 后缀欺骗', async () => {
  const L = await load('lib.js');
  const rules = 'https://math.pansgo.com, https://*.cn-math-taxonomy.pages.dev';
  assert.ok(L.originAllowed('https://math.pansgo.com', rules));
  assert.ok(L.originAllowed('https://abc123.cn-math-taxonomy.pages.dev', rules));
  assert.ok(L.originAllowed('https://feat-x.cn-math-taxonomy.pages.dev', rules));
  [
    'http://math.pansgo.com', 'https://math.pansgo.com.evil.com', 'https://evil.com', 'https://xmath.pansgo.com',
    'https://a.b.cn-math-taxonomy.pages.dev', 'https://cn-math-taxonomy.pages.dev', 'https://evilcn-math-taxonomy.pages.dev',
    'https://math.pansgo.com:8443', '', null
  ].forEach((o) => assert.ok(!L.originAllowed(o, rules), String(o)));
  assert.ok(!L.originAllowed('https://math.pansgo.com', ''));
});

test('同步载荷与 base_updated_at 校验', async () => {
  const L = await load('lib.js');
  assert.strictEqual(L.validatePayload('{"a":1}'), null);
  assert.strictEqual(L.validatePayload('null'), null);
  assert.strictEqual(L.validatePayload(''), 'bad_payload');
  assert.strictEqual(L.validatePayload('{bad'), 'bad_payload');
  assert.strictEqual(L.validatePayload({ a: 1 }), 'bad_payload');
  assert.strictEqual(L.validatePayload('"' + 'x'.repeat(L.MAX_PAYLOAD_CHARS) + '"'), 'payload_too_large');
  assert.deepStrictEqual(L.parseBase(null), { ok: true, base: null });
  assert.deepStrictEqual(L.parseBase(undefined), { ok: true, base: null });
  assert.deepStrictEqual(L.parseBase(123), { ok: true, base: 123 });
  ['12', -1, 1.5, NaN, {}].forEach((bad) => assert.strictEqual(L.parseBase(bad).ok, false));
  assert.deepStrictEqual(Object.values(L.DATASETS), ['cnmChildren.v1', 'cnmChildren.records.v1', 'cnmWrong.v1', 'cnmFinals.v1']);
  assert.ok(L.isDataset('wrongbook'));
  ['toString', '__proto__', 'users', 5, null].forEach((bad) => assert.ok(!L.isDataset(bad)));
});

/* ------------------------------------------------------------ 发信 */

test('发信：DRY_RUN 只写日志不联网；生产走 Resend；缺密钥 / 失败会抛错', async () => {
  const { createMailer } = await load('mail.js');
  const warns = [];
  const origWarn = console.warn;
  console.warn = (...a) => warns.push(a.join(' '));
  let fetched = 0;
  try {
    const dry = createMailer({ MAIL_DRY_RUN: '1' }, async () => { fetched++; return { ok: true }; });
    assert.deepStrictEqual(await dry('a@b.com', '主题', '验证码 654321'), { dryRun: true });
  } finally { console.warn = origWarn; }
  assert.strictEqual(fetched, 0);
  assert.ok(warns.some((w) => w.includes('MAIL_DRY_RUN') && w.includes('654321') && w.includes('生产必须关闭')));

  let seen = null;
  const send = createMailer({ RESEND_API_KEY: 're_test', MAIL_DRY_RUN: '0' }, async (url, init) => { seen = { url, init }; return { ok: true, status: 200 }; });
  await send('a@b.com', '主题', '正文');
  assert.strictEqual(seen.url, 'https://api.resend.com/emails');
  assert.strictEqual(seen.init.method, 'POST');
  assert.strictEqual(seen.init.headers.Authorization, 'Bearer re_test');
  assert.deepStrictEqual(JSON.parse(seen.init.body), { from: '知识图谱 <noreply@math.pansgo.com>', to: ['a@b.com'], subject: '主题', text: '正文' });

  const custom = createMailer({ RESEND_API_KEY: 'k', MAIL_FROM: 'X <x@y.com>' }, async (u, init) => { seen = { init }; return { ok: true }; });
  await custom('a@b.com', 's', 't');
  assert.strictEqual(JSON.parse(seen.init.body).from, 'X <x@y.com>');

  await assert.rejects(createMailer({}, async () => ({ ok: true }))('a@b.com', 's', 't'), /mail_not_configured/);
  await assert.rejects(createMailer({ RESEND_API_KEY: 'k' }, async () => ({ ok: false, status: 422 }))('a@b.com', 's', 't'), /mail_failed_422/);
});

/* ------------------------------------------------------------ Worker（真实路由 + 内存 SQLite） */

let sqlite = null;
try { sqlite = require('node:sqlite'); } catch (e) { /* Node 太老：跳过 Worker 集成测试 */ }

function makeD1() {
  const db = new sqlite.DatabaseSync(':memory:');
  db.exec(fs.readFileSync(path.join(API, 'schema.sql'), 'utf8'));
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

async function makeWorld(envExtra) {
  const { createHandler } = await load('worker.js');
  const d1 = makeD1();
  const world = { now: Date.parse('2026-11-22T08:00:00Z'), mails: [], d1, ip: '1.1.1.1' };
  const env = Object.assign({ DB: d1, MAIL_DRY_RUN: '0', ALLOWED_ORIGINS: 'https://math.pansgo.com,https://*.cn-math-taxonomy.pages.dev' }, envExtra || {});
  const handler = createHandler({
    now: () => world.now,
    sendMail: async (to, subject, text) => { world.mails.push({ to, subject, text, code: (/\b(\d{6})\b/.exec(text) || [])[1] }); }
  });
  world.call = async (method, route, body, opts) => {
    const o = opts || {};
    const headers = { 'CF-Connecting-IP': o.ip || world.ip };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (o.token) headers.Authorization = 'Bearer ' + o.token;
    if (o.origin) headers.Origin = o.origin;
    const res = await handler(new Request('https://api.test' + route, { method, headers, body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)) }), env);
    const text = await res.text();
    let data = null;
    try { data = JSON.parse(text); } catch (e) { /* 204 */ }
    return { status: res.status, data, headers: res.headers };
  };
  world.login = async (email, consent) => {
    world.now += 61000;
    const r = await world.call('POST', '/auth/request-code', { email });
    assert.strictEqual(r.status, 200, JSON.stringify(r.data));
    const code = world.mails[world.mails.length - 1].code;
    const v = await world.call('POST', '/auth/verify', Object.assign({ email, code }, consent || {}));
    assert.strictEqual(v.status, 200, JSON.stringify(v.data));
    return v.data.token;
  };
  return world;
}

function worldTest(name, fn) {
  test(name, async () => {
    if (!sqlite) { console.log('  skip ' + name + '（需要 node:sqlite，Node ≥ 22.13）'); passed--; return; }
    await fn(await makeWorld());
  });
}

worldTest('request-code：已注册与未注册邮箱返回完全一样的成功响应；邮件里有 6 位码', async (w) => {
  const first = await w.call('POST', '/auth/request-code', { email: 'New@Example.com' });
  assert.strictEqual(first.status, 200);
  assert.strictEqual(w.mails.length, 1);
  assert.strictEqual(w.mails[0].to, 'new@example.com');
  assert.match(w.mails[0].code, /^\d{6}$/);
  await w.login('old@example.com');
  w.now += 61000;
  const known = await w.call('POST', '/auth/request-code', { email: 'old@example.com' });
  w.now += 61000;
  const unknown = await w.call('POST', '/auth/request-code', { email: 'brand-new@example.com' });
  assert.strictEqual(known.status, 200);
  assert.deepStrictEqual(known.data, unknown.data);
  assert.deepStrictEqual(known.data, first.data);
  assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'nope' })).status, 400);
  assert.strictEqual((await w.call('POST', '/auth/request-code', '{bad')).status, 400);
});

worldTest('验证码和令牌在库里只有哈希，响应与日志里没有明文验证码', async (w) => {
  const logs = [];
  const orig = { log: console.log, warn: console.warn, error: console.error, info: console.info };
  ['log', 'warn', 'error', 'info'].forEach((k) => { console[k] = (...a) => logs.push(a.join(' ')); });
  let token, res;
  try {
    res = await w.call('POST', '/auth/request-code', { email: 'a@example.com' });
    const code = w.mails[0].code;
    const wrong = await w.call('POST', '/auth/verify', { email: 'a@example.com', code: code === '000000' ? '111111' : '000000' });
    assert.strictEqual(wrong.status, 400);
    const ok = await w.call('POST', '/auth/verify', { email: 'a@example.com', code });
    token = ok.data.token;
  } finally { Object.assign(console, orig); }
  const code = w.mails[0].code;
  const otp = w.d1.db.prepare('SELECT * FROM otp_codes').all();
  assert.strictEqual(otp.length, 1);
  assert.match(otp[0].code_hash, /^[0-9a-f]{64}$/);
  assert.ok(Object.values(otp[0]).every((v) => String(v) !== code));
  assert.strictEqual(otp[0].ip, '1.1.1.1');
  const sess = w.d1.db.prepare('SELECT * FROM sessions').all();
  assert.strictEqual(sess.length, 1);
  assert.notStrictEqual(sess[0].token_hash, token);
  assert.ok(!JSON.stringify(sess[0]).includes(token));
  assert.ok(!JSON.stringify(res.data).includes(code));
  assert.ok(!logs.some((l) => l.includes(code) || l.includes(token)), logs.join('\n'));
});

worldTest('限流：60 秒冷却（带 Retry-After）、同邮箱每小时 5 次、同 IP 每小时 20 次', async (w) => {
  assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'r@example.com' })).status, 200);
  w.now += 30000;
  const cool = await w.call('POST', '/auth/request-code', { email: 'r@example.com' });
  assert.strictEqual(cool.status, 429);
  assert.strictEqual(cool.data.reason, 'cooldown');
  assert.strictEqual(cool.headers.get('Retry-After'), '30');
  assert.strictEqual(w.mails.length, 1);
  for (let i = 0; i < 4; i++) {
    w.now += 61000;
    assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'r@example.com' })).status, 200, 'send ' + (i + 2));
  }
  w.now += 61000;
  const hourly = await w.call('POST', '/auth/request-code', { email: 'r@example.com' });
  assert.strictEqual(hourly.status, 429);
  assert.strictEqual(hourly.data.reason, 'email_hourly');
  w.now += 3600000;
  assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'r@example.com' })).status, 200);
});

worldTest('限流：同 IP 每小时最多 20 次，换 IP 不受影响', async (w) => {
  w.ip = '9.9.9.9';
  for (let i = 0; i < 20; i++) assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'u' + i + '@example.com' })).status, 200, 'req ' + i);
  const over = await w.call('POST', '/auth/request-code', { email: 'u99@example.com' });
  assert.strictEqual(over.status, 429);
  assert.strictEqual(over.data.reason, 'ip_hourly');
  assert.strictEqual((await w.call('POST', '/auth/request-code', { email: 'u99@example.com' }, { ip: '8.8.8.8' })).status, 200);
});

worldTest('发信失败：返回 502，不占用限流名额', async (w) => {
  const { createHandler } = await load('worker.js');
  const handler = createHandler({ now: () => w.now, sendMail: async () => { throw new Error('boom'); } });
  const env = { DB: w.d1, ALLOWED_ORIGINS: 'https://math.pansgo.com' };
  const origErr = console.error;
  console.error = () => {};
  let res;
  try {
    res = await handler(new Request('https://api.test/auth/request-code', { method: 'POST', body: JSON.stringify({ email: 'f@example.com' }) }), env);
  } finally { console.error = origErr; }
  assert.strictEqual(res.status, 502);
  assert.strictEqual(w.d1.db.prepare('SELECT COUNT(*) AS n FROM otp_codes').get().n, 0);
});

worldTest('verify：错 5 次后锁定（正确码也不行）；用过的码不能再用；过期失效；新码作废旧码', async (w) => {
  await w.call('POST', '/auth/request-code', { email: 'v@example.com' });
  const code = w.mails[0].code;
  const wrong = code === '123456' ? '654321' : '123456';
  for (let i = 0; i < 5; i++) assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'v@example.com', code: wrong })).status, 400);
  const locked = await w.call('POST', '/auth/verify', { email: 'v@example.com', code });
  assert.strictEqual(locked.status, 429);
  assert.strictEqual(locked.data.error, 'too_many_attempts');

  w.now += 61000;
  await w.call('POST', '/auth/request-code', { email: 'v@example.com' });
  const second = w.mails[1].code;
  const ok = await w.call('POST', '/auth/verify', { email: 'v@example.com', code: second });
  assert.strictEqual(ok.status, 200);
  assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'v@example.com', code: second })).status, 400);

  w.now += 61000;
  await w.call('POST', '/auth/request-code', { email: 'v@example.com' });
  const third = w.mails[2].code;
  w.now += 61000;
  await w.call('POST', '/auth/request-code', { email: 'v@example.com' });
  const fourth = w.mails[3].code;
  if (third !== fourth) assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'v@example.com', code: third })).status, 400);

  w.now += 61000;
  await w.call('POST', '/auth/request-code', { email: 'exp@example.com' });
  const expiring = w.mails[w.mails.length - 1].code;
  w.now += 10 * 60 * 1000 + 1;
  assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'exp@example.com', code: expiring })).status, 400);
  assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'v@example.com', code: 'abc' })).status, 400);
  assert.strictEqual((await w.call('POST', '/auth/verify', { email: 'nobody@example.com', code: '123456' })).status, 400);
});

worldTest('注册：记录两类同意（营销默认不勾）；已有账号再登录不改同意', async (w) => {
  await w.login('c@example.com', { mail_consent: true, mkt_consent: false });
  let u = w.d1.db.prepare('SELECT * FROM users WHERE email = ?').get('c@example.com');
  assert.strictEqual(u.mail_consent, 1);
  assert.strictEqual(u.mkt_consent, 0);
  assert.ok(u.mail_consent_at > 0);
  assert.strictEqual(u.mkt_consent_at, null);
  await w.login('c@example.com', { mail_consent: false, mkt_consent: true });
  u = w.d1.db.prepare('SELECT * FROM users WHERE email = ?').get('c@example.com');
  assert.strictEqual(u.mail_consent, 1);
  assert.strictEqual(u.mkt_consent, 0);
  assert.strictEqual(w.d1.db.prepare('SELECT COUNT(*) AS n FROM users').get().n, 1);

  const token = await w.login('d@example.com', { mail_consent: true, mkt_consent: true });
  const me = await w.call('GET', '/auth/me', undefined, { token });
  assert.deepStrictEqual(me.data.email, 'd@example.com');
  assert.strictEqual(me.data.mkt_consent, true);
  await w.login('e@example.com');
  assert.strictEqual(w.d1.db.prepare('SELECT mail_consent FROM users WHERE email = ?').get('e@example.com').mail_consent, 0);
});

worldTest('会话：/auth/me 与 /sync 必须带有效令牌；退出后失效；30 天过期', async (w) => {
  for (const [m, p] of [['GET', '/auth/me'], ['POST', '/auth/logout'], ['GET', '/sync'], ['PUT', '/sync/wrongbook']]) {
    assert.strictEqual((await w.call(m, p, m === 'PUT' ? { payload: '{}' } : undefined)).status, 401, m + ' ' + p);
    assert.strictEqual((await w.call(m, p, m === 'PUT' ? { payload: '{}' } : undefined, { token: 'x'.repeat(43) })).status, 401);
  }
  const token = await w.login('s@example.com');
  assert.strictEqual((await w.call('GET', '/auth/me', undefined, { token })).status, 200);
  assert.strictEqual((await w.call('POST', '/auth/logout', undefined, { token })).status, 200);
  assert.strictEqual((await w.call('GET', '/auth/me', undefined, { token })).status, 401);
  assert.strictEqual((await w.call('GET', '/sync', undefined, { token })).status, 401);

  const t2 = await w.login('s@example.com');
  const exp = w.d1.db.prepare('SELECT created_at, expires_at FROM sessions').get();
  assert.strictEqual(exp.expires_at - exp.created_at, 30 * 24 * 3600 * 1000);
  w.now += 30 * 24 * 3600 * 1000 + 1000;
  assert.strictEqual((await w.call('GET', '/auth/me', undefined, { token: t2 })).status, 401);
});

worldTest('会话滚动续期：剩余不足 15 天顺延到 now+30 天，充足不写库，已过期仍拒绝', async (w) => {
  const DAY = 24 * 3600 * 1000;
  const token = await w.login('roll@example.com');
  const row = () => w.d1.db.prepare('SELECT expires_at FROM sessions').get().expires_at;
  const created = row();

  w.now += 10 * DAY;
  const early = await w.call('GET', '/auth/me', undefined, { token });
  assert.strictEqual(early.status, 200);
  assert.strictEqual(row(), created);
  assert.strictEqual(early.data.expires_at, created);
  assert.strictEqual(early.headers.get('X-Session-Expires'), String(created));

  w.now = created - 14 * DAY;
  const renewed = await w.call('GET', '/auth/me', undefined, { token });
  assert.strictEqual(renewed.status, 200);
  assert.strictEqual(row(), w.now + 30 * DAY);
  assert.strictEqual(renewed.data.expires_at, w.now + 30 * DAY);
  assert.strictEqual(renewed.headers.get('X-Session-Expires'), String(w.now + 30 * DAY));
  const after = row();

  w.now += 1000;
  assert.strictEqual((await w.call('GET', '/sync', undefined, { token })).status, 200);
  assert.strictEqual(row(), after);

  w.now = after + 1000;
  assert.strictEqual((await w.call('GET', '/auth/me', undefined, { token })).status, 401);
  assert.strictEqual(w.d1.db.prepare('SELECT COUNT(*) AS n FROM sessions').get().n, 0);
});

worldTest('同步：GET / PUT 乐观并发（base 不符 409 并带云端现状）', async (w) => {
  const token = await w.login('sync@example.com');
  const empty = await w.call('GET', '/sync', undefined, { token });
  assert.deepStrictEqual(empty.data, { datasets: {} });

  const p1 = JSON.stringify({ v: 1, at: 1, data: { c1: [{ qid: 'q1', ts: 1 }] } });
  const put1 = await w.call('PUT', '/sync/wrongbook', { payload: p1, base_updated_at: null }, { token });
  assert.strictEqual(put1.status, 200);
  assert.ok(put1.data.updated_at > 0);

  const dup = await w.call('PUT', '/sync/wrongbook', { payload: '{"x":1}', base_updated_at: null }, { token });
  assert.strictEqual(dup.status, 409);
  assert.strictEqual(dup.data.payload, p1);
  assert.strictEqual(dup.data.updated_at, put1.data.updated_at);

  const p2 = JSON.stringify({ v: 1, at: 2, data: { c1: [] } });
  const put2 = await w.call('PUT', '/sync/wrongbook', { payload: p2, base_updated_at: put1.data.updated_at }, { token });
  assert.strictEqual(put2.status, 200);
  assert.ok(put2.data.updated_at > put1.data.updated_at);

  const stale = await w.call('PUT', '/sync/wrongbook', { payload: p1, base_updated_at: put1.data.updated_at }, { token });
  assert.strictEqual(stale.status, 409);
  assert.strictEqual(stale.data.payload, p2);
  assert.strictEqual(stale.data.updated_at, put2.data.updated_at);

  await w.call('PUT', '/sync/finals', { payload: 'null' }, { token });
  const all = await w.call('GET', '/sync', undefined, { token });
  assert.deepStrictEqual(Object.keys(all.data.datasets).sort(), ['finals', 'wrongbook']);
  assert.strictEqual(all.data.datasets.wrongbook.payload, p2);
  assert.strictEqual(all.data.datasets.wrongbook.updated_at, put2.data.updated_at);
});

worldTest('同步：同一毫秒内连续写入，updated_at 仍然严格递增', async (w) => {
  const token = await w.login('tick@example.com');
  let base = null;
  const seen = [];
  for (let i = 0; i < 4; i++) {
    const r = await w.call('PUT', '/sync/children', { payload: JSON.stringify({ i }), base_updated_at: base }, { token });
    assert.strictEqual(r.status, 200);
    seen.push(r.data.updated_at);
    base = r.data.updated_at;
  }
  assert.deepStrictEqual(seen, seen.slice().sort((a, b) => a - b));
  assert.strictEqual(new Set(seen).size, 4);
});

worldTest('同步：未知 dataset 404、坏载荷 400、超大 413、坏 base 400', async (w) => {
  const token = await w.login('bad@example.com');
  assert.strictEqual((await w.call('PUT', '/sync/users', { payload: '{}' }, { token })).status, 404);
  assert.strictEqual((await w.call('PUT', '/sync/__proto__', { payload: '{}' }, { token })).status, 404);
  assert.strictEqual((await w.call('PUT', '/sync/wrongbook', { payload: { a: 1 } }, { token })).status, 400);
  assert.strictEqual((await w.call('PUT', '/sync/wrongbook', { payload: '{oops' }, { token })).status, 400);
  assert.strictEqual((await w.call('PUT', '/sync/wrongbook', { payload: '{}', base_updated_at: 'x' }, { token })).status, 400);
  assert.strictEqual((await w.call('PUT', '/sync/wrongbook', '[1]', { token })).status, 400);
  const big = JSON.stringify({ pad: 'x'.repeat(1100000) });
  assert.strictEqual((await w.call('PUT', '/sync/wrongbook', { payload: big }, { token })).status, 413);
  assert.strictEqual(w.d1.db.prepare('SELECT COUNT(*) AS n FROM sync_data').get().n, 0);
  assert.strictEqual((await w.call('GET', '/nope', undefined, { token })).status, 404);
  assert.strictEqual((await w.call('DELETE', '/sync', undefined, { token })).status, 405);
});

worldTest('同步：账号之间数据互相隔离', async (w) => {
  const a = await w.login('iso-a@example.com');
  const b = await w.login('iso-b@example.com');
  await w.call('PUT', '/sync/wrongbook', { payload: '{"owner":"a"}' }, { token: a });
  assert.deepStrictEqual((await w.call('GET', '/sync', undefined, { token: b })).data, { datasets: {} });
  const putB = await w.call('PUT', '/sync/wrongbook', { payload: '{"owner":"b"}' }, { token: b });
  assert.strictEqual(putB.status, 200);
  assert.strictEqual(JSON.parse((await w.call('GET', '/sync', undefined, { token: a })).data.datasets.wrongbook.payload).owner, 'a');
});

worldTest('CORS：只放行正式站和灰度子域；预检 204；陌生来源 403；无 Origin（curl）照常', async (w) => {
  const ok = await w.call('POST', '/auth/request-code', { email: 'cors@example.com' }, { origin: 'https://math.pansgo.com' });
  assert.strictEqual(ok.status, 200);
  assert.strictEqual(ok.headers.get('Access-Control-Allow-Origin'), 'https://math.pansgo.com');
  assert.strictEqual(ok.headers.get('Vary'), 'Origin');
  assert.strictEqual(ok.headers.get('Cache-Control'), 'no-store');

  const gray = await w.call('OPTIONS', '/sync', undefined, { origin: 'https://abc.cn-math-taxonomy.pages.dev' });
  assert.strictEqual(gray.status, 204);
  assert.strictEqual(gray.headers.get('Access-Control-Allow-Origin'), 'https://abc.cn-math-taxonomy.pages.dev');
  assert.match(gray.headers.get('Access-Control-Allow-Headers'), /Authorization/);
  assert.match(gray.headers.get('Access-Control-Allow-Methods'), /PUT/);

  const evil = await w.call('POST', '/auth/request-code', { email: 'cors2@example.com' }, { origin: 'https://evil.example' });
  assert.strictEqual(evil.status, 403);
  assert.strictEqual(evil.headers.get('Access-Control-Allow-Origin'), null);
  assert.strictEqual((await w.call('OPTIONS', '/sync', undefined, { origin: 'https://math.pansgo.com.evil.com' })).status, 403);
  assert.strictEqual(w.mails.length, 1);

  const token = await w.login('cors3@example.com');
  const err = await w.call('GET', '/sync', undefined, { origin: 'https://math.pansgo.com' });
  assert.strictEqual(err.status, 401);
  assert.strictEqual(err.headers.get('Access-Control-Allow-Origin'), 'https://math.pansgo.com');
  assert.ok(token);
});

test('默认 CORS 白名单只有正式站', async () => {
  const L = await load('lib.js');
  assert.strictEqual(L.DEFAULT_ALLOWED_ORIGINS, 'https://math.pansgo.com');
  const wrangler = fs.readFileSync(path.join(API, 'wrangler.toml'), 'utf8');
  assert.match(wrangler, /^name = "math-pansgo-api"/m);
  assert.match(wrangler, /binding = "DB"/);
  assert.match(wrangler, /MAIL_DRY_RUN = "0"/);
  assert.match(wrangler, /ALLOWED_ORIGINS = "https:\/\/math\.pansgo\.com,/);
  assert.doesNotMatch(wrangler, /RESEND_API_KEY\s*=/);
});

(async () => {
  for (const { name, fn } of queue) {
    await fn();
    passed++;
    console.log('  ok   ' + name);
  }
  console.log('\n' + passed + ' passed');
})().catch((e) => { console.error(e); process.exit(1); });
