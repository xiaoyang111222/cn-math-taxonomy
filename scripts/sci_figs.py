#!/usr/bin/env python3
"""小学科学配图。按 (知识点 key, 第几题) 挂到题目上；只用 currentColor，深色模式下自动反色。"""
from fig_draw import svg, edge, thin, face, line, poly, circ, text, hidden

E, T = edge(), thin()


def wide(w, h, W, b):
    """把偏窄的图放进更宽的画布居中，避免在手机上被拉得过高。"""
    return svg(W, h, '<g transform="translate(%d,0)">%s</g>' % ((W - w) // 2, b))


def path(d, attrs=E):
    return '<path d="%s" %s/>' % (d, attrs)


def rect(x, y, w, h, attrs=E, rx=0):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" %s/>' % (x, y, w, h, rx, attrs)


def arrow(a, b, sw=2.2):
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    l = 11
    p1 = (b[0] - l * math.cos(ang - 0.4), b[1] - l * math.sin(ang - 0.4))
    p2 = (b[0] - l * math.cos(ang + 0.4), b[1] - l * math.sin(ang + 0.4))
    return line(a, b, thin(sw)) + poly([b, p1, p2], face(1))


def sun(x, y, r=18):
    s = circ(x, y, r, face(0.25)) + circ(x, y, r, E)
    import math
    for k in range(8):
        a = k * math.pi / 4
        s += line((x + (r + 5) * math.cos(a), y + (r + 5) * math.sin(a)),
                  (x + (r + 13) * math.cos(a), y + (r + 13) * math.sin(a)), T)
    return s


def bulb(x, y):
    return circ(x, y, 13, E) + line((x - 9, y - 9), (x + 9, y + 9), T) + line((x - 9, y + 9), (x + 9, y - 9), T)


def cell(x, y, label=True):
    """电池符号：竖线一长一短，长的为正极。x,y 为中心，横向导线。"""
    s = line((x - 5, y - 18), (x - 5, y + 18), edge(2.6)) + line((x + 5, y - 9), (x + 5, y + 9), edge(4))
    if label:
        s += text(x - 14, y - 22, "+", 16) + text(x + 16, y - 14, "−", 16)
    return s


def balance():
    b = line((60, 150), (200, 150), E) + line((130, 150), (130, 70), E) + poly([(110, 150), (150, 150), (130, 135)], face(0.3))
    b += line((60, 50), (200, 90), E) + circ(130, 70, 4, face(1))
    b += line((70, 53), (70, 75), T) + path("M45 75 L95 75 L85 92 L55 92 Z")
    b += line((190, 87), (190, 105), T) + path("M165 105 L215 105 L205 122 L175 122 Z")
    b += rect(60, 55, 22, 20, face(0.45)) + circ(190, 98, 6, face(0.45))
    return svg(260, 165, b)


def ruler():
    b = rect(20, 70, 300, 40, E, 3)
    for i in range(0, 11):
        x = 30 + i * 28
        b += line((x, 70), (x, 88), T) + text(x, 104, str(i), 13)
        if i < 10:
            b += line((x + 14, 70), (x + 14, 80), T)
    x0, x1 = 30 + 2 * 28, 30 + 9 * 28
    b += path("M%d 50 Q%d 40 %d 50 L%d 50 Q%d 40 %d 50 Q%d 66 %d 58 L%d 58 Q%d 66 %d 50" %
              (x0 + 6, x0, x0 + 6, x1 - 6, x1, x1 - 6, x1, x1 - 6, x0 + 6, x0, x0 + 6), E)
    b += rect(x0 + 6, 44, x1 - x0 - 12, 12, face(0.25))
    b += line((x0, 40), (x0, 70), hidden(1.4)) + line((x1, 40), (x1, 70), hidden(1.4)) + text(170, 125, "单位：厘米", 13)
    return svg(340, 135, b)


def thermometer(top_c):
    """刻度 -10～30，每格 1℃。液柱顶端在 top_c。"""
    y = lambda c: 220 - (c + 10) * 5
    b = rect(70, 15, 24, 215, E, 12) + circ(82, 238, 15, E) + circ(82, 238, 10, face(0.55))
    b += rect(78, y(top_c), 8, 238 - y(top_c), face(0.55))
    for c in range(-10, 31):
        L = 14 if c % 10 == 0 else (10 if c % 5 == 0 else 6)
        b += line((96, y(c)), (96 + L, y(c)), thin(1.2))
        if c % 10 == 0:
            b += text(128, y(c) + 5, str(c), 13, "start")
    b += text(30, 30, "℃", 16)
    return wide(180, 265, 380, b)


def face_sun():
    b = circ(130, 120, 14, E) + line((130, 106), (130, 80), T) + text(130, 70, "前", 15)
    b += sun(130, 30, 12) + text(175, 34, "早上的太阳", 13, "start")
    b += text(80, 125, "左手", 14) + text(180, 125, "右手", 14) + line((116, 120), (100, 120), T) + line((144, 120), (160, 120), T)
    b += text(130, 165, "（从头顶往下看）", 12)
    return wide(260, 175, 330, b)


def shadow_pm():
    b = line((40, 150), (300, 150), E) + line((170, 150), (170, 80), edge(3.2))
    b += sun(45, 55, 14) + text(45, 100, "西", 16) + text(295, 175, "东", 16) + text(40, 175, "西", 16)
    b += text(170, 175, "?", 16) + line((60, 66), (170, 80), hidden(1.4))
    return svg(330, 185, b)


def cup_in_water():
    b = rect(30, 70, 220, 120, E)
    b += rect(32, 95, 66, 93, face(0.15)) + rect(182, 95, 66, 93, face(0.15)) + rect(98, 150, 84, 38, face(0.15))
    b += line((30, 95), (100, 95), T) + line((180, 95), (250, 95), T) + line((100, 150), (180, 150), T)
    b += path("M100 160 L100 40 L180 40 L180 160")
    b += path("M115 46 Q140 40 165 47 Q170 62 140 66 Q112 62 115 46 Z", face(0.35))
    b += text(140, 115, "空气", 14) + text(215, 130, "水", 14) + text(215, 30, "纸团", 13) + line((190, 28), (160, 50), thin(1.1))
    b += text(140, 210, "杯口朝下，竖直压入水中", 12)
    return svg(280, 220, b)


def bottles():
    b = ""
    for i, (name, lv) in enumerate(zip("甲乙丙丁", [20, 45, 70, 95])):
        x = 30 + i * 70
        b += path("M%d 40 L%d 60 L%d 60 L%d 160 L%d 160 L%d 60 L%d 60 L%d 40" % (x + 18, x + 18, x, x, x + 50, x + 50, x + 32, x + 32))
        b += rect(x + 2, 158 - lv, 46, lv, face(0.3)) + text(x + 25, 185, name, 16)
    return svg(320, 195, b)


def seed():
    b = path("M40 100 C40 40 200 30 210 95 C215 150 60 165 40 100 Z")
    b += path("M50 100 C55 55 195 50 198 98 L50 100 Z", face(0.2)) + line((50, 100), (198, 98), T)
    b += path("M60 100 Q68 88 80 92 Q86 100 78 108 Q66 110 60 100 Z", face(0.5))
    b += path("M80 95 Q92 82 104 86", thin(2))
    labels = [("①", (192, 62), (225, 40)), ("②", (70, 108), (40, 150)), ("③", (140, 80), (230, 120)), ("④", (100, 86), (110, 20))]
    for s, p, q in labels:
        b += line(p, q, thin(1.2)) + text(q[0], q[1] + 6 if q[1] < 30 else q[1] + 12, s, 16)
    return wide(260, 175, 330, b)


def flower():
    b = line((150, 230), (150, 175), E)
    b += path("M150 170 C125 160 118 120 132 100 L168 100 C182 120 175 160 150 170 Z", face(0.25))  # 子房
    b += path("M150 170 C125 160 118 120 132 100 L168 100 C182 120 175 160 150 170 Z")
    b += line((150, 100), (150, 45), E) + path("M140 45 L160 45", edge(4))  # 柱头
    b += path("M110 168 Q80 150 70 120", E) + path("M190 168 Q220 150 230 120", E)  # 萼片
    b += path("M128 168 Q60 110 70 40 Q110 70 132 110", E) + path("M172 168 Q240 110 230 40 Q190 70 168 110", E)  # 花瓣
    b += line((135, 160), (110, 70), T) + circ(110, 66, 6, face(0.6)) + line((165, 160), (190, 70), T) + circ(190, 66, 6, face(0.6))
    labels = [("①", (75, 70), (30, 70)), ("②", (190, 66), (265, 85)), ("③", (158, 45), (230, 20)), ("④", (165, 140), (265, 150)), ("⑤", (75, 128), (30, 160))]
    for s, p, q in labels:
        b += line(p, q, thin(1.1)) + text(q[0] + (10 if q[0] > 200 else -10), q[1] + 6, s, 16)
    return wide(300, 240, 380, b)


def short_circuit():
    b = path("M60 100 L60 40 L240 40 L240 100") + path("M60 140 L60 170 L240 170 L240 140")
    b += line((60, 100), (60, 140), T)
    b = path("M110 105 L60 105 L60 40 L240 40 L240 105 L190 105") + cell(150, 105)
    b += line((110, 105), (145, 105), E) + line((155, 105), (190, 105), E)
    b += text(150, 30, "导线直接连接两极", 13)
    return svg(300, 140, b)


def series():
    b = path("M80 50 L50 50 L50 150 L250 150 L250 50 L220 50") + cell(150, 50)
    b += line((80, 50), (145, 50), E) + line((155, 50), (220, 50), E)
    b = path("M145 50 L50 50 L50 150 L102 150") + path("M128 150 L172 150") + path("M198 150 L250 150 L250 50 L155 50") + cell(150, 50)
    b += bulb(115, 150) + bulb(185, 150) + text(115, 185, "灯 1", 13) + text(185, 185, "灯 2", 13)
    return svg(300, 195, b)


def switch(x, y):
    return circ(x, y, 3, face(1)) + circ(x + 30, y, 3, face(1)) + line((x, y), (x + 27, y - 14), E)


def parallel():
    b = cell(150, 30) + path("M145 30 L40 30 L40 170 L60 170") + path("M155 30 L260 30 L260 170")
    b += path("M40 100 L60 100") + switch(60, 100) + path("M90 100 L137 100") + bulb(150, 100) + path("M163 100 L260 100")
    b += switch(60, 170) + path("M90 170 L137 170") + bulb(150, 170) + path("M163 170 L260 170")
    b += text(75, 125, "开关 1", 12) + text(75, 195, "开关 2", 12) + text(185, 90, "灯 1", 12) + text(185, 160, "灯 2", 12)
    return svg(300, 205, b)


def microscope_view():
    b = circ(110, 100, 80, E) + path("M55 140 Q65 120 85 130 Q95 150 70 155 Q52 152 55 140 Z", face(0.45))
    b += text(110, 200, "显微镜视野", 13)
    return wide(220, 210, 340, b)


def lever():
    yb = lambda x: 140 - (x - 60) * 50 / 245
    b = line((20, 160), (320, 160), E) + path("M25 160 Q25 105 62 108 Q95 112 92 160 Z", face(0.3))
    b += poly([(108, 160), (132, 160), (120, yb(120))], face(0.45)) + line((60, 140), (305, 90), edge(4))
    for name, x in (("A", 165), ("B", 230), ("C", 300)):
        b += circ(x, yb(x), 4, face(1)) + text(x, yb(x) - 12, name, 15)
    b += text(120, 182, "支点", 13) + text(58, 182, "石头", 13)
    return svg(340, 192, b)


def ramps():
    b = poly([(20, 140), (100, 140), (100, 60)], E) + text(60, 165, "甲", 16)
    b += poly([(140, 140), (320, 140), (320, 60)], E) + text(230, 165, "乙", 16)
    b += rect(60, 88, 18, 14, face(0.45)) + rect(220, 103, 18, 14, face(0.45))
    return svg(340, 175, b)


def movable_pulley():
    b = line((30, 20), (210, 20), edge(4)) + line((80, 20), (80, 110), T) + line((160, 20), (160, 110), T)
    b = line((30, 20), (210, 20), edge(4)) + line((90, 20), (90, 110), E) + line((150, 110), (150, 40), E)
    b += path("M90 110 A30 30 0 0 0 150 110") + circ(120, 110, 30, E) + circ(120, 110, 4, face(1))
    b += line((120, 110), (120, 160), T) + rect(95, 160, 50, 34, face(0.4)) + arrow((150, 60), (150, 35))
    b += text(175, 60, "拉", 14) + text(120, 214, "重物", 13)
    return wide(240, 222, 380, b)


def food_chain():
    names = ["草", "蝗虫", "青蛙", "蛇"]
    b = ""
    for i, s in enumerate(names):
        x = 20 + i * 90
        b += rect(x, 30, 64, 36, E, 8) + text(x + 32, 54, s, 15)
        if i < 3:
            b += arrow((x + 66, 48), (x + 88, 48))
    b += text(180, 95, "箭头指向吃它的动物", 12)
    return svg(380, 105, b)


def eclipse():
    b = sun(40, 70, 26) + text(40, 130, "太阳", 13)
    b += circ(170, 70, 8, face(0.7)) + text(170, 130, "X", 15)
    b += circ(290, 70, 22, E) + text(290, 130, "地球", 13)
    b += line((66, 50), (290, 68), hidden(1.2)) + line((66, 90), (290, 72), hidden(1.2))
    return svg(330, 140, b)


FIGS = {
    ("g1b_qingzhong", 1): balance(),
    ("g2b_celiang", 4): ruler(),
    ("g3a_qiwenji", 3): thermometer(23),
    ("g3a_qiwenji", 4): thermometer(-5),
    ("g3b_taiyang", 4): face_sun(),
    ("g3b_yingzi", 4): shadow_pm(),
    ("g4a_zhanju", 1): cup_in_water(),
    ("g4a_gaodi", 4): bottles(),
    ("g4b_zhongzi", 3): seed(),
    ("g4b_guoshi", 1): flower(),
    ("g4b_dengpao", 4): short_circuit(),
    ("g4b_jianyi", 4): series(),
    ("g4b_zhaoming", 1): parallel(),
    ("g5a_xianweijing", 4): microscope_view(),
    ("g5a_ganggan", 4): lever(),
    ("g5a_xiemian", 2): ramps(),
    ("g5a_hualun", 3): movable_pulley(),
    ("g5b_shiwulian", 4): food_chain(),
    ("g6b_rishi", 1): eclipse(),
}
