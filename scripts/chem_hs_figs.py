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
    arrow, ask, beaker, box, bubbles, ell, flame_at, flask, frame, lamp_at, liquid, liquid_tube,
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


def sub(x, y, s, size=10):
    """下标单独成一个小号 ASCII text，不用 Unicode 下标，也不用 tspan。"""
    return text(x, y, s, size, "start")


def rim_stick(a, b, ra, rb, order=1, sw=2.1):
    """键画到圆边为止，避免从圆心穿出半透明的球。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    a2 = (a[0] + ux * ra, a[1] + uy * ra)
    b2 = (b[0] - ux * rb, b[1] - uy * rb)
    return stick(a2, b2, order, sw)


def sun(cx, cy, r=12):
    body = circ(cx, cy, r, edge(1.5))
    for i in range(8):
        ang = math.radians(i * 45)
        body += line(
            (cx + (r + 3) * math.cos(ang), cy + (r + 3) * math.sin(ang)),
            (cx + (r + 11) * math.cos(ang), cy + (r + 11) * math.sin(ang)),
            thin(1.3),
        )
    return body


def gas_puff(x, y):
    body = path("M %g %g C %g %g %g %g %g %g" % (x, y, x + 16, y - 16, x + 28, y + 8, x + 46, y - 8), thin(1.4))
    body += path("M %g %g C %g %g %g %g %g %g" % (x + 6, y + 10, x + 22, y - 2, x + 34, y + 16, x + 52, y + 4), thin(1.3))
    return body


def energy_axes(w=520, h=330):
    """能量纵轴向上，进程横轴向右。返回 (body, 原点)。"""
    x0, y0 = 64, h - 78
    body = line((x0, y0), (w - 56, y0), edge(1.6))
    body += line((x0, y0), (x0, 46), edge(1.6))
    body += arrow((w - 70, y0), (w - 36, y0), 1.4)
    body += arrow((x0, 58), (x0, 36), 1.4)
    body += text(w - 100, y0 + 22, "进程", 13)
    body += text(x0 + 28, 40, "能量", 13, "start")
    return body, x0, y0


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


def cuo_to_cu():
    """两种固体填色不同，不写变化类型。"""
    w, h = 500, 280
    body = rect(70, 110, 70, 46, face(0.45), 4)
    body += rect(70, 110, 70, 46, edge(1.7), 4)
    body += text(105, 188, "氧化铜", 15)
    body += arrow((160, 132), (250, 132), 1.7)
    body += rect(270, 110, 70, 46, face(0.08), 4)
    body += rect(270, 110, 70, 46, edge(1.7), 4)
    body += text(305, 188, "铜", 15)
    body += ask(420, 132)
    return F(w, h, body, "两种固体")


def electron_in():
    """电子箭头指向粒子，化合价箭头向下。不写角色名称。"""
    w, h = 500, 300
    body = circ(78, 140, 22, edge(1.7))
    body += text(78, 146, "e-", 14)
    body += arrow((110, 140), (200, 140), 1.7)
    body += circ(250, 140, 34, edge(1.8))
    body += arrow((360, 78), (360, 196), 1.6)
    body += text(410, 146, "化合价", 15, "start")
    body += ask(250, 240)
    return F(w, h, body, "电子与化合价")


def acid_base_colors():
    """两只烧杯只画现象。不写离子名称。"""
    w, h = 540, 300
    body = beaker(36, 78, 160, 120)
    body += liquid(36, 78, 160, 120, 130)
    body += text(116, 150, "稀硫酸", 14)
    body += text(116, 112, "石蕊", 13)
    body += text(70, 230, "紫", 14)
    body += arrow((92, 224), (150, 224), 1.5)
    body += text(176, 230, "红", 14)
    body += beaker(300, 78, 180, 120)
    body += liquid(300, 78, 180, 120, 130)
    body += text(390, 128, "氢氧化钠", 14)
    body += text(390, 150, "酚酞", 13)
    body += arrow((340, 224), (410, 224), 1.5)
    body += text(436, 230, "红", 14)
    body += ask(270, 250)
    return F(w, h, body, "两种指示剂")


def sodium_burn():
    """只标淡黄色固体，不写产物名称。"""
    w, h = 520, 300
    body = path("M 70 168 Q 130 210 190 168", edge(1.8))
    body += line((70, 168), (190, 168), edge(1.8))
    body += rect(112, 148, 36, 16, face(0.3), 2)
    body += text(130, 108, "钠", 14)
    body += flame_at(130, 146, 1.15)
    body += text(250, 120, "空气", 14)
    body += arrow((210, 150), (290, 150), 1.7)
    body += path("M 310 168 Q 370 210 430 168", edge(1.8))
    body += line((310, 168), (430, 168), edge(1.8))
    body += rect(348, 150, 44, 16, face(0.16), 2)
    body += text(370, 230, "淡黄色", 14)
    body += ask(470, 120)
    return F(w, h, body, "钠在空气中")


def carbonate_heat():
    """两套加热装置相同，石灰水里都留问号。碳酸氢盐用化学式，不写中文名称。"""
    w, h = 560, 360

    def one(ox, formula):
        body = v_tube(ox + 28, 78, 40, 96)
        body += rect(ox + 38, 148, 20, 12, face(0.32), 2)
        body += rect(ox + 34, 66, 28, 14, edge(1.6), 2)
        body += line((ox + 48, 66), (ox + 48, 46), edge(1.6))
        body += line((ox + 48, 46), (ox + 138, 46), edge(1.6))
        # 导管伸到清石灰水液面以下，用来吸收并检验气体。
        body += line((ox + 138, 46), (ox + 138, 150), edge(1.6))
        body += beaker(ox + 98, 96, 80, 78)
        body += liquid(ox + 98, 96, 80, 78, 128)
        body += lamp_at(ox + 48, 250)
        body += text(ox + 138, 196, "澄清石灰水", 12)
        body += ask(ox + 210, 118, 10)
        body += formula
        return body

    left = text(36, 300, "Na", 14, "start")
    left += sub(54, 305, "2")
    left += text(60, 300, "CO", 14, "start")
    left += sub(80, 305, "3")
    right = text(300, 300, "NaHCO", 14, "start")
    right += sub(349, 305, "3")
    body = one(16, left) + one(286, right)
    return F(w, h, body, "加热对比")


def hcl_identify():
    """两支都滴稀盐酸。有气泡的那支不写溶液名称。"""
    w, h = 500, 310
    body = ""
    for i, lab in enumerate(("甲", "乙")):
        x = 70 + i * 210
        body += v_tube(x, 78, 52, 140)
        body += liquid_tube(x, 78, 52, 140, 130)
        body += line((x + 26, 48), (x + 26, 78), edge(1.5))
        body += poly([(x + 18, 72), (x + 34, 72), (x + 26, 86)], face(1))
        body += text(x - 6, 64, "稀盐酸", 13, "end")
        body += text(x + 26, 250, lab, 16)
        if i == 1:
            body += bubbles(x + 26, 150, 3)
        body += ask(x + 26, 110, 9)
    return F(w, h, body, "分别滴加")


def hclo_light():
    """见光后的去向用化学式，不写结论句。"""
    w, h = 520, 300
    body = beaker(40, 90, 150, 120)
    body += liquid(40, 90, 150, 120, 140)
    body += text(115, 160, "氯水", 14)
    body += text(115, 128, "HClO", 14)
    body += sun(250, 70, 12)
    body += text(250, 108, "光", 13)
    body += arrow((210, 150), (300, 150), 1.7)
    body += text(360, 130, "HCl", 16)
    body += text(430, 130, "O", 16, "start")
    body += sub(446, 135, "2")
    body += ask(400, 200)
    return F(w, h, body, "见光之后")


def dissolve_transfer():
    """三步只标短词，不写整句操作。"""
    w, h = 540, 300
    body = beaker(24, 80, 110, 100)
    body += liquid(24, 80, 110, 100, 120)
    body += rect(62, 130, 28, 14, face(0.3), 2)
    body += text(79, 214, "溶解", 14)
    body += text(79, 64, "烧杯", 13)
    body += arrow((146, 140), (186, 140), 1.5)
    body += beaker(196, 80, 110, 100)
    body += liquid(196, 80, 110, 100, 120)
    body += text(251, 214, "冷却", 14)
    body += arrow((318, 140), (358, 140), 1.5)
    # 容量瓶：细颈上的刻度与液面齐平。
    cx = 430
    body += line((cx - 12, 70), (cx - 12, 118), edge(1.7))
    body += line((cx + 12, 70), (cx + 12, 118), edge(1.7))
    body += line((cx - 12, 70), (cx + 12, 70), edge(1.7))
    body += line((cx - 12, 118), (cx - 40, 150), edge(1.7))
    body += line((cx + 12, 118), (cx + 40, 150), edge(1.7))
    body += line((cx - 40, 150), (cx - 40, 190), edge(1.7))
    body += line((cx + 40, 150), (cx + 40, 190), edge(1.7))
    body += line((cx - 40, 190), (cx + 40, 190), edge(1.7))
    body += line((cx - 16, 100), (cx + 16, 100), edge(2))
    # 溶液充到刻度线，凹液面最低处落在线上。
    body += path(
        "M %g 100 L %g 118 L %g 156 L %g 188 L %g 188 L %g 156 L %g 118 L %g 100 Z" % (
            cx - 8, cx - 10, cx - 34, cx - 34, cx + 34, cx + 34, cx + 10, cx + 8),
        face(0.1),
    )
    body += path("M %g 92 Q %g 108 %g 92" % (cx - 8, cx, cx + 8), thin(1.4))
    body += text(cx, 214, "定容", 14)
    body += text(cx, 58, "容量瓶", 13)
    body += ask(270, 250)
    return F(w, h, body, "固体配成溶液")


def atom_parts():
    """质子、中子、电子都标出，不把其中一项圈成答案。"""
    w, h = 500, 320
    cx, cy = 230, 168
    body = ""
    for rx, ry in ((40, 28), (72, 50), (108, 74)):
        body += ell(cx, cy, rx, ry, thin(1.5))
    body += circ(cx, cy, 22, face(0.12))
    body += circ(cx, cy, 22, edge(1.7))
    ex, ey = cx + 108, cy
    body += circ(ex, ey, 5, face(1))
    body += line((cx - 8, cy - 6), (78, 78), thin(1.2))
    body += text(70, 72, "质子", 14, "end")
    body += line((cx + 6, cy + 8), (78, 112), thin(1.2))
    body += text(70, 118, "中子", 14, "end")
    body += line((ex, ey), (400, 120), thin(1.2))
    body += text(408, 124, "电子", 14, "start")
    body += ask(400, 200)
    return F(w, h, body, "原子的组成")


def na_k_radius():
    """钾多一个电子层，半径更大。不写金属性强弱。"""
    w, h = 540, 320
    body = ""
    for rx, ry in ((22, 16), (42, 30), (64, 44)):
        body += ell(150, 150, rx, ry, thin(1.5))
    body += circ(150, 150, 5, face(1))
    body += text(150, 214, "半径", 12)
    body += line((86, 228), (214, 228), thin(1.3))
    body += text(150, 252, "钠", 16)
    for rx, ry in ((20, 14), (38, 26), (56, 38), (78, 52)):
        body += ell(390, 148, rx, ry, thin(1.5))
    body += circ(390, 148, 5, face(1))
    body += text(390, 222, "半径", 12)
    body += line((312, 236), (468, 236), thin(1.3))
    body += text(390, 260, "钾", 16)
    body += ask(270, 150)
    return F(w, h, body, "钠与钾")


def h2_share():
    """一对电子画在两个氢核之间。"""
    w, h = 480, 280
    body = circ(120, 130, 28, edge(1.7))
    body += circ(280, 130, 28, edge(1.7))
    body += text(120, 136, "H", 16)
    body += text(280, 136, "H", 16)
    body += line((148, 130), (252, 130), thin(1.4))
    body += circ(190, 124, 4, face(1))
    body += circ(214, 124, 4, face(1))
    body += text(202, 190, "电子对", 15)
    body += ask(380, 130)
    return F(w, h, body, "两个氢原子")


def na_mg_al_trend():
    """从钠到铝，核电荷增多、半径减小。不写金属性结论。"""
    w, h = 540, 360
    specs = ((100, 54, "+", "钠"), (250, 40, "++", "镁"), (400, 28, "+++", "铝"))
    body = ""
    for cx, r, mark, lab in specs:
        body += circ(cx, 130, r, thin(1.6))
        body += circ(cx, 130, 14, edge(1.5))
        body += text(cx, 135, mark, 12)
        body += text(cx, 200, lab, 16)
    body += arrow((70, 240), (470, 240), 1.5)
    body += text(270, 228, "核电荷", 13)
    body += arrow((470, 278), (70, 278), 1.5)
    body += text(270, 302, "半径", 13)
    body += ask(500, 168)
    return F(w, h, body, "同一周期")


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


def sulfur_burn():
    """硫在空气中燃烧。气态产物不写名称。"""
    w, h = 480, 300
    body = path("M 90 180 Q 160 230 230 180", edge(1.8))
    body += line((90, 180), (230, 180), edge(1.8))
    body += rect(140, 160, 40, 16, face(0.28), 2)
    body += text(160, 108, "硫", 14)
    body += flame_at(160, 158, 1.2)
    body += gas_puff(240, 120)
    body += text(330, 128, "空气", 14)
    body += ask(430, 168)
    return F(w, h, body, "硫在燃烧")


def so2_fuchsin():
    """品红褪色是题干里的现象。不写这种作用的名称。"""
    w, h = 500, 300
    body = text(70, 120, "二氧化硫", 15)
    body += line((70, 132), (70, 70), edge(1.6))
    body += line((70, 70), (230, 70), edge(1.6))
    body += line((230, 70), (230, 168), edge(1.6))
    body += beaker(160, 110, 150, 120)
    body += liquid(160, 110, 150, 120, 160)
    body += bubbles(230, 175, 3)
    body += text(370, 168, "褪色", 14)
    body += text(370, 198, "品红", 15)
    body += ask(450, 120)
    return F(w, h, body, "通入品红")


def open_sulfuric():
    """敞口试剂瓶放在台上，质量箭头向上。不写原因。"""
    w, h = 480, 320
    body = rect(150, 78, 100, 110, edge(1.8), 8)
    body += line((150, 78), (250, 78), edge(1.8))
    body += rect(268, 86, 40, 16, edge(1.5), 3)
    body += text(330, 100, "敞口", 14, "start")
    body += text(200, 140, "浓硫酸", 15)
    body += rect(130, 200, 140, 40, edge(1.8), 4)
    body += text(200, 226, "质量", 15)
    body += arrow((320, 190), (320, 120), 1.6)
    body += ask(400, 170)
    return F(w, h, body, "敞口放置")


def ammonia_litmus():
    """试纸由红变蓝。不写溶液酸碱性的名称。"""
    w, h = 480, 300
    body = beaker(70, 110, 170, 120)
    body += liquid(70, 110, 170, 120, 160)
    body += text(155, 190, "氨水", 15)
    body += rect(200, 78, 22, 110, edge(1.6), 2)
    body += text(268, 86, "红", 15, "start")
    body += arrow((300, 80), (348, 80), 1.5)
    body += text(360, 86, "蓝", 15, "start")
    body += text(300, 160, "石蕊试纸", 14, "start")
    body += ask(400, 210)
    return F(w, h, body, "试纸的颜色")


def nitric_brown():
    """棕色瓶挡住光线。不写完整说法。"""
    w, h = 480, 300
    body = rect(150, 90, 110, 130, edge(1.8), 8)
    for i in range(5):
        y = 110 + i * 18
        body += line((162, y), (248, y + 10), thin(1.1))
    body += rect(175, 74, 60, 16, edge(1.6), 3)
    body += text(278, 148, "浓硝酸", 14, "start")
    body += text(278, 174, "棕色瓶", 14, "start")
    body += sun(70, 80, 14)
    body += line((100, 100), (148, 130), thin(1.3))
    body += line((108, 86), (148, 110), thin(1.3))
    body += ask(400, 150)
    return F(w, h, body, "硝酸的保存")


def nitrogen_valence():
    """氨到一氧化氮再到硝酸，氮的化合价升高。不写角色名称。"""
    w, h = 540, 300
    body = text(50, 120, "N", 16, "start")
    body += text(63, 120, "H", 16, "start")
    body += sub(76, 125, "3")
    body += text(66, 170, "-3", 15)
    body += arrow((100, 114), (170, 114), 1.6)
    body += text(186, 120, "NO", 16, "start")
    body += text(198, 170, "+2", 15)
    body += arrow((236, 114), (306, 114), 1.6)
    body += text(322, 120, "H", 16, "start")
    body += text(335, 120, "N", 16, "start")
    body += text(348, 120, "O", 16, "start")
    body += sub(361, 125, "3")
    body += text(348, 170, "+5", 15)
    body += text(250, 220, "化合价", 14)
    body += arrow((300, 230), (360, 190), 1.5)
    body += ask(470, 160)
    return F(w, h, body, "氮的化合价")


def so2_co2_fuchsin():
    """两种气体都通入品红，两边都不写鉴别结论。"""
    w, h = 540, 300
    labels = ("二氧化硫", "二氧化碳")
    body = ""
    for i, lab in enumerate(labels):
        x = 40 + i * 260
        body += text(x + 70, 58, lab, 14)
        body += v_tube(x + 44, 88, 52, 130)
        body += liquid_tube(x + 44, 88, 52, 130, 140)
        # 导管伸到品红液面以下，气体才能鼓泡。
        body += line((x + 70, 68), (x + 70, 168), edge(1.5))
        body += bubbles(x + 70, 176, 2)
        body += text(x + 70, 250, "品红", 14)
        body += ask(x + 148, 150, 10)
    return F(w, h, body, "分别通入")


def sulfur_valence():
    """只标 0 和 +4，不把选项句子写出来。"""
    w, h = 500, 280
    body = circ(90, 120, 26, edge(1.8))
    body += text(90, 126, "S", 16)
    body += text(90, 180, "0", 16)
    body += text(90, 206, "硫", 14)
    body += arrow((140, 120), (230, 120), 1.7)
    body += text(280, 120, "S", 16, "start")
    body += text(291, 120, "O", 16, "start")
    body += sub(304, 125, "2")
    body += text(296, 180, "+4", 16)
    body += text(250, 220, "化合价", 14)
    body += ask(420, 130)
    return F(w, h, body, "硫的化合价")


def charcoal_exo():
    """生成物能级低于反应物。不写热效应的名称。"""
    w, h = 520, 330
    body, x0, y0 = energy_axes(w, h)
    # 反应物在上，过渡态略高，生成物落到更低处。
    body += path(
        "M 110 110 L 168 110 C 210 110 214 78 250 78 C 300 78 310 210 370 210 L 440 210",
        edge(2.1),
    )
    body += text(140, 86, "木炭", 14)
    body += text(410, 184, "生成物", 14)
    body += ask(250, 160)
    return F(w, h, body, "燃烧的能量")


def caco3_endo():
    """生成物能级高于反应物。不写热效应的名称。"""
    w, h = 520, 330
    body, x0, y0 = energy_axes(w, h)
    body += path(
        "M 110 210 L 168 210 C 210 210 220 70 268 70 C 320 70 330 120 380 120 L 440 120",
        edge(2.1),
    )
    body += text(130, 184, "碳酸钙", 14)
    body += text(420, 94, "生成物", 14)
    body += ask(250, 170)
    return F(w, h, body, "分解的能量")


def catalyst_speed():
    """有催化剂的曲线更早升高。不写快慢的结论词。"""
    w, h = 520, 320
    body = line((60, 240), (460, 240), edge(1.6))
    body += line((60, 240), (60, 50), edge(1.6))
    body += text(430, 262, "时间", 13)
    body += text(78, 46, "产物", 13, "start")
    body += path("M 90 220 C 180 216 240 200 420 150", hidden(1.8))
    body += path("M 90 220 C 140 210 180 120 420 80", edge(2.1))
    body += text(300, 168, "无催化剂", 13)
    body += text(250, 78, "有催化剂", 13)
    body += ask(140, 120)
    return F(w, h, body, "有无催化剂")


def heat_collision():
    """右边温度更高，运动箭头更长，有效碰撞更多。"""
    w, h = 540, 300
    body = rect(30, 70, 200, 160, edge(1.6), 6)
    body += text(130, 58, "低温", 14)
    body += circ(80, 130, 10, edge(1.4))
    body += circ(140, 150, 10, edge(1.4))
    body += arrow((92, 134), (118, 144), 1.3)
    body += circ(160, 110, 10, edge(1.4))
    body += rect(280, 70, 220, 160, edge(1.6), 6)
    body += text(390, 58, "高温", 14)
    spots = ((320, 120), (370, 150), (420, 110), (450, 160), (340, 180))
    for x, y in spots:
        body += circ(x, y, 10, edge(1.4))
    body += arrow((332, 120), (358, 140), 1.4)
    body += arrow((400, 116), (432, 148), 1.4)
    body += circ(345, 132, 4, face(1))
    body += circ(416, 136, 4, face(1))
    body += text(390, 210, "有效碰撞", 13)
    body += arrow((236, 150), (274, 150), 1.5)
    body += ask(250, 250)
    return F(w, h, body, "温度与碰撞")


def catalyst_equilibrium():
    """加催化剂后正逆箭头一起变长，组成条不变。"""
    w, h = 540, 320
    body = text(90, 70, "平衡", 14)
    body += arrow((40, 110), (140, 110), 1.5)
    body += arrow((140, 136), (40, 136), 1.5)
    body += text(90, 100, "正", 13)
    body += text(90, 162, "逆", 13)
    body += arrow((180, 120), (250, 120), 1.6)
    body += text(215, 108, "催化剂", 13)
    body += arrow((270, 96), (430, 96), 1.8)
    body += arrow((430, 150), (270, 150), 1.8)
    body += text(350, 84, "正", 13)
    body += text(350, 176, "逆", 13)
    body += rect(40, 210, 100, 22, face(0.12), 3)
    body += rect(40, 210, 100, 22, edge(1.4), 3)
    body += rect(300, 210, 100, 22, face(0.12), 3)
    body += rect(300, 210, 100, 22, edge(1.4), 3)
    body += text(90, 258, "组成", 13)
    body += text(350, 258, "组成", 13)
    body += ask(470, 120)
    return F(w, h, body, "平衡后再加入")


def closed_circuit():
    """电极伸进液面以下，导线经灯泡连成回路。不接电源。"""
    w, h = 520, 340
    body = beaker(150, 160, 230, 110)
    body += liquid(150, 160, 230, 110, 200)
    body += text(265, 230, "电解质", 14)
    body += rect(200, 110, 12, 120, edge(1.7), 2)
    body += rect(320, 110, 12, 120, edge(1.7), 2)
    body += text(206, 100, "电极", 13)
    body += text(326, 100, "电极", 13)
    body += line((206, 110), (206, 64), edge(1.6))
    body += line((326, 110), (326, 64), edge(1.6))
    # 导线接到灯泡边缘，回路是闭合的，不另接电源。
    body += line((206, 64), (257, 64), edge(1.6))
    body += line((283, 64), (326, 64), edge(1.6))
    body += bulb(270, 64)
    body += text(270, 46, "导线", 13)
    body += ask(90, 200)
    return F(w, h, body, "闭合回路")


def h2o2_mno2():
    """两份过氧化氢，只有右边加二氧化锰，气泡更多。"""
    w, h = 520, 320
    body = ""
    for i, extra in enumerate((None, "二氧化锰")):
        x = 70 + i * 230
        body += v_tube(x, 70, 64, 150)
        body += liquid_tube(x, 70, 64, 150, 130)
        body += text(x + 32, 250, "过氧化氢", 13)
        if extra:
            body += rect(x + 22, 168, 20, 12, face(0.4), 2)
            body += text(x + 32, 48, extra, 13)
            body += bubbles(x + 32, 140, 4)
        else:
            body += text(x + 32, 48, "不加", 13)
            body += bubbles(x + 32, 150, 1)
        body += ask(x + 32, 110, 9)
    return F(w, h, body, "两份对比")


def ethanol_ether_b2():
    """同一分子式的两种连接方式。下标是小号 ASCII。"""
    w, h = 540, 300
    body = text(214, 48, "C", 15, "start")
    body += sub(226, 53, "2")
    body += text(236, 48, "H", 15, "start")
    body += sub(248, 53, "6")
    body += text(258, 48, "O", 15, "start")
    body += dot(48, 140, "C", 15, 12)
    body += stick((63, 140), (98, 140))
    body += dot(113, 140, "C", 15, 12)
    body += stick((128, 140), (163, 140))
    body += dot(178, 140, "O", 15, 12)
    body += stick((193, 140), (220, 112))
    body += text(232, 108, "H", 12, "start")
    body += text(113, 198, "乙醇", 15)
    body += dot(320, 140, "C", 15, 12)
    body += stick((335, 140), (375, 140))
    body += dot(390, 140, "O", 15, 12)
    body += stick((405, 140), (445, 140))
    body += dot(460, 140, "C", 15, 12)
    body += text(390, 198, "甲醚", 15)
    body += ask(270, 240)
    return F(w, h, body, "两种连接")


def ethylene_bond():
    """两个碳之间画两根键。不写这根键的名称。"""
    w, h = 460, 280
    c1, c2 = (160, 130), (280, 130)
    h_pos = ((100, 78), (100, 182), (340, 78), (340, 182))
    body = rim_stick(c1, c2, 18, 18, 2)
    body += rim_stick(c1, h_pos[0], 18, 8)
    body += rim_stick(c1, h_pos[1], 18, 8)
    body += rim_stick(c2, h_pos[2], 18, 8)
    body += rim_stick(c2, h_pos[3], 18, 8)
    body += dot(*c1, "C", 18, 15)
    body += dot(*c2, "C", 18, 15)
    for hx, hy in h_pos:
        body += text(hx, hy, "H", 14)
    body += text(220, 210, "乙烯", 15)
    body += ask(400, 130)
    return F(w, h, body, "乙烯分子")


def ethylene_chain():
    """双键打开后连成一条链。不写反应类型。"""
    w, h = 540, 280
    body = dot(46, 120, "C", 14, 12)
    body += dot(100, 120, "C", 14, 12)
    body += stick((60, 120), (86, 120), 2)
    body += text(73, 168, "乙烯", 13)
    body += arrow((130, 120), (190, 120), 1.6)
    xs = (230, 280, 330, 380, 430)
    for i in range(len(xs) - 1):
        body += stick((xs[i] + 12, 120), (xs[i + 1] - 12, 120))
    for x in xs:
        body += dot(x, 120, "C", 13, 11)
    body += path("M 214 100 L 206 100 L 206 140 L 214 140", edge(1.4))
    body += path("M 446 100 L 454 100 L 454 140 L 446 140", edge(1.4))
    body += text(466, 96, "n", 14, "start")
    body += text(330, 180, "聚乙烯", 14)
    body += ask(490, 180)
    return F(w, h, body, "连成长链")


def ethanol_oh():
    """标出 OH 的位置并加问号。不写官能团的中文名。"""
    w, h = 500, 280
    # 圈先画，氧和氢都落在圈内，不把左边的碳包进去。
    body = circ(252, 122, 50, edge(1.5))
    body += dot(70, 140, "C", 16, 13)
    body += stick((86, 140), (130, 140))
    body += dot(146, 140, "C", 16, 13)
    body += stick((162, 140), (210, 140))
    body += dot(226, 140, "O", 16, 13)
    body += stick((242, 140), (272, 106))
    body += text(276, 104, "H", 14, "start")
    body += text(252, 50, "OH", 14)
    body += ask(430, 70)
    body += text(108, 210, "乙醇", 15)
    return F(w, h, body, "乙醇分子")


def ethanol_to_unknown():
    """催化剂和加热写在箭头上，产物只留问号。"""
    w, h = 520, 280
    body = box(30, 110, 90, 48, "乙醇")
    body += arrow((132, 134), (300, 134), 1.7)
    body += text(210, 112, "铜或银", 14)
    body += text(210, 160, "加热", 14)
    body += text(210, 182, "氧气", 13)
    body += box(312, 110, 80, 48, "?")
    body += ask(450, 134)
    return F(w, h, body, "催化氧化")


def glucose_brick():
    """加热后管底有沉淀。不写官能团名称。"""
    w, h = 480, 360
    body = v_tube(180, 64, 64, 150)
    body += liquid_tube(180, 64, 64, 150, 120)
    body += rect(198, 158, 28, 14, face(0.4), 2)
    body += text(150, 150, "葡萄糖", 14, "end")
    body += text(268, 110, "新制氢氧化铜", 13, "start")
    body += text(300, 200, "砖红色沉淀", 13, "start")
    body += lamp_at(212, 292)
    body += ask(70, 160)
    return F(w, h, body, "加热后的试管")


def methane_space():
    """四根键伸向不同方向，其中一根用虚线。不写形状名称。"""
    w, h = 480, 320
    c = (230, 150)
    top = (230, 70)
    left = (130, 210)
    right = (340, 200)
    back = (160, 96)
    body = rim_stick(c, top, 16, 14)
    body += rim_stick(c, left, 16, 14)
    body += rim_stick(c, right, 16, 14)
    dx, dy = back[0] - c[0], back[1] - c[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    body += line((c[0] + ux * 16, c[1] + uy * 16), (back[0] - ux * 14, back[1] - uy * 14), hidden(1.6))
    body += dot(*c, "C", 16, 13)
    body += dot(*top, "H", 14, 12)
    body += dot(*left, "H", 14, 12)
    body += dot(*right, "H", 14, 12)
    body += dot(*back, "H", 14, 12)
    body += text(230, 260, "甲烷", 15)
    body += ask(420, 80)
    return F(w, h, body, "甲烷模型")


def ethylene_model():
    """两个碳球之间用两根棍连接。"""
    w, h = 500, 300
    c1, c2 = (170, 140), (320, 140)
    body = rim_stick(c1, c2, 20, 20, 2, 2.4)
    body += rim_stick(c1, (90, 70), 20, 14)
    body += rim_stick(c1, (90, 210), 20, 14)
    body += rim_stick(c2, (400, 70), 20, 14)
    body += rim_stick(c2, (400, 210), 20, 14)
    body += dot(*c1, "C", 20, 15)
    body += dot(*c2, "C", 20, 15)
    body += dot(90, 70, "H", 14, 12)
    body += dot(90, 210, "H", 14, 12)
    body += dot(400, 70, "H", 14, 12)
    body += dot(400, 210, "H", 14, 12)
    body += text(245, 250, "乙烯", 15)
    body += ask(455, 150)
    return F(w, h, body, "球棍模型")


def sodium_ethanol():
    """钠进入乙醇，用气泡表示有气体，不写现象的句子。"""
    w, h = 460, 310
    body = beaker(140, 120, 180, 130)
    body += liquid(140, 120, 180, 130, 170)
    body += text(230, 200, "乙醇", 15)
    body += rect(210, 78, 30, 14, edge(1.7), 2)
    body += text(225, 68, "钠", 14)
    body += arrow((225, 96), (225, 140), 1.5)
    body += bubbles(210, 175, 3)
    body += ask(80, 170)
    return F(w, h, body, "钠与乙醇")


def acetic_carbonate():
    """乙酸加到碳酸钠里并冒泡。不写酸性比较的句子。"""
    w, h = 480, 310
    body = v_tube(180, 70, 64, 150)
    body += liquid_tube(180, 70, 64, 150, 140)
    body += rect(198, 158, 28, 16, face(0.28), 2)
    body += text(212, 250, "碳酸钠", 14)
    body += line((212, 48), (212, 70), edge(1.5))
    body += poly([(202, 64), (222, 64), (212, 78)], face(1))
    body += text(268, 100, "乙酸", 14, "start")
    body += bubbles(212, 130, 3)
    body += ask(80, 160)
    return F(w, h, body, "乙酸滴入")


def ester_setup_b2():
    """圆底烧瓶加热。导管口停在接收液液面上方，避免画成伸进液面。"""
    w, h = 540, 400
    body = flask(130, 86, 100, 78)
    body += text(28, 128, "乙醇", 14, "start")
    body += text(28, 152, "乙酸", 14, "start")
    body += text(28, 176, "浓硫酸", 14, "start")
    body += lamp_at(130, 292)
    body += text(130, 322, "加热", 14)
    # 瓶口引出，接收试管敞口，管口高于液面。
    body += line((130, 86), (130, 52), edge(1.7))
    body += line((130, 52), (400, 52), edge(1.7))
    body += line((400, 52), (400, 168), edge(1.7))
    body += v_tube(368, 140, 64, 140)
    body += liquid_tube(368, 140, 64, 140, 210)
    body += text(400, 310, "接收液", 14)
    body += ask(450, 188)
    return F(w, h, body, "酯化装置")


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


def delta_h_negative():
    """生成物能级低于反应物。不写热效应的名称。"""
    w, h = 520, 330
    body, _x0, _y0 = energy_axes(w, h)
    body += path(
        "M 110 108 L 168 108 C 210 108 220 74 262 74 C 314 74 328 198 386 198 L 448 198",
        edge(2.1),
    )
    body += text(132, 92, "反应物", 14)
    body += text(424, 182, "生成物", 14)
    body += line((468, 108), (468, 198), thin(1.3))
    body += line((460, 108), (476, 108), thin(1.3))
    body += line((460, 198), (476, 198), thin(1.3))
    body += text(168, 176, "焓变小于 0", 14)
    body += ask(320, 228)
    return F(w, h, body, "焓变与能级")


def temp_rate_curve():
    """横轴温度升高时，速率曲线走高。不写快慢结论词。"""
    w, h = 520, 320
    body = line((70, 236), (440, 236), edge(1.6))
    body += line((70, 236), (70, 58), edge(1.6))
    body += arrow((420, 236), (468, 236), 1.4)
    body += arrow((70, 72), (70, 42), 1.4)
    body += text(400, 260, "温度", 14)
    body += text(86, 50, "速率", 14, "start")
    body += path("M 104 206 C 180 198 250 150 410 78", edge(2.2))
    body += ask(168, 110)
    return F(w, h, body, "温度与速率")


def catalyst_barrier():
    """两条曲线起止能级相同，有催化剂的峰更低。不写速率结论。"""
    w, h = 540, 340
    body, _x0, _y0 = energy_axes(w, h)
    body += path(
        "M 110 200 L 158 200 C 198 200 214 76 268 76 C 328 76 342 150 392 150 L 458 150",
        edge(2.2),
    )
    body += path(
        "M 110 200 L 158 200 C 206 200 228 126 268 126 C 318 126 342 150 392 150 L 458 150",
        hidden(1.8),
    )
    body += text(128, 184, "反应物", 13)
    body += text(430, 134, "生成物", 13)
    body += text(360, 66, "无催化剂", 13)
    body += text(348, 114, "有催化剂", 12)
    body += line((268, 76), (268, 200), thin(1.2))
    body += text(150, 96, "活化能", 13)
    body += ask(470, 214)
    return F(w, h, body, "活化能")


def catalyst_plateau():
    """有催化剂更早拐平，两条曲线停在同一高度。不写平衡结论句。"""
    w, h = 520, 330
    body = line((64, 248), (440, 248), edge(1.6))
    body += line((64, 248), (64, 54), edge(1.6))
    body += arrow((420, 248), (468, 248), 1.4)
    body += arrow((64, 68), (64, 40), 1.4)
    body += text(400, 272, "时间", 14)
    body += text(80, 48, "浓度", 14, "start")
    body += path("M 96 214 C 128 206 156 108 196 96 L 430 96", edge(2.2))
    body += path("M 96 214 C 190 210 270 150 338 96 L 430 96", hidden(1.8))
    body += text(250, 80, "有催化剂", 13)
    body += text(230, 196, "无催化剂", 13)
    body += ask(380, 176)
    return F(w, h, body, "同一高度")


def quadrant_signs():
    """四个象限只标焓变和熵变的符号，不圈出结论。"""
    w, h = 540, 360
    cx, cy = 250, 176
    body = line((64, cy), (470, cy), edge(1.6))
    body += line((cx, 300), (cx, 58), edge(1.6))
    body += arrow((450, cy), (500, cy), 1.4)
    body += arrow((cx, 70), (cx, 42), 1.4)
    body += text(214, 66, "焓变", 13, "end")
    body += text(455, cy + 20, "熵变", 13)
    pairs = (
        (145, 108, "焓变大于 0", "熵变小于 0"),
        (365, 108, "焓变大于 0", "熵变大于 0"),
        (145, 214, "焓变小于 0", "熵变小于 0"),
        (365, 214, "焓变小于 0", "熵变大于 0"),
    )
    for x, y, a, b in pairs:
        body += text(x, y, a, 13)
        body += text(x, y + 20, b, 13)
    body += ask(508, 300)
    return F(w, h, body, "四个象限")


def tds_bars():
    """吸热且气体粒子变多；高温一侧熵变项更长。不写原因句。"""
    w, h = 540, 340
    body = rect(36, 64, 160, 108, edge(1.6), 6)
    body += text(116, 52, "反应物", 14)
    body += circ(78, 108, 10, edge(1.5))
    body += circ(128, 124, 10, edge(1.5))
    body += arrow((206, 116), (258, 116), 1.6)
    body += text(232, 102, "吸热", 13)
    body += rect(268, 64, 200, 108, edge(1.6), 6)
    body += text(368, 52, "生成物", 14)
    for x, y in ((300, 100), (342, 112), (386, 98), (420, 128), (348, 140)):
        body += circ(x, y, 8, edge(1.4))
    body += text(116, 190, "气体", 13)
    body += text(368, 190, "气体", 13)
    body += text(100, 214, "低温", 14)
    body += text(230, 214, "高温", 14)
    body += rect(70, 258, 64, 34, face(0.12), 2)
    body += rect(70, 258, 64, 34, edge(1.4), 2)
    body += rect(198, 232, 64, 60, face(0.28), 2)
    body += rect(198, 232, 64, 60, edge(1.4), 2)
    body += text(300, 268, "T·熵变", 14, "start")
    body += ask(460, 262)
    return F(w, h, body, "温度与熵变项")


def conc_disturb():
    """平衡后反应物浓度跳升，生成物曲线随后抬高。不写移动方向。"""
    w, h = 540, 340
    body = line((58, 250), (460, 250), edge(1.6))
    body += line((58, 250), (58, 50), edge(1.6))
    body += arrow((440, 250), (488, 250), 1.4)
    body += arrow((58, 64), (58, 38), 1.4)
    body += text(420, 274, "时间", 14)
    body += text(74, 46, "浓度", 14, "start")
    body += path("M 92 78 C 140 128 184 158 236 166 L 252 166", edge(2.1))
    body += line((252, 166), (252, 96), edge(2.1))
    body += path("M 252 96 C 310 112 370 132 456 140", edge(2.1))
    body += path("M 92 220 C 146 190 190 172 252 164", hidden(1.8))
    body += path("M 252 164 C 320 142 380 116 456 106", hidden(1.8))
    body += line((252, 70), (252, 236), hidden(1.2))
    body += text(268, 84, "增大", 13, "start")
    body += text(118, 66, "反应物", 13)
    body += text(130, 236, "生成物", 13)
    body += ask(400, 196)
    return F(w, h, body, "浓度再变化")


def heat_color():
    """升温后右管颜色更深，并标出题目给出的吸热条件。不写移动结论。"""
    w, h = 540, 320
    body = v_tube(56, 72, 72, 150)
    body += liquid_tube(56, 72, 72, 150, 130)
    body += text(92, 252, "升温前", 14)
    body += arrow((148, 146), (214, 146), 1.6)
    body += text(181, 130, "升温", 13)
    body += path("M 232 118 L 232 186 A 34 34 0 0 1 300 186 L 300 118 Z", face(0.4))
    body += v_tube(230, 72, 72, 150)
    body += text(266, 252, "生成物", 14)
    body += text(360, 118, "已知", 14, "start")
    body += text(360, 142, "正反应", 14, "start")
    body += text(360, 166, "吸热", 14, "start")
    body += ask(430, 220)
    return F(w, h, body, "升温后的颜色")


def acetate_add():
    """醋酸的电离平衡旁加入醋酸钠。不写移动方向。"""
    w, h = 540, 300
    body = box(28, 108, 100, 50, "醋酸")
    body += arrow((140, 122), (206, 122), 1.5)
    body += arrow((206, 146), (140, 146), 1.5)
    body += box(216, 86, 118, 46, "醋酸根")
    body += text(360, 114, "+", 16)
    body += text(392, 114, "H+", 16, "start")
    body += rect(248, 186, 40, 20, face(0.28), 2)
    body += rect(248, 186, 40, 20, edge(1.5), 2)
    body += text(268, 230, "醋酸钠", 14)
    body += arrow((268, 182), (268, 140), 1.4)
    body += ask(470, 170)
    return F(w, h, body, "加入醋酸钠")


def acetic_dilution():
    """加水后液面升高、微粒更分散。不写选项句。"""
    w, h = 540, 330
    body = beaker(36, 72, 160, 150)
    body += liquid(36, 72, 160, 150, 150)
    body += text(116, 60, "醋酸", 14)
    for x, y in ((70, 172), (104, 186), (138, 168), (86, 204), (150, 198)):
        body += circ(x, y, 7, edge(1.4))
    body += circ(118, 176, 4, face(0.55))
    body += arrow((214, 156), (286, 156), 1.5)
    body += text(250, 140, "加水", 14)
    body += beaker(300, 72, 190, 150)
    body += liquid(300, 72, 190, 150, 108)
    body += text(395, 60, "醋酸", 14)
    for x, y in ((340, 140), (430, 176), (470, 150)):
        body += circ(x, y, 7, edge(1.4))
    body += circ(380, 200, 4, face(0.55))
    body += circ(450, 210, 4, face(0.55))
    body += ask(270, 250)
    return F(w, h, body, "加水之后")


def acid_kw():
    """纯水中两条柱等高；加酸后氢离子柱更高、氢氧根柱更矮。不写选项句。"""
    w, h = 540, 330
    body = text(130, 52, "纯水", 15)
    body += rect(70, 148, 36, 82, face(0.12), 3)
    body += rect(70, 148, 36, 82, edge(1.4), 3)
    body += rect(150, 148, 40, 82, face(0.12), 3)
    body += rect(150, 148, 40, 82, edge(1.4), 3)
    body += text(88, 252, "H+", 14)
    body += text(170, 252, "OH-", 14)
    body += text(390, 52, "强酸", 15)
    body += rect(330, 96, 36, 134, face(0.3), 3)
    body += rect(330, 96, 36, 134, edge(1.4), 3)
    body += rect(420, 186, 40, 44, face(0.12), 3)
    body += rect(420, 186, 40, 44, edge(1.4), 3)
    body += text(348, 252, "H+", 14)
    body += text(440, 252, "OH-", 14)
    body += text(130, 286, "离子积", 13)
    body += text(390, 286, "离子积", 13)
    body += ask(260, 160)
    return F(w, h, body, "纯水与强酸")


def ammonium_ions():
    """铵根与水可逆地给出 H+。氯离子留在溶液里。不写结论句。"""
    w, h = 540, 310
    body = text(24, 108, "铵根", 15, "start")
    body += text(78, 108, "+", 15, "start")
    body += text(96, 108, "水", 15, "start")
    body += arrow((140, 100), (198, 100), 1.4)
    body += arrow((198, 120), (140, 120), 1.4)
    body += text(210, 96, "H+", 15, "start")
    body += text(210, 122, "一水合氨", 13, "start")
    body += beaker(340, 78, 160, 140)
    body += liquid(340, 78, 160, 140, 120)
    body += text(420, 66, "氯化铵", 14)
    body += text(390, 165, "铵根", 13)
    body += text(470, 200, "氯离子", 13)
    body += ask(300, 210)
    return F(w, h, body, "氯化铵溶液")


def acetate_hydro():
    """醋酸根与水可逆地给出 OH-。不写酸碱性名称。"""
    w, h = 540, 310
    body = text(20, 112, "醋酸根", 15, "start")
    body += text(80, 112, "+", 15, "start")
    body += text(98, 112, "水", 15, "start")
    body += arrow((138, 104), (196, 104), 1.4)
    body += arrow((196, 124), (138, 124), 1.4)
    body += text(208, 100, "醋酸", 15, "start")
    body += text(208, 128, "OH-", 15, "start")
    body += ask(250, 188)
    body += beaker(330, 78, 175, 140)
    body += liquid(330, 78, 175, 140, 120)
    body += text(418, 66, "醋酸钠", 14)
    body += text(385, 168, "钠离子", 13)
    body += text(470, 200, "醋酸根", 13)
    return F(w, h, body, "醋酸钠溶液")


def common_ion_add():
    """难溶盐与离子并存，可溶盐把相同离子送入。不写沉淀增减。"""
    w, h = 540, 320
    body = beaker(36, 70, 210, 160)
    body += liquid(36, 70, 210, 160, 120)
    body += rect(100, 178, 76, 20, face(0.3), 2)
    body += rect(100, 178, 76, 20, edge(1.5), 2)
    body += text(96, 158, "阳离子", 12)
    body += text(196, 158, "阴离子", 12)
    body += text(141, 262, "难溶盐", 14)
    body += box(330, 78, 130, 46, "可溶盐", size=15)
    body += text(395, 150, "相同离子", 13)
    body += arrow((360, 128), (230, 158), 1.5)
    body += ask(470, 220)
    return F(w, h, body, "再加入盐")


def silver_chloride_hcl():
    """氯化银与离子共存，滴管加入浓盐酸。不写原因句。"""
    w, h = 520, 330
    body = beaker(130, 90, 210, 155)
    body += liquid(130, 90, 210, 155, 140)
    body += rect(190, 196, 78, 18, face(0.28), 2)
    body += rect(190, 196, 78, 18, edge(1.5), 2)
    body += text(175, 175, "银离子", 13)
    body += text(270, 168, "氯离子", 13)
    body += text(229, 278, "氯化银", 14)
    body += line((300, 36), (300, 68), edge(1.6))
    body += line((324, 36), (324, 68), edge(1.6))
    body += line((292, 36), (332, 36), edge(1.6))
    body += poly([(300, 68), (324, 68), (312, 82)], face(1))
    body += circ(312, 98, 4, edge(1.4))
    body += text(340, 56, "浓盐酸", 14, "start")
    body += ask(70, 180)
    return F(w, h, body, "滴入盐酸")


def near_endpoint():
    """滴定管尖端只有一滴，锥形瓶旁有转动弧线。不写操作句。"""
    w, h = 500, 420
    body = line((148, 48), (148, 148), edge(1.8))
    body += line((176, 48), (176, 148), edge(1.8))
    body += rect(140, 128, 44, 12, edge(1.4), 2)
    body += line((148, 148), (162, 166), edge(1.6))
    body += line((176, 148), (162, 166), edge(1.6))
    body += circ(162, 182, 5, edge(1.5))
    body += text(196, 78, "滴定管", 14, "start")
    body += text(196, 102, "标准溶液", 13, "start")
    cx, top = 170, 206
    body += line((cx - 22, top), (cx + 22, top), edge(1.8))
    body += line((cx - 22, top), (cx - 22, top + 28), edge(1.8))
    body += line((cx + 22, top), (cx + 22, top + 28), edge(1.8))
    body += line((cx - 22, top + 28), (cx - 78, top + 120), edge(1.8))
    body += line((cx + 22, top + 28), (cx + 78, top + 120), edge(1.8))
    body += line((cx - 78, top + 120), (cx + 78, top + 120), edge(1.8))
    body += path(
        "M %g %g L %g %g L %g %g L %g %g Z" % (
            cx - 50, top + 78, cx + 50, top + 78, cx + 70, top + 114, cx - 70, top + 114),
        face(0.1),
    )
    body += text(cx, top + 148, "锥形瓶", 14)
    body += path("M 300 340 C 360 330 372 270 328 248", edge(1.6))
    body += arrow((344, 262), (326, 250), 1.4)
    body += ask(70, 250)
    return F(w, h, body, "接近终点")


def ferric_colloid():
    """氯化铁液滴落入正在加热、起泡的水中。不写操作整句。"""
    w, h = 480, 420
    body = beaker(150, 118, 180, 145)
    body += liquid(150, 118, 180, 145, 168)
    body += bubbles(230, 200, 3)
    body += line((214, 48), (214, 96), edge(1.6))
    body += line((238, 48), (238, 96), edge(1.6))
    body += line((206, 48), (246, 48), edge(1.6))
    body += poly([(214, 96), (238, 96), (226, 112)], face(1))
    body += circ(226, 128, 4, edge(1.4))
    body += circ(230, 148, 3.5, edge(1.3))
    body += text(260, 72, "氯化铁", 14, "start")
    body += lamp_at(240, 352)
    body += text(120, 330, "加热", 14, "start")
    body += ask(70, 180)
    return F(w, h, body, "滴入热水")


def positive_electrode():
    """电源正极连到右侧电极，该处只留问号。不写电极专名。"""
    w, h = 520, 340
    body = rect(186, 48, 120, 42, edge(1.8), 4)
    body += text(246, 38, "电源", 13)
    body += text(214, 76, "−", 18)
    body += text(278, 76, "+", 18)
    body += line((214, 90), (120, 90), edge(1.6))
    body += line((120, 90), (120, 148), edge(1.6))
    body += line((278, 90), (392, 90), edge(1.6))
    body += line((392, 90), (392, 148), edge(1.6))
    body += beaker(70, 150, 370, 120)
    body += liquid(70, 150, 370, 120, 190)
    body += rect(112, 126, 16, 104, edge(1.8), 2)
    body += rect(384, 126, 16, 104, edge(1.8), 2)
    body += ask(392, 114)
    return F(w, h, body, "电源与电极")


def moist_iron():
    """铁条上有水滴，旁边是空气。不把选项连成一句。"""
    w, h = 520, 300
    body = rect(70, 156, 280, 28, face(0.08), 3)
    body += rect(70, 156, 280, 28, edge(1.8), 3)
    body += text(210, 176, "铁", 16)
    body += circ(130, 144, 8, edge(1.4))
    body += circ(190, 140, 7, edge(1.4))
    body += circ(260, 144, 8, edge(1.4))
    body += text(130, 122, "水", 14)
    body += gas_puff(360, 130)
    body += text(430, 108, "空气", 14, "start")
    body += ask(430, 190)
    return F(w, h, body, "铁与潮湿空气")


def zinc_on_iron():
    """锌块与铁相连，只有锌一侧落下微粒。不写保护方法的名称。"""
    w, h = 540, 300
    body = rect(180, 142, 250, 32, face(0.06), 3)
    body += rect(180, 142, 250, 32, edge(1.8), 3)
    body += text(320, 164, "铁", 16)
    body += rect(70, 126, 78, 48, edge(1.8), 3)
    body += text(109, 156, "锌", 16)
    body += line((148, 150), (180, 150), edge(1.6))
    body += arrow((150, 112), (230, 112), 1.3)
    body += text(190, 100, "e-", 13)
    body += circ(92, 190, 4, edge(1.3))
    body += circ(112, 202, 3.5, edge(1.3))
    body += circ(100, 214, 3, edge(1.3))
    body += text(104, 238, "水", 13)
    body += ask(470, 158)
    return F(w, h, body, "锌与铁相连")


def zn_cu_modes():
    """左为原电池，电子由锌流向铜。右把铜接到电源正极。不写反应类型。"""
    w, h = 560, 370
    body = text(145, 46, "原电池", 14)
    body += beaker(36, 168, 220, 112)
    body += liquid(36, 168, 220, 112, 208)
    body += rect(86, 116, 12, 122, edge(1.7), 2)
    body += rect(186, 116, 12, 122, edge(1.7), 2)
    body += text(92, 106, "锌", 14)
    body += text(192, 106, "铜", 14)
    body += line((92, 116), (92, 76), edge(1.6))
    body += arrow((92, 76), (192, 76), 1.4)
    body += line((192, 76), (192, 116), edge(1.6))
    body += text(142, 66, "e-", 13)
    body += rect(360, 58, 150, 40, edge(1.7), 4)
    body += text(435, 46, "电源", 14)
    body += text(396, 84, "−", 16)
    body += text(474, 84, "+", 16)
    body += beaker(310, 168, 220, 112)
    body += liquid(310, 168, 220, 112, 208)
    body += rect(360, 116, 12, 122, edge(1.7), 2)
    body += rect(470, 116, 12, 122, edge(1.7), 2)
    body += text(366, 106, "锌", 14)
    body += text(476, 106, "铜", 14)
    body += line((366, 116), (366, 98), edge(1.6))
    body += line((366, 98), (396, 98), edge(1.6))
    body += line((476, 116), (476, 98), edge(1.6))
    body += line((476, 98), (474, 98), edge(1.6))
    body += ask(512, 150)
    return F(w, h, body, "两种接法")


def plating_anode():
    """铜片接电源正极，铜离子离开铜片进入溶液。工件接负极。不写作用句。"""
    w, h = 540, 360
    body = rect(170, 46, 180, 44, edge(1.8), 4)
    body += text(260, 36, "电源", 13)
    body += text(210, 74, "+", 18)
    body += text(310, 74, "−", 18)
    body += line((210, 90), (130, 90), edge(1.6))
    body += line((130, 90), (130, 146), edge(1.6))
    body += line((310, 90), (360, 90), edge(1.6))
    body += line((360, 90), (360, 146), edge(1.6))
    body += beaker(60, 148, 370, 130)
    body += liquid(60, 148, 370, 130, 188)
    body += rect(122, 124, 16, 112, edge(1.8), 2)
    body += rect(352, 124, 16, 112, edge(1.8), 2)
    body += text(130, 114, "铜", 14)
    body += text(360, 114, "工件", 14)
    body += arrow((146, 214), (176, 214), 1.3)
    body += circ(190, 206, 5, edge(1.3))
    body += circ(214, 228, 4, edge(1.3))
    body += circ(196, 246, 4, edge(1.3))
    body += text(230, 214, "铜离子", 13, "start")
    body += rect(344, 176, 8, 52, face(0.35), 1)
    body += ask(470, 210)
    return F(w, h, body, "镀铜")


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


def _gap_line(a, b, ra, rb, attrs):
    """从两个圆的边缘连线，避免线段穿过球心。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    p = (a[0] + ux * ra, a[1] + uy * ra)
    q = (b[0] - ux * rb, b[1] - uy * rb)
    return line(p, q, attrs)


