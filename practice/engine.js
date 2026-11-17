/* 巩固过关练习引擎：纯函数、无 DOM、无依赖。浏览器中暴露为 window.PracticeEngine，Node 中 require() 即可。
 *
 * 规则：
 *  - 题目按 basic -> standard -> advanced 推送：当前连对 k 题，就出第 min(k, 2) 档；答错公布解析后回到 basic；
 *  - 首次答错可原位重试一次（同一道题），第二次仍错才公布解析，并把连对清零；
 *  - 两级提示：题目有 hints 用它，没有就按知识点的 description / mastery_criteria 合成（synthesizeHints）；
 *  - 只有“第一次就答对、没用提示”才算连对；用了提示答对，连对清零（不算）；重试答对，连对不变；
 *  - 无提示连对 need（默认 3）题即过关（state.passed = true）。
 *
 * 数据流：createPractice(topic, bank, {seed, need, variant}) -> state
 *         useHint(state) -> state；submit(state, correct) -> state；next(state, bank, {variant}) -> state
 *         state.current 是当前题（可能是 variant 生成的变式题，因此整道题存在 state 里，可 JSON 序列化）。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.PracticeEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const TIERS = ['basic', 'standard', 'advanced'];
  const NEED = 3;
  const MAX_HINTS = 2;

  function hashStr(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h >>> 0;
  }
  function rand01(seed, key) {
    let a = hashStr(String(seed) + '|' + key);
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  function tierOf(q) { const i = TIERS.indexOf(q && q.difficulty); return i < 0 ? 1 : i; }

  /** 可以在练习里自动判分的题（self / short 要人工判，不进练习）。 */
  function practicable(bank) {
    return (bank || []).filter(function (q) { return q && (q.type === 'numeric' || q.type === 'choice'); });
  }

  function firstSentence(text) {
    const s = String(text || '').trim();
    const m = /^[^。；;！!？?]+[。；;！!？?]?/.exec(s);
    return m ? m[0] : s;
  }

  /** 两级提示：第 1 级点方向（知识点要点），第 2 级给方法（掌握标准 / 解析开头）。题目自带 hints 时直接用。 */
  function synthesizeHints(question, topic) {
    if (question && Array.isArray(question.hints) && question.hints.length) return question.hints.slice(0, MAX_HINTS);
    const out = [];
    const desc = topic && topic.description ? firstSentence(topic.description) : '';
    if (desc) out.push('回想一下「' + (topic.name || '这个知识点') + '」：' + desc);
    const crit = topic && Array.isArray(topic.mastery_criteria) ? topic.mastery_criteria.filter(Boolean) : [];
    if (crit.length) out.push('做这类题要会：' + crit.slice(0, 2).join('；') + '。按这个思路一步一步写下来，再检查一遍。');
    if (out.length < MAX_HINTS && question && question.type === 'choice') out.push('先把明显不对的选项排除掉，再在剩下的里面比较。');
    if (out.length < MAX_HINTS) out.push('把题目里的已知条件一条条列出来，想想要用哪一步把它们连起来。');
    return out.slice(0, MAX_HINTS);
  }

  /**
   * 选下一题：优先当前档（min(streak, 2)）里没出过的；没有就找最近档里没出过的；
   * 全出过了就用 opts.variant(question, topicId, seed) 生成变式题；还不行就重出最久以前出过的。
   */
  function pickNext(state, bank, opts) {
    const pool = practicable(bank);
    if (!pool.length) return null;
    const want = Math.min(state.streak, TIERS.length - 1);
    const served = new Set(state.served);
    const fresh = pool.filter(function (q) { return !served.has(q.id); });
    const key = state.round + '';
    const choose = function (list) { return list[Math.floor(rand01(state.seed, key) * list.length)]; };
    // 顺序：当前档没出过的 -> 更容易档没出过的（近的先）-> 当前档的变式题 -> 当前档重出旧题 -> 更难档没出过的
    for (let t = want; t >= 0; t--) {
      const c = fresh.filter(function (q) { return tierOf(q) === t; });
      if (c.length) return choose(c);
    }
    const base = pool.filter(function (q) { return tierOf(q) === want; });
    const src = choose(base.length ? base : pool);
    if (opts && typeof opts.variant === 'function') {
      try {
        const v = opts.variant(src, state.topicId, state.seed + '|' + state.round);
        if (v && !served.has(v.id)) return v;
      } catch (e) { /* 变式失败就往下找 */ }
    }
    // 没有变式题：当前档有题就重出最久以前出过的那道（不越级变难）；当前档根本没题，才用更难档的新题
    const order = state.served.slice();
    const oldestOf = function (list) {
      return list.slice().sort(function (a, b) { return order.lastIndexOf(a.id) - order.lastIndexOf(b.id); })[0];
    };
    if (base.length) return oldestOf(base);
    for (let t = want + 1; t < TIERS.length; t++) {
      const c = fresh.filter(function (q) { return tierOf(q) === t; });
      if (c.length) return choose(c);
    }
    return oldestOf(pool);
  }

  function base(state) {
    return {
      topicId: state.topicId, seed: state.seed, need: state.need, streak: state.streak, best: state.best,
      served: state.served.slice(), round: state.round, current: state.current, attempt: state.attempt,
      hintsUsed: state.hintsUsed, phase: state.phase, passed: state.passed, log: state.log.slice(), total: state.total
    };
  }

  function createPractice(topic, bank, opts) {
    opts = opts || {};
    const s = {
      topicId: topic.id, seed: opts.seed == null ? 'p' : String(opts.seed), need: opts.need || NEED,
      streak: 0, best: 0, served: [], round: 0, current: null, attempt: 1, hintsUsed: 0, phase: 'ask', passed: false, log: [], total: 0
    };
    s.current = pickNext(s, bank, opts);
    if (s.current) s.served.push(s.current.id);
    else s.phase = 'empty';
    return s;
  }

  function useHint(state) {
    if (state.phase !== 'ask' && state.phase !== 'retry') return state;
    const s = base(state);
    s.hintsUsed = Math.min(MAX_HINTS, s.hintsUsed + 1);
    return s;
  }

  /**
   * 提交当前题。phase：
   *   'correct'：答对（看 counted 是否计入连对）；'retry'：首次答错，原位再做一次；
   *   'reveal'：第二次仍错，公布解析，连对清零；'passed'：连对达到 need。
   */
  function submit(state, correct) {
    if (state.phase !== 'ask' && state.phase !== 'retry') return state;
    const s = base(state);
    const q = s.current;
    const entry = { qid: q.id, attempt: s.attempt, correct: !!correct, hints: s.hintsUsed };
    if (correct) {
      if (s.attempt === 1 && !s.hintsUsed) { s.streak++; entry.counted = true; }
      else if (s.hintsUsed) { s.streak = 0; entry.counted = false; }
      else entry.counted = false;                 // 重试答对：连对不变
      s.best = Math.max(s.best, s.streak);
      s.total++;
      s.phase = s.streak >= s.need ? 'passed' : 'correct';
      if (s.phase === 'passed') s.passed = true;
    } else if (s.attempt === 1) {
      s.phase = 'retry';
      s.attempt = 2;
    } else {
      s.streak = 0;
      s.total++;
      s.phase = 'reveal';
    }
    entry.streak = s.streak;
    s.log.push(entry);
    return s;
  }

  function next(state, bank, opts) {
    if (state.phase !== 'correct' && state.phase !== 'reveal') return state;
    const s = base(state);
    s.round++;
    s.attempt = 1;
    s.hintsUsed = 0;
    s.phase = 'ask';
    s.current = pickNext(s, bank, opts);
    if (s.current) s.served.push(s.current.id);
    else s.phase = 'empty';
    return s;
  }

  /* ------------------------------------------------------------ 今日微巩固挑战（交错复习） */

  /** 从到期复习的点（dueIds，已按到期先后排）和不稳的点（shakyIds）里挑 n 个：到期的优先，同一天同一种子结果不变。 */
  function pickChallengeTopics(dueIds, shakyIds, seed, n) {
    n = n || 3;
    const out = [];
    const take = function (list, shuffle) {
      let l = (list || []).filter(function (id) { return out.indexOf(id) < 0; });
      if (shuffle) l = l.map(function (id) { return { id: id, r: rand01(seed, 'pick|' + id) }; }).sort(function (a, b) { return a.r - b.r; }).map(function (x) { return x.id; });
      l.forEach(function (id) { if (out.length < n && out.indexOf(id) < 0) out.push(id); });
    };
    take(dueIds, false);
    take(shakyIds, true);
    return out;
  }

  /**
   * 每个知识点抽 perTopic（默认 2）道可判分的题（basic / standard 优先），再交错混编：
   * 打乱后尽量让相邻两题不是同一个知识点。返回 [{topicId, question}]。
   */
  function buildChallenge(topicIds, banksById, seed, perTopic) {
    perTopic = perTopic || 2;
    const items = [];
    topicIds.forEach(function (id) {
      const pool = practicable(banksById[id]).map(function (q) { return { q: q, r: rand01(seed, id + '|' + q.id) + (tierOf(q) >= 2 ? 1 : 0) }; })
        .sort(function (a, b) { return a.r - b.r; }).slice(0, perTopic);
      pool.forEach(function (x) { items.push({ topicId: id, question: x.q, r: rand01(seed, 'mix|' + x.q.id) }); });
    });
    items.sort(function (a, b) { return a.r - b.r; });
    // 交错：相邻同一知识点时，往后找一个不同的换上来
    for (let i = 1; i < items.length; i++) {
      if (items[i].topicId !== items[i - 1].topicId) continue;
      for (let j = i + 1; j < items.length; j++) {
        if (items[j].topicId !== items[i - 1].topicId) { const t = items[i]; items[i] = items[j]; items[j] = t; break; }
      }
    }
    return items.map(function (x) { return { topicId: x.topicId, question: x.question }; });
  }

  /** 挑战结束后每个知识点的结论：全部一次做对且没看提示 -> 'pass'（复习通过）；否则 'shaky'。 */
  function challengeVerdicts(log) {
    const by = {};
    (log || []).forEach(function (e) {
      const v = by[e.topicId] || (by[e.topicId] = { clean: 0, total: 0 });
      v.total++;
      if (e.firstTry && !e.hints) v.clean++;
    });
    const out = {};
    Object.keys(by).forEach(function (id) { out[id] = by[id].clean === by[id].total ? 'pass' : 'shaky'; });
    return out;
  }

  return {
    pickChallengeTopics: pickChallengeTopics, buildChallenge: buildChallenge, challengeVerdicts: challengeVerdicts,
    TIERS: TIERS, NEED: NEED, MAX_HINTS: MAX_HINTS,
    createPractice: createPractice, useHint: useHint, submit: submit, next: next,
    synthesizeHints: synthesizeHints, practicable: practicable, pickNext: pickNext
  };
});
