# -*- coding: utf-8 -*-
"""小学英语数据的登记与题目生成。由 scripts/en_build.py 调用。"""

import re

TOPICS = []
HARD = []

UNITS = {
    (3, "上", 1): "Hello",
    (3, "上", 2): "Colours",
    (3, "上", 3): "Look at me",
    (3, "上", 4): "We love animals",
    (3, "上", 5): "Let's eat",
    (3, "上", 6): "Happy birthday",
    (3, "下", 1): "Welcome back to school",
    (3, "下", 2): "My family",
    (3, "下", 3): "At the zoo",
    (3, "下", 4): "Where is my car",
    (3, "下", 5): "Do you like pears",
    (3, "下", 6): "How many",
    (4, "上", 1): "Helping at home",
    (4, "上", 2): "My friends",
    (4, "上", 3): "Places we live in",
    (4, "上", 4): "Helping in the community",
    (4, "上", 5): "The weather and us",
    (4, "上", 6): "Changing for the seasons",
    (4, "下", 1): "Class rules",
    (4, "下", 2): "Family rules",
    (4, "下", 3): "Time for school",
    (4, "下", 4): "Going shopping",
    (4, "下", 5): "Farms and us",
    (4, "下", 6): "On the farm",
    (5, "上", 1): "What's he like",
    (5, "上", 2): "My week",
    (5, "上", 3): "What would you like",
    (5, "上", 4): "What can you do",
    (5, "上", 5): "There is a big bed",
    (5, "上", 6): "In a nature park",
    (5, "下", 1): "My day",
    (5, "下", 2): "My favourite season",
    (5, "下", 3): "My school calendar",
    (5, "下", 4): "When is the art show",
    (5, "下", 5): "Whose dog is it",
    (5, "下", 6): "Work quietly",
    (6, "上", 1): "Amazing places",
    (6, "上", 2): "Getting together",
    (6, "上", 3): "Healthy life",
    (6, "上", 4): "Managing money well",
    (6, "上", 5): "Exploring space",
    (6, "上", 6): "Energy, nature and us",
    (6, "下", 1): "How tall are you",
    (6, "下", 2): "Last weekend",
    (6, "下", 3): "Where did you go",
    (6, "下", 4): "Then and now",
}

