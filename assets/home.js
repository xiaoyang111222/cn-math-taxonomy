/* 首页：知识点 / 先修关系 / 题数 / 学科数都从 data 文件现算，不写死；年级入口按当前学科画。
 * 首屏不拉题库：题数只读 data/questions/index.json（几百字节）。 */
(function () {
  'use strict';
  var raw = location.hash.replace(/^#/, '');
  try { raw = decodeURIComponent(raw); } catch (e) { /* 保持原样 */ }
  if (/^(?:cnm|cne|cnp|cnc|cns|cnd|cnh|cng|cnb|cnk|cnz)_[A-Za-z0-9]+$/.test(raw)) return;

  var CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  var SUBJECT_KEYS = ['math', 'english', 'physics', 'chinese', 'science', 'morality', 'history', 'geography', 'biology', 'chemistry', 'politics'];
  var subjectParam = new URLSearchParams(location.search).get('subject');
  var subject = SUBJECT_KEYS.indexOf(subjectParam) >= 0 ? subjectParam : 'math';
  /* 非数学学科：页面标题、眉标、演示入口（年级用 diagnose 的册次写法）。数学是默认页，沿用 index.html 里的静态内容。 */
  var SUBJECT_META = {
    english: { name: '英语', demo: '四上', demoText: '看演示：四年级上册英语' },
    physics: { name: '物理', demo: '八上', demoText: '看演示：八年级上册物理' },
    chinese: { name: '语文', demo: '一上', demoText: '看演示：一年级上册语文' },
    science: { name: '小学科学', demo: '一上', demoText: '看演示：一年级上册科学' },
    morality: { name: '道德与法治', demo: '一上', demoText: '看演示：一年级上册道德与法治' },
    history: { name: '历史', demo: '七上', demoText: '看演示：七年级上册历史' },
    geography: { name: '地理', demo: '七上', demoText: '看演示：七年级上册地理' },
    biology: { name: '生物', demo: '七上', demoText: '看演示：七年级上册生物' },
    chemistry: { name: '化学', demo: '九上', demoText: '看演示：九年级上册化学' },
    politics: { name: '思想政治', demo: '必修一', demoText: '看演示：必修一 中国特色社会主义' }
  };

  function $(id) { return document.getElementById(id); }

  function withSubject(href) {
    if (subject === 'math' || !href || href.indexOf('subject=') >= 0 || href.indexOf('http') === 0) return href;
    return href + (href.indexOf('?') >= 0 ? '&' : '?') + 'subject=' + subject;
  }

  SUBJECT_KEYS.forEach(function (key) {
    if (key !== 'math') document.body.classList.toggle('subject-' + key, subject === key);
  });
  document.querySelectorAll('.subject-link, .pill').forEach(function (link) {
    var on = link.getAttribute('data-subject') === subject;
    link.classList.toggle('on', on);
    if (on) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
  document.querySelectorAll('.site-nav a:not(.subject-link), a.brand, a.entry-card').forEach(function (link) {
    var href = link.getAttribute('href');
    var next = withSubject(href);
    if (next && next !== href) link.setAttribute('href', next);
  });
  var meta = SUBJECT_META[subject];
  if (meta) {
    document.title = meta.name + ' · 中小学·高中知识图谱';
    var eye = document.querySelector('.eyebrow');
    if (eye) eye.textContent = meta.name + ' · 知识图谱 · 查漏补缺';
    var start = $('hero-start');
    if (start) start.setAttribute('href', 'diagnose/?subject=' + subject);
    var demo = $('hero-demo');
    if (demo) {
      demo.setAttribute('href', 'diagnose/?subject=' + subject + '&grade=' + encodeURIComponent(meta.demo) + '&demo=1');
      demo.textContent = meta.demoText;
    }
    var art = document.querySelector('.hero-art');
    if (art) art.hidden = true;
  }

  var more = $('pill-more');
  var morePanel = $('subject-more');
  if (more && morePanel && more.addEventListener) {
    more.addEventListener('click', function () {
      var open = morePanel.hidden;
      morePanel.hidden = !open;
      more.setAttribute('aria-expanded', open ? 'true' : 'false');
      more.textContent = open ? '收起' : '展开';
    });
  }

  function moralityJuniorEyebrow(topicList) {
    var vols = [
      [7, '上', '七上'], [7, '下', '七下'],
      [8, '上', '八上'], [8, '下', '八下'],
      [9, '上', '九上'], [9, '下', '九下']
    ];
    var has = {};
    (topicList || []).forEach(function (topic) {
      if (topic.grade >= 7 && topic.grade <= 9 && (topic.semester === '上' || topic.semester === '下')) {
        has[String(topic.grade) + topic.semester] = true;
      }
    });
    var present = [];
    vols.forEach(function (row) {
      if (has[String(row[0]) + row[1]]) present.push(row[2]);
    });
    var junior = present.length ? ('初中现含' + present.join('、')) : '初中册次尚未录入';
    var g9note = '九年级未录入';
    if (has['9上'] && has['9下']) g9note = '九年级上下册均已录入';
    else if (has['9上']) g9note = '九下未录入';
    else if (has['9下']) g9note = '九上未录入';
    return '统编版：小学与初中 · 只列出已录入册次（' + junior + '；' + g9note + '）';
  }

  function setText(id, value) {
    var node = $(id);
    if (node) node.textContent = value;
  }

  function fmt(n) { return Number(n).toLocaleString('en-US'); }

  /* 「今日学习」卡：登录用户一张卡汇总当前孩子（站内 active child，没有则 guest 桶）——错题待复测、今日英语一句、
   * 到期旧句复习、连续学习天数；没登录时，当前桶有英语 / 打卡进度也显示（游客版）。什么都没有就整张隐藏，不占位。
   * 待复测数沿用第一批口径：全部孩子（含 guest）合计，分散在多个孩子名下时标「（全部孩子合计）」。 */
  function loggedIn() {
    try {
      if (window.CnmAccount && window.CnmAccount.isLoggedIn) return !!window.CnmAccount.isLoggedIn();
      var s = JSON.parse(localStorage.getItem('cnmAuth.v1'));
      return !!(s && typeof s.token === 'string' && Number(s.exp) > Date.now());
    } catch (e) { return false; }
  }
  function setHidden(id, hidden) {
    var node = $(id);
    if (node) node.hidden = !!hidden;
  }
  function currentBucket() {
    try {
      var cur = window.CnmChildren && window.CnmChildren.current && window.CnmChildren.current();
      return cur && cur.id ? cur.id : 'guest';
    } catch (e) { return 'guest'; }
  }
  function renderDueHome() {
    var box = $('due-home');
    if (!box) return;
    var bucket = currentBucket();
    var login = loggedIn();
    var en = null, streak = 0, hasProgress = false;
    try {
      if (window.CnmEnglish && window.CnmEnglish.todayState) {
        en = window.CnmEnglish.todayState(bucket, Date.now());
        hasProgress = en.doneCount > 0;
      }
    } catch (e) { en = null; }
    try {
      if (window.CnmActivity && window.CnmActivity.streak) {
        streak = window.CnmActivity.streak(bucket, Date.now());
        if (window.CnmActivity.hasAny && window.CnmActivity.hasAny(bucket)) hasProgress = true;
      }
    } catch (e) { streak = 0; }
    var show = login || hasProgress;
    var n = 0, spread = false;
    try {
      if (show && window.CnmWrong && window.CnmWrong.dueTotal) {
        n = window.CnmWrong.dueTotal(Date.now());
        spread = n > 0 && !!window.CnmWrong.dueBuckets && window.CnmWrong.dueBuckets(Date.now()) > 1;
      }
    } catch (e) { n = 0; spread = false; }
    if (n > 0) setText('due-home-n', String(n));
    setHidden('due-home-all', !spread);
    setHidden('due-home-line', !(n > 0));
    setHidden('today-en-line', !en);
    if (en) {
      setText('today-en-state', en.finished ? '30 句已学完' : (en.completedToday ? '已完成' : '未学'));
      var rn = en.reviewTotal || 0;
      if (rn > 0) setText('today-en-review-n', String(rn));
      setHidden('today-en-review', !(rn > 0));
    }
    if (streak > 0) setText('today-streak-n', String(streak));
    setHidden('today-streak-line', !(streak > 0));
    box.hidden = !show;
  }
  renderDueHome();
  if (window.addEventListener) {
    window.addEventListener('cnm:auth', renderDueHome);
    window.addEventListener('cnm:sync', renderDueHome);
    window.addEventListener('pageshow', renderDueHome);
  }

  function fail(message) {
    var box = $('load-error');
    if (!box) return;
    box.hidden = false;
    box.textContent = message;
  }

  function renderBlindHome(allTopics) {
    var box = document.getElementById('blind-home');
    var list = document.getElementById('blind-home-list');
    var actions = document.getElementById('blind-home-actions');
    if (!box || !list || !actions || !window.CnmBlind) return;
    var nameOf = {};
    (allTopics || []).forEach(function (t) { nameOf[t.id] = t.name; });
    var rows = window.CnmBlind.list({ subject: subject, limit: 8 });
    if (!rows.length) {
      box.hidden = true;
      list.replaceChildren();
      actions.replaceChildren();
      return;
    }
    box.hidden = false;
    list.replaceChildren();
    rows.forEach(function (row) {
      var li = document.createElement('li');
      li.className = 'blind-home-item';
      var name = document.createElement('a');
      name.className = 'blind-home-name';
      name.href = window.CnmBlind.diagnoseHref([row.id], row.subject || subject);
      name.textContent = nameOf[row.id] || row.id;
      li.appendChild(name);
      var meta = document.createElement('span');
      meta.className = 'blind-home-meta';
      var bits = [row.status === 'weak' ? (row.root ? '根因' : '薄弱') : (row.status === 'retest' ? '需重测' : '不稳')];
      if (row.wrongs && row.status !== 'retest') bits.push('答错 ' + row.wrongs + ' 次');
      meta.textContent = bits.join(' · ');
      li.appendChild(meta);
      list.appendChild(li);
    });
    actions.replaceChildren();
    var cur = window.CnmChildren && window.CnmChildren.current && window.CnmChildren.current();
    var all = document.createElement('a');
    all.className = 'btn';
    all.href = window.CnmBlind.historyHref(cur && cur.id, 'children/');
    all.textContent = '查看全部盲区';
    actions.appendChild(all);
    var weakIds = rows.filter(function (r) { return r.status === 'weak'; }).slice(0, 5).map(function (r) { return r.id; });
    if (weakIds.length) {
      var re = document.createElement('a');
      re.className = 'btn btn-primary';
      re.href = window.CnmBlind.diagnoseHref(weakIds, subject);
      re.textContent = '再测本页薄弱点';
      actions.appendChild(re);
    }
  }


  /* 同 URL 最多 2 次尝试；进行中的 Promise 去重。 */
  var fetchInflight = {};
  function fetchJsonWithRetry(url, attempts) {
    attempts = attempts || 2;
    if (fetchInflight[url]) return fetchInflight[url];
    var run = (function tryOnce(left) {
      return fetch(url).then(function (response) {
        if (!response.ok) {
          var httpErr = new Error('HTTP ' + response.status);
          httpErr.noRetry = true;
          throw httpErr;
        }
        return response.json();
      }).catch(function (err) {
        if (err && err.noRetry) throw err;
        if (left > 1) return tryOnce(left - 1);
        throw err;
      });
    })(attempts);
    fetchInflight[url] = run.then(function (data) {
      delete fetchInflight[url];
      return data;
    }, function (err) {
      delete fetchInflight[url];
      throw err;
    });
    return fetchInflight[url];
  }

  var homeLoadToken = subject;
  var PREFIX_SUBJECT = { cnm_: 'math', cne_: 'english', cnp_: 'physics', cnc_: 'chinese', cns_: 'science', cnd_: 'morality', cnh_: 'history', cng_: 'geography', cnb_: 'biology', cnk_: 'chemistry', cnz_: 'politics' };
  function subjectOfId(id) {
    return PREFIX_SUBJECT[String(id || '').slice(0, 4)] || 'math';
  }

  /* 题数：只读索引，不拉任何题目文件；失败只把题数显示成 — */
  fetchJsonWithRetry('data/questions/index.json', 2).then(function (index) {
    if (typeof (index && index.total) !== 'number') throw new Error('数据格式无法识别');
    setText('n-questions', fmt(index.total));
  }).catch(function () {
    setText('n-questions', '—');
  });

  Promise.all([
    fetch('data/topics.json'),
    fetch('data/dependencies.json')
  ]).then(function (responses) {
    responses.forEach(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
    });
    return Promise.all(responses.map(function (response) { return response.json(); }));
  }).then(function (data) {
    if (homeLoadToken !== subject) return;
    var allTopics = data[0];
    var topics = data[0];
    var deps = data[1];
    if (!Array.isArray(topics) || !Array.isArray(deps)) {
      throw new Error('数据格式无法识别');
    }
    var seen = {};
    allTopics.forEach(function (topic) { seen[topic.subject || subjectOfId(topic.id)] = true; });
    setText('n-topics', fmt(allTopics.length));
    setText('n-edges', fmt(deps.length));
    setText('n-subjects', String(Object.keys(seen).length));
    setText('cover-morality', moralityJuniorEyebrow(allTopics.filter(function (topic) { return (topic.subject || subjectOfId(topic.id)) === 'morality'; })));

    var wantEnglish = subject === 'english';
    var wantPhysics = subject === 'physics';
    var wantPrimary = subject === 'science';
    var wantHistory = subject === 'history';
    var wantGeography = subject === 'geography';
    var wantBiology = subject === 'biology';
    var wantChemistry = subject === 'chemistry';
    var wantPolitics = subject === 'politics';
    topics = topics.filter(function (topic) { return (topic.subject || subjectOfId(topic.id)) === subject; });

    var grades = $('grades');
    if (!grades) return;
    grades.replaceChildren();
    grades.removeAttribute('aria-busy');
    function addCard(g, stageName, title, klass, splitText, href) {
      var list = topics.filter(function (topic) { return topic.grade === g; });
      var link = document.createElement('a');
      link.className = 'grade-card ' + klass;
      link.href = href;
      var stage = document.createElement('span');
      stage.className = 'grade-stage';
      stage.textContent = stageName;
      var name = document.createElement('strong');
      name.textContent = title;
      var count = document.createElement('span');
      count.className = 'grade-count';
      count.textContent = list.length + ' 个知识点';
      var split = document.createElement('span');
      split.className = 'grade-stage';
      split.textContent = splitText;
      link.append(stage, name, count, split);
      grades.append(link);
    }
    var from = wantPolitics ? 10 : (wantPhysics ? 8 : (wantEnglish ? 3 : (wantChemistry ? 9 : (wantHistory || wantGeography || wantBiology ? 7 : 1))));
    var to = wantPolitics ? 9 : (wantPrimary ? 6 : (wantChemistry ? 9 : (wantGeography || wantBiology ? 8 : 9)));
    for (var g = from; g <= to; g++) {
      var list = topics.filter(function (topic) { return topic.grade === g; });
      var up = list.filter(function (topic) { return topic.semester === '上'; }).length;
      var down = list.filter(function (topic) { return topic.semester === '下'; }).length;
      var whole = list.filter(function (topic) { return topic.semester === '全'; }).length;
      if (subject === 'morality' && !list.length) continue;
      var splitText = whole ? '全一册 ' + whole : '上 ' + up + ' · 下 ' + down;
      if (subject === 'morality' && !whole) {
        var morParts = [];
        if (up) morParts.push('上 ' + up);
        if (down) morParts.push('下 ' + down);
        splitText = morParts.join(' · ');
      }
      var href = subject !== 'math' ? 'explore/?subject=' + subject + '&grade=' + g : 'explore/?grade=' + g;
      addCard(g, g <= 6 ? '小学' : (wantPhysics ? '初中物理' : '初中'), CN[g] + '年级', g <= 6 ? 'is-primary' : 'is-junior', splitText, href);
    }
    if (wantPrimary || subject === 'morality') {
      /* 道德与法治到九年级且无高中；科学只到六年级。道德与法治空年级不画卡片 */
    } else if (subject === 'chinese') {
      var zhHsTitle = { 10: '必修上', 11: '必修下', 12: '选必上', 13: '选必中', 14: '选必下' };
      [10, 11, 12, 13, 14].forEach(function (g) {
        if (topics.some(function (topic) { return topic.grade === g; })) {
          addCard(g, '高中语文', zhHsTitle[g], 'is-senior', zhHsTitle[g], 'explore/?subject=chinese&grade=' + g);
        }
      });
    } else if (wantHistory || wantGeography || wantBiology) {
      var srName = wantHistory ? '高中历史' : wantGeography ? '高中地理' : '高中生物';
      var srTitle = wantHistory
        ? { 10: '中外历史纲要（上）', 11: '中外历史纲要（下）', 12: '选择性必修第一册', 13: '选择性必修第二册', 14: '选择性必修第三册' }
        : wantGeography
        ? { 10: '必修第一册', 11: '必修第二册', 12: '选择性必修第一册', 13: '选择性必修第二册', 14: '选择性必修第三册' }
        : { 10: '必修1 分子与细胞', 11: '必修2 遗传与进化', 12: '选择性必修1 稳态与调节', 13: '选择性必修2 生物与环境', 14: '选择性必修3 生物技术与工程' };
      var srWord = { 10: '必修一', 11: '必修二', 12: '选必一', 13: '选必二', 14: '选必三' };
      [10, 11, 12, 13, 14].forEach(function (g) {
        if (topics.some(function (topic) { return topic.grade === g; })) {
          addCard(g, srName, srWord[g], 'is-senior', srTitle[g], 'explore/?subject=' + subject + '&grade=' + g);
        }
      });
    } else if (wantPolitics) {
      var polWord = { 10: '必修一', 11: '必修二', 12: '必修三', 13: '必修四', 14: '选必一', 15: '选必二', 16: '选必三' };
      var polTitle = {
        10: '中国特色社会主义', 11: '经济与社会', 12: '政治与法治', 13: '哲学与文化',
        14: '当代国际政治与经济', 15: '法律与生活', 16: '逻辑与思维'
      };
      [10, 11, 12, 13, 14, 15, 16].forEach(function (g) {
        if (topics.some(function (topic) { return topic.grade === g; })) {
          addCard(g, '高中思想政治', polWord[g], 'is-senior', polTitle[g], 'explore/?subject=politics&grade=' + g);
        }
      });
    } else if (wantChemistry) {
      var chemHsB1 = topics.filter(function (topic) { return topic.grade === 10; });
      var chemHsB2 = topics.filter(function (topic) { return topic.grade === 11; });
      if (chemHsB1.length) addCard(10, '高中化学', '必修一', 'is-senior', '必修第一册', 'explore/?subject=chemistry&grade=10');
      if (chemHsB2.length) addCard(11, '高中化学', '必修二', 'is-senior', '必修第二册', 'explore/?subject=chemistry&grade=11');
      var chemHsS1 = topics.filter(function (topic) { return topic.grade === 12; });
      if (chemHsS1.length) addCard(12, '高中化学', '选必一', 'is-senior', '选择性必修第一册', 'explore/?subject=chemistry&grade=12');
      var chemHsS2 = topics.filter(function (topic) { return topic.grade === 13; });
      if (chemHsS2.length) addCard(13, '高中化学', '选必二', 'is-senior', '选择性必修第二册', 'explore/?subject=chemistry&grade=13');
      var chemHsS3 = topics.filter(function (topic) { return topic.grade === 14; });
      if (chemHsS3.length) addCard(14, '高中化学', '选必三', 'is-senior', '选择性必修第三册', 'explore/?subject=chemistry&grade=14');
    } else if (wantPhysics) {
      addCard(10, '高中物理', '必修一', 'is-senior', '必修第一册', 'explore/?subject=physics&grade=10');
      addCard(11, '高中物理', '必修二', 'is-senior', '必修第二册', 'explore/?subject=physics&grade=11');
      addCard(12, '高中物理', '必修三', 'is-senior', '必修第三册', 'explore/?subject=physics&grade=12');
      addCard(13, '高中物理', '选必一', 'is-senior', '选择性必修第一册', 'explore/?subject=physics&grade=13');
      addCard(14, '高中物理', '选必二', 'is-senior', '选择性必修第二册', 'explore/?subject=physics&grade=14');
      addCard(15, '高中物理', '选必三', 'is-senior', '选择性必修第三册', 'explore/?subject=physics&grade=15');
    } else if (wantEnglish) {
      addCard(10, '高中', '必修一', 'is-senior', '必修第一册', 'explore/?subject=english&grade=10');
      addCard(11, '高中', '必修二', 'is-senior', '必修第二册', 'explore/?subject=english&grade=11');
      addCard(12, '高中', '必修三', 'is-senior', '必修第三册', 'explore/?subject=english&grade=12');
      addCard(13, '高中', '选必一', 'is-senior', '选择性必修第一册', 'explore/?subject=english&grade=13');
      addCard(14, '高中', '选必二', 'is-senior', '选择性必修第二册', 'explore/?subject=english&grade=14');
      addCard(15, '高中', '选必三', 'is-senior', '选择性必修第三册', 'explore/?subject=english&grade=15');
      addCard(16, '高中', '选必四', 'is-senior', '选择性必修第四册', 'explore/?subject=english&grade=16');
    } else {
      addCard(10, '高中', '高一', 'is-senior', '必修第一册', 'explore/?grade=10');
      addCard(11, '高中', '高二', 'is-senior', '必修第二册', 'explore/?grade=11');
      addCard(12, '高中', '选必一', 'is-senior', '选择性必修第一册', 'explore/?grade=12');
      addCard(13, '高中', '选必二', 'is-senior', '选择性必修第二册', 'explore/?grade=13');
      addCard(14, '高中', '选必三', 'is-senior', '选择性必修第三册', 'explore/?grade=14');
    }
    renderBlindHome(allTopics);
  }).catch(function (error) {
    fail('数据没有加载成功（' + (error && error.message ? error.message : error) + '）。请在项目根目录运行 python3 -m http.server 8000，再用浏览器打开，不要直接双击 html 文件。');
  });
})();
