# -*- coding: utf-8 -*-
"""初中地理数据的登记与题目生成。由 scripts/geo_build.py 调用。

目录依据（公开目录，dzskb / 教师之家，未逐页核对纸质课本）：
- 七上：2024 秋修订人教《地理》七年级上册。
- 七下：2024 审定人教《地理》七年级下册（2025 春使用）。
- 八上：2024 审定人教《地理》八年级上册（2025 秋使用）。
- 八下：2024 审定人教《地理》八年级下册（2026 春使用）。
六三制初中地理只开七、八年级，九年级没有地理课。
"""

import re

TOPICS = []
HARD = []

# (年级, 学期, 章号) -> (章名, 领域, 默认课标符号)
UNITS = {
    (7, "上", 1): ("地球", "地球与地图", "em_earth"),
    (7, "上", 2): ("地图", "地球与地图", "em_map"),
    (7, "上", 3): ("陆地和海洋", "地球与地图", "em_land"),
    (7, "上", 4): ("天气与气候", "世界地理", "wg_climate"),
    (7, "上", 5): ("居民与文化", "世界地理", "wg_people"),
    (7, "上", 6): ("发展与合作", "世界地理", "wg_dev"),
    (7, "下", 7): ("我们生活的大洲——亚洲", "世界地理", "wg_asia"),
    (7, "下", 8): ("我们邻近的地区和国家", "世界地理", "wg_near"),
    (7, "下", 9): ("东半球其他的地区和国家", "世界地理", "wg_east"),
    (7, "下", 10): ("西半球的国家", "世界地理", "wg_west"),
    (7, "下", 11): ("极地地区", "世界地理", "wg_polar"),
    (8, "上", 1): ("从世界看中国", "中国地理", "cg_land"),
    (8, "上", 2): ("中国的自然环境", "中国地理", "cg_nature"),
    (8, "上", 3): ("中国的自然资源", "中国地理", "cg_res"),
    (8, "上", 4): ("中国的经济发展", "中国地理", "cg_econ"),
    (8, "上", 5): ("建设美丽中国", "中国地理", "cg_beauty"),
    (8, "下", 6): ("中国的地理差异", "中国地理", "cg_diff"),
    (8, "下", 7): ("北方地区", "中国地理", "cg_north"),
    (8, "下", 8): ("南方地区", "中国地理", "cg_south"),
    (8, "下", 9): ("西北地区", "中国地理", "cg_nw"),
    (8, "下", 10): ("青藏地区", "中国地理", "cg_qing"),
    (8, "下", 11): ("奋进中的中国", "中国地理", "cg_world"),
}

DOMAINS = ("地球与地图", "世界地理", "中国地理")
CODE_OF = {
    "EM": "地球与地图", "WG": "世界地理", "CG": "中国地理",
}

