"""高中必修数据的登记表。由 scripts/hs_build.py 编译进 data/*.json。"""
from __future__ import annotations

TOPICS = []
QUESTIONS = {}
EDGES = []
STANDARDS = []


# 2026-10-21：高中 80 条条目的课标印刷页码（官方 PDF 有文字层，按主题/单元定位；PDF 页码 = 印刷页码 + 3）。
PAGES = {}
for _mod, _spans in {
    "PRE": [(1, 4, 18), (5, 8, 19), (9, 9, 20)],
    "FUN": [(1, 5, 22), (6, 9, 23), (10, 11, 25), (12, 17, 24), (18, 21, 40), (22, 25, 41)],
    "GA": [(1, 4, 28), (5, 7, 29), (8, 11, 30), (12, 12, 31), (13, 15, 44), (16, 19, 45), (20, 23, 46)],
    "PS": [(1, 3, 34), (4, 4, 35), (5, 8, 33), (9, 11, 48), (12, 16, 49), (17, 19, 50)],
    "MI": [(1, 2, 36), (3, 4, 52)],
}.items():
    for _a, _b, _p in _spans:
        for _n in range(_a, _b + 1):
            PAGES["%s.%02d" % (_mod, _n)] = _p

# 课标标星的选学条款（2025 修订版印刷页 40「内容包括…数学归纳法」带星号）
ELECTIVE = {"FUN.21"}


def standard(code, domain, theme, section, clause, text):
    STANDARDS.append({
        "code": code,
        "domain": domain,
        "theme": theme,
        "section": section,
        "clause": clause,
        "text": text,
    })


def topic(key, book, chapter, section, name, domain, typ, desc, crit, std, conf="exact", note=None):
    if any(t["key"] == key for t in TOPICS):
        raise SystemExit("知识点 key 重复：%s" % key)
    if not (2 <= len(crit) <= 3):
        raise SystemExit("%s 掌握标准须 2–3 条" % key)
    TOPICS.append({
        "key": key,
        "book": book,
        "chapter": chapter,
        "section": section,
        "name": name,
        "domain": domain,
        "type": typ,
        "description": desc,
        "mastery_criteria": list(crit),
        "std": std,
        "confidence": conf,
        "note": note,
    })


def questions(key, items):
    if key in QUESTIONS:
        raise SystemExit("题目重复：%s" % key)
    if len(items) != 4:
        raise SystemExit("%s 需要 4 道题，实际 %d" % (key, len(items)))
    QUESTIONS[key] = items


def edge(src, dst, strength, reason):
    EDGES.append((src, dst, strength, reason))


def hard(src, dst, reason):
    edge(src, dst, "hard", reason)


def soft(src, dst, reason):
    edge(src, dst, "soft", reason)
