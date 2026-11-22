# -*- coding: utf-8 -*-
"""初中化学数据的登记与题目生成。由 scripts/chem_build.py 调用。

教材是六三制人教版九年级上、下册（根据 2022 年版课程标准修订的 2024 审定本）。
五四制九年级化学全一册不采用。七、八年级不设化学点。
目录来源写在 README「初中化学」；没逐页核对纸质课本的，标非官方、待核。
课标是《义务教育化学课程标准（2022年版）》五个学习主题的公开转述，不是逐页核对的原文。
"""

import re

TOPICS = []
HARD = []

# 空气一课同时引用物质分类（混合物）。制取氧气同时引用基本反应类型（分解、催化剂）。
# 化石能源一课同时引用跨学科实践。领域仍按主课标。
EXTRA_STD = {
    "g9a_05": ["st_class"],
    "g9a_07": ["st_type"],
    "g9a_26": ["st_cross"],
}

# (年级, 学期, 单元号) -> (单元名, 占位领域, 默认课标符号)
UNITS = {
    (9, "上", 1): ("走进化学世界", "科学探究与化学实验", "st_nature"),
    (9, "上", 2): ("空气和氧气", "物质的性质与应用", "st_air"),
    (9, "上", 3): ("物质构成的奥秘", "物质的组成与结构", "st_particle"),
    (9, "上", 4): ("自然界的水", "物质的性质与应用", "st_water"),
    (9, "上", 5): ("化学反应的定量关系", "物质的化学变化", "st_mass"),
    (9, "上", 6): ("碳和碳的氧化物", "物质的性质与应用", "st_co2"),
    (9, "上", 7): ("能源的合理利用与开发", "化学与社会·跨学科实践", "st_resource"),
    (9, "下", 8): ("金属和金属材料", "物质的性质与应用", "st_metal"),
    (9, "下", 9): ("溶液", "物质的性质与应用", "st_water"),
    (9, "下", 10): ("常见的酸、碱、盐", "物质的性质与应用", "st_acid"),
    (9, "下", 11): ("化学与社会", "化学与社会·跨学科实践", "st_health"),
}

DOMAINS = (
    "科学探究与化学实验",
    "物质的性质与应用",
    "物质的组成与结构",
    "物质的化学变化",
    "化学与社会·跨学科实践",
)
CODE_OF = {
    "SQ": "科学探究与化学实验",
    "SP": "物质的性质与应用",
    "SC": "物质的组成与结构",
    "SR": "物质的化学变化",
    "SS": "化学与社会·跨学科实践",
}

