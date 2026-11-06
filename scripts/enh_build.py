#!/usr/bin/env python3
"""把高中英语草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

只追加 cne_h 知识点。不改已有数学、小学英语、初中英语的 id 和名称，也不回头约简旧边。
先修可以指向初中英语或小学英语，不能指向数学。

用法：python3 scripts/enh_build.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import en_lib  # noqa: E402
import en_topics  # noqa: E402,F401

PRIMARY_TOPICS = list(en_lib.TOPICS)
PRIMARY_BY_KEY = {t["key"]: t for t in PRIMARY_TOPICS}
en_lib.TOPICS = []
en_lib.HARD = []

import enj_topics  # noqa: E402

JUNIOR_TOPICS = list(en_lib.TOPICS)
JUNIOR_BY_KEY = {t["key"]: t for t in JUNIOR_TOPICS}
en_lib.TOPICS = []
en_lib.HARD = []

import enh_topics  # noqa: E402
from en_lib import HARD, TOPICS, check_question, materialise_questions  # noqa: E402
from enh_edges import SOFT  # noqa: E402
from verify_questions import verify_all  # noqa: E402

EN_CODES = {"PH": "语音", "VO": "词汇", "GR": "语法", "FU": "日常表达", "RW": "读写"}

# 课标条目是公开介绍的转述，不是逐页核对的原文。
# band：B 必修，S 选择性必修。编号 ces-2017 是本图谱编的。
STANDARD_ROWS = [
    ("stress", "B", "PH", "语音", "必修 · 语音",
     "能根据单词的重音位置区分词性和意义，并在朗读多音节词时把重音读出来。"),
    ("tone_b", "B", "PH", "语音", "必修 · 语音",
     "能用降调朗读陈述句和特殊疑问句，用升调朗读一般疑问句，并初步听出语气的差别。"),
    ("link", "B", "PH", "语音", "必修 · 语音",
     "能在意群中识别连读和不完全爆破，并在短语里按这个规则朗读。"),
    ("attitude", "S", "PH", "语音", "选择性必修 · 语音",
     "能用语调表达惊讶、犹豫、强调或礼貌等态度，而不是只区分升降调。"),
    ("weak", "S", "PH", "语音", "选择性必修 · 语音",
     "能在句子中识别功能词的弱读，并按节奏朗读较长的句子。"),
    ("vo_school", "B", "VO", "词汇", "必修 · 词汇",
     "能在语篇中理解与校园生活、课程、社团和新生适应有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_world", "B", "VO", "词汇", "必修 · 词汇",
     "能在语篇中理解与旅行、运动、灾害、语言、互联网和音乐有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_soc", "B", "VO", "词汇", "必修 · 词汇",
     "能在语篇中理解与文化遗产、野生动物、历史传统、节日、道德、多元文化、太空探索和金钱价值有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_form", "B", "VO", "词汇", "必修 · 词汇",
     "能根据常见前缀、后缀和词性变化判断派生词的意思。具体词缀表以课标附录为准，本条为转述。"),
    ("vo_people", "S", "VO", "词汇", "选择性必修 · 词汇",
     "能在语篇中理解与人物成就、未来生活、公园、肢体语言和农业生产有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_life", "S", "VO", "词汇", "选择性必修 · 词汇",
     "能在语篇中理解与科学研究、跨文化交流、饮食、长途旅行和急救有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_mind", "S", "VO", "词汇", "选择性必修 · 词汇",
     "能在语篇中理解与艺术、健康生活方式、环境保护、逆境和诗歌有关的词汇。词表以课标附录为准，本条为转述。"),
    ("vo_work", "S", "VO", "词汇", "选择性必修 · 词汇",
     "能在语篇中理解与科幻作品、地标、海洋探索、公益分享和职业规划有关的词汇。词表以课标附录为准，本条为转述。"),
    ("sent", "B", "GR", "语法", "必修 · 语法",
     "能识别主语、谓语、宾语、表语、状语、定语和补语，并分辨主谓、主谓宾、主系表、双宾语和宾语补足语等基本句型。"),
    ("phrase", "B", "GR", "语法", "必修 · 语法",
     "能识别名词短语、形容词短语和副词短语，并判断它们在句中作什么成分。"),
    ("tense", "B", "GR", "语法", "必修 · 语法",
     "能用现在进行时表示已经安排的将来，在时间和条件状语从句中用一般现在时表示将来，并在语篇中选择一般现在时、一般过去时、一般将来时和现在完成时。"),
    ("tag", "B", "GR", "语法", "必修 · 语法",
     "能使用附加疑问句确认信息，并让附加问句的人称、助动词和肯定否定与前面的陈述一致。"),
    ("rel", "B", "GR", "语法", "必修 · 语法",
     "能使用关系代词 who、whom、whose、which、that 和关系副词 when、where、why 引导限制性定语从句，并区分限制性与非限制性定语从句。"),
    ("passive", "B", "GR", "语法", "必修 · 语法",
     "能使用现在进行时和现在完成时的被动语态。进行时被动是 be being 加过去分词，完成时被动是 have been 加过去分词。"),
    ("ing", "B", "GR", "语法", "必修 · 语法",
     "能使用动词的 -ing 形式作定语、表语、宾语补足语和状语。"),
    ("pp", "B", "GR", "语法", "必修 · 语法",
     "能使用过去分词作定语、表语、宾语补足语和状语。"),
    ("toinf", "B", "GR", "语法", "必修 · 语法",
     "能使用动词不定式作主语、宾语、表语、定语、状语和宾语补足语，并注意省略 to 的情况。"),
    ("modal", "B", "GR", "语法", "必修 · 语法",
     "能使用情态动词表示推测、义务和建议，并能理解 must、could、should 等加 have done 表示对过去的判断。"),
    ("reported", "B", "GR", "语法", "必修 · 语法",
     "能把直接引语改为间接引语，并注意人称、时间和时态的变化。"),
    ("nouncls", "S", "GR", "语法", "选择性必修 · 语法",
     "能使用 that、whether 和疑问词引导的主语从句、表语从句和同位语从句，并区分同位语从句与定语从句。"),
    ("nonfin", "S", "GR", "语法", "选择性必修 · 语法",
     "能使用动词 -ing 和不定式的完成式、被动式，并在语境中选择 to do、doing 和 done。"),
    ("subj", "S", "GR", "语法", "选择性必修 · 语法",
     "能使用虚拟语气表达与现在、过去或将来事实相反的假设，以及 wish、if only、as if 和表示建议、命令、要求的从句。"),
    ("invert", "S", "GR", "语法", "选择性必修 · 语法",
     "能在否定副词、only 加状语、so、neither 以及省略 if 的虚拟条件句中使用倒装。"),
    ("emph", "S", "GR", "语法", "选择性必修 · 语法",
     "能使用 It is 或 It was 加被强调部分加 that 或 who 构成强调句，并用助动词 do 强调谓语。"),
    ("ellip", "S", "GR", "语法", "选择性必修 · 语法",
     "能识别并使用省略，避免重复已经出现的动词、不定式 to 后面的部分或从句里的相同成分。"),
    ("advcls", "S", "GR", "语法", "选择性必修 · 语法",
     "能使用 although、even though、while、so that、in case、unless 和 as long as 等引导状语从句，表达让步、对比、目的和条件。"),
    ("mix", "S", "GR", "语法", "选择性必修 · 语法",
     "能在较长的句子和语篇中综合判断时态、语态、非谓语和从句。"),
    ("fu_daily", "B", "FU", "日常表达", "必修 · 日常表达",
     "能问候、介绍自己，并谈论课程、社团和学校生活。"),
    ("fu_plan", "B", "FU", "日常表达", "必修 · 日常表达",
     "能谈论已经安排的计划，发出或回应邀请，并就旅行、运动提出建议。"),
    ("fu_view", "B", "FU", "日常表达", "必修 · 日常表达",
     "能就文化、环境、传统和价值交换看法，说明理由。"),
    ("fu_desc", "S", "FU", "日常表达", "选择性必修 · 日常表达",
     "能描述人物成就、身体语言、地方和过程，并给出清楚的步骤。"),
    ("fu_argue", "S", "FU", "日常表达", "选择性必修 · 日常表达",
     "能说明科学假设、比较文化差异、讨论健康与环境，并给出有依据的看法。"),
    ("fu_plan_s", "S", "FU", "日常表达", "选择性必修 · 日常表达",
     "能谈论职业打算、申请和公益安排，并礼貌地提出请求。"),
    ("rw_detail", "B", "RW", "读写", "必修 · 读写",
     "能读懂与教材话题有关的记叙文和说明文，找出人物、时间、地点、事件和原因。"),
    ("rw_main", "B", "RW", "读写", "必修 · 读写",
     "能概括短文的主旨，并判断作者的态度是赞成、担心还是只在说明事实。"),
    ("rw_write", "B", "RW", "读写", "必修 · 读写",
     "能根据要点选择或补全邮件、海报或报道中的句子，使人称、时态和要点一致。"),
    ("rw_infer", "S", "RW", "读写", "选择性必修 · 读写",
     "能根据上下文推断词义、代词指代和作者没有直接说出的态度。"),
    ("rw_argue", "S", "RW", "读写", "选择性必修 · 读写",
     "能识别议论文或说明文中的论点、依据和段落作用。"),
    ("rw_write_s", "S", "RW", "读写", "选择性必修 · 读写",
     "能根据要点选择概要、申请、步骤说明或观点短文中的句子，使逻辑和人称一致。"),
]

NOTE = {
    "语音": "语音项目按人教版（2019）常见教学顺序编排，没有核到人教社目录，册次待核。",
    "词汇": "人教版（2019）该单元的主题词。课标不逐词列出，词表和册次待核。",
    "语法": "句型按人教版（2019）必修与选择性必修的常见出现顺序编排，册次待核。",
    "日常表达": "教材中的功能句。课标没有逐句列出，册次待核。",
    "读写": "短文为诊断而写，考查阅读或书面表达要点。册次待核。",
}

# (grade, unit) -> (册名, 单元编号或欢迎单元, 英文单元名)
TITLES = {
    (10, 0): ("必修第一册", "欢迎单元", "Welcome Unit"),
    (10, 1): ("必修第一册", "第1单元", "Teenage Life"),
    (10, 2): ("必修第一册", "第2单元", "Travelling Around"),
    (10, 3): ("必修第一册", "第3单元", "Sports and Fitness"),
    (10, 4): ("必修第一册", "第4单元", "Natural Disasters"),
    (10, 5): ("必修第一册", "第5单元", "Languages Around the World"),
    (11, 1): ("必修第二册", "第1单元", "Cultural Heritage"),
    (11, 2): ("必修第二册", "第2单元", "Wildlife Protection"),
    (11, 3): ("必修第二册", "第3单元", "The Internet"),
    (11, 4): ("必修第二册", "第4单元", "History and Traditions"),
    (11, 5): ("必修第二册", "第5单元", "Music"),
    (12, 1): ("必修第三册", "第1单元", "Festivals and Celebrations"),
    (12, 2): ("必修第三册", "第2单元", "Morals and Virtues"),
    (12, 3): ("必修第三册", "第3单元", "Diverse Cultures"),
    (12, 4): ("必修第三册", "第4单元", "Space Exploration"),
    (12, 5): ("必修第三册", "第5单元", "The Value of Money"),
    (13, 1): ("选择性必修第一册", "第1单元", "People of Achievement"),
    (13, 2): ("选择性必修第一册", "第2单元", "Looking into the Future"),
    (13, 3): ("选择性必修第一册", "第3单元", "Fascinating Parks"),
    (13, 4): ("选择性必修第一册", "第4单元", "Body Language"),
    (13, 5): ("选择性必修第一册", "第5单元", "Working the Land"),
    (14, 1): ("选择性必修第二册", "第1单元", "Science and Scientists"),
    (14, 2): ("选择性必修第二册", "第2单元", "Bridging Cultures"),
    (14, 3): ("选择性必修第二册", "第3单元", "Food and Culture"),
    (14, 4): ("选择性必修第二册", "第4单元", "Journey Across a Vast Land"),
    (14, 5): ("选择性必修第二册", "第5单元", "First Aid"),
    (15, 1): ("选择性必修第三册", "第1单元", "Art"),
    (15, 2): ("选择性必修第三册", "第2单元", "Healthy Lifestyle"),
    (15, 3): ("选择性必修第三册", "第3单元", "Environmental Protection"),
    (15, 4): ("选择性必修第三册", "第4单元", "Adversity and Courage"),
    (15, 5): ("选择性必修第三册", "第5单元", "Poems"),
    (16, 1): ("选择性必修第四册", "第1单元", "Science Fiction"),
    (16, 2): ("选择性必修第四册", "第2单元", "Iconic Attractions"),
    (16, 3): ("选择性必修第四册", "第3单元", "Sea Exploration"),
    (16, 4): ("选择性必修第四册", "第4单元", "Sharing"),
    (16, 5): ("选择性必修第四册", "第5单元", "Launching Your Career"),
}

BOOK_GRADE = {
    "必修第一册": 10,
    "必修第二册": 11,
    "必修第三册": 12,
    "选择性必修第一册": 13,
    "选择性必修第二册": 14,
    "选择性必修第三册": 15,
    "选择性必修第四册": 16,
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def chapter(grade, unit):
    book, no, title = TITLES[(grade, unit)]
    return "%s %s %s" % (book, no, title)


def rank_of(grade, semester):
    return grade * 2 + (1 if semester == "下" else 0)


def reaches(adj, src, dst, hard_only):
    seen = {src}
    stack = [src]
    while stack:
        node = stack.pop()
        for pre, strength in adj.get(node, []):
            if hard_only and strength != "hard":
                continue
            if pre == dst:
                return True
            if pre not in seen:
                seen.add(pre)
                stack.append(pre)
    return False


def reduce_senior(edges):
    """只删除 cne_h 上的冗余新边。不改数学边，也不改小学、初中英语边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not str(e["topicId"]).startswith("cne_h"):
            kept.append(e)
            continue
        lst = adj[e["topicId"]]
        idx = next(i for i, (p, s) in enumerate(lst)
                   if p == e["prerequisiteId"] and s == e["strength"])
        lst.pop(idx)
        if reaches(adj, e["topicId"], e["prerequisiteId"], e["strength"] == "hard"):
            dropped += 1
            continue
        lst.append([e["prerequisiteId"], e["strength"]])
        kept.append(e)
    return kept, dropped


