#!/usr/bin/env node
/* 无头 Chrome 冒烟测试 + 截图（无依赖：用 Node 内置 WebSocket 直接说 Chrome DevTools Protocol）。
 *
 *   node scripts/screenshot.js
 *
 * 做的事：起一个 python3 http.server，启动系统 Chrome（headless），
 *   1) 打开 /diagnose/，选目标、「不会」两次（出第二题 → 判薄弱 → 回溯先修）、刷新验证存档、一路答到结果页、导出 JSON、生成 PDF；
 *      再用固定 seed 分别测选择题（点选项）和数值题（输入答案）的自动判题与解析显示；全程监听 console 错误；
 *   2) 用 ?target=cnm_221&demo=1 的演示模式（掌握 / 不稳 / 薄弱 三种状态都会出现）截
 *      screenshots/01-start.png、02-question.png、03-result.png、04-graph.png，
 *      并截答题后显示解析的 05-explanation.png（1280×900）；
 *   3) 首页、知识图谱（cnm_221 / cnm_p001 / cnm_ext_002，以及根路径 #cnm_219）在 1280 与 375 宽下
 *      检查局部图、无横向溢出、无外网脚本/样式/字体/图片请求，并截 06–16；
 *   4) 知识图谱「全部」祖先（cnm_234：默认按年级收起，再展开并对准当前点）、375 宽长名称（cnm_124）
 *      以及 375 宽诊断路径图，截 17–20。
 *      首页儿童智商测试卡片截 36，诊断结果页底部入口截 37。
 *      全站顶部横幅：1280 首页顶部截 41-top-banner.png，375 截 42-top-banner-375.png。
 *      诊断分享图：数学（五年级上册）存 38-share-math.png，英语（现在进行时）存 39-share-en.png，
 *      375 宽弹层存 40-share-modal-375.png，并用 jsQR 解码图中二维码。
 *      小学英语图谱与四年级上册诊断截 32–35。初中英语「现在完成时」截 43–44，
 *      八年级上册英语整册诊断截 45–46。高中英语「虚拟语气」截 51–52，
 *      选择性必修第一册英语整册诊断截 53–54。
 * 环境变量：CHROME=/path/to/chrome  PORT=8765  DEBUG_PORT=9333
 */
'use strict';
const { spawn } = require('child_process');
const WebSocket = globalThis.WebSocket || require('undici').WebSocket;
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const zlib = require('zlib');
const E = require('../diagnose/engine.js');
const jsQR = require('./vendor/jsQR.js');
const SHARE_URL = 'https://math.pansgo.com/?from=share';

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'screenshots');
const PORT = parseInt(process.env.PORT || '8765', 10);
const DEBUG_PORT = parseInt(process.env.DEBUG_PORT || '9333', 10);
const BASE = 'http://127.0.0.1:' + PORT;

// 引擎是确定性的：在 Node 里用同一个 seed 预先算出浏览器里会出现哪道题
const DATA = path.join(ROOT, 'data');
const readJson = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), 'utf8'));
const TOPIC_ROWS = readJson('topics.json');
const DEP_ROWS = readJson('dependencies.json');
const QUESTION_ROWS = readJson('questions.json');
const STD_ITEMS = readJson('cn-curriculum-standards.json').items;
const N_TOPICS = String(TOPIC_ROWS.filter((t) => String(t.id).startsWith('cnm_')).length);
const N_EDGES = String(DEP_ROWS.filter((d) => String(d.topicId).startsWith('cnm_')).length);
const N_QUESTIONS = String(QUESTION_ROWS.filter((q) => String(q.topicId).startsWith('cnm_')).length);
const N_STANDARDS = String(STD_ITEMS.filter((it) => String(it.id).startsWith('cms-')).length);
// 首页统计是全站数字（千分位），不分学科。学科数与首页一样按 topics 里的 subject 现算。
const HOME_SUBJECTS = new Set(TOPIC_ROWS.map((t) => t.subject || 'math')).size;
const HOME_STATS = [TOPIC_ROWS.length, DEP_ROWS.length, QUESTION_ROWS.length, HOME_SUBJECTS].map((n) => n.toLocaleString('en-US'));
const N_GRADE_CARDS = 14;
const TOP_BANNER_EXPR = `(() => {
  const a = document.querySelector('a.top-banner');
  if (!a) return 'missing';
  const rel = (a.getAttribute('rel') || '').split(/\\s+/);
  const text = (a.textContent || '').replace(/\\s+/g, ' ').trim();
  if (a.getAttribute('href') !== 'https://test.pansgo.com/?from=math-top') return 'href';
  if (a.target !== '_blank') return 'target';
  if (rel.indexOf('noopener') < 0) return 'rel';
  if (text !== '🧠 儿童智商测试') return 'text:' + text;
  const header = document.querySelector('.site-header');
  if (!header || (a.compareDocumentPosition(header) & Node.DOCUMENT_POSITION_PRECEDING)) return 'order';
  const ar = a.getBoundingClientRect();
  const hr = header.getBoundingClientRect();
  if (ar.top > 1) return 'not-top:' + Math.round(ar.top);
  if (ar.bottom > hr.top + 1) return 'overlap-nav';
  const cs = getComputedStyle(a);
  const lh = parseFloat(cs.lineHeight);
  const range = document.createRange();
  range.selectNodeContents(a);
  const rh = range.getBoundingClientRect().height;
  if (!(lh > 0) || rh > lh * 1.45) return 'wrap:' + Math.round(rh) + '/' + lh;
  const probe = document.createElement('span');
  probe.textContent = a.textContent;
  probe.style.cssText = 'position:absolute;left:0;top:0;visibility:hidden;white-space:nowrap;font:' + cs.font;
  document.body.appendChild(probe);
  const textW = probe.getBoundingClientRect().width;
  probe.remove();
  const innerW = a.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  if (textW > innerW + 1) return 'clip:' + Math.round(textW) + '/' + Math.round(innerW);
  const navLinks = document.querySelectorAll('.site-nav a');
  for (let i = 0; i < navLinks.length; i++) {
    if (navLinks[i].getBoundingClientRect().height + 0.5 < 44) return 'nav-short';
  }
  const card = document.querySelector('a.iq-card');
  if (card && card.getAttribute('href') !== 'https://test.pansgo.com/?from=math-home') return 'card-href';
  return 'ok';
})()`;
const IQ_HOME_EXPR = `(() => {
  const a = document.querySelector('a.iq-card');
  if (!a) return 'missing';
  const rel = (a.getAttribute('rel') || '').split(/\\s+/);
  const text = a.textContent || '';
  if (a.getAttribute('href') !== 'https://test.pansgo.com/?from=math-home') return 'href';
  if (a.target !== '_blank') return 'target';
  if (rel.indexOf('noopener') < 0) return 'rel';
  if (text.indexOf('儿童智商测试') < 0 || text.indexOf('找规律 · 补图案 · 空间想象') < 0 || text.indexOf('趣味测评，与数学诊断无关') < 0) return 'text';
  if (text.indexOf('免费') >= 0 || text.indexOf('分钟') >= 0) return 'promo';
  return 'ok';
})()`;
const IQ_RESULT_EXPR = `(() => {
  const line = document.getElementById('iq-line');
  const a = line && line.querySelector('a');
  if (!line || !a) return 'missing';
  const page = document.getElementById('root') && document.getElementById('root').lastElementChild;
  if (!page || page.lastElementChild !== line) return 'not-last';
  if (a.getAttribute('href') !== 'https://test.pansgo.com/?from=math-result') return 'href';
  if (a.target !== '_blank') return 'target';
  if ((a.getAttribute('rel') || '').split(/\\s+/).indexOf('noopener') < 0) return 'rel';
  const compact = (line.textContent || '').replace(/\\s+/g, '');
  if (compact !== '做完数学诊断，再测测思维能力？→儿童智商测试') return 'text:' + compact;
  if (a.textContent !== '儿童智商测试') return 'link-text';
  return 'ok';
})()`;
const DERIVE = TOPIC_ROWS.find((t) => t.name === '导数的概念' && t.grade === 13);
const GRAPH = E.buildGraph(readJson('topics.json'), readJson('dependencies.json'), readJson('questions.json'));
function seedFor(topicId, pred) {
  for (let i = 0; i < 60; i++) {
    const seed = 'smoke' + i;
    const it = E.nextItem(GRAPH, E.createSession(GRAPH, [topicId], { seed: seed, avoid: [] }));
    if (pred(it.question)) return { seed: seed, q: it.question };
  }
  throw new Error('找不到合适的 seed：' + topicId);
}

