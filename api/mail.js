/* 发信抽象：createMailer(env) 返回 sendMail(to, subject, text, extra)。
 * extra 可选：{ html, headers }，周报用（HTML 版与退订头）；验证码邮件只传前三个参数。
 * 双通道：阿里云邮件推送 DirectMail 为主、Resend 兜底，主通道失败自动切另一通道。
 *   阿里云：RPC 接口 SingleSendMail（dm.aliyuncs.com），密钥 Worker secret
 *     ALIYUN_AK_ID / ALIYUN_AK_SECRET；发信地址默认取 MAIL_FROM 的地址部分，
 *     可用 ALIYUN_DM_ACCOUNT_NAME / ALIYUN_DM_FROM_ALIAS 覆盖。
 *   Resend：密钥 Worker secret RESEND_API_KEY，发件人 MAIL_FROM。
 *   MAIL_PROVIDER=aliyun|resend 可强制主通道；未设时有阿里云密钥就走阿里云。
 *   注意：阿里云 SingleSendMail 不支持自定义邮件头。带 headers 的邮件（如周报的
 *   List-Unsubscribe）优先走 Resend，Resend 不可用时才走阿里云（头会被丢弃，
 *   正文里的退订链接仍有效）。
 * MAIL_DRY_RUN=1：不真发，把整封邮件（含验证码明文）写进 Worker 日志。
 * !!! DRY_RUN 只准本地 / 灰度调试用，生产必须是 "0"（见 wrangler.toml）。!!! */
import { DEFAULT_MAIL_FROM } from './lib.js';

/* 阿里云 RPC 签名用的 percent-encode：只保留 RFC 3986 非保留字符，
 * 其余全部编码（与阿里云服务端重算口径一致）。 */
export function aliyunPercentEncode(str) {
  return encodeURIComponent(String(str))
    .replace(/[!'()*]/g, (c) => '%' + c.charCodeAt(0).toString(16).toUpperCase())
    .replace(/%7E/g, '~');
}

export function aliyunCanonicalQuery(params) {
  return Object.keys(params).sort()
    .map((k) => aliyunPercentEncode(k) + '=' + aliyunPercentEncode(params[k]))
    .join('&');
}

export function aliyunStringToSign(params) {
  return 'POST&%2F&' + aliyunPercentEncode(aliyunCanonicalQuery(params));
}

function base64(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

export async function aliyunSign(params, accessKeySecret) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(accessKeySecret + '&'),
    { name: 'HMAC', hash: 'SHA-1' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(aliyunStringToSign(params)));
  return base64(new Uint8Array(sig));
}

function parseFrom(from) {
  const m = /^\s*(.*?)\s*<([^>]+)>\s*$/.exec(from || '');
  if (m) return { alias: m[1], address: m[2] };
  return { alias: '', address: String(from || '') };
}

export function createMailer(env, fetchImpl) {
  const doFetch = fetchImpl || ((...args) => fetch(...args));

  async function sendViaResend(to, subject, text, extra) {
    const body = { from: env.MAIL_FROM || DEFAULT_MAIL_FROM, to: [to], subject, text };
    if (extra && extra.html) body.html = extra.html;
    if (extra && extra.headers) body.headers = extra.headers;
    const res = await doFetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('mail_failed_' + res.status);
    return { dryRun: false, via: 'resend' };
  }

  async function sendViaAliyun(to, subject, text, extra) {
    const from = parseFrom(env.MAIL_FROM || DEFAULT_MAIL_FROM);
    const params = {
      AccessKeyId: env.ALIYUN_AK_ID,
      Action: 'SingleSendMail',
      AddressType: '1',
      AccountName: env.ALIYUN_DM_ACCOUNT_NAME || from.address,
      Format: 'JSON',
      ReplyToAddress: 'false',
      SignatureMethod: 'HMAC-SHA1',
      SignatureNonce: crypto.randomUUID(),
      SignatureVersion: '1.0',
      Subject: subject,
      TextBody: text,
      Timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
      ToAddress: to,
      Version: '2015-11-23'
    };
    const alias = env.ALIYUN_DM_FROM_ALIAS || from.alias;
    if (alias) params.FromAlias = alias;
    if (extra && extra.html) params.HtmlBody = extra.html;
    params.Signature = await aliyunSign(params, env.ALIYUN_AK_SECRET);
    const res = await doFetch('https://dm.aliyuncs.com/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: aliyunCanonicalQuery(params)
    });
    if (!res.ok) throw new Error('mail_failed_' + res.status);
    if (typeof res.json === 'function') {
      const data = await res.json().catch(() => null);
      if (data && data.Code) throw new Error('mail_failed_aliyun_' + data.Code);
    }
    return { dryRun: false, via: 'aliyun' };
  }

  return async function sendMail(to, subject, text, extra) {
    if (String(env.MAIL_DRY_RUN) === '1') {
      console.warn('[MAIL_DRY_RUN=1 仅调试用，生产必须关闭] 未真发邮件。收件人=' + to + ' 主题=' + subject + '\n' + text);
      return { dryRun: true };
    }
    const hasAliyun = !!(env.ALIYUN_AK_ID && env.ALIYUN_AK_SECRET);
    const hasResend = !!env.RESEND_API_KEY;
    if (!hasAliyun && !hasResend) throw new Error('mail_not_configured');
    let order;
    if (env.MAIL_PROVIDER === 'resend') order = ['resend', 'aliyun'];
    else if (env.MAIL_PROVIDER === 'aliyun') order = ['aliyun', 'resend'];
    else if (extra && extra.headers && hasResend) order = ['resend', 'aliyun'];
    else order = hasAliyun ? ['aliyun', 'resend'] : ['resend', 'aliyun'];
    order = order.filter((p) => (p === 'aliyun' ? hasAliyun : hasResend));
    let lastErr = null;
    for (const p of order) {
      try {
        return p === 'aliyun'
          ? await sendViaAliyun(to, subject, text, extra)
          : await sendViaResend(to, subject, text, extra);
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr;
  };
}