def _on_ring(cx, cy, r, count, phase, rad=3.2):
    body = ""
    for i in range(count):
        ang = phase + (2 * math.pi * i / float(count))
        body += circ(cx + r * math.cos(ang), cy + r * math.sin(ang), rad, face(1))
    return body


def _beaker_liquid(x, y, w, h, level, op):
    bot = y + h - 2
    pts = [
        (x + 4, level),
        (x + 4, bot - 8),
        (x + w / 2.0, bot + 6),
        (x + w - 4, bot - 8),
        (x + w - 4, level),
    ]
    return poly(pts, face(op)) + line((x + 4, level), (x + w - 4, level), thin(1.3))


def sublevel_order():
    """同一能层 ns、np、nd、nf 由低到高。不把选项顺序写成一句话。"""
    w, h = 480, 320
    body = line((72, 248), (72, 58), edge(1.6))
    body += arrow((72, 70), (72, 40), 1.4)
    body += text(96, 50, "能量", 14, "start")
    for y, lab in ((228, "ns"), (184, "np"), (140, "nd"), (96, "nf")):
        body += line((118, y), (292, y), edge(2.1))
        body += text(312, y + 5, lab, 16, "start")
    body += text(205, 276, "同一能层", 14)
    body += ask(430, 168)
    return F(w, h, body, "能级高低")


