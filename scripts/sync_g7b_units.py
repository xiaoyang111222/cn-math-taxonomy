#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把七下英语生成器里已改的单元、名称写回稳定 id。

不调用 enj_build.main，不追加知识点，不改课标、confidence、verbatim，
也不改题目（不写 questions.json）。可重复运行：没有差异时不改文件。

只用 TOPICS 的 key 顺序映射 cne_j001–cne_j245。cne_j246–cne_j257 不在
TOPICS 里，其中 j247、j248 的 chapter 已正确，本脚本不改它们。

只改生成器 grade/semester 为 7 下的点（含已从其它册改挂到七下的
habit 四点、story 三点）的 name/description/chapter。不用 chapter()
覆盖八上/八下已用新课名的点（尤其 cne_j072 感叹句、cne_j164 unless）。
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

WKND_PENDING_KEYS = {"rw_wknd"}
WKND_REMOUNT_KEYS = {"vo_wknd", "fu_wknd"}
WKND_KEYS = WKND_PENDING_KEYS | WKND_REMOUNT_KEYS
REMOUNT_KEYS = {
    "vo_habit", "gr_howoften", "fu_habit", "rw_habit",
    "vo_story", "fu_story", "rw_story",
}
NEVER_OVERWRITE_CHAPTER = {"cne_j072", "cne_j164"}

# 软边理由：已按官方目录改挂的，改写成官方课序；仍待核的，避免说成已挂进某一课。
REASON_OVERRIDE = {
    ("cne_j093", "cne_j092"): (
        "旅行日记在七下第7单元 A Day to Remember；周末活动在官方七下目录无同名课"
        "（第8单元是讲故事），这条软边只保留原来的学习顺序。"
    ),
    ("cne_j094", "cne_j093"): (
        "Did 提问在七下第8单元 Once upon a Time（Simple past tense (2)）；"
        "周末活动无同名课，软边只保留原来的学习顺序。"
    ),
    ("cne_j095", "cne_j094"): (
        "Did 提问和不规则动词过去式都在七下第8单元 Once upon a Time"
        "（Simple past tense (2)）。"
    ),
    ("cne_j096", "cne_j095"): (
        "不规则动词过去式在第8单元；谈论上周末无同名课，软边只保留原来的学习顺序。"
    ),
    ("cne_j097", "cne_j096"): (
        "谈论上周末和读周末日记在官方七下目录均无同名课，软边只保留原来的学习顺序。"
    ),
    ("cne_j163", "cne_j097"): (
        "故事用词在七下第8单元 Once upon a Time；读周末日记无同名课，"
        "软边只保留原来的学习顺序。"
    ),
}


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


def nontarget_hash(topics, questions, deps, allowed):
    rows = []
    for t in topics:
        if t["id"] in allowed:
            skip = {"name", "description", "chapter"}
            if t["id"] in {"cne_j010", "cne_j093", "cne_j096", "cne_j097"}:
                skip |= {"grade", "semester"}
            rows.append(("t", t["id"], {k: t[k] for k in t if k not in skip}))
        else:
            rows.append(("t", t["id"], t))
    rows.append(("q", None, questions))
    dep_rows = []
    for e in deps:
        key = (e["topicId"], e["prerequisiteId"])
        if key in REASON_OVERRIDE:
            dep_rows.append({k: e[k] for k in e if k != "reason"})
        else:
            dep_rows.append(e)
    rows.append(("d", None, dep_rows))
    return sha(canon(rows))


