/* 诊断引擎：纯函数、无 DOM、无依赖。浏览器中暴露为 window.DiagEngine，Node 中 require() 即可。
 *
 * 数据流：buildGraph(topics, deps, questions?) -> graph      （questions 缺失时用 topics 的 diagnostic_question）
 *         createSession(graph, targets, {limit, seed, avoid}) -> session   （会话是可 JSON 序列化的纯数据）
 *         nextQuestion(graph, session) -> topicId | null     （下一个要考的知识点）
 *         nextItem(graph, session) -> {topicId, question, attempt} | null   （要出的具体题目；attempt 从 1 起）
 *         applyAnswer(graph, session, id, 'correct'|'wrong'|'skip', {text}) -> 新 session（不修改入参）
 *         summarize(graph, session) -> 结果（根因、学习路径、掌握/不稳/薄弱/未测）
 *         gradeTargets(graph, '一年级'|'七上'|'高一'|'选必二', subject?) -> {ids, volumes, label} | null
 *           默认 subject 为 math，不把英语卷进数学的整册；'english' 只取英语（含九全），'physics' 只取物理（八上、八下、九全），'all' 不限学科
 *         createSession(graph, ids, {mode:'screen', confirm}) -> 筛查会话：范围 = 目标本身，回溯不出范围，默认题量上限 SCREEN_LIMIT
 *         chapterSummary(graph, session) -> 按章汇总（薄弱章节在前）
 *         layout(graph, session, summary) -> 路径图的分层布局
 *         judgeQuestion(question, userText) -> {verdict:'correct'|'wrong'|'manual', reason}
 *         judgeAnswer(user, reference) -> 同上（只按参考答案文本判，旧接口）
 *
 * 每个知识点需连续答对 confirm 题才判掌握（默认 3，可选 2/3/5；题库更少时以题库为准）：
 *   连续答对满额 -> 掌握（并推断祖先掌握）；中途错 / 不会 -> 再出一道更基础的题确认：
 *   确认题对 -> 不稳（shaky，不向先修回溯）；确认题也错 -> 薄弱（weak，向先修回溯，hard 先于 soft）。
 *   选题：第一题优先 standard（提高）；连续答对再出 challenge（拓展）确认掌握；答错先补 basic。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.DiagEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* ------------------------------------------------------------------ 图 */

  const DIFF_RANK = { basic: 0, standard: 1, challenge: 2, advanced: 2 };

  function qNum(q) { const m = /_q(\d+)$/.exec(q.id); return m ? parseInt(m[1], 10) : 0; }

  function buildGraph(topics, deps, questions) {
    const byId = Object.create(null);
    const index = Object.create(null);
    topics.forEach(function (t, i) { byId[t.id] = t; index[t.id] = i; });
    const prereqs = Object.create(null);
    const dependents = Object.create(null);
    topics.forEach(function (t) { prereqs[t.id] = []; dependents[t.id] = []; });
    const seen = Object.create(null);
    deps.forEach(function (d) {
      if (!byId[d.topicId] || !byId[d.prerequisiteId]) return;
      const k = d.topicId + '<' + d.prerequisiteId;
      if (seen[k]) return;
      seen[k] = true;
      const strength = d.strength === 'soft' ? 'soft' : 'hard';
      prereqs[d.topicId].push({ id: d.prerequisiteId, strength: strength, reason: d.reason });
      dependents[d.prerequisiteId].push({ id: d.topicId, strength: strength });
    });
    // 先修按 hard 优先、再 soft，同级按 topics 文件顺序，保证出题次序确定
    const rank = function (e) { return (e.strength === 'hard' ? 0 : 1) * 1e6 + index[e.id]; };
    Object.keys(prereqs).forEach(function (id) {
      prereqs[id].sort(function (a, b) { return rank(a) - rank(b); });
      dependents[id].sort(function (a, b) { return index[a.id] - index[b.id]; });
    });
    // 题库：每个知识点的题目，按题号排序；没有题库（或某知识点没有题）时回退到 diagnostic_question
    const bank = Object.create(null);
    topics.forEach(function (t) { bank[t.id] = []; });
    let fromFile = 0;
    (Array.isArray(questions) ? questions : []).forEach(function (q) {
      if (q && bank[q.topicId] && !byId[q.topicId].external) { bank[q.topicId].push(q); fromFile++; }
    });
    topics.forEach(function (t) {
      const dq = t.diagnostic_question;
      if (!t.external && !bank[t.id].length && dq && dq.question) {
        bank[t.id].push({ id: t.id + '_q1', topicId: t.id, difficulty: 'standard', type: 'legacy', prompt: dq.question, answer: dq.answer, explanation: '' });
      }
    });
    Object.keys(bank).forEach(function (id) { bank[id].sort(function (a, b) { return qNum(a) - qNum(b); }); });
    return {
      topics: topics, byId: byId, index: index, prereqs: prereqs, dependents: dependents, bank: bank,
      hasBank: fromFile > 0, _anc: Object.create(null)
    };
  }

  /** 严格祖先集合（不含自身），带缓存。 */
  function ancestorSet(graph, id) {
    const memo = graph._anc;
    if (memo[id]) return memo[id];
    const visiting = graph._visiting || (graph._visiting = Object.create(null));
    if (visiting[id]) throw new Error('先修图存在环：' + id);
    visiting[id] = true;
    const out = new Set();
    graph.prereqs[id].forEach(function (p) {
      out.add(p.id);
      ancestorSet(graph, p.id).forEach(function (a) { out.add(a); });
    });
    visiting[id] = false;
    memo[id] = out;
    return out;
  }

  function ancestors(graph, ids) {
    const list = Array.isArray(ids) ? ids : [ids];
    const out = new Set();
    list.forEach(function (id) { ancestorSet(graph, id).forEach(function (a) { out.add(a); }); });
    return out;
  }

  /** 对节点子集做拓扑排序（先修在前）；同层按 topics 文件顺序，确定性。 */
  function topoSort(graph, ids) {
    const set = new Set(ids);
    const indeg = Object.create(null);
    set.forEach(function (id) {
      indeg[id] = graph.prereqs[id].filter(function (p) { return set.has(p.id); }).length;
    });
    const ready = [];
    set.forEach(function (id) { if (indeg[id] === 0) ready.push(id); });
    const byIndex = function (a, b) { return graph.index[a] - graph.index[b]; };
    const order = [];
    while (ready.length) {
      ready.sort(byIndex);
      const id = ready.shift();
      order.push(id);
      graph.dependents[id].forEach(function (d) {
        if (!set.has(d.id)) return;
        indeg[d.id] -= 1;
        if (indeg[d.id] === 0) ready.push(d.id);
      });
    }
    if (order.length !== set.size) throw new Error('拓扑排序失败：子图存在环');
    return order;
  }

  /** 目标集合的先修子图：目标 + 所有祖先（含小学外部节点），拓扑序。 */
  function subgraph(graph, targets) {
    const set = new Set(targets);
    ancestors(graph, targets).forEach(function (a) { set.add(a); });
    return { nodes: topoSort(graph, set), set: set };
  }

  function isTestable(graph, id) {
    const t = graph.byId[id];
    return !!(t && !t.external && graph.bank[id] && graph.bank[id].length);
  }

  function questionById(graph, qid) {
    const m = /^(.*)_q\d+$/.exec(qid || '');
    const list = m ? graph.bank[m[1]] : null;
    return (list || []).find(function (q) { return q.id === qid; }) || null;
  }

  /* ------------------------------------------------------------------ 会话 */

  const RESULTS = { correct: 1, wrong: 1, skip: 1 };
  const DEFAULT_LIMIT = 16;
  const SCREEN_LIMIT = 40;
  const DEFAULT_CONFIRM = 3;
  const CONFIRM_CHOICES = [2, 3, 5];

  /** 界面可选值：只接受 2 / 3 / 5，其它回退默认。 */
  function clampConfirm(n) {
    const v = Math.floor(Number(n));
    return CONFIRM_CHOICES.indexOf(v) >= 0 ? v : DEFAULT_CONFIRM;
  }

  /** 引擎内部：任意 ≥1 的确认题数（测试可用 1；界面仍走 clampConfirm）。 */
  function normalizeConfirm(n) {
    const v = Math.floor(Number(n));
    return v >= 1 && v <= 10 ? v : DEFAULT_CONFIRM;
  }

  /** 该知识点判「掌握」所需的连续答对题数：取 confirm 与题库题数的较小值（至少 1）。 */
  function needConfirm(graph, session, id) {
    const bankLen = (graph.bank[id] || []).length;
    const conf = session && session.confirm != null ? session.confirm : DEFAULT_CONFIRM;
    return Math.max(1, Math.min(conf, bankLen || 1));
  }

  function createSession(graph, targets, opts) {
    opts = opts || {};
    const ts = Array.from(new Set(targets));
    if (!ts.length) throw new Error('至少需要一个目标知识点');
    ts.forEach(function (id) { if (!graph.byId[id]) throw new Error('未知知识点：' + id); });
    const screen = opts.mode === 'screen';
    const limit = Math.max(1, Math.floor(opts.limit == null ? (screen ? SCREEN_LIMIT : DEFAULT_LIMIT) : opts.limit));
    const confirm = normalizeConfirm(opts.confirm == null ? DEFAULT_CONFIRM : opts.confirm);
    // 筛查模式：诊断范围就是目标集合本身（不把先修祖先并进来），回溯只在范围内进行
    const sub = screen ? { nodes: topoSort(graph, ts) } : subgraph(graph, ts);
    const pos = Object.create(null);
    sub.nodes.forEach(function (id, i) { pos[id] = i; });
    // 离目标最近（拓扑序最靠后）的目标先问；其余目标作为后备留在栈里
    const stack = ts.filter(function (id) { return isTestable(graph, id); })
      .sort(function (a, b) { return pos[b] - pos[a]; });
    return {
      targets: ts, limit: limit, confirm: confirm, order: sub.nodes, status: {}, stack: stack, answers: [], attempts: {},
      mode: screen ? 'screen' : 'target', scope: screen ? ts.slice() : null,
      seed: opts.seed == null ? 'default' : String(opts.seed),
      avoid: Array.from(new Set(opts.avoid || []))
    };
  }

  function cloneSession(s) {
    const attempts = {};
    Object.keys(s.attempts).forEach(function (k) { attempts[k] = s.attempts[k].slice(); });
    return {
      targets: s.targets.slice(), limit: s.limit, confirm: s.confirm, order: s.order, stack: s.stack.slice(),
      status: Object.assign({}, s.status), answers: s.answers.slice(), attempts: attempts,
      seed: s.seed, avoid: s.avoid, mode: s.mode, scope: s.scope ? s.scope.slice() : null
    };
  }

  /* ---- 可种子化的伪随机：同一 (seed, 知识点, 第几题) 永远得到同一个数，所以会话可以重放 ---- */
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

  function rand01(seed, key) {
    const f = mulberry32(hashStr(String(seed) + '|' + key));
    f();
    return f();
  }

  const rankOf = function (q) { return DIFF_RANK[q.difficulty] == null ? 1 : DIFF_RANK[q.difficulty]; };

  /**
   * 给知识点 id 选第 attempt 题。
   *  - 已在本次会话里出过的题不再出；
   *  - 第一题：优先 standard（提高），没有再退到 basic，尽量不出拓展；
   *  - 连续答对、尚未错过：优先 challenge（拓展）确认掌握，再 standard，再 basic；
   *  - 错过之后的确认题：同级或更容易——优先 basic，其次与第一题同难度，再其次其它更容易的，最后才是更难的（取最容易的）；
   *    难度优先于“没出过”，同档里仍优先没出过（session.avoid 之外）的；
   *  - 档内用 seed 决定的伪随机数选一道。
   */
  function pickQuestion(graph, session, id, attempt) {
    const all = graph.bank[id] || [];
    const tried = (session.attempts[id] || []).map(function (a) { return a.qid; });
    const pool = all.filter(function (q) { return tried.indexOf(q.id) < 0; });
    if (!pool.length) return null;
    const avoid = new Set(session.avoid || []);
    const freshFirst = function (list) {
      const f = list.filter(function (q) { return !avoid.has(q.id); });
      return f.length ? f : list;
    };
    const pickRank = function (list, ranks) {
      for (let i = 0; i < ranks.length; i++) {
        const hit = list.filter(function (q) { return rankOf(q) === ranks[i]; });
        if (hit.length) return freshFirst(hit);
      }
      return freshFirst(list);
    };
    const prev = session.attempts[id] || [];
    const hadFail = prev.some(function (a) { return a.result !== 'correct'; });
    let cand;
    if (attempt <= 1 || !hadFail) {
      const base = freshFirst(pool);
      if (attempt <= 1) cand = pickRank(base, [1, 0]);
      else cand = pickRank(base, [2, 1, 0]);
    } else {
      const first = all.find(function (q) { return q.id === tried[0]; });
      const r0 = first ? rankOf(first) : 1;
      const tiers = [
        pool.filter(function (q) { return rankOf(q) === 0; }),
        pool.filter(function (q) { return rankOf(q) === r0; }),
        pool.filter(function (q) { return rankOf(q) < r0; })
      ];
      const hit = tiers.find(function (t) { return t.length; });
      if (hit) cand = freshFirst(hit);
      else {
        const lo = Math.min.apply(null, pool.map(rankOf));
        cand = freshFirst(pool.filter(function (q) { return rankOf(q) === lo; }));
      }
    }
    const idx = Math.min(cand.length - 1, Math.floor(rand01(session.seed, id + '|' + attempt) * cand.length));
    return cand[idx];
  }

  /**
   * 记录一次作答（针对 nextItem 给出的那道题）。
   *  - 连续答对满 needConfirm 题：该点及其所有尚未判定的祖先记为掌握（祖先为 inferred）；
   *  - 连续答对尚未满额：还没有结论，继续出同知识点下一题；
   *  - 中途 wrong/skip：还没有结论，再出一道确认题（没有可出的就直接判薄弱）；
   *  - 确认题 correct：不稳（shaky），不向先修回溯；
   *  - 确认题 wrong/skip：薄弱，并把其先修（hard 先、soft 后）压到出题栈顶。
   * 直接作答（direct）的判定不会被推断（inferred）覆盖。extra.text 是用户输入的答案（只用于记录）。
   */
  function applyAnswer(graph, session, id, result, extra) {
    if (!RESULTS[result]) throw new Error('作答结果必须是 correct / wrong / skip');
    if (!graph.byId[id]) throw new Error('未知知识点：' + id);
    const s = cloneSession(session);
    if (s.status[id]) { delete s.status[id]; s.attempts[id] = []; } // 对已有结论的点重新作答 = 重新开始
    const prev = s.attempts[id] || [];
    const q = pickQuestion(graph, s, id, prev.length + 1);
    const rec = { id: id, qid: q ? q.id : null, result: result };
    if (extra && extra.text != null && extra.text !== '') rec.text = String(extra.text);
    s.answers.push(rec);
    s.attempts[id] = prev.concat([{ qid: rec.qid, result: result }]);
    const attempts = s.attempts[id];
    const fails = attempts.filter(function (a) { return a.result !== 'correct'; }).length;
    const corrects = attempts.filter(function (a) { return a.result === 'correct'; }).length;
    const need = needConfirm(graph, s, id);
    if (result === 'correct') {
      if (fails === 0 && corrects >= need) {
        s.status[id] = { s: 'mastered', src: 'direct' };
        ancestorSet(graph, id).forEach(function (a) {
          if (!s.status[a]) s.status[a] = { s: 'mastered', src: 'inferred' };
        });
      } else if (fails > 0) {
        s.status[id] = { s: 'shaky', src: 'direct' };
      }
      // 否则：连续答对尚未满额，继续出题
    } else if (fails === 1 && pickQuestion(graph, s, id, attempts.length + 1)) {
      // 第一次没过：等确认题再下结论
    } else {
      s.status[id] = { s: 'weak', src: 'direct' };
      const scope = s.scope ? new Set(s.scope) : null;
      const push = graph.prereqs[id]
        .map(function (p) { return p.id; })
        .filter(function (p) { return isTestable(graph, p) && !s.status[p] && (!scope || scope.has(p)); });
      const pushed = new Set(push);
      s.stack = push.concat(s.stack.filter(function (x) { return !pushed.has(x); }));
    }
    return s;
  }

  function nextQuestion(graph, session) {
    if (session.answers.length >= session.limit) return null;
    for (let i = 0; i < session.stack.length; i++) {
      const id = session.stack[i];
      if (!session.status[id] && isTestable(graph, id)) return id;
    }
    return null;
  }

  function nextItem(graph, session) {
    const id = nextQuestion(graph, session);
    if (!id) return null;
    const attempt = (session.attempts[id] || []).length + 1;
    const q = pickQuestion(graph, session, id, attempt);
    return q ? { topicId: id, question: q, attempt: attempt } : null;
  }

  /** 由作答记录重建会话（用于刷新恢复、撤销、更正）。 */
  function replay(graph, targets, answers, opts) {
    let s = createSession(graph, targets, opts);
    answers.forEach(function (a) { s = applyAnswer(graph, s, a.id, a.result, { text: a.text }); });
    return s;
  }

  /** 状态：mastered / shaky / weak / unknown。只答错一题就遇到题量上限的点按 weak 算（见 isUnconfirmed）。 */
  function statusOf(session, id) {
    const st = session.status[id];
    if (st) return st.s;
    return isUnconfirmed(session, id) ? 'weak' : 'unknown';
  }

  /** 答过错、但没来得及出确认题（题量用完）的点。 */
  function isUnconfirmed(session, id) {
    const a = session.attempts[id];
    if (session.status[id] || !a || !a.length) return false;
    return a.some(function (x) { return x.result !== 'correct'; });
  }

  /* ------------------------------------------------------------------ 结果 */

  function summarize(graph, session) {
    const nodes = session.order;
    const st = function (id) { return statusOf(session, id); };
    const mastered = nodes.filter(function (id) { return st(id) === 'mastered'; });
    const shaky = nodes.filter(function (id) { return st(id) === 'shaky'; });
    const weak = nodes.filter(function (id) { return st(id) === 'weak'; });
    const unconfirmed = weak.filter(function (id) { return isUnconfirmed(session, id); });
    const untested = nodes.filter(function (id) { return st(id) === 'unknown'; });
    const scope = session.scope ? new Set(session.scope) : null;
    const inScope = function (id) { return !scope || scope.has(id); };

    const roots = weak.filter(function (id) {
      return !graph.prereqs[id].some(function (p) { return st(p.id) === 'weak'; });
    }).map(function (id) {
      const unk = graph.prereqs[id].filter(function (p) { return st(p.id) === 'unknown'; });
      const testableUnk = unk.filter(function (p) { return isTestable(graph, p.id); });
      return {
        id: id,
        // 先修里还没测到的（题量用完）——此时它未必是真正的根因
        pendingPrereqs: testableUnk.filter(function (p) { return inScope(p.id); }).map(function (p) { return p.id; }),
        // 筛查模式下范围之外的先修（不在本次范围内，没有检查）
        outOfScopePrereqs: testableUnk.filter(function (p) { return !inScope(p.id); }).map(function (p) { return p.id; }),
        // 小学外部节点（无诊断题，不测）
        externalPrereqs: unk.filter(function (p) { return !isTestable(graph, p.id); }).map(function (p) { return p.id; })
      };
    });

    // 学习路径：（根因 ∪ 不稳的点）的所有后代（子图内）∪ 它们自己，去掉已掌握，按拓扑序
    const inSub = new Set(nodes);
    const reach = new Set();
    const queue = roots.map(function (r) { return r.id; }).concat(shaky);
    queue.forEach(function (id) { reach.add(id); });
    while (queue.length) {
      const id = queue.shift();
      graph.dependents[id].forEach(function (d) {
        if (inSub.has(d.id) && !reach.has(d.id)) { reach.add(d.id); queue.push(d.id); }
      });
    }
    const rootSet = new Set(roots.map(function (r) { return r.id; }));
    const targetSet = new Set(scope ? [] : session.targets); // 筛查模式下“全部知识点都是目标”没有意义，不标目标
    const topoPos = Object.create(null);
    nodes.forEach(function (id, i) { topoPos[id] = i; });
    const path = nodes.filter(function (id) { return reach.has(id) && st(id) !== 'mastered'; })
      .map(function (id) {
        return { id: id, status: st(id), isRoot: rootSet.has(id), isTarget: targetSet.has(id) };
      });
    // 学习路径按年级从低到高；同一年级内保持拓扑序（先修在前）。没有 grade 的手造图保持原顺序。
    path.sort(function (a, b) {
      return gradeRank(graph, a.id) - gradeRank(graph, b.id) || topoPos[a.id] - topoPos[b.id];
    });

    const pending = session.stack.filter(function (id) { return !session.status[id] && isTestable(graph, id); });
    const next = nextQuestion(graph, session);
    return {
      mode: session.mode || 'target',
      targets: session.targets.slice(),
      asked: session.answers.length,
      limit: session.limit,
      finished: next === null,
      limitReached: session.answers.length >= session.limit && pending.length > 0,
      mastered: mastered, shaky: shaky, weak: weak, unconfirmed: unconfirmed, untested: untested,
      roots: roots, path: path
    };
  }

  /* ------------------------------------------------------------------ 路径图布局 */

  /**
   * 选出要画的节点：学习路径 ∪ 目标 ∪ 根因 ∪ 实际问过的点；
   * 边取这些节点上的“可达关系的传递约简”，非直接先修的边标 direct:false（画虚线）。
   * 分层：纵向，先修在上、目标在下。
   */
  function layout(graph, session, summary) {
    const S = new Set();
    const screen = !!session.scope;
    summary.path.forEach(function (p) { S.add(p.id); });
    if (!screen) session.targets.forEach(function (id) { S.add(id); });
    summary.roots.forEach(function (r) { S.add(r.id); });
    session.answers.forEach(function (a) { S.add(a.id); });
    if (S.size < 3 && !screen) {
      session.targets.forEach(function (id) {
        graph.prereqs[id].slice(0, 6).forEach(function (p) { S.add(p.id); });
      });
    }
    const ids = topoSort(graph, S);
    const edges = [];
    ids.forEach(function (b) {
      const anc = ancestorSet(graph, b);
      ids.forEach(function (a) {
        if (a === b || !anc.has(a)) return;
        const between = ids.some(function (c) {
          return c !== a && c !== b && anc.has(c) && ancestorSet(graph, c).has(a);
        });
        if (between) return;
        const direct = graph.prereqs[b].find(function (p) { return p.id === a; });
        edges.push({ from: a, to: b, direct: !!direct, strength: direct ? direct.strength : 'hard' });
      });
    });
    const layer = Object.create(null);
    ids.forEach(function (id) {
      let l = 0;
      edges.forEach(function (e) { if (e.to === id) l = Math.max(l, layer[e.from] + 1); });
      layer[id] = l;
    });
    const nLayers = ids.reduce(function (m, id) { return Math.max(m, layer[id] + 1); }, 1);
    const rows = [];
    for (let i = 0; i < nLayers; i++) rows.push([]);
    ids.forEach(function (id) { rows[layer[id]].push(id); });
    // 重心法减少交叉
    const slot = Object.create(null);
    rows.forEach(function (r) { r.forEach(function (id, i) { slot[id] = i; }); });
    const bary = function (id, nbrs) {
      if (!nbrs.length) return slot[id];
      return nbrs.reduce(function (s, n) { return s + slot[n]; }, 0) / nbrs.length;
    };
    for (let it = 0; it < 4; it++) {
      for (let l = 1; l < nLayers; l++) {
        rows[l].sort(function (a, b) {
          return bary(a, edges.filter(function (e) { return e.to === a; }).map(function (e) { return e.from; })) -
                 bary(b, edges.filter(function (e) { return e.to === b; }).map(function (e) { return e.from; }));
        });
        rows[l].forEach(function (id, i) { slot[id] = i; });
      }
      for (let l = nLayers - 2; l >= 0; l--) {
        rows[l].sort(function (a, b) {
          return bary(a, edges.filter(function (e) { return e.from === a; }).map(function (e) { return e.to; })) -
                 bary(b, edges.filter(function (e) { return e.from === b; }).map(function (e) { return e.to; }));
        });
        rows[l].forEach(function (id, i) { slot[id] = i; });
      }
    }
    const rootSet = new Set(summary.roots.map(function (r) { return r.id; }));
    const targetSet = new Set(screen ? [] : session.targets);
    const nodes = [];
    rows.forEach(function (r, l) {
      r.forEach(function (id, i) {
        nodes.push({
          id: id, layer: l, col: i, cols: r.length,
          status: statusOf(session, id), isTarget: targetSet.has(id), isRoot: rootSet.has(id)
        });
      });
    });
    return { nodes: nodes, edges: edges, layers: nLayers, maxCols: rows.reduce(function (m, r) { return Math.max(m, r.length); }, 1) };
  }

  /* ------------------------------------------------------------------ 章节解析 */

  /** 年级数字 ×2 + 学期，用于学习路径排序。没有 grade 时返回 0。 */
  function gradeRank(graph, id) {
    const t = graph.byId[id];
    if (!t || typeof t.grade !== 'number') return 0;
    return t.grade * 2 + (t.semester === '下' ? 1 : 0);
  }

  /**
   * 初中："七上 第一章 有理数 1.1" -> {volume:'七上', chapterNo:'第一章', chapterName:'有理数', section:'1.1'}
   * 小学："一年级上册 第1单元 单元名" 或 "一年级上册 综合与实践 活动名"
   */
  function parseChapter(chapter) {
    const s = chapter || '';
    const pm = /^([一二三四五六七八九])年级([上下全])册 (第\d+单元|预备单元\d) (.+)$/.exec(s);
    if (pm) return { volume: pm[1] + pm[2], chapterNo: pm[3], chapterName: pm[4], section: '' };
    // 资源页没有写进某一课的项目，例如「七年级上册 待核」。仍算进该册，不假装有单元号。
    const pend = /^([一二三四五六七八九])年级([上下全])册 待核$/.exec(s);
    if (pend) return { volume: pend[1] + pend[2], chapterNo: '待核', chapterName: '未挂到具体单元', section: '' };
    const pi = /^([一二三四五六])年级([上下])册 (综合与实践) (.+)$/.exec(s);
    if (pi) return { volume: pi[1] + pi[2], chapterNo: pi[3], chapterName: pi[4], section: '' };
    // 小学英语复习 / Recycle（如「四年级上册 复习 Let's help!」）
    const prev = /^([一二三四五六])年级([上下])册 (复习) (.+)$/.exec(s);
    if (prev) return { volume: prev[1] + prev[2], chapterNo: prev[3], chapterName: prev[4], section: '' };
    // 高中英语按册名解析，避免「第1单元 Teenage Life」被空格拆成章名和节。
    const enHs = /^(必修第([一二三])册|选择性必修第([一二三四])册) (欢迎单元|第\d+单元) (.+)$/.exec(s);
    if (enHs) {
      return {
        volume: enHs[2] ? ('必修' + enHs[2]) : ('选必' + enHs[3]),
        chapterNo: enHs[4],
        chapterName: enHs[5],
        section: ''
      };
    }
    // 高中数学不拆上下册。高一/高二是必修两册，选必一/二/三是选择性必修三册。
    const hs = /^(高[一二]|选必[一二三]) (数学建模|数学探究) (\S+)$/.exec(s);
    if (hs) return { volume: hs[1], chapterNo: hs[2], chapterName: hs[3], section: '' };
    const m = /^(\S+) (第\S+章) (\S+?)(?: (\S+))?$/.exec(s);
    if (!m) return { volume: '', chapterNo: '', chapterName: s, section: '' };
    return { volume: m[1], chapterNo: m[2], chapterName: m[3], section: m[4] || '' };
  }

  /** 学科：显式 subject 优先，否则 cne_ 是英语、cnp_ 是物理、cnc_ 是语文、cns_ 是科学、cnd_ 是道德与法治、cnh_ 是历史、cng_ 是地理、cnb_ 是生物、cnk_ 是化学，其余算数学。 */
  function subjectOf(topic) {
    if (!topic) return 'math';
    if (topic.subject === 'english' || topic.subject === 'math' || topic.subject === 'physics' || topic.subject === 'chinese' || topic.subject === 'science' || topic.subject === 'morality' || topic.subject === 'history' || topic.subject === 'geography' || topic.subject === 'biology' || topic.subject === 'chemistry') return topic.subject;
    if (String(topic.id || '').indexOf('cne_') === 0) return 'english';
    if (String(topic.id || '').indexOf('cnp_') === 0) return 'physics';
    if (String(topic.id || '').indexOf('cnc_') === 0) return 'chinese';
    if (String(topic.id || '').indexOf('cns_') === 0) return 'science';
    if (String(topic.id || '').indexOf('cnd_') === 0) return 'morality';
    if (String(topic.id || '').indexOf('cnh_') === 0) return 'history';
    if (String(topic.id || '').indexOf('cng_') === 0) return 'geography';
    if (String(topic.id || '').indexOf('cnb_') === 0) return 'biology';
    if (String(topic.id || '').indexOf('cnk_') === 0) return 'chemistry';
    return 'math';
  }

  /**
   * 整年级 / 整册的知识点：'一年级' = 一上 + 一下，'七上' = 七年级上册。
   * 高中不拆上下册：'高一' / '高一必修' = 必修第一册，'高二' / '高二必修' = 必修第二册。
   * '选必一' / '选择性必修第一册'、选必二、选必三 = 选择性必修三册。
   * 高中英语用「必修一」「必修二」「必修三」「选必四」，不占用数学的「高一」「高二」。
   * subject 默认 math，避免三上、四上和选必一把英语和数学混在一起。
   * 不带 subject 时「必修一」没有数学知识点，返回 null。
   * 返回 {ids, volumes, label}（ids 按 topics 文件顺序，只含正式知识点）；不认识的写法返回 null。
   */
  function gradeTargets(graph, scope, subject) {
    const subj = subject == null || subject === '' ? 'math' : subject;
    const key = String(scope == null ? '' : scope).trim();
    const books = {
      '高一': ['高一', '高一（必修第一册）'],
      '高一必修': ['高一', '高一（必修第一册）'],
      '高二': ['高二', '高二（必修第二册）'],
      '高二必修': ['高二', '高二（必修第二册）'],
      '选必一': ['选必一', '选必一（选择性必修第一册）'],
      '选择性必修第一册': ['选必一', '选必一（选择性必修第一册）'],
      '选必二': ['选必二', '选必二（选择性必修第二册）'],
      '选择性必修第二册': ['选必二', '选必二（选择性必修第二册）'],
      '选必三': ['选必三', '选必三（选择性必修第三册）'],
      '选择性必修第三册': ['选必三', '选必三（选择性必修第三册）'],
      '必修一': ['必修一', '必修一（必修第一册）'],
      '必修第一册': ['必修一', '必修一（必修第一册）'],
      '必修二': ['必修二', '必修二（必修第二册）'],
      '必修第二册': ['必修二', '必修二（必修第二册）'],
      '必修三': ['必修三', '必修三（必修第三册）'],
      '必修第三册': ['必修三', '必修三（必修第三册）'],
      '选必四': ['选必四', '选必四（选择性必修第四册）'],
      '选择性必修第四册': ['选必四', '选必四（选择性必修第四册）']
    };
    let volumes = null;
    let label = '';
    if (books[key]) {
      volumes = [books[key][0]];
      label = books[key][1];
    } else {
      const g = /^([一二三四五六七八九])年级$/.exec(key);
      const v = /^([一二三四五六七八九])([上下])$/.exec(key);
      const whole = /^([一二三四五六七八九])全$/.exec(key);
      if (g) {
        volumes = [g[1] + '上', g[1] + '下'];
        if (g[1] === '九') volumes.push('九全');
        label = g[1] + '年级';
      } else if (whole) {
        volumes = [whole[1] + '全'];
        label = whole[1] + '年级全一册';
      } else if (v) { volumes = [key]; label = v[1] + '年级' + (v[2] === '上' ? '上册' : '下册'); }
    }
    if (!volumes) return null;
    const ids = graph.topics.filter(function (t) {
      if (t.external) return false;
      if (subj !== 'all' && subjectOf(t) !== subj) return false;
      return volumes.indexOf(parseChapter(t.chapter).volume) >= 0;
    }).map(function (t) { return t.id; });
    return ids.length ? { ids: ids, volumes: volumes, label: label } : null;
  }

  /**
   * 按章汇总：范围内每章的 掌握 / 不稳 / 薄弱 / 未测 数量和薄弱、不稳的知识点 id。
   * 章按教材顺序给出，再按「薄弱数多、不稳数多」稳定排序，薄弱的章排前面。
   */
  function chapterSummary(graph, session) {
    const inOrder = new Set(session.order);
    const byKey = Object.create(null);
    const list = [];
    graph.topics.forEach(function (t) {
      if (t.external || !inOrder.has(t.id)) return;
      const c = parseChapter(t.chapter);
      const key = c.volume + ' ' + c.chapterNo + ' ' + c.chapterName;
      let ch = byKey[key];
      if (!ch) {
        ch = byKey[key] = {
          key: key, volume: c.volume, chapterNo: c.chapterNo, chapterName: c.chapterName,
          label: (c.volume ? c.volume + ' ' : '') + c.chapterNo + ' ' + c.chapterName,
          total: 0, mastered: 0, shaky: 0, weak: 0, untested: 0, weakIds: [], shakyIds: [], untestedIds: [], _i: list.length
        };
        list.push(ch);
      }
      const st = statusOf(session, t.id);
      ch.total++;
      if (st === 'mastered') ch.mastered++;
      else if (st === 'shaky') { ch.shaky++; ch.shakyIds.push(t.id); }
      else if (st === 'weak') { ch.weak++; ch.weakIds.push(t.id); }
      else { ch.untested++; ch.untestedIds.push(t.id); }
    });
    list.sort(function (a, b) { return b.weak - a.weak || b.shaky - a.shaky || a._i - b._i; });
    list.forEach(function (ch) { delete ch._i; });
    return list;
  }

  /**
   * 把 URL / 选择器里的 id 展开成图中的知识点。
   * aliases 形如 { "cnm_ext_002": { targets: ["cnm_p010", ...] } } 或 { id: ["cnm_p010"] }。
   * 未知 id 原样保留，交给 createSession 报错。
   */
  function resolveTargets(rawIds, aliases) {
    const map = aliases || {};
    const out = [];
    const seen = Object.create(null);
    (Array.isArray(rawIds) ? rawIds : [rawIds]).forEach(function (id) {
      if (!id) return;
      let targets = null;
      const spec = map[id];
      if (spec && Array.isArray(spec.targets)) targets = spec.targets;
      else if (Array.isArray(spec)) targets = spec;
      const list = targets && targets.length ? targets : [id];
      list.forEach(function (tid) {
        if (!seen[tid]) { seen[tid] = true; out.push(tid); }
      });
    });
    return out;
  }

  /* ------------------------------------------------------------------ 判题 */

  function normalizeText(input) {
    let s = String(input == null ? '' : input);
    s = s.replace(/²/g, '^2').replace(/³/g, '^3').replace(/[º˚∘゜]/g, '°');
    s = s.normalize('NFKC'); // 全角 -> 半角（数字、字母、，；：（）＝－ 等）
    s = s.replace(/[−‐-―﹣]/g, '-')
      .replace(/[、]/g, ',')
      .replace(/[。]/g, '.')
      .replace(/[“”‘’]/g, '"')
      .replace(/[×·⋅∙]/g, '*')
      .replace(/÷/g, '/')
      .replace(/[≦⩽]/g, '≤').replace(/[≧⩾]/g, '≥')
      .replace(/<=/g, '≤').replace(/>=/g, '≥')
      .replace(/[\[\]{}]/g, function (c) { return c === '[' || c === '{' ? '(' : ')'; });
    s = s.replace(/(\d)\s*度/g, '$1°');
    s = s.replace(/(\d)\s+(\d+\s*\/\s*\d+)/g, '$1又$2'); // 带分数 "1 1/2"
    s = s.replace(/\s+/g, '').toLowerCase();
    s = s.replace(/^(答案|答)[:=]/, '').replace(/或者/g, '或');
    s = s.replace(/[.!]+$/, '');
    if (/^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$/.test(s)) s = s.replace(/,/g, ''); // 千分位
    return s;
  }

  function splitTop(s, seps) {
    const parts = [];
    let depth = 0;
    let cur = '';
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      if (c === '(') depth++;
      else if (c === ')') depth = Math.max(0, depth - 1);
      if (depth === 0 && seps.indexOf(c) >= 0) { parts.push(cur); cur = ''; } else cur += c;
    }
    parts.push(cur);
    return parts.filter(function (p) { return p !== ''; });
  }

  function gcd(a, b) { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) { const t = a % b; a = b; b = t; } return a; }

  function ratio(n, d) {
    if (d === 0n) return null;
    if (d < 0n) { n = -n; d = -d; }
    const g = gcd(n, d) || 1n;
    return [n / g, d / g];
  }

  function decToRatio(str) {
    const i = str.indexOf('.');
    if (i < 0) return ratio(BigInt(str), 1n);
    const frac = str.slice(i + 1);
    const whole = str.slice(0, i) || '0';
    return ratio(BigInt(whole + frac), 10n ** BigInt(frac.length));
  }

  function isWrapped(t) {
    if (t[0] !== '(' || t[t.length - 1] !== ')') return false;
    let depth = 0;
    for (let i = 0; i < t.length; i++) {
      if (t[i] === '(') depth++;
      else if (t[i] === ')') { depth--; if (depth === 0 && i < t.length - 1) return false; }
    }
    return depth === 0;
  }

  const UNIT_ALIASES = {
    '米': 'm', 'm': 'm', '厘米': 'cm', 'cm': 'cm', '毫米': 'mm', 'mm': 'mm', '千米': 'km', '公里': 'km', 'km': 'km',
    '千克': 'kg', '公斤': 'kg', 'kg': 'kg', '克': 'g', 'g': 'g', '秒': 's', 's': 's', '分钟': 'min', 'min': 'min',
    '小时': 'h', 'h': 'h', '平方米': 'm^2', 'm^2': 'm^2', '平方厘米': 'cm^2', 'cm^2': 'cm^2',
    '立方米': 'm^3', 'm^3': 'm^3', '立方厘米': 'cm^3', 'cm^3': 'cm^3', '元': '元', '度': '°', '°': '°',
    // 物理：只收多字母单位，单字母（a、v、w、n、j）会和数学里的字母答案混淆，不收
    'm/s': 'm/s', '米/秒': 'm/s', 'km/h': 'km/h', '千米/时': 'km/h', 'kg/m^3': 'kg/m^3', 'g/cm^3': 'g/cm^3',
    'pa': 'Pa', '帕': 'Pa', '帕斯卡': 'Pa', 'kpa': 'kPa', 'hz': 'Hz', '赫兹': 'Hz', 'db': 'dB', '分贝': 'dB',
    'kw*h': 'kW·h', '千瓦时': 'kW·h', 'ml': 'mL', '毫升': 'mL', 'n/kg': 'N/kg', 'j/kg': 'J/kg'
  };

  function canonUnit(u) {
    if (!u) return { name: '', known: true };
    if (UNIT_ALIASES[u]) return { name: UNIT_ALIASES[u], known: true };
    if (/^[一-龥]{1,4}$/.test(u)) return { name: u, known: false };
    return null; // 不像单位，说明这不是“数+单位”
  }

  /** 解析数值：整数、小数、分数 a/b、带分数、百分数、带符号/括号；末尾可带单位。失败返回 null。 */
  function parseNumeric(str) {
    let t = str;
    let neg = false;
    for (let guard = 0; guard < 4; guard++) {
      if (isWrapped(t)) { t = t.slice(1, -1); continue; }
      if ((t[0] === '-' || t[0] === '+') && isWrapped(t.slice(1))) { if (t[0] === '-') neg = !neg; t = t.slice(2, -1); continue; }
      break;
    }
    const m = /^([+-]?)(?:(\d+)又)?(\d+(?:\.\d+)?|\.\d+)(?:\/(\d+(?:\.\d+)?|\.\d+))?(%|°)?(.*)$/.exec(t);
    if (!m) return null;
    const whole = m[2], numS = m[3], denS = m[4], mark = m[5];
    let rest = m[6];
    if (whole && !denS) return null;
    let val;
    if (whole) {
      const n = decToRatio(numS), d = decToRatio(denS);
      if (!n || !d || d[0] === 0n) return null;
      const f = ratio(n[0] * d[1], n[1] * d[0]);
      const w = ratio(BigInt(whole), 1n);
      val = ratio(w[0] * f[1] + f[0], f[1]);
    } else if (denS) {
      const n = decToRatio(numS), d = decToRatio(denS);
      if (!n || !d || d[0] === 0n) return null;
      val = ratio(n[0] * d[1], n[1] * d[0]);
    } else {
      val = decToRatio(numS);
    }
    if (!val) return null;
    if (m[1] === '-') neg = !neg;
    let n = neg ? -val[0] : val[0];
    let d = val[1];
    let unit = { name: '', known: true };
    if (mark === '%') {
      const r = ratio(n, d * 100n);
      n = r[0]; d = r[1];
      if (rest) return null;
    } else if (mark === '°') {
      unit = { name: '°', known: true };
      if (!/^[一-龥]{0,2}$/.test(rest)) return null;
    } else if (rest) {
      unit = canonUnit(rest);
      if (!unit) return null;
    }
    return { key: n + '/' + d, unit: unit };
  }

  function analyzePart(p) {
    let variable = '';
    let body = p;
    const m = /^([a-z](?:\([a-z]\))?)=(.+)$/.exec(p);
    if (m) { variable = m[1]; body = m[2]; }
    const num = parseNumeric(body);
    if (num) return { raw: p, variable: variable, kind: 'num', key: num.key, unit: num.unit };
    const tm = /^\((.+)\)$/.exec(body);
    if (tm) {
      const items = splitTop(tm[1], ',');
      const nums = items.map(parseNumeric);
      if (items.length > 1 && nums.every(Boolean)) {
        return { raw: p, variable: variable, kind: 'tuple', key: 't:' + nums.map(function (x) { return x.key; }).join(','), unit: { name: '', known: true } };
      }
    }
    return { raw: p, variable: variable, kind: 'text', key: body, unit: { name: '', known: true } };
  }

  function parseAnswer(input) {
    const norm = normalizeText(input);
    const parts = splitTop(norm.replace(/[和或与及]/g, ','), ',;').map(analyzePart);
    return { norm: norm, parts: parts };
  }

  // 'eq' | 'ne' | 'unsure'
  function partCompare(a, b) {
    if (a.kind !== b.kind || a.key !== b.key) return 'ne';
    const ua = a.unit, ub = b.unit;
    if (!ua.name || !ub.name || ua.name === ub.name) return 'eq';
    return ua.known && ub.known ? 'ne' : 'unsure';
  }

  function sameMultiset(as, bs, ignoreVar) {
    if (as.length !== bs.length) return null;
    const left = bs.slice();
    let fuzzy = false;
    for (let i = 0; i < as.length; i++) {
      let hit = -1;
      for (let j = 0; j < left.length; j++) {
        if (!ignoreVar && as[i].variable !== left[j].variable) continue;
        const c = partCompare(as[i], left[j]);
        if (c === 'ne') continue;
        if (c === 'unsure') fuzzy = true;
        hit = j;
        break;
      }
      if (hit < 0) return null;
      left.splice(hit, 1);
    }
    return fuzzy ? 'unsure' : 'eq';
  }

  function allNumeric(parts) { return parts.every(function (p) { return p.kind === 'num' || p.kind === 'tuple'; }); }

  function compareParsed(u, r) {
    let res = null;
    if (u.parts.length === r.parts.length) {
      const refVars = r.parts.map(function (p) { return p.variable; });
      const refVarsDistinct = r.parts.length > 1 && refVars.every(Boolean) && new Set(refVars).size === refVars.length;
      if (refVarsDistinct) {
        if (u.parts.every(function (p) { return p.variable; })) res = sameMultiset(u.parts, r.parts, false);
        else if (u.parts.every(function (p) { return !p.variable; })) {
          // 未写变量名时按参考答案的出现顺序对应（x 在前 y 在后）
          res = 'eq';
          for (let i = 0; i < u.parts.length; i++) {
            const c = partCompare(u.parts[i], r.parts[i]);
            if (c === 'ne') { res = null; break; }
            if (c === 'unsure') res = 'unsure';
          }
        } else return { relation: 'unsure' };
      } else {
        res = sameMultiset(u.parts, r.parts, true);
      }
    }
    if (res === 'eq') return { relation: 'equal' };
    if (res === 'unsure') return { relation: 'unsure' };
    return { relation: allNumeric(u.parts) && allNumeric(r.parts) ? 'different' : 'unsure' };
  }

  /**
   * 判题：只在“可靠”时给 correct/wrong，其余返回 manual（让用户对照参考答案自评）。
   *  - 规范化后完全相同、或数值/多答案集合等价 -> correct
   *  - 双方都能解析为数值（含坐标）但不等价 -> wrong
   *  - 其余（代数式、文字、多种写法）-> manual
   */
  function judgeAnswer(user, reference) {
    const u = parseAnswer(user);
    const r = parseAnswer(reference);
    if (!u.norm) return { verdict: 'manual', reason: 'empty' };
    if (u.norm === r.norm) return { verdict: 'correct', reason: 'identical' };
    if (!r.parts.length) return { verdict: 'manual', reason: 'no-reference' };
    const c = compareParsed(u, r);
    if (c.relation === 'equal') return { verdict: 'correct', reason: 'equivalent' };
    if (c.relation === 'different') return { verdict: 'wrong', reason: 'numeric-mismatch' };
    return { verdict: 'manual', reason: 'unsure' };
  }

  /* ------------------------------------------------------------------ 按题型判题 */

  const MANUAL_EMPTY = { verdict: 'manual', reason: 'empty' };

  function judgeChoice(user, q) {
    const raw = String(user == null ? '' : user).trim();
    if (!raw) return MANUAL_EMPTY;
    const choices = q.choices || [];
    const keys = choices.map(function (c) { return c.key; });
    let letter = null;
    const m = /^[(（]?([A-Za-z])[)）.．、:：]?$/.exec(raw);
    if (m) letter = m[1].toUpperCase();
    else {
      const n = normalizeText(raw);
      const hit = choices.find(function (c) { return normalizeText(c.text) === n; });
      if (hit) letter = hit.key;
    }
    if (!letter || keys.indexOf(letter) < 0) return { verdict: 'manual', reason: 'unrecognized' };
    return letter === q.answer ? { verdict: 'correct', reason: 'choice' } : { verdict: 'wrong', reason: 'choice' };
  }

  function judgeNumeric(user, q) {
    const u = parseAnswer(user);
    if (!u.norm) return MANUAL_EMPTY;
    const refs = [q.answer].concat(q.accept || []);
    for (let i = 0; i < refs.length; i++) {
      if (parseAnswer(refs[i]).norm === u.norm) return { verdict: 'correct', reason: 'identical' };
    }
    const main = parseAnswer(q.answer);
    if (!q.unordered && main.parts.length > 1) {
      // 多个答案且顺序有关：逐项按顺序比较（变量名忽略）
      if (u.parts.length !== main.parts.length) {
        return allNumeric(u.parts) ? { verdict: 'wrong', reason: 'count-mismatch' } : { verdict: 'manual', reason: 'unsure' };
      }
      let res = 'eq';
      for (let i = 0; i < u.parts.length; i++) {
        const c = partCompare(u.parts[i], main.parts[i]);
        if (c === 'ne') { res = 'ne'; break; }
        if (c === 'unsure') res = 'unsure';
      }
      if (res === 'eq') return { verdict: 'correct', reason: 'equivalent' };
      if (res === 'ne' && allNumeric(u.parts) && allNumeric(main.parts)) return { verdict: 'wrong', reason: 'numeric-mismatch' };
      return { verdict: 'manual', reason: 'unsure' };
    }
    const r = judgeAnswer(user, q.answer);
    if (r.verdict === 'correct') return r;
    for (let i = 1; i < refs.length; i++) {
      if (judgeAnswer(user, refs[i]).verdict === 'correct') return { verdict: 'correct', reason: 'accept' };
    }
    return r;
  }

  function judgeShort(user, q) {
    const u = normalizeText(user);
    if (!u) return MANUAL_EMPTY;
    const refs = [q.answer].concat(q.accept || []);
    for (let i = 0; i < refs.length; i++) {
      if (normalizeText(refs[i]) === u) return { verdict: 'correct', reason: i ? 'accept' : 'identical' };
    }
    for (let i = 0; i < refs.length; i++) {
      if (judgeAnswer(user, refs[i]).verdict === 'correct') return { verdict: 'correct', reason: 'equivalent' };
    }
    return { verdict: 'manual', reason: 'unsure' }; // 文字 / 代数式写法太多，不可靠时让用户对照参考答案自评
  }

  /** 按题型判题：choice 比字母（或选项文字）；numeric 数值等价；short 规范化精确匹配 + accept；self 永远自评。 */
  /**
   * 带 percent: true 的题（目前只有物理的效率题），answer 是百分数的数值部分，如 50 表示 50%。
   * 学生写 50 或 50%（全角 ％ 也算）都判对；0.5 不算，题干问的是「百分之多少」，0.5 也可能是把 0.5% 写错。
   * 没有 percent 的题（全部数学题）不经过这里，50% 仍按 0.5 判。
   */
  function stripPercent(user) {
    const s = String(user == null ? '' : user).trim();
    return s.replace(/\s*[%％]$/, '');
  }

  function judgeQuestion(q, user) {
    switch (q.type) {
      case 'choice': return judgeChoice(user, q);
      case 'numeric': return judgeNumeric(q.percent === true ? stripPercent(user) : user, q);
      case 'short': return judgeShort(user, q);
      case 'self': return { verdict: 'manual', reason: 'self' };
      default: return judgeAnswer(user, q.answer); // legacy：来自 diagnostic_question
    }
  }

  return {
    DEFAULT_LIMIT: DEFAULT_LIMIT,
    SCREEN_LIMIT: SCREEN_LIMIT,
    DEFAULT_CONFIRM: DEFAULT_CONFIRM,
    CONFIRM_CHOICES: CONFIRM_CHOICES.slice(),
    clampConfirm: clampConfirm,
    normalizeConfirm: normalizeConfirm,
    needConfirm: needConfirm,
    gradeTargets: gradeTargets,
    subjectOf: subjectOf,
    chapterSummary: chapterSummary,
    buildGraph: buildGraph,
    questionById: questionById,
    pickQuestion: pickQuestion,
    nextItem: nextItem,
    isUnconfirmed: isUnconfirmed,
    mulberry32: mulberry32,
    judgeQuestion: judgeQuestion,
    ancestors: ancestors,
    topoSort: topoSort,
    subgraph: subgraph,
    isTestable: isTestable,
    createSession: createSession,
    applyAnswer: applyAnswer,
    nextQuestion: nextQuestion,
    replay: replay,
    statusOf: statusOf,
    summarize: summarize,
    layout: layout,
    parseChapter: parseChapter,
    gradeRank: gradeRank,
    resolveTargets: resolveTargets,
    normalizeText: normalizeText,
    judgeAnswer: judgeAnswer
  };
});
