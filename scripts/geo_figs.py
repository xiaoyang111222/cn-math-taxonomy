#!/usr/bin/env python3
"""给初中地理（topicId 以 cng_j 开头）里最需要看位置、地形或过程的题写入内联 SVG。

只改下面登记的题，大约 35–50 道，不给全部题目硬配。可重复运行：
  python3 scripts/geo_figs.py
  python3 scripts/geo_figs.py --preview /tmp/geo-figs.html

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

# 示意国界（经纬度），只求相对位置能认，不作为实测地图。
_BORDER_LL = [
    (75, 40), (82, 45), (92, 47), (102, 48), (112, 48), (118, 50),
    (126, 52), (134, 48), (130, 43), (124, 40), (121, 37), (119, 34),
    (122, 31), (120, 27), (116, 23.5), (110, 21.5), (104, 22), (97, 25),
    (90, 28), (82, 32), (76, 36),
]


def _xy(lon, lat, ox, oy, s):
    x = ox + (lon - 73) / 62 * s
    y = oy + (54 - lat) / 36 * s * 0.92
    return (x, y)


def _china(ox, oy, s):
    return [_xy(lon, lat, ox, oy, s) for lon, lat in _BORDER_LL]


def _at(lon, lat, ox, oy, s):
    return _xy(lon, lat, ox, oy, s)


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
    length = 10
    tip = b
    p1 = (b[0] - length * math.cos(ang - 0.42), b[1] - length * math.sin(ang - 0.42))
    p2 = (b[0] - length * math.cos(ang + 0.42), b[1] - length * math.sin(ang + 0.42))
    end = (b[0] - 1.5 * math.cos(ang), b[1] - 1.5 * math.sin(ang))
    return line(a, end, thin(sw)) + poly([tip, p1, p2], face(1))


def blob(pts, op=0.08, sw=1.7):
    return poly(pts, face(op)) + poly(pts, edge(sw))


def box(x, y, w, h, lines, op=0.07, size=15, sw=1.8):
    if isinstance(lines, str):
        lines = [lines]
    body = rect(x, y, w, h, face(op), 8) + rect(x, y, w, h, edge(sw), 8)
    gap = size + 5
    block = gap * len(lines)
    y0 = y + (h - block) / 2 + size - 1
    for i, line_s in enumerate(lines):
        body += text(x + w / 2, y0 + i * gap, line_s, size)
    return body


def pin(x, y, label, dx=0, dy=-12, size=14, anchor="middle", r=4.2):
    return circ(x, y, r, face(1)) + text(x + dx, y + dy, label, size, anchor)


def ask(x, y, r=12):
    return circ(x, y, r, edge(2.1)) + text(x, y + 5, "?", 16)


def north(x, y):
    return arrow((x, y + 16), (x, y), 1.6) + text(x, y + 30, "北", 12)


def frame(w, h, body, title, note="示意图"):
    if title:
        body += text(w / 2, 20, title, 15)
    if note:
        body += text(w / 2, h - 12, note, 12)
    return svg(w, h, body)


def land_china(ox, oy, s, op=0.08):
    return blob(_china(ox, oy, s), op)


def sun(x, y, r=16):
    body = circ(x, y, r, face(0.22)) + circ(x, y, r, edge(2))
    for k in range(8):
        a = k * math.pi / 4
        body += line(
            (x + (r + 4) * math.cos(a), y + (r + 4) * math.sin(a)),
            (x + (r + 11) * math.cos(a), y + (r + 11) * math.sin(a)),
            thin(1.4),
        )
    return body


def globe(cx, cy, r):
    body = circ(cx, cy, r, face(0.05)) + circ(cx, cy, r, edge(2.2))
    body += ell(cx, cy, r, r * 0.28, edge(1.4))
    body += ell(cx, cy, r * 0.38, r, hidden(1.3))
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


# ---------------------------------------------------------------- 地球与太阳系

def solar_type():
    """太阳和行星都画出来。地球属于哪一类天体留空。"""
    w, h = 440, 220
    body = sun(48, 110, 18)
    body += text(48, 148, "太阳", 14)
    xs = [110, 150, 194, 238, 286, 328, 364, 398]
    rs = [5, 6, 7, 6, 11, 10, 8, 8]
    for x, r in zip(xs, rs):
        body += circ(x, 110, r, face(0.12)) + circ(x, 110, r, edge(1.6))
    body += text(194, 86, "地球", 14)
    body += ask(194, 154)
    return frame(w, h, body, "太阳系")


def earth_moon():
    """月球绕地球。月球属于哪一类天体留空。"""
    w, h = 420, 230
    body = ell(200, 118, 110, 48, hidden(1.6))
    body += circ(200, 118, 36, face(0.08)) + circ(200, 118, 36, edge(2.2))
    body += text(200, 124, "地球", 15)
    body += circ(310, 118, 10, face(0.16)) + circ(310, 118, 10, edge(1.7))
    body += text(310, 86, "月球", 14)
    body += ask(310, 154)
    return frame(w, h, body, "地月系")


def eight_planets():
    """由近及远排开。不写第几位。"""
    w, h = 460, 220
    body = sun(40, 108, 16)
    body += text(40, 144, "太阳", 13)
    xs = [96, 136, 178, 220, 268, 314, 356, 396]
    rs = [5, 6, 7, 6, 12, 11, 8, 8]
    names = ["水星", "金星", "地球", "火星", "", "", "", ""]
    for x, r, lab in zip(xs, rs, names):
        body += circ(x, 108, r, face(0.12)) + circ(x, 108, r, edge(1.6))
        if lab:
            body += text(x, 142, lab, 13)
    body += text(230, 176, "由近及远", 13)
    return frame(w, h, body, "太阳系八大行星")


def prime_meridian():
    """0° 经线画出来，专名留空。"""
    w, h = 420, 250
    cx, cy, r = 200, 128, 72
    body = globe(cx, cy, r)
    body += line((cx, cy - r), (cx, cy + r), edge(2.2))
    body += text(cx + 18, cy - 50, "0°", 15, "start")
    body += text(cx, cy + r + 22, "赤道", 14)
    body += ask(320, 90)
    return frame(w, h, body, "地球仪")


def lat_direction():
    """纬线画出来，指示的方向留空。"""
    w, h = 420, 250
    cx, cy, r = 190, 128, 72
    body = globe(cx, cy, r)
    body += ell(cx, cy - 22, r * 0.88, 16, edge(2.2))
    body += text(cx, cy - 48, "纬线", 14)
    body += text(cx, cy + r + 22, "经线", 14)
    body += line((cx, cy - r + 4), (cx, cy + r - 4), thin(1.5))
    body += ask(330, 108)
    return frame(w, h, body, "经纬网")


def rotation_dir():
    """画出地球。自转方向留空。"""
    w, h = 420, 240
    cx, cy, r = 190, 120, 70
    body = globe(cx, cy, r)
    body += text(cx, cy - r - 10, "北", 14)
    body += text(cx - r - 16, cy + 5, "西", 14, "end")
    body += text(cx + r + 16, cy + 5, "东", 14, "start")
    body += text(cx, 214, "地球", 14)
    body += ask(330, 120)
    return frame(w, h, body, "地球自转")


def day_night():
    """昼和夜画出来。由哪种运动引起留空。"""
    w, h = 440, 230
    body = sun(56, 118, 18)
    body += text(56, 158, "太阳", 13)
    cx, cy, r = 230, 118, 64
    body += circ(cx, cy, r, face(0.06)) + circ(cx, cy, r, edge(2.2))
    body += path("M %s %s A %s %s 0 0 1 %s %s L %s %s Z" % (
        n(cx), n(cy - r), n(r), n(r), n(cx), n(cy + r), n(cx), n(cy - r)), face(0.28))
    body += text(cx - 28, cy + 6, "昼", 15)
    body += text(cx + 28, cy + 6, "夜", 15)
    body += ask(360, 118)
    return frame(w, h, body, "昼夜")


def summer_solstice():
    """直射点画出来。是哪一条纬线留空。"""
    w, h = 440, 250
    body = sun(54, 128, 16)
    body += text(54, 168, "太阳", 13)
    cx, cy, r = 240, 128, 70
    body = body + globe(cx, cy, r)
    body += line((cx - r + 4, cy), (cx + r - 4, cy), edge(1.8))
    body += text(cx + r + 8, cy + 5, "赤道", 14, "start")
    body += ell(cx, cy - 26, r * 0.86, 14, hidden(1.8))
    body += arrow((86, 102), (cx - 12, cy - 26), 2.0)
    body += ask(cx, cy - 52)
    return frame(w, h, body, "北半球夏至日")


def revolution():
    """公转轨道画出来。产生的现象留空。"""
    w, h = 440, 250
    body = ell(220, 128, 150, 62, hidden(1.6))
    body += sun(220, 128, 16)
    body += text(220, 158, "太阳", 13)
    spots = [(70, 128), (220, 66), (370, 128), (220, 190)]
    for x, y in spots:
        body += circ(x, y, 11, face(0.12)) + circ(x, y, 11, edge(1.6))
    body += text(70, 154, "地球", 13)
    body += ask(220, 214)
    return frame(w, h, body, "地球公转")


# ---------------------------------------------------------------- 地图与等高线

def map_elements():
    """三件东西分开画，不把三要素写成一句。"""
    w, h = 440, 250
    body = rect(40, 48, 200, 150, face(0.04), 8) + rect(40, 48, 200, 150, edge(1.8), 8)
    body += north(210, 70)
    body += line((60, 170), (140, 170), edge(2))
    body += line((60, 166), (60, 174), edge(2)) + line((140, 166), (140, 174), edge(2))
    body += text(100, 190, "比例尺", 14)
    body += box(270, 56, 120, 52, "河流  ～～", 0.06, 14)
    body += text(330, 128, "图例", 14)
    body += text(140, 70, "地图", 14)
    return frame(w, h, body, "阅读地图")


def default_dir():
    """没有指向标的图。默认方向留空。"""
    w, h = 420, 240
    body = rect(90, 50, 240, 140, face(0.04), 8) + rect(90, 50, 240, 140, edge(1.8), 8)
    body += text(210, 92, "地图", 16)
    body += text(210, 118, "无指向标", 14)
    body += ask(210, 160)
    return frame(w, h, body, "一般地图")


def scale_bar():
    """写出 1:100000。实地距离留空。"""
    w, h = 440, 220
    body = box(80, 50, 280, 48, "1:100000", 0.06, 18)
    body += line((80, 140), (200, 140), edge(2.4))
    body += line((80, 134), (80, 146), edge(2.2))
    body += line((200, 134), (200, 146), edge(2.2))
    body += text(140, 128, "图上 1 厘米", 14)
    body += ask(320, 140)
    body += text(320, 168, "实地", 13)
    return frame(w, h, body, "数字式比例尺")


def contour_dense():
    """密集和稀疏对照。坡度结论留空。"""
    w, h = 440, 250
    body = rect(36, 48, 170, 150, face(0.04), 6) + rect(36, 48, 170, 150, edge(1.5), 6)
    body += rect(234, 48, 170, 150, face(0.04), 6) + rect(234, 48, 170, 150, edge(1.5), 6)
    for i in range(8):
        y = 68 + i * 14
        body += line((52, y), (190, y), thin(1.5))
    for i in range(4):
        y = 72 + i * 28
        body += line((250, y), (388, y), thin(1.5))
    body += text(121, 216, "密集", 14)
    body += text(319, 216, "稀疏", 14)
    body += ask(220, 216)
    return frame(w, h, body, "等高线地形图")


def valley_contour():
    """向高处凸。地形名称留空。"""
    w, h = 420, 260
    curves = [
        "M 70 200 Q 210 150 350 200",
        "M 90 176 Q 210 120 330 176",
        "M 114 152 Q 210 96 306 152",
        "M 140 130 Q 210 78 280 130",
    ]
    body = ""
    for d in curves:
        body += path(d, edge(1.8))
    body += text(210, 58, "高", 15)
    body += text(210, 224, "低", 15)
    body += ask(210, 118)
    return frame(w, h, body, "等高线")


# ---------------------------------------------------------------- 海陆与板块

def land_sea():
    """海陆都标出来。面积比例留空。"""
    w, h = 440, 250
    body = rect(40, 48, 360, 160, face(0.04), 10) + rect(40, 48, 360, 160, edge(1.4), 10)
    body += ell(150, 130, 70, 48, face(0.14)) + ell(150, 130, 70, 48, edge(1.8))
    body += text(150, 136, "陆地", 15)
    body += text(310, 120, "海洋", 15)
    body += ask(380, 88)
    return frame(w, h, body, "地球表面")


def _world_base(asia_label=None):
    """七大洲相对位置。亚洲留给调用方去标。"""
    body = rect(24, 44, 412, 176, face(0.04), 8)
    parts = [
        (78, 100, 32, 36, "北美洲"),
        (96, 172, 18, 32, "南美洲"),
        (198, 86, 22, 14, "欧洲"),
        (208, 142, 28, 40, "非洲"),
        (348, 182, 22, 12, "大洋洲"),
        (220, 210, 96, 8, "南极洲"),
    ]
    for cx, cy, rx, ry, lab in parts:
        body += ell(cx, cy, rx, ry, face(0.12)) + ell(cx, cy, rx, ry, edge(1.5))
        if lab == "南极洲":
            body += text(cx, cy + 4, lab, 12)
        elif lab == "欧洲":
            body += text(cx, cy + 4, lab, 12)
        else:
            body += text(cx, cy + 4, lab, 13)
    body += ell(300, 108, 62, 36, face(0.16)) + ell(300, 108, 62, 36, edge(1.7))
    if asia_label:
        body += text(300, 112, asia_label, 14)
    return body


def continents():
    """亚洲最大，名称留空。"""
    w, h = 460, 270
    body = _world_base()
    body += ask(300, 108)
    return frame(w, h, body, "七大洲")


def suez():
    """亚非之间的通道留空。"""
    w, h = 440, 240
    body = ell(150, 130, 50, 70, face(0.1)) + ell(150, 130, 50, 70, edge(1.7))
    body += text(150, 136, "非洲", 15)
    body += ell(300, 92, 70, 40, face(0.1)) + ell(300, 92, 70, 40, edge(1.7))
    body += text(300, 96, "亚洲", 15)
    body += line((198, 92), (232, 92), edge(2.4))
    body += ask(216, 64)
    return frame(w, h, body, "亚洲与非洲")


def continental_drift():
    """南美洲和非洲轮廓能对上。学名留空。"""
    w, h = 440, 240
    left = [(70, 70), (110, 80), (120, 130), (100, 190), (70, 170), (56, 110)]
    right = [(250, 80), (300, 70), (330, 120), (310, 190), (250, 170), (236, 120)]
    body = blob(left, 0.12) + blob(right, 0.12)
    body += text(90, 214, "南美洲", 14)
    body += text(290, 214, "非洲", 14)
    body += arrow((130, 120), (220, 120), 2.0)
    body += ask(380, 90)
    return frame(w, h, body, "两块大陆的轮廓")


def plate_volcanoes():
    """火山画在交界处。集中地带的名称留空。"""
    w, h = 440, 230
    body = rect(40, 70, 160, 100, face(0.08), 6) + rect(40, 70, 160, 100, edge(1.7), 6)
    body += rect(240, 70, 160, 100, face(0.08), 6) + rect(240, 70, 160, 100, edge(1.7), 6)
    body += text(120, 124, "板块", 15)
    body += text(320, 124, "板块", 15)
    for y in (86, 120, 154):
        body += poly([(210, y - 14), (222, y + 10), (198, y + 10)], face(0.3))
        body += poly([(210, y - 14), (222, y + 10), (198, y + 10)], edge(1.4))
    body += text(210, 196, "火山", 14)
    body += ask(210, 54)
    return frame(w, h, body, "火山和地震")


def red_sea_rift():
    """红海在中间。两侧怎么运动留空。"""
    w, h = 440, 230
    body = rect(50, 60, 120, 120, face(0.1), 6) + rect(50, 60, 120, 120, edge(1.7), 6)
    body += rect(270, 60, 120, 120, face(0.1), 6) + rect(270, 60, 120, 120, edge(1.7), 6)
    body += rect(178, 70, 84, 100, face(0.05), 4)
    body += text(220, 124, "红海", 15)
    body += arrow((160, 120), (70, 120), 2.2)
    body += arrow((280, 120), (370, 120), 2.2)
    body += ask(220, 54)
    return frame(w, h, body, "红海两侧")


# ---------------------------------------------------------------- 气候

def temp_latitude():
    """赤道到极地。递变规律留空。"""
    w, h = 420, 250
    cx, cy, r = 180, 128, 72
    body = globe(cx, cy, r)
    body += text(cx + r + 10, cy + 5, "赤道", 14, "start")
    body += text(cx, cy - r - 8, "极地", 14)
    body += text(cx, cy + r + 20, "极地", 14)
    body += ask(340, 90)
    return frame(w, h, body, "世界气温")


def temp_altitude():
    """1000 米来自题干。升降留空。"""
    w, h = 420, 260
    body = poly([(70, 210), (200, 58), (330, 210)], face(0.08))
    body += poly([(70, 210), (200, 58), (330, 210)], edge(2))
    body += line((200, 58), (200, 210), hidden(1.5))
    body += text(214, 78, "1000米", 14, "start")
    body += ask(200, 150)
    body += text(200, 236, "同纬度", 13)
    return frame(w, h, body, "海拔与气温")


def windward_slope():
    """迎风坡和背风坡都标。原因留空。"""
    w, h = 440, 250
    body = poly([(80, 200), (220, 70), (360, 200)], face(0.08))
    body += poly([(80, 200), (220, 70), (360, 200)], edge(2))
    body += arrow((50, 150), (150, 118), 2.2)
    body += text(70, 136, "湿润气流", 13, "start")
    body += text(140, 188, "迎风坡", 14)
    body += text(300, 188, "背风坡", 14)
    body += path("M 150 100 q 10 16 0 28 q 12 10 4 22", thin(1.6))
    body += path("M 168 96 q 10 16 0 28", thin(1.6))
    body += ask(220, 48)
    return frame(w, h, body, "地形雨")


def rainforest_belt():
    """赤道附近画一条带。具体名称留空。"""
    w, h = 460, 260
    body = _world_base("亚洲")
    body += rect(40, 118, 380, 22, face(0.18))
    body += text(50, 110, "赤道", 13, "start")
    body += ask(220, 96)
    return frame(w, h, body, "气候分布带")


def climograph():
    """夏热冬雨。不写气候名称。"""
    w, h = 440, 260
    body = line((70, 40), (70, 200), edge(1.6))
    body += line((70, 200), (400, 200), edge(1.6))
    body += text(40, 56, "气温", 13)
    body += text(400, 56, "降水", 13, "end")
    months = [("冬", 110), ("春", 190), ("夏", 270), ("秋", 350)]
    heights = [70, 36, 16, 40]
    for (lab, x), ht in zip(months, heights):
        body += rect(x - 16, 200 - ht, 32, ht, face(0.18))
        body += rect(x - 16, 200 - ht, 32, ht, edge(1.3))
        body += text(x, 220, lab, 14)
    body += path("M 110 150 Q 190 120 270 70 Q 350 110 350 130", edge(2.2))
    body += text(270, 58, "气温", 13)
    return frame(w, h, body, "某地气温与降水")


def asia_relief():
    """中部高四周低画出来。不写成一句。"""
    w, h = 440, 250
    body = ell(220, 128, 150, 78, face(0.06)) + ell(220, 128, 150, 78, edge(1.8))
    body += ell(220, 128, 46, 28, face(0.2)) + ell(220, 128, 46, 28, edge(1.6))
    body += text(220, 134, "高", 16)
    body += text(90, 128, "低", 14)
    body += text(350, 128, "低", 14)
    body += text(220, 54, "低", 14)
    body += text(220, 210, "低", 14)
    body += text(220, 236, "亚洲", 13)
    return frame(w, h, body, "亚洲地势")


# ---------------------------------------------------------------- 世界区域

def japan_plates():
    """日本画在交界。交界名称留空。"""
    w, h = 440, 230
    body = rect(40, 64, 150, 110, face(0.08), 6) + rect(40, 64, 150, 110, edge(1.6), 6)
    body += rect(250, 64, 150, 110, face(0.08), 6) + rect(250, 64, 150, 110, edge(1.6), 6)
    body += text(115, 124, "板块", 14)
    body += text(325, 124, "板块", 14)
    body += arrow((175, 110), (205, 110), 2)
    body += arrow((265, 110), (235, 110), 2)
    body += ell(220, 150, 16, 28, face(0.2)) + ell(220, 150, 16, 28, edge(1.6))
    body += text(220, 196, "日本", 14)
    body += ask(220, 54)
    return frame(w, h, body, "日本附近")


def japan_industry():
    """工业点画在太平洋一侧。具体岸段留空。"""
    w, h = 420, 250
    body = ell(200, 80, 18, 16, face(0.1)) + ell(200, 80, 18, 16, edge(1.5))
    body += ell(210, 130, 40, 28, face(0.1)) + ell(210, 130, 40, 28, edge(1.5))
    body += ell(200, 172, 16, 12, face(0.1)) + ell(200, 172, 16, 12, edge(1.5))
    body += ell(168, 168, 14, 10, face(0.1)) + ell(168, 168, 14, 10, edge(1.5))
    body += text(200, 214, "日本", 14)
    body += text(80, 128, "日本海", 13)
    body += text(330, 128, "太平洋", 13)
    for x, y in ((248, 118), (246, 140), (232, 158), (220, 172)):
        body += circ(x, y, 4, face(1))
    body += ask(248, 96)
    return frame(w, h, body, "日本工业")


def malacca():
    """海峡画出来。连接的大洋留空。"""
    w, h = 440, 240
    body = poly([(80, 50), (160, 50), (140, 200), (60, 200)], face(0.1))
    body += poly([(80, 50), (160, 50), (140, 200), (60, 200)], edge(1.6))
    body += ell(280, 140, 36, 70, face(0.1)) + ell(280, 140, 36, 70, edge(1.6))
    body += text(110, 128, "半岛", 14)
    body += text(280, 128, "岛屿", 14)
    body += text(200, 90, "马六甲海峡", 14)
    body += ask(200, 160)
    body += ask(200, 54)
    return frame(w, h, body, "马六甲海峡")


def three_continents():
    """三洲画出来。五海之名不逐一写。"""
    w, h = 440, 250
    body = ell(250, 90, 70, 36, face(0.1)) + ell(250, 90, 70, 36, edge(1.5))
    body += text(270, 86, "亚洲", 14)
    body += ell(140, 90, 40, 28, face(0.1)) + ell(140, 90, 40, 28, edge(1.5))
    body += text(130, 94, "欧洲", 14)
    body += ell(170, 170, 46, 36, face(0.1)) + ell(170, 170, 46, 36, edge(1.5))
    body += text(170, 176, "非洲", 14)
    for cx, cy in ((200, 70), (90, 130), (200, 130), (250, 150), (310, 140)):
        body += ell(cx, cy, 16, 10, face(0.04)) + ell(cx, cy, 16, 10, edge(1.3))
    body += text(330, 176, "海", 13)
    body += ask(360, 70)
    return frame(w, h, body, "西亚位置")


def australia_rings():
    """半环画出来。分布特点留空。"""
    w, h = 420, 250
    body = ell(210, 130, 90, 70, face(0.05)) + ell(210, 130, 90, 70, edge(1.8))
    body += path("M 130 90 A 90 70 0 0 1 290 90", edge(2))
    body += path("M 150 104 A 70 52 0 0 1 270 104", edge(1.7))
    body += path("M 170 118 A 50 36 0 0 1 250 118", edge(1.5))
    body += text(210, 150, "澳大利亚", 14)
    body += ask(210, 54)
    return frame(w, h, body, "气候和植被带")


def amazon_basin():
    """巴西轮廓。雨林所在流域留空。"""
    w, h = 420, 250
    pts = [(160, 60), (280, 80), (300, 150), (240, 210), (140, 180), (120, 110)]
    body = blob(pts, 0.08)
    body += text(200, 230, "巴西", 14)
    body += path("M 150 120 C 190 110, 230 120, 270 130", edge(2))
    body += ask(210, 120)
    return frame(w, h, body, "巴西")


# ---------------------------------------------------------------- 中国

def four_seas():
    """自北向南四个海区。名称留空。"""
    w, h = 420, 270
    ox, oy, s = 36, 40, 210
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    labels = [("甲", 122, 39), ("乙", 121, 36), ("丙", 122, 31), ("丁", 116, 22)]
    for lab, lon, lat in labels:
        x, y = _at(lon, lat, ox, oy, s)
        body += ask(x + 36, y) if lab == "甲" else circ(x + 36, y, 11, edge(1.6))
        if lab != "甲":
            body += text(x + 36, y + 5, lab, 13)
        else:
            body += text(x + 58, y + 5, lab, 13, "start")
    body += text(w - 48, 230, "南", 13)
    body += text(w - 48, 88, "北", 13)
    return frame(w, h, body, "濒临的海洋")


def pop_density():
    """东南密西北疏。结论留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    dense = [(117, 39), (121, 31), (114, 30), (113, 23), (120, 36), (118, 34), (116, 28), (119, 32)]
    sparse = [(87, 43), (84, 41), (91, 38), (95, 36), (88, 37)]
    for lon, lat in dense:
        x, y = _at(lon, lat, ox, oy, s)
        body += circ(x, y, 3.2, face(1))
        body += circ(x + 6, y + 5, 2.6, face(1))
        body += circ(x - 5, y + 4, 2.4, face(1))
    for lon, lat in sparse:
        x, y = _at(lon, lat, ox, oy, s)
        body += circ(x, y, 2.4, face(1))
    body += text(_at(118, 28, ox, oy, s)[0], _at(118, 28, ox, oy, s)[1] + 28, "东南", 13)
    body += text(_at(86, 42, ox, oy, s)[0], _at(86, 42, ox, oy, s)[1] - 14, "西北", 13)
    body += ask(w - 36, 120)
    return frame(w, h, body, "人口分布")


