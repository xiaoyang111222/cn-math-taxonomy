# -*- coding: utf-8 -*-
"""小学科学数据的登记与题目生成。由 scripts/sci_build.py 调用。

目录依据（逐课核对过公开目录）：
- 一上 2024 秋、一下 2025 春、二上 2025 秋、二下 2026 春、三上 2025 秋、三下 2026 春、
  四上 2026 秋、五上 2026 秋、六上 2026 秋：教科版 2024 年起修订的新教材。
- 四下、五下、六下：修订版尚未发行，按教科版现行（2017 年起使用、2020 前后修订）目录编排。
"""

import re

TOPICS = []
HARD = []
# SOFT 只登记 (topic, prereq, reason)，供编译脚本从官方课序软边链中拆出；本文件不生成边。
SOFT = []
MATH = []   # (key, cnm_id, reason)

# (年级, 学期, 单元) -> (单元名, 领域, 默认课标符号)
UNITS = {
    (1, "上", 1): ("周围的植物", "生命科学", "sm1_sys"),
    (1, "上", 2): ("我们自己", "生命科学", "sm1_body"),
    (1, "下", 1): ("身边的物体", "物质科学", "wz1_mat"),
    (1, "下", 2): ("常见的动物", "生命科学", "sm1_env"),
    (2, "上", 1): ("造房子", "技术与工程", "jg1_eng"),
    (2, "上", 2): ("地球家园", "地球与宇宙科学", "dq1_sys"),
    (2, "下", 1): ("探秘恐龙", "生命科学", "sm1_evo"),
    (2, "下", 2): ("玩磁铁", "物质科学", "wz1_force"),
    (3, "上", 1): ("天气", "地球与宇宙科学", "dq2_sys"),
    (3, "上", 2): ("水", "物质科学", "wz2_chg"),
    (3, "上", 3): ("物体的运动", "物质科学", "wz2_mot"),
    (3, "下", 1): ("辨别方向", "物质科学", "wz2_mot"),
    (3, "下", 2): ("动物的一生", "生命科学", "sm2_cyc"),
    (3, "下", 3): ("只有一个地球", "地球与宇宙科学", "dq2_space"),
    (4, "上", 1): ("空气", "物质科学", "wz2_mat"),
    (4, "上", 2): ("呼吸与消化", "生命科学", "sm2_body"),
    (4, "上", 3): ("声音", "物质科学", "wz2_en"),
    (4, "下", 1): ("植物的生长变化", "生命科学", "sm2_cyc"),
    (4, "下", 2): ("电路", "物质科学", "wz2_en"),
    (4, "下", 3): ("岩石与土壤", "地球与宇宙科学", "dq2_sys"),
    (5, "上", 1): ("微小世界", "生命科学", "sm3_cell"),
    (5, "上", 2): ("工具与技术", "技术与工程", "jg3_tech"),
    (5, "上", 3): ("运动和力", "物质科学", "wz3_force"),
    (5, "上", 4): ("地球表面的变化", "地球与宇宙科学", "dq3_sys"),
    (5, "下", 1): ("生物与环境", "生命科学", "sm3_env"),
    (5, "下", 2): ("船的研究", "技术与工程", "jg3_eng"),
    (5, "下", 3): ("环境与我们", "地球与宇宙科学", "dq3_human"),
    (5, "下", 4): ("热", "物质科学", "wz3_en"),
    (6, "上", 1): ("健康生活", "生命科学", "sm3_body"),
    (6, "上", 2): ("光", "物质科学", "wz3_en"),
    (6, "上", 3): ("地球的运动", "地球与宇宙科学", "dq3_space"),
    (6, "上", 4): ("计量时间", "技术与工程", "jg3_tech"),
    (6, "下", 1): ("小小工程师", "技术与工程", "jg3_eng"),
    (6, "下", 2): ("生物的多样性", "生命科学", "sm3_evo"),
    (6, "下", 3): ("宇宙", "地球与宇宙科学", "dq3_space"),
    (6, "下", 4): ("物质的变化", "物质科学", "wz3_chg"),
}

