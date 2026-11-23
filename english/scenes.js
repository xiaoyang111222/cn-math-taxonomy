/* 英语每日一句的动画场景：固定简笔小人 + 10 个场景模板。每个模板是一个渲染函数，输入 sceneProps，输出一段内联 SVG 字符串。
 * 动作全部靠 CSS 类（english/style.css 的 .an-*）驱动；带 CSS 动画的元素不写 transform 属性（会被覆盖），位置放在外层 <g>。
 * 浏览器里是 window.CnmEnglishScenes，Node 里 module.exports 同一份（tests/test_english_data.js 检查模板与道具）。 */
(function (root) {
  'use strict';
  var INK = '#334155';
  var SW = 3.5;

  function f(n) { return String(Math.round(n * 100) / 100); }
  function num(v, d) { return typeof v === 'number' && isFinite(v) ? v : d; }

  /* ---------------------------------------------------------------- 小人 */

  function limb(px, py, angle, len, anim, mirror, delay) {
    var rot = mirror ? -angle : angle;
    var style = delay ? ' style="animation-delay:' + delay + 's"' : '';
    return '<g transform="translate(' + px + ' ' + py + ')"><g class="limb' + (anim ? ' ' + anim : '') + '"' + style + '>' +
      '<line transform="rotate(' + f(rot) + ')" x1="0" y1="0" x2="0" y2="' + len + '" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/></g></g>';
  }

  function face(mood) {
    var eyes = '<circle cx="-6" cy="-95" r="2" fill="' + INK + '"/><circle cx="6" cy="-95" r="2" fill="' + INK + '"/>';
    var closed = '<path d="M-9 -95h6M3 -95h6" stroke="' + INK + '" stroke-width="2" stroke-linecap="round" fill="none"/>';
    var mouth = {
      smile: '<path d="M-7 -88Q0 -80 7 -88" stroke="' + INK + '" stroke-width="2.2" stroke-linecap="round" fill="none"/>',
      sad: '<path d="M-6 -83Q0 -90 6 -83" stroke="' + INK + '" stroke-width="2.2" stroke-linecap="round" fill="none"/>',
      flat: '<path d="M-5 -85h10" stroke="' + INK + '" stroke-width="2.2" stroke-linecap="round" fill="none"/>',
      open: '<g class="an-chew"><ellipse cx="0" cy="-85" rx="4.5" ry="5" fill="' + INK + '"/></g>',
      small: '<ellipse cx="0" cy="-85" rx="3" ry="3.5" fill="' + INK + '"/>'
    };
    var m = { happy: 'smile', smile: 'smile', sad: 'sad', tired: 'flat', hungry: 'small', sleepy: 'small', sing: 'open', chew: 'open', flat: 'flat' }[mood] || 'smile';
    var sleepy = mood === 'sleepy' || mood === 'tired';
    return (sleepy ? closed : eyes) + mouth[m];
  }

  /* o: x, y（脚底）, s 缩放, mood, color（上衣）, hair（short / bun）, skirt, shades,
   *    armL / armR / legL / legR（离开身体向下的角度，0 向下、90 水平、180 向上；L 往画面左、R 往画面右）,
   *    aL / aR / lL / lR（动画类）, bob（整体动画类）, tilt（整体前倾角度）, noArms */
  function figure(o) {
    var s = num(o.s, 1);
    var color = o.color || '#0f6e62';
    var hair = '';
    if (o.hair === 'short') hair = '<path d="M-16 -92A16 16 0 0 1 16 -92Q8 -102 0 -101Q-8 -102 -16 -92Z" fill="' + INK + '"/>';
    if (o.hair === 'bun') hair = '<circle cx="0" cy="-111" r="7" fill="' + INK + '"/><path d="M-16 -92A16 16 0 0 1 16 -92Q8 -103 0 -102Q-8 -103 -16 -92Z" fill="' + INK + '"/>';
    var skirt = o.skirt ? '<path d="M-10 -58L-20 -34H20L10 -58Z" fill="' + color + '" stroke="' + INK + '" stroke-width="2.5" stroke-linejoin="round"/>' : '';
    var shades = o.shades ? '<rect x="-11" y="-99" width="9" height="6" rx="2.4" fill="' + INK + '"/><rect x="2" y="-99" width="9" height="6" rx="2.4" fill="' + INK + '"/><path d="M-2 -96h4" stroke="' + INK + '" stroke-width="1.6"/>' : '';
    var arms = o.noArms ? '' :
      limb(0, -70, num(o.armL, 14), 28, o.aL, false) + limb(0, -70, num(o.armR, 14), 28, o.aR, true);
    var legs = limb(0, -38, num(o.legL, 8), 38, o.lL, false) + limb(0, -38, num(o.legR, 8), 38, o.lR, true);
    var tilt = o.tilt ? ' rotate(' + o.tilt + ')' : '';
    return '<g transform="translate(' + f(o.x) + ' ' + f(num(o.y, 172)) + ') scale(' + f(s) + ')' + tilt + '"><g class="' + (o.bob || '') + '">' +
      legs +
      '<rect x="-9" y="-76" width="18" height="38" rx="7" fill="' + color + '" stroke="' + INK + '" stroke-width="3"/>' + skirt +
      arms +
      '<circle cx="0" cy="-92" r="16" fill="#fff" stroke="' + INK + '" stroke-width="' + SW + '"/>' + hair + face(o.mood || 'smile') + shades +
      '</g></g>';
  }

  /* ---------------------------------------------------------------- 道具 */

  function stroke(extra) { return ' stroke="' + INK + '" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"' + (extra || ''); }

  /* 每个道具以「底部中心」为原点向上画，宽约 ≤ 44、高约 ≤ 50。 */
  var ITEMS = {
    apple: function () {
      return '<circle cx="0" cy="-14" r="14" fill="#ef4444"' + stroke() + '/><path d="M0 -28Q2 -35 8 -37" fill="none"' + stroke() + '/><ellipse cx="8" cy="-34" rx="6" ry="3" fill="#22c55e"' + stroke(' transform="rotate(-25 8 -34)"') + '/>';
    },
    milk: function () {
      return '<rect x="-11" y="-38" width="22" height="38" rx="2" fill="#fff"' + stroke() + '/><path d="M-11 -38L-6 -49H6L11 -38Z" fill="#dbeafe"' + stroke() + '/><rect x="-11" y="-26" width="22" height="12" fill="#60a5fa"' + stroke() + '/>';
    },
    cake: function () {
      return '<rect x="-19" y="-20" width="38" height="20" rx="4" fill="#fcd9b6"' + stroke() + '/><rect x="-19" y="-27" width="38" height="9" rx="4" fill="#f9a8d4"' + stroke() + '/><rect x="-2" y="-39" width="4" height="12" fill="#fbbf24"' + stroke(' stroke-width="1.8"') + '/><ellipse cx="0" cy="-43" rx="3" ry="4.5" fill="#f97316"/>';
    },
    cat: function () {
      return '<path d="M12 -6Q30 -8 26 -26" fill="none"' + stroke(' stroke-width="4"') + '/><ellipse cx="0" cy="-14" rx="15" ry="14" fill="#fbbf24"' + stroke() + '/>' +
        '<circle cx="0" cy="-36" r="12" fill="#fbbf24"' + stroke() + '/><path d="M-11 -42L-10 -54L-2 -47ZM11 -42L10 -54L2 -47Z" fill="#fbbf24"' + stroke() + '/>' +
        '<circle cx="-4.5" cy="-37" r="1.7" fill="' + INK + '"/><circle cx="4.5" cy="-37" r="1.7" fill="' + INK + '"/><path d="M-2 -32L0 -30L2 -32" fill="none" stroke="' + INK + '" stroke-width="1.6" stroke-linecap="round"/>' +
        '<path d="M-14 -34h-7M-14 -31l-6 2M14 -34h7M14 -31l6 2" stroke="' + INK + '" stroke-width="1.3" stroke-linecap="round"/>';
    },
    dog: function () {
      return '<path d="M13 -10Q26 -14 24 -26" fill="none"' + stroke(' stroke-width="4"') + '/><ellipse cx="0" cy="-14" rx="16" ry="13" fill="#d6a46c"' + stroke() + '/>' +
        '<circle cx="0" cy="-36" r="13" fill="#d6a46c"' + stroke() + '/><ellipse cx="-14" cy="-36" rx="5" ry="10" fill="#a16d3b"' + stroke() + '/><ellipse cx="14" cy="-36" rx="5" ry="10" fill="#a16d3b"' + stroke() + '/>' +
        '<circle cx="-4.5" cy="-38" r="1.7" fill="' + INK + '"/><circle cx="4.5" cy="-38" r="1.7" fill="' + INK + '"/><ellipse cx="0" cy="-32" rx="3.4" ry="2.6" fill="' + INK + '"/>' +
        '<path d="M-4 -27Q0 -23 4 -27" fill="none" stroke="' + INK + '" stroke-width="1.6" stroke-linecap="round"/>';
    },
    book: function () {
      return '<rect x="-17" y="-24" width="34" height="24" rx="2" fill="#60a5fa"' + stroke() + '/><path d="M-11 -24V0" stroke="' + INK + '" stroke-width="2"/><rect x="-5" y="-17" width="16" height="3.5" rx="1.5" fill="#fff"/><rect x="-5" y="-10" width="11" height="3.5" rx="1.5" fill="#fff"/>';
    },
    story: function () {
      return ITEMS.book() + '<path d="M16 -30l2.4 5 5.4.7-4 3.7 1 5.4-4.8-2.7-4.8 2.7 1-5.4-4-3.7 5.4-.7Z" fill="#fbbf24"' + stroke(' stroke-width="1.6"') + '/>';
    }
  };
  function item(name, x, y, s, cls, delay) {
    var draw = ITEMS[name];
    if (!draw) return '';
    var style = delay ? ' style="animation-delay:' + delay + 's"' : '';
    return '<g transform="translate(' + f(x) + ' ' + f(y) + ') scale(' + f(s || 1) + ')"><g class="' + (cls || '') + '"' + style + '>' + draw() + '</g></g>';
  }

  /* ---------------------------------------------------------------- 小装饰 */

  function heart(x, y, s, delay) {
    return '<g transform="translate(' + f(x) + ' ' + f(y) + ') scale(' + f(s) + ')"><g class="an-float" style="animation-delay:' + delay + 's">' +
      '<path d="M0 -4C-8 -14 -18 -2 0 10C18 -2 8 -14 0 -4Z" fill="#ef4444"/></g></g>';
  }
  function note(x, y, ch, delay) {
    return '<g transform="translate(' + f(x) + ' ' + f(y) + ')"><g class="an-float" style="animation-delay:' + delay + 's">' +
      '<text font-size="24" font-weight="700" fill="#7c3aed" text-anchor="middle">' + ch + '</text></g></g>';
  }
  function zzz(x, y) {
    return '<g transform="translate(' + f(x) + ' ' + f(y) + ')">' +
      '<g class="an-float" style="animation-delay:0s"><text font-size="22" font-weight="800" fill="#6366f1" text-anchor="middle">Z</text></g>' +
      '<g transform="translate(14 -14)"><g class="an-float" style="animation-delay:.7s"><text font-size="17" font-weight="800" fill="#6366f1" text-anchor="middle">z</text></g></g>' +
      '<g transform="translate(26 -26)"><g class="an-float" style="animation-delay:1.4s"><text font-size="13" font-weight="800" fill="#6366f1" text-anchor="middle">z</text></g></g></g>';
  }
  function star(x, y, s, delay) {
    return '<g transform="translate(' + f(x) + ' ' + f(y) + ') scale(' + f(s) + ')"><g class="an-twinkle" style="animation-delay:' + delay + 's">' +
      '<path d="M0 -7L2 -2 7 0 2 2 0 7-2 2-7 0-2-2Z" fill="#fbbf24"/></g></g>';
  }
  function sun(x, y, r) {
    var rays = '';
    for (var i = 0; i < 8; i++) rays += '<line transform="rotate(' + i * 45 + ')" x1="0" y1="' + -(r + 6) + '" x2="0" y2="' + -(r + 15) + '" stroke="#f59e0b" stroke-width="4" stroke-linecap="round"/>';
    return '<g transform="translate(' + x + ' ' + y + ')"><g class="an-spin">' + rays + '</g><circle r="' + r + '" fill="#fbbf24" stroke="#f59e0b" stroke-width="3"/></g>';
  }
  function moon(x, y) {
    return '<g transform="translate(' + x + ' ' + y + ')"><path d="M0 -20A20 20 0 1 0 20 4A16 16 0 0 1 0 -20Z" fill="#fde68a"/></g>';
  }
  function cloud(x, y, fill, cls) {
    return '<g transform="translate(' + x + ' ' + y + ')"><g class="' + (cls || '') + '"><path d="M-30 12Q-44 12 -42 -2Q-40 -14 -26 -12Q-22 -28 -4 -26Q10 -38 24 -22Q42 -22 42 -4Q44 12 28 12Z" fill="' + fill + '" stroke="' + INK + '" stroke-width="2.5" stroke-linejoin="round"/></g></g>';
  }
  function house(x, y) {
    return '<g transform="translate(' + x + ' ' + y + ')"><path d="M0 0V-46L34 -76L68 -46V0Z" fill="#fff7ed"' + stroke() + '/><path d="M-6 -44L34 -80L74 -44" fill="none"' + stroke(' stroke="#b45309" stroke-width="4"') + '/>' +
      '<rect x="26" y="-26" width="16" height="26" rx="2" fill="#fbbf24"' + stroke(' stroke-width="2"') + '/><rect x="48" y="-40" width="12" height="12" fill="#bae6fd"' + stroke(' stroke-width="2"') + '/></g>';
  }
  function bubble(x, y, w, h) {
    return '<g transform="translate(' + x + ' ' + y + ')"><ellipse cx="' + w / 2 + '" cy="' + h / 2 + '" rx="' + w / 2 + '" ry="' + h / 2 + '" fill="#fff"' + stroke(' stroke-width="2.2"') + '/>' +
      '<circle cx="' + (w * 0.18) + '" cy="' + (h + 8) + '" r="5" fill="#fff"' + stroke(' stroke-width="2"') + '/><circle cx="' + (w * 0.06) + '" cy="' + (h + 20) + '" r="3" fill="#fff"' + stroke(' stroke-width="2"') + '/></g>';
  }
  function ground(fill) {
    return '<path d="M0 172H320V200H0Z" fill="' + (fill || '#dcefe3') + '"/><path d="M0 172H320" stroke="' + INK + '" stroke-width="2" opacity=".35"/>';
  }
  function frame(label, bg, inner) {
    return '<svg class="scene-svg" viewBox="0 0 320 200" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg">' +
      '<rect width="320" height="200" rx="14" fill="' + bg + '"/>' + inner + '</svg>';
  }
  function nightSky() {
    return star(40, 34, 1.2, 0) + star(92, 60, 0.9, 0.6) + star(214, 28, 1, 1.1) + star(172, 52, 0.8, 0.3) + star(290, 78, 1, 0.9) + moon(268, 44);
  }

  /* ---------------------------------------------------------------- 模板 */

  var RENDERERS = {};

  /* 表情：mood = happy / sad / tired / hungry / sleepy；place = home 时背景加一座小房子 */
  RENDERERS.emotion = function (p) {
    var mood = p.mood || 'happy';
    var home = p.place === 'home';
    var x = home ? 112 : 160;
    var o = { x: x, mood: mood, color: '#0f6e62' };
    var extra = '';
    var bg = '#eef6ff';
    if (mood === 'happy') {
      o.armL = 128; o.armR = 128; o.aL = 'an-wave'; o.aR = 'an-wave2'; o.bob = 'an-bob';
      extra = star(x - 56, 70, 1.3, 0) + star(x + 58, 56, 1.1, 0.5) + star(x + 40, 100, 0.9, 1);
    } else if (mood === 'sad') {
      o.armL = 8; o.armR = 8; bg = '#e8edf5';
      extra = cloud(x, 38, '#cbd5e1') + '<g transform="translate(' + (x - 6) + ' 76)"><g class="an-drop"><path d="M0 0Q-4 6 0 9Q4 6 0 0Z" fill="#60a5fa"/></g></g>' +
        '<g transform="translate(' + (x + 10) + ' 66)"><g class="an-drop" style="animation-delay:.8s"><path d="M0 0Q-4 6 0 9Q4 6 0 0Z" fill="#60a5fa"/></g></g>';
    } else if (mood === 'tired') {
      o.armL = 6; o.armR = 6; o.bob = 'an-sway'; bg = '#f1efe8';
      extra = '<g transform="translate(' + (x + 24) + ' 70)"><g class="an-drop"><path d="M0 0Q-5 8 0 11Q5 8 0 0Z" fill="#60a5fa"/></g></g>';
    } else if (mood === 'hungry') {
      o.armL = 30; o.armR = 30; o.bob = 'an-nod';
      extra = '<g class="an-pulse"><path d="M' + (x - 24) + ' 138q-7 5 0 10M' + (x + 24) + ' 138q7 5 0 10" fill="none" stroke="#f97316" stroke-width="2.5" stroke-linecap="round"/></g>' +
        bubble(x + 36, 18, 76, 52) + item('apple', x + 74, 58, 1, 'an-bob');
    } else {
      o.armL = 10; o.armR = 10; o.bob = 'an-nod'; bg = '#e7e9fb';
      extra = zzz(x + 34, 84);
    }
    return frame('小人表情：' + mood, bg, ground() + (home ? house(196, 172) : '') + extra + figure(o));
  };

  /* 指物展示：items 站在右边，小人指着它们；mode = have / like（like 时头顶飘爱心）；place = home 加房子 */
  RENDERERS.show = function (p) {
    var items = (p.items || []).slice(0, 2);
    var xs = items.length > 1 ? [190, 252] : [214];
    var inner = ground() + (p.place === 'home' ? house(196, 172) : '');
    inner += figure({ x: 96, mood: 'smile', armL: 12, armR: 98, aR: 'an-point', bob: 'an-bob' });
    items.forEach(function (name, i) {
      inner += item(name, xs[i], 172, 1.25, 'an-bob', i * 0.4);
      if (p.mode === 'like') inner += heart(xs[i] - 4, 86, 1, i * 0.5);
    });
    return frame('指物展示', '#fff8ec', inner);
  };

  /* 吃喝：mode = eat（咀嚼）/ want（头顶想法泡泡）/ like（爱心）；food、food2 摆在桌上 */
  RENDERERS.eat = function (p) {
    var mode = p.mode || 'eat';
    var inner = ground('#e9e2d0');
    var table = '<rect x="168" y="138" width="124" height="9" rx="3" fill="#d6b88c"' + stroke() + '/><path d="M180 147V172M280 147V172" stroke="' + INK + '" stroke-width="4" stroke-linecap="round"/>';
    var foods = [p.food, p.food2].filter(Boolean);
    var xs = foods.length > 1 ? [204, 256] : [230];
    if (mode === 'want') {
      inner += figure({ x: 110, mood: 'smile', armL: 12, armR: 120, aR: 'an-point' });
      inner += bubble(150, 20, 96, 66) + item(p.food, 198, 74, 1.1, 'an-pulse');
      return frame('想要吃的', '#fff8ec', inner);
    }
    inner += table;
    inner += figure({ x: 104, mood: mode === 'eat' ? 'chew' : 'smile', armL: 12, armR: mode === 'eat' ? 150 : 40, aR: mode === 'eat' ? 'an-eat' : 'an-wave', bob: mode === 'like' ? 'an-bob' : '' });
    foods.forEach(function (name, i) {
      inner += item(name, xs[i], 138, 1.15, mode === 'eat' ? 'an-pulse' : '', i * 0.3);
      if (mode === 'like') inner += heart(xs[i], 74, 1, i * 0.5);
    });
    return frame('吃喝', '#fff8ec', inner);
  };

  function wavePath(h) {
    var d = 'M-40 0Q-30 -7 -20 0';
    for (var x = 0; x <= 360; x += 20) d += 'T' + x + ' 0';
    return d + 'V' + h + 'H-40Z';
  }
  /* 一块会流动的水面：左右边界 x0 / x1，水面线 y，深度 h；clip 用来裁掉流动时多出的部分。 */
  function water(id, x0, x1, y, h, opacity) {
    return '<clipPath id="' + id + '"><rect x="' + x0 + '" y="' + (y - 10) + '" width="' + (x1 - x0) + '" height="' + (h + 10) + '"/></clipPath>' +
      '<g clip-path="url(#' + id + ')" opacity="' + opacity + '"><g transform="translate(0 ' + y + ')"><g class="an-wave-x"><path d="' + wavePath(h) + '" fill="#38bdf8"/></g></g></g>';
  }

  /* 游泳：默认小人在水里划水；mode = want 时小人站在岸边，头顶泡泡里是泳圈；sun = true 加太阳 */
  RENDERERS.swim = function (p) {
    var inner = p.sun ? sun(40, 40, 18) : '';
    if (p.mode === 'want') {
      inner += ground() + water('pool-clip', 150, 320, 146, 54, 0.85) + figure({ x: 70, mood: 'smile', armL: 12, armR: 130, aR: 'an-wave2' });
      inner += bubble(96, 14, 90, 60) + '<g transform="translate(141 44)"><g class="an-pulse"><circle r="15" fill="none" stroke="#f97316" stroke-width="8"/><circle r="15" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="10 14"/></g></g>';
      return frame('想去游泳', '#e8f6ff', inner);
    }
    inner += '<circle cx="146" cy="116" r="15" fill="#fff" stroke="' + INK + '" stroke-width="3.5"/><circle cx="152" cy="113" r="2" fill="' + INK + '"/><path d="M148 121Q153 125 158 121" fill="none" stroke="' + INK + '" stroke-width="2.2" stroke-linecap="round"/>' +
      '<path d="M131 112Q146 98 161 112Z" fill="#0ea5e9" stroke="' + INK + '" stroke-width="2.5" stroke-linejoin="round"/>';
    inner += '<g transform="translate(172 126)"><g class="an-crawl"><line x1="0" y1="0" x2="0" y2="-30" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/></g></g>' +
      '<g transform="translate(172 126)"><g class="an-crawl" style="animation-delay:-1.2s"><line x1="0" y1="0" x2="0" y2="-30" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/></g></g>';
    inner += water('pool-clip', 0, 320, 128, 72, 0.7) + '<rect x="0" y="150" width="320" height="50" fill="#0ea5e9" opacity=".25"/>';
    inner += '<g transform="translate(212 116)"><g class="an-drop"><circle r="3" fill="#fff"/></g></g><g transform="translate(236 110)"><g class="an-drop" style="animation-delay:.6s"><circle r="2.5" fill="#fff"/></g></g>';
    return frame('游泳', '#e8f6ff', inner);
  };

  /* 跑步 */
  RENDERERS.run = function () {
    var lines = '<g class="an-speed"><path d="M20 120H70M10 138H60M30 154H72" stroke="#94a3b8" stroke-width="3.5" stroke-linecap="round"/></g>';
    var inner = ground() + lines +
      figure({ x: 170, mood: 'smile', tilt: 8, armL: 50, armR: 50, aL: 'an-run-a', aR: 'an-run-b', legL: 20, legR: 20, lL: 'an-run-b', lR: 'an-run-a', bob: 'an-bob' }) +
      '<g transform="translate(120 170)"><g class="an-drop"><circle r="4" fill="#cbd5e1"/></g></g>';
    return frame('跑步', '#eef6ff', inner);
  };

  /* 唱歌：extra = song 时音符更多 */
  RENDERERS.sing = function (p) {
    var notes = note(206, 96, '♪', 0) + note(238, 80, '♫', 0.6) + note(80, 90, '♫', 1.1);
    if (p.extra === 'song') notes += note(222, 130, '♪', 0.3) + note(96, 124, '♪', 0.9) + note(176, 40, '♫', 1.4);
    var inner = ground() + notes + figure({ x: 150, mood: 'sing', armL: 130, armR: 130, aL: 'an-wave', aR: 'an-wave2', bob: 'an-bob' });
    return frame('唱歌', '#f4efff', inner);
  };

  /* 睡觉：夜晚、床、盖被子、飘 Z */
  RENDERERS.sleep = function () {
    var inner = nightSky() +
      '<rect x="60" y="150" width="200" height="22" rx="6" fill="#a16207"' + stroke() + '/><rect x="60" y="138" width="14" height="34" rx="4" fill="#a16207"' + stroke() + '/><rect x="246" y="144" width="14" height="28" rx="4" fill="#a16207"' + stroke() + '/>' +
      '<rect x="74" y="136" width="172" height="16" rx="6" fill="#fde68a"' + stroke() + '/>' +
      '<ellipse cx="102" cy="132" rx="24" ry="10" fill="#fff"' + stroke() + '/>' +
      '<circle cx="104" cy="120" r="16" fill="#fff" stroke="' + INK + '" stroke-width="3.5"/><path d="M96 118h6M107 118h6" stroke="' + INK + '" stroke-width="2" stroke-linecap="round"/><path d="M100 126Q104 129 108 126" fill="none" stroke="' + INK + '" stroke-width="2" stroke-linecap="round"/>' +
      '<g class="an-breathe"><rect x="116" y="118" width="136" height="32" rx="12" fill="#60a5fa"' + stroke() + '/><path d="M140 120V148M170 120V148M200 120V148" stroke="#93c5fd" stroke-width="3"/></g>' +
      zzz(132, 92);
    return frame('睡觉', '#1e293b', inner);
  };

  /* 家人：who = all（爸爸、妈妈、我）/ mom / [mom, dad]；mode = like 时飘爱心；我（小个子）指着家人 */
  RENDERERS.family = function (p) {
    var who = p.who || 'all';
    var all = who === 'all';
    var targets = all ? ['dad', 'mom'] : (Array.isArray(who) ? who : [who]);
    var xs = all ? [100, 168] : (targets.length === 2 ? [168, 238] : [208]);
    var inner = ground();
    targets.forEach(function (t, i) {
      inner += t === 'dad'
        ? figure({ x: xs[i], s: 1.05, mood: 'smile', hair: 'short', color: '#1d4ed8', bob: 'an-bob' })
        : figure({ x: xs[i], s: 1, mood: 'smile', hair: 'bun', skirt: true, color: '#be185d', bob: 'an-bob' });
      if (p.mode === 'like') inner += heart(xs[i], 40, 1.1, i * 0.5);
    });
    if (all) {
      inner += figure({ x: 252, s: 0.72, mood: 'smile', armL: 128, armR: 128, aL: 'an-wave', aR: 'an-wave2', bob: 'an-bob' });
      if (p.mode === 'like') inner += heart(252, 70, 0.9, 1);
    } else {
      inner += figure({ x: targets.length === 2 ? 96 : 104, s: 0.78, mood: 'smile', armL: 14, armR: 98, aR: 'an-point' });
    }
    return frame('我的家人', '#fff1f5', inner);
  };

  /* 读书：when = day / night；item = book / story */
  RENDERERS.read = function (p) {
    var night = p.when === 'night';
    var x = 150;
    var arm = function (dx) { return '<path d="M' + x + ' 104L' + (x + dx) + ' 124" fill="none" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/>'; };
    var book = '<g transform="translate(' + x + ' 130)"><path d="M0 -8L-30 -14V12L0 18Z" fill="#fff"' + stroke() + '/><path d="M0 -8L30 -14V12L0 18Z" fill="#fff"' + stroke() + '/>' +
      '<g class="an-flip"><path d="M0 -8L28 -12V10L0 16Z" fill="#e0f2fe"' + stroke(' stroke-width="1.8"') + '/></g>' +
      '<path d="M-24 -4L-6 -1M-24 3L-6 6M6 -1L22 -4M6 6L22 3" stroke="#94a3b8" stroke-width="1.6" stroke-linecap="round"/></g>';
    var inner;
    if (night) {
      inner = nightSky() + '<g transform="translate(250 130)"><path d="M0 0V-34" stroke="#92400e" stroke-width="5" stroke-linecap="round"/><path d="M-12 -34L-6 -50H6L12 -34Z" fill="#fde68a"' + stroke() + '/><circle cx="0" cy="-20" r="46" fill="#fde68a" opacity=".18"/></g>' + ground('#334155');
    } else {
      inner = sun(268, 44, 16) + ground();
    }
    inner += figure({ x: x, mood: 'smile', noArms: true }) + arm(-26) + arm(26) + book;
    if (p.item === 'story') inner += star(x - 52, 84, 1.2, 0) + star(x + 56, 74, 1, 0.6) + star(x + 30, 50, 0.8, 1.1);
    return frame(night ? '夜晚读书' : '白天读书', night ? '#1e293b' : '#eef6ff', inner);
  };

  /* 天气：kind = sunny / rainy；night = true 是夜晚 */
  RENDERERS.weather = function (p) {
    var night = !!p.night;
    var inner = '';
    if (p.kind === 'rainy') {
      inner += (night ? nightSky() : '') + cloud(160, 34, night ? '#64748b' : '#94a3b8') + cloud(240, 52, night ? '#64748b' : '#a8b4c6');
      var drops = '';
      [60, 96, 128, 196, 226, 262, 288].forEach(function (dx, i) {
        drops += '<g transform="translate(' + dx + ' 56)"><g class="an-rain" style="animation-delay:' + (i * 0.18) + 's"><line x1="0" y1="0" x2="-4" y2="12" stroke="#38bdf8" stroke-width="3" stroke-linecap="round"/></g></g>';
      });
      inner += drops + ground(night ? '#475569' : '#cfe3d6') + '<ellipse cx="248" cy="178" rx="30" ry="6" fill="#7dd3fc" opacity=".7"/>';
      inner += figure({ x: 130, mood: 'smile', armL: 14, armR: 120 }) +
        '<g transform="translate(130 172)"><path d="M24 -116V-84" stroke="' + INK + '" stroke-width="3" stroke-linecap="round"/><path d="M-34 -116Q24 -170 82 -116Q53 -126 24 -116Q-5 -126 -34 -116Z" fill="#f87171"' + stroke() + '/></g>';
    } else {
      inner += sun(82, 58, 22) + cloud(250, 44, '#fff', 'an-drift') + ground() + figure({ x: 190, mood: 'smile', shades: true, armL: 14, armR: 128, aR: 'an-wave', bob: 'an-bob' });
    }
    return frame(p.kind === 'rainy' ? '下雨天' : '晴天', night ? '#1e293b' : (p.kind === 'rainy' ? '#dbe4ee' : '#dff1ff'), inner);
  };

  var IDS = Object.keys(RENDERERS);

  function render(id, props) {
    var fn = RENDERERS[id];
    return fn ? fn(props || {}) : '';
  }

  var api = { IDS: IDS, ITEMS: Object.keys(ITEMS), render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CnmEnglishScenes = api;
})(typeof window !== 'undefined' ? window : globalThis);
