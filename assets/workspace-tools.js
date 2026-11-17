/* 题卡底部的两个工具抽屉（零依赖、离线可用）：
 *   ✏️ 草稿本：Canvas 手写，支持 Apple Pencil（压感）、触控、鼠标；画笔 / 橡皮 / 网格 / 撤销 / 清空。
 *   🧮 CPA 实验台（具体—形象—抽象）：动态数轴、百格与分数面积板、代数天平；按 topic.domain 自动选默认标签页。
 * 用法：CnmWorkspace.mount(容器元素, topic) -> 根元素；CnmWorkspace.defaultTab(topic) 是纯函数（Node 里也能 require）。
 * 每次 mount 都是新的草稿（换题时重画题卡即清空），不往 localStorage 写东西。 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.CnmWorkspace = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /** 按知识点选实验台默认标签页：方程 / 等式 -> 天平；分数 / 小数 / 百分 / 面积 / 图形 / 概率 -> 面积板；其余 -> 数轴。 */
  function defaultTab(topic) {
    const name = (topic && topic.name) || '';
    const domain = (topic && topic.domain) || '';
    const desc = (topic && topic.description) || '';
    if (/方程|等式|移项|天平/.test(name + desc)) return 'balance';
    if (/分数|小数|百分|面积|比例|概率|频率/.test(name)) return 'area';
    if (domain === '图形与几何' || domain === '统计与概率') return 'area';
    return 'line';
  }

  if (typeof document === 'undefined') return { defaultTab: defaultTab };

  function h(tag, attrs) {
    const el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      const v = attrs[k];
      if (v == null || v === false) return;
      if (k === 'text') el.textContent = v;
      else if (k.indexOf('on') === 0) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    });
    for (let i = 2; i < arguments.length; i++) {
      const kids = [].concat(arguments[i]);
      kids.forEach(function (c) { if (c != null) el.append(c.nodeType ? c : document.createTextNode(String(c))); });
    }
    return el;
  }
  function css(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  /* ------------------------------------------------------------ 草稿本 */
  function sketchpad() {
    const strokes = [];
    let tool = 'pen';
    let grid = true;
    let cur = null;
    const canvas = h('canvas', { class: 'ws-canvas', 'aria-label': '草稿本画布' });
    const wrap = h('div', { class: 'ws-canvas-wrap' }, canvas);
    const btn = function (label, fn, id) { return h('button', { type: 'button', class: 'small', 'data-tool': id || null, onclick: fn }, label); };
    const penBtn = btn('✏️ 画笔', function () { tool = 'pen'; sync(); }, 'pen');
    const eraseBtn = btn('🧽 橡皮', function () { tool = 'eraser'; sync(); }, 'eraser');
    const gridBtn = btn('网格', function () { grid = !grid; sync(); redraw(); }, 'grid');
    const bar = h('div', { class: 'ws-toolbar row' }, penBtn, eraseBtn, gridBtn,
      btn('↶ 撤销', function () { strokes.pop(); redraw(); }),
      btn('清空', function () { if (strokes.length && confirm('清空草稿本？')) { strokes.length = 0; redraw(); } }));
    function sync() {
      penBtn.classList.toggle('on', tool === 'pen');
      eraseBtn.classList.toggle('on', tool === 'eraser');
      gridBtn.classList.toggle('on', grid);
      canvas.style.cursor = tool === 'eraser' ? 'cell' : 'crosshair';
    }
    function size() {
      const dpr = window.devicePixelRatio || 1;
      const w = Math.max(200, wrap.clientWidth || 600);
      const hgt = Math.round(Math.min(420, Math.max(220, w * 0.55)));
      canvas.style.height = hgt + 'px';
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(hgt * dpr);
      redraw();
    }
    function redraw() {
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (grid) {
        ctx.strokeStyle = css('--ws-grid', 'rgba(15,110,98,.13)');
        ctx.lineWidth = 1;
        const w = canvas.width / dpr; const hh = canvas.height / dpr;
        ctx.beginPath();
        for (let x = 20; x < w; x += 20) { ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, hh); }
        for (let y = 20; y < hh; y += 20) { ctx.moveTo(0, y + 0.5); ctx.lineTo(w, y + 0.5); }
        ctx.stroke();
      }
      strokes.forEach(drawStroke);
    }
    function drawStroke(s) {
      const ctx = canvas.getContext('2d');
      ctx.save();
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      if (s.tool === 'eraser') { ctx.globalCompositeOperation = 'destination-out'; ctx.strokeStyle = '#000'; }
      else ctx.strokeStyle = css('--text', '#1d2b29');
      for (let i = 1; i < s.pts.length; i++) {
        const a = s.pts[i - 1]; const b = s.pts[i];
        ctx.lineWidth = s.tool === 'eraser' ? 18 : 1.2 + 2.6 * (b.p || 0.5);
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }
      if (s.pts.length === 1 && s.tool !== 'eraser') {
        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath(); ctx.arc(s.pts[0].x, s.pts[0].y, 1.6, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    function pt(e) {
      const r = canvas.getBoundingClientRect();
      // 鼠标没有压感（pressure 恒为 0 或 0.5），按 0.5 算；Pencil / 触控笔按实际压感
      const p = e.pointerType === 'pen' ? (e.pressure || 0.5) : 0.5;
      return { x: e.clientX - r.left, y: e.clientY - r.top, p: p };
    }
    canvas.addEventListener('pointerdown', function (e) {
      if (e.button !== 0 && e.pointerType === 'mouse') return;
      canvas.setPointerCapture(e.pointerId);
      cur = { tool: tool, pts: [pt(e)] };
      strokes.push(cur);
      drawStroke(cur);
      e.preventDefault();
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!cur) return;
      const evs = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
      evs.forEach(function (ev) { cur.pts.push(pt(ev)); });
      redraw();
      e.preventDefault();
    });
    const end = function () { if (cur && cur.tool === 'eraser') redraw(); cur = null; };
    canvas.addEventListener('pointerup', end);
    canvas.addEventListener('pointercancel', end);
    sync();
    const box = h('div', { class: 'ws-sketch' }, bar, wrap, h('p', { class: 'muted small', text: '在这里打草稿，支持 Apple Pencil、手指和鼠标。换下一题会清空。' }));
    box._open = function () { size(); };
    if (window.ResizeObserver) new ResizeObserver(function () { if (box.offsetParent) size(); }).observe(wrap);
    return box;
  }

  /* ------------------------------------------------------------ 数轴 */
  function numberLine() {
    let lo = -10; let hi = 10; let a = 2; let b = 3;
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('class', 'ws-svg');
    svg.setAttribute('viewBox', '0 0 640 120');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', '数轴');
    const num = function (v, fn, step) {
      return h('input', { type: 'number', value: v, step: step || 'any', class: 'ws-num', oninput: function (e) { const x = parseFloat(e.target.value); if (isFinite(x)) { fn(x); draw(); } } });
    };
    const out = h('p', { class: 'ws-out' });
    function el(tag, attrs, text) {
      const n = document.createElementNS(svgNS, tag);
      Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
      if (text != null) n.textContent = text;
      svg.appendChild(n);
      return n;
    }
    function X(v) { return 30 + (v - lo) / (hi - lo) * 580; }
    function draw() {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      const ink = css('--text', '#1d2b29');
      const acc = css('--accent', '#0f6e62');
      el('line', { x1: 20, y1: 80, x2: 625, y2: 80, stroke: ink, 'stroke-width': 1.5 });
      el('path', { d: 'M625 80 l-8 -5 v10 z', fill: ink });
      const span = hi - lo;
      const step = span <= 24 ? 1 : span <= 60 ? 5 : span <= 240 ? 10 : Math.pow(10, Math.floor(Math.log10(span / 10)));
      for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) {
        const x = X(v);
        el('line', { x1: x, y1: 74, x2: x, y2: 86, stroke: ink, 'stroke-width': v === 0 ? 2 : 1 });
        el('text', { x: x, y: 104, 'text-anchor': 'middle', 'font-size': 12, fill: ink }, String(Math.round(v * 1000) / 1000));
      }
      const s = a + b;
      const inRange = function (v) { return v >= lo && v <= hi; };
      if (inRange(a)) el('circle', { cx: X(a), cy: 80, r: 6, fill: acc });
      if (inRange(a) && inRange(s) && b !== 0) {
        const x1 = X(a); const x2 = X(s); const mid = (x1 + x2) / 2;
        el('path', { d: 'M' + x1 + ' 72 Q ' + mid + ' 18 ' + x2 + ' 72', fill: 'none', stroke: acc, 'stroke-width': 2.5 });
        el('path', { d: 'M' + x2 + ' 72 l' + (b > 0 ? -9 : 9) + ' -6 l0 10 z', fill: acc });
        el('text', { x: mid, y: 30, 'text-anchor': 'middle', 'font-size': 13, fill: acc }, (b > 0 ? '+' : '') + b);
      }
      if (inRange(s)) el('circle', { cx: X(s), cy: 80, r: 6, fill: 'none', stroke: acc, 'stroke-width': 2.5 });
      out.textContent = a + (b < 0 ? ' − ' + (-b) : ' + ' + b) + ' = ' + (Math.round(s * 1e6) / 1e6) +
        (inRange(a) && inRange(s) ? '' : '（超出数轴范围，调大范围看看）');
    }
    const box = h('div', { class: 'ws-pane' },
      h('div', { class: 'row ws-controls' },
        h('label', null, '起点 ', num(a, function (x) { a = x; })),
        h('label', null, '跳 ', num(b, function (x) { b = x; })),
        h('label', null, '范围 ', num(lo, function (x) { if (x < hi) lo = x; }), ' 到 ', num(hi, function (x) { if (x > lo) hi = x; }))),
      svg, out,
      h('p', { class: 'muted small', text: '向右跳是加（正数），向左跳是减（负数）。改范围可以看小数或更大的数。' }));
    draw();
    return box;
  }

  /* ------------------------------------------------------------ 百格 / 分数面积板 */
  function areaBoard() {
    const cells = new Array(100).fill(false);
    const gridEl = h('div', { class: 'ws-hundred', role: 'grid', 'aria-label': '百格图' });
    const out = h('p', { class: 'ws-out' });
    let dragging = null;
    function upd() {
      const n = cells.filter(Boolean).length;
      out.textContent = '涂了 ' + n + ' 格 = ' + n + '/100 = ' + (n / 100) + ' = ' + n + '%';
      Array.prototype.forEach.call(gridEl.children, function (c, i) { c.classList.toggle('on', cells[i]); });
    }
    for (let i = 0; i < 100; i++) {
      const c = h('span', { class: 'ws-cell', 'data-i': i });
      c.addEventListener('pointerdown', function (e) { dragging = !cells[i]; cells[i] = dragging; upd(); e.preventDefault(); });
      c.addEventListener('pointerenter', function () { if (dragging != null) { cells[i] = dragging; upd(); } });
      gridEl.appendChild(c);
    }
    gridEl.addEventListener('pointermove', function (e) {
      if (dragging == null || e.pointerType === 'mouse') return;
      const t = document.elementFromPoint(e.clientX, e.clientY);
      if (t && t.classList.contains('ws-cell')) { cells[+t.getAttribute('data-i')] = dragging; upd(); }
    });
    window.addEventListener('pointerup', function () { dragging = null; });

    let num = 3; let den = 4; let num2 = 1; let den2 = 2;
    const bars = h('div', { class: 'ws-frac' });
    const fout = h('p', { class: 'ws-out' });
    function fracBar(n, d) {
      const bar = h('div', { class: 'ws-fbar', 'aria-label': n + '/' + d });
      for (let i = 0; i < d; i++) bar.appendChild(h('span', { class: i < n ? 'on' : '' }));
      return bar;
    }
    function gcd(a, b) { while (b) { const t = a % b; a = b; b = t; } return a; }
    function fdraw() {
      while (bars.firstChild) bars.removeChild(bars.firstChild);
      bars.append(h('div', { class: 'ws-fl' }, h('b', { text: num + '/' + den }), fracBar(num, den)),
        h('div', { class: 'ws-fl' }, h('b', { text: num2 + '/' + den2 }), fracBar(num2, den2)));
      const l = num * den2; const r = num2 * den;
      const sn = l + r; const sd = den * den2; const g = gcd(sn, sd);
      fout.textContent = num + '/' + den + (l > r ? ' > ' : l < r ? ' < ' : ' = ') + num2 + '/' + den2 +
        '；和 = ' + (sn / g) + '/' + (sd / g) + '（通分：' + l + '/' + sd + ' + ' + r + '/' + sd + '）';
    }
    const ni = function (v, fn, max) {
      return h('input', { type: 'number', min: 0, max: max || 24, step: 1, value: v, class: 'ws-num', oninput: function (e) {
        const x = parseInt(e.target.value, 10); if (isFinite(x) && x >= 0 && x <= 24) { fn(x); fdraw(); } } });
    };
    const box = h('div', { class: 'ws-pane' },
      h('div', { class: 'ws-two' },
        h('div', null, h('b', { text: '百格图' }), gridEl, out,
          h('div', { class: 'row' }, h('button', { type: 'button', class: 'small', onclick: function () { cells.fill(false); upd(); } }, '清空'))),
        h('div', null, h('b', { text: '分数面积条' }),
          h('div', { class: 'row ws-controls' },
            ni(num, function (x) { num = Math.min(x, den); }), '/', ni(den, function (x) { if (x >= 1) { den = x; num = Math.min(num, den); } }),
            h('span', { class: 'muted', text: ' 和 ' }),
            ni(num2, function (x) { num2 = Math.min(x, den2); }), '/', ni(den2, function (x) { if (x >= 1) { den2 = x; num2 = Math.min(num2, den2); } })),
          bars, fout)),
      h('p', { class: 'muted small', text: '百格图里拖动涂色，看分数、小数、百分数是同一个量；面积条比较两个分数的大小、看通分。' }));
    upd(); fdraw();
    return box;
  }

  /* ------------------------------------------------------------ 代数天平 */
  function balance() {
    // 左边 a·x + b，右边 c·x + d；对两边做同样的操作
    let st = { a: 2, b: 3, c: 0, d: 11 };
    const hist = [];
    let k = 1;
    const view = h('div', { class: 'ws-balance' });
    const out = h('p', { class: 'ws-out' });
    function side(a, b) {
      const parts = [];
      if (a) parts.push((a === 1 ? '' : a === -1 ? '−' : fmt(a)) + 'x');
      if (b || !a) parts.push((parts.length ? (b < 0 ? ' − ' : ' + ') + fmt(Math.abs(b)) : fmt(b)));
      return parts.join('');
    }
    function fmt(v) { return String(Math.round(v * 1e6) / 1e6).replace('-', '−'); }
    function blocks(a, b) {
      const g = h('div', { class: 'ws-pan-items' });
      const n = Math.min(Math.abs(a), 12);
      for (let i = 0; i < n; i++) g.appendChild(h('span', { class: 'ws-x' + (a < 0 ? ' neg' : ''), text: 'x' }));
      const m = Math.min(Math.abs(Math.round(b)), 20);
      for (let i = 0; i < m; i++) g.appendChild(h('span', { class: 'ws-one' + (b < 0 ? ' neg' : ''), text: '1' }));
      return g;
    }
    function draw() {
      while (view.firstChild) view.removeChild(view.firstChild);
      // 只看式子本身不知道 x，天平保持水平：方程就是“两边一样重”
      view.append(
        h('div', { class: 'ws-pan' }, blocks(st.a, st.b), h('div', { class: 'ws-plate' })),
        h('div', { class: 'ws-pivot', text: '=' }),
        h('div', { class: 'ws-pan' }, blocks(st.c, st.d), h('div', { class: 'ws-plate' })));
      let msg = side(st.a, st.b) + ' = ' + side(st.c, st.d);
      if (st.c !== 0 && st.a !== st.c) msg += '　→ 先让两边同时减去 ' + fmt(st.c) + 'x';
      else if (st.c === 0 && st.a !== 0 && st.b !== 0) msg += '　→ 两边同时减去 ' + fmt(st.b);
      else if (st.c === 0 && st.b === 0 && st.a !== 0) msg += st.a === 1 ? '　✔ 解出来了！x = ' + fmt(st.d) : '　→ 两边同时除以 ' + fmt(st.a);
      out.textContent = msg;
    }
    function op(fn) { hist.push(Object.assign({}, st)); fn(); draw(); }
    const kIn = h('input', { type: 'number', value: k, step: 'any', class: 'ws-num', oninput: function (e) { const x = parseFloat(e.target.value); if (isFinite(x)) k = x; } });
    const setIn = function (key) {
      return h('input', { type: 'number', step: 'any', value: st[key], class: 'ws-num', oninput: function (e) { const x = parseFloat(e.target.value); if (isFinite(x)) { st[key] = x; hist.length = 0; draw(); } } });
    };
    const box = h('div', { class: 'ws-pane' },
      h('div', { class: 'row ws-controls' }, '摆放：', setIn('a'), 'x +', setIn('b'), ' = ', setIn('c'), 'x +', setIn('d')),
      view, out,
      h('div', { class: 'row ws-controls' }, '两边同时 ', kIn, ' ：',
        h('button', { type: 'button', class: 'small', onclick: function () { op(function () { st.b -= k; st.d -= k; }); } }, '减去 k'),
        h('button', { type: 'button', class: 'small', onclick: function () { op(function () { st.b += k; st.d += k; }); } }, '加上 k'),
        h('button', { type: 'button', class: 'small', onclick: function () { op(function () { st.a -= k; st.c -= k; }); } }, '减去 k·x'),
        h('button', { type: 'button', class: 'small', onclick: function () { if (k) op(function () { st.a /= k; st.b /= k; st.c /= k; st.d /= k; }); } }, '除以 k'),
        h('button', { type: 'button', class: 'small', onclick: function () { if (hist.length) { st = hist.pop(); draw(); } } }, '↶ 撤销')),
      h('p', { class: 'muted small', text: '天平两边一样重才平衡。对两边做同样的事，天平一直平衡——这就是解方程。' }));
    draw();
    return box;
  }

  /* ------------------------------------------------------------ 组装 */
  function lab(topic) {
    const tabs = [['line', '数轴'], ['area', '百格 / 分数'], ['balance', '代数天平']];
    const makers = { line: numberLine, area: areaBoard, balance: balance };
    const built = {};
    let cur = defaultTab(topic);
    const body = h('div', { class: 'ws-lab-body' });
    const bar = h('div', { class: 'ws-tabs row', role: 'tablist' });
    function show(id) {
      cur = id;
      Array.prototype.forEach.call(bar.children, function (b) { b.classList.toggle('on', b.getAttribute('data-tab') === id); b.setAttribute('aria-selected', b.getAttribute('data-tab') === id); });
      Object.keys(built).forEach(function (k) { built[k].hidden = k !== id; });
      if (!built[id]) { built[id] = makers[id](); body.appendChild(built[id]); }
    }
    tabs.forEach(function (t) {
      bar.appendChild(h('button', { type: 'button', class: 'small', role: 'tab', 'data-tab': t[0], onclick: function () { show(t[0]); } }, t[1]));
    });
    const box = h('div', { class: 'ws-lab' }, bar, body);
    show(cur);
    return box;
  }

  const STYLE = [
    '.ws-tools{margin-top:14px;display:grid;gap:8px}',
    '.ws-drawer{border:1px solid var(--line,#d6e2df);border-radius:10px;background:var(--card,#fff)}',
    '.ws-drawer>summary{cursor:pointer;padding:8px 12px;font-weight:600;user-select:none}',
    '.ws-drawer[open]>summary{border-bottom:1px solid var(--line,#d6e2df)}',
    '.ws-sketch,.ws-lab{padding:10px 12px}',
    '.ws-toolbar,.ws-tabs,.ws-controls{gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px}',
    '.ws-toolbar button.on,.ws-tabs button.on{background:var(--accent,#0f6e62);color:#fff;border-color:transparent}',
    '.ws-canvas-wrap{width:100%;border:1px dashed var(--line,#c9d8d4);border-radius:8px;overflow:hidden;background:var(--bg,#fff)}',
    '.ws-canvas{display:block;width:100%;touch-action:none}',
    '.ws-svg{width:100%;max-width:640px;height:auto;display:block}',
    '.ws-num{width:4.5em;padding:3px 6px}',
    '.ws-out{font-variant-numeric:tabular-nums;margin:6px 0}',
    '.ws-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}',
    '.ws-hundred{display:grid;grid-template-columns:repeat(10,1fr);gap:2px;max-width:260px;margin:6px 0;touch-action:none}',
    '.ws-cell{aspect-ratio:1;border:1px solid var(--line,#c9d8d4);border-radius:2px;cursor:pointer}',
    '.ws-cell.on{background:var(--accent,#0f6e62);border-color:var(--accent,#0f6e62)}',
    '.ws-fl{display:grid;grid-template-columns:3em 1fr;align-items:center;gap:8px;margin:6px 0}',
    '.ws-fbar{display:flex;height:26px;border:1.5px solid var(--text,#1d2b29);border-radius:4px;overflow:hidden}',
    '.ws-fbar span{flex:1;border-right:1px solid var(--text,#1d2b29)}',
    '.ws-fbar span:last-child{border-right:0}',
    '.ws-fbar span.on{background:rgba(15,110,98,.55)}',
    '.ws-balance{display:grid;grid-template-columns:1fr auto 1fr;align-items:end;gap:10px;margin:8px 0}',
    '.ws-pan{display:flex;flex-direction:column;align-items:stretch}',
    '.ws-pan-items{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;min-height:34px;padding-bottom:4px}',
    '.ws-plate{height:6px;border-radius:3px;background:var(--text,#1d2b29)}',
    '.ws-pivot{font-size:22px;font-weight:700;padding:0 6px}',
    '.ws-x,.ws-one{display:inline-grid;place-items:center;font-size:13px;font-weight:600;border-radius:5px}',
    '.ws-x{width:30px;height:30px;background:#2f7dd1;color:#fff}',
    '.ws-one{width:20px;height:20px;background:#e8a33a;color:#fff;border-radius:50%}',
    '.ws-x.neg,.ws-one.neg{background:transparent;color:inherit;border:2px dashed currentColor}'
  ].join('\n');
  function injectStyle() {
    if (document.getElementById('ws-tools-style')) return;
    const st = document.createElement('style');
    st.id = 'ws-tools-style';
    st.textContent = STYLE;
    document.head.appendChild(st);
  }

  function mount(container, topic) {
    injectStyle();
    const pad = sketchpad();
    const labBox = lab(topic);
    const d1 = h('details', { class: 'ws-drawer', 'data-drawer': 'sketch' }, h('summary', null, '✏️ 草稿本'), pad);
    const d2 = h('details', { class: 'ws-drawer', 'data-drawer': 'lab' }, h('summary', null, '🧮 CPA 实验台'), labBox);
    d1.addEventListener('toggle', function () { if (d1.open) pad._open(); });
    const rootEl = h('div', { class: 'ws-tools no-print' }, d1, d2);
    if (container) container.appendChild(rootEl);
    return rootEl;
  }

  return { mount: mount, defaultTab: defaultTab };
});
