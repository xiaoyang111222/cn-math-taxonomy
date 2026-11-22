# -*- coding: utf-8 -*-
"""初中历史数据的登记与题目生成。由 scripts/his_build.py 调用。

目录依据（公开目录，dzskb / dzkbw，未逐页核对纸质课本）：
- 七上：2024 秋修订统编《中国历史》七年级上册。
- 七下：2025 春修订统编《中国历史》七年级下册。
- 八上：2025 秋修订统编《中国历史》八年级上册。
- 八下：2026 春修订统编《中国历史》八年级下册。
- 九上：2026 秋修订统编《世界历史》九年级上册。
- 九下：修订版目录站未上线，按现行统编《世界历史》九年级下册（dzskb rjbls9xc），并改正「明治雏新」为「明治维新」。
"""

import re

TOPICS = []
HARD = []
# 补边：真实但与课序软边重叠、不会被传递约简保留的先修关系。编译时在约简之后写入，不参与约简。
EXTRA = []

# (年级, 学期, 单元) -> (单元名, 领域, 默认课标符号)
UNITS = {
    (7, "上", 1): ("史前时期：原始社会与中华文明的起源", "中国古代史", "ca_origin"),
    (7, "上", 2): ("夏商周时期：奴隶制王朝的更替和向封建社会的过渡", "中国古代史", "ca_xia"),
    (7, "上", 3): ("秦汉时期：统一多民族封建国家的建立和巩固", "中国古代史", "ca_qinhan"),
    (7, "上", 4): ("三国两晋南北朝时期：孕育统一和民族交融", "中国古代史", "ca_split"),
    (7, "下", 1): ("隋唐时期：繁荣与开放的时代", "中国古代史", "ca_sui"),
    (7, "下", 2): ("辽宋夏金元时期：民族关系发展和社会变化", "中国古代史", "ca_liao"),
    (7, "下", 3): ("明清时期（至鸦片战争前）：统一多民族封建国家的巩固与发展", "中国古代史", "ca_ming"),
    (8, "上", 1): ("中国开始沦为半殖民地半封建社会", "中国近代史", "cn_opium"),
    (8, "上", 2): ("早期现代化的初步探索和民族危机加剧", "中国近代史", "cn_opium"),
    (8, "上", 3): ("资产阶级民主革命与中华民国的建立", "中国近代史", "cn_republic"),
    (8, "上", 4): ("新民主主义革命的兴起", "中国近代史", "cn_republic"),
    (8, "上", 5): ("从国共合作到农村革命根据地的建立", "中国近代史", "cn_republic"),
    (8, "上", 6): ("中华民族的抗日战争", "中国近代史", "cn_war"),
    (8, "上", 7): ("人民解放战争", "中国近代史", "cn_war"),
    (8, "下", 1): ("中华人民共和国成立和社会主义制度建立", "中国现代史", "cm_found"),
    (8, "下", 2): ("社会主义建设道路的探索", "中国现代史", "cm_found"),
    (8, "下", 3): ("改革开放与中国特色社会主义的开创", "中国现代史", "cm_reform"),
    (8, "下", 4): ("中国特色社会主义迈向21世纪", "中国现代史", "cm_reform"),
    (8, "下", 5): ("在新形势下坚持和发展中国特色社会主义", "中国现代史", "cm_reform"),
    (8, "下", 6): ("中国特色社会主义进入新时代", "中国现代史", "cm_new"),
    (8, "下", 7): ("全面建设社会主义现代化国家", "中国现代史", "cm_new"),
    (9, "上", 1): ("文明的产生和古代亚非文明", "世界古代史", "wa_af"),
    (9, "上", 2): ("古代欧洲文明", "世界古代史", "wa_eu"),
    (9, "上", 3): ("封建时代的欧洲", "世界古代史", "wa_eu"),
    (9, "上", 4): ("中古时期的亚洲、非洲和美洲", "世界古代史", "wa_eu"),
    (9, "上", 5): ("走向近代", "世界近代史", "wn_dawn"),
    (9, "上", 6): ("资本主义制度的初步确立", "世界近代史", "wn_dawn"),
    (9, "上", 7): ("第一次工业革命和马克思主义的诞生", "世界近代史", "wn_dawn"),
    (9, "下", 1): ("殖民地人民的反抗与资本主义制度的扩展", "世界近代史", "wn_ind"),
    (9, "下", 2): ("第二次工业革命和近代科学文化", "世界近代史", "wn_ind"),
    (9, "下", 3): ("第一次世界大战和战后初期的世界", "世界现代史", "wm_war"),
    (9, "下", 4): ("经济大危机和第二次世界大战", "世界现代史", "wm_war"),
    (9, "下", 5): ("二战后的世界变化", "世界现代史", "wm_cold"),
    (9, "下", 6): ("走向和平发展的世界", "世界现代史", "wm_cold"),
}

DOMAINS = ("中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史")
CODE_OF = {
    "CA": "中国古代史", "CN": "中国近代史", "CM": "中国现代史",
    "WA": "世界古代史", "WN": "世界近代史", "WM": "世界现代史",
}

