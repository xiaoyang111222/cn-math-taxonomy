/* math.pansgo.com 账号（邮箱验证码）与云同步 Worker。
 *   POST /auth/request-code  POST /auth/verify  POST /auth/logout  GET /auth/me
 *   GET /sync                PUT /sync/:dataset
 * 会话令牌走 Authorization: Bearer，只存 SHA-256 哈希；验证码只存哈希，日志不打明文（MAIL_DRY_RUN 除外）。 */
import {
  DEFAULT_ALLOWED_ORIGINS, OTP_TTL_MS, SESSION_TTL_MS, HOUR_MS,
  isDataset, normalizeEmail, generateOtp, hashOtp, timingSafeEqual, otpUsable, rateLimit,
  generateToken, hashToken, parseBearer, originAllowed, validatePayload, parseBase
} from './lib.js';
import { createMailer } from './mail.js';

const MAX_BODY_CHARS = 1200000;
const REQUEST_OK_MESSAGE = '如果邮箱填写无误，验证码已发送，请在 10 分钟内查收（也看看垃圾邮件）。';

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, headers || {})
  });
}

function fail(status, error, message, extra) {
  return json(Object.assign({ error, message: message || error }, extra || {}), status, extra && extra.retry_after ? { 'Retry-After': String(extra.retry_after) } : null);
}

async function readJson(request) {
  const declared = Number(request.headers.get('Content-Length'));
  if (declared > MAX_BODY_CHARS * 3) return { error: 'payload_too_large' };
  const text = await request.text();
  if (text.length > MAX_BODY_CHARS) return { error: 'payload_too_large' };
  try {
    const value = JSON.parse(text);
    if (!value || typeof value !== 'object' || Array.isArray(value)) return { error: 'bad_json' };
    return { value };
  } catch (e) {
    return { error: 'bad_json' };
  }
}

async function authenticate(request, env, now) {
  const token = parseBearer(request.headers.get('Authorization'));
  if (!token) return null;
  const tokenHash = await hashToken(token);
  const row = await env.DB.prepare(
    'SELECT s.token_hash, s.expires_at, u.id AS user_id, u.email, u.mail_consent, u.mkt_consent ' +
    'FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?'
  ).bind(tokenHash).first();
  if (!row) return null;
  if (row.expires_at <= now) {
    await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(tokenHash).run();
    return null;
  }
  return { tokenHash, userId: row.user_id, email: row.email, expiresAt: row.expires_at, mailConsent: row.mail_consent, mktConsent: row.mkt_consent };
}

async function requestCode(request, env, deps, now) {
  const parsed = await readJson(request);
  if (parsed.error) return fail(400, parsed.error);
  const email = normalizeEmail(parsed.value.email);
  if (!email) return fail(400, 'invalid_email', '邮箱格式不对。');
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';

  await env.DB.prepare('DELETE FROM otp_codes WHERE created_at < ?').bind(now - 24 * HOUR_MS).run();
  await env.DB.prepare('DELETE FROM sessions WHERE expires_at < ?').bind(now).run();

  const since = now - HOUR_MS;
  const byEmail = await env.DB.prepare('SELECT MAX(created_at) AS last_at, COUNT(*) AS n FROM otp_codes WHERE email = ? AND created_at > ?').bind(email, since).first();
  const byIp = await env.DB.prepare('SELECT COUNT(*) AS n FROM otp_codes WHERE ip = ? AND created_at > ?').bind(ip, since).first();
  const limit = rateLimit({ now, lastEmailAt: byEmail && byEmail.last_at, emailCount: byEmail ? byEmail.n : 0, ipCount: byIp ? byIp.n : 0 });
  if (!limit.ok) {
    return fail(429, 'rate_limited', '请求太频繁，请稍后再试。', { reason: limit.code, retry_after: limit.retryAfterSec });
  }

  const code = generateOtp();
  const codeHash = await hashOtp(email, code, env.OTP_PEPPER);
  await env.DB.prepare('UPDATE otp_codes SET used = 1 WHERE email = ? AND used = 0').bind(email).run();
  const inserted = await env.DB.prepare('INSERT INTO otp_codes (email, code_hash, expires_at, used, attempts, created_at, ip) VALUES (?, ?, ?, 0, 0, ?, ?)')
    .bind(email, codeHash, now + OTP_TTL_MS, now, ip).run();
  const otpId = inserted.meta.last_row_id;

  try {
    await deps.sendMail(email, '数学知识图谱登录验证码', '你的验证码是 ' + code + '，10 分钟内有效。\n如果不是你本人在操作，请直接忽略这封邮件。');
  } catch (e) {
    await env.DB.prepare('DELETE FROM otp_codes WHERE id = ?').bind(otpId).run();
    console.error('sendMail failed: ' + (e && e.message));
    return fail(502, 'mail_failed', '验证码邮件没发出去，请稍后再试。');
  }
  return json({ ok: true, message: REQUEST_OK_MESSAGE });
}