# 课标条目是公开介绍的转述，不是逐页核对的原文。symbolic 名在本文件内使用。
STANDARD_ROWS = [
    ("letters", "1", "PH", "语音", "一级 · 语音",
     "能按顺序认读英语字母表中的 26 个字母，并能区分同一个字母的大写和小写。"),
    ("vowel_letter", "1", "PH", "语音", "一级 · 语音",
     "能区分元音字母 a、e、i、o、u 和常见辅音字母。"),
    ("short_vowel", "1", "PH", "语音", "一级 · 语音",
     "能感知元音字母在重读闭音节中的常见短元音，并用来拼读简单单词。"),
    ("consonant", "1", "PH", "语音", "一级 · 语音",
     "能把常见辅音字母和它在单词开头的读音初步对应起来。"),
    ("magic_e", "1", "PH", "语音", "一级 · 语音",
     "能感知元音字母在开音节中的常见读音，如 a-e、i-e、o-e、u-e。"),
    ("blend", "2", "PH", "语音", "二级 · 语音",
     "能根据已学字母组合和常见开头辅音连缀拼读单词。"),
    ("tone", "2", "PH", "语音", "二级 · 语音",
     "能在朗读中注意句子重音，并区分陈述句和一般疑问句的基本语调。"),
    ("vocab34", "1", "VO", "词汇", "一级 · 词汇",
     "能在图片和简短语境中认读与问候、颜色、身体、动物、食物、学校、家庭等主题有关的核心单词。一级词表的具体词目以课标附录为准，本条为转述。"),
    ("vocab56", "2", "VO", "词汇", "二级 · 词汇",
     "能在语境中理解并运用与星期、月份、季节、运动、场所、交通、职业、情绪和计划有关的词汇。二级词表以课标附录为准，本条为转述。"),
    ("confuse", "2", "VO", "词汇", "二级 · 词汇",
     "能在句子中区分部分易混词的意义和用法，如 there 与 their、its 与 it's、too 与 two。"),
    ("be", "1", "GR", "语法", "一级 · 语法",
     "能在句子中运用 am、is、are，构成简单的肯定句，并与 I、you、he、she、it、they 搭配。"),
    ("plural", "1", "GR", "语法", "一级 · 语法",
     "能识别可数名词的单数和复数，并正确使用词尾 -s 或 -es 的常见形式。"),
    ("pronoun", "1", "GR", "语法", "一级 · 语法",
     "能在句子中运用人称代词主格和常见形容词性物主代词，如 I、you、he、she、my、your、his、her。"),
    ("pointer", "1", "GR", "语法", "一级 · 语法",
     "能运用 this、that、these、those 以及方位介词 in、on、under 表示近指、远指和位置。"),
    ("present_basic", "1", "GR", "语法", "一级 · 语法",
     "能用一般现在时的常见句式表达喜好和拥有，如 I like、Do you like、He has。"),
    ("number_q", "1", "GR", "语法", "一级 · 语法",
     "能运用基数词，并用 How many、How old、What time、How much 询问数量、年龄、时刻和价格。"),
    ("lets", "1", "GR", "语法", "一级 · 语法",
     "能理解 Let's 开头的建议句，以及 whose 和名词所有格 's 询问、说明物品属于谁。"),
    ("present3", "2", "GR", "语法", "二级 · 语法",
     "能运用一般现在时描述习惯，包括第三人称单数的动词形式，以及 do、does 引导的疑问句。"),
    ("continuous", "2", "GR", "语法", "二级 · 语法",
     "能运用现在进行时描述正在发生的动作，结构是 am、is、are 加动词的 -ing 形式。"),
    ("can_there", "2", "GR", "语法", "二级 · 语法",
     "能运用 can 谈论能力，并用 There is、There are 及其疑问形式描述某处有什么。"),
    ("when_ord", "2", "GR", "语法", "二级 · 语法",
     "能运用频度副词、序数词和 in、on、at 表达作息、日期和月份。"),
    ("poss_pron", "2", "GR", "语法", "二级 · 语法",
     "能运用名词性物主代词 mine、yours、his、hers、ours、theirs 说明物品属于谁。"),
    ("future", "2", "GR", "语法", "二级 · 语法",
     "能运用 be going to 表达打算或将要做的事。"),
    ("modal_imp", "2", "GR", "语法", "二级 · 语法",
     "能运用祈使句以及 should、must 提出建议或说明规则。"),
    ("past", "2", "GR", "语法", "二级 · 语法",
     "能运用一般过去时谈论已经发生的事情，包括规则动词 -ed 和常见不规则动词。"),
    ("compare", "2", "GR", "语法", "二级 · 语法",
     "能运用形容词比较级，并用 than 对两者进行比较。"),
    ("func_greet", "1", "FU", "日常表达", "一级 · 日常表达",
     "能用简单英语问候、告别、致谢，并介绍自己的姓名、年龄和来自哪里。"),
    ("func_daily", "1", "FU", "日常表达", "一级 · 日常表达",
     "能用简单句型询问和表达颜色、位置、喜好、家庭、时间和价格。"),
    ("func_place", "1", "FU", "日常表达", "一级 · 日常表达",
     "能在学校、家里、餐桌和商店等情境中使用常见功能句。"),
    ("func_life", "2", "FU", "日常表达", "二级 · 日常表达",
     "能询问和说明课程、作息、日期、季节、能力和正在做的事情。"),
    ("func_out", "2", "FU", "日常表达", "二级 · 日常表达",
     "能问路指路、说明出行方式、谈论计划和感受，并给出简单建议。"),
    ("read_pic", "1", "RW", "读写", "一级 · 读写",
     "能借助文字描述的图片信息认读单词和句子，并选出与图意相符的一句英文。"),
    ("read_short", "1", "RW", "读写", "一级 · 读写",
     "能读懂配有明确信息的简短对话或短文，找出人物、颜色、数量或位置。"),
    ("read_text", "2", "RW", "读写", "二级 · 读写",
     "能读懂与教材话题有关的简短日记、通知或信件，抓住时间、地点、人物和事件。"),
    ("read_write", "2", "RW", "读写", "二级 · 读写",
     "能根据提示选择意思连贯的英文句子，描述人物、计划或过去的一天。"),
]

