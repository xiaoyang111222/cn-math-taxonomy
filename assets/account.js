/* 账号：邮箱验证码登录 + 会话管理 + 页头入口。
 * 登录完全可选；不登录时本站一切照旧，这个文件只往页头放一个「登录」按钮，再按页面里预留的位置
 * （.cnm-nudge-slot[data-nudge]）放可关闭的登录提示，别的什么都不做。
 * 会话令牌存在 localStorage 的 cnmAuth.v1；云同步见 assets/sync.js。window.CnmAccount。 */
(function () {
  'use strict';
  var SESSION_KEY = 'cnmAuth.v1';
  var DEFAULT_API = 'https://api.math.pansgo.com';
  var COOLDOWN_SEC = 60;

  /* 接口地址：灰度时可在控制台 localStorage.setItem('cnmApiBase', 'https://xxx.workers.dev') 覆盖。 */
  function apiBase() {
    var v = window.CNM_API_BASE || lsGet('cnmApiBase') || DEFAULT_API;
    return String(v).replace(/\/+$/, '');
  }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
  function lsRemove(k) { try { localStorage.removeItem(k); } catch (e) { /* 隐私模式 */ } }

  function readSession() {
    try {
      var s = JSON.parse(lsGet(SESSION_KEY));
      if (s && typeof s.token === 'string' && typeof s.email === 'string' && Number(s.exp) > Date.now()) return s;
    } catch (e) { /* 损坏当作没登录 */ }
    return null;
  }
  function isLoggedIn() { return !!readSession(); }
  function email() { var s = readSession(); return s ? s.email : ''; }

  function emitAuth() {
    try { window.dispatchEvent(new CustomEvent('cnm:auth', { detail: { loggedIn: isLoggedIn(), email: email() } })); } catch (e) { /* 老浏览器 */ }
  }

  /* 带会话令牌的请求，resolve { status, data }；网络不通时 reject。 */
  function api(method, path, body) {
    var headers = {};
    var s = readSession();
    if (s) headers.Authorization = 'Bearer ' + s.token;
    var init = { method: method, headers: headers };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(body);
      if (init.body.length < 60000) init.keepalive = true;
    }
    return fetch(apiBase() + path, init).then(function (res) {
      /* 服务端滚动续期：会话被顺延后，本机记的过期时间跟着更新，否则 30 天后本机会误判已过期。 */
      var ext = Number(res.headers && res.headers.get && res.headers.get('X-Session-Expires'));
      var cur = readSession();
      if (ext && cur && cur.token === (s && s.token) && ext > cur.exp) {
        lsSet(SESSION_KEY, JSON.stringify({ token: cur.token, email: cur.email, exp: ext }));
      }
      return res.json().catch(function () { return null; }).then(function (data) { return { status: res.status, data: data }; });
    });
  }

  function requestCode(address) { return api('POST', '/auth/request-code', { email: address }); }
  function verify(address, code, mailConsent, mktConsent) {
    return api('POST', '/auth/verify', { email: address, code: code, mail_consent: !!mailConsent, mkt_consent: !!mktConsent }).then(function (res) {
      if (res.status === 200 && res.data && res.data.token) {
        lsSet(SESSION_KEY, JSON.stringify({ token: res.data.token, email: res.data.email || address, exp: res.data.expires_at }));
        emitAuth();
      }
      return res;
    });
  }
  /* 主动退出：先通知服务端作废令牌（尽力而为），本机数据保留。 */
  function logout() {
    var pending = isLoggedIn() ? api('POST', '/auth/logout').catch(function () { /* 离线也照样退出 */ }) : Promise.resolve();
    lsRemove(SESSION_KEY);
    emitAuth();
    return pending;
  }
  /* 令牌被服务端拒绝（过期 / 被撤销）：只清本机会话。 */
  function expire() {
    lsRemove(SESSION_KEY);
    emitAuth();
  }

  /* ------------------------------------------------------------------ 界面 */

  function h(tag, attrs) {
    var el = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'text') el.textContent = attrs[k];
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) el.setAttribute(k, attrs[k] === true ? '' : attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) if (arguments[i]) el.appendChild(arguments[i]);
    return el;
  }

  var CSS = [
    '.cnm-acc-wrap{display:inline-flex;align-items:center;gap:8px;margin-left:6px;min-width:0}',
    '.nav-link.cnm-account-btn{border:1px solid var(--brand,#0f6e62);background:var(--brand,#0f6e62);color:var(--on-brand,#fff);font:inherit;font-size:1.05rem;font-weight:750;padding:0 18px;cursor:pointer;gap:7px;max-width:15em}',
    '.nav-link.cnm-account-btn:hover{background:var(--brand-strong,#0c574e);color:var(--on-brand,#fff)}',
    '.nav-link.cnm-account-btn.cnm-on{background:var(--brand-soft,#e6f4f1);color:var(--brand-strong,#0c574e);font-size:1rem;padding:0 14px}',
    '.nav-link.cnm-account-btn.cnm-on:hover{background:var(--brand-soft,#e6f4f1);color:var(--brand-strong,#0c574e)}',
    '.nav-link.cnm-account-btn:focus-visible{outline:2px solid var(--focus,#0f6e62);outline-offset:2px}',
    '.cnm-acc-email{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}',
    '.cnm-acc-hint{font-size:.76rem;line-height:1.3;color:var(--muted,#5c6370);white-space:nowrap}',
    '@media (max-width:560px){.cnm-acc-hint{display:none}.cnm-acc-wrap{margin-left:0}.nav-link.cnm-account-btn{font-size:1rem;padding:0 14px;min-height:36px}}',
    '.cnm-nudge{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin:12px 0;padding:10px 8px 10px 14px;border:1px solid var(--line,#e3e6ed);border-radius:var(--radius-sm,10px);background:var(--brand-soft,#e6f4f1);color:var(--text,#17191f);font-size:.92rem;line-height:1.5}',
    '.cnm-nudge[data-kind="home"]{justify-content:center;margin:0;border-width:0 0 1px;border-radius:0;padding:8px 12px}',
    '.cnm-nudge-text{flex:0 1 auto;min-width:0}',
    '.cnm-nudge-go{min-height:36px;padding:0 16px;font:inherit;font-weight:700;border-radius:999px;border:1px solid var(--brand,#0f6e62);background:var(--brand,#0f6e62);color:var(--on-brand,#fff);cursor:pointer;white-space:nowrap}',
    '.cnm-nudge-go:hover{background:var(--brand-strong,#0c574e)}',
    '.cnm-nudge-x{width:36px;height:36px;padding:0;font-size:1.3rem;line-height:1;border:0;border-radius:50%;background:transparent;color:var(--muted,#5c6370);cursor:pointer}',
    '.cnm-nudge-x:hover{background:var(--bg-muted,#eef0f3);color:var(--text,#17191f)}',
    '.cnm-nudge-go:focus-visible,.cnm-nudge-x:focus-visible{outline:2px solid var(--focus,#0f6e62);outline-offset:2px}',
    '@media print{.cnm-acc-wrap,.cnm-nudge{display:none!important}}',
    '.cnm-dot{width:8px;height:8px;border-radius:50%;background:var(--ok,#157a3a);flex:none}',
    '.cnm-dot[data-s="syncing"]{background:var(--warn,#9a3412)}',
    '.cnm-dot[data-s="error"]{background:var(--bad,#b91c1c)}',
    '.cnm-acc-mask{position:fixed;inset:0;z-index:1000;background:rgba(15,23,32,.45);display:flex;align-items:center;justify-content:center;padding:16px}',
    '.cnm-acc-box{width:100%;max-width:380px;max-height:100%;overflow:auto;background:var(--bg-elev,#fff);color:var(--text,#17191f);border:1px solid var(--line,#e3e6ed);border-radius:var(--radius,14px);box-shadow:0 18px 50px rgba(0,0,0,.25);padding:20px 20px 18px;font-family:var(--font,sans-serif)}',
    '.cnm-acc-box h2{margin:0 0 6px;font-size:1.15rem}',
    '.cnm-acc-box p{margin:6px 0;font-size:.9rem;line-height:1.55;color:var(--muted,#5c6370)}',
    '.cnm-acc-box label.cnm-field{display:block;margin:12px 0 4px;font-size:.88rem;font-weight:650}',
    '.cnm-acc-box input[type=email],.cnm-acc-box input[type=text]{width:100%;box-sizing:border-box;padding:10px 12px;font:inherit;font-size:1rem;border:1px solid var(--line,#ccd);border-radius:var(--radius-sm,10px);background:var(--bg,#fff);color:inherit}',
    '.cnm-acc-box input:focus-visible,.cnm-acc-box button:focus-visible{outline:2px solid var(--focus,#0f6e62);outline-offset:2px}',
    '.cnm-acc-box .cnm-check{display:flex;gap:8px;align-items:flex-start;margin:10px 0;font-size:.86rem;line-height:1.5;color:var(--text,#17191f)}',
    '.cnm-acc-box .cnm-check input{margin-top:3px;flex:none}',
    '.cnm-acc-row{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}',
    '.cnm-acc-row button{flex:1 1 auto;min-height:42px;padding:0 14px;font:inherit;font-weight:650;border-radius:var(--radius-sm,10px);border:1px solid var(--line,#ccd);background:var(--bg-muted,#eef0f3);color:inherit;cursor:pointer}',
    '.cnm-acc-row button.cnm-primary{background:var(--brand,#0f6e62);border-color:var(--brand,#0f6e62);color:var(--on-brand,#fff)}',
    '.cnm-acc-row button:disabled{opacity:.55;cursor:default}',
    '.cnm-acc-msg{min-height:1.2em;margin:8px 0 0;font-size:.86rem;color:var(--bad,#b91c1c)}',
    '.cnm-acc-msg.ok{color:var(--ok,#157a3a)}',
    '.cnm-toast{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:1001;max-width:calc(100% - 32px);display:flex;gap:12px;align-items:center;padding:10px 14px;border-radius:999px;background:var(--text,#17191f);color:var(--bg-elev,#fff);font-size:.9rem;box-shadow:0 8px 24px rgba(0,0,0,.25)}',
    '.cnm-toast button{white-space:nowrap;font:inherit;font-weight:700;border:0;background:transparent;color:inherit;text-decoration:underline;cursor:pointer;padding:4px}'
  ].join('\n');

  var wrap = null;
  var button = null;
  var hint = null;
  var dot = null;
  var mask = null;
  var returnFocus = null;
  var syncStatus = { state: 'idle', at: 0, message: '' };

  function syncText() {
    var st = syncStatus.state;
    if (st === 'syncing') return '同步中……';
    if (st === 'error') return '同步没成功：' + (syncStatus.message || '网络不通') + '。改动仍保存在本机，稍后会重试。';
    var eng = window.CnmSyncEngine;
    var at = (eng && eng.lastSyncAt()) || 0;
    if (!at) return '已登录，还没完成第一次同步。';
    var min = Math.floor((Date.now() - at) / 60000);
    return '已同步 · ' + (min < 1 ? '刚刚' : min + ' 分钟前');
  }

  function syncShort() {
    var st = syncStatus.state;
    if (st === 'syncing') return '同步中……';
    if (st === 'error') return '同步未成功';
    var eng = window.CnmSyncEngine;
    var at = (eng && eng.lastSyncAt()) || 0;
    if (!at) return '尚未同步';
    var min = Math.floor((Date.now() - at) / 60000);
    return '已同步 · ' + (min < 1 ? '刚刚' : min + ' 分钟前');
  }

  function refreshButton() {
    if (!button) return;
    var on = isLoggedIn();
    button.className = 'nav-link cnm-account-btn' + (on ? ' cnm-on' : '');
    button.textContent = '';
    if (on) {
      dot = h('span', { class: 'cnm-dot', 'data-s': syncStatus.state === 'syncing' ? 'syncing' : (syncStatus.state === 'error' ? 'error' : 'ok'), 'aria-hidden': 'true' });
      button.appendChild(dot);
      button.appendChild(h('span', { class: 'cnm-acc-email', text: email() }));
      button.setAttribute('aria-label', '账号：' + email());
    } else {
      button.textContent = '登录';
      button.removeAttribute('aria-label');
    }
    button.title = on ? email() + ' · ' + syncText() : '登录后可在多台设备间同步档案和错题（可选）';
    hint.textContent = on ? syncShort() : '登录后换手机不丢';
  }

  function closeDialog() {
    if (!mask) return;
    document.removeEventListener('keydown', onKey, true);
    mask.remove();
    mask = null;
    if (returnFocus && returnFocus.focus) returnFocus.focus();
  }
  function onKey(e) { if (e.key === 'Escape') { e.stopPropagation(); closeDialog(); } }

  function openDialog() {
    if (mask) return;
    returnFocus = document.activeElement;
    var box = h('div', { class: 'cnm-acc-box', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'cnm-acc-title' });
    mask = h('div', { class: 'cnm-acc-mask', onclick: function (e) { if (e.target === mask) closeDialog(); } }, box);
    document.body.appendChild(mask);
    document.addEventListener('keydown', onKey, true);
    if (isLoggedIn()) renderAccount(box); else renderEmail(box, '');
  }

  function errorText(res) {
    var d = res && res.data;
    if (res && res.status === 429 && d && d.error === 'rate_limited') {
      var sec = Number(d.retry_after);
      return d.reason === 'cooldown' && sec ? '发得太快了，请 ' + sec + ' 秒后再试。' : '请求太频繁，请稍后再试。';
    }
    if (d && d.message) return d.message;
    return '服务暂时不可用，请稍后再试。';
  }

  function renderEmail(box, initial) {
    var input = h('input', { type: 'email', id: 'cnm-acc-email', autocomplete: 'email', inputmode: 'email', placeholder: 'name@example.com', value: initial || '' });
    var msg = h('p', { class: 'cnm-acc-msg', role: 'alert' });
    var send = h('button', { type: 'button', class: 'cnm-primary', text: '发送验证码' });
    function submit() {
      var address = input.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(address)) { msg.textContent = '请填写正确的邮箱。'; return; }
      send.disabled = true;
      msg.className = 'cnm-acc-msg';
      msg.textContent = '发送中……';
      requestCode(address).then(function (res) {
        if (res.status === 200) renderCode(box, address.toLowerCase(), true);
        else { msg.textContent = errorText(res); send.disabled = false; }
      }, function () { msg.textContent = '网络不通，请检查网络后再试。'; send.disabled = false; });
    }
    send.addEventListener('click', submit);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });
    box.replaceChildren(
      h('h2', { id: 'cnm-acc-title', text: '登录 / 注册' }),
      h('p', { text: '用邮箱收一个验证码就能登录，没有密码。登录后，孩子档案、诊断记录、错题本和期末计划会同步到云端，换手机或电脑也能接着用。不登录也能完整使用全部功能。' }),
      h('label', { class: 'cnm-field', for: 'cnm-acc-email', text: '邮箱' }), input, msg,
      h('div', { class: 'cnm-acc-row' }, send, h('button', { type: 'button', text: '取消', onclick: closeDialog }))
    );
    input.focus();
  }

  function renderCode(box, address, justSent) {
    var code = h('input', { type: 'text', id: 'cnm-acc-code', inputmode: 'numeric', autocomplete: 'one-time-code', maxlength: '6', placeholder: '6 位验证码' });
    var mail = h('input', { type: 'checkbox', id: 'cnm-acc-mail', checked: true });
    var mkt = h('input', { type: 'checkbox', id: 'cnm-acc-mkt' });
    var msg = h('p', { class: 'cnm-acc-msg' + (justSent ? ' ok' : ''), role: 'alert', text: justSent ? '验证码已发送，请查收邮件（也看看垃圾邮件）。' : '' });
    var go = h('button', { type: 'button', class: 'cnm-primary', text: '登录' });
    var resend = h('button', { type: 'button', text: '重新发送' });
    var timerId = null;
    function countdown(left) {
      if (!mask) return;
      resend.disabled = left > 0;
      resend.textContent = left > 0 ? '重新发送（' + left + '）' : '重新发送';
      if (left > 0) timerId = setTimeout(function () { countdown(left - 1); }, 1000);
    }
    function submit() {
      var value = code.value.replace(/\s+/g, '');
      if (!/^\d{6}$/.test(value)) { msg.className = 'cnm-acc-msg'; msg.textContent = '请输入邮件里的 6 位数字。'; return; }
      go.disabled = true;
      msg.className = 'cnm-acc-msg';
      msg.textContent = '登录中……';
      verify(address, value, mail.checked, mkt.checked).then(function (res) {
        if (res.status === 200 && res.data && res.data.token) { closeDialog(); return; }
        msg.textContent = res.data && res.data.error === 'too_many_attempts' ? '试错次数太多了，请点「重新发送」换一个验证码。' : errorText(res);
        go.disabled = false;
      }, function () { msg.textContent = '网络不通，请检查网络后再试。'; go.disabled = false; });
    }
    go.addEventListener('click', submit);
    code.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });
    resend.addEventListener('click', function () {
      resend.disabled = true;
      requestCode(address).then(function (res) {
        if (res.status === 200) { msg.className = 'cnm-acc-msg ok'; msg.textContent = '新验证码已发送。'; countdown(COOLDOWN_SEC); }
        else { msg.className = 'cnm-acc-msg'; msg.textContent = errorText(res); resend.disabled = false; }
      }, function () { msg.className = 'cnm-acc-msg'; msg.textContent = '网络不通，请检查网络后再试。'; resend.disabled = false; });
    });
    box.replaceChildren(
      h('h2', { id: 'cnm-acc-title', text: '输入验证码' }),
      h('p', { text: '验证码发到了 ' + address + '，10 分钟内有效。' }),
      h('label', { class: 'cnm-field', for: 'cnm-acc-code', text: '验证码' }), code,
      h('label', { class: 'cnm-check', for: 'cnm-acc-mail' }, mail, h('span', { text: '接收服务邮件（验证码、账号与同步相关通知）' })),
      h('label', { class: 'cnm-check', for: 'cnm-acc-mkt' }, mkt, h('span', { text: '接收学习资料与活动推送（营销邮件，可不选，随时可退订）' })),
      h('p', { text: '以上两项只在第一次注册时记录，已有账号登录不会改动你之前的选择。' }),
      msg,
      h('div', { class: 'cnm-acc-row' }, go, resend, h('button', { type: 'button', text: '换邮箱', onclick: function () { clearTimeout(timerId); renderEmail(box, address); } }))
    );
    countdown(justSent ? COOLDOWN_SEC : 0);
    code.focus();
  }

  function renderAccount(box) {
    var status = h('p', { text: syncText() });
    var sync = h('button', { type: 'button', text: '立即同步', onclick: function () {
      if (window.CnmSyncEngine) window.CnmSyncEngine.syncAll();
    } });
    box.replaceChildren(
      h('h2', { id: 'cnm-acc-title', text: '我的账号' }),
      h('p', { text: email() }),
      status,
      h('p', { text: '退出登录不会删除这台设备上的数据；以后再登录会继续同步。' }),
      h('div', { class: 'cnm-acc-row' }, sync,
        h('button', { type: 'button', text: '退出登录', onclick: function () { logout().then(closeDialog, closeDialog); } }),
        h('button', { type: 'button', text: '关闭', onclick: closeDialog }))
    );
    box._status = status;
  }

  function showToast(text, label, action) {
    var old = document.querySelector('.cnm-toast');
    if (old) old.remove();
    var toast = h('div', { class: 'cnm-toast', role: 'status' },
      h('span', { text: text }),
      h('button', { type: 'button', text: label, onclick: function () { toast.remove(); action(); } }));
    document.body.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 15000);
  }

  var cssAdded = false;
  function ensureStyle() {
    if (cssAdded || !document.head) return;
    cssAdded = true;
    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function mount() {
    if (button || !document.body) return;
    var host = document.querySelector('.site-nav .page-links') || document.querySelector('.site-nav');
    if (!host) return;
    ensureStyle();
    button = h('button', { type: 'button', class: 'nav-link cnm-account-btn', id: 'cnm-account-btn', onclick: openDialog });
    hint = h('span', { class: 'cnm-acc-hint' });
    wrap = h('span', { class: 'cnm-acc-wrap' }, button, hint);
    var search = host.querySelector('.resource-search-btn');
    if (search) host.insertBefore(wrap, search); else host.appendChild(wrap);
    refreshButton();
    setInterval(function () { if (isLoggedIn() && !document.hidden) refreshButton(); }, 60000);
  }

  /* ------------------------------------------------------------------ 登录提示（可关闭，关闭后本机不再出现） */

  var NUDGES = {
    home: { kind: 'home', text: '登录后，孩子档案、诊断记录和错题本会同步到云端，换手机或电脑也不丢。登录可选，不登录一切照旧。' },
    diagnose: { kind: 'card', text: '登录后，诊断记录和错题本换设备也能看。' },
    wrongbook: { kind: 'card', text: '登录后，错题本和诊断记录换设备也能看。' }
  };
  function nudgeKey(name) { return 'cnmNudge.' + name; }

  function fillNudge(slot) {
    var name = slot.getAttribute('data-nudge');
    var def = NUDGES[name];
    slot.setAttribute('data-cnm-done', '1');
    if (!def) return;
    if (isLoggedIn()) { if (name === 'home') lsSet(nudgeKey(name), '1'); return; }
    if (lsGet(nudgeKey(name))) return;
    ensureStyle();
    function dismiss() { lsSet(nudgeKey(name), '1'); slot.replaceChildren(); }
    slot.appendChild(h('aside', { class: 'cnm-nudge', 'data-kind': def.kind, 'aria-label': '登录提示' },
      h('span', { class: 'cnm-nudge-text', text: def.text }),
      h('button', { type: 'button', class: 'cnm-nudge-go', text: '去登录', onclick: openDialog }),
      h('button', { type: 'button', class: 'cnm-nudge-x', 'aria-label': '关闭提示', title: '关闭，不再提示', text: '×', onclick: dismiss })));
  }
  function fillNudges() {
    var slots = document.querySelectorAll('.cnm-nudge-slot[data-nudge]:not([data-cnm-done])');
    for (var i = 0; i < slots.length; i++) fillNudge(slots[i]);
  }
  function clearNudges() {
    var slots = document.querySelectorAll('.cnm-nudge-slot[data-nudge]');
    for (var i = 0; i < slots.length; i++) {
      if (slots[i].getAttribute('data-nudge') === 'home') lsSet(nudgeKey('home'), '1');
      slots[i].replaceChildren();
    }
  }
  /* 页面的结果区 / 错题列表会重绘，位置是后来才出现的，所以盯着 DOM 变化补填。 */
  function watchSlots() {
    fillNudges();
    if (!window.MutationObserver || !document.body) return;
    var queued = false;
    new MutationObserver(function () {
      if (queued) return;
      queued = true;
      (window.requestAnimationFrame || setTimeout)(function () { queued = false; fillNudges(); });
    }).observe(document.body, { childList: true, subtree: true });
  }

  window.addEventListener('cnm:auth', function () {
    syncStatus = { state: 'idle', at: 0, message: '' };
    refreshButton();
    if (mask && !isLoggedIn()) closeDialog();
    if (isLoggedIn()) clearNudges();
  });
  window.addEventListener('cnm:sync', function (e) {
    syncStatus = e.detail || syncStatus;
    refreshButton();
    if (mask) {
      var st = mask.querySelector('.cnm-acc-box');
      if (st && st._status) st._status.textContent = syncText();
    }
    if (syncStatus.state === 'applied') showToast('已从云端同步了新数据', '刷新页面', function () { location.reload(); });
    if (syncStatus.state === 'signedout') showToast('登录已过期，本机数据都还在。要继续同步请重新登录。', '登录', openDialog);
  });

  window.CnmAccount = {
    isLoggedIn: isLoggedIn, email: email, api: api, requestCode: requestCode, verify: verify,
    logout: logout, expire: expire, open: openDialog, fillNudges: fillNudges
  };

  function start() { mount(); watchSlots(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
