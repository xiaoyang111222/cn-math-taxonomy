# -*- coding: utf-8 -*-
"""高中思想政治（统编版 2019，必修 1–4，选择性必修 1–3）的登记实例。

册次沿用图谱约定，在历史、地理的五册编码上按同样规则顺延：
必修一至必修四 = grade 10–13，选必一至选必三 = grade 14–16，semester 都是「上」。
没有单独的初中思想政治 id；与初中道德与法治有真实承接的点，用 J:cnd_j 硬连。
"""
import re

from senior_lib import Senior, C, N  # noqa: F401

DOMAINS = (
    "中国特色社会主义", "经济与社会", "政治与法治", "哲学与文化",
    "当代国际政治与经济", "法律与生活", "逻辑与思维",
)
BOOK_WORDS = {
    10: "必修一", 11: "必修二", 12: "必修三", 13: "必修四",
    14: "选必一", 15: "选必二", 16: "选必三",
}
BOOK_CODES = {
    10: "B1", 11: "B2", 12: "B3", 13: "B4",
    14: "S1", 15: "S2", 16: "S3",
}
# 章节按「课」编排：必修一 第一课 课名 [框名]。课名、框名内部不要有空格。
CHAPTER_RE = re.compile(
    r"^(必修一|必修二|必修三|必修四|选必一|选必二|选必三) "
    r"第[一二三四五六七八九十]+课 \S+(?: \S+)?$"
)
STD_NOTE = (
    "2026-11-22 已对照人教社转载课标 PDF 的内容要求转述。"
    "编号为本图谱自编，verbatim 为 false。页码见课标条目 page_or_ref。"
)

S = Senior(
    subject="politics", label="思想政治", tag="pol", edition="统编版",
    id_prefix="cnz_h", junior_prefix="cnd_j",
    std_prefix="czs-hs-2017:", std_key="politics_senior",
    std_meta={
        "title": "普通高中思想政治课程标准（2017年版2020年修订）",
        "issuer": "中华人民共和国教育部",
        "year": 2017,
        "stage": "高中必修与选择性必修",
        "note": (
            "条目是对高中思想政治课标必修、选择性必修【内容要求】的转述。"
            "2026-11-22 已逐条对照人教社转载的《普通高中思想政治课程标准（2017年版2020年修订）》PDF"
            "（https://www.pep.com.cn/xw/zt/rjwy/gzkb2020/202205/P020220517519869509154.pdf，文字层；"
            "封面为 PDF 第 1 页，印刷页码 1 在 PDF 第 2 页，印刷页码 = PDF 页码减 1）。"
            "page_or_ref 为课标印刷页码。库存不收教学提示和学业要求，verbatim 仍为 false。"
            "编号 czs-hs-2017 是本图谱编的，不是教育部原编号；"
            "B1–B4 对应必修《中国特色社会主义》《经济与社会》《政治与法治》《哲学与文化》，"
            "S1–S3 对应选择性必修《当代国际政治与经济》《法律与生活》《逻辑与思维》。"
            "章节依据统编版（2019）高中思想政治的公开课序，未逐页核对纸质课本。"
        ),
        "textbook": (
            "人民教育出版社统编版必修1《中国特色社会主义》、必修2《经济与社会》、"
            "必修3《政治与法治》、必修4《哲学与文化》，"
            "选择性必修1《当代国际政治与经济》、选择性必修2《法律与生活》、"
            "选择性必修3《逻辑与思维》（2019年版）"
        ),
    },
    domains=DOMAINS,
    book_title={
        10: "必修1《中国特色社会主义》",
        11: "必修2《经济与社会》",
        12: "必修3《政治与法治》",
        13: "必修4《哲学与文化》",
        14: "选择性必修1《当代国际政治与经济》",
        15: "选择性必修2《法律与生活》",
        16: "选择性必修3《逻辑与思维》",
    },
    book_words=BOOK_WORDS,
    book_codes=BOOK_CODES,
    chapter_re=CHAPTER_RE,
    std_note=STD_NOTE,
    count_expect={10: 20, 11: 26, 12: 30, 13: 27, 14: 20, 15: 15, 16: 15},
)
T = S.T
plan = S.plan
clause = S.clause


def Q4(rows):
    """四题，顺序必须是 basic、basic、standard、challenge。每题 (prompt, right, [三个干扰], expl)。"""
    diffs = ("basic", "basic", "standard", "challenge")
    if len(rows) != 4:
        raise SystemExit("Q4 需要恰好 4 题")
    out = []
    for diff, row in zip(diffs, rows):
        prompt, right, wrongs, expl = row
        out.append(C(diff, prompt, right, wrongs, expl))
    return out
