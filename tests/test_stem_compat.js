#!/usr/bin/env node
/* cnc_p124_q3/q4 同 ID 题干改写后的历史兼容测试。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { spawnSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const StemCompat = require(path.join(ROOT, 'assets/stem-compat.js'));
const Engine = require(path.join(ROOT, 'diagnose/engine.js'));
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/cnc_p124_pre_b.json'), 'utf8'));
const liveQuestions = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/questions.json'), 'utf8'))
  .filter((q) => String(q.id || '').startsWith('cnc_p124_'));

let passed = 0;
function test(name, fn) {
  fn();
  passed++;
  console.log('  ok   ' + name);
}

function loadChildren(entries) {
  const storage = new Map(Object.entries(entries || {}));
  const context = {
    window: { StemCompat },
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'assets/children.js'), 'utf8'), context, { filename: 'assets/children.js' });
  return { api: context.window.CnmChildren, storage };
}

function loadBlind(entries) {
  const storage = new Map(Object.entries(entries || {}));
  const context = {
    window: { StemCompat },
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); }
    }
  };
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'assets/blindspots.js'), 'utf8'), context, { filename: 'assets/blindspots.js' });
  return { api: context.window.CnmBlind, storage };
}

function tinyGraph(questions) {
  const topics = [{
    id: 'cnc_p124', name: '语文园地一·注意说话的语气', grade: '二下',
    chapter: '第1单元', domain: '习作基础', subject: 'chinese'
  }];
  return Engine.buildGraph(topics, [], questions);
}

test('夹具题干与 StemCompat.RETIRED / CURRENT 对齐，且现行题库已是语气', () => {
  const byId = Object.fromEntries(fixture.questions.map((q) => [q.id, q]));
  assert.equal(byId.cnc_p124_q3.prompt, StemCompat.RETIRED.cnc_p124_q3);
  assert.equal(byId.cnc_p124_q4.prompt, StemCompat.RETIRED.cnc_p124_q4);
  const live = Object.fromEntries(liveQuestions.map((q) => [q.id, q]));
  assert.equal(live.cnc_p124_q3.prompt, StemCompat.CURRENT.cnc_p124_q3);
  assert.equal(live.cnc_p124_q4.prompt, StemCompat.CURRENT.cnc_p124_q4);
  assert.notEqual(live.cnc_p124_q3.prompt, StemCompat.RETIRED.cnc_p124_q3);
  assert.notEqual(live.cnc_p124_q4.prompt, StemCompat.RETIRED.cnc_p124_q4);
  assert.equal(live.cnc_p124_q1.prompt, byId.cnc_p124_q1.prompt);
  assert.equal(live.cnc_p124_q2.prompt, byId.cnc_p124_q2.prompt);
});

test('若本机有 git，夹具与 d3e2dac 原文一致', () => {
  const r = spawnSync('git', ['show', 'd3e2dac:data/questions.json'], {
    cwd: ROOT, encoding: 'utf8', maxBuffer: 30 * 1024 * 1024
  });
  if (r.status !== 0) {
    console.log('  skip git show d3e2dac（环境无该对象）');
    return;
  }
  const old = JSON.parse(r.stdout).filter((q) => String(q.id || '').startsWith('cnc_p124_'));
  assert.deepEqual(old, fixture.questions);
});

test('无 prompt 的旧 session：排除 q3/q4，q1/q2 保留；过滤回放不成语气掌握', () => {
  const answers = [
    { id: 'cnc_p124', qid: 'cnc_p124_q1', result: 'correct' },
    { id: 'cnc_p124', qid: 'cnc_p124_q3', result: 'correct' },
    { id: 'cnc_p124', qid: 'cnc_p124_q2', result: 'correct' }
  ];
  const effect = StemCompat.sessionEffect(answers);
  assert.deepEqual(effect.answers.map((a) => a.qid), ['cnc_p124_q1', 'cnc_p124_q2']);
  assert.deepEqual(effect.retestTopicIds, ['cnc_p124']);
  const prepared = StemCompat.prepareReplayAnswers(answers);
  assert.equal(prepared.excluded.length, 1);
  assert.equal(prepared.excluded[0].qid, 'cnc_p124_q3');
  assert.equal(prepared.excluded[0].prompt, StemCompat.RETIRED.cnc_p124_q3);

  const graph = tinyGraph(liveQuestions);
  const raw = Engine.replay(graph, ['cnc_p124'], answers, { confirm: 3, limit: 10, seed: 1 });
  assert.equal(Engine.statusOf(raw, 'cnc_p124'), 'mastered');

  const filtered = Engine.replay(graph, ['cnc_p124'], prepared.answers, { confirm: 3, limit: 10, seed: 1 });
  assert.notEqual(Engine.statusOf(filtered, 'cnc_p124'), 'mastered');
  assert.deepEqual(filtered.answers.map((a) => a.qid), ['cnc_p124_q1', 'cnc_p124_q2']);
});

test('无 stemRev 的孩子记录：presentRecord / latestStatus 剔除语气结论并标需重测；备份保留原字节', () => {
  const PROFILE_KEY = 'cnmChildren.v1';
  const RECORD_KEY = 'cnmChildren.records.v1';
  const profiles = {
    v: 1, current: 'c1',
    children: [{ id: 'c1', name: '小测', grade: '二年级', textbook: '人教版', createdAt: '2026-11-01T00:00:00.000Z' }]
  };
  const oldRec = {
    key: 'chinese|old|cnc_p124', subject: 'chinese', label: '园地一', mode: 'target', asked: 3,
    targets: ['cnc_p124'],
    counts: { weak: 0, shaky: 0, mastered: 1, untested: 0 },
    weak: [], roots: [], shaky: [], mastered: ['cnc_p124'],
    savedAt: '2026-11-01T00:00:00.000Z'
  };
  const rawRecords = JSON.stringify({ c1: [oldRec] });
  const { api, storage } = loadChildren({
    [PROFILE_KEY]: JSON.stringify(profiles),
    [RECORD_KEY]: rawRecords
  });
  const view = api.presentRecord(oldRec);
  assert.deepEqual(view.mastered, []);
  assert.deepEqual(view.needsRetest, ['cnc_p124']);
  assert.equal(view.counts.mastered, 0);
  assert.deepEqual(oldRec.mastered, ['cnc_p124']); // 不改原对象

  const latest = api.latestStatus('c1', 'chinese');
  assert.equal(latest.cnc_p124.status, 'retest');
  assert.equal(latest.cnc_p124.needsRetest, true);

  const backup = api.exportBackup();
  assert.equal(JSON.stringify(backup.records.c1[0].mastered), JSON.stringify(['cnc_p124']));
  assert.equal(storage.get(RECORD_KEY), rawRecords);
});

test('盲区：无戳旧结论与无 prompt 旧错题不计入语气薄弱；新 stamped 可信', () => {
  const KEY = 'cnmBlind.local.v1';
  const { api, storage } = loadBlind({
    [KEY]: JSON.stringify({
      v: 1,
      byId: {
        cnc_p124: {
          id: 'cnc_p124', subject: 'chinese', status: 'weak', root: true,
          hits: 2, wrongs: 3, lastAt: '2026-11-01T00:00:00.000Z', lastLabel: '旧混合'
        }
      }
    })
  });
  const stale = api.list({ subject: 'chinese' });
  assert.equal(stale.length, 1);
  assert.equal(stale[0].status, 'retest');
  assert.equal(stale[0].wrongs, 0);

  api.noteResult({
    subject: 'chinese', key: 'sess-old', label: '旧会话',
    weak: ['cnc_p124'], shaky: [], mastered: [], roots: ['cnc_p124'],
    answers: [
      { id: 'cnc_p124', qid: 'cnc_p124_q3', result: 'wrong' },
      { id: 'cnc_p124', qid: 'cnc_p124_q1', result: 'correct' }
    ]
  });
  const afterOld = api.list({ subject: 'chinese' });
  assert.equal(afterOld[0].status, 'retest');
  assert.equal(afterOld[0].wrongs, 0);

  api.noteResult({
    subject: 'chinese', key: 'sess-new', label: '新语气',
    weak: ['cnc_p124'], shaky: [], mastered: [], roots: ['cnc_p124'],
    answers: [
      { id: 'cnc_p124', qid: 'cnc_p124_q3', result: 'wrong', prompt: StemCompat.CURRENT.cnc_p124_q3 },
      { id: 'cnc_p124', qid: 'cnc_p124_q1', result: 'wrong', prompt: liveQuestions.find((q) => q.id === 'cnc_p124_q1').prompt }
    ]
  });
  const fresh = api.list({ subject: 'chinese' });
  assert.equal(fresh[0].status, 'weak');
  assert.ok(fresh[0].wrongs >= 1);
  const raw = JSON.parse(storage.get(KEY));
  assert.equal(raw.byId.cnc_p124.stemRev, StemCompat.REV);
});

console.log('\n' + passed + ' passed');
