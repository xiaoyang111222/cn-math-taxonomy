#!/usr/bin/env python3
"""README 数字一致性检查（仅标准库）。

从 data/ 重算统计数字，与 README.md「### 数据规模」一节的合计段落、分学科表格，
以及「hujiao-math.json … N 条」表述逐项比对。全部一致 exit 0，否则逐条打印
「位置 / README 值 / 实测值」并 exit 1。按内容锚点定位，不依赖行号。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

# 知识点按 id 前缀归属学科。依据：topics.json 里除数学外的每个知识点都带 subject 字段，
# 且「前缀 -> subject」在全部 4,231 条上一一对应（数学 cnm 无 subject 字段）。
# 脚本另会交叉校验 subject 字段与本表一致；某前缀映射为 None 则只校验该学科题数。
PREFIX_TO_SUBJECT = {
    "cnm": "math",
    "cnc": "chinese",
    "cne": "english",
    "cnp": "physics",
    "cnd": "morality",
    "cns": "science",
    "cnh": "history",
    "cnb": "biology",
    "cng": "geography",
    "cnz": "politics",
    "cnk": "chemistry",
}

# README 表格中的学科中文名 -> questions/index.json 的学科键
LABEL_TO_SUBJECT = {
    "数学": "math",
    "语文": "chinese",
    "英语": "english",
    "物理": "physics",
    "道德与法治": "morality",
    "科学": "science",
    "历史": "history",
    "生物": "biology",
    "地理": "geography",
    "思想政治": "politics",
    "化学": "chemistry",
}

problems = []


def mismatch(where, readme_val, actual):
    problems.append((where, readme_val, actual))


def num(s):
    return int(s.replace(",", ""))


def load(rel):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def compute():
    topics = load("data/topics.json")
    deps = load("data/dependencies.json")
    qindex = load("data/questions/index.json")
    standards = load("data/cn-curriculum-standards.json")
    hujiao = load("data/mappings/hujiao-math.json")

    strength = Counter(d.get("strength") for d in deps)
    q_by_subject = {k: v["count"] for k, v in qindex["subjects"].items()}

    topics_by_subject = Counter()
    unknown_prefix = Counter()
    for t in topics:
        m = re.match(r"^([a-z]+)", t["id"])
        prefix = m.group(1) if m else ""
        subj = PREFIX_TO_SUBJECT.get(prefix)
        if subj is None:
            unknown_prefix[prefix] += 1
            continue
        declared = t.get("subject")
        if declared is not None and declared != subj:
            mismatch(f"topics.json {t['id']} 的 subject 字段与 id 前缀映射", declared, subj)
        topics_by_subject[subj] += 1

    return {
        "topics": len(topics),
        "edges": len(deps),
        "hard": strength.get("hard", 0),
        "soft": strength.get("soft", 0),
        "questions": qindex["total"],
        "q_sum": sum(q_by_subject.values()),
        "q_by_subject": q_by_subject,
        "t_by_subject": dict(topics_by_subject),
        "unknown_prefix": dict(unknown_prefix),
        "subjects": len(q_by_subject),
        "standards": len(standards["items"]),
        "hujiao": len(hujiao["entries"]),
    }


def section_after(text, heading):
    m = re.search(r"^###\s*" + re.escape(heading) + r"\s*$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^#{1,6}\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def check_paragraph(para, a):
    def grab(label, pattern, actual):
        m = re.search(pattern, para)
        if not m:
            mismatch(f"数据规模·合计段落：{label}", "（未找到该表述）", actual)
            return
        val = num(m.group(1))
        if val != actual:
            mismatch(f"数据规模·合计段落：{label}", val, actual)

    grab("知识点总数", r"([\d,]+)\*\*\s*个知识点", a["topics"])
    grab("先修边总数", r"([\d,]+)\*\*\s*条先修边", a["edges"])
    grab("hard 边数", r"hard\s*([\d,]+)", a["hard"])
    grab("soft 边数", r"soft\s*([\d,]+)", a["soft"])
    grab("题目总数", r"([\d,]+)\*\*\s*道题", a["questions"])
    grab("学科数", r"([\d,]+)\*\*\s*个学科", a["subjects"])
    grab("课程标准条目数", r"课程标准条目\s*\*\*([\d,]+)\*\*", a["standards"])


def check_table(table_lines, a):
    rows = {}
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not re.fullmatch(r"[\d,]+", cells[1]) or not re.fullmatch(r"[\d,]+", cells[2]):
            continue
        rows[cells[0]] = (num(cells[1]), num(cells[2]))

    if not rows:
        mismatch("数据规模·分学科表格", "（未找到数据行）", "11 个学科 + 合计")
        return

    for label, subj in LABEL_TO_SUBJECT.items():
        if label not in rows:
            mismatch(f"数据规模·表格行「{label}」", "（缺行）", "应有")
            continue
        t_readme, q_readme = rows[label]
        q_actual = a["q_by_subject"].get(subj)
        if q_actual is not None and q_readme != q_actual:
            mismatch(f"数据规模·表格「{label}」题数", q_readme, q_actual)
        if PREFIX_TO_SUBJECT and subj in PREFIX_TO_SUBJECT.values():
            t_actual = a["t_by_subject"].get(subj, 0)
            if t_readme != t_actual:
                mismatch(f"数据规模·表格「{label}」知识点数", t_readme, t_actual)

    for label in rows:
        if label not in LABEL_TO_SUBJECT and label != "合计":
            mismatch(f"数据规模·表格行「{label}」", "（未知学科名）", "无对应学科")

    if "合计" not in rows:
        mismatch("数据规模·表格合计行", "（缺行）", "应有")
    else:
        t_readme, q_readme = rows["合计"]
        if t_readme != a["topics"]:
            mismatch("数据规模·表格合计行知识点", t_readme, a["topics"])
        if q_readme != a["questions"]:
            mismatch("数据规模·表格合计行题数", q_readme, a["questions"])


def check_hujiao(text, a):
    pattern = re.compile(r"(?:hujiao-math\.json|沪教版小学数学映射)[^\n]*?([\d,]+)\s*条")
    for m in pattern.finditer(text):
        val = num(m.group(1))
        line_no = text.count("\n", 0, m.start()) + 1
        if val != a["hujiao"]:
            mismatch(f"README 第 {line_no} 行 hujiao-math.json 映射条数", val, a["hujiao"])


def main():
    a = compute()
    text = README.read_text(encoding="utf-8")

    if a["unknown_prefix"]:
        mismatch("topics.json 出现映射表之外的 id 前缀", a["unknown_prefix"], "需补充 PREFIX_TO_SUBJECT")
    if a["questions"] != a["q_sum"]:
        mismatch("questions/index.json total 与各科 count 之和", a["questions"], a["q_sum"])
    if a["hard"] + a["soft"] != a["edges"]:
        mismatch("dependencies.json strength 仅含 hard/soft", a["hard"] + a["soft"], a["edges"])

    sec = section_after(text, "数据规模")
    if sec is None:
        mismatch("README 「### 数据规模」标题", "（未找到）", "应存在")
    else:
        lines = sec.splitlines()
        first_table = next((i for i, l in enumerate(lines) if l.lstrip().startswith("|")), len(lines))
        check_paragraph("\n".join(lines[:first_table]), a)
        check_table([l for l in lines[first_table:] if l.lstrip().startswith("|")], a)

    check_hujiao(text, a)

    if problems:
        print(f"README 数字与 data/ 实测不一致，共 {len(problems)} 处：")
        for where, readme_val, actual in problems:
            print(f"  - {where} / README 值: {readme_val} / 实测值: {actual}")
        return 1

    print(
        f"OK README 数字与 data/ 一致："
        f"知识点 {a['topics']:,}，先修边 {a['edges']:,}（hard {a['hard']:,}，soft {a['soft']:,}），"
        f"题 {a['questions']:,}，学科 {a['subjects']}，课标条目 {a['standards']:,}，沪教映射 {a['hujiao']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
