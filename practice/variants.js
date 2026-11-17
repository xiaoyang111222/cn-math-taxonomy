/* 变式题生成：纯函数、无 DOM、无依赖。浏览器中暴露为 window.CnmVariants，Node 中 require() 即可。
 *
 *   generateVariant(question, topicId, seed, templates?) -> 新题 | null
 *     1) templates（data/question-templates.json 的内容，可选）里有这个知识点的模板 -> 按模板出一道新题；
 *     2) 否则对 numeric 题做“参数扰动”：题干和 verify 里同时出现的数一起换成附近的数，用有理数求值器重算答案；
 *        保持原数之间的大小关系、原答案的整数性与正负，算不出来或不像样就返回 null（调用方改用原题）。
 *   模板 kind：arith（整数四则）、decimal（小数加减乘）、fraction（分数加减乘除）、
 *             linear（一元一次方程）、quadratic（一元二次方程，两整数根）、polygon-area（长方形/平行四边形/三角形/梯形面积）。
 *   同一 (question.id, topicId, seed) 永远得到同一道题（mulberry32）。
 *   evaluate(expr) -> {n, d}（BigInt 分数）| null：只认 + - * / ** ^ ( ) 小数 和 Fraction(a, b)。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.CnmVariants = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* ------------------------------------------------------------ 随机 */
  function hashStr(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function rng(seed) { const f = mulberry32(hashStr(String(seed))); f(); return f; }
  function randInt(r, lo, hi) { return lo + Math.floor(r() * (hi - lo + 1)); }

  /* ------------------------------------------------------------ 有理数 */
  function babs(x) { return x < 0n ? -x : x; }
  function gcd(a, b) { a = babs(a); b = babs(b); while (b) { const t = a % b; a = b; b = t; } return a; }
  function Q(n, d) {
    n = BigInt(n); d = d == null ? 1n : BigInt(d);
    if (d === 0n) return null;
    if (d < 0n) { n = -n; d = -d; }
    const g = gcd(n, d) || 1n;
    return { n: n / g, d: d / g };
  }
  function fromDecimal(s) {
    const m = /^(\d+)(?:\.(\d+))?$/.exec(s);
    if (!m) return null;
    const frac = m[2] || '';
    return Q(BigInt(m[1] + frac), 10n ** BigInt(frac.length));
  }
  const add = function (a, b) { return Q(a.n * b.d + b.n * a.d, a.d * b.d); };
  const sub = function (a, b) { return Q(a.n * b.d - b.n * a.d, a.d * b.d); };
  const mul = function (a, b) { return Q(a.n * b.n, a.d * b.d); };
  const div = function (a, b) { return b.n === 0n ? null : Q(a.n * b.d, a.d * b.n); };
  function pow(a, b) {
    if (b.d !== 1n || babs(b.n) > 64n) return null;
    let e = b.n; let base = a;
    if (e < 0n) { base = div(Q(1), a); if (!base) return null; e = -e; }
    let out = Q(1);
    for (let i = 0n; i < e; i++) out = mul(out, base);
    return out;
  }
  function toNumber(q) { return Number(q.n) / Number(q.d); }

  /** 有理数求值：只支持 + - * / ** ^ 括号、整数 / 小数、Fraction(a, b)。其它（sqrt、变量……）返回 null。 */
  function evaluate(expr) {
    const src = String(expr).replace(/\s+/g, '');
    let i = 0;
    const peek = function () { return src[i]; };
    function primary() {
      if (src.startsWith('Fraction(', i)) {
        i += 9;
        const a = sum(); if (!a) return null;
        let b = Q(1);
        if (peek() === ',') { i++; b = sum(); if (!b) return null; }
        if (peek() !== ')') return null;
        i++;
        return div(a, b);
      }
      if (peek() === '(') {
        i++;
        const v = sum();
        if (!v || peek() !== ')') return null;
        i++;
        return v;
      }
      const m = /^\d+(?:\.\d+)?/.exec(src.slice(i));
      if (!m) return null;
      i += m[0].length;
      return fromDecimal(m[0]);
    }
    function unary() {
      if (peek() === '-') { i++; const v = unary(); return v && Q(-v.n, v.d); }
      if (peek() === '+') { i++; return unary(); }
      return power();
    }
    function power() {
      const base = primary();
      if (!base) return null;
      if (src.startsWith('**', i) || peek() === '^') {
        i += peek() === '^' ? 1 : 2;
        const e = unary();
        return e && pow(base, e);
      }
      return base;
    }
    function product() {
      let v = unary();
      while (v && (peek() === '*' || peek() === '/') && !src.startsWith('**', i)) {
        const op = src[i++];
        const r = unary();
        if (!r) return null;
        v = op === '*' ? mul(v, r) : div(v, r);
      }
      return v;
    }
    function sum() {
      let v = product();
      while (v && (peek() === '+' || peek() === '-')) {
        const op = src[i++];
        const r = product();
        if (!r) return null;
        v = op === '+' ? add(v, r) : sub(v, r);
      }
      return v;
    }
    const v = sum();
    return v && i === src.length ? v : null;
  }

  /** 有理数 -> 答案文本：整数；有限小数（最多 4 位）；否则最简分数 p/q。 */
  function formatQ(q, preferFraction) {
    if (q.d === 1n) return String(q.n);
    if (!preferFraction) {
      let d = q.d; let k = 0;
      while (d % 2n === 0n) { d /= 2n; k++; }
      while (d % 5n === 0n) { d /= 5n; k++; }
      if (d === 1n && k <= 4) {
        const scale = 10n ** BigInt(Math.max(k, 1));
        const v = q.n * scale / q.d;
        const neg = v < 0n;
        let s = String(babs(v)).padStart(Math.max(k, 1) + 1, '0');
        s = s.slice(0, s.length - Math.max(k, 1)) + '.' + s.slice(s.length - Math.max(k, 1));
        s = s.replace(/\.?0+$/, '');
        return (neg ? '-' : '') + s;
      }
    }
    return String(q.n) + '/' + String(q.d);
  }

  /* ------------------------------------------------------------ 参数扰动 */
  const NUM_RE = /\d+(?:\.\d+)?/g;
  function decimals(s) { const k = s.indexOf('.'); return k < 0 ? 0 : s.length - k - 1; }

  function numbersIn(text) {
    const out = [];
    let m;
    NUM_RE.lastIndex = 0;
    while ((m = NUM_RE.exec(text))) out.push({ s: m[0], at: m.index });
    return out;
  }

  /** verify 里作为指数的数（** 或 ^ 后面的）不扰动。 */
  function exponentValues(verify) {
    const out = new Set();
    const re = /(?:\*\*|\^)\(?(\d+(?:\.\d+)?)/g;
    let m;
    while ((m = re.exec(verify))) out.add(m[1]);
    return out;
  }

  function perturbOne(r, s) {
    const k = decimals(s);
    const scale = Math.pow(10, k);
    const v = Math.round(parseFloat(s) * scale);
    const lo = Math.max(2, Math.round(v * 0.5));
    let hi = Math.max(lo + 2, Math.round(v * 1.5));
    // 守住“10 以内”“20 以内”“100 以内”这类范围
    const cap = [10, 20, 100].find(function (c) { return v <= c * scale; });
    if (cap) hi = Math.min(hi, k ? cap * scale - 1 : (cap === 100 ? 99 : cap));
    if (hi <= lo) return s;
    let nv = randInt(r, lo, hi);
    if (nv === v) nv = nv + 1;
    if (k && nv % 10 === 0) nv += 1; // 小数保持位数
    return k ? (nv / scale).toFixed(k) : String(nv);
  }

  function replaceAll(text, map) {
    return text.replace(NUM_RE, function (m) { return Object.prototype.hasOwnProperty.call(map, m) ? map[m] : m; });
  }

  function perturb(question, seed) {
    if (!question || question.type !== 'numeric' || !question.verify || question.unordered) return null;
    if (/[，,]/.test(question.answer)) return null;
    const orig = evaluate(question.verify);
    if (!orig) return null;
    const exps = exponentValues(question.verify);
    const inPrompt = new Set(numbersIn(question.prompt).map(function (x) { return x.s; }));
    const cand = Array.from(new Set(numbersIn(question.verify).map(function (x) { return x.s; })))
      .filter(function (s) { return inPrompt.has(s) && !exps.has(s) && parseFloat(s) >= 2; });
    if (!cand.length) return null;
    const origAns = String(question.answer);
    const wantFraction = /\//.test(origAns);
    const wantInt = /^-?\d+$/.test(origAns);
    const origSign = orig.n < 0n ? -1 : orig.n > 0n ? 1 : 0;
    const order = cand.slice().sort(function (a, b) { return parseFloat(a) - parseFloat(b); });
    for (let tries = 0; tries < 40; tries++) {
      const r = rng(seed + '|' + question.id + '|' + tries);
      const map = {};
      cand.forEach(function (s) { map[s] = perturbOne(r, s); });
      // 原来 a < b 的，换完还要 a < b（减法不出负数、真分数仍是真分数）；也不能撞成同一个数
      const vals = order.map(function (s) { return parseFloat(map[s]); });
      let ok = true;
      for (let j = 1; j < vals.length; j++) if (!(vals[j] > vals[j - 1])) ok = false;
      if (!ok) continue;
      const verify = replaceAll(question.verify, map);
      const v = evaluate(verify);
      if (!v) continue;
      const sign = v.n < 0n ? -1 : v.n > 0n ? 1 : 0;
      if (sign !== origSign) continue;
      if (wantInt && v.d !== 1n) continue;
      if (!wantInt && !wantFraction && formatQ(v).indexOf('/') >= 0) continue; // 原来是小数，换完也要能写成有限小数
      if (Math.abs(toNumber(v)) > 1e7) continue;
      const answer = formatQ(v, wantFraction);
      if (answer === origAns) continue;
      return {
        id: question.id + '_v' + hashStr(seed + '|' + tries).toString(36),
        topicId: question.topicId, difficulty: question.difficulty, type: 'numeric',
        prompt: replaceAll(question.prompt, map), answer: answer,
        explanation: '这是由原题换了数字的变式题，做法与原题相同。原题解析：' + (question.explanation || ''),
        verify: verify, variantOf: question.id, hints: question.hints
      };
    }
    return null;
  }

  /* ------------------------------------------------------------ 模板 */
  const OPS = { '+': '＋', '-': '－', '*': '×', '/': '÷' };

  function range(t, key, lo, hi) { const x = t[key]; return Array.isArray(x) && x.length === 2 ? x : [lo, hi]; }

  const KINDS = {
    arith: function (r, t) {
      const op = t.op || '+';
      const rg = range(t, 'range', 2, 99);
      let a = randInt(r, rg[0], rg[1]); let b = randInt(r, rg[0], rg[1]);
      if (op === '-' && b > a) { const x = a; a = b; b = x; }
      if (op === '/') { const q = randInt(r, rg[0], Math.max(rg[0], Math.min(rg[1], 12))); a = b * q; }
      const v = evaluate(a + op + b);
      return { prompt: '计算：' + a + ' ' + OPS[op] + ' ' + b + ' ＝？', verify: a + op + b, answer: formatQ(v) };
    },
    decimal: function (r, t) {
      const op = t.op || '+';
      const k = t.places || 1;
      const rg = range(t, 'range', 1, 99);
      const mk = function () {
        let n = randInt(r, rg[0] * Math.pow(10, k), rg[1] * Math.pow(10, k));
        if (n % 10 === 0) n += 1; // 不出 66.0 这种末位是 0 的小数
        return (n / Math.pow(10, k)).toFixed(k);
      };
      let a = mk(); let b = mk();
      if (op === '-' && parseFloat(b) > parseFloat(a)) { const x = a; a = b; b = x; }
      if (op === '*') b = String(randInt(r, 2, 9));
      const v = evaluate(a + op + b);
      return { prompt: '计算：' + a + ' ' + OPS[op] + ' ' + b + ' ＝？（用小数作答）', verify: a + op + b, answer: formatQ(v) };
    },
    fraction: function (r, t) {
      const op = t.op || '+';
      const maxD = t.maxDen || 12;
      const sameDen = !!t.sameDen;
      const d1 = randInt(r, 2, maxD); const d2 = sameDen ? d1 : randInt(r, 2, maxD);
      let n1 = randInt(r, 1, d1 - 1); let n2 = randInt(r, 1, d2 - 1);
      if (op === '-' && n1 * d2 < n2 * d1) { const x = n1; n1 = n2; n2 = x; }
      if (op === '-' && n1 * d2 === n2 * d1) return null;
      const verify = 'Fraction(' + n1 + ',' + d1 + ')' + op + 'Fraction(' + n2 + ',' + (sameDen ? d1 : d2) + ')';
      const v = evaluate(verify);
      if (!v || v.n < 0n) return null;
      return { prompt: '计算：' + n1 + '/' + d1 + ' ' + OPS[op] + ' ' + n2 + '/' + (sameDen ? d1 : d2) + ' ＝？（结果写成最简分数或整数）', verify: verify, answer: formatQ(v, true) };
    },
    linear: function (r, t) {
      const x = randInt(r, -9, 9) || 3;
      const a = randInt(r, 2, 9) * (r() < 0.25 ? -1 : 1);
      const b = randInt(r, -20, 20);
      const c = a * x + b;
      const bs = b === 0 ? '' : (b > 0 ? ' + ' + b : ' − ' + (-b));
      return { prompt: '解方程：' + (a === 1 ? '' : a === -1 ? '−' : String(a).replace('-', '−')) + 'x' + bs + ' = ' + String(c).replace('-', '−') + '，x ＝？',
        verify: '(' + c + '-(' + b + '))/(' + a + ')', answer: String(x) };
    },
    quadratic: function (r) {
      let p = randInt(r, -9, 9); let q = randInt(r, -9, 9);
      if (p === q) q = p + 2;
      if (p > q) { const x = p; p = q; q = x; }
      const b = -(p + q); const c = p * q;
      const term = function (k, s) { return k === 0 ? '' : (k > 0 ? ' + ' : ' − ') + (Math.abs(k) === 1 && s ? '' : Math.abs(k)) + s; };
      return { prompt: '解方程：x²' + term(b, 'x') + term(c, '') + ' = 0。（两个根从小到大写，用逗号隔开）',
        verify: '[' + p + ', ' + q + ']', answer: p + '，' + q, unordered: true };
    },
    'polygon-area': function (r, t) {
      const shapes = Array.isArray(t.shapes) && t.shapes.length ? t.shapes : ['rect', 'para', 'tri', 'trap'];
      const shape = shapes[Math.floor(r() * shapes.length)];
      const unit = t.unit || '厘米';
      const a = randInt(r, 3, 20); const b = randInt(r, 3, 20); const hgt = randInt(r, 2, 16);
      if (shape === 'rect') return { prompt: '一个长方形长 ' + a + ' ' + unit + '、宽 ' + b + ' ' + unit + '，面积是多少平方' + unit + '？', verify: a + '*' + b, answer: String(a * b) };
      if (shape === 'para') return { prompt: '一个平行四边形底 ' + a + ' ' + unit + '、高 ' + hgt + ' ' + unit + '，面积是多少平方' + unit + '？', verify: a + '*' + hgt, answer: String(a * hgt) };
      if (shape === 'tri') {
        const v = evaluate(a + '*' + hgt + '/2');
        return { prompt: '一个三角形底 ' + a + ' ' + unit + '、高 ' + hgt + ' ' + unit + '，面积是多少平方' + unit + '？', verify: a + '*' + hgt + '/2', answer: formatQ(v) };
      }
      const lo = Math.min(a, b); const hi = Math.max(a, b) + (a === b ? 2 : 0);
      const v = evaluate('(' + lo + '+' + hi + ')*' + hgt + '/2');
      return { prompt: '一个梯形上底 ' + lo + ' ' + unit + '、下底 ' + hi + ' ' + unit + '、高 ' + hgt + ' ' + unit + '，面积是多少平方' + unit + '？', verify: '(' + lo + '+' + hi + ')*' + hgt + '/2', answer: formatQ(v) };
    }
  };

  function templatesFor(templates, topicId) {
    const list = templates && Array.isArray(templates.templates) ? templates.templates : [];
    return list.filter(function (t) { return t && t.topicId === topicId && KINDS[t.kind]; });
  }

  function fromTemplate(question, topicId, seed, templates) {
    const ts = templatesFor(templates, topicId);
    if (!ts.length) return null;
    const qid = question && question.id ? question.id : topicId;
    for (let tries = 0; tries < 10; tries++) {
      const r = rng(seed + '|' + qid + '|tpl|' + tries);
      const t = ts[Math.floor(r() * ts.length)];
      const made = KINDS[t.kind](r, t);
      if (!made) continue;
      return Object.assign({
        id: topicId + '_t' + hashStr(seed + '|' + qid + '|' + tries).toString(36),
        topicId: topicId, difficulty: t.difficulty || (question && question.difficulty) || 'basic', type: 'numeric',
        explanation: t.explanation || '按同类题的方法计算即可。', variantOf: question ? question.id : null, template: t.kind
      }, made);
    }
    return null;
  }

  function generateVariant(question, topicId, seed, templates) {
    const tid = topicId || (question && question.topicId);
    const s = seed == null ? 'v' : String(seed);
    return fromTemplate(question, tid, s, templates) || perturb(question, s);
  }

  return {
    generateVariant: generateVariant,
    evaluate: evaluate,
    formatQ: formatQ,
    perturb: perturb,
    fromTemplate: fromTemplate,
    KINDS: Object.keys(KINDS),
    mulberry32: mulberry32
  };
});
