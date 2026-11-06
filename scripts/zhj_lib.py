# -*- coding: utf-8 -*-
"""初中语文数据的登记与题目生成。由 scripts/zhj_build.py 调用。

只追加 cnc_j 知识点。不改小学语文 cnc_p 的 id、名称、题目和边。

目录依据（查证日期 2026-11-06；未逐页核对纸质课本）：
- 七上：2024 秋修订统编《语文》七年级上册。课文目录对照教师之家
  （renjiaoshe，统编版 2024 七年级上册）和学科网对国家中小学智慧教育平台
  电子课本目录的转述（contentId=8b9c7052-add4-4744-ab04-69d6c180d5d9）。
  智慧教育平台正文本次未能打开。目录本身只标「第×单元」，单元短名取公开导读常用名。
- 七下：2024 年版、2025 春开始使用。篇目调整、人文主题和整本书安排，以人教社
  王立军《2024年版统编语文教材七年级下册的主要变化及教学建议》为准
  （https://www.pep.com.cn/xw/zt/hd/12/zbtjc/202505/t20250507_1999894.html）。
  课文顺序再对照教师之家、电子书课本网的转载目录。
- 八上：2024 审定统编《语文》八年级上册。课文目录对照教师之家
  （统编版 2024 八年级上册）和电子书课本网 2024 审定目录
  （五四制页 https://www.dzskb.com/tbb54yw8sc-2024.html 与教师之家篇目一致）。
  智慧教育平台正文未打开。非逐页核对纸质课本。
- 八下：2024 审定统编《语文》八年级下册，公开材料对应 2026 春使用。
  目录对照电子书课本网 2024 审定版（https://www.dzskb.com/tbbyw8xc-2024.html）。
  与旧版相比，自读换为《月亮是从哪里来的》，演讲单元增《敬业与乐业》，
  整本书为《经典常谈》《昆虫记》。非逐页核对纸质课本。
- 九上：2024 审定统编《语文》九年级上册。课文目录对照电子书课本网
  （https://www.dzskb.com/tbbyw9sc-2024.html，2026-07-28，标「2024审定版·现行最新」）。
  智慧教育平台正文未打开，未逐页核对纸质课本。目录转写有明显笔误处已按通行篇名改正，
  并在九年级脚本里注明。部分教辅把《培养德智体美劳全面发展的社会主义建设者和接班人》
  标成第二单元第7课，与该站全册页码不符，本图谱按全册目录放在第五单元。
- 九下：未见 2024 审定目录页（dzskb 只有现行页 https://www.dzskb.com/tbbyw9xc.html，
  2025-07-22，未标审定年份）。修订版预计 2027 春使用，公开目录未上线，暂用现行统编九年级下册。
  已出现在七上或新九上的篇目不重复建点：《梅岭三章》，《蒲柳人家》，《简·爱》，
  以及现行九下第六单元的《曹刿论战》《邹忌讽齐王纳谏》《陈涉世家》《出师表》《诗词曲五首》。
  第六单元只保留现行目录里尚未移走的写作和课外古诗词。2024 年夏的变化综述曾说九下整本书
  将为《水浒传》《儒林外史》，修订版目录未出，不据此新增《水浒传》。
"""

import re

TOPICS = []
HARD = []

# (年级, 学期, 单元) -> 单元名。教材目录多只写「第×单元」，短名取公开导读或编者文章里的人文主题。
UNITS = {
    (7, "上", 1): "四季美景",
    (7, "上", 2): "至爱亲情",
    (7, "上", 3): "学习生活",
    (7, "上", 4): "人生之舟",
    (7, "上", 5): "人与动物",
    (7, "上", 6): "想象之翼",
    (7, "下", 1): "群星闪耀",
    (7, "下", 2): "家国情怀",
    (7, "下", 3): "凡人小事",
    (7, "下", 4): "修身正己",
    (7, "下", 5): "哲理之思",
    (7, "下", 6): "科学探索",
    (8, "上", 1): "活动探究·新闻",
    (8, "上", 2): "生活的记忆",
    (8, "上", 3): "山川美景",
    (8, "上", 4): "情感哲思",
    (8, "上", 5): "文明的印迹",
    (8, "上", 6): "情操与志趣",
    (8, "下", 1): "民风民俗",
    (8, "下", 2): "科技之光",
    (8, "下", 3): "思想与情趣",
    (8, "下", 4): "活动探究·演讲",
    (8, "下", 5): "江山多娇",
    (8, "下", 6): "情趣理趣",
    (9, "上", 1): "活动探究·诗歌",
    (9, "上", 2): "观点与思辨",
    (9, "上", 3): "游目骋怀",
    (9, "上", 4): "小说中的人",
    (9, "上", 5): "议论的力量",
    (9, "上", 6): "史传与家国",
    (9, "下", 1): "现代诗情",
    (9, "下", 2): "小说人物",
    (9, "下", 3): "取义与求学",
    (9, "下", 4): "读书与鉴赏",
    (9, "下", 5): "舞台人生",
    (9, "下", 6): "创意与余响",
}

