#!/usr/bin/env node
/* 知识点独立静态页生成器（零依赖）：node scripts/gen-kp-pages.mjs [--out <dir>]
 * 输出：kp/<id>.html、kp/index.html、kp/<subject>.html、sitemap.xml、robots.txt。
 * 同输入同输出（无时间戳、无随机）。
 * URL 形式：Cloudflare Pages 会把 /x.html 308 到 /x，所以 canonical、sitemap 与站内链接统一用无后缀形式。 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ORIGIN = 'https://math.pansgo.com';
const SITE_TITLE = '中小学知识图谱';
const OG_IMAGE = ORIGIN + '/assets/og-cover.jpg';

/* 学科顺序与 explore 页导航一致；中文名与诊断页/错题本一致。 */
const SUBJECTS = [
  ['math', '数学'], ['chinese', '语文'], ['science', '科学'], ['morality', '道德与法治'],
  ['history', '历史'], ['geography', '地理'], ['biology', '生物'], ['chemistry', '化学'],
  ['english', '英语'], ['physics', '物理'], ['politics', '思想政治']
];
const SUBJECT_NAME = Object.fromEntries(SUBJECTS);
const NUM_ZH = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
const SEMESTER_ORDER = { '上': 0, '下': 1, '全': 2 };

const MAIN_PAGES = [
  ['/', '1.0'], ['/diagnose/', '1.0'], ['/explore/', '0.9'], ['/goods/', '0.9'], ['/wrongbook/', '0.9'], ['/finals/', '0.9']
];

function parseArgs(argv) {
  let out = path.join(process.cwd(), 'kp-out');
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--out') {
      if (!argv[i + 1]) throw new Error('--out 缺少目录参数');
      out = path.resolve(argv[++i]);
    } else if (argv[i].startsWith('--out=')) {
      out = path.resolve(argv[i].slice(6));
    } else {
      throw new Error('未知参数：' + argv[i]);
    }
  }
  return { out };
}

const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
}

function truncate(text, max) {
  const chars = Array.from(String(text).replace(/\s+/g, ' ').trim());
  return chars.length <= max ? chars.join('') : chars.slice(0, max).join('') + '…';
}

const subjectOf = (t) => (t.subject && SUBJECT_NAME[t.subject] ? t.subject : 'math');

function stageOf(t) {
  const g = Number(t.grade);
  if (g >= 1 && g <= 6) return '小学';
  if (g >= 7 && g <= 9) return '初中';
  if (g >= 10) return '高中';
  const c = String(t.chapter || '');
  if (/高[一二三]|必修|选必|选择性必修/.test(c)) return '高中';
  if (/[七八九]年级|初[一二三]/.test(c)) return '初中';
  if (/[一二三四五六]年级/.test(c)) return '小学';
  return '';
}

/* 年级文字：1–9 年级 + 上/下学期；高中章节以「必修」「选必」开头的取该首词（必修一、选必二…），其余 10–12 高一至高三，13 及以上取章节首段。 */
function gradeLabel(t) {
  const g = Number(t.grade);
  if (g >= 1 && g <= 9) {
    const sem = t.semester === '上' || t.semester === '下' ? t.semester + '学期' : '';
    return NUM_ZH[g] + '年级' + sem;
  }
  if (subjectOf(t) === 'chinese' && g >= 10 && g <= 14) {
    return { 10: '必修上', 11: '必修下', 12: '选必上', 13: '选必中', 14: '选必下' }[g];
  }
  const first = String(t.chapter || '').split(/\s+/)[0] || '';
  if (g >= 10 && /^(必修|选必)/.test(first)) return first;
  if (g >= 10 && g <= 12) return '高' + NUM_ZH[g - 9];
  if (g >= 13) return first;
  return '';
}

const kpPath = (id) => '/kp/' + id;
const kpUrl = (id) => ORIGIN + kpPath(id);

