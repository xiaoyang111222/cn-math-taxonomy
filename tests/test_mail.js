#!/usr/bin/env node
/* 发信双通道测试：node tests/test_mail.js（无依赖、不联网）。
 * 覆盖阿里云 DirectMail 的 RPC 签名（固定向量）、通道选择与失败兜底。 */
'use strict';
const assert = require('assert');
const path = require('path');
const { pathToFileURL } = require('url');

const load = (f) => import(pathToFileURL(path.join(__dirname, '../api', f)).href);

let passed = 0;
const queue = [];
function test(name, fn) { queue.push({ name, fn }); }

const FIXED_PARAMS = {
  AccessKeyId: 'testid', Action: 'SingleSendMail', AddressType: '1',
  AccountName: 'noreply@math.pansgo.com', Format: 'JSON', ReplyToAddress: 'false',
  SignatureMethod: 'HMAC-SHA1', SignatureNonce: 'test-nonce-1234', SignatureVersion: '1.0',
  Subject: '测试', TextBody: 'code 123456', Timestamp: '2026-11-23T12:00:00Z',
  ToAddress: 'a@b.com', Version: '2015-11-23'
};

test('阿里云签名：固定参数的 StringToSign 与签名值可复现', async () => {
  const M = await load('mail.js');
  assert.strictEqual(
    M.aliyunStringToSign(FIXED_PARAMS),
    'POST&%2F&AccessKeyId%3Dtestid%26AccountName%3Dnoreply%2540math.pansgo.com%26Action%3DSingleSendMail%26AddressType%3D1%26Format%3DJSON%26ReplyToAddress%3Dfalse%26SignatureMethod%3DHMAC-SHA1%26SignatureNonce%3Dtest-nonce-1234%26SignatureVersion%3D1.0%26Subject%3D%25E6%25B5%258B%25E8%25AF%2595%26TextBody%3Dcode%2520123456%26Timestamp%3D2026-11-23T12%253A00%253A00Z%26ToAddress%3Da%2540b.com%26Version%3D2015-11-23');
  assert.strictEqual(await M.aliyunSign(FIXED_PARAMS, 'testsecret'), 's0lR/o9/eJrayIu0VJZG7EWCzqM=');
});

test('通道选择：有阿里云密钥默认走阿里云，请求形态正确', async () => {
  const { createMailer } = await load('mail.js');
  let seen = null;
  const send = createMailer(
    { ALIYUN_AK_ID: 'id', ALIYUN_AK_SECRET: 'sec', MAIL_DRY_RUN: '0' },
    async (url, init) => { seen = { url, init }; return { ok: true, status: 200, json: async () => ({ EnvId: 'x' }) }; });
  const r = await send('a@b.com', '主题', '正文');
  assert.strictEqual(r.via, 'aliyun');
  assert.strictEqual(seen.url, 'https://dm.aliyuncs.com/');
  const body = new URLSearchParams(seen.init.body);
  assert.strictEqual(body.get('Action'), 'SingleSendMail');
  assert.strictEqual(body.get('AccountName'), 'noreply@math.pansgo.com');
  assert.strictEqual(body.get('FromAlias'), '知识图谱');
  assert.strictEqual(body.get('ToAddress'), 'a@b.com');
  assert.ok(body.get('Signature'), '应带签名');
});

test('兜底：阿里云失败自动切 Resend；Resend 失败抛 mail_failed', async () => {
  const { createMailer } = await load('mail.js');
  const env = { ALIYUN_AK_ID: 'id', ALIYUN_AK_SECRET: 'sec', RESEND_API_KEY: 'rk' };
  const calls = [];
  const send = createMailer(env, async (url) => {
    calls.push(url);
    if (url.includes('dm.aliyuncs.com')) return { ok: false, status: 400 };
    return { ok: true, status: 200 };
  });
  const r = await send('a@b.com', 's', 't');
  assert.strictEqual(r.via, 'resend');
  assert.strictEqual(calls.length, 2);
  const both = createMailer(env, async () => ({ ok: false, status: 500 }));
  await assert.rejects(both('a@b.com', 's', 't'), /mail_failed_500/);
});

test('通道选择：MAIL_PROVIDER=resend 时 Resend 优先；带 headers 的邮件优先 Resend', async () => {
  const { createMailer } = await load('mail.js');
  const env = { ALIYUN_AK_ID: 'id', ALIYUN_AK_SECRET: 'sec', RESEND_API_KEY: 'rk', MAIL_PROVIDER: 'resend' };
  const ok = async () => ({ ok: true, status: 200, json: async () => ({}) });
  const r1 = await createMailer(env, ok)('a@b.com', 's', 't');
  assert.strictEqual(r1.via, 'resend');
  const env2 = { ALIYUN_AK_ID: 'id', ALIYUN_AK_SECRET: 'sec', RESEND_API_KEY: 'rk' };
  const r2 = await createMailer(env2, ok)('a@b.com', 's', 't', { headers: { 'List-Unsubscribe': '<https://x>' } });
  assert.strictEqual(r2.via, 'resend');
});

test('未配置任何通道抛 mail_not_configured；DRY_RUN 不真发', async () => {
  const { createMailer } = await load('mail.js');
  await assert.rejects(createMailer({}, async () => ({ ok: true }))('a@b.com', 's', 't'), /mail_not_configured/);
  let fetched = 0;
  const dry = createMailer({ MAIL_DRY_RUN: '1', ALIYUN_AK_ID: 'id', ALIYUN_AK_SECRET: 'sec' },
    async () => { fetched++; return { ok: true }; });
  const r = await dry('a@b.com', 's', 't');
  assert.strictEqual(r.dryRun, true);
  assert.strictEqual(fetched, 0);
});

(async () => {
  for (const { name, fn } of queue) {
    await fn();
    passed++;
    console.log('  ok  ', name);
  }
  console.log(passed + ' passed');
})().catch((e) => { console.error(e); process.exit(1); });
