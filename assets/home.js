/* 首页：统计和年级入口都从 data/*.json 计算，不写死数量。 */
(function () {
  'use strict';
  var raw = location.hash.replace(/^#/, '');
  try { raw = decodeURIComponent(raw); } catch (e) { /* 保持原样 */ }
  if (/^(?:cnm|cne|cnp|cnc|cns|cnd|cnh|cng|cnb|cnk)_[A-Za-z0-9]+$/.test(raw)) return;

  var CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  var subjectParam = new URLSearchParams(location.search).get('subject');
  var subject = subjectParam === 'english' || subjectParam === 'physics' || subjectParam === 'chinese' || subjectParam === 'science' || subjectParam === 'morality' || subjectParam === 'history' || subjectParam === 'geography' || subjectParam === 'biology' || subjectParam === 'chemistry' ? subjectParam : 'math';
  var PREFIX = { math: 'cnm_', english: 'cne_', physics: 'cnp_', chinese: 'cnc_', science: 'cns_', morality: 'cnd_', history: 'cnh_', geography: 'cng_', biology: 'cnb_', chemistry: 'cnk_' };
  var STD_PREFIX = { math: 'cms-', english: 'ces-', physics: 'cps-', chinese: 'ccs-', science: 'css-', morality: 'cds-', history: 'chs-', geography: 'cgs-', biology: 'cbs-', chemistry: 'cks-' };

  function withSubject(href) {
    if (subject === 'math' || !href || href.indexOf('subject=') >= 0 || href.indexOf('http') === 0) return href;
    return href + (href.indexOf('?') >= 0 ? '&' : '?') + 'subject=' + subject;
  }

  document.body.classList.toggle('subject-english', subject === 'english');
  document.body.classList.toggle('subject-physics', subject === 'physics');
  document.body.classList.toggle('subject-chinese', subject === 'chinese');
  document.body.classList.toggle('subject-science', subject === 'science');
  document.body.classList.toggle('subject-morality', subject === 'morality');
  document.body.classList.toggle('subject-history', subject === 'history');
  document.body.classList.toggle('subject-geography', subject === 'geography');
  document.body.classList.toggle('subject-biology', subject === 'biology');
  document.body.classList.toggle('subject-chemistry', subject === 'chemistry');
  document.querySelectorAll('.subject-link').forEach(function (link) {
    var on = link.getAttribute('data-subject') === subject;
    link.classList.toggle('on', on);
    if (on) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
  document.querySelectorAll('.site-nav a:not(.subject-link), a.brand').forEach(function (link) {
    var href = link.getAttribute('href');
    var next = withSubject(href);
    if (next && next !== href) link.setAttribute('href', next);
  });
  if (subject === 'english') {
    document.title = '英语 · 中小学·高中知识图谱';
    var eye = document.querySelector('.eyebrow');
    if (eye) eye.textContent = '英语：三年级到高中';
    var primary = document.querySelector('.hero-actions a.btn-primary');
    var browse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (primary) primary.setAttribute('href', 'diagnose/?subject=english');
    if (browse) browse.setAttribute('href', 'explore/?subject=english');
    var demo = document.querySelector('.quiet-link a');
    if (demo) {
      demo.setAttribute('href', 'diagnose/?subject=english&grade=' + encodeURIComponent('四上') + '&demo=1');
      demo.textContent = '先看一遍演示：四年级上册英语';
    }
  } else if (subject === 'physics') {
    document.title = '物理 · 中小学·高中知识图谱';
    var peye = document.querySelector('.eyebrow');
    if (peye) peye.textContent = '物理：初中八、九年级 · 高中必修与选择性必修';
    var pprimary = document.querySelector('.hero-actions a.btn-primary');
    var pbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (pprimary) pprimary.setAttribute('href', 'diagnose/?subject=physics');
    if (pbrowse) pbrowse.setAttribute('href', 'explore/?subject=physics');
    var pdemo = document.querySelector('.quiet-link a');
    if (pdemo) {
      pdemo.setAttribute('href', 'diagnose/?subject=physics&grade=' + encodeURIComponent('八上') + '&demo=1');
      pdemo.textContent = '先看一遍演示：八年级上册物理';
    }
  } else if (subject === 'chinese') {
    document.title = '小学语文 · 中小学·高中知识图谱';
    var zeye = document.querySelector('.eyebrow');
    if (zeye) zeye.textContent = '语文：小学一至六年级 · 统编版';
    var zprimary = document.querySelector('.hero-actions a.btn-primary');
    var zbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (zprimary) zprimary.setAttribute('href', 'diagnose/?subject=chinese');
    if (zbrowse) zbrowse.setAttribute('href', 'explore/?subject=chinese');
    var zdemo = document.querySelector('.quiet-link a');
    if (zdemo) {
      zdemo.setAttribute('href', 'diagnose/?subject=chinese&grade=' + encodeURIComponent('一上') + '&demo=1');
      zdemo.textContent = '先看一遍演示：一年级上册语文';
    }
  } else if (subject === 'science') {
    document.title = '小学科学 · 中小学·高中知识图谱';
    var seye = document.querySelector('.eyebrow');
    if (seye) seye.textContent = '科学：小学一至六年级 · 教科版';
    var sprimary = document.querySelector('.hero-actions a.btn-primary');
    var sbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (sprimary) sprimary.setAttribute('href', 'diagnose/?subject=science');
    if (sbrowse) sbrowse.setAttribute('href', 'explore/?subject=science');
    var sdemo = document.querySelector('.quiet-link a');
    if (sdemo) {
      sdemo.setAttribute('href', 'diagnose/?subject=science&grade=' + encodeURIComponent('一上') + '&demo=1');
      sdemo.textContent = '先看一遍演示：一年级上册科学';
    }
  } else if (subject === 'morality') {
    document.title = '小学道德与法治 · 中小学·高中知识图谱';
    var meye = document.querySelector('.eyebrow');
    if (meye) meye.textContent = '道德与法治：小学一至六年级 · 统编版';
    var mprimary = document.querySelector('.hero-actions a.btn-primary');
    var mbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (mprimary) mprimary.setAttribute('href', 'diagnose/?subject=morality');
    if (mbrowse) mbrowse.setAttribute('href', 'explore/?subject=morality');
    var mdemo = document.querySelector('.quiet-link a');
    if (mdemo) {
      mdemo.setAttribute('href', 'diagnose/?subject=morality&grade=' + encodeURIComponent('一上') + '&demo=1');
      mdemo.textContent = '先看一遍演示：一年级上册道德与法治';
    }
  } else if (subject === 'history') {
    document.title = '初中历史 · 中小学·高中知识图谱';
    var heye = document.querySelector('.eyebrow');
    if (heye) heye.textContent = '历史：初中七至九年级 · 统编版';
    var hprimary = document.querySelector('.hero-actions a.btn-primary');
    var hbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (hprimary) hprimary.setAttribute('href', 'diagnose/?subject=history');
    if (hbrowse) hbrowse.setAttribute('href', 'explore/?subject=history');
    var hdemo = document.querySelector('.quiet-link a');
    if (hdemo) {
      hdemo.setAttribute('href', 'diagnose/?subject=history&grade=' + encodeURIComponent('七上') + '&demo=1');
      hdemo.textContent = '先看一遍演示：七年级上册历史';
    }
  } else if (subject === 'geography') {
    document.title = '初中地理 · 中小学·高中知识图谱';
    var geye = document.querySelector('.eyebrow');
    if (geye) geye.textContent = '地理：初中七至八年级 · 人教版';
    var gprimary = document.querySelector('.hero-actions a.btn-primary');
    var gbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (gprimary) gprimary.setAttribute('href', 'diagnose/?subject=geography');
    if (gbrowse) gbrowse.setAttribute('href', 'explore/?subject=geography');
    var gdemo = document.querySelector('.quiet-link a');
    if (gdemo) {
      gdemo.setAttribute('href', 'diagnose/?subject=geography&grade=' + encodeURIComponent('七上') + '&demo=1');
      gdemo.textContent = '先看一遍演示：七年级上册地理';
    }
  } else if (subject === 'biology') {
    document.title = '初中生物 · 中小学·高中知识图谱';
    var beye = document.querySelector('.eyebrow');
    if (beye) beye.textContent = '生物：初中七至八年级 · 人教版';
    var bprimary = document.querySelector('.hero-actions a.btn-primary');
    var bbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (bprimary) bprimary.setAttribute('href', 'diagnose/?subject=biology');
    if (bbrowse) bbrowse.setAttribute('href', 'explore/?subject=biology');
    var bdemo = document.querySelector('.quiet-link a');
    if (bdemo) {
      bdemo.setAttribute('href', 'diagnose/?subject=biology&grade=' + encodeURIComponent('七上') + '&demo=1');
      bdemo.textContent = '先看一遍演示：七年级上册生物';
    }
  } else if (subject === 'chemistry') {
    document.title = '化学 · 中小学·高中知识图谱';
    var ceye = document.querySelector('.eyebrow');
    if (ceye) ceye.textContent = '化学：初中九年级 · 人教版';
    var cprimary = document.querySelector('.hero-actions a.btn-primary');
    var cbrowse = document.querySelector('.hero-actions a.btn:not(.btn-primary)');
    if (cprimary) cprimary.setAttribute('href', 'diagnose/?subject=chemistry');
    if (cbrowse) cbrowse.setAttribute('href', 'explore/?subject=chemistry');
    var cdemo = document.querySelector('.quiet-link a');
    if (cdemo) {
      cdemo.setAttribute('href', 'diagnose/?subject=chemistry&grade=' + encodeURIComponent('九上') + '&demo=1');
      cdemo.textContent = '先看一遍演示：九年级上册化学';
    }
  }

  function setText(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function fail(message) {
    var box = document.getElementById('load-error');
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
      var bits = [row.status === 'weak' ? (row.root ? '根因' : '薄弱') : '不稳'];
      if (row.wrongs) bits.push('答错 ' + row.wrongs + ' 次');
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

  Promise.all([
    fetch('data/topics.json'),
    fetch('data/dependencies.json'),
    fetch('data/questions.json'),
    fetch('data/cn-curriculum-standards.json')
  ]).then(function (responses) {
    responses.forEach(function (response, index) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
    });
    return Promise.all(responses.map(function (response) { return response.json(); }));
  }).then(function (data) {
    var allTopics = data[0];
    var topics = data[0];
    var deps = data[1];
    var questions = data[2];
    var standards = data[3];
    if (!Array.isArray(topics) || !Array.isArray(deps) || !Array.isArray(questions)) {
      throw new Error('数据格式无法识别');
    }
    var items = standards && Array.isArray(standards.items) ? standards.items : [];
    function subjectOfId(id) {
      id = String(id || '');
      if (id.indexOf('cne_') === 0) return 'english';
      if (id.indexOf('cnp_') === 0) return 'physics';
      if (id.indexOf('cnc_') === 0) return 'chinese';
      if (id.indexOf('cns_') === 0) return 'science';
      if (id.indexOf('cnd_') === 0) return 'morality';
      if (id.indexOf('cnh_') === 0) return 'history';
      if (id.indexOf('cng_') === 0) return 'geography';
      if (id.indexOf('cnb_') === 0) return 'biology';
      if (id.indexOf('cnk_') === 0) return 'chemistry';
      return 'math';
    }
    function subjectOfStd(id) {
      id = String(id || '');
      if (id.indexOf('ces-') === 0) return 'english';
      if (id.indexOf('cps-') === 0) return 'physics';
      if (id.indexOf('ccs-') === 0) return 'chinese';
      if (id.indexOf('css-') === 0) return 'science';
      if (id.indexOf('cds-') === 0) return 'morality';
      if (id.indexOf('chs-') === 0) return 'history';
      if (id.indexOf('cgs-') === 0) return 'geography';
      if (id.indexOf('cbs-') === 0) return 'biology';
      if (id.indexOf('cks-') === 0) return 'chemistry';
      return 'math';
    }
    var wantEnglish = subject === 'english';
    var wantPhysics = subject === 'physics';
    var wantChinese = subject === 'chinese' || subject === 'science' || subject === 'morality';
    var wantHistory = subject === 'history';
    var wantGeography = subject === 'geography';
    var wantBiology = subject === 'biology';
    var wantChemistry = subject === 'chemistry';
    topics = topics.filter(function (topic) { return (topic.subject || subjectOfId(topic.id)) === subject; });
    deps = deps.filter(function (edge) { return subjectOfId(edge.topicId) === subject; });
    questions = questions.filter(function (question) { return subjectOfId(question.topicId) === subject; });
    items = items.filter(function (item) { return subjectOfStd(item.id) === subject; });
    setText('n-topics', String(topics.length));
    setText('n-edges', String(deps.length));
    setText('n-questions', String(questions.length));
    setText('n-standards', String(items.length));

    var grades = document.getElementById('grades');
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
    var from = wantPhysics ? 8 : (wantEnglish ? 3 : (wantChemistry ? 9 : (wantHistory || wantGeography || wantBiology ? 7 : 1)));
    var to = wantChinese ? 6 : (wantChemistry ? 9 : (wantGeography || wantBiology ? 8 : 9));
    for (var g = from; g <= to; g++) {
      var list = topics.filter(function (topic) { return topic.grade === g; });
      var up = list.filter(function (topic) { return topic.semester === '上'; }).length;
      var down = list.filter(function (topic) { return topic.semester === '下'; }).length;
      var whole = list.filter(function (topic) { return topic.semester === '全'; }).length;
      var splitText = whole ? '全一册 ' + whole : '上 ' + up + ' · 下 ' + down;
      var href = subject !== 'math' ? 'explore/?subject=' + subject + '&grade=' + g : 'explore/?grade=' + g;
      addCard(g, g <= 6 ? '小学' : (wantPhysics ? '初中物理' : '初中'), CN[g] + '年级', g <= 6 ? 'is-primary' : 'is-junior', splitText, href);
    }
    if (wantChinese) {
      /* 小学语文、小学科学、小学道德与法治只到六年级 */
    } else if (wantHistory) {
      /* 初中历史只到九年级 */
    } else if (wantGeography) {
      /* 初中地理只到八年级 */
    } else if (wantBiology) {
      /* 初中生物只到八年级，九年级没有生物课 */
    } else if (wantChemistry) {
      /* 初中化学只开九年级，没有小学、七八年级和高中卡片 */
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
