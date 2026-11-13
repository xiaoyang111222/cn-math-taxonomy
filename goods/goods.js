/* 「学习好物」商品页渲染。数据在 goods-data.js。
 * 有推广链接的商品显示京东/淘宝按钮（rel="sponsored nofollow noopener"，带「推广」角标）；
 * 没链接的显示「即将上架」，不出现死按钮。 */
(function () {
  'use strict';

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function channelBtn(p, channel, href, label) {
    var a = el('a', 'goods-btn goods-btn-' + channel, label);
    a.href = href;
    a.target = '_blank';
    a.rel = 'sponsored nofollow noopener';
    return a;
  }

  function card(p) {
    var item = el('article', 'goods-item');
    var head = el('div', 'goods-head');
    head.appendChild(el('h3', 'goods-title', p.title));
    if (p.tag) head.appendChild(el('span', 'goods-tag', p.tag));
    item.appendChild(head);
    if (p.desc) item.appendChild(el('p', 'goods-desc', p.desc));
    var meta = el('div', 'goods-meta');
    if (p.price) meta.appendChild(el('span', 'goods-price', '参考价位：' + p.price));
    if (p.jd || p.tb) meta.appendChild(el('span', 'goods-ad', '推广'));
    item.appendChild(meta);
    var row = el('div', 'goods-row');
    if (p.jd) row.appendChild(channelBtn(p, 'jd', p.jd, '京东看看'));
    if (p.tb) row.appendChild(channelBtn(p, 'tb', p.tb, '淘宝看看'));
    if (!p.jd && !p.tb) row.appendChild(el('span', 'goods-soon', '即将上架'));
    item.appendChild(row);
    return item;
  }

  function render(root) {
    var goods = window.GOODS || [];
    var cats = window.GOODS_CATS || [];
    cats.forEach(function (c) {
      var items = goods.filter(function (p) { return p.cat === c.id; });
      if (!items.length) return;
      var sec = el('section', 'goods-cat');
      sec.appendChild(el('h2', 'section-title', c.name));
      var grid = el('div', 'goods-grid');
      items.forEach(function (p) { grid.appendChild(card(p)); });
      sec.appendChild(grid);
      root.appendChild(sec);
    });
  }

  window.GoodsPage = { render: render, card: card };

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.getElementById('goods-root');
    if (root) render(root);
  });
})();