# 课标条目是《义务教育地理课程标准（2022年版）》第四学段内容要求的公开转述，不是逐页核对的原文。
STANDARD_ROWS = [
    ("em_earth", "EM", "地球", "结合科学故事、史实材料等，说出人类对地球形状的认识过程，使用数据、类比等方式描述地球的大小。运用图片、影视资料以及数字技术等手段，描述地球的宇宙环境、地球在太阳系中的位置，认识地球是人类唯一的家园。运用地球仪或软件，演示地球的自转运动，说出地球的自转方向、周期。结合实例，说出地球自转产生的主要自然现象及其对人们生产生活的影响。运用模型或软件，演示地球的公转运动，说出地球的公转方向、周期。结合实例，说出地球公转产生的主要自然现象及其对人们生产生活的影响。在地球仪上识别经线和纬线，说出经度和纬度的分布规律；用经纬度描述某一地理事物或现象所在地的位置。"),
    ("em_map", "EM", "地图", "会读普通地图和地形图，选用合适的地图获取地理信息。"),
    ("em_land", "EM", "陆地和海洋", "阅读世界地图，描述世界海陆分布状况，说出七大洲、四大洋的分布。在世界地形图上指出陆地主要地形和海底主要地形的分布，观察地形分布大势。结合实例，说明海洋和陆地处于不断的运动变化之中；说出板块构造学说的基本观点，并解释世界火山、地震带的分布与板块运动的关系。"),
    ("wg_climate", "WG", "天气与气候", "阅读世界年平均气温和1月、7月平均气温分布图，描述和简要归纳世界气温分布特点。阅读世界年降水量分布图，描述和简要归纳世界降水分布特点。阅读某地区气温、降水数据资料，并据此绘制气温曲线图和降水量柱状图，说出气温与降水量随时间变化的特点。阅读世界气候类型分布图，描述世界主要气候类型的分布特征；结合实例，说明纬度位置、海陆分布、地形等对气候的影响。"),
    ("wg_people", "WG", "居民与文化", "运用地图和相关资料，描述并简要归纳世界人口数量变化和人口空间分布特点。通过阅读图像、观看视频或实地考察等，描述城镇与乡村的景观特征及其变化。运用反映人种、语言、宗教、习俗等内容的图文资料，描述世界文化的丰富多彩，树立尊重世界文化多样性的意识。"),
    ("wg_dev", "WG", "发展与合作", "以某发达国家和某发展中国家为例，描述不同国家发展水平的差异。结合实例，说明加强国际合作的重要意义。"),
    ("wg_asia", "WG", "亚洲", "运用地图和资料，说出亚洲的位置、自然环境特点和人文地理概况。"),
    ("wg_near", "WG", "邻近的地区和国家", "认识日本、东南亚、印度和俄罗斯的位置、自然环境和经济发展特点。"),
    ("wg_east", "WG", "东半球其他地区和国家", "认识西亚、欧洲西部、撒哈拉以南非洲和澳大利亚的地理位置与区域特征。"),
    ("wg_west", "WG", "西半球的国家", "认识美国和巴西的位置、自然环境和经济发展特点。"),
    ("wg_polar", "WG", "极地地区", "根据南极、北极地区自然地理环境的特殊性，说明开展极地科学考察和保护极地环境的重要性。"),
    ("cg_land", "CG", "疆域人口民族", "运用地图，描述中国的地理位置与疆域特征，说明南海诸岛是中国领土的组成部分，钓鱼岛及其附属岛屿是中国固有领土，增强国家版图意识与海洋权益意识。运用中国行政区划图，识别34个省级行政区，记住它们的简称和行政中心。运用地图和相关资料，描述中国人口的基本状况和变化。运用地图和相关资料，简要归纳中国的民族分布特点，树立中华民族共同体意识。"),
    ("cg_nature", "CG", "中国的自然环境", "运用地图和相关资料，简要归纳中国地形、气候、河湖等的特征；简要分析影响中国气候的主要因素。"),
    ("cg_res", "CG", "中国的自然资源", "运用地图和相关资料，描述中国水资源、土地资源、矿产资源和海洋资源等自然资源的主要特征，举例说明自然资源与人们生产生活的关系，认识开发、利用、保护自然资源的重要意义。"),
    ("cg_econ", "CG", "中国的经济发展", "借助地图和相关资料，举例描述中国农业、工业等生产活动的分布，并用实例说明科学技术在产业发展中的重要作用。运用地图和相关资料，说明中国交通运输线的分布特征，以及高速公路、高速铁路的快速发展对人们生产生活的影响。"),
    ("cg_beauty", "CG", "建设美丽中国", "运用地图和相关资料，描述中国主要的自然灾害和环境问题；针对某一自然灾害或环境问题提出合理的防治建议；掌握一定的气象灾害和地质灾害的安全防护技能。"),
    ("cg_diff", "CG", "中国的地理差异", "运用地图、图像等资料，说明秦岭—淮河等重要自然地理界线在地理分区中的意义。结合实例，描述不同区域的差异，说明区域联系和协同发展对经济社会发展的意义。"),
    ("cg_north", "CG", "北方地区", "认识北方地区的自然特征与农业，以及东北三省、黄土高原和北京的区域特点。"),
    ("cg_south", "CG", "南方地区", "认识南方地区的自然特征与农业，以及长江三角洲、香港澳门和台湾的区域特点。"),
    ("cg_nw", "CG", "西北地区", "认识西北地区的自然特征与农业，以及塔里木盆地的区域特点。"),
    ("cg_qing", "CG", "青藏地区", "认识青藏地区的自然特征与农业，以及三江源地区的生态意义。"),
    ("cg_world", "CG", "奋进中的中国", "知道中国发展成就、面临的挑战，以及在世界上的责任与作用。"),
]

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "地球与地图": ["能说出本课的基本概念、数据和空间位置", "能在地图或示意图上作出与教材相符的判断"],
    "世界地理": ["能说出本课的位置、自然或人文特征", "能把区域特征对应到教材中的典型事实"],
    "中国地理": ["能说出本课的位置、分布或基本国情", "能把自然或人文特征对应到教材中的典型事实"],
}
NOTE = "人教版该课的常见教学内容。条目是公开转述，不是逐页核对的原文。"

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求|你认为|是否应该|谁之过|是否必要")
_BANNED_COPY = re.compile("免费|AI\\s*初稿")
_CUR = {}


