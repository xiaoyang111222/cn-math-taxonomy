/* 教材版本（人教 / 沪教 / 北师大 / 苏教）：选版本、读 data/mappings/<edition>.json、把对照覆写到知识点上。
 * 纯函数部分（无 DOM）在 Node 里可 require；浏览器里暴露为 window.CnmEditions。
 *
 *   EDITIONS：[{key, label, textbook}]，key 为空串表示人教版（知识点自己的 grade/semester/chapter）
 *   choose({query, stored, textbook}) -> key：URL ?edition= > 导航栏选择（localStorage）> 当前孩子的 textbook > 人教
 *   applyEdition(topics, key, file) -> 新数组：有对照的知识点换成该版本的 grade/semester/chapter，
 *     并带上 _edition = {key, label, volume, unit, chapter}；没有对照的知识点原样保留（仍按人教版显示）。
 *     对照来源：file.entries（data/mappings/<key>.json，status 为 example 的示例文件不读）和 topic.mappings[key]，文件优先。
 *   load(base, key) -> Promise<file|null>：404 / 示例文件 / 出错都返回 null（=不覆写）。
 *   mountSelect(onChange)：在导航栏里放一个版本下拉框（只在数学页面用）。
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.CnmEditions = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const EDITIONS = [
    { key: '', label: '人教版', textbook: '人教版' },
    { key: 'hujiao_math', label: '沪教版', textbook: '沪教版' },
    { key: 'beishida_math', label: '北师大版', textbook: '北师大版' },
    { key: 'sujiao_math', label: '苏教版', textbook: '苏教版' }
  ];
  const STORE_KEY = 'cnmEdition.v1';
  const CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  const HS = { 10: '高一', 11: '高二', 12: '选必一', 13: '选必二', 14: '选必三' };

  function known(key) { return EDITIONS.some(function (e) { return e.key === key; }); }
  function labelOf(key) { const e = EDITIONS.find(function (x) { return x.key === key; }); return e ? e.label : '人教版'; }
  function editionForTextbook(textbook) {
    const e = EDITIONS.find(function (x) { return x.textbook === textbook; });
    return e ? e.key : '';
  }

  /** stored：'renjiao' 表示用户在导航栏明确选了人教版（区别于“没选过”）。 */
  function choose(opts) {
    opts = opts || {};
    const q = opts.query;
    if (q === 'renjiao') return '';
    if (q != null && known(q)) return q;
    if (opts.stored === 'renjiao') return '';
    if (opts.stored && known(opts.stored)) return opts.stored;
    return editionForTextbook(opts.textbook);
  }

  /** 册名：一–九年级为「七上」「九全」这种；高中数学不分上下册。 */
  function volumeWord(grade, term) {
    if (HS[grade]) return HS[grade];
    return (CN[grade] || String(grade)) + (term || '上');
  }
  function volumeLabel(grade, term) {
    if (HS[grade]) return HS[grade];
    return (CN[grade] || String(grade)) + '年级' + (term || '上') + '册';
  }

  function entriesOf(file) {
    if (!file || file.status === 'example' || !Array.isArray(file.entries)) return {};
    const by = {};
    file.entries.forEach(function (e) { if (e && e.topicId) by[e.topicId] = e; });
    return by;
  }

  function applyEdition(topics, key, file) {
    if (!key) return topics;
    const fromFile = entriesOf(file);
    const label = labelOf(key);
    return topics.map(function (t) {
      const m = fromFile[t.id] || (t.mappings && t.mappings[key]);
      if (!m || !m.grade || !m.term) return t;
      const unit = m.unit || '';
      const chapter = m.chapter || '';
      const vol = volumeLabel(m.grade, m.term);
      const text = [vol, unit, chapter].filter(Boolean).join(' ') || vol;
      return Object.assign({}, t, {
        grade: m.grade, semester: m.term, chapter: text,
        _edition: { key: key, label: label, volume: volumeWord(m.grade, m.term), unit: unit || '（' + label + '未注明单元）', chapter: chapter, original: t.chapter }
      });
    });
  }

  function load(base, key) {
    if (!key || typeof fetch === 'undefined') return Promise.resolve(null);
    return fetch(base + 'data/mappings/' + key + '.json').then(function (r) {
      return r.ok ? r.json() : null;
    }).then(function (j) {
      return j && j.edition === key && j.status !== 'example' ? j : null;
    }).catch(function () { return null; });
  }

  function readStored() { try { return localStorage.getItem(STORE_KEY); } catch (e) { return null; } }
  function writeStored(v) { try { localStorage.setItem(STORE_KEY, v); } catch (e) { /* 隐私模式 */ } }

  /** 浏览器里：按 URL / 导航栏 / 当前孩子选版本。 */
  function current() {
    let q = null;
    try { q = new URLSearchParams(location.search).get('edition'); } catch (e) { q = null; }
    let tb = '';
    try { const c = window.CnmChildren && window.CnmChildren.current(); tb = c ? c.textbook : ''; } catch (e) { tb = ''; }
    return choose({ query: q, stored: readStored(), textbook: tb });
  }

  function mountSelect(onChange) {
    if (typeof document === 'undefined') return null;
    const nav = document.querySelector('.site-nav');
    if (!nav || document.getElementById('edition-select')) return null;
    const sel = document.createElement('select');
    sel.id = 'edition-select';
    sel.className = 'edition-select';
    sel.setAttribute('aria-label', '教材版本');
    sel.title = '教材版本：有对照表时，章节和目录按所选版本显示';
    EDITIONS.forEach(function (e) {
      const o = document.createElement('option');
      o.value = e.key || 'renjiao';
      o.textContent = e.label;
      sel.appendChild(o);
    });
    sel.value = current() || 'renjiao';
    sel.addEventListener('change', function () {
      writeStored(sel.value);
      if (onChange) onChange(sel.value === 'renjiao' ? '' : sel.value);
    });
    const wrap = document.createElement('div');
    wrap.className = 'edition-switch';
    wrap.appendChild(sel);
    nav.insertBefore(wrap, nav.firstChild ? nav.firstChild.nextSibling : null);
    return sel;
  }

  return {
    EDITIONS: EDITIONS, STORE_KEY: STORE_KEY,
    choose: choose, editionForTextbook: editionForTextbook, labelOf: labelOf,
    volumeWord: volumeWord, volumeLabel: volumeLabel, applyEdition: applyEdition,
    load: load, current: current, mountSelect: mountSelect
  };
});