DOMAINS = ("物质科学", "生命科学", "地球与宇宙科学", "技术与工程")
CODE_OF = {"WZ": "物质科学", "SM": "生命科学", "DQ": "地球与宇宙科学", "JG": "技术与工程"}

# 课标条目是《义务教育科学课程标准（2022年版）》学段要求的公开转述，不是逐页核对的原文。
# 学段 1 对应一、二年级，2 对应三、四年级，3 对应五、六年级。(符号, 学段, 代码, 核心概念, 转述)
STANDARD_ROWS = [
    ("wz1_mat", "1", "WZ", "物质的结构与性质", "能观察、描述常见物体的颜色、形状、轻重等外部特征，并按特征给物体分类；知道水是无色、透明、会流动的液体。"),
    ("wz1_force", "1", "WZ", "物质的运动与相互作用", "知道磁铁能吸引铁一类的物体，磁铁有两个磁极，同极相斥、异极相吸。"),
    ("sm1_sys", "1", "SM", "生命系统的构成层次", "能识别周围常见的植物，说出植物的根、茎、叶等外部特征，知道植物需要水和阳光。"),
    ("sm1_body", "1", "SM", "生物体的稳态与调节", "能说出人体的主要外部器官，知道眼、耳、鼻、舌、皮肤等感官能帮助我们认识周围世界，并注意保护感官。"),
    ("sm1_env", "1", "SM", "生物与环境的相互关系", "能观察、描述常见动物的外部特征和生活环境，知道动物需要食物和水，能简单分类。"),
    ("sm1_evo", "1", "SM", "生命的延续与进化", "知道恐龙等古生物曾在地球上生活，能借助化石等证据了解它们的特征。"),
    ("dq1_sys", "1", "DQ", "宇宙中的地球与地球系统", "知道地球上有水、空气、土壤、岩石和生物，能描述天气和季节的变化，观察太阳和月亮的位置变化。"),
    ("jg1_eng", "1", "JG", "工程设计与物化", "能用简单材料按设计制作简单作品，展示并说出改进想法。"),
    ("wz2_mat", "2", "WZ", "物质的结构与性质", "知道空气是无色、无味、透明的气体，占据空间、有质量，受热会膨胀。"),
    ("wz2_chg", "2", "WZ", "物质的变化与化学反应", "知道水有固态、液态、气态三种形态，温度变化会引起蒸发、凝结、沸腾、结冰和熔化；知道有些物质能溶解在水中。"),
    ("wz2_mot", "2", "WZ", "物质的运动与相互作用", "能用参照物描述物体的位置和运动，比较运动的快慢；知道磁铁能指示南北方向。"),
    ("wz2_en", "2", "WZ", "能的转化与能量守恒", "知道声音由物体振动产生，有强弱和高低；能连接简单电路，区分导体和绝缘体，注意用电安全。"),
    ("sm2_body", "2", "SM", "生物体的稳态与调节", "能说出人体呼吸、消化器官的名称和作用，养成保护器官的习惯。"),
    ("sm2_cyc", "2", "SM", "生命的延续与进化", "能描述动物和植物从出生（发芽）到死亡的生命周期，知道生物能繁殖后代。"),
    ("dq2_sys", "2", "DQ", "宇宙中的地球与地球系统", "能用工具测量气温、降水量和风，描述天气；知道岩石和土壤的组成和作用。"),
    ("dq2_space", "2", "DQ", "宇宙中的地球与地球系统", "知道地球是一个球体，表面大部分是海洋；知道太阳和月球的基本特征，观察一天中影子的变化。"),
    ("wz3_force", "3", "WZ", "物质的运动与相互作用", "知道力能改变物体的运动状态，认识重力、弹力和摩擦力，会用测力计测量力的大小。"),
    ("wz3_en", "3", "WZ", "能的转化与能量守恒", "知道热会从温度高的物体传到温度低的物体，比较不同材料的导热性；知道光沿直线传播，能被反射。"),
    ("wz3_chg", "3", "WZ", "物质的变化与化学反应", "能区分物理变化和化学变化，知道化学变化会产生新物质，常伴随发光、发热、产生气体等现象。"),
    ("sm3_cell", "3", "SM", "生命系统的构成层次", "会使用放大镜和显微镜，知道生物由细胞构成，了解微生物与人类的关系。"),
    ("sm3_body", "3", "SM", "生物体的稳态与调节", "知道均衡营养、充足睡眠和调节情绪对健康的作用，了解脑和神经的作用。"),
    ("sm3_env", "3", "SM", "生物与环境的相互关系", "能用对比实验研究环境因素对生物的影响，知道食物链和食物网，体会生物与环境相互依存。"),
    ("sm3_evo", "3", "SM", "生命的延续与进化", "能描述生物的多样性，知道化石是古生物的证据，懂得保护生物多样性。"),
    ("dq3_sys", "3", "DQ", "宇宙中的地球与地球系统", "知道地球表面有山地、平原等地形，火山、地震、流水和风会改变地表，认识常见岩石。"),
    ("dq3_space", "3", "DQ", "宇宙中的地球与地球系统", "知道地球自转形成昼夜交替、公转和地轴倾斜形成四季；认识太阳系、星座和宇宙。"),
    ("dq3_human", "3", "DQ", "人类活动与环境", "知道地球资源有限，能说出常见环境问题，参与垃圾分类、节约资源等保护环境的行动。"),
    ("jg3_tech", "3", "JG", "技术、工程与社会", "知道工具和机械能让工作更省力或更方便，了解计时工具的发展，体会技术推动社会进步。"),
    ("jg3_eng", "3", "JG", "工程设计与物化", "能按明确问题、设计、制作、测试、改进的过程完成小船、塔台等简单工程任务。"),
]

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "物质科学": ["能说出物体或现象的主要特征", "能用观察或实验的结果解释简单现象"],
    "生命科学": ["能说出生物的主要特征或生命活动", "能把特征和生活环境、功能联系起来"],
    "地球与宇宙科学": ["能描述地球或天体的基本特征和变化", "能用模型或观测记录解释简单现象"],
    "技术与工程": ["能说出工具、结构或作品要解决的问题", "能按设计、制作、测试、改进的顺序完成任务"],
}
NOTE = "教科版该课的常见教学内容。条目是公开转述，不是逐页核对的原文。"


