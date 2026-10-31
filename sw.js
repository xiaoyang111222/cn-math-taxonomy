/* 离线缓存：站点壳（页面、脚本、样式、图标）和图谱数据。
 * 页面和脚本：网络优先，断网时用缓存；数据和图标：先用缓存，同时后台更新。
 * 改了 SHELL 或 DATA 列表、或数据结构变了，就把 VERSION 加一。 */
'use strict';

var VERSION = 'v4';
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

async function networkFirst(req, ignoreSearch, fallbackUrl) {
  try {
    var res = await Promise.race([fetch(req), timeout(5000)]);
    put(req, res);
    return res;
  } catch (e) {
    var hit = await caches.match(req, { ignoreSearch: ignoreSearch });
    if (hit) return hit;
    if (fallbackUrl) {
      var fb = await caches.match(fallbackUrl);
      if (fb) return fb;
    }
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

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname === '/sw.js') return;
  if (url.pathname.indexOf('/store/') === 0) return; // 跨设备同步数据必须走网络，不能吃缓存
  if (req.mode === 'navigate') {
    event.respondWith(networkFirst(req, true, abs('./')));
    return;
  }
  if (/\.(?:json|png|svg|ico|webmanifest)$/.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(req));
    return;
  }
  event.respondWith(networkFirst(req, false, null));
});
