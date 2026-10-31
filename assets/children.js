/* 孩子档案、诊断记录、进行中的诊断会话：本机 localStorage 是缓存，另有 /store/ 与家人同步（见下方同步段）。
 * 诊断页和档案页共用。window.CnmChildren。 */
(function () {
  'use strict';
  var KEY = 'cnmChildren.v1';
  var REC_KEY = 'cnmChildren.records.v1';
  var MAX_CHILDREN = 8;
  var MAX_RECORDS = 40;
  var MAX_BACKUP_BYTES = 10 * 1024 * 1024;
  var GRADES = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三'];
  var TEXTBOOKS = ['人教版', '北师大版', '苏教版', '沪教版', '外研版', '译林版', '其他'];

  function read(k, fallback) {
    try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? fallback : v; } catch (e) { return fallback; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; }
  }

  /* ===== 跨设备同步：家人共用一份档案 =====
   * /store/*.json 由 nginx 的 DAV 模块提供，外面套着 Basic Auth；localStorage 仍是本地缓存。
   * 读永远同步（页面启动不等网络），写完异步推上去，打开页面时拉一次、合并后刷新一次。
   * 诊断页用它自己的 lsSet/lsDel 写会话和已出过的题，不走 write()，所以在存储原语上挂一道。
   * 限制：整文件 PUT，两人同时改同一条记录时后写者赢（家庭场景够用）。 */
  var SYNC = {};
  SYNC[KEY] = { file: 'children.json', merge: mergeState };
  SYNC[REC_KEY] = { file: 'records.json', merge: mergeRecords };
  SYNC['cnmDiagnose.session.v2'] = { file: 'session-math.json', merge: mergeSession, tomb: true };
  SYNC['cneDiagnose.session.v2'] = { file: 'session-en.json', merge: mergeSession, tomb: true };
  SYNC['cnpDiagnose.session.v2'] = { file: 'session-phy.json', merge: mergeSession, tomb: true };
  SYNC['cncDiagnose.session.v2'] = { file: 'session-zh.json', merge: mergeSession, tomb: true };
  SYNC['cnmDiagnose.seen.v1'] = { file: 'seen.json', merge: unionList };
  var inflight = {};
  var holding = false; // 拉取时刚从服务端拿下来的值不回推，省一次无用 PUT

  (function hookStorage() {
    var origSet = localStorage.setItem;
    var origDel = localStorage.removeItem;
    localStorage.setItem = function (k, v) {
      origSet.call(localStorage, k, v);
      if (SYNC[k] && !holding) push(k);
    };
    localStorage.removeItem = function (k) {
      var cfg = SYNC[k];
      if (cfg && cfg.tomb) { // 会话被放弃：写墓碑而不是真删，否则另一台设备会把它复活
        origSet.call(localStorage, k, JSON.stringify({ deletedAt: new Date().toISOString() }));
        push(k);
        return;
      }
      origDel.call(localStorage, k);
    };
  })();

  function parseJson(s) { try { var v = JSON.parse(s); return v == null ? null : v; } catch (e) { return null; } }
  function emptyState() { return { v: 1, current: null, children: [], deleted: {} }; }
  function isEmptyValue(k, v) {
    if (v == null) return true;
    if (k === KEY) {
      if (!Array.isArray(v.children)) return true;
      // 有墓碑就不算空：全删光的档案也要上传，否则另一端会把孩子复活
      return v.children.length === 0 && !(v.deleted && Object.keys(v.deleted).length);
    }
    if (Array.isArray(v)) return v.length === 0;   // seen：题目 id 列表
    if (typeof v !== 'object') return false;
    if (v.deletedAt) return false;                 // 墓碑必须上传，否则放弃的存档会回来
    if (k.indexOf('.session.') >= 0) return !Array.isArray(v.targets) || v.targets.length === 0;
    return Object.keys(v).length === 0;
  }
  function ts(x) { return String((x && (x.updatedAt || x.createdAt)) || ''); }
  function rts(r) { return String((r && (r.updatedAt || r.savedAt)) || ''); }

  /* 合并两份孩子档案：按 id 取并集，同 id 取时间戳新的；墓碑 deleted 不让被删的孩子复活 */
  function mergeState(a, b) {
    a = a && Array.isArray(a.children) ? a : emptyState();
    b = b && Array.isArray(b.children) ? b : emptyState();
    var deleted = Object.assign({}, a.deleted || {}, b.deleted || {});
    var byId = {};
    function put(c) {
      if (!c || !c.id) return;
      var tomb = deleted[c.id];
      if (tomb && ts(c) < tomb) return;        // 删除比这次改动晚 → 不复活
      if (tomb && ts(c) >= tomb) delete deleted[c.id]; // 删除之后又改过 → 视为撤销删除
      var o = byId[c.id];
      if (!o || ts(c) > ts(o)) byId[c.id] = c;
    }
    a.children.forEach(put);
    b.children.forEach(put);
    var children = Object.keys(byId).map(function (id) { return byId[id]; }).sort(function (x, y) {
      return ts(x) < ts(y) ? -1 : ts(x) > ts(y) ? 1 : (String(x.id) < String(y.id) ? -1 : 1);
    });
    var cur = a.current && byId[a.current] ? a.current : (b.current && byId[b.current] ? b.current : null);
    var out = { v: 1, current: cur, children: children };
    if (Object.keys(deleted).length) out.deleted = deleted; // 没有墓碑就别加这个字段，否则每台设备都会多回写一次
    return out;
  }

  /* 合并诊断记录：按 childId → rec.key 取并集，同 key 取新的那条 */
  function mergeRecords(a, b) {
    a = a && typeof a === 'object' && !Array.isArray(a) ? a : {};
    b = b && typeof b === 'object' && !Array.isArray(b) ? b : {};
    var ids = {};
    Object.keys(a).forEach(function (id) { ids[id] = 1; });
    Object.keys(b).forEach(function (id) { ids[id] = 1; });
    var out = {};
    Object.keys(ids).forEach(function (id) {
      var byKey = {};
      [a[id], b[id]].forEach(function (arr) {
        (Array.isArray(arr) ? arr : []).forEach(function (r) {
          if (!r || !r.key) return;
          var o = byKey[r.key];
          if (!o || rts(r) > rts(o)) byKey[r.key] = r;
        });
      });
      var list = Object.keys(byKey).map(function (k) { return byKey[k]; }).sort(function (x, y) {
        return String(y.savedAt || '').localeCompare(String(x.savedAt || ''));
      });
      // 导入进来的完整历史不截断，与 saveRecord/moveRecord 的规则一致
      var keep = (Array.isArray(a[id]) && a[id].length > MAX_RECORDS) ||
                 (Array.isArray(b[id]) && b[id].length > MAX_RECORDS);
      if (list.length) out[id] = keep ? list : list.slice(0, MAX_RECORDS);
    });
    return out;
  }

  /* 诊断会话存档：整份取 savedAt 新的；墓碑 deletedAt 不让被放弃的存档复活 */
  function mergeSession(a, b) {
    var da = a && a.deletedAt, db = b && b.deletedAt;
    if (da || db) {
      var tomb = da && db ? (da > db ? da : db) : (da || db);
      var other = da ? b : a;
      if (other && !other.deletedAt && String(other.savedAt || '') > tomb) return other; // 放弃之后又接着做 → 撤销墓碑
      return { deletedAt: tomb };
    }
    if (!a) return b;
    if (!b) return a;
    return String(a.savedAt || '') >= String(b.savedAt || '') ? a : b;
  }

  /* 已出过的题：取并集，谁也别覆盖谁，两台设备才不会重复出题 */
  function unionList(a, b) {
    var out = [], seen = {};
    [a, b].forEach(function (arr) {
      (Array.isArray(arr) ? arr : []).forEach(function (x) { if (!seen[x]) { seen[x] = 1; out.push(x); } });
    });
    return out;
  }

  /* 推送：每个文件一个在途请求，期间又写了就记 pending，在途的回来再推最新值（避免乱序覆盖） */
  function push(k) {
    var cfg = SYNC[k];
    if (!cfg || typeof fetch !== 'function') return; // 老浏览器没 fetch → 只用本地存储
    if (inflight[cfg.file]) { inflight[cfg.file].pending = true; return; }
    var body = localStorage.getItem(k);
    if (isEmptyValue(k, parseJson(body))) return; // 空档案不上传，免得把别人的数据覆盖成空
    inflight[cfg.file] = { pending: false };
    fetch('/store/' + cfg.file, { method: 'PUT', body: body || '', headers: { 'Content-Type': 'application/json' } })
      .catch(function () { /* 离线或没通过认证：留在本地，下次写入再推 */ })
      .then(function () {
        var st = inflight[cfg.file];
        delete inflight[cfg.file];
        if (st && st.pending) push(k);
      });
  }

  /* 拉取：服务端有就合并进本地；服务端还没有而本地非空，就用本地建库（手机首次把自己的档案推上去） */
  function pullOne(k) {
    var cfg = SYNC[k];
    return fetch('/store/' + cfg.file, { cache: 'no-store' }).then(function (res) {
      if (res.status === 404) {
        if (!isEmptyValue(k, parseJson(localStorage.getItem(k)))) push(k);
        return false;
      }
      if (!res.ok) return false;
      return res.json().then(function (remote) {
        var local = parseJson(localStorage.getItem(k));
        if (isEmptyValue(k, local)) {
          holding = true; // 这份就是从服务端拿下来的，原样写进去就行，不用再推回去
          try { localStorage.setItem(k, JSON.stringify(remote)); } finally { holding = false; }
          return true;
        }
        var merged = cfg.merge(local, remote);
        if (JSON.stringify(merged) === JSON.stringify(local)) return false;
        localStorage.setItem(k, JSON.stringify(merged)); // setItem 钩子会把合并结果推上去
        return true;
      });
    }).catch(function () { return false; });
  }
  function pull() {
    return Promise.all(Object.keys(SYNC).map(pullOne)).then(function (r) { return r.some(Boolean); });
  }

  /* 打开页面时拉一次；拉到新数据就刷新一次让已渲染的页面显示出来（sessionStorage 保证最多刷一次，不会循环） */
  function bootstrap() {
    if (typeof fetch !== 'function' || typeof Promise !== 'function') return; // 老浏览器只用本地存储
    var FLAG = 'cnmSync.reloaded';
    var reloaded = false;
    try { reloaded = sessionStorage.getItem(FLAG) === '1'; sessionStorage.removeItem(FLAG); } catch (e) { /* 隐私模式 */ }
    pull().then(function (changed) {
      if (!changed || reloaded) return;
      try { sessionStorage.setItem(FLAG, '1'); } catch (e) { return; }
      location.reload();
    });
  }

  function state() {
    var s = read(KEY, null);
    if (!s || !Array.isArray(s.children)) s = { v: 1, current: null, children: [] };
    if (s.current && !s.children.some(function (c) { return c.id === s.current; })) s.current = s.children.length ? s.children[0].id : null;
    return s;
  }
  function records() {
    var r = read(REC_KEY, null);
    return r && typeof r === 'object' && !Array.isArray(r) ? r : {};
  }
  function newId() { return 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

  function list() { return state().children.slice(); }
  function get(id) { return state().children.filter(function (c) { return c.id === id; })[0] || null; }
  function current() { var s = state(); return s.current ? get(s.current) : null; }
  function setCurrent(id) {
    var s = state();
    if (id && !s.children.some(function (c) { return c.id === id; })) return false;
    s.current = id || null;
    return write(KEY, s);
  }

  function clean(f) {
    var name = String(f && f.name || '').replace(/\s+/g, ' ').trim();
    var grade = GRADES.indexOf(f && f.grade) >= 0 ? f.grade : '';
    var textbook = TEXTBOOKS.indexOf(f && f.textbook) >= 0 ? f.textbook : TEXTBOOKS[0];
    return { name: name, grade: grade, textbook: textbook };
  }
  function check(s, f, selfId) {
    if (!f.name) return '请填写孩子的昵称。';
    if (f.name.length > 12) return '昵称最多 12 个字。';
    if (!f.grade) return '请选择年级。';
    if (s.children.some(function (c) { return c.id !== selfId && c.name === f.name; })) return '已经有叫「' + f.name + '」的孩子了，换个昵称区分。';
    return '';
  }

  /* 返回 { ok, error, child } */
  function add(form) {
    var s = state();
    var f = clean(form);
    if (s.children.length >= MAX_CHILDREN) return { ok: false, error: '最多可以建 ' + MAX_CHILDREN + ' 个孩子。' };
    var err = check(s, f, null);
    if (err) return { ok: false, error: err };
    var child = { id: newId(), name: f.name, grade: f.grade, textbook: f.textbook, createdAt: new Date().toISOString() };
    s.children.push(child);
    if (!s.current) s.current = child.id;
    if (!write(KEY, s)) return { ok: false, error: '浏览器不允许保存数据（可能是隐私模式），档案无法保存。' };
    return { ok: true, child: child };
  }
  function update(id, form) {
    var s = state();
    var f = clean(form);
    var i = s.children.map(function (c) { return c.id; }).indexOf(id);
    if (i < 0) return { ok: false, error: '找不到这个孩子。' };
    var err = check(s, f, id);
    if (err) return { ok: false, error: err };
    s.children[i] = Object.assign({}, s.children[i], f, { updatedAt: new Date().toISOString() });
    write(KEY, s);
    return { ok: true, child: s.children[i] };
  }
  function remove(id) {
    var s = state();
    s.children = s.children.filter(function (c) { return c.id !== id; });
    if (s.current === id) s.current = s.children.length ? s.children[0].id : null;
    s.deleted = s.deleted || {};
    s.deleted[id] = new Date().toISOString(); // 墓碑：没有它，另一台设备合并时会把这个孩子复活
    write(KEY, s);
    var r = records();
    delete r[id];
    write(REC_KEY, r);
  }

  function recordsOf(childId) {
    var r = records()[childId];
    return Array.isArray(r) ? r.slice().sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); }) : [];
  }
  /* 按 rec.key 覆盖：同一次诊断反复打开结果页、更正答案，只会更新这一条 */
  function saveRecord(childId, rec) {
    if (!childId || !rec || !rec.key) return false;
    var all = records();
    var arr = Array.isArray(all[childId]) ? all[childId] : [];
    var keepImportedHistory = arr.length > MAX_RECORDS;
    var i = arr.map(function (x) { return x.key; }).indexOf(rec.key);
    var now = new Date().toISOString();
    if (i >= 0) arr[i] = Object.assign({}, rec, { savedAt: arr[i].savedAt, updatedAt: now });
    else arr.push(Object.assign({}, rec, { savedAt: now, updatedAt: now }));
    arr.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
    all[childId] = keepImportedHistory ? arr : arr.slice(0, MAX_RECORDS);
    return write(REC_KEY, all);
  }
  function hasRecord(childId, key) {
    return recordsOf(childId).some(function (x) { return x.key === key; });
  }
  function moveRecord(key, fromId, toId) {
    if (!key || fromId === toId) return;
    var all = records();
    var from = Array.isArray(all[fromId]) ? all[fromId] : [];
    var rec = from.filter(function (x) { return x.key === key; })[0];
    if (!rec) return;
    all[fromId] = from.filter(function (x) { return x.key !== key; });
    var to = Array.isArray(all[toId]) ? all[toId] : [];
    var keepImportedHistory = to.length > MAX_RECORDS;
    if (!to.some(function (x) { return x.key === key; })) to.push(rec);
    to.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
    all[toId] = keepImportedHistory ? to : to.slice(0, MAX_RECORDS);
    write(REC_KEY, all);
  }
  function removeRecord(childId, key) {
    var all = records();
    if (!Array.isArray(all[childId])) return;
    all[childId] = all[childId].filter(function (x) { return x.key !== key; });
    write(REC_KEY, all);
  }

  /* 把某个孩子的全部记录合成「每个知识点现在的状态」：越新的记录越说了算。
   * 返回 { byId: { id: { status, recKey, at, label, root } } } */
  function latestStatus(childId, subject) {
    var recs = recordsOf(childId).filter(function (r) { return !subject || r.subject === subject; }).reverse();
    var by = {};
    recs.forEach(function (r) {
      var roots = {};
      (r.roots || []).forEach(function (id) { roots[id] = true; });
      var put = function (ids, status) {
        (ids || []).forEach(function (id) { by[id] = { status: status, recKey: r.key, at: r.savedAt, label: r.label, root: !!roots[id], subject: r.subject }; });
      };
      put(r.mastered, 'mastered');
      put(r.shaky, 'shaky');
      put(r.weak, 'weak');
    });
    return by;
  }

  /* 备份保留完整档案与记录，不经过页面的筛选、排序或最近 40 条截取。
   * 不能用 read() 的兜底值：读取失败时导出空数据会让用户误以为备份成功。 */
  function exportBackup() {
    var profiles, history;
    try {
      var rawProfiles = localStorage.getItem(KEY);
      var rawRecords = localStorage.getItem(REC_KEY);
      profiles = rawProfiles === null ? { v: 1, current: null, children: [] } : JSON.parse(rawProfiles);
      history = rawRecords === null ? {} : JSON.parse(rawRecords);
    } catch (e) {
      throw new Error('无法读取档案数据，未生成备份。请检查浏览器是否允许访问本机存储，以及数据是否完整。');
    }
    if (!profiles || !Array.isArray(profiles.children) ||
        !profiles.children.every(function (c) { return c && typeof c.id === 'string' && c.id; }) ||
        !history || typeof history !== 'object' || Array.isArray(history) ||
        !Object.keys(history).every(function (id) { return Array.isArray(history[id]); })) {
      throw new Error('档案数据格式异常，未生成备份。');
    }
    if (!profiles.children.length) throw new Error('还没有可导出的孩子档案。');
    return {
      format: 'cn-math-taxonomy.children',
      version: 1,
      exportedAt: new Date().toISOString(),
      profiles: profiles,
      records: history
    };
  }

  function isObject(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
  function validDate(value) { return typeof value === 'string' && Number.isFinite(Date.parse(value)); }
  function own(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }
  function copy(value) { return JSON.parse(JSON.stringify(value)); }
  function validId(value) {
    return typeof value === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(value) &&
      ['__proto__', 'constructor', 'prototype'].indexOf(value) < 0;
  }
  function checkSafeKeys(value) {
    if (!value || typeof value !== 'object') return;
    Object.keys(value).forEach(function (key) {
      if (['__proto__', 'constructor', 'prototype'].indexOf(key) >= 0) throw new Error('备份含有不允许的数据字段。');
      checkSafeKeys(value[key]);
    });
  }
  function checkArchive(profiles, history, allowEmpty) {
    if (!isObject(profiles) || profiles.v !== 1 || !Array.isArray(profiles.children) ||
        (!allowEmpty && !profiles.children.length) || profiles.children.length > MAX_CHILDREN || !isObject(history)) {
      throw new Error('档案数据格式或数量不正确。');
    }
    var ids = new Set();
    profiles.children.forEach(function (c) {
      if (!isObject(c) || !validId(c.id) || ids.has(c.id) ||
          typeof c.name !== 'string' || !c.name.trim() || c.name.length > 12 ||
          GRADES.indexOf(c.grade) < 0 || TEXTBOOKS.indexOf(c.textbook) < 0 || !validDate(c.createdAt)) {
        throw new Error('孩子资料不完整、ID 重复，或年级和教材版本不正确。');
      }
      ids.add(c.id);
    });
    if (profiles.current !== null && !ids.has(profiles.current)) throw new Error('当前孩子不在备份档案中。');
    Object.keys(history).forEach(function (id) {
      if (!ids.has(id) || !Array.isArray(history[id])) throw new Error('诊断记录没有对应的孩子档案。');
      var keys = new Set();
      history[id].forEach(function (r) {
        if (!isObject(r) || typeof r.key !== 'string' || !r.key || keys.has(r.key) ||
            ['math', 'chinese', 'science', 'morality', 'history', 'english', 'physics'].indexOf(r.subject) < 0 || !validDate(r.savedAt) ||
            (own(r, 'updatedAt') && !validDate(r.updatedAt))) throw new Error('诊断记录的标识、学科或时间不正确。');
        keys.add(r.key);
        ['weak', 'roots', 'shaky', 'mastered', 'targets'].forEach(function (field) {
          if (!own(r, field) || (field === 'targets' && r[field] === null)) return;
          if (!Array.isArray(r[field]) || !r[field].every(validId)) throw new Error('诊断记录的知识点列表不正确。');
        });
        if ((own(r, 'asked') && (!Number.isInteger(r.asked) || r.asked < 0)) ||
            (own(r, 'label') && typeof r.label !== 'string') ||
            (own(r, 'mode') && ['target', 'screen'].indexOf(r.mode) < 0)) throw new Error('诊断记录的范围或题数不正确。');
        if (own(r, 'counts') && (!isObject(r.counts) || !Object.keys(r.counts).every(function (key) {
          return Number.isInteger(r.counts[key]) && r.counts[key] >= 0;
        }))) throw new Error('诊断记录的统计不正确。');
      });
    });
    checkSafeKeys(profiles);
    checkSafeKeys(history);
  }
  function checkBackup(backup) {
    if (!isObject(backup) || backup.format !== 'cn-math-taxonomy.children') throw new Error('请选择本站导出的档案备份文件。');
    if (backup.version !== 1) throw new Error('暂不支持这个备份版本。');
    if (!validDate(backup.exportedAt)) throw new Error('备份导出时间不正确。');
    checkArchive(backup.profiles, backup.records, false);
    checkSafeKeys(backup);
  }
  function parseBackup(text) {
    if (typeof text !== 'string' || text.length > MAX_BACKUP_BYTES) throw new Error('备份文件不能超过 10 MB。');
    var backup;
    try { backup = JSON.parse(text.replace(/^\uFEFF/, '')); }
    catch (e) { throw new Error('文件不是有效的 JSON，档案未改变。'); }
    checkBackup(backup);
    return backup;
  }
  function importSnapshot() {
    var rawProfiles, rawRecords, profiles, history;
    try {
      rawProfiles = localStorage.getItem(KEY);
      rawRecords = localStorage.getItem(REC_KEY);
      profiles = rawProfiles === null ? { v: 1, current: null, children: [] } : JSON.parse(rawProfiles);
      history = rawRecords === null ? {} : JSON.parse(rawRecords);
    } catch (e) { throw new Error('无法读取本机档案，导入已停止。请先检查本机数据。'); }
    checkArchive(profiles, history, true);
    return { profiles: profiles, records: history, rawRecords: rawRecords, token: JSON.stringify([rawProfiles, rawRecords]) };
  }
  function recordTime(r) { return Math.max(Date.parse(r.savedAt), Date.parse(r.updatedAt || r.savedAt)); }
  function prepareImport(backup) {
    checkBackup(backup);
    var before = importSnapshot();
    var profiles = copy(before.profiles);
    var history = copy(before.records);
    var byId = new Map();
    var names = new Set();
    profiles.children.forEach(function (c) { byId.set(c.id, c); names.add(c.name); });
    var additions = backup.profiles.children.filter(function (c) { return !byId.has(c.id); }).length;
    if (profiles.children.length + additions > MAX_CHILDREN) throw new Error('合并后会超过 ' + MAX_CHILDREN + ' 个孩子，请先整理现有档案。');
    // 先保留所有不冲突的原名，再为同名的新档案分配名称，重复导入仍按 ID 合并。
    backup.profiles.children.forEach(function (c) { if (!byId.has(c.id)) names.add(c.name); });
    var summary = { addedChildren: 0, matchedChildren: 0, renamedChildren: 0, addedRecords: 0, updatedRecords: 0, keptRecords: 0, children: [], token: before.token };
    var usedNames = new Set(profiles.children.map(function (c) { return c.name; }));
    backup.profiles.children.forEach(function (source) {
      var child = byId.get(source.id);
      var action = 'merge';
      if (child) summary.matchedChildren++;
      else {
        child = copy(source);
        if (usedNames.has(child.name)) {
          var n = 1, candidate;
          do {
            var suffix = n === 1 ? '（导入）' : '（导入' + n + '）';
            candidate = source.name.slice(0, Math.max(0, 12 - suffix.length)) + suffix;
            n++;
          } while (names.has(candidate));
          child.name = candidate;
          summary.renamedChildren++;
          action = 'rename';
        } else action = 'add';
        usedNames.add(child.name); names.add(child.name);
        byId.set(child.id, child); profiles.children.push(child); summary.addedChildren++;
      }
      var merged = new Map();
      (history[child.id] || []).forEach(function (r) { merged.set(r.key, r); });
      (backup.records[child.id] || []).forEach(function (r) {
        var old = merged.get(r.key);
        if (!old) { merged.set(r.key, copy(r)); summary.addedRecords++; }
        else if (recordTime(r) > recordTime(old)) { merged.set(r.key, copy(r)); summary.updatedRecords++; }
        else summary.keptRecords++;
      });
      if (own(history, child.id) || own(backup.records, child.id)) history[child.id] = Array.from(merged.values());
      summary.children.push({ name: child.name, sourceName: source.name, action: action, records: merged.size });
    });
    if (!before.profiles.children.length) profiles.current = backup.profiles.current;
    Object.keys(backup.profiles).forEach(function (key) { if (!own(profiles, key)) profiles[key] = copy(backup.profiles[key]); });
    return { before: before, profiles: profiles, records: history, summary: summary };
  }
  function previewImport(backup) { return prepareImport(backup).summary; }
  function importBackup(backup, token) {
    var plan = prepareImport(backup);
    if (token !== plan.before.token) throw new Error('本机档案已发生变化，请重新预览后再导入。');
    var recordsWritten = false;
    try {
      localStorage.setItem(REC_KEY, JSON.stringify(plan.records));
      recordsWritten = true;
      localStorage.setItem(KEY, JSON.stringify(plan.profiles));
    } catch (e) {
      if (recordsWritten) {
        try {
          if (plan.before.rawRecords === null) localStorage.removeItem(REC_KEY);
          else localStorage.setItem(REC_KEY, plan.before.rawRecords);
        } catch (rollbackError) { throw new Error('导入未完成，原记录恢复失败。请保留备份文件并检查浏览器存储。'); }
      }
      throw new Error('浏览器无法保存导入数据，原有档案和记录未改变。可能是存储空间不足。');
    }
    return plan.summary;
  }

  window.CnmChildren = {
    GRADES: GRADES, TEXTBOOKS: TEXTBOOKS, MAX_CHILDREN: MAX_CHILDREN,
    list: list, get: get, current: current, setCurrent: setCurrent,
    add: add, update: update, remove: remove,
    recordsOf: recordsOf, saveRecord: saveRecord, hasRecord: hasRecord, moveRecord: moveRecord, removeRecord: removeRecord,
    latestStatus: latestStatus, exportBackup: exportBackup,
    MAX_BACKUP_BYTES: MAX_BACKUP_BYTES, parseBackup: parseBackup, previewImport: previewImport, importBackup: importBackup,
    sync: pull // 暴露给 tests/test_sync.js
  };
  bootstrap();
})();
