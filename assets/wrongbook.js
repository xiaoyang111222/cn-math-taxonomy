/* 错题本：诊断时答错 / 不会的题按孩子收进本机，供错题本页查看、重做、打印。
 * 只读写 localStorage，不上传、不需要账号。题目内容存快照，错题本页不必加载题库。window.CnmWrong。 */
(function () {
  'use strict';
  var KEY = 'cnmWrong.v1';
  var MAX_PER_BUCKET = 300;
  var GUEST = 'guest';
  var MAX_TEXT = 4000;
  var DAY_MS = 24 * 60 * 60 * 1000;
  /* 复测间隔（天），下标是轮次 stage。与 api/lib.js 的 INTERVALS_DAYS 必须同值（周报用它算「待复测」）。 */
  var INTERVALS_DAYS = [1, 3, 7, 15];
  var LAST_STAGE = INTERVALS_DAYS.length - 1;
  var SUBJECT_NAME = {
    math: '数学', chinese: '语文', science: '科学',
    morality: '道德与法治', history: '历史', geography: '地理', biology: '生物', chemistry: '化学', english: '英语', physics: '物理', politics: '思想政治'
  };

  function read(k, fallback) {
    try {
      var v = JSON.parse(localStorage.getItem(k));
      return v == null ? fallback : v;
    } catch (e) { return fallback; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; }
  }

  function store() {
    var s = read(KEY, null);
    if (!s || typeof s !== 'object' || Array.isArray(s)) return {};
    return s;
  }
  function bucketKey(childId) { return childId ? String(childId) : GUEST; }
  function bucketOf(s, childId) {
    var b = s[bucketKey(childId)];
    return Array.isArray(b) ? b.filter(function (e) { return e && typeof e === 'object' && e.qid; }) : [];
  }
  function text(v) { return v == null ? '' : String(v).slice(0, MAX_TEXT); }
  function cleanChoices(list) {
    if (!Array.isArray(list) || !list.length) return null;
    var out = [];
    list.forEach(function (c) {
      if (c && c.key != null) out.push({ key: text(c.key), text: text(c.text) });
    });
    return out.length ? out : null;
  }

  /* entry.childId 决定写入哪个孩子的桶（没有则 guest），不会存进条目。
   * 同一孩子同一 qid 已存在：更新 chosen / kind / ts，count + 1。每桶最多 300 条，超了丢最旧的。 */
  function record(entry) {
    if (!entry || !entry.qid) return false;
    var s = store();
    var key = bucketKey(entry.childId);
    var rows = bucketOf(s, key);
    var qid = String(entry.qid);
    var kind = entry.kind === 'skip' ? 'skip' : 'wrong';
    var ts = Number(entry.ts) > 0 ? Number(entry.ts) : Date.now();
    var hit = null;
    rows.forEach(function (e) { if (e.qid === qid) hit = e; });
    if (hit) {
      hit.chosen = text(entry.chosen);
      hit.kind = kind;
      hit.ts = ts;
      hit.count = (Number(hit.count) > 0 ? Number(hit.count) : 1) + 1;
      hit.stage = 0;
      hit.dueAt = ts + DAY_MS;
      hit.done = false;
      hit.reviewedAt = ts;
    } else {
      rows.push({
        qid: qid,
        topicId: text(entry.topicId),
        topic: text(entry.topic),
        subject: text(entry.subject) || 'math',
        prompt: text(entry.prompt),
        choices: cleanChoices(entry.choices),
        answer: text(entry.answer),
        explanation: entry.explanation ? text(entry.explanation) : '',
        chosen: text(entry.chosen),
        kind: kind,
        ts: ts,
        count: 1,
        stage: 0,
        dueAt: ts + DAY_MS,
        done: false,
        reviewedAt: ts
      });
    }
    rows.sort(function (a, b) { return (a.ts || 0) - (b.ts || 0); });
    if (rows.length > MAX_PER_BUCKET) rows = rows.slice(rows.length - MAX_PER_BUCKET);
    s[key] = rows;
    return write(KEY, s);
  }

  /* 最近答错的在前。 */
  function list(childId) {
    return bucketOf(store(), childId).sort(function (a, b) { return (b.ts || 0) - (a.ts || 0); });
  }
  function count(childId) { return bucketOf(store(), childId).length; }

  function remove(childId, qid) {
    var s = store();
    var key = bucketKey(childId);
    var rows = bucketOf(s, key);
    var left = rows.filter(function (e) { return e.qid !== String(qid); });
    if (left.length === rows.length) return false;
    s[key] = left;
    return write(KEY, s);
  }

  /* ---- 到期复测。stage / dueAt / done 都可缺省（老条目）：stage 0、dueAt = ts + 1 天、done false。
   * 与 api/lib.js 的 computeDue 同规则。 */
  function stageOf(e) {
    var n = Math.floor(Number(e && e.stage));
    return n >= 0 ? Math.min(n, LAST_STAGE) : 0;
  }
  function dueAtOf(e) {
    var d = Number(e && e.dueAt);
    return d > 0 ? d : (Number(e && e.ts) || 0) + DAY_MS;
  }
  function isDue(e, now) {
    return !!e && !e.done && dueAtOf(e) <= (now == null ? Date.now() : now);
  }

  function dueList(childId, now) {
    var t = now == null ? Date.now() : now;
    return bucketOf(store(), childId).filter(function (e) { return isDue(e, t); })
      .sort(function (a, b) { return dueAtOf(a) - dueAtOf(b); });
  }

  /* 全部孩子（含 guest）合计的到期数，首页用。 */
  function dueTotal(now) {
    var s = store();
    var t = now == null ? Date.now() : now;
    var n = 0;
    Object.keys(s).forEach(function (k) {
      bucketOf(s, k).forEach(function (e) { if (isDue(e, t)) n++; });
    });
    return n;
  }

  /* 有到期题的桶（孩子 / guest）个数，首页据此判断合计数是否跨孩子。 */
  function dueBuckets(now) {
    var s = store();
    var t = now == null ? Date.now() : now;
    return Object.keys(s).filter(function (k) {
      return bucketOf(s, k).some(function (e) { return isDue(e, t); });
    }).length;
  }

  /* reviewedAt：复测进度（stage / dueAt / done）最后一次变动的时间，record 与 review 都会更新，同步合并按它判断谁的进度更新。 */
  /* 通过：stage + 1，原 stage 为最后一轮则毕业；未过：stage 不变，明天再测。返回更新后的条目，找不到返回 null。 */
  function review(childId, qid, passed, now) {
    var s = store();
    var key = bucketKey(childId);
    var rows = bucketOf(s, key);
    var hit = null;
    rows.forEach(function (e) { if (e.qid === String(qid)) hit = e; });
    if (!hit) return null;
    if (!hit.done) {
      var t = now == null ? Date.now() : now;
      var stage = stageOf(hit);
      hit.reviewedAt = t;
      if (passed) {
        if (stage >= LAST_STAGE) {
          hit.stage = LAST_STAGE;
          hit.done = true;
          delete hit.dueAt;
        } else {
          hit.stage = stage + 1;
          hit.dueAt = t + INTERVALS_DAYS[stage + 1] * DAY_MS;
          hit.done = false;
        }
      } else {
        hit.stage = stage;
        hit.dueAt = t + DAY_MS;
        hit.done = false;
      }
    }
    s[key] = rows;
    return write(KEY, s) ? hit : null;
  }

  /* 选择题条目的正确选项 key：answer 存的是「B. 文字」。 */
  function answerKey(e) {
    var m = /^([^.\s]+)\./.exec(String((e && e.answer) || ''));
    return m ? m[1] : String((e && e.answer) || '').trim();
  }

  /* 条目行上的复测状态小字。 */
  function reviewLabel(e, now) {
    if (e.done) return '已毕业 ✓';
    if (isDue(e, now)) return '第 ' + (stageOf(e) + 1) + ' 轮 · 已到期';
    var d = new Date(dueAtOf(e));
    return '下次复测 ' + (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日';
  }

  function clear(childId) {
    var s = store();
    var key = bucketKey(childId);
    if (!(key in s)) return true;
    delete s[key];
    return write(KEY, s);
  }

  window.CnmWrong = {
    KEY: KEY,
    GUEST: GUEST,
    MAX_PER_BUCKET: MAX_PER_BUCKET,
    SUBJECT_NAME: SUBJECT_NAME,
    record: record,
    list: list,
    count: count,
    remove: remove,
    clear: clear,
    INTERVALS_DAYS: INTERVALS_DAYS,
    dueAtOf: dueAtOf,
    isDue: isDue,
    dueList: dueList,
    dueTotal: dueTotal,
    dueBuckets: dueBuckets,
    review: review,
    answerKey: answerKey,
    reviewLabel: reviewLabel
  };
})();
