#!/usr/bin/env python3
"""把 his_edges.py 里登记的初中历史补边（extra）增量写进 data/dependencies.json。

补边的源头是 his_edges.py；his_build.py 整体重建时也会在约简之后写入同一批边。
本脚本只追加边，不动知识点、题目、课标，也不重排文件，用于已有数据上的增量补边。
可重复运行：已存在且内容相同的边跳过；与已有边冲突则报错。

用法：python3 scripts/his_extra_edges.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import his_build  # noqa: E402
from his_lib import EXTRA, TOPICS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    dry = "--dry-run" in sys.argv
    if his_build.order_topics() != 0:
        return 1
    id_of = {t["key"]: "cnh_j%03d" % i for i, t in enumerate(TOPICS, start=1)}
    by_key = {t["key"]: t for t in TOPICS}
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    path = os.path.join(ROOT, "data", "dependencies.json")
    with open(path, encoding="utf-8") as f:
        deps = json.load(f)
    topics_path = os.path.join(ROOT, "data", "topics.json")
    with open(topics_path, encoding="utf-8") as f:
        names = {t["id"]: t["name"] for t in json.load(f) if t["id"].startswith("cnh_j")}
    for key, tid in id_of.items():
        if names.get(tid) != by_key[key]["name"]:
            print("topics.json 里 %s 的名称与源脚本不一致，先运行 his_build.py" % tid, file=sys.stderr)
            return 1
    existing = {(e["topicId"], e["prerequisiteId"]): e for e in deps}
    errors, todo, seen = [], [], set()
    for src, dst, strength, reason in EXTRA:
        if src not in id_of or dst not in id_of:
            errors.append("端点不存在：%s <- %s" % (src, dst))
            continue
        if index[dst] >= index[src]:
            errors.append("先修不早于后续：%s <- %s" % (src, dst))
            continue
        if strength not in ("hard", "soft") or not str(reason).strip():
            errors.append("强度或理由不合法：%s <- %s" % (src, dst))
            continue
        pair = (id_of[src], id_of[dst])
        if pair in seen:
            errors.append("本脚本内重复：%s <- %s" % (src, dst))
            continue
        seen.add(pair)
        old = existing.get(pair)
        if old is not None:
            if old["strength"] != strength or old["reason"] != reason:
                errors.append("与已有边重复且内容不同：%s <- %s" % (src, dst))
            continue
        todo.append({"topicId": pair[0], "prerequisiteId": pair[1], "strength": strength, "reason": reason})
    adj = defaultdict(list)
    for e in deps + todo:
        adj[e["topicId"]].append(e["prerequisiteId"])
    color = {}
    for s in list(adj):
        if s in color:
            continue
        stack = [(s, iter(adj[s]))]
        color[s] = 1
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                color[node] = 2
                stack.pop()
                continue
            c = color.get(nxt, 0)
            if c == 1:
                errors.append("成环：经过 %s -> %s" % (node, nxt))
            elif c == 0:
                color[nxt] = 1
                stack.append((nxt, iter(adj[nxt])))
    if errors:
        for m in errors:
            print(m, file=sys.stderr)
        return 1
    print("计划新增 %d 条（脚本内共 %d 条，已存在跳过 %d 条）" % (len(todo), len(EXTRA), len(EXTRA) - len(todo)))
    if dry or not todo:
        return 0
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deps + todo, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
