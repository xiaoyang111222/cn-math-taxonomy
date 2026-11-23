/* 每周学习周报：周一 08:00（北京）由 cron 触发，也可用 POST /admin/digest/run 手动 / dry-run。
 * 收件人：mail_consent = 1 且 digest_opt_out = 0。内容只来自用户自己同步上来的四份数据，没内容不发。
 * DIGEST_DRY_RUN 不是 "0" 时一律只算不发、不写 digest_log。 */
import { DAY_MS, WRONGBOOK_URL, DIGEST_UNSUB_BASE, computeDue, isoWeekKey, maskEmail, generateDigestToken } from './lib.js';

const PAGE_SIZE = 50;
const WEEK_MS = 7 * DAY_MS;
const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000;
const FINALS_DAYS = 7;

function isObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }

/* 同步载荷是 {v, at, data} 信封（assets/sync.js）；容忍直接存数据本体。解析失败当没有数据。 */
function parseData(payload) {
  if (typeof payload !== 'string') return null;
  try {
    const value = JSON.parse(payload);
    return isObj(value) && 'data' in value ? value.data : value;
  } catch (e) {
    return null;
  }
}

function toMs(v) {
  if (typeof v === 'number' && isFinite(v) && v > 0) return v;
  if (typeof v === 'string') { const t = Date.parse(v); return isNaN(t) ? 0 : t; }
  return 0;
}

function cleanName(raw) {
  const name = String(raw == null ? '' : raw).replace(/[\u0000-\u001f\u007f\s]+/g, ' ').trim();
  return name.slice(0, 12);
}

function dayNumber(y, m, d) { return Date.UTC(y, m - 1, d); }

/* 期末补漏计划（finals/finals.js）：startDate 起 7 天；过了第 7 天就不再算「进行中」。 */
function activeFinals(plan, now) {
  if (!isObj(plan) || !Array.isArray(plan.days) || plan.days.length !== FINALS_DAYS) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(plan.startDate || ''));
  if (!m) return null;
  const start = dayNumber(Number(m[1]), Number(m[2]), Number(m[3]));
  const end = start + (FINALS_DAYS - 1) * DAY_MS;
  const nowShanghai = new Date(now + SHANGHAI_OFFSET_MS);
  const today = dayNumber(nowShanghai.getUTCFullYear(), nowShanghai.getUTCMonth() + 1, nowShanghai.getUTCDate());
  if (today > end) return null;
  const endDate = new Date(end);
  return { endMonth: endDate.getUTCMonth() + 1, endDay: endDate.getUTCDate() };
}

/* datasets: { children, records, wrongbook, finals } 解析后的数据（缺的是 null）。 */
export function summarizeUser(datasets, now) {
  const kids = isObj(datasets.children) && Array.isArray(datasets.children.children) ? datasets.children.children : [];
  const first = kids.find((c) => isObj(c) && cleanName(c.name));
  const name = first ? cleanName(first.name) : '';

  let newWrong = 0;
  let due = 0;
  let graduated = 0;
  if (isObj(datasets.wrongbook)) {
    Object.keys(datasets.wrongbook).forEach((bucket) => {
      const rows = datasets.wrongbook[bucket];
      if (!Array.isArray(rows)) return;
      rows.forEach((e) => {
        if (!isObj(e) || !e.qid) return;
        const ts = toMs(e.ts);
        if (ts > now - WEEK_MS && ts <= now) newWrong++;
        if (e.done) graduated++;
        else if (computeDue(e, now)) due++;
      });
    });
  }

  /* 诊断记录 {孩子id: [记录]}，记录的日期字段是 savedAt（ISO 字符串，首次保存时间）。 */
  let diagnoses = 0;
  if (isObj(datasets.records)) {
    Object.keys(datasets.records).forEach((child) => {
      const rows = datasets.records[child];
      if (!Array.isArray(rows)) return;
      rows.forEach((r) => {
        if (!isObj(r)) return;
        const at = toMs(r.savedAt);
        if (at > now - WEEK_MS && at <= now) diagnoses++;
      });
    });
  }

  const finals = activeFinals(datasets.finals, now);
  const hasContent = newWrong > 0 || due > 0 || graduated > 0 || diagnoses > 0 || !!finals;
  return { name, newWrong, due, graduated, diagnoses, finals, hasContent };
}

