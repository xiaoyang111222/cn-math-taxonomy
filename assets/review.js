/* 审校模式（URL 带 ?review=1）：老师在先修边和题目下方直接标注修改意见，暂存在本机，一键导出 review-patch.json。
 * 只记录意见，不改动任何数据文件；维护者拿到 review-patch.json 后人工合并。
 *
 * 纯函数（Node 里可 require）：
 *   upsert(patches, patch) -> 新数组（同一条边 / 同一道题的同一字段只保留最新一条）
 *   remove(patches, key) -> 新数组；keyOf(patch)；buildExport(patches, meta) -> review-patch.json 内容
 *   patch 形如：
 *     {type:'edge', topicId, prerequisiteId, action:'hard'|'soft'|'remove', from:'hard'|'soft', comment?, at}
 *     {type:'question', questionId, topicId, field:'prompt'|'explanation'|'answer', from, to, comment?, at}
 * 浏览器里：window.CnmReview = { enabled, list, add, clear, edgeControls, questionControls, mountPanel, download }
 *   存储键 localStorage['cnmReview.patches.v1']。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.CnmReview = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const STORE_KEY = 'cnmReview.patches.v1';
  const EDGE_ACTIONS = { hard: '改为 hard（硬先修）', soft: '改为 soft（软先修）', remove: '这条边多余，建议删除' };
  const Q_FIELDS = { prompt: '题干', explanation: '解析', answer: '答案' };

  function keyOf(p) {
    if (p.type === 'edge') return 'edge:' + p.topicId + '<' + p.prerequisiteId;
    return 'question:' + p.questionId + ':' + p.field;
  }

  function valid(p) {
    if (!p || typeof p !== 'object') return false;
    if (p.type === 'edge') return !!(p.topicId && p.prerequisiteId && EDGE_ACTIONS[p.action]);
    if (p.type === 'question') return !!(p.questionId && Q_FIELDS[p.field] && typeof p.to === 'string' && p.to.trim() && p.to !== p.from);
    return false;
  }

  function upsert(patches, patch) {
    if (!valid(patch)) return patches.slice();
    const k = keyOf(patch);
    const out = patches.filter(function (x) { return keyOf(x) !== k; });
    // 把边改回它原来的强度 = 撤销这条意见
    if (patch.type === 'edge' && patch.action === patch.from) return out;
    out.push(Object.assign({}, patch, { at: patch.at || new Date().toISOString() }));
    return out;
  }

  function remove(patches, key) { return patches.filter(function (x) { return keyOf(x) !== key; }); }

  function buildExport(patches, meta) {
    const edges = patches.filter(function (p) { return p.type === 'edge'; });
    const questions = patches.filter(function (p) { return p.type === 'question'; });
    return Object.assign({
      format: 'cnm-review-patch', version: 1, exportedAt: new Date().toISOString(),
      summary: { edges: edges.length, questions: questions.length },
      note: '审校意见，未合并进数据文件。edge.action：hard / soft 改强度，remove 删除；question：field 字段从 from 改为 to。'
    }, meta || {}, { patches: patches.slice() });
  }

  const api = { STORE_KEY: STORE_KEY, EDGE_ACTIONS: EDGE_ACTIONS, Q_FIELDS: Q_FIELDS, keyOf: keyOf, valid: valid, upsert: upsert, remove: remove, buildExport: buildExport };
  if (typeof document === 'undefined') return api;

  /* ------------------------------------------------------------ 浏览器 */
  function enabled() {
    try { return new URLSearchParams(location.search).get('review') === '1'; } catch (e) { return false; }
  }
  function list() {
    try { const v = JSON.parse(localStorage.getItem(STORE_KEY)); return Array.isArray(v) ? v.filter(valid) : []; } catch (e) { return []; }
  }
  function save(ps) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(ps)); } catch (e) { alert('浏览器不允许保存（可能是隐私模式），审校意见没有存下来。'); }
    listeners.forEach(function (fn) { try { fn(ps); } catch (e) { /* ignore */ } });
  }
  const listeners = [];
  function add(patch) { const ps = upsert(list(), patch); save(ps); return ps; }
  function drop(key) { const ps = remove(list(), key); save(ps); return ps; }
  function clear() { save([]); }
  function find(key) { return list().filter(function (p) { return keyOf(p) === key; })[0] || null; }

  function h(tag, attrs) {
    const el = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      const v = attrs[k];
      if (v == null || v === false) return;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k.indexOf('on') === 0) el.addEventListener(k.slice(2), v);
      else if (k === 'value') el.value = v;
      else el.setAttribute(k, v === true ? '' : v);
    });
    for (let i = 2; i < arguments.length; i++) [].concat(arguments[i]).forEach(function (c) { if (c != null) el.append(c.nodeType ? c : document.createTextNode(String(c))); });
    return el;
  }
  function injectStyle() {
    if (document.getElementById('review-style')) return;
    const st = document.createElement('style');
    st.id = 'review-style';
    st.textContent = [
      '.rv{margin:4px 0 8px;padding:6px 8px;border:1px dashed #c58b00;border-radius:8px;background:rgba(227,179,65,.10);font-size:.85rem}',
      '.rv .rv-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}',
      '.rv button{font-size:.82rem;padding:2px 8px}',
      '.rv button.on{background:#c58b00;color:#fff;border-color:transparent}',
      '.rv textarea{width:100%;min-height:4em;margin:4px 0;font:inherit}',
      '.rv-done{color:#8a6100;font-weight:600}',
      '.rv-panel{position:fixed;right:12px;bottom:12px;z-index:50;background:var(--bg,#fff);border:2px solid #c58b00;border-radius:12px;padding:8px 12px;box-shadow:0 4px 16px rgba(0,0,0,.15);font-size:.9rem;max-width:calc(100vw - 24px)}',
      '.rv-panel .rv-row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}'
    ].join('\n');
    document.head.appendChild(st);
  }

  /** 一条先修边下方的审校按钮：改 hard / 改 soft / 多余。 */
  function edgeControls(topicId, prerequisiteId, strength, meta) {
    injectStyle();
    const from = strength === 'soft' ? 'soft' : 'hard';
    const key = keyOf({ type: 'edge', topicId: topicId, prerequisiteId: prerequisiteId });
    const box = h('div', { class: 'rv rv-edge', 'data-edge': topicId + '<' + prerequisiteId });
    function draw() {
      box.textContent = '';
      const cur = find(key);
      const btn = function (action, label) {
        return h('button', { type: 'button', class: cur && cur.action === action ? 'on' : null, title: EDGE_ACTIONS[action],
          onclick: function (e) {
            e.preventDefault(); e.stopPropagation();
            if (cur && cur.action === action) drop(key);
            else add({ type: 'edge', topicId: topicId, prerequisiteId: prerequisiteId, action: action, from: from, names: meta || undefined });
            draw();
          } }, label);
      };
      box.append(h('div', { class: 'rv-row' },
        h('span', { class: 'muted', text: '审校：现为 ' + from }),
        from === 'soft' ? btn('hard', '应为 hard') : btn('soft', '应为 soft'),
        btn('remove', '多余'),
        cur ? h('span', { class: 'rv-done', text: '✔ 已记：' + EDGE_ACTIONS[cur.action] }) : null));
    }
    draw();
    return box;
  }

  /** 一道题下方的审校按钮：修正题干 / 解析（/ 答案）。 */
  function questionControls(q) {
    injectStyle();
    const box = h('div', { class: 'rv rv-question', 'data-qid': q.id });
    let editing = null;
    function draw() {
      box.textContent = '';
      const done = Object.keys(Q_FIELDS).filter(function (f) { return find(keyOf({ type: 'question', questionId: q.id, field: f })); });
      box.append(h('div', { class: 'rv-row' },
        h('span', { class: 'muted', text: '审校 ' + q.id + '：' }),
        Object.keys(Q_FIELDS).map(function (f) {
          return h('button', { type: 'button', class: editing === f ? 'on' : null, onclick: function (e) { e.preventDefault(); editing = editing === f ? null : f; draw(); } }, '修正' + Q_FIELDS[f]);
        }),
        done.length ? h('span', { class: 'rv-done', text: '✔ 已记：' + done.map(function (f) { return Q_FIELDS[f]; }).join('、') }) : null));
      if (editing) {
        const f = editing;
        const k = keyOf({ type: 'question', questionId: q.id, field: f });
        const prev = find(k);
        const ta = h('textarea', { value: prev ? prev.to : (q[f] || ''), 'aria-label': '修正后的' + Q_FIELDS[f] });
        const note = h('input', { type: 'text', placeholder: '说明（可选）：为什么要改', value: prev && prev.comment ? prev.comment : '', style: 'width:100%' });
        box.append(ta, note, h('div', { class: 'rv-row' },
          h('button', { type: 'button', class: 'primary', onclick: function (e) {
            e.preventDefault();
            const to = ta.value.trim();
            if (!to || to === (q[f] || '')) { alert('内容没有变化。'); return; }
            add({ type: 'question', questionId: q.id, topicId: q.topicId, field: f, from: q[f] || '', to: to, comment: note.value.trim() || undefined });
            editing = null; draw();
          } }, '暂存这条修正'),
          prev ? h('button', { type: 'button', onclick: function (e) { e.preventDefault(); drop(k); editing = null; draw(); } }, '撤销这条') : null,
          h('button', { type: 'button', onclick: function (e) { e.preventDefault(); editing = null; draw(); } }, '取消')));
      }
    }
    draw();
    return box;
  }

  function download() {
    const blob = new Blob([JSON.stringify(buildExport(list(), { page: location.pathname }), null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'review-patch.json';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /** 右下角浮动面板：已暂存几条、导出、清空。 */
  function mountPanel() {
    injectStyle();
    if (document.getElementById('review-panel')) return;
    const count = h('b');
    const panel = h('div', { class: 'rv-panel no-print', id: 'review-panel', role: 'region', 'aria-label': '审校模式' },
      h('div', { class: 'rv-row' },
        h('span', null, '📝 审校模式 · 已暂存 ', count, ' 条'),
        h('button', { type: 'button', class: 'primary', id: 'btn-review-export', onclick: download }, '导出 review-patch.json'),
        h('button', { type: 'button', onclick: function () { if (list().length && confirm('清空本机暂存的全部审校意见？')) { clear(); location.reload(); } } }, '清空')));
    const upd = function () { count.textContent = String(list().length); };
    listeners.push(upd);
    upd();
    document.body.appendChild(panel);
  }

  return Object.assign(api, {
    enabled: enabled, list: list, add: add, drop: drop, clear: clear,
    edgeControls: edgeControls, questionControls: questionControls, mountPanel: mountPanel, download: download
  });
});
