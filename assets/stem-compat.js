/* 题干身份：同一题号被改写后，没有题干快照的旧作答不能算到新题上。
 * 目前只处理 cnc_p124_q3 / q4。B 提交 43c1ea0 在这两个 id 下把古诗改成了语气。
 * q1 / q2 的题干没变。旧的知识点级结论没有逐题快照，不能证明没用到 q3 / q4，
 * 所以不计入现在的语气，也不改记到 cnc_p494。浏览器里是 window.StemCompat，Node 里可 require。 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.StemCompat = api;
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var TOPIC = 'cnc_p124';
  var REV = 'tone-2026-11-07';
  /* 与 d3e2dac（43c1ea0 的父提交）里的题干一致。现行题干见 CURRENT。 */
  var RETIRED = {
    cnc_p124_q3: '「离离原上草」的下一句是哪一句？',
    cnc_p124_q4: '「野火烧不尽」的下一句是哪一句？作者是谁？'
  };
  var CURRENT = {
    cnc_p124_q3: '同学把水洒在你身上，你要提醒他，怎样说更合适？',
    cnc_p124_q4: '做错了事向别人道歉，下面哪一句语气更合适？'
  };

  function isRetiredQid(qid) { return Object.prototype.hasOwnProperty.call(RETIRED, qid); }

  /* 有现行题干快照才算这道新题。没有快照，或快照仍是旧诗句，都不算语气。 */
  function answerExcluded(answer) {
    if (!answer || !isRetiredQid(answer.qid)) return false;
    return answer.prompt !== CURRENT[answer.qid];
  }

  function sessionEffect(answers) {
    var keep = [];
    var retest = Object.create(null);
    (answers || []).forEach(function (answer) {
      if (answerExcluded(answer)) {
        if (answer.id) retest[answer.id] = true;
        return;
      }
      keep.push(answer);
    });
    return { answers: keep, retestTopicIds: Object.keys(retest) };
  }

  function prepareReplayAnswers(answers) {
    var effect = sessionEffect(answers);
    return {
      answers: effect.answers.map(function (answer) {
        if (answer && answer.qid) {
          var copy = {};
          Object.keys(answer).forEach(function (key) { copy[key] = answer[key]; });
          copy.pin = true;
          return copy;
        }
        return answer;
      }),
      excluded: (answers || []).filter(answerExcluded).map(function (answer) {
        return {
          id: answer.id,
          qid: answer.qid,
          result: answer.result,
          prompt: typeof answer.prompt === 'string' && answer.prompt ? answer.prompt : RETIRED[answer.qid],
          reason: 'stem-changed'
        };
      })
    };
  }

  function restoreParts(saved) {
    var prepared = prepareReplayAnswers(saved && saved.answers);
    var excluded = prepared.excluded.length
      ? prepared.excluded
      : (saved && Array.isArray(saved.excluded) ? saved.excluded : []);
    var avoid = ((saved && saved.avoid) || []).filter(function (id) { return !isRetiredQid(id); });
    return { answers: prepared.answers, excluded: excluded, avoid: avoid };
  }

  /* 排除的作答不能显示现行题干。调用方应改显示「不计入」。 */
  function displayPrompt(answer, live) {
    if (answerExcluded(answer)) return null;
    if (live && typeof live.prompt === 'string') return live.prompt;
    if (answer && typeof answer.prompt === 'string') return answer.prompt;
    return '';
  }

  function topicTrusted(carrier, topicId) {
    if (topicId !== TOPIC) return true;
    if (!carrier) return false;
    var stamp = carrier.stemRev;
    if (stamp === REV) return true;
    return !!(stamp && typeof stamp === 'object' && stamp[TOPIC] === REV);
  }

  function stamp() {
    var out = {};
    out[TOPIC] = REV;
    return out;
  }

  /* 不改存储。无现行戳的 cnc_p124 从掌握 / 薄弱 / 不稳里拿掉，标 needsRetest。targets 保留，方便重测。 */
  function presentRecord(record) {
    if (!record || typeof record !== 'object') return record;
    var copy = {};
    Object.keys(record).forEach(function (key) { copy[key] = record[key]; });
    if (topicTrusted(record, TOPIC)) {
      copy.needsRetest = Array.isArray(record.needsRetest) ? record.needsRetest.slice() : [];
      return copy;
    }
    var hit = false;
    ['weak', 'shaky', 'mastered', 'roots'].forEach(function (field) {
      if (!Array.isArray(record[field])) return;
      if (record[field].indexOf(TOPIC) >= 0) hit = true;
      copy[field] = record[field].filter(function (id) { return id !== TOPIC; });
    });
    if (record.counts && typeof record.counts === 'object') {
      var counts = {};
      Object.keys(record.counts).forEach(function (key) { counts[key] = record.counts[key]; });
      ['weak', 'shaky', 'mastered'].forEach(function (field) {
        if (Array.isArray(record[field]) && record[field].indexOf(TOPIC) >= 0 && Number.isInteger(counts[field])) {
          counts[field] = Math.max(0, counts[field] - 1);
        }
      });
      copy.counts = counts;
    }
    if (hit) copy.needsRetest = [TOPIC];
    else copy.needsRetest = Array.isArray(record.needsRetest) ? record.needsRetest.slice() : [];
    return copy;
  }

  return {
    TOPIC: TOPIC,
    REV: REV,
    RETIRED: RETIRED,
    CURRENT: CURRENT,
    isRetiredQid: isRetiredQid,
    answerExcluded: answerExcluded,
    sessionEffect: sessionEffect,
    prepareReplayAnswers: prepareReplayAnswers,
    restoreParts: restoreParts,
    displayPrompt: displayPrompt,
    topicTrusted: topicTrusted,
    stamp: stamp,
    presentRecord: presentRecord
  };
});
