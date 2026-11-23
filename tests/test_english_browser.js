#!/usr/bin/env node
/* 英语每日一句页浏览器测试：node tests/test_english_browser.js
 * 需要 Node 22+ 和 Chrome/Chromium（可用 CHROME 指定路径），无 npm 依赖；不在 npm test 里（同 test_children_browser.js）。
 * 在隔离的浏览器资料里走完整的一天：翻开翻译、排序、造句、完成打卡、第二天解锁、旧句复习到期。 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');
const assert = require('assert');
const { spawn } = require('child_process');
const root = path.resolve(__dirname, '..');
const out = fs.mkdtempSync(path.join(os.tmpdir(), 'cnm-english-browser-'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, label) {
  const end = Date.now() + 15000;
  while (Date.now() < end) { const v = await fn(); if (v) return v; await sleep(100); }
  throw new Error('Timeout: ' + label);
}
class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = [];
    ws.addEventListener('message', e => {
      const m = JSON.parse(e.data);
      if (m.id) {
        const p = this.pending.get(m.id); this.pending.delete(m.id);
        if (m.error) p.reject(new Error(p.method + ': ' + m.error.message)); else p.resolve(m.result);
      } else this.handlers.forEach(fn => fn(m));
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => { this.pending.set(id, { resolve, reject, method }); this.ws.send(JSON.stringify({ id, method, params })); });
  }
  async eval(expression) {
    const r = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  }
}
const server = http.createServer((req, res) => {
  let file = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (file.endsWith('/')) file += 'index.html';
  if (file === '/assets/stats-config.js') { res.setHeader('Content-Type', 'text/javascript'); res.end('window.CNM_STATS = {};'); return; }
  const full = path.resolve(root, '.' + file);
  if (!full.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
  fs.readFile(full, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', ({ '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png' })[path.extname(full)] || 'application/octet-stream');
    res.end(data);
  });
});

let chrome;
(async () => {
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const chromePath = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => p && fs.existsSync(p));
  if (!chromePath) throw new Error('找不到 Chrome/Chromium，请设置 CHROME 环境变量');
  chrome = spawn(chromePath, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-sync', '--disable-extensions', '--disable-component-update',
    '--remote-debugging-port=0', '--user-data-dir=' + path.join(out, 'profile'), 'about:blank'
  ], { stdio: ['ignore', 'ignore', fs.openSync(path.join(out, 'chrome.log'), 'w')] });
  const activePort = path.join(out, 'profile', 'DevToolsActivePort');
  await until(() => fs.existsSync(activePort), 'Chrome debugger');
  const port = fs.readFileSync(activePort, 'utf8').split('\n')[0];
  const tabs = await fetch('http://127.0.0.1:' + port + '/json').then(r => r.json());
  const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.addEventListener('open', resolve); ws.addEventListener('error', reject); });
  const cdp = new CDP(ws);
  const errors = [];
  cdp.handlers.push(m => { if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails); });
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
  await cdp.send('Network.setBypassServiceWorker', { bypass: true });
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 420, height: 900, deviceScaleFactor: 1, mobile: true });
  const base = 'http://127.0.0.1:' + server.address().port;
  const days = JSON.parse(fs.readFileSync(path.join(root, 'data/english/days.json'), 'utf8'));
  async function open() {
    await cdp.send('Page.navigate', { url: base + '/english/' });
    await until(() => cdp.eval('document.readyState === "complete" && !!document.querySelector(".lesson, .complete, .eng-flash, .load-error")'), 'page load');
  }
  const click = sel => cdp.eval(`document.querySelector(${JSON.stringify(sel)}).click()`);
  async function shot(name) {
    const r = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    fs.writeFileSync(path.join(out, name + '.png'), Buffer.from(r.data, 'base64'));
  }
  let passed = 0;
  const test = (name) => { passed++; console.log('  ok   ' + name); };

  await open();
  await cdp.eval('localStorage.clear()');
  await open();
  assert.strictEqual(await cdp.eval('document.querySelectorAll(".scene svg").length'), 1);
  assert.ok(await cdp.eval('document.querySelector(".sentence").textContent.includes("I am happy")'));
  assert.strictEqual(await cdp.eval('document.querySelector(".finish").disabled'), true);
  test('第 1 句：渲染动画与句子，完成按钮未解锁');

  await shot('lesson-1-start');
  await click('.layer summary');
  assert.ok(await cdp.eval('document.querySelectorAll(".check.done").length === 1'), '翻开翻译即勾猜出意思');
  test('翻开翻译 → 猜出意思打卡');

  for (const w of days[0].words) {
    await cdp.eval(`[...document.querySelectorAll('.sort-pool .sort-card')].find(b => b.textContent === ${JSON.stringify(w.en)}).click()`);
  }
  assert.ok(await cdp.eval('document.querySelectorAll(".check.done").length === 2'), '排序正确打卡');
  test('词卡排序排对 → 排序打卡');

  await click('.variants .chip');
  assert.ok(await cdp.eval('document.querySelectorAll(".check.done").length === 3'), '造句打卡');
  assert.strictEqual(await cdp.eval('document.querySelector(".finish").disabled'), false);
  test('换词造句 → 三项齐全，完成按钮可点');
  await shot('lesson-1-ready');

  await click('.finish');
  await until(() => cdp.eval('!!document.querySelector(".complete")'), '完成卡');
  const stored = JSON.parse(await cdp.eval('localStorage.getItem("cnmEnglish.v1")'));
  assert.ok(stored.guest.done['1'] && stored.guest.reviews['1'].dueOrd === 3);
  const act = JSON.parse(await cdp.eval('localStorage.getItem("cnmActivity.v1")'));
  assert.strictEqual(act.guest.length, 1);
  assert.ok(await cdp.eval('document.querySelector(".preview").textContent.includes("I am hungry") === false && document.querySelector(".preview").textContent.includes("第 2 句")'));
  assert.ok(await cdp.eval('document.querySelector(".cal-cell.done")'));
  await shot('lesson-1-complete');
  test('完成 → 写进 cnmEnglish.v1 与 cnmActivity.v1，出现完成卡与明日预告');

  await open();
  assert.ok(await cdp.eval('!!document.querySelector(".complete") && !document.querySelector(".lesson")'), '同一天不再给新句');
  test('刷新后同一天仍是完成态，不出新句');

  await cdp.eval(`(() => { const s = JSON.parse(localStorage.getItem('cnmEnglish.v1')); s.guest.done['1'].at -= 86400000; localStorage.setItem('cnmEnglish.v1', JSON.stringify(s)); })()`);
  await open();
  assert.ok(await cdp.eval('document.querySelector(".lesson .lesson-no").textContent === "第 2 句"'));
  test('过一天 → 解锁第 2 句');

  await cdp.eval(`(() => { const s = JSON.parse(localStorage.getItem('cnmEnglish.v1')); s.guest.done['2'] = {at: Date.now() - 86400000, checks: {guess: true, order: true, build: true}}; s.guest.reviews['2'] = {dueOrd: 4, doneOrds: []}; s.guest.done['1'].at -= 86400000; localStorage.setItem('cnmEnglish.v1', JSON.stringify(s)); })()`);
  await open();
  assert.ok(await cdp.eval('document.querySelector(".lesson .lesson-no").textContent === "第 3 句"'));
  assert.ok(await cdp.eval('!!document.querySelector(".review .rev-card")'), '第 3 句当天第 1 句复习到期');
  await shot('review');
  for (const w of days[0].words) {
    await cdp.eval(`[...document.querySelectorAll('.review .sort-pool .sort-card')].find(b => b.textContent === ${JSON.stringify(w.en)}).click()`);
  }
  await cdp.eval(`(() => { const i = document.querySelector('.review .dictation'); i.value = 'i am happy'; })()`);
  await cdp.eval(`[...document.querySelectorAll('.review button')].find(b => b.textContent === '检查听写').click()`);
  assert.strictEqual(await cdp.eval('[...document.querySelectorAll(".review button")].find(b => b.textContent === "完成这次复习").disabled'), false);
  await cdp.eval(`[...document.querySelectorAll('.review button')].find(b => b.textContent === '完成这次复习').click()`);
  await until(() => cdp.eval('!document.querySelector(".review .rev-card")'), '复习后不再到期');
  const after = JSON.parse(await cdp.eval('localStorage.getItem("cnmEnglish.v1")'));
  assert.deepStrictEqual(after.guest.reviews['1'], { dueOrd: 5, doneOrds: [3] });
  test('旧句复习：排序 + 听写通过 → 记下这一轮，下一轮 +4');

  assert.deepStrictEqual(errors, [], JSON.stringify(errors));
  test('页面没有未捕获异常');
  console.log(passed + ' passed；截图在 ' + out);
})().catch(e => { console.error(e); process.exitCode = 1; }).finally(() => { if (chrome) chrome.kill(); server.close(); });
