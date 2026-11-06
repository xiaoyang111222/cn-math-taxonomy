#!/usr/bin/env python3
"""把初中英语草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

只追加 cne_j 知识点。不改已有数学、小学英语的 id 和名称，也不回头约简旧边。
先修可以指向小学英语，不能指向数学。

用法：python3 scripts/enj_build.py
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
from en_lib import HARD, TOPICS, check_question, materialise_questions  # noqa: E402
from verify_questions import verify_all  # noqa: E402

EN_CODES = {"PH": "语音", "VO": "词汇", "GR": "语法", "FU": "日常表达", "RW": "读写"}
CN = "零一二三四五六七八九"

# 课标条目是公开介绍的转述，不是逐页核对的原文。
STANDARD_ROWS = [
    ("stress", "3", "PH", "语音", "三级 · 语音",
     "能识别常见双音节和多音节单词的重音位置，并在朗读时把重音读出来。"),
    ("tone", "3", "PH", "语音", "三级 · 语音",
     "能用降调朗读陈述句和特殊疑问句，用升调朗读一般疑问句。"),
    ("esound", "3", "PH", "语音", "三级 · 语音",
     "能根据词尾音分辨名词复数和动词第三人称单数 -s、-es 的常见读音。"),
    ("edsound", "3", "PH", "语音", "三级 · 语音",
     "能根据动词词尾分辨规则动词过去式 -ed 的三种常见读音。"),
    ("link", "3", "PH", "语音", "三级 · 语音",
     "能感知辅音结尾的词与元音开头的词之间的连读，并在短语中初步朗读。"),
    ("plosion", "3", "PH", "语音", "三级 · 语音",
     "能感知爆破音相邻时的不完全爆破，如 sit down 中的 /t/。"),
    ("pause", "3", "PH", "语音", "三级 · 语音",
     "能按意群停顿朗读句子，不把一个意群从中间拆开。"),
    ("vocab7", "3", "VO", "词汇", "三级 · 词汇",
     "能在语境中理解与姓名、家庭、学校、食物、衣物、动物、天气和场所有关的核心词汇。三级词表以课标附录为准，本条为转述。"),
    ("vocab8", "3", "VO", "词汇", "三级 · 词汇",
     "能在语境中理解与习惯、比较、计划、健康、家务、故事和旅行经历有关的词汇。三级词表以课标附录为准，本条为转述。"),
    ("vocab9", "3", "VO", "词汇", "三级 · 词汇",
     "能在语境中理解并初步运用与学习、节日、发明、规则、习俗和环保有关的词汇。三级词表以课标附录为准，本条为转述。"),
    ("be_have", "3", "GR", "语法", "三级 · 语法",
     "能在句子中正确使用 am、is、are，并区分 have 和 has。"),
    ("noun_pron", "3", "GR", "语法", "三级 · 语法",
     "能区分可数名词与不可数名词，使用名词复数、指示代词和形容词性物主代词。"),
    ("present", "3", "GR", "语法", "三级 · 语法",
     "能用一般现在时描述习惯和事实，包括第三人称单数，以及 do、does 引导的疑问句和否定句。"),
    ("continuous", "3", "GR", "语法", "三级 · 语法",
     "能用现在进行时描述正在发生的动作，结构是 am、is、are 加动词的 -ing 形式。"),
    ("past", "3", "GR", "语法", "三级 · 语法",
     "能用一般过去时叙述过去的事情，包括 was、were、规则动词 -ed 和常见不规则动词，以及 Did 提问。"),
    ("future", "3", "GR", "语法", "三级 · 语法",
     "能用 be going to 表达打算，用 will 表达预测或临时决定。"),
    ("pastcont", "3", "GR", "语法", "三级 · 语法",
     "能用过去进行时描述过去某一时刻正在做的事，并用 when、while 连接两个过去的动作。"),
    ("perfect", "3", "GR", "语法", "三级 · 语法",
     "能用现在完成时谈论经历和已经发生的事，并正确使用 already、yet、ever、never、been、gone、for 和 since。"),
    ("pastperf", "3", "GR", "语法", "三级 · 语法",
     "能用过去完成时表示在过去某一动作之前已经发生的事，结构是 had 加过去分词。"),
    ("modal", "3", "GR", "语法", "三级 · 语法",
     "能使用 can、could、must、should、have to、would 和 might，表示能力、义务、请求、建议或推测。"),
    ("compare", "3", "GR", "语法", "三级 · 语法",
     "能使用形容词和副词的比较级、最高级，对两者或三者以上进行比较。"),
    ("sentence", "3", "GR", "语法", "三级 · 语法",
     "能使用祈使句、感叹句和反意疑问句。"),
    ("question", "3", "GR", "语法", "三级 · 语法",
     "能用 what、where、when、who、why、how、how much、how often 和 how far 获取信息。"),
    ("to_ing", "3", "GR", "语法", "三级 · 语法",
     "能使用动词不定式作宾语、宾语补足语和目的状语，并区分部分动词后接不定式或动名词。"),
    ("clause_obj", "3", "GR", "语法", "三级 · 语法",
     "能使用 that、if、whether 和疑问词引导的宾语从句，从句使用陈述语序。"),
    ("clause_attr", "3", "GR", "语法", "三级 · 语法",
     "能使用 who、which、that 引导的限制性定语从句修饰人或物。"),
    ("clause_adv", "3", "GR", "语法", "三级 · 语法",
     "能使用 because、if、unless、when、although 和 so that 引导状语从句。"),
    ("passive", "3", "GR", "语法", "三级 · 语法",
     "能使用一般现在时和一般过去时的被动语态，结构是 be 加过去分词。"),
    ("there_prep", "3", "GR", "语法", "三级 · 语法",
     "能用 There be 和方位介词描述某处有什么、物品在哪里。"),
    ("tense", "3", "GR", "语法", "三级 · 语法",
     "能根据时间状语和语境，在一般现在时、一般过去时、一般将来时、进行时和完成时之间作出选择。"),
    ("func_school", "3", "FU", "日常表达", "三级 · 日常表达",
     "能问候、介绍自己和家人，谈论学科、作息、规则和学校活动。"),
    ("func_life", "3", "FU", "日常表达", "三级 · 日常表达",
     "能购物、点餐、问路、谈论天气、外貌、动物和正在做的事。"),
    ("func_plan", "3", "FU", "日常表达", "三级 · 日常表达",
     "能发出邀请、接受或拒绝，提出建议，谈论计划和已经发生的经历。"),
    ("func_view", "3", "FU", "日常表达", "三级 · 日常表达",
     "能表达观点，礼貌提问，说明习俗，并就规则、健康和环保交换看法。"),
    ("read_detail", "3", "RW", "读写", "三级 · 读写",
     "能读懂与教材话题有关的简短文章，找出人物、时间、地点、事件和原因。"),
    ("read_cloze", "3", "RW", "读写", "三级 · 读写",
     "能根据上下文，为短文选择意思连贯的词或句子。"),
    ("write_point", "3", "RW", "读写", "三级 · 读写",
     "能根据要点选择或补全书面表达中的句子，使人称、时态和要点一致。"),
]

NOTE = {
    "语音": "语音项目按初中常见教学顺序编排，没有核到人教社目录，册次待核。",
    "词汇": "人教版 Go for it! 该单元的主题词。课标不逐词列出，词表和册次待核。",
    "语法": "句型按人教版 Go for it! 七上到九年级全一册的常见出现顺序编排，册次待核。",
    "日常表达": "教材中的功能句。课标没有逐句列出，册次待核。",
    "读写": "短文为诊断而写，考查阅读或书面表达要点。册次待核。",
}

# 七上单元名对照人教社资源页 2026-11-06（Asia/Tokyo）：
# https://www.pep.com.cn/zslth/yyptzy/czyy/7s/
# 101–103 是 Starter Unit 1–3；1–7 是 Unit 1–7；90 是未挂到具体单元的待核项。
# 40 只给已经入库为「七年级下册 第4单元 Eat Well」的食物点占位，避免和七上第 6 单元抢编号。
UNITS = {
    (7, "上", 101): "Hello!",
    (7, "上", 102): "Keep Tidy!",
    (7, "上", 103): "Welcome!",
    (7, "上", 1): "You and Me",
    (7, "上", 2): "We're Family!",
    (7, "上", 3): "My School",
    (7, "上", 4): "My Favourite Subject",
    (7, "上", 5): "Fun Clubs",
    (7, "上", 6): "A Day in the Life",
    (7, "上", 7): "Happy Birthday!",
    (7, "上", 90): "待核",
    (7, "下", 40): "Eat Well",
    (7, "下", 1): "Can you play the guitar",
    (7, "下", 2): "What time do you go to school",
    (7, "下", 3): "How do you get to school",
    (7, "下", 4): "Don't eat in class",
    (7, "下", 5): "Why do you like pandas",
    (7, "下", 6): "I'm watching TV",
    (7, "下", 7): "It's raining",
    (7, "下", 8): "Is there a post office near here",
    (7, "下", 9): "What does he look like",
    (7, "下", 10): "I'd like some noodles",
    (7, "下", 11): "How was your school trip",
    (7, "下", 12): "What did you do last weekend",
    (8, "上", 1): "Where did you go on vacation",
    (8, "上", 2): "How often do you exercise",
    (8, "上", 3): "I'm more outgoing than my sister",
    (8, "上", 4): "What's the best movie theater",
    (8, "上", 5): "Do you want to watch a game show",
    (8, "上", 6): "I'm going to study computer science",
    (8, "上", 7): "Will people have robots",
    (8, "上", 8): "How do you make a banana milk shake",
    (8, "上", 9): "Can you come to my party",
    (8, "上", 10): "If you go to the party, you'll have a great time",
    (8, "下", 1): "What's the matter",
    (8, "下", 2): "I'll help to clean up the city parks",
    (8, "下", 3): "Could you please clean your room",
    (8, "下", 4): "Why don't you talk to your parents",
    (8, "下", 5): "What were you doing when the rainstorm came",
    (8, "下", 6): "An old man tried to move the mountains",
    (8, "下", 7): "What's the highest mountain in the world",
    (8, "下", 8): "Have you read Treasure Island yet",
    (8, "下", 9): "Have you ever been to a museum",
    (8, "下", 10): "I've had this bike for three years",
    (9, "全", 1): "How can we become good learners",
    (9, "全", 2): "I think that mooncakes are delicious",
    (9, "全", 3): "Could you please tell me where the restrooms are",
    (9, "全", 4): "I used to be afraid of the dark",
    (9, "全", 5): "What are the shirts made of",
    (9, "全", 6): "When was it invented",
    (9, "全", 7): "Teenagers should be allowed to choose their own clothes",
    (9, "全", 8): "It must belong to Carla",
    (9, "全", 9): "I like music that I can dance to",
    (9, "全", 10): "You're supposed to shake hands",
    (9, "全", 11): "Sad movies make me cry",
    (9, "全", 12): "Life is full of the unexpected",
    (9, "全", 13): "We're trying to save the earth",
    (9, "全", 14): "I remember meeting all of you in Grade 7",
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def chapter(grade, sem, unit):
    title = UNITS[(grade, sem, unit)]
    if grade == 7 and sem == "上" and unit >= 101:
        return "七年级上册 预备单元%d %s" % (unit - 100, title)
    if grade == 7 and sem == "上" and unit == 90:
        return "七年级上册 待核"
    if grade == 7 and sem == "上":
        return "七年级上册 第%d单元 %s" % (unit, title)
    if (grade, sem, unit) == (7, "下", 40):
        return "七年级下册 第4单元 Eat Well"
    return "%s年级%s册 第%d单元 %s" % (CN[grade], sem, unit, title)


def rank(grade, sem):
    return grade * 2 + (1 if sem == "下" else 0)


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


def reduce_junior(edges):
    """只删除 cne_j 上的冗余新边。不改数学边，也不改小学英语边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not str(e["topicId"]).startswith("cne_j"):
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


