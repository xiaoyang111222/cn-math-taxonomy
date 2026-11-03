# -*- coding: utf-8 -*-
"""初中生物数据的登记与题目生成。由 scripts/bio_build.py 调用。

目录依据（公开目录，非人教社官网逐页核对，非官方、待核）：
- 七上：教师之家人教版(2024) https://www.renjiaoshe.com/jiaocai/3467.html ，
  并对照 dzskb https://www.dzskb.com/rjbsw7sc.html 。章名采用教师之家
  「藻类与植物的类群 / 藻类、苔藓植物和蕨类植物」；dzskb 写成
  「植物的类群 / 藻类、苔藓和蕨类」，用词不一致，待核纸质课本。
- 七下：教师之家 https://www.renjiaoshe.com/jiaocai/3468.html 与
  dzskb https://www.dzskb.com/rjbsw7xc.html 一致。第五章无分节，整章一个点。
- 八上：教师之家 https://www.renjiaoshe.com/jiaocai/3469.html 与
  dzskb https://www.dzskb.com/rjbsw8sc-2024.html 一致。
- 八下：dzskb https://www.dzskb.com/rjbsw8xc-2024.html （标 2024 审定）。
  教师之家未检索到 2024 八下独立目录页。21cnjy 2026 春目录预览与之同结构。
使用学期按地理类推，版权页印次未核：七上 2024 秋，七下 2025 春，八上 2025 秋，八下 2026 春。
六三制初中生物只开七、八年级，九年级没有生物课。综合实践项目不单建点。
课标是《义务教育生物学课程标准（2022年版）》第四学段的公开转述，不是逐页核对的原文。
"""

import re

TOPICS = []
HARD = []

# 真菌一课额外引用「生物学与社会·跨学科实践」（发酵食品制作）。领域仍按主课标。
EXTRA_STD = {"g7a_19": ["st_cross"]}

# (年级, 学期, 单元号) -> (单元名, 占位领域, 默认课标符号)
# 知识点的领域以课标代码为准，不按单元名硬套。
UNITS = {
    (7, "上", 1): ("生物和细胞", "生物体的结构层次", "st_observe"),
    (7, "上", 2): ("多种多样的生物", "生物的多样性", "st_plant"),
    (7, "下", 3): ("植物的生活", "植物的生活", "st_life"),
    (7, "下", 4): ("人体生理与健康（一）", "人体生理与健康", "st_human"),
    (8, "上", 4): ("人体生理与健康（二）", "人体生理与健康", "st_human"),
    (8, "上", 5): ("生物与环境", "生物与环境", "st_eco"),
    (8, "下", 6): ("生命的延续和发展", "遗传与进化", "st_repro"),
}

DOMAINS = (
    "生物体的结构层次",
    "生物的多样性",
    "生物与环境",
    "植物的生活",
    "人体生理与健康",
    "遗传与进化",
    "生物学与社会·跨学科实践",
)
CODE_OF = {
    "BS": "生物体的结构层次",
    "BD": "生物的多样性",
    "BE": "生物与环境",
    "BP": "植物的生活",
    "BH": "人体生理与健康",
    "BG": "遗传与进化",
    "BX": "生物学与社会·跨学科实践",
}

