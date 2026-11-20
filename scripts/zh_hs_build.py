#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把高中语文（必修上、下，选择性必修上、中、下）编译进 data/ 下的四个文件。

只清除并重写 cnc_h、ccs-hs-2017: 和 chinese_senior；小学语文 cnc_p、初中语文 cnc_j 及其他学科原样保留。
可重复运行。

用法：python3 scripts/zh_hs_build.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zh_hs_lib import S  # noqa: E402
import zh_hs_plan  # noqa: E402,F401
import zh_hs_std  # noqa: E402,F401
import zh_hs_fill  # noqa: E402,F401
import senior_build  # noqa: E402

if __name__ == "__main__":
    sys.exit(senior_build.run(S))
