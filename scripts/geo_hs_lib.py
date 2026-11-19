# -*- coding: utf-8 -*-
"""高中地理（人教版 2019，必修第一、二册，选择性必修 1–3）的登记实例。内容文件从这里取 C、N、T。"""
from senior_lib import Senior, C, N  # noqa: F401

DOMAINS = ("自然地理基础", "人文地理基础", "区域发展", "资源环境与国家安全")

S = Senior(
    subject="geography", label="地理", tag="geo", edition="人教版",
    id_prefix="cng_h", junior_prefix="cng_j", std_prefix="cgs-hs-2017:", std_key="geography_senior",
    std_meta={
        "title": "普通高中地理课程标准（2017年版2020年修订）",
        "issuer": "中华人民共和国教育部",
        "year": 2017,
        "stage": "高中必修与选择性必修",
        "note": "条目是对高中地理课标必修、选择性必修内容要求的公开转述，不是逐页核对的原文。verbatim 为 false，page_or_ref 为「待核」。编号 cgs-hs-2017 是本图谱编的，不是教育部原编号；B1、B2 对应必修第一、二册，S1、S2、S3 对应选择性必修第一、二、三册。章节依据人教版（2019）高中地理的公开目录，未逐页核对纸质课本。",
        "textbook": "人民教育出版社《地理》必修第一册、必修第二册，选择性必修1《自然地理基础》、选择性必修2《区域发展》、选择性必修3《资源、环境与国家安全》（2019年版）",
    },
    domains=DOMAINS,
    book_title={10: "必修第一册", 11: "必修第二册", 12: "选择性必修第一册", 13: "选择性必修第二册", 14: "选择性必修第三册"},
)
T = S.T
plan = S.plan
clause = S.clause
