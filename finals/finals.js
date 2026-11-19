/* 期末 7 天补漏计划：选学科 + 年级，从今天起排 6 天补漏 + 第 7 天复测。
 * 只读 data/topics.json、data/dependencies.json 和本机 localStorage，不上传、不需要账号。
 * 计划存在 localStorage 的 cnmFinals.v1。window.CnmFinals（Node 里 module.exports 同一份，供测试）。 */
(function (root) {
  'use strict';
  var KEY = 'cnmFinals.v1';
  var DAYS = 7;
  var STUDY_DAYS = 6;
  var MIN_TOTAL = 21;
  var MAX_TOTAL = 28;
  var FILL_TARGET = 24;

  var SUBJECTS = [
    ['math', '数学'], ['chinese', '语文'], ['english', '英语'], ['physics', '物理'], ['chemistry', '化学'],
    ['biology', '生物'], ['history', '历史'], ['geography', '地理'], ['morality', '道德与法治'], ['science', '科学']
  ];
  var PREFIX = {
    cne_: 'english', cnp_: 'physics', cnc_: 'chinese', cns_: 'science', cnd_: 'morality',
    cnh_: 'history', cng_: 'geography', cnb_: 'biology', cnk_: 'chemistry'
  };
  var SEMESTER_ORDER = { '上': 0, '下': 1, '全': 2 };
  var CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  var HS_GRADE = {
    english: { 10: '必修一', 11: '必修二', 12: '必修三', 13: '选必一', 14: '选必二', 15: '选必三', 16: '选必四' },
    physics: { 10: '必修一', 11: '必修二', 12: '必修三', 13: '选必一', 14: '选必二', 15: '选必三' },
    chemistry: { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' },
    history: { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' },
    geography: { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' },
    biology: { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' },
    math: { 10: '高一', 11: '高二', 12: '选必一', 13: '选必二', 14: '选必三' }
  };

  function subjectOf(t) {
    if (!t) return 'math';
    for (var i = 0; i < SUBJECTS.length; i++) if (t.subject === SUBJECTS[i][0]) return t.subject;
    return PREFIX[String(t.id || '').slice(0, 4)] || 'math';
  }
  function subjectName(s) {
    for (var i = 0; i < SUBJECTS.length; i++) if (SUBJECTS[i][0] === s) return SUBJECTS[i][1];
    return '数学';
  }
  function gradeLabel(subject, grade) {
    if (grade >= 1 && grade <= 9) return CN[grade] + '年级';
    return (HS_GRADE[subject] || HS_GRADE.math)[grade] || ('册' + grade);
  }

  /* 日期都按本机日历日处理，格式 YYYY-MM-DD。 */
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function fmtDate(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function parseDate(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ''));
    return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null;
  }
  function dayDate(startDate, i) {
    var d = parseDate(startDate);
    if (!d) return null;
    return new Date(d.getFullYear(), d.getMonth(), d.getDate() + i);
  }
  function isExpired(plan, now) {
    var last = dayDate(plan.startDate, DAYS - 1);
    return !last || fmtDate(now || new Date()) > fmtDate(last);
  }
  function todayIndex(plan, now) {
    var today = fmtDate(now || new Date());
    for (var i = 0; i < DAYS; i++) if (fmtDate(dayDate(plan.startDate, i)) === today) return i;
    return -1;
  }

  /* 全学科先修拓扑序：只看本学科、非外部节点之间的边；同时可选时年级低、学期靠前、文件顺序靠前的先出。 */
  function topoRanks(list, deps) {
    var index = {};
    list.forEach(function (t, i) { index[t.id] = i; });
    var indeg = {};
    var out = {};
    var dependents = {};
    list.forEach(function (t) { indeg[t.id] = 0; out[t.id] = []; dependents[t.id] = 0; });
    var seen = {};
    (deps || []).forEach(function (e) {
      var a = e && e.prerequisiteId;
      var b = e && e.topicId;
      if (!(a in index) || !(b in index) || a === b) return;
      var k = a + '>' + b;
      if (seen[k]) return;
      seen[k] = true;
      out[a].push(b);
      indeg[b]++;
      dependents[a]++;
    });
    function before(x, y) {
      var tx = list[index[x]], ty = list[index[y]];
      return (tx.grade - ty.grade) ||
        ((SEMESTER_ORDER[tx.semester] || 0) - (SEMESTER_ORDER[ty.semester] || 0)) ||
        (index[x] - index[y]);
    }
    var ready = list.filter(function (t) { return indeg[t.id] === 0; }).map(function (t) { return t.id; });
    var rank = {};
    var n = 0;
    while (ready.length) {
      var best = 0;
      for (var i = 1; i < ready.length; i++) if (before(ready[i], ready[best]) < 0) best = i;
      var id = ready.splice(best, 1)[0];
      rank[id] = n++;
      out[id].forEach(function (b) { if (--indeg[b] === 0) ready.push(b); });
    }
    list.forEach(function (t) { if (!(t.id in rank)) rank[t.id] = n++; });
    return { rank: rank, dependents: dependents };
  }

  /* 把 total 个点分到 6 天，每天 3–5 个，多出来的从第 1 天起各多一个。 */
  function splitDays(ids) {
    var base = Math.floor(ids.length / STUDY_DAYS);
    var extra = ids.length % STUDY_DAYS;
    var days = [];
    var at = 0;
    for (var d = 0; d < STUDY_DAYS; d++) {
      var size = base + (d < extra ? 1 : 0);
      days.push(ids.slice(at, at + size));
      at += size;
    }
    days.push([]);
    return days;
  }

  /* wrongRows：CnmWrong.list() 的条目；blindRows：CnmBlind.list() 的条目。
   * 优先级：错题本知识点（错题多的在前）→ 诊断薄弱 / 不稳 → 年级知识点按被依赖度补齐。 */
  function buildPlan(opts) {
    var subject = opts.subject;
    var grade = Number(opts.grade);
    var now = opts.now || new Date();
    var list = (opts.topics || []).filter(function (t) { return !t.external && subjectOf(t) === subject; });
    var byId = {};
    list.forEach(function (t) { byId[t.id] = t; });
    var topo = topoRanks(list, opts.deps);

    var picked = [];
    var inPlan = {};
    function take(id) {
      if (!byId[id] || inPlan[id] || picked.length >= MAX_TOTAL) return;
      inPlan[id] = true;
      picked.push(id);
    }

    var wrongCount = {};
    var wrongLast = {};
    (opts.wrongRows || []).forEach(function (e) {
      if (!e || !e.topicId || !byId[e.topicId]) return;
      wrongCount[e.topicId] = (wrongCount[e.topicId] || 0) + 1;
      wrongLast[e.topicId] = Math.max(wrongLast[e.topicId] || 0, Number(e.ts) || 0);
    });
    Object.keys(wrongCount).sort(function (a, b) {
      return (wrongCount[b] - wrongCount[a]) || (wrongLast[b] - wrongLast[a]) || (topo.rank[a] - topo.rank[b]);
    }).forEach(take);

    (opts.blindRows || []).forEach(function (r) {
      if (r && (r.status === 'weak' || r.status === 'shaky')) take(r.id);
    });

    if (picked.length < MIN_TOTAL) {
      var fillers = list.filter(function (t) { return !inPlan[t.id] && t.grade === grade; });
      for (var g = grade - 1; fillers.length + picked.length < MIN_TOTAL && g >= 1; g--) {
        fillers = fillers.concat(list.filter(function (t) { return !inPlan[t.id] && t.grade === g; }));
      }
      fillers.sort(function (a, b) {
        return ((grade - a.grade) - (grade - b.grade)) ||
          (topo.dependents[b.id] - topo.dependents[a.id]) || (topo.rank[a.id] - topo.rank[b.id]);
      });
      var want = Math.max(MIN_TOTAL, Math.min(FILL_TARGET, picked.length + fillers.length));
      for (var i = 0; i < fillers.length && picked.length < want; i++) take(fillers[i].id);
    }

    picked.sort(function (a, b) { return topo.rank[a] - topo.rank[b]; });
    return {
      subject: subject,
      grade: grade,
      startDate: fmtDate(now),
      days: splitDays(picked),
      done: [false, false, false, false, false, false, false],
      createdAt: now.getTime()
    };
  }

  function validPlan(p) {
    if (!p || typeof p !== 'object' || !p.subject || !parseDate(p.startDate)) return false;
    if (!Array.isArray(p.days) || p.days.length !== DAYS || !Array.isArray(p.done) || p.done.length !== DAYS) return false;
    return p.days.every(function (d) { return Array.isArray(d); });
  }
  function loadPlan(storage) {
    try {
      var p = JSON.parse(storage.getItem(KEY));
      return validPlan(p) ? p : null;
    } catch (e) { return null; }
  }
  function savePlan(storage, plan) {
    try { storage.setItem(KEY, JSON.stringify(plan)); return true; } catch (e) { return false; }
  }
  function clearPlan(storage) {
    try { storage.removeItem(KEY); } catch (e) { /* 隐私模式等 */ }
  }
  function doneCount(plan) { return plan.done.filter(Boolean).length; }

  function practiceHref(id, subject) {
    return '../diagnose/?' + (subject !== 'math' ? 'subject=' + encodeURIComponent(subject) + '&' : '') + 'target=' + encodeURIComponent(id);
  }
  function retestHref(plan) {
    var ids = [];
    plan.days.forEach(function (d) { ids = ids.concat(d); });
    return '../diagnose/?' + (plan.subject !== 'math' ? 'subject=' + encodeURIComponent(plan.subject) + '&' : '') +
      'target=' + ids.map(encodeURIComponent).join(',');
  }

  var api = {
    KEY: KEY, SUBJECTS: SUBJECTS, subjectOf: subjectOf, subjectName: subjectName, gradeLabel: gradeLabel,
    fmtDate: fmtDate, parseDate: parseDate, dayDate: dayDate, isExpired: isExpired, todayIndex: todayIndex,
    buildPlan: buildPlan, splitDays: splitDays, loadPlan: loadPlan, savePlan: savePlan, clearPlan: clearPlan,
    doneCount: doneCount, practiceHref: practiceHref, retestHref: retestHref
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CnmFinals = api;

  /* ------------------------------------------------------------ 页面 */
  if (typeof document === 'undefined' || !document.getElementById('finals-root')) return;

  var WEEK = ['日', '一', '二', '三', '四', '五', '六'];
  var host = document.getElementById('finals-root');
  var data = null;
  var formState = { subject: 'math', grade: null };

  function h(tag, attrs) {
    var el = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'text') el.textContent = attrs[k];
      else if (k.indexOf('on') === 0) el.addEventListener(k.slice(2), attrs[k]);
      else el.setAttribute(k, attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null) continue;
      if (Array.isArray(c)) c.forEach(function (x) { el.appendChild(x); });
      else el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return el;
  }
  function dateText(d) { return (d.getMonth() + 1) + '月' + d.getDate() + '日 周' + WEEK[d.getDay()]; }

  function currentChildId() {
    var CC = root.CnmChildren;
    var cur = CC && CC.current ? CC.current() : null;
    return cur ? cur.id : 'guest';
  }
  function wrongRows() { return root.CnmWrong ? root.CnmWrong.list(currentChildId()) : []; }
  function blindRows(subject) { return root.CnmBlind ? root.CnmBlind.list({ subject: subject }) : []; }

  function gradesOf(subject) {
    var seen = {};
    data.topics.forEach(function (t) {
      if (!t.external && subjectOf(t) === subject && typeof t.grade === 'number') seen[t.grade] = true;
    });
    return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; });
  }
  function nameOf(id) {
    var t = data.byId[id];
    return t ? t.name : id;
  }

  function defaultGrade(subject, grades) {
    var rows = wrongRows().filter(function (e) { return (e.subject || 'math') === subject; });
    var ids = rows.map(function (e) { return e.topicId; }).concat(blindRows(subject).map(function (r) { return r.id; }));
    for (var i = 0; i < ids.length; i++) {
      var t = data.byId[ids[i]];
      if (t && grades.indexOf(t.grade) >= 0) return t.grade;
    }
    return grades[0];
  }

  function renderForm(note) {
    var grades = gradesOf(formState.subject);
    if (grades.indexOf(formState.grade) < 0) formState.grade = defaultGrade(formState.subject, grades);
    var subjectSel = h('select', { id: 'f-subject', 'aria-label': '学科' });
    SUBJECTS.forEach(function (s) {
      var o = h('option', { value: s[0], text: s[1] });
      if (s[0] === formState.subject) o.selected = true;
      subjectSel.appendChild(o);
    });
    var gradeSel = h('select', { id: 'f-grade', 'aria-label': '年级' });
    grades.forEach(function (g) {
      var o = h('option', { value: String(g), text: gradeLabel(formState.subject, g) });
      if (g === formState.grade) o.selected = true;
      gradeSel.appendChild(o);
    });
    subjectSel.addEventListener('change', function () { formState.subject = subjectSel.value; formState.grade = null; renderForm(); });
    gradeSel.addEventListener('change', function () { formState.grade = Number(gradeSel.value); });

    var wrongN = {};
    wrongRows().forEach(function (e) { if (e.topicId && data.byId[e.topicId] && subjectOf(data.byId[e.topicId]) === formState.subject) wrongN[e.topicId] = 1; });
    var blindN = blindRows(formState.subject).filter(function (r) { return r.status === 'weak' || r.status === 'shaky'; }).length;
    var hint = Object.keys(wrongN).length || blindN
      ? '本机错题本里有 ' + Object.keys(wrongN).length + ' 个' + subjectName(formState.subject) + '知识点、诊断里有 ' + blindN + ' 个薄弱 / 不稳点，会优先排进计划，不够的用该年级知识点补齐。'
      : '本机还没有' + subjectName(formState.subject) + '的错题或诊断记录，计划会按年级知识点的先修顺序排。先做一次诊断，计划会更准。';

    host.replaceChildren(
      h('div', { class: 'fin-card' },
        h('h2', { text: '生成补漏计划' }),
        note ? h('p', { class: 'fin-note', text: note }) : null,
        h('div', { class: 'fin-form' },
          h('label', { for: 'f-subject', text: '学科' }), subjectSel,
          h('label', { for: 'f-grade', text: '年级' }), gradeSel),
        h('p', { class: 'muted', id: 'f-hint', text: hint }),
        h('button', { class: 'primary btn-lg', id: 'f-go', type: 'button', onclick: generate, text: '生成 7 天计划' })));
  }

  function generate() {
    var plan = buildPlan({
      topics: data.topics, deps: data.deps, subject: formState.subject, grade: formState.grade,
      wrongRows: wrongRows().filter(function (e) { return (e.subject || 'math') === formState.subject; }),
      blindRows: blindRows(formState.subject)
    });
    savePlan(localStorage, plan);
    renderPlan(plan);
  }

  function renderPlan(plan) {
    var today = todayIndex(plan);
    var total = doneCount(plan);
    var count = plan.days.reduce(function (n, d) { return n + d.length; }, 0);
    var start = dayDate(plan.startDate, 0);
    var end = dayDate(plan.startDate, DAYS - 1);

    var head = h('div', { class: 'fin-card fin-head' },
      h('h2', { text: subjectName(plan.subject) + ' · ' + gradeLabel(plan.subject, plan.grade) }),
      h('p', { class: 'muted', text: dateText(start) + ' 至 ' + dateText(end) + ' · 共 ' + count + ' 个知识点' }),
      h('div', { class: 'fin-progress', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(DAYS), 'aria-valuenow': String(total) },
        h('span', { style: 'width:' + Math.round(total / DAYS * 100) + '%' })),
      h('p', { class: 'fin-progress-text', id: 'fin-progress-text', text: '已打卡 ' + total + '/' + DAYS }));

    var cards = plan.days.map(function (ids, i) {
      var date = dayDate(plan.startDate, i);
      var done = !!plan.done[i];
      var cls = 'fin-day' + (done ? ' is-done' : '') + (i === today ? ' is-today' : '');
      var title = h('h3', null, '第 ' + (i + 1) + ' 天' + (i === DAYS - 1 ? ' · 复测日' : ''),
        h('span', { class: 'fin-date', text: dateText(date) + (i === today ? ' · 今天' : '') }));
      var body;
      if (i === DAYS - 1) {
        body = h('div', null,
          h('p', { text: '前 6 天不排新知识点。今天把这 ' + count + ' 个知识点复测一遍：答对的说明补上了，仍然答错的会在结果里标成薄弱，再针对性补一补。' }),
          h('a', { class: 'btn primary', href: retestHref(plan), text: '开始复测' }));
      } else {
        body = h('ul', { class: 'fin-kps' }, ids.map(function (id) {
          return h('li', null,
            h('span', { class: 'fin-kp-name', text: nameOf(id) }),
            h('span', { class: 'fin-links' },
              h('a', { href: '../kp/' + encodeURIComponent(id), text: '看讲解' }),
              h('a', { href: practiceHref(id, plan.subject), text: '去练题' })));
        }));
      }
      var btn = h('button', {
        type: 'button', class: done ? 'fin-check on' : 'fin-check primary', 'aria-pressed': done ? 'true' : 'false',
        onclick: function () { plan.done[i] = !plan.done[i]; savePlan(localStorage, plan); renderPlan(plan); },
        text: done ? '已完成 ✓' : (i === today ? '完成今天' : '完成这一天')
      });
      return h('section', { class: cls, id: 'day-' + (i + 1) }, title, body, h('div', { class: 'fin-foot' }, btn));
    });

    var again = h('button', {
      type: 'button', id: 'fin-reset',
      onclick: function () {
        if (!confirm('重新生成会清掉当前计划和打卡记录，确定吗？')) return;
        clearPlan(localStorage);
        formState.subject = plan.subject;
        formState.grade = plan.grade;
        renderForm();
      },
      text: '重新生成'
    });
    host.replaceChildren.apply(host, [head].concat(cards, [h('p', { class: 'fin-reset' }, again)]));
  }

  function show() {
    var plan = loadPlan(localStorage);
    if (plan && !isExpired(plan)) { renderPlan(plan); return; }
    if (plan) {
      clearPlan(localStorage);
      formState.subject = plan.subject;
      renderForm('上一个计划（' + subjectName(plan.subject) + ' · ' + gradeLabel(plan.subject, plan.grade) + '，' + plan.startDate + ' 开始）已经结束，可以重新生成一个。');
      return;
    }
    renderForm();
  }

  function init() {
    var q = new URLSearchParams(location.search).get('subject');
    if (q && SUBJECTS.some(function (s) { return s[0] === q; })) formState.subject = q;
    Promise.all([
      fetch('../data/topics.json').then(function (r) { if (!r.ok) throw new Error('topics ' + r.status); return r.json(); }),
      fetch('../data/dependencies.json').then(function (r) { if (!r.ok) throw new Error('dependencies ' + r.status); return r.json(); })
    ]).then(function (res) {
      data = { topics: res[0], deps: res[1], byId: {} };
      data.topics.forEach(function (t) { data.byId[t.id] = t; });
      show();
    }).catch(function (e) {
      host.replaceChildren(h('div', { class: 'fin-card' },
        h('p', { class: 'fin-note', text: '知识点数据加载失败：' + (e && e.message || e) + '。请检查网络后刷新。' })));
    });
  }
  init();
})(typeof window !== 'undefined' ? window : globalThis);