def heihe_tengchong():
    """黑河和腾冲连起来。这条线的意义留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    a = _at(127.5, 50.2, ox, oy, s)
    b = _at(98.5, 25.0, ox, oy, s)
    body += line(a, b, hidden(2.2))
    body += pin(a[0], a[1], "黑河", dx=14, dy=-8, anchor="start", size=13)
    body += pin(b[0], b[1], "腾冲", dx=-10, dy=16, anchor="end", size=13)
    body += ask((a[0] + b[0]) / 2 + 18, (a[1] + b[1]) / 2)
    return frame(w, h, body, "黑河—腾冲一线")


def three_steps():
    """西高东低三级台阶。特征句子留空。"""
    w, h = 440, 250
    body = poly([(40, 200), (40, 80), (150, 80), (150, 200)], face(0.18))
    body += poly([(40, 200), (40, 80), (150, 80), (150, 200)], edge(1.7))
    body += poly([(150, 200), (150, 120), (270, 120), (270, 200)], face(0.12))
    body += poly([(150, 200), (150, 120), (270, 120), (270, 200)], edge(1.7))
    body += poly([(270, 200), (270, 160), (390, 160), (390, 200)], face(0.07))
    body += poly([(270, 200), (270, 160), (390, 160), (390, 200)], edge(1.7))
    body += text(40, 220, "西", 14, "start")
    body += text(390, 220, "东", 14, "end")
    body += ask(220, 54)
    return frame(w, h, body, "地势剖面")


def step_mountains():
    """一、二级阶梯分界画出来。山脉名称留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    pts = [_at(lon, lat, ox, oy, s) for lon, lat in ((80, 36), (95, 38), (99, 36), (102, 28))]
    for i in range(len(pts) - 1):
        body += line(pts[i], pts[i + 1], edge(2.4))
    body += text(_at(90, 33, ox, oy, s)[0], _at(90, 33, ox, oy, s)[1], "第一级", 13)
    body += text(_at(108, 36, ox, oy, s)[0], _at(108, 36, ox, oy, s)[1], "第二级", 13)
    body += ask(pts[1][0], pts[1][1] - 22)
    return frame(w, h, body, "地势阶梯分界")


