/* 巩固过关练习界面。规则全部在 engine.js（PracticeEngine），变式题在 variants.js（CnmVariants），
 * 判题沿用 diagnose/engine.js（DiagEngine.judgeQuestion）。这里只负责加载数据、渲染和本地存储。
 * URL：?target=<知识点 id>&subject=<math|english|physics>（subject 省略时按 id 前缀推断） */
(function () {
  'use strict';
  const E = window.DiagEngine;
  const P = window.PracticeEngine;
  const V = window.CnmVariants;
  const CC = window.CnmChildren;
  const WS = window.CnmWorkspace;
  const LS_PREFIX = 'cnmPractice.v1:';
  const DIFF_LABEL = { basic: '基础', standard: '标准', advanced: '提高' };

  const root = document.getElementById('root');
  const params = new URLSearchParams(location.search);
  const target = (params.get('target') || '').trim();
  const subject = (function () {
    const s = params.get('subject');
    if (s === 'math' || s === 'english' || s === 'physics') return s;
    return /^cne_/.test(target) ? 'english' : /^cnp_/.test(target) ? 'physics' : 'math';
  })();
  let topic = null;
  let bank = [];
  let templates = null;
  let state = null;
  let ui = null;

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
      else if (k === 'disabled' || k === 'value') el[k] = v;
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
  function show(node) { while (root.firstChild) root.removeChild(root.firstChild); root.append(node); }
  function lsGet(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* 隐私模式 */ } }
  function lsDel(k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } }
  function storeKey() { return LS_PREFIX + target; }
  function figureEl(svg) {
    if (typeof svg !== 'string' || svg.indexOf('<svg') !== 0) return null;
    if (/<\s*script|foreignObject|<\s*image\b|https?:\/\//i.test(svg.replace('xmlns="http://www.w3.org/2000/svg"', ''))) return null;
    const wrap = h('div', { class: 'q-figure' });
    wrap.innerHTML = svg;
    return wrap.querySelector('svg') ? wrap : null;
  }
  function withSubject(href) { return subject === 'math' ? href : href + (href.indexOf('?') >= 0 ? '&' : '?') + 'subject=' + subject; }
  function variant(q, tid, seed) { return V ? V.generateVariant(q, tid, seed, templates) : null; }
  function fmtDate(iso) {
    const d = new Date(iso);
    const p = function (n) { return ('0' + n).slice(-2); };
    return (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日 ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function applySubjectUi() {
    document.body.classList.toggle('subject-english', subject === 'english');
    document.body.classList.toggle('subject-physics', subject === 'physics');
    document.querySelectorAll('.subject-link').forEach(function (link) {
      const on = link.getAttribute('data-subject') === subject;
      link.classList.toggle('on', on);
      link.setAttribute('href', '../diagnose/' + (link.getAttribute('data-subject') === 'math' ? '' : '?subject=' + link.getAttribute('data-subject')));
    });
  }

  /* ------------------------------------------------------------ 数据 */
  async function fetchJson(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(url + ' → HTTP ' + r.status);
    return r.json();
  }
  async function loadQuestions() {
    for (const url of ['../data/questions-' + subject + '.json', '../data/questions.json']) {
      try { const rows = await fetchJson(url); if (Array.isArray(rows)) return rows; } catch (e) { /* 回退 */ }
    }
    return [];
  }
  async function load() {
    const topics = await fetchJson('../data/topics.json');
    topic = topics.find(function (t) { return t.id === target; }) || null;
    if (!topic) return;
    const rows = await loadQuestions();
    bank = rows.filter(function (q) { return q.topicId === target; });
    if (subject === 'math') {
      try { templates = await fetchJson('../data/question-templates.json'); } catch (e) { templates = null; }
    }
  }

  /* ------------------------------------------------------------ 状态 */
  function save() { if (state) lsSet(storeKey(), state); }
  function begin(fresh) {
    const saved = fresh ? null : lsGet(storeKey());
    if (saved && saved.topicId === target && saved.current && !saved.passed) state = saved;
    else state = P.createPractice(topic, bank, { seed: Math.random().toString(36).slice(2, 10), variant: variant });
    ui = { answer: '', picked: null, verdict: null };
    save();
    render();
  }

  function submit() {
    const q = state.current;
    const val = (q.type === 'choice' ? ui.picked || '' : ui.answer).trim();
    if (!val) { const el = document.getElementById('ans'); if (el) el.focus(); return; }
    const r = E.judgeQuestion(q, val);
    if (r.verdict === 'manual') { ui.verdict = r; render(); return; }
    commit(r.verdict === 'correct');
  }
  function commit(ok) {
    state = P.submit(state, ok);
    ui.verdict = null;
    if (state.phase === 'retry') { ui.answer = ''; ui.picked = null; }
    if (state.phase === 'passed') onPassed();
    if (state.phase === 'reveal') onReveal();
    save();
    render();
  }
  function goNext() {
    state = P.next(state, bank, { variant: variant });
    ui = { answer: '', picked: null, verdict: null };
    save();
    render();
  }
  let passedEntry = null;
  function onPassed() {
    passedEntry = CC && CC.markPracticed ? CC.markPracticed(target, { subject: subject }) : null;
    lsDel(storeKey());
  }
  function onReveal() {
    // 复习到期的知识点练习时又错了：降回不稳，复习间隔从头来
    const cur = CC && CC.current();
    if (!cur || !CC.practiceOf) return;
    const e = CC.practiceOf(cur.id)[target];
    if (e && e.status === 'mastered' && Date.parse(e.nextReviewAt) <= Date.now()) CC.markShaky(target, { subject: subject });
  }

  /* ------------------------------------------------------------ 渲染 */
  function streakDots() {
    const dots = [];
    for (let i = 0; i < state.need; i++) dots.push(h('span', { class: 'dot' + (i < state.streak ? ' on' : ''), 'aria-hidden': 'true' }));
    return h('div', { class: 'streak', 'aria-label': '已连对 ' + state.streak + ' / ' + state.need },
      dots, h('span', { class: 'muted small', text: '　无提示连对 ' + state.streak + ' / ' + state.need }));
  }

  function header() {
    const cur = CC && CC.current();
    return h('div', { class: 'card', id: 'practice-head' },
      h('h2', null, '巩固过关：' + topic.name, ' ', h('span', { class: 'tag', text: topic.chapter || '' })),
      topic.description ? h('p', { class: 'muted small', text: topic.description }) : null,
      h('p', { class: 'muted small' },
        '规则：题目由易到难；不看提示、一次做对算 1 连对，连对 ' + state.need + ' 题就过关。第一次做错可以马上再试一次，再错会给出解析并重新计数。',
        cur ? ' 过关结果会记到「' + cur.name + '」的档案里。' : ' 没有选孩子档案，过关结果不会保存。'));
  }

  function answerArea(q) {
    if (q.type === 'choice') {
      return h('div', { class: 'choices' + (q.hideChoiceText ? ' fig-icons' : ''), id: 'choices' }, (q.choices || []).map(function (c) {
        const hideName = !!(q.hideChoiceText && c.figure);
        const kids = [h('b', { class: 'choice-key', text: hideName ? c.key : (c.key + '.') })];
        if (!hideName) kids.push(document.createTextNode(' ' + c.text));
        const fig = c.figure ? figureEl(c.figure) : null;
        if (fig) kids.push(fig);
        return h('button', {
          class: 'choice' + (c.figure ? ' fig-choice' : '') + (ui.picked === c.key ? ' picked' : ''), id: 'choice-' + c.key,
          onclick: function () { ui.picked = c.key; render(); }
        }, kids);
      }));
    }
    return h('input', {
      type: 'text', class: 'ans-input', id: 'ans', autocomplete: 'off', value: ui.answer,
      placeholder: '在这里输入答案（数字、分数；多个答案用逗号隔开）',
      oninput: function (e) { ui.answer = e.target.value; },
      onkeydown: function (e) { if (e.key === 'Enter' && !e.isComposing) submit(); }
    });
  }

  function answerText(q) {
    if (q.type === 'choice') {
      const c = (q.choices || []).find(function (x) { return x.key === q.answer; });
      return q.answer + (c ? '. ' + c.text : '');
    }
    return q.answer;
  }

  function questionCard() {
    const q = state.current;
    const hints = P.synthesizeHints(q, topic);
    const card = h('div', { class: 'card', id: 'practice-card' });
    card.append(
      h('div', { class: 'row small' },
        h('span', { class: 'tag diff-' + q.difficulty, text: DIFF_LABEL[q.difficulty] || q.difficulty }),
        q.variantOf ? h('span', { class: 'tag', text: '变式题' }) : null,
        h('span', { class: 'grow' }),
        h('span', { class: 'muted', text: '第 ' + (state.round + 1) + ' 题' })),
      streakDots(),
      h('div', { class: 'q-text', id: 'q-text', text: q.prompt }),
      figureEl(q.figure));

    if (state.phase === 'ask' || state.phase === 'retry') {
      if (state.phase === 'retry') card.append(h('p', { class: 'notice', id: 'retry-note' }, '这次没做对，别急，再看一遍题目，原地再试一次。'));
      card.append(answerArea(q));
      if (ui.verdict && ui.verdict.verdict === 'manual') {
        card.append(h('div', { class: 'notice' }, '这道题没法自动判，请对照参考答案自己判断：',
          h('div', { class: 'refans' }, h('b', null, '参考答案：'), answerText(q)),
          h('div', { class: 'row' },
            h('button', { class: 'good', onclick: function () { commit(true); } }, '我做对了'),
            h('button', { class: 'bad', onclick: function () { commit(false); } }, '没做对'))));
      }
      card.append(h('div', { class: 'row', style: 'margin-top:10px' },
        h('button', { class: 'primary', id: 'btn-submit', onclick: submit }, state.phase === 'retry' ? '再交一次' : '提交答案'),
        state.hintsUsed < hints.length
          ? h('button', { id: 'btn-hint', onclick: function () { state = P.useHint(state); save(); render(); } }, state.hintsUsed ? '再给一点提示（第 2 级）' : '给点提示（第 1 级）')
          : null));
      if (state.hintsUsed) {
        card.append(h('div', { class: 'hints', id: 'hints' },
          hints.slice(0, state.hintsUsed).map(function (x, i) { return h('p', { class: 'hint' }, h('b', null, '提示 ' + (i + 1) + '：'), x); }),
          h('p', { class: 'muted small', text: '看了提示做对，这题不算连对。' })));
      }
    } else if (state.phase === 'correct') {
      const last = state.log[state.log.length - 1];
      card.append(
        h('div', { class: 'verdict ok' }, last.counted ? '✔ 做对了！连对 +1' : (last.hints ? '✔ 做对了（用了提示，这题不算连对）' : '✔ 改对了！（重试做对不算连对，但连对也没有断）')),
        q.explanation ? h('div', { class: 'explain' }, h('b', null, '解析：'), q.explanation) : null,
        h('div', { class: 'row' }, h('button', { class: 'primary', id: 'btn-next', onclick: goNext }, '下一题')));
    } else if (state.phase === 'reveal') {
      card.append(
        h('div', { class: 'verdict no' }, '两次都没做对，连对重新计数。看看解析：'),
        h('div', { class: 'refans' }, h('b', null, '参考答案：'), answerText(q)),
        q.explanation ? h('div', { class: 'explain', id: 'explain' }, h('b', null, '解析：'), q.explanation) : null,
        h('div', { class: 'row' }, h('button', { class: 'primary', id: 'btn-next', onclick: goNext }, '看懂了，下一题')));
    }
    // 同一题（含原位重试）重画时沿用同一个抽屉，草稿不丢；下一题才换新的
    if (WS && (state.phase === 'ask' || state.phase === 'retry')) {
      if (!ui.ws || ui.wsRound !== state.round) { ui.ws = WS.mount(null, topic); ui.wsRound = state.round; }
      card.append(ui.ws);
    }
    return card;
  }

  function passedCard() {
    const cur = CC && CC.current();
    return h('div', { class: 'card passed', id: 'passed' },
      h('h2', null, '🎉 过关！「' + topic.name + '」已巩固'),
      h('p', null, '一共做了 ' + state.total + ' 题，不看提示连对 ' + state.need + ' 题。'),
      passedEntry
        ? h('p', null, '已记入「' + cur.name + '」的档案：状态升为「已掌握」，建议 ', h('b', { text: fmtDate(passedEntry.nextReviewAt) }), ' 之后回来复习一次（间隔会越来越长：12 小时 → 3 天 → 7 天 → 14 天）。')
        : h('p', { class: 'muted' }, '没有选孩子档案，这次过关没有保存。'),
      h('div', { class: 'row' },
        h('a', { class: 'btn btn-primary', href: withSubject('../children/history.html'), text: '回到档案' }),
        h('a', { class: 'btn', href: withSubject('../explore/') + '#' + encodeURIComponent(target), text: '在知识图谱里看它' }),
        h('button', { onclick: function () { passedEntry = null; begin(true); } }, '再练一轮')));
  }

  function render() {
    if (!state) return;
    const page = h('div');
    page.append(header());
    if (state.phase === 'empty') page.append(h('div', { class: 'card' }, h('p', null, '这个知识点暂时没有可以自动判分的练习题。'),
      h('a', { class: 'btn', href: withSubject('../diagnose/?target=' + encodeURIComponent(target)), text: '去做诊断' })));
    else if (state.phase === 'passed') page.append(passedCard());
    else page.append(questionCard());
    show(page);
    const inp = document.getElementById('ans');
    if (inp && (state.phase === 'ask' || state.phase === 'retry')) inp.focus();
  }

  function renderMissing() {
    show(h('div', { class: 'card' },
      h('h2', null, '巩固过关'),
      h('p', null, target ? '找不到知识点「' + target + '」。' : '还没有选要巩固的知识点。'),
      h('p', { class: 'muted' }, '从诊断结果页或孩子档案里的薄弱 / 不稳知识点旁点「去巩固过关（3连对）」进来。'),
      h('div', { class: 'row' },
        h('a', { class: 'btn btn-primary', href: withSubject('../diagnose/'), text: '去诊断' }),
        h('a', { class: 'btn', href: withSubject('../children/history.html'), text: '孩子档案' }))));
  }

  applySubjectUi();
  load().then(function () {
    if (!topic) { renderMissing(); return; }
    document.title = '巩固 · ' + topic.name;
    begin(false);
  }).catch(function (e) {
    show(h('div', { class: 'card' }, h('p', { class: 'notice' }, '无法读取数据（' + (e && e.message || e) + '）。请在项目根目录运行 python3 -m http.server 8000，不要直接用 file:// 打开。')));
  });
})();