# 2026-11-06 对照人教社电子书印刷页。文件页 N 的页脚是 N-7：
# files/large/26.jpg = 印刷页 19 表9，27.jpg = 印刷页 20 表10，28.jpg = 印刷页 21 表11。
# https://www.pep.com.cn/ebook/2022yjkcbz/yy/mobile/index.html
# 日常表达、读写对应的语用表和语言技能表大图没有打开，仍是「待核」。
YY_STATUS = (
    "2026-11-06 对照人教社电子书《义务教育英语课程标准（2022年版）》印刷页，"
    "text 仍是转述，不是表内逐字原文"
)
YY_UNSEEN = (
    "2026-11-06 已打开表9–11（印刷页19–21）；语用知识和语言技能表的大图未打开，本条仍待核"
)
_P19 = "人教社电子书印刷页19，"
_P20 = "人教社电子书印刷页20，"
_P21 = "人教社电子书印刷页21，"
PAGE_REF = {
    "letters": _P19 + "表9一级第1条（转述；课标写识别并读出26个大、小写字母，未写按顺序认读）",
    "vowel_letter": _P19 + "表9一级第2条（转述；未单列 a、e、i、o、u）",
    "short_vowel": _P19 + "表9一级第3条（转述；未单列重读闭音节短元音）",
    "consonant": _P19 + "表9一级第2–3条（转述；未单列词首辅音）",
    "magic_e": _P19 + "表9一级第3条（转述；开音节和 a-e 等不在表9，附录2大图未打开）",
    "blend": _P19 + "表9二级第1条（转述；未单列辅音连缀）",
    "tone": _P19 + "表9一级第4条及二级第3–4条（转述；未把陈述句和一般疑问句的语调分开写）",
    "vocab34": _P20 + "表10一级第2条（转述；问候、颜色等主题词不在表10，附录3未逐条核对）",
    "vocab56": _P20 + "表10二级第1–3条（转述；星期、月份等主题不在表10；二级是约500个单词，见附录3）",
    "confuse": _P20 + "表10二级（转述；there 与 their 等易混词不在表10）",
    "be": _P21 + "表11一级第1–2条（转述；未单列 am、is、are）",
    "plural": _P21 + "表11一级（转述；名词复数不在表11分条，附录4大图未打开）",
    "pronoun": _P21 + "表11一级（转述；人称代词和物主代词不在表11分条）",
    "pointer": _P21 + "表11一级（转述；this、that 和方位介词不在表11分条）",
    "present_basic": _P21 + "表11一级第2条（转述；未单列 I like、Do you like、He has）",
    "number_q": _P21 + "表11一级（转述；How many 等不在表11分条）",
    "lets": _P21 + "表11一级第1条（转述；Let's 和 whose 不在表11分条）",
    "present3": _P21 + "表11一级第2条（转述；库存标成二级，表11把一般现在时写在一级，未单列第三人称和 does）",
    "continuous": _P21 + "表11一级第2条（转述；库存标成二级，表11把现在进行时写在一级，未写 be 加 -ing）",
    "can_there": _P21 + "表11二级第1、3条（转述；can 和 There be 不在表11分条）",
    "when_ord": _P21 + "表11二级第3条（转述；频度副词、序数词和 in、on、at 不在表11分条）",
    "poss_pron": _P21 + "表11二级（转述；名词性物主代词不在表11分条）",
    "future": _P21 + "表11二级第2条（转述；只写一般将来时，未单列 be going to）",
    "modal_imp": _P21 + "表11二级第1条（转述；祈使句、should、must 不在表11分条）",
    "past": _P21 + "表11二级第2条（转述；未单列 -ed 和不规则动词）",
    "compare": _P21 + "表11二级第3条（转述；比较级和 than 不在表11分条）",
}


def yy_fields(symbol):
    if symbol not in PAGE_REF:
        return "待核", YY_UNSEEN
    return PAGE_REF[symbol], YY_STATUS