function findChrome() {
  const cands = [process.env.CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].filter(Boolean);
  const hit = cands.find((p) => fs.existsSync(p));
  if (!hit) throw new Error('找不到 Chrome/Chromium，请设置环境变量 CHROME');
  return hit;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function pngInk(file, box) {
  const buf = fs.readFileSync(file);
  let off = 8, width = 0, height = 0, colorType = 0;
  const chunks = [];
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      colorType = data[9];
    } else if (type === 'IDAT') chunks.push(data);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  const bpp = colorType === 6 ? 4 : colorType === 2 ? 3 : 0;
  if (!bpp) throw new Error('无法解析截图颜色：' + file);
  const raw = zlib.inflateSync(Buffer.concat(chunks));
  const stride = width * bpp;
  const x0 = box ? Math.max(0, box.x) : 0;
  const y0 = box ? Math.max(0, box.y) : 0;
  const x1 = box ? Math.min(width, box.x + box.w) : width;
  const y1 = box ? Math.min(height, box.y + box.h) : height;
  let pos = 0, orange = 0, blue = 0;
  let prev = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[pos++];
    const row = Buffer.alloc(stride);
    for (let i = 0; i < stride; i++) {
      const x = raw[pos++];
      const a = i >= bpp ? row[i - bpp] : 0;
      const b = prev[i];
      const c = i >= bpp ? prev[i - bpp] : 0;
      let v = x;
      if (filter === 1) v = (x + a) & 255;
      else if (filter === 2) v = (x + b) & 255;
      else if (filter === 3) v = (x + ((a + b) >> 1)) & 255;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        const pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        v = (x + pr) & 255;
      }
      row[i] = v;
    }
    prev = row;
    if (y < y0 || y >= y1 || (y % 2)) continue;
    for (let x = x0; x < x1; x += 2) {
      const i = x * bpp;
      const r = row[i], g = row[i + 1], bch = row[i + 2];
      if (r > 180 && g > 60 && g < 190 && bch < 100) orange++;
      if (bch > 140 && bch > r + 40 && bch > g) blue++;
    }
  }
  return { width, height, orange, blue };
}

