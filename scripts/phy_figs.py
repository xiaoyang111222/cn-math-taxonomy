#!/usr/bin/env python3
"""给初中物理（topicId 以 cnp_ 开头且非 cnp_h）里最需要看示意图的题写入内联 SVG。

只改下面登记的题，大约 48 道（含原有 6 道），不给全部题目硬配。可重复运行：
  python3 scripts/phy_figs.py
  python3 scripts/phy_figs.py --preview /tmp/phy-j-figs.html

图只用 currentColor，不引用外网。正确选项的整句不写入图中。
图里的阿拉伯数字必须能在该题题干或选项里找到。
若标出名称或结论就会直接泄题，图上用「?」或省略。
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fig_draw as D  # noqa: E402
from check_figures import figure_problems  # noqa: E402
from phy_fig_lib import Fig, Slope, axes, n  # noqa: E402

ROOT = os.path.dirname(HERE)
QUESTIONS = os.path.join(ROOT, "data", "questions.json")


def ask(f, x, y, r=12):
    f.ring(x, y, r, 2.1)
    f.t(x, y + 5, "?", 16)


def finish(f, title, note="示意图"):
    if title:
        f.t(f.w / 2, 18, title, 15)
    if note:
        f.t(f.w / 2, f.h - 10, note, 12)
    return f.svg()


def convex_lens(f, cx, cy, hh=70, bulge=16):
    top, bot = cy - hh / 2, cy + hh / 2
    d = "M %s %s Q %s %s %s %s Q %s %s %s %s Z" % (
        n(cx), n(top), n(cx + bulge), n(cy), n(cx), n(bot),
        n(cx - bulge), n(cy), n(cx), n(top))
    f.raw('<path d="%s" %s/>' % (d, D.face(0.10)))
    f.raw('<path d="%s" %s/>' % (d, D.edge(2.1)))


def concave_lens(f, cx, cy, hh=70, dent=10, thick=18):
    top, bot = cy - hh / 2, cy + hh / 2
    d = ("M %s %s L %s %s Q %s %s %s %s L %s %s L %s %s Q %s %s %s %s Z" % (
        n(cx - thick), n(top), n(cx + thick), n(top),
        n(cx + thick - dent), n(cy), n(cx + thick), n(bot),
        n(cx - thick), n(bot), n(cx - thick), n(bot),
        n(cx - thick + dent), n(cy), n(cx - thick), n(top)))
    f.raw('<path d="%s" %s/>' % (d, D.face(0.10)))
    f.raw('<path d="%s" %s/>' % (d, D.edge(2.1)))


def lamp(f, x, y, r=12, lab=None):
    f.ring(x, y, r, 2.0)
    s = r * 0.62
    f.thin((x - s, y - s), (x + s, y + s), 1.5)
    f.thin((x - s, y + s), (x + s, y - s), 1.5)
    if lab:
        f.t(x, y + r + 16, lab, 13)


def resistor(f, x, y, w=44, h=18, lab=None):
    f.box(x, y - h / 2, w, h, lab, 13, 0.08, 2.0)


def meter(f, x, y, lab, r=13):
    f.ring(x, y, r, 2.0)
    f.t(x, y + 5, lab, 14)


def battery_v(f, x, y):
    """底边上的电池：左侧长线为正极，右侧短粗线为负极。"""
    f.ln((x, y - 16), (x, y + 16), 2.0)
    f.ln((x + 12, y - 9), (x + 12, y + 9), 3.6)


def switch_open(f, x, y, w=28):
    f.dot(x, y, 3)
    f.ln((x, y), (x + w * 0.78, y - 10), 2.0)
    f.dot(x + w, y, 3)


# ---------------------------------------------------------------- 已有 6 道


def reflect_30():
    """入射光线与镜面成 30°，法线竖直。不标反射角。"""
    f = Fig(360, 210)
    f.ln((40, 160), (320, 160), 3.0)
    f.t(330, 164, "镜面", 13, "start")
    f.thin((180, 36), (180, 160), 1.6, dash=True)
    f.t(192, 48, "N", 15, "start")
    a, o = (70, 96), (180, 160)
    b = (290, 96)
    f.arr(a, o, 2.4)
    f.arr(o, b, 2.4)
    f.t(56, 92, "A", 15, "end")
    f.t(180, 182, "O", 15)
    f.angle(a, o, (40, 160), r=28, label="30°", size=13, extra=14)
    ask(f, 300, 50)
    return finish(f, "光的反射")


def cup_balance():
    f = Fig(340, 210)
    f.ground(30, 310, 150)
    f.box(145, 108, 50, 42)
    f.dot(170, 129, 3)
    f.arr((170, 129), (170, 42), 2.4)
    f.arr((170, 129), (170, 188), 2.4)
    f.t(186, 50, "F", 15, "start")
    f.t(186, 186, "G", 15, "start")
    f.t(170, 102, "杯子", 13)
    return finish(f, "杯子受力")


def lever_balance():
    f = Fig(400, 220)
    f.ln((30, 100), (370, 100), 4.2)
    f.poly([(190, 102), (176, 138), (204, 138)], 0.16, 2.0)
    f.t(190, 156, "O", 14)
    f.ln((60, 100), (60, 148), 2.0)
    f.box(46, 148, 28, 26)
    f.arr((340, 100), (340, 168), 2.3)
    f.t(48, 198, "G = 60 N", 13, "start")
    f.t(352, 164, "F", 15, "start")
    f.dim((60, 62), (190, 62), "0.4 m", lp=(0, -8))
    f.dim((190, 62), (340, 62), "1.2 m", lp=(0, -8))
    return finish(f, "杠杆平衡")


def series_circuit():
    """串联：电源、R₁、R₂，电流表在干路，电压表并在 R₁ 两端。"""
    f = Fig(400, 230)
    y1, y2 = 70, 168
    x0, x1, x2, x3 = 50, 110, 210, 330
    f.ln((x0, y1), (x1, y1), 2.0)
    resistor(f, x1, y1, 48, 20, "R₁")
    f.ln((x1 + 48, y1), (x2, y1), 2.0)
    resistor(f, x2, y1, 48, 20, "R₂")
    f.ln((x2 + 48, y1), (x3, y1), 2.0)
    f.ln((x3, y1), (x3, 96), 2.0)
    meter(f, x3, 118, "A")
    f.ln((x3, 140), (x3, y2), 2.0)
    f.ln((x3, y2), (x0 + 26, y2), 2.0)
    battery_v(f, x0 + 14, y2)
    f.t(x0 + 20, y2 + 28, "电源", 12)
    f.ln((x0, y2), (x0, y1), 2.0)
    f.ln((x0 + 18, y1), (x0 + 18, 118), 2.0)
    f.ln((x0 + 18, 118), (128, 118), 2.0)
    meter(f, 150, 118, "V")
    f.ln((172, 118), (178, 118), 2.0)
    f.ln((178, 118), (178, y1), 2.0)
    f.dot(x0 + 18, y1, 2.6)
    f.dot(178, y1, 2.6)
    return finish(f, "串联电路")


# ---------------------------------------------------------------- 运动、测量、热学实验


def incline_speed():
    f = Fig(440, 240)
    sl = Slope((40, 188), 18)
    f.poly([sl.P(0, 0), sl.P(300, 0), sl.P(300, -4), sl.P(0, -4)], 0.08, 2.2)
    f.ground(40, 420, 188)
    sl.block(f, 36, 86, 28, "小车", 12)
    f.dot(*sl.P(20, 0), 3.2)
    f.dot(*sl.P(160, 0), 3.2)
    f.dot(*sl.P(300, 0), 3.2)
    f.t(sl.P(160, 0)[0], 208, "0.8 m", 13)
    f.t(sl.P(90, 36)[0], sl.P(90, 36)[1], "前半程 2.5 s", 12)
    f.t(sl.P(250, 28)[0], 48, "全程 4 s", 13)
    f.t(40, 44, "斜面", 13, "start")
    ask(f, 400, 70)
    return finish(f, "测平均速度")


def thermometer():
    """液柱在 0 ℃ 下方第 6 小格。读数用问号。"""
    f = Fig(300, 280)
    x = 130
    f.box(x - 10, 36, 20, 168, None, 12, 0.04, 2.0)
    f.ring(x, 220, 18, 2.0, 0.12)
    f.ln((x - 10, 202), (x - 10, 36), 2.0)
    f.ln((x + 10, 202), (x + 10, 36), 2.0)
    zero_y = 100
    for i in range(-8, 9):
        y = zero_y - i * 8
        w = 14 if i % 5 == 0 else 8
        f.thin((x + 12, y), (x + 12 + w, y), 1.4)
    f.t(x + 40, zero_y + 5, "0 ℃", 14, "start")
    f.box(x - 7, 148, 14, 70, None, 12, 0.18, 0)
    f.t(x - 48, 148, "第 6 小格", 13, "end")
    f.thin((x - 12, 148), (x - 44, 148), 1.3)
    ask(f, 230, 148)
    return finish(f, "温度计")


def melt_graph():
    f = Fig(400, 250)
    ox, oy = 70, 200
    axes(f, ox, oy, 280, 150, "t", "T/℃")
    f.t(ox + 6, oy - 118, "48", 13, "end")
    f.thin((ox, oy - 110), (ox + 250, oy - 110), 1.3, dash=True)
    pts = [(ox + 20, oy - 20), (ox + 80, oy - 110), (ox + 170, oy - 110), (ox + 240, oy - 150)]
    f.path(pts, 2.4)
    f.dim((ox + 80, oy - 40), (ox + 170, oy - 40), "6 min", lp=(0, 16))
    ask(f, 340, 70)
    return finish(f, "熔化图像")


def density_cylinder():
    f = Fig(420, 260)
    def cyl(x, top, h, level, lab, stone=False):
        f.ln((x, top), (x, top + h), 2.1)
        f.ln((x + 50, top), (x + 50, top + h), 2.1)
        f.ln((x, top + h), (x + 50, top + h), 2.1)
        ly = top + h - level
        f.box(x + 3, ly, 44, level, None, 12, 0.10, 0)
        f.thin((x + 3, ly), (x + 47, ly), 1.3)
        f.t(x + 25, top + h + 20, lab, 13)
        if stone:
            f.box(x + 14, top + h - 28, 22, 18, None, 12, 0.18, 1.8)
            f.t(x + 25, top + h - 34, "石块", 12)
    cyl(70, 50, 150, 70, "40 mL")
    cyl(220, 50, 150, 110, "60 mL", stone=True)
    f.t(340, 90, "m = 52 g", 14, "start")
    ask(f, 360, 140)
    return finish(f, "测石块密度")


def spring_hang():
    f = Fig(400, 250)
    f.ceiling(40, 360, 36)
    f.spring((110, 36), (110, 116), turns=6, lead=8)
    f.dim((78, 36), (78, 116), "10 cm", lp=(-22, 5))
    f.t(110, 138, "原长", 13)
    f.spring((250, 36), (250, 132), turns=7, lead=8)
    f.box(232, 132, 36, 28, "2 N", 13)
    f.dim((286, 36), (286, 132), "12 cm", lp=(22, 5))
    f.t(250, 188, "挂 2 N", 13)
    f.t(340, 90, "挂 5 N", 13, "start")
    ask(f, 360, 130)
    return finish(f, "弹簧伸长")


# ---------------------------------------------------------------- 光学


def pinhole():
    f = Fig(420, 230)
    f.arr((50, 70), (50, 150), 2.0)
    f.t(50, 64, "物体", 13)
    f.ln((180, 40), (180, 100), 2.4)
    f.ln((180, 112), (180, 190), 2.4)
    f.t(180, 210, "小孔", 13)
    f.ln((320, 48), (320, 182), 2.2)
    f.t(348, 70, "光屏", 13, "start")
    f.thin((50, 70), (180, 106), 1.4)
    f.thin((50, 150), (180, 106), 1.4)
    f.thin((180, 106), (320, 70), 1.4, dash=True)
    f.thin((180, 106), (320, 150), 1.4, dash=True)
    f.t(320, 44, "像", 13)
    ask(f, 380, 120)
    return finish(f, "小孔成像")


def paper_fold():
    f = Fig(400, 230)
    f.ln((40, 170), (280, 170), 3.0)
    f.t(40, 188, "镜面", 13, "start")
    f.thin((160, 50), (160, 170), 1.5, dash=True)
    f.arr((60, 90), (160, 170), 2.3)
    f.t(52, 86, "入射", 13, "end")
    f.box(148, 48, 70, 88, "纸板 F", 13, 0.06, 1.8)
    f.thin((218, 70), (268, 40), 1.8, dash=True)
    f.t(280, 44, "向后折", 13, "start")
    ask(f, 330, 120)
    return finish(f, "探究反射")


def plane_mirror():
    f = Fig(420, 230)
    f.ln((210, 40), (210, 180), 2.6)
    f.t(222, 54, "平面镜", 13, "start")
    f.box(70, 90, 36, 70, "人", 14)
    f.box(314, 90, 36, 70, "像", 14, 0.05, 1.8)
    f.thin((314, 90), (350, 90), 1.3, dash=True)
    f.thin((314, 160), (350, 160), 1.3, dash=True)
    f.thin((350, 90), (350, 160), 1.3, dash=True)
    f.dim((106, 200), (210, 200), "2 m", lp=(0, 16))
    f.dim((210, 200), (314, 200), "2 m", lp=(0, 16))
    ask(f, 370, 70)
    return finish(f, "平面镜成像")


def glass_plate():
    f = Fig(420, 230)
    f.ln((210, 44), (210, 176), 2.2)
    f.t(222, 56, "玻璃板", 13, "start")
    f.box(88, 96, 28, 56, "蜡烛", 12)
    f.box(304, 96, 28, 56, None, 12, 0.04, 1.6)
    f.t(318, 88, "像", 13)
    f.t(70, 176, "物", 13, "start")
    ask(f, 360, 80)
    return finish(f, "玻璃板代替平面镜")


def refraction():
    f = Fig(400, 240)
    f.ln((40, 120), (360, 120), 2.4)
    f.t(48, 52, "空气", 14, "start")
    f.t(48, 196, "水", 14, "start")
    f.box(40, 120, 320, 70, None, 12, 0.06, 0)
    f.thin((200, 40), (200, 200), 1.5, dash=True)
    f.t(214, 52, "法线", 13, "start")
    f.arr((80, 50), (200, 120), 2.3)
    f.arr((200, 120), (250, 200), 2.3)
    f.t(86, 46, "入射", 13, "start")
    f.t(262, 196, "折射", 13, "start")
    ask(f, 330, 70)
    return finish(f, "光的折射")


def spear_fish():
    f = Fig(400, 240)
    f.ln((30, 90), (370, 90), 2.2)
    f.t(40, 50, "空气", 13, "start")
    f.t(40, 210, "水", 13, "start")
    f.box(30, 90, 340, 110, None, 12, 0.06, 0)
    f.t(250, 126, "看到的鱼", 13)
    f.ring(250, 132, 10, 1.6, 0.08)
    f.thin((250, 142), (250, 176), 1.4, dash=True)
    f.ring(250, 186, 10, 1.8)
    f.t(268, 190, "?", 16, "start")
    f.t(80, 70, "叉", 13, "start")
    f.arr((90, 70), (160, 90), 2.0)
    ask(f, 340, 50)
    return finish(f, "叉鱼")


def convex_converge():
    """平行光入射，出射侧用问号，不画出交于焦点。"""
    f = Fig(400, 230)
    f.thin((40, 120), (360, 120), 1.4, dash=True)
    f.t(40, 112, "主光轴", 12, "start")
    convex_lens(f, 200, 120, 90, 18)
    f.t(200, 40, "凸透镜", 13)
    for y in (80, 120, 160):
        f.arr((50, y), (176, y), 2.0)
    ask(f, 280, 120)
    f.dot(310, 120, 3.4)
    f.t(324, 124, "F", 14, "start")
    return finish(f, "凸透镜对光的作用")


def focal_spot():
    f = Fig(400, 230)
    f.thin((40, 120), (360, 120), 1.4, dash=True)
    convex_lens(f, 140, 120, 90, 18)
    f.t(140, 44, "凸透镜", 13)
    for y in (86, 120, 154):
        f.arr((40, y), (122, y), 1.8)
        f.arr((158, y if y == 120 else 120 + (y - 120) * 0.15), (230, 120), 1.8)
    f.ln((230, 70), (230, 170), 2.2)
    f.t(246, 86, "光斑", 13, "start")
    f.dim((140, 196), (230, 196), "?", lp=(0, 16))
    ask(f, 330, 70)
    return finish(f, "测焦距")


def lens_setup(u_lab, title):
    f = Fig(440, 230)
    ox, cy = 40, 120
    f.thin((ox, cy), (410, cy), 1.4, dash=True)
    lx = 200
    convex_lens(f, lx, cy, 86, 16)
    f.t(lx, 44, "凸透镜", 13)
    f.dot(lx - 40, cy, 3.2)
    f.t(lx - 40, cy + 22, "F", 13)
    f.dot(lx + 40, cy, 3.2)
    f.t(lx + 40, cy + 22, "F", 13)
    f.arr((lx - 120, 70), (lx - 120, 170), 2.0)
    f.t(lx - 120, 62, "物", 13)
    f.dim((lx - 120, 196), (lx, 196), u_lab, lp=(0, 16))
    f.t(lx + 90, 70, "光屏", 13, "start")
    f.ln((lx + 130, 70), (lx + 130, 170), 2.0)
    ask(f, 380, 80)
    return finish(f, title)


def lens_u30():
    return lens_setup("30 cm", "凸透镜成像")


def lens_u15():
    return lens_setup("15 cm", "凸透镜成像")


def myopia():
    f = Fig(420, 230)
    f.ring(150, 120, 56, 2.2)
    f.ring(118, 120, 14, 1.8, 0.10)
    f.t(150, 44, "眼睛", 13)
    f.arr((40, 100), (104, 114), 1.8)
    f.arr((40, 140), (104, 126), 1.8)
    f.dot(168, 120, 3.4)
    f.t(176, 112, "像", 13, "start")
    f.thin((206, 80), (206, 160), 1.5, dash=True)
    f.t(220, 92, "视网膜", 13, "start")
    f.t(300, 80, "矫正", 13)
    ask(f, 300, 120)
    return finish(f, "近视眼")


def hyperopia():
    f = Fig(420, 230)
    f.ring(150, 120, 56, 2.2)
    f.ring(118, 120, 14, 1.8, 0.10)
    f.t(150, 44, "眼睛", 13)
    f.arr((40, 92), (108, 112), 1.8)
    f.arr((40, 148), (108, 128), 1.8)
    f.thin((206, 80), (206, 160), 1.5, dash=True)
    f.t(220, 92, "视网膜", 13, "start")
    ask(f, 250, 120)
    f.t(300, 80, "像的位置", 13)
    return finish(f, "远视眼")


# ---------------------------------------------------------------- 力学：力、压强、浮力、机械


def book_forces():
    f = Fig(360, 230)
    f.ground(40, 320, 160)
    f.box(140, 108, 80, 52, "书", 15)
    f.arr((180, 134), (180, 50), 2.3)
    f.arr((180, 134), (180, 200), 2.3)
    f.arr((180, 160), (180, 200), 2.0)
    f.t(196, 58, "?", 16, "start")
    f.t(70, 100, "桌面", 13, "start")
    ask(f, 300, 80)
    return finish(f, "书的受力")


def friction_pull():
    f = Fig(420, 220)
    f.ground(40, 390, 160)
    f.box(150, 118, 90, 42, "木块", 14)
    f.ln((90, 139), (150, 139), 2.0)
    f.box(48, 124, 44, 30, "测力计", 11)
    f.arr((240, 100), (300, 100), 2.2)
    f.t(270, 88, "匀速", 13)
    ask(f, 350, 80)
    return finish(f, "测滑动摩擦力")


def forces_same():
    f = Fig(380, 200)
    f.dot(80, 110, 4)
    f.arr((80, 110), (180, 110), 2.4)
    f.arr((80, 110), (250, 110), 2.4)
    f.t(150, 96, "3 N", 14)
    f.t(230, 96, "5 N", 14)
    f.t(80, 140, "同一直线、同向", 13, "start")
    ask(f, 310, 80)
    return finish(f, "二力合成")


def forces_opp():
    f = Fig(380, 200)
    f.dot(190, 110, 4)
    f.arr((190, 110), (80, 110), 2.4)
    f.arr((190, 110), (320, 110), 2.4)
    f.t(120, 96, "3 N", 14)
    f.t(270, 96, "5 N", 14)
    f.t(190, 150, "同一直线、反向", 13)
    ask(f, 340, 50)
    return finish(f, "二力合成")


def dam():
    f = Fig(400, 240)
    f.poly([(80, 60), (140, 60), (200, 190), (60, 190)], 0.12, 2.2)
    f.t(120, 50, "坝", 14)
    f.box(200, 100, 160, 90, None, 12, 0.08, 0)
    f.ln((200, 100), (360, 100), 1.6)
    f.t(280, 88, "水面", 13)
    f.t(280, 150, "水", 14)
    f.t(80, 210, "上窄下宽", 13, "start")
    ask(f, 340, 50)
    return finish(f, "拦河大坝")


def pressure_probe():
    f = Fig(400, 240)
    f.box(50, 50, 180, 150, None, 12, 0.06, 2.0)
    f.t(140, 40, "液体", 13)
    f.ring(140, 130, 14, 2.0)
    f.t(140, 134, "探头", 12)
    f.arr((140, 116), (140, 88), 1.8)
    f.arr((154, 130), (182, 130), 1.8)
    f.arr((140, 144), (140, 172), 1.8)
    f.arr((126, 130), (98, 130), 1.8)
    f.box(270, 80, 70, 90, None, 12, 0.04, 2.0)
    f.t(305, 70, "U 形管", 13)
    f.ln((292, 100), (292, 150), 2.0)
    f.ln((318, 110), (318, 150), 2.0)
    f.ln((292, 150), (318, 150), 2.0)
    ask(f, 360, 50)
    return finish(f, "压强计")


def torricelli():
    """水银柱高度用问号，不写 760。"""
    f = Fig(360, 260)
    f.box(70, 180, 180, 40, None, 12, 0.14, 2.0)
    f.t(160, 206, "水银", 13)
    f.ln((150, 50), (150, 200), 2.2)
    f.ln((178, 50), (178, 200), 2.2)
    f.ln((150, 50), (178, 50), 2.2)
    f.box(152, 90, 24, 110, None, 12, 0.16, 0)
    f.t(200, 70, "真空", 13, "start")
    f.dim((200, 90), (200, 180), "?", lp=(16, 5))
    return finish(f, "托里拆利实验")


def airplane_wing():
    f = Fig(420, 230)
    f.raw('<path d="M 80 120 Q 200 70 340 120 Q 200 132 80 120 Z" %s/>' % D.face(0.10))
    f.raw('<path d="M 80 120 Q 200 70 340 120 Q 200 132 80 120 Z" %s/>' % D.edge(2.1))
    f.t(210, 108, "机翼", 13)
    f.arr((70, 70), (150, 70), 1.8)
    f.arr((160, 70), (240, 70), 1.8)
    f.arr((250, 70), (330, 70), 1.8)
    f.t(210, 58, "上方气流", 13)
    f.arr((70, 170), (160, 170), 1.8)
    f.arr((170, 170), (260, 170), 1.8)
    f.t(210, 196, "下方气流", 13)
    ask(f, 370, 90)
    return finish(f, "飞机升力")


def weigh_buoy():
    f = Fig(420, 250)
    f.ceiling(40, 180, 40)
    f.ln((110, 40), (110, 70), 2.0)
    f.box(86, 70, 48, 28, "8 N", 13)
    f.box(86, 98, 48, 36, "物", 13)
    f.t(110, 160, "空气中", 13)
    f.ceiling(230, 390, 40)
    f.ln((310, 40), (310, 70), 2.0)
    f.box(286, 70, 48, 28, "5 N", 13)
    f.box(240, 120, 140, 90, None, 12, 0.08, 2.0)
    f.t(310, 114, "水", 13)
    f.box(292, 132, 36, 30, "物", 12)
    ask(f, 380, 80)
    return finish(f, "称重法测浮力")


def pressure_diff():
    f = Fig(380, 240)
    f.box(80, 50, 180, 160, None, 12, 0.06, 2.0)
    f.t(170, 40, "液体", 13)
    f.box(140, 100, 60, 50, "物", 14)
    f.arr((170, 100), (170, 70), 2.2)
    f.arr((170, 150), (170, 190), 2.2)
    f.t(186, 78, "向下", 12, "start")
    f.t(186, 186, "向上", 12, "start")
    ask(f, 310, 120)
    return finish(f, "浮力的产生")


def hydrometer():
    f = Fig(400, 250)
    def col(x, depth, lab):
        f.box(x, 50, 70, 160, None, 12, 0.06, 2.0)
        f.t(x + 35, 40, lab, 13)
        f.ln((x + 35, 60), (x + 35, 60 + depth), 3.4)
        f.box(x + 27, 60 + depth, 16, 18, None, 12, 0.2, 1.6)
        f.t(x + 35, 226, "密度计", 12)
    col(80, 70, "液体甲")
    col(220, 120, "液体乙")
    ask(f, 350, 90)
    return finish(f, "密度计")


def kinetic_exp():
    f = Fig(440, 230)
    sl = Slope((40, 170), 22)
    f.poly([sl.P(0, 0), sl.P(160, 0), sl.P(160, -3), sl.P(0, -3)], 0.08, 2.1)
    f.ground(40, 420, 170)
    f.ring(*sl.P(40, 16), 10, 2.0, 0.12)
    f.t(sl.P(40, 40)[0], sl.P(40, 40)[1], "小球", 12)
    f.box(240, 148, 36, 22)
    f.box(280, 148, 28, 22)
    f.box(312, 148, 22, 22)
    f.t(290, 196, "木块", 13)
    f.t(120, 50, "不同高度", 13)
    ask(f, 390, 70)
    return finish(f, "探究动能")


def lever_arm():
    f = Fig(400, 230)
    f.ln((50, 130), (350, 90), 3.4)
    f.poly([(160, 122), (148, 158), (176, 154)], 0.16, 2.0)
    f.t(148, 176, "支点", 13)
    f.arr((300, 96), (300, 170), 2.3)
    f.t(314, 160, "力", 13, "start")
    f.thin((162, 126), (300, 126), 1.5, dash=True)
    f.right((300, 126), (162, 126), (300, 170), 12)
    f.t(230, 114, "?", 16)
    return finish(f, "力臂")


def fixed_pulley():
    f = Fig(360, 240)
    f.ceiling(80, 280, 36)
    f.ln((180, 36), (180, 58), 2.0)
    f.ring(180, 78, 20, 2.2)
    f.dot(180, 78, 3)
    f.ln((160, 78), (160, 170), 2.0)
    f.box(144, 170, 32, 28, "旗", 12)
    f.ln((200, 78), (200, 150), 2.0)
    f.arr((200, 150), (200, 190), 2.0)
    f.t(216, 186, "F", 14, "start")
    f.t(180, 48, "?", 16)
    return finish(f, "旗杆上的滑轮")


def movable_pulley():
    f = Fig(360, 250)
    f.ceiling(80, 280, 36)
    f.ln((140, 36), (140, 150), 2.0)
    f.ring(160, 150, 18, 2.2)
    f.dot(160, 150, 3)
    f.ln((160, 168), (160, 190), 2.0)
    f.box(140, 190, 40, 26, "100 N", 12)
    f.ln((180, 150), (180, 80), 2.0)
    f.arr((180, 80), (180, 50), 2.2)
    f.t(196, 60, "F", 14, "start")
    ask(f, 280, 90)
    return finish(f, "动滑轮")


def pulley_group():
    f = Fig(380, 260)
    f.ceiling(70, 300, 36)
    f.ring(150, 70, 16, 2.0)
    f.ring(200, 70, 16, 2.0)
    f.ln((150, 36), (150, 54), 2.0)
    f.ln((200, 36), (200, 54), 2.0)
    f.ring(150, 150, 16, 2.0)
    f.ring(200, 150, 16, 2.0)
    f.ln((175, 166), (175, 186), 2.0)
    f.box(140, 186, 70, 28, "240 N", 13)
    f.t(250, 154, "30 N", 13, "start")
    f.ln((134, 70), (134, 150), 2.0)
    f.ln((166, 70), (166, 150), 2.0)
    f.ln((184, 70), (184, 150), 2.0)
    f.ln((216, 70), (216, 50), 2.0)
    f.arr((216, 50), (216, 36), 2.0)
    f.t(232, 44, "F", 14, "start")
    f.t(70, 110, "3 段", 13, "start")
    ask(f, 320, 90)
    return finish(f, "滑轮组")


def incline_work():
    f = Fig(420, 240)
    sl = Slope((50, 190), 18)
    f.poly([sl.P(0, 0), sl.P(280, 0), (330, 190), (50, 190)], 0.08, 2.2)
    sl.block(f, 120, 180, 30, "箱", 12)
    f.arr(sl.P(100, 16), sl.P(70, 16), 2.2)
    f.t(sl.P(70, 36)[0], sl.P(70, 36)[1], "250 N", 13)
    f.dim((50, 210), (330, 210), "4 m", lp=(0, 16))
    f.dim((340, 190), (340, 190 - 280 * math.sin(math.radians(18))), "1 m", lp=(18, 5))
    f.t(200, 50, "G = 500 N", 13)
    ask(f, 380, 70)
    return finish(f, "斜面")


# ---------------------------------------------------------------- 电路


def parallel_lamps():
    f = Fig(400, 240)
    y1, y2, y3 = 70, 130, 180
    f.ln((60, y1), (60, y3), 2.0)
    f.ln((60, y1), (140, y1), 2.0)
    switch_open(f, 140, y1)
    f.ln((168, y1), (200, y1), 2.0)
    f.ln((200, y1), (200, y3), 2.0)
    f.ln((200, y2), (260, y2), 2.0)
    lamp(f, 290, y2, 14)
    f.ln((304, y2), (340, y2), 2.0)
    f.ln((200, y3), (260, y3), 2.0)
    lamp(f, 290, y3, 14)
    f.ln((304, y3), (340, y3), 2.0)
    f.ln((340, y2), (340, y3), 2.0)
    f.ln((60, y3), (200, y3), 2.0)
    battery_v(f, 80, y3)
    f.t(140, 54, "开关", 12)
    ask(f, 360, 90)
    return finish(f, "两灯一开关")


def ammeter_how():
    f = Fig(400, 220)
    f.ln((50, 90), (110, 90), 2.0)
    battery_v(f, 62, 90)
    f.t(68, 118, "电源", 12)
    f.ln((74, 90), (74, 50), 2.0)
    f.ln((74, 50), (180, 50), 2.0)
    lamp(f, 210, 50, 14, "灯")
    f.ln((224, 50), (300, 50), 2.0)
    f.ln((300, 50), (300, 90), 2.0)
    f.ln((300, 90), (74, 90), 2.0)
    meter(f, 340, 70, "A")
    f.thin((300, 50), (328, 60), 1.3, dash=True)
    f.thin((300, 90), (328, 80), 1.3, dash=True)
    ask(f, 370, 130)
    return finish(f, "电流表接入")


def rheostat():
    f = Fig(400, 220)
    f.box(80, 90, 200, 28, None, 12, 0.08, 2.0)
    f.t(180, 78, "电阻丝", 13)
    f.dot(100, 118, 3)
    f.dot(260, 118, 3)
    f.ln((180, 90), (180, 70), 2.2)
    f.box(168, 52, 24, 18, None, 12, 0.12, 1.8)
    f.t(180, 46, "滑片", 13)
    f.t(100, 150, "接线柱", 12)
    f.t(260, 150, "接线柱", 12)
    ask(f, 330, 80)
    return finish(f, "滑动变阻器")


def ohm_ir():
    f = Fig(420, 240)
    y1, y2 = 70, 170
    f.ln((50, y1), (110, y1), 2.0)
    resistor(f, 110, y1, 50, 20, "5 Ω")
    f.ln((160, y1), (250, y1), 2.0)
    f.box(250, 58, 70, 24, "10 Ω", 13, 0.06, 1.8)
    f.arr((200, 50), (250, 50), 1.8)
    f.t(220, 40, "换", 12)
    f.ln((320, y1), (360, y1), 2.0)
    meter(f, 360, 118, "A")
    f.ln((360, 140), (360, y2), 2.0)
    f.ln((360, y2), (70, y2), 2.0)
    battery_v(f, 80, y2)
    f.ln((50, y2), (50, y1), 2.0)
    meter(f, 135, 118, "V")
    f.ln((135, 70), (135, 105), 1.8)
    f.ln((135, 131), (135, y1), 1.8)
    f.box(200, 150, 70, 24, "变阻器", 12)
    ask(f, 300, 110)
    return finish(f, "探究电流与电阻")


def voltameter():
    f = Fig(400, 230)
    y1, y2 = 70, 170
    f.ln((50, y1), (120, y1), 2.0)
    resistor(f, 120, y1, 50, 20, "R")
    f.ln((170, y1), (300, y1), 2.0)
    f.ln((300, y1), (300, y2), 2.0)
    f.ln((300, y2), (70, y2), 2.0)
    battery_v(f, 80, y2)
    f.ln((50, y2), (50, y1), 2.0)
    meter(f, 340, 90, "V")
    meter(f, 340, 150, "A")
    f.thin((145, y1), (328, 90), 1.3, dash=True)
    f.thin((300, 120), (328, 150), 1.3, dash=True)
    ask(f, 220, 120)
    return finish(f, "伏安法测电阻")


def switch_live():
    f = Fig(400, 230)
    f.t(54, 50, "甲", 14, "start")
    f.t(54, 170, "乙", 14, "start")
    f.ln((110, 50), (250, 50), 2.0)
    f.ln((110, 170), (250, 170), 2.0)
    lamp(f, 280, 110, 16, "灯")
    f.ln((250, 50), (280, 94), 2.0)
    f.ln((250, 170), (280, 126), 2.0)
    f.box(160, 38, 50, 24, "开关", 12)
    ask(f, 340, 50)
    return finish(f, "家庭电路")


# ---------------------------------------------------------------- 电磁


def field_lines():
    f = Fig(400, 230)
    f.box(150, 100, 100, 36, None, 12, 0.12, 2.2)
    f.t(168, 122, "S", 16)
    f.t(232, 122, "N", 16)
    f.curve_arr((250, 100), (300, 60), (250, 118), 1.8)
    f.curve_arr((250, 136), (300, 176), (250, 136), 1.8)
    f.curve_arr((150, 100), (100, 60), (150, 118), 1.8)
    f.curve_arr((150, 136), (100, 176), (150, 136), 1.8)
    ask(f, 330, 80)
    return finish(f, "磁感线")


def ampere_rule():
    f = Fig(400, 230)
    f.box(140, 80, 120, 50, None, 12, 0.08, 2.1)
    for x in range(150, 250, 16):
        f.thin((x, 80), (x, 130), 1.4)
    f.t(200, 70, "螺线管", 13)
    f.arr((140, 90), (120, 90), 1.8)
    f.arr((260, 120), (280, 120), 1.8)
    f.t(110, 86, "电流", 12, "end")
    f.t(130, 160, "?", 16)
    f.t(270, 160, "?", 16)
    f.t(200, 180, "N 极", 13)
    return finish(f, "安培定则")


def induction():
    f = Fig(420, 230)
    f.box(70, 80, 36, 90, "N", 14, 0.10, 2.0)
    f.box(250, 80, 36, 90, "S", 14, 0.10, 2.0)
    f.ln((106, 100), (250, 100), 1.5, dash=True)
    f.ln((106, 125), (250, 125), 1.5, dash=True)
    f.ln((106, 150), (250, 150), 1.5, dash=True)
    f.ln((160, 70), (160, 180), 2.4)
    f.t(176, 70, "导体", 13, "start")
    f.arr((160, 70), (210, 70), 2.2)
    f.t(220, 66, "运动", 13, "start")
    f.ring(340, 125, 16, 2.0)
    f.t(340, 130, "G", 14)
    f.thin((160, 180), (340, 141), 1.4)
    ask(f, 340, 70)
    return finish(f, "电磁感应")


def fiber():
    f = Fig(420, 210)
    f.ln((50, 70), (370, 70), 2.0)
    f.ln((50, 130), (370, 130), 2.0)
    f.t(60, 54, "光纤", 13, "start")
    f.arr((40, 100), (70, 100), 2.0)
    f.t(40, 90, "激光", 13, "start")
    ask(f, 200, 100)
    f.t(300, 100, "?", 16)
    return finish(f, "光纤通信")


# ---------------------------------------------------------------- 登记、检查、写入


def catalog():
    """(题号, svg, 题干里必须有的片段, 额外允许的数字, 图里必须有的文字)。"""
    D._ids = 0
    rows = []

    def add(qid, drawing, expect, extra=(), must=()):
        rows.append((qid, drawing, expect, set(extra), tuple(must)))

    # 已有 6 道
    add("cnp_016_q3", reflect_30(), "入射光线 AO 与镜面的夹角是 30°", must=("A", "O", "30°"))
    add("cnp_033_q2", cup_balance(), "杯子静止在水平桌面上", must=("F", "G"))
    add("cnp_049_q3", lever_balance(), "轻质杠杆在水平位置平衡", must=("60 N", "0.4 m", "1.2 m", "O"))
    add("cnp_065_q4", series_circuit(), "电压表测量的是哪一部分的电压", must=("R₁", "R₂", "V", "A"))
    add("cnp_066_q3", series_circuit(), "电源电压 6 V，电压表示数为 2.5 V", must=("R₁", "R₂", "V"))
    add("cnp_073_q2", series_circuit(), "R₁ = 10 Ω，R₂ = 20 Ω，电源电压 6 V", must=("R₁", "R₂", "A"))

    # 实验与测量
    add("cnp_004_q3", incline_speed(), "小车从斜面顶端滑到底端", must=("小车", "0.8 m", "4 s", "?"))
    add("cnp_010_q3", thermometer(), "温度计液柱的上表面在 0 ℃ 下方第 6 小格", must=("0 ℃", "第 6 小格", "?"))
    add("cnp_011_q3", melt_graph(), "温度在 48 ℃ 保持不变共 6 min", must=("48", "6 min", "?"))
    add("cnp_027_q2", density_cylinder(), "量筒中原有水 40 mL", must=("40 mL", "60 mL", "52 g", "?"))
    add("cnp_030_q3", spring_hang(), "一根弹簧原长 10 cm", must=("10 cm", "12 cm", "2 N", "5 N", "?"))

    # 光学
    add("cnp_015_q4", pinhole(), "小孔成像中，像的形状由什么决定", must=("物体", "小孔", "像", "?"))
    add("cnp_016_q4", paper_fold(), "把纸板 F 向后折", must=("纸板 F", "镜面", "?"))
    add("cnp_017_q1", plane_mirror(), "人站在平面镜前 2 m 处", must=("平面镜", "2 m", "?"))
    add("cnp_017_q3", glass_plate(), "用玻璃板代替平面镜", must=("玻璃板", "蜡烛", "?"))
    add("cnp_018_q1", refraction(), "光从空气斜射入水中时", must=("空气", "水", "入射", "折射", "?"))
    add("cnp_018_q4", spear_fish(), "渔民用鱼叉叉鱼时", must=("看到的鱼", "?"))
    add("cnp_020_q2", convex_converge(), "平行于主光轴的光经过凸透镜后会怎样", must=("凸透镜", "F", "?"))
    add("cnp_020_q4", focal_spot(), "在离透镜 10 cm 处得到最小最亮的光斑", must=("凸透镜", "光斑", "?"))
    add("cnp_022_q1", lens_u30(), "凸透镜焦距 10 cm，蜡烛放在离透镜 30 cm 处", must=("凸透镜", "30 cm", "F", "?"))
    add("cnp_022_q2", lens_u15(), "凸透镜焦距 10 cm，物体放在离透镜 15 cm 处", must=("凸透镜", "15 cm", "F", "?"))
    add("cnp_023_q1", myopia(), "近视眼应该配戴什么透镜矫正", must=("眼睛", "视网膜", "?"))
    add("cnp_023_q3", hyperopia(), "远视眼看近处物体时，像成在什么位置", must=("眼睛", "视网膜", "?"))

    # 力、压强、浮力、机械
    add("cnp_033_q1", book_forces(), "静止在水平桌面上的书，受到的平衡力是哪一对", must=("书", "桌面", "?"))
    add("cnp_034_q3", friction_pull(), "用弹簧测力计测木块受到的滑动摩擦力", must=("木块", "测力计", "?"))
    add("cnp_035_q1", forces_same(), "同一直线上方向相同的 3 N 和 5 N", must=("3 N", "5 N", "?"))
    add("cnp_035_q2", forces_opp(), "同一直线上方向相反的 3 N 和 5 N", must=("3 N", "5 N", "?"))
    add("cnp_037_q2", dam(), "拦河大坝修成“上窄下宽”", must=("坝", "水面", "?"))
    add("cnp_037_q4", pressure_probe(), "用压强计探究液体压强", must=("探头", "U 形管", "?"))
    add("cnp_038_q3", torricelli(), "1 个标准大气压能支持多高的水银柱", must=("水银", "真空", "?"))
    add("cnp_040_q3", airplane_wing(), "飞机机翼上表面凸起、下表面较平", must=("机翼", "?"))
    add("cnp_041_q2", weigh_buoy(), "一个物体在空气中称重 8 N，浸没在水中时测力计示数为 5 N", must=("8 N", "5 N", "水", "?"))
    add("cnp_041_q4", pressure_diff(), "浮力产生的原因是什么", must=("液体", "物", "?"))
    add("cnp_044_q2", hydrometer(), "密度计在液体中浸入得越深", must=("密度计", "?"))
    add("cnp_047_q3", kinetic_exp(), "让同一小球从斜面不同高度由静止滚下", must=("小球", "木块", "?"))
    add("cnp_049_q2", lever_arm(), "力臂是指什么", must=("支点", "力", "?"))
    add("cnp_051_q1", fixed_pulley(), "旗杆顶部的滑轮是什么滑轮", must=("旗", "?", "F"))
    add("cnp_051_q2", movable_pulley(), "用一个动滑轮匀速提起重 100 N 的物体", must=("100 N", "F", "?"))
    add("cnp_051_q3", pulley_group(), "承担物重的绳子有 3 段", must=("240 N", "30 N", "3 段", "?"))
    add("cnp_052_q3", incline_work(), "用斜面把重 500 N 的箱子推上 1 m 高的平台", must=("4 m", "1 m", "250 N", "500 N", "?"))

    # 电路
    add("cnp_062_q3", parallel_lamps(), "教室里一个开关同时控制两盏日光灯", must=("开关", "?"))
    add("cnp_063_q1", ammeter_how(), "电流表应怎样接入电路", must=("A", "灯", "?"))
    add("cnp_068_q1", rheostat(), "滑动变阻器是通过改变什么来改变电阻的", must=("电阻丝", "滑片", "?"))
    add("cnp_070_q3", ohm_ir(), "把 5 Ω 的电阻换成 10 Ω 后", must=("5 Ω", "10 Ω", "V", "A", "?"))
    add("cnp_072_q2", voltameter(), "伏安法测电阻时，电压表和电流表分别怎样连接", must=("R", "V", "A", "?"))
    add("cnp_079_q4", switch_live(), "控制电灯的开关应接在哪根线上", must=("灯", "开关", "?"))

    # 电磁
    add("cnp_081_q2", field_lines(), "在磁体外部，磁感线的方向是怎样的", must=("N", "S", "?"))
    add("cnp_082_q3", ampere_rule(), "安培定则：用右手握住螺线管", must=("螺线管", "电流", "N 极", "?"))
    add("cnp_086_q3", induction(), "产生感应电流的条件是什么", must=("导体", "运动", "?"))
    add("cnp_089_q2", fiber(), "激光在光导纤维中是怎样传播的", must=("光纤", "激光", "?"))
    return rows


def figure_for(q):
    """按题号取图。题干对不上就停，避免知识点重排后图贴错题。未登记的题保留原有 figure。"""
    hit = _BY_ID.get(q.get("id"))
    if not hit:
        return q.get("figure")
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


def _tw(s, size):
    width = 0.0
    for ch in s:
        width += size if ord(ch) > 127 else size * 0.56
    return width


def overflow_problems(drawing):
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
    if not (48 <= len(items) <= 55):
        problems.append("配图题数 %d 不在 48–55" % len(items))
    for qid, drawing, expect, extra, must in items:
        if qid in seen:
            problems.append("重复登记 " + qid)
        seen.add(qid)
        q = byid.get(qid)
        if not q:
            problems.append("找不到题目 " + qid)
            continue
        tid = str(q.get("topicId") or "")
        if not re.match(r"^cnp_\d", tid) or tid.startswith("cnp_h"):
            problems.append("%s 不是初中物理题" % qid)
        if expect not in q.get("prompt", ""):
            problems.append("%s 题干不含「%s」" % (qid, expect))
        problems += figure_problems(drawing, qid)
        problems += overflow_problems(drawing)
        blob = q.get("prompt", "") + " " + " ".join(
            c.get("text", "") for c in (q.get("choices") or []) if isinstance(c, dict))
        if q.get("answer") and q.get("type") == "numeric":
            blob += " " + str(q.get("answer"))
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
    keep = ("cnp_016_q3", "cnp_033_q2", "cnp_049_q3", "cnp_065_q4", "cnp_066_q3", "cnp_073_q2")
    for qid in keep:
        if qid not in seen:
            problems.append("未保留已有配图 " + qid)
    return problems


def write_preview(items, path, byid):
    parts = [
        "<!DOCTYPE html><meta charset=\"utf-8\"><title>初中物理图示预览</title>",
        "<style>body{margin:0;font-family:sans-serif;background:#fff;color:#162033}",
        ".row{display:flex;gap:12px;flex-wrap:wrap;padding:8px}",
        ".card{width:440px;padding:8px;box-sizing:border-box;border:1px solid #ddd}",
        "svg{width:100%;height:auto;display:block}h2{font-size:13px;margin:4px 0}",
        "p{font-size:12px;margin:2px 0 6px;color:#444}</style><div class=\"row\">",
    ]
    for qid, drawing, _e, _x, _m in items:
        q = byid.get(qid, {})
        prompt = D.esc(q.get("prompt", ""))
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
    print("初中物理带图题：%d（本次新写入或更新 %d）" % (len(items), added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