export function digestSubject(summary) {
  if (summary.due > 0) {
    return '知识图谱周报：' + (summary.name ? summary.name + '有 ' : '有 ') + summary.due + ' 道错题待复测';
  }
  return '知识图谱周报：本周学习小结';
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function lines(summary) {
  const out = [
    ['本周新增错题', summary.newWrong + ' 道'],
    ['现在待复测', summary.due + ' 道'],
    ['已毕业的错题', summary.graduated + ' 道'],
    ['本周诊断', summary.diagnoses + ' 次']
  ];
  return out;
}

export function renderDigest(summary, unsubUrl) {
  const greet = summary.name ? '您好，这是' + summary.name + '这一周在知识图谱上的学习小结：' : '您好，这是这一周在知识图谱上的学习小结：';
  const finalsLine = summary.finals ? '期末计划进行中，计划到 ' + summary.finals.endMonth + ' 月 ' + summary.finals.endDay + ' 日。' : '';
  const rows = lines(summary);
  const footer = '这是您注册时同意接收的服务邮件。不想再收到，可以退订：' + unsubUrl;

  const text = [greet, '']
    .concat(rows.map((r) => '- ' + r[0] + '：' + r[1]))
    .concat(finalsLine ? ['', finalsLine] : [])
    .concat(['', '去错题本复测：' + WRONGBOOK_URL, '', '--', footer])
    .join('\n');

  const rowHtml = rows.map((r) =>
    '<tr><td style="padding:6px 16px 6px 0;color:#555">' + escapeHtml(r[0]) + '</td>' +
    '<td style="padding:6px 0;font-weight:700">' + escapeHtml(r[1]) + '</td></tr>').join('');
  const html = '<!DOCTYPE html><html lang="zh-CN"><body style="margin:0;padding:24px;background:#f4f5f7;font-family:-apple-system,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;color:#1f2933">' +
    '<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:24px">' +
    '<p style="margin:0 0 16px;line-height:1.6">' + escapeHtml(greet) + '</p>' +
    '<table role="presentation" style="border-collapse:collapse;font-size:15px">' + rowHtml + '</table>' +
    (finalsLine ? '<p style="margin:16px 0 0;line-height:1.6">' + escapeHtml(finalsLine) + '</p>' : '') +
    '<p style="margin:24px 0"><a href="' + WRONGBOOK_URL + '" style="display:inline-block;padding:10px 20px;background:#0f6e62;color:#fff;text-decoration:none;border-radius:6px;font-weight:700">去错题本复测</a></p>' +
    '<p style="margin:24px 0 0;padding-top:12px;border-top:1px solid #e5e7eb;font-size:12px;color:#777;line-height:1.6">这是您注册时同意接收的服务邮件。不想再收到，可以<a href="' + escapeHtml(unsubUrl) + '" style="color:#777">退订</a>。</p>' +
    '</div></body></html>';
  return { text, html };
}

async function loadDatasets(env, userIds) {
  const byUser = new Map();
  if (!userIds.length) return byUser;
  const marks = userIds.map(() => '?').join(',');
  const res = await env.DB.prepare('SELECT user_id, dataset, payload FROM sync_data WHERE user_id IN (' + marks + ')').bind(...userIds).all();
  (res.results || []).forEach((r) => {
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, {});
    byUser.get(r.user_id)[r.dataset] = parseData(r.payload);
  });
  return byUser;
}

