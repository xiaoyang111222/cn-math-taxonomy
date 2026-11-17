/* 孩子档案：多个孩子、当前孩子、每个孩子的诊断记录。全部保存在本机 localStorage，不上传、不需要账号。
 * 诊断页和档案页共用。window.CnmChildren。 */
(function () {
  'use strict';
  var KEY = 'cnmChildren.v1';
  var REC_KEY = 'cnmChildren.records.v1';
  var PRACTICE_KEY = 'cnmChildren.practice.v1';
  var HOUR = 3600 * 1000;
  // 过关后的复习间隔：第 1 次过关 12 小时后复习，之后每次复习通过依次 3 天、7 天、14 天（之后保持 14 天）
  var REVIEW_INTERVALS = [12 * HOUR, 3 * 24 * HOUR, 7 * 24 * HOUR, 14 * 24 * HOUR];
  var MAX_CHILDREN = 30;   // 一个班
  var MAX_RECORDS = 60;    // 每个孩子保留最近的诊断记录条数
  var GRADES = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三'];
  var TEXTBOOKS = ['人教版', '北师大版', '苏教版', '沪教版', '外研版', '译林版', '其他'];

  function read(k, fallback) {
    try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? fallback : v; } catch (e) { return fallback; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; }
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
    s.children[i] = Object.assign({}, s.children[i], f);
    write(KEY, s);
    return { ok: true, child: s.children[i] };
  }
  function remove(id) {
    var s = state();
    s.children = s.children.filter(function (c) { return c.id !== id; });
    if (s.current === id) s.current = s.children.length ? s.children[0].id : null;
    write(KEY, s);
    var r = records();
    delete r[id];
    write(REC_KEY, r);
    var p = practiceAll();
    delete p[id];
    write(PRACTICE_KEY, p);
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
    var i = arr.map(function (x) { return x.key; }).indexOf(rec.key);
    var now = new Date().toISOString();
    if (i >= 0) arr[i] = Object.assign({}, rec, { savedAt: arr[i].savedAt, updatedAt: now });
    else arr.push(Object.assign({}, rec, { savedAt: now, updatedAt: now }));
    arr.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
    all[childId] = arr.slice(0, MAX_RECORDS);
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
    if (!to.some(function (x) { return x.key === key; })) to.push(rec);
    to.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
    all[toId] = to.slice(0, MAX_RECORDS);
    write(REC_KEY, all);
  }
  function removeRecord(childId, key) {
    var all = records();
    if (!Array.isArray(all[childId])) return;
    all[childId] = all[childId].filter(function (x) { return x.key !== key; });
    write(REC_KEY, all);
  }

  /* ---------------- 巩固练习：过关 -> mastered + nextReviewAt（间隔复习） ---------------- */
  function practiceAll() {
    var r = read(PRACTICE_KEY, null);
    return r && typeof r === 'object' && !Array.isArray(r) ? r : {};
  }
  function practiceOf(childId) {
    var p = practiceAll()[childId];
    return p && typeof p === 'object' ? p : {};
  }
  function reviewDelay(stage) { return REVIEW_INTERVALS[Math.min(Math.max(stage, 0), REVIEW_INTERVALS.length - 1)]; }
  /* 练习过关：opts = { childId?（默认当前孩子）, subject?, now?（毫秒，测试用） }。返回写入的条目，没有孩子时返回 null。
   * 同一知识点再次过关（到期复习通过）会进入下一级间隔。 */
  function markPracticed(topicId, opts) {
    opts = opts || {};
    var childId = opts.childId || (current() && current().id);
    if (!childId || !topicId) return null;
    var all = practiceAll();
    var mine = all[childId] && typeof all[childId] === 'object' ? all[childId] : {};
    var prev = mine[topicId];
    var now = opts.now != null ? opts.now : Date.now();
    var stage = prev && prev.status === 'mastered' ? Math.min((prev.stage || 0) + 1, REVIEW_INTERVALS.length - 1) : 0;
    var entry = {
      status: 'mastered', stage: stage, subject: opts.subject || (prev && prev.subject) || subjectOfId(topicId),
      at: new Date(now).toISOString(), nextReviewAt: new Date(now + reviewDelay(stage)).toISOString(),
      passes: ((prev && prev.passes) || 0) + 1
    };
    mine[topicId] = entry;
    all[childId] = mine;
    return write(PRACTICE_KEY, all) ? entry : null;
  }
  /* 练习 / 复习没过：状态降为 shaky，并马上到期（nextReviewAt = now），间隔从头来。 */
  function markShaky(topicId, opts) {
    opts = opts || {};
    var childId = opts.childId || (current() && current().id);
    if (!childId || !topicId) return null;
    var all = practiceAll();
    var mine = all[childId] && typeof all[childId] === 'object' ? all[childId] : {};
    var now = opts.now != null ? opts.now : Date.now();
    var entry = { status: 'shaky', stage: 0, subject: opts.subject || subjectOfId(topicId), at: new Date(now).toISOString(), nextReviewAt: new Date(now).toISOString(),
      passes: (mine[topicId] && mine[topicId].passes) || 0 };
    mine[topicId] = entry;
    all[childId] = mine;
    return write(PRACTICE_KEY, all) ? entry : null;
  }
  function subjectOfId(id) { return /^cne_/.test(id) ? 'english' : /^cnp_/.test(id) ? 'physics' : 'math'; }
  /* 到期要复习的知识点（过关后到了 nextReviewAt 的），按到期时间早的在前。 */
  function dueReviews(childId, opts) {
    opts = opts || {};
    var now = opts.now != null ? opts.now : Date.now();
    var p = practiceOf(childId);
    return Object.keys(p).filter(function (id) {
      var e = p[id];
      return e && e.status === 'mastered' && (!opts.subject || e.subject === opts.subject) && Date.parse(e.nextReviewAt) <= now;
    }).sort(function (a, b) { return Date.parse(p[a].nextReviewAt) - Date.parse(p[b].nextReviewAt); });
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
    // 巩固练习的结果比它更早的诊断记录新，就覆盖（带上 nextReviewAt）
    var p = practiceOf(childId);
    Object.keys(p).forEach(function (id) {
      var e = p[id];
      if (!e || (subject && e.subject !== subject)) return;
      var cur = by[id];
      if (!cur || String(e.at) >= String(cur.at)) {
        by[id] = { status: e.status, recKey: null, at: e.at, label: '巩固练习', root: false, subject: e.subject, nextReviewAt: e.nextReviewAt, practiced: true };
      } else if (cur) cur.nextReviewAt = e.nextReviewAt;
    });
    return by;
  }

  /* ---------------- 全班档案导出 / 导入（JSON） ---------------- */
  var EXPORT_FORMAT = 'cnm-class-archive';
  function exportAll() {
    return {
      format: EXPORT_FORMAT, version: 1, exportedAt: new Date().toISOString(),
      state: state(), records: records(), practice: practiceAll()
    };
  }
  /* mode: 'merge'（默认，按昵称合并：同名孩子合并记录，新孩子追加，超出上限的跳过）/ 'replace'（整体替换）。
   * 返回 { ok, error?, added, merged, skipped } */
  function importAll(data, mode) {
    if (typeof data === 'string') { try { data = JSON.parse(data); } catch (e) { return { ok: false, error: '不是有效的 JSON 文件。' }; } }
    if (!data || data.format !== EXPORT_FORMAT || !data.state || !Array.isArray(data.state.children)) {
      return { ok: false, error: '这不是本站导出的全班档案文件。' };
    }
    var inKids = data.state.children.filter(function (c) { return c && c.id && clean(c).name; });
    var inRecs = data.records && typeof data.records === 'object' ? data.records : {};
    var inPrac = data.practice && typeof data.practice === 'object' ? data.practice : {};
    if (mode === 'replace') {
      var kids = inKids.slice(0, MAX_CHILDREN).map(function (c) { return Object.assign({}, c, clean(c)); });
      var keep = {};
      kids.forEach(function (c) { keep[c.id] = true; });
      var recs = {}; var prac = {};
      Object.keys(inRecs).forEach(function (id) { if (keep[id] && Array.isArray(inRecs[id])) recs[id] = inRecs[id].slice(0, MAX_RECORDS); });
      Object.keys(inPrac).forEach(function (id) { if (keep[id]) prac[id] = inPrac[id]; });
      var cur = keep[data.state.current] ? data.state.current : (kids[0] ? kids[0].id : null);
      var ok = write(KEY, { v: 1, current: cur, children: kids }) && write(REC_KEY, recs) && write(PRACTICE_KEY, prac);
      return ok ? { ok: true, added: kids.length, merged: 0, skipped: inKids.length - kids.length } : { ok: false, error: '浏览器不允许保存数据。' };
    }
    var s = state(); var allRecs = records(); var allPrac = practiceAll();
    var added = 0, merged = 0, skipped = 0;
    inKids.forEach(function (c) {
      var f = clean(c);
      var same = s.children.filter(function (x) { return x.name === f.name; })[0];
      var targetId;
      if (same) { targetId = same.id; merged++; }
      else if (s.children.length >= MAX_CHILDREN) { skipped++; return; }
      else {
        targetId = s.children.some(function (x) { return x.id === c.id; }) ? newId() : c.id;
        s.children.push({ id: targetId, name: f.name, grade: f.grade, textbook: f.textbook, createdAt: c.createdAt || new Date().toISOString() });
        added++;
      }
      var mine = Array.isArray(allRecs[targetId]) ? allRecs[targetId] : [];
      (Array.isArray(inRecs[c.id]) ? inRecs[c.id] : []).forEach(function (r) {
        if (r && r.key && !mine.some(function (x) { return x.key === r.key; })) mine.push(r);
      });
      mine.sort(function (a, b) { return String(b.savedAt).localeCompare(String(a.savedAt)); });
      allRecs[targetId] = mine.slice(0, MAX_RECORDS);
      var pm = allPrac[targetId] && typeof allPrac[targetId] === 'object' ? allPrac[targetId] : {};
      var pin = inPrac[c.id] && typeof inPrac[c.id] === 'object' ? inPrac[c.id] : {};
      Object.keys(pin).forEach(function (tid) { if (!pm[tid] || String(pin[tid].at) > String(pm[tid].at)) pm[tid] = pin[tid]; });
      allPrac[targetId] = pm;
    });
    if (!s.current && s.children.length) s.current = s.children[0].id;
    var ok2 = write(KEY, s) && write(REC_KEY, allRecs) && write(PRACTICE_KEY, allPrac);
    return ok2 ? { ok: true, added: added, merged: merged, skipped: skipped } : { ok: false, error: '浏览器不允许保存数据。' };
  }

  window.CnmChildren = {
    GRADES: GRADES, TEXTBOOKS: TEXTBOOKS, MAX_CHILDREN: MAX_CHILDREN, MAX_RECORDS: MAX_RECORDS,
    exportAll: exportAll, importAll: importAll,
    list: list, get: get, current: current, setCurrent: setCurrent,
    add: add, update: update, remove: remove,
    recordsOf: recordsOf, saveRecord: saveRecord, hasRecord: hasRecord, moveRecord: moveRecord, removeRecord: removeRecord,
    latestStatus: latestStatus,
    REVIEW_INTERVALS: REVIEW_INTERVALS,
    markPracticed: markPracticed, markShaky: markShaky, practiceOf: practiceOf, dueReviews: dueReviews
  };
})();
