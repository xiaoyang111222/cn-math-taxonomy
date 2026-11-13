/* 离线缓存：站点壳（页面、脚本、样式、图标）和图谱数据。
 * 页面和脚本：网络优先，断网时用缓存；数据和图标：先用缓存，同时后台更新。
 * 改了 SHELL 或 DATA 列表、或数据结构变了，就把 VERSION 加一。
 * 导航回退：只有站点根路径才回退到缓存首页；其它页面先找同 URL / 同目录的
 * 缓存壳，再不行给一张内联的离线提示页，不拿首页内容顶替别的页面。 */
'use strict';

var VERSION = 'v25';
var CACHE = 'cnm-pwa-' + VERSION;
var SCOPE = self.registration.scope;

var SHELL = [
  './',
  'index.html',
  'explore/',
  'explore/app.js',
  'diagnose/',
  'diagnose/app.js',
  'diagnose/engine.js',
  'diagnose/share.js',
  'diagnose/style.css',
  'children/',
  'children/history.html',
  'children/children.css',
  'children/page.js',
  'children/history.js',
  'assets/site.css',
  'assets/explore.css',
  'assets/home.js',
  'assets/stats-config.js',
  'assets/stats.js',
  'assets/stem-compat.js',
  'assets/children.js',
  'assets/blindspots.js',
  'assets/pwa.js',
  'assets/pwa.css',
  'assets/vendor/cytoscape.min.js',
  'assets/vendor/cytoscape-dagre.js',
  'assets/vendor/dagre.min.js',
  'assets/vendor/qrcode.js',
  'assets/icons/icon-192.png',
  'assets/icons/icon-512.png',
  'assets/icons/apple-touch-icon.png',
  'manifest.webmanifest'
];

var DATA = [
  'data/topics.json',
  'data/dependencies.json',
  'data/cn-curriculum-standards.json',
  'data/questions.json',
  'data/id-aliases.json'
];

function abs(path) { return new URL(path, SCOPE).href; }

function fresh(path) { return new Request(abs(path), { cache: 'reload' }); }

function scopeRootPath() { return new URL('./', SCOPE).pathname; }

/* 内联的离线提示页：不带外链样式，断网时也能看。 */
function offlinePage() {
  var base = new URL('./', SCOPE).href;
  var html = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<title>暂时打不开 · 知识图谱</title></head>' +
    '<body style="margin:0;padding:2rem;font:16px/1.7 system-ui,-apple-system,\'Segoe UI\',sans-serif;color:#123">' +
    '<h1 style="font-size:1.4rem">暂时打不开这个页面</h1>' +
    '<p>网络没有响应，这个页面也没有缓存过。</p>' +
    '<p>先回到：</p>' +
    '<ul>' +
    '<li><a href="' + base + '">首页</a></li>' +
    '<li><a href="' + base + 'explore/">知识图谱</a></li>' +
    '<li><a href="' + base + 'diagnose/">诊断</a></li>' +
    '<li><a href="' + base + 'children/">儿童档案</a></li>' +
    '</ul>' +
    '<p><a href="">重试</a></p>' +
    '</body></html>';
  return new Response(html, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}

self.addEventListener('install', function (event) {
  event.waitUntil((async function () {
    var cache = await caches.open(CACHE);
    // 壳必须齐全；数据尽量缓存，失败不挡安装（之后第一次访问时会补上）
    await cache.addAll(SHELL.map(fresh));
    await Promise.all(DATA.map(function (p) { return cache.add(fresh(p)).catch(function () { /* 稍后运行时再缓存 */ }); }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', function (event) {
  event.waitUntil((async function () {
    var names = await caches.keys();
    await Promise.all(names.filter(function (n) { return n.indexOf('cnm-pwa-') === 0 && n !== CACHE; }).map(function (n) { return caches.delete(n); }));
    await self.clients.claim();
  })());
});

function cacheable(res) {
  return res && res.status === 200 && res.type === 'basic' && !res.redirected;
}

function put(req, res) {
  if (!cacheable(res)) return;
  var copy = res.clone();
  caches.open(CACHE).then(function (c) { return c.put(req, copy); }).catch(function () { /* 空间不足等 */ });
}

function timeout(ms) {
  return new Promise(function (_, reject) { setTimeout(function () { reject(new Error('timeout')); }, ms); });
}

async function networkFirst(req, ignoreSearch) {
  try {
    var res = await Promise.race([fetch(req), timeout(5000)]);
    put(req, res);
    return res;
  } catch (e) {
    var hit = await caches.match(req, { ignoreSearch: ignoreSearch });
    if (hit) return hit;
    // 超时但没有缓存：再等网络
    return fetch(req);
  }
}

async function staleWhileRevalidate(req) {
  var hit = await caches.match(req);
  var update = fetch(req).then(function (res) { put(req, res); return res; });
  if (hit) { update.catch(function () { /* 断网 */ }); return hit; }
  return update;
}

/* 导航（打开页面、刷新、点链接）失败时的回退顺序：
 * 1) 同一 URL 的缓存（忽略查询串，例如 ?subject=english）；
 * 2) 同目录的缓存壳：/children/index.html -> /children/；
 * 3) 只有站点根路径才回退缓存首页；
 * 4) 其余一律返回离线提示页，绝不把首页内容顶给别的页面。 */
async function navigationFallback(req) {
  var hit = await caches.match(req, { ignoreSearch: true });
  if (hit) return hit;
  var url = new URL(req.url);
  if (/\/index\.html$/.test(url.pathname)) {
    var shell = await caches.match(new URL('./', url).href);
    if (shell) return shell;
  }
  if (url.pathname === scopeRootPath()) {
    var home = await caches.match(abs('./'));
    if (home) return home;
  }
  return offlinePage();
}

async function navigate(req) {
  try {
    var res = await Promise.race([fetch(req), timeout(5000)]);
    put(req, res);
    return res;
  } catch (e) {
    return navigationFallback(req);
  }
}

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname === '/sw.js') return;
  if (req.mode === 'navigate') {
    event.respondWith(navigate(req));
    return;
  }
  if (/\.(?:json|png|svg|ico|webmanifest)$/.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(req));
    return;
  }
  event.respondWith(networkFirst(req, false));
});
