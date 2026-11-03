#!/usr/bin/env python3
"""把初中历史草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

可以重复运行：先去掉已有的 cnh_ 知识点和 chs- 课标条目，再按脚本重新写入。
不改数学、英语、物理、语文、科学、道德与法治、地理的知识点、先修、题目和课标。
先修边只对历史边做传递约简。

用法：python3 scripts/his_build.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import his_g7  # noqa: E402,F401
import his_g8  # noqa: E402,F401
import his_g9  # noqa: E402,F401
import his_edges  # noqa: E402,F401
from his_lib import HARD, CODE_OF, STANDARD_ROWS, TOPICS, chapter, check_question, materialise_questions  # noqa: E402
from his_figs import figure_for  # noqa: E402
from verify_questions import verify_all  # noqa: E402

CHAPTER_RE = re.compile(r"^([一二三四五六七八九])年级([上下全])册 (第\d+单元|预备单元\d) (.+)$")
VOLUMES = ["7上", "7下", "8上", "8下", "9上", "9下"]
EXPECT = {"7上": 21, "7下": 22, "8上": 22, "8下": 24, "9上": 22, "9下": 23}
LABEL = {"7上": "七上", "7下": "七下", "8上": "八上", "8下": "八下", "9上": "九上", "9下": "九下"}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_his_topic_id(tid):
    return str(tid).startswith("cnh_")


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


def reduce_history(edges):
    """只删除历史知识点上的冗余边。hard 仅当另有全 hard 路径时删；soft 只要另有路径就删。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_his_topic_id(e["topicId"]):
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
    for symbol, code, section, text in STANDARD_ROWS:
        domain = CODE_OF[code]
        counters[code] = counters.get(code, 0) + 1
        sid = "chs-2022:%s.%02d" % (code, counters[code])
        id_of[symbol] = sid
        items.append({
            "id": sid,
            "domain": domain,
            "section": section,
            "clause": "(%d)" % counters[code],
            "text": text,
            "page_or_ref": "待核",
            "verbatim": False,
            "text_status": "公开转述，未与《义务教育历史课程标准（2022年版）》逐页核对",
        })
    return id_of, items


def build_question(tid, index, made, slot):
    qid = "%s_q%d" % (tid, index)
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