function pngDecode(file) {
  const buf = fs.readFileSync(file);
  if (buf.toString('ascii', 1, 4) !== 'PNG') throw new Error('不是 PNG：' + file);
  let off = 8, width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idats = [];
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      interlace = data[12];
    } else if (type === 'IDAT') idats.push(data);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (bitDepth !== 8 || interlace !== 0 || (colorType !== 2 && colorType !== 6)) {
    throw new Error('无法解码 PNG：' + file + ' depth=' + bitDepth + ' color=' + colorType + ' interlace=' + interlace);
  }
  const bpp = colorType === 6 ? 4 : 3;
  const raw = zlib.inflateSync(Buffer.concat(idats));
  const stride = width * bpp;
  const rgba = new Uint8ClampedArray(width * height * 4);
  let pos = 0;
  let prev = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[pos++];
    const row = Buffer.alloc(stride);
    for (let i = 0; i < stride; i++) {
      const x = raw[pos++];
      const a = i >= bpp ? row[i - bpp] : 0;
      const b = prev[i];
      const c = i >= bpp ? prev[i - bpp] : 0;
      let v = x;
      if (filter === 1) v = (x + a) & 255;
      else if (filter === 2) v = (x + b) & 255;
      else if (filter === 3) v = (x + ((a + b) >> 1)) & 255;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        const pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        v = (x + pr) & 255;
      }
      row[i] = v;
    }
    prev = row;
    for (let x = 0; x < width; x++) {
      const s = x * bpp;
      const d = (y * width + x) * 4;
      rgba[d] = row[s];
      rgba[d + 1] = row[s + 1];
      rgba[d + 2] = row[s + 2];
      rgba[d + 3] = bpp === 4 ? row[s + 3] : 255;
    }
  }
  return { width, height, data: rgba };
}
function pngRgba(file) { return pngDecode(file); }
function pngPixel(img, x, y) {
  const i = (y * img.width + x) * 4;
  return [img.data[i], img.data[i + 1], img.data[i + 2], img.data[i + 3]];
}
function cropRgba(img, box) {
  const x0 = Math.max(0, box.x), y0 = Math.max(0, box.y);
  const x1 = Math.min(img.width, box.x + box.w), y1 = Math.min(img.height, box.y + box.h);
  const w = x1 - x0, h = y1 - y0;
  const out = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) {
    const src = ((y0 + y) * img.width + x0) * 4;
    out.set(img.data.subarray(src, src + w * 4), y * w * 4);
  }
  return { width: w, height: h, data: out };
}
function decodeQr(img) {
  const boxes = [
    { x: 48, y: 1500, w: 400, h: 400 },
    { x: 0, y: img.height - 480, w: 560, h: 480 },
    { x: 0, y: 0, w: img.width, h: img.height }
  ];
  for (let i = 0; i < boxes.length; i++) {
    const crop = cropRgba(img, boxes[i]);
    const code = jsQR(crop.data, crop.width, crop.height, { inversionAttempts: 'dontInvert' });
    if (code && code.data) return code.data;
  }
  return null;
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => { let b = ''; res.on('data', (c) => (b += c)); res.on('end', () => { try { resolve(JSON.parse(b)); } catch (e) { reject(e); } }); }).on('error', reject);
  });
}
async function waitFor(fn, what, ms) {
  const end = Date.now() + (ms || 15000);
  for (;;) {
    try { const v = await fn(); if (v) return v; } catch (e) { /* retry */ }
    if (Date.now() > end) throw new Error('等待超时：' + what);
    await sleep(100);
  }
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = []; ws.addEventListener('message', (m) => this.onMessage(m.data)); }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((res, rej) => { ws.addEventListener('open', res); ws.addEventListener('error', rej); });
    return new CDP(ws);
  }
  onMessage(data) {
    const msg = JSON.parse(data);
    if (msg.id && this.pending.has(msg.id)) {
      const { resolve, reject } = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message)); else resolve(msg.result);
    } else if (msg.method) this.handlers.forEach((h) => h(msg));
  }
  send(method, params) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params: params || {} }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  on(fn) { this.handlers.push(fn); }
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const chromePath = findChrome();
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'cnm-chrome-'));
  const server = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: ROOT, stdio: 'ignore' });
  const chrome = spawn(chromePath, [
    '--headless=new', '--remote-debugging-port=' + DEBUG_PORT, '--user-data-dir=' + profile,
    '--window-size=1280,900', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
    '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage',
    '--disable-background-networking', '--disable-sync', '--disable-default-apps', '--disable-extensions',
    '--disable-component-update', '--disable-domain-reliability', '--metrics-recording-only', '--no-pings',
    '--safebrowsing-disable-auto-update',
    '--disable-features=Translate,OptimizationHints,MediaRouter,DialMediaRouteProvider',
    'about:blank'
  ], { stdio: 'ignore' });
  const errors = [];
  const externalReqs = [];
  const checks = [];
  const check = (ok, msg) => { checks.push([ok, msg]); console.log((ok ? '  ok   ' : '  FAIL ') + msg); };
  let exitCode = 0;
  let dumpPage = null;
  try {
    await waitFor(() => getJson(BASE + '/diagnose/engine.js').then(() => true, () => fetchOk(BASE + '/diagnose/engine.js')), 'http.server');
    const targets = await waitFor(async () => { const l = await getJson('http://127.0.0.1:' + DEBUG_PORT + '/json/list'); return l.find((t) => t.type === 'page'); }, 'Chrome 调试端口');
    const cdp = await CDP.connect(targets.webSocketDebuggerUrl);
    cdp.on((m) => {
      if (m.method === 'Runtime.exceptionThrown') errors.push('exception: ' + (m.params.exceptionDetails.exception && m.params.exceptionDetails.exception.description || m.params.exceptionDetails.text));
      if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push('console.error: ' + m.params.args.map((a) => a.value || a.description).join(' '));
      if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errors.push('log: ' + m.params.entry.text + ' ' + (m.params.entry.url || ''));
      if (m.method === 'Network.responseReceived' && m.params.response.status >= 400) {
        const url = m.params.response.url;
        if (!/\/favicon\.ico(?:$|\?)/.test(url)) errors.push('http ' + m.params.response.status + ' ' + url);
      }
      if (m.method === 'Network.requestWillBeSent') noteExternal(m.params, externalReqs);
    });
    await Promise.all(['Runtime', 'Log', 'Page', 'Network'].map((d) => cdp.send(d + '.enable')));
    let viewW = 1280, viewH = 900;
    const setView = async (w, h) => {
      viewW = w; viewH = h;
      await cdp.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
      await sleep(80);
    };
    await setView(1280, 900);

    const evalJs = async (expr) => {
      const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error('evaluate 失败：' + expr + ' → ' + JSON.stringify(r.exceptionDetails.exception && r.exceptionDetails.exception.description));
      return r.result.value;
    };
    const goto = async (url) => {
      await cdp.send('Page.navigate', { url });
      await waitFor(() => evalJs('document.readyState === "complete"'), 'load ' + url);
    };
    dumpPage = () => evalJs('document.body.innerText.slice(0, 1500)');
    const exists = (sel) => evalJs('!!document.querySelector(' + JSON.stringify(sel) + ')');
    const click = (sel) => evalJs('(() => { const e = document.querySelector(' + JSON.stringify(sel) + '); if (!e) throw new Error("no " + ' + JSON.stringify(sel) + '); e.click(); return true; })()');
    const shot = async (file, selector, clipH, opts) => {
      await sleep(300);
      // 默认截当前视口宽度、从页面顶部起；给 selector 则从该元素上沿起截（可超出当前视口）。
      // 大图的 canvas 在 captureBeyondViewport 下会拍成空白，视口内的图改用视口截图。
      const beyond = !opts || opts.beyond !== false;
      const y = selector ? await evalJs('Math.max(0, document.querySelector(' + JSON.stringify(selector) + ').getBoundingClientRect().top + window.scrollY - 12)') : 0;
      const r = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: beyond, clip: { x: 0, y: beyond ? y : 0, width: viewW, height: clipH || viewH, scale: 1 } });
      fs.writeFileSync(path.join(OUT, file), Buffer.from(r.data, 'base64'));
      console.log('  截图 screenshots/' + file);
    };
    const overflowOf = () => evalJs('(() => { const doc = document.documentElement; const sw = Math.max(doc.scrollWidth, document.body ? document.body.scrollWidth : 0); return { sw: sw, cw: doc.clientWidth, ok: sw <= doc.clientWidth + 1 }; })()');
    const assetsOf = () => evalJs(LOCAL_ASSET_EXPR);
    const checkPage = async (label) => {
      const ov = await overflowOf();
      check(ov.ok, label + ' 无横向溢出（scrollWidth ' + ov.sw + ' / clientWidth ' + ov.cw + '）');
      const bad = await assetsOf();
      check(bad.length === 0, label + ' 没有外网 script/link/font/img' + (bad.length ? '：' + bad.join('；') : ''));
    };
    const checkBanner = async (label) => {
      const banner = await evalJs(TOP_BANNER_EXPR);
      check(banner === 'ok', label + ' 顶部横幅（' + banner + '）');
    };
    const NODE_METRICS_JS = `
      let tall = 0, spill = 0, uncut = 0, overlap = 0, primary = 0, junior = 0, senior = 0, grades = 0;
      const limit = window.matchMedia('(max-width: 700px)').matches ? 8 : 10;
      const boxes = [];
      cy.nodes().forEach(function (n) {
        if (n.hasClass('primary')) primary++;
        if (n.hasClass('junior')) junior++;
        if (n.hasClass('senior')) senior++;
        if (n.hasClass('grade')) grades++;
        if (n.height() > 40) tall++;
        const body = n.boundingBox({ includeLabels: false });
        const withL = n.boundingBox({ includeLabels: true });
        if (withL.w > body.w + 4 || withL.h > body.h + 4) spill++;
        const name = n.data('name') || '';
        const label = n.data('label') || '';
        if (Array.from(name).length > limit && !String(label).endsWith('…')) uncut++;
        if (Array.from(label).length > limit) uncut++;
        boxes.push(withL);
      });
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i], b = boxes[j];
          if (a.x1 < b.x2 - 2 && a.x2 > b.x1 + 2 && a.y1 < b.y2 - 2 && a.y2 > b.y1 + 2) overlap++;
        }
      }
    `;
    const EXPLORE_GRAPH_EXPR = `(() => {
      const cy = window.__cy;
      const hard = cy.edges('.hard');
      const soft = cy.edges('.soft');
      ${NODE_METRICS_JS}
      return {
        nodes: cy.nodes().length, hash: location.hash,
        title: (document.querySelector('.detail-title') || {}).textContent || '',
        idCode: (document.querySelector('.id-code') || {}).textContent || '',
        meta: document.getElementById('graph-meta').textContent,
        diag: (document.querySelector('a.diag-btn') || {}).getAttribute ? document.querySelector('a.diag-btn').getAttribute('href') : '',
        alias: (document.querySelector('.alias-note') || {}).textContent || '',
        hard: hard.length ? hard[0].style('line-style') : '',
        soft: soft.length ? soft[0].style('line-style') : '',
        hardN: hard.length, softN: soft.length,
        current: cy.nodes('.current').length,
        primary, junior, senior, grades, tall, spill, uncut, overlap,
        wrap: cy.nodes().length ? cy.nodes()[0].style('text-wrap') : ''
      };
    })()`;
    const PATH_GRAPH_EXPR = `(() => {
      const cy = window.__pathCy;
      if (!cy) return null;
      ${NODE_METRICS_JS}
      const hard = cy.edges('.hard');
      const soft = cy.edges('.soft');
      const indirect = cy.edges('.indirect');
      return {
        nodes: cy.nodes().length, primary, junior, senior, grades, tall, spill, uncut, overlap,
        root: cy.nodes('.root').length,
        target: cy.nodes('.target').length,
        rootBorder: cy.nodes('.root').length ? cy.nodes('.root')[0].style('border-width') : '',
        hard: hard.length ? hard[0].style('line-style') : '',
        soft: soft.length ? soft[0].style('line-style') : '',
        indirect: indirect.length ? indirect[0].style('line-style') : '',
        hardN: hard.length, softN: soft.length, indirectN: indirect.length,
        pathItems: document.querySelectorAll('#path ol.path > li').length,
        svg: !!document.querySelector('svg.graph')
      };
    })()`;
    const checkPathGraph = async (label) => {
      await waitFor(() => evalJs('document.getElementById("path-cy") && document.getElementById("path-cy").dataset.ready === "1"'), label + ' 路径图', 15000);
      const g = await evalJs(PATH_GRAPH_EXPR);
      check(!g.svg && g.nodes > 0 && g.pathItems > 0, label + ' 有 Cytoscape 路径图和文字路径（' + g.nodes + ' 个点，' + g.pathItems + ' 步）');
      check(g.primary + g.junior + g.senior === g.nodes, label + ' 节点按小学/初中/高中区分（小学 ' + g.primary + '，初中 ' + g.junior + '，高中 ' + g.senior + '）');
      check(g.root >= 1 && parseFloat(g.rootBorder) >= 4, label + ' 薄弱根因已高亮');
      check(g.target >= 1, label + ' 标出了目标');
      check(g.hardN === 0 || g.hard === 'solid', label + ' 硬先修实线');
      check(g.softN === 0 || g.soft === 'dashed', label + ' 软先修虚线');
      check(g.indirectN === 0 || g.indirect === 'dotted', label + ' 省略边为点线');
      check(g.tall === 0 && g.spill === 0 && g.uncut === 0, label + ' 标签单行截断（高 ' + g.tall + '，溢出 ' + g.spill + '，未截 ' + g.uncut + '）');
      check(g.overlap === 0, label + ' 节点不重叠（' + g.overlap + '）');
      return g;
    };

    console.log('冒烟测试');
    await goto(BASE + '/diagnose/');
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('#target-list .topic-row'), '开始页列表');
    const rows = await evalJs('document.querySelectorAll("#target-list .topic-row").length');
    check(rows > 100, '开始页渲染了知识点列表（' + rows + ' 行）');
    check(await exists('.chap-head button.primary'), '有「以整章为目标」按钮');
    check(await evalJs('document.querySelector("a.back").getAttribute("href")') === '../explore/', '有返回知识图谱的链接');
    await checkBanner('诊断开始页 1280');
    await checkPage('诊断开始页 1280');

    // 搜索并选目标
    await evalJs('(() => { const s = document.getElementById("search"); s.value = "配方法"; s.dispatchEvent(new Event("input", {bubbles:true})); })()');
    const found = await evalJs('document.querySelectorAll("#target-list .topic-row").length');
    check(found >= 1 && found < 20, '搜索「配方法」得到 ' + found + ' 个知识点');
    await click('#target-list .topic-row button');
    await waitFor(() => exists('.q-text'), '出题页');
    check(true, '能选目标并进入出题页');
    check((await evalJs('document.querySelector(".q-title").textContent')).includes('配方法'), '首题是目标知识点本身（配方法）');

    // 第一题：点「不会」→ 显示解析与参考答案 → 下一题；同一知识点出第二题
    check(await exists('.tag.diff-basic, .tag.diff-standard, .tag.diff-advanced'), '题目显示难度标签');
    check(await exists('#btn-skip'), '有「不会」按钮');
    await click('#btn-skip');
    await waitFor(() => exists('.refans'), '「不会」后显示参考答案');
    check(await exists('#explain') && (await evalJs('document.querySelector("#explain").textContent')).includes('解析'), '「不会」后显示解析和参考答案');
    await click('#btn-next');
    await waitFor(() => evalJs('document.querySelector(".q-text") && !document.querySelector(".refans")'), '第二题');
    const cardText2 = await evalJs('document.querySelector(".card").textContent');
    check(/第 2 题/.test(cardText2) && cardText2.includes('本知识点第 2 题') && (await evalJs('document.querySelector(".q-title").textContent')).includes('配方法'),
      '第一题没过 → 同一知识点（配方法）再出第 2 题');
    await click('#btn-skip');
    await click('#btn-next');
    await waitFor(() => evalJs('document.querySelector(".q-text") && !document.querySelector(".refans")'), '回溯到先修');
    const cardText3 = await evalJs('document.querySelector(".card").textContent');
    check(/第 3 题/.test(cardText3) && !(await evalJs('document.querySelector(".q-title").textContent')).includes('配方法') && cardText3.includes('本知识点第 1 题'),
      '两题都没过 → 判薄弱并回溯到先修知识点（第 3 题是别的知识点）');
    const saved = await evalJs('JSON.parse(localStorage.getItem("cnmDiagnose.session.v2")).answers.length');
    check(saved === 2, '进度已保存到 localStorage（answers=' + saved + '）');
    check(await evalJs('JSON.parse(localStorage.getItem("cnmDiagnose.seen.v1")).length') === 2, '出过的题 id 记录在 localStorage（2 道）');

    // 刷新后可继续
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('.banner button.primary'), '继续存档横幅');
    await click('.banner button.primary');
    await waitFor(() => exists('.q-text'), '继续后的出题页');
    check(/第 3 题/.test(await evalJs('document.querySelector(".card").textContent')), '刷新后点「继续」仍在第 3 题');

    // 一路点「不会」到结果页
    for (let i = 0; i < 40; i++) {
      if (await exists('#summary')) break;
      if (await exists('#btn-skip')) await click('#btn-skip');
      await waitFor(() => exists('#btn-next'), '下一题按钮');
      await click('#btn-next');
      await sleep(30);
    }
    await waitFor(() => exists('#summary'), '结果页');
    check(await exists('#roots') && await exists('#path') && await exists('#shaky') && await exists('ol.path'), '结果页含 根因 / 不稳 / 文字版学习路径');
    await checkPathGraph('结果页');
    const asked = await evalJs('document.querySelectorAll("#log tbody tr").length');
    check(asked > 2 && asked <= 16, '答题数不超过上限 16（实际 ' + asked + '）');
    check((await evalJs('document.querySelectorAll("#roots details.topic").length')) >= 1, '至少有一个薄弱根因可展开');
    check((await evalJs('document.querySelectorAll("#standards .std").length')) >= 1, '列出了相关课标条目（含原文）');
    await click('#btn-export');
    check(true, '「导出 JSON」点击无异常');
    const pdf = await cdp.send('Page.printToPDF', { printBackground: true });
    check(pdf.data.length > 1000, '打印为 PDF 成功（' + Math.round(pdf.data.length * 0.75 / 1024) + ' KB）');
    // 改答案
    await evalJs('(() => { const sel = document.querySelector("#log select"); sel.value = "correct"; sel.dispatchEvent(new Event("change", {bubbles:true})); })()');
    await sleep(200);
    check(await exists('#summary') || await exists('.q-text'), '更正某题答案后页面正常重算');

    // 选择题：固定 seed，点选项 → 提交 → 自动判题 + 解析
    console.log('选择题 / 数值题');
    const ch = seedFor('cnm_221', (q) => q.type === 'choice');
    await goto(BASE + '/diagnose/');
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/?target=cnm_221&seed=' + ch.seed);
    await waitFor(() => exists('#choices'), '选择题出题页');
    check((await evalJs('document.querySelector("#q-text").textContent')) === ch.q.prompt, '固定 seed 出的是预期的题（' + ch.q.id + '）');
    check((await evalJs('document.querySelectorAll("#choices .choice").length')) === ch.q.choices.length, '渲染了 ' + ch.q.choices.length + ' 个选项');
    const wrongKey = ch.q.choices.find((c) => c.key !== ch.q.answer).key;
    await click('#choice-' + wrongKey);
    await click('#btn-submit');
    await waitFor(() => exists('.verdict'), '选择题判定');
    check((await evalJs('document.querySelector(".verdict").textContent')).includes('不正确'), '选错的选项被判为不正确');
    check((await evalJs('document.querySelector("#explain").textContent')).includes(ch.q.explanation), '自动判题后也显示解析');
    check((await evalJs('document.querySelector(".refans").textContent')).includes(ch.q.answer + '.'), '显示参考答案（含选项文字）');
    await click('#btn-flip');
    // 默认每知识点需连续答对 3 题才掌握：改判为对后继续本知识点下一题，而不是直接结束
    await waitFor(() => evalJs('!!document.querySelector(".q-text") && !document.querySelector("#summary")'), '改判为对后继续本知识点下一题');
    check((await evalJs('JSON.parse(localStorage.getItem("cnmDiagnose.session.v2")).answers[0].result')) === 'correct', '「判错了，我其实做对了」可更正为对');
    check((await evalJs('Array.from(document.querySelectorAll(".tag")).some(e => /本知识点第 2/.test(e.textContent))')), '改判为对后进入本知识点第 2 题');

    // 找一个答案是分数 / 负数的数值题，用全角写法作答
    let nu = null, nuTopic = null;
    for (const t of GRAPH.topics) {
      if (t.external) continue;
      try { nu = seedFor(t.id, (q) => q.type === 'numeric' && /^-?\d+\/\d+$|^-\d+$/.test(q.answer)); nuTopic = t.id; break; } catch (e) { /* 换一个知识点 */ }
    }
    await goto(BASE + '/diagnose/');
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/?target=' + nuTopic + '&seed=' + nu.seed);
    await waitFor(() => exists('#ans'), '数值题出题页');
    const typed = nu.q.answer;
    await evalJs('(() => { const i = document.getElementById("ans"); i.value = ' + JSON.stringify(typed.replace(/[0-9]/g, (d) => String.fromCharCode(d.charCodeAt(0) + 0xFEE0)).replace('-', '－').replace('/', '／')) + '; i.dispatchEvent(new Event("input", {bubbles:true})); })()');
    await click('#btn-submit');
    await waitFor(() => exists('.verdict'), '数值题自动判定');
    check((await evalJs('document.querySelector(".verdict").textContent')).includes('正确'), '数值题自动判题：全角写法的「' + typed + '」被判为正确（' + nu.q.id + '）');
    await shot('05-explanation.png');

    // 截图（演示模式）
    console.log('截图');
    await goto(BASE + '/diagnose/');
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('#target-list .topic-row'), '开始页');
    await shot('01-start.png');
    await goto(BASE + '/diagnose/?target=cnm_221&demo=1&step=2');
    await waitFor(() => exists('.q-text'), '演示出题页');
    await shot('02-question.png');
    await goto(BASE + '/diagnose/?target=cnm_221&demo=1');
    await waitFor(() => exists('#summary'), '演示结果页');
    check(await exists('#roots details.topic'), '演示模式到达结果页并有根因');
    const stat = (cls) => evalJs('parseInt(document.querySelector("#summary .stat.' + cls + ' b").textContent, 10)');
    check((await stat('ok')) > 0 && (await stat('shaky')) > 0 && (await stat('bad')) > 0,
      '演示模式同时出现 掌握（' + await stat('ok') + '）/ 不稳（' + await stat('shaky') + '）/ 薄弱（' + await stat('bad') + '）三种状态');
    check(await exists('#shaky details.topic') && await exists('#path .tag.shaky'), '「不稳」的点单独列出，并出现在学习路径里');
    await shot('03-result.png');
    const iqResult = await evalJs(IQ_RESULT_EXPR);
    check(iqResult === 'ok', '诊断结果页底部有儿童智商测试入口（' + iqResult + '）');
    await shot('37-result-iq.png', '#iq-line', 160);
    await checkPathGraph('演示结果页');
    // 路径图单独存一张便于检查
    await shot('04-graph.png', '#graph', 720);

    // 整章目标（URL 参数 chapter）+ 数值题自动判题
    await goto(BASE + '/diagnose/?chapter=' + encodeURIComponent('七上 第一章') + '&demo=1');
    await waitFor(() => exists('#summary'), '整章演示结果页');
    check((await evalJs('document.querySelector("#summary h2").textContent')).includes('整章'), '整章作为目标（?chapter=七上 第一章）可诊断');

    console.log('首页 / 知识图谱');
    await setView(1280, 900);
    await goto(BASE + '/');
    await waitFor(() => evalJs('document.getElementById("n-topics") && document.getElementById("n-topics").textContent !== "…" && document.querySelectorAll("a.grade-card").length === ' + N_GRADE_CARDS), '首页统计');
    const stats = await evalJs('[document.getElementById("n-topics").textContent, document.getElementById("n-edges").textContent, document.getElementById("n-questions").textContent, document.getElementById("n-subjects").textContent].join(",")');
    check(stats === HOME_STATS.join(','), '首页统计来自数据文件（' + stats + '）');
    check(!(await evalJs('document.body.innerText')).includes('未经教师审核') && !(await evalJs('document.title')).includes('草稿'), '页脚不含初稿声明，标题不含「草稿」');
    check((await evalJs('document.querySelector("a.grade-card").getAttribute("href")')) === 'explore/?grade=1', '一年级卡片指向知识图谱');
    const iqHome = await evalJs(IQ_HOME_EXPR);
    check(iqHome === 'ok', '首页儿童智商测试卡片（' + iqHome + '）');
    await checkBanner('首页 1280');
    await checkPage('首页 1280');
    await shot('06-home.png', null, 1900);
    await shot('36-home-iq.png', 'a.iq-card', 280);
    await shot('41-top-banner.png', null, 280);

    const checkExplore = async (id, expect) => {
      await goto(BASE + '/explore/#' + encodeURIComponent(id));
      await waitFor(() => evalJs('document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1"'), '局部图 ' + id, 20000);
      const info = await evalJs(EXPLORE_GRAPH_EXPR);
      check(info.ready !== 'err' && info.nodes > 1 && info.nodes < 80, id + ' 局部图渲染了 ' + info.nodes + ' 个节点（不是全图 ' + N_TOPICS + '）');
      check(info.primary + info.junior + info.senior === info.nodes, id + ' 节点按学段着色（小学 ' + info.primary + '，初中 ' + info.junior + '，高中 ' + info.senior + '）');
      check(info.meta.indexOf('向上 2 层') >= 0, id + ' 图注含「向上 2 层」（' + info.meta + '）');
      check(info.hash === '#' + id, id + ' 地址栏哈希保持为 ' + info.hash);
      check(info.title.indexOf(expect.title) >= 0 && info.idCode === expect.idCode, id + ' 详情是「' + info.title + '」' + info.idCode);
      check(info.diag.indexOf('target=' + encodeURIComponent(expect.diag)) >= 0, id + ' 诊断按钮指向 ' + expect.diag);
      check(info.current === 1, id + ' 当前节点已高亮');
      if (expect.alias) check(info.alias.indexOf(expect.alias) >= 0 && info.alias.indexOf(id) >= 0, id + ' 显示旧编号说明');
      if (info.hardN) check(info.hard === 'solid', id + ' 硬先修为实线');
      if (info.softN) check(info.soft === 'dashed', id + ' 软先修为虚线（' + info.softN + ' 条）');
      check(info.wrap === 'ellipsis' && info.tall === 0 && info.spill === 0 && info.uncut === 0 && info.overlap === 0,
        id + ' 标签单行省略且不重叠（未截断 ' + info.uncut + '，溢出 ' + info.spill + '，重叠 ' + info.overlap + '，过高 ' + info.tall + '）');
      await checkPage('图谱 ' + id + ' ' + viewW);
      return info;
    };

    await checkExplore('cnm_221', { title: '配方法', idCode: 'cnm_221', diag: 'cnm_221' });
    await checkBanner('图谱 1280');
    await shot('07-explore-221.png');
    await checkExplore('cnm_p001', { title: '1到5', idCode: 'cnm_p001', diag: 'cnm_p001' });
    await shot('08-explore-p001.png');
    await checkExplore('cnm_ext_002', { title: '分数的意义', idCode: 'cnm_p165', diag: 'cnm_p165', alias: '分数的意义与四则运算' });
    await shot('09-explore-ext002.png');

    await goto(BASE + '/#cnm_219');
    await waitFor(() => evalJs('location.pathname.indexOf("/explore/") >= 0 && location.hash === "#cnm_219" && document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1"'), '根路径 #cnm_219', 20000);
    check((await evalJs('(document.querySelector(".id-code") || {}).textContent')) === 'cnm_219', '根路径 #cnm_219 仍定位到该知识点');
    await checkPage('根路径 #cnm_219');
    await shot('16-explore-219.png');

    console.log('全部祖先');
    await goto(BASE + '/explore/#cnm_234');
    await waitFor(() => evalJs('document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1"'), 'cnm_234 局部图', 20000);
    await click('#depth-switch [data-depth="all"]');
    await waitFor(() => evalJs('document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1" && document.getElementById("cy").dataset.mode === "grade"'), '全部祖先收起', 20000);
    const folded = await evalJs(EXPLORE_GRAPH_EXPR);
    const foldTotal = await evalJs('document.getElementById("cy").dataset.total');
    const foldBtn = await evalJs('(document.getElementById("btn-expand-all") || {}).textContent || ""');
    check(Number(foldTotal) > 40 && folded.nodes <= 40 && folded.nodes > 1, '全部祖先默认收起（画出 ' + folded.nodes + ' / 共 ' + foldTotal + '）');
    check(folded.grades >= 2 && folded.primary > 0 && folded.junior > 0, '收起后按年级分组，小学和初中都在（年级节点 ' + folded.grades + '）');
    check(foldBtn === '共 ' + foldTotal + ' 个，点此展开全部', '收起提示为「' + foldBtn + '」');
    check(folded.wrap === 'ellipsis' && folded.overlap === 0 && folded.spill === 0, '收起图标签不重叠');
    if (folded.hardN) check(folded.hard === 'solid', '收起图硬先修为实线');
    if (folded.softN) check(folded.soft === 'dashed', '收起图软先修为虚线');
    await checkPage('全部祖先收起');
    await shot('17-explore-all.png');
    const expandStarted = Date.now();
    await click('#btn-expand-all');
    await waitFor(() => evalJs('document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1" && document.getElementById("cy").dataset.mode === "full"'), '全部祖先展开', 20000);
    const expandMs = Date.now() - expandStarted;
    const opened = await evalJs(EXPLORE_GRAPH_EXPR);
    check(opened.nodes === Number(foldTotal) && opened.nodes > 40, '展开后画出全部 ' + opened.nodes + ' 个知识点');
    check(expandMs < 8000, '展开布局耗时 ' + expandMs + ' ms');
    check(opened.overlap === 0 && opened.spill === 0 && opened.tall === 0, '展开后节点不重叠、标签不溢出');
    check((opened.meta || '').indexOf('已对准当前知识点') >= 0, '大图展开后说明已对准当前知识点');
    const visible = await evalJs('(() => { const cy = window.__cy; const node = cy.getElementById("cnm_234"); const r = node.renderedBoundingBox(); const w = cy.width(), h = cy.height(); let colored = 0; document.querySelectorAll("#cy canvas").forEach(function (c) { const ctx = c.getContext("2d"); if (!ctx || !c.width || !c.height) return; const data = ctx.getImageData(0, 0, c.width, c.height).data; const step = 4; for (let y = 0; y < c.height; y += step) { for (let x = 0; x < c.width; x += step) { const i = (y * c.width + x) * 4; const R = data[i], G = data[i + 1], B = data[i + 2], A = data[i + 3]; if (A > 20 && (R < 240 || G < 240 || B < 240)) colored++; } } }); return { h: Math.round(r.h), w: Math.round(r.w), colored: colored, zoom: cy.zoom(), inside: r.x2 > 8 && r.x1 < w - 8 && r.y2 > 8 && r.y1 < h - 8 }; })()');
    check(visible.inside && visible.h >= 24 && visible.colored > 80, '展开后当前节点可读且画布有内容（高 ' + visible.h + '，着色采样 ' + visible.colored + '，缩放 ' + visible.zoom.toFixed(2) + '）');
    const cyBox = await evalJs('(() => { const r = document.getElementById("cy").getBoundingClientRect(); return { x: Math.max(0, Math.floor(r.x)), y: Math.max(0, Math.floor(r.y)), w: Math.round(r.width), h: Math.round(r.height) }; })()');
    await shot('18-explore-all-open.png', null, null, { beyond: false });
    const ink = pngInk(path.join(OUT, '18-explore-all-open.png'), cyBox);
    check(ink.orange > 40 && ink.blue > 40, '展开截图画布里能看见节点（蓝 ' + ink.blue + '，橙 ' + ink.orange + '，区域 ' + cyBox.x + ',' + cyBox.y + ' ' + cyBox.w + '×' + cyBox.h + '）');
    const zoomBefore = await evalJs('window.__cy.zoom()');
    await click('#btn-zoom-in');
    const zoomAfter = await evalJs('window.__cy.zoom()');
    check(zoomAfter > zoomBefore, '展开后仍可缩放（' + zoomBefore.toFixed(3) + ' → ' + zoomAfter.toFixed(3) + '）');
    await click('#btn-fit');
    const fitted = await evalJs('(() => { const cy = window.__cy; const r = cy.getElementById("cnm_234").renderedBoundingBox(); return { zoom: cy.zoom(), h: r.h }; })()');
    check(fitted.zoom >= 0.45 && fitted.h >= 12, '适配画面后节点不缩成点（缩放 ' + fitted.zoom.toFixed(3) + '，高 ' + Math.round(fitted.h) + '）');
    await evalJs('sessionStorage.setItem("cnmExplore.depth","2")');

    console.log('窄屏 375');
    await setView(375, 812);
    await goto(BASE + '/');
    await waitFor(() => evalJs('document.getElementById("n-topics") && document.getElementById("n-topics").textContent === ' + JSON.stringify(HOME_STATS[0])), '首页 375');
    check((await evalJs(IQ_HOME_EXPR)) === 'ok', '375 首页儿童智商测试卡片');
    await checkBanner('首页 375');
    await checkPage('首页 375');
    await shot('10-home-375.png', null, 2900);
    await shot('42-top-banner-375.png', null, 420);
    await checkExplore('cnm_221', { title: '配方法', idCode: 'cnm_221', diag: 'cnm_221' });
    await checkBanner('图谱 375');
    await shot('11-explore-221-375.png', null, 1100);
    await checkExplore('cnm_p001', { title: '1到5', idCode: 'cnm_p001', diag: 'cnm_p001' });
    await shot('12-explore-p001-375.png', null, 1100);
    await checkExplore('cnm_ext_002', { title: '分数的意义', idCode: 'cnm_p165', diag: 'cnm_p165', alias: '分数的意义与四则运算' });
    await shot('13-explore-ext002-375.png', null, 1100);
    await evalJs('sessionStorage.setItem("cnmExplore.depth","2")');
    await goto(BASE + '/explore/#cnm_124');
    await waitFor(() => evalJs('document.getElementById("cy") && document.getElementById("cy").dataset.ready === "1" && document.querySelector(".id-code") && document.querySelector(".id-code").textContent === "cnm_124"'), '长名称 375', 20000);
    const longName = '全等判定：角边角（ASA）与角角边（AAS）';
    const longInfo = await evalJs('(() => { const cy = window.__cy; const node = cy.getElementById("cnm_124"); node.emit("mouseover"); const tip = document.getElementById("node-tip"); const base = ' + EXPLORE_GRAPH_EXPR + '; return Object.assign(base, { tip: tip && !tip.hidden ? tip.textContent : "", label: node.data("label"), name: node.data("name"), hidden: !tip || tip.hidden }); })()');
    check(longInfo.name === longName && longInfo.tip === longName, '375 宽悬停显示全名（' + longInfo.tip + '）');
    check(Array.from(longInfo.label).length <= 8 && longInfo.label.endsWith('…'), '375 宽长名称已省略（' + longInfo.label + '）');
    check(longInfo.spill === 0 && longInfo.overlap === 0 && longInfo.tall === 0, '375 宽长名称不折行、不溢出、不重叠');
    await checkPage('长名称 375');
    await shot('19-longname-375.png', '.graph-pane', 760);
    await goto(BASE + '/diagnose/?target=cnm_221&demo=1');
    await waitFor(() => exists('#summary'), '诊断结果页 375');
    check((await evalJs(IQ_RESULT_EXPR)) === 'ok', '375 诊断结果页底部有儿童智商测试入口');
    await checkBanner('诊断结果 375');
    await checkPathGraph('375 结果页');
    const choiceH = await evalJs('(() => { const b = document.querySelector("button"); return b ? b.getBoundingClientRect().height : 0; })()');
    check(choiceH >= 44, '按钮触控高度 ≥ 44px（' + Math.round(choiceH) + '）');
    await checkPage('诊断结果 375');
    await shot('14-diagnose-375.png', null, 1100);
    await shot('20-diagnose-graph-375.png', '#graph', 720);
    await goto(BASE + '/diagnose/');
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('#search'), '诊断开始页 375');
    await checkPage('诊断开始页 375');
    await shot('15-start-375.png', null, 900);

    console.log('高中');
    await setView(1280, 900);
    const hsInfo = await checkExplore('cnm_h027', { title: '函数的概念', idCode: 'cnm_h027', diag: 'cnm_h027' });
    check(hsInfo.senior > 0 && hsInfo.junior > 0, '高中「函数的概念」局部图同时有高中和初中节点');
    check(await evalJs('!!document.querySelector(".legend .sw-h")'), '知识图谱图例有高中');
    check((await evalJs('document.querySelector(".pill").textContent')) === '高中', '详情学段标为高中');
    await shot('21-explore-h027.png');
    await goto(BASE + '/diagnose/?target=cnm_h027&demo=1');
    await waitFor(() => exists('#summary'), '高中函数概念诊断结果');
    const hsPath = await checkPathGraph('高中函数概念');
    check(hsPath.senior > 0 && hsPath.junior > 0, '高中诊断路径图含高中和初中节点');
    check(await evalJs('!!document.querySelector(".legend .sw-h")'), '诊断图例有高中');
    await shot('23-diagnose-h027.png', null, 1400);
    await shot('24-diagnose-h027-graph.png', '#graph', 720);
    await goto(BASE + '/diagnose/?grade=' + encodeURIComponent('高一') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '高一整体诊断', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).includes('高一'), '高一（必修第一册）整体诊断');
    check(await exists('#chapters .chap-sum'), '高一整体诊断有按章汇总');
    await checkPage('高一整体诊断 1280');
    await shot('25-diagnose-gaoyi.png', '#summary', 900);
    await setView(375, 812);
    await checkExplore('cnm_h027', { title: '函数的概念', idCode: 'cnm_h027', diag: 'cnm_h027' });
    await shot('22-explore-h027-375.png', null, 1100);
    await goto(BASE + '/diagnose/?target=cnm_h027&demo=1');
    await waitFor(() => exists('#summary'), '高中诊断结果 375');
    await checkPathGraph('高中函数概念 375');
    await checkPage('高中诊断 375');
    await shot('26-diagnose-h027-375.png', null, 1100);
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('#grade-card'), '诊断开始页年级卡');
    await evalJs('(() => { const b = Array.from(document.querySelectorAll("#grade-card .stage-tab")).find((x) => x.textContent === "高二"); if (!b) throw new Error("没有高二"); b.click(); })()');
    check((await evalJs('document.getElementById("grade-info").textContent')).indexOf('高二（必修第二册）') >= 0, '高二卡片显示必修第二册');
    check(await evalJs('!Array.from(document.querySelectorAll("#grade-card .stage-tab")).some((b) => b.textContent === "上册" || b.textContent === "下册")'), '高中整体诊断不提供上下册');
    await checkPage('高二诊断开始 375');
    await shot('27-diagnose-gaoer-375.png', '#grade-card', 520);

    console.log('选择性必修');
    if (!DERIVE) throw new Error('找不到「导数的概念」');
    await setView(1280, 900);
    const derInfo = await checkExplore(DERIVE.id, { title: '导数的概念', idCode: DERIVE.id, diag: DERIVE.id });
    check(derInfo.senior > 0, '「导数的概念」局部图含高中节点');
    check((await evalJs('document.body.innerText')).indexOf('选必二 · 选择性必修第二册') >= 0, '导数页标明选择性必修第二册');
    await shot('28-explore-der.png');
    await goto(BASE + '/diagnose/?grade=' + encodeURIComponent('选必二') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '选必二整体诊断', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('选必二') >= 0, '选必二（选择性必修第二册）整体诊断');
    check(await exists('#chapters .chap-sum'), '选必二整体诊断有按章汇总');
    await checkPage('选必二整体诊断 1280');
    await shot('30-diagnose-xuanbi2.png', '#summary', 900);
    await setView(375, 812);
    await checkExplore(DERIVE.id, { title: '导数的概念', idCode: DERIVE.id, diag: DERIVE.id });
    check((await evalJs('document.body.innerText')).indexOf('选择性必修第二册') >= 0, '375 导数页仍标明选必二');
    await checkPage('导数概念 375');
    await shot('29-explore-der-375.png', null, 1100);
    await goto(BASE + '/diagnose/?grade=' + encodeURIComponent('选必二') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '选必二整体诊断 375', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('选择性必修第二册') >= 0, '375 选必二整体诊断');
    await checkPage('选必二整体诊断 375');
    await shot('31-diagnose-xuanbi2-375.png', null, 1100);
    await evalJs('localStorage.clear()');
    await goto(BASE + '/diagnose/');
    await waitFor(() => exists('#grade-card'), '诊断开始页选必二');
    await evalJs('(() => { const b = Array.from(document.querySelectorAll("#grade-card .stage-tab")).find((x) => x.textContent === "选必二"); if (!b) throw new Error("没有选必二"); b.click(); })()');
    check((await evalJs('document.getElementById("grade-info").textContent')).indexOf('选必二（选择性必修第二册）') >= 0, '选必二卡片显示选择性必修第二册');
    check(await evalJs('!Array.from(document.querySelectorAll("#grade-card .stage-tab")).some((b) => b.textContent === "上册" || b.textContent === "下册")'), '选必二整体诊断不提供上下册');
    check(await evalJs('Array.from(document.querySelectorAll("#grade-card .stage-tab")).some((b) => b.textContent === "整册")'), '选必二范围是整册');

    console.log('小学英语');
    const ing = TOPIC_ROWS.find((t) => String(t.name).indexOf('现在进行时') >= 0 && String(t.id).startsWith('cne_p'));
    if (!ing) throw new Error('找不到「现在进行时」');
    await setView(1280, 900);
    const ingInfo = await checkExplore(ing.id, { title: '现在进行时', idCode: ing.id, diag: ing.id });
    check(String(ing.id).startsWith('cne_p'), '现在进行时示例仍是小学节点');
    check(ingInfo.primary > 0 && ingInfo.junior >= 1 && ingInfo.senior === 0, '现在进行时局部图以小学为主，并连到初中后续（小学 ' + ingInfo.primary + '，初中 ' + ingInfo.junior + '）');
    check((await evalJs('location.search')).indexOf('subject=english') >= 0, '英语知识点自动带上 subject=english');
    check((await evalJs('document.querySelector("a.diag-btn").getAttribute("href")')).indexOf('subject=english') >= 0, '英语诊断按钮带上学科');
    await checkBanner('英语图谱 1280');
    const switchH = await evalJs('(() => { const a = document.querySelector(".subject-link"); return a ? a.getBoundingClientRect().height : 0; })()');
    check(switchH >= 44, '学科切换触控高度 ≥ 44px（' + Math.round(switchH) + '）');
    await shot('32-explore-ing.png');
    await setView(375, 812);
    await checkExplore(ing.id, { title: '现在进行时', idCode: ing.id, diag: ing.id });
    await checkBanner('英语图谱 375');
    await checkPage('现在进行时 375');
    await shot('33-explore-ing-375.png', null, 1100);
    await setView(1280, 900);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('四上') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '四年级上册英语整体诊断', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('四年级上册') >= 0, '四年级上册英语整体诊断标题');
    check((await evalJs(IQ_RESULT_EXPR)) === 'ok', '英语诊断结果页也有儿童智商测试入口');
    await checkBanner('英语诊断 1280');
    check(await exists('#chapters .chap-sum'), '四年级上册英语整体诊断有按章汇总');
    check((await evalJs('document.body.innerText')).indexOf('配方法') < 0, '英语整册诊断不混入数学知识点');
    await checkPage('四年级上册英语 1280');
    await shot('34-diagnose-en-g4.png', '#summary', 900);
    await setView(375, 812);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('四上') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '四年级上册英语整体诊断 375', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('四年级上册') >= 0, '375 四年级上册英语整体诊断');
    await checkBanner('英语诊断 375');
    await checkPage('四年级上册英语 375');
    await shot('35-diagnose-en-g4-375.png', null, 1100);

    console.log('初中英语');
    const perfect = TOPIC_ROWS.find((t) => t.name === '现在完成时' && String(t.id).startsWith('cne_j'));
    if (!perfect) throw new Error('找不到「现在完成时」');
    await setView(1280, 900);
    const perfInfo = await checkExplore(perfect.id, { title: '现在完成时', idCode: perfect.id, diag: perfect.id });
    check(perfInfo.junior > 0, '现在完成时局部图含初中节点（初中 ' + perfInfo.junior + '，高中 ' + perfInfo.senior + '）');
    const stageTabs = await evalJs('Array.from(document.querySelectorAll("#stage-tabs [data-stage]:not([hidden])")).map((b) => b.textContent).join(",")');
    check(stageTabs === '全部,小学,初中,高中', '英语图谱学段是全部/小学/初中/高中（' + stageTabs + '）');
    const gradeOpts = await evalJs('Array.from(document.querySelectorAll("#fGrade option")).map((o) => o.textContent).join(",")');
    check(gradeOpts.indexOf('九年级') >= 0 && gradeOpts.indexOf('高一') < 0 && gradeOpts.indexOf('一年级') < 0 && gradeOpts.indexOf('必修第一册') >= 0 && gradeOpts.indexOf('选择性必修第四册') >= 0, '英语年级从三年级筛到高中，不用「高一」（' + gradeOpts + '）');
    const legendH = await evalJs('(() => { const li = document.querySelector(".legend li:has(.sw-h)"); if (!li) return "missing"; return getComputedStyle(li).display; })()');
    const legendJ = await evalJs('(() => { const li = document.querySelector(".legend li:has(.sw-j)"); if (!li) return "missing"; return getComputedStyle(li).display; })()');
    check(legendH !== 'none' && legendH !== 'missing' && legendJ !== 'none', '英语图谱图例同时保留初中和高中（初中 ' + legendJ + '，高中 ' + legendH + '）');
    await shot('43-explore-perfect.png');
    await setView(375, 812);
    await checkExplore(perfect.id, { title: '现在完成时', idCode: perfect.id, diag: perfect.id });
    await checkPage('现在完成时 375');
    await shot('44-explore-perfect-375.png', null, 1100);
    await setView(1280, 900);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('八上') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '八年级上册英语整体诊断', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('八年级上册') >= 0, '八年级上册英语整体诊断标题');
    check((await evalJs(IQ_RESULT_EXPR)) === 'ok', '初中英语诊断结果页也有儿童智商测试入口');
    await checkBanner('初中英语诊断 1280');
    check(await exists('#chapters .chap-sum'), '八年级上册英语整体诊断有按章汇总');
    check((await evalJs('document.body.innerText')).indexOf('配方法') < 0, '初中英语整册诊断不混入数学知识点');
    check((await evalJs('document.body.innerText')).indexOf('小学、初中和高中用不同颜色') >= 0, '英语结果页图例说明含小学、初中和高中');
    await checkPage('八年级上册英语 1280');
    await shot('45-diagnose-en-g8.png', '#summary', 900);
    await setView(375, 812);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('八上') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '八年级上册英语整体诊断 375', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('八年级上册') >= 0, '375 八年级上册英语整体诊断');
    await checkBanner('初中英语诊断 375');
    await checkPage('八年级上册英语 375');
    await shot('46-diagnose-en-g8-375.png', null, 1100);

    console.log('高中英语');
    const subj = TOPIC_ROWS.find((t) => t.name === '虚拟语气' && String(t.id).startsWith('cne_h'));
    if (!subj) throw new Error('找不到「虚拟语气」');
    await setView(1280, 900);
    const subInfo = await checkExplore(subj.id, { title: '虚拟语气', idCode: subj.id, diag: subj.id });
    check(subInfo.senior > 0 && subInfo.junior > 0, '虚拟语气局部图含高中和初中（高中 ' + subInfo.senior + '，初中 ' + subInfo.junior + '）');
    check((await evalJs('document.body.innerText')).indexOf('高一') < 0, '虚拟语气页不把英语册次写成高一');
    check((await evalJs('document.body.innerText')).indexOf('选择性必修第二册') >= 0, '虚拟语气页写明选择性必修第二册');
    await checkPage('虚拟语气 1280');
    await shot('51-explore-subjunctive.png');
    await setView(375, 812);
    await checkExplore(subj.id, { title: '虚拟语气', idCode: subj.id, diag: subj.id });
    await checkPage('虚拟语气 375');
    await shot('52-explore-subjunctive-375.png', null, 1100);
    await setView(1280, 900);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('选必一') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '选择性必修第一册英语整体诊断', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('选必一') >= 0, '选必一英语整体诊断标题');
    check((await evalJs('document.body.innerText')).indexOf('配方法') < 0, '高中英语整册诊断不混入数学知识点');
    check((await evalJs('document.body.innerText')).indexOf('People of Achievement') >= 0, '选必一诊断按单元汇总');
    check(await evalJs('!Array.from(document.querySelectorAll("#grade-card .stage-tab")).some((b) => b.textContent === "上册" || b.textContent === "下册")'), '选必一英语不提供上下册');
    await checkPage('选必一英语 1280');
    await shot('53-diagnose-en-xuanbi1.png', '#summary', 900);
    await setView(375, 812);
    await goto(BASE + '/diagnose/?subject=english&grade=' + encodeURIComponent('选必一') + '&demo=1&limit=12');
    await waitFor(() => exists('#chapters'), '选择性必修第一册英语整体诊断 375', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('选必一') >= 0, '375 选必一英语整体诊断');
    await checkPage('选必一英语 375');
    await shot('54-diagnose-en-xuanbi1-375.png', null, 1100);

    console.log('分享图');
    const shareUi = () => evalJs(`(() => {
      const img = document.getElementById('share-preview');
      const dl = document.getElementById('share-download');
      const hint = document.getElementById('share-hint');
      const visible = (el) => !!(el && el.getClientRects().length);
      return {
        tag: img ? img.tagName : '',
        src: img && img.src ? img.src.slice(0, 5) : '',
        w: img ? img.naturalWidth : 0,
        h: img ? img.naturalHeight : 0,
        download: visible(dl),
        downloadName: dl ? (dl.getAttribute('download') || '') : '',
        hint: visible(hint),
        hintText: hint ? (hint.textContent || '').trim() : ''
      };
    })()`);
    const saveShareImage = async (file) => {
      await waitFor(() => evalJs('(() => { const img = document.getElementById("share-preview"); return !!(img && img.complete && img.naturalWidth === 1080 && img.naturalHeight === 1920); })()'), '分享图尺寸 ' + file, 10000);
      const b64 = await evalJs(`(async () => {
        const img = document.getElementById('share-preview');
        const blob = await (await fetch(img.src)).blob();
        const bytes = new Uint8Array(await blob.arrayBuffer());
        let binary = '';
        const chunk = 0x4000;
        for (let i = 0; i < bytes.length; i += chunk) {
          binary += String.fromCharCode.apply(null, bytes.subarray(i, Math.min(i + chunk, bytes.length)));
        }
        return btoa(binary);
      })()`);
      fs.writeFileSync(path.join(OUT, file), Buffer.from(b64, 'base64'));
      console.log('  分享图 screenshots/' + file);
    };
    const assertSharePng = (file) => {
      const img = pngRgba(path.join(OUT, file));
      check(img.width === 1080 && img.height === 1920, file + ' 是 1080×1920');
      const px = pngPixel(img, 80, 40);
      check(px[0] < 80 && px[1] > 80 && px[1] < 170 && px[2] > 70 && px[2] < 160, file + ' 页头是站点青色');
      const decoded = decodeQr(img);
      check(decoded === SHARE_URL, file + ' 二维码内容是分享链接（' + decoded + '）');
    };

    await setView(1280, 900);
    await goto(BASE + '/diagnose/?grade=' + encodeURIComponent('五上') + '&demo=1');
    await waitFor(() => exists('#btn-share'), '数学结果页分享按钮', 20000);
    check((await evalJs('document.getElementById("btn-share").textContent')) === '生成分享图', '按钮文案是生成分享图');
    const qrSrc = await evalJs(`document.querySelector('script[src$="qrcode.js"]').getAttribute('src')`);
    check(qrSrc === '../assets/vendor/qrcode.js', '二维码脚本是本地相对路径（' + qrSrc + '）');
    await checkPage('数学分享结果页 1280');
    await click('#btn-share');
    await waitFor(() => exists('#share-preview'), '数学分享弹层', 10000);
    const mathUi = await shareUi();
    check(mathUi.tag === 'IMG', '桌面预览是 img');
    check(mathUi.src === 'blob:' || mathUi.src === 'data:', '桌面预览地址可长按保存（' + mathUi.src + '）');
    check(mathUi.download && mathUi.downloadName === '知识图谱诊断分享.png', '1280 宽显示下载图片');
    check(!mathUi.hint, '1280 宽不提示长按保存');
    const mathModel = await evalJs('window.__shareModel');
    check(mathModel && mathModel.siteName === '中小学·高中知识图谱' && mathModel.subject === '数学' && String(mathModel.scope).indexOf('五年级上册') >= 0 && mathModel.spotKind === 'chapter', '数学分享范围是五年级上册（' + JSON.stringify(mathModel && { scope: mathModel.scope, subject: mathModel.subject, spotKind: mathModel.spotKind }) + '）');
    check(mathModel && mathModel.spots.length >= 1 && mathModel.spots.length <= 3, '数学分享列出 1–3 个章节');
    check(mathModel && mathModel.roots.length >= 1 && mathModel.roots.length <= 2, '数学分享有 1–2 个根因');
    check(JSON.stringify(mathModel).indexOf('付费') < 0 && JSON.stringify(mathModel).indexOf('姓名') < 0, '分享内容不含付费或姓名');
    await saveShareImage('38-share-math.png');
    assertSharePng('38-share-math.png');

    await setView(375, 812);
    await sleep(200);
    const phoneUi = await shareUi();
    check(phoneUi.tag === 'IMG' && (phoneUi.src === 'blob:' || phoneUi.src === 'data:'), '375 预览仍是可保存的 img');
    check(!phoneUi.download, '375 宽隐藏下载图片');
    check(phoneUi.hint && phoneUi.hintText === '长按图片保存', '375 宽提示长按图片保存（' + phoneUi.hintText + '）');
    await checkPage('分享弹层 375');
    await shot('40-share-modal-375.png', null, 812, { beyond: false });

    await setView(1280, 900);
    await goto(BASE + '/diagnose/?subject=english&target=cne_p148&demo=1');
    await waitFor(() => exists('#btn-share'), '英语结果页分享按钮', 20000);
    check((await evalJs('document.querySelector("#summary h2").textContent')).indexOf('现在进行时') >= 0, '英语现在进行时结果页');
    await checkPage('英语分享结果页 1280');
    await click('#btn-share');
    await waitFor(() => exists('#share-preview'), '英语分享弹层', 10000);
    const enModel = await evalJs('window.__shareModel');
    check(enModel && enModel.subject === '英语' && String(enModel.scope).indexOf('现在进行时') >= 0 && enModel.spotKind === 'topic', '英语分享范围是现在进行时（' + JSON.stringify(enModel && { scope: enModel.scope, subject: enModel.subject, spotKind: enModel.spotKind, spots: (enModel.spots || []).length, roots: (enModel.roots || []).length }) + '）');
    check(enModel && enModel.spots.length >= 1 && enModel.spots.length <= 3 && enModel.roots.length >= 1 && enModel.roots.length <= 2, '英语分享薄弱项 1–3 个、根因 1–2 个');
    const enDesk = await shareUi();
    check(enDesk.download && !enDesk.hint, '英语分享弹层在 1280 宽可下载');
    await saveShareImage('39-share-en.png');
    assertSharePng('39-share-en.png');
    await setView(375, 812);
    await sleep(120);
    const enPhone = await shareUi();
    check(!enPhone.download && enPhone.hintText === '长按图片保存', '英语分享弹层在 375 宽改为长按保存');
    await checkPage('英语分享弹层 375');
    await setView(1280, 900);

    check(externalReqs.length === 0, '运行时没有页面发起的外网资源请求' + (externalReqs.length ? '：\n       ' + externalReqs.slice(0, 8).join('\n       ') : ''));
    check(errors.length === 0, 'console / 网络无错误' + (errors.length ? '：\n       ' + errors.join('\n       ') : ''));
    if (checks.some((c) => !c[0])) exitCode = 1;
    cdp.ws.close();
  } catch (e) {
    console.error('冒烟测试异常：' + (e && e.stack || e));
    if (dumpPage) { try { console.error('当前页面文字：\n' + await dumpPage()); } catch (e2) { /* ignore */ } }
    if (errors.length) console.error('已捕获的浏览器错误：\n' + errors.join('\n'));
    exitCode = 1;
  } finally {
    chrome.kill('SIGKILL');
    server.kill('SIGKILL');
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) { /* ignore */ }
  }
  console.log(exitCode ? '\n冒烟测试未通过' : '\n冒烟测试通过（' + checks.length + ' 项）');
  process.exit(exitCode);
}

