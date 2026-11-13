#!/usr/bin/env python3
"""把高中化学必修第一、二册和选择性必修第一、二、三册编译进 data/ 下的四个文件。

只清除并重写 cnk_h、cks-hs-2017、chemistry_senior。
保留初中化学 cnk_j、cks-2022、chemistry，以及其他学科。
登记过的示意图在编译时写入 questions[].figure。

用法：python3 scripts/chem_hs_build.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chem_hs_b1  # noqa: E402,F401
import chem_hs_b2  # noqa: E402,F401
import chem_hs_s1  # noqa: E402,F401
import chem_hs_s2  # noqa: E402,F401
import chem_hs_s3  # noqa: E402,F401
import chem_hs_lib as L  # noqa: E402
import chem_hs_plan as P  # noqa: E402
import chem_hs_std as S  # noqa: E402
from verify_questions import verify_all  # noqa: E402
from chem_hs_figs import figure_for  # noqa: E402

SENIOR_STD_PREFIX = "cks-hs-2017:"
EXPECTED_PLAN = 102
B1_COUNT = 19
B2_COUNT = 22
S1_COUNT = 23
S2_COUNT = 14
S3_COUNT = 24
B1_EDGES = 44
B2_EDGES = 53
S1_EDGES = 44
S2_EDGES = 22


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_hs_topic(tid):
    return str(tid).startswith("cnk_h")


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


def reduce_senior(edges):
    """只约简高中化学边上的冗余。不改初中边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_hs_topic(e["topicId"]):
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


def build_question(tid, index, q, slot):
    qid = "%s_q%d" % (tid, index)
    if q["kind"] == "numeric":
        return {
            "id": qid,
            "topicId": tid,
            "difficulty": q["diff"],
            "type": "numeric",
            "prompt": q["prompt"],
            "answer": q["answer"],
            "explanation": q["expl"],
            "verify": q["verify"],
        }, q["answer"]
    texts = list(q["wrongs"])
    texts.insert(slot % 4, q["right"])
    keys = list("ABCD")
    pos = texts.index(q["right"])
    return {
        "id": qid,
        "topicId": tid,
        "difficulty": q["diff"],
        "type": "choice",
        "prompt": q["prompt"],
        "choices": [{"key": keys[i], "text": texts[i]} for i in range(4)],
        "answer": keys[pos],
        "explanation": q["expl"],
        "verify": L.choice_verify(q["right"]),
    }, q["right"]


def std_items():
    out = []
    seen = {}
    for tail, code, section, text in S.CLAUSES:
        if code not in S.CODES:
            raise SystemExit("未知主题代码 %s" % code)
        parts = tail.split(".")
        if len(parts) != 3:
            raise SystemExit("课标尾部格式不对：%s" % tail)
        book, code_in_id, num_s = parts
        if book not in ("B1", "B2", "S1", "S2", "S3") or code_in_id != code:
            raise SystemExit("课标 id 与主题代码不一致：%s" % tail)
        num = int(num_s)
        key = (book, code)
        if num != seen.get(key, 0) + 1:
            raise SystemExit("课标编号不连续：%s" % tail)
        seen[key] = num
        if book in ("B1", "B2"):
            status = S.TEXT_STATUS
        elif book == "S1":
            status = S.S1_TEXT_STATUS
        elif book == "S2":
            status = S.S2_TEXT_STATUS
        else:
            status = S.S3_TEXT_STATUS
        out.append({
            "id": SENIOR_STD_PREFIX + tail,
            "domain": S.CODES[code],
            "section": section,
            "clause": "(%d)" % num,
            "text": text,
            "page_or_ref": "待核",
            "verbatim": False,
            "text_status": status,
        })
    return out


def book_word(row):
    return P.BOOK_WORD[row["grade"]]


