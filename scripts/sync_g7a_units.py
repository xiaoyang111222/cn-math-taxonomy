#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把七上英语生成器里已改的单元、名称和题目写回稳定 id。

不调用 enj_build.main，不追加知识点，不改课标、confidence、verbatim，
也不改七年级下册及以后的题目。可重复运行：没有差异时不改文件。
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

import enj_build  # noqa: E402
from en_lib import TOPICS, check_question, materialise_questions  # noqa: E402
from enj_build import build_question, chapter  # noqa: E402

# 只改「」里的旧名称。小学边不在这里改。
NAME_IN_REASON = [
    ("「This is 与 These are」", "「指示代词 this、that、these、those」"),
    ("「认领失物」", "「确认物品是谁的」"),
    ("「读失物招领」", "「读物品归属」"),
    ("「谈论运动」", "「谈论社团运动」"),
    ("「读运动短文」", "「读体育社团短文」"),
    ("「读活动安排」", "「读生日安排」"),
    ("「衣物与颜色」", "「生日聚会」"),
    ("「购物用语」", "「为聚会询价」"),
    ("「读购物对话」", "「读聚会购物」"),
    ("「场所」", "「学校场所」"),
    ("「问路与指路」", "「询问学校场所」"),
    ("「读路线说明」", "「读学校位置」"),
]

# 这些软边如果继续写「新版单元顺序」，会把待核项说成已经挂进某一课。
REASON_OVERRIDE = {
    ("cne_j036", "cne_j056"): (
        "月份与序数词在七年级上册第7单元。出行方式没有核到本册某一单元，"
        "这条软边只保留原来的学习顺序。"
    ),
    ("cne_j040", "cne_j098"): (
        "学科词汇在七年级上册第4单元。连读没有核到该单元，"
        "这条软边只保留原来的学习顺序。"
    ),
    ("cne_j098", "cne_j078"): (
        "连读没有核到七年级上册的某一单元，这条软边只保留原来的学习顺序。"
    ),
    ("cne_j107", "cne_j043"): (
        "不完全爆破没有核到 Fun Clubs，这条软边只保留原来的学习顺序。"
    ),
    ("cne_j008", "cne_p014"): "指示代词 this、that、these、those 承接小学的 This is。",
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parts(q):
    if q.get("type") != "choice":
        raise SystemExit("七上英语题不是选择题：%s" % q.get("id"))
    ans = next(c["text"] for c in q["choices"] if c["key"] == q["answer"])
    wrongs = sorted(c["text"] for c in q["choices"] if c["key"] != q["answer"])
    return q["prompt"], ans, wrongs, q["explanation"]


def main():
    if len(TOPICS) != 245 or TOPICS[0]["key"] != "ph_stress":
        print("初中英语主干不是 245 条", file=sys.stderr)
        return 1
    topics = load("topics.json")
    questions = load("questions.json")
    deps = load("dependencies.json")
    by_id = {t["id"]: t for t in topics}
    standards_before = {t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True) for t in topics}
    figures_before = {q["id"]: q["figure"] for q in questions if "figure" in q}

    q_index = {}
    for i, q in enumerate(questions):
        q_index.setdefault(q["topicId"], []).append(i)

    changed_topics = []
    changed_q = 0
    for i, spec in enumerate(TOPICS, start=1):
        if spec["grade"] != 7 or spec["semester"] != "上":
            continue
        tid = "cne_j%03d" % i
        topic = by_id.get(tid)
        if topic is None:
            print("缺少 %s" % tid, file=sys.stderr)
            return 1
        if topic.get("subject") != "english" or topic.get("grade") != 7 or topic.get("semester") != "上":
            print("%s 不在七年级上册英语" % tid, file=sys.stderr)
            return 1
        made = materialise_questions(spec)
        for item in made:
            check_question(spec["key"], item)
        built = []
        for n, item in enumerate(made, start=1):
            q, shown = build_question(tid, n, item, slot=i + n)
            built.append((q, shown, item))
        idxs = q_index.get(tid, [])
        if len(idxs) != 4:
            print("%s 题目不是 4 道" % tid, file=sys.stderr)
            return 1
        olds = [questions[k] for k in idxs]
        if [q["id"] for q in olds] != ["%s_q%d" % (tid, n) for n in range(1, 5)]:
            print("%s 题目 id 顺序异常" % tid, file=sys.stderr)
            return 1
        ch = chapter(spec["grade"], spec["semester"], spec["unit"])
        q_differ = False
        for old, (_q, _shown, item) in zip(olds, built):
            op, oa, ow, oe = parts(old)
            if (op, oa, ow, oe) != (item["p"], item["a"], sorted(item["w"]), item["e"]):
                q_differ = True
                break
        meta_differ = (
            topic["name"] != spec["name"]
            or topic["description"] != spec["description"]
            or topic["chapter"] != ch
        )
        if not meta_differ and not q_differ:
            continue
        topic["name"] = spec["name"]
        topic["description"] = spec["description"]
        topic["chapter"] = ch
        if q_differ:
            for k, (q, shown, _item) in zip(idxs, built):
                if "figure" in questions[k]:
                    print("%s 带配图，拒绝覆盖" % questions[k]["id"], file=sys.stderr)
                    return 1
                questions[k] = q
                changed_q += 1
            topic["diagnostic_question"] = {"question": built[0][0]["prompt"], "answer": built[0][1]}
        changed_topics.append(tid)

    reason_n = 0
    for e in deps:
        key = (e["topicId"], e["prerequisiteId"])
        if key in REASON_OVERRIDE:
            if e["reason"] != REASON_OVERRIDE[key]:
                e["reason"] = REASON_OVERRIDE[key]
                reason_n += 1
            continue
        if not str(e["topicId"]).startswith("cne_j"):
            continue
        reason = e["reason"]
        new = reason
        for old, nxt in NAME_IN_REASON:
            new = new.replace(old, nxt)
        if new != reason:
            e["reason"] = new
            reason_n += 1

    standards_after = {t["id"]: json.dumps(t.get("standards"), ensure_ascii=False, sort_keys=True) for t in topics}
    if standards_before != standards_after:
        print("standards 被改动", file=sys.stderr)
        return 1
    figures_after = {q["id"]: q["figure"] for q in questions if "figure" in q}
    if figures_before != figures_after:
        print("配图被改动", file=sys.stderr)
        return 1
    for t in topics:
        if t.get("subject") == "english" and t.get("grade") == 7 and t.get("semester") == "上":
            continue
        # 非七上英语的 standards 已在上面整体比对。这里再确认 grade/semester 没被写到七上以外。
    touched = set(changed_topics)
    for t in topics:
        if t["id"] in touched:
            if t.get("grade") != 7 or t.get("semester") != "上":
                print("把 %s 写出了七上" % t["id"], file=sys.stderr)
                return 1

    if not changed_topics and reason_n == 0:
        print("没有差异")
        return 0
    dump("topics.json", topics)
    dump("questions.json", questions)
    dump("dependencies.json", deps)
    print("topics %d questions %d reasons %d" % (len(changed_topics), changed_q, reason_n))
    print(" ".join(changed_topics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
