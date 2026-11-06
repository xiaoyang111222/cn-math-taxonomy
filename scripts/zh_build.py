#!/usr/bin/env python3
"""把小学语文草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

可以重复运行：先去掉已有的 cnc_p 知识点和小学课标条目（ccs-2022 学段 1–3），再按脚本重新写入。
不改数学、英语、物理和初中语文 cnc_j 的知识点、先修、题目和第四学段课标。
先修边只对小学语文边做传递约简。

用法：python3 scripts/zh_build.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zh_g1  # noqa: E402,F401
import zh_g2  # noqa: E402,F401
import zh_g3  # noqa: E402,F401
import zh_g4  # noqa: E402,F401
import zh_g5  # noqa: E402,F401
import zh_g6  # noqa: E402,F401
import zh_edges  # noqa: E402,F401
from zh_lib import (  # noqa: E402
    HARD, STAGE13_REF, STAGE13_STATUS, STANDARD_ROWS, TOPICS,
    chapter, check_question, materialise_questions,
)
from verify_questions import verify_all  # noqa: E402

ZH_CODES = {
    "PY": "拼音", "SZ": "识字写字", "CY": "词语", "JZ": "句子",
    "YD": "阅读理解", "GS": "古诗文积累", "XZ": "习作基础",
}
CHAPTER_RE = re.compile(r"^([一二三四五六七八九])年级([上下全])册 (第\d+单元|预备单元\d) (.+)$")
VOLUMES = ["1上", "1下", "2上", "2下", "3上", "3下", "4上", "4下", "5上", "5下", "6上", "6下"]


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_zh_topic_id(tid):
    """小学语文 id。重跑时只清 cnc_p，不删初中 cnc_j。"""
    return str(tid).startswith("cnc_p")


def is_zh_junior_id(tid):
    return str(tid).startswith("cnc_j")


def is_primary_zh_std(sid):
    return bool(re.match(r"^ccs-2022:[123]\.", str(sid)))


def splice_where(original, pred, new_items):
    """用 new_items 按原顺序替换 original 里 pred 为真的项。条数不同时才改接到末尾。"""
    idxs = [i for i, x in enumerate(original) if pred(x)]
    if len(idxs) != len(new_items):
        kept = [x for x in original if not pred(x)]
        return kept + list(new_items)
    out = list(original)
    for i, item in zip(idxs, new_items):
        out[i] = item
    return out


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


def reduce_chinese(edges):
    """只删除小学语文（cnc_p）上的冗余边。hard 仅当另有全 hard 路径时删；soft 只要另有路径就删。不约简初中语文边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_zh_topic_id(e["topicId"]):
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
        if domain != ZH_CODES[code]:
            raise SystemExit("课标领域不一致：%s" % symbol)
        key = (level, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "ccs-2022:%s.%s.%02d" % (level, code, counters[key])
        id_of[symbol] = sid
        ref = STAGE13_REF.get(symbol)
        status = STAGE13_STATUS.get(symbol)
        if not ref or not status:
            raise SystemExit("第一至第三学段缺少印刷页或核对说明：%s" % symbol)
        if not str(ref).startswith("人教社电子书印刷页") or "转述" not in ref:
            raise SystemExit("第一至第三学段 page_or_ref 不合格：%s" % symbol)
        if "2026-11-06" not in status:
            raise SystemExit("第一至第三学段 text_status 未记下核对日期：%s" % symbol)
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


def rank_of(spec):
    return spec["grade"] * 2 + (1 if spec["semester"] == "下" else 0)


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    by_vol = Counter("%d%s" % (t["grade"], t["semester"]) for t in TOPICS)
    for k in VOLUMES:
        n = by_vol[k]
        # 一上至六下已按统编目录逐课覆盖。
        lo, hi = (30, 48) if k in ("1上", "1下", "2上", "2下", "3上", "3下", "4上", "4下", "5上", "5下", "6上", "6下") else (18, 22)
        if n < lo or n > hi:
            print("%s 有 %d 个知识点，每册应为 %d–%d" % (k, n, lo, hi), file=sys.stderr)
            return 1
    if TOPICS[0]["key"] != "g1a_tian":
        print("第一个知识点必须是 g1a_tian", file=sys.stderr)
        return 1
    if not any("静夜思" in t["name"] for t in TOPICS):
        print("必须有一个名称里含「静夜思」的知识点", file=sys.stderr)
        return 1
    keys = [t["key"] for t in TOPICS]
    if len(set(keys)) != len(keys):
        print("知识点 key 重复", file=sys.stderr)
        return 1

    base_topics = [t for t in topics if not is_zh_topic_id(t.get("id"))]
    # 只去掉小学语文发出的边；初中指向小学的边保留。
    base_deps = [e for e in deps if not is_zh_topic_id(e.get("topicId"))]
    base_questions = [q for q in questions if not is_zh_topic_id(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not is_primary_zh_std(it.get("id", ""))]
    if any(is_zh_topic_id(t.get("id")) for t in base_topics):
        print("剥离小学语文知识点失败", file=sys.stderr)
        return 1

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
        tid = "cnc_p%03d" % i
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
        if spec["key"] == "g1a_tian":
            topic["root_reason"] = "一年级语文从识字「天地人」开始。按2024年修订的统编教材，识字排在汉语拼音前面，前面没有更早的小学语文知识点。"
        new_topics.append(topic)
        new_questions.extend(built)

    raw = []
    for i in range(1, len(TOPICS)):
        cur = TOPICS[i]["key"]
        prev = TOPICS[i - 1]["key"]
        if (cur, prev) in hard_pairs:
            continue
        reason = "按统编教材的常见教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
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

    merged_deps, dropped = reduce_chinese(base_deps + new_edges)
    zh_edges = [e for e in merged_deps if is_zh_topic_id(e["topicId"])]
    if any(not str(e["prerequisiteId"]).startswith("cnc_") for e in zh_edges):
        print("语文边连到了其他学科", file=sys.stderr)
        return 1
    if any(is_zh_topic_id(e["topicId"]) for e in base_deps):
        print("剥离后的依赖里仍有小学语文边", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in zh_edges}
    missing = [t["id"] for t in new_topics if t["id"] != "cnc_p001" and t["id"] not in covered]
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

    kept_std = {k: v for k, v in standards.items() if k != "items" and k != "chinese"}
    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + new_items
    has_junior_std = any(str(it.get("id", "")).startswith("ccs-2022:4.") for it in base_items)
    zh_note = (
        "条目是对第一至第三学段学习要求的公开转述，不是逐页核对的原文。"
        "verbatim 为 false。第一至第三学段 page_or_ref 记人教社电子书印刷页7–13，不是教育部 PDF 页码。"
        "编号 ccs-2022 是本图谱编的，不是教育部原编号。一年级按2024年起修订的统编教材编排，二上、三上按2025秋修订目录编排，"
        "二下、三下按2026春修订目录编排，四上按2024修订统编目录逐课覆盖，四下按统编现行目录逐课覆盖，"
        "五上按2026秋统编目录逐课覆盖，五下按统编现行目录逐课覆盖，六上按2026秋统编目录逐课覆盖，"
        "六下按统编现行目录逐课覆盖，没有写入页码。"
        "2026-11-06 抽查册次：人教社张漫漫《统编小学语文教科书一年级上册修订要点》"
        "（https://www.pep.com.cn/bks/xxyw/jzjd/202505/W020250531415592673618.pdf）"
        "只证实一上减课文、识字量改为280、拼音单元增为三个，没有逐课目录；"
        "六年级上册没有打开到人教社或智慧教育平台的2026秋目录。"
    )
    old_zh = standards.get("chinese") or {}
    if has_junior_std:
        zh_note = zh_note.replace("第一至第三学段学习要求", "第一至第四学段学习要求", 1)
        zh_note = zh_note.replace(
            "第一至第三学段 page_or_ref 记人教社电子书印刷页7–13，不是教育部 PDF 页码。",
            "第一至第三学段 page_or_ref 记人教社电子书印刷页7–13，"
            "第四学段记印刷页14–16，都不是教育部 PDF 页码。",
            1,
        )
        extra = old_zh.get("note") or ""
        marker = "第四学段（7–9年级）"
        if marker in extra and marker not in zh_note:
            # 保留初中编译脚本写入的第四学段说明（含 2026-11-06 人教社电子书印刷页）。
            tail = extra[extra.find(marker):]
            zh_note = (zh_note + " " + tail).strip()
        elif marker not in zh_note:
            zh_note += (
                "第四学段（7–9年级）条目是对学段要求的公开转述，不是逐页核对的原文。"
                "印刷页说明由 scripts/zhj_build.py 写入。"
            )
    standards_out["chinese"] = {
        "title": "义务教育语文课程标准（2022年版）",
        "issuer": "中华人民共和国教育部",
        "year": 2022,
        "stage": "第一至第四学段（1–9年级）" if has_junior_std else "第一至第三学段",
        "note": zh_note,
    }
    for k, v in kept_std.items():
        standards_out[k] = v

    math_before = [(t["id"], t["name"]) for t in base_topics if str(t["id"]).startswith("cnm_")]
    en_before = [(t["id"], t["name"]) for t in base_topics if str(t["id"]).startswith("cne_")]
    phy_before = [(t["id"], t["name"]) for t in base_topics if str(t["id"]).startswith("cnp_")]
    junior_before = [(t["id"], t["name"]) for t in base_topics if is_zh_junior_id(t.get("id"))]

    n_hard = sum(1 for e in zh_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in zh_edges if e["strength"] == "soft")
    by_dom = Counter(t["domain"] for t in new_topics)
    print("语文知识点 %d" % len(new_topics))
    for k in ["1上", "1下", "2上", "2下", "3上", "3下", "4上", "4下", "5上", "5下", "6上", "6下"]:
        print("  %s %d" % (k, by_vol[k]))
    for k, v in by_dom.most_common():
        print("  %s %d" % (k, v))
    print("语文边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(zh_edges), dropped, n_hard, n_soft))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))

    # 按原位置替换小学语文，避免重跑把 cnc_p 挪到文件末尾。
    standards_out["items"] = splice_where(
        standards.get("items") or [],
        lambda it: is_primary_zh_std(it.get("id", "")),
        new_items,
    )
    dump("topics.json", splice_where(topics, lambda t: is_zh_topic_id(t.get("id")), new_topics))
    dump("dependencies.json", splice_where(
        deps, lambda e: is_zh_topic_id(e.get("topicId")), zh_edges))
    dump("questions.json", splice_where(
        questions, lambda q: is_zh_topic_id(q.get("topicId")), new_questions))
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    again_topics = [t for t in again_t if not is_zh_topic_id(t.get("id"))]
    again_deps = [e for e in again_d if not is_zh_topic_id(e.get("topicId"))]
    again_qs = [q for q in again_q if not is_zh_topic_id(q.get("topicId"))]
    again_items = [it for it in again_s.get("items", []) if not is_primary_zh_std(it.get("id", ""))]
    if again_topics != base_topics or again_deps != base_deps or again_qs != base_questions or again_items != base_items:
        print("数学、英语、物理或初中语文数据在写回后发生了变化", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cnm_")] != math_before:
        print("数学知识点 id 或名称变了", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cne_")] != en_before:
        print("英语知识点 id 或名称变了", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cnp_")] != phy_before:
        print("物理知识点 id 或名称变了", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if is_zh_junior_id(t.get("id"))] != junior_before:
        print("初中语文知识点 id 或名称变了", file=sys.stderr)
        return 1
    for k, v in kept_std.items():
        if again_s.get(k) != v:
            print("原课标对象 %s 发生了变化" % k, file=sys.stderr)
            return 1
    if again_s.get("chinese", {}).get("title") != "义务教育语文课程标准（2022年版）":
        print("语文课标标题不正确", file=sys.stderr)
        return 1
    print("数学 %d、英语 %d、物理 %d、初中语文 %d 个知识点的 id 与名称未改" % (
        len(math_before), len(en_before), len(phy_before), len(junior_before)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
