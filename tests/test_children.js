#!/usr/bin/env node
/* 档案备份恢复测试：node tests/test_children.js（无依赖，不访问真实浏览器存储）。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/children.js'), 'utf8');
const PROFILE_KEY = 'cnmChildren.v1';
const RECORD_KEY = 'cnmChildren.records.v1';
let passed = 0;

function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function load(entries, failKey, options = {}) {
  const storage = new Map(Object.entries(entries || {}));
  const writes = [];
  const context = {
    window: {},
    localStorage: {
      getItem(key) {
        if (key === failKey) throw new Error('Storage access denied');
        return storage.has(key) ? storage.get(key) : null;
      },
      setItem(key, value) {
        writes.push(key);
        if (options.failWrite && options.failWrite(key, value)) throw new Error('QuotaExceededError');
        storage.set(key, value);
      },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(source, context, { filename: 'assets/children.js' });
  return { api: context.window.CnmChildren, storage, writes };
}

function exported(api) { return JSON.parse(JSON.stringify(api.exportBackup())); }
const profiles = {
  v: 1, current: 'child-b', children: [
    { id: 'child-a', name: '小满', grade: '三年级', textbook: '人教版', createdAt: '2026-10-01T00:00:00.000Z' },
    { id: 'child-b', name: '小禾', grade: '五年级', textbook: '沪教版', createdAt: '2026-10-02T00:00:00.000Z' }
  ]
};
const records = {
  'child-a': ['math', 'chinese', 'english', 'physics'].map((subject, i) => ({
    key: subject + '|seed|target', subject, label: '测试范围 ' + i, mode: 'target', asked: 8,
    targets: ['topic-' + i], counts: { weak: 1, shaky: 1, mastered: 1, untested: 2 },
    weak: ['weak-' + i], roots: ['weak-' + i], shaky: ['shaky-' + i], mastered: ['mastered-' + i],
    savedAt: '2026-10-20T00:00:00.000Z', updatedAt: '2026-10-21T00:00:00.000Z'
  })),
  'child-b': [{ key: 'screen|seed|targets', subject: 'math', mode: 'screen', targets: null, weak: [], savedAt: '2026-10-20T00:00:00.000Z' }]
};
function fixture() {
  return { [PROFILE_KEY]: JSON.stringify(profiles), [RECORD_KEY]: JSON.stringify(records) };
}

test('导出包含全部孩子、当前孩子和四学科完整历史，并带备份版本和时间', () => {
  const { api } = load(fixture());
  const before = Date.now();
  const backup = exported(api);
  assert.equal(backup.format, 'cn-math-taxonomy.children');
  assert.equal(backup.version, 1);
  assert.ok(Date.parse(backup.exportedAt) >= before && Date.parse(backup.exportedAt) <= Date.now());
  assert.deepStrictEqual(backup.profiles, profiles);
  assert.deepStrictEqual(backup.records, records);
});

test('导出不改写存储、当前孩子或记录时间', () => {
  const entries = fixture();
  const { api, storage, writes } = load(entries);
  api.exportBackup();
  assert.deepStrictEqual(Object.fromEntries(storage), entries);
  assert.deepStrictEqual(writes, []);
});

test('保留未选择当前孩子、未知扩展字段和超过 40 条的已存历史', () => {
  const entries = fixture();
  const extraProfiles = { ...profiles, current: null, futureMetadata: { note: '保留' } };
  const extraRecords = { 'child-a': Array.from({ length: 45 }, (_, i) => ({ key: 'record-' + i, extra: i })) };
  entries[PROFILE_KEY] = JSON.stringify(extraProfiles);
  entries[RECORD_KEY] = JSON.stringify(extraRecords);
  const backup = exported(load(entries).api);
  assert.deepStrictEqual(backup.profiles, extraProfiles);
  assert.deepStrictEqual(backup.records, extraRecords);
});

test('有孩子但没有诊断记录时仍能备份资料', () => {
  const backup = exported(load({ [PROFILE_KEY]: JSON.stringify(profiles) }).api);
  assert.deepStrictEqual(backup.profiles, profiles);
  assert.deepStrictEqual(backup.records, {});
});

test('只导出档案和历史，不混入会话、统计或其他站点存储', () => {
  const entries = { ...fixture(), unrelated: 'private', 'cnmDiagnose.session.v2': '{"seed":"x"}', 'cnmStats.v1': '{}' };
  const backup = exported(load(entries).api);
  assert.deepStrictEqual(Object.keys(backup).sort(), ['exportedAt', 'format', 'profiles', 'records', 'version']);
  assert.ok(!JSON.stringify(backup).includes('private'));
});

test('每次读取最新数据，修改导出快照不会污染已存档案', () => {
  const { api, storage } = load(fixture());
  const backup = api.exportBackup();
  backup.profiles.children[0].name = '修改快照';
  backup.records['child-a'][0].weak.push('extra');
  assert.deepStrictEqual(exported(api).profiles, profiles);
  assert.deepStrictEqual(exported(api).records, records);
  const next = { ...profiles, current: 'child-a' };
  storage.set(PROFILE_KEY, JSON.stringify(next));
  assert.deepStrictEqual(exported(api).profiles, next);
});

test('没有孩子时不生成无意义的空备份', () => {
  assert.throws(() => load().api.exportBackup(), /还没有可导出/);
  assert.throws(() => load({ [PROFILE_KEY]: '{"v":1,"current":null,"children":[]}' }).api.exportBackup(), /还没有可导出/);
});

test('读取任一存储键失败时报告错误，不使用空数据兜底', () => {
  for (const key of [PROFILE_KEY, RECORD_KEY]) {
    const { api, writes } = load(fixture(), key);
    assert.throws(() => api.exportBackup(), /无法读取档案数据/);
    assert.deepStrictEqual(writes, []);
  }
});

test('任一 JSON 损坏时拒绝生成部分备份', () => {
  for (const key of [PROFILE_KEY, RECORD_KEY]) {
    assert.throws(() => load({ ...fixture(), [key]: '{broken' }).api.exportBackup(), /无法读取档案数据/);
  }
});

test('拒绝异常结构，避免静默丢失档案或历史', () => {
  for (const value of [null, [], {}, { children: [null] }, { children: [{ id: '' }] }]) {
    assert.throws(() => load({ ...fixture(), [PROFILE_KEY]: JSON.stringify(value) }).api.exportBackup(), /格式异常/);
  }
  for (const value of [null, [], 'bad', { 'child-a': {} }]) {
    assert.throws(() => load({ ...fixture(), [RECORD_KEY]: JSON.stringify(value) }).api.exportBackup(), /格式异常/);
  }
});

function backup() { return exported(load(fixture()).api); }
function importInto(api, data) { return api.importBackup(data, api.previewImport(data).token); }
function stored(storage, key) { return JSON.parse(storage.get(key)); }

test('新浏览器完整恢复多孩子、当前孩子与四学科历史，弱点汇总仍可用', () => {
  const data = backup();
  const { api, storage } = load();
  const result = importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.equal(result.addedChildren, 2);
  assert.equal(result.addedRecords, 5);
  assert.deepStrictEqual(stored(storage, PROFILE_KEY), profiles);
  assert.deepStrictEqual(stored(storage, RECORD_KEY), records);
  assert.equal(api.current().id, 'child-b');
  assert.equal(api.latestStatus('child-a', 'math')['weak-0'].status, 'weak');
  assert.equal(api.latestStatus('child-a', 'math')['weak-0'].root, true);
});

test('预览和取消前不写入本机存储', () => {
  const { api, storage, writes } = load(fixture());
  const before = Object.fromEntries(storage);
  const preview = api.previewImport(backup());
  assert.equal(preview.matchedChildren, 2);
  assert.equal(preview.addedRecords, 0);
  assert.deepStrictEqual(writes, []);
  assert.deepStrictEqual(Object.fromEntries(storage), before);
});

test('重复导入同一备份不会复制档案或历史，原始时间不变', () => {
  const { api, storage } = load(fixture());
  importInto(api, backup());
  const before = Object.fromEntries(storage);
  importInto(api, backup());
  assert.deepStrictEqual(Object.fromEntries(storage), before);
});

test('合并保留本机资料和当前选择，旧记录保留，新记录加入，同键取较新结果', () => {
  const localProfiles = { ...profiles, current: 'child-a', children: [{ ...profiles.children[0], grade: '六年级' }] };
  const localRecords = { 'child-a': [
    { ...records['child-a'][0], updatedAt: '2026-10-26T00:00:00.000Z', label: '本机较新' },
    { ...records['child-a'][1], updatedAt: '2026-10-19T00:00:00.000Z', label: '本机较旧' },
    { ...records['child-a'][0], key: 'local-only', label: '仅本机' }
  ] };
  const { api, storage } = load({ [PROFILE_KEY]: JSON.stringify(localProfiles), [RECORD_KEY]: JSON.stringify(localRecords) });
  const result = importInto(api, backup());
  const outProfiles = stored(storage, PROFILE_KEY);
  const outRecords = stored(storage, RECORD_KEY);
  assert.equal(outProfiles.current, 'child-a');
  assert.equal(outProfiles.children[0].grade, '六年级');
  assert.equal(outRecords['child-a'].length, 5);
  assert.equal(outRecords['child-a'].find(r => r.key === records['child-a'][0].key).label, '本机较新');
  assert.equal(outRecords['child-a'].find(r => r.key === records['child-a'][1].key).label, records['child-a'][1].label);
  assert.ok(outRecords['child-a'].find(r => r.key === 'local-only'));
  assert.equal(result.addedChildren, 1);
  assert.equal(result.updatedRecords, 1);
});

test('同一条记录时间相同则保留本机结果', () => {
  const data = backup();
  data.records['child-a'][0].label = '备份不同结果';
  const { api, storage } = load(fixture());
  importInto(api, data);
  assert.equal(stored(storage, RECORD_KEY)['child-a'][0].label, records['child-a'][0].label);
});

test('本机明确选择不保存到档案时，导入不改变当前选择', () => {
  const entries = fixture();
  entries[PROFILE_KEY] = JSON.stringify({ ...profiles, current: null });
  const { api, storage } = load(entries);
  importInto(api, backup());
  assert.equal(stored(storage, PROFILE_KEY).current, null);
});

test('同名不同 ID 保留两人并自动改名，反复导入仍按 ID 合并', () => {
  const data = backup();
  data.profiles.children = [{ ...profiles.children[1], name: profiles.children[0].name }];
  data.records = { 'child-b': records['child-b'] };
  const entries = { [PROFILE_KEY]: JSON.stringify({ ...profiles, current: 'child-a', children: [profiles.children[0]] }) };
  const { api, storage } = load(entries);
  const preview = api.previewImport(data);
  assert.equal(preview.renamedChildren, 1);
  assert.equal(preview.children[0].name, '小满（导入）');
  importInto(api, data);
  const first = Object.fromEntries(storage);
  importInto(api, data);
  assert.deepStrictEqual(Object.fromEntries(storage), first);
  assert.deepStrictEqual(stored(storage, PROFILE_KEY).children.map(c => c.id), ['child-a', 'child-b']);
});

test('自动改名不会占用其他待导入孩子的原名，昵称仍不超过 12 字', () => {
  const name = '一二三四五六七八九十甲乙';
  const data = backup();
  data.profiles.children[0].name = name;
  data.profiles.children[1].name = name.slice(0, 8) + '（导入）';
  const localProfiles = { ...profiles, current: 'local', children: [{ ...profiles.children[0], id: 'local', name }] };
  const { api } = load({ [PROFILE_KEY]: JSON.stringify(localProfiles) });
  const preview = api.previewImport(data);
  const names = preview.children.map(c => c.name);
  assert.ok(names[0].length <= 12);
  assert.notEqual(names[0], names[1]);
  assert.equal(names[1], data.profiles.children[1].name);
});

test('合并超过 8 个孩子时拒绝导入，原数据不变', () => {
  const children = Array.from({ length: 8 }, (_, i) => ({ ...profiles.children[0], id: 'local-' + i, name: '孩子' + i }));
  const entries = { [PROFILE_KEY]: JSON.stringify({ v: 1, current: null, children }) };
  const { api, storage, writes } = load(entries);
  assert.throws(() => api.previewImport(backup()), /超过 8/);
  assert.deepStrictEqual(Object.fromEntries(storage), entries);
  assert.deepStrictEqual(writes, []);
});

test('合并保留 80 条历史，之后保存和移动记录也不会批量截断', () => {
  const makeRecords = prefix => Array.from({ length: 40 }, (_, i) => ({ ...records['child-a'][0], key: prefix + i }));
  const data = backup();
  data.records['child-a'] = makeRecords('import-');
  const entries = { [PROFILE_KEY]: JSON.stringify(profiles), [RECORD_KEY]: JSON.stringify({ 'child-a': makeRecords('local-') }) };
  const { api, storage } = load(entries);
  importInto(api, data);
  assert.equal(stored(storage, RECORD_KEY)['child-a'].length, 80);
  api.saveRecord('child-a', { key: 'new-run', subject: 'math' });
  assert.equal(stored(storage, RECORD_KEY)['child-a'].length, 81);
  api.moveRecord(records['child-b'][0].key, 'child-b', 'child-a');
  assert.equal(stored(storage, RECORD_KEY)['child-a'].length, 82);
});

test('普通档案新增诊断仍保持原有最近 40 条规则', () => {
  const { api, storage } = load({ [PROFILE_KEY]: JSON.stringify(profiles) });
  for (let i = 0; i < 41; i++) api.saveRecord('child-a', { key: 'run-' + i, subject: 'math' });
  assert.equal(stored(storage, RECORD_KEY)['child-a'].length, 40);
});

test('合并保留扩展字段，且不会写入会话、设置或统计', () => {
  const data = backup();
  data.profiles.extension = { note: '扩展资料' };
  data.profiles.children[0].custom = { data: [1, 2] };
  data.records['child-a'][0].custom = '扩展记录';
  const { api, storage, writes } = load({ 'cnmDiagnose.session.v2': '{"seed":"local"}' });
  importInto(api, data);
  assert.deepStrictEqual(stored(storage, PROFILE_KEY), data.profiles);
  assert.deepStrictEqual(stored(storage, RECORD_KEY), data.records);
  assert.equal(storage.get('cnmDiagnose.session.v2'), '{"seed":"local"}');
  assert.deepStrictEqual(writes, [RECORD_KEY, PROFILE_KEY]);
});

test('预览后其他页面改变档案时停止写入，必须重新预览', () => {
  const { api, storage, writes } = load(fixture());
  const data = backup();
  const preview = api.previewImport(data);
  storage.set(PROFILE_KEY, JSON.stringify({ ...profiles, current: 'child-a' }));
  assert.throws(() => api.importBackup(data, preview.token), /已发生变化/);
  assert.equal(stored(storage, PROFILE_KEY).current, 'child-a');
  assert.deepStrictEqual(writes, []);
  importInto(api, data);
  assert.equal(stored(storage, PROFILE_KEY).current, 'child-a');
});

test('未预览的调用不能直接写入备份', () => {
  const { api, writes } = load(fixture());
  assert.throws(() => api.importBackup(backup()), /重新预览/);
  assert.deepStrictEqual(writes, []);
});

test('本机存储读取失败或已损坏时不把它当成空浏览器', () => {
  for (const key of [PROFILE_KEY, RECORD_KEY]) {
    const { api, writes } = load(fixture(), key);
    assert.throws(() => api.previewImport(backup()), /无法读取本机档案/);
    assert.deepStrictEqual(writes, []);
    const broken = load({ ...fixture(), [key]: '{broken' });
    assert.throws(() => broken.api.previewImport(backup()), /无法读取本机档案/);
    assert.deepStrictEqual(broken.writes, []);
  }
});

test('第一步写入失败时原档案和记录不变', () => {
  const entries = fixture();
  const { api, storage } = load(entries, null, { failWrite: key => key === RECORD_KEY });
  assert.throws(() => importInto(api, backup()), /原有档案和记录未改变/);
  assert.deepStrictEqual(Object.fromEntries(storage), entries);
});

test('第二步写入失败时回滚原记录，保留原始存储字节', () => {
  const entries = fixture();
  entries[RECORD_KEY] = JSON.stringify(records, null, 2);
  const { api, storage } = load(entries, null, { failWrite: key => key === PROFILE_KEY });
  const data = backup(); data.records['child-a'][0].updatedAt = '2026-10-28T00:00:00.000Z';
  assert.throws(() => importInto(api, data), /原有档案和记录未改变/);
  assert.deepStrictEqual(Object.fromEntries(storage), entries);
});

test('空浏览器写入失败时回滚到没有存储键的状态', () => {
  const { api, storage } = load({}, null, { failWrite: key => key === PROFILE_KEY });
  assert.throws(() => importInto(api, backup()), /原有档案和记录未改变/);
  assert.equal(storage.size, 0);
});

test('回滚也失败时明确提示恢复失败，不报告成功或数据未改变', () => {
  let calls = 0;
  const { api } = load(fixture(), null, { failWrite: () => ++calls > 1 });
  assert.throws(() => importInto(api, backup()), /原记录恢复失败/);
});

test('拒绝错误文件、未知版本、重复 ID 和无归属记录', () => {
  const cases = [
    data => { data.format = 'diagnosis'; },
    data => { data.version = 2; },
    data => { data.profiles.v = 2; },
    data => { data.exportedAt = 'bad'; },
    data => { data.profiles.children[1].id = data.profiles.children[0].id; },
    data => { data.profiles.current = 'missing'; },
    data => { data.records.orphan = []; },
    data => { data.records['child-a'].push(data.records['child-a'][0]); },
    data => { data.records['child-a'][0].weak = 'wrong'; },
    data => { data.records['child-a'][0].counts.weak = -1; },
    data => { data.records['child-a'][0].savedAt = 'bad'; },
    data => { data.profiles.children[0].grade = '不存在的年级'; }
  ];
  for (const mutate of cases) {
    const data = backup(); mutate(data);
    const { api, writes } = load(fixture());
    assert.throws(() => api.parseBackup(JSON.stringify(data)));
    assert.deepStrictEqual(writes, []);
  }
});

test('拒绝危险对象键与超大文件，支持 UTF-8 BOM', () => {
  const { api } = load();
  const data = backup();
  const json = JSON.stringify(data);
  assert.equal(api.parseBackup('\uFEFF' + json).format, data.format);
  assert.throws(() => api.parseBackup('{broken'), /有效的 JSON/);
  assert.throws(() => api.parseBackup(' '.repeat(api.MAX_BACKUP_BYTES + 1)), /10 MB/);
  const unsafe = json.replace('"profiles":{', '"profiles":{"__proto__":{"polluted":true},');
  assert.throws(() => api.parseBackup(unsafe), /不允许/);
  assert.equal({}.polluted, undefined);
});

test('科学学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'science|seed|target', subject: 'science', mode: 'target', targets: ['cns_p001'], weak: [], savedAt: '2026-10-22T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'science'));
});

test('道德与法治学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'morality|seed|target', subject: 'morality', mode: 'target', targets: ['cnd_p001'], weak: [], savedAt: '2026-10-29T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'morality'));
});

test('历史学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'history|seed|target', subject: 'history', mode: 'target', targets: ['cnh_j001'], weak: [], savedAt: '2026-10-30T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'history'));
});

test('地理学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'geography|seed|target', subject: 'geography', mode: 'target', targets: ['cng_j001'], weak: [], savedAt: '2026-10-31T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'geography'));
});

test('生物学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'biology|seed|target', subject: 'biology', mode: 'target', targets: ['cnb_j001'], weak: [], savedAt: '2026-11-03T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'biology'));
});

test('化学学科的诊断记录可以备份和恢复', () => {
  const data = backup();
  data.records['child-b'] = data.records['child-b'].concat([{ key: 'chemistry|seed|target', subject: 'chemistry', mode: 'target', targets: ['cnk_j001'], weak: [], savedAt: '2026-11-04T00:00:00.000Z' }]);
  const { api, storage } = load();
  importInto(api, api.parseBackup(JSON.stringify(data)));
  assert.ok(stored(storage, RECORD_KEY)['child-b'].some((r) => r.subject === 'chemistry'));
});

console.log('\n' + passed + ' passed, 0 failed');