NOTE_VOCAB = "人教 PEP 该单元的主题词。课标不逐词列出，词表和册次待核。"
NOTE_FUNC = "教材中的功能句。课标没有逐句列出，待核。"
NOTE_READ = "用文字把图意或短文写进题干，考查认读和理解。册次待核。"
NOTE_PH = "拼读项目按三年级起点常见 Let's spell 编排，册次待核。"
NOTE_GR = "句型按人教 PEP 三年级起点的常见出现顺序挂到语法条目，册次待核。"


def chapter(grade, sem, unit):
    cn = "零一二三四五六"[grade]
    title = UNITS[(grade, sem, unit)]
    return "%s年级%s册 第%d单元 %s" % (cn, sem, unit, title)


def _add(spec):
    if any(t["key"] == spec["key"] for t in TOPICS):
        raise SystemExit("知识点 key 重复：%s" % spec["key"])
    TOPICS.append(spec)


def vocab(key, name, grade, sem, unit, desc, criteria, words, std):
    _add({
        "key": key, "name": name, "domain": "词汇", "grade": grade, "semester": sem,
        "unit": unit, "type": "conceptual", "description": desc,
        "mastery_criteria": criteria, "std": std, "conf": "inferred", "note": NOTE_VOCAB,
        "gen": "vocab", "words": words,
    })


def sound(key, name, grade, sem, unit, desc, criteria, std, sound_name, goods, bads, mode="vowel"):
    _add({
        "key": key, "name": name, "domain": "语音", "grade": grade, "semester": sem,
        "unit": unit, "type": "procedural", "description": desc,
        "mastery_criteria": criteria, "std": std, "conf": "inferred", "note": NOTE_PH,
        "gen": "sound", "sound": sound_name, "goods": goods, "bads": bads, "mode": mode,
    })


def four(key, name, domain, grade, sem, unit, typ, desc, criteria, std, items, conf="inferred", note=None):
    if note is None:
        note = {"语音": NOTE_PH, "词汇": NOTE_VOCAB, "语法": NOTE_GR, "日常表达": NOTE_FUNC, "读写": NOTE_READ}.get(domain, NOTE_GR)
    if conf == "exact":
        note = None
    _add({
        "key": key, "name": name, "domain": domain, "grade": grade, "semester": sem,
        "unit": unit, "type": typ, "description": desc,
        "mastery_criteria": criteria, "std": std, "conf": conf, "note": note,
        "gen": "custom", "items": items,
    })


def C(prompt, answer, wrongs, expl):
    wrongs = list(wrongs)
    if len(wrongs) != 3:
        raise SystemExit("选项干扰项必须是 3 个：%s" % prompt[:40])
    return ("choice", prompt, answer, wrongs, expl)


def N(prompt, answer, expl):
    return ("numeric", prompt, str(answer), expl)


def hard(topic, prereq, reason):
    HARD.append((topic, prereq, reason))


def gen_vocab(spec):
    words = spec["words"]
    if len(words) < 4:
        raise SystemExit("%s 至少要 4 个词" % spec["key"])
    ens = [w[0] for w in words]
    zhs = [w[1] for w in words]
    if len(set(ens)) != len(ens) or len(set(zhs)) != len(zhs):
        raise SystemExit("%s 词条重复" % spec["key"])

    def others(pool, i):
        return [pool[j] for j in range(len(pool)) if j != i][:3]

    return [
        C("哪个单词的意思是「%s」？" % zhs[0], ens[0], others(ens, 0), "%s 的意思是%s。" % (ens[0], zhs[0])),
        C("「%s」的中文意思是哪一个？" % ens[1], zhs[1], others(zhs, 1), "%s 的意思是%s。" % (ens[1], zhs[1])),
        C("选择表示「%s」的单词。" % zhs[2], ens[2], others(ens, 2), "表示%s的单词是 %s。" % (zhs[2], ens[2])),
        C("哪个单词的意思是「%s」？" % zhs[3], ens[3], others(ens, 3), "%s 的意思是%s。" % (ens[3], zhs[3])),
    ]