# 课标条目是第四学段内容要求的公开转述。被公开摘录截断的句子没有补写。
# 概念 9 的原句未核到，不写入。
STANDARD_ROWS = [
    ("st_observe", "BS", "认识生物",
     "通过观察周边环境中的生物，说出生物的基本特征，并初步学会使用观察工具认识生物。"),
    ("st_cell", "BS", "细胞",
     "细胞是生物体结构和功能的基本单位。一些生物由单细胞构成，一些由多细胞组成。动物细胞和植物细胞都有细胞膜、细胞质和细胞核；植物细胞还有细胞壁、叶绿体等结构。各结构功能不同，共同完成生命活动。细胞核是遗传信息库。"),
    ("st_level", "BS", "结构层次",
     "生物体具有一定的结构层次，能够完成各项生命活动。细胞通过分裂和分化形成不同组织；生物体的各部分在结构上相互联系、在功能上相互配合。"),
    ("st_plant", "BD", "植物类群",
     "根据形态结构、生理功能和繁殖方式等特点，可以把植物分成不同类群。藻类是能进行光合作用、结构比较简单的生物。"),
    ("st_animal", "BD", "动物类群",
     "根据形态结构、生理功能和繁殖方式等特点，可以把动物分成不同类群，并比较常见动物类群的主要特征。"),
    ("st_micro", "BD", "微生物",
     "认识细菌、真菌和病毒等微生物的主要特点，以及它们与人类生活的关系。"),
    ("st_class", "BD", "生物分类",
     "生物分类以特征为依据。分类单位从大到小依次是界、门、纲、目、科、属、种，「种」是最基本的分类单位。"),
    ("st_biodiv", "BD", "生物多样性及其保护",
     "生物可以分为不同的类群，保护生物多样性具有重要意义。认识生物多样性的层次，以及保护生物、与自然和谐共生的基本要求。"),
    ("st_eco", "BE", "生态系统",
     "生物与环境相互依赖、相互影响，形成多种多样的生态系统。生物与非生物环境相互作用，实现物质循环和能量流动。水、温度、空气、光等是生物生存的环境条件。"),
    ("st_safe", "BE", "生态安全",
     "分析人类活动对生态环境的影响，知道维护生态安全的基本要求。"),
    ("st_life", "BP", "植物的生命周期",
     "植物有自己的生命周期，可以制造有机物，直接或间接地为其他生物提供食物，参与生物圈中的水循环，并维持碳氧平衡。"),
    ("st_photo", "BP", "物质与能量",
     "植物通过光合作用制造有机物并释放氧气，通过呼吸作用分解有机物并释放能量；蒸腾作用使植物散失水分，并参与生物圈的水循环。光合作用条款中被公开摘录截断的句子没有补写。"),
    ("st_human", "BH", "人体的结构与功能",
     "人体的结构与功能相适应，各系统协调统一，共同完成复杂的生命活动。认识生殖、营养、呼吸、物质运输和废物排出等过程的基本事实。"),
    ("st_health", "BH", "健康地生活",
     "人体健康受传染病、心血管疾病、癌症及外部伤害的威胁，良好的生活习惯和医疗措施是健康的重要保障。知道传染病的预防、免疫、安全用药与急救的基本要求。"),
    ("st_repro", "BG", "生物的生殖",
     "生物通过无性生殖和有性生殖产生后代。有性生殖要经过两性生殖细胞的结合。"),
    ("st_gene", "BG", "遗传与变异",
     "遗传信息控制生物性状，并由亲代传递给子代。知道基因、显性和隐性、人的性别决定以及变异的基本事实。"),
    ("st_evol", "BG", "生物进化",
     "地球上现存的生物来自共同祖先，是长期进化的结果。知道生命起源、进化历程和自然选择的基本观点。"),
    ("st_cross", "BX", "跨学科实践",
     "生物学与社会·跨学科实践贯穿其他学习主题，大约占课时的十分之一。常见活动包括模型制作、植物栽培和动物饲养、发酵食品制作，解决真实问题时需要综合运用科学、技术、工程和数学。此条据公开解读转述；概念9的原句未核到，没有写入。"),
]

STD_CODE = {row[0]: row[1] for row in STANDARD_ROWS}
TEXT_STATUS = (
    "公开转述 / 待核。核实方式：检索公开报道与课标摘录，未下载教育部 PDF 逐页核对。"
    "来源：中国教育新闻网 http://www.jyb.cn/rmtzcg/xwy/spxw/202208/t20220817_2110935589.html "
    "（七个学习主题）；大概念摘录 https://m.fx361.com/news/2022/0530/22064858.html 。"
    "概念9原句未核到，不写入。网上可见标为「2022年版2025年修订」的摘录页，本条目不把它当成已逐页核对的原文。"
)

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "生物体的结构层次": ["能说出本课的基本结构和生命活动", "能把结构与功能对应到教材中的典型事实"],
    "生物的多样性": ["能说出本课类群或分类的主要特征", "能把类群特征对应到教材中的典型生物"],
    "生物与环境": ["能说出生物与环境、生态系统的基本关系", "能判断食物链、能量流动或生态问题的典型事实"],
    "植物的生活": ["能说出植物生活中的结构和生理过程", "能把实验现象对应到教材中的结论"],
    "人体生理与健康": ["能说出本课涉及的结构、生理过程或健康常识", "能把结构与功能对应到教材中的典型事实"],
    "遗传与进化": ["能说出生殖、遗传或进化的基本事实", "能用教材中的概念解释一个典型例子"],
    "生物学与社会·跨学科实践": ["能说出跨学科实践要解决的真实问题", "能把生物学知识与其他学科方法联系起来"],
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


def K(key, name, unit, typ, desc, qs, std=None):
    """登记一个知识点。qs 是 4 道选择题：(题干, 正确答案, [三个干扰项], 解析)，难度依次 basic、basic、standard、challenge。"""
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
    """解析 V/L/Q 行。L 带课标符号。字段用 | 分开，题目文字里不要写 |。"""
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
