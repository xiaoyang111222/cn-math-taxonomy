# -*- coding: utf-8 -*-
"""把一条课文记录收成课序行和 4 道客观选择题。各册数据文件只调用 P。"""
from __future__ import annotations

import re

_BANNED_START = re.compile(r"^(同一|上题|该题|同上)")
_BANNED = re.compile(r"本知识点|课标|是否要求|你认为|是否应该|谁之过|是否必要|免费|AI\s*初稿")

AUTHORS = [
    "屈原", "杜甫", "苏轼", "鲁迅", "毛泽东", "陶渊明", "李白", "曹雪芹",
    "莎士比亚", "司马迁", "白居易", "辛弃疾", "李清照", "关汉卿", "曹禺",
    "契诃夫", "贾谊", "欧阳修", "艾青", "徐志摩", "老舍", "沈从文", "海明威",
    "屠呦呦", "韩愈", "姚鼐", "李煜", "秦观", "王安石", "张孝祥", "汤显祖",
    "高适", "李贺", "李商隐", "陆游", "柳永", "姜夔", "鲍照", "黄庭坚",
    "王羲之", "柳宗元", "归有光", "李密", "班固", "易卜生", "歌德", "普希金",
    "惠特曼", "孙犁", "赵树理", "夏衍", "贾平凹", "冯至", "闻一多", "郭沫若",
    "铁凝", "郁达夫", "朱自清", "史铁生", "蒲松龄", "施耐庵", "林觉民", "魏征",
    "杜牧", "苏洵", "梁思成", "林庚", "狄更斯", "加西亚·马尔克斯",
]
BOOK_POOL = ["《乡土中国》", "《红楼梦》", "《包身工》", "《茶馆》", "《琵琶行并序》", "《离骚》", "《劝学》", "《祝福》"]
SOURCE_POOL = ["《楚辞》", "《史记》", "《左传》", "《庄子》", "《乐府诗集》", "《世说新语》", "《孟子》", "《战国策》"]
GENRE_WRONG = {
    "诗": ["宋词", "元杂剧", "新闻通讯"],
    "词": ["七言律诗", "文言传记", "新闻通讯"],
    "文言文": ["现代新诗", "新闻通讯", "外国小说"],
    "现代新诗": ["宋词", "文言传记", "元杂剧"],
    "现代散文": ["七言律诗", "元杂剧", "新闻通讯"],
    "现代小说": ["宋词", "文言传记", "科学说明文"],
    "古典小说": ["宋词", "新闻通讯", "实验报告"],
    "新闻通讯": ["宋词", "元杂剧", "楚辞"],
    "议论性文章": ["七言律诗", "元杂剧", "实验报告"],
    "戏剧": ["宋词", "七言律诗", "实验报告"],
    "学术说明文": ["宋词", "元杂剧", "武侠小说"],
    "外国小说": ["宋词", "乐府诗", "新闻通讯"],
    "外国诗歌": ["元杂剧", "新闻通讯", "文言传记"],
    "乐府诗": ["宋词", "新闻通讯", "实验报告"],
    "楚辞": ["元杂剧", "新闻通讯", "现代话剧"],
    "科学说明文": ["宋词", "元杂剧", "武侠小说"],
}

STD = {
    (10, "阅读理解"): "B1.01",
    (10, "古诗文积累"): "B1.02",
    (10, "文言文阅读"): "B1.03",
    (10, "名著阅读"): "B1.04",
    (10, "习作基础"): "B1.05",
    (10, "词语"): "B1.06",
    (11, "文言文阅读"): "B2.01",
    (11, "阅读理解"): "B2.02",
    (11, "古诗文积累"): "B2.03",
    (11, "名著阅读"): "B2.04",
    (12, "阅读理解"): "S1.01",
    (12, "文言文阅读"): "S1.02",
    (12, "句子"): "S1.03",
    (12, "古诗文积累"): "S1.04",
    (13, "阅读理解"): "S2.01",
    (13, "文言文阅读"): "S2.02",
    (13, "古诗文积累"): "S2.03",
    (14, "古诗文积累"): "S3.01",
    (14, "阅读理解"): "S3.02",
    (14, "文言文阅读"): "S3.03",
}

ROWS = []


def _book(title):
    return title if "《" in title else "《%s》" % title


def _rotate(pool, salt):
    if not pool:
        raise SystemExit("空的干扰项池")
    start = sum(ord(ch) for ch in salt) % len(pool)
    return pool[start:] + pool[:start]


def _wrongs(right, pool, salt, n=3):
    out = []
    for item in _rotate(pool, salt):
        if not item or item == right:
            continue
        if item in right or right in item:
            continue
        if item in out:
            continue
        out.append(item)
        if len(out) == n:
            return out
    raise SystemExit("干扰项不够：%s / %s" % (right, salt))