def chapter(grade, sem, unit):
    cn = "零一二三四五六七八九"[grade]
    title = UNITS[(grade, sem, unit)][0]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit, title)


def hard(topic, prereq, reason):
    HARD.append((topic, prereq, reason))


def vol(grade, sem):
    _CUR["g"], _CUR["s"] = grade, sem


def K(key, name, unit, typ, desc, qs, std=None, domain=None):
    """登记一个知识点。qs 是 4 道选择题：(题干, 正确答案, [三个干扰项], 解析)，难度依次 basic、basic、standard、challenge。"""
    g, s = _CUR["g"], _CUR["s"]
    if (g, s, unit) not in UNITS:
        raise SystemExit("%s 单元未登记：%s%s 第%d单元" % (key, g, s, unit))
    _u, udom, ustd = UNITS[(g, s, unit)]
    domain = domain or udom
    if domain not in DOMAINS:
        raise SystemExit("%s 领域无法识别：%s" % (key, domain))
    if typ not in TYPES:
        raise SystemExit("%s type 非法：%s" % (key, typ))
    if len(qs) != 4:
        raise SystemExit("%s 需要恰好 4 题" % key)
    if any(t["key"] == key for t in TOPICS):
        raise SystemExit("知识点 key 重复：%s" % key)
    TOPICS.append({
        "key": key, "name": name, "domain": domain, "grade": g, "semester": s,
        "unit": unit, "type": typ, "description": desc,
        "mastery_criteria": list(CRIT[domain]), "std": std or ustd, "conf": "inferred", "note": NOTE,
        "items": [tuple(q) for q in qs],
    })


def load_block(text):
    """解析 V/L/Q 行。字段用 | 分开，题目文字里不要写 |。"""
    cur = None
    qs = []

    def flush():
        if cur is None:
            return
        key, name, unit, typ, desc = cur
        K(key, name, int(unit), typ, desc, qs)

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        tag = parts[0]
        if tag == "V":
            flush()
            cur, qs = None, []
            if len(parts) != 3:
                raise SystemExit("V 行格式应为 V|年级|学期：%s" % line)
            vol(int(parts[1]), parts[2])
        elif tag == "L":
            flush()
            if len(parts) != 6:
                raise SystemExit("L 行字段数不对：%s" % line)
            cur = parts[1:]
            qs = []
        elif tag == "Q":
            if cur is None:
                raise SystemExit("Q 出现在 L 之前：%s" % line)
            if len(parts) != 7:
                raise SystemExit("Q 行字段数不对：%s" % line)
            _tag, prompt, answer, w1, w2, w3, expl = parts
            qs.append((prompt, answer, [w1, w2, w3], expl))
        else:
            raise SystemExit("无法识别的行：%s" % line[:40])
    flush()


def materialise_questions(spec):
    diffs = ["basic", "basic", "standard", "challenge"]
    made = []
    for diff, item in zip(diffs, spec["items"]):
        prompt, answer, wrongs, expl = item
        if len(wrongs) != 3:
            raise SystemExit("%s 干扰项必须是 3 个：%s" % (spec["key"], prompt[:30]))
        made.append({"d": diff, "t": "choice", "p": str(prompt).strip(), "a": str(answer).strip(),
                     "w": [str(w).strip() for w in wrongs], "e": str(expl).strip()})
    return made


def check_question(key, q):
    if _BANNED_START.match(q["p"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["p"][:20]))
    blob = "\n".join([q["p"], q["e"], q["a"]] + q["w"])
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语：%s" % (key, q["p"][:24]))
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    opts = [q["a"]] + q["w"]
    if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
        raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    if not q["e"]:
        raise SystemExit("%s 缺少解析" % key)
