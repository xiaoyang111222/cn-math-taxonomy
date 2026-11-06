#!/usr/bin/env python3
"""把小学英语草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

只应在还没有 cne_p001 时运行一次。已经编译过再跑会拒绝，避免重复追加。
先修边只对新增的英语边做传递约简，不改已有数学边。

用法：python3 scripts/en_build.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import en_topics  # noqa: E402,F401
from en_lib import (  # noqa: E402
    HARD, STANDARD_ROWS, TOPICS, check_question, materialise_questions, yy_fields,
)
from verify_questions import verify_all  # noqa: E402

EN_CODES = {"PH": "语音", "VO": "词汇", "GR": "语法", "FU": "日常表达", "RW": "读写"}


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


def reduce_english(edges):
    """只删除英语知识点上的冗余新边。hard 仅当另有全 hard 路径时删；soft 只要另有路径就删。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not str(e["topicId"]).startswith("cne_"):
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


def build_standards():
    counters = {}
    id_of = {}
    items = []
    for symbol, level, code, domain, section, text in STANDARD_ROWS:
        if domain != EN_CODES[code]:
            raise SystemExit("课标领域不一致：%s" % symbol)
        key = (level, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "ces-2022:%s.%s.%02d" % (level, code, counters[key])
        id_of[symbol] = sid
        ref, status = yy_fields(symbol)
        if ref != "待核" and ("人教社电子书印刷页" not in ref or "转述" not in ref):
            raise SystemExit("课标页码必须写明人教社电子书印刷页和转述：%s" % symbol)
        items.append({
            "id": sid,
            "domain": domain,
            "section": section,
            "clause": "(%d)" % counters[key],
            "text": text,
            "page_or_ref": ref,
            "verbatim": False,
            "text_status": status,
        })
    return id_of, items


def build_question(tid, index, made, slot):
    qid = "%s_q%d" % (tid, index)
    if made["t"] == "numeric":
        return {
            "id": qid,
            "topicId": tid,
            "difficulty": made["d"],
            "type": "numeric",
            "prompt": made["p"],
            "answer": made["a"],
            "explanation": made["e"],
            "verify": made["v"],
        }, made["a"]
    texts = list(made["w"])
    texts.insert(slot % 4, made["a"])
    keys = list("ABCD")
    pos = texts.index(made["a"])
    return {
        "id": qid,
        "topicId": tid,
        "difficulty": made["d"],
        "type": "choice",
        "prompt": made["p"],
        "choices": [{"key": keys[i], "text": texts[i]} for i in range(4)],
        "answer": keys[pos],
        "explanation": made["e"],
        "verify": json.dumps(made["a"], ensure_ascii=False),
    }, made["a"]


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")
    if any(str(t.get("id", "")).startswith("cne_") for t in topics):
        print("已经有 cne_ 知识点。en_build.py 不能重复编译。", file=sys.stderr)
        return 1
    if not (150 <= len(TOPICS) <= 250):
        print("知识点数量 %d 不在 150–250" % len(TOPICS), file=sys.stderr)
        return 1
    if TOPICS[0]["key"] != "ph_alpha":
        print("第一个知识点必须是 ph_alpha", file=sys.stderr)
        return 1

    id_of_std, new_items = build_standards()
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    by_key = {t["key"]: t for t in TOPICS}
    names = {t["key"]: t["name"] for t in TOPICS}
    hard_pairs = {}
    for src, dst, reason in HARD:
        if src not in index or dst not in index:
            print("硬先修指向未登记的知识点：%s → %s" % (src, dst), file=sys.stderr)
            return 1
        if index[dst] >= index[src]:
            print("硬先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        if (src, dst) in hard_pairs:
            print("重复硬边 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        hard_pairs[(src, dst)] = reason

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_p%03d" % i
        id_of[spec["key"]] = tid
        if spec["std"] not in id_of_std:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        made = materialise_questions(spec)
        for q in made:
            check_question(spec["key"], q)
        built = []
        diag_answer = None
        for n, item in enumerate(made, start=1):
            q, shown = build_question(tid, n, item, slot=i + n)
            built.append(q)
            if n == 1:
                diag_answer = shown
        ref = {"id": id_of_std[spec["std"]], "confidence": spec["conf"]}
        if spec.get("note"):
            ref["note"] = spec["note"]
        topic = {
            "id": tid,
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": spec["grade"],
            "semester": spec["semester"],
            "chapter": __import__("en_lib").chapter(spec["grade"], spec["semester"], spec["unit"]),
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag_answer},
            "external": False,
            "subject": "english",
            "standards": [ref],
        }
        if spec["key"] == "ph_alpha":
            topic["root_reason"] = "三年级英语从认读字母表开始，前面没有更早的小学英语知识点。"
        new_topics.append(topic)
        new_questions.extend(built)

    raw = []
    seen = set()
    for i in range(1, len(TOPICS)):
        cur = TOPICS[i]["key"]
        prev = TOPICS[i - 1]["key"]
        if (cur, prev) in hard_pairs:
            continue
        reason = "按三年级起点的常见教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
        raw.append((cur, prev, "soft", reason))
    for src, dst, reason in HARD:
        raw.append((src, dst, "hard", reason))

    new_edges = []
    for src, dst, strength, reason in raw:
        if index[dst] >= index[src]:
            print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        ra = by_key[src]["grade"] * 2 + (1 if by_key[src]["semester"] == "下" else 0)
        rb = by_key[dst]["grade"] * 2 + (1 if by_key[dst]["semester"] == "下" else 0)
        if rb > ra:
            print("先修年级更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        key = (id_of[src], id_of[dst])
        if key in seen:
            print("重复边 %s → %s" % key, file=sys.stderr)
            return 1
        seen.add(key)
        new_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": id_of[dst],
            "strength": strength,
            "reason": reason,
        })

    merged_deps, dropped = reduce_english(deps + new_edges)
    eng_edges = [e for e in merged_deps if str(e["topicId"]).startswith("cne_")]
    if any(not str(e["prerequisiteId"]).startswith("cne_") for e in eng_edges):
        print("英语边连到了数学知识点", file=sys.stderr)
        return 1
    if any(str(e["topicId"]).startswith("cne_") for e in deps):
        print("原依赖里已有英语边", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in eng_edges}
    missing = [t["id"] for t in new_topics if t["id"] != "cne_p001" and t["id"] not in covered]
    if missing:
        print("约简后仍无先修：%s" % "、".join(missing), file=sys.stderr)
        return 1

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    n_hard = sum(1 for e in eng_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in eng_edges if e["strength"] == "soft")
    by_grade = Counter("%d%s" % (t["grade"], t["semester"]) for t in new_topics)
    by_dom = Counter(t["domain"] for t in new_topics)
    print("英语知识点 %d" % len(new_topics))
    for k in ["3上", "3下", "4上", "4下", "5上", "5下", "6上", "6下"]:
        print("  %s %d" % (k, by_grade[k]))
    for k, v in by_dom.most_common():
        print("  %s %d" % (k, v))
    print("英语边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(eng_edges), dropped, n_hard, n_soft))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))

    old_topic_n = len(topics)
    old_dep_n = len(deps)
    old_q_n = len(questions)
    old_std_n = len(standards["items"])
    standards["english"] = {
        "title": "义务教育英语课程标准（2022年版）",
        "issuer": "中华人民共和国教育部",
        "year": 2022,
        "stage": "义务教育三级（3～4年级，一级）与四级（5～6年级，二级）",
        "note": (
            "2026-11-06 对照人教社电子书印刷页19–21（表9语音、表10词汇、表11语法）。"
            "语音、词汇、语法的 page_or_ref 记这些印刷页，text 仍是转述，verbatim 为 false。"
            "日常表达和读写的大图未打开，page_or_ref 仍为「待核」。"
            "编号 ces-2022 是本图谱编的，不是教育部原编号。教材册次另见核对文档。"
        ),
    }
    standards["items"].extend(new_items)
    dump("topics.json", topics + new_topics)
    dump("dependencies.json", merged_deps)
    dump("questions.json", questions + new_questions)
    dump("cn-curriculum-standards.json", standards)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    if again_t[:old_topic_n] != topics or again_d[:old_dep_n] != deps or again_q[:old_q_n] != questions:
        print("数学数据在写回后发生了变化", file=sys.stderr)
        return 1
    if again_s["items"][:old_std_n] != standards["items"][:old_std_n]:
        print("原课标条目发生了变化", file=sys.stderr)
        return 1
    math_names = [(t["id"], t["name"]) for t in topics]
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cnm_")] != math_names:
        print("数学知识点 id 或名称变了", file=sys.stderr)
        return 1
    print("数学节点 %d 个 id 与名称未改" % len(math_names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
