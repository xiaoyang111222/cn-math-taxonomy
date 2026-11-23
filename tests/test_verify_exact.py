#!/usr/bin/env python3
"""verify 表达式精确求值：全库数值型 verify 的结果必须与 answer 按精确有理数（Fraction）相等。

verify_questions.py 对 float 结果放宽到 1e-9，下游若用 Fraction 精确比较，就会把 sqrt(7)**2 = 7.000000000000001、
sin(radians(30)) = 0.49999999999999994 这类浮点残差判成错。本测试不放宽：
  - 结果是 int / Fraction：必须与 answer 精确相等；
  - 结果是 float：取最短十进制表示（repr）转成 Fraction，必须与 answer 精确相等（round(x, 6) 之后的 3.14 这类合格，
    7.000000000000001 这类不合格）。
字符串型 verify（选项文字）和选项带单位但无法拆出数值的 choice 不在此列。
"""
import json
import math
import os
import sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate as V  # noqa: E402
import verify_questions as VQ  # noqa: E402


def exact_equal(expected, got):
    if isinstance(got, bool):
        return False
    if isinstance(got, (int, Fraction)):
        return Fraction(got) == expected
    if isinstance(got, float):
        if math.isnan(got) or math.isinf(got):
            return False
        return Fraction(repr(got)) == expected
    return False


def expected_values(q, res):
    """返回 (期望值列表, 实际值列表)；这题不是数值型 verify 就返回 None。"""
    if q.get("type") == "numeric":
        exp = V.parse_numeric_answer(q["answer"])
        got = VQ.flatten_result(res)
        if exp is None or any(isinstance(g, str) for g in got):
            return None
        return exp, got
    texts = {c["key"]: c["text"].strip() for c in q["choices"]}
    right = texts[q["answer"]]
    rv = VQ.choice_text_value(right)
    if rv is None and str(q["id"]).startswith("cnp_"):
        pv = VQ.phy_choice_value(right)
        rv = [pv[0]] if pv else None
    if rv is None or len(rv) != 1 or isinstance(res, (str, bool)) or not isinstance(res, (int, float, Fraction)):
        return None
    return rv, [res]


def inexact(q):
    """返回 None（通过或不适用）或描述不精确的字符串。"""
    res = VQ.safe_eval(q["verify"])
    pair = expected_values(q, res)
    if pair is None:
        return None
    exp, got = pair
    if len(exp) != len(got):
        return "答案个数不同"
    if q.get("unordered") is True:
        left = list(got)
        for e in exp:
            hit = next((i for i, g in enumerate(left) if exact_equal(e, g)), None)
            if hit is None:
                return "answer 中的 %s 在 verify 结果 %r 里没有精确对应" % (e, res)
            left.pop(hit)
        return None
    for e, g in zip(exp, got):
        if not exact_equal(e, g):
            return "answer %s ≠ verify 结果 %r" % (e, g)
    return None


def main():
    with open(os.path.join(ROOT, "data", "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)

    # 负控制：这些写法必须被判为不精确，否则下面的全库检查形同虚设
    assert inexact({"id": "t1", "type": "numeric", "answer": "7", "verify": "sqrt(7)**2"}), "sqrt(7)**2 应判为不精确"
    assert inexact({"id": "t2", "type": "numeric", "answer": "1/2", "verify": "sin(radians(30))"}), "sin(radians(30)) 应判为不精确"
    assert inexact({"id": "t3", "type": "numeric", "answer": "6/7", "verify": "2/7*3"}), "2/7*3 应判为不精确"
    assert inexact({"id": "t4", "type": "numeric", "answer": "7", "verify": "round(sqrt(7)**2, 6)"}) is None
    assert inexact({"id": "t5", "type": "numeric", "answer": "6/7", "verify": "Fraction(2,7)*3"}) is None
    assert inexact({"id": "t6", "type": "numeric", "answer": "5，7", "verify": "[5, round(sqrt(7)**2, 6)]"}) is None

    checked = 0
    bad = []
    for q in questions:
        if not q.get("verify") or q.get("type") not in ("numeric", "choice"):
            continue
        why = inexact(q)
        if expected_values(q, VQ.safe_eval(q["verify"])) is not None:
            checked += 1
        if why:
            bad.append("%s  verify=%r  %s" % (q["id"], q["verify"], why))
    assert checked > 2500, "数值型 verify 题只有 %d 道，统计口径可能坏了" % checked
    if bad:
        print("以下 %d 道题的 verify 求值与 answer 不能精确相等：" % len(bad))
        for b in bad[:60]:
            print("  - " + b)
        sys.exit(1)
    print("  ok   数值型 verify 精确求值与 answer 相等（%d 道）" % checked)


if __name__ == "__main__":
    main()