def gen_sound(spec):
    goods, bads = spec["goods"], spec["bads"]
    sound = spec["sound"]
    if len(goods) < 4 or len(bads) < 4:
        raise SystemExit("%s 正例和反例都至少要 4 个" % spec["key"])
    if len(set(goods)) != len(goods) or len(set(bads)) != len(bads) or set(goods) & set(bads):
        raise SystemExit("%s 正例和反例必须各不相同" % spec["key"])
    if spec["mode"] == "start":
        same = "%s 和哪个词的开头音相同？" % goods[1]
        why = "%s 和 %s 的开头都是%s。" % (goods[1], goods[2], sound)
    else:
        same = "%s 和哪个词的元音相同？" % goods[1]
        why = "%s 和 %s 都含有%s。" % (goods[1], goods[2], sound)
    return [
        C("哪个单词含有%s？" % sound, goods[0], bads[:3], "%s 含有%s。" % (goods[0], sound)),
        C("哪个单词不含%s？" % sound, bads[0], goods[:3], "%s 不含%s。" % (bads[0], sound)),
        C(same, goods[2], bads[:3], why),
        C("选择含有%s的单词。" % sound, goods[3], bads[1:4], "%s 含有%s。" % (goods[3], sound)),
    ]


def gen_custom(spec):
    items = spec["items"]
    if len(items) != 4:
        raise SystemExit("%s 需要恰好 4 题" % spec["key"])
    diffs = ["basic", "basic", "standard", "standard"]
    out = []
    for diff, item in zip(diffs, items):
        if item[0] == "choice":
            out.append((diff,) + item)
        elif item[0] == "numeric":
            out.append((diff,) + item)
        else:
            raise SystemExit("%s 题型无法识别" % spec["key"])
    return out


def materialise_questions(spec):
    if spec["gen"] == "vocab":
        raw = gen_vocab(spec)
    elif spec["gen"] == "sound":
        raw = gen_sound(spec)
    else:
        raw = gen_custom(spec)
    diffs = ["basic", "basic", "standard", "standard"]
    made = []
    for i, item in enumerate(raw):
        # gen_vocab/sound 返回的 C() 没有 difficulty；gen_custom 已带 difficulty
        if item[0] in ("basic", "standard", "advanced"):
            diff, kind = item[0], item[1]
            rest = item[2:]
        else:
            diff, kind, rest = diffs[i], item[0], item[1:]
        if kind == "choice":
            prompt, answer, wrongs, expl = rest
            made.append({"d": diff, "t": "choice", "p": prompt, "a": answer, "w": list(wrongs), "e": expl})
        else:
            prompt, answer, expl = rest
            made.append({"d": diff, "t": "numeric", "p": prompt, "a": str(answer), "e": expl, "v": str(answer)})
    if len(made) != 4:
        raise SystemExit("%s 生成了 %d 题" % (spec["key"], len(made)))
    return made


_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED_META = re.compile(r"本知识点|课标|是否要求")
_BAD_CORRECT = (
    " a apple", " a elephant", " a orange", " a ice", " a umbrella", " a hour",
    "He are", "He am", "She are", "She am", "It are", "It am", "I is", "I are",
    "They is", "more bigger", "more taller", "more big", "gooses", "childs",
    "teached", "buyed", "goed", "eated", "comed",
)


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
        raise SystemExit("%s 出现课标元问题用语" % key)
    if q["t"] == "choice":
        opts = [q["a"]] + list(q["w"])
        if len(opts) != 4:
            raise SystemExit("%s 选项不是 4 个" % key)
        if len(set(opts)) != 4:
            raise SystemExit("%s 选项重复：%s" % (key, opts))
        if len(set(norm_opt(o) for o in opts)) != 4:
            raise SystemExit("%s 选项规范化后重复：%s" % (key, opts))
        for o in opts:
            if re.fullmatch(r"[A-Za-z]", o.strip()):
                raise SystemExit("%s 选项不能是单个字母：%s" % (key, o))
        for bad in _BAD_CORRECT:
            if bad in q["a"] or bad in prompt:
                raise SystemExit("%s 正确文本疑似病句：%s" % (key, bad))
    if not str(q["e"]).strip():
        raise SystemExit("%s 缺少解析" % key)