async function verify(request, env, now) {
  const parsed = await readJson(request);
  if (parsed.error) return fail(400, parsed.error);
  const body = parsed.value;
  const email = normalizeEmail(body.email);
  const code = typeof body.code === 'string' ? body.code.trim() : '';
  if (!email || !/^\d{6}$/.test(code)) return fail(400, 'invalid_code', '验证码不对或已过期。');

  const row = await env.DB.prepare('SELECT * FROM otp_codes WHERE email = ? AND used = 0 ORDER BY id DESC LIMIT 1').bind(email).first();
  const state = otpUsable(row, now);
  if (state === 'locked') return fail(429, 'too_many_attempts', '试错次数太多，请重新获取验证码。');
  if (state !== 'ok') return fail(400, 'invalid_code', '验证码不对或已过期。');

  const bumped = await env.DB.prepare('UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ? AND used = 0 AND attempts < 5').bind(row.id).run();
  if (bumped.meta.changes !== 1) return fail(429, 'too_many_attempts', '试错次数太多，请重新获取验证码。');
  const expected = await hashOtp(email, code, env.OTP_PEPPER);
  if (!timingSafeEqual(expected, row.code_hash)) return fail(400, 'invalid_code', '验证码不对或已过期。');
  const consumed = await env.DB.prepare('UPDATE otp_codes SET used = 1 WHERE id = ? AND used = 0').bind(row.id).run();
  if (consumed.meta.changes !== 1) return fail(400, 'invalid_code', '验证码不对或已过期。');

  let user = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first();
  let isNew = false;
  if (!user) {
    const mail = body.mail_consent === true ? 1 : 0;
    const mkt = body.mkt_consent === true ? 1 : 0;
    const created = await env.DB.prepare(
      'INSERT OR IGNORE INTO users (email, created_at, mail_consent, mkt_consent, mail_consent_at, mkt_consent_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(email, now, mail, mkt, mail ? now : null, mkt ? now : null).run();
    isNew = created.meta.changes === 1;
    user = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first();
  }

  const token = generateToken();
  const expiresAt = now + SESSION_TTL_MS;
  await env.DB.prepare('INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)')
    .bind(await hashToken(token), user.id, now, expiresAt).run();
  return json({ token, expires_at: expiresAt, email, is_new: isNew });
}

async function syncGet(env, session) {
  const rows = await env.DB.prepare('SELECT dataset, payload, updated_at FROM sync_data WHERE user_id = ?').bind(session.userId).all();
  const datasets = {};
  (rows.results || []).forEach((r) => { datasets[r.dataset] = { payload: r.payload, updated_at: r.updated_at }; });
  return json({ datasets });
}

async function syncPut(request, env, session, dataset, now) {
  if (!isDataset(dataset)) return fail(404, 'unknown_dataset');
  const parsed = await readJson(request);
  if (parsed.error) return fail(parsed.error === 'payload_too_large' ? 413 : 400, parsed.error);
  const payloadError = validatePayload(parsed.value.payload);
  if (payloadError) return fail(payloadError === 'payload_too_large' ? 413 : 400, payloadError);
  const base = parseBase(parsed.value.base_updated_at);
  if (!base.ok) return fail(400, 'bad_base');

  let changes;
  let updatedAt;
  if (base.base === null) {
    updatedAt = now;
    const res = await env.DB.prepare('INSERT INTO sync_data (user_id, dataset, payload, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT (user_id, dataset) DO NOTHING')
      .bind(session.userId, dataset, parsed.value.payload, updatedAt).run();
    changes = res.meta.changes;
  } else {
    updatedAt = Math.max(now, base.base + 1);
    const res = await env.DB.prepare('UPDATE sync_data SET payload = ?, updated_at = ? WHERE user_id = ? AND dataset = ? AND updated_at = ?')
      .bind(parsed.value.payload, updatedAt, session.userId, dataset, base.base).run();
    changes = res.meta.changes;
  }
  if (changes === 1) return json({ ok: true, updated_at: updatedAt });

  const current = await env.DB.prepare('SELECT payload, updated_at FROM sync_data WHERE user_id = ? AND dataset = ?').bind(session.userId, dataset).first();
  return json({ error: 'conflict', message: '云端有更新，请合并后重新提交。', payload: current ? current.payload : null, updated_at: current ? current.updated_at : null }, 409);
}

export function createHandler(overrides) {
  return async function handle(request, env) {
    const deps = Object.assign({ sendMail: createMailer(env), now: () => Date.now() }, overrides || {});
    const origin = request.headers.get('Origin');
    const allowed = env.ALLOWED_ORIGINS || DEFAULT_ALLOWED_ORIGINS;
    const corsOk = origin && originAllowed(origin, allowed);
    const headers = { 'Cache-Control': 'no-store', Vary: 'Origin' };
    if (corsOk) {
      headers['Access-Control-Allow-Origin'] = origin;
      headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type';
      headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS';
      headers['Access-Control-Max-Age'] = '86400';
    }
    const done = (res) => {
      Object.keys(headers).forEach((k) => res.headers.set(k, headers[k]));
      return res;
    };

    if (origin && !corsOk) return done(fail(403, 'origin_not_allowed'));
    if (request.method === 'OPTIONS') return done(new Response(null, { status: 204 }));

    try {
      const url = new URL(request.url);
      const path = url.pathname.replace(/\/+$/, '') || '/';
      const method = request.method;
      const now = deps.now();

      if (path === '/auth/request-code' && method === 'POST') return done(await requestCode(request, env, deps, now));
      if (path === '/auth/verify' && method === 'POST') return done(await verify(request, env, now));

      const isAuthRoute = path === '/auth/logout' || path === '/auth/me' || path === '/sync' || path.indexOf('/sync/') === 0;
      if (!isAuthRoute) return done(fail(404, 'not_found'));
      const session = await authenticate(request, env, now);
      if (!session) return done(fail(401, 'unauthorized', '请先登录。'));

      if (path === '/auth/me' && method === 'GET') {
        return done(json({ email: session.email, expires_at: session.expiresAt, mail_consent: !!session.mailConsent, mkt_consent: !!session.mktConsent }));
      }
      if (path === '/auth/logout' && method === 'POST') {
        await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(session.tokenHash).run();
        return done(json({ ok: true }));
      }
      if (path === '/sync' && method === 'GET') return done(await syncGet(env, session));
      if (path.indexOf('/sync/') === 0 && method === 'PUT') return done(await syncPut(request, env, session, path.slice(6), now));
      return done(fail(405, 'method_not_allowed'));
    } catch (e) {
      console.error('unhandled: ' + (e && e.message));
      return done(fail(500, 'server_error', '服务暂时不可用。'));
    }
  };
}

const handler = createHandler();

export default {
  fetch(request, env) { return handler(request, env); }
};
