# -*- coding: utf-8 -*-
"""高中地理、生物、历史共用的编译器：把 Senior 实例里登记的课序、课标转述、知识点、题目和先修
写进 data/topics.json、dependencies.json、questions.json、cn-curriculum-standards.json。

只清除并重写本科高中点（id 前缀 cnX_h）、本科高中课标条目和 std_key 对象；初中点与其他学科原样保留。
可重复运行，同输入同输出。由 geo_hs_build.py / bio_hs_build.py / his_hs_build.py 调用。
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

from senior_lib import choice_verify
from verify_questions import verify_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


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


def reduce_senior(edges, is_senior):
    """只约简高中点上的冗余边：hard 仅当另有全 hard 路径时删；soft 只要另有路径就删。不改初中边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_senior(e["topicId"]):
            kept.append(e)
            continue
        lst = adj[e["topicId"]]
        idx = next(i for i, (p, s) in enumerate(lst) if p == e["prerequisiteId"] and s == e["strength"])
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
            "id": qid, "topicId": tid, "difficulty": q["diff"], "type": "numeric",
            "prompt": q["prompt"], "answer": q["answer"], "explanation": q["expl"], "verify": q["verify"],
        }, q["answer"]
    texts = list(q["wrongs"])
    texts.insert(slot % 4, q["right"])
    keys = list("ABCD")
    pos = texts.index(q["right"])
    return {
        "id": qid, "topicId": tid, "difficulty": q["diff"], "type": "choice", "prompt": q["prompt"],
        "choices": [{"key": keys[i], "text": texts[i]} for i in range(4)],
        "answer": keys[pos], "explanation": q["expl"], "verify": choice_verify(q["right"]),
    }, q["right"]


def soft_reason(S, prev, cur):
    ed, lab = S.edition, S.label
    if prev["grade"] == cur["grade"]:
        return "按%s高中%s%s的教学顺序，先学「%s」，再学「%s」。" % (
            ed, lab, S.book_title[cur["grade"]], prev["name"], cur["name"])
    return "按%s高中%s课序，学完%s的「%s」后进入%s的「%s」。" % (
        ed, lab, S.book_title[prev["grade"]], prev["name"], S.book_title[cur["grade"]], cur["name"])