def first_ie():
    """气态基态原子失去一个电子，同时标出能量。不写定义全文。"""
    w, h = 520, 320
    cx, cy = 176, 156
    body = ""
    for r in (30, 58, 88):
        body += circ(cx, cy, r, thin(1.5))
    body += circ(cx, cy, 7, face(0.5))
    body += circ(cx + 88, cy, 4.5, face(1))
    body += arrow((cx + 100, cy), (cx + 168, cy), 1.6)
    body += text(cx + 132, cy - 16, "e-", 15)
    body += text(cx + 132, cy + 28, "第一", 13)
    body += text(28, 64, "气态", 14, "start")
    body += text(28, 86, "基态", 14, "start")
    body += text(28, 108, "原子", 14, "start")
    body += arrow((46, 230), (108, 188), 1.5)
    body += text(28, 254, "能量", 14, "start")
    body += circ(438, 156, 32, edge(1.7))
    body += text(438, 162, "+", 18)
    body += ask(438, 78)
    return F(w, h, body, "失去电子")


def ie_period_trend():
    """同周期总趋势画成上升曲线。不写增大或减小。"""
    w, h = 520, 330
    body = line((64, 228), (430, 228), edge(1.6))
    body += line((64, 228), (64, 52), edge(1.6))
    body += arrow((414, 228), (468, 228), 1.4)
    body += arrow((64, 64), (64, 38), 1.4)
    body += text(392, 252, "从左到右", 14)
    body += text(84, 50, "第一电离能", 13, "start")
    body += path("M 96 200 C 170 192 230 150 300 118 C 360 90 400 72 440 62", edge(2.2))
    body += text(150, 272, "同周期", 14)
    body += text(320, 292, "稀有气体除外", 13)
    body += ask(150, 108)
    return F(w, h, body, "总趋势")


