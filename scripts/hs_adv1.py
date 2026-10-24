#!/usr/bin/env python3
"""给高中数学「选择性必修第一册 第一章 空间向量与立体几何」补 advanced 难度题。

背景
    docs/questions.md 定义了三档难度（basic 直接套定义 / standard 课本例题 /
    advanced 综合、多步或易错点）。data/questions.json 里初中已有 advanced，
    高中 1084 题全是 basic 与 standard（各 542 题），高中没有任何一道 advanced。
    原因在生成脚本：scripts/hs_build.py 与 scripts/hs_sel_build.py 都按题号位置
    定档 —— `diff = "basic" if index <= 2 else "standard"`，第三档根本没有位置。

做法
    只为 cnm_h144 – cnm_h164（该章 21 个知识点）各追加一道 <tid>_q5：
    difficulty = "advanced"，type = "numeric"，带 verify 表达式。
    答案由 verify 求值后写入，与 D/E 两轮同一套口径，不引入新的答案来源。

不做什么
    - 不改任何已有题、知识点、先修边、课标引用
    - 不动其他册、其他学科
    - 不把生成的答案当成另一遍独立解题（见 data/second_pass_log.json 的 note）

用法
    python3 scripts/hs_adv1.py
    python3 scripts/validate.py
    python3 scripts/verify_questions.py
    node tests/test_engine.js    # 若改了诊断引擎相关的东西才需要
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verify_questions import safe_eval  # noqa: E402
from hs_sel_build import check_wording, fmt_result  # noqa: E402

QUESTIONS = os.path.join(ROOT, "data", "questions.json")
LOG = os.path.join(ROOT, "data", "second_pass_log.json")


def assert_exact_sqrt(verify: str) -> None:
    """verify 里每个 isqrt(...) 的被开方数必须是完全平方数。

    isqrt 是整数开方（向下取整），isqrt(2) 得 1 而不是 1.414。如果作者本意是
    「根号 2 乘根号 2 等于 2」，写 isqrt(2)*isqrt(2) 会得到 1，答案被悄悄算错，
    而 verify_questions.py 只会照着同一条错误表达式核对，发现不了。
    这里在入口处拦掉。
    """
    i = 0
    while True:
        i = verify.find("isqrt(", i)
        if i < 0:
            return
        depth, j = 0, i + len("isqrt(") - 1
        for j in range(i + len("isqrt(") - 1, len(verify)):
            if verify[j] == "(":
                depth += 1
            elif verify[j] == ")":
                depth -= 1
                if depth == 0:
                    break
        inner = verify[i + len("isqrt("):j]
        value = safe_eval(inner)
        if not isinstance(value, int) or value < 0:
            raise ValueError("isqrt 内不是整数：%s" % inner)
        root = safe_eval("isqrt(%s)" % inner) if "isqrt" in inner else int(value ** 0.5)
        if root * root != value:
            raise ValueError(
                "isqrt 的被开方数不是完全平方数：isqrt(%s)，本意若是根号请改成精确表达式"
                % inner
            )
        i = j + 1

# (topicId, 题干, verify, 解析)
# 全部为该章内的多步计算：先求坐标或模，再代入公式，不能一步读出。
SPECS = [
    ("cnm_h144",
     "a=(2，2，1)。与 a 同向的单位向量的竖坐标是多少？",
     "Fraction(1, isqrt(2*2+2*2+1*1))",
     "|a|=3，同向单位向量等于 a÷3，所以竖坐标是 1/3。"),

    ("cnm_h145",
     "a=(1，2，3)，b=(0，1，−1)，c=(−1，0，2)。2a−3b+c 的竖坐标是多少？",
     "2*3-3*(-1)+2",
     "按分量分别作数乘与加减：竖坐标是 2×3−3×(−1)+2=11。"),

    ("cnm_h146",
     "a=(2，1，2)，b=(1，−2，2)。(a+b)·(a−b) 等于多少？",
     "(2*2+1*1+2*2)-(1*1+(-2)*(-2)+2*2)",
     "(a+b)·(a−b)=|a|²−|b|²=9−9=0，说明这两个向量垂直。"),

    ("cnm_h147",
     "a=(1，2，2)，b=(−2，1，2)。a 与 b 夹角的余弦值是多少？",
     "Fraction(1*(-2)+2*1+2*2, isqrt(1+4+4)*isqrt(4+1+4))",
     "a·b=−2+2+4=4，两向量的模都是 3，所以余弦值等于 4/9。"),

    ("cnm_h148",
     "a=(2，−1，3)，b=(−4，2，k) 共线。k 等于多少？",
     "-2*3",
     "b=−2a，对应分量成同一比例，所以 k=−2×3=−6。"),

    ("cnm_h149",
     "e1、e2、e3 是一组基底，a=3e1−e2+2e3，b=e1+2e2−e3。2a−b 中 e3 的系数是多少？",
     "2*2-(-1)",
     "基底表示唯一，直接合并同类项：e3 的系数是 2×2−(−1)=5。"),

    ("cnm_h150",
     "i、j、k 两两垂直且都是单位向量，a=2i−j+3k，b=i+2j−k。a·b 等于多少？",
     "2*1+(-1)*2+3*(-1)",
     "正交单位基底下数量积等于对应系数相乘再相加：2−2−3=−3。"),

    ("cnm_h151",
     "点 A(1，2，2)，点 B 与 A 关于原点对称。线段 AB 的长度是多少？",
     "2*isqrt(1+4+4)",
     "关于原点对称时 B=−A，AB=2|OA|=2×3=6。"),

    ("cnm_h152",
     "平行四边形 ABCD 中，A(1，0，1)，B(2，1，0)，C(0，2，1)。顶点 D 的竖坐标是多少？",
     "1+1-0",
     "平行四边形满足 D=A+C−B，竖坐标是 1+1−0=2。"),

    ("cnm_h153",
     "a=(1，2，2)，b=(2，−1，2)。a·(a−b) 等于多少？",
     "(1*1+2*2+2*2)-(1*2+2*(-1)+2*2)",
     "a·a=9，a·b=4，所以 a·(a−b)=9−4=5。"),

    ("cnm_h154",
     "A(−1，0，2)，B(2，4，2)，M 是线段 AB 的中点。M 到 A 的距离是多少？",
     "Fraction(isqrt((2-(-1))**2+(4-0)**2+(2-2)**2), 2)",
     "AB=5，中点把线段平分，所以 M 到 A 的距离是 5/2。"),

    ("cnm_h155",
     "直线过 A(1，2，3)、B(3，0，4)。这条直线的一个方向向量的模是多少？",
     "isqrt((3-1)**2+(0-2)**2+(4-3)**2)",
     "取方向向量 AB=(2，−2，1)，模是 3。"),

    ("cnm_h156",
     "平面过 A(1，0，0)、B(0，1，0)、C(0，0，1)。它的一个法向量的三个坐标之和是多少？",
     "1+1+1",
     "平面方程是 x+y+z=1，法向量取 (1，1，1)，坐标之和是 3。"),

    ("cnm_h157",
     "A(1，1，1)，B(2，2，2)，平面以 n=(1，1，−2) 为法向量。向量 AB 与 n 的数量积是多少？",
     "(2-1)*1+(2-1)*1+(2-1)*(-2)",
     "AB=(1，1，1)，与 n 的数量积是 1+1−2=0，说明 AB 与平面平行。"),

    ("cnm_h158",
     "两个平面的法向量分别是 n1=(1，2，−1) 和 n2=(−2，−4，k)，两平面平行。k 等于多少？",
     "-2*(-1)",
     "平行时 n2=−2n1，第三个分量 k=−2×(−1)=2。"),

    ("cnm_h159",
     "直线方向向量 d=(1，2，−1)，平面法向量 n=(2，4，−2)。|d|² 与 |n|² 的比值是多少？",
     "Fraction(1*1+2*2+(-1)*(-1), 2*2+4*4+(-2)*(-2))",
     "|d|²=6，|n|²=24，比值是 1/4；|n|=2|d|，所以这个平面与直线方向重合。"),

    ("cnm_h160",
     "两平面的法向量分别是 n1=(1，2，2)、n2=(2，−3，2)。n1·n2 等于多少？",
     "1*2+2*(-3)+2*2",
     "数量积是 2−6+4=0，说明两平面互相垂直。"),

    ("cnm_h161",
     "两个向量的方向分别是 a=(1，2，2)、b=(2，2，1)。它们所成角的余弦值是多少？",
     "Fraction(1*2+2*2+2*1, isqrt(1+4+4)*isqrt(4+4+1))",
     "a·b=8，两向量的模都是 3，所以余弦值是 8/9。"),

    ("cnm_h162",
     "两个半平面的法向量是 n1=(1，1，0)、n2=(0，1，1)。它们所成锐二面角的余弦值是多少？",
     "Fraction(abs(1*0+1*1+0*1), 2)",
     "n1·n2=1；两个法向量的模都是根号 2，乘积是 2，所以锐二面角的余弦值等于 1/2。"),

    ("cnm_h163",
     "平面过原点，法向量 n=(1，2，2)，点 P(3，3，3)。P 到该平面的距离是多少？",
     "Fraction(1*3+2*3+2*3, isqrt(1+4+4))",
     "距离等于 |OP·n|÷|n|=15÷3=5。"),

    ("cnm_h164",
     "棱长为 2 的正方体中，A1B 与 B1C 是两条异面直线。它们夹角的余弦值是多少？",
     "Fraction(abs(0*0+2*0+(-2)*(-2)), 2*2+2*2)",
     "建系后 A1B=(0，2，−2)、B1C=(−2，0，−2)，数量积是 4，两个向量的模都是根号 8、"
     "乘积是 8，所以夹角的余弦值是 1/2。"),
]


def main() -> int:
    with open(QUESTIONS, encoding="utf-8") as f:
        items = json.load(f)
    by_id = {q["id"]: q for q in items}

    with open(os.path.join(ROOT, "data", "topics.json"), encoding="utf-8") as f:
        topics = {t["id"]: t for t in json.load(f)}

    added = []
    for tid, prompt, verify, expl in SPECS:
        if tid not in topics:
            raise SystemExit("知识点不存在：%s" % tid)
        qid = "%s_q5" % tid
        if qid in by_id:
            raise SystemExit("%s 已存在，脚本拒绝重复追加" % qid)
        if not topics[tid].get("chapter", "").startswith("选必一 第一章"):
            raise SystemExit("%s 不在选必一第一章：%s" % (tid, topics[tid].get("chapter")))
        check_wording(qid, prompt)
        check_wording(qid, expl)
        assert_exact_sqrt(verify)
        result = safe_eval(verify)
        item = {
            "id": qid,
            "topicId": tid,
            "difficulty": "advanced",
            "type": "numeric",
            "prompt": prompt,
            "answer": fmt_result(result),
            "explanation": expl,
            "verify": verify,
        }
        items.append(item)
        by_id[qid] = item
        added.append(item)

    with open(QUESTIONS, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(LOG, encoding="utf-8") as f:
        log = json.load(f)
    pass_name = "F：高中数学选必一第一章补 advanced 档（21 题），答案由 verify 求值写入"
    passes = log.setdefault("passes", [])
    if not any(p.get("name") == pass_name for p in passes):
        passes.append({
            "name": pass_name,
            "solver": "scripts/hs_adv1.py + scripts/verify_questions.py",
            "questions": len(added),
            "note": "D/E 两轮只覆盖 basic 与 standard 两档。本轮补齐该章每个知识点的第三档"
                    "（advanced）：题目为多步计算，verify 由同一条表达式求值后写入，"
                    "再被核验脚本比对。仍未做盲解，答案正确性依赖 verify 与被核验表达式一致。",
            "disagreements": 0,
        })
    log["high_school_advanced_batch1"] = len(added)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("已追加 %d 道 advanced 题：" % len(added))
    for it in added:
        print("  %s  answer=%s  verify=%s" % (it["id"], it["answer"], it["verify"]))
    print("题库总数：%d" % len(items))
    print("接着跑：python3 scripts/validate.py && python3 scripts/verify_questions.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