def run(S):
    is_senior = lambda tid: str(tid).startswith(S.id_prefix)  # noqa: E731
    is_junior = lambda tid: str(tid).startswith(S.junior_prefix)  # noqa: E731
    partial = os.environ.get("SENIOR_PARTIAL") == "1"
    if partial:
        # 开发期：只编译已登记内容的点，课标缺引用也不报错；正式构建不要设置
        S.PLAN[:] = [r for r in S.PLAN if r["key"] in S.HS]
        S.ORDER.clear()
        S.ORDER.update({r["key"]: i for i, r in enumerate(S.PLAN)})
        S.count_expect = {}
    PLAN, HS = S.PLAN, S.HS
    if not PLAN:
        print("课序为空", file=sys.stderr)
        return 1
    missing = [row["key"] for row in PLAN if row["key"] not in HS]
    extra = [key for key in HS if key not in S.PLAN_BY_KEY]
    if missing or extra:
        print("草稿与课序不一致：缺 %s，多 %s" % (missing, extra), file=sys.stderr)
        return 1
    for g, n in S.count_expect.items():
        have = sum(1 for r in PLAN if r["grade"] == g)
        if have != n:
            print("%s 应有 %d 点，实际 %d" % (S.book_words[g], n, have), file=sys.stderr)
            return 1

    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    junior = {t["id"]: t for t in topics if is_junior(t["id"])}
    if not junior:
        print("找不到初中点 %s*" % S.junior_prefix, file=sys.stderr)
        return 1
    extra_ids = {
        t["id"] for t in topics
        if any(str(t["id"]).startswith(p) for p in S.extra_prereq_prefixes)
    }

    base_topics = [t for t in topics if not is_senior(t["id"])]
    base_deps = [e for e in deps if not is_senior(e["topicId"])]
    base_questions = [q for q in questions if not is_senior(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not str(it.get("id", "")).startswith(S.std_prefix)]
    if any(is_senior(e["prerequisiteId"]) for e in base_deps):
        print("有非本科高中点的边把本科高中点当先修，无法安全重建", file=sys.stderr)
        return 1

    # ---- 课标
    std_items = []
    seen_std = Counter()
    for tail, domain, section, text in S.CLAUSES:
        book = tail.split(".")[0]
        seen_std[book] += 1
        if S.CHECK is not None:
            page_ref, text_status = S.CHECK[tail]
        else:
            page_ref = "待核"
            text_status = "公开转述，未与课程标准 PDF 逐页核对；%s本图谱自编号。" % S.book_words[S.code_grade[book]]
        std_items.append({
            "id": S.std_prefix + tail, "domain": domain, "section": section,
            "clause": "(%d)" % seen_std[book], "text": text, "page_or_ref": page_ref, "verbatim": False,
            "text_status": text_status,
        })
    std_by_tail = {it["id"][len(S.std_prefix):]: it["id"] for it in std_items}
    cited = set()

    id_of = {row["key"]: "%s%03d" % (S.id_prefix, i) for i, row in enumerate(PLAN, start=1)}

    def resolve_pid(ref, key):
        if ref.startswith("J:"):
            pid = ref[2:]
            if pid not in junior:
                print("%s 的初中先修不存在：%s" % (key, pid), file=sys.stderr)
                return None
            return pid
        if ref.startswith("P:"):
            pid = ref[2:]
            if pid not in extra_ids:
                print("%s 的跨学段先修不存在或不在允许前缀内：%s" % (key, pid), file=sys.stderr)
                return None
            return pid
        if ref not in id_of or S.ORDER[ref] >= S.ORDER[key]:
            print("%s 的先修 %s 不存在或不在它前面" % (key, ref), file=sys.stderr)
            return None
        return id_of[ref]

    new_topics, new_questions = [], []
    hard_pairs = {}
    for i, row in enumerate(PLAN, start=1):
        key = row["key"]
        draft = HS[key]
        tid = id_of[key]
        refs = []
        for tail in draft["std"]:
            if tail not in std_by_tail:
                print("%s 引用了不存在的课标 %s" % (key, tail), file=sys.stderr)
                return 1
            cited.add(tail)
            refs.append({"id": std_by_tail[tail], "confidence": "inferred", "note": S.std_note})
        built, diag = [], None
        for n, q in enumerate(draft["qs"], start=1):
            obj, shown = build_question(tid, n, q, slot=i + n)
            built.append(obj)
            if n == 1:
                diag = shown
        if built[0]["type"] != "choice" or built[0]["difficulty"] != "basic":
            print("%s 诊断题必须是 basic 选择题" % key, file=sys.stderr)
            return 1
        new_topics.append({
            "id": tid, "name": row["name"], "domain": draft["domain"], "grade": row["grade"],
            "semester": row["semester"], "chapter": row["chapter"], "type": draft["type"],
            "description": draft["description"], "mastery_criteria": draft["mastery"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag},
            "external": False, "subject": S.subject, "standards": refs,
        })
        new_questions.extend(built)
        for ref, reason, strength in draft["pre"]:
            if partial and not ref.startswith("J:") and not ref.startswith("P:") and ref not in id_of:
                continue  # 开发期：先修指向还没登记内容的点，先跳过
            if not str(reason).strip():
                print("%s 先修缺少理由：%s" % (key, ref), file=sys.stderr)
                return 1
            pid = resolve_pid(ref, key)
            if pid is None:
                return 1
            pair = (tid, pid)
            if pair in hard_pairs:
                print("重复先修 %s → %s" % pair, file=sys.stderr)
                return 1
            hard_pairs[pair] = (reason, strength)

    unused = [c[0] for c in S.CLAUSES if c[0] not in cited]
    if unused and not partial:
        print("课标条目没有被任何知识点引用：%s" % "、".join(unused), file=sys.stderr)
        return 1
    first = PLAN[0]["key"]
    if not partial and not any(ref.startswith("J:") and st == "hard" for ref, _r, st in HS[first]["pre"]):
        print("%s 是本科高中第一个点，必须硬连至少一个初中点" % first, file=sys.stderr)
        return 1

    # ---- 边：显式先修 + 课序软边
    new_edges = []
    for i, row in enumerate(PLAN):
        tid = id_of[row["key"]]
        for ref, reason, strength in HS[row["key"]]["pre"]:
            if partial and not ref.startswith("J:") and not ref.startswith("P:") and ref not in id_of:
                continue
            pid = resolve_pid(ref, row["key"])
            if pid is None:
                return 1
            new_edges.append({"topicId": tid, "prerequisiteId": pid, "strength": strength, "reason": reason})
        if i > 0:
            prev = PLAN[i - 1]
            pid = id_of[prev["key"]]
            if (tid, pid) not in hard_pairs:
                new_edges.append({
                    "topicId": tid, "prerequisiteId": pid, "strength": "soft",
                    "reason": soft_reason(S, prev, row),
                })
    merged, dropped = reduce_senior(base_deps + new_edges, is_senior)
    senior_edges = [e for e in merged if is_senior(e["topicId"])]
    covered = {e["topicId"] for e in senior_edges}
    lonely = [t["id"] for t in new_topics if t["id"] not in covered]
    if lonely:
        print("约简后仍无先修：%s" % "、".join(lonely), file=sys.stderr)
        return 1
    def prereq_ok(pid):
        if is_senior(pid) or is_junior(pid):
            return True
        return any(str(pid).startswith(p) for p in S.extra_prereq_prefixes)

    for e in senior_edges:
        if not prereq_ok(e["prerequisiteId"]):
            print("高中边连到了其他学科或非初中点：%s" % e["prerequisiteId"], file=sys.stderr)
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

    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + std_items
    standards_out[S.std_key] = dict(S.std_meta)

    by_book = Counter(r["grade"] for r in PLAN)
    n_hard = sum(1 for e in senior_edges if e["strength"] == "hard")
    n_soft = len(senior_edges) - n_hard
    n_to_junior = sum(1 for e in senior_edges if is_junior(e["prerequisiteId"]))
    print("%s高中知识点 %d" % (S.label, len(new_topics)))
    for g in sorted(by_book):
        print("  %s %d" % (S.book_words[g], by_book[g]))
    for name, n in Counter(t["domain"] for t in new_topics).items():
        print("  领域 %s %d" % (name, n))
    print("高中边写入 %d（约简删去 %d）；hard %d，soft %d；连到初中的 %d；平均先修 %.2f" % (
        len(senior_edges), dropped, n_hard, n_soft, n_to_junior, len(senior_edges) / float(len(new_topics))))
    print("题目 %d；课标条目 %d" % (len(new_questions), len(std_items)))

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", merged)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t, again_d = load("topics.json"), load("dependencies.json")
    again_q, again_s = load("questions.json"), load("cn-curriculum-standards.json")
    if ([t for t in again_t if not is_senior(t["id"])] != base_topics
            or [e for e in again_d if not is_senior(e["topicId"])] != base_deps
            or [q for q in again_q if not is_senior(q.get("topicId"))] != base_questions
            or [it for it in again_s.get("items", []) if not str(it.get("id", "")).startswith(S.std_prefix)] != base_items):
        print("其他数据在写回后发生了变化", file=sys.stderr)
        return 1
    print("初中点、其他学科与其他课标原样保留")
    return 0
