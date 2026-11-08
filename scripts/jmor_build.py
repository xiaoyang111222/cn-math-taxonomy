#!/usr/bin/env python3
"""把初中道德与法治（七上至八下）编译进 data/。

可以重复运行。只替换 cnd_j 知识点和 cds-2022:4 课标条目。
保留小学 cnd_p、其他学科、以及第一至第三学段道法课标。
不建九上、九下。不把第三方目录标成已核实。

用法：python3 scripts/jmor_build.py
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jmor_lib as L  # noqa: E402

for _mod in ("jmor_g7a", "jmor_g7b", "jmor_g8a", "jmor_g8b"):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _mod + ".py")
    if os.path.isfile(path):
        importlib.import_module(_mod)

from jmor_lib import (  # noqa: E402
    CATALOG_STATUS, CODE_OF, EDGES, NOTICE_URL, PDF_URL, STANDARD_ROWS, TOPICS,
    check_question, materialise_questions,
)
from verify_questions import verify_all  # noqa: E402

KEEP_PREFIXES = ("cnd_p", "cnm_", "cne_", "cnp_", "cnc_", "cns_", "cnh_", "cng_", "cnb_", "cnk_")


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    """与 HEAD 的 data/questions.json 相同：indent=2，文件以换行结束。"""
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_junior(tid):
    return str(tid).startswith("cnd_j")


def is_junior_std(sid):
    return str(sid).startswith("cds-2022:4.")


def rank_of(spec):
    return spec["grade"] * 2 + (1 if spec["semester"] == "下" else 0)


def id_num(spec):
    """cnd_jNNN 的数字部分。不改写 id 本身。"""
    tail = str(spec["id"])[6:]
    if not tail.isdigit():
        raise SystemExit("无法按原 id 排序：%s" % spec["id"])
    return int(tail)


def sort_topics(rows):
    rows.sort(key=lambda t: (rank_of(t), t["unit"], id_num(t)))
    return rows


def stored_junior_ids(topics, deps, questions):
    ids = {t["id"] for t in topics if is_junior(t.get("id"))}
    for edge in deps:
        for key in ("topicId", "prerequisiteId"):
            if is_junior(edge.get(key)):
                ids.add(edge[key])
    for q in questions:
        if is_junior(q.get("topicId")):
            ids.add(q["topicId"])
    return ids


def lost_junior_ids(old_ids, new_ids):
    """旧 cnd_j 必须是本次将写入 id 的子集，否则拒绝，避免缺模块时删点。"""
    return sorted(set(old_ids) - set(new_ids))


VOL_CN = {7: "七", 8: "八", 9: "九"}


def volume_labels(rows):
    labels = []
    seen = set()
    for spec in sorted(rows, key=lambda t: (t["grade"], 0 if t["semester"] == "上" else 1)):
        label = "%s%s" % (VOL_CN.get(spec["grade"], spec["grade"]), spec["semester"])
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def coverage_text(rows):
    labels = volume_labels(rows)
    listed = "、".join(labels) if labels else "无"
    return (
        "本批已入库 %d 个知识点，册次只有 %s。"
        "未出现的册次没有建点。这不是四册全覆盖，九上、九下也未建点。"
        "课级目录仍待官方逐课核实。"
    ) % (len(rows), listed)


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
    }


def sig(rows, prefix):
    return [(r.get("id"), r.get("name")) for r in rows if str(r.get("id", "")).startswith(prefix)]


def main():
    if not TOPICS:
        print("没有初中道法知识点可写", file=sys.stderr)
        return 1
    if any(t["grade"] == 9 for t in TOPICS):
        print("九上九下不允许出现在本批", file=sys.stderr)
        return 1
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    before = {p: sig(topics, p) for p in KEEP_PREFIXES}
    q_before = Counter(next((p for p in KEEP_PREFIXES if str(q.get("topicId", "")).startswith(p)), "other") for q in questions)

    new_ids = [t["id"] for t in TOPICS]
    lost = lost_junior_ids(stored_junior_ids(topics, deps, questions), new_ids)
    if lost:
        print("拒绝写入：本次生成的 cnd_j 盖不住已入库 id（缺册模块会删点）：%s" % "、".join(lost), file=sys.stderr)
        return 1

    order = {t["id"]: i for i, t in enumerate(TOPICS)}
    sort_topics(TOPICS)
    keys = [t["key"] for t in TOPICS]
    ids = [t["id"] for t in TOPICS]
    if len(set(keys)) != len(keys) or len(set(ids)) != len(ids):
        print("key 或 id 重复", file=sys.stderr)
        return 1
    # 稳定编号：已入库的 cnd_j 若还在本批，名称不得被换成另一个 key 的旧 id。
    old_by_id = {t["id"]: t for t in topics if is_junior(t.get("id"))}
    for spec in TOPICS:
        old = old_by_id.get(spec["id"])
        if old and old.get("name") != spec["name"]:
            print("拒绝改旧 id 的名称：%s 原「%s」新「%s」" % (spec["id"], old.get("name"), spec["name"]), file=sys.stderr)
            return 1

    by_key = {t["key"]: t for t in TOPICS}
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    id_of = {t["key"]: t["id"] for t in TOPICS}

    for src, dst, strength, reason in EDGES:
        if src not in by_key or dst not in by_key:
            print("先修指向未登记知识点：%s → %s" % (src, dst), file=sys.stderr)
            return 1
        if index[dst] >= index[src]:
            print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        if rank_of(by_key[dst]) > rank_of(by_key[src]):
            print("先修册次更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
            return 1
        if strength not in ("hard", "soft"):
            print("非法强度 %s" % strength, file=sys.stderr)
            return 1
        if strength == "hard" and "概念上必须先掌握" not in reason and "不掌握则后续概念不能独立成立" not in reason:
            print("硬边理由必须说明概念必要：%s → %s" % (src, dst), file=sys.stderr)
            return 1

    # 不建全书一条链，也不为消除孤立去造边。
    # 没有先修时必须有 root_reason。validate 允许这种独立根。
    incoming = defaultdict(list)
    for src, dst, strength, reason in EDGES:
        incoming[src].append(dst)
    for spec in TOPICS:
        if not incoming[spec["key"]] and not spec.get("root_reason"):
            print("%s 没有先修，也没有 root_reason" % spec["id"], file=sys.stderr)
            return 1

    id_of_std = {}
    new_items = []
    counters = {}
    for symbol, level, code, section, text in STANDARD_ROWS:
        key = (level, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "cds-2022:%s.%s.%02d" % (level, code, counters[key])
        id_of_std[symbol] = sid
        new_items.append({
            "id": sid,
            "domain": CODE_OF[code],
            "section": section,
            "clause": "(%d)" % counters[key],
            "text": text,
            "page_or_ref": "待核",
            "verbatim": False,
            "text_status": "inferred。公开解读归纳的第四学段主题名称，不是课标原文。教育部通知 PDF 为扫描件，本次未逐页核对。",
            "notice_url": NOTICE_URL,
            "pdf_url": PDF_URL,
        })
    used = {t["std"] for t in TOPICS}
    missing = [row[0] for row in STANDARD_ROWS if row[0] not in used]
    # 第四学段五个主题不限于当前册。七、八年级未引用时只警告，不拒绝生成，也不为消警告去映射。
    if missing:
        print("警告：第四学段五主题不限于当前册，未强行映射。尚未引用：%s" % "、".join(missing))

    new_topics = []
    new_questions = []
    for i, spec in enumerate(TOPICS):
        if spec["catalog_status"] != CATALOG_STATUS:
            print("%s 目录状态不是待核" % spec["id"], file=sys.stderr)
            return 1
        made = materialise_questions(spec)
        for q in made:
            check_question(spec["key"], q)
        built = []
        for n, item in enumerate(made, start=1):
            built.append(build_question(spec["id"], n, item, slot=i + n))
        ref = {
            "id": id_of_std[spec["std"]],
            "confidence": "inferred",
            "note": spec["note"],
        }
        topic = {
            "id": spec["id"],
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": spec["grade"],
            "semester": spec["semester"],
            "chapter": L.chapter(spec["grade"], spec["semester"], spec["unit"]),
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": made[0]["a"]},
            "external": False,
            "subject": "morality",
            "standards": [ref],
            "catalog_status": CATALOG_STATUS,
            "lesson": spec["lesson"],
            "frames": spec["frames"],
        }
        if spec.get("root_reason"):
            topic["root_reason"] = spec["root_reason"]
        new_topics.append(topic)
        new_questions.extend(built)

    seen = set()
    new_edges = []
    for src, dst, strength, reason in EDGES:
        pair = (id_of[src], id_of[dst])
        if pair in seen:
            print("重复边 %s → %s" % pair, file=sys.stderr)
            return 1
        seen.add(pair)
        new_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": id_of[dst],
            "strength": strength,
            "reason": reason,
        })

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:20]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("mismatch %d unverifiable %d" % (len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    base_topics = [t for t in topics if not is_junior(t.get("id"))]
    base_deps = [e for e in deps if not is_junior(e.get("topicId")) and not is_junior(e.get("prerequisiteId"))]
    base_questions = [q for q in questions if not is_junior(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not is_junior_std(it.get("id"))]

    # 小学 id 必须仍在剥离结果里，证明没有误伤 cnd_p。
    if any(is_junior(t.get("id")) for t in base_topics):
        print("剥离初中知识点失败", file=sys.stderr)
        return 1
    if sig(base_topics, "cnd_p") != before["cnd_p"]:
        print("小学道法知识点被改动", file=sys.stderr)
        return 1

    mo = dict(standards.get("morality") or {})
    mo["title"] = "义务教育道德与法治课程标准（2022年版）"
    mo["issuer"] = "中华人民共和国教育部"
    mo["year"] = 2022
    mo["notice_url"] = NOTICE_URL
    mo["pdf_url"] = PDF_URL
    mo["pdf_status"] = "官方通知所附 PDF 为扫描件，未逐页核对，页码待核，verbatim 均为 false"
    mo["junior_stage"] = "第四学段五主题为公开解读的推断，不是课标原文"
    labels = volume_labels(new_topics)
    mo["coverage"] = coverage_text(new_topics)
    mo["junior_note"] = (
        "cds-2022:4.* 只标第四学段五个学习主题的名称，confidence 为 inferred，verbatim 为 false，page_or_ref 为「待核」。"
        "通知页 %s ，PDF %s 。教材目录字段 catalog_status=pending_official_lesson_list。"
        "已入库 %d 个知识点（%s）。不把未入库册次写成已经完整覆盖。"
    ) % (NOTICE_URL, PDF_URL, len(new_topics), "、".join(labels))
    primary_stage = "第一至第三学段（1–6年级）"
    mo["stage"] = primary_stage + "；第四学段（7–9年级）仅主题推断。已入库册次：%s（%d 个知识点）" % (
        "、".join(labels), len(new_topics))
    sentence = "初中道法由 scripts/jmor_build.py 写入：已入库%d个知识点（%s），目录待官方逐课核实，未出现的册次未建点。" % (
        len(new_topics), "、".join(labels))
    note = mo.get("note") or ""
    note = re.sub(r"初中道法由 scripts/jmor_build.py 写入：[^。]*。", "", note)
    note = re.sub(r"初中七上至八下由 scripts/jmor_build.py 写入，目录待官方逐课核实，九上九下未建点。", "", note)
    mo["note"] = (note.strip() + " " + sentence).strip()
    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + new_items
    standards_out["morality"] = mo

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", base_deps + new_edges)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_q = load("questions.json")
    for p in KEEP_PREFIXES:
        if sig(again_t, p) != before[p]:
            print("写回后 %s 知识点变化" % p, file=sys.stderr)
            return 1
    q_after = Counter(next((p for p in KEEP_PREFIXES if str(q.get("topicId", "")).startswith(p)), "other") for q in again_q)
    for p in KEEP_PREFIXES:
        if q_before[p] != q_after[p]:
            print("写回后 %s 题目数量变化 %s → %s" % (p, q_before[p], q_after[p]), file=sys.stderr)
            return 1
    junior = [t for t in again_t if is_junior(t.get("id"))]
    if [t["id"] for t in junior] != [t["id"] for t in new_topics]:
        print("初中 id 顺序写回不一致", file=sys.stderr)
        return 1
    if any(t.get("catalog_status") != CATALOG_STATUS for t in junior):
        print("存在未标待核的初中点", file=sys.stderr)
        return 1
    if any(t.get("standards", [{}])[0].get("confidence") != "inferred" for t in junior):
        print("存在非 inferred 的初中对齐", file=sys.stderr)
        return 1

    by_vol = Counter("%s%s" % (VOL_CN.get(t["grade"], t["grade"]), t["semester"]) for t in new_topics)
    n_hard = sum(1 for e in new_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in new_edges if e["strength"] == "soft")
    print("初中道法知识点 %d 题 %d 边 %d（hard %d soft %d）" % (
        len(new_topics), len(new_questions), len(new_edges), n_hard, n_soft))
    for k in volume_labels(new_topics):
        print("  %s %d" % (k, by_vol[k]))
    print("课标第四学段 %d 条，全部 verbatim false" % len(new_items))
    print("小学 cnd_p %d 未改" % len(before["cnd_p"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