def two_rivers():
    """两条大河。最长的那条不写名称。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    yellow = [_at(lon, lat, ox, oy, s) for lon, lat in ((100, 36), (110, 35), (114, 35), (118, 38))]
    yangtze = [_at(lon, lat, ox, oy, s) for lon, lat in ((97, 33), (105, 30), (112, 30), (121, 32))]
    for i in range(len(yellow) - 1):
        body += line(yellow[i], yellow[i + 1], thin(2.0))
    for i in range(len(yangtze) - 1):
        body += line(yangtze[i], yangtze[i + 1], edge(2.4))
    body += text(yangtze[2][0], yangtze[2][1] + 18, "甲", 14)
    body += text(yellow[2][0], yellow[2][1] - 12, "乙", 14)
    body += ask(yangtze[0][0] - 6, yangtze[0][1] - 10)
    return frame(w, h, body, "两条大河")


def south_north_water():
    """水从南方调向北方。工程名称留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    a = _at(114, 30.5, ox, oy, s)
    b = _at(116, 39.5, ox, oy, s)
    c = _at(112, 34.5, ox, oy, s)
    d = _at(108, 34.2, ox, oy, s)
    e = _at(109, 38.0, ox, oy, s)
    body += arrow(a, b, 2.2)
    body += arrow(c, e, 2.0)
    body += arrow(d, e, 2.0)
    body += text(a[0] - 8, a[1] + 16, "长江", 13, "end")
    body += text(b[0] + 10, b[1] - 6, "北方", 13, "start")
    body += ask(w - 36, 130)
    return frame(w, h, body, "跨流域调水")


