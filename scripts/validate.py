#!/usr/bin/env python3
"""校验 data/topics.json 与 data/dependencies.json（仅使用标准库）。

用法：python3 scripts/validate.py
全部通过时打印 "VALIDATION PASSED" 并以退出码 0 结束，否则退出码为 1。

课标对齐（data/cn-curriculum-standards.json）：
- 文件存在时，topic.standards[].id 必须出现在其 items[].id 中，confidence 只能是 exact / inferred；
- 正式知识点 standards 为空只打印 WARNING（至多列 30 个），不影响退出码；
  设置环境变量 STRICT_STANDARDS=1 时，此类空 standards 视为错误。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_figures import question_figure_problems  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_PATH = os.path.join(ROOT, "data", "topics.json")
DEPS_PATH = os.path.join(ROOT, "data", "dependencies.json")
STANDARDS_PATH = os.path.join(ROOT, "data", "cn-curriculum-standards.json")
QUESTIONS_PATH = os.path.join(ROOT, "data", "questions.json")
STRICT_STANDARDS = os.environ.get("STRICT_STANDARDS") == "1"

MATH_DOMAINS = {"数与代数", "图形与几何", "统计与概率", "综合与实践"}
EN_DOMAINS = {"语音", "词汇", "语法", "日常表达", "读写"}
ZH_DOMAINS = {"拼音", "识字写字", "词语", "句子", "阅读理解", "古诗文积累", "习作基础"}
SCI_DOMAINS = {"物质科学", "生命科学", "地球与宇宙科学", "技术与工程"}
MOR_DOMAINS = {"生活与安全", "学校生活", "家庭与亲情", "社会规则", "公民与国家", "自然与环境"}
HIS_DOMAINS = {"中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史"}
# 物理知识点的 domain 用课标一级主题；“实验探究”只出现在课标条目上。
PHY_DOMAINS = {"物质", "运动和相互作用", "能量", "跨学科实践"}
PHY_STD_TOPS = {"1": "物质", "2": "运动和相互作用", "3": "能量", "4": "实验探究", "5": "跨学科实践"}
PHY_STD_ID_RE = re.compile(r"^cps-2022:([1-5])\.(\d)\.(\d+)$")
# 高中物理课标：cps-hs-2017:<B 必修|S 选择性必修><册号 1-3>.<主题 1-4 或 X 学生必做实验>.<序号>
PHY_HS_STD_ID_RE = re.compile(r"^cps-hs-2017:([BS])([1-3])\.([1-4X])\.(\d+)$")
PHY_HS_STD_DOMAINS = {"物质", "运动和相互作用", "能量", "实验探究", "跨学科实践"}
PHY_SENIOR_GRADES = (10, 11, 12, 13, 14, 15)
DOMAINS = MATH_DOMAINS | EN_DOMAINS | PHY_DOMAINS | ZH_DOMAINS | SCI_DOMAINS | MOR_DOMAINS | HIS_DOMAINS
TYPES = {"conceptual", "procedural", "reasoning", "application", "modeling"}
STRENGTHS = {"hard", "soft"}
CONFIDENCES = {"exact", "inferred"}
MAX_STANDARDS_PER_TOPIC = 3
MAX_WARNINGS_LISTED = 30
STD_DOMAIN_CODES = {"NA": "数与代数", "GG": "图形与几何", "SP": "统计与概率", "IP": "综合与实践"}
STD_ID_RE = re.compile(r"^cms-2022:([1-4])\.(NA|GG|SP|IP)\.(\d{2,})$")
# 高中必修：cms-2017:H.<模块>.NN。模块不是领域代码（几何与代数横跨数与代数和图形与几何）。
HS_STD_ID_RE = re.compile(r"^cms-2017:H\.(PRE|FUN|GA|PS|MI)\.(\d{2,})$")
HS_STD_MODULES = ("PRE", "FUN", "GA", "PS", "MI")
EN_STD_CODES = {"PH": "语音", "VO": "词汇", "GR": "语法", "FU": "日常表达", "RW": "读写"}
EN_STD_ID_RE = re.compile(r"^ces-2022:([123])\.(PH|VO|GR|FU|RW)\.(\d{2,})$")
# 高中英语：ces-2017:H.B 必修，ces-2017:H.S 选择性必修。编号是本图谱编的。
EN_HS_STD_ID_RE = re.compile(r"^ces-2017:H\.(B|S)\.(PH|VO|GR|FU|RW)\.(\d{2,})$")
# 小学语文：ccs-2022:<学段 1–3>.<PY|SZ|CY|JZ|YD|GS|XZ>.<NN>。编号是本图谱编的。
ZH_STD_CODES = {
    "PY": "拼音", "SZ": "识字写字", "CY": "词语", "JZ": "句子",
    "YD": "阅读理解", "GS": "古诗文积累", "XZ": "习作基础",
}
SCI_STD_CODES = {"WZ": "物质科学", "SM": "生命科学", "DQ": "地球与宇宙科学", "JG": "技术与工程"}
SCI_STD_ID_RE = re.compile(r"^css-2022:([123])\.(WZ|SM|DQ|JG)\.(\d{2,})$")
MOR_STD_CODES = {"LS": "生活与安全", "XX": "学校生活", "JT": "家庭与亲情", "SH": "社会规则", "GM": "公民与国家", "ZR": "自然与环境"}
MOR_STD_ID_RE = re.compile(r"^cds-2022:([123])\.(LS|XX|JT|SH|GM|ZR)\.(\d{2,})$")
HIS_STD_CODES = {
    "CA": "中国古代史", "CN": "中国近代史", "CM": "中国现代史",
    "WA": "世界古代史", "WN": "世界近代史", "WM": "世界现代史",
}
HIS_STD_ID_RE = re.compile(r"^chs-2022:(CA|CN|CM|WA|WN|WM)\.(\d{2,})$")
ZH_STD_ID_RE = re.compile(r"^ccs-2022:([123])\.(PY|SZ|CY|JZ|YD|GS|XZ)\.(\d{2,})$")
EN_PROMPT_START_RE = re.compile(r"^(同一|上题|该题|同上)")
EN_PROMPT_BAN_RE = re.compile(r"本知识点|课标|是否要求")
CORE_FIELDS = ["id", "name", "domain", "grade", "semester", "chapter", "type",
               "description", "mastery_criteria", "diagnostic_question", "external"]
EXT_FIELDS = ["id", "name", "domain", "grade", "description", "external"]
# cnm_001 初中正式；cnm_p001 小学正式；cnm_h001 高中正式。cne_p001 小学英语，cne_j001 初中英语，cne_h001 高中英语。
# cnp_001 初中物理；cnp_h001 高中物理（必修一至选必三，grade 10–15）。cnc_p001 小学语文；cns_p001 小学科学；cnd_p001 小学道德与法治；cnh_j001 初中历史。
ID_RE = re.compile(r"^(?:cnm_(?:p|h)?|cne_[pjh]|cnp_h?|cnc_p|cns_p|cnd_p|cnh_j)\d{3,}$")
# 10、11 是必修第一、二册；12、13、14 是选择性必修第一、二、三册，不是教学年份。
GRADES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
ALIASES_PATH = os.path.join(ROOT, "data", "id-aliases.json")
ALIAS_ID_RE = re.compile(r"^cnm_ext_\d{3,}$")
# 教材版本对照（可选）：topic.mappings 与 data/mappings/*.json，说明见 docs/edition-mappings.md
MAPPINGS_DIR = os.path.join(ROOT, "data", "mappings")
EDITION_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
EDITION_RESERVED = {"renjiao_math", "pep_math"}  # 人教版就是 topic 自己的 grade/semester/chapter
MAPPING_TERMS = ("上", "下", "全")
MAPPING_ENTRY_FIELDS = {"grade", "term", "unit", "chapter", "note"}
MAPPING_FILE_STATUS = ("example", "draft", "reviewed")

errors = []
warnings = []
N_PHY_EDGES = 0
N_HIS_EDGES = 0


def err(msg):
    errors.append(msg)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        err("文件不存在：%s" % path)
    except json.JSONDecodeError as e:
        err("JSON 不合法：%s（%s）" % (path, e))
    return None


def nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def is_english_id(tid):
    return str(tid).startswith("cne_")


def is_physics_id(tid):
    return str(tid).startswith("cnp_")


def is_physics_senior_id(tid):
    return str(tid).startswith("cnp_h")


def is_chinese_id(tid):
    return str(tid).startswith("cnc_")


def is_science_id(tid):
    return str(tid).startswith("cns_")


def is_morality_id(tid):
    return str(tid).startswith("cnd_")


def is_history_id(tid):
    return str(tid).startswith("cnh_")


def topic_subject(tid):
    if is_english_id(tid):
        return "english"
    if is_physics_id(tid):
        return "physics"
    if is_chinese_id(tid):
        return "chinese"
    if is_science_id(tid):
        return "science"
    if is_morality_id(tid):
        return "morality"
    if is_history_id(tid):
        return "history"
    if str(tid).startswith("cnm_"):
        return "math"
    return ""


def volume_rank(topic):
    grade = topic.get("grade")
    if not isinstance(grade, int):
        return None
    return grade * 2 + (1 if topic.get("semester") == "下" else 0)


def physics_rank(topic):
    """初中物理 8、9 年级在前，高中物理（cnp_h，grade 10–15）在后；先修不能比本知识点更晚。"""
    g = topic.get("grade")
    if not isinstance(g, int):
        return None
    return 100 + g if is_physics_senior_id(topic.get("id")) else g


def english_prompt_problem(text):
    s = str(text or "").strip()
    if EN_PROMPT_START_RE.match(s):
        return "题干不能以「同一 / 上题 / 该题 / 同上」开头"
    if EN_PROMPT_BAN_RE.search(s):
        return "题干不能出现「本知识点 / 课标 / 是否要求」"
    return ""


def check_mapping_entry(m, where):
    """一条教材版本对照：{grade, term, unit?, chapter?, note?}。grade 为整数，term 为 上/下/全。"""
    if not isinstance(m, dict):
        err("%s 必须是对象" % where)
        return
    for k in m:
        if k not in MAPPING_ENTRY_FIELDS:
            err("%s 有未知字段 %s（允许：%s）" % (where, k, "、".join(sorted(MAPPING_ENTRY_FIELDS))))
    g = m.get("grade")
    if not (isinstance(g, int) and not isinstance(g, bool) and g in GRADES):
        err("%s grade 必须是 1–14 的整数" % where)
    if m.get("term") not in MAPPING_TERMS:
        err("%s term 必须是 上/下/全" % where)
    for k in ("unit", "chapter", "note"):
        if k in m and not nonempty_str(m[k]):
            err("%s %s 若出现必须是非空字符串" % (where, k))


def check_mappings(maps, where):
    """topic.mappings：{版本键: 对照条目}，可选；缺省即只有人教版。"""
    if not (isinstance(maps, dict) and maps):
        err("%s mappings 必须是非空对象（没有对照就不要写这个字段）" % where)
        return
    for key, m in maps.items():
        if not (isinstance(key, str) and EDITION_KEY_RE.match(key)):
            err("%s mappings 的版本键 %r 不合法（小写字母、数字、下划线，如 hujiao_math）" % (where, key))
        elif key in EDITION_RESERVED:
            err("%s mappings 不应包含人教版（%s）：人教版就是知识点自己的 grade/semester/chapter" % (where, key))
        check_mapping_entry(m, "%s mappings.%s" % (where, key))


def check_mapping_files(ids):
    """data/mappings/*.json：贡献用的对照表文件。目录不存在或为空都合法。返回 (文件数, 条目数)。"""
    if not os.path.isdir(MAPPINGS_DIR):
        return 0, 0
    n_files = n_entries = 0
    for fn in sorted(os.listdir(MAPPINGS_DIR)):
        if not fn.endswith(".json"):
            continue
        n_files += 1
        where = "data/mappings/%s" % fn
        data = load(os.path.join(MAPPINGS_DIR, fn))
        if not isinstance(data, dict):
            err("%s 顶层必须是对象" % where)
            continue
        edition = data.get("edition")
        if not (isinstance(edition, str) and EDITION_KEY_RE.match(edition)) or edition in EDITION_RESERVED:
            err("%s edition 不合法：%r" % (where, edition))
        elif not fn.startswith(edition + "."):
            err("%s 文件名必须以 edition（%s）开头" % (where, edition))
        if not nonempty_str(data.get("label")):
            err("%s 缺少 label（版本中文名）" % where)
        status = data.get("status")
        if status not in MAPPING_FILE_STATUS:
            err("%s status 必须是 %s" % (where, " / ".join(MAPPING_FILE_STATUS)))
        if ".example." in fn and status != "example":
            err("%s 是示例文件，status 必须是 example" % where)
        if status == "example" and ".example." not in fn:
            err("%s status 为 example，文件名应为 <edition>.example.json" % where)
        if status in ("draft", "reviewed") and not nonempty_str(data.get("source")):
            err("%s 非示例文件必须在 source 里写明对照依据" % where)
        entries = data.get("entries")
        if not (isinstance(entries, list) and entries):
            err("%s entries 必须是非空数组" % where)
            continue
        if status == "example" and len(entries) > 10:
            err("%s 示例文件至多 10 条，现有 %d 条" % (where, len(entries)))
        expected_subject = "english" if isinstance(edition, str) and edition.endswith("_english") else "math"
        subject_label = "英语" if expected_subject == "english" else "数学"
        seen = set()
        for i, e in enumerate(entries):
            ew = "%s entries[%d]" % (where, i)
            if not isinstance(e, dict):
                err("%s 不是对象" % ew)
                continue
            tid = e.get("topicId")
            t = ids.get(tid)
            if t is None:
                err("%s topicId 不存在：%r" % (ew, tid))
            elif t.get("external") or topic_subject(tid) != expected_subject:
                err("%s 只能对照%s正式知识点：%s" % (ew, subject_label, tid))
            if tid in seen:
                err("%s topicId 重复：%s" % (ew, tid))
            seen.add(tid)
            check_mapping_entry({k: v for k, v in e.items() if k != "topicId"}, ew)
            n_entries += 1
    return n_files, n_entries


def check_topics(topics):
    ids = {}
    if not isinstance(topics, list):
        err("topics.json 顶层必须是数组")
        return ids
    for i, t in enumerate(topics):
        where = "topics[%d]" % i
        if not isinstance(t, dict):
            err("%s 不是对象" % where)
            continue
        tid = t.get("id")
        if not nonempty_str(tid):
            err("%s 缺少 id" % where)
            continue
        where = "%s(%s)" % (tid, t.get("name", "?"))
        if tid in ids:
            err("id 重复：%s" % tid)
        ids[tid] = t
        if not ID_RE.match(tid):
            err("%s id 格式不合法" % where)
        ext = t.get("external")
        if not isinstance(ext, bool):
            err("%s 的 external 必须是布尔值" % where)
            continue
        if ext != ("_ext_" in tid):
            err("%s 的 external 与 id 前缀不一致" % where)
        fields = EXT_FIELDS if ext else CORE_FIELDS
        for f in fields:
            if f not in t:
                err("%s 缺少必填字段 %s" % (where, f))
            elif f not in ("mastery_criteria", "diagnostic_question", "external") and not nonempty_str(t[f]) \
                    and not (f == "grade" and isinstance(t[f], int)):
                err("%s 字段 %s 为空或类型错误" % (where, f))
        subj = topic_subject(tid)
        marked = t.get("subject")
        if subj == "english":
            if marked != "english":
                err("%s 英语知识点的 subject 必须是 english" % where)
            if t.get("domain") not in EN_DOMAINS:
                err("%s 英语 domain 取值非法：%r" % (where, t.get("domain")))
        elif subj == "physics":
            if marked != "physics":
                err("%s 物理知识点的 subject 必须是 physics" % where)
            if t.get("domain") not in PHY_DOMAINS:
                err("%s 物理 domain 取值非法：%r" % (where, t.get("domain")))
            sem_p = t.get("semester")
            if is_physics_senior_id(tid):
                if t.get("grade") not in PHY_SENIOR_GRADES:
                    err("%s 高中物理 grade 必须是 10–15（10–12 必修三册，13–15 选择性必修三册）" % where)
                if sem_p != "上":
                    err("%s 高中物理 semester 必须是 上" % where)
            else:
                if t.get("grade") not in (8, 9):
                    err("%s 初中物理 grade 必须是 8 或 9" % where)
                if (t.get("grade") == 8 and sem_p not in ("上", "下")) or (t.get("grade") == 9 and sem_p != "全"):
                    err("%s 物理 semester：八年级为 上/下，九年级为 全（人教版九年级全一册）" % where)
            for j, ml in enumerate(t.get("mathLinks") or []):
                if not (isinstance(ml, dict) and nonempty_str(ml.get("id")) and nonempty_str(ml.get("reason"))):
                    err("%s mathLinks[%d] 必须是 {id, reason}" % (where, j))
                elif not str(ml["id"]).startswith("cnm_"):
                    err("%s mathLinks[%d] 只能指向数学知识点：%s" % (where, j, ml["id"]))
            if "mathLinks" in t and not (isinstance(t["mathLinks"], list) and t["mathLinks"]):
                err("%s mathLinks 必须是非空数组" % where)
        elif subj == "science":
            if marked != "science":
                err("%s 科学知识点的 subject 必须是 science" % where)
            if t.get("domain") not in SCI_DOMAINS:
                err("%s 科学 domain 取值非法：%r" % (where, t.get("domain")))
            if "mathLinks" in t and not (isinstance(t["mathLinks"], list) and t["mathLinks"]):
                err("%s mathLinks 必须是非空数组" % where)
            for j, ml in enumerate(t.get("mathLinks") or []):
                if not (isinstance(ml, dict) and nonempty_str(ml.get("id")) and nonempty_str(ml.get("reason"))):
                    err("%s mathLinks[%d] 必须是 {id, reason}" % (where, j))
                elif not str(ml["id"]).startswith("cnm_"):
                    err("%s mathLinks[%d] 只能指向数学知识点：%s" % (where, j, ml["id"]))
        elif subj == "morality":
            if marked != "morality":
                err("%s 道德与法治知识点的 subject 必须是 morality" % where)
            if t.get("domain") not in MOR_DOMAINS:
                err("%s 道德与法治 domain 取值非法：%r" % (where, t.get("domain")))
            if "mathLinks" in t:
                err("%s 只有物理和科学知识点可以带 mathLinks" % where)
        elif subj == "history":
            if marked != "history":
                err("%s 历史知识点的 subject 必须是 history" % where)
            if t.get("domain") not in HIS_DOMAINS:
                err("%s 历史 domain 取值非法：%r" % (where, t.get("domain")))
            if "mathLinks" in t:
                err("%s 只有物理和科学知识点可以带 mathLinks" % where)
        elif subj == "chinese":
            if marked != "chinese":
                err("%s 语文知识点的 subject 必须是 chinese" % where)
            if t.get("domain") not in ZH_DOMAINS:
                err("%s 语文 domain 取值非法：%r" % (where, t.get("domain")))
            if "mathLinks" in t:
                err("%s 只有物理和科学知识点可以带 mathLinks" % where)
        else:
            if "mathLinks" in t:
                err("%s 只有物理和科学知识点可以带 mathLinks" % where)
            if marked not in (None, "math"):
                err("%s 数学知识点不能标成其他学科：%r" % (where, marked))
            if t.get("domain") not in MATH_DOMAINS:
                err("%s domain 取值非法：%r" % (where, t.get("domain")))
        if "mappings" in t:
            if ext:
                err("%s 外部节点不能带 mappings" % where)
            else:
                check_mappings(t["mappings"], where)
        if ext:
            if t.get("grade") != "小学":
                err("%s 外部节点 grade 必须为 \"小学\"" % where)
            continue
        g = t.get("grade")
        if subj == "english" and str(tid).startswith("cne_h"):
            if g not in (10, 11, 12, 13, 14, 15, 16):
                err("%s 高中英语 grade 必须是 10–16（10–12 必修三册，13–16 选择性必修四册）" % where)
        elif subj == "physics" and is_physics_senior_id(tid):
            pass
        elif g not in GRADES:
            err("%s grade 必须是 1–14 的整数（10、11 为必修两册，12–14 为选择性必修三册）" % where)
        if subj == "science" and g not in (1, 2, 3, 4, 5, 6):
            err("%s 小学科学 grade 必须是 1–6" % where)
        if subj == "morality" and g not in (1, 2, 3, 4, 5, 6):
            err("%s 小学道德与法治 grade 必须是 1–6" % where)
        if subj == "history" and g not in (7, 8, 9):
            err("%s 初中历史 grade 必须是 7–9" % where)
        if subj == "chinese" and g not in (1, 2, 3, 4, 5, 6):
            err("%s 小学语文 grade 必须是 1–6" % where)
        if subj == "english":
            if str(tid).startswith("cne_p") and g not in (3, 4, 5, 6):
                err("%s 小学英语 grade 必须是 3–6" % where)
            elif str(tid).startswith("cne_j") and g not in (7, 8, 9):
                err("%s 初中英语 grade 必须是 7–9" % where)
            elif str(tid).startswith("cne_h") and t.get("semester") != "上":
                err("%s 高中英语 semester 必须是 上" % where)
        sem = t.get("semester")
        if subj == "physics":
            pass
        elif subj == "english" and t.get("grade") == 9:
            if sem not in ("上", "全"):
                err("%s 九年级英语 semester 必须是 上（新版九上）或 全（旧版全一册，新版九下未出）" % where)
        elif sem not in ("上", "下"):
            err("%s semester 必须是 上/下" % where)
        if t.get("type") not in TYPES:
            err("%s type 取值非法：%r" % (where, t.get("type")))
        mc = t.get("mastery_criteria")
        if not (isinstance(mc, list) and 2 <= len(mc) <= 3 and all(nonempty_str(x) for x in mc)):
            err("%s mastery_criteria 必须是 2-3 条非空字符串" % where)
        dq = t.get("diagnostic_question")
        if not (isinstance(dq, dict) and nonempty_str(dq.get("question")) and nonempty_str(dq.get("answer"))):
            err("%s diagnostic_question 必须含非空 question 与 answer" % where)
        if "root_reason" in t and not nonempty_str(t["root_reason"]):
            err("%s root_reason 为空" % where)
        if subj in ("english", "chinese", "science", "morality", "history") and isinstance(t.get("diagnostic_question"), dict):
            problem = english_prompt_problem(t["diagnostic_question"].get("question"))
            if problem:
                err("%s 诊断题%s" % (where, problem))
    return ids


def check_deps(deps, ids):
    prereqs = defaultdict(list)   # topic -> [prerequisite]
    dependents = defaultdict(list)
    seen = set()
    n_hard = n_soft = n_en_hard = n_en_soft = 0
    global N_PHY_EDGES, N_HIS_EDGES
    N_PHY_EDGES = 0
    N_HIS_EDGES = 0
    if not isinstance(deps, list):
        err("dependencies.json 顶层必须是数组")
        return prereqs, dependents, 0, 0, 0, 0
    for i, d in enumerate(deps):
        where = "dependencies[%d]" % i
        if not isinstance(d, dict):
            err("%s 不是对象" % where)
            continue
        a, b = d.get("topicId"), d.get("prerequisiteId")
        for f in ("topicId", "prerequisiteId", "strength", "reason"):
            if not nonempty_str(d.get(f)):
                err("%s 缺少或为空字段 %s" % (where, f))
        if a not in ids:
            err("%s topicId 不存在：%r" % (where, a))
        if b not in ids:
            err("%s prerequisiteId 不存在：%r" % (where, b))
        if a == b:
            err("%s 自环：%r" % (where, a))
        if d.get("strength") not in STRENGTHS:
            err("%s strength 取值非法：%r" % (where, d.get("strength")))
        elif d["strength"] == "hard":
            n_hard += 1
        else:
            n_soft += 1
        sa, sb = topic_subject(a), topic_subject(b)
        if sa and sb and sa != sb:
            err("%s 跨学科边：%s -> %s" % (where, a, b))
        if sa == "physics":
            N_PHY_EDGES += 1
        if sa == "history":
            N_HIS_EDGES += 1
        if sa == "english" and d.get("strength") in STRENGTHS:
            if d["strength"] == "hard":
                n_en_hard += 1
            else:
                n_en_soft += 1
        if sa == "english" and sb == "english" and a in ids and b in ids:
            ra, rb = volume_rank(ids[a]), volume_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 英语先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        if sa == "science" and sb == "science" and a in ids and b in ids:
            ra, rb = volume_rank(ids[a]), volume_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 科学先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        if sa == "morality" and sb == "morality" and a in ids and b in ids:
            ra, rb = volume_rank(ids[a]), volume_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 道德与法治先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        if sa == "history" and sb == "history" and a in ids and b in ids:
            ra, rb = volume_rank(ids[a]), volume_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 历史先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        if sa == "chinese" and sb == "chinese" and a in ids and b in ids:
            ra, rb = volume_rank(ids[a]), volume_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 语文先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        if sa == "physics" and sb == "physics" and a in ids and b in ids:
            ra, rb = physics_rank(ids[a]), physics_rank(ids[b])
            if ra is not None and rb is not None and rb > ra:
                err("%s 物理先修年级或册次更晚：%s 依赖 %s" % (where, a, b))
        key = (a, b)
        if key in seen:
            err("%s 重复边：%s -> %s" % (where, a, b))
        seen.add(key)
        if a in ids and b in ids and a != b:
            prereqs[a].append(b)
            dependents[b].append(a)
    return prereqs, dependents, n_hard, n_soft, n_en_hard, n_en_soft


def find_cycle(ids, prereqs):
    WHITE, GREY, BLACK = 0, 1, 2
    color = {t: WHITE for t in ids}
    for start in ids:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(prereqs.get(start, [])))]
        path = [start]
        color[start] = GREY
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                color[node] = BLACK
                stack.pop()
                path.pop()
                continue
            if color[nxt] == GREY:
                return path[path.index(nxt):] + [nxt]
            if color[nxt] == WHITE:
                color[nxt] = GREY
                stack.append((nxt, iter(prereqs.get(nxt, []))))
                path.append(nxt)
    return None


def check_graph(ids, prereqs, dependents):
    cyc = find_cycle(ids, prereqs)
    if cyc:
        err("存在环路：" + " -> ".join("%s(%s)" % (c, ids[c].get("name")) for c in cyc))
    for tid, t in ids.items():
        has_pre = bool(prereqs.get(tid))
        has_dep = bool(dependents.get(tid))
        if not t.get("external") and not has_pre and not nonempty_str(t.get("root_reason")):
            err("%s(%s) 没有先修边，也没有 root_reason" % (tid, t.get("name")))
        if not has_pre and not has_dep:
            err("%s(%s) 完全孤立（既无先修也未被依赖）" % (tid, t.get("name")))


def report(ids, prereqs, dependents, n_hard, n_soft, n_en_hard, n_en_soft):
    core = [t for t in ids.values() if not t.get("external")]
    ext = [t for t in ids.values() if t.get("external")]
    math_core = [t for t in core if topic_subject(t.get("id")) == "math"]
    en_core = [t for t in core if is_english_id(t.get("id"))]
    phy_core = [t for t in core if is_physics_id(t.get("id"))]
    zh_core = [t for t in core if is_chinese_id(t.get("id"))]
    sci_core = [t for t in core if is_science_id(t.get("id"))]
    mor_core = [t for t in core if is_morality_id(t.get("id"))]
    his_core = [t for t in core if is_history_id(t.get("id"))]
    print("知识点总数：%d（正式 %d，小学外部 %d）" % (len(ids), len(core), len(ext)))
    print("其中数学 %d，语文 %d，英语 %d，物理 %d，科学 %d，道德与法治 %d，历史 %d" % (
        len(math_core), len(zh_core), len(en_core), len(phy_core), len(sci_core), len(mor_core), len(his_core)))
    print("\n按 domain（数学正式知识点）：")
    for k, v in sorted(Counter(t["domain"] for t in math_core).items(), key=lambda x: -x[1]):
        print("  %-8s %d" % (k, v))
    print("\n按 grade+semester（数学正式知识点）：")
    zh = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}

    def vol_label(t):
        if is_physics_senior_id(t.get("id")):
            return {10: "物必一", 11: "物必二", 12: "物必三", 13: "物选必一", 14: "物选必二", 15: "物选必三"}.get(t["grade"], str(t["grade"]))
        if is_english_id(t.get("id")) and isinstance(t.get("grade"), int) and t["grade"] >= 10:
            return {10: "必修一", 11: "必修二", 12: "必修三", 13: "选必一", 14: "选必二", 15: "选必三", 16: "选必四"}.get(t["grade"], str(t["grade"]))
        if t["grade"] == 10:
            return "高一必修一"
        if t["grade"] == 11:
            return "高二必修二"
        if t["grade"] == 12:
            return "选必一"
        if t["grade"] == 13:
            return "选必二"
        if t["grade"] == 14:
            return "选必三"
        return "%s%s" % (zh.get(t["grade"], t["grade"]), t["semester"])

    c = Counter(vol_label(t) for t in math_core)
    order = ["一上", "一下", "二上", "二下", "三上", "三下", "四上", "四下", "五上", "五下", "六上", "六下",
             "七上", "七下", "八上", "八下", "九上", "九下", "高一必修一", "高二必修二", "选必一", "选必二", "选必三"]
    for k in order:
        if c.get(k, 0) or k[0] in "七八九" or k.startswith("高") or k.startswith("选必"):
            print("  %-8s %d" % (k, c.get(k, 0)))
    n_pri = sum(1 for t in math_core if isinstance(t.get("grade"), int) and t["grade"] <= 6)
    n_jun = sum(1 for t in math_core if isinstance(t.get("grade"), int) and 7 <= t["grade"] <= 9)
    n_req = sum(1 for t in math_core if t.get("grade") in (10, 11))
    n_sel = sum(1 for t in math_core if isinstance(t.get("grade"), int) and t["grade"] >= 12)
    print("其中小学（1–6 年级）%d，初中（7–9 年级）%d，高中必修（10–11）%d，选择性必修（12–14）%d" % (
        n_pri, n_jun, n_req, n_sel))
    if zh_core:
        print("\n语文按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in zh_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        print("语文按册：")
        zc = Counter(vol_label(t) for t in zh_core)
        for k in ["一上", "一下", "二上", "二下", "三上", "三下", "四上", "四下", "五上", "五下", "六上", "六下"]:
            print("  %-8s %d" % (k, zc.get(k, 0)))
    if sci_core:
        print("\n科学按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in sci_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        print("科学按册：")
        scc = Counter(vol_label(t) for t in sci_core)
        for k in ["一上", "一下", "二上", "二下", "三上", "三下", "四上", "四下", "五上", "五下", "六上", "六下"]:
            print("  %-8s %d" % (k, scc.get(k, 0)))
    if mor_core:
        print("\n道德与法治按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in mor_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        print("道德与法治按册：")
        mc = Counter(vol_label(t) for t in mor_core)
        for k in ["一上", "一下", "二上", "二下", "三上", "三下", "四上", "四下", "五上", "五下", "六上", "六下"]:
            print("  %-8s %d" % (k, mc.get(k, 0)))
    if his_core:
        print("\n历史按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in his_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        print("历史按册：")
        hc = Counter(vol_label(t) for t in his_core)
        for k in ["七上", "七下", "八上", "八下", "九上", "九下"]:
            print("  %-8s %d" % (k, hc.get(k, 0)))
        print("历史先修边 %d 条" % N_HIS_EDGES)
    if en_core:
        print("\n英语按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in en_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        print("英语按册：")
        ec = Counter(vol_label(t) for t in en_core)
        for k in ["三上", "三下", "四上", "四下", "五上", "五下", "六上", "六下", "七上", "七下", "八上", "八下", "九上", "九全",
                  "必修一", "必修二", "必修三", "选必一", "选必二", "选必三", "选必四"]:
            if ec.get(k, 0) or k in ("必修一", "必修二", "必修三", "选必一", "选必二", "选必三", "选必四"):
                print("  %-8s %d" % (k, ec.get(k, 0)))
    if phy_core:
        print("\n物理按 domain：")
        for k, v in sorted(Counter(t["domain"] for t in phy_core).items(), key=lambda x: -x[1]):
            print("  %-8s %d" % (k, v))
        pc = Counter(vol_label(t) for t in phy_core)
        print("物理按册：" + "，".join("%s %d" % (k, pc.get(k, 0)) for k in (
            "八上", "八下", "九全", "物必一", "物必二", "物必三", "物选必一", "物选必二", "物选必三")))
    print("\n按 type（正式知识点）：")
    for k, v in sorted(Counter(t["type"] for t in core).items(), key=lambda x: -x[1]):
        print("  %-12s %d" % (k, v))
    total = n_hard + n_soft
    print("\n先修边：%d 条（hard %d，soft %d）" % (total, n_hard, n_soft))
    if en_core:
        print("其中英语 %d 条（hard %d，soft %d），物理 %d 条，数学 %d 条" % (
            n_en_hard + n_en_soft, n_en_hard, n_en_soft, N_PHY_EDGES, total - n_en_hard - n_en_soft - N_PHY_EDGES))
    roots = [t["id"] for t in core if not prereqs.get(t["id"])]
    leaves = [t["id"] for t in core if not dependents.get(t["id"])]
    print("带 root_reason 的根节点：%d；未被任何知识点依赖的末端节点：%d" % (len(roots), len(leaves)))
    if core:
        print("正式知识点平均先修数：%.2f" % (sum(len(prereqs.get(t["id"], [])) for t in core) / len(core)))


def check_standards_file(std):
    """校验课标条目文件本身，返回 {id: item}。文件不存在时返回 None。"""
    if std is None:
        return None
    items_by_id = {}
    if not isinstance(std, dict):
        err("cn-curriculum-standards.json 顶层必须是对象")
        return items_by_id
    src = std.get("source")
    if not isinstance(src, dict):
        err("cn-curriculum-standards.json 缺少 source 对象")
    else:
        for f in ("title", "issuer", "stage", "url", "retrieved", "note"):
            if not nonempty_str(src.get(f)):
                err("source.%s 缺失或为空" % f)
        if not isinstance(src.get("year"), int):
            err("source.year 必须是整数")
    items = std.get("items")
    if not isinstance(items, list) or not items:
        err("cn-curriculum-standards.json 的 items 必须是非空数组")
        return items_by_id
    last = {}
    saw_english = False
    saw_physics = False
    saw_physics_senior = False
    saw_chinese = False
    saw_science = False
    saw_morality = False
    saw_history = False
    for i, it in enumerate(items):
        where = "standards.items[%d]" % i
        if not isinstance(it, dict):
            err("%s 不是对象" % where)
            continue
        sid = it.get("id")
        if not nonempty_str(sid):
            err("%s 缺少 id" % where)
            continue
        where = "%s(%s)" % (where, sid)
        if sid in items_by_id:
            err("课标条目 id 重复：%s" % sid)
        items_by_id[sid] = it
        m = STD_ID_RE.match(sid)
        hm = HS_STD_ID_RE.match(sid)
        em = EN_STD_ID_RE.match(sid)
        ehm = EN_HS_STD_ID_RE.match(sid)
        zm = ZH_STD_ID_RE.match(sid)
        scm = SCI_STD_ID_RE.match(sid)
        mrm = MOR_STD_ID_RE.match(sid)
        hism = HIS_STD_ID_RE.match(sid)
        pm = PHY_STD_ID_RE.match(sid)
        phm = PHY_HS_STD_ID_RE.match(sid)
        if phm:
            saw_physics_senior = True
            kind, vol, sec, num = phm.group(1), phm.group(2), phm.group(3), int(phm.group(4))
            if it.get("domain") not in PHY_HS_STD_DOMAINS:
                err("%s domain 取值非法：%r" % (where, it.get("domain")))
            if sec == "X":
                if it.get("domain") != "实验探究":
                    err("%s 学生必做实验的 domain 必须是 实验探究" % where)
                if not re.match(r"^实验 \d+$", str(it.get("clause", ""))):
                    err("%s 实验的 clause 必须形如「实验 N」（课标原序号）" % where)
            elif it.get("clause") != "%s.%s.%d" % (vol, sec, num):
                err("%s clause 必须是 %s.%s.%d（课标条款号）" % (where, vol, sec, num))
            key = ("cpshs", kind, vol, sec)
            if num != last.get(key, 0) + 1:
                err("%s 编号在册内主题内不连续（上一条为 %d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 高中物理课标条目必须显式标 verbatim:false（出版社 PDF 文字层，未与纸本逐字核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 高中物理课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif pm:
            saw_physics = True
            if it.get("domain") != PHY_STD_TOPS[pm.group(1)]:
                err("%s domain 与 id 中的一级主题不一致：%r" % (where, it.get("domain")))
            if it.get("clause") != "%s.%s.%s" % pm.groups():
                err("%s clause 必须与 id 中的条款编号一致" % where)
            key = ("cps", pm.group(1), pm.group(2))
            if int(pm.group(3)) != last.get(key, 0) + 1:
                err("%s 编号在二级主题内不连续（上一条为 %d）" % (where, last.get(key, 0)))
            last[key] = int(pm.group(3))
            if it.get("verbatim") is not False:
                err("%s 物理课标条目必须显式标 verbatim:false（OCR 后人工校对，未逐字核对纸本）" % where)
        elif m:
            stage, code, num = m.group(1), m.group(2), int(m.group(3))
            if it.get("domain") != STD_DOMAIN_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("2022", stage, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
        elif hm:
            code, num = hm.group(1), int(hm.group(2))
            if it.get("domain") not in MATH_DOMAINS:
                err("%s domain 取值非法：%r" % (where, it.get("domain")))
            key = ("2017", code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在模块内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 高中条目必须显式标 verbatim:false（原文未逐页核对）" % where)
        elif em:
            saw_english = True
            level, code, num = em.group(1), em.group(2), int(em.group(3))
            if it.get("domain") != EN_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            if level not in ("1", "2", "3"):
                err("%s 英语课标级别必须是 1、2 或 3" % where)
            key = ("ces", level, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在级别和领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 英语课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 英语课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif ehm:
            saw_english = True
            band, code, num = ehm.group(1), ehm.group(2), int(ehm.group(3))
            if it.get("domain") != EN_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("ces2017", band, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在级别和领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 高中英语课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 高中英语课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif scm:
            saw_science = True
            level, code, num = scm.group(1), scm.group(2), int(scm.group(3))
            if it.get("domain") != SCI_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("css", level, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在学段和领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 科学课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 科学课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif zm:
            saw_chinese = True
            level, code, num = zm.group(1), zm.group(2), int(zm.group(3))
            if it.get("domain") != ZH_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("ccs", level, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在学段和领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 语文课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 语文课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif mrm:
            saw_morality = True
            level, code, num = mrm.group(1), mrm.group(2), int(mrm.group(3))
            if it.get("domain") != MOR_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("cds", level, code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在学段和领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 道德与法治课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 道德与法治课标 page_or_ref 必须是「待核」，不能编页码" % where)
        elif hism:
            saw_history = True
            code, num = hism.group(1), int(hism.group(2))
            if it.get("domain") != HIS_STD_CODES[code]:
                err("%s domain 与 id 中的领域代码不一致：%r" % (where, it.get("domain")))
            key = ("chs", code)
            if num != last.get(key, 0) + 1:
                err("%s 编号在领域内不连续（上一条为 %02d）" % (where, last.get(key, 0)))
            last[key] = num
            if it.get("verbatim") is not False:
                err("%s 历史课标必须显式标 verbatim:false（原文未逐页核对）" % where)
            if it.get("page_or_ref") != "待核":
                err("%s 历史课标 page_or_ref 必须是「待核」，不能编页码" % where)
        else:
            err("%s id 格式不合法（应为 cms-2022:<学段>.<NA|GG|SP|IP>.<NN>、cms-2017:H.<PRE|FUN|GA|PS|MI>.<NN>、ces-2022:<1|2|3>.<PH|VO|GR|FU|RW>.<NN> 、ces-2017:H.<B|S>.<PH|VO|GR|FU|RW>.<NN> 、ccs-2022:<1|2|3>.<PY|SZ|CY|JZ|YD|GS|XZ>.<NN> 、css-2022:<1|2|3>.<WZ|SM|DQ|JG>.<NN> 、cds-2022:<1|2|3>.<LS|XX|JT|SH|GM|ZR>.<NN> 、chs-2022:<CA|CN|CM|WA|WN|WM>.<NN> 、cps-2022:<1-5>.<二级>.<序号> 或 cps-hs-2017:<B|S><1-3>.<1-4|X>.<序号>）" % where)
        for f in ("domain", "section", "text"):
            if not nonempty_str(it.get(f)):
                err("%s 字段 %s 缺失或为空" % (where, f))
        if "verbatim" in it and not isinstance(it["verbatim"], bool):
            err("%s verbatim 必须是布尔值" % where)
        if nonempty_str(it.get("text")) and not re.search(r"[\u4e00-\u9fff]", it["text"]):
            err("%s text 必须是中文" % where)
    if saw_physics:
        phy = std.get("physics")
        if not isinstance(phy, dict):
            err("有物理课标条目，但缺少 physics 对象")
        else:
            for f in ("title", "issuer", "stage", "note", "revision"):
                if not nonempty_str(phy.get(f)):
                    err("physics.%s 缺失或为空" % f)
            if not isinstance(phy.get("year"), int):
                err("physics.year 必须是整数")
    if saw_physics_senior:
        phs = std.get("physics_senior")
        if not isinstance(phs, dict):
            err("有高中物理课标条目，但缺少 physics_senior 对象")
        else:
            for f in ("title", "issuer", "stage", "note", "revision", "url", "textbook"):
                if not nonempty_str(phs.get(f)):
                    err("physics_senior.%s 缺失或为空" % f)
            if not isinstance(phs.get("year"), int):
                err("physics_senior.year 必须是整数")
    if saw_english:
        eng = std.get("english")
        if not isinstance(eng, dict):
            err("有英语课标条目，但缺少 english 对象")
        else:
            for f in ("title", "issuer", "stage", "note"):
                if not nonempty_str(eng.get(f)):
                    err("english.%s 缺失或为空" % f)
            if not isinstance(eng.get("year"), int):
                err("english.year 必须是整数")
            if any(str(sid).startswith("ces-2017:H.") for sid in items_by_id):
                senior = eng.get("senior")
                if not isinstance(senior, dict):
                    err("有高中英语课标条目，但缺少 english.senior")
                else:
                    for f in ("title", "issuer", "url", "note"):
                        if not nonempty_str(senior.get(f)):
                            err("english.senior.%s 缺失或为空" % f)
                    if senior.get("year") != 2025:
                        err("english.senior.year 必须是 2025（2017年版2025年修订）")
    if saw_science:
        sc = std.get("science")
        if not isinstance(sc, dict):
            err("有科学课标条目，但缺少 science 对象")
        else:
            for f in ("title", "issuer", "stage", "note"):
                if not nonempty_str(sc.get(f)):
                    err("science.%s 缺失或为空" % f)
            if sc.get("title") != "义务教育科学课程标准（2022年版）":
                err("science.title 必须是「义务教育科学课程标准（2022年版）」")
            if sc.get("year") != 2022:
                err("science.year 必须是 2022")
    if saw_chinese:
        zh = std.get("chinese")
        if not isinstance(zh, dict):
            err("有语文课标条目，但缺少 chinese 对象")
        else:
            for f in ("title", "issuer", "stage", "note"):
                if not nonempty_str(zh.get(f)):
                    err("chinese.%s 缺失或为空" % f)
            if zh.get("title") != "义务教育语文课程标准（2022年版）":
                err("chinese.title 必须是「义务教育语文课程标准（2022年版）」")
            if not isinstance(zh.get("year"), int):
                err("chinese.year 必须是整数")
            elif zh.get("year") != 2022:
                err("chinese.year 必须是 2022")
    if saw_morality:
        mo = std.get("morality")
        if not isinstance(mo, dict):
            err("有道德与法治课标条目，但缺少 morality 对象")
        else:
            for f in ("title", "issuer", "stage", "note"):
                if not nonempty_str(mo.get(f)):
                    err("morality.%s 缺失或为空" % f)
            if mo.get("title") != "义务教育道德与法治课程标准（2022年版）":
                err("morality.title 必须是「义务教育道德与法治课程标准（2022年版）」")
            if mo.get("year") != 2022:
                err("morality.year 必须是 2022")
    if saw_history:
        hi = std.get("history")
        if not isinstance(hi, dict):
            err("有历史课标条目，但缺少 history 对象")
        else:
            for f in ("title", "issuer", "stage", "note"):
                if not nonempty_str(hi.get(f)):
                    err("history.%s 缺失或为空" % f)
            if hi.get("title") != "义务教育历史课程标准（2022年版）":
                err("history.title 必须是「义务教育历史课程标准（2022年版）」")
            if hi.get("year") != 2022:
                err("history.year 必须是 2022")
    return items_by_id


def check_topic_standards(ids, std_items):
    """校验每个知识点的 standards 字段，返回 (被引用的课标 id 集合, 正式知识点中 standards 为空的列表)。"""
    cited = set()
    empty_core = []
    for tid, t in ids.items():
        where = "%s(%s)" % (tid, t.get("name"))
        core = not t.get("external")
        if "standards" not in t:
            if core:
                empty_core.append(t)
            continue
        sts = t["standards"]
        if not isinstance(sts, list):
            err("%s 的 standards 必须是数组" % where)
            continue
        if not sts and core:
            empty_core.append(t)
        if len(sts) > MAX_STANDARDS_PER_TOPIC:
            err("%s 的 standards 超过 %d 条" % (where, MAX_STANDARDS_PER_TOPIC))
        seen = set()
        for j, s in enumerate(sts):
            sw = "%s standards[%d]" % (where, j)
            if not isinstance(s, dict):
                err("%s 不是对象" % sw)
                continue
            sid = s.get("id")
            if not nonempty_str(sid):
                err("%s 缺少 id" % sw)
                continue
            if sid in seen:
                err("%s 重复引用课标条目 %s" % (where, sid))
            seen.add(sid)
            if std_items is None:
                err("%s 引用了 %s，但 data/cn-curriculum-standards.json 不存在" % (sw, sid))
            elif sid not in std_items:
                err("%s 的课标条目不存在于 cn-curriculum-standards.json：%s" % (sw, sid))
            else:
                cited.add(sid)
                if is_physics_id(tid) != str(sid).startswith("cps-"):
                    err("%s 学科与课标条目不一致：%s" % (sw, sid))
                elif is_physics_id(tid) and is_physics_senior_id(tid) != str(sid).startswith("cps-hs-2017:"):
                    err("%s 初中物理只能引用 cps-2022，高中物理只能引用 cps-hs-2017：%s" % (sw, sid))
                if is_chinese_id(tid) != str(sid).startswith("ccs-"):
                    err("%s 学科与课标条目不一致：%s" % (sw, sid))
                if is_science_id(tid) != str(sid).startswith("css-"):
                    err("%s 学科与课标条目不一致：%s" % (sw, sid))
                if is_morality_id(tid) != str(sid).startswith("cds-"):
                    err("%s 学科与课标条目不一致：%s" % (sw, sid))
                if is_history_id(tid) != str(sid).startswith("chs-"):
                    err("%s 学科与课标条目不一致：%s" % (sw, sid))
            if s.get("confidence") not in CONFIDENCES:
                err("%s confidence 只能是 exact 或 inferred：%r" % (sw, s.get("confidence")))
            if "note" in s and not nonempty_str(s["note"]):
                err("%s note 为空" % sw)
    return cited, empty_core


def report_standards(ids, std_items, cited, empty_core):
    core = [t for t in ids.values() if not t.get("external")]
    if std_items is None:
        print("\n课标对齐：未找到 data/cn-curriculum-standards.json，跳过")
        return
    c = Counter(it.get("domain") for it in std_items.values())
    std_order = ("数与代数", "图形与几何", "统计与概率", "综合与实践",
                 "拼音", "识字写字", "词语", "句子", "阅读理解", "古诗文积累", "习作基础",
                 "语音", "词汇", "语法", "日常表达", "读写",
                 "物质", "运动和相互作用", "能量", "实验探究", "跨学科实践",
                 "物质科学", "生命科学", "地球与宇宙科学", "技术与工程",
                 "生活与安全", "学校生活", "家庭与亲情", "社会规则", "公民与国家", "自然与环境",
                 "中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史", "世界现代史")
    print("\n课标条目：%d 条（%s）" % (len(std_items), "，".join("%s %d" % (k, c[k]) for k in std_order if c[k])))
    n_ok = len(core) - len(empty_core)
    pct = 100.0 * n_ok / len(core) if core else 0.0
    print("正式知识点 standards 非空：%d / %d（%.1f%%）；standards 为空：%d" % (n_ok, len(core), pct, len(empty_core)))
    conf = Counter(s.get("confidence") for t in core for s in t.get("standards", []) if isinstance(s, dict))
    print("映射条数：exact %d，inferred %d；至少有一条 exact 的知识点 %d" % (
        conf.get("exact", 0), conf.get("inferred", 0),
        sum(1 for t in core if any(isinstance(s, dict) and s.get("confidence") == "exact" for s in t.get("standards", [])))))
    print("被至少一个知识点引用的课标条目：%d / %d；无对应知识点的课标条目：%d" % (
        len(cited), len(std_items), len(std_items) - len(cited)))
    if empty_core:
        label = "ERROR" if STRICT_STANDARDS else "WARNING"
        print("\n%s：以下正式知识点的 standards 为空（共 %d 个，至多列 %d 个）：" % (label, len(empty_core), MAX_WARNINGS_LISTED))
        for t in empty_core[:MAX_WARNINGS_LISTED]:
            print("  %s %s" % (t["id"], t.get("name")))
        if len(empty_core) > MAX_WARNINGS_LISTED:
            print("  ……另有 %d 个未列出" % (len(empty_core) - MAX_WARNINGS_LISTED))


# ---------------------------------------------------------------- 题库（data/questions.json）

Q_DIFFICULTIES = ("basic", "standard", "challenge")
Q_DIFFICULTY_ALIASES = {"advanced": "challenge"}  # 旧名，与 challenge 同档
Q_TYPES = ("numeric", "choice", "short", "self")
Q_FIELDS = {"id", "topicId", "difficulty", "type", "prompt", "answer", "choices", "accept",
            "explanation", "verify", "unordered", "fixed_from_source", "figure", "hideChoiceText", "percent"}
# 与知识点无关的纯整数/小数四则（不含分数写法 a/b）。
# 一至六年级 challenge 不得直接「计算：…＝？」。低年级允许写进情境里的简单计算，
# 但整题不能只是「计算：2＋3＝？」或「3＋2 的得数是哪一个？」。
PURE_ARITH_PROMPT_RE = re.compile(
    r"^(计算：)?\d+(?:\.\d+)?(?:\s*[＋+\-－×*÷]\s*\d+(?:\.\d+)?)+＝？(?:（用小数作答）)?$"
)
PURE_ARITH_CHOICE_RE = re.compile(
    r"^\d+(?:\.\d+)?(?:\s*[＋+\-－×*÷]\s*\d+(?:\.\d+)?)+ 的得数是哪一个？$"
)
CHALLENGE_BARE_CALC_RE = re.compile(r"^计算：.*＝？")
Q_ID_RE = re.compile(r"^((?:cnm_(?:p|h)?|cne_[pjh]|cnp_h?|cnc_p|cns_p|cnd_p|cnh_j)\d{3,})_q([1-9]\d*)$")
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?$")
MIN_QUESTIONS_PER_TOPIC = 3
MIN_AUTO_SHARE = 0.60


def parse_numeric_answer(s):
    """把 numeric 题的 answer 解析成 Fraction 列表；不合法返回 None。
    单个数：整数、小数、分数 a/b、负数；多个答案用全角「，」（或半角逗号）分隔。"""
    if not isinstance(s, str):
        return None
    parts = [p.replace(" ", "") for p in re.split(r"[，,]", s)]
    out = []
    for p in parts:
        if not NUM_RE.match(p):
            return None
        try:
            out.append(Fraction(p))
        except (ValueError, ZeroDivisionError):
            return None
    return out


def question_errors(questions, topics_by_id, require_coverage=True):
    """返回 (错误列表, 统计字典)。require_coverage=False 时用于单个批次文件（不要求每个知识点 >=3 题）。"""
    errs = []
    stats = {"total": 0, "by_type": Counter(), "by_difficulty": Counter(), "per_topic": Counter()}
    if not isinstance(questions, list):
        return ["questions.json 顶层必须是数组"], stats
    seen = set()
    by_topic = defaultdict(list)
    for i, q in enumerate(questions):
        w = "questions[%d]" % i
        if not isinstance(q, dict):
            errs.append("%s 不是对象" % w)
            continue
        qid = q.get("id")
        if not nonempty_str(qid):
            errs.append("%s 缺少 id" % w)
            continue
        w = qid
        if qid in seen:
            errs.append("%s id 重复" % w)
        seen.add(qid)
        m = Q_ID_RE.match(qid)
        if not m:
            errs.append("%s id 格式应为 <topicId>_q<N>" % w)
        unknown = set(q) - Q_FIELDS
        if unknown:
            errs.append("%s 含未知字段：%s" % (w, "、".join(sorted(unknown))))
        tid = q.get("topicId")
        t = topics_by_id.get(tid) if isinstance(tid, str) else None
        if t is None:
            errs.append("%s 的 topicId 不存在：%r" % (w, tid))
        elif t.get("external"):
            errs.append("%s 的 topicId 是外部节点（外部节点不出题）：%s" % (w, tid))
        if m and tid != m.group(1):
            errs.append("%s 的 id 前缀与 topicId(%r) 不一致" % (w, tid))
        for f in ("difficulty", "type", "prompt", "answer", "explanation"):
            if not nonempty_str(q.get(f)):
                errs.append("%s 字段 %s 缺失或为空（answer 必须是字符串）" % (w, f))
        if is_english_id(tid) or is_chinese_id(tid) or is_science_id(tid) or is_morality_id(tid) or is_history_id(tid):
            problem = english_prompt_problem(q.get("prompt"))
            if problem:
                errs.append("%s %s" % (w, problem))
        diff, typ = q.get("difficulty"), q.get("type")
        if nonempty_str(diff) and diff not in Q_DIFFICULTIES and diff not in Q_DIFFICULTY_ALIASES:
            errs.append("%s difficulty 取值非法：%r" % (w, diff))
        if nonempty_str(typ) and typ not in Q_TYPES:
            errs.append("%s type 取值非法：%r" % (w, typ))
        if "accept" in q:
            acc = q["accept"]
            if not (isinstance(acc, list) and all(nonempty_str(x) for x in acc)):
                errs.append("%s accept 必须是非空字符串数组" % w)
        if "verify" in q and not nonempty_str(q["verify"]):
            errs.append("%s verify 必须是非空字符串" % w)
        if "unordered" in q and not (q["unordered"] is True and typ == "numeric"):
            errs.append("%s unordered 只能用于 numeric 题且取值为 true" % w)
        if "percent" in q and not (q["percent"] is True and typ == "numeric" and is_physics_id(tid)):
            errs.append("%s percent 只能用于物理 numeric 题且取值为 true（answer 写百分数的数值部分）" % w)
        if "fixed_from_source" in q and not nonempty_str(q["fixed_from_source"]):
            errs.append("%s fixed_from_source 为空" % w)
        ans = q.get("answer")
        if typ == "choice":
            ch = q.get("choices")
            if not (isinstance(ch, list) and 3 <= len(ch) <= 4):
                errs.append("%s choice 题必须有 3–4 个选项" % w)
            else:
                keys = []
                texts = []
                for c in ch:
                    if not (isinstance(c, dict) and nonempty_str(c.get("key")) and nonempty_str(c.get("text"))
                            and set(c) <= {"key", "text", "figure"}):
                        errs.append("%s 选项必须形如 {key, text} 且非空，图示放在可选的 figure" % w)
                        break
                    keys.append(c["key"])
                    texts.append(c["text"].strip())
                else:
                    if len(set(keys)) != len(keys):
                        errs.append("%s 选项 key 重复" % w)
                    if keys != list("ABCD")[:len(keys)]:
                        errs.append("%s 选项 key 必须依次为 A、B、C、D：%r" % (w, keys))
                    if len(set(texts)) != len(texts):
                        errs.append("%s 选项文字重复" % w)
                    if nonempty_str(ans) and ans not in keys:
                        errs.append("%s answer(%r) 不是任何一个选项的 key" % (w, ans))
        elif "choices" in q:
            errs.append("%s 只有 choice 题可以带 choices" % w)
        if typ == "numeric" and nonempty_str(ans):
            vals = parse_numeric_answer(ans)
            if vals is None:
                errs.append("%s numeric 题 answer 不是可解析的数：%r" % (w, ans))
            elif len(vals) == 1 and q.get("unordered") is True:
                errs.append("%s 只有一个答案时不应写 unordered" % w)
        errs.extend(question_figure_problems(q))
        if isinstance(tid, str):
            by_topic[tid].append(q)
        if nonempty_str(typ):
            stats["by_type"][typ] += 1
        if nonempty_str(diff):
            stats["by_difficulty"][diff] += 1
        stats["total"] += 1
    for tid, qs in by_topic.items():
        stats["per_topic"][tid] = len(qs)
    if require_coverage:
        for tid, t in topics_by_id.items():
            if t.get("external"):
                continue
            qs = by_topic.get(tid, [])
            if len(qs) < MIN_QUESTIONS_PER_TOPIC:
                errs.append("%s(%s) 只有 %d 道题，至少需要 %d 道" % (tid, t.get("name"), len(qs), MIN_QUESTIONS_PER_TOPIC))
            ds = {q.get("difficulty") for q in qs}
            if qs and not {"basic", "standard"} <= ds:
                errs.append("%s(%s) 的难度需至少含 basic 和 standard" % (tid, t.get("name")))
            # 一至六年级数学：三档齐全；禁止与知识点无关的纯整数/小数四则；拓展不得直接「计算：…＝？」
            if t.get("grade") in (1, 2, 3, 4, 5, 6) and str(tid).startswith("cnm_") and not (
                    is_english_id(tid) or is_physics_id(tid) or is_chinese_id(tid)):
                label = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}[t.get("grade")]
                if qs and ("standard" not in ds or "challenge" not in ds):
                    errs.append("%s(%s) %s年级题库需至少含 1 道 standard 和 1 道 challenge" % (
                        tid, t.get("name"), label))
                for q in qs:
                    p = str(q.get("prompt") or "").strip()
                    if PURE_ARITH_PROMPT_RE.match(p) or PURE_ARITH_CHOICE_RE.match(p):
                        errs.append("%s 是与知识点无关的纯整数或小数计算题" % q.get("id"))
                    if q.get("difficulty") == "challenge" and CHALLENGE_BARE_CALC_RE.match(p):
                        errs.append("%s challenge 题干不得直接「计算：…＝？」" % q.get("id"))
            q1 = [q for q in qs if q.get("id") == tid + "_q1"]
            dq = (t.get("diagnostic_question") or {}).get("question")
            if qs and not q1:
                errs.append("%s 缺少 %s_q1（应由 diagnostic_question 迁移）" % (tid, tid))
            elif q1 and nonempty_str(dq) and "fixed_from_source" not in q1[0] \
                    and not str(q1[0].get("prompt", "")).startswith(dq):
                errs.append("%s_q1 的题干应以 topics.json 的 diagnostic_question.question 开头" % tid)
    return errs, stats


def report_questions(stats, topics_by_id):
    core = [tid for tid, t in topics_by_id.items() if not t.get("external")]
    counts = [stats["per_topic"].get(tid, 0) for tid in core]
    print("\n题库：共 %d 题" % stats["total"])
    print("按 type：" + "，".join("%s %d" % (k, stats["by_type"].get(k, 0)) for k in Q_TYPES))
    print("按 difficulty：" + "，".join("%s %d" % (k, stats["by_difficulty"].get(k, 0)) for k in Q_DIFFICULTIES + ("advanced",)))
    auto = stats["by_type"].get("numeric", 0) + stats["by_type"].get("choice", 0)
    if stats["total"]:
        print("numeric + choice 占比：%.1f%%" % (100.0 * auto / stats["total"]))
    if counts:
        dist = Counter(counts)
        print("每知识点题数：最少 %d，最多 %d，平均 %.2f；分布 %s" % (
            min(counts), max(counts), sum(counts) / float(len(counts)),
            "，".join("%d 题×%d" % (k, dist[k]) for k in sorted(dist))))


def check_aliases(ids):
    """data/id-aliases.json：旧 cnm_ext_* 必须映射到仍存在的小学正式知识点。"""
    if not os.path.exists(ALIASES_PATH):
        err("缺少 data/id-aliases.json（旧 cnm_ext_* 的跳转表）")
        return
    data = load(ALIASES_PATH)
    if not isinstance(data, dict):
        return
    aliases = data.get("aliases")
    if not isinstance(aliases, dict) or not aliases:
        err("id-aliases.json 的 aliases 必须是非空对象")
        return
    for i in range(1, 19):
        key = "cnm_ext_%03d" % i
        if key not in aliases:
            err("id-aliases.json 缺少旧节点 %s" % key)
    for key, spec in aliases.items():
        if not ALIAS_ID_RE.match(key):
            err("别名 id 格式不合法：%s" % key)
        if key in ids:
            err("别名 %s 仍作为知识点存在，应只出现在 id-aliases.json" % key)
        targets = spec.get("targets") if isinstance(spec, dict) else None
        if not (isinstance(targets, list) and targets):
            err("别名 %s 的 targets 必须是非空数组" % key)
            continue
        if len(set(targets)) != len(targets):
            err("别名 %s 的 targets 有重复" % key)
        for tid in targets:
            t = ids.get(tid)
            if t is None:
                err("别名 %s 指向不存在的知识点 %s" % (key, tid))
            elif t.get("external") or not (isinstance(t.get("grade"), int) and t["grade"] <= 6):
                err("别名 %s 必须指向小学正式知识点，而不是 %s" % (key, tid))
        if isinstance(spec, dict) and not nonempty_str(spec.get("name")):
            err("别名 %s 缺少原名称 name" % key)


def main():
    topics = load(TOPICS_PATH)
    deps = load(DEPS_PATH)
    if topics is None or deps is None:
        for e in errors:
            print("错误：" + e)
        print("VALIDATION FAILED")
        return 1
    ids = check_topics(topics)
    check_aliases(ids)
    n_map_files, n_map_entries = check_mapping_files(ids)
    n_topic_maps = sum(1 for t in ids.values() if "mappings" in t)
    print("教材版本对照（可选）：topic.mappings %d 个知识点；data/mappings %d 个文件、%d 条" % (
        n_topic_maps, n_map_files, n_map_entries))
    prereqs, dependents, n_hard, n_soft, n_en_hard, n_en_soft = check_deps(deps, ids)
    check_graph(ids, prereqs, dependents)
    std_items = None
    if os.path.exists(STANDARDS_PATH):
        std_items = check_standards_file(load(STANDARDS_PATH))
    cited, empty_core = check_topic_standards(ids, std_items)
    if STRICT_STANDARDS and std_items is not None and empty_core:
        err("STRICT_STANDARDS=1：%d 个正式知识点的 standards 为空" % len(empty_core))
    report(ids, prereqs, dependents, n_hard, n_soft, n_en_hard, n_en_soft)
    report_standards(ids, std_items, cited, empty_core)
    if os.path.exists(QUESTIONS_PATH):
        qs = load(QUESTIONS_PATH)
        if qs is not None:
            qerrs, qstats = question_errors(qs, ids, require_coverage=True)
            for e in qerrs:
                err("题库：" + e)
            auto = qstats["by_type"].get("numeric", 0) + qstats["by_type"].get("choice", 0)
            if qstats["total"] and auto < MIN_AUTO_SHARE * qstats["total"]:
                err("题库：numeric + choice 占比 %.1f%% < %d%%" % (100.0 * auto / qstats["total"], MIN_AUTO_SHARE * 100))
            report_questions(qstats, ids)
    else:
        print("\n题库：未找到 data/questions.json，跳过")
    print()
    if errors:
        for e in errors:
            print("错误：" + e)
        print("\n共 %d 个错误" % len(errors))
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