# 课标条目是五个学习主题内容要求的公开转述。被公开材料截断的句子没有补写。
STANDARD_ROWS = [
    ("st_nature", "SQ", "化学科学本质",
     "知道化学是研究物质的组成、结构、性质、转化及应用的一门基础学科，其特征是从分子层次认识物质，通过化学变化创造物质；初步了解化学科学的发展历程，体会实验探究和模型建构是化学科学研究的基本方法；认识化学科学、技术、社会、环境的相互关系，了解化学科学对社会发展和人类文明进步的重要价值。"),
    ("st_inquiry", "SQ", "科学探究",
     "知道科学探究是收集证据和作出解释，进行发现、创造与应用的科学实践活动，也是获取科学知识、理解科学本质、认识客观世界的重要途径。了解科学探究过程包括提出问题、形成假设、设计并实施实验或调查方案、获取证据、分析解释数据、形成结论及建构模型、反思评价及表达交流等要素。经历科学探究的一般过程，认识从问题和假设出发确定探究目标、依据探究目标设计并实施实验方案、通过观察和实验等方法获取证据、基于证据进行分析推理及形成结论等对于科学探究的意义，体会合作与交流在科学探究中的重要作用。"),
    ("st_skill", "SQ", "基本实验技能",
     "知道化学实验是进行科学探究的重要方式，具备基本的化学实验技能是学习化学和进行探究活动的基础和保证。对于化学实验技能，应达到如下基本要求。（1）熟悉化学实验室安全警示标志，学会正确使用安全防护设施，学习妥善应对实验安全问题的必要措施。（2）学会试剂的取用、简单仪器的使用及连接、加热等实验基本操作。（3）初步学会在教师指导下根据实验需要选择实验试剂和仪器，并能安全操作。（4）初步学会配制一定溶质质量分数的溶液。（5）学会用酸碱指示剂、pH试纸检验溶液的酸碱性。（6）初步学会根据某些性质检验和区分一些常见的物质。（7）初步学习使用过滤、蒸发的方法对混合物进行分离。（8）初步学习运用简单的装置和方法制取某些气体。（9）初步学会观察实验现象，并如实记录、处理实验数据，撰写实验报告等技能。"),
    ("st_lab", "SQ", "学生必做实验",
     "（1）粗盐中难溶性杂质的去除。（2）氧气的实验室制取与性质。（3）二氧化碳的实验室制取与性质。（4）常见金属的物理性质和化学性质。（5）常见酸、碱的化学性质。（6）一定溶质质量分数的氯化钠溶液的配制。（7）水的组成及变化的探究。（8）燃烧条件的探究。（9）跨学科实践活动（原则上从学习主题5中选择，所用课时不少于本学科总课时的10%）。"),
    ("st_air", "SP", "空气与氧气",
     "知道空气的主要成分及用途，认识氧气的主要性质，了解实验室制取氧气的原理和检验方法。"),
    ("st_carbon", "SP", "碳单质",
     "知道金刚石、石墨等碳单质的物理性质差异很大，但它们都由碳元素组成。"),
    ("st_co2", "SP", "碳的氧化物",
     "知道二氧化碳的主要性质、用途和实验室制取方法，了解一氧化碳的可燃性、毒性和与某些金属氧化物的反应。"),
    ("st_water", "SP", "水和溶液",
     "知道水的组成和净化水的常用方法，认识溶液、溶解度，能用溶质的质量分数表示溶液组成。"),
    ("st_metal", "SP", "金属与金属矿物",
     "知道常见金属的物理性质和化学性质，了解金属活动性顺序、金属矿物的利用、锈蚀条件和防锈的常见方法。"),
    ("st_acid", "SP", "常见的酸、碱、盐",
     "认识常见酸、碱、盐的主要性质和用途，知道中和反应，会用酸碱指示剂和 pH 判断溶液的酸碱性。"),
    ("st_particle", "SC", "分子、原子与离子",
     "认识物质可以由分子、原子或离子构成。分子和原子都在不断运动；化学变化中分子可以分成原子，原子可以重新组合成新的分子。原子由原子核和核外电子构成。"),
    ("st_element", "SC", "元素",
     "元素是质子数（核电荷数）相同的一类原子的总称。能识记常见元素符号，并初步看懂元素周期表中的原子序数、元素符号和相对原子质量。"),
    ("st_formula", "SC", "物质组成的表示",
     "能用化学式表示常见物质的组成，知道常见元素的化合价，并能根据化学式计算相对分子质量和元素的质量比。"),
    ("st_class", "SC", "物质的分类",
     "能区分纯净物和混合物、单质和化合物，知道氧化物是由两种元素组成且其中一种是氧元素的化合物。"),
    ("st_change", "SR", "化学变化的特征",
     "化学变化有新物质生成。能区分物理变化和化学变化，也能区分物理性质和化学性质。"),
    ("st_mass", "SR", "质量守恒定律与化学方程式",
     "认识质量守恒定律，能从微观上用原子的种类、数目和质量不变来解释，并据此书写简单的化学方程式。"),
    ("st_calc", "SR", "根据化学方程式的计算",
     "能根据化学方程式，由一种纯净物的质量求出另一种物质的质量。参加计算的质量必须是实际参加反应的纯净物质量。"),
    ("st_type", "SR", "化学反应的基本类型",
     "认识化合反应、分解反应、置换反应和复分解反应，知道氧化反应，知道催化剂能改变化学反应速率，而本身的质量和化学性质在反应前后不变。"),
    ("st_burn", "SR", "燃烧与灭火",
     "知道燃烧需要可燃物、与氧气（或空气）接触，以及温度达到着火点。灭火就是去掉其中至少一个条件。"),
    ("st_resource", "SS", "资源、能源与环境",
     "知道爱护水资源、保护空气，了解化石能源的合理利用，以及节约能源、减少排放对可持续发展的意义。"),
    ("st_health", "SS", "化学与健康、材料",
     "知道人体所需的主要营养物质和一些常量元素、微量元素，了解合成材料，认识化学在健康、材料和可持续发展中的作用。"),
    ("st_cross", "SS", "跨学科实践",
     "（1）微型空气质量“检测站”的组装与使用。（2）基于特定需求设计和制作简易供氧器。（3）水质检测及自制净水器。（4）基于碳中和理念设计低碳行动方案。（5）垃圾的分类与回收利用。（6）探究土壤酸碱性对植物生长的影响。（7）海洋资源的综合利用与制盐。（8）制作模型并展示科学家探索物质组成与结构的历程。（9）调查家用燃料的变迁与合理使用。（10）调查我国航天科技领域中新型材料、新型能源的应用。注：跨学科实践活动原则上从以上10项中选择，所用课时不少于本学科总课时的10%。"),
]

