#!/usr/bin/env node
/* 首页题库异步：假 DOM + 可控 fetch。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/home.js'), 'utf8');
let passed = 0;

async function test(name, fn) {
  await fn();
  passed++;
  console.log('  ok   ' + name);
}

const flush = async () => { for (let i = 0; i < 12; i++) await new Promise(r => setImmediate(r)); };

function element() {
  const attrs = {};
  const el = {
    textContent: '', hidden: true, children: [], className: '', href: '',
    classList: { toggle() {}, add() {}, remove() {} },
    setAttribute(k, v) { attrs[k] = String(v); },
    getAttribute(k) { return k in attrs ? attrs[k] : null; },
    removeAttribute(k) { delete attrs[k]; },
    hasAttribute(k) { return k in attrs; },
    replaceChildren() { el.children = []; },
    append(...nodes) { el.children.push(...nodes); },
    appendChild(node) { el.children.push(node); return node; }
  };
  return el;
}

const topics = [
  { id: 'cnm_a', grade: 1, semester: '上' },
  { id: 'cnm_b', grade: 7, semester: '下' },
  { id: 'cne_a', grade: 3, semester: '上' },
  { id: 'cnp_a', grade: 8, semester: '上' }
];
const deps = [{ topicId: 'cnm_b', prerequisiteId: 'cnm_a' }];
const qIndex = {
  total: 12345,
  subjects: { math: { file: 'math.json', count: 3 }, english: { file: 'english.json', count: 1 }, physics: { file: 'physics.json', count: 1 } }
};
const INDEX_URL = 'data/questions/index.json';

function load(search, topicRows, extraWindow) {
  const ids = {};
  ['due-home', 'due-home-line', 'due-home-n', 'due-home-all', 'today-en-line', 'today-en-state', 'today-en-review', 'today-en-review-n', 'today-streak-line', 'today-streak-n', 'n-topics', 'n-edges', 'n-questions', 'n-subjects', 'cover-morality', 'hero-start', 'hero-demo', 'load-error', 'grades'].forEach(id => { ids[id] = element(); });
  ids.grades.setAttribute('aria-busy', 'true');
  const calls = [];
  function fetch(url) {
    let resolve, reject;
    const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
    calls.push({ url, resolve, reject, promise });
    return promise;
  }
  const context = {
    window: Object.assign({}, extraWindow || {}),
    location: { hash: '', search: search || '' },
    URLSearchParams,
    fetch,
    document: {
      title: '',
      body: { classList: { toggle() {} } },
      querySelector() { return null; },
      querySelectorAll() { return []; },
      getElementById(id) { return ids[id] || null; },
      createElement(tag) { const el = element(); el.tagName = String(tag || '').toUpperCase(); return el; }
    }
  };
  vm.runInNewContext(source, context, { filename: 'assets/home.js' });
  const all = url => calls.filter(c => c.url === url);
  const call = url => all(url)[0];
  const respond = (url, data, status) => {
    const c = call(url);
    assert.ok(c, 'expected fetch of ' + url);
    const ok = status === undefined || (status >= 200 && status < 300);
    c.resolve({ ok, status: status || 200, json: () => Promise.resolve(data) });
  };
  const failNet = (url) => {
    const c = call(url);
    assert.ok(c, 'expected fetch of ' + url);
    c.reject(new Error('network'));
  };
  async function baseMeta() {
    respond('data/topics.json', topicRows || topics);
    respond('data/dependencies.json', deps);
    await flush();
  }
  return { ids, calls, all, call, respond, failNet, baseMeta, context };
}

(async () => {
  await test('元数据到后渲染全站数字（不分学科），题数在索引到达前不显示数字', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    assert.strictEqual(ids['n-topics'].textContent, '4');
    assert.strictEqual(ids['n-edges'].textContent, '1');
    assert.strictEqual(ids['n-subjects'].textContent, '3');
    assert.ok(['', '…'].includes(ids['n-questions'].textContent), '题数在索引到之前不应有数字');
    assert.ok(ids.grades.children.length > 0, 'grade cards rendered');
    respond(INDEX_URL, qIndex);
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '12,345');
  });

  await test('数字带千分位', async () => {
    const rows = [];
    for (let i = 0; i < 1500; i++) rows.push({ id: 'cnm_x' + i, grade: 1, semester: '上' });
    const { ids, baseMeta } = load('', rows);
    await baseMeta();
    assert.strictEqual(ids['n-topics'].textContent, '1,500');
  });

  await test('题库索引 404 显示 — 且不整页 fail', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    respond(INDEX_URL, null, 404);
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '—');
    assert.strictEqual(ids['load-error'].hidden, true);
    assert.strictEqual(ids['n-topics'].textContent, '4');
  });

  await test('题库索引格式不对显示 —', async () => {
    const { ids, baseMeta, respond } = load('');
    await baseMeta();
    respond(INDEX_URL, { subjects: { math: {} } });
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '—');
  });

  await test('题库索引网络错误会重试至多 2 次', async () => {
    const { ids, all, baseMeta, failNet } = load('');
    await baseMeta();
    assert.strictEqual(all(INDEX_URL).length, 1);
    failNet(INDEX_URL);
    await flush();
    assert.ok(all(INDEX_URL).length >= 2, 'retried');
    const second = all(INDEX_URL)[1];
    second.resolve({ ok: true, status: 200, json: () => Promise.resolve(qIndex) });
    await flush();
    assert.strictEqual(ids['n-questions'].textContent, '12,345');
  });

  await test('首页只请求 topics、dependencies 和题库索引，不拉任何题目文件', async () => {
    const { calls, baseMeta, respond } = load('');
    await baseMeta();
    respond(INDEX_URL, qIndex);
    await flush();
    assert.deepStrictEqual(calls.map(c => c.url).sort(), ['data/dependencies.json', INDEX_URL, 'data/topics.json'].sort());
  });

  await test('进行中 Promise 去重', async () => {
    assert.ok(source.includes('fetchInflight'), 'inflight map present');
    assert.ok(source.includes('fetchJsonWithRetry'), 'retry helper present');
  });

  await test('topics 无效仍 fail', async () => {
    const { ids, respond } = load('');
    respond('data/topics.json', { bad: true });
    respond('data/dependencies.json', deps);
    await flush();
    assert.strictEqual(ids['load-error'].hidden, false);
  });

  await test('语文高中卡片写必修上', async () => {
    const rows = topics.concat([{ id: 'cnc_h001', grade: 10, semester: '上', subject: 'chinese' }]);
    const { ids, baseMeta } = load('?subject=chinese', rows);
    await baseMeta();
    const titles = ids.grades.children.map((card) => {
      const strong = (card.children || []).find((node) => node.tagName === 'STRONG');
      return strong ? strong.textContent : '';
    });
    assert.ok(titles.includes('必修上'), 'cards: ' + titles.join(','));
    assert.ok(!titles.includes('高一') && !titles.includes('必修一'), titles.join(','));
  });

  await test('英语页：统计仍是全站数字，年级入口只算英语，开始诊断指向英语', async () => {
    const { ids, baseMeta, respond } = load('?subject=english');
    await baseMeta();
    respond(INDEX_URL, qIndex);
    await flush();
    assert.strictEqual(ids['n-topics'].textContent, '4');
    assert.strictEqual(ids['n-questions'].textContent, '12,345');
    const counts = ids.grades.children.map((card) => card.children[2].textContent);
    assert.ok(counts.includes('1 个知识点'), counts.join(','));
    assert.strictEqual(ids['hero-start'].getAttribute('href'), 'diagnose/?subject=english');
    assert.ok(ids['hero-demo'].getAttribute('href').indexOf('subject=english') >= 0);
  });

  const dueWindow = (loggedIn, n, buckets) => {
    const handlers = {};
    const state = { loggedIn, n, buckets: buckets === undefined ? 1 : buckets };
    return {
      state, handlers,
      win: {
        CnmAccount: { isLoggedIn: () => state.loggedIn },
        CnmWrong: { dueTotal: () => state.n, dueBuckets: () => state.buckets },
        addEventListener: (name, fn) => { handlers[name] = fn; }
      }
    };
  };

  await test('首页待复测卡片：登录且有到期题才显示，带数量', async () => {
    const d = dueWindow(true, 5);
    const { ids } = load('', undefined, d.win);
    assert.strictEqual(ids['due-home'].hidden, false);
    assert.strictEqual(ids['due-home-n'].textContent, '5');
  });

  await test('首页待复测卡片：到期题分散在多个孩子名下时标明是全部孩子合计，单个孩子不标', async () => {
    const multi = load('', undefined, dueWindow(true, 6, 2).win).ids;
    assert.strictEqual(multi['due-home-n'].textContent, '6');
    assert.strictEqual(multi['due-home-all'].hidden, false);
    const single = load('', undefined, dueWindow(true, 6, 1).win).ids;
    assert.strictEqual(single['due-home-all'].hidden, true);
    const d = dueWindow(true, 6, 2);
    const { ids } = load('', undefined, d.win);
    d.state.buckets = 1;
    d.handlers['cnm:sync']();
    assert.strictEqual(ids['due-home-all'].hidden, true);
  });

  await test('首页待复测卡片：未登录且没有任何进度不显示；登录但没有到期题时待复测一行隐藏（卡片仍在）', async () => {
    const out = dueWindow(false, 5);
    assert.strictEqual(load('', undefined, out.win).ids['due-home'].hidden, true);
    const none = dueWindow(true, 0);
    const { ids } = load('', undefined, none.win);
    assert.strictEqual(ids['due-home'].hidden, false, '登录用户的「今日学习」卡常在');
    assert.strictEqual(ids['due-home-line'].hidden, true);
    assert.strictEqual(ids['today-en-line'].hidden, true, '没有英语脚本时不显示英语一行');
    assert.strictEqual(load('').ids['due-home'].hidden, true, '没有错题本脚本时不显示、不报错');
  });

  await test('首页待复测卡片：登录 / 同步事件后刷新', async () => {
    const d = dueWindow(false, 3);
    const { ids } = load('', undefined, d.win);
    assert.strictEqual(ids['due-home'].hidden, true);
    d.state.loggedIn = true;
    d.handlers['cnm:auth']();
    assert.strictEqual(ids['due-home'].hidden, false);
    assert.strictEqual(ids['due-home-line'].hidden, false);
    assert.strictEqual(ids['due-home-n'].textContent, '3');
    d.state.n = 0;
    d.handlers['cnm:sync']();
    assert.strictEqual(ids['due-home-line'].hidden, true);
  });

  const todayWindow = (opts) => {
    const state = Object.assign({ loggedIn: true, n: 0, child: { id: 'c1' }, en: { doneCount: 0, completedToday: false, finished: false, reviewTotal: 0 }, streak: 0, any: false }, opts || {});
    const seen = {};
    const win = {
      CnmAccount: { isLoggedIn: () => state.loggedIn },
      CnmWrong: { dueTotal: () => state.n, dueBuckets: () => 1 },
      CnmChildren: { current: () => state.child },
      CnmEnglish: { todayState: (bucket) => { seen.enBucket = bucket; return state.en; } },
      CnmActivity: { streak: (bucket) => { seen.actBucket = bucket; return state.streak; }, hasAny: () => state.any },
      addEventListener: (name, fn) => { seen[name] = fn; }
    };
    return { state, seen, win };
  };

  await test('今日学习卡：当前孩子的英语一句（未学 / 已完成 / 学完）、到期旧句复习与连续天数', async () => {
    const t = todayWindow({ n: 4, streak: 6, en: { doneCount: 3, completedToday: false, finished: false, reviewTotal: 2 } });
    const { ids } = load('', undefined, t.win);
    assert.strictEqual(t.seen.enBucket, 'c1', '用站内当前孩子');
    assert.strictEqual(t.seen.actBucket, 'c1');
    assert.strictEqual(ids['due-home'].hidden, false);
    assert.strictEqual(ids['due-home-n'].textContent, '4');
    assert.strictEqual(ids['today-en-line'].hidden, false);
    assert.strictEqual(ids['today-en-state'].textContent, '未学');
    assert.strictEqual(ids['today-en-review'].hidden, false);
    assert.strictEqual(ids['today-en-review-n'].textContent, '2');
    assert.strictEqual(ids['today-streak-line'].hidden, false);
    assert.strictEqual(ids['today-streak-n'].textContent, '6');
    t.state.en = { doneCount: 4, completedToday: true, finished: false, reviewTotal: 0 };
    t.state.streak = 0;
    t.seen['cnm:sync']();
    assert.strictEqual(ids['today-en-state'].textContent, '已完成');
    assert.strictEqual(ids['today-en-review'].hidden, true);
    assert.strictEqual(ids['today-streak-line'].hidden, true);
    t.state.en = { doneCount: 30, completedToday: false, finished: true, reviewTotal: 0 };
    t.seen['cnm:sync']();
    assert.strictEqual(ids['today-en-state'].textContent, '30 句已学完');
  });

  await test('今日学习卡：没有孩子档案用 guest 桶；未登录的游客有英语或打卡进度才显示游客版', async () => {
    const g = todayWindow({ loggedIn: false, child: null, en: { doneCount: 2, completedToday: true, finished: false, reviewTotal: 0 } });
    const { ids } = load('', undefined, g.win);
    assert.strictEqual(g.seen.enBucket, 'guest');
    assert.strictEqual(ids['due-home'].hidden, false);
    const none = todayWindow({ loggedIn: false, child: null });
    assert.strictEqual(load('', undefined, none.win).ids['due-home'].hidden, true);
    const act = todayWindow({ loggedIn: false, child: null, any: true, streak: 1 });
    assert.strictEqual(load('', undefined, act.win).ids['due-home'].hidden, false);
  });

  await test('首页硬约束：数字条、学科胶囊、登录入口脚本、统计埋点、页脚友链、英语入口都在', async () => {
    const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
    ['id="stats"', 'id="n-topics"', 'id="pill-row"', 'data-subject="english"', 'assets/account.js', 'assets/stats.js', 'assets/stats-config.js', 'id="blind-home"', 'class="site-footer"', 'issues/new/choose'].forEach((frag) => {
      assert.ok(html.includes(frag), frag);
    });
    assert.ok(/<a class="english-entry[^"]*" href="english\/">英语每日一句 · 每天 3 分钟 →<\/a>/.test(html));
    assert.ok(html.indexOf('id="subject-more"') < html.indexOf('class="english-entry'), '入口在学科区下方');
    assert.ok(html.indexOf('assets/english.js') < html.indexOf('assets/home.js') && html.indexOf('assets/activity.js') < html.indexOf('assets/home.js'));
    assert.ok(html.includes('href="wrongbook/"') && html.includes('href="english/"'), '卡内两个链接');
  });

  console.log(passed + ' passed');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