DOMAINS = (
    "识字写字", "词语", "句子", "阅读理解",
    "古诗文积累", "文言文阅读", "名著阅读", "习作基础",
)
CODES = {
    "SZ": "识字写字", "CY": "词语", "JZ": "句子", "YD": "阅读理解",
    "GS": "古诗文积累", "WY": "文言文阅读", "MZ": "名著阅读", "XZ": "习作基础",
}
CODE_OF = CODES
TEXT_STATUS = "公开转述，未与《义务教育语文课程标准（2022年版）》第四学段逐页核对"

# 课标条目是《义务教育语文课程标准（2022年版）》第四学段内容要求的公开转述，不是逐页核对的原文。
# 来源：中国教育在线、龙源期刊网等对 2022 年版课标第四学段的公开介绍（查证日期 2026-11-05）。
STANDARD_ROWS = [
    ("sz_79", "4", "SZ", "识字写字", "第四学段 · 识字与写字",
     "累计认识常用汉字约3500个，能正确工整地书写汉字，并熟练使用字典、词典独立识字。学写规范、通行的行楷字，临摹名家书法，体会书法的审美价值。"),
    ("cy_79", "4", "CY", "词语", "第四学段 · 词语",
     "能在具体语境中理解词语的含义，体会词语的感情色彩和表达效果，并积累常用成语和课文中的词语。"),
    ("jz_79", "4", "JZ", "句子", "第四学段 · 句子",
     "能理清句子之间的关系，修改明显语病，并体会比喻、拟人、排比等常见修辞手法的表达作用。"),
    ("yd_79", "4", "YD", "阅读理解", "第四学段 · 阅读与鉴赏",
     "能较熟练地运用略读和浏览的方法，扩大阅读范围；在通读课文的基础上，理清思路，理解、分析主要内容。"),
    ("yd_lit", "4", "YD", "阅读理解", "第四学段 · 文学作品",
     "欣赏文学作品，有自己的情感体验，初步领悟作品的内涵，从中获得对自然、社会、人生的有益启示。"),
    ("yd_prac", "4", "YD", "阅读理解", "第四学段 · 实用类文本",
     "阅读新闻和说明性文章，能把握观点和材料；阅读简单的议论文，区分观点与材料，并能判断材料能否支持观点。"),
    ("gs_79", "4", "GS", "古诗文积累", "第四学段 · 古诗文",
     "诵读古代诗词，展开想象，体会作品的情感和意境，背诵优秀诗文80篇（段）。"),
    ("wy_79", "4", "WY", "文言文阅读", "第四学段 · 文言文",
     "阅读浅易文言文，能借助注释和工具书理解基本内容。注重积累、感悟和运用，提高自己的欣赏品位。"),
    ("mz_79", "4", "MZ", "名著阅读", "第四学段 · 整本书阅读",
     "每学年阅读两三部名著，探索个性化的阅读方法，分享阅读感受。课外阅读总量不少于260万字。"),
    ("xz_narr", "4", "XZ", "习作基础", "第四学段 · 记叙与观察",
     "多角度观察生活，抓住事物特征，写记叙性文章，表达意图明确，内容具体充实。"),
    ("xz_arg", "4", "XZ", "习作基础", "第四学段 · 说明议论与应用",
     "写简单的说明性文章，注意抓住事物的特征；写简单的议论性文章，做到观点明确，有理有据；根据生活需要，写常见应用文。能进行缩写、扩写和改写。"),
    ("xz_oral", "4", "XZ", "习作基础", "第四学段 · 口语交际",
     "能注意对象和场合，学习文明得体地交流。讲述见闻，内容具体、语言生动。能就适当的话题作即席讲话和有准备的主题演讲。"),
]

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "识字写字": ["能借助字典、词典理解课文中的字词", "能分辨常见文言实词和通假字的常用义"],
    "词语": ["能理解词语在句子里的意思", "能体会词语的感情色彩和表达效果"],
    "句子": ["能指出句子使用的修辞或层次关系", "能判断哪一句更通顺、更得体"],
    "阅读理解": ["能根据课文选出和文字一致的信息", "能说出文章的主要内容和思想感情"],
    "古诗文积累": ["能背出本课要求积累的诗句", "能分清作者、诗题和名句，不把字句记错"],
    "文言文阅读": ["能借助注释说出文章大意", "能指出常见文言虚词、实词在句中的意思"],
    "名著阅读": ["能说出这部名著的作者、主要人物或主要内容", "能把情节和人物对应起来，不张冠李戴"],
    "习作基础": ["能判断哪一段更符合本次写作要求", "能指出材料、中心或顺序上的明显问题"],
}
NOTE = "统编版该课的常见教学内容。条目是公开转述，不是逐页核对的原文。"

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求|你认为|是否应该")
_BANNED_COPY = re.compile(r"免费|AI\s*初稿|AI初稿")
_CUR = {}