# 与 en_lib 同一套人教社电子书印刷页。三级语音在表9，词汇在表10（三级+续表在印刷页21），语法在表11。
J_STATUS = (
    "2026-11-06 对照人教社电子书《义务教育英语课程标准（2022年版）》印刷页，"
    "text 仍是转述，不是表内逐字原文"
)
J_UNSEEN = (
    "2026-11-06 已打开表9–11（印刷页19–21）；语用知识和语言技能表的大图未打开，本条仍待核"
)
_P19 = "人教社电子书印刷页19，"
_P20 = "人教社电子书印刷页20，"
_P21 = "人教社电子书印刷页21，"
_GR3 = _P21 + "表11三级第1–4条（转述；具体时态、从句和语态不在表11分条，附录4大图未打开）"
J_PAGE_REF = {
    "stress": _P19 + "表9三级第3–4条（转述；未单列双音节、多音节重音位置）",
    "tone": _P19 + "表9三级第3–4条（转述；未把降调、升调按句类分开写）",
    "esound": _P19 + "表9三级第5条（转述；未单列名词复数和第三人称 -s、-es 的读音）",
    "edsound": _P19 + "表9三级第5条（转述；未单列过去式 -ed 的三种读音）",
    "link": _P19 + "表9三级（转述；连读不在表9分条，附录2大图未打开）",
    "plosion": _P19 + "表9三级（转述；不完全爆破不在表9分条）",
    "pause": _P19 + "表9三级第2条（转述；写的是按意群表达，未单列停顿规则）",
    "vocab7": _P20 + "表10三级第4–5条（转述；姓名、家庭等主题不在表10；三级约1600词见附录3）",
    "vocab8": _P20 + "表10三级第4–5条（转述；习惯、比较等主题不在表10）",
    "vocab9": _P20 + "表10三级第4–5条（转述；学习、节日等主题不在表10；印刷页21三级+是约1800加200，本条未改挂）",
}