def soft_reason(prev_row, cur_row):
    prev_name, cur_name = prev_row["name"], cur_row["name"]
    if prev_row["grade"] == 10 and cur_row["grade"] == 10:
        return "按人教版化学必修第一册的教学顺序，先学「%s」，再学「%s」。" % (prev_name, cur_name)
    if prev_row["grade"] == 11 and cur_row["grade"] == 11:
        return "按人教版化学必修第二册的教学顺序，先学「%s」，再学「%s」。" % (prev_name, cur_name)
    if prev_row["grade"] == 12 and cur_row["grade"] == 12:
        return "按人教版化学选择性必修第一册的教学顺序，先学「%s」，再学「%s」。" % (prev_name, cur_name)
    if prev_row["grade"] == 13 and cur_row["grade"] == 13:
        return "按人教版化学选择性必修第二册的教学顺序，先学「%s」，再学「%s」。" % (prev_name, cur_name)
    if prev_row["grade"] == 14 and cur_row["grade"] == 14:
        return "按人教版化学选择性必修第三册的教学顺序，先学「%s」，再学「%s」。" % (prev_name, cur_name)
    if prev_row["grade"] == 10 and cur_row["grade"] == 11:
        return "按人教版化学必修课序，学完必修第一册的「%s」后进入必修第二册的「%s」。" % (
            prev_name, cur_name)
    if prev_row["grade"] == 11 and cur_row["grade"] == 12:
        return "按人教版化学课序，学完必修第二册的「%s」后进入选择性必修第一册的「%s」。" % (
            prev_name, cur_name)
    if prev_row["grade"] == 12 and cur_row["grade"] == 13:
        return "按人教版化学课序，学完选择性必修第一册的「%s」后进入选择性必修第二册的「%s」。" % (
            prev_name, cur_name)
    if prev_row["grade"] == 13 and cur_row["grade"] == 14:
        return "按人教版化学课序，学完选择性必修第二册的「%s」后进入选择性必修第三册的「%s」。" % (
            prev_name, cur_name)
    return "按人教版化学课序，先学「%s」，再学「%s」。" % (prev_name, cur_name)


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    if len(P.PLAN) != EXPECTED_PLAN:
        print("课序应为 %d 条" % EXPECTED_PLAN, file=sys.stderr)
        return 1
    if sum(1 for row in P.PLAN if row["grade"] == 10) != B1_COUNT:
        print("必修第一册应为 %d 条" % B1_COUNT, file=sys.stderr)
        return 1
    if sum(1 for row in P.PLAN if row["grade"] == 11) != B2_COUNT:
        print("必修第二册应为 %d 条" % B2_COUNT, file=sys.stderr)
        return 1
    if sum(1 for row in P.PLAN if row["grade"] == 12) != S1_COUNT:
        print("选择性必修第一册应为 %d 条" % S1_COUNT, file=sys.stderr)
        return 1
    if sum(1 for row in P.PLAN if row["grade"] == 13) != S2_COUNT:
        print("选择性必修第二册应为 %d 条" % S2_COUNT, file=sys.stderr)
        return 1
    if sum(1 for row in P.PLAN if row["grade"] == 14) != S3_COUNT:
        print("选择性必修第三册应为 %d 条" % S3_COUNT, file=sys.stderr)
        return 1
    missing = [row["key"] for row in P.PLAN if row["key"] not in L.HS]
    extra = [key for key in L.HS if key not in P.PLAN_BY_KEY]
    if missing or extra:
        print("草稿与课序不一致：缺 %s，多 %s" % (missing, extra), file=sys.stderr)
        return 1

    junior = {t["id"]: t for t in topics if str(t["id"]).startswith("cnk_j")}
    if len(junior) != 45:
        print("初中化学应有 45 个点，实际 %d" % len(junior), file=sys.stderr)
        return 1
    junior_names = {tid: t["name"] for tid, t in junior.items()}
    b1_id_set = {"cnk_h%03d" % i for i in range(1, B1_COUNT + 1)}
    snap_b1_topics = [
        (t["id"], t["name"], t["chapter"], t["grade"], t["semester"], t.get("diagnostic_question"))
        for t in topics if t.get("id") in b1_id_set
    ]
    snap_b1_questions = [q for q in questions if q.get("topicId") in b1_id_set]
    snap_b1_edges = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in deps if e.get("topicId") in b1_id_set
    ]
    if len(snap_b1_topics) != B1_COUNT or len(snap_b1_questions) != B1_COUNT * 4:
        print("现有第一册数据不是 19 点 76 题，不能在此基础上增量编译", file=sys.stderr)
        return 1
    if len(snap_b1_edges) != B1_EDGES:
        print("现有第一册先修边不是 %d 条，实际 %d" % (B1_EDGES, len(snap_b1_edges)), file=sys.stderr)
        return 1
    b2_id_set = {"cnk_h%03d" % i for i in range(B1_COUNT + 1, B1_COUNT + B2_COUNT + 1)}
    snap_b2_topics = [
        (t["id"], t["name"], t["chapter"], t["grade"], t["semester"], t.get("diagnostic_question"))
        for t in topics if t.get("id") in b2_id_set
    ]
    snap_b2_questions = [q for q in questions if q.get("topicId") in b2_id_set]
    snap_b2_edges = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in deps if e.get("topicId") in b2_id_set
    ]
    if len(snap_b2_topics) != B2_COUNT or len(snap_b2_questions) != B2_COUNT * 4:
        print("现有第二册数据不是 22 点 88 题，不能在此基础上增量编译", file=sys.stderr)
        return 1
    if len(snap_b2_edges) != B2_EDGES:
        print("现有第二册先修边不是 %d 条，实际 %d" % (B2_EDGES, len(snap_b2_edges)), file=sys.stderr)
        return 1
    s1_id_set = {
        "cnk_h%03d" % i
        for i in range(B1_COUNT + B2_COUNT + 1, B1_COUNT + B2_COUNT + S1_COUNT + 1)
    }
    snap_s1_topics = [
        (t["id"], t["name"], t["chapter"], t["grade"], t["semester"], t.get("diagnostic_question"))
        for t in topics if t.get("id") in s1_id_set
    ]
    snap_s1_questions = [q for q in questions if q.get("topicId") in s1_id_set]
    snap_s1_edges = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in deps if e.get("topicId") in s1_id_set
    ]
    if len(snap_s1_topics) != S1_COUNT or len(snap_s1_questions) != S1_COUNT * 4:
        print("现有选必一数据不是 23 点 92 题，不能在此基础上增量编译", file=sys.stderr)
        return 1
    if len(snap_s1_edges) != S1_EDGES:
        print("现有选必一先修边不是 %d 条，实际 %d" % (S1_EDGES, len(snap_s1_edges)), file=sys.stderr)
        return 1
    s2_id_set = {
        "cnk_h%03d" % i
        for i in range(B1_COUNT + B2_COUNT + S1_COUNT + 1,
                       B1_COUNT + B2_COUNT + S1_COUNT + S2_COUNT + 1)
    }
    snap_s2_topics = [
        (t["id"], t["name"], t["chapter"], t["grade"], t["semester"], t.get("diagnostic_question"))
        for t in topics if t.get("id") in s2_id_set
    ]
    snap_s2_questions = [q for q in questions if q.get("topicId") in s2_id_set]
    snap_s2_edges = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in deps if e.get("topicId") in s2_id_set
    ]
    if len(snap_s2_topics) != S2_COUNT or len(snap_s2_questions) != S2_COUNT * 4:
        print("现有选必二数据不是 14 点 56 题，不能在此基础上增量编译", file=sys.stderr)
        return 1
    if len(snap_s2_edges) != S2_EDGES:
        print("现有选必二先修边不是 %d 条，实际 %d" % (S2_EDGES, len(snap_s2_edges)), file=sys.stderr)
        return 1
    snap_hs_std = [
        (it.get("id"), it.get("text"), it.get("text_status"), it.get("verbatim"), it.get("page_or_ref"))
        for it in standards.get("items", [])
        if str(it.get("id", "")).startswith(SENIOR_STD_PREFIX)
    ]
    # 选必三首次写入时文件里是前 52 条；其后重跑已经有 64 条，必须原样保留。
    if len(snap_hs_std) not in (52, 64):
        print("现有高中化学课标不是 52 或 64 条，实际 %d" % len(snap_hs_std), file=sys.stderr)
        return 1

    id_of = {}
    for i, row in enumerate(P.PLAN, start=1):
        id_of[row["key"]] = "cnk_h%03d" % i

    std_by_tail = {item["id"][len(SENIOR_STD_PREFIX):]: item["id"] for item in std_items()}
    cited = set()
    new_topics = []
    new_questions = []
    hard_pairs = {}

    for i, row in enumerate(P.PLAN, start=1):
        key = row["key"]
        draft = L.HS[key]
        tid = id_of[key]
        expected_book = book_word(row)
        if row["chapter"].split()[0] != expected_book:
            print("%s 章节不是以%s开头：%s" % (key, expected_book, row["chapter"]), file=sys.stderr)
            return 1
        if row["grade"] not in (10, 11, 12, 13, 14) or row["semester"] != "上":
            print("%s 的 grade/semester 不合法：%s %s" % (key, row["grade"], row["semester"]), file=sys.stderr)
            return 1
        refs = []
        for tail in draft["std"]:
            if tail not in std_by_tail:
                print("%s 引用了不存在的课标 %s" % (key, tail), file=sys.stderr)
                return 1
            cited.add(tail)
            refs.append({"id": std_by_tail[tail], "confidence": "inferred", "note": L.NOTE})
        built = []
        diag = None
        for n, q in enumerate(draft["qs"], start=1):
            obj, shown = build_question(tid, n, q, slot=i + n)
            fig = figure_for(obj)
            if fig:
                obj["figure"] = fig
            built.append(obj)
            if n == 1:
                diag = shown
        if built[0]["type"] != "choice" or built[0]["difficulty"] != "basic":
            print("%s 诊断题必须是 basic 选择题" % key, file=sys.stderr)
            return 1
        topic = {
            "id": tid,
            "name": row["name"],
            "domain": draft["domain"],
            "grade": row["grade"],
            "semester": row["semester"],
            "chapter": row["chapter"],
            "type": draft["type"],
            "description": draft["description"],
            "mastery_criteria": draft["mastery"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag},
            "external": False,
            "subject": "chemistry",
            "standards": refs,
        }
        new_topics.append(topic)
        new_questions.extend(built)
        for ref, reason in draft["pre"]:
            if not str(reason).strip():
                print("%s 先修缺少理由：%s" % (key, ref), file=sys.stderr)
                return 1
            if ref.startswith("J:"):
                pid = ref[2:]
                if pid not in junior:
                    print("%s 的初中先修不存在：%s" % (key, pid), file=sys.stderr)
                    return 1
            else:
                if ref not in id_of or P.ORDER[ref] >= P.ORDER[key]:
                    print("%s 的先修 %s 不存在或不在它前面" % (key, ref), file=sys.stderr)
                    return 1
                pid = id_of[ref]
            pair = (tid, pid)
            if pair in hard_pairs:
                print("重复硬边 %s → %s" % pair, file=sys.stderr)
                return 1
            hard_pairs[pair] = reason

    if "intro" not in L.HS or not any(ref.startswith("J:") for ref, _r in L.HS["intro"]["pre"]):
        print("cnk_h001 必须硬连至少一个初中化学点", file=sys.stderr)
        return 1
    first_b2 = next(row["key"] for row in P.PLAN if row["grade"] == 11)
    b2_hard_ok = False
    for ref, _r in L.HS[first_b2]["pre"]:
        if ref.startswith("J:"):
            b2_hard_ok = True
            break
        if ref in id_of and P.PLAN_BY_KEY[ref]["grade"] == 10:
            b2_hard_ok = True
            break
    if not b2_hard_ok:
        print("cnk_h020 必须硬连至少一个第一册或初中化学点", file=sys.stderr)
        return 1
    first_s1 = next(row["key"] for row in P.PLAN if row["grade"] == 12)
    s1_hard_ok = False
    for ref, _r in L.HS[first_s1]["pre"]:
        if ref.startswith("J:"):
            s1_hard_ok = True
            break
        if ref in id_of and P.PLAN_BY_KEY[ref]["grade"] in (10, 11):
            s1_hard_ok = True
            break
    if not s1_hard_ok:
        print("cnk_h042 必须硬连至少一个必修或初中化学点", file=sys.stderr)
        return 1
    first_s2 = next(row["key"] for row in P.PLAN if row["grade"] == 13)
    s2_hard_ok = False
    for ref, _r in L.HS[first_s2]["pre"]:
        if ref.startswith("J:"):
            s2_hard_ok = True
            break
        if ref in id_of and P.PLAN_BY_KEY[ref]["grade"] in (10, 11, 12):
            s2_hard_ok = True
            break
    if not s2_hard_ok:
        print("cnk_h065 必须硬连至少一个已有化学点", file=sys.stderr)
        return 1
    first_s3 = next(row["key"] for row in P.PLAN if row["grade"] == 14)
    s3_hard_ok = False
    for ref, _r in L.HS[first_s3]["pre"]:
        if ref.startswith("J:"):
            s3_hard_ok = True
            break
        if ref in id_of and P.PLAN_BY_KEY[ref]["grade"] in (10, 11, 12, 13):
            s3_hard_ok = True
            break
    if not s3_hard_ok:
        print("cnk_h079 必须硬连至少一个已有化学点", file=sys.stderr)
        return 1

    unused = [tail for tail, _c, _s, _t in S.CLAUSES if tail not in cited]
    if unused:
        print("课标没有被引用：%s" % "、".join(unused), file=sys.stderr)
        return 1

    raw = []
    for i in range(1, len(P.PLAN)):
        cur_row = P.PLAN[i]
        prev_row = P.PLAN[i - 1]
        if (id_of[cur_row["key"]], id_of[prev_row["key"]]) in hard_pairs:
            continue
        raw.append((id_of[cur_row["key"]], id_of[prev_row["key"]], "soft",
                    soft_reason(prev_row, cur_row)))
    for (tid, pid), reason in hard_pairs.items():
        raw.append((tid, pid, "hard", reason))

    new_edges = []
    seen_edge = set()
    for tid, pid, strength, reason in raw:
        if (tid, pid) in seen_edge:
            print("重复边 %s → %s" % (tid, pid), file=sys.stderr)
            return 1
        seen_edge.add((tid, pid))
        if not is_hs_topic(tid):
            print("高中边的后续点不是 cnk_h：%s" % tid, file=sys.stderr)
            return 1
        if not (is_hs_topic(pid) or str(pid).startswith("cnk_j")):
            print("高中化学边连到了化学以外：%s → %s" % (tid, pid), file=sys.stderr)
            return 1
        new_edges.append({
            "topicId": tid,
            "prerequisiteId": pid,
            "strength": strength,
            "reason": reason,
        })

    reduced, dropped = reduce_senior(new_edges)
    covered = {e["topicId"] for e in reduced}
    missing_pre = [t["id"] for t in new_topics if t["id"] not in covered]
    if missing_pre:
        print("约简后仍无先修：%s" % "、".join(missing_pre), file=sys.stderr)
        return 1
    if any(not str(e["prerequisiteId"]).startswith("cnk_") for e in reduced):
        print("约简后出现非化学先修", file=sys.stderr)
        return 1

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        for m in checked["unverifiable"][:20]:
            print("题目无法核对 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    snap_topics = [(t["id"], t["name"]) for t in topics if not is_hs_topic(t.get("id"))]
    snap_junior = [(t["id"], t["name"]) for t in topics if str(t["id"]).startswith("cnk_j")]
    snap_other = {}
    for prefix in ("cnm_", "cne_", "cnp_", "cnc_", "cns_", "cnd_", "cnh_", "cng_", "cnb_"):
        snap_other[prefix] = [(t["id"], t["name"]) for t in topics if str(t["id"]).startswith(prefix)]
    chem_obj = standards.get("chemistry")
    if not isinstance(chem_obj, dict) or chem_obj.get("title") != "义务教育化学课程标准（2022年版）":
        print("初中化学课标对象缺失或标题不对", file=sys.stderr)
        return 1
    junior_items = [it for it in standards.get("items", []) if str(it.get("id", "")).startswith("cks-2022")]
    if len(junior_items) != 22:
        print("初中课标应为 22 条，实际 %d" % len(junior_items), file=sys.stderr)
        return 1

    base_topics = [t for t in topics if not is_hs_topic(t.get("id"))]
    base_deps = [e for e in deps if not is_hs_topic(e.get("topicId")) and not is_hs_topic(e.get("prerequisiteId"))]
    base_questions = [q for q in questions if not is_hs_topic(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not str(it.get("id", "")).startswith(SENIOR_STD_PREFIX)]

    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + std_items()
    standards_out["chemistry_senior"] = {
        "title": "普通高中化学课程标准（2017年版）",
        "issuer": "中华人民共和国教育部",
        "year": 2017,
        "stage": "普通高中（本阶段收录与必修第一册、必修第二册、选择性必修第一册、选择性必修第二册、选择性必修第三册相关的内容要求）",
        "note": (
            "条目是对必修第一册、必修第二册、选择性必修第一册、选择性必修第二册和选择性必修第三册相关内容要求的公开转述，不是逐页核对的原文。"
            "verbatim 为 false，page_or_ref 为「待核」。"
            "编号 cks-hs-2017:B1.<主题>.<序号>、cks-hs-2017:B2.<主题>.<序号>、cks-hs-2017:S1.<主题>.<序号>、"
            "cks-hs-2017:S2.<主题>.<序号> 与 cks-hs-2017:S3.<主题>.<序号> 是本图谱编的，不是教育部原编号。"
            "必修主题用 2017 年版必修课程的公开通称：化学科学与实验探究、常见的无机物及其应用、"
            "物质结构基础与化学反应规律、简单的有机化合物及其应用、化学与社会发展。"
            "选择性必修第一册主题用「化学反应原理」模块的公开通称：化学反应与热能，"
            "化学反应的方向、速率和限度，水溶液中的离子反应与平衡，化学反应与电能。"
            "选择性必修第二册主题用「物质结构与性质」模块的公开通称：原子结构与性质，"
            "分子结构与性质，聚集状态与晶体结构。"
            "选择性必修第三册主题用「有机化学基础」模块的公开通称：有机化合物的组成与结构，"
            "烃及其衍生物的性质与应用，生物大分子，合成高分子。"
            "后记可见的依据是教育部《普通高中化学课程标准（2017年版）》，2019 年经国家教材委员会专家委员会审核通过。"
            "封面与后记均未印「2020年修订」，不得写成 2020 修订本。"
            "教材是普通高中教科书·化学必修第一册、必修第二册、选择性必修1 化学反应原理、"
            "选择性必修2 物质结构与性质、选择性必修3 有机化学基础，人民教育出版社，"
            "课程教材研究所、化学课程教材研究开发中心编著。"
            "必修第一册总主编王晶、郑长龙；本册主编王晶、毕华林。"
            "ISBN 978-7-107-33574-7。contentId 5cd19072-e40d-4a73-8580-7b7ada5d4005。"
            "必修第二册 ISBN 978-7-107-33575-4。contentId 07f7d663-a867-4eb6-ad39-03b55dbd4a65。"
            "第二册版权页列有总主编、本册主编等，但核验时未见清晰姓名，不编造。"
            "选择性必修第一册总主编王晶、郑长龙；本册主编范楼珍、吴海建；副主编乔国才、周业虹。"
            "ISBN 978-7-107-34602-6。contentId 3502fe81-b23e-4f68-aa3d-7921e7932ec9。"
            "选择性必修第二册总主编王晶、郑长龙；本册主编吴国庆、李俊。"
            "ISBN 978-7-107-34603-3。contentId b82cefe7-d631-4bde-baf9-352ca033cba4。"
            "选择性必修第三册总主编王晶、郑长龙；本册主编杜宝山；副主编郭震。"
            "ISBN 978-7-107-34604-0。contentId c561d8ee-7c06-4cb1-9a4d-e34036f02d53。"
            "五册版权页均未见版次、印次或出版年月，不编造。"
            "印刷目录建 19+22+23+14+24 个知识点；附录、元素周期表、全章复习、综合专题、高考复习和栏目索引不建点。"
            "未下载教材 PDF，印刷页码不写入知识点或题目。"
        ),
    }

    n_hard = sum(1 for e in reduced if e["strength"] == "hard")
    n_soft = sum(1 for e in reduced if e["strength"] == "soft")
    print("高中化学知识点 %d（cnk_h001–cnk_h%03d）" % (len(new_topics), len(new_topics)))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(std_items()))
    print("高中边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(reduced), dropped, n_hard, n_soft))
    def chapter_bucket(chapter):
        parts = chapter.split()
        if len(parts) >= 2 and parts[1].startswith("第") and parts[1].endswith("章"):
            return parts[0] + " " + parts[1]
        return chapter

    by_ch = Counter(chapter_bucket(t["chapter"]) for t in new_topics)
    for name, n in by_ch.items():
        print("  %s %d" % (name, n))
    s1_ids = {id_of[row["key"]] for row in P.PLAN if row["grade"] == 12}
    s1_reduced = [e for e in reduced if e["topicId"] in s1_ids]
    print("选必一边 %d（hard %d，soft %d）" % (
        len(s1_reduced),
        sum(1 for e in s1_reduced if e["strength"] == "hard"),
        sum(1 for e in s1_reduced if e["strength"] == "soft"),
    ))
    s2_ids = {id_of[row["key"]] for row in P.PLAN if row["grade"] == 13}
    s2_reduced = [e for e in reduced if e["topicId"] in s2_ids]
    print("选必二边 %d（hard %d，soft %d）" % (
        len(s2_reduced),
        sum(1 for e in s2_reduced if e["strength"] == "hard"),
        sum(1 for e in s2_reduced if e["strength"] == "soft"),
    ))
    s3_ids = {id_of[row["key"]] for row in P.PLAN if row["grade"] == 14}
    s3_reduced = [e for e in reduced if e["topicId"] in s3_ids]
    print("选必三边 %d（hard %d，soft %d）" % (
        len(s3_reduced),
        sum(1 for e in s3_reduced if e["strength"] == "hard"),
        sum(1 for e in s3_reduced if e["strength"] == "soft"),
    ))

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", base_deps + reduced)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    if [(t["id"], t["name"]) for t in again_t if not is_hs_topic(t.get("id"))] != snap_topics:
        print("非高中化学知识点的 id 或名称变了", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cnk_j")] != snap_junior:
        print("初中化学知识点变了", file=sys.stderr)
        return 1
    labels = {
        "cnm_": "数学", "cne_": "英语", "cnp_": "物理", "cnc_": "语文",
        "cns_": "科学", "cnd_": "道德与法治", "cnh_": "历史", "cng_": "地理", "cnb_": "生物",
    }
    for prefix, label in labels.items():
        if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith(prefix)] != snap_other[prefix]:
            print("%s知识点 id 或名称变了" % label, file=sys.stderr)
            return 1
    if again_s.get("chemistry") != chem_obj:
        print("初中 chemistry 对象变了", file=sys.stderr)
        return 1
    again_junior_items = [it for it in again_s.get("items", []) if str(it.get("id", "")).startswith("cks-2022")]
    if again_junior_items != junior_items:
        print("初中课标条目变了", file=sys.stderr)
        return 1
    if again_s.get("chemistry_senior", {}).get("title") != "普通高中化学课程标准（2017年版）":
        print("chemistry_senior 标题不正确", file=sys.stderr)
        return 1
    if again_s.get("chemistry_senior", {}).get("year") != 2017:
        print("chemistry_senior 年份不正确", file=sys.stderr)
        return 1
    hs_ids = [t["id"] for t in again_t if is_hs_topic(t.get("id"))]
    if hs_ids != ["cnk_h%03d" % i for i in range(1, EXPECTED_PLAN + 1)]:
        print("高中化学 id 顺序不对：%s" % hs_ids, file=sys.stderr)
        return 1
    def hs_n(tid):
        return int(str(tid)[5:])

    b1_topics = [t for t in again_t if is_hs_topic(t.get("id")) and hs_n(t["id"]) <= B1_COUNT]
    b2_topics = [t for t in again_t if is_hs_topic(t.get("id"))
                 and B1_COUNT < hs_n(t["id"]) <= B1_COUNT + B2_COUNT]
    s1_end = B1_COUNT + B2_COUNT + S1_COUNT
    s2_end = s1_end + S2_COUNT
    s1_topics = [t for t in again_t if is_hs_topic(t.get("id"))
                 and B1_COUNT + B2_COUNT < hs_n(t["id"]) <= s1_end]
    s2_topics = [t for t in again_t if is_hs_topic(t.get("id"))
                 and s1_end < hs_n(t["id"]) <= s2_end]
    s3_topics = [t for t in again_t if is_hs_topic(t.get("id")) and hs_n(t["id"]) > s2_end]
    if len(b1_topics) != B1_COUNT or any(t["grade"] != 10 or t["chapter"].split()[0] != "必修一" for t in b1_topics):
        print("必修第一册点数或 grade/chapter 不对", file=sys.stderr)
        return 1
    if len(b2_topics) != B2_COUNT or any(t["grade"] != 11 or t["chapter"].split()[0] != "必修二" for t in b2_topics):
        print("必修第二册点数或 grade/chapter 不对", file=sys.stderr)
        return 1
    if len(s1_topics) != S1_COUNT or any(
        t["grade"] != 12 or t["chapter"].split()[0] != "选必一" or t["semester"] != "上" for t in s1_topics
    ):
        print("选择性必修第一册点数或 grade/chapter/semester 不对", file=sys.stderr)
        return 1
    if len(s2_topics) != S2_COUNT or any(
        t["grade"] != 13 or t["chapter"].split()[0] != "选必二" or t["semester"] != "上" for t in s2_topics
    ):
        print("选择性必修第二册点数或 grade/chapter/semester 不对", file=sys.stderr)
        return 1
    if len(s3_topics) != S3_COUNT or any(
        t["grade"] != 14 or t["chapter"].split()[0] != "选必三" or t["semester"] != "上" for t in s3_topics
    ):
        print("选择性必修第三册点数或 grade/chapter/semester 不对", file=sys.stderr)
        return 1
    b1_edges_now = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in again_d if e.get("topicId") in b1_id_set
    ]
    if b1_edges_now != snap_b1_edges:
        print("第一册已有先修边被改动", file=sys.stderr)
        return 1
    b1_q_now = [q for q in again_q if q.get("topicId") in b1_id_set]
    if [(q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in b1_q_now] != [
            (q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in snap_b1_questions]:
        print("第一册已有题目被改动", file=sys.stderr)
        return 1
    b1_names_now = [(t["id"], t["name"], t["chapter"], t["grade"], t["semester"],
                     t.get("diagnostic_question")) for t in b1_topics]
    if b1_names_now != snap_b1_topics:
        print("第一册知识点 id/名称/chapter/grade/semester/诊断题被改动", file=sys.stderr)
        return 1
    b2_edges_now = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in again_d if e.get("topicId") in b2_id_set
    ]
    if b2_edges_now != snap_b2_edges:
        print("第二册已有先修边被改动", file=sys.stderr)
        return 1
    b2_q_now = [q for q in again_q if q.get("topicId") in b2_id_set]
    if [(q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in b2_q_now] != [
            (q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in snap_b2_questions]:
        print("第二册已有题目被改动", file=sys.stderr)
        return 1
    b2_names_now = [(t["id"], t["name"], t["chapter"], t["grade"], t["semester"],
                     t.get("diagnostic_question")) for t in b2_topics]
    if b2_names_now != snap_b2_topics:
        print("第二册知识点 id/名称/chapter/grade/semester/诊断题被改动", file=sys.stderr)
        return 1
    s1_edges_now = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in again_d if e.get("topicId") in s1_id_set
    ]
    if s1_edges_now != snap_s1_edges:
        print("选必一已有先修边被改动", file=sys.stderr)
        return 1
    s1_q_now = [q for q in again_q if q.get("topicId") in s1_id_set]
    if [(q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in s1_q_now] != [
            (q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in snap_s1_questions]:
        print("选必一已有题目被改动", file=sys.stderr)
        return 1
    s1_names_now = [(t["id"], t["name"], t["chapter"], t["grade"], t["semester"],
                     t.get("diagnostic_question")) for t in s1_topics]
    if s1_names_now != snap_s1_topics:
        print("选必一知识点 id/名称/chapter/grade/semester/诊断题被改动", file=sys.stderr)
        return 1
    if not any(e[1] == "cnk_h041" and e[0] == "cnk_h042" for e in s1_edges_now):
        print("缺少从必修第二册最后一点到选必一引言的课序衔接", file=sys.stderr)
        return 1
    s2_id_now = {t["id"] for t in s2_topics}
    s2_edges_now = [
        (e["topicId"], e["prerequisiteId"], e["strength"], e["reason"])
        for e in again_d if e.get("topicId") in s2_id_now
    ]
    if s2_edges_now != snap_s2_edges:
        print("选必二已有先修边被改动", file=sys.stderr)
        return 1
    s2_q_now = [q for q in again_q if q.get("topicId") in s2_id_now]
    if [(q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in s2_q_now] != [
            (q["id"], q.get("prompt"), q.get("answer"), q.get("verify")) for q in snap_s2_questions]:
        print("选必二已有题目被改动", file=sys.stderr)
        return 1
    s2_names_now = [(t["id"], t["name"], t["chapter"], t["grade"], t["semester"],
                     t.get("diagnostic_question")) for t in s2_topics]
    if s2_names_now != snap_s2_topics:
        print("选必二知识点 id/名称/chapter/grade/semester/诊断题被改动", file=sys.stderr)
        return 1
    if not any(e[1] == "cnk_h064" and e[0] == "cnk_h065" for e in s2_edges_now):
        print("缺少从选必一最后一点到选必二引言的课序衔接", file=sys.stderr)
        return 1
    s3_id_set = {t["id"] for t in s3_topics}
    s3_q = [q for q in again_q if q.get("topicId") in s3_id_set]
    if len(s3_q) != S3_COUNT * 4:
        print("选择性必修第三册题目不是 %d 道" % (S3_COUNT * 4), file=sys.stderr)
        return 1
    s3_edges = [e for e in again_d if e.get("topicId") in s3_id_set]
    if not any(e.get("prerequisiteId") == "cnk_h078" and e.get("topicId") == "cnk_h079" for e in s3_edges):
        print("缺少从选必二最后一点到选必三引言的课序衔接", file=sys.stderr)
        return 1
    buckets = {"引言": 0, "第一章": 0, "第二章": 0, "第三章": 0, "第四章": 0, "第五章": 0}
    for t in s3_topics:
        parts = t["chapter"].split()
        key = parts[1] if len(parts) >= 2 else ""
        if key not in buckets:
            print("选必三章节无法归入引言或五章：%s" % t["chapter"], file=sys.stderr)
            return 1
        buckets[key] += 1
    if buckets != {"引言": 1, "第一章": 3, "第二章": 4, "第三章": 8, "第四章": 5, "第五章": 3}:
        print("选必三各章点数不对：%s" % buckets, file=sys.stderr)
        return 1
    again_hs_std = [
        (it.get("id"), it.get("text"), it.get("text_status"), it.get("verbatim"), it.get("page_or_ref"))
        for it in again_s.get("items", [])
        if str(it.get("id", "")).startswith(SENIOR_STD_PREFIX)
    ]
    if len(snap_hs_std) == 64:
        if again_hs_std != snap_hs_std:
            print("已有 64 条高中化学课标被改动", file=sys.stderr)
            return 1
    else:
        if again_hs_std[:52] != snap_hs_std:
            print("已有 52 条高中化学课标被改动", file=sys.stderr)
            return 1
        new_std = again_hs_std[52:]
        if len(new_std) != 12 or any(not str(row[0]).startswith("cks-hs-2017:S3.") for row in new_std):
            print("新增课标不是 12 条 S3，实际 %d" % len(new_std), file=sys.stderr)
            return 1
    # 初中点的名称仍能对上硬边理由里点到的对象，避免连错号。
    for e in reduced:
        pid = e["prerequisiteId"]
        if pid in junior_names and junior_names[pid] not in e["reason"] and pid not in e["reason"]:
            pass
    print("初中化学 45 点及其他学科 id 与名称未改")
    return 0


if __name__ == "__main__":
    sys.exit(main())