def na_ne_valence():
    """钠多一个能层且最外层一个电子，氖最外层已排满。不写选项全文。"""
    w, h = 540, 340
    nax, nay = 150, 156
    body = ""
    for r in (26, 52, 80):
        body += circ(nax, nay, r, thin(1.5))
    body += circ(nax, nay, 6, face(0.55))
    body += _on_ring(nax, nay, 26, 2, -math.pi / 2)
    body += _on_ring(nax, nay, 52, 8, math.pi / 8)
    body += circ(nax + 80, nay, 4, face(1))
    nex, ney = 400, 156
    for r in (34, 70):
        body += circ(nex, ney, r, thin(1.5))
    body += circ(nex, ney, 6, face(0.55))
    body += _on_ring(nex, ney, 34, 2, -math.pi / 2)
    body += _on_ring(nex, ney, 70, 8, math.pi / 8)
    body += text(nax, 268, "钠", 16)
    body += text(nex, 268, "氖", 16)
    body += text(268, 78, "最外层", 14)
    body += line((250, 88), (nax + 76, nay - 8), thin(1.2))
    body += line((300, 88), (nex - 66, ney - 22), thin(1.2))
    body += ask(276, 168)
    return F(w, h, body, "钠与氖")


def orbital_share():
    """两团轨道重叠，重叠区有一对电子。不写定义全文。"""
    w, h = 520, 300
    left, right, cy, rad = 186, 304, 152, 70
    body = circ(left, cy, rad, thin(1.6))
    body += circ(right, cy, rad, thin(1.6))
    body += ell(245, cy, 24, 48, face(0.1))
    body += ell(245, cy, 24, 48, thin(1.3))
    body += circ(left, cy, 5, face(1))
    body += circ(right, cy, 5, face(1))
    body += circ(234, cy - 8, 4, face(1))
    body += circ(256, cy - 8, 4, face(1))
    body += text(245, 62, "轨道重叠", 15)
    body += text(245, 236, "共用电子对", 15)
    body += ask(460, 152)
    return F(w, h, body, "两个轨道")


