#!/usr/bin/env python3
"""把高中选择性必修草稿编译进 data/topics.json 等文件。

只应在还没有 cnm_h144 时运行一次。已经编译过再跑会拒绝，避免重复追加。
先修边只对新增知识点上的边做传递约简，不改已有小学、初中和必修边，也不改已有节点的 id 与名称。

用法：python3 scripts/hs_sel_build.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hs_sel_common import EDGES, QUESTIONS, STANDARDS, TOPICS  # noqa: E402
from hs_common import ELECTIVE, PAGES  # noqa: E402
import hs_sel_standards  # noqa: E402,F401
import hs_sel_b1  # noqa: E402,F401
import hs_sel_b2  # noqa: E402,F401
import hs_sel_b3  # noqa: E402,F401
import hs_sel_edges  # noqa: E402,F401
from verify_questions import safe_eval  # noqa: E402

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
BAD_START = ("同一", "上题", "该函数", "这个函数", "同上")
BAD_ANY = ("本知识点", "课标", "是否要求")
FIRST_ID = 144

# 跨出选择性必修、指向已有知识点。名称写在这里，编译时核对，避免指错 id。
KNOWN = {
    "cnm_056": "角的概念与表示",
    "cnm_065": "垂线段最短与点到直线的距离",
    "cnm_067": "平行线与平行公理",
    "cnm_071": "定义、命题与定理",
    "cnm_082": "平面直角坐标系与点的坐标",
    "cnm_174": "勾股定理",
    "cnm_201": "一次函数的概念",
    "cnm_211": "平均数",
    "cnm_215": "极差、方差与标准差",
    "cnm_219": "一元二次方程的概念",
    "cnm_229": "二次函数的概念",
    "cnm_250": "圆的有关概念",
    "cnm_286": "用列举法求概率",
    "cnm_p095": "简单的搭配",
    "cnm_h027": "函数的概念",
    "cnm_h028": "函数的定义域",
    "cnm_h032": "函数的单调性",
    "cnm_h034": "函数的最大（小）值",
    "cnm_h037": "幂函数",
    "cnm_h041": "指数函数的概念",
    "cnm_h042": "指数函数的性质",
    "cnm_h079": "平面向量的概念",
    "cnm_h081": "向量加法",
    "cnm_h084": "向量共线定理",
    "cnm_h085": "平面向量基本定理",
    "cnm_h086": "向量的坐标表示",
    "cnm_h088": "向量数量积",
    "cnm_h090": "向量的模与夹角",
    "cnm_h113": "平面的基本事实",
    "cnm_h114": "空间直线的位置关系",
    "cnm_h116": "直线与平面平行的判定",
    "cnm_h118": "平面与平面平行的判定",
    "cnm_h120": "直线与平面垂直的判定",
    "cnm_h122": "平面与平面垂直",
    "cnm_h127": "频率分布直方图",
    "cnm_h130": "用样本估计总体的中心",
    "cnm_h134": "样本点与样本空间",
    "cnm_h135": "随机事件",
    "cnm_h137": "古典概型",
    "cnm_h140": "事件的相互独立",
    "cnm_h141": "独立事件的概率计算",
    "cnm_h142": "频率与概率",
}

VOLUMES = {1: "选必一", 2: "选必二", 3: "选必三"}
GRADES = {1: 12, 2: 13, 3: 14}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fmt_one(v):
    if isinstance(v, bool) or v is None:
        raise TypeError(repr(v))
    if isinstance(v, str):
        raise TypeError("数值题的 verify 不应返回字符串：%r" % v)
    if isinstance(v, float):
        fr = Fraction(v).limit_denominator(64)
        if abs(float(fr) - v) > 1e-9:
            raise ValueError("结果不是简单分数：%r" % (v,))
        v = fr
    if isinstance(v, int):
        v = Fraction(v)
    if not isinstance(v, Fraction):
        raise TypeError(type(v).__name__)
    if v.denominator == 1:
        return str(int(v))
    return "%d/%d" % (v.numerator, v.denominator)


def fmt_result(v):
    if isinstance(v, (list, tuple)):
        if len(v) < 2:
            raise ValueError("多个答案至少 2 个")
        return "，".join(fmt_one(x) for x in v)
    return fmt_one(v)


def check_wording(qid, text):
    body = text.strip()
    for prefix in BAD_START:
        if body.startswith(prefix):
            raise ValueError("%s 题干以「%s」开头" % (qid, prefix))
    for word in BAD_ANY:
        if word in text:
            raise ValueError("%s 出现「%s」" % (qid, word))


def build_question(tid, index, spec, slot):
    kind = spec[0]
    diff = "basic" if index <= 2 else "standard"
    qid = "%s_q%d" % (tid, index)
    if kind in ("n", "nu"):
        prompt, verify, expl = spec[1], spec[2], spec[3]
        check_wording(qid, prompt)
        check_wording(qid, expl)
        res = safe_eval(verify)
        answer = fmt_result(res)
        multi = isinstance(res, (list, tuple))
        item = {
            "id": qid,
            "topicId": tid,
            "difficulty": diff,
            "type": "numeric",
            "prompt": prompt,
            "answer": answer,
            "explanation": expl,
            "verify": verify,
        }
        if kind == "nu":
            if not multi:
                raise ValueError("%s 标记了无序但 verify 不是多个答案" % qid)
            item["unordered"] = True
        return item, answer
    if kind == "c":
        prompt, correct, wrongs, expl = spec[1], spec[2], spec[3], spec[4]
        check_wording(qid, prompt)
        check_wording(qid, expl)
        check_wording(qid, correct)
        for wrong in wrongs:
            check_wording(qid, wrong)
        texts = list(wrongs)
        if correct in texts or len(set(texts)) != len(texts):
            raise ValueError("%s 选项重复或正确项混进错误项" % qid)
        if not (2 <= len(wrongs) <= 3):
            raise ValueError("%s 干扰项须 2–3 个" % qid)
        texts.insert(slot % (len(wrongs) + 1), correct)
        if len(set(t.strip() for t in texts)) != len(texts):
            raise ValueError("%s 选项文字重复" % qid)
        keys = list("ABCD")[:len(texts)]
        pos = texts.index(correct)
        item = {
            "id": qid,
            "topicId": tid,
            "difficulty": diff,
            "type": "choice",
            "prompt": prompt,
            "choices": [{"key": keys[i], "text": texts[i]} for i in range(len(texts))],
            "answer": keys[pos],
            "explanation": expl,
            "verify": json.dumps(correct, ensure_ascii=False),
        }
        return item, correct
    raise ValueError("未知题型 %s" % kind)


def reaches(adj, src, dst, hard_only):
    seen = {src}
    stack = [src]
    while stack:
        node = stack.pop()
        for pre, strength in adj.get(node, []):
            if hard_only and strength != "hard":
                continue
            if pre == dst:
                return True
            if pre not in seen:
                seen.add(pre)
                stack.append(pre)
    return False


def reduce_new(edges, new_ids):
    """只删除新增知识点上的冗余边。已有边原样保留。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if e["topicId"] not in new_ids:
            kept.append(e)
            continue
        lst = adj[e["topicId"]]
        idx = next(i for i, (p, s) in enumerate(lst)
                   if p == e["prerequisiteId"] and s == e["strength"])
        lst.pop(idx)
        if reaches(adj, e["topicId"], e["prerequisiteId"], e["strength"] == "hard"):
            dropped += 1
            continue
        lst.append([e["prerequisiteId"], e["strength"]])
        kept.append(e)
    return kept, dropped


