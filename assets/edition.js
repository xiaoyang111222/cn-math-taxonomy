/* 教材版本落点投影：把 data/mappings/<version>-<subject>.json 变成内存里的落点表，供诊断页与图谱页共用。
 * 浏览器里是 window.CnmEdition，Node 里 require() 即可。纯函数、无 DOM；调用方负责 fetch 与读写档案。
 * 规则见 docs/hujiao-mapping-plan.md：不改写 topic 对象；没有映射条目的点一律写成「该版本暂未覆盖」，
 * 不退回人教版的 grade / semester / chapter。 */
(function (root, factory) {
  'use strict';
  var api = factory(root);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.CnmEdition = api;
})(typeof window !== 'undefined' ? window : this, function (root) {
  'use strict';

  var RENJIAO = 'renjiao';
  var HUJIAO = 'hujiao';
  var VERSIONS = [RENJIAO, HUJIAO];
  var UNCOVERED = '该版本暂未覆盖';
  var DRAFT_NOTE = '册次依据为草稿';
  var PREP_NOTE = '沪教版的六年级是初中预备年级，小学册次未收录，这里没有六年级的册次。';
  var EMPTY_VOLUME_NOTE = '沪教版这一册暂时没有收录知识点（该版本暂未覆盖）。';
  var BEYOND_PRIMARY_NOTE = '沪教版初中、高中的册次暂未收录（一期只有小学），该版本暂未覆盖。';
  var NUM = ['', '一', '二', '三', '四', '五', '六'];
  var FAR = 1e12;

  function engine() {
    if (root && root.DiagEngine) return root.DiagEngine;
    if (typeof require === 'function') return require('../diagnose/engine.js');
    throw new Error('需要先加载 diagnose/engine.js');
  }

  function semesterOf(term) { return term === 2 ? '下' : '上'; }

  /** 第 grade 年级第 term 学期 -> 诊断已有的册键，如 '三上'。 */
  function volumeKey(grade, term) { return NUM[grade] + semesterOf(term); }

  function volumeTitle(grade, term) { return NUM[grade] + '年级' + (term === 2 ? '下册' : '上册'); }

  /** 映射文件相对站点根目录的路径。一期只有 primary（小学）。 */
  function mappingPath(version, subject, stage) {
    return 'data/mappings/' + version + '-' + subject + (stage && stage !== 'primary' ? '-' + stage : '') + '.json';
  }

  /**
   * 映射文件 -> 落点表 P。entries 的书写顺序就是教学顺序，保留为 order。
   * P.byId[id] = { stage, grade, term, semester, unit, chapter, note, volume, order, unitOrder, covered: true }
   * 不碰任何 topic 对象。
   */
  function buildPlacement(mapping) {
    if (!mapping || typeof mapping !== 'object' || !mapping.entries || typeof mapping.entries !== 'object' || Array.isArray(mapping.entries)) {
      throw new Error('映射文件格式不对');
    }
    var byId = Object.create(null);
    var unitFirst = Object.create(null);
    var order = 0;
    Object.keys(mapping.entries).forEach(function (id) {
      var e = mapping.entries[id];
      var uk = e.grade + '|' + e.term + '|' + e.unit;
      if (unitFirst[uk] === undefined) unitFirst[uk] = order;
      byId[id] = {
        id: id,
        stage: mapping.stage || 'primary',
        grade: e.grade,
        term: e.term,
        semester: semesterOf(e.term),
        unit: e.unit,
        chapter: e.chapter || '',
        note: e.note || '',
        volume: volumeKey(e.grade, e.term),
        order: order,
        unitOrder: unitFirst[uk],
        covered: true
      };
      order++;
    });
    return {
      version: mapping.version,
      subject: mapping.subject,
      stage: mapping.stage || 'primary',
      status: mapping.status || 'draft',
      label: mapping.label || '',
      byId: byId,
      count: order
    };
  }

  /** 拉取并建表。opts: { fetch, base, version, subject, stage }。一期只认 primary。 */
  function load(opts) {
    var o = opts || {};
    var stage = o.stage || 'primary';
    if (stage !== 'primary') return Promise.reject(new Error('一期只有小学映射'));
    var f = o.fetch || (root && root.fetch && root.fetch.bind(root));
    var url = (o.base || '') + mappingPath(o.version || HUJIAO, o.subject || 'math', stage);
    return f(url).then(function (r) {
      if (!r.ok) throw new Error('映射文件加载失败：' + r.status);
      return r.json();
    }).then(buildPlacement);
  }

  function placementOf(P, id) { return (P && P.byId[id]) || null; }

  function isCovered(P, id) { return !!placementOf(P, id); }

  /** 排序用的数：年级、学期、单元首次出现的位置、条目顺序；没有落点的排最后。 */
  function orderKey(P, id) {
    var p = placementOf(P, id);
    if (!p) return FAR;
    return (p.grade * 10 + p.term) * 1e6 + p.unitOrder * 1e3 + p.order;
  }

  /** 按落点排序（年级、学期、文件里的单元先后、单元内顺序）；没有落点的保持原相对顺序排在最后。 */
  function sortIds(P, ids) {
    return ids.map(function (id, i) { return { id: id, k: orderKey(P, id), i: i }; })
      .sort(function (a, b) { return a.k - b.k || a.i - b.i; })
      .map(function (x) { return x.id; });
  }

  /** 章节文案：没传落点表（人教版）原样返回 topic.chapter；沪教版有落点写单元名（有节名再接节名），没有写「该版本暂未覆盖」。 */
  function chapterText(P, topic) {
    if (!P) return (topic && topic.chapter) || '';
    var p = placementOf(P, topic && topic.id);
    if (!p) return UNCOVERED;
    return p.chapter ? p.unit + ' · ' + p.chapter : p.unit;
  }

  /** 给 engine.chapterSummary 的 view：按落点的册与单元分章，没有落点的单独一章排最后。 */
  function chapterView(P) {
    return {
      chapterOf: function (t) {
        var p = placementOf(P, t.id);
        return p
          ? { volume: p.volume, chapterNo: '', chapterName: p.unit, section: '' }
          : { volume: '', chapterNo: '', chapterName: UNCOVERED, section: '' };
      },
      order: function (t) { return orderKey(P, t.id); }
    };
  }

  /** 给 engine.filterByProgress 的取值函数：读落点的年级与学期；没有落点返回 null（当作保留）。 */
  function progressPlace(P) {
    return function (id) {
      var p = placementOf(P, id);
      return p ? { grade: p.grade, semester: p.semester } : null;
    };
  }

  /** 学习进度再滤一层。进度为「上」时去掉「当前年级、落点学期为下」的点，curGrade 为 null 时所有落点为下的点。 */
  function filterByProgress(graph, P, ids, progress, curGrade) {
    return engine().filterByProgress(graph, ids, progress, curGrade, progressPlace(P));
  }

  function isPrimaryScope(scope) {
    return /^[一二三四五六](年级|[上下])$/.test(String(scope == null ? '' : scope).trim());
  }

  /**
   * 沪教版整年级 / 整册的目标池。scope 写法同引擎：'三年级' | '三上' | '三下'。只认小学一至六年级，其它写法返回 null。
   * 返回 { ids, volumes, label, empty, reason }：ids 按落点顺序，只含映射里有的、graph 里存在且非 external 的点。
   * 六年级一律空，reason 说明预备年级；这里不会去取人教六年级的点。
   */
  function gradeTargets(graph, P, scope, subject) {
    var subj = subject == null || subject === '' ? 'math' : subject;
    if (!P || subj !== P.subject) return null;
    var key = String(scope == null ? '' : scope).trim();
    var g = /^([一二三四五六])年级$/.exec(key);
    var v = /^([一二三四五六])([上下])$/.exec(key);
    var m = g || v;
    if (!m) return null;
    var grade = NUM.indexOf(m[1]);
    var volumes = g ? [m[1] + '上', m[1] + '下'] : [key];
    var label = g ? m[1] + '年级' : m[1] + '年级' + (m[2] === '上' ? '上册' : '下册');
    if (grade >= 6) return { ids: [], volumes: volumes, label: label, empty: true, reason: PREP_NOTE };
    var hit = Object.keys(P.byId).filter(function (id) {
      var t = graph.byId[id];
      return t && !t.external && volumes.indexOf(P.byId[id].volume) >= 0;
    });
    var ids = sortIds(P, hit);
    return { ids: ids, volumes: volumes, label: label, empty: !ids.length, reason: ids.length ? '' : EMPTY_VOLUME_NOTE };
  }

  /**
   * 把 ids 按沪教册与单元分组：{ volumes: [{ volume, grade, term, title, units: [{ unit, ids }] }], uncovered: [id...] }。
   * 册按年级、学期升序；单元按文件里首次出现的先后；没有落点的点放 uncovered，不进任何册。
   */
  function groupByUnit(P, ids) {
    var sorted = sortIds(P, ids);
    var volumes = [];
    var vMap = Object.create(null);
    var uncovered = [];
    sorted.forEach(function (id) {
      var p = placementOf(P, id);
      if (!p) { uncovered.push(id); return; }
      var v = vMap[p.volume];
      if (!v) {
        v = vMap[p.volume] = { volume: p.volume, grade: p.grade, term: p.term, title: volumeTitle(p.grade, p.term), units: [], _u: Object.create(null) };
        volumes.push(v);
      }
      var u = v._u[p.unit];
      if (!u) { u = v._u[p.unit] = { unit: p.unit, ids: [] }; v.units.push(u); }
      u.ids.push(id);
    });
    volumes.forEach(function (v) { delete v._u; });
    return { volumes: volumes, uncovered: uncovered };
  }

  /** 册次依据说明：映射文件还是草稿时返回「册次依据为草稿」，否则空串。 */
  function draftNote(P) { return P && P.status !== 'reviewed' ? DRAFT_NOTE : ''; }

  return {
    RENJIAO: RENJIAO,
    HUJIAO: HUJIAO,
    VERSIONS: VERSIONS,
    UNCOVERED: UNCOVERED,
    DRAFT_NOTE: DRAFT_NOTE,
    PREP_NOTE: PREP_NOTE,
    EMPTY_VOLUME_NOTE: EMPTY_VOLUME_NOTE,
    BEYOND_PRIMARY_NOTE: BEYOND_PRIMARY_NOTE,
    mappingPath: mappingPath,
    buildPlacement: buildPlacement,
    load: load,
    placementOf: placementOf,
    isCovered: isCovered,
    orderKey: orderKey,
    sortIds: sortIds,
    chapterText: chapterText,
    chapterView: chapterView,
    progressPlace: progressPlace,
    filterByProgress: filterByProgress,
    isPrimaryScope: isPrimaryScope,
    gradeTargets: gradeTargets,
    groupByUnit: groupByUnit,
    volumeKey: volumeKey,
    volumeTitle: volumeTitle,
    draftNote: draftNote
  };
});
