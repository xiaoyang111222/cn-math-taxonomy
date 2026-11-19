#!/usr/bin/env python3
"""把高中地理（必修第一、二册，选择性必修第一、二、三册）编译进 data/ 下的四个文件。

只清除并重写 cng_h、cgs-hs-2017: 和 geography_senior；初中地理 cng_j、cgs-2022 及其他学科原样保留。
可重复运行。开发期可设 SENIOR_PARTIAL=1，只编译已登记内容的点。

用法：python3 scripts/geo_hs_build.py
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geo_hs_lib import S  # noqa: E402

for _m in ("geo_hs_plan", "geo_hs_std", "geo_hs_b1", "geo_hs_b2", "geo_hs_s1", "geo_hs_s2", "geo_hs_s3"):
    try:
        importlib.import_module(_m)
    except ModuleNotFoundError as e:
        if os.environ.get("SENIOR_PARTIAL") != "1" or e.name != _m:
            raise

import senior_build  # noqa: E402

if __name__ == "__main__":
    sys.exit(senior_build.run(S))