def bond_length_nuclei():
    """尺寸线对齐两核中心，但不穿过核。不写定义全文。"""
    w, h = 500, 290
    a, b, y, rad = 150, 350, 108, 24
    body = _gap_line((a, y), (b, y), rad, rad, edge(2))
    body += circ(a, y, rad, face(0.08)) + circ(a, y, rad, edge(1.7))
    body += circ(b, y, rad, face(0.08)) + circ(b, y, rad, edge(1.7))
    body += text(a, y + 5, "核", 14)
    body += text(b, y + 5, "核", 14)
    y0 = y + rad + 10
    body += line((a, y0), (a, 186), hidden(1.2))
    body += line((b, y0), (b, 186), hidden(1.2))
    body += line((a, 186), (b, 186), edge(1.5))
    body += line((a, 176), (a, 196), edge(1.5))
    body += line((b, 176), (b, 196), edge(1.5))
    body += text(250, 222, "核间距", 15)
    body += ask(440, 108)
    return F(w, h, body, "两个原子核")


def methane_vsepr():
    """碳在中心，三个氢构成前面，背后一条键用虚线。不写构型名称。"""
    w, h = 500, 330
    c = (236, 156)
    top = (236, 64)
    left = (112, 224)
    right = (360, 216)
    back = (168, 108)
    body = text(24, 52, "价层电子对", 14, "start")
    body += _gap_line(top, left, 15, 15, thin(1.2))
    body += _gap_line(top, right, 15, 15, thin(1.2))
    body += _gap_line(left, right, 15, 15, thin(1.2))
    body += _gap_line(c, top, 16, 15, edge(2))
    body += _gap_line(c, left, 16, 15, edge(2))
    body += _gap_line(c, right, 16, 15, edge(2))
    body += _gap_line(c, back, 16, 15, hidden(1.6))
    body += dot(c[0], c[1], "C", 16, 13)
    for p in (top, left, right, back):
        body += dot(p[0], p[1], "H", 15, 13)
    body += text(236, 286, "甲烷", 16)
    body += ask(452, 150)
    return F(w, h, body, "四个方向")


def water_vsepr():
    """氧上两对孤对，两个氢折向一侧。不写构型名称。"""
    w, h = 500, 320
    cx, cy = 250.0, 162.0
    half = math.radians(52.2)
    arm = 88.0
    h1 = (cx - arm * math.sin(half), cy + arm * math.cos(half))
    h2 = (cx + arm * math.sin(half), cy + arm * math.cos(half))
    body = text(24, 54, "价层电子对", 14, "start")
    body += _gap_line((cx, cy), h1, 18, 14, edge(2))
    body += _gap_line((cx, cy), h2, 18, 14, edge(2))
    spread = math.radians(46)
    lp = 46.0
    for sign in (-1, 1):
        px = cx + sign * lp * math.sin(spread)
        py = cy - lp * math.cos(spread)
        body += ell(px, py, 18, 12, edge(1.4))
        body += circ(px - 5, py, 2.5, face(1))
        body += circ(px + 5, py, 2.5, face(1))
    body += text(cx, 78, "孤对", 14)
    body += dot(cx, cy, "O", 18, 14)
    body += dot(h1[0], h1[1], "H", 14, 12)
    body += dot(h2[0], h2[1], "H", 14, 12)
    body += ask(440, 168)
    return F(w, h, body, "水分子")


def polar_centers():
    """正电荷中心和负电荷中心分成两处。不写定义全文。"""
    w, h = 520, 300
    body = rim_stick((148, 176), (318, 176), 16, 30)
    body += dot(148, 176, "H", 16, 14)
    body += dot(318, 176, "Cl", 30, 16)
    body += circ(186, 118, 3.4, face(1))
    body += circ(270, 118, 3.4, face(1))
    body += line((186, 118), (270, 118), hidden(1.3))
    body += text(186, 100, "+", 16)
    body += text(270, 100, "−", 16)
    body += text(28, 72, "正电荷中心", 14, "start")
    body += line((98, 80), (180, 112), thin(1.2))
    body += text(332, 72, "负电荷中心", 14, "start")
    body += line((332, 80), (276, 112), thin(1.2))
    body += ask(462, 176)
    return F(w, h, body, "电荷中心")


def co2_dipoles():
    """直线分子两侧偶极等长反向。不写分子极性的结论。"""
    w, h = 540, 280
    y = 150
    body = dot(110, y, "O", 18, 14)
    body += dot(250, y, "C", 18, 14)
    body += dot(390, y, "O", 18, 14)
    body += stick((128, y), (232, y), 2)
    body += stick((268, y), (372, y), 2)
    body += arrow((214, 96), (142, 96), 1.5)
    body += arrow((286, 96), (358, 96), 1.5)
    body += text(168, 78, "偶极", 13)
    body += text(332, 78, "偶极", 13)
    body += text(250, 78, "+", 14)
    body += text(250, 214, "对称", 15)
    body += ask(478, 150)
    return F(w, h, body, "二氧化碳")


def cell_from_lattice():
    """从点阵里框出一个重复单元再取出来。不写定义全文。"""
    w, h = 540, 320
    xs = (52, 114, 176, 238)
    ys = (62, 124, 186)
    body = ""
    for x in xs:
        for y in ys:
            body += circ(x, y, 5, face(0.45))
    body += rect(114, 62, 62, 62, edge(2.3))
    body += arrow((188, 78), (300, 108), 1.5)
    body += rect(312, 78, 148, 148, edge(1.9))
    for px, py in ((312, 78), (460, 78), (312, 226), (460, 226)):
        body += circ(px, py, 8, face(0.16)) + circ(px, py, 8, edge(1.5))
    body += text(138, 246, "晶格", 15)
    body += text(386, 268, "晶胞", 15)
    body += ask(498, 150)
    return F(w, h, body, "从晶格取出")


def metal_electron_sea():
    """金属离子分成两层，电子留在层间和离子间隙。不写结合作用的名称。"""
    w, h = 520, 300
    body = wave(78, 152, 300, 7, 4)
    spots = [(100 + c * 80, y) for c in range(4) for y in (108, 196)]
    for x, y in spots:
        body += circ(x, y, 16, face(0.08)) + circ(x, y, 16, edge(1.6))
        body += text(x, y + 5, "+", 14)
    for x in (140, 220, 300):
        body += circ(x, 108, 3.2, face(1))
        body += circ(x, 196, 3.2, face(1))
        body += circ(x, 152, 3.2, face(1))
    body += text(430, 108, "e-", 15)
    body += line((408, 114), (318, 148), thin(1.2))
    body += text(220, 252, "金属离子", 14)
    body += ask(460, 196)
    return F(w, h, body, "金属晶体")


def nacl_lattice():
    """钠离子和氯离子交替排列。不写晶体类型的名称。"""
    w, h = 480, 320
    body = ""
    for r in range(3):
        for c in range(3):
            x = 118 + c * 74
            y = 86 + r * 68
            if (r + c) % 2 == 0:
                lab, rad = "Na+", 16
            else:
                lab, rad = "Cl−", 22
            body += circ(x, y, rad, face(0.08))
            body += circ(x, y, rad, edge(1.6))
            body += text(x, y + 4, lab, 12)
    body += ask(430, 160)
    return F(w, h, body, "氯化钠")


def metal_slide_conduct():
    """一边电子沿离子移动，一边原子层错开。不写选项全文。"""
    w, h = 540, 320
    body = text(130, 52, "导电", 15)
    for x in (70, 130, 190):
        body += circ(x, 128, 15, face(0.08)) + circ(x, 128, 15, edge(1.6))
        body += text(x, 133, "+", 13)
    for x in (100, 160):
        body += circ(x, 166, 3.2, face(1))
    body += arrow((48, 166), (214, 166), 1.5)
    body += text(130, 198, "电子", 14)
    body += text(400, 52, "延展", 15)
    for x in (330, 395, 460):
        body += circ(x, 196, 14, face(0.08)) + circ(x, 196, 14, edge(1.6))
        body += text(x, 201, "+", 12)
    for x in (362, 427, 492):
        body += circ(x, 118, 14, face(0.08)) + circ(x, 118, 14, edge(1.6))
        body += text(x, 123, "+", 12)
    for x in (360, 425, 490):
        body += circ(x, 156, 3, face(1))
    body += arrow((348, 90), (500, 90), 1.5)
    body += text(424, 78, "滑动", 13)
    body += ask(270, 230)
    return F(w, h, body, "两种表现")


def coord_donate():
    """配体的孤对电子指向中心离子的空轨道。不写键的名称。"""
    w, h = 540, 300
    body = circ(96, 160, 26, face(0.08)) + circ(96, 160, 26, edge(1.7))
    body += text(96, 166, "L", 16)
    body += text(96, 214, "配体", 14)
    body += circ(132, 152, 3.5, face(1))
    body += circ(132, 168, 3.5, face(1))
    body += arrow((148, 160), (292, 160), 1.6)
    body += ell(330, 160, 30, 20, hidden(1.5))
    body += text(330, 112, "空轨道", 14)
    body += circ(392, 160, 32, face(0.08)) + circ(392, 160, 32, edge(1.7))
    body += text(392, 166, "M", 16)
    body += text(392, 220, "中心离子", 14)
    body += ask(486, 72)
    return F(w, h, body, "中心与配体")


def cuso4_ammonia():
    """硫酸铜加过量氨水：先有固体，再变成颜色更深的溶液。不写选项全文。"""
    w, h = 540, 330
    body = _beaker_liquid(28, 72, 108, 146, 118, 0.1)
    body += beaker(28, 72, 108, 146)
    body += text(82, 252, "硫酸铜", 14)
    body += arrow((146, 150), (186, 150), 1.5)
    body += text(166, 118, "过量", 13)
    body += text(166, 136, "氨水", 13)
    body += _beaker_liquid(198, 72, 108, 146, 118, 0.1)
    for dx in (0, 18, 36):
        body += circ(232 + dx, 186, 6, face(0.55))
    body += beaker(198, 72, 108, 146)
    body += arrow((316, 150), (356, 150), 1.5)
    body += _beaker_liquid(368, 72, 108, 146, 118, 0.42)
    body += beaker(368, 72, 108, 146)
    body += text(422, 252, "深蓝", 14)
    body += ask(492, 250)
    return F(w, h, body, "加入氨水")


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


# ---------------------------------------------------------------- 选必三 · 补图


