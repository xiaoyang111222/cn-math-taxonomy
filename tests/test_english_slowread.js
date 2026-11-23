#!/usr/bin/env node
/* 英语每日一句：逐词慢读队列与点词单读：node tests/test_english_slowread.js（不测真实语音，用假 speechSynthesis 记录朗读顺序） */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const read = (f) => fs.readFileSync(path.join(__dirname, '..', f), 'utf8');
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log('  ok   ' + name); }

const ctx = { window: {}, localStorage: { getItem: () => null, setItem() {}, removeItem() {} } };
vm.runInNewContext(read('assets/english.js'), ctx);
const EN = ctx.window.CnmEnglish;
const plain = (v) => JSON.parse(JSON.stringify(v));

function loadSpeaker(withSynth) {
  const spoken = [];
  const active = [];
  const w = {};
  if (withSynth) {
    w.SpeechSynthesisUtterance = function (text) { this.text = text; };
    w.speechSynthesis = {
      getVoices: () => [], cancel() {},
      speak(u) { spoken.push({ text: u.text, rate: u.rate }); setTimeout(() => u.onend && u.onend(), 5); }
    };
  }
  const src = read('english/app.js');
  const from = src.indexOf('  var synth =');
  const to = src.indexOf('  function showTtsNote');
  const toEnd = src.indexOf('/* ---', to);
  const code = src.slice(from, toEnd);
  const sandbox = { window: w, setTimeout, clearTimeout, ttsNote: null, EN: EN, spoken, active };
  vm.createContext(sandbox);
  vm.runInContext(code + '\nthis.speakSeq = speakSeq;', sandbox);
  return { speakSeq: sandbox.speakSeq, spoken, active };
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  await test('常量：逐词 rate 0.75、停顿在 350–500ms，点词慢速 0.6', () => {
    assert.strictEqual(EN.WORD_SLOW.rate, 0.75);
    assert.ok(EN.WORD_SLOW.gapMs >= 350 && EN.WORD_SLOW.gapMs <= 500);
    assert.ok(EN.WORD_SLOW.gapMinMs === 350 && EN.WORD_SLOW.gapMaxMs === 500);
    assert.strictEqual(EN.WORD_TAP.rate, 1);
    assert.strictEqual(EN.WORD_TAP.slowRate, 0.6);
  });

  await test('逐词队列：按词序一词一项，词间留停顿，末词不停', () => {
    const plan = plain(EN.wordPlan(['I', 'am', 'happy']));
    assert.deepStrictEqual(plan.map((s) => s.text), ['I', 'am', 'happy']);
    assert.deepStrictEqual(plan.map((s) => s.idx), [0, 1, 2]);
    assert.ok(plan.every((s) => s.rate === 0.75));
    assert.deepStrictEqual(plan.map((s) => s.gapMs), [EN.WORD_SLOW.gapMs, EN.WORD_SLOW.gapMs, 0]);
    assert.deepStrictEqual(plain(EN.wordPlan([])), []);
  });

  await test('点词单读：第一下常速、重复点慢速 0.6，单项无停顿', () => {
    assert.deepStrictEqual(plain(EN.tapPlan('happy', 2, false)), [{ idx: 2, text: 'happy', rate: 1, gapMs: 0 }]);
    assert.deepStrictEqual(plain(EN.tapPlan('happy', 2, true)), [{ idx: 2, text: 'happy', rate: 0.6, gapMs: 0 }]);
  });

  await test('有语音：按词序逐个 utterance、rate 0.75，高亮依次推进后清除', async () => {
    const s = loadSpeaker(true);
    let ended = false;
    const seq = [];
    s.speakSeq(EN.wordPlan(['I', 'am', 'happy']), { onActive: (i) => seq.push(i), onEnd: () => { ended = true; } });
    await sleep(EN.WORD_SLOW.gapMs * 2 + 300);
    assert.deepStrictEqual(s.spoken, [{ text: 'I', rate: 0.75 }, { text: 'am', rate: 0.75 }, { text: 'happy', rate: 0.75 }]);
    assert.deepStrictEqual(seq, [0, 1, 2, -1]);
    assert.ok(ended);
  });

  await test('词间停顿真实存在：第 2 个词不会在 gap 之前开读', async () => {
    const s = loadSpeaker(true);
    s.speakSeq(EN.wordPlan(['a', 'b']), {});
    await sleep(EN.WORD_SLOW.gapMs - 150);
    assert.strictEqual(s.spoken.length, 1);
    await sleep(300);
    assert.strictEqual(s.spoken.length, 2);
  });

  await test('无语音降级：不报错，仍按同样词序与节奏走高亮', async () => {
    const s = loadSpeaker(false);
    const seq = [];
    s.speakSeq(EN.wordPlan(['I', 'am']), { onActive: (i) => seq.push(i) });
    assert.deepStrictEqual(seq, [0]);
    await sleep(2000);
    assert.deepStrictEqual(seq, [0, 1, -1]);
  });

  await test('新的朗读会打断上一个队列', async () => {
    const s = loadSpeaker(true);
    s.speakSeq(EN.wordPlan(['one', 'two', 'three']), {});
    await sleep(50);
    s.speakSeq(EN.tapPlan('solo', 0, false), {});
    await sleep(EN.WORD_SLOW.gapMs + 300);
    assert.deepStrictEqual(s.spoken.map((x) => x.text), ['one', 'solo']);
  });

  await test('页面接线：逐词慢读按钮、点词与词卡点读、常速整句保持', () => {
    const app = read('english/app.js');
    assert.ok(app.includes("btn('逐词慢读', null, sayByWord)"));
    assert.ok(!app.includes("'慢速听'"));
    assert.ok(app.includes("btn('听一遍', 'primary', function () { say(entry.sentence, tokens, 1); })"));
    assert.ok(app.includes('speakSeq(EN.wordPlan(tokens)'));
    assert.ok(app.includes("var c = btn('', 'chip ' + wc(i), function () { tapWord(i); })"));
    assert.ok(/s\.addEventListener\('click', function \(\) \{ tapWord\(i\); \}\)/.test(app));
  });

  await test('sw 升到 v41 且清单仍含英语文件', () => {
    const sw = read('sw.js');
    assert.ok(/var VERSION = 'v41';/.test(sw));
    ['english/app.js', 'assets/english.js', 'data/english/days.json'].forEach((f) => assert.ok(sw.includes("'" + f + "'"), f));
  });

  console.log('\n' + passed + ' passed');
})().catch((e) => { console.error(e); process.exit(1); });
