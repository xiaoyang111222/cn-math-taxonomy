/* 错题本页：按孩子查看诊断时答错 / 不会的题，可删除、清空，并打印成重做练习页。数据来自 assets/wrongbook.js（localStorage）。 */
(function () {
  'use strict';
  var CC = window.CnmChildren;
  var CW = window.CnmWrong;
  var GUEST = CW.GUEST;
  var SUBJECT_NAME = CW.SUBJECT_NAME;
  var picker = document.getElementById('picker');
  var content = document.getElementById('content');
  var childId = GUEST;
  var subjectSel = '';
  var answersShown = false;
  var flash = '';
  var revealed = {};

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pad(n) { return ('0' + n).slice(-2); }
  function fmt(ts) {
    var d = new Date(ts);
    if (isNaN(d)) return '';
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function subjectName(key) { return SUBJECT_NAME[key] || key || '数学'; }
  function childName() {
    var c = childId !== GUEST ? CC.get(childId) : null;
    return c ? c.name : '';
  }

  function renderPicker(kids) {
    picker.textContent = '';
    var guestN = CW.count(GUEST);
    if (!kids.length && !guestN) return;
    if (kids.length) {
      var label = el('label', null, '孩子');
      label.setAttribute('for', 'kid-select');
      var sel = el('select');
      sel.id = 'kid-select';
      kids.forEach(function (c) {
        var o = el('option', null, c.name + '（' + c.grade + '）');
        o.value = c.id;
        sel.appendChild(o);
      });
      if (guestN) {
        var g = el('option', null, '未建档时收集的（' + guestN + '）');
        g.value = GUEST;
        sel.appendChild(g);
      }
      sel.value = childId;
      sel.addEventListener('change', function () {
        childId = sel.value;
        subjectSel = '';
        flash = '';
        revealed = {};
        if (childId !== GUEST) CC.setCurrent(childId);
        history.replaceState(null, '', location.pathname + (childId !== GUEST ? '?child=' + encodeURIComponent(childId) : ''));
        render();
      });
      picker.appendChild(label);
      picker.appendChild(sel);
    }
    var manage = el('a', 'btn', '管理档案');
    manage.href = '../children/';
    picker.appendChild(manage);
  }

  function toolbar(total, shown, subjects) {
    var bar = el('div', 'wb-bar no-print');
    bar.appendChild(el('span', 'wb-total', subjectSel
      ? '共 ' + total + ' 题，当前显示 ' + shown + ' 题'
      : '共 ' + total + ' 题'));

    var lab = el('label', 'wb-field', '学科');
    lab.setAttribute('for', 'wb-subject');
    var sel = el('select');
    sel.id = 'wb-subject';
    var all = el('option', null, '全部');
    all.value = '';
    sel.appendChild(all);
    subjects.forEach(function (s) {
      var o = el('option', null, subjectName(s));
      o.value = s;
      sel.appendChild(o);
    });
    sel.value = subjectSel;
    sel.addEventListener('change', function () { subjectSel = sel.value; render(); });
    bar.appendChild(lab);
    bar.appendChild(sel);

    var print = el('button', 'primary', '打印练习页');
    print.type = 'button';
    print.id = 'wb-print';
    print.disabled = !shown;
    print.addEventListener('click', function () { window.print(); });
    bar.appendChild(print);

    var withAns = el('label', 'wb-check');
    var cb = el('input');
    cb.type = 'checkbox';
    cb.id = 'wb-print-answers';
    cb.checked = document.body.classList.contains('print-answers');
    cb.addEventListener('change', function () { document.body.classList.toggle('print-answers', cb.checked); });
    withAns.appendChild(cb);
    withAns.appendChild(document.createTextNode(' 打印时附答案'));
    bar.appendChild(withAns);

    var clr = el('button', 'danger', '清空错题本');
    clr.type = 'button';
    clr.id = 'wb-clear';
    clr.addEventListener('click', function () {
      var who = childName();
      if (!confirm('清空' + (who ? '「' + who + '」的' : '') + '错题本里的全部 ' + total + ' 道题？清空后无法恢复。')) return;
      CW.clear(childId);
      subjectSel = '';
      render();
    });
    bar.appendChild(clr);
    return bar;
  }

  function badge(cls, text) { return el('span', 'wb-tag ' + cls, text); }

  function nextDateText(e) {
    var d = new Date(CW.dueAtOf(e));
    return (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日';
  }

  function doReview(e, passed) {
    var updated = CW.review(childId, e.qid, passed, Date.now());
    if (updated && passed && window.CnmActivity) window.CnmActivity.mark(childId, Date.now());
    delete revealed[e.qid];
    if (!updated) flash = '没能保存复测结果，请稍后再试。';
    else if (updated.done) flash = '答对了，这道题已毕业 ✓';
    else if (passed) flash = '答对了，下次复测 ' + nextDateText(updated) + '。';
    else flash = '没答对，明天再测一次。正确答案：' + e.answer;
    render();
  }

  function dueCard(e, no) {
    var art = el('article', 'wb-card wb-due-card');
    var head = el('div', 'wb-q');
    head.appendChild(el('span', 'wb-no', no + '.'));
    head.appendChild(el('span', 'wb-prompt', e.prompt));
    art.appendChild(head);
    art.appendChild(el('p', 'wb-due-meta', subjectName(e.subject) + ' · ' + (e.topic || '') + ' · ' + CW.reviewLabel(e, Date.now())));

    if (e.choices && e.choices.length) {
      var right = CW.answerKey(e);
      var ul = el('ul', 'wb-due-choices');
      e.choices.forEach(function (c) {
        var li = el('li');
        var b = el('button', 'wb-due-choice', c.key + '. ' + c.text);
        b.type = 'button';
        b.addEventListener('click', function () { doReview(e, c.key === right); });
        li.appendChild(b);
        ul.appendChild(li);
      });
      art.appendChild(ul);
      return art;
    }

    var box = el('div', 'wb-due-self');
    if (!revealed[e.qid]) {
      var show = el('button', null, '显示答案');
      show.type = 'button';
      show.addEventListener('click', function () { revealed[e.qid] = true; render(); });
      box.appendChild(show);
    } else {
      box.appendChild(el('p', 'wb-line wb-right', '正确答案：' + e.answer));
      if (e.explanation) box.appendChild(el('p', 'wb-line wb-explain', '解析：' + e.explanation));
      var ok = el('button', 'primary', '会了');
      ok.type = 'button';
      ok.addEventListener('click', function () { doReview(e, true); });
      var no2 = el('button', null, '还没会');
      no2.type = 'button';
      no2.addEventListener('click', function () { doReview(e, false); });
      var row = el('div', 'wb-due-actions');
      row.appendChild(ok);
      row.appendChild(no2);
      box.appendChild(row);
    }
    art.appendChild(box);
    return art;
  }

  function dueSection(due) {
    var sec = el('section', 'wb-due no-print');
    sec.id = 'wb-due';
    sec.appendChild(el('h2', null, '今日待复测（' + due.length + ' 题）'));
    sec.appendChild(el('p', 'muted', '答错的题隔 1、3、7、15 天各回头测一次，连续答对四轮就算毕业；没答对会明天再测。'));
    due.forEach(function (e, i) { sec.appendChild(dueCard(e, i + 1)); });
    return sec;
  }

  function questionCard(e, no) {
    var art = el('article', 'wb-card');
    var head = el('div', 'wb-q');
    head.appendChild(el('span', 'wb-no', no + '.'));
    head.appendChild(el('span', 'wb-prompt', e.prompt));
    art.appendChild(head);

    if (e.choices && e.choices.length) {
      var ul = el('ul', 'wb-choices');
      e.choices.forEach(function (c) { ul.appendChild(el('li', null, c.key + '. ' + c.text)); });
      art.appendChild(ul);
    }
    art.appendChild(el('div', 'wb-write'));

    var info = el('div', 'wb-info no-print');
    var tags = el('div', 'wb-tags');
    tags.appendChild(badge(e.kind === 'skip' ? 'skip' : 'wrong', e.kind === 'skip' ? '不会' : '答错'));
    tags.appendChild(badge('count', '答错 ' + (e.count || 1) + ' 次'));
    tags.appendChild(badge(e.done ? 'done' : (CW.isDue(e, Date.now()) ? 'due' : 'later'), CW.reviewLabel(e, Date.now())));
    tags.appendChild(el('span', 'wb-date', fmt(e.ts)));
    info.appendChild(tags);
    info.appendChild(el('p', 'wb-line', e.kind === 'skip' ? '孩子选的：（点了「不会」）' : '孩子选的：' + (e.chosen || '（空）')));
    info.appendChild(el('p', 'wb-line wb-right', '正确答案：' + e.answer));
    if (e.explanation) info.appendChild(el('p', 'wb-line wb-explain', '解析：' + e.explanation));
    var del = el('button', 'danger small', '删除');
    del.type = 'button';
    del.addEventListener('click', function () { CW.remove(childId, e.qid); render(); });
    info.appendChild(del);
    art.appendChild(info);
    return art;
  }

  function groupRows(rows) {
    var order = [];
    var by = {};
    rows.forEach(function (e) {
      var k = e.subject + '|' + (e.topicId || e.topic);
      if (!by[k]) { by[k] = { subject: e.subject, topic: e.topic || e.topicId, rows: [] }; order.push(k); }
      by[k].rows.push(e);
    });
    return order.map(function (k) { return by[k]; });
  }

  function render() {
    var kids = CC.list();
    if (childId === GUEST && kids.length && !CW.count(GUEST)) {
      var cur = CC.current();
      childId = (cur && cur.id) || kids[0].id;
    }
    renderPicker(kids);
    content.textContent = '';
    if (flash) {
      var note = el('p', 'wb-flash no-print', flash);
      note.setAttribute('role', 'status');
      content.appendChild(note);
      flash = '';
    }
    var all = CW.list(childId);
    if (!kids.length) {
      content.appendChild(el('p', 'kid-empty no-print', '未建孩子档案，按本机记录显示。'));
    }
    if (!all.length) {
      content.appendChild(el('p', 'kid-empty no-print', '还没有错题，去做一次诊断，答错的题会自动收进来。'));
      var go = el('a', 'btn btn-primary no-print', '去做诊断');
      go.href = '../diagnose/';
      content.appendChild(go);
      return;
    }
    var subjects = [];
    all.forEach(function (e) { if (subjects.indexOf(e.subject) < 0) subjects.push(e.subject); });
    if (subjectSel && subjects.indexOf(subjectSel) < 0) subjectSel = '';
    var rows = subjectSel ? all.filter(function (e) { return e.subject === subjectSel; }) : all;
    var slot = el('div', 'cnm-nudge-slot no-print');
    slot.setAttribute('data-nudge', 'wrongbook');
    content.appendChild(slot);
    var due = CW.dueList(childId, Date.now());
    if (due.length) content.appendChild(dueSection(due));
    content.appendChild(toolbar(all.length, rows.length, subjects));

    var who = childName();
    var title = el('div', 'wb-print-title');
    title.appendChild(el('h2', null, '错题重做练习' + (who ? ' · ' + who : '')));
    title.appendChild(el('p', null, (subjectSel ? subjectName(subjectSel) + ' · ' : '') + '共 ' + rows.length + ' 题 · ' + fmt(Date.now()) +
      '　姓名：__________　得分：______'));
    content.appendChild(title);

    var groups = groupRows(rows);
    var no = 0;
    var numbered = [];
    groups.forEach(function (g) {
      var sec = el('section', 'wb-group');
      sec.appendChild(el('h2', 'wb-group-title', subjectName(g.subject) + ' · ' + g.topic));
      g.rows.forEach(function (e) {
        no++;
        numbered.push({ no: no, e: e });
        sec.appendChild(questionCard(e, no));
      });
      content.appendChild(sec);
    });

    var sheet = el('section', 'wb-answers' + (answersShown ? ' shown' : ''));
    sheet.id = 'wb-answers';
    sheet.appendChild(el('h2', null, '参考答案'));
    var ol = el('ul', 'wb-answer-list');
    numbered.forEach(function (n) { ol.appendChild(el('li', null, n.no + '. ' + n.e.answer)); });
    sheet.appendChild(ol);

    var toggle = el('button', 'no-print', answersShown ? '收起参考答案' : '查看参考答案');
    toggle.type = 'button';
    toggle.id = 'wb-toggle-answers';
    toggle.addEventListener('click', function () { answersShown = !answersShown; render(); });
    content.appendChild(el('div', 'wb-answers-toggle no-print')).appendChild(toggle);
    content.appendChild(sheet);
  }

  function init() {
    var kids = CC.list();
    var want = new URLSearchParams(location.search).get('child');
    var cur = CC.current();
    childId = (want && CC.get(want) && want) || (cur && cur.id) || (kids[0] && kids[0].id) || GUEST;
    render();
  }
  init();
})();
