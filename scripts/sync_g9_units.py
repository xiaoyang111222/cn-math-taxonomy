#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把九年级英语生成器里已改的单元写回稳定 id。

不调用 enj_build.main，不追加知识点，不改课标、confidence、verbatim，
也不写 questions.json。可重复运行：没有差异时不改文件。

只用 TOPICS 的 key 顺序映射 cne_j001–cne_j245。cne_j246 及以后不在
本轮改写范围内。cne_j249–cne_j251 与 cne_j252–cne_j257 的 chapter 已正确，
本脚本不改它们。

只改生成器 grade 为 9 的点的 name、description、chapter。改挂待核
（unit 90）的点可以同步 grade、semester。不改七年级、八年级点。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

import enj_build  # noqa: E402
from en_lib import TOPICS  # noqa: E402
from enj_build import chapter  # noqa: E402

Q_SHA = "c641379ab95d7a328690e47671a8d34146d29b7ed4671bd7c47f0a700b4aa8dd"

# id -> (key, grade, semester, unit, chapter)
# 与 2026-11-11 官方阅读器改挂表一致。chapter 必须由 chapter() 算出。
U1 = "九年级上册 第1单元 The Changing World"
U3 = "九年级上册 第3单元 Smart Learning"
U4 = "九年级上册 第4单元 Our Memory"
U5 = "九年级上册 第5单元 Power of Ideas"
U7 = "九年级上册 第7单元 Feel the Rhythm"
PEND = "九年级上册 待核"

EXPECTED = {
    "cne_j200": ("vo_change9", 9, "上", 1, U1),
    "cne_j202": ("fu_used", 9, "上", 1, U1),
    "cne_j203": ("rw_used", 9, "上", 1, U1),
    "cne_j187": ("vo_learn", 9, "上", 3, U3),
    "cne_j189": ("fu_learn", 9, "上", 3, U3),
    "cne_j190": ("rw_learn", 9, "上", 3, U3),
    "cne_j192": ("gr_that", 9, "上", 3, U3),
    "cne_j193": ("gr_ifwhether", 9, "上", 3, U3),
    "cne_j197": ("gr_whobj", 9, "上", 4, U4),
    "cne_j205": ("gr_pass", 9, "上", 5, U5),
    "cne_j208": ("vo_invent", 9, "上", 5, U5),
    "cne_j209": ("gr_passpast", 9, "上", 5, U5),
    "cne_j210": ("fu_invent", 9, "上", 5, U5),
    "cne_j211": ("rw_invent", 9, "上", 5, U5),
    "cne_j220": ("vo_music", 9, "上", 7, U7),
    "cne_j221": ("gr_attr", 9, "上", 7, U7),
    "cne_j222": ("fu_music", 9, "上", 7, U7),
    "cne_j223": ("rw_music", 9, "上", 7, U7),
    "cne_j201": ("gr_used", 9, "上", 90, PEND),
    "cne_j188": ("gr_by", 9, "上", 90, PEND),
    "cne_j196": ("vo_polite", 9, "上", 90, PEND),
    "cne_j198": ("fu_polite", 9, "上", 90, PEND),
    "cne_j199": ("rw_polite", 9, "上", 90, PEND),
    "cne_j204": ("vo_material", 9, "上", 90, PEND),
    "cne_j206": ("fu_made", 9, "上", 90, PEND),
    "cne_j207": ("rw_made", 9, "上", 90, PEND),
    "cne_j191": ("vo_fest", 9, "上", 90, PEND),
    "cne_j194": ("fu_fest", 9, "上", 90, PEND),
    "cne_j195": ("rw_fest", 9, "上", 90, PEND),
    "cne_j212": ("vo_teen", 9, "上", 90, PEND),
    "cne_j213": ("gr_allow", 9, "上", 90, PEND),
    "cne_j214": ("fu_allow", 9, "上", 90, PEND),
    "cne_j215": ("rw_allow", 9, "上", 90, PEND),
    "cne_j216": ("vo_owner", 9, "上", 90, PEND),
    "cne_j217": ("gr_mustbe", 9, "上", 90, PEND),
    "cne_j218": ("fu_guess", 9, "上", 90, PEND),
    "cne_j219": ("rw_guess", 9, "上", 90, PEND),
    "cne_j228": ("vo_emotion", 9, "上", 90, PEND),
    "cne_j229": ("gr_make", 9, "上", 90, PEND),
    "cne_j230": ("fu_feel9", 9, "上", 90, PEND),
    "cne_j231": ("rw_movie", 9, "上", 90, PEND),
    "cne_j232": ("vo_unexp", 9, "上", 90, PEND),
    "cne_j233": ("gr_ppast", 9, "上", 90, PEND),
    "cne_j234": ("fu_unexp", 9, "上", 90, PEND),
    "cne_j235": ("rw_unexp", 9, "上", 90, PEND),
    "cne_j236": ("vo_earth", 9, "上", 90, PEND),
    "cne_j237": ("gr_review", 9, "上", 90, PEND),
    "cne_j238": ("fu_earth", 9, "上", 90, PEND),
    "cne_j239": ("rw_earth", 9, "上", 90, PEND),
    "cne_j240": ("rw_cloze9", 9, "上", 90, PEND),
    "cne_j241": ("vo_memory", 9, "上", 90, PEND),
    "cne_j242": ("gr_ger", 9, "上", 90, PEND),
    "cne_j243": ("gr_tag", 9, "上", 90, PEND),
    "cne_j244": ("fu_memory", 9, "上", 90, PEND),
    "cne_j245": ("rw_write", 9, "上", 90, PEND),
}

