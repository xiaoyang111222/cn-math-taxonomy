#!/usr/bin/env node
/* 知识点静态页测试：node tests/test_kp_pages.js（无依赖，生成到临时目录后检查）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const OUT = fs.mkdtempSync(path.join(os.tmpdir(), 'kp-test-'));
const ORIGIN = 'https://math.pansgo.com';
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
const readJson = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const page = (id) => fs.readFileSync(path.join(OUT, 'kp', id + '.html'), 'utf8');
const subjectOf = (t) => t.subject || 'math';

const topics = readJson('data/topics.json');
const deps = readJson('data/dependencies.json');
const questions = readJson('data/questions.json');
const byId = new Map(topics.map((t) => [t.id, t]));
const SUBJECTS = ['math', 'chinese', 'science', 'morality', 'history', 'geography', 'biology', 'chemistry', 'english', 'physics'];

let log;
try {
  log = execFileSync(process.execPath, [path.join(ROOT, 'scripts/gen-kp-pages.mjs'), '--out', OUT], { encoding: 'utf8' });
  const log2 = execFileSync(process.execPath, [path.join(ROOT, 'scripts/gen-kp-pages.mjs'), '--out', OUT + '-b'], { encoding: 'utf8' });

  test('知识点页数等于 topics 条数', () => {
    const files = fs.readdirSync(path.join(OUT, 'kp')).filter((f) => /^[a-z]{3}_[a-z0-9]+\.html$/.test(f));
    assert.equal(files.length, topics.length);
    for (const t of topics) assert.ok(fs.existsSync(path.join(OUT, 'kp', t.id + '.html')), t.id);
    assert.match(log, new RegExp('知识点页：' + topics.length));
  });

  test('总索引与 10 个学科索引页', () => {
    assert.ok(fs.existsSync(path.join(OUT, 'kp/index.html')));
    for (const s of SUBJECTS) assert.ok(fs.existsSync(path.join(OUT, 'kp', s + '.html')), s);
    const index = fs.readFileSync(path.join(OUT, 'kp/index.html'), 'utf8');
    for (const s of SUBJECTS) {
      const n = topics.filter((t) => subjectOf(t) === s).length;
      assert.ok(index.includes(`href="/kp/${s}"`), s);
      assert.ok(index.includes(`${n} 个知识点`), s + ' 数量');
      const sp = fs.readFileSync(path.join(OUT, 'kp', s + '.html'), 'utf8');
      const links = sp.match(/<a href="\/kp\/[a-z]{3}_[a-z0-9]+">/g) || [];
      assert.equal(links.length, n, s + ' 学科页链接数');
    }
  });

  test('抽 3 个学科的页面含 name、description、canonical、先修链接与诊断深链', () => {
    for (const s of ['math', 'english', 'chemistry']) {
      const edge = deps.find((e) => subjectOf(byId.get(e.topicId)) === s && byId.has(e.prerequisiteId));
      assert.ok(edge, s + ' 没有先修边');
      const t = byId.get(edge.topicId);
      const html = page(t.id);
      assert.ok(html.includes('<h1>' + esc(t.name) + '</h1>'), 'h1');
      assert.ok(html.includes(esc(t.description)), 'description');
      assert.ok(html.includes(`<link rel="canonical" href="${ORIGIN}/kp/${t.id}">`), 'canonical');
      assert.ok(html.includes(`<meta property="og:url" content="${ORIGIN}/kp/${t.id}">`), 'og:url');
      assert.ok(html.includes('<meta property="og:type" content="article">'));
      assert.ok(html.includes(`content="${ORIGIN}/assets/og-cover.jpg"`));
      assert.ok(html.includes(`href="/kp/${edge.prerequisiteId}"`), '先修链接');
      assert.ok(html.includes(esc(edge.reason)), '先修 reason');
      const pre = page(edge.prerequisiteId);
      assert.ok(pre.includes(`href="/kp/${t.id}"`), '反向链接');
      const n = questions.filter((q) => q.topicId === t.id).length;
      if (n) assert.ok(html.includes(`本站共有 ${n} 道`), '配套题数');
      const deep = s === 'math' ? `/diagnose/?target=${t.id}` : `/diagnose/?subject=${s}&amp;target=${t.id}`;
      assert.ok(html.includes(`href="${deep}"`), '诊断深链 ' + deep);
      assert.match(html, /<title>[^<]+｜[^<]*知识点讲解与自测 - 中小学知识图谱<\/title>/);
    }
  });

  test('可选区块缺失时不渲染', () => {
    const noDq = topics.find((t) => !(t.diagnostic_question && t.diagnostic_question.question));
    if (noDq) assert.ok(!page(noDq.id).includes('自测一题'));
    const noRoot = topics.find((t) => !t.root_reason);
    if (noRoot) assert.ok(!page(noRoot.id).includes('常见卡点'));
    const noPre = topics.find((t) => !deps.some((e) => e.topicId === t.id));
    if (noPre) assert.ok(!page(noPre.id).includes('先修知识点'));
  });

  test('meta description 截断到约 110 字', () => {
    for (const t of topics) {
      const m = page(t.id).match(/<meta name="description" content="([^"]*)">/);
      assert.ok(m, t.id);
      assert.ok(Array.from(m[1]).length <= 400, t.id);
    }
    const long = topics.find((t) => Array.from(t.description).length > 110);
    if (long) {
      const m = page(long.id).match(/<meta name="description" content="([^"]*)">/);
      assert.equal(Array.from(m[1].replace(/&[a-z#0-9]+;/g, 'x')).length <= 111, true);
      assert.ok(m[1].endsWith('…'));
    }
  });

  test('sitemap URL 数 = 知识点数 + 索引与主要页面数', () => {
    const xml = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8');
    const locs = xml.match(/<loc>[^<]+<\/loc>/g) || [];
    assert.equal(locs.length, topics.length + 1 + SUBJECTS.length + 5);
    assert.equal(new Set(locs).size, locs.length);
    for (const p of ['/', '/diagnose/', '/explore/', '/goods/', '/wrongbook/', '/kp/']) {
      assert.ok(xml.includes(`<loc>${ORIGIN}${p}</loc>`), p);
    }
    for (const s of SUBJECTS) assert.ok(xml.includes(`<loc>${ORIGIN}/kp/${s}</loc>`), s);
    const kp = topics.filter((t) => xml.includes(`<loc>${ORIGIN}/kp/${t.id}</loc>`));
    assert.equal(kp.length, topics.length);
  });

  test('robots.txt 允许抓取并指向 sitemap', () => {
    const robots = fs.readFileSync(path.join(OUT, 'robots.txt'), 'utf8');
    assert.match(robots, /^User-agent: \*$/m);
    assert.match(robots, /^Allow: \/$/m);
    assert.ok(robots.includes(`Sitemap: ${ORIGIN}/sitemap.xml`));
  });

  test('数据里的 < & " 等字符全部转义，原文不会进入 HTML', () => {
    const special = topics.filter((t) => /[<>&"']/.test(JSON.stringify([t.name, t.description, t.chapter, t.domain, t.mastery_criteria, t.diagnostic_question, t.root_reason])));
    assert.ok(special.length >= 5, '应有含特殊字符的条目');
    const lt = special.find((t) => t.description.includes('<') || t.name.includes('<') || (t.diagnostic_question && String(t.diagnostic_question.question).includes('<')));
    assert.ok(lt, '应有含 < 的条目');
    for (const t of special) {
      const html = page(t.id);
      const strings = [t.name, t.description, t.chapter, t.domain, t.root_reason,
        ...(t.mastery_criteria || []), t.diagnostic_question && t.diagnostic_question.question, t.diagnostic_question && t.diagnostic_question.answer]
        .filter((x) => typeof x === 'string' && /[<>&"']/.test(x));
      for (const s of strings) {
        assert.ok(!html.includes(s), t.id + ' 含未转义原文：' + s);
        assert.ok(html.includes(esc(s)), t.id + ' 缺少转义后的文本：' + s);
      }
    }
    for (const t of topics) {
      const body = page(t.id).replace(/<[a-zA-Z!/][^<>]*>/g, '');
      assert.ok(!/[<>]/.test(body), t.id + ' 正文残留未转义的尖括号');
    }
  });

  test('生成结果确定：两次输出逐字节一致', () => {
    const a = OUT;
    const b = OUT + '-b';
    const names = fs.readdirSync(path.join(a, 'kp')).sort();
    assert.deepEqual(fs.readdirSync(path.join(b, 'kp')).sort(), names);
    for (const n of names) assert.ok(fs.readFileSync(path.join(a, 'kp', n)).equals(fs.readFileSync(path.join(b, 'kp', n))), n);
    assert.ok(fs.readFileSync(path.join(a, 'sitemap.xml')).equals(fs.readFileSync(path.join(b, 'sitemap.xml'))));
    assert.equal(log, log2.split(OUT + '-b').join(OUT));
  });

  test('统计输出含先修边覆盖数', () => {
    assert.match(log, new RegExp('先修边：' + deps.length + '/' + deps.length));
  });
} finally {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.rmSync(OUT + '-b', { recursive: true, force: true });
}

console.log(`\n${passed} passed`);
