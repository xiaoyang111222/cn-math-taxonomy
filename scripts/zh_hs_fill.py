# -*- coding: utf-8 -*-
"""把每课 4 道选择题登记成知识点。"""
from zh_hs_lib import C, T
from zh_hs_rows import ROWS

_DIFFS = ("basic", "basic", "standard", "challenge")

for _r in ROWS:
    _qs = [C(d, q[0], q[1], q[2], q[3]) for d, q in zip(_DIFFS, _r["qs"])]
    T(_r["key"], _r["domain"], "conceptual", _r["desc"], _r["mastery"], [_r["std"]], _r["pre"], _qs)
