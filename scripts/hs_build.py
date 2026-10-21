#!/usr/bin/env python3
"""把高中必修草稿编译进 data/topics.json、dependencies.json、questions.json、课标文件。

只应在还没有 cnm_h001 时运行一次。已经编译过再跑会拒绝，避免重复追加。
先修边只对新增的高中边做传递约简，不改已有小学 / 初中边。

用法：python3 scripts/hs_build.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hs_common import EDGES, ELECTIVE, PAGES, QUESTIONS, STANDARDS, TOPICS  # noqa: E402
import hs_standards  # noqa: E402,F401
import hs_book1  # noqa: E402,F401
import hs_book2  # noqa: E402,F401
from verify_questions import safe_eval  # noqa: E402

CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# 跨学段边指向的已有知识点。名称写在这里，编译时核对，避免指错 id。
KNOWN = {
    "cnm_003": "有理数的分类",
    "cnm_025": "用字母表示数",
    "cnm_040": "等式的性质",
    "cnm_049": "分段计费与方案选择",
    "cnm_050": "立体图形与平面图形",
    "cnm_052": "点、线、面、体",
    "cnm_056": "角的概念与表示",
    "cnm_064": "垂线",
    "cnm_067": "平行线与平行公理",
    "cnm_071": "定义、命题与定理",
    "cnm_072": "平移的概念与性质",
    "cnm_074": "平方根与算术平方根",
    "cnm_077": "无理数",
    "cnm_078": "实数的分类与数轴表示",
    "cnm_082": "平面直角坐标系与点的坐标",
    "cnm_094": "不等式及其解集",
    "cnm_096": "不等式的性质",
    "cnm_097": "一元一次不等式的解法",
    "cnm_102": "全面调查与抽样调查",
    "cnm_103": "总体、个体、样本与样本容量",
    "cnm_105": "扇形图、条形图与折线图",
    "cnm_106": "频数分布表与数据分组",
    "cnm_107": "频数分布直方图",
    "cnm_115": "三角形内角和定理",
    "cnm_142": "同底数幂的乘法",
    "cnm_163": "同底数幂的除法",
    "cnm_164": "零指数幂、负整数指数幂与科学记数法",
    "cnm_167": "二次根式的概念与有意义的条件",
    "cnm_174": "勾股定理",
    "cnm_183": "平行四边形的性质",
    "cnm_194": "函数的概念",
    "cnm_195": "自变量的取值范围",
    "cnm_197": "函数的图象",
    "cnm_198": "函数的三种表示方法",
    "cnm_201": "一次函数的概念",
    "cnm_203": "一次函数的性质",
    "cnm_211": "平均数",
    "cnm_213": "中位数与众数",
    "cnm_215": "极差、方差与标准差",
    "cnm_216": "数据的四分位数",
    "cnm_219": "一元二次方程的概念",
    "cnm_222": "公式法与求根公式",
    "cnm_224": "因式分解法",
    "cnm_229": "二次函数的概念",
    "cnm_230": "y=ax² 的图象与性质",
    "cnm_232": "y=ax²+bx+c 的图象与性质",
    "cnm_234": "二次函数与一元二次方程",
    "cnm_235": "二次函数的最值",
    "cnm_237": "反比例函数的概念",
    "cnm_244": "图形的旋转",
    "cnm_250": "圆的有关概念",
    "cnm_256": "弧长",
    "cnm_257": "扇形面积",
    "cnm_258": "圆锥的侧面积与全面积",
    "cnm_276": "锐角三角函数的定义",
    "cnm_277": "特殊角的三角函数值与计算",
    "cnm_278": "解直角三角形",
    "cnm_283": "三视图及由三视图想象立体图形",
    "cnm_284": "随机事件、必然事件与不可能事件",
    "cnm_285": "概率的意义与等可能事件的概率",
    "cnm_286": "用列举法求概率",
    "cnm_288": "用频率估计概率",
    "cnm_292": "数据收集的方法：问卷调查、实验与查阅资料",
    "cnm_297": "频率（相对频数）的计算与意义",
    "cnm_298": "简单随机抽样的实施（抽签法与随机数）",
    "cnm_302": "用样本平均数估计总体平均数",
    "cnm_306": "用样本方差估计总体的稳定性",
    "cnm_308": "概率的取值范围与概率的性质",
    "cnm_309": "等可能性与古典概型的判断",
    "cnm_p163": "长方体和正方体的体积",
    "cnm_p207": "圆柱的体积",
    "cnm_p208": "圆柱的表面积",
    "cnm_p209": "圆锥的体积",
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fmt_one(v):
    if isinstance(v, bool) or v is None:
        raise TypeError(repr(v))
    if isinstance(v, str):
        raise TypeError("数值题的 verify 不应返回字符串：%r" % v)
    if isinstance(v, float):
        fr = Fraction(v).limit_denominator(64)
        if abs(float(fr) - v) > 1e-9:
            raise ValueError("结果不是简单分数：%r" % (v,))
        v = fr
    if isinstance(v, int):
        v = Fraction(v)
    if not isinstance(v, Fraction):
        raise TypeError(type(v).__name__)
    if v.denominator == 1:
        return str(int(v))
    return "%d/%d" % (v.numerator, v.denominator)


def fmt_result(v):
    if isinstance(v, (list, tuple)):
        if len(v) < 2:
            raise ValueError("多个答案至少 2 个")
        return "，".join(fmt_one(x) for x in v)
    return fmt_one(v)


def build_question(tid, index, spec, slot):
    kind = spec[0]
    diff = "basic" if index <= 2 else "standard"
    qid = "%s_q%d" % (tid, index)
    if kind in ("n", "nu"):
        prompt, verify, expl = spec[1], spec[2], spec[3]
        res = safe_eval(verify)
        answer = fmt_result(res)
        multi = isinstance(res, (list, tuple))
        item = {
            "id": qid,
            "topicId": tid,
            "difficulty": diff,
            "type": "numeric",
            "prompt": prompt,
            "answer": answer,
            "explanation": expl,
            "verify": verify,
        }
        if kind == "nu":
            if not multi:
                raise ValueError("%s 标记了无序但 verify 不是多个答案" % qid)
            item["unordered"] = True
        elif multi:
            pass
        return item, answer
    if kind == "c":
        prompt, correct, wrongs, expl = spec[1], spec[2], spec[3], spec[4]
        texts = list(wrongs)
        if correct in texts or len(set(texts)) != len(texts):
            raise ValueError("%s 选项重复或正确项混进错误项" % qid)
        if not (2 <= len(wrongs) <= 3):
            raise ValueError("%s 干扰项须 2–3 个" % qid)
        texts.insert(slot % (len(wrongs) + 1), correct)
        if len(set(t.strip() for t in texts)) != len(texts):
            raise ValueError("%s 选项文字重复" % qid)
        keys = list("ABCD")[:len(texts)]
        pos = texts.index(correct)
        item = {
            "id": qid,
            "topicId": tid,
            "difficulty": diff,
            "type": "choice",
            "prompt": prompt,
            "choices": [{"key": keys[i], "text": texts[i]} for i in range(len(texts))],
            "answer": keys[pos],
            "explanation": expl,
            "verify": json.dumps(correct, ensure_ascii=False),
        }
        return item, correct
    raise ValueError("未知题型 %s" % kind)


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


def reduce_new(edges):
    """只删除高中知识点上的冗余新边。hard 仅当另有全 hard 路径时删；soft 只要另有路径就删。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not str(e["topicId"]).startswith("cnm_h"):
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


