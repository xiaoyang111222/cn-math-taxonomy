# -*- coding: utf-8 -*-
"""按册导入课文记录。导入即填充 zh_hs_make.ROWS，顺序就是教学顺序。"""
import zh_hs_b1  # noqa: F401
import zh_hs_b2  # noqa: F401
import zh_hs_s1  # noqa: F401
import zh_hs_s2  # noqa: F401
import zh_hs_s3  # noqa: F401
from zh_hs_make import ROWS

EXPECTED = {10: 39, 11: 31, 12: 21, 13: 26, 14: 27}


def _check():
    from collections import Counter
    grades = Counter(r["grade"] for r in ROWS)
    if grades != Counter(EXPECTED) or len(ROWS) != 144:
        raise SystemExit("高中语文点数不对：%s" % dict(grades))
    keys = [r["key"] for r in ROWS]
    if len(set(keys)) != len(keys):
        raise SystemExit("课序 key 重复")
    seen = set()
    for r in ROWS:
        for edge in r["pre"]:
            ref = edge[0]
            if ref.startswith("J:") or ref.startswith("P:"):
                continue
            if ref not in seen:
                raise SystemExit("%s 的先修 %s 不在它前面" % (r["key"], ref))
        seen.add(r["key"])


_check()