function pageShell({ title, description, canonical, ogType, subject, body }) {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(canonical)}">
<meta property="og:type" content="${ogType}">
<meta property="og:site_name" content="中小学·高中知识图谱">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}">
<meta property="og:image" content="${OG_IMAGE}">
<link rel="icon" type="image/png" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0f6e62">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/kp.css">
</head>
<body class="page-kp${subject && subject !== 'math' ? ' subject-' + subject : ''}">
<header class="site-header">
  <a class="brand" href="/">
    <svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><path fill="var(--logo-sheet)" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" d="M6.6 4.8H17L27.4 15.2V25Q27.4 27.4 25.2 27.4H6.6Q4.4 27.4 4.4 25.2V7Q4.4 4.8 6.6 4.8Z"/><path fill="var(--logo-fold)" d="M17.7 6.3 26.1 14.7H17.7Z"/><path fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" d="M17.7 6.3V14.7H26.1"/><path fill="none" stroke="currentColor" stroke-width="2.15" stroke-linecap="round" stroke-linejoin="round" d="M8.3 24.2H12.4Q14.2 24.2 14.2 22.4V20.2Q14.2 18.6 16 18.6H18.8"/><path fill="currentColor" d="M18.5 16.85 23 18.6 18.5 20.35Z"/></svg>
    <span class="brand-copy">
      <span class="brand-name">中小学·高中知识图谱</span>
      <span class="brand-kicker">知识点索引</span>
    </span>
  </a>
  <nav class="site-nav" aria-label="主导航">
    <div class="page-links">
      <a class="nav-link" href="/">首页</a>
      <a class="nav-link" href="/explore/">知识图谱</a>
      <a class="nav-link" href="/diagnose/">诊断</a>
      <a class="nav-link" href="/children/">档案</a>
      <a class="nav-link" href="/wrongbook/">错题本</a>
      <a class="nav-link" href="/goods/">学习好物</a>
      <a class="nav-link active" href="/kp/" aria-current="page">知识点索引</a>
    </div>
  </nav>
</header>
<main class="kp">
${body}
</main>
<footer class="site-footer">
  <p><a href="/kp/">返回知识点索引</a> · <a href="/">返回首页</a></p>
</footer>
</body>
</html>
`;
}

function breadcrumb(items) {
  const parts = items.map((it, i) => (it.href && i < items.length - 1
    ? `<a href="${esc(it.href)}">${esc(it.text)}</a>`
    : `<span aria-current="page">${esc(it.text)}</span>`));
  return `<nav class="kp-crumb" aria-label="面包屑">${parts.join('<span class="sep" aria-hidden="true">/</span>')}</nav>`;
}

function topicPage(t, ctx) {
  const subject = subjectOf(t);
  const subjectName = SUBJECT_NAME[subject];
  const stage = stageOf(t);
  const grade = gradeLabel(t);
  const title = `${t.name}｜${subjectName}${grade}知识点讲解与自测 - ${SITE_TITLE}`;
  const description = truncate(t.description, 110);
  const canonical = kpUrl(t.id);

  const info = [subjectName, stage, grade, t.domain ? '领域 ' + t.domain : '', t.chapter].filter(Boolean);
  const sections = [];

  sections.push(`<section class="kp-sec"><h2>学什么</h2><p>${esc(t.description)}</p></section>`);

  const criteria = Array.isArray(t.mastery_criteria) ? t.mastery_criteria.filter(Boolean) : [];
  if (criteria.length) {
    sections.push(`<section class="kp-sec"><h2>掌握标准</h2><ul>${criteria.map((c) => `<li>${esc(c)}</li>`).join('')}</ul></section>`);
  }

  const dq = t.diagnostic_question;
  if (dq && dq.question) {
    const answer = dq.answer != null && String(dq.answer) !== ''
      ? `<details><summary>查看答案</summary><p>${esc(dq.answer)}</p></details>` : '';
    sections.push(`<section class="kp-sec"><h2>自测一题</h2><p class="kp-q">${esc(dq.question)}</p>${answer}</section>`);
  }

  if (t.root_reason) {
    sections.push(`<section class="kp-sec"><h2>常见卡点</h2><p>${esc(t.root_reason)}</p></section>`);
  }

  const pre = ctx.pre.get(t.id) || [];
  if (pre.length) {
    const items = pre.map((e) => {
      const p = ctx.byId.get(e.prerequisiteId);
      const reason = e.reason || `学习「${t.name}」需要先掌握「${p.name}」。`;
      return `<li><a href="${kpPath(p.id)}">${esc(p.name)}</a><span class="kp-reason">${esc(reason)}</span></li>`;
    });
    sections.push(`<section class="kp-sec"><h2>先修知识点</h2><ul class="kp-links">${items.join('')}</ul></section>`);
  }

  const post = ctx.post.get(t.id) || [];
  if (post.length) {
    const items = post.map((id) => {
      const n = ctx.byId.get(id);
      return `<li><a href="${kpPath(n.id)}">${esc(n.name)}</a></li>`;
    });
    sections.push(`<section class="kp-sec"><h2>学完这个之后</h2><ul class="kp-links kp-plain">${items.join('')}</ul></section>`);
  }

  const n = ctx.qcount.get(t.id) || 0;
  const diag = subject === 'math'
    ? `/diagnose/?target=${t.id}`
    : `/diagnose/?subject=${subject}&target=${t.id}`;
  const practice = n > 0
    ? `本站共有 ${n} 道「${esc(t.name)}」的配套题。`
    : `「${esc(t.name)}」暂无题库配套题，可直接进入诊断，系统会沿先修关系为你出题。`;
  sections.push(`<section class="kp-sec"><h2>配套练习</h2><p>${practice}</p><p><a class="btn btn-lg" href="${esc(diag)}">开始诊断自测</a></p></section>`);

  const body = `${breadcrumb([
    { text: '首页', href: '/' }, { text: '知识点索引', href: '/kp/' },
    { text: subjectName, href: '/kp/' + subject }, { text: t.name }
  ])}