function fetchOk(url) { return fetch(url).then((r) => r.ok, () => false); }

function noteExternal(params, bucket) {
  const initiator = (params.initiator && params.initiator.type) || '';
  if (initiator !== 'parser' && initiator !== 'script') return;
  const url = params.request && params.request.url;
  if (!url || !/^https?:/i.test(url)) return;
  let host = '';
  try { host = new URL(url).hostname; } catch (e) { return; }
  if (host === '127.0.0.1' || host === 'localhost') return;
  const type = params.type || '';
  if (['Script', 'Stylesheet', 'Image', 'Font', 'XHR', 'Fetch', 'Document', 'Other'].indexOf(type) < 0) return;
  const line = type + ' ' + initiator + ' ' + url;
  if (bucket.indexOf(line) < 0) bucket.push(line);
}

const LOCAL_ASSET_EXPR = `(() => {
  const bad = [];
  const local = (raw) => {
    if (!raw || raw.indexOf('data:') === 0 || raw.indexOf('blob:') === 0 || raw.charAt(0) === '#') return true;
    try {
      const u = new URL(raw, location.href);
      return u.protocol === 'data:' || u.protocol === 'blob:' || u.hostname === '127.0.0.1' || u.hostname === 'localhost';
    } catch (e) { return false; }
  };
  document.querySelectorAll('script[src], link[href], img[src], iframe[src], video[src], audio[src], source[src]').forEach((el) => {
    const raw = el.getAttribute('src') || el.getAttribute('href') || '';
    if (!local(raw)) bad.push(el.tagName.toLowerCase() + ' ' + raw);
  });
  Array.from(document.styleSheets).forEach((sheet) => {
    let rules;
    try { rules = sheet.cssRules; } catch (e) { bad.push('stylesheet ' + (sheet.href || 'inline')); return; }
    const walk = (list) => {
      if (!list) return;
      for (const rule of list) {
        if (rule.style) {
          for (let i = 0; i < rule.style.length; i++) {
            const val = rule.style.getPropertyValue(rule.style[i]);
            const re = /url\\(([^)]+)\\)/g;
            let m;
            while ((m = re.exec(val))) {
              const raw = m[1].trim().replace(/^['"]|['"]$/g, '');
              if (!local(raw)) bad.push('css ' + raw);
            }
          }
        }
        if (rule.cssRules) walk(rule.cssRules);
      }
    };
    walk(rules);
  });
  return bad;
})()`;

main();