# 课标条目是《义务教育历史课程标准（2022年版）》内容要求的公开转述，不是逐页核对的原文。
STANDARD_ROWS = [
    ("ca_origin", "CA", "中华文明的起源", "通过考古发现和遗址，知道中国境内早期人类、原始农耕和中华文明起源的基本史实。"),
    ("ca_xia", "CA", "夏商周时期", "知道夏商周的更替、春秋战国的社会变革和百家争鸣。"),
    ("ca_qinhan", "CA", "秦汉时期", "知道秦汉统一多民族封建国家的建立和巩固，以及丝绸之路的开通。"),
    ("ca_split", "CA", "三国两晋南北朝", "知道三国两晋南北朝的政权更迭、江南开发、民族交融和科技文化。"),
    ("ca_sui", "CA", "隋唐时期", "知道隋朝统一与大运河、唐朝盛世与衰亡，以及民族交往和中外文化交流。"),
    ("ca_liao", "CA", "辽宋夏金元时期", "知道辽宋夏金元的并立、统一，以及这一时期经济文化和对外交流的基本史实。"),
    ("ca_ming", "CA", "明清时期（至鸦片战争前）", "知道明朝的统治与对外关系、清朝对边疆的治理和君主专制的强化，以及明清社会经济与科技文化。"),
    ("cn_opium", "CN", "列强侵华与早期探索", "知道鸦片战争至八国联军侵华的基本史实，以及洋务运动、戊戌变法等早期探索。"),
    ("cn_republic", "CN", "辛亥革命与新民主主义革命", "知道辛亥革命、五四运动、中国共产党诞生、国共合作、井冈山道路和长征的基本史实。"),
    ("cn_war", "CN", "抗日战争与解放战争", "知道九一八事变、西安事变、全民族抗战、解放战争和中华人民共和国成立前的基本史实。"),
    ("cm_found", "CM", "中华人民共和国成立与社会主义制度", "知道中华人民共和国成立、政权巩固、社会主义制度建立和早期外交的基本史实。"),
    ("cm_reform", "CM", "改革开放", "知道十一届三中全会、改革开放的进程和社会主义初级阶段基本路线。"),
    ("cm_new", "CM", "中国特色社会主义新时代", "知道中共十八大以来，中国特色社会主义进入新时代，党和人民面临的主要任务是，实现第一个百年奋斗目标，开启实现第二个百年奋斗目标新征程；了解习近平新时代中国特色社会主义思想；通过新时代中国在经济建设、政治建设、文化建设、社会建设、生态文明建设等领域取得的成就，以及综合国力和国际影响力不断提高的史事，特别是取得脱贫攻坚的伟大胜利、全面建成小康社会的史事，认识中国特色社会主义建设对中国社会发展的意义及对世界的贡献；认识中国共产党百年奋斗的历史意义和历史经验。"),
    ("wa_af", "WA", "古代亚非文明", "知道从原始社会到奴隶社会的变化，以及古代两河流域、埃及、印度文明的代表性史实。"),
    ("wa_eu", "WA", "古代欧洲与中古世界", "知道古代希腊罗马、西欧封建制度，以及中古时期亚洲、非洲和美洲的代表性史实。"),
    ("wn_dawn", "WN", "走向近代与资产阶级革命", "知道文艺复兴、新航路开辟、早期殖民掠夺，以及英、美、法资产阶级革命和第一次工业革命、马克思主义诞生的基本史实。"),
    ("wn_ind", "WN", "19世纪的世界", "知道殖民地人民的反抗、俄国农奴制改革、美国内战、明治维新，以及第二次工业革命和近代科学文化。"),
    ("wm_war", "WM", "两次世界大战与战后初期", "知道第一次世界大战、十月革命、凡尔赛—华盛顿体系、经济大危机和第二次世界大战的基本史实。"),
    ("wm_cold", "WM", "冷战与当代世界", "知道冷战、战后世界变化、联合国与世界贸易组织，以及用历史背景理解时事的基本方法。"),
]

TYPES = ("conceptual", "procedural", "reasoning", "application", "modeling")
CRIT = {
    "中国古代史": ["能说出本课的时间、人物或地点", "能判断与教材表述相符的史实"],
    "中国近代史": ["能说出本课的关键年代、条约或事件", "能把原因和结果对应到教材中的史实"],
    "中国现代史": ["能说出本课的关键年代和基本史实", "能把政策或事件与教材中的时间对应起来"],
    "世界古代史": ["能说出本课的文明、人物或制度", "能判断与教材表述相符的史实"],
    "世界近代史": ["能说出本课的关键年代、人物或文件", "能把事件与结果对应到教材中的史实"],
    "世界现代史": ["能说出本课的关键年代、组织或事件", "能判断与教材表述相符的史实"],
}
NOTE = "统编版该课的常见教学内容。条目是公开转述，不是逐页核对的原文。"

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


def extra(topic, prereq, strength, reason):
    EXTRA.append((topic, prereq, strength, reason))


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
