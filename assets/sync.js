/* 云端同步引擎。本地优先：现有功能只读写 localStorage，不依赖网络与登录；
 * 未登录时这个文件什么都不做（不拦截、不弹窗、不挂钩子）。
 * 同步四份数据：children=cnmChildren.v1、records=cnmChildren.records.v1、wrongbook=cnmWrong.v1、finals=cnmFinals.v1。
 * 合并函数是纯函数（Node 里 module.exports 同一份，tests/test_sync.js 覆盖）；
 * 删除靠「上次同步的基线」做三方合并推断：基线里有、一边没了、另一边没改过 → 删除；另一边改过 → 保留改动。
 * 云端没有可用数据（没有这一行 / 载荷损坏）时不推断任何删除。 */
(function (root) {
  'use strict';

  var DATASETS = { children: 'cnmChildren.v1', records: 'cnmChildren.records.v1', wrongbook: 'cnmWrong.v1', finals: 'cnmFinals.v1' };
  var NAMES = ['children', 'records', 'wrongbook', 'finals'];
  var META_KEY = 'cnmSync.meta.v1';
  var BASE_KEY = 'cnmSync.base.v1';
  var MAX_PER_BUCKET = 300;
  var DEBOUNCE_MS = 5000;
  var MAX_RETRY = 2;

  /* ---------------------------------------------------------------- 纯函数 */

  function isObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
  function stable(v) {
    if (v === undefined) return 'undefined';
    if (v === null || typeof v !== 'object') return JSON.stringify(v);
    if (Array.isArray(v)) return '[' + v.map(stable).join(',') + ']';
    return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + stable(v[k]); }).join(',') + '}';
  }
  function same(a, b) { return stable(a) === stable(b); }
  /* 数字毫秒或 ISO 字符串 → 毫秒；认不出返回 0。 */
  function ms(v) {
    if (typeof v === 'number' && isFinite(v) && v > 0) return v;
    if (typeof v === 'string') { var t = Date.parse(v); return isNaN(t) ? 0 : t; }
    return 0;
  }
  function childTs(c) { return Math.max(ms(c && c.updatedAt), ms(c && c.createdAt)); }
  function recTs(r) { return Math.max(ms(r && r.updatedAt), ms(r && r.savedAt)); }
  function wrongTs(e) { return ms(e && e.ts); }
  function planTs(p) { return Math.max(ms(p && p.updatedAt), ms(p && p.createdAt)); }

  /* 两边都有同一项且内容不同：两边都有时间戳取较新（相同取本地）；缺时间戳按整表较新的一边，再相同取本地。 */
  function pickNewer(l, r, tsOf, ctx) {
    if (same(l, r)) return l;
    var a = tsOf(l), b = tsOf(r);
    if (a && b) return b > a ? r : l;
    return (ctx.remoteAt || 0) > (ctx.localAt || 0) ? r : l;
  }

  function indexBy(list, keyOf) {
    var map = Object.create(null);
    var order = [];
    (Array.isArray(list) ? list : []).forEach(function (x) {
      var k = isObj(x) ? keyOf(x) : null;
      if (k == null || k === '') return;
      k = String(k);
      if (!(k in map)) order.push(k);
      map[k] = x;
    });
    return { map: map, order: order };
  }

  /* 按键合并两个列表。hasBase 为 false 时只做并集，不推断删除。带 deleted 标记的条目：任一边标了就删。 */
  function mergeKeyed(local, remote, base, hasBase, keyOf, tsOf, ctx, pick) {
    var L = indexBy(local, keyOf), R = indexBy(remote, keyOf), B = indexBy(base, keyOf);
    var order = L.order.concat(R.order.filter(function (k) { return !(k in L.map); }));
    var out = [];
    order.forEach(function (k) {
      var l = L.map[k], r = R.map[k], b = B.map[k];
      var item;
      if (l && r) item = (l.deleted || r.deleted) ? null : (pick || pickNewer)(l, r, tsOf, ctx);
      else if (l) item = (hasBase && b && same(l, b)) ? null : l;
      else item = (hasBase && b && same(r, b)) ? null : r;
      if (item && !item.deleted) out.push(item);
    });
    return out;
  }

  function childList(state) {
    return isObj(state) && Array.isArray(state.children) ? state.children.filter(function (c) { return isObj(c) && c.id; }) : [];
  }

  /* 档案昵称不能重名（children.js 的规则）：合并后撞名的，较晚创建的加「（2）」。 */
  function dedupeNames(children, ctx) {
    var order = children.slice().sort(function (a, b) {
      return (ms(a.createdAt) - ms(b.createdAt)) || (String(a.id) < String(b.id) ? -1 : 1);
    });
    var taken = Object.create(null);
    var renamed = Object.create(null);
    order.forEach(function (c) {
      var name = String(c.name || '');
      if (!taken[name]) { taken[name] = true; return; }
      for (var n = 2; ; n++) {
        var suffix = '（' + n + '）';
        var candidate = name.slice(0, Math.max(1, 12 - suffix.length)) + suffix;
        if (!taken[candidate]) {
          taken[candidate] = true;
          renamed[c.id] = candidate;
          return;
        }
      }
    });
    if (!Object.keys(renamed).length) return children;
    var stamp = new Date(typeof ctx.now === 'number' ? ctx.now : Date.now()).toISOString();
    return children.map(function (c) {
      return renamed[c.id] ? Object.assign({}, c, { name: renamed[c.id], updatedAt: stamp }) : c;
    });
  }

  function mergeChildren(local, remote, base, ctx) {
    var merged = mergeKeyed(childList(local), childList(remote), childList(base), base !== undefined,
      function (c) { return c.id; }, childTs, ctx);
    if (!merged.length && !isObj(local)) return null;
    merged = dedupeNames(merged, ctx);
    var ids = merged.map(function (c) { return c.id; });
    var current = null;
    [isObj(local) && local.current, isObj(remote) && remote.current].forEach(function (id) {
      if (current === null && id && ids.indexOf(id) >= 0) current = id;
    });
    if (current === null && ids.length) current = ids[0];
    return { v: 1, current: current, children: merged };
  }

  function mapOf(v) { return isObj(v) ? v : {}; }
  function bucketNames(maps) {
    var seen = Object.create(null);
    var names = [];
    maps.forEach(function (m) { Object.keys(m).forEach(function (k) { if (!seen[k]) { seen[k] = true; names.push(k); } }); });
    return names;
  }

  /* 诊断记录 {孩子id: [记录]}：按记录 key 逐条合并（比整表覆盖少丢一台设备的诊断）。 */
  function mergeRecords(local, remote, base, ctx) {
    var L = mapOf(local), R = mapOf(remote), B = mapOf(base);
    var out = {};
    bucketNames([L, R]).forEach(function (child) {
      var list = mergeKeyed(L[child], R[child], B[child], base !== undefined,
        function (r) { return r.key; }, recTs, ctx);
      list.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
      if (list.length || child in L) out[child] = list;
    });
    if (!Object.keys(out).length && !isObj(local)) return null;
    return out;
  }

  /* 错题本复测进度（stage / dueAt / done，与 assets/wrongbook.js 同规则，缺省值：0 / ts + 1 天 / false）。 */
  var DAY_MS = 24 * 60 * 60 * 1000;
  function wrongStage(e) { var n = Math.floor(Number(e && e.stage)); return n >= 0 ? Math.min(n, 3) : 0; }
  function wrongDueAt(e) { var d = Number(e && e.dueAt); return d > 0 ? d : ms(e && e.ts) + DAY_MS; }
  /* 复测进度谁更靠前：done=true 优先，其次 stage 高者，其次 dueAt 晚者；打平返回 0。 */
  function progressCmp(a, b) {
    if (!!a.done !== !!b.done) return a.done ? 1 : -1;
    if (wrongStage(a) !== wrongStage(b)) return wrongStage(a) > wrongStage(b) ? 1 : -1;
    var da = wrongDueAt(a), db = wrongDueAt(b);
    return da === db ? 0 : (da > db ? 1 : -1);
  }
  /* 同一 qid 两份条目：ts / count / chosen 等沿用 pickNewer（较新的 ts 胜），复测进度单独取更靠前的一份，旧副本不会冲掉复测进度。 */
  function pickWrong(l, r, tsOf, ctx) {
    var win = pickNewer(l, r, tsOf, ctx);
    if (same(l, r)) return win;
    var c = progressCmp(r, l);
    var best = c > 0 ? r : (c < 0 ? l : win);
    var out = Object.assign({}, win);
    ['stage', 'dueAt', 'done'].forEach(function (k) {
      if (k in best) out[k] = best[k]; else delete out[k];
    });
    if (out.done) delete out.dueAt;
    return same(out, win) ? win : out;
  }

  /* 错题本 {孩子id 或 guest: [错题]}：按 qid 逐条合并，较新的 ts 胜（复测进度另算，见 pickWrong），每桶最多 300 条。 */
  function mergeWrongbook(local, remote, base, ctx) {
    var L = mapOf(local), R = mapOf(remote), B = mapOf(base);
    var out = {};
    bucketNames([L, R]).forEach(function (bucket) {
      var list = mergeKeyed(L[bucket], R[bucket], B[bucket], base !== undefined,
        function (e) { return e.qid; }, wrongTs, ctx, pickWrong);
      list.sort(function (a, b) { return (a.ts || 0) - (b.ts || 0); });
      if (list.length > MAX_PER_BUCKET) list = list.slice(list.length - MAX_PER_BUCKET);
      if (list.length || bucket in L) out[bucket] = list;
    });
    if (!Object.keys(out).length && !isObj(local)) return null;
    return out;
  }

  /* 整份数据（期末计划）：较新的一份胜。本地没了而云端没动过 → 删除；云端明确清空而本地没动过 → 删除。 */
  function mergeWhole(local, remote, base, ctx) {
    var hasBase = base !== undefined && base !== null;
    if (local == null && remote == null) return null;
    if (local == null) {
      if (hasBase && same(remote, base)) return null;
      return remote;
    }
    if (remote == null) {
      if (remote === null && hasBase && same(local, base)) return null;
      return local;
    }
    return pickNewer(local, remote, planTs, ctx);
  }

  var MERGERS = { children: mergeChildren, records: mergeRecords, wrongbook: mergeWrongbook, finals: mergeWhole };

  /* local / remote / base 都是解析后的 JSON 值（没有就是 null）。
   * remote 为 undefined 表示「云端没有可用数据」，此时不用基线推断删除。
   * ctx: { remoteAt, localAt, now }。 */
  function mergeDataset(name, local, remote, base, ctx) {
    var fn = MERGERS[name];
    if (!fn) throw new Error('unknown dataset ' + name);
    if (local === undefined) local = null;
    if (remote === undefined) base = undefined;
    return fn(local, remote, base, ctx || {});
  }

  function parseEnvelope(payload) {
    try {
      var e = JSON.parse(payload);
      if (isObj(e) && 'data' in e) return { at: ms(e.at), data: e.data };
    } catch (err) { /* 载荷损坏：当作云端没有 */ }
    return null;
  }

  /* ---------------------------------------------------------------- 引擎（可注入依赖，便于测试） */

  /* deps: storage（getItem/setItem/removeItem）、api(method, path, body) → Promise<{status, data}>、
   *       now、setTimer、clearTimer、emit(status)、confirmSwitch(oldEmail, newEmail) → boolean */
  function createEngine(deps) {
    var storage = deps.storage;
    var api = deps.api;
    var now = deps.now || Date.now;
    var setTimer = deps.setTimer || setTimeout;
    var clearTimer = deps.clearTimer || clearTimeout;
    var debounce = deps.debounceMs == null ? DEBOUNCE_MS : deps.debounceMs;
    var active = false;
    var applying = false;
    var timer = null;
    var queue = Promise.resolve();
    var last = { state: 'idle', at: 0, message: '' };

    function emit(state, message) {
      last = { state: state, at: now(), message: message || '' };
      if (deps.emit) deps.emit(last);
    }
    function readJson(key) {
      try {
        var raw = storage.getItem(key);
        return raw == null ? null : JSON.parse(raw);
      } catch (e) { return null; }
    }
    function writeJson(key, value) {
      try { storage.setItem(key, JSON.stringify(value)); return true; } catch (e) { return false; }
    }
    function meta() { var m = readJson(META_KEY); return isObj(m) ? m : {}; }
    function saveMeta(m) { writeJson(META_KEY, m); }
    function baseStore() { var b = readJson(BASE_KEY); return isObj(b) ? b : {}; }
    function readLocal(name) { return readJson(DATASETS[name]); }
    function writeLocal(name, value) {
      applying = true;
      try {
        if (value == null) storage.removeItem(DATASETS[name]);
        else storage.setItem(DATASETS[name], JSON.stringify(value));
        return true;
      } catch (e) { return false; } finally { applying = false; }
    }

    function recordBase(name, value, stamp) {
      var b = baseStore();
      var m = meta();
      m.stamps = isObj(m.stamps) ? m.stamps : {};
      if (value === undefined) delete b[name]; else b[name] = value;
      if (stamp) m.stamps[name] = stamp; else delete m.stamps[name];
      writeJson(BASE_KEY, b);
      saveMeta(m);
    }

    /* 同步一个 dataset。remoteRow: { data, at, updated_at } 或 undefined（云端没有可用数据）。
     * 返回 { applied: 本地被改写了没有 }。 */
    async function syncDataset(name, remoteRow) {
      var applied = false;
      for (var attempt = 0; ; attempt++) {
        var base = baseStore();
        var hasBase = name in base;
        var local = readLocal(name);
        var remote = remoteRow ? remoteRow.data : undefined;
        var merged = mergeDataset(name, local, remote, hasBase ? base[name] : undefined,
          { remoteAt: remoteRow ? remoteRow.at : 0, localAt: 0, now: now() });
        if (!same(merged, local)) {
          if (!writeLocal(name, merged)) throw new Error('本地存储写入失败');
          applied = true;
        }
        var needPush = remoteRow ? !same(merged, remote) : merged != null;
        if (!needPush) {
          recordBase(name, remoteRow ? merged : undefined, remoteRow ? remoteRow.updated_at : null);
          return { applied: applied };
        }
        var res = await api('PUT', '/sync/' + name, {
          payload: JSON.stringify({ v: 1, at: now(), data: merged }),
          base_updated_at: remoteRow ? remoteRow.updated_at : null
        });
        if (res.status === 200 && res.data && res.data.updated_at) {
          recordBase(name, merged, res.data.updated_at);
          return { applied: applied };
        }
        if (res.status === 409 && attempt < MAX_RETRY) {
          var env = res.data && res.data.payload != null ? parseEnvelope(res.data.payload) : null;
          remoteRow = res.data && res.data.updated_at
            ? { data: env ? env.data : undefined, at: env ? env.at : 0, updated_at: res.data.updated_at }
            : undefined;
          continue;
        }
        if (res.status === 401) throw Object.assign(new Error('登录已过期'), { unauthorized: true });
        throw new Error('同步失败（' + res.status + '）');
      }
    }

    function fail(e) {
      if (e && e.unauthorized) {
        active = false;
        emit('signedout', '登录已过期，请重新登录。');
        if (deps.onUnauthorized) deps.onUnauthorized();
      } else {
        emit('error', e && e.message ? e.message : '网络不通');
      }
    }

    function enqueue(fn) {
      var run = queue.then(fn, fn);
      queue = run.catch(function () { /* 错误已在 fn 内处理 */ });
      return run;
    }

    /* 登录后第一步：拉云端、按 dataset 合并、写回本地、再推上云。 */
    async function doSyncAll() {
      if (!active) return { applied: false };
      emit('syncing');
      try {
        var res = await api('GET', '/sync');
        if (res.status === 401) throw Object.assign(new Error('登录已过期'), { unauthorized: true });
        if (res.status !== 200 || !res.data) throw new Error('同步失败（' + res.status + '）');
        var rows = isObj(res.data.datasets) ? res.data.datasets : {};
        var applied = false;
        for (var i = 0; i < NAMES.length; i++) {
          var name = NAMES[i];
          var row = rows[name];
          var env = row ? parseEnvelope(row.payload) : null;
          var remoteRow = row ? { data: env ? env.data : undefined, at: env ? env.at : 0, updated_at: row.updated_at } : undefined;
          var r = await syncDataset(name, remoteRow);
          if (r.applied) applied = true;
        }
        var m = meta();
        m.lastSyncAt = now();
        saveMeta(m);
        emit(applied ? 'applied' : 'idle');
        return { applied: applied };
      } catch (e) {
        fail(e);
        return { applied: false, error: true };
      }
    }
    function syncAll() { return enqueue(doSyncAll); }

    /* 本地改动后：只推有变化的 dataset；没有云端戳（还没拉过）就走完整同步。 */
    async function doPushChanged() {
      if (!active) return { applied: false };
      var stamps = isObj(meta().stamps) ? meta().stamps : {};
      var base = baseStore();
      var changed = NAMES.filter(function (name) {
        var local = readLocal(name);
        return name in base ? !same(local, base[name]) : local != null;
      });
      if (!changed.length) return { applied: false };
      if (changed.some(function (name) { return !(name in base) || !stamps[name]; })) return doSyncAll();
      emit('syncing');
      try {
        var applied = false;
        for (var i = 0; i < changed.length; i++) {
          var name = changed[i];
          var r = await syncDataset(name, { data: base[name], at: 0, updated_at: stamps[name] });
          if (r.applied) applied = true;
        }
        var m = meta();
        m.lastSyncAt = now();
        saveMeta(m);
        emit(applied ? 'applied' : 'idle');
        return { applied: applied };
      } catch (e) {
        fail(e);
        return { applied: false, error: true };
      }
    }
    function pushChanged() { return enqueue(doPushChanged); }

    /* 本地数据变了：防抖 5 秒后上传。未登录 / 正在写回云端数据时什么都不做。 */
    function notifyLocalChange() {
      if (!active || applying) return;
      if (timer) clearTimer(timer);
      timer = setTimer(function () { timer = null; pushChanged(); }, debounce);
    }
    function flush() {
      if (!timer) return null;
      clearTimer(timer);
      timer = null;
      return pushChanged();
    }

    /* 登录后调用。同一浏览器之前同步过另一个账号：问一句再合并，否则返回 false（调用方应退出登录）。 */
    function begin(email) {
      var m = meta();
      if (m.email && m.email !== email) {
        if (!deps.confirmSwitch || !deps.confirmSwitch(m.email, email)) return false;
        m = {};
        writeJson(BASE_KEY, {});
      }
      m.email = email;
      saveMeta(m);
      active = true;
      return true;
    }
    function stop() {
      active = false;
      if (timer) { clearTimer(timer); timer = null; }
    }

    return {
      begin: begin, stop: stop, syncAll: syncAll, pushChanged: pushChanged,
      notifyLocalChange: notifyLocalChange, flush: flush,
      isActive: function () { return active; },
      status: function () { return last; },
      lastSyncAt: function () { return meta().lastSyncAt || 0; }
    };
  }

  var api = {
    DATASETS: DATASETS, NAMES: NAMES, stable: stable,
    mergeDataset: mergeDataset, mergeChildren: mergeChildren, mergeRecords: mergeRecords,
    mergeWrongbook: mergeWrongbook, mergeWhole: mergeWhole, parseEnvelope: parseEnvelope,
    createEngine: createEngine
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CnmSync = api;

  /* ---------------------------------------------------------------- 浏览器挂接 */
  if (typeof window === 'undefined' || typeof document === 'undefined' || !window.CnmAccount) return;
  var account = window.CnmAccount;
  var watch = {};
  NAMES.forEach(function (n) { watch[DATASETS[n]] = true; });
  var engine = createEngine({
    storage: window.localStorage,
    api: account.api,
    emit: function (status) { window.dispatchEvent(new CustomEvent('cnm:sync', { detail: status })); },
    onUnauthorized: function () { account.expire(); },
    confirmSwitch: function (oldEmail, newEmail) {
      return window.confirm('这台设备上的数据之前同步到了 ' + oldEmail + '。\n要把它们合并到 ' + newEmail + ' 吗？\n\n确定：合并并同步；取消：不登录这个账号。');
    }
  });
  var hooked = false;

  function installHook() {
    if (hooked || typeof Storage === 'undefined') return;
    hooked = true;
    var origSet = Storage.prototype.setItem;
    var origRemove = Storage.prototype.removeItem;
    Storage.prototype.setItem = function (key) {
      var r = origSet.apply(this, arguments);
      if (this === window.localStorage && watch[key]) engine.notifyLocalChange();
      return r;
    };
    Storage.prototype.removeItem = function (key) {
      var r = origRemove.apply(this, arguments);
      if (this === window.localStorage && watch[key]) engine.notifyLocalChange();
      return r;
    };
  }

  function begin() {
    if (!account.isLoggedIn()) return;
    if (!engine.begin(account.email())) { account.logout(); return; }
    installHook();
    engine.syncAll();
  }

  window.addEventListener('cnm:auth', function () {
    if (account.isLoggedIn()) begin(); else engine.stop();
  });
  document.addEventListener('visibilitychange', function () {
    if (!engine.isActive()) return;
    if (document.visibilityState === 'hidden') engine.flush();
    else if (Date.now() - engine.lastSyncAt() > 60000) engine.syncAll();
  });
  window.addEventListener('online', function () { if (engine.isActive()) engine.syncAll(); });

  window.CnmSyncEngine = engine;
  if (account.isLoggedIn()) setTimeout(begin, 800);
})(typeof window !== 'undefined' ? window : globalThis);