def typhoon_path():
    """从海上指向东南沿海。影响地区留空。"""
    w, h = 420, 270
    ox, oy, s = 50, 40, 210
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    p = _at(125, 22, ox, oy, s)
    q = _at(118, 24.5, ox, oy, s)
    body += circ(p[0] + 20, p[1] + 10, 16, edge(1.6))
    body += path("M %s %s q 12 -14 0 -24 q -16 8 -8 20" % (n(p[0] + 20), n(p[1] + 10)), thin(1.6))
    body += arrow((p[0] + 8, p[1]), q, 2.2)
    body += ask(q[0] - 6, q[1] - 16)
    return frame(w, h, body, "台风")


def four_regions():
    """四个区域分开。名称组合留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    a = _at(104, 34, ox, oy, s)
    b = _at(119, 33, ox, oy, s)
    body += line(a, b, edge(2))
    c = _at(98, 38, ox, oy, s)
    d = _at(110, 42, ox, oy, s)
    body += line(c, d, hidden(1.8))
    e = _at(80, 36, ox, oy, s)
    f = _at(102, 28, ox, oy, s)
    body += line(e, f, hidden(1.8))
    marks = [(92, 33, "甲"), (100, 42, "乙"), (116, 38, "丙"), (112, 26, "丁")]
    for lon, lat, lab in marks:
        x, y = _at(lon, lat, ox, oy, s)
        body += text(x, y, lab, 14)
    body += ask(w - 36, 120)
    return frame(w, h, body, "四大地理区域")


def qinling_huaihe():
    """南北分开。界线名称留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    a = _at(104, 34, ox, oy, s)
    b = _at(119, 33, ox, oy, s)
    body += line(a, b, edge(2.3))
    body += text(_at(113, 38, ox, oy, s)[0], _at(113, 38, ox, oy, s)[1], "北方", 14)
    body += text(_at(112, 26, ox, oy, s)[0], _at(112, 26, ox, oy, s)[1], "南方", 14)
    body += ask((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 18)
    return frame(w, h, body, "北方与南方")


def loess_plateau():
    """黄土高原位置留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    yellow = [_at(lon, lat, ox, oy, s) for lon, lat in ((100, 36), (110, 35), (114, 35), (118, 38))]
    for i in range(len(yellow) - 1):
        body += line(yellow[i], yellow[i + 1], edge(2.2))
    body += text(yellow[-1][0] + 8, yellow[-1][1] - 6, "黄河", 13, "start")
    p = _at(109, 37, ox, oy, s)
    body += ell(p[0], p[1], 28, 18, face(0.16)) + ell(p[0], p[1], 28, 18, edge(1.6))
    body += ask(p[0], p[1])
    return frame(w, h, body, "黄土高原")


def hk_macau():
    """澳门在西侧。香港一侧留空。"""
    w, h = 440, 240
    body = path("M 40 70 L 200 70 L 200 40 L 360 40 L 360 70 L 400 70 L 400 200 L 40 200 Z", face(0.06))
    body += path("M 40 70 L 200 70 L 200 40 L 360 40 L 360 70 L 400 70", edge(2))
    body += text(220, 92, "珠江口", 14)
    body += ell(150, 150, 22, 16, face(0.14)) + ell(150, 150, 22, 16, edge(1.6))
    body += text(150, 186, "澳门", 14)
    body += text(150, 128, "珠海", 13)
    body += ell(310, 150, 22, 16, face(0.14)) + ell(310, 150, 22, 16, edge(1.6))
    body += ask(310, 150)
    body += text(220, 54, "北", 13)
    return frame(w, h, body, "珠江口")


def taiwan_strait():
    """海峡名称留空。"""
    w, h = 420, 250
    body = path("M 40 50 L 180 50 L 200 200 L 40 200 Z", face(0.08))
    body += path("M 40 50 L 180 50 L 200 200 L 40 200 Z", edge(1.7))
    body += ell(310, 130, 28, 70, face(0.1)) + ell(310, 130, 28, 70, edge(1.7))
    body += text(110, 128, "福建", 15)
    body += text(310, 128, "台湾岛", 14)
    body += ask(240, 130)
    return frame(w, h, body, "台湾岛与大陆")


def nw_zones():
    """自东向西三带。景观序列留空。"""
    w, h = 440, 230
    body = rect(40, 60, 120, 110, face(0.18), 4) + rect(40, 60, 120, 110, edge(1.5), 4)
    body += rect(160, 60, 120, 110, face(0.10), 4) + rect(160, 60, 120, 110, edge(1.5), 4)
    body += rect(280, 60, 120, 110, face(0.04), 4) + rect(280, 60, 120, 110, edge(1.5), 4)
    body += text(40, 196, "东", 14, "start")
    body += text(400, 196, "西", 14, "end")
    body += ask(220, 54)
    return frame(w, h, body, "西北地区")


def oasis_beads():
    """盆地边缘的水源点。成因留空。"""
    w, h = 440, 250
    body = ell(220, 130, 150, 78, face(0.04)) + ell(220, 130, 150, 78, edge(1.8))
    body += text(220, 136, "沙漠", 14)
    body += path("M 80 70 Q 140 40 220 48 Q 300 40 360 70", edge(2))
    body += text(220, 40, "高山", 14)
    for x, y in ((100, 100), (140, 86), (200, 80), (270, 86), (330, 104)):
        body += circ(x, y, 8, face(0.2)) + circ(x, y, 8, edge(1.4))
    body += text(100, 196, "绿洲", 14, "start")
    body += ask(220, 54)
    return frame(w, h, body, "盆地边缘")


def three_source():
    """三条河从源区流出。河名留空。"""
    w, h = 420, 270
    ox, oy, s = 70, 40, 220
    body = land_china(ox, oy, s)
    body += north(w - 28, 48)
    src = _at(95, 34.5, ox, oy, s)
    body += ell(src[0], src[1], 18, 12, face(0.16)) + ell(src[0], src[1], 18, 12, edge(1.5))
    body += text(src[0] - 14, src[1] + 22, "三江源", 13, "end")
    ends = [(121, 32), (118, 38), (100, 24)]
    for lon, lat in ends:
        body += arrow(src, _at(lon, lat, ox, oy, s), 2.0)
        body += ask(_at(lon, lat, ox, oy, s)[0], _at(lon, lat, ox, oy, s)[1])
    return frame(w, h, body, "三江源")


# ---------------------------------------------------------------- 登记

def catalog():
    """(题号, svg, 题干里必须有的片段, 额外允许的数字, 图里必须有的文字)。"""
    rows = []

    def add(qid, drawing, expect, extra=(), must=()):
        rows.append((qid, drawing, expect, set(extra), tuple(must)))

    add("cng_j001_q1", solar_type(), "地球在太阳系中属于哪一类天体", must=("太阳", "地球", "?"))
    add("cng_j001_q2", earth_moon(), "月球属于哪一类天体", must=("地球", "月球", "?"))
    add("cng_j001_q3", eight_planets(), "太阳系八大行星按距太阳由近及远", must=("太阳", "地球"))
    add("cng_j002_q2", prime_meridian(), "0°经线又称为", must=("0°", "赤道", "?"))
    add("cng_j002_q3", lat_direction(), "纬线指示的方向是", must=("纬线", "经线", "?"))
    add("cng_j003_q1", rotation_dir(), "地球自转的方向是", must=("地球", "东", "西", "?"))
    add("cng_j003_q2", day_night(), "昼夜交替主要是由哪一种运动引起的", must=("昼", "夜", "?"))
    add("cng_j003_q3", summer_solstice(), "北半球夏至日，太阳直射的纬线是", must=("赤道", "?"))
    add("cng_j003_q4", revolution(), "地球公转产生的地理现象是", must=("太阳", "地球", "?"))
    add("cng_j004_q1", map_elements(), "地图的三要素是", must=("比例尺", "图例", "北"))
    add("cng_j004_q2", default_dir(), "在没有指向标的一般地图上，默认方向是", must=("地图", "?"))
    add("cng_j004_q4", scale_bar(), "数字式比例尺 1:100000", must=("1:100000", "1", "?"))
    add("cng_j005_q1", contour_dense(), "等高线地形图上，等高线越密集", must=("密集", "稀疏", "?"))
    add("cng_j005_q3", valley_contour(), "等高线向海拔高处凸出的部位通常是", must=("高", "低", "?"))
    add("cng_j007_q1", land_sea(), "地球表面海洋与陆地面积大约是", must=("海洋", "陆地", "?"))
    add("cng_j007_q2", continents(), "面积最大的大洲是", must=("非洲", "?"))
    add("cng_j007_q3", suez(), "亚洲与非洲的分界线是", must=("亚洲", "非洲", "?"))
    add("cng_j009_q2", continental_drift(), "魏格纳提出的学说是", must=("南美洲", "非洲", "?"))
    add("cng_j009_q3", plate_volcanoes(), "世界火山、地震主要集中在", must=("火山", "板块", "?"))
    add("cng_j009_q4", red_sea_rift(), "红海面积在不断扩大", must=("红海", "?"))
    add("cng_j011_q2", temp_latitude(), "世界气温分布的基本规律是", must=("赤道", "极地", "?"))
    add("cng_j011_q3", temp_altitude(), "海拔每升高 1000 米", must=("1000", "?"))
    add("cng_j012_q4", windward_slope(), "迎风坡降水往往多于背风坡", must=("迎风坡", "背风坡", "?"))
    add("cng_j013_q1", rainforest_belt(), "热带雨林气候主要分布在", must=("赤道", "?"))
    add("cng_j013_q2", climograph(), "地中海气候的特征是", must=("气温", "降水", "夏", "冬"))
    add("cng_j018_q2", asia_relief(), "亚洲的地势特征是", must=("高", "低", "亚洲"))
    add("cng_j020_q2", japan_plates(), "日本多火山地震，主要因为位于", must=("日本", "板块", "?"))
    add("cng_j020_q3", japan_industry(), "日本工业集中分布在", must=("日本", "太平洋", "?"))
    add("cng_j021_q2", malacca(), "马六甲海峡是连接哪两个大洋的重要通道", must=("马六甲海峡", "?"))
    add("cng_j024_q1", three_continents(), "西亚地处亚、欧、非三洲交界", must=("亚洲", "欧洲", "非洲", "?"))
    add("cng_j027_q3", australia_rings(), "澳大利亚气候和植被带的分布特点是", must=("澳大利亚", "?"))
    add("cng_j029_q2", amazon_basin(), "世界上面积最大的热带雨林主要分布在巴西的", must=("巴西", "?"))
    add("cng_j031_q3", four_seas(), "濒临的海洋自北向南依次是", must=("北", "南", "?"))
    add("cng_j032_q1", pop_density(), "人口分布的基本特点是", must=("东南", "西北", "?"))
    add("cng_j032_q2", heihe_tengchong(), "黑河—腾冲一线是我国重要的", must=("黑河", "腾冲", "?"))
    add("cng_j034_q1", three_steps(), "我国地势的基本特征是", must=("西", "东", "?"))
    add("cng_j034_q2", step_mountains(), "第一级阶梯和第二级阶梯的分界山脉包括", must=("第一级", "第二级", "?"))
    add("cng_j036_q1", two_rivers(), "我国最长的河流是", must=("甲", "乙", "?"))
    add("cng_j038_q3", south_north_water(), "缓解北方缺水的跨流域调水工程是", must=("长江", "北方", "?"))
    add("cng_j044_q2", typhoon_path(), "台风主要影响我国的", must=("?",))
    add("cng_j046_q1", four_regions(), "我国四大地理区域是", must=("甲", "乙", "丙", "丁", "?"))
    add("cng_j046_q2", qinling_huaihe(), "北方地区和南方地区的分界线大致是", must=("北方", "南方", "?"))
    add("cng_j049_q1", loess_plateau(), "黄土高原是世界上最大的黄土堆积区，主要位于", must=("黄河", "?"))
    add("cng_j053_q2", hk_macau(), "香港位于珠江口的", must=("珠江口", "澳门", "?"))
    add("cng_j054_q1", taiwan_strait(), "台湾岛是我国面积最大的岛屿，西隔什么与福建省相望", must=("台湾岛", "福建", "?"))
    add("cng_j055_q2", nw_zones(), "从东到西，西北地区的自然景观大致是", must=("东", "西", "?"))
    add("cng_j056_q2", oasis_beads(), "盆地边缘出现串珠状绿洲", must=("绿洲", "沙漠", "高山", "?"))
    add("cng_j058_q1", three_source(), "三江源地区位于青海省南部，是哪些大河的源头", must=("三江源", "?"))
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
        if not str(q.get("topicId", "")).startswith("cng_j"):
            problems.append("%s 不是初中地理题" % qid)
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
        "<!DOCTYPE html><meta charset=\"utf-8\"><title>地理图示预览</title>",
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
    print("初中地理带图题：%d（本次新写入或更新 %d）" % (len(items), added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
