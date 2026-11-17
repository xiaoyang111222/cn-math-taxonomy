/* 班级热力图（children/classroom.html）。
 * 纯函数（Node 里可 require）：anonName(i)、aggregate(students, topicsById, subject) -> {columns, rows, topRoots}
 * 浏览器里：读 CnmChildren 的全部孩子 -> latestStatus -> 画热力图和全班高频薄弱根因 Top 5。 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else { root.CnmClassroom = api; if (typeof document !== 'undefined') api.boot(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const MATHEMATICIANS = ['阿基米德', '欧几里得', '毕达哥拉斯', '祖冲之', '刘徽', '高斯', '欧拉', '牛顿', '莱布尼茨', '费马',
    '笛卡尔', '帕斯卡', '黎曼', '希尔伯特', '诺特', '拉格朗日', '柯西', '华罗庚', '陈景润', '秦九韶',
    '杨辉', '贾宪', '张丘建', '海伦', '托勒密', '斐波那契', '阿贝尔', '伽罗瓦', '图灵', '冯·诺依曼'];

  /** 第 i 个学生（从 0 开始）的匿名代号：「阿基米德 #1」……超过 30 个就轮回，编号继续递增。 */
  function anonName(i) { return MATHEMATICIANS[i % MATHEMATICIANS.length] + ' #' + (i + 1); }

  const STATUS_RANK = { weak: 0, shaky: 1, mastered: 2 };

  /**
   * students：[{id, name, status: {topicId: {status, root}}}]（status 即 CnmChildren.latestStatus 的结果）
   * topicsById：{id: topic}（用来排序和过滤学科）；subject：'math' / 'english' / 'physics' / null
   * 返回：
   *   columns：出现过的知识点，按年级、再按 topics 文件顺序（topicsById 的插入顺序）；
   *   rows：[{id, name, cells: [status|'unknown'], weak, shaky, mastered}]；
   *   topRoots：全班高频薄弱根因 Top 5：[{id, rootCount, weakCount, students:[name]}]，
   *             先按“被判为根因的学生数”，再按“薄弱的学生数”排序。
   */
  function aggregate(students, topicsById, subject) {
    const order = Object.create(null);
    Object.keys(topicsById || {}).forEach(function (id, i) { order[id] = i; });
    const subjectOf = function (id) { return /^cne_/.test(id) ? 'english' : /^cnp_/.test(id) ? 'physics' : 'math'; };
    const hasTopics = !!topicsById && Object.keys(topicsById).length > 0;
    const keep = function (id) { return (!subject || subjectOf(id) === subject) && (!hasTopics || topicsById[id]); };
    const seen = Object.create(null);
    const tally = Object.create(null);
    students.forEach(function (s) {
      Object.keys(s.status || {}).forEach(function (id) {
        if (!keep(id)) return;
        seen[id] = true;
        const st = s.status[id];
        if (st.status !== 'weak') return;
        const t = tally[id] || (tally[id] = { id: id, rootCount: 0, weakCount: 0, students: [] });
        t.weakCount++;
        if (st.root) t.rootCount++;
        t.students.push(s.name);
      });
    });
    const grade = function (id) { const t = topicsById && topicsById[id]; return t && t.grade != null ? t.grade : 99; };
    const columns = Object.keys(seen).sort(function (a, b) {
      return grade(a) - grade(b) || (order[a] == null ? 1e9 : order[a]) - (order[b] == null ? 1e9 : order[b]) || (a < b ? -1 : 1);
    });
    const rows = students.map(function (s) {
      const cells = columns.map(function (id) { const st = s.status && s.status[id]; return st && STATUS_RANK[st.status] != null ? st.status : 'unknown'; });
      const count = function (k) { return cells.filter(function (c) { return c === k; }).length; };
      return { id: s.id, name: s.name, cells: cells, weak: count('weak'), shaky: count('shaky'), mastered: count('mastered') };
    });
    const topRoots = Object.keys(tally).map(function (id) { return tally[id]; })
      .sort(function (a, b) { return b.rootCount - a.rootCount || b.weakCount - a.weakCount || grade(a.id) - grade(b.id); })
      .slice(0, 5);
    return { columns: columns, rows: rows, topRoots: topRoots };
  }

  /* ------------------------------------------------------------ 浏览器 */
  function boot() {
    const CC = window.CnmChildren;
    const ANON_KEY = 'cnmClassroom.anon.v1';
    const SUBJECTS = [['math', '数学'], ['english', '英语'], ['physics', '物理']];
    let subject = 'math';
    let topics = {};
    const $ = function (id) { return document.getElementById(id); };
    function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
    function anonOn() { try { return localStorage.getItem(ANON_KEY) === '1'; } catch (e) { return false; } }
    function setAnon(v) { try { localStorage.setItem(ANON_KEY, v ? '1' : '0'); } catch (e) { /* ignore */ } }
    function sub(href) { return subject === 'math' ? href : href + (href.indexOf('?') >= 0 ? '&' : '?') + 'subject=' + subject; }
    function exploreHref(id) { return sub('../explore/') + '#' + encodeURIComponent(id); }
    function demoHref(id) { return sub('../diagnose/?target=' + encodeURIComponent(id) + '&demo=1'); }
    function nameOf(id) { return topics[id] ? topics[id].name : id; }
    const STATUS_TEXT = { mastered: '已掌握', shaky: '不稳', weak: '薄弱', unknown: '没测过' };

    function tabs() {
      const box = $('subject-tabs');
      box.textContent = '';
      SUBJECTS.forEach(function (s) {
        const b = el('button', 'stage-tab' + (s[0] === subject ? ' on' : ''), s[1]);
        b.type = 'button';
        b.setAttribute('role', 'tab');
        b.setAttribute('aria-selected', s[0] === subject ? 'true' : 'false');
        b.addEventListener('click', function () { subject = s[0]; render(); });
        box.appendChild(b);
      });
    }

    function render() {
      tabs();
      const anon = anonOn();
      $('anon').checked = anon;
      const kids = CC.list();
      const students = kids.map(function (c, i) {
        return { id: c.id, name: anon ? anonName(i) : c.name, status: CC.latestStatus(c.id, subject) };
      });
      const agg = aggregate(students, topics, subject);

      const top = $('top-roots');
      top.textContent = '';
      top.appendChild(el('h2', null, '全班高频薄弱根因 Top 5'));
      if (!kids.length) top.appendChild(el('p', 'kid-empty', '这台设备上还没有孩子档案。'));
      else if (!agg.topRoots.length) top.appendChild(el('p', 'kid-empty', '按最近的诊断，全班在这个学科没有薄弱知识点。'));
      else {
        const ol = el('ol', 'cls-top');
        agg.topRoots.forEach(function (r) {
          const li = el('li');
          const a = el('a', 'cls-top-name', nameOf(r.id));
          a.href = exploreHref(r.id);
          li.appendChild(a);
          li.appendChild(el('span', 'muted small', '　' + r.rootCount + ' 人是根因、' + r.weakCount + ' 人薄弱' + (topics[r.id] && topics[r.id].chapter ? ' · ' + topics[r.id].chapter : '')));
          const links = el('div', 'cls-top-links');
          const g = el('a', 'btn btn-small', '知识图谱'); g.href = exploreHref(r.id);
          const d = el('a', 'btn btn-small', '课堂演示'); d.href = demoHref(r.id); d.title = '用演示学生走一遍诊断回溯，适合投屏讲解';
          links.appendChild(g); links.appendChild(d);
          li.appendChild(links);
          li.title = '薄弱的学生：' + r.students.join('、');
          ol.appendChild(li);
        });
        top.appendChild(ol);
      }

      const box = $('heatmap');
      box.textContent = '';
      if (!agg.columns.length) { box.appendChild(el('p', 'kid-empty', '还没有这个学科的诊断记录。')); return; }
      const table = el('table', 'cls-table');
      const thead = el('thead');
      const hr = el('tr');
      hr.appendChild(el('th', 'cls-corner', '学生'));
      agg.columns.forEach(function (id) {
        const th = el('th', 'cls-col');
        const a = el('a', null, nameOf(id));
        a.href = exploreHref(id);
        a.title = nameOf(id) + (topics[id] && topics[id].chapter ? '（' + topics[id].chapter + '）' : '');
        th.appendChild(a);
        hr.appendChild(th);
      });
      thead.appendChild(hr);
      table.appendChild(thead);
      const tb = el('tbody');
      agg.rows.forEach(function (r) {
        const tr = el('tr');
        const th = el('th', 'cls-name', r.name);
        th.title = '薄弱 ' + r.weak + '，不稳 ' + r.shaky + '，已掌握 ' + r.mastered;
        tr.appendChild(th);
        r.cells.forEach(function (c, j) {
          const td = el('td');
          const i = el('i', 'cls-cell ' + c);
          td.title = r.name + ' · ' + nameOf(agg.columns[j]) + '：' + STATUS_TEXT[c];
          td.appendChild(i);
          tr.appendChild(td);
        });
        tb.appendChild(tr);
      });
      table.appendChild(tb);
      box.appendChild(table);
    }

    $('anon').addEventListener('change', function (e) { setAnon(e.target.checked); render(); });
    fetch('../data/topics.json').then(function (r) { return r.ok ? r.json() : []; }).then(function (rows) {
      topics = {};
      rows.forEach(function (t) { topics[t.id] = t; });
    }).catch(function () { topics = {}; }).then(render);
  }

  return { anonName: anonName, aggregate: aggregate, boot: boot, MATHEMATICIANS: MATHEMATICIANS };
});