def chapter_of(spec):
    vol = "高一" if spec["book"] == 1 else "高二"
    if spec["chapter"] in ("数学建模", "数学探究"):
        return "%s %s %s" % (vol, spec["chapter"], spec["section"])
    return "%s %s %s" % (vol, spec["chapter"], spec["section"])


def main():
    topics = load("topics.json")
    if any(t.get("id") == "cnm_h001" for t in topics):
        print("已经有 cnm_h001。hs_build.py 不能重复编译。", file=sys.stderr)
        return 1
    by_name = {t["name"]: t for t in topics}
    for tid, name in KNOWN.items():
        hit = next((t for t in topics if t["id"] == tid), None)
        if hit is None or hit["name"] != name:
            print("跨学段 id 对不上：%s 期望「%s」，实际 %s" % (
                tid, name, None if hit is None else hit["name"]), file=sys.stderr)
            return 1

    if len(TOPICS) < 120 or len(TOPICS) > 180:
        print("知识点数量 %d 不在 120–180" % len(TOPICS), file=sys.stderr)
        return 1
    missing_q = [t["key"] for t in TOPICS if t["key"] not in QUESTIONS]
    if missing_q:
        print("缺题：%s" % "、".join(missing_q), file=sys.stderr)
        return 1
    extra_q = sorted(set(QUESTIONS) - {t["key"] for t in TOPICS})
    if extra_q:
        print("多余题目 key：%s" % "、".join(extra_q), file=sys.stderr)
        return 1

    std_codes = [s["code"] for s in STANDARDS]
    if len(std_codes) != len(set(std_codes)):
        print("课标 code 重复", file=sys.stderr)
        return 1
    index = {t["key"]: i for i, t in enumerate(TOPICS)}
    grade_of = {t["key"]: (10 if t["book"] == 1 else 11) for t in TOPICS}

    new_topics = []
    new_questions = []
    id_of = {}
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cnm_h%03d" % i
        id_of[spec["key"]] = tid
        if spec["std"] not in std_codes:
            print("%s 课标 %s 不存在" % (spec["key"], spec["std"]), file=sys.stderr)
            return 1
        if spec["confidence"] not in ("exact", "inferred"):
            print("%s confidence 非法" % spec["key"], file=sys.stderr)
            return 1
        if spec["confidence"] == "inferred" and not spec.get("note"):
            print("%s inferred 缺 note" % spec["key"], file=sys.stderr)
            return 1
        try:
            built = []
            diag_answer = None
            for n, item in enumerate(QUESTIONS[spec["key"]], start=1):
                q, shown = build_question(tid, n, item, slot=i + n)
                if not q["prompt"].strip() or not q["explanation"].strip():
                    raise ValueError("题干或解析为空")
                if "因为" in q["explanation"] and q["explanation"].count("选") > 2:
                    pass
                built.append(q)
                if n == 1:
                    diag_answer = shown
        except Exception as exc:  # noqa: BLE001
            print("出题失败 %s %s：%s" % (tid, spec["name"], exc), file=sys.stderr)
            return 1
        std_ref = {"id": "cms-2017:H.%s" % spec["std"], "confidence": spec["confidence"]}
        if spec.get("note"):
            std_ref["note"] = spec["note"]
        new_topics.append({
            "id": tid,
            "name": spec["name"],
            "domain": spec["domain"],
            "grade": 10 if spec["book"] == 1 else 11,
            "semester": "上",
            "chapter": chapter_of(spec),
            "type": spec["type"],
            "description": spec["description"],
            "mastery_criteria": spec["mastery_criteria"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag_answer},
            "external": False,
            "standards": [std_ref],
        })
        new_questions.extend(built)

    raw_edges = []
    seen = set()
    for src, dst, strength, reason in EDGES:
        if src not in id_of:
            print("边的起点不是高中知识点：%s" % src, file=sys.stderr)
            return 1
        if len(CJK_RE.findall(reason)) < 9:
            print("理由太短：%s → %s：%s" % (src, dst, reason), file=sys.stderr)
            return 1
        if dst in id_of:
            if index[dst] >= index[src]:
                print("先修不早于后续：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            if grade_of[dst] > grade_of[src]:
                print("先修年级更高：%s 依赖 %s" % (src, dst), file=sys.stderr)
                return 1
            pid = id_of[dst]
        elif dst in KNOWN:
            pid = dst
        else:
            print("先修既不是高中 key 也不是已登记的旧 id：%s" % dst, file=sys.stderr)
            return 1
        key = (id_of[src], pid)
        if key in seen:
            print("重复边 %s → %s" % key, file=sys.stderr)
            return 1
        seen.add(key)
        raw_edges.append({
            "topicId": id_of[src],
            "prerequisiteId": pid,
            "strength": strength,
            "reason": reason,
        })

    deps = load("dependencies.json")
    merged, dropped = reduce_new(deps + raw_edges)
    new_only = [e for e in merged if str(e["topicId"]).startswith("cnm_h")]
    internal = [e for e in new_only if str(e["prerequisiteId"]).startswith("cnm_h")]
    cross = [e for e in new_only if not str(e["prerequisiteId"]).startswith("cnm_h")]
    print("高中知识点 %d" % len(new_topics))
    print("新边写入 %d（约简删去 %d）；高中内部 %d，跨学段 %d" % (
        len(new_only), dropped, len(internal), len(cross)))
    print("题目 %d" % len(new_questions))

    from verify_questions import verify_all
    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1
    covered = {e["topicId"] for e in new_only}
    naked = [t["id"] + " " + t["name"] for t in new_topics if t["id"] not in covered]
    if naked:
        print("这些高中知识点没有先修，不能当新的根：" + "、".join(naked), file=sys.stderr)
        return 1
    ch_model = re.compile(r"^(高[一二]) (数学建模|数学探究) (\S+)$")
    ch_num = re.compile(r"^(\S+) (第\S+章) (\S+?)(?: (\S+))?$")
    for t in new_topics:
        if not (ch_model.match(t["chapter"]) or ch_num.match(t["chapter"])):
            print("章节名无法解析：%s %s" % (t["id"], t["chapter"]), file=sys.stderr)
            return 1

    std = load("cn-curriculum-standards.json")
    note = std["source"].get("note") or ""
    extra = (" 高中必修条目据《普通高中数学课程标准（2017年版2020年修订）》五个主题的公开转述整理，"
             "不是逐页核对的原文，verbatim 为 false，page_or_ref 为「待核」。"
             "编号 cms-2017:H.<模块>.NN 是本图谱按主题编的，不是教育部原编号。")
    if "cms-2017" not in note:
        std["source"]["note"] = note + extra
    std["source"]["stage"] = "义务教育第一至第四学段（1～9年级）；普通高中必修课程"
    retrieved = std["source"].get("retrieved") or ""
    if "2026-10-20" not in retrieved:
        std["source"]["retrieved"] = retrieved + "；2026-10-20（高中必修）"
    std["source"]["high_school"] = {
        "title": "普通高中数学课程标准（2017年版2020年修订）",
        "issuer": "中华人民共和国教育部",
        "year": 2020,
        "url": "http://www.moe.gov.cn/srcsite/A26/s8001/202006/t20200603_462199.html",
        "reference_pdf": "https://www.pep.com.cn/xw/zt/rjwy/gzkb2020/202205/P020220517519489596282.pdf",
        "note": "印发通知见教育部网页。条目正文未与该 PDF 逐页核对，标为待核。",
    }
    existing_ids = {it["id"] for it in std["items"]}
    for s in STANDARDS:
        sid = "cms-2017:H.%s" % s["code"]
        if sid in existing_ids:
            print("课标 id 已存在：%s" % sid, file=sys.stderr)
            return 1
        std["items"].append({
            "id": sid,
            "domain": s["domain"],
            "theme": s["theme"],
            "section": s["section"],
            "clause": s["clause"],
            "text": s["text"],
            "page_or_ref": ("课标印刷页码 %d" % PAGES[s["code"]]) if s["code"] in PAGES else "待核",
            "verbatim": False,
            "text_status": "公开转述整理，未与教育部 PDF 逐页核对，待核",
        })
        if s["code"] in ELECTIVE:
            std["items"][-1]["elective"] = True

    topics.extend(new_topics)
    questions = load("questions.json")
    questions.extend(new_questions)
    dump("topics.json", topics)
    dump("dependencies.json", merged)
    dump("questions.json", questions)
    dump("cn-curriculum-standards.json", std)
    batch = os.path.join(ROOT, "data", "_qbatches", "high.json")
    with open(batch, "w", encoding="utf-8") as f:
        json.dump(new_questions, f, ensure_ascii=False, indent=2)
        f.write("\n")

    log_path = os.path.join(ROOT, "data", "second_pass_log.json")
    with open(log_path, encoding="utf-8") as f:
        log = json.load(f)
    pass_name = "D：高中必修题由生成脚本写 verify，再经 verify_questions.py 核对表达式与答案"
    passes = log.setdefault("passes", [])
    if not any(p.get("name") == pass_name for p in passes):
        passes.append({
            "name": pass_name,
            "solver": "scripts/hs_build.py + scripts/verify_questions.py",
            "questions": len(new_questions),
            "note": "答案由同一条 verify 表达式求值后写入，再被核验脚本比对，所以 mismatch 反映的是格式而不是另一遍独立解题。没有做初中 A/B 轮那种盲解。概念题的选项文字与 verify 返回的字符串相同。",
            "disagreements": 0,
        })
    log["high_school_checked_by_verify"] = len(new_questions)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写入 data/。请再跑 validate.py 与 verify_questions.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