# 本轮仍留在七、八年级的点，以及已正确挂着、不改的点。误改必须失败退出。
FROZEN = {
    "cne_j010": (7, "下", "七年级下册 第1单元 Animal Friends"),
    "cne_j053": (7, "上", "七年级上册 待核"),
    "cne_j054": (7, "上", "七年级上册 待核"),
    "cne_j055": (7, "上", "七年级上册 待核"),
    "cne_j056": (7, "上", "七年级上册 待核"),
    "cne_j093": (7, "下", "七年级下册 第7单元 A Day to Remember"),
    "cne_j096": (7, "下", "七年级下册 第7单元 A Day to Remember"),
    "cne_j097": (7, "下", "七年级下册 待核"),
    "cne_j113": (8, "上", "八年级上册 待核"),
    "cne_j115": (8, "上", "八年级上册 待核"),
    "cne_j116": (8, "上", "八年级上册 待核"),
    "cne_j133": (8, "上", "八年级上册 待核"),
    "cne_j134": (8, "上", "八年级上册 待核"),
    "cne_j135": (8, "上", "八年级上册 待核"),
    "cne_j136": (8, "上", "八年级上册 待核"),
    "cne_j138": (8, "上", "八年级上册 待核"),
    "cne_j141": (8, "上", "八年级上册 待核"),
    "cne_j117": (8, "上", "八年级上册 待核"),
    "cne_j119": (8, "上", "八年级上册 待核"),
    "cne_j120": (8, "上", "八年级上册 待核"),
    "cne_j156": (8, "下", "八年级下册 待核"),
    "cne_j157": (8, "下", "八年级下册 待核"),
    "cne_j172": (8, "下", "八年级下册 待核"),
    "cne_j225": (8, "下", "八年级下册 待核"),
    "cne_j178": (8, "下", "八年级下册 待核"),
    "cne_j180": (8, "下", "八年级下册 待核"),
    "cne_j181": (8, "下", "八年级下册 待核"),
    "cne_j182": (8, "下", "八年级下册 待核"),
    "cne_j183": (8, "下", "八年级下册 待核"),
    "cne_j185": (8, "下", "八年级下册 待核"),
    "cne_j186": (8, "下", "八年级下册 待核"),
    "cne_j224": (8, "下", "八年级下册 第6单元 Crossing Cultures"),
    "cne_j226": (8, "下", "八年级下册 第6单元 Crossing Cultures"),
    "cne_j227": (8, "下", "八年级下册 第6单元 Crossing Cultures"),
    "cne_j249": (8, "上", "八年级上册 第1单元 Happy Holiday"),
    "cne_j250": (8, "上", "八年级上册 第3单元 Same or Different?"),
    "cne_j251": (8, "下", "八年级下册 第2单元 Stay Healthy"),
    "cne_j252": (9, "上", "九年级上册 第1单元 The Changing World"),
    "cne_j253": (9, "上", "九年级上册 第2单元 Inspiring People"),
    "cne_j254": (9, "上", "九年级上册 第6单元 Beyond Earth"),
    "cne_j255": (9, "上", "九年级上册 第6单元 Beyond Earth"),
    "cne_j256": (9, "上", "九年级上册 第8单元 More than a Game"),
    "cne_j257": (9, "上", "九年级上册 第8单元 More than a Game"),
}

