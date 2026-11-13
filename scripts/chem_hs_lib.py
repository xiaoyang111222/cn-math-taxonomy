# -*- coding: utf-8 -*-
"""高中化学草稿的登记和题目检查。章节、名称从 chem_hs_plan.py 取（含必修一、二）。

题目规则与初中化学一致：每点 4 题，难度 basic、basic、standard、challenge。
q1 必须是 basic 选择题。禁用词与 chem_lib.check_question 相同。
"""
from __future__ import annotations

import json
import re

from chem_lib import DOMAINS, _BANNED_COPY, _BANNED_META, _BANNED_START, _NUM_RE
from chem_hs_plan import ORDER, PLAN, PLAN_BY_KEY  # noqa: F401

HS = {}
TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
DIFFS = ("basic", "basic", "standard", "challenge")
NOTE = "公开转述，本图谱自编号，未逐页核对教育部 PDF。"


def C(diff, prompt, right, wrongs, expl):
    return {
        "kind": "choice", "diff": diff, "prompt": str(prompt).strip(),
        "right": str(right).strip(), "wrongs": [str(w).strip() for w in wrongs],
        "expl": str(expl).strip(),
    }


def N(diff, prompt, answer, verify, expl):
    return {
        "kind": "numeric", "diff": diff, "prompt": str(prompt).strip(),
        "answer": str(answer).strip(), "verify": str(verify).strip(),
        "expl": str(expl).strip(),
    }


def check_question(key, q):
    if _BANNED_START.match(q["prompt"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["prompt"][:20]))
    blob = "\n".join([q["prompt"], q["expl"], q.get("right", ""), q.get("answer", "")] + q.get("wrongs", []))
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语：%s" % (key, q["prompt"][:24]))
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    if not q["expl"]:
        raise SystemExit("%s 缺少解析" % key)
    if q["kind"] == "choice":
        if len(q["wrongs"]) != 3:
            raise SystemExit("%s 干扰项必须是 3 个：%s" % (key, q["prompt"][:30]))
        opts = [q["right"]] + q["wrongs"]
        if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
            raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    elif q["kind"] == "numeric":
        if not _NUM_RE.match(q["answer"].replace(" ", "")):
            raise SystemExit("%s 数值题答案不是数：%s" % (key, q["answer"]))
        if not q.get("verify"):
            raise SystemExit("%s 数值题缺少 verify" % key)
    else:
        raise SystemExit("%s 题型非法：%s" % (key, q.get("kind")))


def T(key, domain, typ, desc, mastery, std, pre, qs):
    if key not in PLAN_BY_KEY:
        raise SystemExit("chem_hs_plan.py 里没有这个 key：%s" % key)
    if key in HS:
        raise SystemExit("重复登记：%s" % key)
    if domain not in DOMAINS:
        raise SystemExit("%s 领域不在初中化学五个领域里：%s" % (key, domain))
    if typ not in TYPES:
        raise SystemExit("%s type 非法：%s" % (key, typ))
    if not (2 <= len(mastery) <= 3) or not all(str(x).strip() for x in mastery):
        raise SystemExit("%s mastery 必须是 2–3 条" % key)
    if len(qs) != 4:
        raise SystemExit("%s 需要恰好 4 题" % key)
    for q, diff in zip(qs, DIFFS):
        if q["diff"] != diff:
            raise SystemExit("%s 难度顺序必须是 basic、basic、standard、challenge" % key)
        check_question(key, q)
    if qs[0]["kind"] != "choice":
        raise SystemExit("%s 第 1 题必须是选择题" % key)
    if not std or len(std) > 3:
        raise SystemExit("%s 课标引用必须是 1–3 条" % key)
    HS[key] = {
        "key": key, "domain": domain, "type": typ, "description": str(desc).strip(),
        "mastery": [str(x).strip() for x in mastery], "std": list(std),
        "pre": list(pre), "qs": list(qs),
    }
    return HS[key]


def choice_verify(text):
    return json.dumps(text, ensure_ascii=False)
