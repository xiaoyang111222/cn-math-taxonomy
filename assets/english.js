/* 英语每日一句的进度存储与解锁 / 复习规则。只读写 localStorage（cnmEnglish.v1），不上传、不需要账号；登录后由 sync.js 同步。
 * 结构 { [孩子id 或 guest]: { done: { [day]: {at, checks} }, reviews: { [day]: {dueOrd, doneOrds: []} } } }。
 * 解锁按进度不按日历：下一句 = 最小的未学 day；一个自然日只学 1 句新句。
 * 旧句复习按「完成序号」计：第 n0 句完成后，在学到第 n0+2、n0+4、n0+7、n0+15 句的那天各回炉一次，不占新句名额。window.CnmEnglish。 */
(function () {
  'use strict';
  var KEY = 'cnmEnglish.v1';
  var GUEST = 'guest';
  var TOTAL = 30;
  var OFFSETS = [2, 4, 7, 15];
  var REVIEW_CAP = 5;
  var WEEK_MS = 7 * 24 * 60 * 60 * 1000;
  var CHECKS = ['guess', 'order', 'build'];

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
  function isObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }

  function bucket(s, childId) {
    var b = s[bucketKey(childId)];
    if (!isObj(b)) b = {};
    return { done: isObj(b.done) ? b.done : {}, reviews: isObj(b.reviews) ? b.reviews : {} };
  }
  function progress(childId) { return bucket(read(), childId); }
  function doneDays(b) {
    return Object.keys(b.done).map(Number).filter(function (d) { return d >= 1 && d <= TOTAL && isObj(b.done[d]); });
  }
  function doneCount(childId) { return doneDays(progress(childId)).length; }
  function hasProgress(childId) { return doneCount(childId) > 0; }

  function dateStr(ms) {
    var d = new Date(ms);
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function nextUnlearned(b) {
    for (var d = 1; d <= TOTAL; d++) if (!isObj(b.done[d])) return d;
    return null;
  }
  function checksComplete(checks) {
    return isObj(checks) && CHECKS.every(function (k) { return checks[k] === true; });
  }

  /* 今日状态：
   * day = 今天要学（或今天刚学完）的那一句，学完 30 句后为 null；completedToday = 今天已经学完新句；
   * nextDay = 明天要学的那一句（学完当天预告用）；
   * reviews = 到期的旧句复习，最多 REVIEW_CAP 条，按到期序号从早到晚；reviewTotal = 实际到期总数。 */
  function todayState(childId, now) {
    var t = now == null ? Date.now() : now;
    var b = progress(childId);
    var days = doneDays(b);
    var n = days.length;
    var today = dateStr(t);
    var todayDone = days.filter(function (d) { return dateStr(Number(b.done[d].at) || 0) === today; });
    var completedToday = todayDone.length > 0;
    var finished = n >= TOTAL;
    var next = nextUnlearned(b);
    var day = completedToday ? Math.max.apply(null, todayDone) : next;
    var ordToday = completedToday ? n : n + 1;
    var due = [];
    Object.keys(b.reviews).forEach(function (k) {
      var r = b.reviews[k];
      var d = Number(k);
      if (!isObj(r) || !isObj(b.done[d]) || r.dueOrd == null) return;
      var dueOrd = Number(r.dueOrd);
      if (!(dueOrd > 0) || dueOrd > ordToday) return;
      var stage = Array.isArray(r.doneOrds) ? r.doneOrds.length + 1 : 1;
      if (stage > OFFSETS.length) return;
      due.push({ day: d, dueOrd: dueOrd, stage: stage });
    });
    due.sort(function (a, c) { return (a.dueOrd - c.dueOrd) || (a.day - c.day); });
    return {
      total: TOTAL, doneCount: n, finished: finished, day: finished && !completedToday ? null : day,
      completedToday: completedToday, nextDay: completedToday ? next : null,
      reviews: due.slice(0, REVIEW_CAP), reviewTotal: due.length
    };
  }

  /* 完成某天的新句：三项打卡都为 true 才算；只能完成「下一句」；已完成的再调用原样返回。
   * 返回 { ok, error, record }。 */
  function completeDay(childId, day, checks, now) {
    var t = now == null ? Date.now() : now;
    day = Number(day);
    var s = read();
    var key = bucketKey(childId);
    var b = bucket(s, key);
    if (!(day >= 1 && day <= TOTAL)) return { ok: false, error: 'day' };
    if (isObj(b.done[day])) return { ok: true, record: b.done[day], already: true };
    if (!checksComplete(checks)) return { ok: false, error: 'checks' };
    if (nextUnlearned(b) !== day) return { ok: false, error: 'locked' };
    var today = dateStr(t);
    var learnedToday = doneDays(b).some(function (d) { return dateStr(Number(b.done[d].at) || 0) === today; });
    if (learnedToday) return { ok: false, error: 'today' };
    var rec = { at: t, checks: { guess: true, order: true, build: true } };
    b.done[day] = rec;
    b.reviews[day] = { dueOrd: doneDays(b).length + OFFSETS[0], doneOrds: [] };
    s[key] = b;
    if (!write(s)) return { ok: false, error: 'storage' };
    try {
      if (window.CnmActivity && window.CnmActivity.mark) window.CnmActivity.mark(childId, t);
    } catch (e) { /* 打卡失败不影响学习进度 */ }
    return { ok: true, record: rec };
  }

  /* 完成一次旧句复习：记下这一轮，下一轮排到 n0 + 下一个间隔；四轮完成后不再到期。 */
  function completeReview(childId, day) {
    day = Number(day);
    var s = read();
    var key = bucketKey(childId);
    var b = bucket(s, key);
    var r = b.reviews[day];
    if (!isObj(r) || !isObj(b.done[day]) || r.dueOrd == null) return false;
    var done = Array.isArray(r.doneOrds) ? r.doneOrds.slice() : [];
    if (done.length >= OFFSETS.length) return false;
    var n0 = Number(r.dueOrd) - OFFSETS[done.length];
    done.push(Number(r.dueOrd));
    b.reviews[day] = { dueOrd: done.length >= OFFSETS.length ? null : n0 + OFFSETS[done.length], doneOrds: done };
    s[key] = b;
    return write(s);
  }

  /* 最近 7 天（含此刻）完成的新句天数，与周报的「本周」同口径。 */
  function weekStats(childId, now) {
    var t = now == null ? Date.now() : now;
    var b = progress(childId);
    var days = doneDays(b);
    var week = days.filter(function (d) {
      var at = Number(b.done[d].at) || 0;
      return at > t - WEEK_MS && at <= t;
    }).length;
    return { days: week, total: days.length };
  }

  window.CnmEnglish = {
    KEY: KEY, GUEST: GUEST, TOTAL: TOTAL, OFFSETS: OFFSETS, REVIEW_CAP: REVIEW_CAP, CHECKS: CHECKS,
    progress: progress, doneCount: doneCount, hasProgress: hasProgress, checksComplete: checksComplete,
    todayState: todayState, completeDay: completeDay, completeReview: completeReview, weekStats: weekStats,
    dateStr: dateStr
  };
})();
