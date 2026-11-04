/* 站内错题盲区汇总：把本机诊断结果里的薄弱 / 不稳按知识点聚合，供首页、诊断页、档案页一键再测。
 * 只读写 localStorage，不上传、不需要账号。window.CnmBlind。 */
(function () {
  'use strict';
  var KEY = 'cnmBlind.local.v1';
  var MAX_TOPICS = 200;
  var SUBJECT_NAME = {
    math: '数学', chinese: '语文', science: '科学',
    morality: '道德与法治', history: '历史', geography: '地理', biology: '生物', chemistry: '化学', english: '英语', physics: '物理'
  };
  var SESSION_KEYS = [
    { key: 'cnmDiagnose.session.v2', subject: 'math' },
    { key: 'cneDiagnose.session.v2', subject: 'english' },
    { key: 'cnpDiagnose.session.v2', subject: 'physics' },
    { key: 'cncDiagnose.session.v2', subject: 'chinese' },
    { key: 'cnsDiagnose.session.v1', subject: 'science' },
    { key: 'cndDiagnose.session.v1', subject: 'morality' },
    { key: 'cnhDiagnose.session.v1', subject: 'history' },
    { key: 'cngDiagnose.session.v1', subject: 'geography' },
    { key: 'cnbDiagnose.session.v1', subject: 'biology' },
    { key: 'cnkDiagnose.session.v1', subject: 'chemistry' }
  ];

  function read(k, fallback) {
    try {
      var v = JSON.parse(localStorage.getItem(k));
      return v == null ? fallback : v;
    } catch (e) { return fallback; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; }
  }

  function subjectOfId(id) {
    id = String(id || '');
    if (id.indexOf('cne_') === 0) return 'english';
    if (id.indexOf('cnp_') === 0) return 'physics';
    if (id.indexOf('cnc_') === 0) return 'chinese';
    if (id.indexOf('cns_') === 0) return 'science';
    if (id.indexOf('cnd_') === 0) return 'morality';
    if (id.indexOf('cnh_') === 0) return 'history';
    if (id.indexOf('cng_') === 0) return 'geography';
    if (id.indexOf('cnb_') === 0) return 'biology';
    if (id.indexOf('cnk_') === 0) return 'chemistry';
    return 'math';
  }

  function emptyStore() { return { v: 1, byId: {} }; }

  function store() {
    var s = read(KEY, null);
    if (!s || typeof s !== 'object' || Array.isArray(s) || s.v !== 1 || !s.byId || typeof s.byId !== 'object') {
      return emptyStore();
    }
    return s;
  }

  function prune(byId) {
    var ids = Object.keys(byId);
    if (ids.length <= MAX_TOPICS) return byId;
    ids.sort(function (a, b) {
      return String(byId[b].lastAt || '').localeCompare(String(byId[a].lastAt || ''));
    });
    var keep = {};
    ids.slice(0, MAX_TOPICS).forEach(function (id) { keep[id] = byId[id]; });
    return keep;
  }

  function tallyWrongs(answers) {
    var out = {};
    (answers || []).forEach(function (a) {
      if (!a || !a.id) return;
      if (a.result === 'wrong' || a.result === 'skip') out[a.id] = (out[a.id] || 0) + 1;
    });
    return out;
  }

  /* 诊断结果页调用：无论有没有孩子档案，都把本轮薄弱 / 不稳写入本机盲区账本。 */
  function noteResult(payload) {
    if (!payload || payload.demo) return false;
    var s = store();
    var now = new Date().toISOString();
    var wrongs = tallyWrongs(payload.answers);
    var rootSet = {};
    (payload.roots || []).forEach(function (id) { rootSet[id] = true; });
    var subject = payload.subject || 'math';

    function put(ids, status) {
      (ids || []).forEach(function (id) {
        if (!id) return;
        var prev = s.byId[id] || { id: id, hits: 0, wrongs: 0 };
        var bump = status === 'weak' || status === 'shaky';
        s.byId[id] = {
          id: id,
          subject: subject || subjectOfId(id),
          status: status,
          root: status === 'weak' && !!rootSet[id],
          hits: (prev.hits || 0) + (bump ? 1 : 0),
          wrongs: (prev.wrongs || 0) + (wrongs[id] || 0),
          lastAt: now,
          lastLabel: payload.label || prev.lastLabel || '',
          lastKey: payload.key || prev.lastKey || ''
        };
      });
    }

    put(payload.mastered, 'mastered');
    put(payload.shaky, 'shaky');
    put(payload.weak, 'weak');
    s.byId = prune(s.byId);
    return write(KEY, s);
  }

  function fromLedger(subject) {
    var by = store().byId;
    var out = {};
    Object.keys(by).forEach(function (id) {
      var row = by[id];
      if (!row || (row.status !== 'weak' && row.status !== 'shaky')) return;
      if (subject && row.subject !== subject && subjectOfId(id) !== subject) return;
      out[id] = {
        id: id,
        subject: row.subject || subjectOfId(id),
        status: row.status,
        root: !!row.root,
        hits: row.hits || 0,
        wrongs: row.wrongs || 0,
        at: row.lastAt || '',
        label: row.lastLabel || '',
        source: 'local'
      };
    });
    return out;
  }

  function fromChild(subject) {
    var CC = typeof window !== 'undefined' ? window.CnmChildren : null;
    if (!CC || !CC.current) return {};
    var cur = CC.current();
    if (!cur) return {};
    var latest = CC.latestStatus(cur.id, subject || null);
    var out = {};
    Object.keys(latest).forEach(function (id) {
      var info = latest[id];
      if (!info || (info.status !== 'weak' && info.status !== 'shaky')) return;
      out[id] = {
        id: id,
        subject: info.subject || subjectOfId(id),
        status: info.status,
        root: !!info.root,
        hits: 1,
        wrongs: 0,
        at: info.at || '',
        label: info.label || '',
        source: 'child'
      };
    });
    return out;
  }

  /* 未结束的诊断会话：把答错过的知识点先标成待复测（不覆盖已有更明确的薄弱结论）。 */
  function fromSessions(subject) {
    var out = {};
    SESSION_KEYS.forEach(function (item) {
      if (subject && item.subject !== subject) return;
      var sess = read(item.key, null);
      if (!sess || !Array.isArray(sess.answers) || !sess.answers.length) return;
      var wrongs = tallyWrongs(sess.answers);
      Object.keys(wrongs).forEach(function (id) {
        if (out[id] && out[id].status === 'weak') {
          out[id].wrongs += wrongs[id];
          return;
        }
        out[id] = {
          id: id,
          subject: item.subject,
          status: 'shaky',
          root: false,
          hits: 1,
          wrongs: wrongs[id],
          at: sess.savedAt || '',
          label: sess.label || '未完成的诊断',
          source: 'session'
        };
      });
    });
    return out;
  }

  function mergeMaps() {
    var maps = [].slice.call(arguments);
    var out = {};
    maps.forEach(function (map) {
      Object.keys(map || {}).forEach(function (id) {
        var row = map[id];
        var prev = out[id];
        if (!prev) {
          out[id] = Object.assign({}, row);
          return;
        }
        var newer = String(row.at || '').localeCompare(String(prev.at || '')) >= 0;
        if (newer) {
          out[id] = Object.assign({}, row, {
            hits: Math.max(prev.hits || 0, row.hits || 0),
            wrongs: Math.max(prev.wrongs || 0, row.wrongs || 0)
          });
        } else {
          prev.hits = Math.max(prev.hits || 0, row.hits || 0);
          prev.wrongs = Math.max(prev.wrongs || 0, row.wrongs || 0);
        }
      });
    });
    return out;
  }

  /* 汇总本机盲区。优先：孩子档案最新状态 + 本机账本 + 未完成会话答错。 */
  function list(opts) {
    opts = opts || {};
    var subject = opts.subject || null;
    var merged = mergeMaps(fromSessions(subject), fromLedger(subject), fromChild(subject));
    var rows = Object.keys(merged).map(function (id) { return merged[id]; });
    rows.sort(function (a, b) {
      var ra = (a.status === 'weak' ? 0 : 2) + (a.root ? 0 : 1);
      var rb = (b.status === 'weak' ? 0 : 2) + (b.root ? 0 : 1);
      return ra - rb || (b.wrongs || 0) - (a.wrongs || 0) || (b.hits || 0) - (a.hits || 0) ||
        String(b.at || '').localeCompare(String(a.at || ''));
    });
    if (opts.limit && opts.limit > 0) rows = rows.slice(0, opts.limit);
    return rows;
  }

  function count(opts) {
    return list(opts || {}).length;
  }

  function diagnoseHref(ids, subject, base) {
    ids = (Array.isArray(ids) ? ids : [ids]).filter(Boolean);
    if (!ids.length) return (base || 'diagnose/') + (subject && subject !== 'math' ? '?subject=' + subject : '');
    var sub = subject || subjectOfId(ids[0]);
    var q = 'target=' + ids.map(encodeURIComponent).join(',');
    if (sub && sub !== 'math') q = 'subject=' + encodeURIComponent(sub) + '&' + q;
    return (base || 'diagnose/') + '?' + q;
  }

  function historyHref(childId, base) {
    var path = (base || 'children/') + 'history.html';
    if (childId) path += '?child=' + encodeURIComponent(childId);
    return path;
  }

  function clear() { return write(KEY, emptyStore()); }

  window.CnmBlind = {
    KEY: KEY,
    SUBJECT_NAME: SUBJECT_NAME,
    SESSION_KEYS: SESSION_KEYS.map(function (x) { return x.key; }),
    subjectOfId: subjectOfId,
    noteResult: noteResult,
    list: list,
    count: count,
    diagnoseHref: diagnoseHref,
    historyHref: historyHref,
    clear: clear
  };
})();
