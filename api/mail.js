/* 发信抽象：createMailer(env) 返回 sendMail(to, subject, text, extra)。
 * extra 可选：{ html, headers }，周报用（HTML 版与退订头）；验证码邮件只传前三个参数。
 * 生产：Resend API，密钥来自 Worker secret RESEND_API_KEY，发件人 MAIL_FROM。
 * MAIL_DRY_RUN=1：不真发，把整封邮件（含验证码明文）写进 Worker 日志。
 * !!! DRY_RUN 只准本地 / 灰度调试用，生产必须是 "0"（见 wrangler.toml）。!!! */
import { DEFAULT_MAIL_FROM } from './lib.js';

export function createMailer(env, fetchImpl) {
  const doFetch = fetchImpl || ((...args) => fetch(...args));
  return async function sendMail(to, subject, text, extra) {
    if (String(env.MAIL_DRY_RUN) === '1') {
      console.warn('[MAIL_DRY_RUN=1 仅调试用，生产必须关闭] 未真发邮件。收件人=' + to + ' 主题=' + subject + '\n' + text);
      return { dryRun: true };
    }
    if (!env.RESEND_API_KEY) throw new Error('mail_not_configured');
    const body = { from: env.MAIL_FROM || DEFAULT_MAIL_FROM, to: [to], subject, text };
    if (extra && extra.html) body.html = extra.html;
    if (extra && extra.headers) body.headers = extra.headers;
    const res = await doFetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('mail_failed_' + res.status);
    return { dryRun: false };
  };
}