STD_CODE = {row[0]: row[1] for row in STANDARD_ROWS}
TEXT_STATUS = (
    "公开转述 / 待核。核实方式：检索公开报道、课标目录对照和教材修订说明，未下载教育部 PDF 逐页核对。"
    "来源：中国教育新闻网 http://www.jyb.cn/rmtzcg/xwy/spxw/202208/t20220803_2110932643.html "
    "（五个学习主题的名称）；二级主题框架的公开对照 "
    "https://m.fx361.com/news/2022/0530/21987573.html 。"
    "内容要求的句子是转述，不是逐页核对的原文。学生必做实验的具体名单未逐条对照教育部文本。"
    "没有把未经核对的「2022年版2025年修订」摘录写成化学课标原文。"
)

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "科学探究与化学实验": ["能说出本课的探究步骤或实验操作要点", "能把现象和证据对应到教材中的结论"],
    "物质的性质与应用": ["能说出本课物质的主要性质或用途", "能用性质解释一个教材中的典型事实"],
    "物质的组成与结构": ["能用微粒、元素或化学式表示物质的组成", "能完成教材要求的简单判断或计算"],
    "物质的化学变化": ["能判断变化类型或写出相关的化学方程式", "能用质量守恒或反应规律解释一个典型事实"],
    "化学与社会·跨学科实践": ["能说出化学与资源、健康或材料的一个基本事实", "能判断一种常见做法是否符合节约资源和保护环境"],
}
NOTE = "人教版该课的常见教学内容。条目是公开转述，不是逐页核对的原文。"

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求|你认为|是否应该|谁之过|是否必要")
_BANNED_COPY = re.compile("免费|AI\\s*初稿")
_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?$")
_CUR = {}


def chapter(grade, sem, unit):
    cn = "零一二三四五六七八九"[grade]
    title = UNITS[(grade, sem, unit)][0]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit, title)


def hard(topic, prereq, reason):
    HARD.append((topic, prereq, reason))


def vol(grade, sem):
    _CUR["g"], _CUR["s"] = grade, sem


def K(key, name, unit, typ, desc, qs, std=None):
    """登记一个知识点。qs 恰好 4 题，难度依次 basic、basic、standard、challenge。"""
    g, s = _CUR["g"], _CUR["s"]
    if (g, s, unit) not in UNITS:
        raise SystemExit("%s 单元未登记：%s%s 第%d单元" % (key, g, s, unit))
    std = std or UNITS[(g, s, unit)][2]
    if std not in STD_CODE:
        raise SystemExit("%s 课标符号不存在：%s" % (key, std))
    domain = CODE_OF[STD_CODE[std]]
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
        "mastery_criteria": list(CRIT[domain]), "std": std, "conf": "inferred", "note": NOTE,
        "items": [tuple(q) for q in qs],
    })


def load_block(text):
    """解析 V/L/Q/N 行。Q 是选择题，N 是数值题。字段用 | 分开，题目文字里不要写 |。"""
    cur = None
    qs = []

    def flush():
        if cur is None:
            return
        key, name, unit, typ, std, desc = cur
        K(key, name, int(unit), typ, desc, qs, std=std)

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
            if len(parts) != 7:
                raise SystemExit("L 行字段数不对：%s" % line)
            cur = parts[1:]
            qs = []
        elif tag == "Q":
            if cur is None:
                raise SystemExit("Q 出现在 L 之前：%s" % line)
            if len(parts) != 7:
                raise SystemExit("Q 行字段数不对：%s" % line)
            _tag, prompt, answer, w1, w2, w3, expl = parts
            qs.append(("choice", prompt, answer, [w1, w2, w3], expl))
        elif tag == "N":
            if cur is None:
                raise SystemExit("N 出现在 L 之前：%s" % line)
            if len(parts) != 5:
                raise SystemExit("N 行字段数不对：%s" % line)
            _tag, prompt, answer, verify, expl = parts
            qs.append(("numeric", prompt, answer, verify, expl))
        else:
            raise SystemExit("无法识别的行：%s" % line[:40])
    flush()


def materialise_questions(spec):
    diffs = ["basic", "basic", "standard", "challenge"]
    made = []
    for diff, item in zip(diffs, spec["items"]):
        kind = item[0]
        if kind == "choice":
            _k, prompt, answer, wrongs, expl = item
            made.append({
                "d": diff, "t": "choice", "p": str(prompt).strip(), "a": str(answer).strip(),
                "w": [str(w).strip() for w in wrongs], "e": str(expl).strip(),
            })
        elif kind == "numeric":
            _k, prompt, answer, verify, expl = item
            made.append({
                "d": diff, "t": "numeric", "p": str(prompt).strip(), "a": str(answer).strip(),
                "v": str(verify).strip(), "e": str(expl).strip(),
            })
        else:
            raise SystemExit("%s 题型无法识别：%s" % (spec["key"], kind))
    return made


def check_question(key, q):
    if _BANNED_START.match(q["p"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["p"][:20]))
    blob = "\n".join([q["p"], q["e"], q["a"]] + q.get("w", []))
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语：%s" % (key, q["p"][:24]))
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    if not q["e"]:
        raise SystemExit("%s 缺少解析" % key)
    if q["t"] == "choice":
        if len(q["w"]) != 3:
            raise SystemExit("%s 干扰项必须是 3 个：%s" % (key, q["p"][:30]))
        opts = [q["a"]] + q["w"]
        if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
            raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    elif q["t"] == "numeric":
        if not _NUM_RE.match(q["a"].replace(" ", "")):
            raise SystemExit("%s 数值题答案不是数：%s" % (key, q["a"]))
        if not q.get("v"):
            raise SystemExit("%s 数值题缺少 verify" % key)
    else:
        raise SystemExit("%s 题型非法：%s" % (key, q["t"]))
