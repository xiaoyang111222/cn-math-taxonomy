#!/usr/bin/env python3
"""给高中化学（topicId 以 cnk_h 开头）里需要看结构、装置、曲线或电极的题写内联 SVG。

不给全部 408 题硬配。图在编译时由 chem_hs_build.py 调用 figure_for 写入，
重跑构建不会丢掉。单独运行只做自检，不改题库：

  python3 scripts/chem_hs_figs.py
  python3 scripts/chem_hs_figs.py --preview /tmp/chem-hs-figs.html

图只用 currentColor，不引用外网。同一代码每次得到同一张 SVG。
题干对不上就停，避免题号错位后贴错图。
正确选项的全文不写进图里的文字。图是示意图，不是比例图。
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fig_draw import circ, edge, esc, face, hidden, line, poly, text, thin  # noqa: E402
from chem_figs import (  # noqa: E402
    arrow, ask, beaker, box, ell, flask, frame, lamp_at, liquid, liquid_tube,
    overflow_problems, path, rect, v_tube,
)
from check_figures import figure_problems  # noqa: E402

ROOT = os.path.dirname(HERE)
QUESTIONS = os.path.join(ROOT, "data", "questions.json")
NOTE = "示意图，非比例"


def F(w, h, body, title):
    return frame(w, h, body, title, NOTE)


def stick(a, b, order=1, sw=2.1):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    if order == 1:
        offs = (0,)
    elif order == 2:
        offs = (-3.4, 3.4)
    else:
        offs = (-6.2, 0, 6.2)
    body = ""
    for off in offs:
        body += line((a[0] + px * off, a[1] + py * off), (b[0] + px * off, b[1] + py * off), edge(sw))
    return body


def dot(x, y, lab, r=16, size=13):
    body = circ(x, y, r, face(0.08)) + circ(x, y, r, edge(1.7))
    if lab:
        body += text(x, y + size * 0.35, lab, size)
    return body


def wave(x, y, length, amp=10, steps=4):
    d = "M %g %g" % (x, y)
    seg = length / float(steps)
    for i in range(steps):
        x1 = x + seg * i + seg * 0.5
        y1 = y + (amp if i % 2 == 0 else -amp)
        x2 = x + seg * (i + 1)
        d += " Q %g %g %g %g" % (x1, y1, x2, y)
    return path(d, edge(1.8))


def bulb(x, y):
    body = circ(x, y, 13, edge(1.7))
    body += line((x - 6, y - 4), (x + 5, y + 4), thin(1.3))
    body += line((x - 6, y + 4), (x + 5, y - 4), thin(1.3))
    return body


# ---------------------------------------------------------------- 必修一


def ions_mix():
    """四种离子都标出，不标明哪一对结合。"""
    w, h = 500, 320
    body = beaker(150, 78, 200, 170)
    body += liquid(150, 78, 200, 170, 120)
    body += dot(205, 165, "H+", 18, 13)
    body += dot(295, 165, "OH-", 20, 12)
    body += dot(205, 215, "Na+", 20, 12)
    body += dot(295, 215, "Cl-", 20, 12)
    body += ask(430, 170)
    return F(w, h, body, "酸碱溶液中的离子")


def na_cl2():
    """钠和氯气分开画，中间没有键。"""
    w, h = 520, 280
    body = dot(78, 140, "Na", 22, 16)
    body += text(148, 148, "+", 22)
    body += dot(230, 140, "Cl", 20, 15)
    body += stick((252, 140), (308, 140), 1)
    body += dot(330, 140, "Cl", 20, 15)
    body += text(280, 198, "氯", 15)
    body += ask(450, 140)
    return F(w, h, body, "钠与氯气")


def na_into_water():
    """钠还在水面上方，不把现象画成结论。"""
    w, h = 480, 320
    body = beaker(160, 120, 170, 140)
    body += liquid(160, 120, 170, 140, 170)
    body += text(245, 200, "水", 15)
    body += rect(228, 62, 28, 16, edge(1.8), 2)
    body += text(242, 52, "钠", 14)
    body += line((220, 78), (200, 100), edge(1.6))
    body += line((264, 78), (284, 100), edge(1.6))
    body += arrow((242, 84), (242, 112), 1.6)
    body += ask(90, 180)
    return F(w, h, body, "钠放入水")


def chlorine_cloth():
    w, h = 480, 310
    body = beaker(150, 100, 180, 140)
    body += liquid(150, 100, 180, 140, 150)
    body += text(240, 190, "氯水", 15)
    body += rect(200, 70, 70, 110, edge(1.7), 2)
    body += text(300, 64, "有色布条", 14, "start")
    body += ask(80, 160)
    return F(w, h, body, "氯水与布条")


def vol_flask_eyes():
    """三条视线都画出，不标明哪一条对应浓度偏大或偏小。"""
    w, h = 520, 330
    body = line((230, 58), (230, 150), edge(2))
    body += line((274, 58), (274, 150), edge(2))
    body += line((230, 150), (160, 200), edge(2))
    body += line((274, 150), (344, 200), edge(2))
    body += line((160, 200), (160, 250), edge(2))
    body += line((344, 200), (344, 250), edge(2))
    body += line((160, 250), (344, 250), edge(2))
    body += line((218, 108), (286, 108), edge(2.2))
    body += text(200, 100, "刻度线", 14, "end")
    # 凹液面最低处落在刻度线上；平视穿过最低处。控制点使曲线中点正在 y=108。
    body += path("M 236 96 Q 252 120 268 96", edge(1.6))
    body += line((274, 78), (360, 56), thin(1.4))
    body += text(368, 60, "俯视", 15, "start")
    body += line((274, 108), (360, 108), thin(1.4))
    body += text(368, 126, "平视", 15, "start")
    body += line((274, 150), (360, 182), thin(1.4))
    body += text(368, 186, "仰视", 15, "start")
    body += text(252, 278, "容量瓶", 15)
    return F(w, h, body, "定容视线")


def nail_cuso4():
    w, h = 460, 300
    body = beaker(140, 80, 170, 150)
    body += liquid(140, 80, 170, 150, 120)
    body += rect(214, 96, 14, 90, edge(1.8), 2)
    body += text(221, 78, "铁钉", 14)
    body += text(300, 170, "硫酸铜", 14, "start")
    body += ask(70, 160)
    return F(w, h, body, "铁钉放入溶液")


def scn_test():
    w, h = 460, 310
    body = v_tube(190, 90, 52, 150)
    body += liquid_tube(190, 90, 52, 150, 150)
    body += text(216, 270, "Fe3+", 14)
    body += line((216, 48), (216, 88), edge(1.6))
    body += poly([(208, 84), (224, 84), (216, 96)], face(1))
    body += text(250, 52, "硫氰化钾", 14, "start")
    body += ask(80, 160)
    return F(w, h, body, "滴加试剂")


def atom_p11():
    w, h = 480, 320
    cx, cy = 210, 175
    body = ""
    for rx, ry in ((52, 38), (86, 62), (122, 88)):
        body += ell(cx, cy, rx, ry, thin(1.5))
    body += dot(cx, cy, "11", 18, 14)
    body += text(70, 70, "质子数", 15, "start")
    body += line((78, 78), (cx - 16, cy - 8), thin(1.2))
    body += text(400, 168, "电子", 15, "start")
    body += ask(400, 120)
    return F(w, h, body, "中性原子")


def period_row():
    w, h = 520, 280
    body = ""
    labels = ("左", "", "", "右")
    for i, lab in enumerate(labels):
        x = 40 + i * 78
        body += rect(x, 90, 64, 44, edge(1.7), 6)
        if lab:
            body += text(x + 32, 118, lab, 15)
    body += rect(390, 90, 90, 44, edge(1.7), 6)
    body += text(435, 118, "稀有气体", 13)
    body += text(250, 170, "同周期", 14)
    body += arrow((70, 200), (330, 200), 1.7)
    body += text(200, 224, "金属性", 15)
    body += ask(300, 230)
    return F(w, h, body, "同周期主族")


def ion_pair():
    w, h = 460, 280
    body = dot(140, 130, "+", 28, 18)
    body += dot(300, 130, "−", 28, 18)
    body += line((168, 130), (272, 130), thin(1.6))
    body += text(140, 190, "阳离子", 15)
    body += text(300, 190, "阴离子", 15)
    body += ask(230, 210)
    return F(w, h, body, "离子键")


def na_mg_al():
    """三支管子都不画气泡多少。"""
    w, h = 500, 310
    body = ""
    for i, lab in enumerate(("钠", "镁", "铝")):
        x = 70 + i * 140
        body += v_tube(x, 70, 48, 140)
        body += liquid_tube(x, 70, 48, 140, 130)
        body += text(x + 24, 240, lab, 16)
        body += ask(x + 24, 110, 10)
    body += text(250, 276, "水或酸", 14)
    return F(w, h, body, "钠、镁、铝")


# ---------------------------------------------------------------- 必修二


def reagent_order():
    """顺序是题干已经给出的，问号留给原因。"""
    w, h = 520, 280
    body = box(30, 100, 120, 52, "氯化钡")
    body += arrow((160, 126), (210, 126), 1.8)
    body += text(186, 110, "之后", 13)
    body += box(220, 100, 120, 52, "碳酸钠")
    body += ask(420, 126)
    return F(w, h, body, "加入顺序")


def zn_cu_acid():
    """单池锌铜，导线上不画电子方向，锌上不画气泡。"""
    w, h = 520, 340
    body = beaker(140, 168, 240, 110)
    body += liquid(140, 168, 240, 110, 200)
    body += text(260, 232, "稀硫酸", 15)
    body += rect(190, 118, 14, 112, edge(1.8), 2)
    body += rect(320, 118, 14, 112, edge(1.8), 2)
    body += text(197, 106, "锌", 15)
    body += text(327, 106, "铜", 15)
    body += line((197, 118), (197, 72), edge(1.6))
    body += line((327, 118), (327, 72), edge(1.6))
    body += line((197, 72), (245, 72), edge(1.6))
    body += line((285, 72), (327, 72), edge(1.6))
    body += bulb(265, 72)
    body += text(265, 54, "导线", 14)
    body += ask(100, 200)
    return F(w, h, body, "锌铜插入稀硫酸")


def chunk_powder():
    w, h = 520, 360
    body = beaker(40, 90, 150, 140)
    body += liquid(40, 90, 150, 140, 140)
    body += rect(95, 155, 40, 28, face(0.2), 3)
    body += rect(95, 155, 40, 28, edge(1.6), 3)
    body += text(115, 268, "块状", 15)
    body = body + beaker(280, 90, 150, 140)
    body += liquid(280, 90, 150, 140, 140)
    for dx, dy in ((20, 30), (40, 22), (60, 36), (34, 48), (70, 50)):
        body += circ(300 + dx, 150 + dy, 5, face(0.35))
    body += text(355, 268, "粉末", 15)
    body += text(260, 304, "稀盐酸", 14)
    body += ask(250, 70)
    return F(w, h, body, "大理石与酸")


def equilibrium_rates():
    w, h = 480, 280
    body = box(40, 100, 110, 50, "反应物")
    body += box(310, 100, 110, 50, "生成物")
    body += arrow((160, 112), (300, 112), 1.7)
    body += arrow((300, 138), (160, 138), 1.7)
    body += text(230, 100, "正", 14)
    body += text(230, 168, "逆", 14)
    body += ask(230, 210)
    return F(w, h, body, "可逆反应")


def zn_electrode_role():
    w, h = 500, 320
    body = beaker(140, 120, 230, 130)
    body += liquid(140, 120, 230, 130, 170)
    body += rect(185, 70, 14, 120, edge(1.8), 2)
    body += rect(310, 70, 14, 120, edge(1.8), 2)
    body += line((192, 70), (317, 70), edge(1.6))
    body += text(192, 56, "锌", 15)
    body += text(214, 56, "较活泼", 13, "start")
    body += text(317, 56, "铜", 15)
    body += ask(70, 170)
    return F(w, h, body, "锌铜原电池")


def two_hcl():
    """两边都不画气泡，避免把哪边更快画死。"""
    w, h = 480, 310
    body = ""
    for i, lab in enumerate(("稀盐酸", "浓盐酸")):
        x = 90 + i * 200
        body += v_tube(x, 70, 56, 150)
        body += liquid_tube(x, 70, 56, 150, 130)
        body += rect(x + 20, 150, 16, 22, face(0.25), 2)
        body += text(x + 28, 250, lab, 15)
        body += ask(x + 28, 110, 10)
    return F(w, h, body, "两份盐酸")


def ethylene_h2():
    w, h = 520, 280
    c1, c2 = (70, 140), (140, 140)
    body = stick(c1, c2, 2)
    body += dot(70, 140, "C", 16, 14)
    body += dot(140, 140, "C", 16, 14)
    body += text(40, 100, "H", 13)
    body += text(40, 180, "H", 13)
    body += text(170, 100, "H", 13)
    body += text(170, 180, "H", 13)
    body += text(105, 210, "乙烯", 14)
    body += text(250, 140, "H–H", 16)
    body += text(250, 168, "氢气", 13)
    body += arrow((300, 140), (360, 140), 1.8)
    body += ask(430, 140)
    return F(w, h, body, "乙烯与氢气")


def ester_scheme_b2():
    w, h = 520, 280
    body = box(24, 90, 90, 48, "乙醇")
    body += text(132, 120, "+", 18)
    body += box(154, 90, 90, 48, "乙酸")
    body += arrow((254, 114), (310, 114), 1.8)
    body += text(282, 96, "?", 16)
    body += box(320, 78, 70, 40, "酯", size=14)
    body += box(400, 78, 70, 40, "水", size=14)
    body += text(250, 180, "浓硫酸", 14)
    body += text(250, 206, "加热", 14)
    return F(w, h, body, "乙醇与乙酸")


def ethane_ethanol_models():
    w, h = 520, 300
    body = dot(70, 140, "C", 16, 13)
    body += stick((86, 140), (124, 140))
    body += dot(140, 140, "C", 16, 13)
    body += text(105, 200, "乙烷", 15)
    body += dot(280, 140, "C", 16, 13)
    body += stick((296, 140), (334, 140))
    body += dot(350, 140, "C", 16, 13)
    body += stick((366, 140), (404, 140))
    body += dot(420, 140, "O", 16, 13)
    body += stick((436, 140), (468, 120))
    body += text(478, 116, "H", 12, "start")
    body += text(350, 200, "乙醇", 15)
    body += ask(230, 250)
    return F(w, h, body, "球棍模型")


def fraction_column():
    """汽油出口在上，柴油出口在下。"""
    w, h = 460, 330
    body = rect(170, 60, 80, 190, edge(2), 10)
    body += line((120, 220), (170, 220), edge(1.8))
    body += text(110, 224, "石油", 15, "end")
    body += line((250, 100), (330, 100), edge(1.8))
    body += text(338, 104, "汽油", 15, "start")
    body += line((250, 190), (330, 190), edge(1.8))
    body += text(338, 194, "柴油", 15, "start")
    body += ask(80, 140)
    return F(w, h, body, "石油分馏")


# ---------------------------------------------------------------- 选必一


def hess_paths():
    """两条已知焓变都标出，待求的一步只留问号。"""
    w, h = 540, 300
    body = text(24, 58, "直接", 14, "start")
    body += box(24, 72, 96, 42, "石墨")
    body += text(178, 64, "-394", 15)
    body += arrow((132, 93), (220, 93), 1.6)
    body += text(176, 128, "+ O2", 13)
    body += box(232, 72, 110, 42, "CO2")
    body += text(24, 156, "分步", 14, "start")
    body += box(24, 170, 84, 42, "石墨")
    body += text(150, 158, "+1/2 O2", 12)
    body += text(150, 176, "?", 15)
    body += arrow((116, 191), (178, 191), 1.5)
    body += box(188, 170, 70, 42, "CO")
    body += text(302, 158, "+1/2 O2", 12)
    body += text(302, 176, "-283", 14)
    body += arrow((268, 191), (338, 191), 1.5)
    body += box(350, 170, 110, 42, "CO2")
    return F(w, h, body, "两条途径")


def rate_graph():
    w, h = 480, 320
    body = line((70, 230), (420, 230), edge(1.7))
    body += line((70, 230), (70, 60), edge(1.7))
    body += arrow((400, 230), (430, 230), 1.5)
    body += arrow((70, 80), (70, 52), 1.5)
    body += text(400, 258, "时间", 14, "start")
    body += text(78, 48, "浓度", 14, "start")
    body += line((110, 90), (340, 180), edge(2.2))
    body += circ(110, 90, 4, face(1))
    body += circ(340, 180, 4, face(1))
    body += text(110, 78, "0.80", 14)
    body += text(360, 176, "0.20", 14, "start")
    body += text(340, 214, "2 s", 14)
    body += ask(220, 150)
    return F(w, h, body, "浓度变化")


def conc_level():
    w, h = 480, 310
    body = line((70, 230), (420, 230), edge(1.7))
    body += line((70, 230), (70, 60), edge(1.7))
    body += text(400, 256, "时间", 14, "start")
    body += text(78, 52, "浓度", 14, "start")
    body += path("M 90 90 C 150 96 180 150 250 168 C 320 180 360 184 400 186", edge(2))
    body += path("M 90 200 C 150 190 190 150 250 140 C 320 132 360 128 400 126", edge(2))
    body += line((300, 80), (300, 220), hidden(1.3))
    body += ask(360, 100)
    return F(w, h, body, "浓度随时间")


def q_vs_k():
    w, h = 500, 260
    body = line((60, 140), (440, 140), edge(1.8))
    body += line((300, 120), (300, 160), edge(2))
    body += text(300, 110, "K", 16)
    body += text(300, 184, "平衡常数", 13)
    body += circ(160, 140, 6, face(1))
    body += text(160, 110, "Q", 16)
    body += text(160, 184, "浓度商", 13)
    body += ask(160, 220)
    return F(w, h, body, "浓度商与平衡常数")


def pressure_shift():
    w, h = 500, 300
    body = rect(50, 100, 150, 110, edge(2), 4)
    body += text(125, 160, "气体", 15)
    body += arrow((220, 140), (280, 140), 1.8)
    body += text(250, 124, "加压", 14)
    body += rect(300, 120, 110, 80, edge(2), 4)
    body += line((310, 112), (400, 112), edge(2))
    body += line((355, 96), (355, 112), edge(2))
    body += text(250, 230, "气体分子数减少", 14)
    body += ask(430, 200)
    return F(w, h, body, "压强")


def heat_shift():
    w, h = 480, 280
    body = box(40, 110, 110, 50, "反应物")
    body += box(310, 110, 110, 50, "生成物")
    body += arrow((160, 135), (300, 135), 1.8)
    body += text(230, 118, "正反应", 13)
    body += text(230, 186, "吸热", 15)
    body += ask(230, 220)
    return F(w, h, body, "升高温度")


def acetic_partial():
    w, h = 480, 300
    body = beaker(150, 80, 190, 160)
    body += liquid(150, 80, 190, 160, 120)
    body += text(245, 70, "醋酸", 15)
    for x, y in ((190, 160), (230, 175), (270, 165), (210, 210), (260, 205)):
        body += circ(x, y, 7, edge(1.4))
    body += dot(330, 150, "+", 12, 12)
    body += text(400, 154, "离子", 14, "start")
    body += arrow((120, 140), (150, 160), 1.4)
    body += arrow((150, 180), (120, 200), 1.4)
    body += ask(70, 120)
    return F(w, h, body, "醋酸溶液")


def ph_line():
    w, h = 480, 260
    body = rect(70, 110, 340, 32, face(0.08), 8)
    body += rect(70, 110, 340, 32, edge(1.8), 8)
    body += line((240, 98), (240, 154), edge(1.8))
    body += text(240, 88, "7", 16)
    body += text(140, 176, "小于 7", 15)
    body += ask(140, 70)
    return F(w, h, body, "pH")


def heat_fecl3():
    w, h = 460, 320
    body = beaker(150, 130, 170, 120)
    body += liquid(150, 130, 170, 120, 170)
    body += text(235, 200, "热水", 14)
    body += v_tube(210, 70, 44, 120)
    body += liquid_tube(210, 70, 44, 120, 120)
    body += text(300, 90, "氯化铁", 14, "start")
    body += text(120, 250, "加热", 15, "start")
    body += ask(80, 140)
    return F(w, h, body, "氯化铁溶液")


def caco3_acid():
    w, h = 460, 310
    body = beaker(140, 70, 180, 170)
    body += liquid(140, 70, 180, 170, 120)
    body += text(230, 150, "盐酸", 15)
    body += rect(200, 190, 50, 22, face(0.22), 3)
    body += rect(200, 190, 50, 22, edge(1.6), 3)
    body += text(225, 250, "碳酸钙", 14)
    body += circ(190, 160, 4, edge(1.3))
    body += circ(210, 145, 3, edge(1.3))
    body += ask(80, 150)
    return F(w, h, body, "碳酸钙与盐酸")


def burette_read():
    w, h = 500, 330
    body = line((210, 50), (210, 250), edge(2))
    body += line((246, 50), (246, 250), edge(2))
    body += line((210, 250), (246, 250), edge(2))
    for i in range(8):
        yy = 70 + i * 20
        body += line((246, yy), (234, yy), thin(1.2))
    # 凹液面最低处在刻度 y=150；平视穿过这一点。
    body += path("M 214 136 Q 228 164 242 136", edge(1.6))
    body += line((246, 118), (330, 86), thin(1.3))
    body += text(338, 90, "俯视", 15, "start")
    body += line((246, 150), (330, 150), thin(1.3))
    body += text(338, 168, "平视", 15, "start")
    body += line((246, 190), (330, 222), thin(1.3))
    body += text(338, 226, "仰视", 15, "start")
    body += text(140, 150, "滴定管", 15, "end")
    body += ask(80, 210)
    return F(w, h, body, "滴定管读数")


def foam_mix():
    w, h = 520, 300
    body = box(30, 80, 120, 48, "硫酸铝", size=14)
    body += box(30, 160, 140, 48, "碳酸氢钠", size=14)
    body += arrow((160, 104), (230, 140), 1.6)
    body += arrow((180, 184), (230, 160), 1.6)
    body += v_tube(250, 90, 60, 140)
    for i in range(4):
        body += circ(268 + (i % 2) * 16, 70 - i * 8, 6, edge(1.3))
    body += text(400, 80, "泡沫", 15, "start")
    body += ask(450, 180)
    return F(w, h, body, "两种溶液混合")


def salt_bridge_cell():
    """盐桥两端伸进液面以下，导线上不画电子方向。"""
    w, h = 540, 360
    body = beaker(40, 176, 170, 116)
    body += liquid(40, 176, 170, 116, 214)
    body += beaker(340, 176, 170, 116)
    body += liquid(340, 176, 170, 116, 214)
    body += rect(100, 118, 14, 128, edge(1.8), 2)
    body += rect(430, 118, 14, 128, edge(1.8), 2)
    body += text(107, 106, "锌", 15)
    body += text(437, 106, "铜", 15)
    body += line((107, 118), (107, 72), edge(1.7))
    body += line((437, 118), (437, 72), edge(1.7))
    body += line((107, 72), (437, 72), edge(1.7))
    body += text(168, 60, "导线", 14, "start")
    body += ask(280, 48)
    body += path("M 155 236 C 155 132, 395 132, 395 236", edge(1.8))
    body += text(275, 124, "盐桥", 14)
    body += ask(175, 268, 10)
    body += text(125, 322, "溶液", 13)
    body += text(425, 322, "溶液", 13)
    return F(w, h, body, "有盐桥的原电池")


def electro_cucl2():
    w, h = 500, 330
    body = rect(190, 48, 100, 40, edge(1.8), 4)
    body += text(210, 74, "−", 16)
    body += text(270, 74, "+", 16)
    body += text(240, 40, "电源", 13)
    body += line((200, 88), (120, 88), edge(1.6))
    body += line((120, 88), (120, 150), edge(1.6))
    body += line((280, 88), (380, 88), edge(1.6))
    body += line((380, 88), (380, 150), edge(1.6))
    body += beaker(70, 150, 360, 120)
    body += liquid(70, 150, 360, 120, 190)
    body += text(250, 230, "氯化铜", 15)
    body += rect(112, 130, 16, 100, edge(1.8), 2)
    body += rect(372, 130, 16, 100, edge(1.8), 2)
    body += text(120, 124, "惰性", 13)
    body += text(380, 124, "惰性", 13)
    body += ask(180, 250)
    body += ask(330, 250)
    return F(w, h, body, "电解装置")


def broken_plate():
    w, h = 500, 280
    body = rect(80, 130, 340, 36, face(0.06), 4)
    body += rect(80, 130, 340, 36, edge(1.8), 4)
    body += text(180, 154, "铁", 15)
    body += rect(80, 118, 130, 14, edge(1.6), 2)
    body += rect(290, 118, 130, 14, edge(1.6), 2)
    body += text(130, 108, "铜", 14)
    body += text(340, 108, "铜", 14)
    body += path("M 230 110 C 240 90 270 90 280 112", edge(1.5))
    body += text(255, 86, "潮湿", 14)
    body += ask(255, 200)
    return F(w, h, body, "镀层有缺口")


def plate_setup():
    """电源与镀槽分开。两极上下排列，不和电极左右对齐，也不画虚线接线。"""
    w, h = 540, 360
    body = beaker(36, 128, 250, 124)
    body += liquid(36, 128, 250, 124, 172)
    body += text(161, 210, "电镀", 15)
    body += rect(96, 96, 14, 116, edge(1.8), 2)
    body += rect(212, 96, 14, 116, edge(1.8), 2)
    body += text(161, 292, "待镀工件和镀层金属", 14)
    body += rect(372, 108, 108, 132, edge(1.8), 6)
    body += text(426, 92, "电源", 14)
    body += text(426, 156, "+", 20)
    body += text(426, 208, "−", 20)
    body += ask(324, 176)
    return F(w, h, body, "电镀槽")


def fuel_cell():
    w, h = 520, 300
    body = rect(140, 90, 240, 130, edge(2), 6)
    body += text(260, 160, "电解质", 15)
    body += rect(150, 70, 16, 90, edge(1.8), 2)
    body += rect(350, 70, 16, 90, edge(1.8), 2)
    body += text(110, 120, "氢气", 15, "end")
    body += text(410, 120, "氧气", 15, "start")
    body += line((158, 70), (158, 48), edge(1.6))
    body += line((358, 70), (358, 48), edge(1.6))
    body += line((158, 48), (240, 48), edge(1.6))
    body += line((290, 48), (358, 48), edge(1.6))
    body += ask(265, 48)
    return F(w, h, body, "氢氧燃料电池")


# ---------------------------------------------------------------- 选必二


def shells_123():
    w, h = 480, 320
    cx, cy = 180, 175
    body = circ(cx, cy, 8, face(0.4))
    names = ("第一", "第二", "第三")
    for i, lab in enumerate(names):
        r = 36 + i * 40
        body += circ(cx, cy, r, thin(1.6))
        body += text(cx + 8, cy - r + 16, lab, 13, "start")
    body += ask(420, 160)
    return F(w, h, body, "三个能层")


def sodium_shells():
    w, h = 460, 310
    cx, cy = 190, 165
    body = ""
    for rx in (48, 82, 118):
        body += circ(cx, cy, rx, thin(1.5))
    body += dot(cx, cy, "11", 18, 14)
    body += text(70, 60, "原子序数", 14, "start")
    body += ask(400, 160)
    return F(w, h, body, "钠原子")


def sigma_pi():
    """π 的上下两瓣在两核之间有重叠，图内不写重叠方式。"""
    w, h = 540, 300
    body = circ(100, 158, 36, edge(1.7))
    body += circ(152, 158, 36, edge(1.7))
    body += line((36, 158), (220, 158), hidden(1.2))
    body += text(126, 78, "σ", 18)
    x1, x2, y = 328, 380, 162
    body += circ(x1, y, 4, face(1))
    body += circ(x2, y, 4, face(1))
    body += line((270, y), (450, y), hidden(1.2))
    body += ell(x1, 124, 36, 34, edge(1.6))
    body += ell(x2, 124, 36, 34, edge(1.6))
    body += ell(x1, 200, 36, 34, edge(1.6))
    body += ell(x2, 200, 36, 34, edge(1.6))
    body += text(354, 68, "π", 18)
    return F(w, h, body, "轨道重叠")


def co2_linear():
    w, h = 500, 260
    body = dot(110, 130, "O", 18, 14)
    body += dot(230, 130, "C", 18, 14)
    body += dot(350, 130, "O", 18, 14)
    body += stick((128, 130), (212, 130), 2)
    body += stick((248, 130), (332, 130), 2)
    body += text(230, 190, "直线形", 15)
    body += ask(440, 130)
    return F(w, h, body, "二氧化碳")


def ammonia_pyramid():
    w, h = 460, 340
    nxy = (230, 130)
    hs = ((140, 220), (230, 258), (320, 220))
    body = ""
    for hxy in hs:
        body += stick(nxy, hxy)
    body += dot(230, 130, "N", 18, 14)
    for hxy in hs:
        body += dot(hxy[0], hxy[1], "H", 16, 14)
    body += text(230, 300, "三角锥形", 14)
    body += ask(230, 68)
    return F(w, h, body, "氨分子")


def _methane(cx, cy, length):
    body = ""
    ends = []
    for ang in (50, 150, 230, 320):
        rad = math.radians(ang)
        hx = cx + length * math.cos(rad)
        hy = cy + length * math.sin(rad)
        body += stick((cx, cy), (hx, hy))
        ends.append((hx + 11 * math.cos(rad), hy + 12 * math.sin(rad)))
    body += dot(cx, cy, "C", 15, 13)
    for hx, hy in ends:
        body += text(hx, hy, "H", 13)
    return body


def water_methane():
    """两分子水都画成折线，中间用虚线和问号，不写相互作用的名称。"""
    w, h = 540, 340
    o1, h1a, h1b = (78, 150), (40, 198), (128, 138)
    o2, h2a, h2b = (214, 128), (214, 78), (258, 168)
    body = stick(o1, h1a) + stick(o1, h1b) + stick(o2, h2a) + stick(o2, h2b)
    body += line((128, 138), (198, 128), hidden(1.5))
    body += ask(164, 118, 10)
    body += dot(*o1, "O", 16, 14)
    body += dot(*o2, "O", 16, 14)
    body += text(h1a[0], h1a[1] + 16, "H", 13)
    body += text(h1b[0] - 2, h1b[1] - 14, "H", 13)
    body += text(h2a[0], h2a[1] - 8, "H", 13)
    body += text(h2b[0] + 12, h2b[1] + 4, "H", 13)
    body += text(140, 250, "水", 16)
    body += _methane(390, 118, 32)
    body += _methane(470, 210, 26)
    body += text(430, 286, "甲烷", 16)
    return F(w, h, body, "分子之间")


def simple_cubic():
    w, h = 480, 340
    s = 120
    x, y = 130, 230
    dx, dy = 58, -44
    A = (x, y)
    B = (x + s, y)
    C = (x + s, y - s)
    D = (x, y - s)
    E = (x + dx, y + dy)
    Ff = (x + s + dx, y + dy)
    G = (x + s + dx, y - s + dy)
    H = (x + dx, y - s + dy)
    body = ""
    for a, b in ((A, E), (E, Ff), (E, H)):
        body += line(a, b, hidden(1.6))
    for a, b in ((A, B), (B, C), (C, D), (D, A), (B, Ff), (Ff, G), (G, C), (D, H), (H, G)):
        body += line(a, b, edge(1.8))
    for p in (A, B, C, D, E, Ff, G, H):
        body += circ(p[0], p[1], 7, face(0.2)) + circ(p[0], p[1], 7, edge(1.5))
    body += text(240, 292, "8 个顶点", 15)
    body += text(70, 70, "每个顶点被 8 个晶胞共用", 13, "start")
    body += ask(430, 180)
    return F(w, h, body, "简单立方")


def dryice_diamond():
    """干冰是分开的直线分子；金刚石每个碳连四个碳，其中一条用虚线表示朝后。"""
    w, h = 540, 340
    body = ""
    for y in (78, 132, 186):
        body += stick((62, y), (92, y), 2, 1.5)
        body += stick((120, y), (150, y), 2, 1.5)
        body += dot(48, y, "O", 14, 12)
        body += dot(106, y, "C", 14, 12)
        body += dot(164, y, "O", 14, 12)
    body += text(106, 236, "干冰", 15)
    center = (400, 156)
    front_l = (332, 208)
    front_r = (468, 204)
    up = (408, 86)
    back = (352, 112)
    ext = (468, 64)
    rC = 16

    def bond(a, b, attrs):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        return line((a[0] + ux * rC, a[1] + uy * rC), (b[0] - ux * rC, b[1] - uy * rC), attrs)

    body += bond(center, front_l, edge(1.7))
    body += bond(center, front_r, edge(1.7))
    body += bond(center, up, edge(1.7))
    body += bond(center, back, hidden(1.5))
    body += bond(up, ext, edge(1.6))
    for p in (center, front_l, front_r, up, back, ext):
        body += dot(p[0], p[1], "C", rC, 13)
    body += text(400, 258, "金刚石", 15)
    body += text(400, 282, "空间连接", 13)
    return F(w, h, body, "两种固体")


def ionic_states():
    w, h = 520, 300
    body = ""
    for r in range(3):
        for c in range(3):
            cx, cy = 70 + c * 42, 100 + r * 42
            mark = "+" if (r + c) % 2 == 0 else "−"
            body += circ(cx, cy, 12, edge(1.4))
            body += text(cx, cy + 4, mark, 12)
    body += text(112, 240, "固态", 15)
    spots = ((320, 100, "+"), (380, 130, "−"), (430, 100, "+"),
             (340, 170, "−"), (400, 190, "+"), (450, 160, "−"))
    for x, y, mark in spots:
        body += circ(x, y, 12, edge(1.4))
        body += text(x, y + 4, mark, 12)
    body += text(390, 240, "熔融", 15)
    body += ask(250, 150)
    return F(w, h, body, "离子晶体")


def cu_ammine():
    w, h = 480, 320
    cx, cy = 230, 160
    arms = ((cx, cy - 78), (cx + 90, cy), (cx, cy + 78), (cx - 90, cy))
    body = ""
    for x, y in arms:
        body += stick((cx, cy), (x, y))
    body += dot(cx, cy, "Cu", 18, 13)
    for x, y in arms:
        body += dot(x, y, "NH3", 22, 13)
    body += ask(430, 70)
    return F(w, h, body, "铜与氨")


# ---------------------------------------------------------------- 选必三


def ether_ethanol():
    w, h = 540, 300
    # 下标用普通数字，不用 U+2082/U+2086。Noto Sans CJK 常缺这些字形，预览会变成方框。
    # 字宽按 Noto Sans CJK SC 粗体：字母 15px（C 9.8、H 11.4、O 11.6），数字 10px（各 5.9），中心仍在 x=250。
    body = text(225.1, 52, "C", 15, "start")
    body += text(235.9, 57, "2", 10, "start")
    body += text(243.4, 52, "H", 15, "start")
    body += text(255.8, 57, "6", 10, "start")
    body += text(263.3, 52, "O", 15, "start")
    body += dot(50, 140, "C", 15, 12)
    body += stick((65, 140), (100, 140))
    body += dot(115, 140, "C", 15, 12)
    body += stick((130, 140), (165, 140))
    body += dot(180, 140, "O", 15, 12)
    body += stick((195, 140), (220, 112))
    body += text(232, 108, "H", 12, "start")
    body += text(120, 200, "乙醇", 15)
    body += dot(330, 140, "C", 15, 12)
    body += stick((345, 140), (385, 140))
    body += dot(400, 140, "O", 15, 12)
    body += stick((415, 140), (455, 140))
    body += dot(470, 140, "C", 15, 12)
    body += text(400, 200, "甲醚", 15)
    body += ask(270, 240)
    return F(w, h, body, "同一分子式")


def ethylene_br():
    """四个氢围着双键，和乙烯加氢那张同一画法。不写反应类型。"""
    w, h = 540, 300
    c1, c2 = (78, 124), (148, 124)
    body = stick(c1, c2, 2)
    body += dot(78, 124, "C", 16, 14)
    body += dot(148, 124, "C", 16, 14)
    body += text(46, 84, "H", 13)
    body += text(46, 166, "H", 13)
    body += text(180, 84, "H", 13)
    body += text(180, 166, "H", 13)
    body += text(113, 206, "乙烯", 14)
    body += text(258, 128, "Br–Br", 16)
    body += beaker(330, 78, 150, 124)
    body += liquid(330, 78, 150, 124, 128)
    body += text(405, 168, "四氯化碳", 13)
    body += ask(258, 214)
    return F(w, h, body, "乙烯与溴")


def benzene_ring():
    w, h = 420, 320
    cx, cy, r = 200, 165, 72
    pts = []
    for i in range(6):
        ang = math.radians(-90 + i * 60)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    body = ""
    for i in range(6):
        body += line(pts[i], pts[(i + 1) % 6], edge(2.2))
    body += circ(cx, cy, 36, edge(1.7))
    body += text(cx, 268, "苯", 15)
    body += ask(360, 80)
    return F(w, h, body, "苯的环")


def bromoethane_cond():
    w, h = 520, 300
    body = dot(60, 120, "C", 16, 13)
    body += stick((76, 120), (114, 120))
    body += dot(130, 120, "C", 16, 13)
    body += stick((146, 120), (190, 120))
    body += dot(210, 120, "Br", 18, 13)
    body += text(130, 170, "溴乙烷", 14)
    body += box(270, 70, 210, 44, "氢氧化钠的醇溶液", size=14)
    body += text(375, 150, "加热", 15)
    body += arrow((250, 120), (300, 190), 1.6)
    body += ask(430, 210)
    return F(w, h, body, "溴乙烷")


def ethanol_oxidize():
    w, h = 500, 270
    body = box(30, 100, 90, 48, "乙醇")
    body += arrow((130, 124), (220, 124), 1.8)
    body += text(175, 100, "氧气", 14)
    body += text(175, 156, "铜或银", 13)
    body += text(175, 178, "加热", 13)
    body += ask(320, 124)
    return F(w, h, body, "乙醇被氧化")


def aldehyde_test():
    w, h = 480, 360
    body = v_tube(190, 64, 56, 140)
    body += liquid_tube(190, 64, 56, 140, 120)
    body += text(168, 150, "乙醛", 15, "end")
    body += text(268, 112, "新制氢氧化铜", 13, "start")
    body += lamp_at(218, 292)
    body += ask(70, 160)
    return F(w, h, body, "乙醛共热")


def ester_scheme_s3():
    w, h = 540, 280
    body = box(24, 96, 80, 46, "乙酸")
    body += text(122, 124, "+", 18)
    body += box(144, 96, 80, 46, "乙醇")
    body += arrow((234, 119), (300, 119), 1.8)
    body += text(268, 100, "?", 16)
    body += box(310, 96, 120, 46, "乙酸乙酯", size=14)
    body += text(250, 180, "浓硫酸", 14)
    body += text(250, 204, "加热", 14)
    return F(w, h, body, "乙酸与乙醇")


def ester_receiver():
    """圆底烧瓶。导管口停在液面上方。接收液面接近水平，略凹。"""
    w, h = 540, 400
    cx, top = 118, 90
    neck_w, neck_h = 24, 32
    rx, ry = 56, 50
    cy = top + neck_h + ry - 4
    half = neck_w / 2.0
    y_join = cy - ry * math.sqrt(1.0 - (half / rx) ** 2)
    body = ell(cx, cy, rx, ry, edge(1.8))
    body += line((cx - half, top), (cx - half, y_join), edge(1.8))
    body += line((cx + half, top), (cx + half, y_join), edge(1.8))
    body += line((cx - half, top), (cx + half, top), edge(1.8))
    body += text(cx - half - 8, top + 16, "蒸出", 14, "end")
    tube_y, mouth_x, tube_end = 58, 392, 176
    body += line((cx, top), (cx, tube_y), edge(1.8))
    body += line((cx, tube_y), (mouth_x, tube_y), edge(1.8))
    body += line((mouth_x, tube_y), (mouth_x, tube_end), edge(1.8))
    body += text(250, tube_y - 8, "乙酸乙酯", 14)
    x0, y0, tw, th = 354, 148, 76, 128
    rr = tw / 2.0
    y_arc = y0 + th - rr
    x1 = x0 + tw
    body += path(
        "M %g %g L %g %g A %g %g 0 0 0 %g %g L %g %g" % (x0, y0, x0, y_arc, rr, rr, x1, y_arc, x1, y0),
        edge(1.8),
    )
    level = 214
    inset = 4
    xl, xr = x0 + inset, x1 - inset
    mid = (xl + xr) / 2.0
    r_in = (xr - xl) / 2.0
    body += path(
        "M %g %g L %g %g A %g %g 0 0 0 %g %g L %g %g Q %g %g %g %g Z" % (
            xl, level, xl, y_arc, r_in, r_in, xr, y_arc, xr, level, mid, level + 5, xl, level),
        face(0.1),
    )
    body += path("M %g %g Q %g %g %g %g" % (xl, level, mid, level + 5, xr, level), thin(1.3))
    body += text(mouth_x, y0 + th + 34, "饱和碳酸钠", 14)
    body += lamp_at(cx, 346)
    body += ask(498, 200)
    return F(w, h, body, "蒸出后接收")


def silver_setup():
    w, h = 460, 320
    body = beaker(140, 130, 190, 120)
    body += liquid(140, 130, 190, 120, 170)
    body += v_tube(200, 70, 48, 130)
    body += line((210, 96), (210, 170), thin(1.3))
    body += line((238, 96), (238, 170), thin(1.3))
    body += text(300, 100, "银镜反应", 14, "start")
    body += ask(80, 170)
    return F(w, h, body, "水浴中的试管")


def peptide_four():
    w, h = 540, 260
    body = ""
    for i in range(4):
        body += box(30 + i * 125, 90, 100, 48, "氨基酸", size=14)
    body += text(250, 180, "4 个", 16)
    body += ask(270, 210)
    return F(w, h, body, "缩成一条肽")


def glucose_test():
    w, h = 500, 360
    body = v_tube(176, 64, 60, 140)
    body += liquid_tube(176, 64, 60, 140, 120)
    body += text(154, 156, "葡萄糖", 15, "end")
    body += text(260, 112, "新制氢氧化铜", 13, "start")
    body += lamp_at(206, 292)
    body += ask(64, 160)
    return F(w, h, body, "葡萄糖共热")


def poly_ethylene():
    w, h = 540, 280
    body = dot(50, 130, "C", 15, 12)
    body += dot(110, 130, "C", 15, 12)
    body += stick((65, 130), (95, 130), 2)
    body += text(80, 180, "乙烯", 14)
    body += arrow((150, 130), (210, 130), 1.8)
    xs = (250, 300, 350, 400)
    for i in range(len(xs) - 1):
        body += stick((xs[i] + 12, 130), (xs[i + 1] - 12, 130))
    for x in xs:
        body += dot(x, 130, "C", 14, 12)
    body += path("M 236 108 L 228 108 L 228 152 L 236 152", edge(1.5))
    body += path("M 414 108 L 422 108 L 422 152 L 414 152", edge(1.5))
    body += text(430, 100, "n", 14, "start")
    body += text(325, 186, "聚乙烯", 15)
    body += ask(490, 140)
    return F(w, h, body, "由小分子到长链")


def rubber_vulcan():
    w, h = 540, 300
    body = ""
    for i, y in enumerate((90, 140, 190)):
        body += wave(40, y, 160, 8, 3)
    body += text(120, 240, "硫化前", 14)
    for i, y in enumerate((90, 140, 190)):
        body += wave(280, y, 160, 8, 3)
    body += line((330, 98), (330, 132), edge(1.6))
    body += line((390, 148), (390, 182), edge(1.6))
    body += text(318, 122, "S", 12, "end")
    body += text(402, 170, "S", 12, "start")
    body += text(360, 240, "硫化", 15)
    body += ask(490, 140)
    return F(w, h, body, "橡胶的链")


# ---------------------------------------------------------------- 登记


def catalog():
    """(题号, svg, 题干片段, 额外允许的数字, 图中必须出现的文字)。"""
    rows = []

    def add(qid, drawing, expect, extra=(), must=()):
        rows.append((qid, drawing, expect, set(extra), tuple(must)))

    add("cnk_h003_q3", ions_mix(), "稀盐酸与氢氧化钠溶液反应", must=("H+", "OH-", "Na+", "Cl-", "?"))
    add("cnk_h004_q2", na_cl2(), "2Na + Cl2 = 2NaCl", must=("Na", "Cl", "?"))
    add("cnk_h006_q2", na_into_water(), "一小块钠放入水中", must=("钠", "水", "?"))
    add("cnk_h007_q2", chlorine_cloth(), "新制氯水能使有色布条褪色", must=("氯水", "有色布条", "?"))
    add("cnk_h010_q4", vol_flask_eyes(), "定容时若俯视容量瓶的刻度线", must=("容量瓶", "刻度线", "俯视", "平视", "仰视"))
    add("cnk_h011_q1", nail_cuso4(), "把铁钉放入硫酸铜溶液", must=("铁钉", "硫酸铜", "?"))
    add("cnk_h014_q2", scn_test(), "要确认反应后溶液里有没有 Fe3+", must=("硫氰化钾", "Fe3+", "?"))
    add("cnk_h015_q3", atom_p11(), "一种中性原子的质子数是 11", must=("11", "质子数", "电子", "?"))
    add("cnk_h016_q3", period_row(), "主族元素从同周期的左边到右边", must=("稀有气体", "金属性", "?"))
    add("cnk_h017_q1", ion_pair(), "离子键通常存在于", must=("阳离子", "阴离子", "?"))
    add("cnk_h019_q2", na_mg_al(), "比较钠、镁、铝的金属性", must=("钠", "镁", "铝", "?"))

    add("cnk_h024_q3", reagent_order(), "碳酸钠溶液要在氯化钡溶液之后加入", must=("氯化钡", "碳酸钠", "?"))
    add("cnk_h026_q4", zn_cu_acid(), "锌片和铜片用导线连接后插入稀硫酸", must=("锌", "铜", "稀硫酸", "导线", "?"))
    add("cnk_h027_q1", chunk_powder(), "把块状大理石改成粉末", must=("块状", "粉末", "稀盐酸", "?"))
    add("cnk_h027_q3", equilibrium_rates(), "可逆反应达到化学平衡时", must=("正", "逆", "?"))
    add("cnk_h029_q3", zn_electrode_role(), "锌–铜原电池中，较活泼的锌片", must=("锌", "铜", "较活泼", "?"))
    add("cnk_h030_q3", two_hcl(), "一份用稀盐酸，一份用更浓的盐酸", must=("稀盐酸", "浓盐酸", "?"))
    add("cnk_h032_q2", ethylene_h2(), "乙烯与氢气在一定条件下反应", must=("乙烯", "氢气", "?"))
    add("cnk_h033_q4", ester_scheme_b2(), "乙醇与乙酸在浓硫酸加热条件下", must=("乙醇", "乙酸", "浓硫酸", "?"))
    add("cnk_h036_q4", ethane_ethanol_models(), "用模型比较乙烷和乙醇", must=("乙烷", "乙醇", "O", "?"))
    add("cnk_h038_q3", fraction_column(), "石油分馏可以得到汽油、柴油", must=("石油", "汽油", "柴油", "?"))

    add("cnk_h044_q4", hess_paths(), "C(石墨)＋O2(g)＝CO2(g)", must=("石墨", "CO2", "-394", "-283", "?"))
    add("cnk_h046_q3", rate_graph(), "某反应物的浓度在 2 s 内从 0.80 mol/L", must=("0.80", "0.20", "2 s", "浓度", "?"))
    add("cnk_h047_q1", conc_level(), "可逆反应达到化学平衡时，正确的是", must=("浓度", "时间", "?"))
    add("cnk_h047_q3", q_vs_k(), "浓度商小于平衡常数", must=("浓度商", "平衡常数", "?"))
    add("cnk_h049_q2", pressure_shift(), "对气体分子数减少的可逆反应，增大压强", must=("加压", "气体分子数减少", "?"))
    add("cnk_h049_q3", heat_shift(), "已知某可逆反应的正反应吸热", must=("正反应", "吸热", "?"))
    add("cnk_h052_q2", acetic_partial(), "醋酸在水中只有一部分分子电离", must=("醋酸", "?"))
    add("cnk_h053_q1", ph_line(), "常温下，pH 小于 7 的溶液呈", must=("7", "小于 7", "?"))
    add("cnk_h054_q4", heat_fecl3(), "加热能促进氯化铁水解", must=("氯化铁", "加热", "?"))
    add("cnk_h055_q3", caco3_acid(), "碳酸钙能溶于盐酸", must=("碳酸钙", "盐酸", "?"))
    add("cnk_h057_q2", burette_read(), "读取滴定管读数时应当", must=("滴定管", "俯视", "平视", "仰视", "?"))
    add("cnk_h058_q3", foam_mix(), "泡沫灭火器里用硫酸铝和碳酸氢钠", must=("硫酸铝", "碳酸氢钠", "泡沫", "?"))
    add("cnk_h059_q4", salt_bridge_cell(), "锌铜原电池用导线和盐桥连通后", must=("锌", "铜", "导线", "盐桥", "?"))
    add("cnk_h060_q3", electro_cucl2(), "用惰性电极电解氯化铜溶液", must=("电源", "氯化铜", "惰性", "?"))
    add("cnk_h061_q4", broken_plate(), "铁上的铜镀层一旦破裂", must=("铁", "铜", "潮湿", "?"))
    add("cnk_h063_q1", plate_setup(), "简单电镀实验中，待镀工件应当连接", must=("电源", "工件", "电镀", "?"))
    add("cnk_h064_q2", fuel_cell(), "氢氧燃料电池中，氢气所在的电极", must=("氢气", "氧气", "?"))

    add("cnk_h066_q1", shells_123(), "原子核外电子按能层排布时", must=("第一", "第二", "第三", "?"))
    add("cnk_h066_q4", sodium_shells(), "基态钠原子（原子序数 11）", must=("11", "?"))
    add("cnk_h069_q4", sigma_pi(), "σ 键和 π 键的差别", must=("σ", "π"))
    add("cnk_h070_q2", co2_linear(), "二氧化碳分子是直线形", must=("直线形", "C", "O", "?"))
    add("cnk_h070_q4", ammonia_pyramid(), "氨分子是三角锥形而不是平面三角形", must=("三角锥形", "N", "?"))
    add("cnk_h071_q4", water_methane(), "水的沸点明显高于相对分子质量相近的甲烷", must=("水", "甲烷", "?"))
    add("cnk_h073_q3", simple_cubic(), "简单立方晶胞有 8 个顶点", must=("8", "顶点", "?"))
    add("cnk_h074_q4", dryice_diamond(), "比较干冰和金刚石", must=("干冰", "金刚石"))
    add("cnk_h075_q3", ionic_states(), "离子晶体一般能在熔融或水溶液中导电", must=("固态", "熔融", "?"))
    add("cnk_h076_q3", cu_ammine(), "[Cu(NH3)4]2+ 中，氨分子的角色", must=("Cu", "NH3", "?"))

    add("cnk_h080_q4", ether_ethanol(), "乙醇和甲醚的分子式都是 C2H6O", must=("乙醇", "甲醚", ">2</text>", ">6</text>", "?"))
    add("cnk_h084_q2", ethylene_br(), "乙烯使溴的四氯化碳溶液褪色", must=("乙烯", "四氯化碳", "?"))
    add("cnk_h085_q2", benzene_ring(), "苯分子中六个碳碳键的关系是", must=("苯", "?"))
    add("cnk_h087_q3", bromoethane_cond(), "溴乙烷在氢氧化钠的醇溶液中加热", must=("溴乙烷", "氢氧化钠的醇溶液", "加热", "?"))
    add("cnk_h088_q3", ethanol_oxidize(), "乙醇在铜或银催化下加热", must=("乙醇", "氧气", "?"))
    add("cnk_h089_q2", aldehyde_test(), "乙醛与新制氢氧化铜悬浊液共热", must=("乙醛", "新制氢氧化铜", "?"))
    add("cnk_h090_q2", ester_scheme_s3(), "乙酸与乙醇在浓硫酸加热条件下生成乙酸乙酯", must=("乙酸", "乙醇", "乙酸乙酯", "?"))
    add("cnk_h093_q3", ester_receiver(), "用饱和碳酸钠溶液处理蒸出的乙酸乙酯", must=("乙酸乙酯", "饱和碳酸钠", "蒸出", "?"))
    add("cnk_h094_q2", silver_setup(), "银镜反应呈阳性", must=("银镜反应", "?"))
    add("cnk_h096_q3", peptide_four(), "4 个氨基酸分子缩合成一条肽链", must=("氨基酸", "4", "?"))
    add("cnk_h099_q2", glucose_test(), "葡萄糖与新制氢氧化铜悬浊液共热", must=("葡萄糖", "新制氢氧化铜", "?"))
    add("cnk_h100_q1", poly_ethylene(), "乙烯生成聚乙烯的反应类型是", must=("乙烯", "聚乙烯", "?"))
    add("cnk_h101_q4", rubber_vulcan(), "天然橡胶经过硫化后弹性更好", must=("硫化", "?"))
    return rows


def _index():
    out = {}
    for qid, drawing, expect, _extra, _must in catalog():
        out[qid] = (drawing, expect)
    return out


_BY_ID = _index()


def figure_for(q):
    """按题号取图。题干对不上就停，避免知识点重排后图贴错题。"""
    hit = _BY_ID.get(q.get("id"))
    if not hit:
        return None
    drawing, expect = hit
    if expect not in (q.get("prompt") or ""):
        raise SystemExit("配图题干对不上 %s，需要含「%s」" % (q.get("id"), expect))
    return drawing


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


def answer_text(q):
    if q.get("type") == "choice":
        for c in q.get("choices") or []:
            if isinstance(c, dict) and c.get("key") == q.get("answer"):
                return c.get("text") or ""
        return ""
    return str(q.get("answer") or "")


def leaks_answer(drawing, answer):
    if not answer:
        return False
    visible = "\n".join(svg_texts(drawing))
    if answer in visible:
        return True
    # 短数字答案不要去整段 SVG 的坐标里找，只看写出来的文字。
    if len(answer) >= 4 and answer in drawing:
        return True
    return False


def book_of(qid):
    n = int(qid[5:8])
    if n <= 19:
        return "必修一"
    if n <= 41:
        return "必修二"
    if n <= 64:
        return "选必一"
    if n <= 78:
        return "选必二"
    return "选必三"


def check_items(items, byid):
    problems = []
    seen = set()
    counts = {}
    first, second = None, None
    for qid, drawing, expect, extra, must in items:
        if qid in seen:
            problems.append("重复登记 " + qid)
        seen.add(qid)
        counts[book_of(qid)] = counts.get(book_of(qid), 0) + 1
        if first is None:
            first = drawing
        elif second is None and qid != items[0][0]:
            pass
        q = byid.get(qid)
        if not q:
            problems.append("找不到题目 " + qid)
            continue
        if not str(q.get("topicId", "")).startswith("cnk_h"):
            problems.append("%s 不是高中化学题" % qid)
        if expect not in (q.get("prompt") or ""):
            problems.append("%s 题干不含「%s」" % (qid, expect))
        problems += figure_problems(drawing, qid)
        problems += overflow_problems(drawing)
        if "currentColor" not in drawing:
            problems.append(qid + " 没有 currentColor")
        if NOTE not in drawing:
            problems.append(qid + " 缺少「" + NOTE + "」")
        blob = q.get("prompt", "") + " " + " ".join(
            c.get("text", "") for c in (q.get("choices") or []) if isinstance(c, dict))
        problems += number_problems(qid, drawing, blob, extra)
        if re.search(r"AI\s*初稿|免费", drawing):
            problems.append(qid + " 图里有不允许的文案")
        answer = answer_text(q)
        if leaks_answer(drawing, answer):
            problems.append("%s 的图里写出了正确答案「%s」" % (qid, answer))
        for phrase in must:
            if phrase not in drawing:
                problems.append("%s 的图缺少「%s」" % (qid, phrase))
    for name in ("必修一", "必修二", "选必一", "选必二", "选必三"):
        if counts.get(name, 0) < 1:
            problems.append(name + " 没有配图")
    again = catalog()
    if [row[1] for row in again] != [row[1] for row in items]:
        problems.append("同一目录连跑两次，SVG 不一致")
    return problems, counts


def write_preview(items, path, byid):
    parts = [
        "<!DOCTYPE html><meta charset=\"utf-8\"><title>高中化学图示预览</title>",
        "<style>body{margin:0;font-family:sans-serif;background:#fff;color:#162033}",
        ".row{display:flex;gap:12px;flex-wrap:wrap;padding:8px}",
        ".card{width:460px;padding:8px;box-sizing:border-box;border:1px solid #ddd}",
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
    problems, counts = check_items(items, byid)
    if problems:
        print("图示自检失败：")
        for p in problems:
            print("  " + p)
        return 1
    if len(sys.argv) >= 3 and sys.argv[1] == "--preview":
        write_preview(items, sys.argv[2], byid)
        return 0
    print("高中化学配图自检通过：%d 张" % len(items))
    for name in ("必修一", "必修二", "选必一", "选必二", "选必三"):
        print("  %s %d" % (name, counts.get(name, 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