# 已从 UNITS 删掉的旧版九年级课名。理由若还写这些，并且边碰到本轮改挂点，就停止。
OLD_UNIT_TITLES = (
    "How can we become good learners",
    "I think that mooncakes are delicious",
    "Could you please tell me where the restrooms are",
    "I used to be afraid of the dark",
    "What are the shirts made of",
    "When was it invented",
    "Teenagers should be allowed to choose their own clothes",
    "It must belong to Carla",
    "I like music that I can dance to",
    "You're supposed to shake hands",
    "Sad movies make me cry",
    "Life is full of the unexpected",
    "We're trying to save the earth",
    "I remember meeting all of you in Grade 7",
)


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        digest.update(f.read())
    return digest.hexdigest()


def nontarget_hash(topics, questions, deps, allowed, pending_ids):
    rows = []
    for t in topics:
        if t["id"] in allowed:
            skip = {"name", "description", "chapter"}
            if t["id"] in pending_ids:
                skip |= {"grade", "semester"}
            rows.append(("t", t["id"], {k: t[k] for k in t if k not in skip}))
        else:
            rows.append(("t", t["id"], t))
    rows.append(("q", None, questions))
    rows.append(("d", None, deps))
    return sha(canon(rows))


def main():
    if len(TOPICS) != 245 or TOPICS[0]["key"] != "ph_stress":
        print("初中英语主干不是 245 条", file=sys.stderr)
        return 1

    q_path = os.path.join(ROOT, "data", "questions.json")
    if file_sha(q_path) != Q_SHA:
        print("questions.json 哈希与本轮基线不一致", file=sys.stderr)
        return 1

    topics = load("topics.json")
    questions = load("questions.json")
    deps = load("dependencies.json")
    by_id = {t["id"]: t for t in topics}
    q_bytes_before = open(q_path, "rb").read()
    standards_before = {
        t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True)
        for t in topics
    }

    specs_by_id = {}
    for i, spec in enumerate(TOPICS, start=1):
        specs_by_id["cne_j%03d" % i] = spec

    grade9 = {tid for tid, spec in specs_by_id.items() if spec["grade"] == 9}
    if grade9 != set(EXPECTED):
        extra = sorted(grade9 - set(EXPECTED))
        missing = sorted(set(EXPECTED) - grade9)
        print("九年级生成器集合与改挂表不一致 多 %s 缺 %s" % (
            " ".join(extra), " ".join(missing)), file=sys.stderr)
        return 1

    pending_ids = set()
    for tid, (key, grade, sem, unit, ch) in EXPECTED.items():
        spec = specs_by_id[tid]
        if (spec["key"], spec["grade"], spec["semester"], spec["unit"]) != (key, grade, sem, unit):
            print("%s 生成器是 %s %s%s U%s，表是 %s %s%s U%s" % (
                tid, spec["key"], spec["grade"], spec["semester"], spec["unit"],
                key, grade, sem, unit), file=sys.stderr)
            return 1
        got = chapter(spec["grade"], spec["semester"], spec["unit"])
        if got != ch:
            print("%s chapter() 是 %s，表是 %s" % (tid, got, ch), file=sys.stderr)
            return 1
        if unit == 90:
            pending_ids.add(tid)
        if tid in FROZEN:
            print("改挂表碰到了应冻结的 %s" % tid, file=sys.stderr)
            return 1

    for tid, (grade, sem, ch) in FROZEN.items():
        topic = by_id.get(tid)
        if topic is None:
            print("缺少冻结点 %s" % tid, file=sys.stderr)
            return 1
        if (topic.get("grade"), topic.get("semester"), topic.get("chapter")) != (grade, sem, ch):
            print("冻结点已被改动 %s %s%s %s" % (
                tid, topic.get("grade"), topic.get("semester"), topic.get("chapter")), file=sys.stderr)
            return 1
        if topic.get("subject") != "english":
            print("%s 不是英语" % tid, file=sys.stderr)
            return 1

    # 保留点的册次必须已经与生成器一致。待核点才允许改 grade、semester。
    for tid, (key, grade, sem, unit, ch) in EXPECTED.items():
        if unit == 90:
            continue
        topic = by_id.get(tid)
        if topic is None:
            print("缺少 %s" % tid, file=sys.stderr)
            return 1
        if topic.get("grade") != grade or topic.get("semester") != sem:
            print("保留点 %s 数据册次是 %s%s，生成器是 %s%s" % (
                tid, topic.get("grade"), topic.get("semester"), grade, sem), file=sys.stderr)
            return 1

    touched = set()
    for tid, (key, grade, sem, unit, ch) in EXPECTED.items():
        topic = by_id[tid]
        if (topic.get("chapter") != ch or topic.get("grade") != grade
                or topic.get("semester") != sem):
            touched.add(tid)

    for e in deps:
        if e["topicId"] not in touched and e["prerequisiteId"] not in touched:
            continue
        if not any(title in e["reason"] for title in OLD_UNIT_TITLES):
            continue
        if e["strength"] == "hard":
            print("硬边理由仍写旧版课名，本脚本不改 %s←%s" % (
                e["topicId"], e["prerequisiteId"]), file=sys.stderr)
            return 1
        print("软边理由仍写旧版课名 %s←%s：%s" % (
            e["topicId"], e["prerequisiteId"], e["reason"]), file=sys.stderr)
        return 1

    before_hash = nontarget_hash(topics, questions, deps, set(EXPECTED), pending_ids)

    changed_topics = []
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_j%03d" % i
        if tid not in EXPECTED:
            continue
        topic = by_id.get(tid)
        if topic is None:
            print("缺少 %s" % tid, file=sys.stderr)
            return 1
        if topic.get("subject") != "english":
            print("%s 不是英语" % tid, file=sys.stderr)
            return 1
        ch = chapter(spec["grade"], spec["semester"], spec["unit"])
        grade_differ = False
        if spec["unit"] == 90 and (
            topic.get("grade") != spec["grade"] or topic.get("semester") != spec["semester"]
        ):
            grade_differ = True
        meta_differ = (
            topic["name"] != spec["name"]
            or topic["description"] != spec["description"]
            or topic["chapter"] != ch
            or grade_differ
        )
        if not meta_differ:
            continue
        topic["name"] = spec["name"]
        topic["description"] = spec["description"]
        topic["chapter"] = ch
        if spec["unit"] == 90:
            topic["grade"] = spec["grade"]
            topic["semester"] = spec["semester"]
        changed_topics.append(tid)

    standards_after = {
        t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True)
        for t in topics
    }
    if standards_before != standards_after:
        print("standards 被改动", file=sys.stderr)
        return 1
    if open(q_path, "rb").read() != q_bytes_before or file_sha(q_path) != Q_SHA:
        print("questions.json 被改动", file=sys.stderr)
        return 1
    after_hash = nontarget_hash(topics, questions, deps, set(EXPECTED), pending_ids)
    if after_hash != before_hash:
        print("非目标对象被改动", file=sys.stderr)
        return 1
    for tid, (grade, sem, ch) in FROZEN.items():
        topic = by_id[tid]
        if (topic.get("grade"), topic.get("semester"), topic.get("chapter")) != (grade, sem, ch):
            print("误改冻结点 %s" % tid, file=sys.stderr)
            return 1
    for tid in changed_topics:
        if not tid.startswith("cne_j") or tid >= "cne_j246":
            print("误改 %s" % tid, file=sys.stderr)
            return 1

    if not changed_topics:
        print("没有差异")
        return 0
    dump("topics.json", topics)
    print("topics %d questions 0 reasons 0 dropped 0" % len(changed_topics))
    print(" ".join(changed_topics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