<h1>${esc(t.name)}</h1>
<p class="kp-info">${info.map(esc).join(' · ')}</p>
${sections.join('\n')}`;
  return pageShell({ title, description, canonical, ogType: 'article', subject, body });
}

function subjectPage(subject, topics) {
  const name = SUBJECT_NAME[subject];
  const title = `${name}知识点索引（共 ${topics.length} 个）- ${SITE_TITLE}`;
  const description = `${name}全部 ${topics.length} 个知识点，按年级和教材章节排列，每个知识点都有讲解、掌握标准、自测题与先修关系。`;
  const groups = new Map();
  for (const t of topics) {
    const g = Number.isFinite(Number(t.grade)) && t.grade != null ? Number(t.grade) : 99;
    const key = g + '|' + (t.semester || '');
    if (!groups.has(key)) groups.set(key, { g, sem: t.semester || '', label: gradeLabel(t) || '其他', chapters: new Map() });
    const grp = groups.get(key);
    const ch = t.chapter || '其他';
    if (!grp.chapters.has(ch)) grp.chapters.set(ch, []);
    grp.chapters.get(ch).push(t);
  }
  const ordered = [...groups.values()].sort((a, b) => a.g - b.g || (SEMESTER_ORDER[a.sem] ?? 9) - (SEMESTER_ORDER[b.sem] ?? 9));
  const html = ordered.map((grp) => {
    const chapters = [...grp.chapters.entries()].map(([ch, list]) =>
      `<h3>${esc(ch)}</h3><ul class="kp-grid">${list.map((t) => `<li><a href="${kpPath(t.id)}">${esc(t.name)}</a></li>`).join('')}</ul>`).join('\n');
    return `<section class="kp-sec"><h2>${esc(grp.label)}</h2>\n${chapters}</section>`;
  }).join('\n');
  const body = `${breadcrumb([{ text: '首页', href: '/' }, { text: '知识点索引', href: '/kp/' }, { text: name }])}
<h1>${esc(name)}知识点索引</h1>
<p class="kp-info">共 ${topics.length} 个知识点，按年级与教材章节排列</p>
${html}`;
  return pageShell({ title, description, canonical: ORIGIN + '/kp/' + subject, ogType: 'website', subject, body });
}

function indexPage(counts) {
  const total = SUBJECTS.reduce((s, [k]) => s + counts[k], 0);
  const title = `知识点索引｜中小学全学科知识点讲解与自测 - ${SITE_TITLE}`;
  const description = `覆盖数学、语文、英语等 ${SUBJECTS.length} 个学科共 ${total} 个知识点，每个知识点附讲解、掌握标准、自测题和先修关系。`;
  const cards = SUBJECTS.map(([k, name]) =>
    `<li><a class="kp-card" href="/kp/${k}"><strong>${esc(name)}</strong><span>${counts[k]} 个知识点</span></a></li>`).join('\n');
  const body = `${breadcrumb([{ text: '首页', href: '/' }, { text: '知识点索引' }])}