def formula_at(x, y, spec, size=15):
    """分子式。连续数字写成更小的 ASCII text，不用 Unicode 下标。返回 (svg, 右端 x)。"""
    scale = size / 15.0
    wide = {"C": 9.8, "H": 11.4, "O": 11.6, "N": 11.2}
    body = ""
    cursor = float(x)
    i = 0
    sub_size = int(round(size * 0.66))
    while i < len(spec):
        if spec[i].isdigit():
            j = i + 1
            while j < len(spec) and spec[j].isdigit():
                j += 1
            token = spec[i:j]
            body += text(cursor, y + size * 0.30, token, sub_size, "start")
            cursor += (5.9 * len(token) + 1.6) * scale
            i = j
        else:
            ch = spec[i]
            body += text(cursor, y, ch, size, "start")
            cursor += (wide.get(ch, 10.0) + 0.8) * scale
            i += 1
    return body, cursor


def formula_mid(cx, y, spec, size=15):
    _body, right = formula_at(0, y, spec, size)
    return formula_at(cx - right / 2.0, y, spec, size)[0]


def h_bond(c, h, cr=15, gap=12):
    dx, dy = h[0] - c[0], h[1] - c[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    a = (c[0] + ux * cr, c[1] + uy * cr)
    b = (h[0] - ux * gap, h[1] - uy * gap)
    return stick(a, b, 1)


def benzene_at(cx, cy, r):
    pts = []
    for i in range(6):
        ang = math.radians(-90 + i * 60)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    body = ""
    for i in range(6):
        body += line(pts[i], pts[(i + 1) % 6], edge(2.1))
    body += circ(cx, cy, r * 0.50, edge(1.6))
    return body, pts


def c4h10_isomers():
    """直链四个碳，支链是三碳链加一个甲基。不写种数。"""
    w, h = 560, 310
    body = formula_mid(280, 54, "C4H10", 16)
    straight = [(52, 178), (116, 124), (180, 178), (244, 124)]
    for i in range(3):
        body += rim_stick(straight[i], straight[i + 1], 15, 15, 1)
    for p in straight:
        body += dot(p[0], p[1], "C", 15, 12)
    body += text(148, 224, "正丁烷", 15)
    hub = (410, 162)
    arms = [(338, 162), (482, 162), (410, 96)]
    for arm in arms:
        body += rim_stick(hub, arm, 15, 15, 1)
    body += dot(hub[0], hub[1], "C", 15, 12)
    for arm in arms:
        body += dot(arm[0], arm[1], "C", 15, 12)
    body += text(410, 224, "异丁烷", 15)
    body += ask(280, 262)
    return F(w, h, body, "碳骨架")


def parallel_open(a, b, half, sw=1.7):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    body = line((a[0] + px * half, a[1] + py * half), (b[0] + px * half, b[1] + py * half), edge(sw))
    body += line((a[0] - px * half, a[1] - py * half), (b[0] - px * half, b[1] - py * half), edge(sw))
    return body


def tube(x, y, w, h, sw=2):
    """试管。圆底用三次曲线，避免刚好半圆的弧在渲染时翻到另一侧。"""
    r = w / 2.0
    k = 0.5523 * r
    cx = x + r
    yb = y + h - r
    bot = y + h
    d = "M %g %g L %g %g C %g %g %g %g %g %g C %g %g %g %g %g %g L %g %g" % (
        x, y, x, yb,
        x, yb + k, cx - k, bot, cx, bot,
        cx + k, bot, x + w, yb + k, x + w, yb,
        x + w, y)
    return path(d, edge(sw))


def tube_fill(x, y, w, h, level, op):
    """液面停在管壁内侧，并跟着圆底收进去。"""
    inset = 3.0
    r = w / 2.0 - inset
    k = 0.5523 * r
    x0, x1 = x + inset, x + w - inset
    cx = (x0 + x1) / 2.0
    yb = y + h - w / 2.0
    bot = y + h - inset
    d = "M %g %g L %g %g C %g %g %g %g %g %g C %g %g %g %g %g %g L %g %g Z" % (
        x0, level, x0, yb,
        x0, yb + k, cx - k, bot, cx, bot,
        cx + k, bot, x1, yb + k, x1, yb,
        x1, level)
    return path(d, face(op))


def distill_setup():
    """冷凝管靠近接收瓶的一端进水、靠近烧瓶的一端出水。接收瓶敞口，管口停在液面上方。"""
    w, h = 600, 430
    cx, top = 108, 62
    neck_w, neck_h, rx, ry = 26, 70, 54, 48
    cy = top + neck_h + ry - 4
    half = neck_w / 2.0
    y_join = cy - ry * math.sqrt(max(0.0, 1.0 - (half / rx) ** 2))
    body = ell(cx, cy, rx, ry, edge(1.8))
    body += line((cx - half, top), (cx - half, y_join), edge(1.8))
    body += line((cx + half, top), (cx + half, y_join), edge(1.8))
    body += line((cx - half, top), (cx - half - 7, top - 16), edge(1.7))
    body += line((cx + half, top), (cx + half + 7, top - 16), edge(1.7))
    body += line((cx - half - 7, top - 16), (cx + half + 7, top - 16), edge(1.7))
    arm_y = top + 32
    body += line((cx, top - 22), (cx, arm_y + 8), edge(1.5))
    body += rect(cx - 5, arm_y - 8, 10, 16, edge(1.4), 2)
    level = cy + 8
    dx = rx * math.sqrt(max(0.0, 1.0 - ((level - cy) / ry) ** 2))
    body += path(
        "M %g %g A %g %g 0 0 1 %g %g L %g %g Z" % (cx - dx, level, rx, ry, cx + dx, level, cx - dx, level),
        face(0.1),
    )
    body += line((cx - dx, level), (cx + dx, level), thin(1.2))
    # 蒸汽从颈中部斜向下，管口停在敞口正中、液面上方。b 更低，进水接在 b 端。
    a = (cx + half, arm_y)
    b = (484, 208)
    ux, uy, length = (b[0] - a[0]) / 1.0, (b[1] - a[1]) / 1.0, math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = ux / length, uy / length
    px, py = -uy, ux
    body += parallel_open(a, b, 5.5, 1.7)
    j0 = (a[0] + ux * length * 0.20, a[1] + uy * length * 0.20)
    j1 = (a[0] + ux * length * 0.74, a[1] + uy * length * 0.74)
    body += parallel_open(j0, j1, 16, 1.8)
    body += line((j0[0] + px * 16, j0[1] + py * 16), (j0[0] - px * 16, j0[1] - py * 16), edge(1.8))
    body += line((j1[0] + px * 16, j1[1] + py * 16), (j1[0] - px * 16, j1[1] - py * 16), edge(1.8))
    # +p 朝画面下方。下端进水，上端出水。
    inn = (j1[0] + px * 16, j1[1] + py * 16)
    in_far = (inn[0] + px * 36, inn[1] + py * 36)
    outn = (j0[0] - px * 16, j0[1] - py * 16)
    out_far = (outn[0] - px * 34, outn[1] - py * 34)
    body += arrow(in_far, inn, 1.5)
    body += arrow(outn, out_far, 1.5)
    body += text(in_far[0] + px * 16, in_far[1] + py * 16 + 6, "进水", 14)
    body += text(out_far[0] - px * 8, out_far[1] - py * 14, "出水", 14)
    mouth_y, mouth_l, mouth_r = 228, 448, 520
    neck_y, base_y = 258, 336
    base_l, base_r = 418, 552
    body += line((mouth_l, mouth_y), (mouth_r, mouth_y), edge(1.8))
    body += line((mouth_l, mouth_y), (mouth_l, neck_y), edge(1.8))
    body += line((mouth_r, mouth_y), (mouth_r, neck_y), edge(1.8))
    body += line((mouth_l, neck_y), (base_l, base_y), edge(1.8))
    body += line((mouth_r, neck_y), (base_r, base_y), edge(1.8))
    body += line((base_l, base_y), (base_r, base_y), edge(1.8))
    liq = 292
    t = (liq - neck_y) / float(base_y - neck_y)
    ll = mouth_l + (base_l - mouth_l) * t
    lr = mouth_r + (base_r - mouth_r) * t
    body += poly([(ll + 3, liq), (base_l + 4, base_y - 3), (base_r - 4, base_y - 3), (lr - 3, liq)], face(0.1))
    body += line((ll + 3, liq), (lr - 3, liq), thin(1.2))
    body += circ(b[0], b[1] + 8, 3.2, face(0.8))
    body += text((base_l + base_r) / 2.0, base_y + 24, "接收", 15)
    body += lamp_at(cx, 328)
    body += text(cx, 362, "加热", 14)
    body += ask(32, 210)
    return F(w, h, body, "蒸馏装置")


def alkane_chain():
    """碳和碳之间只画一根键。不写选项里的键名。"""
    w, h = 520, 290
    pts = [(78, 176), (156, 116), (234, 176), (312, 116)]
    body = ""
    for i in range(3):
        body += rim_stick(pts[i], pts[i + 1], 16, 16, 1)
    for p in pts:
        body += dot(p[0], p[1], "C", 16, 13)
    body += text(195, 230, "烷烃", 16)
    body += ask(440, 150)
    return F(w, h, body, "碳架")


def methane_light_cl():
    """四个单键的甲烷。一个氢换成氯，同时离开 HCl。不要画成双键加成。"""
    w, h = 620, 310
    c = (78, 148)
    hydrogens = ((78, 84), (78, 210), (26, 148), (130, 148))
    body = ""
    for hpos in hydrogens:
        body += h_bond(c, hpos, 16, 12)
        body += text(hpos[0], hpos[1], "H", 13)
    body += dot(c[0], c[1], "C", 16, 13)
    body += text(78, 246, "甲烷", 14)
    body += text(168, 154, "+", 18)
    body += rim_stick((196, 148), (248, 148), 15, 15, 1)
    body += dot(196, 148, "Cl", 15, 12)
    body += dot(248, 148, "Cl", 15, 12)
    body += text(222, 196, "氯气", 14)
    body += sun(318, 62, 11)
    body += text(352, 68, "光照", 14, "start")
    body += arrow((300, 148), (368, 148), 1.6)
    pc = (430, 148)
    body += h_bond(pc, (430, 88), 16, 12)
    body += text(430, 88, "H", 13)
    body += h_bond(pc, (430, 208), 16, 12)
    body += text(430, 208, "H", 13)
    body += h_bond(pc, (378, 148), 16, 12)
    body += text(378, 148, "H", 13)
    body += rim_stick(pc, (492, 148), 16, 15, 1)
    body += dot(pc[0], pc[1], "C", 16, 13)
    body += dot(492, 148, "Cl", 15, 12)
    body += text(538, 118, "+", 16)
    body += text(568, 118, "HCl", 15)
    body += ask(568, 210)
    return F(w, h, body, "光照")


def unsaturation_three():
    """按题干顺序画单键、双键、三键。名称里正好是答案的那个词不写，用分子式区分。"""
    w, h = 640, 340
    body = ""
    # 乙烷 C2H6：六个氢，碳碳单键
    c1, c2 = (78, 150), (148, 150)
    eth_h = ((28, 150), (198, 150), (78, 96), (78, 204), (148, 96), (148, 204))
    body += rim_stick(c1, c2, 14, 14, 1)
    for hpos in eth_h:
        src = c1 if abs(hpos[0] - c1[0]) <= abs(hpos[0] - c2[0]) else c2
        body += h_bond(src, hpos, 14, 11)
        body += text(hpos[0], hpos[1], "H", 13)
    body += dot(c1[0], c1[1], "C", 14, 12)
    body += dot(c2[0], c2[1], "C", 14, 12)
    body += formula_mid(113, 262, "C2H6", 15)
    # 乙烯 C2H4：四个氢，碳碳双键
    e1, e2 = (292, 150), (368, 150)
    ethene_h = ((246, 108), (246, 192), (414, 108), (414, 192))
    body += rim_stick(e1, e2, 14, 14, 2)
    for i, hpos in enumerate(ethene_h):
        src = e1 if i < 2 else e2
        body += h_bond(src, hpos, 14, 11)
        body += text(hpos[0], hpos[1], "H", 13)
    body += dot(e1[0], e1[1], "C", 14, 12)
    body += dot(e2[0], e2[1], "C", 14, 12)
    body += formula_mid(330, 262, "C2H4", 15)
    # 第三个：两个氢，碳碳三键。分子式 C2H2
    y1, y2 = (490, 150), (566, 150)
    body += rim_stick(y1, y2, 14, 14, 3)
    body += h_bond(y1, (444, 150), 14, 11)
    body += text(444, 150, "H", 13)
    body += h_bond(y2, (612, 150), 14, 11)
    body += text(612, 150, "H", 13)
    body += dot(y1[0], y1[1], "C", 14, 12)
    body += dot(y2[0], y2[1], "C", 14, 12)
    body += formula_mid(528, 262, "C2H2", 15)
    body += ask(590, 64)
    return F(w, h, body, "不饱和程度")


def benzene_febr():
    """产物仍是苯环，只连一个溴，旁边离开 HBr。不要画成加成后的饱和环。"""
    w, h = 560, 320
    ring, _pts = benzene_at(108, 158, 50)
    body = ring
    body += text(108, 236, "苯", 15)
    body += text(228, 124, "Br–Br", 16)
    body += text(228, 154, "液溴", 14)
    body += text(228, 186, "铁或溴化铁", 13)
    body += arrow((300, 158), (352, 158), 1.6)
    ring2, pts2 = benzene_at(430, 158, 46)
    body += ring2
    top = pts2[0]
    body += line(top, (top[0], top[1] - 22), edge(2.0))
    body += text(top[0], top[1] - 34, "Br", 14)
    body += text(392, 250, "+", 16)
    body += text(430, 250, "HBr", 14)
    body += ask(520, 78)
    return F(w, h, body, "苯与液溴")


def toluene_benzene_kmno():
    """左边甲基使结构可辨，现象用题干里的词。不写氧化原因。"""
    w, h = 560, 360
    body = text(280, 50, "酸性高锰酸钾", 15)
    left, pts = benzene_at(130, 128, 34)
    body += left
    top = pts[0]
    body += line(top, (top[0], top[1] - 20), edge(2.0))
    body += text(130, 186, "甲苯", 15)
    body += tube(100, 200, 60, 96)
    body += tube_fill(100, 200, 60, 96, 228, 0.08)
    body += text(130, 318, "褪色", 14)
    right, _rp = benzene_at(400, 128, 34)
    body += right
    body += text(400, 186, "苯", 15)
    body += tube(370, 200, 60, 96)
    body += tube_fill(370, 200, 60, 96, 228, 0.32)
    body += text(400, 318, "通常不能", 14)
    body += ask(265, 250)
    return F(w, h, body, "两种芳烃")


def halo_cx():
    """圈出碳和 X 相连的那一段。不写官能团的中文名。"""
    w, h = 500, 280
    body = dot(78, 145, "C", 16, 13)
    body += rim_stick((78, 145), (168, 145), 16, 16, 1)
    body += dot(168, 145, "C", 16, 13)
    body += rim_stick((168, 145), (236, 145), 16, 8, 1)
    body += text(246, 151, "X", 18, "start")
    body += circ(214, 145, 52, edge(1.5))
    body += text(123, 214, "卤代烃", 15)
    body += ask(440, 78)
    return F(w, h, body, "碳与卤素")


def bromoethane_water():
    """水溶液加热。不写醇溶液，也不写产物名称。"""
    w, h = 560, 340
    body = dot(46, 118, "C", 15, 12)
    body += rim_stick((46, 118), (108, 118), 15, 15, 1)
    body += dot(108, 118, "C", 15, 12)
    body += rim_stick((108, 118), (176, 118), 15, 16, 1)
    body += dot(176, 118, "Br", 16, 12)
    body += text(110, 168, "溴乙烷", 14)
    body += arrow((214, 118), (268, 118), 1.6)
    body += beaker(286, 72, 150, 112)
    body += liquid(286, 72, 150, 112, 118)
    body += text(361, 140, "氢氧化钠水溶液", 12)
    body += lamp_at(361, 268)
    body += text(470, 210, "加热", 15)
    body += ask(500, 118)
    return F(w, h, body, "水溶液中加热")


def phenol_fecl3():
    """试管和滴管。不写颜色。"""
    w, h = 460, 340
    body = tube(176, 108, 58, 146)
    body += tube_fill(176, 108, 58, 146, 160, 0.12)
    body += text(205, 286, "苯酚", 15)
    body += ell(205, 52, 10, 14, edge(1.6))
    body += line((205, 66), (205, 104), edge(1.6))
    body += line((199, 104), (211, 104), edge(1.5))
    body += text(236, 64, "三氯化铁", 14, "start")
    body += ask(78, 180)
    return F(w, h, body, "滴加")


def acetaldehyde_fg():
    """两个碳，圈住羰基碳以及它连着的氧和氢。不写官能团中文名。"""
    w, h = 520, 300
    body = dot(72, 176, "C", 16, 13)
    body += rim_stick((72, 176), (186, 176), 16, 16, 1)
    body += dot(186, 176, "C", 16, 13)
    body += rim_stick((186, 176), (186, 90), 16, 16, 2)
    body += dot(186, 74, "O", 16, 13)
    body += h_bond((186, 176), (258, 158), 16, 12)
    body += text(258, 158, "H", 15)
    body += circ(214, 130, 90, edge(1.45))
    body += text(72, 236, "乙醛", 15)
    body += ask(468, 72)
    return F(w, h, body, "乙醛分子")


def aldehyde_plus_h2():
    """反应物和氢气。产物位置只留问号，不写名称。"""
    w, h = 520, 260
    body = box(24, 96, 100, 50, "乙醛")
    body += text(152, 126, "+", 18)
    body += text(196, 126, "H", 16)
    body += stick((210, 126), (244, 126), 1)
    body += text(258, 126, "H", 16)
    body += arrow((286, 121), (368, 121), 1.7)
    body += text(327, 98, "催化", 14)
    body += ask(430, 121)
    return F(w, h, body, "催化加氢")


def acetic_fg():
    """甲基在圈外。圈内是羰基和羟基。不写官能团中文名。"""
    w, h = 540, 320
    body = dot(48, 186, "C", 16, 13)
    body += rim_stick((48, 186), (156, 186), 16, 16, 1)
    body += dot(156, 186, "C", 16, 13)
    body += rim_stick((156, 186), (156, 108), 16, 16, 2)
    body += dot(156, 92, "O", 16, 13)
    body += rim_stick((156, 186), (252, 186), 16, 16, 1)
    body += dot(252, 186, "O", 16, 13)
    body += h_bond((252, 186), (304, 146), 16, 12)
    body += text(304, 146, "H", 15)
    body += circ(214, 152, 112, edge(1.45))
    body += text(48, 262, "乙酸", 15)
    body += ask(492, 64)
    return F(w, h, body, "乙酸分子")


def ester_naoh():
    """条件写在装置上。产物不命名。"""
    w, h = 560, 330
    body = box(20, 108, 132, 50, "乙酸乙酯", size=15)
    body += arrow((162, 133), (236, 133), 1.6)
    body += beaker(252, 78, 160, 116)
    body += liquid(252, 78, 160, 116, 124)
    body += text(332, 150, "氢氧化钠溶液", 13)
    body += lamp_at(332, 286)
    body += text(460, 168, "加热", 15)
    body += ask(490, 120)
    return F(w, h, body, "在碱液中")


def route_unknown(left, right, title):
    w, h = 540, 260
    body = box(24, 96, 140, 52, left, size=16)
    body += arrow((174, 122), (330, 122), 1.8)
    body += ask(252, 72)
    body += text(252, 176, "条件", 15)
    body += box(340, 96, 160, 52, right, size=16)
    return F(w, h, body, title)


def route_br_ethanol():
    """箭头上方是问号。不写水溶液或加热的那句条件。"""
    return route_unknown("溴乙烷", "乙醇", "条件未知")


def route_ethanol_ester():
    """起点和终点清楚，中间步骤和条件都是问号。不写那条唯一路线的句子。"""
    w, h = 580, 270
    body = box(16, 100, 100, 50, "乙醇")
    body += arrow((124, 125), (196, 125), 1.6)
    body += ask(160, 74)
    body += box(204, 100, 72, 50, "?", size=18)
    body += arrow((284, 125), (360, 125), 1.6)
    body += ask(322, 74)
    body += box(368, 100, 140, 50, "乙酸乙酯", size=15)
    body += text(290, 190, "路线", 15)
    return F(w, h, body, "分步")


def route_br_ethene():
    """和水解那条路线用同一个问号空位，终点改成乙烯。不写醇溶液条件。"""
    return route_unknown("溴乙烷", "乙烯", "条件未知")


def acetic_phenol_pair():
    """两支试管对照。不写哪一边冒气、哪一边显色。"""
    w, h = 520, 320
    body = tube(70, 70, 60, 150)
    body += tube_fill(70, 70, 60, 150, 130, 0.12)
    body += text(100, 252, "乙酸", 16)
    body += tube(250, 70, 60, 150)
    body += tube_fill(250, 70, 60, 150, 130, 0.12)
    body += text(280, 252, "苯酚", 16)
    body += text(190, 150, "对照", 15)
    body += ask(430, 150)
    return F(w, h, body, "两支试管")


def amino_both():
    """中心碳连着四个基团。氨基和羧基写成式子，不写那句中文。"""
    w, h = 540, 310
    body = text(36, 156, "-NH", 18, "start")
    body += sub(72, 164, "2")
    body += stick((88, 150), (162, 150), 1)
    body += dot(178, 150, "C", 16, 13)
    body += stick((194, 150), (246, 150), 1)
    body += text(254, 156, "-COOH", 18, "start")
    body += stick((178, 134), (178, 92), 1)
    body += text(178, 78, "R", 15)
    body += stick((178, 166), (178, 206), 1)
    body += text(178, 228, "H", 15)
    body += text(250, 268, "氨基酸", 15)
    body += ask(490, 78)
    return F(w, h, body, "同一个分子")


def nucleotide_parts():
    """三块连在一起。糖不写成更具体的那一个名字。"""
    w, h = 540, 280
    body = box(20, 96, 120, 52, "磷酸")
    body += line((140, 122), (196, 122), edge(2.0))
    body += box(196, 96, 120, 52, "糖")
    body += line((316, 122), (372, 122), edge(2.0))
    body += box(372, 96, 120, 52, "碱基")
    body += text(256, 190, "核苷酸", 15)
    body += ask(256, 230)
    return F(w, h, body, "三部分")


def dna_rna_pair():
    """糖的差别画出来，碱基只标类别。不写两种碱基的名字。"""
    w, h = 540, 310
    body = text(145, 58, "DNA", 16)
    body += box(40, 76, 180, 48, "脱氧核糖", size=16)
    body += line((130, 124), (130, 156), edge(1.6))
    body += box(70, 156, 120, 48, "碱基")
    body += text(400, 58, "RNA", 16)
    body += box(320, 76, 150, 48, "核糖", size=16)
    body += line((395, 124), (395, 156), edge(1.6))
    body += box(345, 156, 120, 48, "碱基")
    body += ask(270, 180)
    return F(w, h, body, "糖与碱基")


def sucrose_then_silver():
    """先水解，再放到银镜装置前。不写中和酸的那一句。"""
    w, h = 580, 290
    body = box(16, 100, 96, 50, "蔗糖")
    body += arrow((120, 125), (188, 125), 1.6)
    body += text(154, 100, "水解", 14)
    body += box(196, 100, 124, 50, "水解产物", size=14)
    body += arrow((328, 125), (400, 125), 1.6)
    body += text(364, 100, "银镜", 14)
    body += tube(408, 78, 44, 100)
    body += text(270, 196, "注意", 15)
    body += ask(520, 130)
    return F(w, h, body, "检验之前")


def starch_iodine_two():
    """左边颜色在，右边颜色没了。不写这说明了什么。"""
    w, h = 560, 340
    body = tube(64, 64, 64, 150)
    body += tube_fill(64, 64, 64, 150, 108, 0.36)
    body += text(96, 246, "淀粉", 15)
    body += text(96, 270, "碘水", 15)
    body += text(96, 294, "蓝色", 15)
    body += arrow((156, 140), (248, 140), 1.6)
    body += text(202, 118, "水解较完全", 13)
    body += tube(268, 64, 64, 150)
    body += tube_fill(268, 64, 64, 150, 108, 0.08)
    body += text(300, 252, "碘水", 15)
    body += text(300, 278, "蓝色消失", 14)
    body += ask(470, 150)
    return F(w, h, body, "加碘前后")


def cond_vs_add():
    """下面一行才有离开的小分子。不写选项那句。"""
    w, h = 560, 330
    body = text(70, 78, "加聚", 16, "start")
    for x in (70, 124, 178):
        body += circ(x, 118, 13, edge(1.7))
    body += arrow((210, 118), (258, 118), 1.5)
    xs = (290, 340, 390)
    for i in range(len(xs) - 1):
        body += line((xs[i] + 13, 118), (xs[i + 1] - 13, 118), edge(2.0))
    for x in xs:
        body += circ(x, 118, 13, edge(1.7))
    body += text(70, 188, "缩聚", 16, "start")
    for x in (70, 124, 178):
        body += circ(x, 228, 13, edge(1.7))
    body += arrow((210, 228), (258, 228), 1.5)
    for i in range(len(xs) - 1):
        body += line((xs[i] + 13, 228), (xs[i + 1] - 13, 228), edge(2.0))
    for x in xs:
        body += circ(x, 228, 13, edge(1.7))
    body += arrow((390, 244), (450, 286), 1.4)
    body += circ(468, 292, 12, edge(1.6))
    body += text(488, 298, "小分子", 14, "start")
    body += ask(510, 78)
    return F(w, h, body, "两种方式")


def linear_heat():
    """直链并排，加热后变弯、彼此分开，冷却箭头指回去。链与链之间不画交联。不写材料类别。"""
    w, h = 560, 330
    body = ""
    for y in (96, 124, 152):
        body += line((32, y), (196, y), edge(2.1))
    body += text(114, 188, "线型", 15)
    body += arrow((214, 124), (308, 124), 1.6)
    body += text(261, 102, "加热", 14)
    for y in (84, 128, 172):
        body += wave(328, y, 170, 8, 3)
    body += arrow((460, 236), (250, 236), 1.5)
    body += text(355, 218, "冷却", 14)
    body += ask(512, 196)
    return F(w, h, body, "链的形态")


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
    add("cnk_h002_q4", cuo_to_cu(), "把氧化铜变成铜单质", must=("氧化铜", "铜", "?"))
    add("cnk_h004_q3", electron_in(), "氧化剂在反应中的变化", must=("e-", "化合价", "?"))
    add("cnk_h005_q3", acid_base_colors(), "稀硫酸使紫色石蕊变红", must=("稀硫酸", "石蕊", "氢氧化钠", "酚酞", "?"))
    add("cnk_h006_q1", sodium_burn(), "钠在空气中燃烧", must=("钠", "空气", "淡黄色", "?"))
    add("cnk_h006_q3", carbonate_heat(), "加热时更容易分解并放出二氧化碳", ("2", "3"), must=("Na", "澄清石灰水", ">2</text>", ">3</text>", "?"))
    add("cnk_h006_q4", hcl_identify(), "鉴别碳酸钠溶液和氢氧化钠溶液", must=("稀盐酸", "甲", "乙", "?"))
    add("cnk_h007_q3", hclo_light(), "久置的氯水漂白能力变弱", ("2",), must=("HClO", "光", ">2</text>", "?"))
    add("cnk_h010_q3", dissolve_transfer(), "用固体配制溶液时", must=("烧杯", "溶解", "冷却", "容量瓶", "定容", "?"))
    add("cnk_h015_q1", atom_parts(), "决定元素种类的是原子中的", must=("质子", "中子", "电子", "?"))
    add("cnk_h016_q4", na_k_radius(), "比较钠和钾的金属性", must=("钠", "钾", "半径", "?"))
    add("cnk_h017_q2", h2_share(), "共价键的形成方式", must=("电子对", "?"))
    add("cnk_h018_q4", na_mg_al_trend(), "钠、镁、铝位于同一周期", must=("钠", "镁", "铝", "核电荷", "半径", "?"))

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
    add("cnk_h020_q1", sulfur_burn(), "硫在空气中燃烧", must=("硫", "空气", "?"))
    add("cnk_h020_q2", so2_fuchsin(), "二氧化硫使品红溶液褪色", must=("二氧化硫", "品红", "褪色", "?"))
    add("cnk_h020_q3", open_sulfuric(), "浓硫酸敞口放置后质量增加", must=("浓硫酸", "敞口", "质量", "?"))
    add("cnk_h021_q2", ammonia_litmus(), "氨水使红色石蕊试纸变蓝", must=("氨水", "石蕊试纸", "红", "蓝", "?"))
    add("cnk_h021_q4", nitric_brown(), "下列关于硝酸的说法", must=("浓硝酸", "棕色瓶", "?"))
    add("cnk_h023_q3", nitrogen_valence(), "氨催化氧化可以得到一氧化氮", ("2",), must=("-3", "+2", "+5", "化合价", "?"))
    add("cnk_h023_q4", so2_co2_fuchsin(), "要区分二氧化硫和二氧化碳", must=("二氧化硫", "二氧化碳", "品红", "?"))
    add("cnk_h025_q2", sulfur_valence(), "硫单质变成二氧化硫时", must=("0", "+4", "化合价", ">2</text>", "?"))
    add("cnk_h026_q1", charcoal_exo(), "木炭在空气中燃烧时", must=("木炭", "生成物", "能量", "进程", "?"))
    add("cnk_h026_q3", caco3_endo(), "碳酸钙受热分解需要持续加热", must=("碳酸钙", "生成物", "能量", "进程", "?"))
    add("cnk_h027_q2", catalyst_speed(), "加入催化剂后，化学反应速率一般会", must=("无催化剂", "有催化剂", "时间", "?"))
    add("cnk_h027_q4", heat_collision(), "升高温度通常使反应加快", must=("低温", "高温", "有效碰撞", "?"))
    add("cnk_h028_q4", catalyst_equilibrium(), "某可逆反应已经达到平衡", must=("正", "逆", "催化剂", "组成", "?"))
    add("cnk_h029_q4", closed_circuit(), "做这个实验时，比较合理的做法是", must=("电极", "电解质", "导线", "?"))
    add("cnk_h030_q4", h2o2_mno2(), "用过氧化氢分解来看催化剂的作用", must=("过氧化氢", "二氧化锰", "不加", "?"))
    add("cnk_h031_q4", ethanol_ether_b2(), "分子式都是 C2H6O", must=("乙醇", "甲醚", ">2</text>", ">6</text>", "?"))
    add("cnk_h032_q1", ethylene_bond(), "乙烯分子中的特征结构", must=("乙烯", "C", "H", "?"))
    add("cnk_h032_q3", ethylene_chain(), "大量乙烯分子打开双键", must=("乙烯", "聚乙烯", "?"))
    add("cnk_h033_q1", ethanol_oh(), "乙醇分子中决定其主要化学性质的官能团", must=("乙醇", "OH", "?"))
    add("cnk_h033_q3", ethanol_to_unknown(), "乙醇在铜或银作催化剂并加热", must=("乙醇", "铜或银", "加热", "氧气", "?"))
    add("cnk_h034_q4", glucose_brick(), "葡萄糖能使新制氢氧化铜悬浊液", must=("葡萄糖", "新制氢氧化铜", "砖红色沉淀", "?"))
    add("cnk_h036_q2", methane_space(), "甲烷分子的空间形状", must=("甲烷", "C", "H", "?"))
    add("cnk_h036_q3", ethylene_model(), "搭建乙烯模型时", must=("乙烯", "C", "H", "?"))
    add("cnk_h037_q2", sodium_ethanol(), "少量钠放入乙醇中", must=("钠", "乙醇", "?"))
    add("cnk_h037_q3", acetic_carbonate(), "乙酸与碳酸钠反应放出气体", must=("乙酸", "碳酸钠", "?"))
    add("cnk_h037_q4", ester_setup_b2(), "做乙醇与乙酸的酯化时", must=("乙醇", "乙酸", "浓硫酸", "加热", "接收液", "?"))

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

    add("cnk_h043_q1", delta_h_negative(), "一个反应的焓变小于零", must=("反应物", "生成物", "焓变小于 0", "能量", "?"))
    add("cnk_h046_q1", temp_rate_curve(), "升高温度时，化学反应速率通常会", must=("温度", "速率", "?"))
    add("cnk_h046_q4", catalyst_barrier(), "加入催化剂后，正确的是", must=("活化能", "无催化剂", "有催化剂", "?"))
    add("cnk_h047_q4", catalyst_plateau(), "只加入催化剂", must=("无催化剂", "有催化剂", "浓度", "时间", "?"))
    add("cnk_h048_q2", quadrant_signs(), "焓变小于零、熵变大于零", must=("焓变", "熵变", "焓变小于 0", "熵变大于 0", "?"))
    add("cnk_h048_q4", tds_bars(), "气体分子数明显增多", must=("吸热", "气体", "熵变", "?"))
    add("cnk_h049_q1", conc_disturb(), "增大反应物浓度", must=("反应物", "生成物", "浓度", "时间", "?"))
    add("cnk_h051_q3", heat_color(), "颜色向生成物一侧变化", must=("升温", "生成物", "吸热", "?"))
    add("cnk_h052_q3", acetate_add(), "加入少量醋酸钠固体", must=("醋酸", "醋酸根", "醋酸钠", "H+", "?"))
    add("cnk_h052_q4", acetic_dilution(), "把醋酸溶液加水稀释", must=("醋酸", "加水", "?"))
    add("cnk_h053_q4", acid_kw(), "向纯水中加入少量强酸", must=("纯水", "强酸", "H+", "OH-", "离子积", "?"))
    add("cnk_h054_q1", ammonium_ions(), "氯化铵溶液常显酸性", must=("氯化铵", "铵根", "H+", "?"))
    add("cnk_h054_q2", acetate_hydro(), "醋酸钠溶液常显", must=("醋酸钠", "醋酸根", "OH-", "?"))
    add("cnk_h055_q2", common_ion_add(), "含相同离子的可溶盐", must=("难溶盐", "可溶盐", "相同离子", "?"))
    add("cnk_h056_q4", silver_chloride_hcl(), "氯化银的沉淀溶解平衡", must=("氯化银", "浓盐酸", "氯离子", "?"))
    add("cnk_h057_q3", near_endpoint(), "接近终点时，标准溶液应当", must=("滴定管", "锥形瓶", "标准溶液", "?"))
    add("cnk_h058_q4", ferric_colloid(), "得到氢氧化铁胶体", must=("氯化铁", "加热", "?"))
    add("cnk_h060_q2", positive_electrode(), "与电源正极相连的电极是", must=("电源", "+", "?"))
    add("cnk_h061_q1", moist_iron(), "铁在中性潮湿空气中腐蚀", must=("铁", "水", "空气", "?"))
    add("cnk_h061_q2", zinc_on_iron(), "锌先被腐蚀", must=("锌", "铁", "e-", "?"))
    add("cnk_h062_q4", zn_cu_modes(), "铜极接到电源正极", must=("锌", "铜", "原电池", "电源", "+", "e-", "?"))
    add("cnk_h063_q3", plating_anode(), "铜阳极的作用是", must=("铜", "工件", "电源", "铜离子", "+", "?"))

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

    add("cnk_h066_q2", sublevel_order(), "在一个能层里，能量通常由低到高", must=("ns", "np", "nd", "nf", "能量", "同一能层", "?"))
    add("cnk_h067_q1", first_ie(), "第一电离能指的是", must=("气态", "基态", "原子", "e-", "能量", "第一", "?"))
    add("cnk_h067_q3", ie_period_trend(), "第一电离能的总趋势", must=("第一电离能", "从左到右", "稀有气体除外", "同周期", "?"))
    add("cnk_h068_q3", na_ne_valence(), "钠比氖更容易失去一个电子", must=("钠", "氖", "最外层", "?"))
    add("cnk_h069_q1", orbital_share(), "共价键是", must=("轨道重叠", "共用电子对", "?"))
    add("cnk_h069_q2", bond_length_nuclei(), "键长通常指", must=("核间距", "核", "?"))
    add("cnk_h070_q1", methane_vsepr(), "甲烷分子的空间构型是", must=("甲烷", "C", "H", "价层电子对", "?"))
    add("cnk_h070_q3", water_vsepr(), "用水分子的价层电子对互斥模型判断", must=("孤对", "O", "H", "价层电子对", "?"))
    add("cnk_h071_q1", polar_centers(), "极性分子的特点是", must=("正电荷中心", "负电荷中心", "?"))
    add("cnk_h071_q3", co2_dipoles(), "二氧化碳是直线形对称分子", must=("偶极", "对称", "C", "O", "?"))
    add("cnk_h073_q2", cell_from_lattice(), "晶胞指的是", must=("晶胞", "晶格", "?"))
    add("cnk_h075_q1", metal_electron_sea(), "金属原子（或离子）靠什么结合", must=("e-", "金属离子", "?"))
    add("cnk_h075_q2", nacl_lattice(), "氯化钠晶体属于", must=("Na+", "Cl−", "氯化钠", "?"))
    add("cnk_h075_q4", metal_slide_conduct(), "金属具有延展性和导电性", must=("电子", "滑动", "导电", "延展", "?"))
    add("cnk_h076_q1", coord_donate(), "中心原子（或离子）与配体之间", must=("配体", "中心离子", "空轨道", "?"))
    add("cnk_h078_q2", cuso4_ammonia(), "向硫酸铜溶液中加入过量氨水", must=("硫酸铜", "氨水", "过量", "深蓝", "?"))

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

    add("cnk_h080_q3", c4h10_isomers(), "分子式为 C4H10 的饱和链烃", must=("正丁烷", "异丁烷", ">4</text>", ">10</text>", "?"))
    add("cnk_h081_q2", distill_setup(), "蒸馏适用于分离的混合物通常是", must=("加热", "进水", "出水", "接收", "?"))
    add("cnk_h083_q1", alkane_chain(), "烷烃分子中，碳原子之间只含有", must=("烷烃", "C", "?"))
    add("cnk_h083_q4", methane_light_cl(), "甲烷与氯气在光照下主要发生的反应类型是", must=("甲烷", "氯气", "光照", "HCl", "?"))
    add("cnk_h084_q4", unsaturation_three(), "比较乙烷、乙烯和乙炔", ("2", "4", "6"), must=("C", "H", ">2</text>", ">4</text>", ">6</text>", "?"))
    add("cnk_h085_q3", benzene_febr(), "苯与液溴在铁或溴化铁催化下", must=("苯", "液溴", "铁或溴化铁", "?"))
    add("cnk_h085_q4", toluene_benzene_kmno(), "甲苯能使酸性高锰酸钾溶液褪色", must=("甲苯", "苯", "酸性高锰酸钾", "褪色", "?"))
    add("cnk_h087_q1", halo_cx(), "卤代烃分子中的官能团是", must=("卤代烃", "C", "X", "?"))
    add("cnk_h087_q2", bromoethane_water(), "溴乙烷在氢氧化钠水溶液中加热", must=("溴乙烷", "氢氧化钠水溶液", "加热", "?"))
    add("cnk_h088_q2", phenol_fecl3(), "苯酚溶液中滴加三氯化铁溶液", must=("苯酚", "三氯化铁", "?"))
    add("cnk_h089_q1", acetaldehyde_fg(), "乙醛分子中的官能团是", must=("乙醛", "C", "O", "H", "?"))
    add("cnk_h089_q4", aldehyde_plus_h2(), "乙醛催化加氢的主要产物是", must=("乙醛", "催化", "H", "?"))
    add("cnk_h090_q1", acetic_fg(), "乙酸分子中的官能团是", must=("乙酸", "C", "O", "H", "?"))
    add("cnk_h090_q4", ester_naoh(), "乙酸乙酯在氢氧化钠溶液中加热", must=("乙酸乙酯", "氢氧化钠溶液", "加热", "?"))
    add("cnk_h091_q2", route_br_ethanol(), "由溴乙烷制备乙醇", must=("溴乙烷", "乙醇", "条件", "?"))
    add("cnk_h091_q3", route_ethanol_ester(), "由乙醇制备乙酸乙酯", must=("乙醇", "乙酸乙酯", "路线", "?"))
    add("cnk_h091_q4", route_br_ethene(), "由溴乙烷制备乙烯", must=("溴乙烷", "乙烯", "条件", "?"))
    add("cnk_h094_q4", acetic_phenol_pair(), "要区分乙酸和苯酚", must=("乙酸", "苯酚", "对照", "?"))
    add("cnk_h096_q2", amino_both(), "氨基酸分子中通常同时含有", ("2",), must=("氨基酸", "-NH", "-COOH", ">2</text>", "?"))
    add("cnk_h097_q2", nucleotide_parts(), "一个核苷酸通常由哪三部分组成", must=("磷酸", "糖", "碱基", "核苷酸", "?"))
    add("cnk_h097_q3", dna_rna_pair(), "DNA 与 RNA 的一个差别是", must=("DNA", "RNA", "脱氧核糖", "核糖", "碱基", "?"))
    add("cnk_h099_q3", sucrose_then_silver(), "蔗糖本身通常不能发生银镜反应", must=("蔗糖", "水解", "银镜", "?"))
    add("cnk_h099_q4", starch_iodine_two(), "淀粉溶液加碘水变蓝", must=("淀粉", "碘水", "蓝色", "水解较完全", "消失", "?"))
    add("cnk_h100_q2", cond_vs_add(), "缩聚反应与加聚反应的一个重要差别是", must=("缩聚", "加聚", "小分子", "?"))
    add("cnk_h101_q2", linear_heat(), "线型高分子加热可以软化", must=("线型", "加热", "冷却", "?"))
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