def chapter(grade, sem, unit):
    cn = "零一二三四五六七八九"[grade]
    title = UNITS[(grade, sem, unit)]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit, title)


def hard(topic, prereq, reason):
    """登记硬先修。prereq 可以是初中 key，或 p:小学语文 key（如 p:g1a_tian）。"""
    HARD.append((topic, prereq, reason))


def vol(grade, sem):
    _CUR["g"], _CUR["s"] = grade, sem


def K(key, name, unit, typ, desc, qs, std, domain):
    """登记一个知识点。qs 是 4 道选择题：(题干, 正确答案, [三个干扰项], 解析)，难度依次 basic、basic、standard、challenge。"""
    g, s = _CUR["g"], _CUR["s"]
    if (g, s, unit) not in UNITS:
        raise SystemExit("%s 单元未登记：%s%s 第%d单元" % (key, g, s, unit))
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
    """解析 V/L/Q 行。字段用 | 分开，题目文字里不要写 |。

    V|年级|学期
    L|key|名称|单元|type|领域|课标符号|说明
    Q|题干|正确答案|干扰1|干扰2|干扰3|解析
    """
    cur = None
    qs = []

    def flush():
        if cur is None:
            return
        key, name, unit, typ, domain, std, desc = cur
        K(key, name, int(unit), typ, desc, qs, std, domain)

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
            if len(parts) != 8:
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
        made.append({
            "d": diff, "t": "choice", "p": str(prompt).strip(), "a": str(answer).strip(),
            "w": [str(w).strip() for w in wrongs], "e": str(expl).strip(),
        })
    if len(made) != 4:
        raise SystemExit("%s 生成了 %d 题" % (spec["key"], len(made)))
    return made


def norm_opt(text):
    s = str(text).strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[.!\s]+$", "", s)
    return s


def check_question(key, q):
    prompt = q["p"]
    if _BANNED_START.match(prompt.strip()):
        raise SystemExit("%s 题干以禁用词开头：%s" % (key, prompt[:20]))
    blob = prompt + "\n" + q["e"] + "\n" + q["a"]
    if q["t"] == "choice":
        blob += "\n" + "\n".join(q["w"])
    if _BANNED_META.search(blob):
        raise SystemExit("%s 出现禁用元问题用语" % key)
    if _BANNED_COPY.search(blob):
        raise SystemExit("%s 出现不该出现的字样" % key)
    if q["t"] != "choice":
        raise SystemExit("%s 初中语文题目一律用选择题" % key)
    opts = [q["a"]] + list(q["w"])
    if len(opts) != 4 or len(set(opts)) != 4:
        raise SystemExit("%s 选项重复或不是 4 个：%s" % (key, opts))
    if len(set(norm_opt(o) for o in opts)) != 4:
        raise SystemExit("%s 选项规范化后重复：%s" % (key, opts))
    for o in opts:
        if not str(o).strip():
            raise SystemExit("%s 有空选项" % key)
        if re.fullmatch(r"[A-Za-z]", o.strip()):
            raise SystemExit("%s 选项不能是单个字母：%s" % (key, o))
    if not str(q["e"]).strip():
        raise SystemExit("%s 缺少解析" % key)
