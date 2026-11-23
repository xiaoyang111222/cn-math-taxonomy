/* 学习打卡：记下孩子哪些天学过东西（每日一句完成、错题复测通过、诊断完成），算连续学习天数。
 * localStorage 键 cnmActivity.v1：{ [孩子id 或 guest]: ['YYYY-MM-DD', ...] }，本地时区日期，去重排序。window.CnmActivity。 */
(function () {
  'use strict';
  var KEY = 'cnmActivity.v1';
  var GUEST = 'guest';
  var DAY_MS = 24 * 60 * 60 * 1000;

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY));
      return v && typeof v === 'object' && !Array.isArray(v) ? v : {};
    } catch (e) { return {}; }
  }
  function write(s) {
    try { localStorage.setItem(KEY, JSON.stringify(s)); return true; } catch (e) { return false; }
  }
  function bucketKey(childId) { return childId ? String(childId) : GUEST; }
  function validDate(v) { return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v); }
  function dateStr(ms) {
    var d = new Date(ms);
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function utcDay(str) {
    var p = str.split('-');
    return Date.UTC(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
  }
  function utcStr(day) {
    var d = new Date(day);
    return d.getUTCFullYear() + '-' + ('0' + (d.getUTCMonth() + 1)).slice(-2) + '-' + ('0' + d.getUTCDate()).slice(-2);
  }
  function datesOf(s, childId) {
    var a = s[bucketKey(childId)];
    return Array.isArray(a) ? a.filter(validDate) : [];
  }

  function dates(childId) { return datesOf(read(), childId).slice().sort(); }
  function hasAny(childId) { return datesOf(read(), childId).length > 0; }

  /* 记今天（本地日期）学过；同一天重复调用只留一条。 */
  function mark(childId, now) {
    var s = read();
    var key = bucketKey(childId);
    var list = datesOf(s, key);
    var today = dateStr(now == null ? Date.now() : now);
    if (list.indexOf(today) < 0) list.push(today);
    list = list.filter(function (d, i) { return list.indexOf(d) === i; }).sort();
    s[key] = list;
    return write(s);
  }

  /* 连续学习天数：从今天往回连续；今天还没学，则从昨天往回数（昨天学过就还不算断）。 */
  function streak(childId, now) {
    var set = {};
    datesOf(read(), childId).forEach(function (d) { set[d] = true; });
    var day = utcDay(dateStr(now == null ? Date.now() : now));
    if (!set[utcStr(day)]) day -= DAY_MS;
    var n = 0;
    while (set[utcStr(day)]) { n++; day -= DAY_MS; }
    return n;
  }

  window.CnmActivity = { KEY: KEY, GUEST: GUEST, mark: mark, dates: dates, hasAny: hasAny, streak: streak, dateStr: dateStr };
})();
