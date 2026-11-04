/* 诊断小工具界面。核心逻辑全部在 engine.js，这里只负责数据加载、渲染与本地存储。 */
(function () {
  'use strict';
  const E = window.DiagEngine;
  const LS_SESSION = 'cnmDiagnose.session.v2';
  const LS_SESSION_EN = 'cneDiagnose.session.v2';
  const LS_SESSION_PHY = 'cnpDiagnose.session.v2';
  const LS_SESSION_ZH = 'cncDiagnose.session.v2';
  const LS_SESSION_SCI = 'cnsDiagnose.session.v1';
  const LS_SESSION_MOR = 'cndDiagnose.session.v1';
  const LS_SESSION_HIS = 'cnhDiagnose.session.v1';
  const LS_SESSION_GEO = 'cngDiagnose.session.v1';
  const LS_SESSION_BIO = 'cnbDiagnose.session.v1';
  const LS_SESSION_CHEM = 'cnkDiagnose.session.v1';
  const LS_SETTINGS = 'cnmDiagnose.settings.v2';
  const LS_SEEN = 'cnmDiagnose.seen.v1';
  const LIMIT_MIN = 8, LIMIT_MAX = 30;
  const SCREEN_MIN = 20, SCREEN_MAX = 60;
  const GRADES = '一二三四五六七八九'.split('');
  const VOLUMES = [
    ['一上', '一年级上册'], ['一下', '一年级下册'], ['二上', '二年级上册'], ['二下', '二年级下册'],
    ['三上', '三年级上册'], ['三下', '三年级下册'], ['四上', '四年级上册'], ['四下', '四年级下册'],
    ['五上', '五年级上册'], ['五下', '五年级下册'], ['六上', '六年级上册'], ['六下', '六年级下册'],
    ['七上', '七年级上册'], ['七下', '七年级下册'], ['八上', '八年级上册'], ['八下', '八年级下册'],
    ['九上', '九年级上册'], ['九下', '九年级下册'], ['九全', '九年级全一册'],
    ['必修一', '必修一 · 必修第一册'], ['必修二', '必修二 · 必修第二册'], ['必修三', '必修三 · 必修第三册'],
    ['高一', '高一 · 必修第一册'], ['高二', '高二 · 必修第二册'],
    ['选必一', '选必一 · 选择性必修第一册'], ['选必二', '选必二 · 选择性必修第二册'],
    ['选必三', '选必三 · 选择性必修第三册'], ['选必四', '选必四 · 选择性必修第四册']
  ];
  const RESULT_LABEL = { correct: '对', wrong: '错', skip: '不会' };
  const STATUS_LABEL = { mastered: '已掌握', shaky: '不稳', weak: '薄弱', unknown: '未测' };
  const DIFF_LABEL = { basic: '基础', standard: '提高', challenge: '拓展', advanced: '拓展' };
  const TYPE_LABEL = { numeric: '数值题', choice: '选择题', short: '短答题', self: '开放题', legacy: '诊断题' };

  const root = document.getElementById('root');
  let D = null;            // 数据：{topics, deps, stdById, graph, tree}
  let session = null;      // 引擎会话
  let sessionMeta = null;  // {label, chapterKey?}
  let demo = null;         // 演示模式：{oracle}
  let ui = { key: null, phase: 'ask', answer: '', verdict: null };
  let subject = 'math';
  let startQuery = '';
  let startStage = '';
  let chapterOpen = false;
  let gradeSel = '七';     // 开始页「按年级整体诊断」：年级
  let volSel = '';         // '' 整年级 / '上' / '下'
  let seedParam = null;    // URL 参数 seed：固定选题的随机种子
  let pathCy = null;
  let pathToken = 0;
  let pathTipLock = false;
  let pathExpanded = false;
  const PATH_FOLD_AT = 40;
  let shareBlobUrl = null;
  let shareToken = 0;

  /* ------------------------------------------------------------ 小工具 */
  function h(tag, attrs) {
    const el = document.createElement(tag);
    const a = attrs || {};
    Object.keys(a).forEach(function (k) {
      const v = a[k];
      if (v == null || v === false) return;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
      else if (k === 'open' || k === 'disabled' || k === 'selected' || k === 'value') el[k] = v === true ? true : v;
      else el.setAttribute(k, v === true ? '' : v);
    });
    for (let i = 2; i < arguments.length; i++) append(el, arguments[i]);
    return el;
  }
  function append(el, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { append(el, x); }); return; }
    el.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function figureEl(svg) {
    if (typeof svg !== 'string' || svg.indexOf('<svg') !== 0) return null;
    if (/<\s*script|foreignObject|<\s*image\b|https?:\/\//i.test(svg.replace('xmlns="http://www.w3.org/2000/svg"', ''))) return null;
    const wrap = h('div', { class: 'q-figure' });
    wrap.innerHTML = svg;
    const node = wrap.querySelector('svg');
    if (!node) return null;
    node.setAttribute('role', 'img');
    node.setAttribute('aria-hidden', 'true');
    node.setAttribute('focusable', 'false');
    return wrap;
  }
  function sessionKey() {
    if (subject === 'english') return LS_SESSION_EN;
    if (subject === 'physics') return LS_SESSION_PHY;
    if (subject === 'chinese') return LS_SESSION_ZH;
    if (subject === 'science') return LS_SESSION_SCI;
    if (subject === 'morality') return LS_SESSION_MOR;
    if (subject === 'history') return LS_SESSION_HIS;
    if (subject === 'geography') return LS_SESSION_GEO;
    if (subject === 'biology') return LS_SESSION_BIO;
    if (subject === 'chemistry') return LS_SESSION_CHEM;
    return LS_SESSION;
  }
  function withSubject(href) {
    if (subject === 'math' || !href || href.indexOf('subject=') >= 0 || href.indexOf('http') === 0) return href;
    return href + (href.indexOf('?') >= 0 ? '&' : '?') + 'subject=' + subject;
  }
  function detectSubject() {
    const params = new URLSearchParams(location.search);
    const explicit = params.get('subject');
    if (explicit === 'english' || explicit === 'math' || explicit === 'physics' || explicit === 'chinese' || explicit === 'science' || explicit === 'morality' || explicit === 'history' || explicit === 'geography' || explicit === 'biology' || explicit === 'chemistry') return explicit;
    const target = params.get('target') || '';
    let hashId = (location.hash || '').replace(/^#/, '');
    try { hashId = decodeURIComponent(hashId); } catch (e) { /* 保持原样 */ }
    if (/(^|,)\s*cne_/.test(target) || /^cne_/.test(hashId)) {
      params.set('subject', 'english');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'english';
    }
    if (/(^|,)\s*cnp_/.test(target) || /^cnp_/.test(hashId)) {
      params.set('subject', 'physics');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'physics';
    }
    if (/(^|,)\s*cns_/.test(target) || /^cns_/.test(hashId)) {
      params.set('subject', 'science');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'science';
    }
    if (/(^|,)\s*cnd_/.test(target) || /^cnd_/.test(hashId)) {
      params.set('subject', 'morality');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'morality';
    }
    if (/(^|,)\s*cng_/.test(target) || /^cng_/.test(hashId)) {
      params.set('subject', 'geography');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'geography';
    }
    if (/(^|,)\s*cnb_/.test(target) || /^cnb_/.test(hashId)) {
      params.set('subject', 'biology');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'biology';
    }
    if (/(^|,)\s*cnk_/.test(target) || /^cnk_/.test(hashId)) {
      params.set('subject', 'chemistry');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'chemistry';
    }
    if (/(^|,)\s*cnh_/.test(target) || /^cnh_/.test(hashId)) {
      params.set('subject', 'history');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'history';
    }
    if (/(^|,)\s*cnc_/.test(target) || /^cnc_/.test(hashId)) {
      params.set('subject', 'chinese');
      history.replaceState(null, '', location.pathname + '?' + params.toString() + location.hash);
      return 'chinese';
    }
    return 'math';
  }
  function applySubjectChrome() {
    document.body.classList.toggle('subject-english', subject === 'english');
    document.body.classList.toggle('subject-physics', subject === 'physics');
    document.body.classList.toggle('subject-chinese', subject === 'chinese');
    document.body.classList.toggle('subject-science', subject === 'science');
    document.body.classList.toggle('subject-morality', subject === 'morality');
    document.body.classList.toggle('subject-history', subject === 'history');
    document.body.classList.toggle('subject-geography', subject === 'geography');
    document.body.classList.toggle('subject-biology', subject === 'biology');
    document.body.classList.toggle('subject-chemistry', subject === 'chemistry');
    document.querySelectorAll('.site-nav a:not(.subject-link), a.brand').forEach(function (link) {
      const href = link.getAttribute('href');
      const next = withSubject(href);
      if (next && next !== href) link.setAttribute('href', next);
    });
    document.querySelectorAll('.subject-link').forEach(function (link) {
      const on = link.getAttribute('data-subject') === subject;
      link.classList.toggle('on', on);
      if (on) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    if (subject === 'english') {
      document.title = '诊断 · 英语';
      var juniorOk = '三四五六七八九'.indexOf(gradeSel) >= 0;
      var seniorOk = gradeSel.indexOf('必修') === 0 || gradeSel.indexOf('选必') === 0;
      if (!juniorOk && !seniorOk) gradeSel = '四';
    }
    if (subject === 'physics') {
      document.title = '诊断 · 物理';
      if (gradeSel !== '八' && gradeSel !== '九' && !/^(必修[一二三]|选必[一二三])$/.test(gradeSel)) gradeSel = '八';
      if (gradeSel === '九') volSel = '全';
    }
    if (subject === 'science') {
      document.title = '诊断 · 小学科学';
      if ('一二三四五六'.indexOf(gradeSel) < 0) gradeSel = '一';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'morality') {
      document.title = '诊断 · 小学道德与法治';
      if ('一二三四五六'.indexOf(gradeSel) < 0) gradeSel = '一';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'history') {
      document.title = '诊断 · 初中历史';
      if ('七八九'.indexOf(gradeSel) < 0) gradeSel = '七';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'geography') {
      document.title = '诊断 · 初中地理';
      if ('七八'.indexOf(gradeSel) < 0) gradeSel = '七';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'biology') {
      document.title = '诊断 · 初中生物';
      if ('七八'.indexOf(gradeSel) < 0) gradeSel = '七';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'chemistry') {
      document.title = '诊断 · 初中化学';
      if (gradeSel !== '九') gradeSel = '九';
      if (volSel === '全') volSel = '';
    }
    if (subject === 'chinese') {
      document.title = '诊断 · 小学语文';
      if ('一二三四五六'.indexOf(gradeSel) < 0) gradeSel = '一';
      if (volSel === '全') volSel = '';
    }
  }
  function lsGet(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* 隐私模式等 */ } }
  function lsDel(k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } }
  function nameOf(id) { const t = D.graph.byId[id]; return t ? t.name : id; }
  function getSettings() {
    const st = lsGet(LS_SETTINGS) || {};
    let limit = parseInt(st.limit, 10);
    if (!(limit >= LIMIT_MIN && limit <= LIMIT_MAX)) limit = E.DEFAULT_LIMIT;
    let screenLimit = parseInt(st.screenLimit, 10);
    if (!(screenLimit >= SCREEN_MIN && screenLimit <= SCREEN_MAX)) screenLimit = E.SCREEN_LIMIT;
    const confirm = E.clampConfirm(st.confirm);
    return { limit: limit, screenLimit: screenLimit, confirm: confirm };
  }
  function setSetting(k, v) { const o = getSettings(); o[k] = v; lsSet(LS_SETTINGS, o); }
  function seenList() { const v = lsGet(LS_SEEN); return Array.isArray(v) ? v : []; }
  function markSeen(qid) {
    if (!qid || demo) return;
    const v = seenList();
    if (v.indexOf(qid) < 0) { v.push(qid); lsSet(LS_SEEN, v); }
  }
  function newSeed() { return seedParam != null ? seedParam : Math.random().toString(36).slice(2, 10); }
  function resetUi() { ui = { key: null, phase: 'ask', answer: '', verdict: null, picked: null }; }
  function clearRoot() { while (root.firstChild) root.removeChild(root.firstChild); }
  function teardownPath() {
    pathToken++;
    pathTipLock = false;
    if (pathCy) { pathCy.destroy(); pathCy = null; window.__pathCy = null; }
  }
  function show(node) { teardownPath(); closeShare(); clearRoot(); root.append(node); window.scrollTo(0, 0); }
  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function theme() {
    return {
      primary: cssVar('--node-primary'), primaryBg: cssVar('--node-primary-bg'),
      junior: cssVar('--node-junior'), juniorBg: cssVar('--node-junior-bg'),
      senior: cssVar('--node-senior'), seniorBg: cssVar('--node-senior-bg'),
      currentBg: cssVar('--node-current-bg'), currentBorder: cssVar('--node-current-border'),
      text: cssVar('--node-text'), edge: cssVar('--edge'), edgeSoft: cssVar('--edge-soft'),
      bad: cssVar('--diagram-bad'), badBg: cssVar('--diagram-bad-bg')
    };
  }
  function labelLimit() { return window.matchMedia('(max-width: 700px)').matches ? 8 : 10; }
  function clipLabel(name) {
    const chars = Array.from(name || '');
    const limit = labelLimit();
    if (chars.length <= limit) return name || '';
    return chars.slice(0, limit - 1).join('') + '…';
  }

  /* ------------------------------------------------------------ 数据 */
  async function loadData() {
    const urls = ['../data/topics.json', '../data/dependencies.json', '../data/cn-curriculum-standards.json', '../data/id-aliases.json'];
    const rs = await Promise.all(urls.map(function (u) { return fetch(u); }));
    rs.forEach(function (r, i) { if (!r.ok) throw new Error(urls[i] + ' → HTTP ' + r.status); });
    const js = await Promise.all(rs.map(function (r) { return r.json(); }));
    // 题库可选：缺失（404）或损坏时回退到 topics.json 的 diagnostic_question
    let questions = null;
    try {
      const qr = await fetch('../data/questions.json');
      if (qr.ok) questions = await qr.json();
    } catch (e) { questions = null; }
    const topics = js[0].filter(function (t) { return E.subjectOf(t) === subject; });
    const allow = {};
    topics.forEach(function (t) { allow[t.id] = true; });
    const deps = js[1].filter(function (d) { return allow[d.topicId] && allow[d.prerequisiteId]; });
    if (questions) questions = questions.filter(function (q) { return allow[q.topicId]; });
    const stdById = {};
    js[2].items.forEach(function (x) { stdById[x.id] = x; });
    const graph = E.buildGraph(topics, deps, questions);
    D = { topics: topics, deps: deps, stdById: stdById, graph: graph, tree: buildTree(topics), aliases: (js[3] && js[3].aliases) || {} };
  }

  function buildTree(topics) {
    const vols = {};
    topics.forEach(function (t) {
      if (t.external) return;
      const c = E.parseChapter(t.chapter);
      const v = vols[c.volume] || (vols[c.volume] = { chapters: [], byKey: {} });
      const key = c.chapterNo + ' ' + c.chapterName;
      let ch = v.byKey[key];
      if (!ch) {
        ch = v.byKey[key] = { volume: c.volume, key: c.volume + ' ' + c.chapterNo, label: c.chapterNo + ' ' + c.chapterName, topics: [] };
        v.chapters.push(ch);
      }
      ch.topics.push({ t: t, section: c.section });
    });
    return vols;
  }

  /* ------------------------------------------------------------ 孩子档案 */
  const CC = window.CnmChildren;
  function childLabel(c) { return c.name + (c.grade ? '（' + c.grade + '）' : ''); }
  function childrenHref(path) { return '../children/' + (path || ''); }
  function fromQuery() { return '?from=diagnose' + (subject !== 'math' ? '&subject=' + subject : ''); }
  function childSelect(onPick) {
    const cur = CC.current();
    const sel = h('select', { id: 'child-select', 'aria-label': '当前孩子' },
      h('option', { value: '' }, '不保存到档案'),
      CC.list().map(function (c) { return h('option', { value: c.id, selected: !!cur && cur.id === c.id }, childLabel(c)); }));
    sel.value = cur ? cur.id : '';
    sel.addEventListener('change', function () { onPick(sel.value || null); });
    return sel;
  }
  function childBar(mode) {
    if (demo) return null;
    const kids = CC.list();
    const cur = CC.current();
    if (!kids.length) {
      return h('div', { class: 'banner child-bar no-print', id: 'child-bar' },
        h('b', { text: '还没有孩子档案。' }),
        '添加后，诊断结果会按孩子保存，之后能回看每次的记录和薄弱知识点。', ' ',
        h('a', { class: 'btn btn-primary', href: childrenHref(fromQuery()), text: '添加孩子' }));
    }
    if (mode === 'question') {
      return h('div', { class: 'child-bar compact row no-print', id: 'child-bar' },
        h('span', { class: 'muted small' }, '当前孩子'),
        childSelect(function (id) { CC.setCurrent(id); }));
    }
    if (mode === 'result') {
      const key = recordKey();
      return h('div', { class: 'card child-bar no-print', id: 'child-bar' },
        h('p', { style: 'margin:0 0 8px' }, cur
          ? [h('b', { text: '已保存到「' + cur.name + '」的档案。' }), ' 换成别的孩子会把这条记录一起挪过去。']
          : [h('b', { text: '这次结果还没有存入档案。' }), ' 选一个孩子，就会保存。']),
        h('div', { class: 'row' },
          h('label', { for: 'child-select' }, '保存到'),
          childSelect(function (id) {
            if (cur && id !== cur.id) { if (id) CC.moveRecord(key, cur.id, id); else CC.removeRecord(cur.id, key); }
            CC.setCurrent(id);
            renderResult();
          }),
          cur ? h('a', { class: 'btn', href: childrenHref('history.html?child=' + encodeURIComponent(cur.id)), text: '盲区与历史' }) : null));
    }
    return h('div', { class: 'card child-bar no-print', id: 'child-bar' },
      h('div', { class: 'row' },
        h('label', { for: 'child-select' }, '当前孩子'),
        childSelect(function (id) { CC.setCurrent(id); renderStart(); }),
        h('span', { class: 'grow' }),
        cur ? h('a', { class: 'btn', href: childrenHref('history.html?child=' + encodeURIComponent(cur.id)), text: '盲区与历史' }) : null,
        h('a', { class: 'btn', href: childrenHref(fromQuery()), text: '孩子档案' })),
      h('p', { class: 'muted small', style: 'margin:8px 0 0' },
        cur ? '诊断做完，结果会保存到「' + cur.name + '」的档案里。' : '选了“不保存到档案”时，诊断结果不会存下来。'));
  }
  function recordKey() { return [subject, session.seed, session.targets.join(',')].join('|'); }
  function saveToChild(sum) {
    const cur = CC.current();
    if (demo || !cur || !sum.asked) return;
    CC.saveRecord(cur.id, {
      key: recordKey(), subject: subject, label: sessionMeta.label, mode: sum.mode, asked: sum.asked,
      targets: sum.mode === 'screen' || sum.targets.length > 6 ? null : sum.targets,
      counts: { weak: sum.weak.length, shaky: sum.shaky.length, mastered: sum.mastered.length, untested: sum.untested.length },
      weak: sum.weak, roots: sum.roots.map(function (r) { return r.id; }), shaky: sum.shaky, mastered: sum.mastered
    });
  }
  function noteBlind(sum) {
    if (demo || !sum || !sum.asked || !window.CnmBlind) return;
    window.CnmBlind.noteResult({
      subject: subject, key: recordKey(), label: sessionMeta.label, demo: demo,
      weak: sum.weak, shaky: sum.shaky, mastered: sum.mastered,
      roots: sum.roots.map(function (r) { return r.id; }),
      answers: session.answers
    });
  }
  function diagnoseHrefFor(ids) {
    if (window.CnmBlind) return window.CnmBlind.diagnoseHref(ids, subject, './');
    const list = (Array.isArray(ids) ? ids : [ids]).filter(Boolean);
    let q = 'target=' + list.map(encodeURIComponent).join(',');
    if (subject !== 'math') q = 'subject=' + subject + '&' + q;
    return './?' + q;
  }
  function blindStartCard() {
    if (!window.CnmBlind) return null;
    const rows = window.CnmBlind.list({ subject: subject, limit: 6 });
    if (!rows.length) return null;
    const cur = CC.current();
    const more = window.CnmBlind.historyHref(cur && cur.id, '../children/');
    return h('div', { class: 'card', id: 'blind-start' },
      h('h2', { text: '本机盲区（最近薄弱点）' }),
      h('p', { class: 'muted small' }, '根据本机诊断记录汇总，数据只留在这台浏览器。点「再测」会按该知识点重新诊断。'),
      h('ul', { class: 'blind-list' }, rows.map(function (row) {
        return h('li', { class: 'blind-item' },
          h('span', { class: 'blind-name', text: nameOf(row.id) }),
          ' ',
          h('span', { class: 'tag ' + (row.status === 'weak' ? 'weak' : 'shaky'), text: row.status === 'weak' ? (row.root ? '根因' : '薄弱') : '不稳' }),
          row.wrongs ? h('span', { class: 'muted small', text: ' · 答错 ' + row.wrongs + ' 次' }) : null,
          ' ',
          h('a', { class: 'blind-retest', href: diagnoseHrefFor([row.id]), text: '再测' }));
      })),
      h('p', { class: 'row' },
        h('a', { class: 'btn', href: more, text: '查看全部盲区' }),
        rows[0] ? h('a', { class: 'btn btn-primary', href: diagnoseHrefFor(rows.filter(function (r) { return r.status === 'weak'; }).slice(0, 5).map(function (r) { return r.id; })), text: '再测前几个薄弱点' }) : null));
  }
  function blindResultCard(sum) {
    const weakIds = (sum.weak || []).slice();
    const rootIds = (sum.roots || []).map(function (r) { return r.id; });
    const shakyIds = (sum.shaky || []).slice();
    if (!weakIds.length && !shakyIds.length) return null;
    const cur = CC.current();
    const hist = window.CnmBlind ? window.CnmBlind.historyHref(cur && cur.id, '../children/') : '../children/history.html';
    return h('div', { class: 'card no-print', id: 'blind-result' },
      h('h2', { text: '盲区再测' }),
      h('p', { class: 'muted small' }, '把本轮判为薄弱或不稳的知识点收进本机盲区汇总，可一键再测。不会上传答题内容。'),
      rootIds.length ? h('p', null,
        h('a', { class: 'btn btn-primary', href: diagnoseHrefFor(rootIds), text: '再测薄弱根因（' + rootIds.length + '）' })) : null,
      weakIds.length && weakIds.join(',') !== rootIds.join(',') ? h('p', null,
        h('a', { class: 'btn', href: diagnoseHrefFor(weakIds.slice(0, 8)), text: '再测薄弱知识点（' + Math.min(8, weakIds.length) + (weakIds.length > 8 ? '+' : '') + '）' })) : null,
      shakyIds.length ? h('p', null,
        h('a', { class: 'btn', href: diagnoseHrefFor(shakyIds.slice(0, 8)), text: '再测不稳知识点（' + Math.min(8, shakyIds.length) + (shakyIds.length > 8 ? '+' : '') + '）' })) : null,
      h('p', null, h('a', { href: hist, text: '打开本机盲区汇总' })));
  }

  /* ------------------------------------------------------------ 会话 */
  function save() {
    if (demo || !session) return;
    lsSet(sessionKey(), {
      v: 2, mode: session.mode, targets: session.targets, limit: session.limit, confirm: session.confirm,
      label: sessionMeta.label, answers: session.answers,
      seed: session.seed, avoid: session.avoid, savedAt: new Date().toISOString()
    });
  }

  function startSession(targets, label, limit, mode) {
    pathExpanded = false;
    const screen = mode === 'screen';
    const st = getSettings();
    session = E.createSession(D.graph, targets, {
      mode: mode, limit: limit || (screen ? st.screenLimit : st.limit), confirm: st.confirm, seed: newSeed(), avoid: seenList()
    });
    sessionMeta = { label: label };
    resetUi();
    save();
    render();
  }

  function restoreSession(saved) {
    try {
      session = E.replay(D.graph, saved.targets, saved.answers, {
        mode: saved.mode, limit: saved.limit, confirm: saved.confirm, seed: saved.seed, avoid: saved.avoid
      });
      sessionMeta = { label: saved.label || saved.targets.map(nameOf).join('、') };
      return true;
    } catch (e) { return false; }
  }

  function restart() {
    pathExpanded = false;
    session = null; demo = null;
    lsDel(sessionKey());
    history.replaceState(null, '', location.pathname + (subject !== 'math' ? '?subject=' + subject : ''));
    render();
  }

  function commit(result) {
    const item = E.nextItem(D.graph, session);
    session = E.applyAnswer(D.graph, session, item.topicId, result, { text: ui.answer });
    markSeen(item.question.id);
    resetUi();
    save();
    render();
  }

  function rebuild(answers, limit) {
    session = E.replay(D.graph, session.targets, answers, {
      mode: session.mode, limit: limit == null ? session.limit : limit, confirm: session.confirm,
      seed: session.seed, avoid: session.avoid
    });
    resetUi();
    save();
    render();
  }

  /* ------------------------------------------------------------ 演示模式 */
  // 演示用的“学生”：目标不会（错、错 -> 薄弱）；它的第一个可测先修也不会；再往前（或另一个先修）答错一次、第二题答对 -> 不稳；其余都会
  function makeOracle(targets, mode) {
    const G = D.graph;
    if (mode === 'screen') {
      // 整体筛查：按知识点序号，约 1/6 不会、1/6 不稳，其余都会（与 scripts/demo_grade.js 相同）
      return function (id, attempt) {
        const i = G.index[id];
        if (i % 6 === 0) return 'wrong';
        if (i % 6 === 3) return attempt === 1 ? 'wrong' : 'correct';
        return 'correct';
      };
    }
    const t0 = E.createSession(G, targets).stack[0];
    const testablePre = function (id) { return G.prereqs[id].filter(function (x) { return E.isTestable(G, x.id); }).map(function (x) { return x.id; }); };
    const weak = new Set([t0]);
    const shaky = new Set();
    const p = testablePre(t0);
    if (p.length) {
      const q = testablePre(p[0]);
      if (q.length) { weak.add(p[0]); shaky.add(q[0]); }
      else if (p.length > 1) { weak.add(p[0]); shaky.add(p[1]); }
      else shaky.add(p[0]);
    }
    return function (id, attempt) {
      if (weak.has(id)) return 'wrong';
      if (shaky.has(id)) return attempt === 1 ? 'wrong' : 'correct';
      return 'correct';
    };
  }

  function runDemo(steps) {
    let n = 0;
    while (n < steps) {
      const item = E.nextItem(D.graph, session);
      if (!item) break;
      session = E.applyAnswer(D.graph, session, item.topicId, demo.oracle(item.topicId, item.attempt));
      n++;
    }
  }

  /* ------------------------------------------------------------ 渲染入口 */
  function render() {
    if (!session) return renderStart();
    const item = E.nextItem(D.graph, session);
    if (item) renderQuestion(item); else renderResult();
  }

  /* ------------------------------------------------------------ 开始页 */
  function stageButton(value, label) {
    return h('button', {
      type: 'button',
      class: 'stage-tab' + (startStage === value ? ' on' : ''),
      role: 'tab',
      'aria-selected': startStage === value ? 'true' : 'false',
      onclick: function () { startStage = value; renderStart(); }
    }, label);
  }

  function renderStart(errMsg) {
    const page = h('div');
    const saved = lsGet(sessionKey());
    if (saved && saved.targets && D.graph.byId[saved.targets[0]]) {
      page.append(h('div', { class: 'banner' },
        h('b', { text: '有一份未清除的诊断：' }), saved.label || saved.targets.map(nameOf).join('、'),
        '（已答 ' + (saved.answers || []).length + ' 题）　',
        h('button', { class: 'primary', onclick: function () { if (restoreSession(saved)) render(); else { lsDel(sessionKey()); renderStart('存档无法恢复，已清除。'); } } }, '继续'),
        ' ', h('button', { onclick: function () { lsDel(sessionKey()); renderStart(); } }, '放弃存档')));
    }
    if (errMsg) page.append(h('p', { class: 'err', text: errMsg }));
    page.append(childBar('start'));
    const startBlind = blindStartCard();
    if (startBlind) page.append(startBlind);

    const st = getSettings();
    const limitInput = h('input', { type: 'number', min: LIMIT_MIN, max: LIMIT_MAX, step: 1, value: String(st.limit), id: 'limit-input', 'aria-label': '题量上限' });
    limitInput.addEventListener('change', function () {
      let v = parseInt(limitInput.value, 10);
      if (!(v >= LIMIT_MIN)) v = LIMIT_MIN;
      if (v > LIMIT_MAX) v = LIMIT_MAX;
      limitInput.value = String(v);
      setSetting('limit', v);
    });
    const confirmSelect = h('select', { id: 'confirm-select', 'aria-label': '每知识点确认题数' },
      E.CONFIRM_CHOICES.map(function (n) {
        return h('option', { value: String(n), selected: st.confirm === n }, String(n) + ' 题');
      }));
    confirmSelect.addEventListener('change', function () {
      const v = E.clampConfirm(confirmSelect.value);
      setSetting('confirm', v);
      renderStart();
    });
    const listBox = h('div', { id: 'target-list' });
    const browser = h('details', { class: 'chapter-browser', id: 'chapter-browser', open: chapterOpen || !!startQuery },
      h('summary', null, '按册、章浏览'),
      h('p', { class: 'muted small', text: '列表按年级、册、章折叠。想直接开始，用上面的搜索更快。' }),
      listBox);
    browser.addEventListener('toggle', function () { chapterOpen = browser.open; });
    const confirmHelp = '同一知识点连续答对 ' + st.confirm + ' 题（可在下方改成 2 / 3 / 5；题库更少时以题库为准）才算掌握；答错会再出一道同级或更容易的题——确认题也错才算薄弱并回溯先修，确认题答对则标为「不稳」。';
    page.append(h('div', { class: 'card' },
      h('h1', { text: '选择诊断目标' }),
      h('p', { class: 'muted' }, subject === 'physics'
        ? '选一个想学会或想检查的物理知识点。' + confirmHelp
        : subject === 'english'
        ? '选一个想学会或想检查的英语知识点。' + confirmHelp
        : subject === 'chinese'
        ? '选一个想学会或想检查的语文知识点。' + confirmHelp
        : subject === 'science'
        ? '选一个想学会或想检查的科学知识点。' + confirmHelp
        : subject === 'morality'
        ? '选一个想学会或想检查的道德与法治知识点。' + confirmHelp
        : subject === 'history'
        ? '选一个想学会或想检查的历史知识点。' + confirmHelp
        : subject === 'geography'
        ? '选一个想学会或想检查的地理知识点。' + confirmHelp
        : subject === 'biology'
        ? '选一个想学会或想检查的生物知识点。' + confirmHelp
        : subject === 'chemistry'
        ? '选一个想学会或想检查的化学知识点。' + confirmHelp
        : '选一个想学会或想检查的知识点。' + confirmHelp),
      h('div', { class: 'stage-tabs', role: 'tablist', 'aria-label': '学段' },
        subject === 'physics' ? [stageButton('', '全部'), stageButton('j', '初中'), stageButton('h', '高中')]
          : subject === 'history' || subject === 'geography' || subject === 'biology' || subject === 'chemistry' ? [stageButton('', '全部'), stageButton('j', '初中')]
          : subject === 'chinese' || subject === 'science' || subject === 'morality' ? [stageButton('', '全部'), stageButton('p', '小学')]
          : [stageButton('', '全部'), stageButton('p', '小学'), stageButton('j', '初中'), stageButton('h', '高中')]),
      h('input', {
        type: 'search', class: 'search-lg', id: 'search',
        placeholder: subject === 'physics' ? '搜索知识点，例如：欧姆定律、浮力、牛顿第二定律、楞次定律' : subject === 'english' ? '搜索知识点，例如：现在进行时、虚拟语气、there is' : subject === 'chinese' ? '搜索知识点，例如：声母、静夜思、的地得' : subject === 'science' ? '搜索知识点，例如：溶解、电路、昼夜交替' : subject === 'morality' ? '搜索知识点，例如：升国旗、排队、宪法、节约用水' : subject === 'history' ? '搜索知识点，例如：鸦片战争、丝绸之路、五四运动' : subject === 'geography' ? '搜索知识点，例如：经纬网、季风气候、长江' : subject === 'biology' ? '搜索知识点，例如：细胞、光合作用、基因' : subject === 'chemistry' ? '搜索知识点，例如：氧气、质量守恒定律、酸碱盐' : '搜索知识点，例如：配方法、20 以内加法、一次函数',
        value: startQuery, autocomplete: 'off', 'aria-label': '搜索知识点',
        oninput: function (e) {
          startQuery = e.target.value;
          fillList(listBox);
          if (startQuery.trim()) { browser.open = true; chapterOpen = true; }
        }
      }),
      h('p', { class: 'muted small', id: 'match-count' }),
      h('div', { class: 'row' },
        h('label', null, '单点 / 整章题量上限（' + LIMIT_MIN + '–' + LIMIT_MAX + '）', limitInput),
        h('label', null, '每知识点确认题数', confirmSelect),
        h('span', { class: 'muted small' }, '连续答对这么多题才判掌握；中途答错会再出一道确认题。到上限后，没测到的标为「未测」。'))));
    page.append(gradeCard());
    page.append(h('div', { class: 'card' }, browser));
    page.append(h('p', { class: 'muted small' },
      '可以诊断的知识点：' + D.topics.length + ' 个。进度和出过的题只保存在这台浏览器里。'));
    show(page);
    fillList(listBox);
    if (startQuery) { const el = document.getElementById('search'); if (el) el.focus(); }
  }

  function seniorGrade(sel) {
    return sel === '高一' || sel === '高二' || String(sel).indexOf('选必') === 0 || String(sel).indexOf('必修') === 0;
  }
  function seniorRangeLabel(sel) { return String(sel).indexOf('选必') === 0 ? '整册' : '必修整册'; }
  function gradeScope() {
    if (seniorGrade(gradeSel)) return gradeSel;
    if (subject === 'physics' && gradeSel === '九') return '九全';
    if (subject === 'english' && gradeSel === '九') return volSel === '上' ? '九上' : (volSel === '全' ? '九全' : '九年级');
    return gradeSel + (volSel ? volSel : '年级');
  }

  function gradeCard() {
    const box = h('div', { class: 'card', id: 'grade-card' });
    const fill = function () {
      while (box.firstChild) box.removeChild(box.firstChild);
      const g = E.gradeTargets(D.graph, gradeScope(), subject);
      const tabs = function (label, items, current, set) {
        return h('div', { class: 'stage-tabs', role: 'tablist', 'aria-label': label }, items.map(function (it) {
          return h('button', {
            type: 'button', class: 'stage-tab' + (current === it[0] ? ' on' : ''), role: 'tab',
            'aria-selected': current === it[0] ? 'true' : 'false', 'data-value': it[0],
            onclick: function () { set(it[0]); fill(); }
          }, it[1]);
        }));
      };
      const limitInput = h('input', {
        type: 'number', min: SCREEN_MIN, max: SCREEN_MAX, step: 1, value: String(getSettings().screenLimit), id: 'screen-limit-input', 'aria-label': '整体诊断题量上限'
      });
      limitInput.addEventListener('change', function () {
        let v = parseInt(limitInput.value, 10);
        if (!(v >= SCREEN_MIN)) v = SCREEN_MIN;
        if (v > SCREEN_MAX) v = SCREEN_MAX;
        limitInput.value = String(v);
        setSetting('screenLimit', v);
      });
      box.append(
        h('h2', { text: '按年级整体诊断' }),
        h('p', { class: 'muted' }, '本测评检查本年级知识点是否掌握，不是竞赛拔高。按「基础 / 提高 / 拓展」出题：先出提高题，答对再出拓展题确认掌握；答错会先补基础题，仍错会回到前面年级的相关知识点。每个知识点连续答对 ' + getSettings().confirm + ' 题才算掌握（可在上方改），最后按章汇总出哪几章薄弱。适合期初摸底、学期末复习。'),
        tabs('年级', subject === 'physics'
          ? [['八', '八年级'], ['九', '九年级'], ['必修一', '必修一'], ['必修二', '必修二'], ['必修三', '必修三'],
            ['选必一', '选必一'], ['选必二', '选必二'], ['选必三', '选必三']]
          : subject === 'english'
          ? '三四五六七八九'.split('').map(function (x) { return [x, x + '年级']; }).concat([
            ['必修一', '必修一'], ['必修二', '必修二'], ['必修三', '必修三'],
            ['选必一', '选必一'], ['选必二', '选必二'], ['选必三', '选必三'], ['选必四', '选必四']
          ])
          : subject === 'history'
          ? '七八九'.split('').map(function (x) { return [x, x + '年级']; })
          : subject === 'geography' || subject === 'biology'
          ? '七八'.split('').map(function (x) { return [x, x + '年级']; })
          : subject === 'chemistry'
          ? [['九', '九年级']]
          : subject === 'chinese' || subject === 'science' || subject === 'morality'
          ? '一二三四五六'.split('').map(function (x) { return [x, x + '年级']; })
          : GRADES.map(function (x) { return [x, x + '年级']; }).concat([
            ['高一', '高一'], ['高二', '高二'], ['选必一', '选必一'], ['选必二', '选必二'], ['选必三', '选必三']
          ]), gradeSel, function (v) {
          gradeSel = v;
          if (seniorGrade(v)) volSel = '';
          else if (subject === 'physics' && v === '九') volSel = '全';
          else if (subject === 'english' && v === '九') volSel = '';
          else if (volSel === '全') volSel = '';
        }),
        h('div', { style: 'margin-top:8px' }),
        seniorGrade(gradeSel)
          ? tabs('范围', [['', seniorRangeLabel(gradeSel)]], '', function () { volSel = ''; })
          : (subject === 'physics' && gradeSel === '九')
            ? tabs('范围', [['全', '全一册']], '全', function () { volSel = '全'; })
          : (subject === 'english' && gradeSel === '九')
            ? tabs('范围', [['', '整年级'], ['上', '上册（新版）'], ['全', '全一册（旧版，九下暂用）']], volSel, function (v) { volSel = v; })
            : tabs('范围', [['', '整年级'], ['上', '上册'], ['下', '下册']], volSel, function (v) { volSel = v; }),
        h('p', { class: 'muted', id: 'grade-info' }, g ? g.label + '：' + g.ids.length + ' 个知识点。' : '这个范围没有知识点。'),
        h('div', { class: 'row' },
          h('label', null, '题量上限（' + SCREEN_MIN + '–' + SCREEN_MAX + '）', limitInput),
          h('button', {
            class: 'primary', id: 'btn-grade-start', disabled: !g,
            onclick: function () { if (g) startSession(g.ids, g.label + '（整体筛查）', null, 'screen'); }
          }, '开始整体诊断')),
        h('p', { class: 'muted small' }, '知识点多、题量有限，到上限后没测到的标为「未测」；结果页可以再加题。默认 ' + E.SCREEN_LIMIT + ' 题。'));
    };
    fill();
    return box;
  }

  function fillList(box) {
    while (box.firstChild) box.removeChild(box.firstChild);
    const q = startQuery.trim().toLowerCase();
    let shown = 0;
    function volumeStage(key) {
      if (key === '高一' || key === '高二' || key.indexOf('选必') === 0 || key.indexOf('必修') === 0) return 'h';
      if ('一二三四五六'.indexOf(key.charAt(0)) >= 0) return 'p';
      return 'j';
    }
    VOLUMES.forEach(function (vv) {
      if (startStage && volumeStage(vv[0]) !== startStage) return;
      const v = D.tree[vv[0]];
      if (!v) return;
      const chapters = [];
      v.chapters.forEach(function (ch) {
        const chHit = q && ch.label.toLowerCase().indexOf(q) >= 0;
        const rows = ch.topics.filter(function (x) {
          if (!q || chHit) return true;
          return (x.t.name + ' ' + x.t.description + ' ' + x.t.chapter).toLowerCase().indexOf(q) >= 0;
        });
        if (rows.length) chapters.push({ ch: ch, rows: rows });
      });
      if (!chapters.length) return;
      const count = chapters.reduce(function (n, c) { return n + c.rows.length; }, 0);
      shown += count;
      const openVol = subject === 'physics' ? '八上' : subject === 'english' ? '三上' : subject === 'chemistry' ? '九上' : subject === 'history' || subject === 'geography' || subject === 'biology' ? '七上' : '一上';
      const juniorOpen = subject === 'chemistry' ? '九上' : '七上';
      const seniorOpen = subject === 'english' || subject === 'physics' ? '必修一' : '高一';
      const det = h('details', { class: 'vol', open: !!q || (startStage === 'j' ? vv[0] === juniorOpen : startStage === 'h' ? vv[0] === seniorOpen : vv[0] === openVol) },
        h('summary', null, vv[1] + '（' + count + ' 个知识点）'));
      chapters.forEach(function (c) {
        const ch = c.ch;
        det.append(h('div', { class: 'chap' },
          h('div', { class: 'chap-head' },
            h('span', { class: 't', text: ch.label }),
            h('button', {
              class: 'primary', title: '把本章全部 ' + ch.topics.length + ' 个知识点一起作为目标',
              onclick: function () { startSession(ch.topics.map(function (x) { return x.t.id; }), ch.volume + ' ' + ch.label + '（整章）'); }
            }, '以整章为目标')),
          c.rows.map(function (x) {
            return h('div', { class: 'topic-row', title: x.t.description },
              h('span', { class: 'nm', text: x.t.name }),
              h('span', { class: 'sec', text: x.section }),
              h('button', { onclick: function () { startSession([x.t.id], x.t.name); } }, '选为目标'));
          })));
      });
      box.append(det);
    });
    if (!shown) box.append(h('p', { class: 'muted', text: '没有匹配的知识点。' }));
    const mc = document.getElementById('match-count');
    if (mc) mc.textContent = (q ? '找到 ' : '册章列表里有 ') + shown + ' 个知识点';
    const browser = document.getElementById('chapter-browser');
    if (browser && q) browser.open = true;
  }

  /* ------------------------------------------------------------ 出题页 */
  function targetMinGrade() {
    let m = Infinity;
    (session.targets || []).forEach(function (tid) {
      const x = D.graph.byId[tid];
      if (x && typeof x.grade === 'number' && x.grade < m) m = x.grade;
    });
    return m;
  }
  function isPrereqKnowledge(id) {
    const t = D.graph.byId[id];
    if (!t || !session || (session.targets || []).indexOf(id) >= 0) return false;
    return typeof t.grade === 'number' && t.grade < targetMinGrade();
  }
  function reasonFor(item) {
    const id = item.topicId;
    const need = E.needConfirm(D.graph, session, id);
    const prev = session.attempts[id] || [];
    const hadFail = prev.some(function (a) { return a.result !== 'correct'; });
    const diff = item.question && item.question.difficulty;
    if (isPrereqKnowledge(id)) {
      return '这是前面年级的前置知识：因为本年级相关知识点还没过关，先回来检查它。';
    }
    if (hadFail) return '前面有题没答对，再出一道' + (diff === 'basic' ? '基础' : '同级或更容易') + '的题确认：这一题也错才算薄弱，答对则标为「不稳」。';
    if (item.attempt > 1) {
      if (diff === 'challenge' || diff === 'advanced') {
        return '上一题已答对，再出一道拓展题确认掌握（当前第 ' + item.attempt + ' 题，连续答对 ' + need + ' 题才算掌握）。';
      }
      return '同一知识点需连续答对 ' + need + ' 题才算掌握（当前第 ' + item.attempt + ' 题）。';
    }
    for (let i = session.answers.length - 1; i >= 0; i--) {
      const a = session.answers[i];
      if (a.result === 'correct') continue;
      const p = D.graph.prereqs[a.id].find(function (x) { return x.id === id; });
      if (p && E.statusOf(session, a.id) === 'weak') return '因为「' + nameOf(a.id) + '」确认后仍没通过，现在检查它的' + (p.strength === 'hard' ? '硬' : '软') + '先修知识点。';
    }
    if (session.mode === 'screen') return '整体诊断：先测本年级知识点（离章末近的先测）。先出提高题，答对再出拓展题确认；答错先补基础题。';
    if (session.targets.length > 1) return '这是所选章节的知识点（离章末最近的先测，连续答对会连带跳过它的先修）。';
    return session.targets.indexOf(id) >= 0 ? '这是你选择的目标知识点，先从它开始测（连续答对 ' + need + ' 题才算掌握）。' : '检查目标的先修知识点。';
  }

  function judgeAndGo(item) {
    const q = item.question;
    const val = ui.answer.trim();
    if (!val) { const el = document.getElementById('ans'); if (el) el.focus(); return; }
    const r = E.judgeQuestion(q, val);
    ui.verdict = r;
    ui.phase = r.verdict === 'manual' ? 'self' : 'auto';
    renderQuestion(item);
  }

  function answerText(q) {
    if (q.type === 'choice') {
      const c = (q.choices || []).find(function (x) { return x.key === q.answer; });
      return q.answer + (c ? '. ' + c.text : '');
    }
    return q.answer;
  }

  function feedbackBlock(q) {
    return h('div', { class: 'feedback' },
      h('div', { class: 'refans' }, h('b', null, '参考答案：'), answerText(q)),
      q.explanation ? h('div', { class: 'explain', id: 'explain' }, h('b', null, '解析：'), q.explanation) : null);
  }

  function renderQuestion(item) {
    const id = item.topicId;
    const q = item.question;
    const t = D.graph.byId[id];
    const key = id + '#' + item.attempt;
    if (ui.key !== key) ui = { key: key, phase: 'ask', answer: '', verdict: null, picked: null };
    const n = session.answers.length;
    const card = h('div', { class: 'card' });
    card.append(
      h('div', { class: 'row' },
        h('span', { class: 'muted' }, '目标：' + sessionMeta.label),
        h('span', { class: 'grow' }),
        h('span', { class: 'muted' }, '第 ' + (n + 1) + ' 题 / 上限 ' + session.limit)),
      h('div', { class: 'progress' }, h('i', { style: 'width:' + Math.round(n / session.limit * 100) + '%' })),
      h('h2', { class: 'q-title' }, t.name, ' ', h('span', { class: 'tag', text: t.chapter })),
      h('div', { class: 'row small', style: 'margin:2px 0' },
        isPrereqKnowledge(id) ? h('span', { class: 'tag ext', text: '前置知识' }) : null,
        h('span', { class: 'tag diff-' + q.difficulty, text: DIFF_LABEL[q.difficulty] || q.difficulty }),
        h('span', { class: 'tag', text: TYPE_LABEL[q.type] || q.type }),
        h('span', { class: 'tag', text: '本知识点第 ' + item.attempt + ' / ' + E.needConfirm(D.graph, session, id) + ' 题' })),
      h('div', { class: 'reason', text: reasonFor(item) }),
      h('div', { class: 'q-text', id: 'q-text', text: q.prompt }));
    const stemFig = figureEl(q.figure);
    if (stemFig) {
      const qt = card.querySelector('#q-text');
      if (qt) qt.insertAdjacentElement('afterend', stemFig);
    }

    if (ui.phase === 'ask') {
      if (q.type === 'choice') {
        card.append(h('div', { class: 'choices' + (q.hideChoiceText ? ' fig-icons' : ''), id: 'choices' }, (q.choices || []).map(function (c) {
          const hideName = !!(q.hideChoiceText && c.figure);
          const kids = [h('b', { class: 'choice-key', text: hideName ? c.key : (c.key + '.') })];
          if (!hideName) kids.push(document.createTextNode(' ' + c.text));
          const fig = c.figure ? figureEl(c.figure) : null;
          if (fig) kids.push(fig);
          return h('button', {
            class: 'choice' + (c.figure ? ' fig-choice' : '') + (ui.picked === c.key ? ' picked' : ''),
            id: 'choice-' + c.key, 'data-key': c.key,
            'aria-label': hideName ? ('选项 ' + c.key) : null,
            onclick: function () { ui.picked = c.key; ui.answer = c.key; renderQuestion(item); }
          }, kids);
        })));
      } else if (q.type === 'self') {
        card.append(h('textarea', {
          class: 'ans-input', id: 'ans', rows: 3, placeholder: '开放题：可以写下自己的思路（不会自动判分），再点「看参考答案并自评」', value: ui.answer,
          oninput: function (e) { ui.answer = e.target.value; }
        }));
      } else {
        card.append(h('input', {
          type: 'text', class: 'ans-input', id: 'ans', autocomplete: 'off', placeholder: '在这里输入答案（数字、分数、多个答案用逗号或“和”分开）', value: ui.answer,
          oninput: function (e) { ui.answer = e.target.value; },
          onkeydown: function (e) { if (e.key === 'Enter' && !e.isComposing) judgeAndGo(item); }
        }));
      }
      card.append(h('div', { class: 'row', style: 'margin-top:10px' },
        q.type === 'self' ? null : h('button', { class: 'primary', id: 'btn-submit', onclick: function () { judgeAndGo(item); } }, '提交答案'),
        q.type === 'choice' ? null : h('button', { id: 'btn-peek', onclick: function () { ui.phase = 'self'; ui.verdict = null; renderQuestion(item); } }, '看参考答案并自评'),
        h('button', { id: 'btn-skip', onclick: function () { ui.phase = 'skip'; renderQuestion(item); } }, '不会')));
    } else if (ui.phase === 'auto') {
      const ok = ui.verdict.verdict === 'correct';
      card.append(
        h('div', { class: 'muted' }, '你的答案：' + (q.type === 'choice' ? answerOfKey(q, ui.answer) : ui.answer)),
        h('div', { class: 'verdict ' + (ok ? 'ok' : 'no') }, ok ? '自动判定：正确' : '自动判定：不正确'),
        feedbackBlock(q),
        h('div', { class: 'row' },
          h('button', { class: 'primary', id: 'btn-next', onclick: function () { commit(ok ? 'correct' : 'wrong'); } }, '下一题'),
          h('button', { id: 'btn-flip', onclick: function () { commit(ok ? 'wrong' : 'correct'); } }, ok ? '判错了，我其实没做对' : '判错了，我其实做对了'),
          h('button', { onclick: function () { ui.phase = 'ask'; renderQuestion(item); } }, '重新作答')));
    } else if (ui.phase === 'skip') {
      card.append(
        h('div', { class: 'muted' }, '你选择了「不会」。看一下答案和解析再继续：'),
        feedbackBlock(q),
        h('div', { class: 'row' }, h('button', { class: 'primary', id: 'btn-next', onclick: function () { commit('skip'); } }, '下一题')));
    } else {
      card.append(
        ui.answer ? h('div', { class: 'muted' }, '你的答案：' + ui.answer) : null,
        q.type === 'self' ? h('div', { class: 'muted' }, '开放题：请对照参考答案自己判断。')
          : (ui.verdict ? h('div', { class: 'muted' }, '这道题的答案无法被自动可靠地判定，请对照参考答案自己判断。') : null),
        feedbackBlock(q),
        h('div', { class: 'row' },
          h('button', { class: 'good', id: 'btn-right', onclick: function () { commit('correct'); } }, '对（我做对了）'),
          h('button', { class: 'bad', id: 'btn-wrong', onclick: function () { commit('wrong'); } }, '不对'),
          h('button', { id: 'btn-skip2', onclick: function () { commit('skip'); } }, '不会')));
    }

    card.append(h('div', { class: 'notice' }, '提示：自动判题只是近似的（数字、分数、多个答案会做规范化后比较），一切以参考答案为准；判错了可以手动更正。'));
    card.append(h('div', { class: 'row no-print', style: 'margin-top:12px' },
      n > 0 ? h('button', { class: 'small', onclick: function () { rebuild(session.answers.slice(0, -1)); } }, '撤销上一题') : null,
      h('button', { class: 'small', onclick: function () { if (confirm('确定放弃当前诊断并回到开始页吗？')) restart(); } }, '重新开始')));
    const page = h('div');
    if (demo) page.append(demoBanner());
    page.append(childBar('question'));
    page.append(card);
    show(page);
    const inp = document.getElementById('ans');
    if (inp && inp.setSelectionRange && inp.tagName === 'INPUT') { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); }
    else if (inp) inp.focus();
  }

  function answerOfKey(q, key) {
    const c = (q.choices || []).find(function (x) { return x.key === key; });
    return c ? c.key + '. ' + c.text : key;
  }

  function demoBanner() {
    return h('div', { class: 'banner demo no-print' }, '演示模式：由程序模拟一位学生作答（不会保存进度）。',
      h('a', { href: location.pathname }, '退出演示'));
  }

  /* ------------------------------------------------------------ 分享图 */
  function onShareKey(e) { if (e.key === 'Escape') closeShare(); }
  function closeShare() {
    shareToken++;
    document.removeEventListener('keydown', onShareKey);
    var modal = document.getElementById('share-modal');
    if (modal) modal.remove();
    document.body.classList.remove('share-open');
    if (shareBlobUrl) { URL.revokeObjectURL(shareBlobUrl); shareBlobUrl = null; }
  }
  function shareScopeText() {
    var raw = sessionMeta && sessionMeta.label ? String(sessionMeta.label) : '本次诊断';
    raw = raw.replace(/（整体筛查）/g, '').replace(/（整章）/g, '').replace(/（旧编号已对应到小学知识点）/g, '');
    raw = raw.replace(/\s+/g, ' ').trim();
    return raw || '本次诊断';
  }
  function buildShareModel(sum, chapters) {
    var subjectName = subject === 'english' ? '英语' : subject === 'physics' ? '物理' : subject === 'chinese' ? '语文' : subject === 'science' ? '科学' : subject === 'morality' ? '道德与法治' : subject === 'history' ? '历史' : subject === 'geography' ? '地理' : subject === 'biology' ? '生物' : subject === 'chemistry' ? '化学' : '数学';
    var spots = [];
    var spotKind = 'topic';
    if (chapters && chapters.length) {
      spotKind = 'chapter';
      var hot = chapters.filter(function (c) { return c.weak > 0 || c.shaky > 0; });
      if (!hot.length) hot = chapters.slice(0, 3);
      spots = hot.slice(0, 3).map(function (c) {
        return { title: c.label, detail: '薄弱 ' + c.weak + ' · 不稳 ' + c.shaky + ' · 未测 ' + c.untested };
      });
    } else {
      var seen = Object.create(null);
      var ids = [];
      var pushId = function (id) {
        if (!id || seen[id] || ids.length >= 3) return;
        seen[id] = true;
        ids.push(id);
      };
      sum.roots.forEach(function (r) { pushId(r.id); });
      sum.weak.forEach(pushId);
      sum.shaky.forEach(pushId);
      spots = ids.map(function (id) {
        return { title: nameOf(id), detail: STATUS_LABEL[E.statusOf(session, id)] || '' };
      });
    }
    var now = new Date();
    return {
      siteName: '中小学·高中知识图谱',
      subject: subjectName,
      scope: shareScopeText(),
      mastered: sum.mastered.length,
      shaky: sum.shaky.length,
      weak: sum.weak.length,
      untested: sum.untested.length,
      spotKind: spotKind,
      spots: spots,
      roots: sum.roots.slice(0, 2).map(function (r) { return nameOf(r.id); }),
      date: now.getFullYear() + '年' + (now.getMonth() + 1) + '月' + now.getDate() + '日'
    };
  }
  function mountShareModal(url) {
    var old = document.getElementById('share-modal');
    if (old) old.remove();
    var img = h('img', { id: 'share-preview', alt: '诊断分享图', src: url });
    var modal = h('div', {
      id: 'share-modal', class: 'share-modal no-print', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'share-title',
      onclick: function (e) { if (e.target === modal) closeShare(); }
    }, h('div', { class: 'share-panel', onclick: function (e) { e.stopPropagation(); } },
      h('div', { class: 'share-bar' },
        h('h2', { id: 'share-title', text: '分享图' }),
        h('button', { type: 'button', id: 'share-close', onclick: closeShare }, '关闭')),
      h('p', { id: 'share-hint', class: 'share-hint', text: '长按图片保存' }),
      h('div', { class: 'share-scroll' }, img),
      h('div', { class: 'share-actions' },
        h('a', { id: 'share-download', class: 'btn btn-primary', href: url, download: '知识图谱诊断分享.png' }, '下载图片'))));
    document.body.classList.add('share-open');
    document.body.append(modal);
    document.addEventListener('keydown', onShareKey);
  }
  function openShare() {
    if (!window.ShareCard) {
      var host0 = document.getElementById('summary');
      if (host0) host0.append(h('p', { id: 'share-error', class: 'err', text: '分享图没有生成：组件没有加载' }));
      return;
    }
    var token = ++shareToken;
    var sum = E.summarize(D.graph, session);
    var chapters = session.mode === 'screen' ? E.chapterSummary(D.graph, session) : null;
    var model = buildShareModel(sum, chapters);
    window.__shareModel = model;
    var canvas = document.createElement('canvas');
    try { window.ShareCard.draw(canvas, model); }
    catch (err) {
      var host = document.getElementById('summary');
      if (host) host.append(h('p', { id: 'share-error', class: 'err', text: '分享图没有生成：' + (err && err.message ? err.message : err) }));
      return;
    }
    var finish = function (url) {
      if (token !== shareToken) {
        if (String(url).indexOf('blob:') === 0) URL.revokeObjectURL(url);
        return;
      }
      if (shareBlobUrl && shareBlobUrl !== url) URL.revokeObjectURL(shareBlobUrl);
      shareBlobUrl = String(url).indexOf('blob:') === 0 ? url : null;
      mountShareModal(url);
    };
    if (canvas.toBlob) {
      canvas.toBlob(function (blob) {
        if (token !== shareToken) return;
        if (!blob) { finish(canvas.toDataURL('image/png')); return; }
        finish(URL.createObjectURL(blob));
      }, 'image/png');
    } else finish(canvas.toDataURL('image/png'));
  }

  /* ------------------------------------------------------------ 结果页 */
  function standardsBlock(id) {
    const t = D.graph.byId[id];
    const list = t.standards || [];
    if (!list.length) return h('div', { class: 'muted small', text: t.external ? '小学阶段知识点，未对应第四学段课标条目。' : '没有对应的课标条目。' });
    return h('div', null, h('b', null, '课标条目：'), list.map(function (sd) {
      const item = D.stdById[sd.id];
      return h('div', { class: 'std' },
        h('code', { text: sd.id }), h('span', { class: 'conf', text: sd.confidence === 'exact' ? '直接对应' : '推断对应' }),
        h('div', { text: item ? item.text : '（课标文件中找不到该条目）' }),
        sd.note ? h('div', { class: 'muted small', text: '说明：' + sd.note }) : null);
    }));
  }

  function topicBody(id, extra) {
    const t = D.graph.byId[id];
    const body = h('div', { class: 'body' });
    body.append(h('div', { class: 'muted' }, (t.external ? '小学先修知识点（无诊断题）' : t.chapter) + (t.domain ? ' · ' + t.domain : '')));
    body.append(h('div', { text: t.description }));
    if (t.mastery_criteria && t.mastery_criteria.length) {
      body.append(h('div', null, h('b', null, '掌握标准：'), h('ul', null, t.mastery_criteria.map(function (m) { return h('li', { text: m }); }))));
    }
    if (extra) body.append(extra);
    body.append(standardsBlock(id));
    return body;
  }

  function topicItem(id, tags, extra) {
    const t = D.graph.byId[id];
    return h('details', { class: 'topic' },
      h('summary', null, tags, h('span', { text: t.name }), ' ', h('span', { class: 'muted small', text: t.external ? '小学' : t.chapter })),
      topicBody(id, extra));
  }

  function tag(cls, text) { return h('span', { class: 'tag ' + cls, text: text }); }
  function statusTags(id, rootSet, targetSet) {
    const st = E.statusOf(session, id);
    const out = [];
    if (targetSet.has(id)) out.push(tag('target', '目标'));
    if (rootSet.has(id)) out.push(tag('root', '根因'));
    if (isPrereqKnowledge(id)) out.push(tag('ext', '前置知识'));
    out.push(tag(st, STATUS_LABEL[st]));
    if (D.graph.byId[id].external) out.push(tag('ext', '小学'));
    return out;
  }

  function renderResult() {
    const sum = E.summarize(D.graph, session);
    const rootSet = new Set(sum.roots.map(function (r) { return r.id; }));
    const screen = session.mode === 'screen';
    const targetSet = new Set(screen ? [] : session.targets);
    const page = h('div');
    if (demo) page.append(demoBanner());
    saveToChild(sum);
    noteBlind(sum);
    page.append(childBar('result'));

    const targetsMastered = session.targets.every(function (id) { return E.statusOf(session, id) === 'mastered'; });
    const chapters = screen ? E.chapterSummary(D.graph, session) : null;
    const outOfScope = screen ? sum.roots.filter(function (r) { return r.outOfScopePrereqs.length; }) : [];
    let headline;
    if (screen) {
      if (!sum.weak.length && !sum.shaky.length) headline = sum.untested.length
        ? '已测到的知识点没有发现薄弱点，另有 ' + sum.untested.length + ' 个没测到。'
        : '范围内的知识点都已掌握，没有发现薄弱点。';
      else headline = '范围内共 ' + session.targets.length + ' 个知识点：薄弱 ' + sum.weak.length + '、不稳 ' + sum.shaky.length + '、未测 ' + sum.untested.length +
        '。先看下面的「按章汇总」，薄弱的章排在前面。';
    }
    else if (!sum.roots.length && !sum.shaky.length && targetsMastered) headline = '目标知识点已掌握，没有发现需要补的先修。';
    else if (!sum.roots.length && !sum.shaky.length) headline = '没有判出薄弱点，但目标尚未全部测到。';
    else if (!sum.roots.length) headline = '没有判出薄弱点，但有 ' + sum.shaky.length + ' 个知识点「不稳」（中途答错过、确认题答对），建议巩固。';
    else headline = '共发现 ' + sum.roots.length + ' 个薄弱根因' + (sum.shaky.length ? '、' + sum.shaky.length + ' 个不稳的知识点' : '') + '，按下面的学习路径从前往后补。';

    const more = screen ? 10 : 4;
    const summaryCard = h('div', { class: 'card', id: 'summary' },
      h('h2', { text: '诊断结果：' + sessionMeta.label }),
      h('p', null, headline),
      h('div', { class: 'stats' },
        stat('ask', sum.asked, '已答题数'),
        stat('bad', sum.weak.length, '薄弱'),
        stat('shaky', sum.shaky.length, '不稳'),
        stat('ok', sum.mastered.length, '已掌握'),
        stat('unk', sum.untested.length, '未测')),
      sum.unconfirmed.length ? h('p', { class: 'notice' }, '「' + sum.unconfirmed.map(nameOf).join('」「') + '」答错过但还没完成确认就到了题量上限，没来得及复测，暂按薄弱处理。') : null,
      sum.limitReached ? h('p', { class: 'notice' }, '已达到题量上限（' + sum.limit + '），剩余没测到的知识点标为「未测」。薄弱根因的先修里若有未测点，真正的根因可能更靠前。',
        session.limit >= 60 ? null : h('button', { class: 'no-print', style: 'margin-left:8px', onclick: function () { rebuild(session.answers, Math.min(session.limit + more, 60)); } }, '再多答 ' + Math.min(more, 60 - session.limit) + ' 题')) : null,
      h('p', { class: 'muted small' }, '自动判题只是近似的，答题记录里可以更正任何一题。生成时间：' + new Date().toLocaleString('zh-CN')),
      h('div', { class: 'row no-print' },
        h('button', { class: 'primary', id: 'btn-share', onclick: openShare }, '生成分享图'),
        h('button', { id: 'btn-export', onclick: exportJson }, '导出 JSON'),
        h('button', { id: 'btn-print', onclick: printPage }, '打印 / 另存为 PDF'),
        h('button', { onclick: function () { if (confirm('重新开始会清除当前进度，确定吗？')) restart(); } }, '重新开始'),
        session.answers.length ? h('button', { onclick: function () { rebuild(session.answers.slice(0, -1)); } }, '撤销上一题') : null));
    page.append(summaryCard);
    const blindCard = blindResultCard(sum);
    if (blindCard) page.append(blindCard);
    if (screen) page.append(chaptersCard(chapters, outOfScope));

    page.append(h('div', { class: 'card', id: 'roots' },
      h('h2', { text: '薄弱的先修知识点（根因）' }),
      h('p', { class: 'muted small' }, '根因 = 被判为薄弱、且它的直接先修里没有薄弱点的知识点。点击展开看描述、掌握标准和课标条目。'),
      sum.roots.length ? sum.roots.map(function (r) {
        const notes = h('div');
        if (r.pendingPrereqs.length) notes.append(h('div', { class: 'notice', text: '它的先修「' + r.pendingPrereqs.map(nameOf).join('」「') + '」没来得及测（题量用完），真正的根因可能更靠前。' }));
        if (r.outOfScopePrereqs.length) notes.append(h('div', { class: 'notice', text: '它的前置知识「' + r.outOfScopePrereqs.map(nameOf).join('」「') + '」不在所选范围内，没有检查。' }));
        if (r.externalPrereqs.length) notes.append(h('div', { class: 'muted small', text: '小学先修（无诊断题，未测）：' + r.externalPrereqs.map(nameOf).join('、') }));
        return topicItem(r.id, statusTags(r.id, rootSet, targetSet), notes);
      }) : h('p', { text: targetsMastered ? '没有。' : '暂未发现。' })));

    page.append(h('div', { class: 'card', id: 'shaky' },
      h('h2', { text: '不稳的知识点（' + sum.shaky.length + '）' }),
      h('p', { class: 'muted small' }, '中途答错过，但确认题（同级或更容易）答对了：可能是粗心，也可能掌握得不牢。它们会出现在学习路径里需要巩固，但工具没有继续向它们的先修回溯（只有确认后仍错才回溯）。'),
      sum.shaky.length ? sum.shaky.map(function (id) { return topicItem(id, statusTags(id, rootSet, targetSet)); }) : h('p', { text: '没有。' })));

    page.append(h('div', { class: 'card', id: 'path' },
      h('h2', { text: '推荐学习路径' }),
      h('p', { class: 'muted small' }, '从根因（和「不稳」的点）出发到目标之间、尚未判定为掌握的知识点，按年级从低到高排列（同一年级里先修在前），从上往下学。「不稳」「未测」的点也在路径上，建议先巩固 / 自查。'),
      sum.path.length ? h('ol', { class: 'path' }, sum.path.map(function (p) {
        return h('li', null, topicItem(p.id, statusTags(p.id, rootSet, targetSet)));
      })) : h('p', { text: '不需要补课。' })));

    page.append(h('div', { class: 'card', id: 'graph' },
      h('h2', { text: '路径图' }),
      h('p', { class: 'muted small' }, '小学、初中和高中用不同颜色。硬先修是实线，软先修是虚线，点线表示中间省略了没画出来的知识点。红框是薄弱根因，橙框是目标。节点较多时先按年级收起中间点，可再展开。名称太长会省略，悬停或点按可看全名。滚轮缩放，拖动平移。上面的列表是完整学习顺序。'),
      h('div', { class: 'path-tools no-print' },
        h('button', { type: 'button', id: 'path-zoom-out', onclick: function () { pathZoom(0.8); } }, '缩小'),
        h('button', { type: 'button', id: 'path-zoom-in', onclick: function () { pathZoom(1.25); } }, '放大'),
        h('button', { type: 'button', id: 'path-fit', onclick: pathFit }, '适配画面')),
      h('p', { id: 'path-fold', class: 'graph-fold no-print', hidden: true }),
      h('ul', { class: 'legend' },
        h('li', null, h('i', { class: 'swatch sw-p' }), '小学'),
        h('li', null, h('i', { class: 'swatch sw-j' }), '初中'),
        h('li', null, h('i', { class: 'swatch sw-h' }), '高中'),
        h('li', null, h('i', { class: 'swatch sw-root' }), '薄弱根因'),
        h('li', null, h('i', { class: 'swatch sw-target' }), '目标'),
        h('li', null, h('i', { class: 'swatch line-hard' }), '硬先修（实线）'),
        h('li', null, h('i', { class: 'swatch line-soft' }), '软先修（虚线）'),
        h('li', null, h('i', { class: 'swatch line-skip' }), '中间省略（点线）')),
      h('div', { class: 'path-graph' },
        h('div', { id: 'path-cy', role: 'img', 'aria-label': '先修路径图' }),
        h('div', { id: 'node-tip', class: 'node-tip', role: 'tooltip', hidden: true }))));

    page.append(h('details', { class: 'card', id: 'mastered' },
      h('summary', null, h('b', null, '已掌握的知识点（' + sum.mastered.length + '）')),
      sum.mastered.map(function (id) {
        const src = session.status[id].src === 'direct' ? '答对' : '由后续知识点答对推断';
        return topicItem(id, [tag('mastered', src)].concat(D.graph.byId[id].external ? [tag('ext', '小学')] : []));
      })));

    page.append(h('details', { class: 'card', id: 'untested' },
      h('summary', null, h('b', null, '未测的知识点（' + sum.untested.length + '）')),
      h('p', { class: 'muted small' }, '题量用完，或不必再测，所以没问到的知识点。小学知识点同样会出题。'),
      sum.untested.map(function (id) { return topicItem(id, statusTags(id, rootSet, targetSet)); })));

    page.append(standardsCard(sum));
    page.append(logCard());
    page.append(h('p', { class: 'iq-line', id: 'iq-line' },
      '做完数学诊断，再测测思维能力？→ ',
      h('a', {
        href: 'https://test.pansgo.com/?from=math-result',
        target: '_blank',
        rel: 'noopener',
        text: '儿童智商测试'
      })));
    show(page);
    mountPathGraph(sum);
  }

  function nameList(ids) { return ids.map(nameOf).join('、'); }

  function chaptersCard(chapters, outOfScope) {
    const seg = function (cls, n, total) { return n ? h('i', { class: cls, style: 'width:' + (n / total * 100) + '%' }) : null; };
    return h('div', { class: 'card', id: 'chapters' },
      h('h2', { text: '按章汇总' }),
      h('p', { class: 'muted small' }, '每章的知识点掌握情况，薄弱多的章排在前面；点开看具体是哪几个知识点。色条从左到右：掌握、不稳、薄弱、未测。'),
      outOfScope.length ? h('p', { class: 'notice', id: 'out-of-scope' }, '部分薄弱点的前置知识在所选年级之外，未检查（涉及 ' + outOfScope.length + ' 个薄弱点，如「' +
        outOfScope.slice(0, 3).map(function (r) { return nameOf(r.id); }).join('」「') + '」）。可对这些知识点单独做诊断，沿先修继续往前查。') : null,
      chapters.map(function (c) {
        return h('details', { class: 'topic chap-sum', open: c.weak > 0 || c.shaky > 0 },
          h('summary', null,
            h('span', { class: 'chap-name', text: c.label }),
            h('span', { class: 'chap-counts' },
              tag('mastered', '掌握 ' + c.mastered), tag('shaky', '不稳 ' + c.shaky), tag('weak', '薄弱 ' + c.weak), tag('unknown', '未测 ' + c.untested)),
            h('span', { class: 'chap-bar', 'aria-hidden': 'true' },
              seg('m', c.mastered, c.total), seg('s', c.shaky, c.total), seg('w', c.weak, c.total), seg('u', c.untested, c.total))),
          h('div', { class: 'body' },
            h('div', { class: 'muted small', text: '共 ' + c.total + ' 个知识点' }),
            c.weakIds.length ? h('div', { class: 'chap-names' }, tag('weak', '薄弱'), nameList(c.weakIds),
              ' ', h('a', { class: 'blind-retest no-print', href: diagnoseHrefFor(c.weakIds), text: '再测本章薄弱' })) : null,
            c.shakyIds.length ? h('div', { class: 'chap-names' }, tag('shaky', '不稳'), nameList(c.shakyIds),
              ' ', h('a', { class: 'blind-retest no-print', href: diagnoseHrefFor(c.shakyIds), text: '再测本章不稳' })) : null,
            !c.weakIds.length && !c.shakyIds.length ? h('div', { class: 'muted small', text: c.untested ? '没有发现薄弱或不稳的点，另有 ' + c.untested + ' 个没测到。' : '没有发现薄弱或不稳的点。' }) : null));
      }));
  }

  function stat(cls, n, label) { return h('div', { class: 'stat ' + cls }, h('b', { text: String(n) }), label); }

  function standardsCard(sum) {
    const ids = new Set(session.mode === 'screen' ? [] : session.targets);
    sum.path.forEach(function (p) { ids.add(p.id); });
    const by = {};
    ids.forEach(function (id) {
      (D.graph.byId[id].standards || []).forEach(function (sd) { (by[sd.id] || (by[sd.id] = [])).push(id); });
    });
    const keys = Object.keys(by).sort();
    return h('div', { class: 'card', id: 'standards' },
      h('h2', { text: '相关课标条目' }),
      h('p', { class: 'muted small' }, subject === 'physics'
        ? '目标与学习路径上的知识点对应的《义务教育物理课程标准（2022年版2025年修订）》和《普通高中物理课程标准（2017年版2020年修订）》内容要求（编号与课标条款一致）。'
        : subject === 'english'
        ? '目标与学习路径上的知识点对应的《义务教育英语课程标准（2022年版）》和《普通高中英语课程标准（2017年版2025年修订）》公开转述（一级、二级、三级，以及高中必修、选择性必修）。'
        : subject === 'chinese'
        ? '目标与学习路径上的知识点对应的《义务教育语文课程标准（2022年版）》第一至第三学段的公开转述。'
        : subject === 'science'
        ? '目标与学习路径上的知识点对应的《义务教育科学课程标准（2022年版）》第一至第三学段学习内容的公开转述。'
        : subject === 'morality'
        ? '目标与学习路径上的知识点对应的《义务教育道德与法治课程标准（2022年版）》第一至第三学段内容要求的公开转述。'
        : subject === 'history'
        ? '目标与学习路径上的知识点对应的《义务教育历史课程标准（2022年版）》第四学段内容要求的公开转述。'
        : subject === 'geography'
        ? '目标与学习路径上的知识点对应的《义务教育地理课程标准（2022年版）》第四学段内容要求的公开转述。'
        : subject === 'biology'
        ? '目标与学习路径上的知识点对应的《义务教育生物学课程标准（2022年版）》第四学段内容要求的公开转述。'
        : subject === 'chemistry'
        ? '目标与学习路径上的知识点对应的《义务教育化学课程标准（2022年版）》五个学习主题内容要求的公开转述。'
        : '目标与学习路径上的知识点对应的《义务教育数学课程标准（2022年版）》内容要求（第一至第四学段）。'),
      keys.length ? keys.map(function (k) {
        const item = D.stdById[k];
        return h('div', { class: 'std' }, h('code', { text: k }),
          h('div', { text: item ? item.text : '' }),
          h('div', { class: 'muted small', text: '对应知识点：' + by[k].map(nameOf).join('、') }));
      }) : h('p', { class: 'muted', text: '无。' }));
  }

  function logCard() {
    const rows = session.answers.map(function (a, i) {
      const q = E.questionById(D.graph, a.qid) || { prompt: '', answer: '' };
      const sel = h('select', {
        onchange: function (e) {
          const next = session.answers.map(function (x, j) { return j === i ? Object.assign({}, x, { result: e.target.value }) : x; });
          rebuild(next);
        }
      }, ['correct', 'wrong', 'skip'].map(function (r) { return h('option', { value: r, selected: r === a.result }, RESULT_LABEL[r]); }));
      return h('tr', null, h('td', { text: String(i + 1) }),
        h('td', null, nameOf(a.id), h('div', { class: 'muted small', text: q.prompt.length > 60 ? q.prompt.slice(0, 59) + '…' : q.prompt })),
        h('td', { class: 'muted', text: a.text || '' }),
        h('td', null, sel), h('td', { class: 'muted', text: q.answer }));
    });
    return h('div', { class: 'card', id: 'log' },
      h('h2', { text: '答题记录（可更正）' }),
      h('p', { class: 'muted small' }, '自动判题可能判错。在这里改某一题的结果会重新计算整份诊断（后续是否还需要追问也会随之变化）。'),
      session.answers.length ? h('table', { class: 'log' },
        h('thead', null, h('tr', null, h('th', { text: '#' }), h('th', { text: '知识点 / 题目' }), h('th', { text: '你的答案' }), h('th', { text: '结果' }), h('th', { text: '参考答案' }))),
        h('tbody', null, rows)) : h('p', { class: 'muted', text: '还没有答题。' }));
  }

  /* ------------------------------------------------------------ 路径图（Cytoscape + dagre） */
  function stageKind(grade) { return grade <= 6 ? 'primary' : grade <= 9 ? 'junior' : 'senior'; }
  function gradeWord(grade) {
    const cn = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
    if (subject === 'english') {
      if (grade >= 1 && grade <= 9) return cn[grade] + '年级';
      const en = { 10: '必修一', 11: '必修二', 12: '必修三', 13: '选必一', 14: '选必二', 15: '选必三', 16: '选必四' };
      return en[grade] || ('册' + grade);
    }
    if (grade >= 1 && grade <= 9) return cn[grade] + '年级';
    if (subject === 'physics') return { 10: '必修一', 11: '必修二', 12: '必修三', 13: '选必一', 14: '选必二', 15: '选必三' }[grade] || ('册' + grade);
    const math = { 10: '高一', 11: '高二', 12: '选必一', 13: '选必二', 14: '选必三' };
    return math[grade] || ('年级' + grade);
  }
  function toneOf(kind, colors) {
    if (kind === 'primary') return [colors.primaryBg, colors.primary];
    if (kind === 'junior') return [colors.juniorBg, colors.junior];
    return [colors.seniorBg, colors.senior];
  }
  function pathNodeElement(n, colors) {
    const topic = D.graph.byId[n.id];
    const grade = topic && typeof topic.grade === 'number' ? topic.grade : 7;
    const kind = stageKind(grade);
    const name = nameOf(n.id);
    const bits = [name];
    if (n.isRoot) bits.push('薄弱根因');
    if (n.isTarget) bits.push('目标');
    bits.push(STATUS_LABEL[n.status] || n.status);
    const tone = toneOf(kind, colors);
    let bg = tone[0];
    let border = tone[1];
    if (n.isTarget) { bg = colors.currentBg; border = colors.currentBorder; }
    if (n.isRoot) { bg = colors.badBg; border = colors.bad; }
    const classes = [kind];
    if (n.isRoot) classes.push('root');
    if (n.isTarget) classes.push('target', 'current');
    return {
      data: { id: n.id, name: name, full: bits.join(' · '), label: clipLabel(name), bg: bg, border: border, color: colors.text },
      classes: classes.join(' ')
    };
  }
  function buildPathElements(lay, colors, folded) {
    const elements = [];
    const bucket = new Map();
    const gradeMembers = new Map();
    lay.nodes.forEach(function (n) {
      if (!folded || n.isRoot || n.isTarget) {
        bucket.set(n.id, n.id);
        elements.push(pathNodeElement(n, colors));
        return;
      }
      const topic = D.graph.byId[n.id];
      const grade = topic && typeof topic.grade === 'number' ? topic.grade : 0;
      if (!gradeMembers.has(grade)) gradeMembers.set(grade, []);
      gradeMembers.get(grade).push(n.id);
    });
    gradeMembers.forEach(function (ids, grade) {
      const id = 'grade-' + grade;
      const kind = stageKind(grade);
      const tone = toneOf(kind, colors);
      const name = gradeWord(grade) + '·' + ids.length + '个';
      elements.push({
        data: {
          id: id, name: name, full: gradeWord(grade) + '的 ' + ids.length + ' 个知识点',
          label: clipLabel(name), bg: tone[0], border: tone[1], color: colors.text
        },
        classes: kind + ' grade'
      });
      ids.forEach(function (topicId) { bucket.set(topicId, id); });
    });
    const seen = new Map();
    lay.edges.forEach(function (e) {
      const a = bucket.get(e.from);
      const b = bucket.get(e.to);
      if (!a || !b || a === b) return;
      const key = a + '>' + b;
      const kind = !e.direct ? 'indirect' : (e.strength === 'soft' ? 'soft' : 'hard');
      const rank = kind === 'hard' ? 3 : kind === 'soft' ? 2 : 1;
      const prev = seen.get(key);
      if (!prev || rank > prev.rank) seen.set(key, { kind: kind, rank: rank });
    });
    let edgeIndex = 0;
    seen.forEach(function (info, key) {
      const parts = key.split('>');
      const color = info.kind === 'hard' ? colors.edge : colors.edgeSoft;
      elements.push({
        data: { id: 'e' + (edgeIndex++), source: parts[0], target: parts[1], color: color },
        classes: info.kind
      });
    });
    return elements;
  }
  function updatePathFold(total, folded) {
    const box = document.getElementById('path-fold');
    if (!box) return;
    if (total <= PATH_FOLD_AT) {
      box.hidden = true;
      box.replaceChildren();
      return;
    }
    box.hidden = false;
    if (folded) {
      box.replaceChildren(
        document.createTextNode('路径较长，已按年级收起中间知识点。根因和目标仍单独画出。'),
        h('button', { type: 'button', id: 'btn-path-expand', text: '展开全部 ' + total + ' 个' })
      );
    } else {
      box.replaceChildren(
        document.createTextNode('已展开全部 ' + total + ' 个知识点。'),
        h('button', { type: 'button', id: 'btn-path-collapse', text: '按年级收起' })
      );
    }
  }
  function pathZoom(factor) {
    if (!pathCy) return;
    const rect = pathCy.container().getBoundingClientRect();
    pathCy.zoom({
      level: Math.max(pathCy.minZoom(), Math.min(pathCy.maxZoom(), pathCy.zoom() * factor)),
      renderedPosition: { x: rect.width / 2, y: rect.height / 2 }
    });
  }
  function pathFit() {
    if (!pathCy) return;
    pathCy.resize();
    const many = pathCy.nodes().length > 48;
    if (many) pathCy.minZoom(0.45);
    pathCy.fit(undefined, 28);
    if (many && pathCy.zoom() < 0.45) {
      pathCy.zoom(0.55);
      pathCy.center();
    }
  }
  function hidePathTip() {
    const tip = document.getElementById('node-tip');
    if (tip) tip.hidden = true;
  }
  function showPathTip(node) {
    const tip = document.getElementById('node-tip');
    const stage = document.querySelector('.path-graph');
    if (!tip || !stage || !pathCy || !node || node.empty()) return;
    const text = node.data('full') || node.data('label') || '';
    if (!text) { tip.hidden = true; return; }
    tip.textContent = text;
    tip.hidden = false;
    const stageRect = stage.getBoundingClientRect();
    const cyRect = pathCy.container().getBoundingClientRect();
    const bb = node.renderedBoundingBox({ includeLabels: true });
    const tipW = tip.offsetWidth;
    const tipH = tip.offsetHeight;
    const cx = cyRect.left - stageRect.left + (bb.x1 + bb.x2) / 2;
    const top = cyRect.top - stageRect.top + bb.y1;
    let left = Math.max(8, Math.min(cx - tipW / 2, Math.max(8, stageRect.width - tipW - 8)));
    let y = top - tipH - 8;
    if (y < 4) y = cyRect.top - stageRect.top + bb.y2 + 8;
    if (y + tipH > stageRect.height - 4) y = Math.max(4, stageRect.height - tipH - 4);
    tip.style.left = left + 'px';
    tip.style.top = y + 'px';
  }
  function ensureDagre() {
    if (!window.cytoscape || !window.dagre || !window.cytoscapeDagre) throw new Error('图形库没有加载');
    if (!ensureDagre.ready) { window.cytoscape.use(window.cytoscapeDagre); ensureDagre.ready = true; }
  }
  function mountPathGraph(sum) {
    const token = ++pathToken;
    if (pathCy) { pathCy.destroy(); pathCy = null; window.__pathCy = null; }
    const cyEl = document.getElementById('path-cy');
    if (!cyEl) return;
    cyEl.dataset.ready = '0';
    hidePathTip();
    const lay = E.layout(D.graph, session, sum);
    requestAnimationFrame(function () {
      if (token !== pathToken || !document.body.contains(cyEl)) return;
      try {
        ensureDagre();
        const colors = theme();
        const narrow = labelLimit() <= 8;
        const textMax = narrow ? 104 : 126;
        const boxW = narrow ? 118 : 142;
        const FONT = '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "Noto Sans SC", sans-serif';
        const total = lay.nodes.length;
        const folded = total > PATH_FOLD_AT && !pathExpanded;
        const heavy = !folded && total > 48;
        updatePathFold(total, folded);
        cyEl.dataset.mode = folded ? 'grade' : 'full';
        cyEl.dataset.total = String(total);
        const elements = buildPathElements(lay, colors, folded);
        pathCy = window.cytoscape({
          container: cyEl,
          elements: elements,
          minZoom: heavy ? 0.45 : 0.2,
          maxZoom: 2.8,
          wheelSensitivity: 0.28,
          boxSelectionEnabled: false,
          autoungrabify: true,
          userPanningEnabled: true,
          userZoomingEnabled: true,
          style: [
            { selector: 'node', style: {
              label: 'data(label)', 'text-wrap': 'ellipsis', 'text-max-width': textMax + 'px',
              'text-overflow-wrap': 'anywhere',
              'text-valign': 'center', 'text-halign': 'center',
              'font-size': 13, 'font-family': FONT, color: 'data(color)',
              'background-color': 'data(bg)', 'border-width': 2, 'border-color': 'data(border)',
              shape: 'round-rectangle', width: boxW, height: 34, padding: 0, 'corner-radius': 8
            } },
            { selector: 'node.current', style: { 'border-width': 4, 'z-index': 8 } },
            { selector: 'node.root', style: {
              'background-color': colors.badBg, 'border-color': colors.bad, 'border-width': 4, 'z-index': 11
            } },
            { selector: 'edge', style: {
              width: 1.6, 'line-color': 'data(color)', 'target-arrow-color': 'data(color)',
              'target-arrow-shape': 'triangle', 'curve-style': heavy ? 'straight' : 'bezier', 'arrow-scale': 0.8, 'line-style': 'solid'
            } },
            { selector: 'edge.soft', style: { 'line-style': 'dashed', width: 1.5 } },
            { selector: 'edge.indirect', style: { 'line-style': 'dotted', width: 1.4 } }
          ]
        });
        window.__pathCy = pathCy;
        pathCy.on('mouseover', 'node', function (event) { showPathTip(event.target); });
        pathCy.on('mouseout', 'node', function () { if (!pathTipLock) hidePathTip(); });
        pathCy.on('tap', 'node', function (event) { pathTipLock = true; showPathTip(event.target); });
        pathCy.on('tap', function (event) {
          if (event.target === pathCy) { pathTipLock = false; hidePathTip(); }
        });
        const layout = pathCy.layout({
          name: 'dagre', rankDir: 'TB',
          rankSep: heavy ? 46 : 64,
          nodeSep: heavy ? 16 : 22,
          edgeSep: heavy ? 8 : 10,
          ranker: heavy ? 'longest-path' : 'network-simplex',
          padding: 16, animate: false, fit: true, nodeDimensionsIncludeLabels: false, spacingFactor: heavy ? 1.02 : 1.05
        });
        layout.one('layoutstop', function () {
          if (token !== pathToken || !pathCy) return;
          requestAnimationFrame(function () {
            if (token !== pathToken || !pathCy) return;
            pathCy.resize();
            pathCy.fit(undefined, heavy ? 20 : 24);
            if (heavy && pathCy.zoom() < 0.7) {
              pathCy.zoom(0.8);
              const focusNode = lay.nodes.find(function (n) { return n.isRoot; }) || lay.nodes.find(function (n) { return n.isTarget; }) || lay.nodes[0];
              const focus = focusNode ? pathCy.getElementById(focusNode.id) : null;
              if (focus && !focus.empty()) pathCy.center(focus);
            }
            cyEl.dataset.ready = '1';
          });
        });
        layout.run();
      } catch (error) {
        cyEl.dataset.ready = 'err';
        cyEl.append(h('p', { class: 'muted', text: '图没有画出来：' + (error && error.message ? error.message : error) }));
      }
    });
  }

  /* ------------------------------------------------------------ 导出 / 打印 */
  function exportJson() {
    const sum = E.summarize(D.graph, session);
    const stdIds = new Set();
    const brief = function (id) { return { id: id, name: nameOf(id) }; };
    sum.path.concat(session.mode === 'screen' ? [] : session.targets.map(function (id) { return { id: id }; })).forEach(function (p) {
      (D.graph.byId[p.id].standards || []).forEach(function (sd) { stdIds.add(sd.id); });
    });
    const chapters = session.mode === 'screen' ? E.chapterSummary(D.graph, session) : null;
    const out = {
      tool: 'cn-math-taxonomy/diagnose', version: 2, mode: session.mode || 'target', generatedAt: new Date().toISOString(),
      note: '自动判题是近似的，以参考答案为准。',
      label: sessionMeta.label,
      targets: session.targets.map(brief),
      limit: session.limit, seed: session.seed, asked: sum.asked, finished: sum.finished, limitReached: sum.limitReached,
      answers: session.answers.map(function (a, i) {
        const q = E.questionById(D.graph, a.qid) || {};
        return {
          order: i + 1, topicId: a.id, name: nameOf(a.id), questionId: a.qid, difficulty: q.difficulty, type: q.type,
          prompt: q.prompt, userAnswer: a.text == null ? null : a.text, result: a.result,
          referenceAnswer: q.answer, explanation: q.explanation || ''
        };
      }),
      chapters: chapters ? chapters.map(function (c) {
        return {
          label: c.label, total: c.total, mastered: c.mastered, shaky: c.shaky, weak: c.weak, untested: c.untested,
          weakTopics: c.weakIds.map(brief), shakyTopics: c.shakyIds.map(brief), untestedTopics: c.untestedIds.map(brief)
        };
      }) : undefined,
      weakRoots: sum.roots.map(function (r) {
        return Object.assign(brief(r.id), {
          pendingPrereqs: r.pendingPrereqs, outOfScopePrereqs: r.outOfScopePrereqs, externalPrereqs: r.externalPrereqs,
          masteryCriteria: D.graph.byId[r.id].mastery_criteria || [],
          standards: (D.graph.byId[r.id].standards || []).map(function (sd) { return sd.id; })
        });
      }),
      path: sum.path.map(function (p, i) { return Object.assign({ order: i + 1 }, brief(p.id), { status: p.status, isRoot: p.isRoot, isTarget: p.isTarget }); }),
      weak: sum.weak.map(brief),
      shaky: sum.shaky.map(brief),
      mastered: sum.mastered.map(function (id) { return Object.assign(brief(id), { source: session.status[id].src }); }),
      untested: sum.untested.map(function (id) { return Object.assign(brief(id), { external: !!D.graph.byId[id].external }); }),
      standards: Array.from(stdIds).sort().map(function (k) { return { id: k, text: D.stdById[k] ? D.stdById[k].text : '' }; })
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'diagnosis-' + new Date().toISOString().slice(0, 10) + '.json' });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }

  function printPage() { window.print(); }
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('details:not([open])').forEach(function (d) { d.setAttribute('open', ''); d.dataset.autoOpen = '1'; });
    if (pathCy) { pathCy.resize(); pathCy.fit(undefined, 20); }
  });
  window.addEventListener('afterprint', function () {
    document.querySelectorAll('details[data-auto-open]').forEach(function (d) { d.removeAttribute('open'); delete d.dataset.autoOpen; });
  });

  /* ------------------------------------------------------------ 启动 */
  function resolveTargets(params) {
    const t = params.get('target');
    if (t) {
      const raw = t.split(',').map(function (x) { return x.trim(); }).filter(Boolean);
      const ids = E.resolveTargets(raw, D.aliases);
      const bad = ids.filter(function (id) { return !D.graph.byId[id] || D.graph.byId[id].external; });
      if (bad.length) throw new Error('URL 参数 target 里有无效知识点：' + bad.join(', '));
      const aliased = raw.filter(function (id) { return D.aliases[id]; });
      let label = ids.map(nameOf).join('、');
      if (aliased.length) {
        label = aliased.map(function (id) { return (D.aliases[id].name || id); }).join('、') + '（旧编号已对应到小学知识点）';
        if (ids.length <= 6) label += '：' + ids.map(nameOf).join('、');
      }
      return { ids: ids, label: label };
    }
    const c = params.get('chapter');
    if (c) {
      const hit = [];
      VOLUMES.forEach(function (vv) {
        ((D.tree[vv[0]] || {}).chapters || []).forEach(function (ch) { if (ch.key === c.trim()) hit.push(ch); });
      });
      if (!hit.length) throw new Error('URL 参数 chapter 没有匹配的章节：' + c + '（格式如 “七上 第一章”）');
      return { ids: hit[0].topics.map(function (x) { return x.t.id; }), label: hit[0].volume + ' ' + hit[0].label + '（整章）' };
    }
    const grade = (params.get('grade') || '').trim();
    const volume = (params.get('volume') || '').trim();
    if (grade || volume) {
      let scope = volume || grade;
      const seniorUrl = {
        '高一': '高一', '高一必修': '高一', '高二': '高二', '高二必修': '高二',
        '选必一': '选必一', '选择性必修第一册': '选必一',
        '选必二': '选必二', '选择性必修第二册': '选必二',
        '选必三': '选必三', '选择性必修第三册': '选必三',
        '选必四': '选必四', '选择性必修第四册': '选必四',
        '必修一': '必修一', '必修第一册': '必修一',
        '必修二': '必修二', '必修第二册': '必修二',
        '必修三': '必修三', '必修第三册': '必修三'
      };
      if (seniorUrl[grade]) {
        if (volume && volume !== '必修' && volume !== '整册' && volume !== '必修整册') {
          throw new Error(subject === 'english'
            ? '高中英语不拆上下册：' + grade + ' / ' + volume + '（用 grade=必修一 或 grade=选必一）'
            : subject === 'physics'
            ? '高中物理不拆上下册：' + grade + ' / ' + volume + '（用 grade=必修一 或 grade=选必一）'
            : '高中不拆上下册：' + grade + ' / ' + volume + '（用 grade=高一、grade=高二 或 grade=选必二）');
        }
        scope = seniorUrl[grade];
      } else if (grade && volume) {
        const gch = /^[一二三四五六七八九]$/.test(grade) ? grade : grade.charAt(0);
        scope = (volume === '全' || volume === '全一册') ? gch + '全' : (/^[上下]$/.test(volume) ? gch + volume : volume);
        if (scope.charAt(0) !== gch) throw new Error('URL 参数 grade 与 volume 不一致：' + grade + ' / ' + volume);
      }
      if (/^[一二三四五六七八九]$/.test(scope)) scope += '年级';
      const g = E.gradeTargets(D.graph, scope, subject);
      if (!g) throw new Error('URL 参数 grade / volume 无法识别：' + (volume || grade) + '（写法如 grade=七年级、volume=七上）');
      return { ids: g.ids, label: g.label + '（整体筛查）', mode: 'screen' };
    }
    return null;
  }

  async function init() {
    subject = detectSubject();
    applySubjectChrome();
    try { await loadData(); } catch (e) {
      clearRoot();
      root.append(h('div', { class: 'card' }, h('h2', { class: 'err', text: '数据加载失败' }),
        h('p', null, String(e.message || e)),
        h('p', null, '请在项目根目录运行 ', h('code', { text: 'python3 -m http.server 8000' }), '，再访问 http://localhost:8000/diagnose/ （不能直接用 file:// 打开）。')));
      return;
    }
    const params = new URLSearchParams(location.search);
    let resolved = null;
    try { resolved = resolveTargets(params); } catch (e) { renderStart(e.message); return; }
    if (params.get('seed')) seedParam = params.get('seed');
    const paramLimit = parseInt(params.get('limit'), 10);
    const limit = paramLimit > 0 ? paramLimit : undefined;
    if (resolved && params.get('demo')) {
      demo = { oracle: makeOracle(resolved.ids, resolved.mode) };
      session = E.createSession(D.graph, resolved.ids, {
        mode: resolved.mode, limit: limit || (resolved.mode === 'screen' ? getSettings().screenLimit : getSettings().limit),
        confirm: getSettings().confirm, seed: seedParam == null ? 'demo' : seedParam
      });
      sessionMeta = { label: resolved.label };
      const step = parseInt(params.get('step'), 10);
      runDemo(step >= 0 ? step : Infinity);
      render();
      return;
    }
    if (resolved) {
      const saved = lsGet(sessionKey());
      const same = saved && JSON.stringify(saved.targets) === JSON.stringify(Array.from(new Set(resolved.ids))) &&
        (saved.mode || 'target') === (resolved.mode || 'target') && (seedParam == null || saved.seed === seedParam);
      if (same && restoreSession(saved)) { render(); return; }
      startSession(resolved.ids, resolved.label, limit, resolved.mode);
      return;
    }
    renderStart();
  }

  document.addEventListener('click', function (event) {
    const origin = event.target && event.target.closest ? event.target : (event.target && event.target.parentElement);
    if (!origin || !origin.closest) return;
    if (!origin.closest('#btn-path-expand') && !origin.closest('#btn-path-collapse')) return;
    pathExpanded = !!origin.closest('#btn-path-expand');
    if (session && D) mountPathGraph(E.summarize(D.graph, session));
  });

  if (window.matchMedia) {
    const scheme = window.matchMedia('(prefers-color-scheme: dark)');
    const relayout = function () {
      if (!session || !document.getElementById('path-cy')) return;
      mountPathGraph(E.summarize(D.graph, session));
    };
    if (scheme.addEventListener) scheme.addEventListener('change', relayout);
    const narrow = window.matchMedia('(max-width: 700px)');
    if (narrow.addEventListener) narrow.addEventListener('change', relayout);
  }

  init();
})();
