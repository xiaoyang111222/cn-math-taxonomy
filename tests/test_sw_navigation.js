#!/usr/bin/env node
/* Service Worker 导航回退：断网/超时时不能把首页内容顶给其它页面。
 * node tests/test_sw_navigation.js（无依赖，用 vm 造假 caches/fetch，不需要浏览器） */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
const ORIGIN = 'http://127.0.0.1:8011';

let passed = 0;

function home() { return html('<title>首页</title><main class="home">home</main>'); }
function children() { return html('<title>儿童档案</title><main class="children">children</main>'); }
function childrenHistory() { return html('<title>历史</title><main class="history">history</main>'); }
function diagnose() { return html('<title>诊断</title><main class="diagnose">diagnose</main>'); }

function html(body) {
  return new Response(body, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}

/* 假 caches：按绝对 URL 存 Response，match 支持 ignoreSearch。 */
function makeHarness(store, scope) {
  const root = scope || ORIGIN + '/';
  const listeners = {};
  const cache = {
    add() { return Promise.resolve(); },
    addAll() { return Promise.resolve(); },
    put() { return Promise.resolve(); },
    match(req, opts) {
      const url = typeof req === 'string' ? req : req.url;
      if (store.has(url)) return Promise.resolve(store.get(url));
      if (opts && opts.ignoreSearch) {
        const base = url.split('?')[0];
        for (const [k, v] of store) if (k.split('?')[0] === base) return Promise.resolve(v);
      }
      return Promise.resolve(undefined);
    }
  };
  const caches = {
    open() { return Promise.resolve(cache); },
    match: cache.match,
    keys() { return Promise.resolve([]); },
    delete() { return Promise.resolve(true); }
  };
  let fetchImpl = () => Promise.reject(new Error('offline'));
  const self = {
    registration: { scope: root },
    location: { origin: new URL(root).origin },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    skipWaiting() { return Promise.resolve(); },
    clients: { claim() { return Promise.resolve(); } }
  };
  const sandbox = {
    self, caches, URL, Response, Request,
    fetch: (req) => fetchImpl(req),
    setTimeout, clearTimeout, console
  };
  vm.createContext(sandbox);
  vm.runInContext(SOURCE, sandbox, { filename: 'sw.js' });
  return {
    setFetch(fn) { fetchImpl = fn; },
    async navigate(url) {
      let responded = null;
      const event = { request: { method: 'GET', mode: 'navigate', url }, respondWith(p) { responded = p; } };
      for (const fn of listeners.fetch || []) fn(event);
      assert.ok(responded, 'fetch 监听器没有 respondWith');
      return responded;
    }
  };
}

function storeOf(entries) {
  const m = new Map();
  for (const [k, v] of entries) m.set(k, v);
  return m;
}

async function test(name, fn) {
  await fn();
  passed++;
  console.log('  ok   ' + name);
}

(async () => {
  await test('断网：/children/index.html 回退同目录缓存壳，不是首页', async () => {
    const h = makeHarness(storeOf([
      [ORIGIN + '/', home()],
      [ORIGIN + '/children/', children()]
    ]));
    const body = await (await h.navigate(ORIGIN + '/children/index.html')).text();
    assert.match(body, /儿童档案/);
    assert.doesNotMatch(body, /class="home"/);
  });

  await test('断网：/explore/index.html 无同类缓存时给离线提示页，不是首页', async () => {
    const h = makeHarness(storeOf([[ORIGIN + '/', home()]]));
    const body = await (await h.navigate(ORIGIN + '/explore/index.html')).text();
    assert.match(body, /暂时打不开这个页面/);
    assert.match(body, /href="http:\/\/127\.0\.0\.1:8011\/explore\/"/);
    assert.doesNotMatch(body, /class="home"/);
  });

  await test('断网：/random-page/ 给离线提示页，不是首页', async () => {
    const h = makeHarness(storeOf([[ORIGIN + '/', home()]]));
    const body = await (await h.navigate(ORIGIN + '/random-page/')).text();
    assert.match(body, /暂时打不开这个页面/);
    assert.doesNotMatch(body, /class="home"/);
  });

  await test('断网：站点根仍然回退缓存首页', async () => {
    const h = makeHarness(storeOf([[ORIGIN + '/', home()]]));
    const body = await (await h.navigate(ORIGIN + '/')).text();
    assert.match(body, /class="home"/);
  });

  await test('断网：根路径也没有缓存时才给离线提示页', async () => {
    const h = makeHarness(storeOf([]));
    const body = await (await h.navigate(ORIGIN + '/')).text();
    assert.match(body, /暂时打不开这个页面/);
  });

  await test('断网：/diagnose/?subject=english 忽略查询串命中缓存页', async () => {
    const h = makeHarness(storeOf([
      [ORIGIN + '/', home()],
      [ORIGIN + '/diagnose/', diagnose()]
    ]));
    const body = await (await h.navigate(ORIGIN + '/diagnose/?subject=english')).text();
    assert.match(body, /class="diagnose"/);
    assert.doesNotMatch(body, /class="home"/);
  });

  await test('断网：缓存的 history.html 按原 URL 命中', async () => {
    const h = makeHarness(storeOf([
      [ORIGIN + '/', home()],
      [ORIGIN + '/children/history.html', childrenHistory()]
    ]));
    const body = await (await h.navigate(ORIGIN + '/children/history.html')).text();
    assert.match(body, /class="history"/);
  });

  await test('在线正常时直接用网络响应，不走回退', async () => {
    const h = makeHarness(storeOf([]));
    h.setFetch(() => Promise.resolve(html('<main class="net">net</main>')));
    const body = await (await h.navigate(ORIGIN + '/explore/')).text();
    assert.match(body, /class="net"/);
    assert.doesNotMatch(body, /暂时打不开/);
  });

  await test('子路径部署时离线提示页的链接按 scope 根拼接', async () => {
    const sub = ORIGIN + '/cn/';
    const h = makeHarness(storeOf([]), sub);
    const body = await (await h.navigate(ORIGIN + '/cn/missing/')).text();
    assert.match(body, /href="http:\/\/127\.0\.0\.1:8011\/cn\/explore\/"/);
    assert.match(body, /href="http:\/\/127\.0\.0\.1:8011\/cn\/diagnose\/"/);
  });

  console.log('\n' + passed + ' passed');
})().catch((e) => {
  console.error('FAILED:', e && e.stack || e);
  process.exit(1);
});
