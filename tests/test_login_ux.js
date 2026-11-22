#!/usr/bin/env node
/* 登录体验静态检查：node tests/test_login_ux.js（无依赖）。
 * 页头入口、首访提示条 / 价值时刻小卡的预留位置、关闭标记，以及两个同意勾选的默认状态。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const read = (f) => fs.readFileSync(path.join(__dirname, '..', f), 'utf8');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }

const account = read('assets/account.js');

test('页头入口是实心主色胶囊，旁带利益点，已登录显示邮箱和同步状态', () => {
  assert.ok(/\.nav-link\.cnm-account-btn\{[^}]*background:var\(--brand/.test(account));
  assert.ok(account.includes('登录后换手机不丢'));
  assert.ok(account.includes("class: 'cnm-acc-email', text: email()"));
  assert.ok(account.includes('syncShort()'));
});

test('提示条与小卡：三处预留位置，各自独立的 localStorage 标记，已登录不渲染', () => {
  assert.ok(read('index.html').includes('data-nudge="home"'));
  assert.ok(read('diagnose/app.js').includes("'data-nudge': 'diagnose'"));
  assert.ok(read('wrongbook/wrongbook.js').includes("'data-nudge', 'wrongbook'"));
  assert.ok(account.includes("'cnmNudge.' + name"));
  assert.ok(/if \(isLoggedIn\(\)\) \{ if \(name === 'home'\) lsSet\(nudgeKey\(name\), '1'\); return; \}/.test(account));
  assert.ok(/if \(isLoggedIn\(\)\) clearNudges\(\)/.test(account));
});

test('首访提示条只在首页，错题小卡只在有错题时放位置', () => {
  ['diagnose/index.html', 'wrongbook/index.html', 'finals/index.html', 'children/index.html'].forEach((f) => {
    assert.ok(!read(f).includes('data-nudge'), f);
  });
  const wb = read('wrongbook/wrongbook.js');
  assert.ok(wb.indexOf("'data-nudge', 'wrongbook'") > wb.indexOf('if (!all.length)'));
});

test('两个同意勾选的默认状态不变：服务邮件默认勾、营销邮件默认不勾', () => {
  assert.ok(account.includes("id: 'cnm-acc-mail', checked: true"));
  assert.ok(account.includes("h('input', { type: 'checkbox', id: 'cnm-acc-mkt' })"));
});

console.log(passed + ' passed');
