#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把八年级英语生成器里已改的单元写回稳定 id。

不调用 enj_build.main，不追加知识点，不改课标、confidence、verbatim，
也不写 questions.json。可重复运行：没有差异时不改文件。

只用 TOPICS 的 key 顺序映射 cne_j001–cne_j245。cne_j246 及以后不在
本轮范围内，其中 cne_j249、cne_j250、cne_j251 的 chapter 已正确，本脚本不改它们。

只改生成器 grade 为 8 的点的 name、description、chapter。改挂待核
（unit 90）的点可以同步 grade、semester。不改七年级点，也不改九年级其余点。
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
EXPECTED = {
    "cne_j099": ("vo_vac", 8, "上", 1, "八年级上册 第1单元 Happy Holiday"),
    "cne_j100": ("gr_past8", 8, "上", 1, "八年级上册 第1单元 Happy Holiday"),
    "cne_j101": ("fu_vac", 8, "上", 1, "八年级上册 第1单元 Happy Holiday"),
    "cne_j102": ("rw_vac", 8, "上", 1, "八年级上册 第1单元 Happy Holiday"),
    "cne_j137": ("ph_pause", 8, "上", 2, "八年级上册 第2单元 Home Sweet Home"),
    "cne_j150": ("vo_chore", 8, "上", 2, "八年级上册 第2单元 Home Sweet Home"),
    "cne_j151": ("gr_could", 8, "上", 2, "八年级上册 第2单元 Home Sweet Home"),
    "cne_j152": ("fu_chore", 8, "上", 2, "八年级上册 第2单元 Home Sweet Home"),
    "cne_j153": ("rw_chore", 8, "上", 2, "八年级上册 第2单元 Home Sweet Home"),
    "cne_j108": ("vo_person", 8, "上", 3, "八年级上册 第3单元 Same or Different?"),
    "cne_j109": ("gr_comp8", 8, "上", 3, "八年级上册 第3单元 Same or Different?"),
    "cne_j110": ("gr_than8", 8, "上", 3, "八年级上册 第3单元 Same or Different?"),
    "cne_j111": ("fu_cmp", 8, "上", 3, "八年级上册 第3单元 Same or Different?"),
    "cne_j112": ("rw_cmp", 8, "上", 3, "八年级上册 第3单元 Same or Different?"),
    "cne_j114": ("gr_super", 8, "上", 4, "八年级上册 第4单元 Amazing Plants and Animals"),
    "cne_j072": ("gr_excl", 8, "上", 5, "八年级上册 第5单元 What a Delicious Meal!"),
    "cne_j129": ("vo_cook", 8, "上", 5, "八年级上册 第5单元 What a Delicious Meal!"),
    "cne_j130": ("gr_seq", 8, "上", 5, "八年级上册 第5单元 What a Delicious Meal!"),
    "cne_j131": ("fu_recipe", 8, "上", 5, "八年级上册 第5单元 What a Delicious Meal!"),
    "cne_j132": ("rw_recipe", 8, "上", 5, "八年级上册 第5单元 What a Delicious Meal!"),
    "cne_j118": ("gr_to", 8, "上", 6, "八年级上册 第6单元 Plan for Yourself"),
    "cne_j121": ("vo_job8", 8, "上", 6, "八年级上册 第6单元 Plan for Yourself"),
    "cne_j122": ("gr_going8", 8, "上", 6, "八年级上册 第6单元 Plan for Yourself"),
    "cne_j123": ("fu_dream", 8, "上", 6, "八年级上册 第6单元 Plan for Yourself"),
    "cne_j124": ("rw_dream", 8, "上", 6, "八年级上册 第6单元 Plan for Yourself"),
    "cne_j125": ("vo_future", 8, "上", 7, "八年级上册 第7单元 When Tomorrow Comes"),
    "cne_j126": ("gr_will", 8, "上", 7, "八年级上册 第7单元 When Tomorrow Comes"),
    "cne_j127": ("fu_predict", 8, "上", 7, "八年级上册 第7单元 When Tomorrow Comes"),
    "cne_j128": ("rw_future", 8, "上", 7, "八年级上册 第7单元 When Tomorrow Comes"),
    "cne_j139": ("gr_if", 8, "上", 8, "八年级上册 第8单元 Let's Communicate!"),
    "cne_j140": ("fu_if", 8, "上", 8, "八年级上册 第8单元 Let's Communicate!"),
    "cne_j113": ("vo_town", 8, "上", 90, "八年级上册 待核"),
    "cne_j115": ("fu_best", 8, "上", 90, "八年级上册 待核"),
    "cne_j116": ("rw_best", 8, "上", 90, "八年级上册 待核"),
    "cne_j133": ("vo_party", 8, "上", 90, "八年级上册 待核"),
    "cne_j134": ("gr_invite", 8, "上", 90, "八年级上册 待核"),
    "cne_j135": ("fu_invite", 8, "上", 90, "八年级上册 待核"),
    "cne_j136": ("rw_invite", 8, "上", 90, "八年级上册 待核"),
    "cne_j138": ("vo_advice", 8, "上", 90, "八年级上册 待核"),
    "cne_j141": ("rw_if", 8, "上", 90, "八年级上册 待核"),
    "cne_j117": ("vo_show", 8, "上", 90, "八年级上册 待核"),
    "cne_j119": ("fu_show", 8, "上", 90, "八年级上册 待核"),
    "cne_j120": ("rw_show", 8, "上", 90, "八年级上册 待核"),
    "cne_j147": ("gr_purpose", 8, "下", 1, "八年级下册 第1单元 Time to Relax"),
    "cne_j142": ("vo_health", 8, "下", 2, "八年级下册 第2单元 Stay Healthy"),
    "cne_j143": ("gr_should8", 8, "下", 2, "八年级下册 第2单元 Stay Healthy"),
    "cne_j144": ("fu_health", 8, "下", 2, "八年级下册 第2单元 Stay Healthy"),
    "cne_j145": ("rw_health", 8, "下", 2, "八年级下册 第2单元 Stay Healthy"),
    "cne_j154": ("vo_mood", 8, "下", 3, "八年级下册 第3单元 Growing Up"),
    "cne_j155": ("gr_although", 8, "下", 3, "八年级下册 第3单元 Growing Up"),
    "cne_j165": ("gr_sothat", 8, "下", 3, "八年级下册 第3单元 Growing Up"),
    "cne_j168": ("vo_geo", 8, "下", 4, "八年级下册 第4单元 The Wonders of Nature"),
    "cne_j169": ("gr_high", 8, "下", 4, "八年级下册 第4单元 The Wonders of Nature"),
    "cne_j170": ("fu_fact", 8, "下", 4, "八年级下册 第4单元 The Wonders of Nature"),
    "cne_j171": ("rw_fact", 8, "下", 4, "八年级下册 第4单元 The Wonders of Nature"),
    "cne_j158": ("vo_storm", 8, "下", 5, "八年级下册 第5单元 Nature's Temper"),
    "cne_j159": ("gr_pasting", 8, "下", 5, "八年级下册 第5单元 Nature's Temper"),
    "cne_j160": ("gr_whenwhile", 8, "下", 5, "八年级下册 第5单元 Nature's Temper"),
    "cne_j161": ("fu_storm", 8, "下", 5, "八年级下册 第5单元 Nature's Temper"),
    "cne_j162": ("rw_storm", 8, "下", 5, "八年级下册 第5单元 Nature's Temper"),
    "cne_j224": ("vo_custom", 8, "下", 6, "八年级下册 第6单元 Crossing Cultures"),
    "cne_j164": ("gr_unless", 8, "下", 6, "八年级下册 第6单元 Crossing Cultures"),
    "cne_j226": ("fu_custom", 8, "下", 6, "八年级下册 第6单元 Crossing Cultures"),
    "cne_j227": ("rw_custom", 8, "下", 6, "八年级下册 第6单元 Crossing Cultures"),
    "cne_j173": ("vo_book", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j174": ("gr_pp", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j175": ("gr_yet", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j176": ("fu_book", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j177": ("rw_book", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j179": ("gr_ever", 8, "下", 7, "八年级下册 第7单元 A Good Read"),
    "cne_j146": ("vo_vol", 8, "下", 8, "八年级下册 第8单元 Making a Difference"),
    "cne_j148": ("fu_help", 8, "下", 8, "八年级下册 第8单元 Making a Difference"),
    "cne_j149": ("rw_help", 8, "下", 8, "八年级下册 第8单元 Making a Difference"),
    "cne_j184": ("gr_since", 8, "下", 8, "八年级下册 第8单元 Making a Difference"),
    "cne_j156": ("fu_advice8", 8, "下", 90, "八年级下册 待核"),
    "cne_j157": ("rw_letter8", 8, "下", 90, "八年级下册 待核"),
    "cne_j172": ("rw_cloze8", 8, "下", 90, "八年级下册 待核"),
    "cne_j225": ("gr_supposed", 8, "下", 90, "八年级下册 待核"),
    "cne_j178": ("vo_museum", 8, "下", 90, "八年级下册 待核"),
    "cne_j180": ("gr_been", 8, "下", 90, "八年级下册 待核"),
    "cne_j181": ("fu_ever", 8, "下", 90, "八年级下册 待核"),
    "cne_j182": ("rw_museum", 8, "下", 90, "八年级下册 待核"),
    "cne_j183": ("vo_own", 8, "下", 90, "八年级下册 待核"),
    "cne_j185": ("fu_since", 8, "下", 90, "八年级下册 待核"),
    "cne_j186": ("rw_since", 8, "下", 90, "八年级下册 待核"),
}

# 七年级冻结项：词尾 s、周末活动/谈论上周末已按正文改挂；交通四点与读周末日记仍待核；以及已正确挂着、不在 TOPICS 里的三点。
FROZEN = {
    "cne_j010": (7, "下", "七年级下册 第1单元 Animal Friends"),
    "cne_j053": (7, "上", "七年级上册 待核"),
    "cne_j054": (7, "上", "七年级上册 待核"),
    "cne_j055": (7, "上", "七年级上册 待核"),
    "cne_j056": (7, "上", "七年级上册 待核"),
    "cne_j093": (7, "下", "七年级下册 第7单元 A Day to Remember"),
    "cne_j096": (7, "下", "七年级下册 第7单元 A Day to Remember"),
    "cne_j097": (7, "下", "七年级下册 待核"),
    "cne_j249": (8, "上", "八年级上册 第1单元 Happy Holiday"),
    "cne_j250": (8, "上", "八年级上册 第3单元 Same or Different?"),
    "cne_j251": (8, "下", "八年级下册 第2单元 Stay Healthy"),
}

# 已从 UNITS 删掉的旧版课名。软边理由若还写这些，并且边碰到本轮改挂点，就要改理由。
OLD_UNIT_TITLES = (
    "Where did you go on vacation",
    "How often do you exercise",
    "I'm more outgoing than my sister",
    "What's the best movie theater",
    "Do you want to watch a game show",
    "I'm going to study computer science",
    "Will people have robots",
    "How do you make a banana milk shake",
    "Can you come to my party",
    "If you go to the party, you'll have a great time",
    "What's the matter",
    "I'll help to clean up the city parks",
    "Could you please clean your room",
    "Why don't you talk to your parents",
    "What were you doing when the rainstorm came",
    "An old man tried to move the mountains",
    "What's the highest mountain in the world",
    "Have you read Treasure Island yet",
    "Have you ever been to a museum",
    "I've had this bike for three years",
    "You're supposed to shake hands",
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

    grade8 = {tid for tid, spec in specs_by_id.items() if spec["grade"] == 8}
    if grade8 != set(EXPECTED):
        extra = sorted(grade8 - set(EXPECTED))
        missing = sorted(set(EXPECTED) - grade8)
        print("八年级生成器集合与改挂表不一致 多 %s 缺 %s" % (
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
