"""把高中物理草稿（phy_hs_a01 … phy_hs_a11）编译成知识点、先修边、题目和课标条目。

不单独运行；由 phy_build.py 调用（那里负责合并进 data/ 下的四个文件，并保证初中物理不被冲掉）。
id：知识点 cnp_h001 起，按 phy_hs_plan.py 的教材顺序固定；课标条目 cps-hs-2017:<B|S><册>.<主题>.<序号>。
"""
from __future__ import annotations

import importlib
import json

import phy_hs_lib as L
import phy_hs_plan as P
import phy_hs_std as S
from verify_questions import verify_all

STD_SOURCE = {
    "title": "普通高中物理课程标准（2017年版2020年修订）",
    "issuer": "中华人民共和国教育部",
    "year": 2017,
    "revision": "2020 年修订",
    "stage": "普通高中（必修 1–3、选择性必修 1–3）",
    "section": "课程内容 · 【内容要求】；学生必做实验",
    "url": "https://www.esph.com.cn/docs/2025-04/b8fb91c002624b2e90ebfb1095f23a32.pdf",
    "textbook": ("人民教育出版社 普通高中教科书·物理（人教版）必修第一册、第二册、第三册、选择性必修第一册、第二册、第三册，"
                 "2019 年审定、依据 2017 年版课标；目录取自 2019 版目录页，各册具体印次未逐册核对版权页。"
                 "知识点按目录到节，个别大节拆成 2–3 个知识点。"),
    "note": (
        "条文最初取自教育科学出版社公开的《普通高中物理课程标准（2017年版2020年修订）》PDF 的文字层，按原文条款分条；2026-11-21 已逐条对照人教社同名课标 PDF（第四章【内容要求】与学生必做实验清单），page_or_ref 为课标印刷页码（页面所印页码），各条 text_status 记核对结论。"
        "库存 text 不收例题与活动建议，也没有与纸本逐字核对，verbatim 仍为 false。"
        "编号 cps-hs-2017:<B 必修 | S 选择性必修><册号>.<主题>.<条款>，与课标“必修 1 的 1.1.1”式条款编号一致。"
        "只收录必修和选择性必修的【内容要求】（87 条）与学生必做实验（21 项，课标原序号写在 clause 里，id 用 X 主题在册内重新编号）；选修课程（选修 1–3）、活动建议和例不收录。"
        "知识点的 domain 沿用初中物理的物质、运动和相互作用、能量、跨学科实践四类，不对应课标主题名。"),
    "retrieved": "2026-10-23",
}


def load_drafts():
    for fid in P.ASSIGN:
        importlib.import_module("phy_hs_" + fid)
        # 分拆文件由主文件自己 import
    return L.HS


def compile_senior(math_ids, junior_id_of, junior_name_of):
    """返回 dict(topics, deps, qs, std_items, errs, verified)。"""
    errs = []
    load_drafts()
    for r in P.PLAN:
        if r["key"] not in L.HS:
            errs.append("缺少高中物理知识点 %s（%s）" % (r["key"], r["name"]))
    std_items = []
    for tail, clause, text in S.CLAUSES:
        mod, sec, n = tail.split(".")
        std_items.append({
            "id": L.std_id(tail),
            "domain": S.DOMAIN["%s.%s" % (mod, sec)],
            "section": "%s · %s.%s %s" % (S.MODULE_NAME[mod], clause.split(".")[0], sec, S.SECTIONS["%s.%s" % (mod, sec)]),
            "module": S.MODULE_NAME[mod],
            "clause": clause,
            "text": text,
            "page_or_ref": S.CHECK[tail][0],
            "verbatim": False,
            "text_status": S.CHECK[tail][1],
        })
    for tail, clause, text in S.EXPERIMENTS:
        mod = tail.split(".")[0]
        std_items.append({
            "id": L.std_id(tail),
            "domain": "实验探究",
            "section": "%s · 学生必做实验" % S.MODULE_NAME[mod],
            "module": S.MODULE_NAME[mod],
            "clause": clause,
            "text": text,
            "page_or_ref": S.CHECK[tail][0],
            "verbatim": False,
            "text_status": S.CHECK[tail][1],
        })
    std_ids = {it["id"] for it in std_items}

    topics, deps, qs = [], [], []
    name_of = {r["key"]: r["name"] for r in P.PLAN}
    for r in P.PLAN:
        key = r["key"]
        t = L.HS.get(key)
        if t is None:
            continue
        tid = L.tid_of(key)
        q1 = t["qs"][0]
        topic = {
            "id": tid, "name": r["name"], "domain": t["domain"], "grade": r["grade"], "semester": "上",
            "chapter": "%s %s %s %s" % r["sec"], "type": t["type"],
            "description": t["description"], "mastery_criteria": t["mastery"],
            "diagnostic_question": {"question": q1["prompt"],
                                    "answer": q1["right"] if q1["kind"] == "choice" else q1["answer"]},
            "external": False, "subject": "physics",
            "standards": [{"id": L.std_id(c), "confidence": conf} for c, conf in t["std"]],
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
        topics.append(topic)
        for pk, strength in t["pre"]:
            if pk.startswith("J:"):
                if pk[2:] not in junior_id_of:
                    errs.append("%s 的初中先修 %s 不存在" % (tid, pk))
                    continue
                pid, pname = junior_id_of[pk[2:]], junior_name_of[pk[2:]]
            else:
                if pk not in L.HS or P.ORDER[pk] >= P.ORDER[key]:
                    errs.append("%s 的先修 %s 不存在或不在它前面" % (tid, pk))
                    continue
                pid, pname = L.tid_of(pk), name_of[pk]
            reason = ("学「%s」要先会「%s」。" if strength == "hard" else "「%s」会用到「%s」里的知识。") % (r["name"], pname)
            deps.append({"topicId": tid, "prerequisiteId": pid, "strength": strength, "reason": reason})
        qs.extend(L.compile_questions(key, tid, t, errs))

    res = verify_all(qs)
    for m in res["mismatch"]:
        errs.append("核验不通过 %s：%s" % (m["id"], m.get("detail")))
    return dict(topics=topics, deps=deps, qs=qs, std_items=std_items, errs=errs, verified=len(res["auto_verified"]))