def j_fields(symbol):
    if symbol in J_PAGE_REF:
        return J_PAGE_REF[symbol], J_STATUS
    row = next(r for r in STANDARD_ROWS if r[0] == symbol)
    if row[2] == "GR":
        return _GR3, J_STATUS
    return "待核", J_UNSEEN


def build_standards():
    counters = {}
    id_of = {}
    items = []
    for symbol, level, code, domain, section, text in STANDARD_ROWS:
        if domain != EN_CODES[code]:
            raise SystemExit("课标领域不一致：%s" % symbol)
        if level != "3":
            raise SystemExit("初中课标级别必须是 3：%s" % symbol)
        key = (level, code)
        counters[key] = counters.get(key, 0) + 1
        sid = "ces-2022:%s.%s.%02d" % (level, code, counters[key])
        id_of[symbol] = sid
        ref, status = j_fields(symbol)
        if ref != "待核" and ("人教社电子书印刷页" not in ref or "转述" not in ref):
            raise SystemExit("课标页码必须写明人教社电子书印刷页和转述：%s" % symbol)
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
    return id_of, items


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


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")
    if any(str(t.get("id", "")).startswith("cne_j") for t in topics):
        print("已经有 cne_j 知识点。enj_build.py 不能重复编译。", file=sys.stderr)
        return 1
    if not any(str(t.get("id", "")) == "cne_p001" for t in topics):
        print("缺少小学英语 cne_p001，不能单独编译初中。", file=sys.stderr)
        return 1
    if not (180 <= len(TOPICS) <= 260):
        print("知识点数量 %d 不在 180–260" % len(TOPICS), file=sys.stderr)
        return 1
    if TOPICS[0]["key"] != enj_topics.SPINE[0]:
        print("第一个知识点与主干不一致", file=sys.stderr)
        return 1

    id_of_std, new_items = build_standards()
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    by_key = {t["key"]: t for t in TOPICS}
    names = {t["key"]: t["name"] for t in TOPICS}
    primary_id = {"p:%s" % t["key"]: "cne_p%03d" % i for i, t in enumerate(PRIMARY_TOPICS, start=1)}
    if len(primary_id) != 197:
        print("小学英语数量不是 197", file=sys.stderr)
        return 1

    hard_pairs = {}
    resolved_hard = []
    for src, dst, reason in HARD:
        if src not in index:
            print("硬先修的后续未登记：%s" % src, file=sys.stderr)
            return 1
        if dst.startswith("p:"):
            if dst not in primary_id:
                print("硬先修指向未知的小学知识点：%s → %s" % (src, dst), file=sys.stderr)
                return 1
            pkey = dst[2:]
            pt = PRIMARY_BY_KEY[pkey]
            if rank(pt["grade"], pt["semester"]) > rank(by_key[src]["grade"], by_key[src]["semester"]):
                print("小学先修比初中更晚：%s 依赖 %s" % (src, pkey), file=sys.stderr)
                return 1
            pid = primary_id[dst]
        else:
            if dst not in index:
                print("硬先修指向未登记的知识点：%s → %s" % (src, dst), file=sys.stderr)
                return 1
            if index[dst] >= index[src]:
                print("硬先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            if rank(by_key[dst]["grade"], by_key[dst]["semester"]) > rank(by_key[src]["grade"], by_key[src]["semester"]):
                print("硬先修年级更晚：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            pid = None
        if (src, dst) in hard_pairs:
            print("重复硬边 %s → %s" % (src, dst), file=sys.stderr)
            return 1
        hard_pairs[(src, dst)] = reason
        resolved_hard.append((src, dst, pid, reason))

    for spec in TOPICS:
        if spec["std"] not in id_of_std:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        spec["note"] = NOTE[spec["domain"]]
        if (spec["grade"], spec["semester"], spec["unit"]) not in UNITS:
            print("%s 单元不存在：%s%s %s" % (spec["key"], spec["grade"], spec["semester"], spec["unit"]), file=sys.stderr)
            return 1
        if spec["grade"] not in (7, 8, 9):
            print("%s 年级不是 7–9" % spec["key"], file=sys.stderr)
            return 1
        if spec["grade"] == 9 and spec["semester"] != "全":
            print("%s 九年级必须是全一册" % spec["key"], file=sys.stderr)
            return 1
        if spec["grade"] != 9 and spec["semester"] not in ("上", "下"):
            print("%s 学期非法" % spec["key"], file=sys.stderr)
            return 1

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_j%03d" % i
        id_of[spec["key"]] = tid
        made = materialise_questions(spec)
        for q in made:
            check_question(spec["key"], q)
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
            "chapter": chapter(spec["grade"], spec["semester"], spec["unit"]),
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
        if (cur, prev) in hard_pairs:
            continue
        reason = "按 Go for it! 的常见教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
        raw.append((cur, prev, "soft", reason, id_of[prev]))
    for src, dst, pid, reason in resolved_hard:
        pre_id = pid if pid else id_of[dst]
        raw.append((src, dst, "hard", reason, pre_id))

    # 第一个初中点没有上一节课，必须另有指向小学的先修。
    if not any(src == TOPICS[0]["key"] for src, _, _, _, _ in raw):
        print("第一个初中知识点没有先修", file=sys.stderr)
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

    merged_deps, dropped = reduce_junior(deps + new_edges)
    jun_edges = [e for e in merged_deps if str(e["topicId"]).startswith("cne_j")]
    if any(not str(e["prerequisiteId"]).startswith("cne_") for e in jun_edges):
        print("初中英语边连到了数学知识点", file=sys.stderr)
        return 1
    if any(str(e["topicId"]).startswith("cne_j") for e in deps):
        print("原依赖里已有初中英语边", file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in jun_edges}
    missing = [t["id"] for t in new_topics if t["id"] not in covered]
    if missing:
        print("约简后仍无先修：%s" % "、".join(missing), file=sys.stderr)
        return 1
    cross = [e for e in jun_edges if str(e["prerequisiteId"]).startswith("cne_p")]
    if len(cross) < 8:
        print("跨到小学英语的边只有 %d 条" % len(cross), file=sys.stderr)
        return 1

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    n_hard = sum(1 for e in jun_edges if e["strength"] == "hard")
    n_soft = sum(1 for e in jun_edges if e["strength"] == "soft")
    n_cross_h = sum(1 for e in cross if e["strength"] == "hard")
    n_cross_s = sum(1 for e in cross if e["strength"] == "soft")
    by_grade = Counter("%d%s" % (t["grade"], t["semester"]) for t in new_topics)
    by_dom = Counter(t["domain"] for t in new_topics)
    print("初中英语知识点 %d" % len(new_topics))
    for k in ["7上", "7下", "8上", "8下", "9全"]:
        print("  %s %d" % (k, by_grade[k]))
    for k, v in by_dom.most_common():
        print("  %s %d" % (k, v))
    print("初中英语边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(jun_edges), dropped, n_hard, n_soft))
    print("其中跨到小学 %d（hard %d，soft %d）" % (len(cross), n_cross_h, n_cross_s))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(new_items))

    old_topic_n = len(topics)
    old_dep_n = len(deps)
    old_q_n = len(questions)
    old_std_n = len(standards["items"])
    old_ids = [(t["id"], t["name"]) for t in topics]
    eng = standards.get("english")
    if not isinstance(eng, dict):
        print("缺少 english 课标对象", file=sys.stderr)
        return 1
    eng["stage"] = "一级（3～4年级）、二级（5～6年级）与三级（7～9年级）"
    eng["note"] = (
        "2026-11-06 对照人教社电子书印刷页19–21（表9语音、表10词汇、表11语法）。"
        "一级至三级的语音、词汇、语法 page_or_ref 记这些印刷页，text 仍是转述，verbatim 为 false。"
        "日常表达和读写的大图未打开，page_or_ref 仍为「待核」。"
        "编号 ces-2022 是本图谱编的，不是教育部原编号。教材册次另见核对文档。"
    )
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
