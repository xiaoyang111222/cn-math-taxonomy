#!/usr/bin/env python3
"""把初中语文草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

只处理 cnc_j 知识点和第四学段（ccs-2022:4.*）课标。可以重复运行：先去掉已有的 cnc_j 再写入。
不改小学语文 cnc_p 的 id、名称、题目和边，也不回头约简小学语文边。
先修可以指向小学语文，不能指向其他学科。

用法：python3 scripts/zhj_build.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zhj_topics  # noqa: E402,F401
from zhj_lib import (  # noqa: E402
    CODES, HARD, STAGE4_REF, STAGE4_STATUS, STANDARD_ROWS, TOPICS,
    chapter, check_question, materialise_questions,
)
from verify_questions import verify_all  # noqa: E402

CHAPTER_RE = re.compile(r"^([一二三四五六七八九])年级([上下全])册 (第\d+单元|预备单元\d) (.+)$")
VOLUMES = ["7上", "7下", "8上", "8下", "9上", "9下"]
LABEL = {"7上": "七上", "7下": "七下", "8上": "八上", "8下": "八下", "9上": "九上", "9下": "九下"}
DOMAIN_ORDER = (
    "识字写字", "词语", "句子", "阅读理解",
    "古诗文积累", "文言文阅读", "名著阅读", "习作基础",
)
PRIMARY_SNAPSHOT_PREFIXES = (
    "cnm_", "cne_", "cnp_", "cnc_p", "cns_", "cnd_", "cnh_", "cng_", "cnb_", "cnk_",
)
PRIMARY_SNAPSHOT_LABELS = {
    "cnm_": "数学", "cne_": "英语", "cnp_": "物理", "cnc_p": "小学语文",
    "cns_": "科学", "cnd_": "道德与法治", "cnh_": "历史", "cng_": "地理",
    "cnb_": "生物", "cnk_": "化学",
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_junior_zh_id(tid):
    return str(tid).startswith("cnc_j")


def is_primary_zh_id(tid):
    return str(tid).startswith("cnc_p")


def is_chinese_id(tid):
    return str(tid).startswith("cnc_")


def is_primary_ref(dst):
    s = str(dst)
    return s.startswith("p:") or s.startswith("cnc_p")


def is_stage4_std(sid):
    return str(sid).startswith("ccs-2022:4.")


def rank_of(spec):
    return spec["grade"] * 2 + (1 if spec["semester"] == "下" else 0)


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


def reduce_junior(edges):
    """只删除 cnc_j 上的冗余新边。不改小学语文边，也不改其他学科边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_junior_zh_id(e["topicId"]):
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
        if domain != CODES[code]:
            raise SystemExit("课标领域不一致：%s" % symbol)
        if level != "4":
            raise SystemExit("初中语文课标学段必须是 4：%s" % symbol)
        key = (level, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "ccs-2022:%s.%s.%02d" % (level, code, counters[key])
        id_of[symbol] = sid
        ref = STAGE4_REF.get(symbol)
        status = STAGE4_STATUS.get(symbol)
        if not ref or not status:
            raise SystemExit("第四学段缺少印刷页或核对说明：%s" % symbol)
        if not str(ref).startswith("人教社电子书印刷页") or "转述" not in ref:
            raise SystemExit("第四学段 page_or_ref 不合格：%s" % symbol)
        if "2026-11-06" not in status:
            raise SystemExit("第四学段 text_status 未记下核对日期：%s" % symbol)
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


def primary_key_map():
    """按 zh_lib 登记顺序，把 p:key 映射到现有 cnc_p 编号。"""
    import zh_g1  # noqa: F401
    import zh_g2  # noqa: F401
    import zh_g3  # noqa: F401
    import zh_g4  # noqa: F401
    import zh_g5  # noqa: F401
    import zh_g6  # noqa: F401
    from zh_lib import TOPICS as PRIMARY
    return {"p:%s" % t["key"]: "cnc_p%03d" % i for i, t in enumerate(PRIMARY, start=1)}, list(PRIMARY)


NEW_FOURTH = (
    "第四学段（7–9年级）12 条于 2026-11-06 对照人教社电子书"
    "《义务教育语文课程标准（2022年版）》印刷页 14–16"
    "（https://www.pep.com.cn/ebook/2022yjkcbz/yw/mobile/index.html ，"
    "大图 files/large/21.jpg、22.jpg、23.jpg）。"
    "该处是课程目标里的学段要求，印刷页 14–16 上没有名为【内容要求】的标题。"
    "课程内容部分的大图本次没有打开，不写入 page_or_ref。"
    "条目 text 仍是压缩转述，verbatim 为 false，"
    "page_or_ref 记人教社电子书印刷页，不是教育部 PDF 页码。"
    "未取得教育部官网 PDF。详见 docs/standards-verify-2026-11-06-junior-chinese.md。"
)
BLANKET_REF = "verbatim 为 false，page_or_ref 为「待核」。"
OLD_CLARIFIED_REF = (
    "verbatim 为 false。第一至第三学段 page_or_ref 仍为「待核」；"
    "第四学段 page_or_ref 记人教社电子书印刷页，不是教育部 PDF 页码。"
)
CLARIFIED_REF = (
    "verbatim 为 false。第一至第三学段 page_or_ref 记人教社电子书印刷页7–13，"
    "第四学段记印刷页14–16，都不是教育部 PDF 页码。"
)


def merge_chinese_meta(existing):
    meta = dict(existing or {})
    meta["title"] = "义务教育语文课程标准（2022年版）"
    meta["issuer"] = meta.get("issuer") or "中华人民共和国教育部"
    meta["year"] = 2022
    meta["stage"] = "第一至第四学段（1–9年级）"
    note = meta.get("note") or ""
    if "第一至第三学段" in note and "第一至第四学段" not in note:
        note = note.replace("第一至第三学段", "第一至第四学段", 1)
    marker = "第四学段（7–9年级）"
    if marker in note:
        note = note[:note.find(marker)].rstrip() + " " + NEW_FOURTH
    else:
        note = (note.rstrip() + " " + NEW_FOURTH).strip()
    if OLD_CLARIFIED_REF in note:
        note = note.replace(OLD_CLARIFIED_REF, CLARIFIED_REF, 1)
    elif BLANKET_REF in note:
        note = note.replace(BLANKET_REF, CLARIFIED_REF, 1)
    meta["note"] = note
    return meta


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    if not any(str(t.get("id", "")) == "cnc_p001" for t in topics):
        print("缺少小学语文 cnc_p001，不能单独编译初中。", file=sys.stderr)
        return 1

    if TOPICS:
        order = {t["key"]: i for i, t in enumerate(TOPICS)}
        TOPICS.sort(key=lambda t: (rank_of(t), t["unit"], order[t["key"]]))
        pre = defaultdict(set)
        for src, dst, _r in HARD:
            if not is_primary_ref(dst):
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
        keys = [t["key"] for t in TOPICS]
        if len(set(keys)) != len(keys):
            print("知识点 key 重复", file=sys.stderr)
            return 1
        if not (1 <= len(TOPICS) <= 220):
            print("知识点数量 %d 不在 1–220" % len(TOPICS), file=sys.stderr)
            return 1

    by_vol = Counter("%d%s" % (t["grade"], t["semester"]) for t in TOPICS)

    base_topics = [t for t in topics if not is_junior_zh_id(t.get("id"))]
    base_deps = [
        e for e in deps
        if not is_junior_zh_id(e.get("topicId")) and not is_junior_zh_id(e.get("prerequisiteId"))
    ]
    base_questions = [q for q in questions if not is_junior_zh_id(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not is_stage4_std(it.get("id", ""))]
    if any(is_junior_zh_id(t.get("id")) for t in base_topics):
        print("剥离初中语文知识点失败", file=sys.stderr)
        return 1
    if any(is_junior_zh_id(e.get("topicId")) or is_junior_zh_id(e.get("prerequisiteId")) for e in base_deps):
        print("剥离后的依赖里仍有初中语文边", file=sys.stderr)
        return 1

    primary_ids = {t["id"] for t in base_topics if is_primary_zh_id(t.get("id"))}
    snapshots = {
        prefix: [(t["id"], t["name"]) for t in base_topics if str(t["id"]).startswith(prefix)]
        for prefix in PRIMARY_SNAPSHOT_PREFIXES
    }

    id_of_std, new_items = build_standards()
    if TOPICS and all(by_vol[k] for k in VOLUMES):
        used_std = {t["std"] for t in TOPICS}
        missing_std = [row[0] for row in STANDARD_ROWS if row[0] not in used_std]
        if missing_std:
            print("课标条目没有被任何知识点引用：%s" % "、".join(missing_std), file=sys.stderr)
            return 1

    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    by_key = {t["key"]: t for t in TOPICS}
    names = {t["key"]: t["name"] for t in TOPICS}

    pmap = None
    primary_specs = None
    hard_pairs = {}
    resolved_hard = []
    for src, dst, reason in HARD:
        if src not in index:
            print("硬先修的后续未登记：%s" % src, file=sys.stderr)
            return 1
        if is_primary_ref(dst):
            if dst.startswith("p:"):
                if pmap is None:
                    pmap, primary_specs = primary_key_map()
                    if len(pmap) != len(primary_ids):
                        print("小学语文数量与 zh_lib 不一致：脚本 %d，数据 %d" % (
                            len(pmap), len(primary_ids)), file=sys.stderr)
                        return 1
                if dst not in pmap:
                    print("硬先修指向未知的小学知识点：%s → %s" % (src, dst), file=sys.stderr)
                    return 1
                pid = pmap[dst]
                pkey = dst[2:]
                pt = next(t for t in primary_specs if t["key"] == pkey)
                if rank_of(pt) > rank_of(by_key[src]):
                    print("小学先修比初中更晚：%s 依赖 %s" % (src, pkey), file=sys.stderr)
                    return 1
            else:
                pid = dst
                if pid not in primary_ids:
                    print("硬先修指向不存在的小学知识点：%s → %s" % (src, dst), file=sys.stderr)
                    return 1
        else:
            if dst not in index:
                print("硬先修指向未登记的知识点：%s → %s" % (src, dst), file=sys.stderr)
                return 1
            if index[dst] >= index[src]:
                print("硬先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            if rank_of(by_key[dst]) > rank_of(by_key[src]):
                print("硬先修册次更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            pid = None
        if (src, dst) in hard_pairs:
            print("重复硬边 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        hard_pairs[(src, dst)] = reason
        resolved_hard.append((src, dst, pid, reason))

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cnc_j%03d" % i
        id_of[spec["key"]] = tid
        if spec["std"] not in id_of_std:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        if spec["grade"] not in (7, 8, 9):
            print("%s 年级不是 7–9" % spec["key"], file=sys.stderr)
            return 1
        if spec["semester"] not in ("上", "下"):
            print("%s 学期非法" % spec["key"], file=sys.stderr)
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
            "subject": "chinese",
            "standards": [ref],
        }
        new_topics.append(topic)
        new_questions.extend(built)

    raw = []
    for i in range(1, len(TOPICS)):
        cur = TOPICS[i]["key"]
        prev = TOPICS[i - 1]["key"]
        if (cur, prev) in hard_pairs:
            continue
        reason = "按统编版语文的教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
        raw.append((cur, prev, "soft", reason, id_of[prev]))
    for src, dst, pid, reason in resolved_hard:
        pre_id = pid if pid else id_of[dst]
        raw.append((src, dst, "hard", reason, pre_id))

    if TOPICS and not any(src == TOPICS[0]["key"] for src, _, _, _, _ in raw):
        print("第一个初中知识点没有先修", file=sys.stderr)
        return 1

    new_edges = []
    seen = set()
    for src, dst, strength, reason, pre_id in raw:
        key = (id_of[src], pre_id)
        if key in seen:
            print("重复边 %s → %s" % key, file=sys.stderr)
            return 1
        seen.add(key)
        if not is_chinese_id(pre_id):
            print("语文边连到了其他学科 %s" % pre_id, file=sys.stderr)
            return 1
        new_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": pre_id,
            "strength": strength,
            "reason": reason,
        })

    merged_deps, dropped = reduce_junior(base_deps + new_edges)
    jun_edges = [e for e in merged_deps if is_junior_zh_id(e["topicId"])]
    if any(not is_chinese_id(e["prerequisiteId"]) for e in jun_edges):
        print("初中语文边连到了其他学科", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in jun_edges}
    missing = [t["id"] for t in new_topics if t["id"] not in covered]
    if missing:
        print("约简后仍无先修：%s" % "、".join(missing), file=sys.stderr)
        return 1

    if new_questions:
        checked = verify_all(new_questions)
        if checked["mismatch"] or checked["unverifiable"]:
            for m in checked["mismatch"][:40]:
                print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
            for m in checked["unverifiable"][:20]:
                print("题目无法核对 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
            print("题目核对未通过：mismatch %d，unverifiable %d" % (
                len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
            return 1

    n_hard = sum(1 for e in jun_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in jun_edges if e["strength"] == "soft")
    cross = [e for e in jun_edges if is_primary_zh_id(e["prerequisiteId"])]
    n_cross_h = sum(1 for e in cross if e["strength"] == "hard")
    n_cross_s = sum(1 for e in cross if e["strength"] == "soft")
    by_dom = Counter(t["domain"] for t in new_topics)
    print("初中语文知识点 %d" % len(new_topics))
    for k in VOLUMES:
        print("  %s %d" % (LABEL[k], by_vol[k]))
    for name in DOMAIN_ORDER:
        if by_dom[name]:
            print("  %s %d" % (name, by_dom[name]))
    print("初中语文边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(jun_edges), dropped, n_hard, n_soft))
    print("其中跨到小学 %d（hard %d，soft %d）" % (len(cross), n_cross_h, n_cross_s))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))

    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + new_items
    standards_out["chinese"] = merge_chinese_meta(standards.get("chinese"))

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", merged_deps)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    again_topics = [t for t in again_t if not is_junior_zh_id(t.get("id"))]
    again_deps = [
        e for e in again_d
        if not is_junior_zh_id(e.get("topicId")) and not is_junior_zh_id(e.get("prerequisiteId"))
    ]
    again_qs = [q for q in again_q if not is_junior_zh_id(q.get("topicId"))]
    again_items = [it for it in again_s.get("items", []) if not is_stage4_std(it.get("id", ""))]
    if again_topics != base_topics or again_deps != base_deps or again_qs != base_questions or again_items != base_items:
        print("小学语文或其他学科数据在写回后发生了变化", file=sys.stderr)
        return 1
    for prefix, label in PRIMARY_SNAPSHOT_LABELS.items():
        if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith(prefix)] != snapshots[prefix]:
            print("%s知识点 id 或名称变了" % label, file=sys.stderr)
            return 1
    if again_s.get("chinese", {}).get("title") != "义务教育语文课程标准（2022年版）":
        print("语文课标标题不正确", file=sys.stderr)
        return 1
    if "第四学段" not in str(again_s.get("chinese", {}).get("stage", "")):
        print("语文课标学段未写入第四学段", file=sys.stderr)
        return 1
    print("小学语文 %d 个知识点的 id 与名称未改；数学 %d、英语 %d、物理 %d" % (
        len(snapshots["cnc_p"]), len(snapshots["cnm_"]), len(snapshots["cne_"]), len(snapshots["cnp_"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
