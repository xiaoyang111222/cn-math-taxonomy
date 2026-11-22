/* 错题本：诊断时答错 / 不会的题按孩子收进本机，供错题本页查看、重做、打印。
 * 只读写 localStorage，不上传、不需要账号。题目内容存快照，错题本页不必加载题库。window.CnmWrong。 */
(function () {
  'use strict';
  var KEY = 'cnmWrong.v1';
  var MAX_PER_BUCKET = 300;
  var GUEST = 'guest';
  var MAX_TEXT = 4000;
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
        count: 1
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
    clear: clear
  };
})();
