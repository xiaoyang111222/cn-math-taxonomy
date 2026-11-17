/* 历史与薄弱点页：某个孩子的诊断记录，以及按最新结果汇总的薄弱 / 不稳知识点（链到知识图谱）。 */
(function () {
  'use strict';
  var CC = window.CnmChildren;
  var picker = document.getElementById('picker');
  var content = document.getElementById('content');
  var SUBJECTS = [['', '全部'], ['math', '数学'], ['english', '英语'], ['physics', '物理']];
  var SUBJECT_NAME = { math: '数学', english: '英语', physics: '物理' };
  var topics = null;
  var childId = null;
  var subjectSel = '';

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function subjectOfId(id) {
    id = String(id || '');
    return id.indexOf('cne_') === 0 ? 'english' : id.indexOf('cnp_') === 0 ? 'physics' : 'math';
  }
  function exploreHref(id) {
    var sub = subjectOfId(id);
    return '../explore/' + (sub === 'math' ? '' : '?subject=' + sub) + '#' + encodeURIComponent(id);
  }
  function pad(n) { return ('0' + n).slice(-2); }
  function fmt(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }
  function nameOf(id) { return topics && topics[id] ? topics[id].name : id; }
  function chapterOf(id) { return topics && topics[id] && topics[id].chapter ? topics[id].chapter : ''; }
  function tag(cls, text) { return el('span', 'kid-tag ' + cls, text); }

  function practiceHref(id) {
    var sub = subjectOfId(id);
    return '../practice/?target=' + encodeURIComponent(id) + (sub === 'math' ? '' : '&subject=' + sub);
  }
  function retestHref(ids) { return '../diagnose/?target=' + ids.map(encodeURIComponent).join(','); }

  function topicRow(id, info) {
    var li = el('li', 'wk-item');
    var top = el('div', 'wk-top');
    var a = el('a', 'wk-name', nameOf(id));
    a.href = exploreHref(id);
    top.appendChild(a);
    top.appendChild(tag(info.status === 'weak' ? 'weak' : 'shaky', info.status === 'weak' ? '薄弱' : '不稳'));
    if (info.root) top.appendChild(tag('root', '根因'));
    top.appendChild(tag('sub', SUBJECT_NAME[subjectOfId(id)]));
    li.appendChild(top);
    var meta = [];
    var ch = chapterOf(id);
    if (ch) meta.push(ch);
    meta.push(fmt(info.at) + (info.practiced ? ' 巩固练习' : ' 诊断'));
    li.appendChild(el('p', 'wk-meta', meta.join(' · ')));
    var re = el('a', 'wk-retest', '再测一次');
    re.href = retestHref([id]);
    li.appendChild(re);
    var pr = el('a', 'wk-retest wk-practice', '去巩固过关（3连对）');
    pr.href = practiceHref(id);
    li.appendChild(pr);
    return li;
  }

  function weakSection(child) {
    var by = CC.latestStatus(child.id, subjectSel || null);
    var ids = Object.keys(by).filter(function (id) { return by[id].status === 'weak' || by[id].status === 'shaky'; });
    var rank = function (id) { return (by[id].status === 'weak' ? 0 : 2) + (by[id].root ? 0 : 1); };
    ids.sort(function (a, b) {
      return rank(a) - rank(b) || ((topics && topics[a] && topics[a].grade) || 99) - ((topics && topics[b] && topics[b].grade) || 99) || String(by[b].at).localeCompare(String(by[a].at));
    });
    var sec = el('section', 'kid-section');
    var weakN = ids.filter(function (id) { return by[id].status === 'weak'; }).length;
    sec.appendChild(el('h2', null, '现在还薄弱的知识点'));
    if (!CC.recordsOf(child.id).length) {
      sec.appendChild(el('p', 'kid-empty', '还没有诊断记录。做完一次诊断，薄弱点会汇总在这里。'));
      return sec;
    }
    if (!ids.length) {
      sec.appendChild(el('p', 'kid-empty', '按最近的诊断结果，没有薄弱或不稳的知识点。'));
      return sec;
    }
    sec.appendChild(el('p', 'muted small', '同一个知识点测过好几次，以最近一次为准。薄弱 ' + weakN + ' 个，不稳 ' + (ids.length - weakN) + ' 个。点名称进知识图谱看先修和学习内容。'));
    var ul = el('ul', 'wk-list');
    ids.forEach(function (id) { ul.appendChild(topicRow(id, by[id])); });
    sec.appendChild(ul);
    return sec;
  }

  function recordCard(child, r) {
    var det = el('details', 'rec');
    var sum = el('summary');
    var line1 = el('div', 'rec-top');
    line1.appendChild(tag('sub', SUBJECT_NAME[r.subject] || '数学'));
    line1.appendChild(el('b', 'rec-label', r.label || '诊断'));
    sum.appendChild(line1);
    var c = r.counts || {};
    var line2 = el('div', 'rec-counts');
    line2.appendChild(el('span', 'rec-date', fmt(r.savedAt)));
    line2.appendChild(tag('weak', '薄弱 ' + (c.weak || 0)));
    line2.appendChild(tag('shaky', '不稳 ' + (c.shaky || 0)));
    line2.appendChild(tag('ok', '掌握 ' + (c.mastered || 0)));
    if (c.untested) line2.appendChild(tag('unk', '未测 ' + c.untested));
    sum.appendChild(line2);
    det.appendChild(sum);

    var body = el('div', 'rec-body');
    body.appendChild(el('p', 'muted small', '共答 ' + (r.asked || 0) + ' 题' + (r.mode === 'screen' ? '，整体筛查' : '') + '。'));
    var rootSet = {};
    (r.roots || []).forEach(function (id) { rootSet[id] = true; });
    var group = function (title, ids, status) {
      if (!ids || !ids.length) return;
      body.appendChild(el('h4', null, title + '（' + ids.length + '）'));
      var ul = el('ul', 'rec-topics');
      ids.forEach(function (id) {
        var li = el('li');
        var a = el('a', null, nameOf(id));
        a.href = exploreHref(id);
        li.appendChild(a);
        if (status === 'weak' && rootSet[id]) li.appendChild(tag('root', '根因'));
        ul.appendChild(li);
      });
      body.appendChild(ul);
    };
    group('薄弱', r.weak, 'weak');
    group('不稳', r.shaky, 'shaky');
    if (!(r.weak || []).length && !(r.shaky || []).length) body.appendChild(el('p', 'kid-empty', '这次没有发现薄弱或不稳的知识点。'));

    var row = el('div', 'rec-actions');
    if (r.targets && r.targets.length) {
      var re = el('a', 'btn', '再测一次');
      re.href = retestHref(r.targets);
      row.appendChild(re);
    }
    var del = el('button', 'danger', '删除这条记录');
    del.type = 'button';
    del.addEventListener('click', function () {
      if (!confirm('删除这条诊断记录？')) return;
      CC.removeRecord(child.id, r.key);
      render();
    });
    row.appendChild(del);
    body.appendChild(row);
    det.appendChild(body);
    return det;
  }

  function recordsSection(child) {
    var recs = CC.recordsOf(child.id).filter(function (r) { return !subjectSel || r.subject === subjectSel; });
    var sec = el('section', 'kid-section');
    sec.appendChild(el('h2', null, '诊断记录（' + recs.length + '）'));
    if (!recs.length) {
      sec.appendChild(el('p', 'kid-empty', subjectSel ? '这个学科还没有记录。' : '还没有诊断记录。'));
    } else {
      recs.forEach(function (r) { sec.appendChild(recordCard(child, r)); });
    }
    var go = el('a', 'btn btn-primary', '去做一次诊断');
    go.href = '../diagnose/' + (subjectSel === 'english' || subjectSel === 'physics' ? '?subject=' + subjectSel : '');
    sec.appendChild(go);
    return sec;
  }

  function renderPicker(kids) {
    picker.textContent = '';
    if (!kids.length) return;
    var label = el('label', null, '孩子');
    label.setAttribute('for', 'kid-select');
    var sel = el('select');
    sel.id = 'kid-select';
    kids.forEach(function (c) {
      var o = el('option', null, c.name + '（' + c.grade + '）');
      o.value = c.id;
      sel.appendChild(o);
    });
    sel.value = childId;
    sel.addEventListener('change', function () {
      childId = sel.value;
      CC.setCurrent(childId);
      history.replaceState(null, '', location.pathname + '?child=' + encodeURIComponent(childId));
      render();
    });
    var manage = el('a', 'btn', '管理档案');
    manage.href = './';
    picker.appendChild(label);
    picker.appendChild(sel);
    picker.appendChild(manage);
  }

  function renderTabs() {
    var row = el('div', 'stage-tabs kid-tabs');
    row.setAttribute('role', 'tablist');
    row.setAttribute('aria-label', '学科');
    SUBJECTS.forEach(function (s) {
      var b = el('button', 'stage-tab' + (subjectSel === s[0] ? ' on' : ''), s[1]);
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', subjectSel === s[0] ? 'true' : 'false');
      b.addEventListener('click', function () { subjectSel = s[0]; render(); });
      row.appendChild(b);
    });
    return row;
  }

  function render() {
    var kids = CC.list();
    renderPicker(kids);
    content.textContent = '';
    if (!kids.length) {
      content.appendChild(el('p', 'kid-empty', '还没有孩子档案。先添加孩子，诊断结果才会按孩子保存。'));
      var add = el('a', 'btn btn-primary', '去添加孩子');
      add.href = './';
      content.appendChild(add);
      return;
    }
    var child = CC.get(childId) || kids[0];
    childId = child.id;
    var head = el('p', 'kid-meta', child.name + ' · ' + child.grade + ' · ' + child.textbook);
    content.appendChild(head);
    content.appendChild(renderTabs());
    content.appendChild(weakSection(child));
    content.appendChild(recordsSection(child));
  }

  function init() {
    var kids = CC.list();
    var want = new URLSearchParams(location.search).get('child');
    var cur = CC.current();
    childId = (want && CC.get(want) && want) || (cur && cur.id) || (kids[0] && kids[0].id) || null;
    if (!kids.length) { render(); return; }
    fetch('../data/topics.json').then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (rows) {
      topics = {};
      rows.forEach(function (t) { topics[t.id] = t; });
    }).catch(function () { topics = null; }).then(render);
  }
  init();
})();
