/* 账号与同步 Worker 的纯逻辑：邮箱规范化、验证码生成与校验、令牌哈希、限流判定、CORS 来源匹配、同步载荷校验。
 * 不碰网络与数据库，tests/test_api.js 直接 import。 */

export const OTP_TTL_MS = 10 * 60 * 1000;
export const OTP_MAX_ATTEMPTS = 5;
export const RESEND_COOLDOWN_MS = 60 * 1000;
export const EMAIL_HOURLY_LIMIT = 5;
export const IP_HOURLY_LIMIT = 20;
export const HOUR_MS = 60 * 60 * 1000;
export const SESSION_TTL_MS = 30 * 24 * 60 * 60 * 1000;
export const SESSION_RENEW_BELOW_MS = 15 * 24 * 60 * 60 * 1000;
export const MAX_PAYLOAD_CHARS = 1000000;
export const DEFAULT_MAIL_FROM = '知识图谱 <noreply@math.pansgo.com>';
export const DEFAULT_ALLOWED_ORIGINS = 'https://math.pansgo.com';

/* dataset 名 → 前端 localStorage 键（仅作文档，服务端不解析内容）。 */
export const DATASETS = {
  children: 'cnmChildren.v1',
  records: 'cnmChildren.records.v1',
  wrongbook: 'cnmWrong.v1',
  finals: 'cnmFinals.v1'
};

export function isDataset(name) {
  return typeof name === 'string' && Object.prototype.hasOwnProperty.call(DATASETS, name);
}

