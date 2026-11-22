# -*- coding: utf-8 -*-
"""高中地理、生物、历史共用的登记库。各科的 xxx_hs_lib.py 用 Senior(...) 建一个实例，
内容文件调用实例的 plan / clause / T，编译由 senior_build.py 完成。

册次与 grade 沿用高中化学：必修一 = 10，必修二 = 11，选必一 = 12，选必二 = 13，选必三 = 14，semester 都是「上」。
题目规则与初中同科一致：每点 4 题，难度 basic、basic、standard、challenge；第 1 题必须是 basic 选择题。
"""
from __future__ import annotations

import json
import re

BOOK_WORD = {10: "必修一", 11: "必修二", 12: "选必一", 13: "选必二", 14: "选必三"}
BOOK_CODE = {10: "B1", 11: "B2", 12: "S1", 13: "S2", 14: "S3"}
CODE_GRADE = {v: k for k, v in BOOK_CODE.items()}
TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
DIFFS = ("basic", "basic", "standard", "challenge")
NOTE = "公开转述，本图谱自编号，未逐页核对教育部课标 PDF。"

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求|你认为|是否应该|谁之过|是否必要")
_BANNED_COPY = re.compile("免费|AI\\s*初稿")
_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?$")
# 章节：必修一 第一章 xxx 1.1 / 必修一 第一单元 xxx 第1课（章名、单元名里不能有空格）
CHAPTER_RE = re.compile(r"^(必修一|必修二|选必一|选必二|选必三) 第[一二三四五六七八九十\d]+(?:章|单元) \S+(?: \S+)?$")


def C(diff, prompt, right, wrongs, expl):
    return {
        "kind": "choice", "diff": diff, "prompt": str(prompt).strip(),
        "right": str(right).strip(), "wrongs": [str(w).strip() for w in wrongs],
        "expl": str(expl).strip(),
    }


def N(diff, prompt, answer, verify, expl):
    return {
        "kind": "numeric", "diff": diff, "prompt": str(prompt).strip(),
        "answer": str(answer).strip(), "verify": str(verify).strip(),
        "expl": str(expl).strip(),
    }


def choice_verify(text):
    return json.dumps(text, ensure_ascii=False)


def check_question(key, q):
    if _BANNED_START.match(q["prompt"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["prompt"][:20]))
    blob = "\n".join([q["prompt"], q["expl"], q.get("right", ""), q.get("answer", "")] + q.get("wrongs", []))
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语：%s" % (key, q["prompt"][:24]))
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    if not q["expl"]:
        raise SystemExit("%s 缺少解析" % key)
    if q["kind"] == "choice":
        if len(q["wrongs"]) != 3:
            raise SystemExit("%s 干扰项必须是 3 个：%s" % (key, q["prompt"][:30]))
        opts = [q["right"]] + q["wrongs"]
        if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
            raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    elif q["kind"] == "numeric":
        if not _NUM_RE.match(q["answer"].replace(" ", "")):
            raise SystemExit("%s 数值题答案不是数：%s" % (key, q["answer"]))
        if not q.get("verify"):
            raise SystemExit("%s 数值题缺少 verify" % key)
    else:
        raise SystemExit("%s 题型非法：%s" % (key, q.get("kind")))


