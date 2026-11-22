#!/usr/bin/env python3
"""把高中思想政治（必修 1–4，选择性必修 1–3）编译进 data/ 下的四个文件。

只清除并重写 cnz_h、czs-hs-2017: 和 politics_senior；其他学科原样保留。
可重复运行。开发期可设 SENIOR_PARTIAL=1，只编译已登记内容的点。

用法：python3 scripts/pol_hs_build.py
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pol_hs_lib import S  # noqa: E402

for _m in ("pol_hs_plan", "pol_hs_std", "pol_hs_b1", "pol_hs_b2", "pol_hs_b3", "pol_hs_b4",
           "pol_hs_s1", "pol_hs_s2", "pol_hs_s3"):
    try:
        importlib.import_module(_m)
    except ModuleNotFoundError as e:
        if os.environ.get("SENIOR_PARTIAL") != "1" or e.name != _m:
            raise

import senior_build  # noqa: E402

if __name__ == "__main__":
    sys.exit(senior_build.run(S))