<h1>知识点索引</h1>
<p class="kp-info">${SUBJECTS.length} 个学科，共 ${total} 个知识点。选一个学科，查看按年级和章节排列的全部知识点。</p>
<ul class="kp-cards">
${cards}
</ul>`;
  return pageShell({ title, description, canonical: ORIGIN + '/kp/', ogType: 'website', subject: '', body });
}

function sitemapXml(entries) {
  const rows = entries.map(([loc, pri]) => `  <url><loc>${esc(loc)}</loc><priority>${pri}</priority></url>`);
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rows.join('\n')}\n</urlset>\n`;
}

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
}

function main() {
  const { out } = parseArgs(process.argv.slice(2));
  const topics = readJson('data/topics.json');
  const deps = readJson('data/dependencies.json');
  const questions = readJson('data/questions.json');

  const byId = new Map(topics.map((t) => [t.id, t]));
  if (byId.size !== topics.length) throw new Error('topics.json 含重复 id');

  const pre = new Map();
  const post = new Map();
  let edges = 0;
  for (const e of deps) {
    if (!byId.has(e.topicId) || !byId.has(e.prerequisiteId)) continue;
    edges++;
    if (!pre.has(e.topicId)) pre.set(e.topicId, []);
    pre.get(e.topicId).push(e);
    if (!post.has(e.prerequisiteId)) post.set(e.prerequisiteId, new Set());
    post.get(e.prerequisiteId).add(e.topicId);
  }
  for (const [k, set] of post) post.set(k, [...set].sort());

  const qcount = new Map();
  for (const q of questions) qcount.set(q.topicId, (qcount.get(q.topicId) || 0) + 1);

  const ctx = { byId, pre, post, qcount };
  const bySubject = Object.fromEntries(SUBJECTS.map(([k]) => [k, []]));
  for (const t of topics) bySubject[subjectOf(t)].push(t);
  const counts = Object.fromEntries(SUBJECTS.map(([k]) => [k, bySubject[k].length]));

  for (const t of topics) write(path.join(out, 'kp', t.id + '.html'), topicPage(t, ctx));
  write(path.join(out, 'kp', 'index.html'), indexPage(counts));
  for (const [k] of SUBJECTS) write(path.join(out, 'kp', k + '.html'), subjectPage(k, bySubject[k]));

  const entries = [
    ...MAIN_PAGES.map(([p, pri]) => [ORIGIN + p, pri]),
    [ORIGIN + '/kp/', '0.9'],
    ...SUBJECTS.map(([k]) => [ORIGIN + '/kp/' + k, '0.9']),
    ...topics.map((t) => [kpUrl(t.id), '0.8'])
  ];
  const skipped = [];
  if (fs.existsSync(path.join(ROOT, 'sitemap.xml'))) skipped.push('sitemap.xml');
  else write(path.join(out, 'sitemap.xml'), sitemapXml(entries));
  if (fs.existsSync(path.join(ROOT, 'robots.txt'))) skipped.push('robots.txt');
  else write(path.join(out, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${ORIGIN}/sitemap.xml\n`);

  const withPre = [...pre.keys()].length;
  const withPost = [...post.keys()].length;
  console.log(`知识点页：${topics.length}`);
  console.log('各学科：' + SUBJECTS.map(([k, n]) => `${n} ${counts[k]}`).join('、'));
  console.log(`先修边：${edges}/${deps.length} 条已索引；有先修的知识点 ${withPre}，有后续的知识点 ${withPost}`);
  console.log(`学科索引页：${SUBJECTS.length}；sitemap URL：${entries.length}`);
  if (skipped.length) console.log('仓库根目录已有，未生成：' + skipped.join('、'));
  console.log('输出目录：' + out);
}

main();
