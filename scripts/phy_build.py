#!/usr/bin/env python3
"""把物理草稿编译进 data/ 下的四个文件：初中（phy_g8a / phy_g8b / phy_g9）和高中（phy_hs_a01 … a11，见 phy_hs_build.py）。

可重复运行：只删掉自己负责的那一部分再重写，另一部分原样保留。
  初中：cnp_NNN 知识点、边、题目，cps-2022: 课标条目
  高中：cnp_hNNN 知识点、边、题目，cps-hs-2017: 课标条目
数学、英语部分一概不动。物理与数学之间不连先修边（validate.py 禁止跨学科边），改用知识点上的 mathLinks 字段。

用法：python3 scripts/phy_build.py                 # 初中 + 高中都重建（高中先修边可以指向初中知识点）
      python3 scripts/phy_build.py --junior-only    # 只重建初中，已有的高中数据保持不动
      python3 scripts/phy_build.py --senior-only    # 只重建高中，已有的初中数据保持不动
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import phy_g8a  # noqa: E402,F401
import phy_g8b  # noqa: E402,F401
import phy_g9  # noqa: E402,F401
from phy_figs import figure_for  # noqa: E402
from phy_lib import TOPICS  # noqa: E402
from phy_std import CLAUSES, SECTIONS, TOP  # noqa: E402
from verify_questions import verify_all  # noqa: E402

GRADE = {"八上": (8, "上"), "八下": (8, "下"), "九全": (9, "全")}
STD_SOURCE = {
    "title": "义务教育物理课程标准（2022年版2025年修订）",
    "issuer": "中华人民共和国教育部",
    "year": 2022,
    "revision": "2025 年日常修订版（教育部《中小学课程方案和课程标准日常修订版》，教材〔2025〕1号）",
    "stage": "义务教育第四学段（8–9 年级）",
    "section": "课程内容 · 【内容要求】",
    "note": ("条文取自 2022年版2025年修订 的课标扫描 PDF，经 OCR 识别后按原页图像人工校对（个别形近字已改正），"
             "没有与纸本逐字核对，verbatim 为 false；page_or_ref 是该 PDF 的文件页码。编号 cps-2022:<一级>.<二级>.<序号> "
             "与课标原文条款编号一致。一级主题“实验探究”（4.1、4.2 学生必做实验）只作为课标条目，知识点 domain 只用"
             "物质、运动和相互作用、能量、跨学科实践。教材为人教版（根据2022年版课程标准修订）八年级上册（2024）、"
             "八年级下册（2025）、九年级全一册（2025），知识点按目录到节。"),
    "retrieved": "2026-10-22",
}


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    with open(os.path.join(ROOT, "data", name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def slot(key, i):
    return int(hashlib.md5(("%s#%d" % (key, i)).encode()).hexdigest(), 16) % 4


JR_TOPIC = re.compile(r"^cnp_\d")
SR_TOPIC = re.compile(r"^cnp_h\d")


def _drop(items, key, rx):
    keep, old = [], []
    for it in items:
        (old if rx.match(str(it.get(key, ""))) else keep).append(it)
    return keep, old


def build_junior(math_ids, id_of, order, name_of):
    std_items = []
    for cid, text, page in CLAUSES:
        top, sec, num = cid.split(".")
        std_items.append({
            "id": "cps-2022:%s" % cid,
            "domain": TOP[top],
            "section": "%s.%s %s" % (top, sec, SECTIONS["%s.%s" % (top, sec)]),
            "clause": cid,
            "text": text,
            "page_or_ref": "PDF 第 %d 页" % page,
            "verbatim": False,
            "text_status": "扫描 PDF 经 OCR 识别后人工校对，未与纸本逐字核对",
        })
    std_ids = {it["id"] for it in std_items}
    new_topics, new_deps, new_qs = [], [], []
    errs = []
    for t in TOPICS:
        tid = id_of[t["key"]]
        vol, chn, chname, secno = t["sec"]
        g, s = GRADE[vol]
        assert " " not in chname, chname
        q1 = t["qs"][0]
        topic = {
            "id": tid, "name": t["name"], "domain": t["domain"], "grade": g, "semester": s,
            "chapter": "%s %s %s %s" % (vol, chn, chname, secno), "type": t["type"],
            "description": t["description"], "mastery_criteria": t["mastery"],
            "diagnostic_question": {"question": q1["prompt"],
                                    "answer": q1["right"] if q1["kind"] == "choice" else q1["answer"]},
            "external": False, "subject": "physics",
            "standards": [{"id": "cps-2022:%s" % c, "confidence": conf} for c, conf in t["std"]],
        }
        for sref in topic["standards"]:
            if sref["id"] not in std_ids:
                errs.append("%s 引用了不存在的课标 %s" % (tid, sref["id"]))
        if t["math"]:
            links = []
            for mid, reason in t["math"]:
                if mid not in math_ids:
                    errs.append("%s 的 mathLinks 指向不存在的数学知识点 %s" % (tid, mid))
                links.append({"id": mid, "reason": reason})
            topic["mathLinks"] = links
        if t["root"]:
            topic["root_reason"] = t["root"]
        if not t["pre"] and not t["root"]:
            errs.append("%s 没有先修也没有 root" % tid)
        new_topics.append(topic)
        for pk, strength in t["pre"]:
            if order[pk] >= order[t["key"]]:
                errs.append("%s 的先修 %s 不在它前面" % (tid, pk))
            reason = ("学「%s」要先会「%s」。" if strength == "hard" else "「%s」会用到「%s」里的知识。") % (
                t["name"], name_of[pk])
            new_deps.append({"topicId": tid, "prerequisiteId": id_of[pk], "strength": strength, "reason": reason})
        if len(t["qs"]) != 4:
            errs.append("%s 题数不是 4" % tid)
        for i, q in enumerate(t["qs"], 1):
            qid = "%s_q%d" % (tid, i)
            if q["kind"] == "numeric":
                obj = {"id": qid, "topicId": tid, "difficulty": q["diff"], "type": "numeric", "prompt": q["prompt"],
                       "answer": q["answer"], "explanation": q["expl"], "verify": q["verify"]}
                if q.get("percent"):
                    obj["percent"] = True
            else:
                texts = list(q["wrongs"])
                if len(set(texts + [q["right"]])) != len(texts) + 1:
                    errs.append("%s 选项重复" % qid)
                pos = q["pos"] if q["pos"] is not None else slot(t["key"], i) % (len(texts) + 1)
                texts.insert(pos, q["right"])
                keys = "ABCD"
                obj = {"id": qid, "topicId": tid, "difficulty": q["diff"], "type": "choice", "prompt": q["prompt"],
                       "choices": [{"key": keys[j], "text": x} for j, x in enumerate(texts)],
                       "answer": keys[pos], "explanation": q["expl"],
                       "verify": q["verify"] if q["verify"] else json.dumps(q["right"], ensure_ascii=False)}
            if q.get("figure"):
                obj["figure"] = q["figure"]
            fig = figure_for(obj)
            if fig:
                obj["figure"] = fig
            new_qs.append(obj)
    res = verify_all(new_qs)
    for m in res["mismatch"]:
        errs.append("核验不通过 %s：%s" % (m["id"], m.get("detail")))
    return dict(topics=new_topics, deps=new_deps, qs=new_qs, std_items=std_items, errs=errs, verified=len(res["auto_verified"]))


def main():
    only_j = "--junior-only" in sys.argv
    only_s = "--senior-only" in sys.argv
    if only_j and only_s:
        print("--junior-only 和 --senior-only 不能同时用", file=sys.stderr)
        return 2
    do_j, do_s = not only_s, not only_j

    topics_all = load("topics.json")
    deps_all = load("dependencies.json")
    qs_all = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    topics, tj = _drop(topics_all, "id", JR_TOPIC)
    topics, ts = _drop(topics, "id", SR_TOPIC)
    deps, dj = _drop(deps_all, "topicId", JR_TOPIC)
    deps, ds = _drop(deps, "topicId", SR_TOPIC)
    questions, qj = _drop(qs_all, "id", JR_TOPIC)
    questions, qsr = _drop(questions, "id", SR_TOPIC)
    items = standards["items"]
    keep_items = [it for it in items if not str(it.get("id", "")).startswith("cps-")]
    sj = [it for it in items if str(it.get("id", "")).startswith("cps-2022:")]
    ss = [it for it in items if str(it.get("id", "")).startswith("cps-hs-2017:")]
    other_cps = [it for it in items if str(it.get("id", "")).startswith("cps-")
                 and not str(it["id"]).startswith(("cps-2022:", "cps-hs-2017:"))]
    if other_cps:
        print("错误：出现不认识的 cps- 课标条目：%s" % other_cps[0]["id"], file=sys.stderr)
        return 1
    math_ids = {t["id"]: t for t in topics if str(t["id"]).startswith("cnm_")}

    id_of = {t["key"]: "cnp_%03d" % (i + 1) for i, t in enumerate(TOPICS)}
    order = {t["key"]: i for i, t in enumerate(TOPICS)}
    name_of = {t["key"]: t["name"] for t in TOPICS}

    J = build_junior(math_ids, id_of, order, name_of)
    errs = list(J["errs"]) if do_j else []
    S_ = None
    if do_s:
        import phy_hs_build  # noqa: E402
        S_ = phy_hs_build.compile_senior(math_ids, id_of, name_of)
        errs += S_["errs"]
    if errs:
        for e in errs:
            print("错误：" + e, file=sys.stderr)
        return 1

    out_topics = topics + (J["topics"] if do_j else tj) + (S_["topics"] if do_s else ts)
    out_deps = deps + (J["deps"] if do_j else dj) + (S_["deps"] if do_s else ds)
    out_qs = questions + (J["qs"] if do_j else qj) + (S_["qs"] if do_s else qsr)
    standards["items"] = keep_items + (J["std_items"] if do_j else sj) + (S_["std_items"] if do_s else ss)
    if do_j:
        standards["physics"] = STD_SOURCE
    if do_s:
        standards["physics_senior"] = phy_hs_build.STD_SOURCE
    dump("topics.json", out_topics)
    dump("dependencies.json", out_deps)
    dump("questions.json", out_qs)
    dump("cn-curriculum-standards.json", standards)

    def line(tag, R):
        print("%s：知识点 %d，先修边 %d（hard %d，soft %d），题目 %d（自动核验 %d），课标条目 %d，mathLinks %d 条（%d 个知识点）" % (
            tag, len(R["topics"]), len(R["deps"]), sum(d["strength"] == "hard" for d in R["deps"]),
            sum(d["strength"] == "soft" for d in R["deps"]), len(R["qs"]), R["verified"], len(R["std_items"]),
            sum(len(t.get("mathLinks", [])) for t in R["topics"]), sum(1 for t in R["topics"] if t.get("mathLinks"))))
    if do_j:
        line("初中物理", J)
    if do_s:
        line("高中物理", S_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
