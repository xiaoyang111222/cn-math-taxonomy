#!/usr/bin/env python3
"""给初中生物（topicId 以 cnb_j 开头）里最需要看结构或过程的题写入内联 SVG。

只改下面登记的题，大约 35–50 道，不给全部题目硬配。可重复运行：
  python3 scripts/bio_figs.py
  python3 scripts/bio_figs.py --preview /tmp/bio-figs.html

图只用 currentColor，不引用外网。正确选项的整句不写入图中。
图里的阿拉伯数字必须能在该题题干或选项里找到。
若标出名称就会直接泄题，图上用「?」或省略。
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
    body = line((ax, ay), (lx, ly), thin(1.3)) + circ(ax, ay, 2.5, face(1))
    dx = 6 if anchor == "start" else (-6 if anchor == "end" else 0)
    body += text(lx + dx, ly + 4, lab, size, anchor)
    return body


def leader_ask(ax, ay, lx, ly, r=11):
    return line((ax, ay), (lx, ly), thin(1.3)) + circ(ax, ay, 2.5, face(1)) + ask(lx, ly, r)


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


# ---------------------------------------------------------------- 细胞与显微镜

def microscope(eye, obj):
    """目镜、物镜分开标。两者怎样合在一起，留给问号。"""
    w, h = 420, 280
    body = rect(78, 232, 200, 18, face(0.08), 4) + rect(78, 232, 200, 18, edge(2.2), 4)
    body += path("M 120 232 L 120 176", edge(2.4))
    body += path("M 120 196 Q 96 120 150 78", edge(2.4))
    body += rect(158, 164, 120, 12, face(0.1), 2) + rect(158, 164, 120, 12, edge(2), 2)
    body += rect(186, 156, 64, 8, edge(1.6), 1)
    body += ell(214, 206, 26, 9, edge(1.8))
    body += rect(190, 70, 36, 78, face(0.05), 4) + rect(190, 70, 36, 78, edge(2.2), 4)
    body += rect(196, 44, 24, 26, edge(2.2), 3)
    body += ell(208, 152, 24, 7, edge(1.8))
    body += circ(192, 158, 7, edge(1.6)) + circ(208, 162, 8, edge(2.2)) + circ(224, 158, 7, edge(1.6))
    body += leader(208, 50, 292, 52, eye, 15, "start")
    body += leader(208, 162, 292, 164, obj, 15, "start")
    body += ask(292, 108)
    return frame(w, h, body, "显微镜")


def slide_field():
    """玻片方向写在题干里。物像往哪边走不标。"""
    w, h = 420, 250
    body = circ(150, 118, 72, edge(2.2)) + circ(150, 118, 72, face(0.04))
    body += ell(168, 126, 16, 10, face(0.35)) + ell(168, 126, 16, 10, edge(1.6))
    body += leader_ask(150, 100, 250, 78)
    body += arrow((250, 188), (360, 188), 2.2)
    body += text(305, 176, "玻片向右", 14)
    return frame(w, h, body, "视野里的物像")


def _organelles(cx, cy, plant):
    body = circ(cx - 16, cy + 6, 16, edge(1.8)) + circ(cx - 16, cy + 6, 16, face(0.08))
    body += circ(cx - 16, cy + 6, 6, face(0.35))
    if plant:
        body += ell(cx + 28, cy + 18, 26, 16, edge(1.6)) + ell(cx + 28, cy + 18, 26, 16, face(0.06))
        body += ell(cx + 34, cy - 22, 12, 7, face(0.2)) + ell(cx + 34, cy - 22, 12, 7, edge(1.5))
        body += ell(cx - 6, cy - 28, 10, 6, face(0.2)) + ell(cx - 6, cy - 28, 10, 6, edge(1.5))
    else:
        body += ell(cx + 22, cy - 8, 8, 5, edge(1.4))
        body += ell(cx + 8, cy + 22, 7, 4, edge(1.4))
    return body


def plant_cell():
    """外层支持保护的那一层用问号，不写名称。"""
    w, h = 420, 280
    body = rect(70, 58, 200, 150, face(0.05), 16) + rect(70, 58, 200, 150, edge(2.6), 16)
    body += rect(84, 72, 172, 122, edge(1.6), 12)
    body += _organelles(168, 132, True)
    body += leader_ask(70, 90, 300, 78)
    return frame(w, h, body, "植物细胞")


def cell_compare():
    """两边都画出来。植物多出来的部分不写名称。"""
    w, h = 460, 280
    body = ell(120, 130, 78, 62, face(0.05)) + ell(120, 130, 78, 62, edge(2.3))
    body += _organelles(120, 130, False)
    body += text(120, 214, "动物细胞", 14)
    body += rect(250, 68, 150, 124, face(0.05), 12) + rect(250, 68, 150, 124, edge(2.6), 12)
    body += rect(262, 80, 126, 100, edge(1.5), 10)
    body += _organelles(318, 128, True)
    body += text(325, 214, "植物细胞", 14)
    body += leader_ask(400, 90, 430, 58, 10)
    return frame(w, h, body, "两种细胞")


def energy_converters():
    """两种结构的名字在题干里。能量怎么变，两边都留空。"""
    w, h = 460, 240
    body = circ(78, 78, 22, face(0.12)) + circ(78, 78, 22, edge(2))
    for k in range(8):
        a = k * math.pi / 4
        body += line((78 + 28 * math.cos(a), 78 + 28 * math.sin(a)),
                     (78 + 38 * math.cos(a), 78 + 38 * math.sin(a)), thin(1.4))
    body += text(78, 128, "光", 14)
    body += arrow((110, 78), (150, 78))
    body += box(150, 54, 88, 48, "叶绿体")
    body += arrow((238, 78), (276, 78))
    body += ask(300, 78)
    body += box(150, 150, 88, 48, "线粒体")
    body += arrow((238, 174), (276, 174))
    body += ask(300, 174)
    return frame(w, h, body, "能量转换器")


def chromosome_change():
    """画出染色体在分裂中的样子，不把变化过程写成一句。"""
    w, h = 460, 230
    def cell(cx, cy, r, chroms):
        s = circ(cx, cy, r, face(0.04)) + circ(cx, cy, r, edge(2))
        for dx, dy, rw in chroms:
            s += rect(cx + dx, cy + dy, 7, rw, face(0.55), 2)
        return s
    body = cell(70, 110, 36, [(-8, -12, 22), (6, -8, 18)])
    body += text(70, 162, "染色体", 13)
    body += arrow((112, 110), (148, 110))
    body += cell(196, 110, 36, [(-12, -14, 16), (-12, 2, 16), (4, -12, 14), (4, 4, 14)])
    body += arrow((238, 110), (274, 110))
    body += cell(318, 96, 26, [(-6, -8, 14), (4, -4, 12)])
    body += cell(368, 128, 26, [(-6, -8, 14), (4, -4, 12)])
    return frame(w, h, body, "细胞分裂")


def two_divisions():
    """第二次之后的数目留空，避免把结果写死。"""
    w, h = 460, 220
    def one(cx, cy, r):
        return circ(cx, cy, r, face(0.05)) + circ(cx, cy, r, edge(2))
    body = one(58, 100, 28)
    body += arrow((92, 100), (124, 100))
    body += text(108, 84, "第一次", 12)
    body += one(156, 78, 22) + one(156, 126, 22)
    body += arrow((186, 100), (230, 100))
    body += text(208, 84, "第二次", 12)
    body += rect(246, 62, 88, 76, hidden(1.6), 8)
    body += ask(290, 100)
    body += text(210, 168, "连续两次", 13)
    return frame(w, h, body, "细胞分裂")


# ---------------------------------------------------------------- 植物

def plant_organs():
    """营养器官和生殖器官都标出来，不写哪一组是营养器官。"""
    w, h = 440, 300
    body = path("M 210 168 L 210 230", edge(2.4))
    body += path("M 210 230 C 170 250 150 270 130 282", edge(2))
    body += path("M 210 230 C 250 252 280 268 300 280", edge(2))
    body += path("M 210 168 C 150 150 120 120 108 96 C 140 100 180 130 210 168 Z", face(0.08))
    body += path("M 210 168 C 150 150 120 120 108 96 C 140 100 180 130 210 168 Z", edge(1.8))
    body += path("M 210 150 C 270 132 310 108 328 86 C 292 96 250 124 210 150 Z", face(0.08))
    body += path("M 210 150 C 270 132 310 108 328 86 C 292 96 250 124 210 150 Z", edge(1.8))
    body += circ(210, 62, 16, face(0.1)) + circ(210, 62, 16, edge(1.8))
    body += ell(248, 78, 14, 18, edge(1.6))
    body += ell(286, 118, 16, 12, face(0.12)) + ell(286, 118, 16, 12, edge(1.6))
    body += ell(300, 100, 5, 7, edge(1.4))
    body += text(210, 40, "花", 14)
    body += text(108, 84, "叶", 14, "end")
    body += text(360, 72, "叶", 14, "start")
    body += text(226, 168, "茎", 14, "start")
    body += text(118, 300, "根", 14)
    body += text(312, 300, "根", 14)
    body += text(286, 156, "果实", 13)
    body += text(372, 104, "种子", 12, "start")
    return frame(440, 340, body, "绿色开花植物")


def seed_sprout():
    """先伸出来的那一端留空。"""
    w, h = 420, 250
    body = ell(200, 120, 90, 58, face(0.06)) + ell(200, 120, 90, 58, edge(2.3))
    body += path("M 150 120 C 170 90 230 90 250 120", edge(1.5))
    body += path("M 118 148 C 100 180 90 196 84 206", edge(2.2))
    body += leader(200, 68, 200, 48, "种皮", 14, "middle")
    body += leader_ask(84, 206, 48, 196)
    return frame(w, h, body, "种子萌发")


def root_tip():
    """有根毛的一段用问号，不写区段名称。"""
    w, h = 420, 300
    body = path("M 180 46 L 150 250 Q 180 278 210 250 L 180 46 Z", face(0.05))
    body += path("M 180 46 L 150 250 Q 180 278 210 250 L 180 46 Z", edge(2.2))
    body += path("M 164 230 Q 180 248 196 230", edge(1.5))
    for y in (70, 86, 102):
        body += line((166, y), (194, y), thin(1.2))
    for x, y in ((158, 150), (176, 142), (194, 156), (168, 168), (188, 172)):
        body += path("M %s %s q -16 8 -8 18" % (n(x), n(y)), thin(1.4))
    body += leader_ask(158, 150, 78, 140)
    body += text(300, 156, "根毛", 14, "start")
    body += line((194, 156), (292, 152), thin(1.2))
    return frame(w, h, body, "根")


def flower_parts():
    """花瓣用来认位置。中间和结实有关的部分不写名称。"""
    w, h = 440, 280
    body = line((210, 230), (210, 150), edge(2.2))
    body += path("M 210 168 C 160 150 130 120 150 90 C 180 110 200 140 210 168 Z", face(0.08))
    body += path("M 210 168 C 160 150 130 120 150 90 C 180 110 200 140 210 168 Z", edge(1.7))
    body += path("M 210 168 C 260 150 290 120 270 90 C 240 110 220 140 210 168 Z", face(0.08))
    body += path("M 210 168 C 260 150 290 120 270 90 C 240 110 220 140 210 168 Z", edge(1.7))
    body += ell(210, 118, 10, 28, edge(2))
    body += circ(210, 86, 8, edge(1.8))
    body += line((196, 150), (188, 100), thin(1.6))
    body += ell(186, 96, 6, 8, edge(1.5))
    body += line((224, 150), (232, 104), thin(1.6))
    body += ell(234, 100, 6, 8, edge(1.5))
    body += text(132, 108, "花瓣", 14, "end")
    body += leader_ask(210, 86, 300, 70)
    return frame(w, h, body, "一朵花")


def ovule_dev():
    """胚珠标出来。它发育成的结构留空。"""
    w, h = 440, 240
    body = ell(120, 120, 70, 48, face(0.05)) + ell(120, 120, 70, 48, edge(2.2))
    body += circ(100, 112, 10, edge(1.6)) + circ(128, 128, 10, edge(1.6)) + circ(112, 136, 8, edge(1.6))
    body += leader(128, 128, 128, 64, "胚珠", 14, "middle")
    body += arrow((190, 120), (250, 120))
    body += ell(320, 120, 48, 36, hidden(1.8))
    body += ask(320, 120)
    return frame(w, h, body, "受精完成之后")


def stem_vessels():
    """水分向上走。管道名称不写。"""
    w, h = 440, 260
    body = circ(150, 130, 78, face(0.04)) + circ(150, 130, 78, edge(2.2))
    for ang in (0.4, 2.2, 4.0):
        x = 150 + 48 * math.cos(ang)
        y = 130 + 48 * math.sin(ang)
        body += circ(x, y, 14, edge(1.6)) + circ(x, y, 5, face(0.35))
    body += arrow((250, 180), (250, 70), 2.2)
    body += text(276, 120, "水分", 14, "start")
    body += leader_ask(150 + 48 * math.cos(0.4), 130 + 48 * math.sin(0.4), 340, 168)
    return frame(w, h, body, "水分上升")


def leaf_stoma():
    """气孔那道缝不写名称。"""
    w, h = 440, 250
    body = rect(70, 70, 220, 110, face(0.04), 8) + rect(70, 70, 220, 110, edge(2), 8)
    body += text(180, 58, "叶片", 14)
    for x in (110, 140, 170, 210, 240):
        body += circ(x, 118, 10, edge(1.3))
    body += path("M 150 168 Q 168 150 186 168 Q 168 186 150 168 Z", edge(1.8))
    body += path("M 186 168 Q 204 150 222 168 Q 204 186 186 168 Z", edge(1.8))
    body += leader_ask(186, 168, 330, 150)
    return frame(w, h, body, "蒸腾")


def photosynthesis_inputs():
    """原料留空。不把原料的名称写上去。"""
    w, h = 440, 250
    body = circ(70, 70, 20, face(0.15)) + circ(70, 70, 20, edge(2))
    body += text(70, 112, "光", 14)
    body += ell(220, 120, 70, 36, face(0.08)) + ell(220, 120, 70, 36, edge(2.2))
    body += line((220, 86), (220, 154), thin(1.3))
    body += arrow((100, 78), (150, 100))
    body += arrow((120, 180), (170, 146))
    body += ask(108, 168)
    body += ask(130, 64)
    return frame(w, h, body, "光合作用")


def iodine_leaf():
    """变蓝只说明实验现象。蓝色代表的物质不写。"""
    w, h = 440, 250
    body = ell(180, 120, 100, 48, face(0.06)) + ell(180, 120, 100, 48, edge(2.2))
    body += rect(90, 86, 70, 68, face(0.22), 2)
    body += line((180, 78), (180, 162), thin(1.2))
    body += path("M 300 70 L 330 120", edge(1.8))
    body += path("M 324 112 L 330 120 L 318 118 Z", face(1))
    body += text(346, 78, "碘液", 14, "start")
    body += text(250, 108, "变蓝", 13, "start")
    body += leader_ask(230, 120, 360, 140)
    return frame(w, h, body, "绿叶在光下")


def pine_seed():
    """种子露在外面。类群名称不写。"""
    w, h = 440, 250
    body = path("M 70 150 C 90 80 150 70 170 130", edge(2.2))
    body += ell(150, 108, 28, 16, edge(1.8))
    body += path("M 138 100 L 162 92 L 158 112 Z", edge(1.5))
    body += ell(250, 150, 22, 30, face(0.1)) + ell(250, 150, 22, 30, edge(2))
    body += text(70, 70, "松树", 14, "start")
    body += text(250, 196, "种子", 14)
    body += path("M 300 120 h 50 v 46 h -50 z", hidden(1.5))
    body += text(325, 112, "果皮", 13)
    return frame(w, h, body, "松的种子")


# ---------------------------------------------------------------- 微生物与分类

def paramecium():
    w, h = 440, 240
    body = path("M 120 130 C 130 70 250 60 290 110 C 320 150 270 190 180 186 C 110 182 90 160 120 130 Z",
                face(0.06))
    body += path("M 120 130 C 130 70 250 60 290 110 C 320 150 270 190 180 186 C 110 182 90 160 120 130 Z",
                 edge(2.2))
    for i in range(12):
        t = i / 11
        x = 130 + t * 150
        y = 78 + 10 * math.sin(t * 3)
        body += line((x, y), (x - 6, y - 14), thin(1.3))
    body += circ(200, 120, 8, edge(1.4))
    body += text(200, 210, "草履虫", 14)
    body += leader_ask(150, 78, 80, 60)
    return frame(w, h, body, "单细胞生物")


def bacteria_yeast():
    """一个有明显的圆形核，一个没有。核的名称不写。"""
    w, h = 460, 240
    body = rect(70, 90, 110, 48, face(0.06), 24) + rect(70, 90, 110, 48, edge(2.2), 24)
    body += path("M 70 114 q -20 -8 -16 -24", thin(1.6))
    body += path("M 100 108 q 10 -6 8 8 q 10 4 6 12", thin(1.3))
    body += text(125, 164, "细菌", 14)
    body += ell(320, 112, 46, 34, face(0.06)) + ell(320, 112, 46, 34, edge(2.2))
    body += circ(348, 100, 16, edge(1.6))
    body += circ(300, 130, 12, edge(1.4))
    body += text(320, 164, "酵母菌", 14)
    body += leader_ask(348, 100, 400, 70)
    return frame(w, h, body, "细菌与酵母菌")


def virus_shape():
    w, h = 420, 240
    pts = []
    for i in range(6):
        a = math.radians(-90 + i * 60)
        pts.append((200 + 48 * math.cos(a), 110 + 48 * math.sin(a)))
    body = poly(pts, face(0.06)) + poly(pts, edge(2.2))
    for x, y in pts:
        ux, uy = (x - 200) / 48, (y - 110) / 48
        body += line((x, y), (x + ux * 16, y + uy * 16), thin(1.6))
    body += circ(200, 110, 16, edge(1.8))
    body += leader_ask(200 + 48, 110, 320, 70)
    body += leader_ask(200, 110, 90, 70)
    body += text(200, 196, "病毒", 14)
    return frame(w, h, body, "病毒")


def classify_ranks():
    """单位从大到小排开。变小之后怎样，留给问号。"""
    w, h = 440, 320
    labels = ["界", "门", "纲", "目", "科", "属", "种"]
    body = ""
    for i, lab in enumerate(labels):
        bw = 250 - i * 26
        x = 40 + i * 13
        y = 42 + i * 34
        body += rect(x, y, bw, 26, face(0.05 + i * 0.015), 6)
        body += rect(x, y, bw, 26, edge(1.6), 6)
        body += text(x + bw / 2, y + 18, lab, 14)
    body += text(340, 268, "越小", 13, "start")
    body += ask(390, 262)
    return frame(w, h, body, "分类单位")


def fish_gill():
    w, h = 460, 230
    body = ell(210, 112, 120, 48, face(0.05)) + ell(210, 112, 120, 48, edge(2.2))
    body += poly([(300, 112), (360, 78), (360, 146)], face(0.06)) + poly([(300, 112), (360, 78), (360, 146)], edge(2))
    body += circ(130, 100, 8, edge(1.6)) + circ(128, 100, 3, face(1))
    body += path("M 168 86 Q 186 112 168 138", edge(1.8))
    body += path("M 176 92 Q 190 112 176 132", thin(1.3))
    body += path("M 210 66 Q 240 40 250 70", edge(1.6))
    body += path("M 200 158 Q 230 186 250 156", edge(1.6))
    body += text(210, 196, "鱼", 14)
    body += leader_ask(176, 100, 80, 70)
    return frame(w, h, body, "鱼")


def bird_lung():
    """肺和气囊的位置。气体怎样经过，不写成一句。"""
    w, h = 460, 250
    body = ell(200, 130, 90, 48, face(0.05)) + ell(200, 130, 90, 48, edge(2.2))
    body += path("M 250 110 Q 320 70 300 40 Q 270 70 250 100", edge(1.8))
    body += circ(150, 112, 6, edge(1.4)) + circ(148, 112, 2, face(1))
    body += ell(210, 124, 28, 18, face(0.1)) + ell(210, 124, 28, 18, edge(2))
    body += text(210, 128, "肺", 13)
    body += ell(150, 100, 18, 12, hidden(1.5))
    body += ell(250, 150, 20, 12, hidden(1.5))
    body += text(118, 86, "气囊", 13, "end")
    body += line((132, 96), (150, 100), thin(1.2))
    body += ask(330, 130)
    return frame(w, h, body, "鸟类呼吸")


# ---------------------------------------------------------------- 人体

def digestive():
    """胃用来认位置。主要吸收的那一段不写名称。"""
    w, h = 420, 300
    body = circ(200, 48, 16, edge(1.8))
    body += path("M 200 64 L 200 96", edge(2))
    body += path("M 188 96 Q 170 130 196 150 Q 230 140 214 108", edge(2))
    body += path("M 188 96 Q 170 130 196 150 Q 230 140 214 108 Z", face(0.06))
    body += text(250, 124, "胃", 14, "start")
    body += path("M 150 150 Q 120 120 150 100 Q 180 80 160 70", edge(1.6))
    body += text(112, 96, "肝", 14, "end")
    body += path("M 196 150 C 160 170 150 220 190 230 C 230 240 250 200 230 170 C 210 150 200 160 196 150", edge(1.8))
    body += leader_ask(190, 210, 300, 210)
    return frame(w, h, body, "消化管")


def swallow_flap():
    """喉和气管按题干标。盖住喉口的那块不写名称。"""
    w, h = 440, 280
    body = path("M 150 40 Q 90 80 110 140 Q 130 170 180 150", edge(2))
    body += path("M 150 70 Q 190 80 200 120", edge(1.6))
    body += text(70, 78, "鼻", 14, "end")
    body += text(214, 100, "口", 14, "start")
    body += path("M 170 150 L 170 210", edge(2.4))
    body += path("M 158 168 L 150 188 L 170 176 Z", face(0.2))
    body += path("M 158 168 L 150 188 L 170 176 Z", edge(1.8))
    body += text(200, 168, "喉", 14, "start")
    for y in (186, 198, 210):
        body += line((160, y), (180, y), thin(1.2))
    body += text(200, 210, "气管", 14, "start")
    body += path("M 160 220 L 130 250", edge(1.8))
    body += path("M 180 220 L 214 250", edge(1.8))
    body += leader_ask(150, 180, 70, 160)
    return frame(w, h, body, "吞咽")


def alveolus_exchange():
    """肺泡和血液按题干标。气体往哪边走不标。"""
    w, h = 440, 260
    body = circ(180, 120, 70, face(0.04)) + circ(180, 120, 70, edge(2.2))
    body += text(180, 116, "肺泡", 14)
    body += path("M 120 160 Q 180 210 250 150 Q 200 190 140 150", edge(2))
    body += ell(200, 186, 8, 5, face(0.4))
    body += text(300, 196, "血液", 14, "start")
    body += line((230, 170), (292, 190), thin(1.2))
    body += leader_ask(150, 80, 70, 60)
    body += leader_ask(230, 100, 320, 70)
    return frame(w, h, body, "气体交换")


def heart_vessels():
    """从心脏送到全身的那条不写血管名称。"""
    w, h = 440, 260
    body = path("M 150 150 C 110 110 120 70 160 78 C 180 40 230 40 246 78 C 290 70 300 120 250 156 C 230 190 180 190 150 150 Z",
                face(0.05))
    body += path("M 150 150 C 110 110 120 70 160 78 C 180 40 230 40 246 78 C 290 70 300 120 250 156 C 230 190 180 190 150 150 Z",
                 edge(2))
    body += text(190, 120, "心脏", 13)
    body += path("M 230 78 C 250 40 300 36 320 70", edge(2.6))
    body += arrow((320, 70), (360, 46))
    body += text(360, 40, "全身", 13, "start")
    body += leader_ask(300, 52, 390, 86)
    body += path("M 150 130 C 110 120 90 150 110 170", edge(1.6))
    body += path("M 210 168 C 200 200 230 210 236 186", thin(1.4))
    return frame(w, h, body, "血管")


def heart_wall():
    """壁画得不一样厚。最厚的那一腔不写名称。"""
    w, h = 440, 270
    body = path("M 150 160 C 100 110 120 60 176 72 C 200 36 250 36 270 74 C 330 58 350 120 300 168 C 270 210 190 214 150 160 Z",
                face(0.04))
    body += path("M 150 160 C 100 110 120 60 176 72 C 200 36 250 36 270 74 C 330 58 350 120 300 168 C 270 210 190 214 150 160 Z",
                 edge(2))
    body += path("M 210 70 L 214 168", edge(2.2))
    body += path("M 150 120 L 300 112", edge(1.6))
    body += path("M 214 112 L 292 108 L 286 168 L 220 172 Z", face(0.1))
    body += path("M 286 108 L 300 112 L 292 170", edge(3.4))
    body += text(250, 200, "心尖", 13)
    body += ask(258, 140)
    return frame(w, h, body, "心脏四个腔")


def circulation_loops():
    """只画两条环路。体循环经过哪些血管不逐个写。"""
    w, h = 460, 260
    body = path("M 210 140 C 180 110 190 90 214 96 C 230 78 258 78 270 98 C 300 92 306 124 276 146 C 258 164 226 164 210 140 Z",
                edge(2))
    body += text(230, 128, "心脏", 12)
    body += path("M 250 96 C 250 50 360 46 360 100 C 360 140 250 130 250 110", edge(1.8))
    body += box(330, 40, 64, 32, "肺", size=14)
    body += path("M 200 146 C 120 170 80 210 160 214 C 220 218 200 170 206 156", edge(1.8))
    body += box(70, 176, 72, 32, "全身", size=14)
    body += text(120, 168, "体循环", 13)
    body += ask(150, 150)
    return frame(w, h, body, "血液循环")


def urinary_outline():
    """器官的形状照着画，名称留给题目。"""
    w, h = 420, 300
    body = ell(150, 110, 28, 40, face(0.06)) + ell(150, 110, 28, 40, edge(2))
    body += ell(250, 110, 28, 40, face(0.06)) + ell(250, 110, 28, 40, edge(2))
    body += path("M 150 148 C 160 190 180 200 200 210", edge(1.8))
    body += path("M 250 148 C 240 190 220 200 200 210", edge(1.8))
    body += ell(200, 230, 26, 18, face(0.08)) + ell(200, 230, 26, 18, edge(2))
    body += line((200, 246), (200, 262), edge(1.8))
    body += ask(108, 110)
    body += ask(292, 168)
    body += ask(248, 230)
    return frame(w, h, body, "泌尿系统")


def nephron():
    """肾小球和肾小囊按题干标。它们所在的单位不写。"""
    w, h = 460, 260
    body = path("M 120 70 C 70 70 60 150 120 156 C 150 160 160 120 140 100", edge(2))
    body += circ(118, 112, 22, edge(1.6))
    for a in range(5):
        ang = a * 0.9
        body += circ(118 + 10 * math.cos(ang), 112 + 10 * math.sin(ang), 4, thin(1.2))
    body += path("M 140 150 C 200 150 210 80 270 90 C 320 98 300 160 250 170 C 200 180 220 210 300 214", edge(2))
    body += text(70, 60, "肾小囊", 13, "start")
    body += text(168, 112, "肾小球", 13, "start")
    body += ask(360, 160)
    return frame(w, h, body, "滤过")


def eye_section():
    """成像的那一层不写名称。瞳孔、视神经用来认方向。"""
    w, h = 480, 250
    body = ell(230, 120, 130, 70, face(0.04)) + ell(230, 120, 130, 70, edge(2.2))
    body += path("M 120 78 Q 78 120 120 162", edge(2.2))
    body += ell(150, 120, 16, 28, face(0.1)) + ell(150, 120, 16, 28, edge(1.8))
    body += path("M 250 62 Q 340 120 250 178", edge(2.4))
    body += rect(348, 108, 46, 24, edge(1.8), 4)
    body += text(78, 124, "瞳孔", 13, "end")
    body += text(400, 100, "视神经", 13)
    body += leader_ask(310, 120, 300, 48)
    return frame(w, h, body, "眼球")


def reflex_arc():
    """五个环节分开写。整条结构的名称留空。"""
    w, h = 520, 210
    names = ["感受器", "传入神经", "神经中枢", "传出神经", "效应器"]
    body = ""
    for i, name in enumerate(names):
        x = 16 + i * 100
        body += box(x, 70, 88, 44, name, size=13)
        if i < 4:
            body += arrow((x + 88, 92), (x + 100, 92))
    body += ask(250, 150)
    return frame(w, h, body, "完成反射")


def elbow_flex():
    """两块肌肉的名字在题干里。哪块收、哪块松不标。"""
    w, h = 440, 260
    body = line((120, 48), (120, 140), edge(3))
    body += circ(120, 140, 10, edge(2))
    body += line((120, 140), (210, 210), edge(3))
    body += path("M 108 60 Q 70 110 108 136", edge(2))
    body += path("M 132 60 Q 160 110 132 136", edge(2))
    body += text(64, 100, "肱二头肌", 13, "end")
    body += text(176, 100, "肱三头肌", 13, "start")
    body += ask(250, 120)
    return frame(w, h, body, "屈肘")


def joint_section():
    """减少摩擦的那两处不写名称。"""
    w, h = 440, 260
    body = path("M 180 40 L 150 110 Q 180 130 210 110 L 180 40 Z", face(0.06))
    body += path("M 180 40 L 150 110 Q 180 130 210 110 L 180 40 Z", edge(2.2))
    body += path("M 120 200 L 150 150 Q 180 130 210 150 L 240 200 Z", face(0.06))
    body += path("M 120 200 L 150 150 Q 180 130 210 150 L 240 200 Z", edge(2.2))
    body += path("M 146 118 Q 110 140 150 168", edge(1.6))
    body += path("M 214 118 Q 250 140 214 168", edge(1.6))
    body += text(300, 80, "关节囊", 14, "start")
    body += line((230, 130), (292, 76), thin(1.2))
    body += leader_ask(180, 122, 70, 90)
    body += ask(180, 168, 10)
    return frame(w, h, body, "关节")


# ---------------------------------------------------------------- 生态、遗传

def carbon_oxygen():
    """气体名称分开标，不把平衡的那句话写全。"""
    w, h = 460, 240
    body = box(40, 90, 100, 52, "植物")
    body += box(300, 90, 100, 52, "动物")
    body += arrow((140, 100), (300, 100))
    body += text(220, 90, "氧气", 14)
    body += arrow((300, 132), (140, 132))
    body += text(220, 156, "二氧化碳", 14)
    return frame(w, h, body, "碳氧平衡")


def food_chain():
    """链上的生物按题干写。能量怎样流，留给问号。"""
    w, h = 480, 220
    labels = ["草", "兔", "狐"]
    body = ""
    for i, lab in enumerate(labels):
        x = 30 + i * 140
        body += box(x, 70, 80, 48, lab)
        if i < 2:
            body += arrow((x + 80, 94), (x + 140, 94))
    body += arrow((70, 150), (360, 150))
    body += text(200, 142, "能量", 14)
    body += ask(400, 150)
    return frame(w, h, body, "食物链")


def ecosystem_roles():
    """能把无机物造成有机物的那一格留空。"""
    w, h = 480, 250
    body = circ(62, 78, 16, face(0.12)) + circ(62, 78, 16, edge(1.8))
    body += text(62, 112, "光", 13)
    body += arrow((84, 78), (124, 78))
    body += ask(154, 78)
    body += text(154, 112, "无机物", 13)
    body += text(154, 130, "→ 有机物", 13)
    body += arrow((184, 78), (236, 78))
    body += ell(286, 78, 28, 14, edge(1.8))
    body += circ(278, 74, 3, face(1))
    body += arrow((318, 86), (360, 130))
    body += path("M 392 124 l 16 20 l -32 0 Z", edge(1.6))
    body += path("M 400 156 q 18 16 0 30 q -18 -14 0 -30", edge(1.6))
    body += arrow((390, 186), (70, 186))
    body += arrow((62, 168), (62, 128))
    return frame(w, h, body, "生态系统")


def biosphere_layers():
    """三个圈的名字标出来。各取哪一部分不写。"""
    w, h = 440, 280
    body = rect(60, 48, 280, 58, face(0.04), 4) + rect(60, 48, 280, 58, edge(1.6), 4)
    body += rect(60, 106, 280, 58, face(0.08), 0) + rect(60, 106, 280, 58, edge(1.6), 0)
    body += rect(60, 164, 280, 58, face(0.14), 4) + rect(60, 164, 280, 58, edge(1.6), 4)
    body += text(200, 80, "大气圈", 15)
    body += text(200, 140, "水圈", 15)
    body += text(200, 198, "岩石圈", 15)
    body += path("M 350 90 L 350 190", edge(1.6))
    body += line((344, 96), (356, 96), thin(1.4))
    body += line((344, 190), (356, 190), thin(1.4))
    body += ask(390, 140)
    return frame(w, h, body, "生物圈")


def graft_join():
    """接穗和砧木标出来。贴紧的那一层不写。"""
    w, h = 440, 270
    body = line((80, 200), (300, 200), edge(1.6))
    body += path("M 160 200 C 140 230 150 250 170 252", edge(1.6))
    body += path("M 190 200 C 210 230 200 248 184 250", edge(1.6))
    body += rect(168, 120, 24, 80, face(0.08), 2) + rect(168, 120, 24, 80, edge(2.2), 2)
    body += rect(160, 78, 40, 42, face(0.05), 4) + rect(160, 78, 40, 42, edge(2.2), 4)
    body += path("M 180 78 C 150 60 140 40 170 36", edge(1.6))
    body += path("M 200 78 C 230 50 250 46 236 30", edge(1.6))
    body += line((158, 120), (202, 120), edge(2.4))
    body += text(250, 100, "接穗", 14, "start")
    body += text(250, 168, "砧木", 14, "start")
    body += leader_ask(180, 120, 80, 100)
    return frame(w, h, body, "嫁接")


def gene_segment():
    """DNA 上的一段用问号。不把定义写全。"""
    w, h = 460, 240
    body = line((78, 48), (122, 150), edge(2.6))
    body += line((122, 48), (78, 150), edge(2.6))
    body += rect(92, 108, 20, 12, face(0.4), 2)
    body += leader_ask(92, 114, 36, 64)
    body += ell(300, 108, 78, 46, edge(1.6))
    body += path("M 240 108 C 262 74 286 74 308 108 C 330 142 354 142 370 108", edge(1.8))
    body += path("M 240 108 C 262 142 286 142 308 108 C 330 74 354 74 370 108", edge(1.8))
    for x in (258, 282, 306, 330, 352):
        body += line((x, 96), (x, 120), thin(1.3))
    body += rect(294, 98, 24, 20, face(0.25), 2)
    body += text(300, 176, "DNA", 14)
    return frame(w, h, body, "基因")


def parent_chromosomes():
    """父方、母方都画了。各出多少不写。"""
    w, h = 460, 260
    body = text(100, 48, "父方", 14)
    body += rect(40, 58, 120, 70, face(0.04), 8) + rect(40, 58, 120, 70, edge(1.8), 8)
    body += rect(78, 74, 8, 36, face(0.5), 2) + rect(100, 80, 8, 26, face(0.5), 2)
    body += text(360, 48, "母方", 14)
    body += rect(300, 58, 120, 70, face(0.04), 8) + rect(300, 58, 120, 70, edge(1.8), 8)
    body += rect(338, 74, 8, 36, face(0.5), 2) + rect(360, 80, 8, 26, face(0.5), 2)
    body += arrow((100, 128), (190, 168))
    body += arrow((360, 128), (270, 168))
    body += circ(230, 196, 26, edge(2))
    body += ask(230, 196, 11)
    return frame(w, h, body, "子女的染色体")


def relative_traits():
    """同一株作物的两种样子。定义不写。"""
    w, h = 440, 260
    def plant(x, top, stem_h):
        s = line((x, top + stem_h), (x, top + 20), edge(2.2))
        s += ell(x - 18, top + 36, 16, 8, edge(1.5))
        s += ell(x + 18, top + 48, 16, 8, edge(1.5))
        s += circ(x, top + 16, 10, edge(1.6))
        s += line((x - 16, top + stem_h), (x + 16, top + stem_h), edge(1.4))
        return s
    body = plant(130, 70, 110)
    body += plant(300, 110, 70)
    return frame(w, h, body, "相对性状")


def genotype_dd():
    w, h = 420, 200
    body = box(50, 70, 100, 56, "Dd", size=22)
    body += arrow((150, 98), (230, 98))
    body += circ(290, 98, 28, edge(2))
    body += ask(290, 98)
    return frame(w, h, body, "基因组成")


def sex_gametes():
    """卵细胞和精子都画。哪一种组合不标。"""
    w, h = 460, 240
    body = circ(90, 110, 28, edge(2))
    body += rect(84, 96, 8, 22, face(0.45), 2)
    body += text(90, 160, "卵细胞", 14)
    body += arrow((130, 110), (190, 70))
    body += arrow((130, 110), (190, 160))
    body += ell(250, 64, 36, 16, edge(1.8))
    body += rect(268, 56, 8, 16, face(0.45), 2)
    body += ell(250, 168, 36, 16, edge(1.8))
    body += rect(268, 156, 7, 20, face(0.45), 2)
    body += text(330, 68, "精子", 14, "start")
    body += text(330, 172, "精子", 14, "start")
    body += ask(400, 64, 10)
    body += ask(400, 168, 10)
    return frame(w, h, body, "生男生女")


def giraffe_necks():
    """高低都有。为什么留下长颈，不写成一句。"""
    w, h = 480, 260
    def giraffe(x, neck):
        s = ell(x, 190, 36, 18, face(0.06)) + ell(x, 190, 36, 18, edge(2))
        s += rect(x - 4, 190 - neck, 8, neck, edge(2), 2)
        s += ell(x + 10, 190 - neck - 8, 16, 10, edge(1.8))
        s += line((x + 22, 190 - neck - 4), (x + 36, 190 - neck - 8), thin(1.4))
        for dx in (-22, -8, 8, 22):
            s += line((x + dx, 204), (x + dx, 230), edge(1.8))
        return s
    body = giraffe(110, 70)
    body += giraffe(230, 120)
    body += rect(360, 70, 10, 160, edge(1.6), 2)
    body += circ(350, 64, 14, edge(1.5)) + circ(378, 58, 12, edge(1.5)) + circ(366, 78, 10, edge(1.5))
    body += ask(300, 78)
    return frame(w, h, body, "长颈鹿")


def biodiversity_levels():
    """三个层次只画样子，不写层次的名称。"""
    w, h = 480, 230
    body = rect(24, 56, 130, 120, edge(1.4), 8)
    body += path("M 50 108 Q 70 72 90 108 T 130 108", edge(1.6))
    body += path("M 50 108 Q 70 140 90 108 T 130 108", edge(1.6))
    body += ask(89, 156, 10)
    body += rect(174, 56, 130, 120, edge(1.4), 8)
    body += ell(214, 100, 16, 10, edge(1.5))
    body += ell(250, 92, 12, 16, edge(1.5))
    body += path("M 230 128 q 16 -18 28 0", edge(1.4))
    body += ask(239, 156, 10)
    body += rect(324, 56, 130, 120, edge(1.4), 8)
    body += path("M 350 120 L 366 80 L 382 120 Z", edge(1.5))
    body += path("M 396 120 L 412 86 L 428 120 Z", edge(1.5))
    body += ell(404, 132, 26, 7, edge(1.3))
    body += ask(389, 162, 9)
    return frame(w, h, body, "生物多样性")


# ---------------------------------------------------------------- 登记

def catalog():
    """(题号, svg, 题干里必须有的片段, 额外允许的数字, 图里必须有的文字)。"""
    rows = []

    def add(qid, drawing, expect, extra=(), must=()):
        rows.append((qid, drawing, expect, set(extra), tuple(must)))

    add("cnb_j003_q1", microscope("目镜", "物镜"), "显微镜的放大倍数等于", must=("目镜", "物镜", "?"))
    add("cnb_j003_q3", microscope("10×", "40×"), "目镜 10×、物镜 40×", must=("10", "40", "?"))
    add("cnb_j003_q4", slide_field(), "把玻片向右移动", must=("玻片", "向右", "?"))
    add("cnb_j004_q1", plant_cell(), "对细胞起支持和保护作用的结构是", must=("植物细胞", "?"))
    add("cnb_j005_q3", cell_compare(), "动物细胞没有的结构是", must=("动物细胞", "植物细胞", "?"))
    add("cnb_j006_q4", energy_converters(), "叶绿体和线粒体都被称为能量转换器", must=("叶绿体", "线粒体", "?"))
    add("cnb_j007_q2", chromosome_change(), "细胞分裂时，染色体的变化是", must=("染色体",))
    add("cnb_j007_q4", two_divisions(), "连续两次分裂", must=("第一次", "第二次", "两次", "?"))
    add("cnb_j009_q2", plant_organs(), "绿色开花植物的营养器官是", must=("根", "茎", "叶", "花", "果实", "种子"))
    add("cnb_j010_q2", paramecium(), "草履虫在水中运动", must=("草履虫", "?"))
    add("cnb_j012_q2", pine_seed(), "松树的种子外面没有果皮包被", must=("松树", "种子", "果皮"))
    add("cnb_j014_q1", fish_gill(), "鱼在水中呼吸", must=("鱼", "?"))
    add("cnb_j016_q1", bird_lung(), "鸟类呼吸的特点是", must=("肺", "气囊", "?"))
    add("cnb_j018_q1", bacteria_yeast(), "细菌与酵母菌相比", must=("细菌", "酵母菌", "?"))
    add("cnb_j020_q1", virus_shape(), "病毒的结构通常包括", must=("病毒", "?"))
    add("cnb_j022_q4", classify_ranks(), "分类单位越小", must=("界", "门", "纲", "目", "科", "属", "种", "?"))
    add("cnb_j023_q2", seed_sprout(), "最先突破种皮的是", must=("种皮", "?"))
    add("cnb_j024_q1", root_tip(), "根吸收水分和无机盐的主要部位是", must=("根毛", "?"))
    add("cnb_j025_q1", flower_parts(), "与结出果实和种子直接有关的结构是", must=("花瓣", "?"))
    add("cnb_j025_q3", ovule_dev(), "胚珠发育成", must=("胚珠", "?"))
    add("cnb_j026_q1", stem_vessels(), "水分在植物体内上升", must=("水分", "?"))
    add("cnb_j026_q2", leaf_stoma(), "蒸腾作用的水主要通过哪里散失", must=("叶片", "?"))
    add("cnb_j027_q1", photosynthesis_inputs(), "光合作用的原料是", must=("光", "?"))
    add("cnb_j027_q2", iodine_leaf(), "滴加碘液后变蓝的部位", must=("碘液", "变蓝", "?"))
    add("cnb_j029_q1", carbon_oxygen(), "碳氧平衡", must=("植物", "动物", "氧气", "二氧化碳"))
    add("cnb_j033_q2", digestive(), "消化和吸收的主要场所是", must=("胃", "?"))
    add("cnb_j035_q4", swallow_flap(), "盖住喉口", must=("喉", "气管", "?"))
    add("cnb_j036_q3", alveolus_exchange(), "肺泡与血液之间的气体交换", must=("肺泡", "血液", "?"))
    add("cnb_j038_q1", heart_vessels(), "把血液从心脏送到全身各处", must=("心脏", "全身", "?"))
    add("cnb_j039_q1", heart_wall(), "壁最厚的是", must=("心尖", "?"))
    add("cnb_j039_q3", circulation_loops(), "体循环的路径是", must=("体循环", "肺", "全身", "?"))
    add("cnb_j040_q2", urinary_outline(), "泌尿系统包括", must=("泌尿系统", "?"))
    add("cnb_j040_q3", nephron(), "肾小球和肾小囊", must=("肾小球", "肾小囊", "?"))
    add("cnb_j041_q1", eye_section(), "在眼球里成像的部位是", must=("瞳孔", "视神经", "?"))
    add("cnb_j042_q1", reflex_arc(), "完成反射的神经结构是", must=("感受器", "传入神经", "神经中枢", "传出神经", "效应器", "?"))
    add("cnb_j043_q3", elbow_flex(), "肱二头肌和肱三头肌", must=("肱二头肌", "肱三头肌", "?"))
    add("cnb_j043_q4", joint_section(), "关节里减少摩擦的结构是", must=("关节囊", "?"))
    add("cnb_j050_q1", ecosystem_roles(), "能把无机物制造成有机物的是", must=("无机物", "有机物", "光", "?"))
    add("cnb_j050_q3", food_chain(), "草→兔→狐", must=("草", "兔", "狐", "能量", "?"))
    add("cnb_j051_q1", biosphere_layers(), "生物圈的范围大致包括", must=("大气圈", "水圈", "岩石圈", "?"))
    add("cnb_j054_q3", graft_join(), "嫁接时，成活的关键是", must=("接穗", "砧木", "?"))
    add("cnb_j056_q1", gene_segment(), "基因是", must=("DNA", "?"))
    add("cnb_j057_q3", parent_chromosomes(), "子女的染色体", must=("父方", "母方", "?"))
    add("cnb_j058_q1", relative_traits(), "相对性状是指", must=("相对性状",))
    add("cnb_j058_q2", genotype_dd(), "基因组成为 Dd", must=("Dd", "?"))
    add("cnb_j059_q3", sex_gametes(), "生男孩还是女孩", must=("卵细胞", "精子", "?"))
    add("cnb_j063_q2", giraffe_necks(), "长颈鹿的长颈", must=("长颈鹿", "?"))
    add("cnb_j065_q1", biodiversity_levels(), "生物多样性包括", must=("生物多样性", "?"))
    return rows


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
        if not str(q.get("topicId", "")).startswith("cnb_j"):
            problems.append("%s 不是初中生物题" % qid)
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
        "<!DOCTYPE html><meta charset=\"utf-8\"><title>生物图示预览</title>",
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
    print("初中生物带图题：%d（本次新写入或更新 %d）" % (len(items), added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