const EMAIL_RE = /^[^\s@<>()[\]\\,;:"]+@[^\s@<>()[\]\\,;:"]+\.[^\s@<>()[\]\\,;:"]{2,}$/;

/* 小写、去空白；不合法返回 null。 */
export function normalizeEmail(raw) {
  if (typeof raw !== 'string') return null;
  const email = raw.trim().toLowerCase();
  if (email.length < 6 || email.length > 254) return null;
  if (!EMAIL_RE.test(email)) return null;
  return email;
}

const encoder = new TextEncoder();

export async function sha256Hex(text) {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(text));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

/* 6 位验证码，拒绝采样，每个数字等概率。random 仅供测试注入。 */
export function generateOtp(random) {
  const rng = random || ((arr) => crypto.getRandomValues(arr));
  const limit = Math.floor(0x100000000 / 1000000) * 1000000;
  const buf = new Uint32Array(1);
  for (;;) {
    rng(buf);
    if (buf[0] < limit) return String(buf[0] % 1000000).padStart(6, '0');
  }
}

/* 哈希绑定邮箱，pepper 是可选的服务端盐（Worker secret OTP_PEPPER）。 */
export function hashOtp(email, code, pepper) {
  return sha256Hex('otp\n' + email + '\n' + code + '\n' + (pepper || ''));
}

export function timingSafeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/* 判断一条验证码记录此刻能不能再试：'ok' | 'used' | 'expired' | 'locked'。 */
export function otpUsable(row, now) {
  if (!row || row.used) return 'used';
  if (row.expires_at <= now) return 'expired';
  if (row.attempts >= OTP_MAX_ATTEMPTS) return 'locked';
  return 'ok';
}

/* 限流：同邮箱 60 秒冷却、每小时 5 次；同 IP 每小时 20 次。
 * 返回 { ok: true } 或 { ok: false, code, retryAfterSec }。 */
export function rateLimit({ now, lastEmailAt, emailCount, ipCount }) {
  if (lastEmailAt && now - lastEmailAt < RESEND_COOLDOWN_MS) {
    return { ok: false, code: 'cooldown', retryAfterSec: Math.ceil((RESEND_COOLDOWN_MS - (now - lastEmailAt)) / 1000) };
  }
  if (emailCount >= EMAIL_HOURLY_LIMIT) return { ok: false, code: 'email_hourly', retryAfterSec: 600 };
  if (ipCount >= IP_HOURLY_LIMIT) return { ok: false, code: 'ip_hourly', retryAfterSec: 600 };
  return { ok: true };
}

/* 32 字节随机令牌，base64url。服务端只存 hashToken(token)。 */
export function generateToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  let bin = '';
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function hashToken(token) {
  return sha256Hex('session\n' + token);
}

export function parseBearer(header) {
  const m = /^Bearer\s+([A-Za-z0-9_-]{20,128})$/.exec(String(header || '').trim());
  return m ? m[1] : null;
}

function escapeRe(s) {
  return s.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
}

/* ALLOWED_ORIGINS：逗号分隔；每项可以带一个 * 通配单级子域，如 https://*.cn-math-taxonomy.pages.dev。 */
export function originAllowed(origin, allowedCsv) {
  if (typeof origin !== 'string' || !origin) return false;
  return String(allowedCsv || '').split(',').map((s) => s.trim()).filter(Boolean).some((rule) => {
    if (rule.indexOf('*') < 0) return rule === origin;
    const re = new RegExp('^' + rule.split('*').map(escapeRe).join('[a-z0-9-]+') + '$');
    return re.test(origin);
  });
}

/* 载荷必须是 JSON 文本字符串；服务端不关心内部结构。返回错误码或 null。 */
export function validatePayload(payload) {
  if (typeof payload !== 'string' || payload.length === 0) return 'bad_payload';
  if (payload.length > MAX_PAYLOAD_CHARS) return 'payload_too_large';
  try { JSON.parse(payload); } catch (e) { return 'bad_payload'; }
  return null;
}

/* base_updated_at：null / 省略表示「云端应当还没有这条」；否则必须是正整数。 */
export function parseBase(value) {
  if (value === null || value === undefined || value === 0) return { ok: true, base: null };
  if (Number.isSafeInteger(value) && value > 0) return { ok: true, base: value };
  return { ok: false };
}

/* ------------------------------------------------------------ 每周学习周报用 */

export const DAY_MS = 24 * 60 * 60 * 1000;
/* 错题复测间隔（天），下标是轮次 stage。与前端 assets/wrongbook.js 的 INTERVALS_DAYS 必须同值（tests/test_digest.js 核对）。 */
export const INTERVALS_DAYS = [1, 3, 7, 15];
export const WRONGBOOK_URL = 'https://math.pansgo.com/wrongbook/';
export const DIGEST_UNSUB_BASE = 'https://api.math.pansgo.com/digest/unsub?t=';
const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000;

/* 一条错题此刻是否到期：与前端 assets/wrongbook.js 的 isDue 同规则。
 * done=true 不到期；dueAt 缺省按 ts + 1 天（老条目，没有复测字段）。 */
export function computeDue(entry, now) {
  if (!entry || typeof entry !== 'object' || entry.done) return false;
  const dueAt = Number(entry.dueAt);
  const at = dueAt > 0 ? dueAt : (Number(entry.ts) || 0) + DAY_MS;
  return at <= now;
}

/* ISO 周（周一为一周之始），按 Asia/Shanghai 的日历日算，如 2026-W48。 */
export function isoWeekKey(ms) {
  const local = new Date(ms + SHANGHAI_OFFSET_MS);
  const day = Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate());
  const mondayOffset = (new Date(day).getUTCDay() + 6) % 7;
  const monday = day - mondayOffset * DAY_MS;
  const thursday = monday + 3 * DAY_MS;
  const isoYear = new Date(thursday).getUTCFullYear();
  const jan4 = Date.UTC(isoYear, 0, 4);
  const week1Monday = jan4 - ((new Date(jan4).getUTCDay() + 6) % 7) * DAY_MS;
  const week = 1 + Math.round((monday - week1Monday) / (7 * DAY_MS));
  return isoYear + '-W' + String(week).padStart(2, '0');
}

/* 邮箱打码：a***@qq.com。 */
export function maskEmail(email) {
  const s = String(email || '');
  const at = s.lastIndexOf('@');
  if (at < 1) return '***';
  return s.slice(0, 1) + '***' + s.slice(at);
}

/* 32 位小写十六进制随机串，只用于周报退订链接，不用于任何登录 / 鉴权。 */
export function generateDigestToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export function isDigestToken(value) {
  return typeof value === 'string' && /^[0-9a-f]{32}$/.test(value);
}
