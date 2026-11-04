/* 孩子档案页：添加、编辑、删除孩子，切换当前孩子。数据来自 assets/children.js（localStorage）。 */
(function () {
  'use strict';
  var CC = window.CnmChildren;
  var listBox = document.getElementById('list');
  var form = document.getElementById('form');
  var nameIn = document.getElementById('f-name');
  var gradeSel = document.getElementById('f-grade');
  var bookSel = document.getElementById('f-book');
  var errBox = document.getElementById('f-error');
  var submitBtn = document.getElementById('f-submit');
  var cancelBtn = document.getElementById('f-cancel');
  var formTitle = document.getElementById('form-title');
  var exportBtn = document.getElementById('export-backup');
  var exportStatus = document.getElementById('export-status');
  var importFile = document.getElementById('import-backup');
  var importPreview = document.getElementById('import-preview');
  var importError = document.getElementById('import-error');
  var importStatus = document.getElementById('import-status');
  var confirmImport = document.getElementById('confirm-import');
  var pendingBackup = null;
  var pendingPreview = null;
  var fileRequest = 0;
  var editing = null;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function fillSelect(sel, items, placeholder) {
    sel.textContent = '';
    if (placeholder) { var o = el('option', null, placeholder); o.value = ''; sel.appendChild(o); }
    items.forEach(function (x) { var o = el('option', null, x); o.value = x; sel.appendChild(o); });
  }
  fillSelect(gradeSel, CC.GRADES, '请选择年级');
  fillSelect(bookSel, CC.TEXTBOOKS);

  var params = new URLSearchParams(location.search);
  if (params.get('from') === 'diagnose') {
    var back = document.getElementById('back');
    var sub = params.get('subject');
    var href = '../diagnose/' + (sub === 'english' || sub === 'physics' || sub === 'chinese' || sub === 'science' || sub === 'morality' || sub === 'history' || sub === 'geography' || sub === 'biology' || sub === 'chemistry' ? '?subject=' + sub : '');
    var a = el('a', null, '← 回到诊断');
    a.href = href;
    back.appendChild(a);
    back.hidden = false;
  }

  function showError(msg) { errBox.textContent = msg || ''; errBox.hidden = !msg; }

  function resetForm() {
    editing = null;
    nameIn.value = '';
    gradeSel.value = '';
    bookSel.value = CC.TEXTBOOKS[0];
    formTitle.textContent = '添加孩子';
    submitBtn.textContent = '添加孩子';
    cancelBtn.hidden = true;
    showError('');
  }

  function startEdit(c) {
    editing = c.id;
    nameIn.value = c.name;
    gradeSel.value = c.grade;
    bookSel.value = c.textbook;
    formTitle.textContent = '修改「' + c.name + '」的信息';
    submitBtn.textContent = '保存修改';
    cancelBtn.hidden = false;
    showError('');
    document.getElementById('form-card').scrollIntoView({ block: 'center' });
    nameIn.focus();
  }

  function stats(c) {
    var recs = CC.recordsOf(c.id);
    var by = CC.latestStatus(c.id);
    var weak = 0;
    Object.keys(by).forEach(function (id) { if (by[id].status === 'weak') weak++; });
    return { runs: recs.length, weak: weak };
  }

  function card(c, isCurrent) {
    var st = stats(c);
    var art = el('article', 'kid-card' + (isCurrent ? ' is-current' : ''));
    var head = el('div', 'kid-head');
    head.appendChild(el('h3', null, c.name));
    if (isCurrent) head.appendChild(el('span', 'kid-badge', '当前'));
    art.appendChild(head);
    art.appendChild(el('p', 'kid-meta', c.grade + ' · ' + c.textbook));
    art.appendChild(el('p', 'kid-stat', st.runs
      ? '已诊断 ' + st.runs + ' 次，目前有 ' + st.weak + ' 个薄弱知识点'
      : '还没有诊断记录'));
    var row = el('div', 'kid-actions');
    if (!isCurrent) {
      var use = el('button', 'primary', '设为当前');
      use.type = 'button';
      use.addEventListener('click', function () { CC.setCurrent(c.id); render(); });
      row.appendChild(use);
    }
    var hist = el('a', 'btn', '盲区与历史');
    hist.href = 'history.html?child=' + encodeURIComponent(c.id);
    row.appendChild(hist);
    var edit = el('button', null, '编辑');
    edit.type = 'button';
    edit.addEventListener('click', function () { startEdit(c); });
    row.appendChild(edit);
    var del = el('button', 'danger', '删除');
    del.type = 'button';
    del.addEventListener('click', function () {
      if (!confirm('删除「' + c.name + '」的档案和全部诊断记录？删除后无法恢复。')) return;
      CC.remove(c.id);
      if (editing === c.id) resetForm();
      render();
    });
    row.appendChild(del);
    art.appendChild(row);
    return art;
  }

  function render() {
    var kids = CC.list();
    var cur = CC.current();
    exportBtn.disabled = !kids.length;
    exportStatus.hidden = true;
    listBox.textContent = '';
    if (!kids.length) {
      listBox.appendChild(el('p', 'kid-empty', '还没有孩子。在下面填昵称和年级，添加第一个。'));
    } else {
      kids.forEach(function (c) { listBox.appendChild(card(c, !!cur && cur.id === c.id)); });
    }
    var full = kids.length >= CC.MAX_CHILDREN && !editing;
    document.getElementById('form-card').hidden = full;
    if (full) {
      var note = el('p', 'muted small', '已经建满 ' + CC.MAX_CHILDREN + ' 个孩子。要添加新的，先删除不用的档案。');
      listBox.appendChild(note);
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var f = { name: nameIn.value, grade: gradeSel.value, textbook: bookSel.value };
    var res = editing ? CC.update(editing, f) : CC.add(f);
    if (!res.ok) { showError(res.error); return; }
    if (!editing && window.cnmTrack) window.cnmTrack('child_added');
    resetForm();
    render();
  });
  cancelBtn.addEventListener('click', function () { resetForm(); render(); });

  function clearImport(keepFile) {
    fileRequest++;
    pendingBackup = null;
    pendingPreview = null;
    if (keepFile !== true) importFile.value = '';
    importPreview.hidden = true;
    importError.hidden = true;
    importStatus.hidden = true;
    confirmImport.disabled = true;
  }
  function showImportError(error) {
    importError.textContent = (error && error.message) || '导入失败，档案未改变。';
    importError.hidden = false;
  }
  function previewBackup(backup) {
    var preview = CC.previewImport(backup);
    pendingBackup = backup;
    pendingPreview = preview;
    document.getElementById('import-summary').textContent =
      '新增 ' + preview.addedChildren + ' 个孩子，合并 ' + preview.matchedChildren + ' 个已有档案；' +
      '新增 ' + preview.addedRecords + ' 条记录，更新 ' + preview.updatedRecords + ' 条记录。';
    var children = document.getElementById('import-children');
    children.textContent = '';
    preview.children.forEach(function (c) {
      var action = c.action === 'rename' ? '同名档案，将改名为「' + c.name + '」' : c.action === 'merge' ? '合并到已有档案' : '新增档案';
      children.appendChild(el('li', null, c.sourceName + '：' + action + '，合并后 ' + c.records + ' 条记录'));
    });
    importPreview.hidden = false;
    confirmImport.disabled = false;
  }
  importFile.addEventListener('change', function () {
    var file = importFile.files[0];
    clearImport(true);
    if (!file) return;
    var request = fileRequest;
    if (file.size > CC.MAX_BACKUP_BYTES) { importFile.value = ''; showImportError(new Error('备份文件不能超过 10 MB。')); return; }
    importStatus.textContent = '正在读取备份文件…';
    importStatus.hidden = false;
    file.text().then(function (text) {
      if (request !== fileRequest) return;
      importStatus.hidden = true;
      previewBackup(CC.parseBackup(text));
    }).catch(function (error) {
      if (request !== fileRequest) return;
      importStatus.hidden = true;
      importFile.value = '';
      showImportError(error);
    });
  });
  document.getElementById('cancel-import').addEventListener('click', clearImport);
  confirmImport.addEventListener('click', function () {
    if (!pendingBackup || !pendingPreview) return;
    confirmImport.disabled = true;
    importError.hidden = true;
    try {
      var result = CC.importBackup(pendingBackup, pendingPreview.token);
      clearImport();
      resetForm();
      render();
      importStatus.textContent = '导入完成：新增 ' + result.addedChildren + ' 个孩子，合并 ' + result.matchedChildren +
        ' 个已有档案，新增 ' + result.addedRecords + ' 条记录，更新 ' + result.updatedRecords + ' 条记录。';
      importStatus.hidden = false;
    } catch (error) {
      // 失败后重新计算预览，防止其他页面的修改让旧预览失效。
      try { previewBackup(pendingBackup); }
      catch (previewError) { pendingPreview = null; importPreview.hidden = true; }
      showImportError(error);
    }
  });

  exportBtn.addEventListener('click', function () {
    var url = null;
    var link = null;
    try {
      var backup = CC.exportBackup();
      var blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json;charset=utf-8' });
      url = URL.createObjectURL(blob);
      link = el('a');
      link.href = url;
      link.download = 'children-backup-' + backup.exportedAt.replace(/[:.]/g, '-') + '.json';
      document.body.appendChild(link);
      link.click();
      exportStatus.className = 'small';
      exportStatus.textContent = '已生成备份文件，请在浏览器下载列表中查看。';
    } catch (e) {
      exportStatus.className = 'small err';
      exportStatus.textContent = (e && e.message) || '导出失败，请重试。';
    } finally {
      if (link) link.remove();
      // 给浏览器时间接管下载，再释放临时地址。
      if (url) setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      exportStatus.hidden = false;
    }
  });

  resetForm();
  render();
})();