class Senior:
    def __init__(self, *, subject, label, tag, edition, id_prefix, junior_prefix, std_prefix, std_key,
                 std_meta, domains, book_title, count_expect=None, book_words=None, chapter_re=None,
                 extra_prereq_prefixes=(), std_note=None, book_codes=None):
        self.subject = subject          # geography
        self.label = label              # 地理
        self.tag = tag                  # geo
        self.edition = edition          # 人教版 / 统编版
        self.id_prefix = id_prefix      # cng_h
        self.junior_prefix = junior_prefix  # cng_j
        self.std_prefix = std_prefix    # cgs-hs-2017:
        self.std_key = std_key          # geography_senior
        self.std_meta = std_meta
        self.domains = tuple(domains)   # 本科高中点允许的 domain（含与初中共用的名称）
        self.book_title = book_title    # {10: "必修第一册", ...}
        # 默认仍是化学式册名。地理、生物、历史、化学都不传，章节字符串保持原样。
        self.book_words = book_words or BOOK_WORD
        self.book_codes = dict(book_codes) if book_codes else dict(BOOK_CODE)
        self.code_grade = {v: k for k, v in self.book_codes.items()}
        self.chapter_re = chapter_re or CHAPTER_RE
        self.extra_prereq_prefixes = tuple(extra_prereq_prefixes)
        self.std_note = std_note or NOTE
        self.count_expect = count_expect or {}
        self.PLAN = []
        self.PLAN_BY_KEY = {}
        self.ORDER = {}
        self.HS = {}
        self.CLAUSES = []   # (tail, domain, section, text)
        self.CHECK = None   # 课标核对表 tail -> (page_or_ref, text_status)；未登记则 senior_build 沿用「待核」
        self.NOTE = self.std_note

    # ------------------------------------------------------------ 课序
    def plan(self, grade, rows):
        """rows: [(key, 显示名, 章节尾部, domain)]。章节尾部不含册名，如「第一章 宇宙中的地球 1.1」；domain 必须在本科允许范围内，T() 会核对。"""
        if grade not in self.book_words:
            raise SystemExit("grade 必须是已登记册次：%s" % grade)
        if self.PLAN and self.PLAN[-1]["grade"] > grade:
            raise SystemExit("课序必须按册从前往后登记：%s" % grade)
        for key, name, tail, domain in rows:
            if domain not in self.domains:
                raise SystemExit("%s 的 domain 不在允许范围里：%s" % (key, domain))
            if key in self.PLAN_BY_KEY:
                raise SystemExit("课序 key 重复：%s" % key)
            chapter = self.book_words[grade] + " " + tail
            if not self.chapter_re.match(chapter):
                raise SystemExit("%s 章节格式不对（名称内不要有空格）：%s" % (key, chapter))
            row = {"key": key, "name": name, "chapter": chapter, "grade": grade, "semester": "上", "domain": domain}
            self.ORDER[key] = len(self.PLAN)
            self.PLAN.append(row)
            self.PLAN_BY_KEY[key] = row

    # ------------------------------------------------------------ 课标转述
    def clause(self, tail, domain, section, text):
        """tail 形如 B1.01、S2.03；册内编号必须连续。允许的册代码来自本实例的 book_codes。"""
        codes = sorted(set(self.book_codes.values()), key=lambda c: (c[0] != "B", c))
        m = re.match(r"^(%s)\.(\d{2})$" % "|".join(codes), tail)
        if not m:
            raise SystemExit("课标尾部格式应为 B1.01：%s" % tail)
        if domain not in self.domains:
            raise SystemExit("课标 %s 的领域不在允许范围内：%s" % (tail, domain))
        if any(c[0] == tail for c in self.CLAUSES):
            raise SystemExit("课标重复：%s" % tail)
        same = [c for c in self.CLAUSES if c[0].startswith(m.group(1) + ".")]
        if int(m.group(2)) != len(same) + 1:
            raise SystemExit("课标编号在册内不连续：%s" % tail)
        if not str(text).strip() or not str(section).strip():
            raise SystemExit("课标 %s 缺少 section 或 text" % tail)
        self.CLAUSES.append((tail, domain, str(section).strip(), str(text).strip()))

    # ------------------------------------------------------------ 知识点
    def T(self, key, domain, typ, desc, mastery, std, pre, qs):
        """pre: [(ref, reason)] 或 [(ref, reason, "soft")]。ref 是本科高中 key，或 "J:cng_j012" 这样的初中知识点 id。"""
        if key not in self.PLAN_BY_KEY:
            raise SystemExit("%s_hs_plan.py 里没有这个 key：%s" % (self.tag, key))
        if key in self.HS:
            raise SystemExit("重复登记：%s" % key)
        if domain not in self.domains:
            raise SystemExit("%s 领域不在允许范围里：%s（允许：%s）" % (key, domain, "、".join(self.domains)))
        if domain != self.PLAN_BY_KEY[key]["domain"]:
            raise SystemExit("%s 的 domain 与课序里登记的不一致：%s ≠ %s" % (key, domain, self.PLAN_BY_KEY[key]["domain"]))
        if typ not in TYPES:
            raise SystemExit("%s type 非法：%s" % (key, typ))
        if not (2 <= len(mastery) <= 3) or not all(str(x).strip() for x in mastery):
            raise SystemExit("%s mastery 必须是 2–3 条" % key)
        if not str(desc).strip():
            raise SystemExit("%s 缺少讲解 description" % key)
        if len(qs) != 4:
            raise SystemExit("%s 需要恰好 4 题" % key)
        for q, diff in zip(qs, DIFFS):
            if q["diff"] != diff:
                raise SystemExit("%s 难度顺序必须是 basic、basic、standard、challenge" % key)
            check_question(key, q)
        if qs[0]["kind"] != "choice":
            raise SystemExit("%s 第 1 题必须是选择题" % key)
        if not std or len(std) > 3:
            raise SystemExit("%s 课标引用必须是 1–3 条" % key)
        edges = []
        for p in pre:
            if len(p) == 2:
                ref, reason, strength = p[0], p[1], "hard"
            else:
                ref, reason, strength = p
            if strength not in ("hard", "soft"):
                raise SystemExit("%s 先修强度非法：%s" % (key, strength))
            edges.append((ref, reason, strength))
        self.HS[key] = {
            "key": key, "domain": domain, "type": typ, "description": str(desc).strip(),
            "mastery": [str(x).strip() for x in mastery], "std": list(std),
            "pre": edges, "qs": list(qs),
        }
        return self.HS[key]