def _check(key, prompt, right, wrongs, expl):
    blob = "\n".join([prompt, right, expl] + list(wrongs))
    if _BANNED_START.match(prompt):
        raise SystemExit("%s 题干以禁用词开头" % key)
    if _BANNED.search(blob):
        raise SystemExit("%s 出现禁用用语：%s" % (key, prompt[:24]))
    if "<" in blob or ">" in blob:
        raise SystemExit("%s 题面里有尖括号" % key)
    opts = [right] + list(wrongs)
    if len(wrongs) != 3 or len(set(re.sub(r"\s+", "", o) for o in opts)) != 4 or not all(opts):
        raise SystemExit("%s 选项重复或为空：%s" % (key, opts))
    if not expl.strip():
        raise SystemExit("%s 缺少解析" % key)


def _q(key, prompt, right, wrongs, expl):
    _check(key, prompt, right, wrongs, expl)
    return (prompt, right, list(wrongs), expl)


def _as_q(key, item):
    """书稿里单题写成 (题干, 正确项, 干扰1, 干扰2, 干扰3, 解析)，整组 qs 写成四元组。"""
    if len(item) == 4 and isinstance(item[2], (list, tuple)):
        return _q(key, item[0], item[1], item[2], item[3])
    if len(item) == 6:
        prompt, right, w1, w2, w3, expl = item
        return _q(key, prompt, right, [w1, w2, w3], expl)
    raise SystemExit("%s 题目格式不对" % key)


def P(key, grade, tail, domain, name, title, author, genre, quote="", trap=None,
      pre=(), selfread=False, source=False, extra="", q1=None, q2=None, q3=None, qs=None):
    """trap 是 (正确说法, 干扰1, 干扰2, 干扰3, 解析)。quote 为空时必须自带 q3 或整组 qs。"""
    if (grade, domain) not in STD:
        raise SystemExit("%s 没有课标对照：%s %s" % (key, grade, domain))
    shown = _book(title)
    if qs is None:
        if q1 is None:
            if source:
                q1 = _q(key, "%s的出处是？" % shown, author,
                        _wrongs(author, SOURCE_POOL, key),
                        "%s出自%s。" % (shown, author))
            else:
                q1 = _q(key, "%s的作者是？" % shown, author,
                        _wrongs(author, AUTHORS, key + "a"),
                        "%s的作者是%s。" % (shown, author))
        else:
            q1 = _as_q(key, q1)
        if q2 is None:
            if genre not in GENRE_WRONG:
                raise SystemExit("%s 未知文体：%s" % (key, genre))
            q2 = _q(key, "从文体看，%s属于哪一类？" % shown, genre, GENRE_WRONG[genre],
                    "%s在教材里按%s来读。" % (shown, genre))
        else:
            q2 = _as_q(key, q2)
        if q3 is None:
            if not quote:
                raise SystemExit("%s 没有名句，也没有单独的第三题" % key)
            q3 = _q(key, "“%s”出自哪一篇？" % quote, shown,
                    _wrongs(shown, BOOK_POOL, key + "q"),
                    "“%s”出自%s。" % (quote, shown))
        else:
            q3 = _as_q(key, q3)
        if trap is None:
            raise SystemExit("%s 缺少第四题" % key)
        true, w1, w2, w3, expl = trap
        q4 = _q(key, "下列关于%s的说法，哪一项正确？" % shown, true, [w1, w2, w3], expl)
        qs = [q1, q2, q3, q4]
    else:
        if len(qs) != 4:
            raise SystemExit("%s 需要 4 题" % key)
        qs = [_as_q(key, item) for item in qs]
    parts = []
    if selfread:
        parts.append("目录标为自读。")
    if author:
        if source:
            parts.append("%s出自%s，文体归入%s。" % (shown, author, genre))
        else:
            parts.append("%s的作者是%s，文体归入%s。" % (shown, author, genre))
    else:
        parts.append("%s在教材里归入%s。" % (shown, genre))
    if quote:
        parts.append("课文里有“%s”。" % quote)
    if extra:
        parts.append(extra)
    desc = "".join(parts)
    if "<" in desc or _BANNED.search(desc):
        raise SystemExit("%s 讲解不合规则" % key)
    ROWS.append({
        "key": key, "grade": grade, "tail": tail, "domain": domain, "name": name,
        "std": STD[(grade, domain)], "desc": desc,
        "mastery": ["能说出%s的作者、出处和文体" % shown, "能判断名句、实词或目录里写明的事实"],
        "pre": list(pre), "qs": qs,
    })
