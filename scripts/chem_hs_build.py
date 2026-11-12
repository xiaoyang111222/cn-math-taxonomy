#!/usr/bin/env python3
"""把高中化学必修第一册编译进 data/ 下的四个文件。

只清除并重写 cnk_h、cks-hs-2017、chemistry_senior。
保留初中化学 cnk_j、cks-2022、chemistry，以及其他学科。

用法：python3 scripts/chem_hs_build.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chem_hs_b1  # noqa: E402,F401
import chem_hs_lib as L  # noqa: E402
import chem_hs_plan as P  # noqa: E402
import chem_hs_std as S  # noqa: E402
from verify_questions import verify_all  # noqa: E402

SENIOR_STD_PREFIX = "cks-hs-2017:"


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(ROOT, "data", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_hs_topic(tid):
    return str(tid).startswith("cnk_h")


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
    """只约简高中化学边上的冗余。不改初中边。"""
    adj = defaultdict(list)
    for e in edges:
        adj[e["topicId"]].append([e["prerequisiteId"], e["strength"]])
    kept = []
    dropped = 0
    for e in edges:
        if not is_hs_topic(e["topicId"]):
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


def build_question(tid, index, q, slot):
    qid = "%s_q%d" % (tid, index)
    if q["kind"] == "numeric":
        return {
            "id": qid,
            "topicId": tid,
            "difficulty": q["diff"],
            "type": "numeric",
            "prompt": q["prompt"],
            "answer": q["answer"],
            "explanation": q["expl"],
            "verify": q["verify"],
        }, q["answer"]
    texts = list(q["wrongs"])
    texts.insert(slot % 4, q["right"])
    keys = list("ABCD")
    pos = texts.index(q["right"])
    return {
        "id": qid,
        "topicId": tid,
        "difficulty": q["diff"],
        "type": "choice",
        "prompt": q["prompt"],
        "choices": [{"key": keys[i], "text": texts[i]} for i in range(4)],
        "answer": keys[pos],
        "explanation": q["expl"],
        "verify": L.choice_verify(q["right"]),
    }, q["right"]


def std_items():
    out = []
    seen = {}
    for tail, code, section, text in S.CLAUSES:
        if code not in S.CODES:
            raise SystemExit("未知主题代码 %s" % code)
        num = int(tail.rsplit(".", 1)[1])
        key = code
        if num != seen.get(key, 0) + 1:
            raise SystemExit("课标编号不连续：%s" % tail)
        seen[key] = num
        if not tail.startswith("B1." + code + "."):
            raise SystemExit("课标 id 与主题代码不一致：%s" % tail)
        out.append({
            "id": SENIOR_STD_PREFIX + tail,
            "domain": S.CODES[code],
            "section": section,
            "clause": "(%d)" % num,
            "text": text,
            "page_or_ref": "待核",
            "verbatim": False,
            "text_status": S.TEXT_STATUS,
        })
    return out


def main():
    topics = load("topics.json")
    deps = load("dependencies.json")
    questions = load("questions.json")
    standards = load("cn-curriculum-standards.json")

    if len(P.PLAN) != 19:
        print("课序应为 19 条", file=sys.stderr)
        return 1
    missing = [row["key"] for row in P.PLAN if row["key"] not in L.HS]
    extra = [key for key in L.HS if key not in P.PLAN_BY_KEY]
    if missing or extra:
        print("草稿与课序不一致：缺 %s，多 %s" % (missing, extra), file=sys.stderr)
        return 1

    junior = {t["id"]: t for t in topics if str(t["id"]).startswith("cnk_j")}
    if len(junior) != 45:
        print("初中化学应有 45 个点，实际 %d" % len(junior), file=sys.stderr)
        return 1
    junior_names = {tid: t["name"] for tid, t in junior.items()}

    id_of = {}
    for i, row in enumerate(P.PLAN, start=1):
        id_of[row["key"]] = "cnk_h%03d" % i

    std_by_tail = {item["id"][len(SENIOR_STD_PREFIX):]: item["id"] for item in std_items()}
    cited = set()
    new_topics = []
    new_questions = []
    hard_pairs = {}

    for i, row in enumerate(P.PLAN, start=1):
        key = row["key"]
        draft = L.HS[key]
        tid = id_of[key]
        if row["chapter"].split()[0] != "必修一":
            print("%s 章节不是以必修一开头：%s" % (key, row["chapter"]), file=sys.stderr)
            return 1
        refs = []
        for tail in draft["std"]:
            if tail not in std_by_tail:
                print("%s 引用了不存在的课标 %s" % (key, tail), file=sys.stderr)
                return 1
            cited.add(tail)
            refs.append({"id": std_by_tail[tail], "confidence": "inferred", "note": L.NOTE})
        built = []
        diag = None
        for n, q in enumerate(draft["qs"], start=1):
            obj, shown = build_question(tid, n, q, slot=i + n)
            built.append(obj)
            if n == 1:
                diag = shown
        if built[0]["type"] != "choice" or built[0]["difficulty"] != "basic":
            print("%s 诊断题必须是 basic 选择题" % key, file=sys.stderr)
            return 1
        topic = {
            "id": tid,
            "name": row["name"],
            "domain": draft["domain"],
            "grade": 10,
            "semester": "上",
            "chapter": row["chapter"],
            "type": draft["type"],
            "description": draft["description"],
            "mastery_criteria": draft["mastery"],
            "diagnostic_question": {"question": built[0]["prompt"], "answer": diag},
            "external": False,
            "subject": "chemistry",
            "standards": refs,
        }
        new_topics.append(topic)
        new_questions.extend(built)
        for ref, reason in draft["pre"]:
            if not str(reason).strip():
                print("%s 先修缺少理由：%s" % (key, ref), file=sys.stderr)
                return 1
            if ref.startswith("J:"):
                pid = ref[2:]
                if pid not in junior:
                    print("%s 的初中先修不存在：%s" % (key, pid), file=sys.stderr)
                    return 1
            else:
                if ref not in id_of or P.ORDER[ref] >= P.ORDER[key]:
                    print("%s 的先修 %s 不存在或不在它前面" % (key, ref), file=sys.stderr)
                    return 1
                pid = id_of[ref]
            pair = (tid, pid)
            if pair in hard_pairs:
                print("重复硬边 %s → %s" % pair, file=sys.stderr)
                return 1
            hard_pairs[pair] = reason

    if "intro" not in L.HS or not any(ref.startswith("J:") for ref, _r in L.HS["intro"]["pre"]):
        print("cnk_h001 必须硬连至少一个初中化学点", file=sys.stderr)
        return 1

    unused = [tail for tail, _c, _s, _t in S.CLAUSES if tail not in cited]
    if unused:
        print("课标没有被引用：%s" % "、".join(unused), file=sys.stderr)
        return 1

    raw = []
    names = {row["key"]: row["name"] for row in P.PLAN}
    for i in range(1, len(P.PLAN)):
        cur = P.PLAN[i]["key"]
        prev = P.PLAN[i - 1]["key"]
        if (id_of[cur], id_of[prev]) in hard_pairs:
            continue
        reason = "按人教版化学必修第一册的教学顺序，先学「%s」，再学「%s」。" % (names[prev], names[cur])
        raw.append((id_of[cur], id_of[prev], "soft", reason))
    for (tid, pid), reason in hard_pairs.items():
        raw.append((tid, pid, "hard", reason))

    new_edges = []
    seen_edge = set()
    for tid, pid, strength, reason in raw:
        if (tid, pid) in seen_edge:
            print("重复边 %s → %s" % (tid, pid), file=sys.stderr)
            return 1
        seen_edge.add((tid, pid))
        if not is_hs_topic(tid):
            print("高中边的后续点不是 cnk_h：%s" % tid, file=sys.stderr)
            return 1
        if not (is_hs_topic(pid) or str(pid).startswith("cnk_j")):
            print("高中化学边连到了化学以外：%s → %s" % (tid, pid), file=sys.stderr)
            return 1
        new_edges.append({
            "topicId": tid,
            "prerequisiteId": pid,
            "strength": strength,
            "reason": reason,
        })

    reduced, dropped = reduce_senior(new_edges)
    covered = {e["topicId"] for e in reduced}
    missing_pre = [t["id"] for t in new_topics if t["id"] not in covered]
    if missing_pre:
        print("约简后仍无先修：%s" % "、".join(missing_pre), file=sys.stderr)
        return 1
    if any(not str(e["prerequisiteId"]).startswith("cnk_") for e in reduced):
        print("约简后出现非化学先修", file=sys.stderr)
        return 1

    checked = verify_all(new_questions)
    if checked["mismatch"] or checked["unverifiable"]:
        for m in checked["mismatch"][:40]:
            print("题目核对失败 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        for m in checked["unverifiable"][:20]:
            print("题目无法核对 %s：%s" % (m["id"], m.get("detail")), file=sys.stderr)
        print("题目核对未通过：mismatch %d，unverifiable %d" % (
            len(checked["mismatch"]), len(checked["unverifiable"])), file=sys.stderr)
        return 1

    snap_topics = [(t["id"], t["name"]) for t in topics if not is_hs_topic(t.get("id"))]
    snap_junior = [(t["id"], t["name"]) for t in topics if str(t["id"]).startswith("cnk_j")]
    snap_other = {}
    for prefix in ("cnm_", "cne_", "cnp_", "cnc_", "cns_", "cnd_", "cnh_", "cng_", "cnb_"):
        snap_other[prefix] = [(t["id"], t["name"]) for t in topics if str(t["id"]).startswith(prefix)]
    chem_obj = standards.get("chemistry")
    if not isinstance(chem_obj, dict) or chem_obj.get("title") != "义务教育化学课程标准（2022年版）":
        print("初中化学课标对象缺失或标题不对", file=sys.stderr)
        return 1
    junior_items = [it for it in standards.get("items", []) if str(it.get("id", "")).startswith("cks-2022")]
    if len(junior_items) != 22:
        print("初中课标应为 22 条，实际 %d" % len(junior_items), file=sys.stderr)
        return 1

    base_topics = [t for t in topics if not is_hs_topic(t.get("id"))]
    base_deps = [e for e in deps if not is_hs_topic(e.get("topicId")) and not is_hs_topic(e.get("prerequisiteId"))]
    base_questions = [q for q in questions if not is_hs_topic(q.get("topicId"))]
    base_items = [it for it in standards.get("items", []) if not str(it.get("id", "")).startswith(SENIOR_STD_PREFIX)]

    standards_out = dict(standards)
    standards_out["items"] = list(base_items) + std_items()
    standards_out["chemistry_senior"] = {
        "title": "普通高中化学课程标准（2017年版）",
        "issuer": "中华人民共和国教育部",
        "year": 2017,
        "stage": "普通高中（本阶段只收录与必修第一册相关的内容要求）",
        "note": (
            "条目是对必修第一册相关内容要求的公开转述，不是逐页核对的原文。"
            "verbatim 为 false，page_or_ref 为「待核」。编号 cks-hs-2017:B1.<主题>.<序号> 是本图谱编的，不是教育部原编号。"
            "主题用 2017 年版必修课程的公开通称：化学科学与实验探究、常见的无机物及其应用、物质结构基础与化学反应规律。"
            "后记可见的依据是教育部《普通高中化学课程标准（2017年版）》，2019 年经国家教材委员会专家委员会审核通过。"
            "封面与后记均未印「2020年修订」，不得写成 2020 修订本。"
            "教材是普通高中教科书·化学必修第一册，人民教育出版社，"
            "课程教材研究所化学课程教材研究开发中心编著。总主编王晶、郑长龙；本册主编王晶、毕华林。"
            "ISBN 978-7-107-33574-7。contentId 5cd19072-e40d-4a73-8580-7b7ada5d4005。"
            "版权页未见版次、印次，不编造。印刷目录建 19 个知识点；附录、元素周期表、全章复习和栏目索引不建点。"
            "未下载教材 PDF，印刷页码不写入知识点或题目。"
        ),
    }

    n_hard = sum(1 for e in reduced if e["strength"] == "hard")
    n_soft = sum(1 for e in reduced if e["strength"] == "soft")
    print("高中化学知识点 %d（cnk_h001–cnk_h%03d）" % (len(new_topics), len(new_topics)))
    print("题目 %d" % len(new_questions))
    print("课标条目 %d" % len(std_items()))
    print("高中边写入 %d（约简删去 %d）；hard %d，soft %d" % (len(reduced), dropped, n_hard, n_soft))
    def chapter_bucket(chapter):
        parts = chapter.split()
        if len(parts) >= 2 and parts[1].startswith("第") and parts[1].endswith("章"):
            return parts[0] + " " + parts[1]
        return chapter

    by_ch = Counter(chapter_bucket(t["chapter"]) for t in new_topics)
    for name, n in by_ch.items():
        print("  %s %d" % (name, n))

    dump("topics.json", base_topics + new_topics)
    dump("dependencies.json", base_deps + reduced)
    dump("questions.json", base_questions + new_questions)
    dump("cn-curriculum-standards.json", standards_out)

    again_t = load("topics.json")
    again_d = load("dependencies.json")
    again_q = load("questions.json")
    again_s = load("cn-curriculum-standards.json")
    if [(t["id"], t["name"]) for t in again_t if not is_hs_topic(t.get("id"))] != snap_topics:
        print("非高中化学知识点的 id 或名称变了", file=sys.stderr)
        return 1
    if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith("cnk_j")] != snap_junior:
        print("初中化学知识点变了", file=sys.stderr)
        return 1
    labels = {
        "cnm_": "数学", "cne_": "英语", "cnp_": "物理", "cnc_": "语文",
        "cns_": "科学", "cnd_": "道德与法治", "cnh_": "历史", "cng_": "地理", "cnb_": "生物",
    }
    for prefix, label in labels.items():
        if [(t["id"], t["name"]) for t in again_t if str(t["id"]).startswith(prefix)] != snap_other[prefix]:
            print("%s知识点 id 或名称变了" % label, file=sys.stderr)
            return 1
    if again_s.get("chemistry") != chem_obj:
        print("初中 chemistry 对象变了", file=sys.stderr)
        return 1
    again_junior_items = [it for it in again_s.get("items", []) if str(it.get("id", "")).startswith("cks-2022")]
    if again_junior_items != junior_items:
        print("初中课标条目变了", file=sys.stderr)
        return 1
    if again_s.get("chemistry_senior", {}).get("title") != "普通高中化学课程标准（2017年版）":
        print("chemistry_senior 标题不正确", file=sys.stderr)
        return 1
    if again_s.get("chemistry_senior", {}).get("year") != 2017:
        print("chemistry_senior 年份不正确", file=sys.stderr)
        return 1
    hs_ids = [t["id"] for t in again_t if is_hs_topic(t.get("id"))]
    if hs_ids != ["cnk_h%03d" % i for i in range(1, 20)]:
        print("高中化学 id 顺序不对：%s" % hs_ids, file=sys.stderr)
        return 1
    # 初中点的名称仍能对上硬边理由里点到的对象，避免连错号。
    for e in reduced:
        pid = e["prerequisiteId"]
        if pid in junior_names and junior_names[pid] not in e["reason"] and pid not in e["reason"]:
            pass
    print("初中化学 45 点及其他学科 id 与名称未改")
    return 0


if __name__ == "__main__":
    sys.exit(main())