async function ensureToken(env, user) {
  if (user.digest_token) return user.digest_token;
  await env.DB.prepare('UPDATE users SET digest_token = ? WHERE id = ? AND digest_token IS NULL').bind(generateDigestToken(), user.id).run();
  const row = await env.DB.prepare('SELECT digest_token FROM users WHERE id = ?').bind(user.id).first();
  if (!row || !row.digest_token) throw new Error('digest_token_missing');
  return row.digest_token;
}

/* opts: { dryRun, now, sendMail }。dryRun 缺省看 env.DIGEST_DRY_RUN，不是 "0" 一律当 dry-run。
 * 返回 JSON 汇总，单个用户失败只记日志、不中断整批。 */
export async function sendWeeklyDigests(env, opts) {
  const o = opts || {};
  const now = typeof o.now === 'number' ? o.now : Date.now();
  const dryRun = o.dryRun === true || (o.dryRun !== false && String(env.DIGEST_DRY_RUN) !== '0');
  const weekKey = isoWeekKey(now);
  const result = {
    week_key: weekKey, dry_run: dryRun, candidates: 0, will_send: 0, sent: 0, failed: 0,
    skipped: { already_sent: 0, no_content: 0 }, items: []
  };
  if (!dryRun && typeof o.sendMail !== 'function') throw new Error('digest_sendMail_required');

  let lastId = 0;
  for (;;) {
    const page = await env.DB.prepare(
      'SELECT u.id AS id, u.email AS email, u.digest_token AS digest_token, l.user_id AS logged ' +
      'FROM users u LEFT JOIN digest_log l ON l.user_id = u.id AND l.week_key = ? ' +
      'WHERE u.mail_consent = 1 AND COALESCE(u.digest_opt_out, 0) = 0 AND u.id > ? ORDER BY u.id LIMIT ' + PAGE_SIZE
    ).bind(weekKey, lastId).all();
    const users = page.results || [];
    if (!users.length) break;
    lastId = users[users.length - 1].id;
    result.candidates += users.length;

    const pending = users.filter((u) => {
      if (u.logged != null) { result.skipped.already_sent++; return false; }
      return true;
    });
    let datasets;
    try {
      datasets = await loadDatasets(env, pending.map((u) => u.id));
    } catch (e) {
      console.error('digest: load sync_data failed: ' + (e && e.message));
      result.failed += pending.length;
      continue;
    }

    for (const user of pending) {
      let item = null;
      try {
        const summary = summarizeUser(datasets.get(user.id) || {}, now);
        if (!summary.hasContent) { result.skipped.no_content++; continue; }
        result.will_send++;
        item = {
          to: maskEmail(user.email), new_wrong: summary.newWrong, due: summary.due, graduated: summary.graduated,
          diagnoses: summary.diagnoses, finals: !!summary.finals, status: dryRun ? 'dry_run' : 'pending'
        };
        result.items.push(item);
        if (dryRun) continue;

        const unsubUrl = DIGEST_UNSUB_BASE + await ensureToken(env, user);
        const body = renderDigest(summary, unsubUrl);
        const sent = await o.sendMail(user.email, digestSubject(summary), body.text, {
          html: body.html, headers: { 'List-Unsubscribe': '<' + unsubUrl + '>' }
        });
        if (sent && sent.dryRun) { item.status = 'mail_dry_run'; continue; }
        item.status = 'sent';
        result.sent++;
        try {
          await env.DB.prepare('INSERT OR IGNORE INTO digest_log (user_id, week_key, sent_at) VALUES (?, ?, ?)').bind(user.id, weekKey, now).run();
        } catch (e) {
          console.error('digest: log write failed for user ' + user.id + ': ' + (e && e.message));
        }
      } catch (e) {
        console.error('digest: user ' + user.id + ' failed: ' + (e && e.message));
        result.failed++;
        if (item) item.status = 'failed';
      }
    }
  }
  return result;
}
