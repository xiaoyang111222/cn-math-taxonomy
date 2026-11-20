# -*- coding: utf-8 -*-
"""把五册课序登记到语文高中实例。必须先于 zh_hs_fill 导入。"""
from zh_hs_lib import plan
from zh_hs_rows import ROWS

for _g in (10, 11, 12, 13, 14):
    plan(_g, [(r["key"], r["name"], r["tail"], r["domain"]) for r in ROWS if r["grade"] == _g])