# 2026-11-06 对照人教社转载 PDF（2017年版2020年修订，不是2025年修订）：
# https://www.pep.com.cn/xw/zt/rjwy/gzkb2020/202205/P020220517522153664167.pdf
# 表4在印刷页20，表5在印刷页21–22，表6正文在印刷页24–25。
H_STATUS = (
    "2026-11-06 对照人教社转载《普通高中英语课程标准（2017年版2020年修订）》PDF 印刷页，"
    "text 仍是转述；未对 2025 年修订版逐条重核"
)
H_UNSEEN = "2026-11-06 已对表4–6；日常表达和读写对应的语言技能表未逐条核对，本条仍待核"
ENG_NOTE = (
    "义务教育部分是对一级（3–4年级）、二级（5–6年级）和三级（7–9年级）语言知识的公开转述。"
    "2026-11-06 对照人教社电子书《义务教育英语课程标准（2022年版）》"
    "（https://www.pep.com.cn/ebook/2022yjkcbz/yy/mobile/index.html）"
    "印刷页19表9、印刷页20表10、印刷页21表11。"
    "语音、词汇、语法的 page_or_ref 记这些印刷页，text 仍是转述，verbatim 为 false。"
    "日常表达和读写的大图未打开，page_or_ref 仍为「待核」。"
    "高中部分对照的是人教社转载 PDF《普通高中英语课程标准（2017年版2020年修订）》"
    "（https://www.pep.com.cn/xw/zt/rjwy/gzkb2020/202205/P020220517522153664167.pdf）"
    "印刷页20表4、21–22表5、24–25表6，不是 2025 年修订版逐条重核，也不是逐字原文。"
    "编号 ces-2022 对应义务教育，ces-2017:H.B 对应高中必修，ces-2017:H.S 对应高中选择性必修，都不是教育部原编号。"
    "教材册次另见核对文档，没有全部升成官方已核。"
)
SENIOR_NOTE = (
    "2026-11-06 对照的是人教社转载的 2020 年修订版 PDF，不是 2025 年日常修订版。"
    "语音、词汇、语法记了表4–6的印刷页；日常表达和读写仍为待核。"
    "必修对应课标中的必修，选择性必修对应课标中的选择性必修。"
    "虚拟语气、倒装、强调在表6里属于选修（提高类），库存仍标在选择性必修，text 未改。"
)
_T4 = "人教社转载 PDF 印刷页20，表4"
_T5 = "人教社转载 PDF 印刷页21–22，表5"
_T6 = "人教社转载 PDF 印刷页24–25，表6"
H_PAGE_REF = {
    "stress": _T4 + "必修第3条（转述；表4写用音标学习多音节词，未写按重音区分词性）",
    "tone_b": _T4 + "必修第1–2条（转述；未把陈述句、特殊疑问句、一般疑问句的升降调分开写）",
    "link": _T4 + "（转述；连读和不完全爆破写在同页教学提示，不是表4的内容要求分条）",
    "attitude": _T4 + "选择性必修第1条（转述；未单列惊讶、犹豫、强调、礼貌）",
    "weak": _T4 + "（转述；弱读不在表4，教学提示也未单列弱读）",
    "vo_school": _T5 + "必修（转述；校园、课程等主题词不在表5）",
    "vo_world": _T5 + "必修（转述；旅行、运动等主题词不在表5）",
    "vo_soc": _T5 + "必修（转述；文化遗产等主题词不在表5）",
    "vo_form": _T5 + "必修第2条（转述；表5写了解词根、词缀和词性变化，未给出词缀表）",
    "vo_people": _T5 + "选择性必修（转述；人物成就等主题词不在表5）",
    "vo_life": _T5 + "选择性必修（转述；科学研究等主题词不在表5）",
    "vo_mind": _T5 + "选择性必修（转述；艺术、健康等主题词不在表5）",
    "vo_work": _T5 + "选择性必修（转述；职业规划等主题词不在表5）",
    "sent": _T6 + "（转述；印刷页23写句法关注句子的成分，表6未逐一列出主谓宾等句型）",
    "phrase": _T6 + "选择性必修第10条（转述；库存标在必修，表6写在选择性必修，且用于分析长句）",
    "tense": _T6 + "（转述；表6未单列现在进行时表将来，也未单列时间、条件从句用一般现在时）",
    "tag": _T6 + "（转述；表6未单列附加疑问句）",
    "rel": _T6 + "必修第8条及选择性必修第8条（转述；非限制性定语从句在选择性必修，库存写在必修）",
    "passive": _T6 + "必修第4条（转述；未写 be being、have been 的公式）",
    "ing": _T6 + "必修第6条及选择性必修第6条（转述；作表语在选择性必修，库存写在必修）",
    "pp": _T6 + "必修第7条及选择性必修第7条（转述；作表语在选择性必修，库存写在必修）",
    "toinf": _T6 + "必修第5条及选择性必修第5条（转述；作主语、表语在选择性必修；省略 to 不在表6分条）",
    "modal": _T6 + "（转述；表6未单列情态动词和 have done）",
    "reported": _T6 + "（转述；表6未单列间接引语）",
    "nouncls": _T6 + "选择性必修第9条（转述；同位语从句在印刷页25选修提高类，不在选择性必修）",
    "nonfin": _T6 + "（转述；表6未单列非谓语的完成式和被动式）",
    "subj": "人教社转载 PDF 印刷页25，表6选修（提高类）第4条（转述；虚拟语气不在选择性必修内容要求，库存标在选择性必修）",
    "invert": "人教社转载 PDF 印刷页25，表6选修（提高类）第3条（转述；倒装不在选择性必修内容要求，库存标在选择性必修）",
    "emph": "人教社转载 PDF 印刷页25，表6选修（提高类）第3条（转述；强调不在选择性必修内容要求，库存标在选择性必修）",
    "ellip": _T6 + "必修第9条（转述；库存标在选择性必修，表6只要求简单的省略句）",
    "advcls": _T6 + "（转述；表6未单列 although、unless 等状语从句）",
    "mix": _T6 + "必修第2条及选择性必修第2条（转述；未按时态、语态、非谓语、从句分条）",
}