def main():
    if len(TOPICS) != 245 or TOPICS[0]["key"] != "ph_stress":
        print("初中英语主干不是 245 条", file=sys.stderr)
        return 1

    topics = load("topics.json")
    questions = load("questions.json")
    deps = load("dependencies.json")
    by_id = {t["id"]: t for t in topics}
    q_bytes_before = open(os.path.join(ROOT, "data", "questions.json"), "rb").read()
    standards_before = {
        t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True)
        for t in topics
    }

    allowed = set()
    specs_by_id = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_j%03d" % i
        if spec["key"] in REMOUNT_KEYS and not (spec["grade"] == 7 and spec["semester"] == "下"):
            print("%s 应从其它册改挂到七下，生成器仍是 %s%s" % (
                spec["key"], spec["grade"], spec["semester"]), file=sys.stderr)
            return 1
        if spec["grade"] != 7 or spec["semester"] != "下":
            continue
        if tid in NEVER_OVERWRITE_CHAPTER:
            print("拒绝覆盖 %s" % tid, file=sys.stderr)
            return 1
        allowed.add(tid)
        specs_by_id[tid] = spec

    missing_remount = REMOUNT_KEYS - {specs_by_id[tid]["key"] for tid in allowed}
    if missing_remount:
        print("改挂点未进入七下集合：%s" % ", ".join(sorted(missing_remount)), file=sys.stderr)
        return 1

    before_hash = nontarget_hash(topics, questions, deps, allowed)

    changed_topics = []
    for tid, spec in specs_by_id.items():
        topic = by_id.get(tid)
        if topic is None:
            print("缺少 %s" % tid, file=sys.stderr)
            return 1
        if topic.get("subject") != "english":
            print("%s 不是英语" % tid, file=sys.stderr)
            return 1
        if tid in NEVER_OVERWRITE_CHAPTER:
            print("拒绝覆盖 %s" % tid, file=sys.stderr)
            return 1
        ch = chapter(spec["grade"], spec["semester"], spec["unit"])
        if spec["key"] in WKND_PENDING_KEYS:
            if ch != "七年级下册 待核":
                print("%s chapter() 不是七下待核：%s" % (tid, ch), file=sys.stderr)
                return 1
            if topic.get("grade") != 7 or topic.get("semester") != "下":
                topic["grade"] = 7
                topic["semester"] = "下"
        if spec["key"] in WKND_REMOUNT_KEYS:
            if ch != "七年级下册 第7单元 A Day to Remember":
                print("%s chapter() 不是七下第7单元：%s" % (tid, ch), file=sys.stderr)
                return 1
            if topic.get("grade") != 7 or topic.get("semester") != "下":
                topic["grade"] = 7
                topic["semester"] = "下"
        meta_differ = (
            topic["name"] != spec["name"]
            or topic["description"] != spec["description"]
            or topic["chapter"] != ch
        )
        if not meta_differ:
            continue
        topic["name"] = spec["name"]
        topic["description"] = spec["description"]
        topic["chapter"] = ch
        changed_topics.append(tid)

    reason_n = 0
    for e in deps:
        key = (e["topicId"], e["prerequisiteId"])
        if key not in REASON_OVERRIDE:
            continue
        if e["strength"] == "hard":
            print("拒绝改硬边理由 %s←%s" % key, file=sys.stderr)
            return 1
        if e["reason"] != REASON_OVERRIDE[key]:
            e["reason"] = REASON_OVERRIDE[key]
            reason_n += 1

    standards_after = {
        t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True)
        for t in topics
    }
    if standards_before != standards_after:
        print("standards 被改动", file=sys.stderr)
        return 1
    q_bytes_after = open(os.path.join(ROOT, "data", "questions.json"), "rb").read()
    if q_bytes_after != q_bytes_before:
        print("questions.json 被改动", file=sys.stderr)
        return 1
    after_hash = nontarget_hash(topics, questions, deps, allowed)
    if after_hash != before_hash:
        print("非目标对象被改动", file=sys.stderr)
        return 1
    for tid in ("cne_j247", "cne_j248", "cne_j072", "cne_j164"):
        if tid in changed_topics:
            print("误改 %s" % tid, file=sys.stderr)
            return 1

    changed_q = 0
    drop_n = 0
    if not changed_topics and reason_n == 0:
        print("没有差异")
        return 0
    dump("topics.json", topics)
    dump("dependencies.json", deps)
    print("topics %d questions %d reasons %d dropped %d" % (
        len(changed_topics), changed_q, reason_n, drop_n))
    print(" ".join(changed_topics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