def chapter_of(spec):
    vol = VOLUMES[spec["book"]]
    if spec["chapter"] in ("数学建模", "数学探究"):
        return "%s %s %s" % (vol, spec["chapter"], spec["section"])
    return "%s %s %s" % (vol, spec["chapter"], spec["section"])


def main():
    topics = load("topics.json")
    if any(t.get("id") == "cnm_h144" for t in topics):
        print("已经有 cnm_h144。hs_sel_build.py 不能重复编译。", file=sys.stderr)
        return 1
    if not any(t.get("id") == "cnm_h143" for t in topics):
        print("缺少 cnm_h143，请先编译高中必修。", file=sys.stderr)
        return 1
    frozen = [(t.get("id"), t.get("name")) for t in topics]
    by_id = {t["id"]: t for t in topics}
    for tid, name in KNOWN.items():
        hit = by_id.get(tid)
        if hit is None or hit["name"] != name:
            print("先修 id 对不上：%s 期望「%s」，实际 %s" % (
                tid, name, None if hit is None else hit["name"]), file=sys.stderr)
            return 1

    if len(TOPICS) < 110 or len(TOPICS) > 160:
        print("知识点数量 %d 不在 110–160" % len(TOPICS), file=sys.stderr)
        return 1
    missing_q = [t["key"] for t in TOPICS if t["key"] not in QUESTIONS]
    if missing_q:
        print("缺题：%s" % "、".join(missing_q), file=sys.stderr)
        return 1
    extra_q = sorted(set(QUESTIONS) - {t["key"] for t in TOPICS})
    if extra_q:
        print("多余题目 key：%s" % "、".join(extra_q), file=sys.stderr)
        return 1

    std_codes = [s["code"] for s in STANDARDS]
    if len(std_codes) != len(set(std_codes)):
        print("课标 code 重复", file=sys.stderr)
        return 1
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    grade_of = {t["key"]: GRADES[t["book"]] for t in TOPICS}

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS):
        tid = "cnm_h%03d" % (FIRST_ID + i)
        id_of[spec["key"]] = tid
        if spec["std"] not in std_codes:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        if spec["confidence"] not in ("exact", "inferred"):
            print("%s confidence 非法" % spec["key"], file=sys.stderr)
            return 1
        if spec["confidence"] == "inferred" and not spec.get("note"):
            print("%s inferred 缺 note" % spec["key"], file=sys.stderr)
            return 1
        if spec["book"] not in GRADES:
            print("%s 册次非法" % spec["key"], file=sys.stderr)
            return 1
        try:
            built = []
            diag_answer = None
            for n, item in enumerate(QUESTIONS[spec["key"]], start=1):
                q, shown = build_question(tid, n, item, slot=i + n)
                if not q["prompt"].strip() or not q["explanation"].strip():
                    raise ValueError("题干或解析为空")
                built.append(q)
                if n == 1:
                    diag_answer = shown
        except Exception as exc:  # noqa: BLE001
            print("出题失败 %s %s：%s" % (tid, spec["name"], exc), file=sys.stderr)
            return 1
        std_ref = {"id": "cms-2017:H.%s" % spec["std"], "confidence": spec["confidence"]}
        if spec.get("note"):
            std_ref["note"] = spec["note"]
        new_topics.append({
            "id": tid,
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": GRADES[spec["book"]],
            "semester": "上",
            "chapter": chapter_of(spec),
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": str(diag_answer)},
            "external": False,
            "standards": [std_ref],
        })
        new_questions.extend(built)

    raw_edges = []
    seen = set()
    for src, dst, strength, reason in EDGES:
        if src not in id_of:
            print("边的起点不是选择性必修知识点：%s" % src, file=sys.stderr)
            return 1
        if len(CJK_RE.findall(reason)) < 9:
            print("理由太短：%s → %s：%s" % (src, dst, reason), file=sys.stderr)
            return 1
        if dst in id_of:
            if index[dst] >= index[src]:
                print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            if grade_of[dst] > grade_of[src]:
                print("先修年级更高：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            pid = id_of[dst]
        elif dst in KNOWN:
            pid = dst
        else:
            print("先修既不是选择性必修 key 也不是已登记的旧 id：%s" % dst, file=sys.stderr)
            return 1
        key = (id_of[src], pid)
        if key in seen:
            print("重复边 %s → %s" % key, file=sys.stderr)
            return 1
        seen.add(key)
        raw_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": pid,
            "strength": strength,
            "reason": reason,
        })

    new_ids = {t["id"] for t in new_topics}
    deps = load("dependencies.json")
    merged, dropped = reduce_new(deps + raw_edges, new_ids)
    new_only = [e for e in merged if e["topicId"] in new_ids]
    internal = [e for e in new_only if e["prerequisiteId"] in new_ids]
    cross = [e for e in new_only if e["prerequisiteId"] not in new_ids]
    to_compulsory = [e for e in cross if str(e["prerequisiteId"]).startswith("cnm_h")]
    to_primary = [e for e in cross if str(e["prerequisiteId"]).startswith("cnm_p")]
    to_junior = [e for e in cross if e not in to_compulsory and e not in to_primary]
    print("选择性必修知识点 %d（选必一 %d，选必二 %d，选必三 %d）" % (
        len(new_topics),
        sum(1 for t in new_topics if t["grade"] == 12),
        sum(1 for t in new_topics if t["grade"] == 13),
        sum(1 for t in new_topics if t["grade"] == 14)))
    print("新边写出 %d，约简删去 %d，保留 %d" % (len(raw_edges), dropped, len(new_only)))
    print("选择性必修内部 %d；跨模块 %d（必修 %d，初中 %d，小学 %d）" % (
        len(internal), len(cross), len(to_compulsory), len(to_junior), len(to_primary)))
    print("题目 %d" % len(new_questions))
    print("课标 %d" % len(STANDARDS))

    from verify_questions import verify_all
    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in new_only}
    naked = [t["id"] + " " + t["name"] for t in new_topics if t["id"] not in covered]
    if naked:
        print("这些新知识点没有先修：" + "、".join(naked), file=sys.stderr)
        return 1
    ch_model = re.compile(r"^(选必[一二三]) (数学建模|数学探究) (\S+)$")
    ch_num = re.compile(r"^(\S+) (第\S+章) (\S+?)(?: (\S+))?$")
    for t in new_topics:
        if not (ch_model.match(t["chapter"]) or ch_num.match(t["chapter"])):
            print("章节名无法解析：%s %s" % (t["id"], t["chapter"]), file=sys.stderr)
            return 1

    std = load("cn-curriculum-standards.json")
    note = std["source"].get("note") or ""
    extra = (" 选择性必修条目续接同一套编号（函数 FUN.18 起，几何与代数 GA.13 起，"
             "概率与统计 PS.09 起，建模与探究 MI.03 起），仍是公开转述，verbatim 为 false，"
             "page_or_ref 为「待核」。")
    if "选择性必修条目" not in note:
        std["source"]["note"] = note + extra
    std["source"]["stage"] = "义务教育第一至第四学段（1～9年级）；普通高中必修课程与选择性必修课程"
    retrieved = std["source"].get("retrieved") or ""
    if "高中选择性必修" not in retrieved:
        std["source"]["retrieved"] = retrieved + "；2026-10-20（高中选择性必修）"
    hs = std["source"].setdefault("high_school", {})
    old_hs_note = hs.get("note") or ""
    if "选择性必修" not in old_hs_note:
        hs["note"] = old_hs_note + " 选择性必修主题同样未逐页核对，标为待核。"
    existing_ids = {it["id"] for it in std["items"]}
    for s in STANDARDS:
        sid = "cms-2017:H.%s" % s["code"]
        if sid in existing_ids:
            print("课标 id 已存在：%s" % sid, file=sys.stderr)
            return 1
        std["items"].append({
            "id": sid,
            "domain": s["domain"],
            "theme": s["theme"],
            "section": s["section"],
            "clause": s["clause"],
            "text": s["text"],
            "page_or_ref": ("课标印刷页码 %d" % PAGES[s["code"]]) if s["code"] in PAGES else "待核",
            "verbatim": False,
            "text_status": "公开转述整理，未与教育部 PDF 逐页核对，待核",
        })
        if s["code"] in ELECTIVE:
            std["items"][-1]["elective"] = True

    topics.extend(new_topics)
    if [(t.get("id"), t.get("name")) for t in topics[:len(frozen)]] != frozen:
        print("已有知识点的 id 或名称被改动。", file=sys.stderr)
        return 1
    questions = load("questions.json")
    questions.extend(new_questions)
    dump("topics.json", topics)
    dump("dependencies.json", merged)
    dump("questions.json", questions)
    dump("cn-curriculum-standards.json", std)
    batch = os.path.join(ROOT, "data", "_qbatches", "high_sel.json")
    with open(batch, "w", encoding="utf-8") as f:
        json.dump(new_questions, f, ensure_ascii=False, indent=2)
        f.write("\n")

    log_path = os.path.join(ROOT, "data", "second_pass_log.json")
    with open(log_path, encoding="utf-8") as f:
        log = json.load(f)
    pass_name = "E：高中选择性必修题由生成脚本写 verify，再经 verify_questions.py 核对表达式与答案"
    passes = log.setdefault("passes", [])
    if not any(p.get("name") == pass_name for p in passes):
        passes.append({
            "name": pass_name,
            "solver": "scripts/hs_sel_build.py + scripts/verify_questions.py",
            "questions": len(new_questions),
            "note": "答案由同一条 verify 表达式求值后写入，再被核验脚本比对，所以 mismatch 反映的是格式而不是另一遍独立解题。没有做初中 A/B 轮那种盲解。概念题的选项文字与 verify 返回的字符串相同。",
            "disagreements": 0,
        })
    log["high_school_selective_checked_by_verify"] = len(new_questions)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写入 data/。请再跑 validate.py 与 verify_questions.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