def chapter(grade, sem, unit):
    cn = "零一二三四五六"[grade]
    title = UNITS[(grade, sem, unit)][0]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit, title)


def hard(topic, prereq, reason):
    HARD.append((topic, prereq, reason))


def soft(topic, prereq, reason):
    """先修软边登记。只追加到 SOFT，不在本文件生成边或改题目。"""
    SOFT.append((topic, prereq, reason))


def math(key, mid, reason):
    MATH.append((key, mid, reason))


_CUR = {}


def vol(grade, sem):
    _CUR["g"], _CUR["s"] = grade, sem


def K(key, name, unit, typ, desc, qs, std=None, domain=None, official=True):
    """登记一个知识点。qs 是 4 道选择题：(题干, 正确答案, [三个干扰项], 解析)，难度依次 basic、basic、standard、challenge。

    official=False：官方目录无同名独立课，作为单元内概念保留，供编译脚本从官方课序软边链中拆出。
    不要把 official 写进对外 JSON 的 schema（本文件不写 JSON）。
    """
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
        "mastery_criteria": list(CRIT[domain]), "std": std or ustd, "official": official,
        "conf": "inferred", "note": NOTE,
        "items": [tuple(q) for q in qs],
    })


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


_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求")
_BANNED_COPY = re.compile("\u514d\u8d39|AI\\s*\u521d\u7a3f")


def check_question(key, q):
    if _BANNED_START.match(q["p"]):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, q["p"][:20]))
    blob = "\n".join([q["p"], q["e"], q["a"]] + q["w"])
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语" % key)
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    opts = [q["a"]] + q["w"]
    if len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
        raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    if not q["e"]:
        raise SystemExit("%s 缺少解析" % key)
