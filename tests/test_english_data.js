#!/usr/bin/env node
/* 英语每日一句句子表与动画模板：node tests/test_english_data.js */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const S = require('../english/scenes.js');
const days = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/english/days.json'), 'utf8'));
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('  ok   ' + name); }
const toks = (s) => s.replace(/[.!?]$/, '').split(' ');

test('30 天齐全、day 连续、句子不重复', () => {
  assert.strictEqual(days.length, 30);
  days.forEach((d, i) => assert.strictEqual(d.day, i + 1));
  assert.strictEqual(new Set(days.map((d) => d.sentence)).size, 30);
});

test('第 1–7 天与定稿一致', () => {
  const fixed = ['I am happy.', 'I have a cat.', 'I like milk.', 'I can swim.', 'This is my family.', 'I read every day.', 'I read a story every night.'];
  fixed.forEach((s, i) => assert.strictEqual(days[i].sentence, s));
  const zh = ['我很开心。', '我有一只猫。', '我喜欢牛奶。', '我会游泳。', '这是我的家人。', '我每天读书。', '我每晚读一个故事。'];
  zh.forEach((s, i) => assert.strictEqual(days[i].translation, s));
});

test('字段完整：translation / words / tip / variants / scene / sceneProps / audio 预留', () => {
  days.forEach((d) => {
    assert.ok(/^[A-Z][A-Za-z' ]+[.?!]$/.test(d.sentence), d.sentence);
    assert.ok(d.translation && /[一-鿿]/.test(d.translation), 'translation ' + d.day);
    assert.strictEqual(typeof d.tip, 'string');
    assert.ok(d.scene && d.sceneProps && typeof d.sceneProps === 'object', 'scene ' + d.day);
    assert.ok('audio' in d && d.audio === null, 'audio 字段预留 ' + d.day);
  });
});

test('每句 3–6 词；words 逐词覆盖全句且每个词有中文', () => {
  days.forEach((d) => {
    const t = toks(d.sentence);
    assert.ok(t.length >= 3 && t.length <= 6, d.sentence);
    assert.deepStrictEqual(d.words.map((w) => w.en), t, 'words 覆盖 ' + d.sentence);
    d.words.forEach((w) => assert.ok(w.zh && w.zh.length, d.sentence + ' ' + w.en));
  });
});

test('variants 3–4 个，只换一个词，且每句所有变体换的是同一个位置', () => {
  days.forEach((d) => {
    assert.ok(d.variants.length >= 3 && d.variants.length <= 4, 'variants 数量 ' + d.day);
    const base = toks(d.sentence);
    const slots = new Set();
    d.variants.forEach((v) => {
      const t = toks(v.en);
      assert.strictEqual(t.length, base.length, v.en);
      const diff = t.map((w, i) => (w !== base[i] ? i : -1)).filter((i) => i >= 0);
      assert.strictEqual(diff.length, 1, d.sentence + ' → ' + v.en);
      slots.add(diff[0]);
      assert.ok(/[一-鿿]/.test(v.zh), v.en);
      assert.strictEqual(v.en.slice(-1), d.sentence.slice(-1));
    });
    assert.strictEqual(slots.size, 1, '换词位置一致 ' + d.day);
  });
});

test('scene 都在模板清单内，清单里的模板都有句子用；道具都有图', () => {
  assert.ok(S.IDS.length >= 8 && S.IDS.length <= 10, S.IDS.join());
  const used = new Set();
  days.forEach((d) => {
    assert.ok(S.IDS.includes(d.scene), d.day + ' ' + d.scene);
    used.add(d.scene);
    const p = d.sceneProps;
    [].concat(p.items || [], p.food || [], p.food2 || [], p.item || []).forEach((name) => assert.ok(S.ITEMS.includes(name), '道具 ' + name));
  });
  S.IDS.forEach((id) => assert.ok(used.has(id), '模板没被用到 ' + id));
});

test('每个模板对 30 句的 sceneProps 都能渲染出 SVG', () => {
  days.forEach((d) => {
    const svg = S.render(d.scene, d.sceneProps);
    assert.ok(svg.startsWith('<svg') && svg.endsWith('</svg>'), d.day);
    assert.ok(!/undefined|NaN/.test(svg), 'svg 里有 undefined / NaN：' + d.day);
  });
  assert.strictEqual(S.render('nope', {}), '');
});

test('后 10 句才出现 and / in / at 等小词扩展', () => {
  const small = /\b(and|in|at|the|to)\b/;
  days.slice(0, 20).forEach((d) => assert.ok(!small.test(d.sentence), d.sentence));
  assert.ok(days.slice(20).some((d) => small.test(d.sentence)));
});

console.log(passed + ' passed');
