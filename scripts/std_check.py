# -*- coding: utf-8 -*-
"""课标待核清尾（2026-11-22）：把 std_check_20261122.json 的核对结果覆盖到各构建脚本生成的课标条目上。

覆盖 page_or_ref、text_status，以及与课标有实质出入而按课标原文改写的 text。
各学科构建脚本在生成课标条目之后调用 apply_check(items)，重跑构建不会把这些条目回退为「待核」。
"""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "std_check_20261122.json")
with open(_PATH, encoding="utf-8") as _f:
    CHECK = json.load(_f)


def apply_check(items):
    for it in items:
        c = CHECK.get(it["id"])
        if c is None:
            continue
        it["text"] = c["text"]
        it["page_or_ref"] = c["page_or_ref"]
        it["text_status"] = c["text_status"]
    return items
