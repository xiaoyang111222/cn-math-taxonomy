#!/usr/bin/env python3
"""给初中化学（topicId 以 cnk_j 开头）里最需要看结构或装置的题写入内联 SVG。

只改下面登记的题，大约 35–50 道，不给全部题目硬配。可重复运行：
  python3 scripts/chem_figs.py
  python3 scripts/chem_figs.py --preview /tmp/chem-figs.html

图只用 currentColor，不引用外网。正确选项的整句不写入图中。
图里的阿拉伯数字必须能在该题题干或选项里找到。
若标出名称或粒子数就会直接泄题，图上用「?」或省略。
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fig_draw import circ, edge, esc, face, hidden, line, n, poly, svg, text, thin  # noqa: E402
from check_figures import figure_problems  # noqa: E402

ROOT = os.path.dirname(HERE)
QUESTIONS = os.path.join(ROOT, "data", "questions.json")


def rect(x, y, w, h, attrs, rx=0):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" %s/>' % (
        n(x), n(y), n(w), n(h), n(rx), attrs)


def ell(cx, cy, rx, ry, attrs):
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" %s/>' % (
        n(cx), n(cy), n(rx), n(ry), attrs)


def path(d, attrs):
    return '<path d="%s" %s/>' % (d, attrs)


def arrow(a, b, sw=2.2):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    length = 9
    tip = b
    p1 = (b[0] - length * math.cos(ang - 0.45), b[1] - length * math.sin(ang - 0.45))
    p2 = (b[0] - length * math.cos(ang + 0.45), b[1] - length * math.sin(ang + 0.45))
    end = (b[0] - 2 * math.cos(ang), b[1] - 2 * math.sin(ang))
    return line(a, end, thin(sw)) + poly([tip, p1, p2], face(1))


def box(x, y, w, h, lines, op=0.07, size=15, sw=1.8):
    if isinstance(lines, str):
        lines = [lines]
    body = rect(x, y, w, h, face(op), 8) + rect(x, y, w, h, edge(sw), 8)
    gap = size + 4
    block = gap * len(lines)
    y0 = y + (h - block) / 2 + size - 1
    for i, line_s in enumerate(lines):
        body += text(x + w / 2, y0 + i * gap, line_s, size)
    return body


def ask(x, y, r=12):
    return circ(x, y, r, edge(2.1)) + text(x, y + 5, "?", 16)


def frame(w, h, body, title, note="示意图"):
    if title:
        body += text(w / 2, 22, title, 15)
    if note:
        body += text(w / 2, h - 12, note, 12)
    return svg(w, h, body)


def leader(ax, ay, lx, ly, lab, size=14, anchor="start"):
    body = line((ax, ay), (lx, ly), thin(1.3)) + circ(ax, ay, 2.4, face(1))
    dx = 6 if anchor == "start" else (-6 if anchor == "end" else 0)
    body += text(lx + dx, ly + 4, lab, size, anchor)
    return body


def beaker(x, y, w, h, sw=2):
    d = "M %s %s L %s %s Q %s %s %s %s L %s %s" % (
        n(x), n(y), n(x), n(y + h - 8), n(x + w / 2), n(y + h + 12), n(x + w), n(y + h - 8), n(x + w), n(y))
    return path(d, edge(sw)) + line((x - 7, y), (x + w + 7, y), edge(sw))


def liquid(x, y, w, h, level):
    bot = y + h - 2
    pts = [(x + 4, level), (x + 4, bot - 8), (x + w / 2, bot + 6), (x + w - 4, bot - 8), (x + w - 4, level)]
    return poly(pts, face(0.1)) + line((x + 4, level), (x + w - 4, level), thin(1.3))


def v_tube(x, y, w, h, sw=2):
    r = w / 2.0
    d = "M %s %s L %s %s A %s %s 0 0 1 %s %s L %s %s" % (
        n(x), n(y), n(x), n(y + h - r), n(r), n(r), n(x + w), n(y + h - r), n(x + w), n(y))
    return path(d, edge(sw))


def h_tube(x, y, w, h, sw=2):
    r = h / 2.0
    d = "M %s %s L %s %s A %s %s 0 0 1 %s %s L %s %s" % (
        n(x), n(y), n(x + w - r), n(y), n(r), n(r), n(x + w - r), n(y + h), n(x), n(y + h))
    return path(d, edge(sw))


def jar(x, y, w, h):
    return rect(x, y, w, h, edge(2.2), 3) + line((x - 6, y), (x + w + 6, y), edge(2.2))


def flame_at(x, y, s=1.0):
    h = 22 * s
    w = 8 * s
    d = "M %s %s Q %s %s %s %s Q %s %s %s %s" % (
        n(x), n(y), n(x - w), n(y - h * 0.45), n(x), n(y - h), n(x + w), n(y - h * 0.45), n(x), n(y))
    return path(d, face(0.16)) + path(d, edge(1.5))


def lamp_at(cx, bottom):
    body = ell(cx, bottom - 3, 26, 7, edge(1.7))
    body += line((cx - 20, bottom - 6), (cx - 12, bottom - 32), edge(1.7))
    body += line((cx + 20, bottom - 6), (cx + 12, bottom - 32), edge(1.7))
    body += line((cx - 12, bottom - 32), (cx + 12, bottom - 32), edge(1.7))
    body += rect(cx - 6, bottom - 44, 12, 14, edge(1.5), 2)
    body += flame_at(cx, bottom - 46, 0.85)
    return body


def flask(cx, top, bw=88, bh=70):
    nw, nh = 20, 16
    body = line((cx - nw / 2, top), (cx + nw / 2, top), edge(1.8))
    body += line((cx - nw / 2, top), (cx - nw / 2, top + nh), edge(1.8))
    body += line((cx + nw / 2, top), (cx + nw / 2, top + nh), edge(1.8))
    body += line((cx - nw / 2, top + nh), (cx - bw / 2, top + nh + bh), edge(1.8))
    body += line((cx + nw / 2, top + nh), (cx + bw / 2, top + nh + bh), edge(1.8))
    body += line((cx - bw / 2, top + nh + bh), (cx + bw / 2, top + nh + bh), edge(1.8))
    return body


def bubbles(x, y, k=3):
    body = ""
    for i in range(k):
        body += circ(x + (i - 1) * 9, y - i * 11, 3.4 + (i % 2), edge(1.3))
    return body


def person(x, y):
    body = circ(x, y, 9, edge(1.6))
    body += line((x, y + 9), (x, y + 32), edge(1.6))
    body += line((x - 12, y + 18), (x + 12, y + 18), edge(1.6))
    body += line((x, y + 32), (x - 9, y + 48), edge(1.6))
    body += line((x, y + 32), (x + 9, y + 48), edge(1.6))
    return body


def particle(cx, cy, r, op=0.08, label=None, size=13):
    body = circ(cx, cy, r, face(op)) + circ(cx, cy, r, edge(1.6))
    if label:
        body += text(cx, cy + size * 0.35, label, size)
    return body


def _tw(s, size):
    width = 0.0
    for ch in s:
        width += size if ord(ch) > 127 else size * 0.56
    return width


def overflow_problems(drawing):
    """文字不要画出 viewBox。"""
    m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', drawing)
    if not m:
        return ["缺少 viewBox"]
    w, h = float(m.group(1)), float(m.group(2))
    bad = []
    for t in re.finditer(
        r'<text x="([^"]+)" y="([^"]+)"[^>]*font-size="([^"]+)" text-anchor="([^"]+)">([^<]*)</text>',
        drawing,
    ):
        x, y = float(t.group(1)), float(t.group(2))
        size = float(t.group(3))
        anchor, s = t.group(4), t.group(5)
        tw = _tw(s, size)
        if anchor == "start":
            left, right = x, x + tw
        elif anchor == "end":
            left, right = x - tw, x
        else:
            left, right = x - tw / 2, x + tw / 2
        if left < 1 or right > w - 1 or y - size < 0 or y > h - 1:
            bad.append("文字越界「%s」" % s)
    return bad


# ---------------------------------------------------------------- 基本操作


def smell_gas():
    """扇闻。不把正确操作整句写出来。"""
    w, h = 460, 280
    body = rect(168, 78, 64, 18, edge(1.7), 2)
    body += rect(150, 96, 100, 120, edge(2), 4)
    body += text(200, 150, "气体", 14)
    body += path("M 250 110 C 300 90 320 130 300 150", thin(1.6))
    body += path("M 248 128 C 292 118 318 150 296 168", thin(1.4))
    body += line((300, 168), (336, 188), edge(1.8))
    body += line((336, 188), (358, 176), edge(1.8))
    body += line((336, 188), (360, 198), edge(1.8))
    body += text(360, 214, "手", 14)
    body += leader(200, 96, 90, 88, "瓶口", 15, "end")
    body += ask(90, 150)
    return frame(w, h, body, "闻气体")


def heat_liquid():
    """试管口方向用问号，不写安全结论。"""
    w, h = 480, 300
    body = person(78, 150)
    body += text(78, 214, "人", 14)
    body += path("M 150 196 L 300 112 A 16 16 0 0 1 318 128 L 168 212 Z", face(0.06))
    body += path("M 150 196 L 300 112 A 16 16 0 0 1 318 128 L 168 212", edge(2))
    body += liquid_slant()
    body += lamp_at(188, 250)
    body += text(230, 236, "酒精灯", 13, "start")
    body += leader(310, 118, 390, 78, "试管口", 15, "start")
    body += ask(400, 140)
    return frame(w, h, body, "给液体加热")


def liquid_slant():
    return path("M 176 196 L 286 132 L 296 142 L 186 204 Z", face(0.12))


def dilute_acid():
    """两种液体都标出来。倒入方向不写结论。"""
    w, h = 480, 300
    body = bottle(46, 70, "浓硫酸")
    body += bottle(360, 70, "水")
    body += beaker(190, 120, 100, 110)
    body += line((230, 78), (230, 168), edge(1.7))
    body += circ(230, 168, 4, edge(1.4))
    body += text(240, 250, "玻璃棒", 13)
    body += arrow((120, 130), (185, 160), 1.8)
    body += arrow((360, 130), (295, 160), 1.8)
    body += ask(240, 78)
    return frame(w, h, body, "稀释")


def bottle(x, y, lab):
    body = rect(x + 18, y, 28, 12, edge(1.6), 2)
    body += rect(x, y + 12, 64, 88, edge(1.9), 4)
    body += text(x + 32, y + 62, lab, 13)
    return body


def filter_rod():
    """玻璃棒的作用留给问号。"""
    w, h = 460, 300
    body = filter_rig(150, 58)
    body += leader(120, 90, 80, 246, "玻璃棒", 15, "end")
    body += text(250, 118, "漏斗", 14, "start")
    body += ask(400, 150)
    return frame(w, h, body, "过滤装置")


def filter_rig(cx, top):
    body = line((cx - 46, top), (cx + 46, top), edge(1.8))
    body += line((cx - 46, top), (cx - 8, top + 48), edge(1.8))
    body += line((cx + 46, top), (cx + 8, top + 48), edge(1.8))
    body += line((cx - 6, top + 48), (cx - 6, top + 92), edge(1.8))
    body += line((cx + 6, top + 48), (cx + 6, top + 92), edge(1.8))
    body += line((cx - 36, top + 8), (cx - 4, top + 40), thin(1.3))
    body += line((cx - 30, top + 8), (cx, top + 40), thin(1.3))
    body += line((cx - 70, top - 6), (cx - 6, top + 36), edge(1.8))
    body += circ(cx - 6, top + 36, 3.5, edge(1.4))
    body += beaker(cx - 48, top + 78, 96, 100)
    body += circ(cx, top + 70, 3, face(0.4))
    return body


def filter_named_parts():
    """操作名称不写出，避免把答案印在图上。"""
    w, h = 460, 300
    body = filter_rig(170, 58)
    body += text(250, 100, "漏斗", 14, "start")
    body += circ(150, 96, 4, face(0.45))
    body += circ(162, 108, 3.5, face(0.45))
    body += text(78, 108, "杂质", 14, "end")
    body += ask(400, 160)
    return frame(w, h, body, "把不溶物分开")


# ---------------------------------------------------------------- 气体


def air_portion():
    w, h = 460, 290
    body = jar(70, 58, 130, 180)
    body += rect(74, 186, 122, 48, face(0.12), 2)
    body += text(135, 214, "水", 15)
    body += circ(135, 100, 11, face(0.35)) + circ(135, 100, 11, edge(1.5))
    body += text(135, 84, "红磷", 14)
    body += line((200, 100), (270, 100), edge(2))
    body += rect(236, 90, 8, 20, edge(1.6), 1)
    body += text(300, 104, "弹簧夹", 13, "start")
    body += ask(360, 170)
    return frame(w, h, body, "测空气成分")


def test_oxygen():
    w, h = 420, 280
    body = jar(150, 70, 110, 150)
    body += path("M 230 78 L 320 50", edge(2.1))
    body += flame_at(328, 48, 0.95)
    body += text(352, 84, "木条", 14, "start")
    body += ask(80, 140)
    return frame(w, h, body, "检验气体")


def iron_oxygen():
    w, h = 440, 300
    body = jar(150, 70, 130, 170)
    body += text(215, 160, "氧气", 14)
    body += path("M 215 78 C 200 110 230 130 210 160 C 196 184 226 190 214 210", edge(1.8))
    body += text(250, 96, "铁丝", 14, "start")
    for dx, dy in ((-18, 120), (22, 140), (-8, 150), (16, 168)):
        body += line((215 + dx, 70 + dy), (215 + dx + 8, 62 + dy), thin(1.3))
    body += ell(215, 228, 16, 6, face(0.35))
    body += ask(80, 150)
    return frame(w, h, body, "铁丝燃烧")


def catalyst_o2():
    w, h = 460, 290
    body = flask(160, 70, 120, 90)
    body += line((118, 150), (202, 150), thin(1.4))
    body += text(160, 142, "过氧化氢", 13)
    body += circ(150, 168, 4, face(0.45))
    body += circ(168, 172, 3, face(0.45))
    body += circ(158, 176, 3.5, face(0.45))
    body += leader(168, 172, 250, 200, "二氧化锰", 14, "start")
    body += bubbles(160, 120, 3)
    body += ask(340, 140)
    return frame(w, h, body, "制取氧气")


def heat_kmno4():
    """导管从水槽伸进倒立的集气瓶，不写收集方法的名称。"""
    w, h = 500, 320
    body = h_tube(16, 64, 150, 32)
    body += rect(48, 72, 62, 14, face(0.16), 2)
    body += text(79, 54, "高锰酸钾", 13)
    body += lamp_at(78, 168)
    body += text(18, 132, "酒精灯", 13, "start")
    body += path("M 166 80 L 214 80 L 214 236 L 318 236 L 318 156", edge(1.8))
    body += rect(230, 210, 240, 52, edge(1.8), 3)
    body += rect(234, 228, 232, 30, face(0.08), 2)
    body += text(448, 204, "水槽", 13, "end")
    body += line((286, 228), (286, 128), edge(1.8))
    body += line((286, 128), (360, 128), edge(1.8))
    body += line((360, 128), (360, 228), edge(1.8))
    body += ask(460, 78)
    return frame(w, h, body, "加热固体制气")


def airtight():
    """不把这一步的名称写成答案。"""
    w, h = 480, 290
    body = v_tube(70, 70, 36, 110)
    body += rect(78, 58, 20, 14, edge(1.6), 2)
    body += path("M 98 64 L 210 64 L 230 150", edge(1.8))
    body += beaker(180, 130, 90, 100)
    body += liquid(180, 130, 90, 100, 170)
    body += text(225, 210, "水", 14)
    body += circ(230, 158, 4, edge(1.3))
    body += line((236, 154), (300, 128), thin(1.2))
    body += text(306, 132, "气泡", 13, "start")
    body += leader(250, 90, 330, 70, "导管", 14, "start")
    body += rect(36, 96, 26, 32, edge(1.5), 6)
    body += text(28, 116, "手", 13, "end")
    body += ask(400, 160)
    return frame(w, h, body, "制氧前")


def two_generators():
    w, h = 480, 300
    body = h_tube(24, 90, 120, 28)
    body += lamp_at(80, 190)
    body += text(80, 206, "加热", 14)
    body += flask(300, 78, 100, 78)
    body += line((300, 70), (300, 150), edge(1.6))
    body += ell(300, 68, 10, 4, edge(1.4))
    body += text(300, 214, "不加热", 14)
    body += ask(200, 120)
    return frame(w, h, body, "两种发生装置")


def collect_co2():
    w, h = 420, 300
    body = jar(140, 60, 120, 180)
    body += path("M 200 40 L 200 210", edge(1.8))
    body += circ(192, 200, 4, face(0.3))
    body += circ(208, 206, 3, face(0.3))
    body += text(270, 80, "集气瓶", 14, "start")
    body += arrow((200, 48), (250, 48), 1.6)
    body += ask(70, 150)
    return frame(w, h, body, "收集气体")


def full_co2():
    w, h = 440, 280
    body = jar(150, 80, 120, 150)
    body += path("M 240 78 L 330 52", edge(2.1))
    body += flame_at(338, 50, 1.0)
    body += text(360, 86, "木条", 14, "start")
    body += leader(210, 80, 70, 70, "瓶口", 15, "end")
    body += ask(70, 150)
    return frame(w, h, body, "验满")


def funnel_tip():
    """两种放法并排，不标哪一种对。"""
    w, h = 480, 300
    body = _funnel_case(36, 46, below=False, tag="甲")
    body += _funnel_case(268, 46, below=True, tag="乙")
    body += text(214, 160, "液面", 13)
    body += ask(230, 108)
    return frame(w, h, body, "长颈漏斗")


def _funnel_case(x, y, below, tag):
    body = flask(x + 60, y + 36, 110, 78)
    liq = y + 108
    body += line((x + 28, liq), (x + 92, liq), thin(1.6))
    stem_end = liq + 14 if below else liq - 20
    body += line((x + 60, y + 6), (x + 60, stem_end), edge(1.8))
    body += ell(x + 60, y + 6, 14, 5, edge(1.5))
    body += text(x + 60, y + 168, tag, 14)
    return body


def candle_stair():
    w, h = 460, 300
    body = beaker(120, 70, 220, 170)
    body += rect(168, 176, 10, 40, edge(1.6), 1)
    body += flame_at(173, 174, 0.7)
    body += text(173, 232, "下", 14)
    body += rect(250, 150, 36, 70, face(0.08))
    body += rect(250, 150, 36, 70, edge(1.4), 2)
    body += rect(262, 112, 10, 40, edge(1.6), 1)
    body += flame_at(267, 110, 0.7)
    body += text(308, 130, "上", 14, "start")
    body += path("M 70 60 L 150 90", edge(1.6))
    body += text(70, 52, "二氧化碳", 13, "start")
    body += ask(400, 140)
    return frame(w, h, body, "阶梯蜡烛")


def phosphorus_exp():
    w, h = 480, 310
    body = beaker(90, 78, 250, 180)
    body += liquid(90, 78, 250, 180, 168)
    body += text(215, 230, "水", 14)
    body += rect(130, 128, 170, 10, face(0.12))
    body += rect(130, 128, 170, 10, edge(1.6), 1)
    body += text(300, 122, "铜片", 13, "start")
    body += circ(170, 118, 7, face(0.3))
    body += flame_at(170, 108, 0.45)
    body += text(170, 96, "白磷", 13)
    body += circ(240, 118, 7, face(0.15))
    body += text(240, 96, "红磷", 13)
    body += circ(190, 196, 7, face(0.3))
    body += text(190, 214, "白磷", 13)
    body += ask(420, 160)
    return frame(w, h, body, "燃烧条件实验")


# ---------------------------------------------------------------- 微粒


def scent_move():
    w, h = 460, 280
    body = _flower(90, 130)
    body += text(90, 188, "花", 14)
    body += rect(190, 60, 16, 160, face(0.1))
    body += rect(190, 60, 16, 160, edge(1.6))
    body += text(198, 48, "墙", 14)
    for i, (x, y) in enumerate(((230, 100), (260, 124), (300, 110), (340, 140), (370, 118))):
        body += circ(x, y, 5, edge(1.3))
    body += ask(400, 180)
    return frame(w, h, body, "墙内开花")


def _flower(x, y):
    body = ""
    for k in range(5):
        a = -math.pi / 2 + k * math.pi * 2 / 5
        body += circ(x + 16 * math.cos(a), y + 16 * math.sin(a), 8, edge(1.4))
    body += circ(x, y, 6, face(0.28))
    return body


def mix_gap():
    w, h = 480, 290
    body = beaker(30, 80, 70, 90)
    body += liquid(30, 80, 70, 90, 120)
    body += text(65, 78, "酒精", 13)
    body += beaker(130, 80, 70, 90)
    body += liquid(130, 80, 70, 90, 120)
    body += text(165, 78, "水", 14)
    body += arrow((210, 130), (250, 130), 1.8)
    body += beaker(270, 90, 90, 110)
    body += liquid(270, 90, 90, 110, 150)
    for i in range(5):
        body += circ(300 + (i % 3) * 16, 160 + (i // 3) * 16, 5, edge(1.3))
        body += circ(308 + (i % 3) * 16, 168 + (i // 3) * 16, 4, face(0.35))
    body += ask(420, 140)
    return frame(w, h, body, "混合之后")


def _mol(x, y, a_op, b_op):
    body = line((x, y), (x + 22, y), thin(1.4))
    body += circ(x, y, 8, face(a_op)) + circ(x, y, 8, edge(1.5))
    body += circ(x + 22, y, 8, face(b_op)) + circ(x + 22, y, 8, edge(1.5))
    return body


def rearrange():
    w, h = 480, 280
    body = text(90, 70, "反应前", 14)
    body += _mol(50, 110, 0.05, 0.4)
    body += _mol(50, 150, 0.05, 0.4)
    body += arrow((130, 130), (190, 130), 2)
    body += text(300, 70, "反应后", 14)
    body += _mol(250, 110, 0.05, 0.05)
    body += _mol(250, 150, 0.4, 0.4)
    body += ask(420, 140)
    return frame(w, h, body, "微观变化")


def freeze_water():
    w, h = 480, 280
    body = text(110, 58, "水", 15)
    for x, y in ((70, 100), (120, 130), (80, 170), (140, 180)):
        body += _mol(x, y, 0.08, 0.35)
    body += text(340, 58, "冰", 15)
    for r in range(2):
        for c in range(2):
            body += _mol(280 + c * 50, 100 + r * 50, 0.08, 0.35)
    body += ask(230, 200)
    return frame(w, h, body, "水变成冰")


def atom_core():
    w, h = 440, 300
    cx, cy, R = 180, 160, 78
    body = circ(cx, cy, R, edge(1.6))
    body += circ(cx, cy, 46, hidden(1.3))
    body += circ(cx, cy, 20, face(0.18)) + circ(cx, cy, 20, edge(2))
    body += text(cx, cy + 6, "?", 18)
    for ang in (0.4, 2.4, 4.2):
        ex, ey = cx + R * math.cos(ang), cy + R * math.sin(ang)
        body += circ(ex, ey, 8, face(0.08)) + circ(ex, ey, 8, edge(1.5))
    body += leader(cx + R, cy - 10, 330, 80, "电子", 15, "start")
    return frame(w, h, body, "原子")


def proton_electron():
    """不标出两边的个数。"""
    w, h = 440, 290
    cx, cy = 160, 150
    body = circ(cx, cy, 78, edge(1.8))
    body += text(cx, cy - 90, "电子", 15)
    body += circ(cx, cy, 26, face(0.22)) + circ(cx, cy, 26, edge(2))
    body += text(cx, cy + 5, "质子", 14)
    body += ask(330, 150)
    return frame(w, h, body, "质子和电子")


def atom_mass():
    w, h = 460, 290
    body = circ(150, 140, 46, face(0.08)) + circ(150, 140, 46, edge(2))
    body += line((150, 100), (150, 180), thin(1.2))
    body += text(124, 146, "质子", 13)
    body += text(176, 146, "中子", 13)
    body += circ(250, 90, 7, edge(1.5))
    body += text(250, 74, "电子", 13)
    body += ask(340, 160)
    return frame(w, h, body, "相对原子质量")


def periodic_cell():
    w, h = 480, 300
    body = ""
    for r in range(3):
        for c in range(3):
            body += rect(36 + c * 34, 78 + r * 34, 32, 32, edge(1.2), 2)
    body += rect(70, 112, 32, 32, face(0.14), 2)
    body += rect(220, 58, 200, 190, edge(2.2), 6)
    body += text(320, 96, "原子序数", 15)
    body += text(320, 142, "?", 26)
    body += text(320, 172, "元素符号", 14)
    body += text(320, 214, "相对原子质量", 15)
    return frame(w, h, body, "周期表的一格")


def water_model():
    w, h = 440, 290
    body = line((150, 150), (210, 110), edge(2))
    body += line((210, 110), (270, 160), edge(2))
    body += particle(150, 150, 16, 0.08, "H", 14)
    body += particle(210, 110, 26, 0.2, "O", 16)
    body += particle(270, 160, 16, 0.08, "H", 14)
    body += text(210, 210, "H2O", 16)
    body += ask(360, 120)
    return frame(w, h, body, "分子模型")


def formula_cao():
    w, h = 460, 280
    body = particle(90, 130, 28, 0.08, "钙", 15)
    body += text(90, 176, "+2", 14)
    body += particle(200, 130, 28, 0.22, "氧", 15)
    body += text(200, 176, "-2", 14)
    body += arrow((240, 130), (300, 130), 2)
    body += box(320, 100, 80, 60, "?", size=20)
    return frame(w, h, body, "书写化学式")


def electro_pole():
    """两支气体都不写名称。"""
    w, h = 460, 330
    body = _electro_base()
    body += text(163, 70, "正极", 14)
    body += text(253, 70, "负极", 14)
    body += ask(390, 140)
    return frame(w, h, body, "电解水")


def electro_volume():
    """正极气体柱画短一些。体积比不写成数字。"""
    w, h = 480, 340
    body = beaker(150, 168, 190, 78)
    body += liquid(150, 168, 190, 78, 198)
    body += rect(188, 96, 32, 124, edge(1.7), 2)
    body += rect(192, 128, 24, 88, face(0.1), 1)
    body += rect(286, 64, 32, 156, edge(1.7), 2)
    body += rect(290, 128, 24, 88, face(0.1), 1)
    body += text(204, 88, "正极", 13)
    body += text(176, 108, "氧气", 13, "end")
    body += text(176, 126, "5 mL", 12, "end")
    body += text(330, 58, "负极", 13, "start")
    body += text(336, 100, "氢气", 14, "start")
    body += rect(210, 286, 64, 22, edge(1.4), 3)
    body += text(242, 302, "电源", 12)
    body += ask(430, 180)
    return frame(w, h, body, "气体体积")


def _electro_base():
    body = beaker(110, 150, 200, 90)
    body += liquid(110, 150, 200, 90, 190)
    body += text(210, 200, "水", 14)
    body += rect(145, 78, 36, 110, edge(1.7), 2)
    body += rect(235, 78, 36, 110, edge(1.7), 2)
    body += rect(160, 272, 80, 24, edge(1.5), 3)
    body += text(200, 289, "电源", 13)
    return body


def mass_micro():
    w, h = 480, 280
    body = text(100, 64, "反应前", 14)
    body += _mol(60, 120, 0.05, 0.4)
    body += _mol(60, 160, 0.05, 0.4)
    body += arrow((150, 140), (210, 140), 2)
    body += text(310, 64, "反应后", 14)
    body += _mol(250, 110, 0.4, 0.05)
    body += _mol(280, 160, 0.05, 0.4)
    body += ask(420, 180)
    return frame(w, h, body, "反应前后")


def sealed_burn():
    w, h = 480, 290
    body = _sealed(70, "反应前")
    body += _sealed(270, "反应后")
    body += text(120, 150, "镁", 13)
    body += text(78, 86, "密闭", 12, "end")
    body += ask(240, 130)
    return frame(w, h, body, "密闭容器")


def _sealed(x, lab):
    body = text(x + 55, 56, lab, 14)
    body += flask(x + 55, 84, 90, 70)
    body += rect(x + 45, 76, 20, 10, edge(1.5), 2)
    body += line((x + 24, 214), (x + 86, 214), edge(1.6))
    body += poly([(x + 55, 202), (x + 24, 214), (x + 86, 214)], edge(1.4))
    body += text(x + 55, 236, "?", 16)
    return body


def carbon_forms():
    w, h = 480, 290
    body = _diamond(120, 140)
    body += text(120, 210, "金刚石", 14)
    body += _graphite(330, 140)
    body += text(330, 210, "石墨", 14)
    body += ask(230, 100)
    return frame(w, h, body, "两种碳单质")


def _diamond(cx, cy):
    pts = [(cx, cy - 34), (cx - 30, cy + 8), (cx + 30, cy + 8), (cx, cy + 32)]
    body = circ(cx, cy, 7, face(0.2)) + circ(cx, cy, 7, edge(1.5))
    for p in pts:
        body += line((cx, cy), p, thin(1.4))
        body += circ(p[0], p[1], 7, edge(1.5))
    return body


def _graphite(cx, cy):
    body = ""
    for dy in (-26, 0, 26):
        body += line((cx - 28, cy + dy), (cx + 28, cy + dy), thin(1.3))
        for k in (-1, 0, 1):
            body += circ(cx + k * 22, cy + dy, 6, edge(1.4))
    return body


def burn_energy():
    w, h = 480, 320
    body = box(24, 48, 120, 40, "可燃物")
    body += box(180, 48, 120, 40, "氧气")
    body += box(336, 48, 120, 40, "着火点")
    body += arrow((84, 88), (200, 150), 1.6)
    body += arrow((240, 88), (230, 145), 1.6)
    body += arrow((396, 88), (270, 150), 1.6)
    body += flame_at(236, 176, 1.3)
    body += arrow((236, 186), (236, 220), 1.8)
    body += box(176, 224, 120, 40, "能量")
    return frame(w, h, body, "燃烧")


def zinc_acid():
    w, h = 420, 290
    body = v_tube(170, 60, 48, 150)
    body += liquid_tube(170, 60, 48, 150, 130)
    body += rect(184, 150, 20, 12, face(0.2), 2)
    body += text(194, 230, "锌", 14)
    body += text(250, 150, "稀硫酸", 14, "start")
    body += bubbles(194, 120, 3)
    body += ask(80, 130)
    return frame(w, h, body, "金属与酸")


def liquid_tube(x, y, w, h, level):
    r = w / 2.0
    d = "M %s %s L %s %s A %s %s 0 0 1 %s %s L %s %s Z" % (
        n(x + 2), n(level), n(x + 2), n(y + h - r), n(r - 2), n(r - 2),
        n(x + w - 2), n(y + h - r), n(x + w - 2), n(level))
    return path(d, face(0.1))


def iron_copper():
    w, h = 440, 280
    body = beaker(140, 80, 140, 140)
    body += liquid(140, 80, 140, 140, 120)
    body += rect(198, 100, 12, 80, edge(1.8), 2)
    body += text(204, 78, "铁钉", 14)
    body += text(250, 160, "硫酸铜", 14, "start")
    body += ask(70, 150)
    return frame(w, h, body, "金属放入溶液")


def rust_tubes():
    w, h = 480, 300
    body = _rust(50, "干燥", water=0)
    body += _rust(190, "水", water=0.45)
    body += _rust(330, "密封", water=0.85, stop=True)
    body += text(240, 64, "铁钉", 14)
    body += ask(430, 160)
    return frame(w, h, body, "三支试管")


def _rust(x, lab, water, stop=False):
    body = v_tube(x, 100, 40, 120)
    body += rect(x + 16, 120, 8, 50, edge(1.4), 1)
    if water:
        lv = 100 + 120 * (1 - water)
        body += liquid_tube(x, 100, 40, 120, lv)
    if stop:
        body += rect(x + 8, 90, 24, 12, edge(1.5), 2)
    body += text(x + 20, 240, lab, 13)
    return body


def activity_tubes():
    """三支管子都先不画气泡多少，避免把顺序画成答案。"""
    w, h = 480, 290
    labels = ("镁", "铁", "铜")
    for i, lab in enumerate(labels):
        x = 70 + i * 130
        body_i = v_tube(x, 70, 44, 130)
        body_i += liquid_tube(x, 70, 44, 130, 120)
        body_i += rect(x + 14, 110, 16, 14, face(0.2), 2)
        body_i += text(x + 22, 220, lab, 15)
        body_i += ask(x + 22, 90, 9)
        if i == 0:
            body = body_i
        else:
            body += body_i
    body += text(240, 248, "稀盐酸", 14)
    return frame(w, h + 20, body, "三种金属")


def dissolve_sugar():
    w, h = 440, 290
    body = beaker(140, 70, 160, 150)
    body += liquid(140, 70, 160, 150, 120)
    body += text(220, 64, "水", 14)
    for x, y, r in ((190, 200, 6), (220, 190, 5), (250, 205, 6), (200, 150, 4), (240, 145, 4), (270, 160, 3)):
        body += circ(x, y, r, edge(1.3))
    body += text(90, 200, "蔗糖", 14, "end")
    body += line((110, 196), (180, 198), thin(1.2))
    body += ask(360, 130)
    return frame(w, h, body, "蔗糖入水")


def solubility_axes():
    """曲线往上走，不把趋势写成那个词。"""
    w, h = 440, 290
    body = line((80, 210), (380, 210), edge(1.6))
    body += line((80, 210), (80, 60), edge(1.6))
    body += arrow((300, 210), (370, 210), 1.6)
    body += arrow((80, 100), (80, 60), 1.6)
    body += text(400, 214, "温度", 14, "end")
    body += text(70, 52, "溶解度", 14, "start")
    body += path("M 100 190 C 160 180 200 150 240 120 C 280 96 320 80 350 70", edge(2))
    body += ask(240, 160)
    return frame(w, h, body, "溶解度")


def read_cylinder():
    w, h = 460, 310
    body = line((200, 60), (200, 230), edge(2))
    body += line((250, 60), (250, 230), edge(2))
    body += line((200, 230), (250, 230), edge(2))
    for i in range(6):
        yy = 80 + i * 24
        body += line((250, yy), (238, yy), thin(1.3))
    body += path("M 204 130 Q 225 142 246 130", edge(1.6))
    body += line((250, 90), (300, 70), thin(1.3))
    body += text(360, 74, "俯视", 14, "start")
    body += line((250, 136), (320, 136), thin(1.3))
    body += text(360, 140, "平视", 14, "start")
    body += line((250, 180), (300, 200), thin(1.3))
    body += text(360, 204, "仰视", 14, "start")
    body += ask(120, 140)
    return frame(w, h, body, "读取量筒")


def salt_steps():
    """三步分开画，从左到右不排成正确顺序，也不连成一句。"""
    w, h = 480, 310
    body = ell(90, 100, 48, 14, edge(1.8))
    body += flame_at(90, 140, 0.65)
    body += text(90, 168, "蒸发", 14)
    body += beaker(190, 70, 80, 80)
    body += liquid(190, 70, 80, 80, 100)
    body += circ(230, 120, 4, face(0.35))
    body += text(230, 170, "溶解", 14)
    body += line((350, 72), (410, 72), edge(1.6))
    body += line((350, 72), (376, 104), edge(1.6))
    body += line((410, 72), (384, 104), edge(1.6))
    body += line((376, 104), (376, 136), edge(1.6))
    body += line((384, 104), (384, 136), edge(1.6))
    body += text(380, 160, "过滤", 14)
    body += ask(240, 230)
    return frame(w, h, body, "粗盐提纯")


def evaporate_dish():
    w, h = 440, 290
    body = ell(200, 120, 90, 22, edge(2))
    body += ell(200, 126, 70, 12, edge(1.3))
    for dx in (-30, -10, 12, 32):
        body += rect(200 + dx, 114, 8, 6, face(0.35), 1)
    body += line((250, 90), (300, 70), edge(1.6))
    body += lamp_at(200, 230)
    body += text(200, 70, "蒸发皿", 14)
    body += ask(340, 140)
    return frame(w, h, body, "蒸发")


def ph_scale():
    w, h = 480, 260
    body = rect(70, 110, 340, 28, face(0.08), 8)
    body += rect(70, 110, 340, 28, edge(1.8), 8)
    body += line((240, 100), (240, 148), edge(1.6))
    body += text(240, 90, "7", 16)
    body += text(130, 168, "小于 7", 14)
    body += ask(150, 70)
    body += ask(360, 70)
    return frame(w, h, body, "pH")


def litmus_drop():
    w, h = 440, 280
    body = beaker(160, 110, 120, 110)
    body += liquid(160, 110, 120, 110, 160)
    body += text(220, 190, "酸性", 14)
    body += path("M 220 40 L 220 90", edge(1.6))
    body += poly([(214, 90), (226, 90), (220, 102)], face(1))
    body += text(250, 56, "石蕊", 14, "start")
    body += ask(80, 150)
    return frame(w, h, body, "指示剂")


def neutralize():
    w, h = 480, 260
    body = box(40, 90, 90, 54, "酸")
    body += text(160, 122, "+", 20)
    body += box(190, 90, 90, 54, "碱")
    body += arrow((290, 117), (340, 117), 2)
    body += box(350, 90, 80, 54, "?", size=20)
    return frame(w, h, body, "中和")


def ion_lattice():
    w, h = 480, 300
    body = ""
    for r in range(3):
        for c in range(4):
            cx, cy = 60 + c * 52, 80 + r * 52
            op = 0.28 if (r + c) % 2 == 0 else 0.05
            mark = "+" if (r + c) % 2 == 0 else "−"
            body += circ(cx, cy, 16, face(op)) + circ(cx, cy, 16, edge(1.5))
            body += text(cx, cy + 5, mark, 14)
    body += leader(232, 140, 300, 176, "阳离子", 14, "start")
    body += leader(232, 78, 300, 64, "阴离子", 14, "start")
    body += ask(400, 200)
    return frame(w, h, body, "离子")


def acid_indicators():
    w, h = 480, 290
    body = v_tube(90, 90, 50, 120)
    body += liquid_tube(90, 90, 50, 120, 140)
    body += text(115, 240, "石蕊", 14)
    body += v_tube(250, 90, 50, 120)
    body += liquid_tube(250, 90, 50, 120, 140)
    body += text(275, 240, "酚酞", 14)
    body += text(200, 60, "稀盐酸", 14)
    body += arrow((170, 70), (115, 100), 1.5)
    body += arrow((230, 70), (275, 100), 1.5)
    body += ask(200, 150)
    return frame(w, h, body, "两种指示剂")


# ---------------------------------------------------------------- 登记


def catalog():
    """(题号, svg, 题干里必须有的片段, 额外允许的数字, 图里必须有的文字)。"""
    rows = []

    def add(qid, drawing, expect, extra=(), must=()):
        rows.append((qid, drawing, expect, set(extra), tuple(must)))

    add("cnk_j004_q1", smell_gas(), "闻气体气味时", must=("瓶口", "手", "?"))
    add("cnk_j004_q2", heat_liquid(), "给试管里的液体加热", must=("试管口", "酒精灯", "?"))
    add("cnk_j004_q3", dilute_acid(), "稀释浓硫酸", must=("浓硫酸", "水", "?"))
    add("cnk_j004_q4", filter_rod(), "过滤时，玻璃棒的作用是", must=("玻璃棒", "漏斗", "?"))
    add("cnk_j005_q2", air_portion(), "测定空气里氧气含量", must=("红磷", "水", "?"))
    add("cnk_j006_q1", test_oxygen(), "检验一瓶气体是不是氧气", must=("木条", "?"))
    add("cnk_j006_q3", iron_oxygen(), "铁丝在氧气中燃烧", must=("铁丝", "氧气", "?"))
    add("cnk_j007_q1", catalyst_o2(), "过氧化氢溶液和二氧化锰", must=("过氧化氢", "二氧化锰", "?"))
    add("cnk_j007_q2", heat_kmno4(), "用高锰酸钾制氧气", must=("高锰酸钾", "酒精灯", "?"))
    add("cnk_j008_q1", airtight(), "制取氧气前，必须先做的一步是", must=("导管", "气泡", "?"))
    add("cnk_j009_q1", scent_move(), "墙内开花墙外香", must=("墙", "花", "?"))
    add("cnk_j009_q2", mix_gap(), "酒精和水混合", must=("酒精", "水", "?"))
    add("cnk_j009_q3", rearrange(), "化学变化中，下列说法正确的是", must=("反应前", "反应后", "?"))
    add("cnk_j009_q4", freeze_water(), "水结成冰", must=("水", "冰", "?"))
    add("cnk_j010_q1", atom_core(), "原子的中心部分是", must=("电子", "?"))
    add("cnk_j010_q3", proton_electron(), "质子数与核外电子数", must=("质子", "电子", "?"))
    add("cnk_j010_q4", atom_mass(), "相对原子质量主要取决于", must=("质子", "中子", "?"))
    add("cnk_j011_q4", periodic_cell(), "在元素周期表的一格中", must=("原子序数", "元素符号", "相对原子质量"))
    add("cnk_j012_q1", filter_named_parts(), "能把不溶性杂质与液体分离", must=("漏斗", "杂质", "?"))
    add("cnk_j012_q4", distill_rig(), "要得到较纯净的蒸馏水", must=("加热", "冷凝", "?"))
    add("cnk_j013_q2", electro_pole(), "与电源负极相连的一端", must=("负极", "正极", "?"))
    add("cnk_j014_q1", water_model(), "化学式 H2O 表示", must=("H2O", "?"))
    add("cnk_j014_q3", formula_cao(), "氧化钙的化学式", must=("钙", "氧", "?"))
    add("cnk_j016_q3", electro_volume(), "若正极得到氧气 5 mL", must=("5", "氢气", "?"))
    add("cnk_j017_q2", mass_micro(), "从微观上看，化学变化前后不变的是", must=("反应前", "反应后", "?"))
    add("cnk_j017_q3", sealed_burn(), "镁条在密闭容器中燃烧", must=("镁", "密闭", "?"))
    add("cnk_j020_q1", carbon_forms(), "金刚石和石墨的相同点", must=("金刚石", "石墨", "?"))
    add("cnk_j023_q2", two_generators(), "制取二氧化碳的发生装置", must=("加热", "不加热", "?"))
    add("cnk_j023_q3", collect_co2(), "收集二氧化碳应选用", must=("集气瓶", "?"))
    add("cnk_j023_q4", full_co2(), "验满二氧化碳时", must=("瓶口", "木条", "?"))
    add("cnk_j024_q1", funnel_tip(), "长颈漏斗的下端应", must=("长颈漏斗", "液面", "?"))
    add("cnk_j024_q2", candle_stair(), "阶梯蜡烛", must=("上", "下", "二氧化碳", "?"))
    add("cnk_j025_q1", burn_energy(), "燃烧需要同时满足的条件是", must=("可燃物", "氧气", "着火点", "能量"))
    add("cnk_j027_q1", phosphorus_exp(), "铜片上的白磷燃烧", must=("白磷", "红磷", "水", "?"))
    add("cnk_j029_q2", zinc_acid(), "把锌粒放入稀硫酸", must=("锌", "稀硫酸", "?"))
    add("cnk_j030_q2", iron_copper(), "把铁钉放入硫酸铜溶液", must=("铁钉", "硫酸铜", "?"))
    add("cnk_j031_q1", rust_tubes(), "铁生锈需要的主要条件是", must=("铁钉", "水", "?"))
    add("cnk_j032_q1", activity_tubes(), "比较镁、铁、铜与同浓度稀盐酸", must=("镁", "铁", "铜", "?"))
    add("cnk_j033_q2", dissolve_sugar(), "蔗糖溶于水", must=("蔗糖", "水", "?"))
    add("cnk_j034_q2", solubility_axes(), "多数固体物质的溶解度随温度升高而", must=("温度", "溶解度", "?"))
    add("cnk_j036_q2", read_cylinder(), "量取水时，读数应", must=("俯视", "平视", "仰视", "?"))
    add("cnk_j037_q1", salt_steps(), "除去粗盐中的泥沙", must=("溶解", "过滤", "蒸发", "?"))
    add("cnk_j037_q3", evaporate_dish(), "蒸发食盐溶液时", must=("蒸发皿", "?"))
    add("cnk_j038_q1", ph_scale(), "pH 小于 7", must=("7", "?"))
    add("cnk_j038_q2", litmus_drop(), "紫色石蕊试液遇酸性溶液变为", must=("石蕊", "?"))
    add("cnk_j041_q1", neutralize(), "中和反应是", must=("酸", "碱", "?"))
    add("cnk_j042_q2", ion_lattice(), "下列物质属于盐的是", must=("阳离子", "阴离子", "?"))
    add("cnk_j043_q1", acid_indicators(), "把稀盐酸分别滴到紫色石蕊和酚酞上", must=("石蕊", "酚酞", "?"))
    return rows


def distill_rig():
    """装置画出加热和冷凝，方法名称不写。"""
    w, h = 480, 300
    body = flask(78, 108, 90, 62)
    body += line((46, 170), (110, 170), thin(1.4))
    body += lamp_at(78, 246)
    body += text(28, 210, "加热", 14, "start")
    body += line((78, 108), (78, 78), edge(1.7))
    body += line((78, 78), (280, 118), edge(1.8))
    body += line((100, 66), (268, 104), thin(1.2))
    body += line((100, 90), (268, 130), thin(1.2))
    body += text(180, 56, "冷凝", 14)
    body += flask(378, 140, 72, 52)
    body += line((280, 118), (368, 148), edge(1.8))
    body += text(378, 228, "接收", 14)
    body += ask(230, 180)
    return frame(w, h, body, "把液体分开")


def figure_for(q):
    """按题号取图。题干对不上就停，避免知识点重排后图贴错题。"""
    hit = _BY_ID.get(q.get("id"))
    if not hit:
        return None
    drawing, expect = hit
    if expect not in (q.get("prompt") or ""):
        raise SystemExit("配图题干对不上 %s，需要含「%s」" % (q.get("id"), expect))
    return drawing


def _index():
    out = {}
    for qid, drawing, expect, _extra, _must in catalog():
        out[qid] = (drawing, expect)
    return out


_BY_ID = _index()


def svg_texts(drawing):
    return re.findall(r">([^<]+)</text>", drawing)


def number_problems(qid, drawing, blob, extra):
    bad = []
    nums = set(re.findall(r"\d+(?:\.\d+)?", blob))
    for s in svg_texts(drawing):
        for tok in re.findall(r"\d+(?:\.\d+)?", s):
            if tok not in nums and tok not in extra and tok != "0":
                bad.append("%s 的图里有数字 %s，题干和选项里没有（文字：%s）" % (qid, tok, s))
    return bad


def check_items(items, byid):
    problems = []
    seen = set()
    if not (35 <= len(items) <= 50):
        problems.append("配图题数 %d 不在 35–50" % len(items))
    for qid, drawing, expect, extra, must in items:
        if qid in seen:
            problems.append("重复登记 " + qid)
        seen.add(qid)
        q = byid.get(qid)
        if not q:
            problems.append("找不到题目 " + qid)
            continue
        if not str(q.get("topicId", "")).startswith("cnk_j"):
            problems.append("%s 不是初中化学题" % qid)
        if expect not in q.get("prompt", ""):
            problems.append("%s 题干不含「%s」" % (qid, expect))
        problems += figure_problems(drawing, qid)
        problems += overflow_problems(drawing)
        blob = q.get("prompt", "") + " " + " ".join(
            c.get("text", "") for c in (q.get("choices") or []) if isinstance(c, dict))
        problems += number_problems(qid, drawing, blob, extra)
        if re.search(r"AI\s*初稿|免费", drawing):
            problems.append(qid + " 图里有不允许的文案")
        answer = ""
        for c in q.get("choices") or []:
            if isinstance(c, dict) and c.get("key") == q.get("answer"):
                answer = c.get("text") or ""
        if answer and answer in drawing:
            problems.append("%s 的图里写出了正确选项「%s」" % (qid, answer))
        for phrase in must:
            if phrase not in drawing:
                problems.append("%s 的图缺少「%s」" % (qid, phrase))
    return problems


def write_preview(items, path, byid):
    parts = [
        "<!DOCTYPE html><meta charset=\"utf-8\"><title>化学图示预览</title>",
        "<style>body{margin:0;font-family:sans-serif;background:#fff;color:#162033}",
        ".row{display:flex;gap:12px;flex-wrap:wrap;padding:8px}",
        ".card{width:440px;padding:8px;box-sizing:border-box;border:1px solid #ddd}",
        "svg{width:100%;height:auto;display:block}h2{font-size:13px;margin:4px 0}",
        "p{font-size:12px;margin:2px 0 6px;color:#444}</style><div class=\"row\">",
    ]
    for qid, drawing, _e, _x, _m in items:
        q = byid.get(qid, {})
        prompt = esc(q.get("prompt", ""))
        parts.append("<div class=\"card\"><h2>%s</h2><p>%s</p>%s</div>" % (qid, prompt, drawing))
    parts.append("</div>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("预览", path, "共", len(items), "题")


def main():
    items = catalog()
    with open(QUESTIONS, encoding="utf-8") as f:
        questions = json.load(f)
    byid = {q["id"]: q for q in questions if isinstance(q, dict) and "id" in q}
    problems = check_items(items, byid)
    if problems:
        print("图示自检失败：")
        for p in problems:
            print("  " + p)
        return 1
    if len(sys.argv) >= 3 and sys.argv[1] == "--preview":
        write_preview(items, sys.argv[2], byid)
        return 0
    added = 0
    for qid, drawing, _e, _x, _m in items:
        q = byid[qid]
        if q.get("figure") != drawing:
            q["figure"] = drawing
            added += 1
    with open(QUESTIONS, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("初中化学带图题：%d（本次新写入或更新 %d）" % (len(items), added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
