# -*- coding: utf-8 -*-
"""初中道德与法治（六三制，七上至九上）登记。由 scripts/jmor_build.py 调用。

七上至九上 catalog_status 为 official_toc：课名、框名和目录印刷页码来自
智慧教育平台官方阅读器。对不上官方课、框的点用 unit 90，章节为「N年级X册 待核」，
catalog_status 为 pending_official_lesson_list。

九下和九年级全一册不建点。

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
PENDING_UNIT = 90
CATALOG_STATUS = "pending_official_lesson_list"
OFFICIAL_CATALOG_STATUS = "official_toc"
CATALOG_NOTE = (
    "本点未能挂到该册官方阅读器目录中的具体课、框。"
    "章节为「N年级X册 待核」，不是已核实的课挂接。"
)
VOLUME_META = {
    (7, "上"): {
        "title": "（根据2022年版课程标准修订）义务教育教科书·道德与法治七年级上册",
        "isbn": "978-7-107-38238-3",
        "content_id": "11446212-4b7b-4094-afe3-bd5b4f2b3f0c",
    },
    (7, "下"): {
        "title": "（根据2022年版课程标准修订）义务教育教科书·道德与法治七年级下册",
        "isbn": "978-7-107-38239-0",
        "content_id": "4e1a2a9e-1e62-451f-a52e-ef99cb4e8bf2",
    },
    (8, "上"): {
        "title": "（根据2022年版课程标准修订）义务教育教科书·道德与法治八年级上册",
        "isbn": "978-7-107-39650-2",
        "content_id": "5a29b928-d6da-4131-a69e-4c54941f7651",
    },
    (8, "下"): {
        "title": "（根据2022年版课程标准修订）义务教育教科书·道德与法治八年级下册",
        "isbn": "978-7-107-40548-8",
        "content_id": "f1db2a19-2513-4626-8e6c-275cf549bdf2",
    },
    (9, "上"): {
        "title": "（根据2022年版课程标准修订）义务教育教科书·道德与法治九年级上册",
        "isbn": "978-7-107-41303-2",
        "content_id": "03d41525-a373-4286-92c3-3f2d7cbe3b79",
    },
}
G9A_CATALOG_STATUS = OFFICIAL_CATALOG_STATUS
G9A_CATALOG_NOTE = (
    "课名、框名和目录页码来自国家中小学智慧教育平台官方阅读器目录。"
    "书名为（根据2022年版课程标准修订）义务教育教科书·道德与法治九年级上册。"
    "ISBN 978-7-107-41303-2。"
    "contentId 03d41525-a373-4286-92c3-3f2d7cbe3b79。"
    "未逐字核对课文正文。"
    "课标仍是主题推断，verbatim 为 false。"
)


def volume_catalog_note(grade, sem):
    if grade == 9 and sem == "上":
        return G9A_CATALOG_NOTE
    meta = VOLUME_META[(grade, sem)]
    return (
        "课名、框名和目录印刷页码来自国家中小学智慧教育平台官方阅读器目录。"
        "书名为%s。"
        "ISBN %s。"
        "contentId %s。"
        "未逐字核对课文正文。"
        "课标仍是主题推断，verbatim 为 false。"
    ) % (meta["title"], meta["isbn"], meta["content_id"])


def pending_catalog_note(grade, sem):
    cn = "零一二三四五六七八九"[grade]
    return (
        "本点未能挂到该册官方阅读器目录中的具体课、框，章节为「%s年级%s册 待核」。"
        "catalog_status 为 pending_official_lesson_list，不是已核实的课挂接。"
    ) % (cn, sem)


def pending_chapter(grade, sem):
    cn = "零一二三四五六七八九"[grade]
    return "%s年级%s册 待核" % (cn, sem)

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
        if s != "上":
            raise SystemExit("九年级只允许上册；九下和九全不建点")
    elif g not in (7, 8) or s not in ("上", "下"):
        raise SystemExit("册次只允许七上、七下、八上、八下、九上")
    if n == PENDING_UNIT:
        if title != "待核":
            raise SystemExit("unit 90 的标题必须是「待核」")
        if g not in (7, 8) or s not in ("上", "下"):
            raise SystemExit("待核桶只允许七上、七下、八上、八下")
    UNITS[(g, s, n)] = title


def chapter(grade, sem, unit_n):
    if unit_n == PENDING_UNIT:
        return pending_chapter(grade, sem)
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


def K(tid, key, name, unit_n, typ, desc, criteria, qs, std, domain, lesson, frames, root_reason=None, frame_note="", note_only=""):
    """qs：4 道选择题 (题干, 正确答案, [三个干扰项], 解析)。难度 basic、basic、standard、challenge。

    note_only 只写入课标对齐说明，不进入 description。已确认点用它记官方目录印刷页码。
    unit 90 是该册待核桶，章节为「N年级X册 待核」，不要拼成「第90单元 待核」。
    """
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
    if unit_n == PENDING_UNIT:
        base_note = pending_catalog_note(g, s)
        status = CATALOG_STATUS
    elif g == 9 and s == "上":
        base_note = G9A_CATALOG_NOTE
        status = G9A_CATALOG_STATUS
    else:
        base_note = volume_catalog_note(g, s)
        status = OFFICIAL_CATALOG_STATUS
    note_parts = [base_note]
    if note_only:
        note_parts.append(note_only.strip())
    if frame_note:
        note_parts.append(frame_note.strip())
    note = " ".join(note_parts).strip()
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
        "catalog_status": status,
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
