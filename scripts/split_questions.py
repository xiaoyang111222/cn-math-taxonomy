#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 data/questions.json 按学科拆成 data/questions/<学科>.json，并写 data/questions/index.json。

data/questions.json 仍是各 *_build.py 的写入目标（源数据）；前端只读拆分后的文件。
改过 questions.json 之后必须重新跑本脚本，tests/test_questions_split.js 会核对两边一致。

  python3 scripts/split_questions.py           拆分并对账（有任何不一致就非零退出）
  python3 scripts/split_questions.py --check   只核对磁盘上的拆分文件是否和 questions.json 一致，不写文件

学科代码与前端 ?subject= 完全一致：math english physics chinese science morality history geography biology chemistry。
归属按知识点：题目的 topicId 对应 topics.json 里的知识点，取其 subject 字段，没有就按 id 前缀。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "questions")

SUBJECTS = ["math", "chinese", "english", "physics", "chemistry", "biology", "history", "geography", "morality", "science"]
PREFIX = {
    "cnm_": "math", "cne_": "english", "cnp_": "physics", "cnc_": "chinese", "cns_": "science",
    "cnd_": "morality", "cnh_": "history", "cng_": "geography", "cnb_": "biology", "cnk_": "chemistry",
}


def subject_of_topic(topic):
    s = topic.get("subject")
    if s in SUBJECTS:
        return s
    tid = str(topic.get("id", ""))
    for p, name in PREFIX.items():
        if tid.startswith(p):
            return name
    return "math"


def dumps(rows):
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"


def build():
    with open(os.path.join(DATA, "questions.json"), encoding="utf-8") as f:
        questions = json.load(f)
    with open(os.path.join(DATA, "topics.json"), encoding="utf-8") as f:
        topics = json.load(f)
    topic_subject = {t["id"]: subject_of_topic(t) for t in topics}

    buckets = {s: [] for s in SUBJECTS}
    for q in questions:
        s = topic_subject.get(q.get("topicId"))
        if s is None:
            raise SystemExit("题目 %s 的 topicId %r 不在 topics.json 里，无法归属学科" % (q.get("id"), q.get("topicId")))
        buckets[s].append(q)

    problems = []
    if sum(len(v) for v in buckets.values()) != len(questions):
        problems.append("拆分后总数 %d != 原 %d" % (sum(len(v) for v in buckets.values()), len(questions)))
    seen = {}
    for s, rows in buckets.items():
        for q in rows:
            if q["id"] in seen:
                problems.append("题 id %s 同时出现在 %s 与 %s" % (q["id"], seen[q["id"]], s))
            seen[q["id"]] = s
    if {q["id"] for q in questions} != set(seen):
        problems.append("拆分前后题 id 集合不一致")
    empty = [s for s, rows in buckets.items() if not rows]
    if empty:
        problems.append("这些学科没有题：" + "、".join(empty))
    if problems:
        raise SystemExit("对账失败：\n  " + "\n  ".join(problems))

    files = {s + ".json": dumps(rows) for s, rows in buckets.items()}
    index = {
        "total": len(questions),
        "subjects": {s: {"file": s + ".json", "count": len(buckets[s])} for s in SUBJECTS},
    }
    files["index.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    return files, buckets


def main():
    check = "--check" in sys.argv[1:]
    files, buckets = build()
    if check:
        bad = []
        for name, text in files.items():
            path = os.path.join(OUT, name)
            if not os.path.exists(path):
                bad.append(name + " 不存在")
            elif open(path, encoding="utf-8").read() != text:
                bad.append(name + " 与 questions.json 不一致")
        extra = sorted(set(os.listdir(OUT)) - set(files)) if os.path.isdir(OUT) else []
        bad += [n + " 是多余文件" for n in extra]
        if bad:
            raise SystemExit("拆分文件过期，请运行 python3 scripts/split_questions.py：\n  " + "\n  ".join(bad))
        print("拆分文件与 questions.json 一致")
        return
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name not in files:
            os.remove(os.path.join(OUT, name))
    for name, text in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(text)
    total = 0
    print("%-10s %8s %12s" % ("学科", "题数", "字节"))
    for s in SUBJECTS:
        size = os.path.getsize(os.path.join(OUT, s + ".json"))
        total += size
        print("%-10s %8d %12d" % (s, len(buckets[s]), size))
    print("%-10s %8d %12d  (原 questions.json %d 字节)" % (
        "合计", sum(len(v) for v in buckets.values()), total, os.path.getsize(os.path.join(DATA, "questions.json"))))


if __name__ == "__main__":
    main()
