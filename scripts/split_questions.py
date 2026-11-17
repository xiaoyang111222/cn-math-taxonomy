#!/usr/bin/env python3
"""把 data/questions.json 按 topicId 前缀拆成三份学科分片（原文件保留不动）。

  cnm_ → data/questions-math.json
  cne_ → data/questions-english.json
  cnp_ → data/questions-physics.json

前端（explore/、diagnose/、practice/）优先读当前学科的分片，分片缺失（404）时回退到 questions.json。
改了题库之后重新运行：python3 scripts/split_questions.py   （--check 只检查分片是否与总文件一致）
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SHARDS = (('cnm_', 'questions-math.json'), ('cne_', 'questions-english.json'), ('cnp_', 'questions-physics.json'))


def split(rows):
    out = {name: [] for _, name in SHARDS}
    for q in rows:
        tid = q.get('topicId', '')
        for prefix, name in SHARDS:
            if tid.startswith(prefix):
                out[name].append(q)
                break
    return out


def dump(rows):
    return json.dumps(rows, ensure_ascii=False, indent=2) + '\n'


def main(argv):
    check = '--check' in argv
    with open(os.path.join(DATA, 'questions.json'), encoding='utf-8') as f:
        rows = json.load(f)
    parts = split(rows)
    missing = len(rows) - sum(len(v) for v in parts.values())
    if missing:
        print('有 %d 道题的 topicId 不属于任何学科前缀' % missing)
        return 1
    bad = []
    for name, part in parts.items():
        path = os.path.join(DATA, name)
        text = dump(part)
        if check:
            try:
                with open(path, encoding='utf-8') as f:
                    if json.load(f) != part:
                        bad.append(name)
            except FileNotFoundError:
                bad.append(name)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        print('%-24s %5d 题' % (name, len(part)))
    if bad:
        print('分片与 questions.json 不一致：%s；请运行 python3 scripts/split_questions.py' % '、'.join(bad))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
