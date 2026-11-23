/* 英语每日一句页：今日句（动画、朗读、三层翻译、拆词、跟读、词卡排序、换词造句、三项打卡）、旧句复习（排序 + 听写）、30 天进度。
 * 数据：data/english/days.json；进度：assets/english.js；打卡：assets/activity.js；朗读：浏览器 speechSynthesis（没有语音时只做文字高亮）。 */
(function () {
  'use strict';
  var CC = window.CnmChildren;
  var EN = window.CnmEnglish;
  var SCENES = window.CnmEnglishScenes;
  var GUEST = EN.GUEST;
  var picker = document.getElementById('picker');
  var app = document.getElementById('app');
  var PALETTE = 6;
  var days = null;
  var childId = GUEST;
  var view = { mode: 'today', day: null };
  var flash = '';

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function btn(text, cls, onClick) {
    var b = el('button', cls || null, text);
    b.type = 'button';
    if (onClick) b.addEventListener('click', onClick);
    return b;
  }
  function wc(i) { return 'wc' + (i % PALETTE); }
  function entryOf(day) { return days[day - 1]; }
  function tokensOf(entry) { return entry.words.map(function (w) { return w.en; }); }

  /* ------------------------------------------------------------ 朗读 */

  var synth = window.speechSynthesis && typeof window.SpeechSynthesisUtterance !== 'undefined' ? window.speechSynthesis : null;
  var speaking = { id: 0, timers: [], onActive: null };
  var ttsNote = null;

  function pickVoice() {
    var list = synth && synth.getVoices ? synth.getVoices() : [];
    var us = list.filter(function (v) { return /^en[-_]US$/i.test(v.lang); });
    var en = list.filter(function (v) { return /^en/i.test(v.lang); });
    return us[0] || en[0] || null;
  }
  if (synth && synth.addEventListener) synth.addEventListener('voiceschanged', function () { /* 下次朗读时重新挑选 */ });

  function clearTimers() {
    speaking.timers.forEach(function (t) { clearTimeout(t); });
    speaking.timers = [];
  }
  function setActive(i) { if (speaking.onActive) speaking.onActive(i); }
  function stopSpeaking() {
    speaking.id++;
    clearTimers();
    setActive(-1);
    if (synth) { try { synth.cancel(); } catch (e) { /* ignore */ } }
  }

  /* text：要读的整句；words：逐词高亮用的词表（可缺）；opts.rate：1 常速 / 0.6 慢速；opts.onActive(i)：读到第 i 个词。
   * 有 boundary 事件就按事件推进，没有就按词长估算时间推进；没有语音时只做高亮，流程不被挡住。 */
  function speak(text, words, opts) {
    opts = opts || {};
    var rate = opts.rate || 1;
    stopSpeaking();
    var id = speaking.id;
    speaking.onActive = opts.onActive || null;
    var offsets = [];
    if (words) {
      var from = 0;
      words.forEach(function (w) {
        var at = text.indexOf(w, from);
        offsets.push(at < 0 ? from : at);
        from = (at < 0 ? from : at) + w.length;
      });
    }
    var boundarySeen = false;
    var started = false;
    function finish() {
      if (speaking.id !== id) return;
      clearTimers();
      setActive(-1);
      if (opts.onEnd) opts.onEnd();
    }
    function startTimers() {
      if (started || !words || boundarySeen) return;
      started = true;
      var t = 0;
      words.forEach(function (w, i) {
        speaking.timers.push(setTimeout(function () { if (speaking.id === id && !boundarySeen) setActive(i); }, t * 1000));
        t += (0.3 + 0.07 * w.length) / rate;
      });
      if (!synth) speaking.timers.push(setTimeout(finish, t * 1000 + 200));
    }
    if (!synth) { startTimers(); if (!words) setTimeout(finish, 600); showTtsNote(true); return; }
    var u = new window.SpeechSynthesisUtterance(text);
    u.lang = 'en-US';
    u.rate = rate;
    var voice = pickVoice();
    if (voice) u.voice = voice;
    u.onstart = function () { if (speaking.id === id) startTimers(); };
    u.onboundary = function (e) {
      if (speaking.id !== id || !words || (e.name && e.name !== 'word')) return;
      boundarySeen = true;
      clearTimers();
      var idx = -1;
      for (var i = 0; i < offsets.length; i++) if (offsets[i] <= e.charIndex) idx = i;
      if (idx >= 0) setActive(idx);
    };
    u.onend = finish;
    u.onerror = function (e) {
      if (speaking.id !== id) return;
      if (e && e.error && e.error !== 'canceled' && e.error !== 'interrupted') showTtsNote(true);
      finish();
    };
    speaking.timers.push(setTimeout(startTimers, 400));
    try { synth.speak(u); } catch (e) { showTtsNote(true); startTimers(); }
    if (!voice && synth.getVoices && synth.getVoices().length === 0) showTtsNote(false);
  }
  /* 按队列逐项朗读（逐词慢读、点词单读共用）：steps 来自 EN.wordPlan / EN.tapPlan，每项 {idx, text, rate, gapMs}。
   * 读到哪项就 setActive(idx)；项与项之间停 gapMs。没有语音或事件不触发时，按词长估算时间推进，高亮节奏不变。 */
  function speakSeq(steps, opts) {
    opts = opts || {};
    stopSpeaking();
    var id = speaking.id;
    speaking.onActive = opts.onActive || null;
    if (!synth) showTtsNote(true);
    function later(fn, ms) { speaking.timers.push(setTimeout(fn, ms)); }
    function end() {
      if (speaking.id !== id) return;
      clearTimers();
      setActive(-1);
      if (opts.onEnd) opts.onEnd();
    }
    function run(k) {
      if (speaking.id !== id) return;
      if (k >= steps.length) { end(); return; }
      var s = steps[k];
      var done = false;
      var est = (0.3 + 0.07 * s.text.length) / s.rate * 1000;
      function next() {
        if (done || speaking.id !== id) return;
        done = true;
        clearTimers();
        if (k + 1 >= steps.length) { end(); return; }
        later(function () { run(k + 1); }, s.gapMs);
      }
      setActive(s.idx);
      if (!synth) { later(next, est); return; }
      var u = new window.SpeechSynthesisUtterance(s.text);
      u.lang = 'en-US';
      u.rate = s.rate;
      var voice = pickVoice();
      if (voice) u.voice = voice;
      u.onend = next;
      u.onerror = function (e) {
        if (speaking.id !== id) return;
        if (e && e.error && e.error !== 'canceled' && e.error !== 'interrupted') showTtsNote(true);
        next();
      };
      later(next, est + 2500);
      try { synth.speak(u); } catch (e) { showTtsNote(true); }
    }
    run(0);
  }
  function showTtsNote(hard) {
    if (!ttsNote) return;
    ttsNote.hidden = false;
    ttsNote.textContent = hard
      ? '这个浏览器没有英语朗读，已改成文字高亮：跟着变色的词，自己大声读出来。'
      : '如果没有听到声音，可能是这台设备没有英语语音，可以跟着变色的词自己读。';
  }

  /* ------------------------------------------------------------ 小工具 */

  function seeded(seed) {
    var s = seed % 2147483647;
    if (s <= 0) s += 2147483646;
    return function () { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
  }
  /* 稳定的洗牌：同一句同一个种子顺序固定，且一定不等于原顺序。 */
  function shuffled(n, seed) {
    var idx = [], i;
    for (i = 0; i < n; i++) idx.push(i);
    if (n < 2) return idx;
    var rnd = seeded(seed);
    for (var tries = 0; tries < 20; tries++) {
      for (i = n - 1; i > 0; i--) {
        var j = Math.floor(rnd() * (i + 1));
        var t = idx[i]; idx[i] = idx[j]; idx[j] = t;
      }
      if (idx.some(function (v, k) { return v !== k; })) return idx;
    }
    return idx.slice(1).concat(idx[0]);
  }
  function normalize(s) {
    return String(s || '').toLowerCase().replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function slotOf(entry) {
    var base = tokensOf(entry);
    var slot = -1;
    entry.variants.forEach(function (v) {
      var t = v.en.replace(/[.!?]$/, '').split(' ');
      t.forEach(function (w, i) { if (slot < 0 && w !== base[i]) slot = i; });
    });
    return slot < 0 ? base.length - 1 : slot;
  }

  /* ------------------------------------------------------------ 词卡排序（lesson 与复习共用） */

  /* 返回 { node, reset }；全部放好且顺序正确时调用 onDone。 */
  function sorter(entry, seed, onDone) {
    var tokens = tokensOf(entry);
    var order = shuffled(tokens.length, seed);
    var line = [];
    var solved = false;
    var box = el('div', 'sorter');
    var lineEl = el('div', 'sort-line');
    var poolEl = el('div', 'sort-pool');
    var msg = el('p', 'sort-msg');
    msg.setAttribute('role', 'status');
    var again = btn('重新排', 'small', function () { line = []; solved = false; draw(); });
    box.append(lineEl, poolEl, msg, again);

    function draw() {
      lineEl.textContent = '';
      poolEl.textContent = '';
      tokens.forEach(function (_, slot) {
        var i = line[slot];
        if (i == null) { lineEl.appendChild(el('span', 'sort-slot', String(slot + 1))); return; }
        var c = btn(tokens[i], 'sort-card placed' + (solved ? ' ok' : ''), function () {
          if (solved) return;
          line.splice(slot, 1);
          draw();
        });
        lineEl.appendChild(c);
      });
      order.forEach(function (i) {
        if (line.indexOf(i) >= 0) return;
        poolEl.appendChild(btn(tokens[i], 'sort-card', function () {
          if (solved) return;
          line.push(i);
          check();
          draw();
        }));
      });
      again.hidden = solved || !line.length;
      msg.className = 'sort-msg' + (solved ? ' ok' : '');
    }
    function check() {
      if (line.length < tokens.length) { msg.textContent = ''; return; }
      var ok = line.every(function (i, k) { return tokens[i] === tokens[k]; });
      if (ok) {
        solved = true;
        msg.textContent = '排对了：' + entry.sentence;
        onDone();
      } else {
        msg.textContent = '顺序还不对，点已放下的词可以拿回来，再试试。';
        msg.className = 'sort-msg bad';
        setTimeout(function () { if (!solved && line.length === tokens.length) { line = []; draw(); } }, 900);
      }
    }
    draw();
    return { node: box };
  }

  /* ------------------------------------------------------------ 今日句 / 回看 */

  function lessonCard(entry, mode, onDone) {
    var tokens = tokensOf(entry);
    var checks = { guess: mode === 'revisit', order: mode === 'revisit', build: mode === 'revisit' };
    var spans = [], pairs = [], zhPairs = [], chips = [];
    var card = el('section', 'eng-card lesson');

    function active(i) {
      [spans, pairs, zhPairs, chips].forEach(function (list) {
        list.forEach(function (n, k) { n.classList.toggle('on', k === i); });
      });
    }
    function say(text, words, rate) { speak(text, words, { rate: rate, onActive: active }); }
    function sayByWord() { speakSeq(EN.wordPlan(tokens), { onActive: active }); }
    /* 点词单读：第一下常速读该词，3 秒内再点同一个词读慢速（rate 0.6）；读的时候高亮该词。句子里的词和拆词区词卡共用。 */
    var lastTap = { i: -1, at: 0 };
    function tapWord(i) {
      var now = Date.now();
      var slow = lastTap.i === i && now - lastTap.at <= EN.WORD_TAP.repeatWindowMs;
      lastTap = slow ? { i: -1, at: 0 } : { i: i, at: now };
      speakSeq(EN.tapPlan(tokens[i], i, slow), { onActive: active });
    }

    var head = el('div', 'lesson-head');
    head.appendChild(el('span', 'lesson-no', mode === 'revisit' ? '回看第 ' + entry.day + ' 句' : '第 ' + entry.day + ' 句'));
    head.appendChild(el('span', 'lesson-grammar', mode === 'revisit' ? '' : '约 3 分钟'));
    card.appendChild(head);

    /* 1 听 + 动画 */
    var scene = el('div', 'scene');
    scene.innerHTML = SCENES.render(entry.scene, entry.sceneProps);
    card.appendChild(scene);
    var sentence = el('p', 'sentence');
    tokens.forEach(function (w, i) {
      var s = el('span', 'w tap ' + wc(i), w);
      s.setAttribute('role', 'button');
      s.tabIndex = 0;
      s.title = '点一下听这个词，再点一下慢读';
      s.addEventListener('click', function () { tapWord(i); });
      s.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tapWord(i); } });
      spans.push(s);
      if (i) sentence.appendChild(document.createTextNode(' '));
      sentence.appendChild(s);
    });
    sentence.appendChild(el('span', 'punct', entry.sentence.slice(-1)));
    card.appendChild(sentence);
    var listen = el('div', 'row');
    listen.appendChild(btn('听一遍', 'primary', function () { say(entry.sentence, tokens, 1); }));
    listen.appendChild(btn('逐词慢读', null, sayByWord));
    card.appendChild(listen);
    ttsNote = el('p', 'tts-note muted');
    ttsNote.hidden = true;
    card.appendChild(ttsNote);
    card.appendChild(el('p', 'step-hint', '先看动画，猜猜这句话是什么意思，再往下翻开答案。点句子里的词可以单独听，再点一下慢读。'));

    /* 2 三层翻译 */
    var trans = el('div', 'layers');
    function layer(title, fill) {
      var d = el('details', 'layer');
      d.appendChild(el('summary', null, title));
      var body = el('div', 'layer-body');
      fill(body);
      d.appendChild(body);
      d.addEventListener('toggle', function () { if (d.open) mark('guess'); });
      trans.appendChild(d);
    }
    layer('第 1 层：逐词对照', function (b) {
      var row = el('div', 'pairs');
      entry.words.forEach(function (w, i) {
        var p = el('span', 'pair ' + wc(i));
        p.appendChild(el('b', null, w.en));
        p.appendChild(el('i', null, w.zh));
        pairs.push(p);
        row.appendChild(p);
      });
      b.appendChild(row);
    });
    layer('第 2 层：照字面连起来', function (b) {
      var row = el('p', 'literal');
      entry.words.forEach(function (w, i) {
        var s = el('span', 'zh ' + wc(i), w.zh);
        zhPairs.push(s);
        row.appendChild(s);
        row.appendChild(document.createTextNode(' '));
      });
      b.appendChild(row);
    });
    layer('第 3 层：整句的意思', function (b) { b.appendChild(el('p', 'meaning', entry.translation)); });
    card.appendChild(trans);

    /* 3 拆词发音 */
    card.appendChild(el('h3', 'sec', '拆词发音（点词卡听，再点一下慢读）'));
    var chipRow = el('div', 'chips');
    entry.words.forEach(function (w, i) {
      var c = btn('', 'chip ' + wc(i), function () { tapWord(i); });
      c.appendChild(el('span', 'en', w.en));
      c.appendChild(el('span', 'zh', w.zh));
      chips.push(c);
      chipRow.appendChild(c);
    });
    card.appendChild(chipRow);
    if (entry.tip) card.appendChild(el('p', 'tip', '易错提醒：' + entry.tip));

    /* 4 跟读（可选） */
    card.appendChild(el('h3', 'sec', '跟读（可选，不影响打卡）'));
    card.appendChild(el('p', 'step-hint', '先慢后快，跟着变色的词大声读一遍。不需要录音。'));
    var follow = el('div', 'row');
    follow.appendChild(btn('逐词慢读', null, sayByWord));
    follow.appendChild(btn('常速跟读', null, function () { say(entry.sentence, tokens, 1); }));
    card.appendChild(follow);

    /* 5 词卡排序 */
    card.appendChild(el('h3', 'sec', '词卡排序：把句子写出来'));
    var sortBox = sorter(entry, entry.day * 7 + 3, function () { mark('order'); say(entry.sentence, tokens, 1); });
    card.appendChild(sortBox.node);

    /* 6 换词造句 */
    card.appendChild(el('h3', 'sec', '换词造句：换一个词，造新句子'));
    var slot = slotOf(entry);
    var built = el('p', 'built');
    var builtZh = el('p', 'built-zh muted');
    var chosen = null;
    function drawBuilt() {
      built.textContent = '';
      tokens.forEach(function (w, i) {
        if (i) built.appendChild(document.createTextNode(' '));
        if (i !== slot) { built.appendChild(el('span', 'w plain', w)); }
        else built.appendChild(el('span', 'w slot' + (chosen ? ' filled' : ''), chosen ? chosen.word : '＿＿＿'));
      });
      built.appendChild(el('span', 'punct', entry.sentence.slice(-1)));
      builtZh.textContent = chosen ? chosen.zh : '点下面的词，换进句子里。';
    }
    drawBuilt();
    card.append(built, builtZh);
    var opts = el('div', 'chips variants');
    entry.variants.forEach(function (v) {
      var word = v.en.replace(/[.!?]$/, '').split(' ')[slot];
      opts.appendChild(btn(word, 'chip plain', function () {
        chosen = { word: word, zh: v.zh };
        drawBuilt();
        speak(v.en, null, { rate: 0.9 });
        mark('build');
      }));
    });
    card.appendChild(opts);

    /* 7 打卡 */
    var checkBox = el('div', 'checks');
    var checkEls = {};
    [['guess', '猜出意思'], ['order', '排序正确'], ['build', '完成造句']].forEach(function (c) {
      var s = el('span', 'check' + (checks[c[0]] ? ' done' : ''), (checks[c[0]] ? '✓ ' : '○ ') + c[1]);
      checkEls[c[0]] = { node: s, label: c[1] };
      checkBox.appendChild(s);
    });
    if (mode !== 'revisit') card.appendChild(el('h3', 'sec', '今日三项打卡'));
    if (mode !== 'revisit') card.appendChild(checkBox);
    var finishBtn = btn('完成今日一句', 'primary finish', function () { if (EN.checksComplete(checks)) onDone(checks); });
    finishBtn.disabled = true;
    if (mode !== 'revisit') card.appendChild(finishBtn);

    function mark(key) {
      if (checks[key]) return;
      checks[key] = true;
      var c = checkEls[key];
      c.node.className = 'check done';
      c.node.textContent = '✓ ' + c.label;
      finishBtn.disabled = !EN.checksComplete(checks);
    }
    return card;
  }

  /* ------------------------------------------------------------ 旧句复习：排序 + 听写 */

  function reviewCard(r) {
    var entry = entryOf(r.day);
    var tokens = tokensOf(entry);
    var card = el('article', 'rev-card');
    var state = { order: false, dictation: false };
    card.appendChild(el('h3', null, '复习第 ' + r.day + ' 句（第 ' + r.stage + ' 轮）'));
    card.appendChild(el('p', 'muted', '先排词卡，再听写。排对、写对就算完成。'));

    var sc = el('div', 'scene small');
    sc.innerHTML = SCENES.render(entry.scene, entry.sceneProps);
    card.appendChild(sc);

    card.appendChild(el('h4', null, '1. 词卡排序'));
    card.appendChild(sorter(entry, entry.day * 11 + r.stage, function () { state.order = true; update(); }).node);

    card.appendChild(el('h4', null, '2. 听写'));
    var voiceless = !synth;
    card.appendChild(el('p', 'step-hint', voiceless ? '这个浏览器没有英语朗读：请对照上面的动画，把这句英语凭记忆写出来。' : '点「播放」听一遍，把听到的句子写下来。'));
    var row = el('div', 'row');
    if (!voiceless) {
      row.appendChild(btn('播放', 'primary', function () { speak(entry.sentence, null, { rate: 1 }); }));
      row.appendChild(btn('慢速播放', null, function () { speak(entry.sentence, null, { rate: 0.6 }); }));
    }
    card.appendChild(row);
    var input = el('input');
    input.type = 'text';
    input.className = 'dictation';
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('spellcheck', 'false');
    input.setAttribute('aria-label', '听写答案');
    card.appendChild(input);
    var msg = el('p', 'sort-msg');
    msg.setAttribute('role', 'status');
    var submit = btn('检查听写', null, function () {
      if (normalize(input.value) === normalize(entry.sentence)) {
        state.dictation = true;
        msg.className = 'sort-msg ok';
        msg.textContent = '写对了：' + entry.sentence;
        input.disabled = true;
        submit.disabled = true;
        update();
      } else {
        msg.className = 'sort-msg bad';
        msg.textContent = '还差一点，再听一遍、检查拼写和空格。（共 ' + tokens.length + ' 个词）';
      }
    });
    card.append(submit, msg);
    var done = btn('完成这次复习', 'primary', function () {
      if (EN.completeReview(childId, r.day)) { flash = '第 ' + r.day + ' 句复习完成。'; render(); }
      else { msg.className = 'sort-msg bad'; msg.textContent = '没能保存复习结果，请稍后再试。'; }
    });
    done.disabled = true;
    card.appendChild(done);
    function update() { done.disabled = !(state.order && state.dictation); }
    return card;
  }

  /* ------------------------------------------------------------ 进度日历、完成卡 */

  function streakText() {
    var n = window.CnmActivity ? window.CnmActivity.streak(childId, Date.now()) : 0;
    return n > 0 ? '连续学习 ' + n + ' 天' : '';
  }

  function calendar(st) {
    var box = el('section', 'eng-card calendar');
    var b = EN.progress(childId);
    var head = el('div', 'cal-head');
    head.appendChild(el('strong', null, '30 天进度：已学 ' + st.doneCount + ' / ' + st.total + ' 句'));
    var s = streakText();
    if (s) head.appendChild(el('span', 'streak', s));
    box.appendChild(head);
    var bar = el('div', 'cal-bar');
    var fill = el('i');
    fill.style.width = Math.round(st.doneCount / st.total * 100) + '%';
    bar.appendChild(fill);
    box.appendChild(bar);
    var grid = el('div', 'cal-grid');
    for (var d = 1; d <= st.total; d++) {
      (function (day) {
        var isDone = !!(b.done[day] && typeof b.done[day] === 'object');
        var isToday = day === st.day && !st.finished;
        var cls = 'cal-cell' + (isDone ? ' done' : '') + (isToday ? ' today' : '') + (!isDone && !isToday ? ' locked' : '');
        var c = btn(isDone ? '✓' : String(day), cls, null);
        c.setAttribute('aria-label', '第 ' + day + ' 句' + (isDone ? '，已完成，点击回看' : (isToday ? '，今天学这句' : '，未解锁')));
        if (isDone) c.addEventListener('click', function () { view = { mode: 'revisit', day: day }; render(); window.scrollTo(0, 0); });
        else c.disabled = !isToday;
        if (isToday) c.addEventListener('click', function () { view = { mode: 'today', day: null }; render(); });
        grid.appendChild(c);
      })(d);
    }
    box.appendChild(grid);
    return box;
  }

  function doneCard(st, entry) {
    var card = el('section', 'eng-card complete');
    card.appendChild(el('h2', null, st.finished ? '30 句全部学完了' : '今天的一句学完了'));
    if (entry) {
      card.appendChild(el('p', 'sentence plain', entry.sentence));
      card.appendChild(el('p', 'muted', entry.translation));
    }
    var meta = [];
    meta.push('已学 ' + st.doneCount + ' / ' + st.total + ' 句');
    var s = streakText();
    if (s) meta.push(s);
    card.appendChild(el('p', 'complete-meta', meta.join(' · ')));
    var row = el('div', 'row');
    if (entry) {
      row.appendChild(btn('再听一遍', null, function () { speak(entry.sentence, null, { rate: 1 }); }));
      row.appendChild(btn('再看一遍', null, function () { view = { mode: 'revisit', day: entry.day }; render(); window.scrollTo(0, 0); }));
    }
    card.appendChild(row);
    if (st.finished) {
      card.appendChild(el('p', 'preview', '敬请期待下一阶段。已学的句子可以在下面的进度表里随时回看。'));
    } else if (st.nextDay) {
      var next = entryOf(st.nextDay);
      var pv = el('div', 'preview');
      pv.appendChild(el('strong', null, '明日预告'));
      pv.appendChild(el('p', null, '明天学第 ' + st.nextDay + ' 句：' + next.sentence));
      card.appendChild(pv);
    }
    return card;
  }

  /* ------------------------------------------------------------ 页面 */

  function renderPicker() {
    picker.textContent = '';
    var kids = CC.list();
    var guestN = EN.doneCount(GUEST);
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
    if (guestN) {
      var g = el('option', null, '未建档时学的（' + guestN + ' 句）');
      g.value = GUEST;
      sel.appendChild(g);
    }
    sel.value = childId;
    sel.addEventListener('change', function () {
      childId = sel.value;
      view = { mode: 'today', day: null };
      flash = '';
      if (childId !== GUEST) CC.setCurrent(childId);
      history.replaceState(null, '', location.pathname + (childId !== GUEST ? '?child=' + encodeURIComponent(childId) : ''));
      render();
    });
    picker.append(label, sel);
    var manage = el('a', 'btn', '管理档案');
    manage.href = '../children/';
    picker.appendChild(manage);
  }

  function render() {
    stopSpeaking();
    renderPicker();
    app.textContent = '';
    if (!days) return;
    var kids = CC.list();
    var st = EN.todayState(childId, Date.now());
    if (flash) {
      var note = el('p', 'eng-flash', flash);
      note.setAttribute('role', 'status');
      app.appendChild(note);
      flash = '';
    }
    if (!kids.length) app.appendChild(el('p', 'kid-empty', '还没建孩子档案，进度先记在这台浏览器的游客名下。'));

    if (view.mode === 'revisit' && view.day) {
      var back = btn('← 回到今天', null, function () { view = { mode: 'today', day: null }; render(); });
      back.className = 'back';
      app.appendChild(back);
      app.appendChild(lessonCard(entryOf(view.day), 'revisit', null));
      app.appendChild(calendar(st));
      return;
    }

    if (st.reviews.length) {
      var rev = el('section', 'eng-card review');
      rev.appendChild(el('h2', null, '今日复习（' + st.reviews.length + ' 句）' + (st.reviewTotal > st.reviews.length ? '，还有 ' + (st.reviewTotal - st.reviews.length) + ' 句明天再复习' : '')));
      rev.appendChild(el('p', 'muted', '学过的句子隔几天回头看一次：排词卡、听写，不占新句名额。'));
      st.reviews.forEach(function (r) { rev.appendChild(reviewCard(r)); });
      app.appendChild(rev);
    }

    if (st.finished || st.completedToday) {
      app.appendChild(doneCard(st, st.day ? entryOf(st.day) : null));
    } else if (st.day) {
      var lesson = lessonCard(entryOf(st.day), 'new', function (checks) {
        var res = EN.completeDay(childId, st.day, checks, Date.now());
        if (res.ok) { flash = ''; render(); window.scrollTo(0, 0); }
        else if (res.error === 'today') { flash = '今天已经学过一句了，明天再来。'; render(); }
        else { flash = '没能保存进度，请稍后再试。'; render(); }
      });
      app.appendChild(lesson);
    }
    app.appendChild(calendar(st));
  }

  function start(data) {
    days = data;
    var want = new URLSearchParams(location.search).get('child');
    var cur = CC.current();
    var kids = CC.list();
    childId = (want && CC.get(want) && want) || (cur && cur.id) || (kids[0] && kids[0].id) || GUEST;
    render();
  }

  fetch('../data/english/days.json').then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function (data) {
    if (!Array.isArray(data) || data.length !== EN.TOTAL) throw new Error('句子表格式不对');
    start(data);
  }).catch(function (e) {
    app.textContent = '';
    app.appendChild(el('p', 'load-error', '句子表没有加载成功（' + (e && e.message ? e.message : e) + '）。请检查网络后刷新页面。'));
  });

  window.addEventListener('cnm:sync', function (ev) {
    var s = ev && ev.detail;
    if (!days || !s || s.state !== 'applied') return;
    if (view.mode === 'today' && !document.querySelector('.lesson .check.done')) render();
  });
  window.addEventListener('pagehide', stopSpeaking);
})();