def rank_of(spec):
    return spec["grade"] * 2 + (1 if spec["semester"] == "下" else 0)


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    order = {t["key"]: i for i, t in enumerate(TOPICS)}
    TOPICS.sort(key=lambda t: (rank_of(t), t["unit"], order[t["key"]]))
    pre = defaultdict(set)
    for src, dst, _r in HARD:
        pre[src].add(dst)
    placed, out = set(), []
    pending = list(TOPICS)
    while pending:
        for j, t in enumerate(pending):
            pending_keys = {x["key"] for x in pending}
            if all(d in placed or d not in order for d in pre[t["key"]] if d in pending_keys):
                out.append(pending.pop(j))
                placed.add(t["key"])
                break
        else:
            print("硬先修成环", file=sys.stderr)
            return 1
    TOPICS[:] = out
    by_vol = Counter("%d%s" % (t["grade"], t["semester"]) for t in TOPICS)
    for k in VOLUMES:
        n = by_vol[k]
        if n != EXPECT[k]:
            print("%s 有 %d 个知识点，应为 %d" % (k, n, EXPECT[k]), file=sys.stderr)
            return 1
    keys = [t["key"] for t in TOPICS]
    if len(set(keys)) != len(keys):
        print("知识点 key 重复", file=sys.stderr)
        return 1

    base_topics = [t for t in topics if not is_his_topic_id(t.get("id"))]
    base_deps = [e for e in deps if not is_his_topic_id(e.get("topicId")) and not is_his_topic_id(e.get("prerequisiteId"))]
    base_questions = [q for q in questions if not is_his_topic_id(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not str(it.get("id", "")).startswith("chs-")]

    id_of_std, new_items = build_standards()
    used_std = {t["std"] for t in TOPICS}
    missing_std = [row[0] for row in STANDARD_ROWS if row[0] not in used_std]
    if missing_std:
        print("课标条目没有被任何知识点引用：%s" % "、".join(missing_std), file=sys.stderr)
        return 1
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
        if rank_of(by_key[dst]) > rank_of(by_key[src]):
            print("硬先修册次更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        if (src, dst) in hard_pairs:
            print("重复硬边 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        hard_pairs[(src, dst)] = reason

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cnh_j%03d" % i
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
            fig = figure_for(q)
            if fig:
                q["figure"] = fig
            built.append(q)
            if n == 1:
                diag_answer = shown
        ch = chapter(spec["grade"], spec["semester"], spec["unit"])
        if not CHAPTER_RE.match(ch):
            print("%s 章节格式无法按册浏览：%s" % (spec["key"], ch), file=sys.stderr)
            return 1
        ref = {"id": id_of_std[spec["std"]], "confidence": spec["conf"]}
        if spec.get("note"):
            ref["note"] = spec["note"]
        topic = {
            "id": tid,
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": spec["grade"],
            "semester": spec["semester"],
            "chapter": ch,
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag_answer},
            "external": False,
            "subject": "history",
            "standards": [ref],
        }
        if i == 1:
            topic["root_reason"] = "七年级上册从史前时期讲起，远古时期的人类活动是初中历史的起点，前面没有更早的初中历史知识点。"
        new_topics.append(topic)
        new_questions.extend(built)

    raw = []
    for i in range(1, len(TOPICS)):
        cur = TOPICS[i]["key"]
        prev = TOPICS[i - 1]["key"]
        if (cur, prev) in hard_pairs:
            continue
        reason = "按统编版历史的教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
        raw.append((cur, prev, "soft", reason))
    for src, dst, reason in HARD:
        raw.append((src, dst, "hard", reason))

    new_edges = []
    seen = set()
    for src, dst, strength, reason in raw:
        if index[dst] >= index[src]:
            print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        if rank_of(by_key[dst]) > rank_of(by_key[src]):
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

    merged_deps, dropped = reduce_history(base_deps + new_edges)
    his_edges_out = [e for e in merged_deps if is_his_topic_id(e["topicId"])]
    if any(not is_his_topic_id(e["prerequisiteId"]) for e in his_edges_out):
        print("历史边连到了其他学科", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in his_edges_out}
    missing = [t["id"] for t in new_topics if t["id"] != "cnh_j001" and t["id"] not in covered]
    if missing:
        print("约简后仍无先修：%s" % "、".join(missing), file=sys.stderr)
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

    kept_std = {k: v for k, v in standards.items() if k != "items" and k != "history"}
    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + new_items
    standards_out["history"] = {
        "title": "义务教育历史课程标准（2022年版）",
        "issuer": "中华人民共和国教育部",
        "year": 2022,
        "stage": "第四学段（7–9年级）",
        "note": "条目是对历史课标中国史、世界史内容要求的公开转述，不是逐页核对的原文。verbatim 为 false，page_or_ref 为「待核」。编号 chs-2022 是本图谱编的，不是教育部原编号。七上按2024秋修订统编目录，七下按2025春，八上按2025秋，八下按2026春，九上按2026秋修订目录；九下修订版公开目录未上线，暂按现行统编九年级下册。",
    }
    for k, v in kept_std.items():
        standards_out[k] = v

    snapshots = {}
    for prefix in ("cnm_", "cne_", "cnp_", "cnc_", "cns_", "cnd_", "cng_", "cnb_"):
        snapshots[prefix] = [(t["id"], t["name"]) for t in base_topics if str(t["id"]).startswith(prefix)]

    n_hard = sum(1 for e in his_edges_out if e["strength"] == "hard")
    n_soft = sum(1 for e in his_edges_out if e["strength"] == "soft")
    by_dom = Counter(t["domain"] for t in new_topics)
    print("历史知识点 %d" % len(new_topics))
    for k in VOLUMES:
        print("  %s %d" % (LABEL[k], by_vol[k]))
    for name in ("中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史"):
        print("  %s %d" % (name, by_dom[name]))
    print("历史边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(his_edges_out), dropped, n_hard, n_soft))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", merged_deps)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    again_topics = [t for t in again_t if not is_his_topic_id(t.get("id"))]
    again_deps = [e for e in again_d if not is_his_topic_id(e.get("topicId")) and not is_his_topic_id(e.get("prerequisiteId"))]
    again_qs = [q for q in again_q if not is_his_topic_id(q.get("topicId"))]
    again_items = [it for it in again_s.get("items", []) if not str(it.get("id", "")).startswith("chs-")]
    if again_topics != base_topics or again_deps != base_deps or again_qs != base_questions or again_items != base_items:
        print("其他学科数据在写回后发生了变化", file=sys.stderr)
        return 1
    labels = {"cnm_": "数学", "cne_": "英语", "cnp_": "物理", "cnc_": "语文", "cns_": "科学", "cnd_": "道德与法治", "cng_": "地理", "cnb_": "生物"}
    for prefix, label in labels.items():
        if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith(prefix)] != snapshots[prefix]:
            print("%s知识点 id 或名称变了" % label, file=sys.stderr)
            return 1
    for k, v in kept_std.items():
        if again_s.get(k) != v:
            print("原课标对象 %s 发生了变化" % k, file=sys.stderr)
            return 1
    if again_s.get("history", {}).get("title") != "义务教育历史课程标准（2022年版）":
        print("历史课标标题不正确", file=sys.stderr)
        return 1
    print("数学 %d、英语 %d、物理 %d、语文 %d、科学 %d、道德与法治 %d、地理 %d、生物 %d 个知识点的 id 与名称未改" % tuple(
        len(snapshots[p]) for p in ("cnm_", "cne_", "cnp_", "cnc_", "cns_", "cnd_", "cng_", "cnb_")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