def h_fields(symbol):
    if symbol not in H_PAGE_REF:
        return "待核", H_UNSEEN
    return H_PAGE_REF[symbol], H_STATUS


def build_standards():
    counters = {}
    id_of = {}
    band_of = {}
    items = []
    for symbol, band, code, domain, section, text in STANDARD_ROWS:
        if domain != EN_CODES[code]:
            raise SystemExit("课标领域不一致：%s" % symbol)
        if band not in ("B", "S"):
            raise SystemExit("课标级别必须是 B 或 S：%s" % symbol)
        key = (band, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "ces-2017:H.%s.%s.%02d" % (band, code, counters[key])
        id_of[symbol] = sid
        band_of[symbol] = band
        ref, status = h_fields(symbol)
        if ref != "待核" and ("人教社转载 PDF 印刷页" not in ref or "转述" not in ref):
            raise SystemExit("课标页码必须写明人教社转载 PDF 印刷页和转述：%s" % symbol)
        items.append({
            "id": sid,
            "domain": domain,
            "section": section,
            "clause": "(%d)" % counters[key],
            "text": text,
            "page_or_ref": ref,
            "verbatim": False,
            "text_status": status,
        })
    return id_of, band_of, items


def build_question(tid, index, made, slot):
    qid = "%s_q%d" % (tid, index)
    if made["t"] == "numeric":
        return {
            "id": qid,
            "topicId": tid,
            "difficulty": made["d"],
            "type": "numeric",
            "prompt": made["p"],
            "answer": made["a"],
            "explanation": made["e"],
            "verify": made["v"],
        }, made["a"]
    texts = list(made["w"])
    texts.insert(slot % 4, made["a"])
    keys = list("ABCD")
    pos = texts.index(made["a"])
    return {
        "id": qid,
        "topicId": tid,
        "difficulty": made["d"],
        "type": "choice",
        "prompt": made["p"],
        "choices": [{"key": keys[i], "text": texts[i]} for i in range(4)],
        "answer": keys[pos],
        "explanation": made["e"],
        "verify": json.dumps(made["a"], ensure_ascii=False),
    }, made["a"]


def resolve_pre(src, dst, index, by_key, primary_id, junior_id):
    """成功时返回先修 id；内部边先返回 key，调用方再换成 cne_h id。失败返回 None。"""
    if dst.startswith("p:"):
        if dst not in primary_id:
            print("先修指向未知的小学知识点：%s → %s" % (src, dst), file=sys.stderr)
            return None
        pkey = dst[2:]
        pt = PRIMARY_BY_KEY[pkey]
        if rank_of(pt["grade"], pt["semester"]) > rank_of(by_key[src]["grade"], by_key[src]["semester"]):
            print("小学先修比高中更晚：%s 依赖 %s" % (src, pkey), file=sys.stderr)
            return None
        return primary_id[dst]
    if dst.startswith("j:"):
        if dst not in junior_id:
            print("先修指向未知的初中知识点：%s → %s" % (src, dst), file=sys.stderr)
            return None
        jkey = dst[2:]
        jt = JUNIOR_BY_KEY[jkey]
        if rank_of(jt["grade"], jt["semester"]) > rank_of(by_key[src]["grade"], by_key[src]["semester"]):
            print("初中先修比高中更晚：%s 依赖 %s" % (src, jkey), file=sys.stderr)
            return None
        return junior_id[dst]
    if dst not in index:
        print("先修指向未登记的知识点：%s → %s" % (src, dst), file=sys.stderr)
        return None
    if index[dst] >= index[src]:
        print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
        return None
    if rank_of(by_key[dst]["grade"], by_key[dst]["semester"]) > rank_of(by_key[src]["grade"], by_key[src]["semester"]):
        print("先修年级更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
        return None
    return "key:" + dst


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")
    if any(str(t.get("id", "")).startswith("cne_h") for t in topics):
        print("已经有 cne_h 知识点。enh_build.py 不能重复编译。", file=sys.stderr)
        return 1
    if not any(str(t.get("id", "")) == "cne_j001" for t in topics):
        print("缺少初中英语 cne_j001，不能单独编译高中。", file=sys.stderr)
        return 1
    if not (220 <= len(TOPICS) <= 320):
        print("知识点数量 %d 不在 220–320" % len(TOPICS), file=sys.stderr)
        return 1
    if not any(t["name"] == "虚拟语气" for t in TOPICS):
        print("缺少名称为「虚拟语气」的知识点", file=sys.stderr)
        return 1

    id_of_std, band_of, new_items = build_standards()
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    by_key = {t["key"]: t for t in TOPICS}
    names = {t["key"]: t["name"] for t in TOPICS}
    primary_id = {"p:%s" % t["key"]: "cne_p%03d" % i for i, t in enumerate(PRIMARY_TOPICS, start=1)}
    junior_id = {"j:%s" % t["key"]: "cne_j%03d" % i for i, t in enumerate(JUNIOR_TOPICS, start=1)}
    if len(primary_id) != 197:
        print("小学英语数量不是 197", file=sys.stderr)
        return 1
    if not (180 <= len(junior_id) <= 260):
        print("初中英语数量 %d 不在 180–260" % len(junior_id), file=sys.stderr)
        return 1

    for spec in TOPICS:
        if spec["std"] not in id_of_std:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        band = band_of[spec["std"]]
        if spec["grade"] <= 12 and band != "B":
            print("%s 在必修册，却挂了选择性必修课标 %s" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        if spec["grade"] >= 13 and band != "S":
            print("%s 在选择性必修册，却挂了必修课标 %s" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        spec["note"] = NOTE[spec["domain"]]
        if (spec["grade"], spec["unit"]) not in TITLES:
            print("%s 单元不存在：grade %s unit %s" % (spec["key"], spec["grade"], spec["unit"]), file=sys.stderr)
            return 1
        if spec["grade"] not in BOOK_GRADE.values():
            print("%s 年级不是 10–16" % spec["key"], file=sys.stderr)
            return 1
        if spec["semester"] != "上":
            print("%s 高中英语学期必须是上" % spec["key"], file=sys.stderr)
            return 1
        book = TITLES[(spec["grade"], spec["unit"])][0]
        if BOOK_GRADE[book] != spec["grade"]:
            print("%s 册次和 grade 不一致" % spec["key"], file=sys.stderr)
            return 1

    hard_pairs = {}
    resolved_hard = []
    for src, dst, reason in HARD:
        if src not in index:
            print("硬先修的后续未登记：%s" % src, file=sys.stderr)
            return 1
        if (src, dst) in hard_pairs:
            print("重复硬边 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        pid = resolve_pre(src, dst, index, by_key, primary_id, junior_id)
        if pid is None:
            return 1
        hard_pairs[(src, dst)] = reason
        resolved_hard.append((src, dst, pid, reason))

    soft_pairs = {}
    resolved_soft = []
    for src, dst, reason in SOFT:
        if src not in index:
            print("软先修的后续未登记：%s" % src, file=sys.stderr)
            return 1
        if (src, dst) in soft_pairs or (src, dst) in hard_pairs:
            print("重复软边或与硬边重复 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        pid = resolve_pre(src, dst, index, by_key, primary_id, junior_id)
        if pid is None:
            return 1
        soft_pairs[(src, dst)] = reason
        resolved_soft.append((src, dst, pid, reason))

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_h%03d" % i
        id_of[spec["key"]] = tid
        made = materialise_questions(spec)
        if not (3 <= len(made) <= 5):
            print("%s 题数 %d 不在 3–5" % (spec["key"], len(made)), file=sys.stderr)
            return 1
        for item in made:
            check_question(spec["key"], item)
        built = []
        diag_answer = None
        for n, item in enumerate(made, start=1):
            q, shown = build_question(tid, n, item, slot=i + n)
            built.append(q)
            if n == 1:
                diag_answer = shown
        ref = {"id": id_of_std[spec["std"]], "confidence": spec["conf"]}
        if spec.get("note"):
            ref["note"] = spec["note"]
        topic = {
            "id": tid,
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": spec["grade"],
            "semester": spec["semester"],
            "chapter": chapter(spec["grade"], spec["unit"]),
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag_answer},
            "external": False,
            "subject": "english",
            "standards": [ref],
        }
        new_topics.append(topic)
        new_questions.extend(built)

    raw = []
    for i in range(1, len(TOPICS)):
        cur = TOPICS[i]["key"]
        prev = TOPICS[i - 1]["key"]
        if (cur, prev) in hard_pairs or (cur, prev) in soft_pairs:
            continue
        reason = "按人教版（2019）的常见教学顺序，先学「%s」，再学「%s」。册次待核。" % (names[prev], names[cur])
        raw.append((cur, prev, "soft", reason, id_of[prev]))
    def edge_id(pid):
        if str(pid).startswith("key:"):
            return id_of[pid[4:]]
        return pid

    for src, dst, pid, reason in resolved_soft:
        raw.append((src, dst, "soft", reason, edge_id(pid)))
    for src, dst, pid, reason in resolved_hard:
        raw.append((src, dst, "hard", reason, edge_id(pid)))

    if not any(src == TOPICS[0]["key"] for src, _, _, _, _ in raw):
        print("第一个高中知识点没有先修", file=sys.stderr)
        return 1

    new_edges = []
    seen = set()
    for src, dst, strength, reason, pre_id in raw:
        key = (id_of[src], pre_id)
        if key in seen:
            print("重复边 %s → %s" % key, file=sys.stderr)
            return 1
        seen.add(key)
        if not str(pre_id).startswith("cne_"):
            print("英语边连到了非英语知识点 %s" % pre_id, file=sys.stderr)
            return 1
        new_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": pre_id,
            "strength": strength,
            "reason": reason,
        })

    merged_deps, dropped = reduce_senior(deps + new_edges)
    hs_edges = [e for e in merged_deps if str(e["topicId"]).startswith("cne_h")]
    if any(not str(e["prerequisiteId"]).startswith("cne_") for e in hs_edges):
        print("高中英语边连到了数学知识点", file=sys.stderr)
        return 1
    if any(str(e["topicId"]).startswith("cne_h") for e in deps):
        print("原依赖里已有高中英语边", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in hs_edges}
    missing = [t["id"] for t in new_topics if t["id"] not in covered]
    if missing:
        print("约简后仍无先修：%s" % "、".join(missing[:20]), file=sys.stderr)
        return 1
    cross_j = [e for e in hs_edges if str(e["prerequisiteId"]).startswith("cne_j")]
    cross_p = [e for e in hs_edges if str(e["prerequisiteId"]).startswith("cne_p")]
    if len(cross_j) < 8:
        print("跨到初中英语的边只有 %d 条" % len(cross_j), file=sys.stderr)
        return 1
    n_hard = sum(1 for e in hs_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in hs_edges if e["strength"] == "soft")
    if n_soft <= n_hard:
        print("软先修 %d 没有多于硬先修 %d" % (n_soft, n_hard), file=sys.stderr)
        return 1

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    by_grade = Counter(t["grade"] for t in new_topics)
    by_dom = Counter(t["domain"] for t in new_topics)
    book_name = {10: "必修一", 11: "必修二", 12: "必修三", 13: "选必一", 14: "选必二", 15: "选必三", 16: "选必四"}
    print("高中英语知识点 %d" % len(new_topics))
    for g in range(10, 17):
        print("  %s %d" % (book_name[g], by_grade[g]))
    for k, v in by_dom.most_common():
        print("  %s %d" % (k, v))
    print("高中英语边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(hs_edges), dropped, n_hard, n_soft))
    print("其中跨到初中 %d，跨到小学 %d" % (len(cross_j), len(cross_p)))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))
    sub_id = next(t["id"] for t in new_topics if t["name"] == "虚拟语气")
    print("虚拟语气 %s" % sub_id)

    eng = standards.get("english")
    if not isinstance(eng, dict):
        print("缺少 english 课标对象", file=sys.stderr)
        return 1
    eng["stage"] = "义务教育一级至三级；普通高中必修与选择性必修"
    eng["note"] = ENG_NOTE
    eng["senior"] = {
        "title": "普通高中英语课程标准（2017年版2025年修订）",
        "issuer": "中华人民共和国教育部",
        "year": 2025,
        "url": "http://www.moe.gov.cn/srcsite/A26/s8001/202006/t20200603_462199.html",
        "note": SENIOR_NOTE,
    }

    old_topic_n = len(topics)
    old_dep_n = len(deps)
    old_q_n = len(questions)
    old_std_n = len(standards["items"])
    old_ids = [(t["id"], t["name"]) for t in topics]
    standards["items"].extend(new_items)
    dump("topics.json", topics + new_topics)
    dump("dependencies.json", merged_deps)
    dump("questions.json", questions + new_questions)
    dump("cn-curriculum-standards.json", standards)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    if again_t[:old_topic_n] != topics or [(t["id"], t["name"]) for t in again_t[:old_topic_n]] != old_ids:
        print("已有知识点在写回后发生了变化", file=sys.stderr)
        return 1
    if again_d[:old_dep_n] != deps or again_q[:old_q_n] != questions:
        print("已有边或题目在写回后发生了变化", file=sys.stderr)
        return 1
    if again_s["items"][:old_std_n] != standards["items"][:old_std_n]:
        print("原课标条目发生了变化", file=sys.stderr)
        return 1
    print("已有节点 %d 个 id 与名称未改" % len(old_ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
