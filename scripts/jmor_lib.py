# -*- coding: utf-8 -*-
"""初中道德与法治（六三制，七上至八下）登记。由 scripts/jmor_build.py 调用。

目录不是官方逐课核实：
教师之家 / dzskb 的课名、框名只作公开转述。人教社公开文本多只核到单元名。
每条 catalog_status 固定为 pending_official_lesson_list，不得写成已核实。
九上、九下本批不建点。

课标五主题是公开解读的推断，verbatim 必须为 false，不编课标原文。
"""

import re

TOPICS = []
EDGES = []  # (src_key, dst_key, strength, reason) src 依赖 dst

DOMAINS = (
    "生命安全与健康教育",
    "法治教育",
    "中华优秀传统文化教育",
    "革命传统教育",
    "国情教育",
)
CODE_OF = {
    "JK": "生命安全与健康教育",
    "FZ": "法治教育",
    "WH": "中华优秀传统文化教育",
    "GY": "革命传统教育",
    "GQ": "国情教育",
}
TYPES = ("conceptual", "procedural", "reasoning", "application")

# 只标主题，不假装是课标条款原文。
STANDARD_ROWS = [
    ("jk", "4", "JK", "生命安全与健康教育",
     "第四学段学习主题：生命安全与健康教育。这里只记下主题名称，供知识点推断对齐，不是教育部 PDF 的逐条内容要求。"),
    ("fz", "4", "FZ", "法治教育",
     "第四学段学习主题：法治教育。这里只记下主题名称，供知识点推断对齐，不是教育部 PDF 的逐条内容要求。"),
    ("wh", "4", "WH", "中华优秀传统文化教育",
     "第四学段学习主题：中华优秀传统文化教育。这里只记下主题名称，供知识点推断对齐，不是教育部 PDF 的逐条内容要求。"),
    ("gy", "4", "GY", "革命传统教育",
     "第四学段学习主题：革命传统教育。这里只记下主题名称，供知识点推断对齐，不是教育部 PDF 的逐条内容要求。"),
    ("gq", "4", "GQ", "国情教育",
     "第四学段学习主题：国情教育。这里只记下主题名称，供知识点推断对齐，不是教育部 PDF 的逐条内容要求。"),
]

UNITS = {}
_CUR = {}

NOTICE_URL = "https://www.moe.gov.cn/srcsite/A26/s8001/202204/t20220420_619921.html"
PDF_URL = "https://www.moe.gov.cn/srcsite/A26/s8001/202204/W020220420582343475848.pdf"
CATALOG_STATUS = "pending_official_lesson_list"
CATALOG_NOTE = (
    "课名和框名来自教师之家、dzskb 等公开转述；人教社公开文本通常只核到单元名。"
    "教材目录待官方逐课核实，本条不是已核实的教材原文。"
)

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求")
_BANNED_COPY = re.compile(r"免费|AI\s*初稿|AI初稿")
_AGE_RULE = re.compile(
    r"刑事责任年龄|不满(?:八|8|十二|12|十四|14|十六|16|十八|18)周岁|"
    r"(?:8|12|14|16|18)\s*周岁(?:以上|以下|不满)|限制民事行为能力|无民事行为能力"
)


def vol(grade, sem):
    _CUR["g"], _CUR["s"] = grade, sem


def unit(n, title):
    g, s = _CUR["g"], _CUR["s"]
    if g == 9:
        raise SystemExit("九上九下本批不建点")
    if g not in (7, 8) or s not in ("上", "下"):
        raise SystemExit("册次只允许七上、七下、八上、八下")
    UNITS[(g, s, n)] = title


def chapter(grade, sem, unit_n):
    cn = "零一二三四五六七八九"[grade]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit_n, UNITS[(grade, sem, unit_n)])


def _edge(topic, prereq, strength, reason):
    if not reason or len(reason) < 8:
        raise SystemExit("先修理由过短：%s → %s" % (topic, prereq))
    EDGES.append((topic, prereq, strength, reason))


def hard(topic, prereq, reason):
    _edge(topic, prereq, "hard", reason)


def soft(topic, prereq, reason):
    _edge(topic, prereq, "soft", reason)


def K(tid, key, name, unit_n, typ, desc, criteria, qs, std, domain, lesson, frames, root_reason=None, frame_note=""):
    """qs：4 道选择题 (题干, 正确答案, [三个干扰项], 解析)。难度 basic、basic、standard、challenge。"""
    g, s = _CUR["g"], _CUR["s"]
    if (g, s, unit_n) not in UNITS:
        raise SystemExit("%s 单元未登记" % key)
    if not re.fullmatch(r"cnd_j\d{3}", tid):
        raise SystemExit("id 必须是 cnd_jNNN：%s" % tid)
    if domain not in DOMAINS:
        raise SystemExit("%s 领域非法：%s" % (key, domain))
    if typ not in TYPES:
        raise SystemExit("%s type 非法：%s" % (key, typ))
    if std not in {row[0] for row in STANDARD_ROWS}:
        raise SystemExit("%s 课标符号非法：%s" % (key, std))
    if not (isinstance(criteria, (list, tuple)) and 2 <= len(criteria) <= 3):
        raise SystemExit("%s mastery_criteria 需要 2–3 条" % key)
    if len(qs) != 4:
        raise SystemExit("%s 需要恰好 4 题" % key)
    if any(t["key"] == key or t["id"] == tid for t in TOPICS):
        raise SystemExit("知识点重复：%s / %s" % (tid, key))
    extra = (" " + frame_note) if frame_note else ""
    note = (CATALOG_NOTE + extra).strip()
    full_desc = "%s框：%s。%s%s" % (lesson, frames, desc, extra)
    TOPICS.append({
        "id": tid,
        "key": key,
        "name": name,
        "domain": domain,
        "grade": g,
        "semester": s,
        "unit": unit_n,
        "type": typ,
        "description": full_desc.strip(),
        "mastery_criteria": list(criteria),
        "std": std,
        "conf": "inferred",
        "note": note.strip(),
        "items": [tuple(q) for q in qs],
        "catalog_status": CATALOG_STATUS,
        "lesson": lesson,
        "frames": frames,
        "root_reason": root_reason,
    })


def check_question(key, q):
    if _BANNED_START.match(q["p"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["p"][:20]))
    blob = "\n".join([q["p"], q["e"], q["a"]] + q["w"])
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语" % key)
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    if _AGE_RULE.search(blob):
        raise SystemExit("%s 含未核年龄细则，本批禁止写入：%s" % (key, q["p"][:24]))
    opts = [q["a"]] + q["w"]
    if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
        raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    if len(q["e"]) < 20:
        raise SystemExit("%s 解析过短" % key)
    if q["a"] not in q["e"] and q["e"].find(q["a"][:6]) < 0:
        # 解析须能独立读懂，不强制复读选项全文，但要有理由句。
        if "。" not in q["e"]:
            raise SystemExit("%s 解析不是完整句子" % key)


def materialise_questions(spec):
    diffs = ["basic", "basic", "standard", "challenge"]
    made = []
    for diff, item in zip(diffs, spec["items"]):
        prompt, answer, wrongs, expl = item
        if len(wrongs) != 3:
            raise SystemExit("%s 干扰项必须是 3 个" % spec["key"])
        made.append({
            "d": diff, "p": str(prompt).strip(), "a": str(answer).strip(),
            "w": [str(w).strip() for w in wrongs], "e": str(expl).strip(),
        })
    return made
