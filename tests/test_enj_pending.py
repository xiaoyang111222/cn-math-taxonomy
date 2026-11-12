#!/usr/bin/env python3
"""初中英语 65 个待核点的两类标记：数据、规格和文档一致，且不改挂、不改题。"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import en_lib  # noqa: E402

en_lib.TOPICS.clear()
en_lib.HARD.clear()
import enj_topics  # noqa: E402,F401
import enj_pending as P  # noqa: E402
from en_lib import TOPICS  # noqa: E402

DOC = os.path.join(ROOT, P.DOC_PATH)
TOPICS_PATH = os.path.join(ROOT, "data", "topics.json")
QUESTIONS_PATH = os.path.join(ROOT, "data", "questions.json")
DEPS_PATH = os.path.join(ROOT, "data", "dependencies.json")
BUILD_PATH = os.path.join(ROOT, "scripts", "enj_build.py")

# 题目、先修和道法 catalog_status 在分类之前锁定。CORE_SHA 只含 id、点名、描述、年级、学期、章节、领域、题型，
# 不含 catalog_status / catalog_note。只改这两项取值时 CORE_SHA 不变。
QUESTION_SHA = "775f38979fc05bc292fc13872ced180aa24c5056dc8351414105be2b9c8761ad"
EDGE_SHA = "7974e573d6e169951d1bc87666236bebd683e3f11048176cddbbede427b28c66"
CORE_SHA = "c9b08b8b71d43e49a3d6a4f3b374466bcb23c05453251de7cd62ccf05702e962"
MORALITY_SHA = "8b377550178306ebd1883671a85939c30ff9ae8a19f3952ad0b418fd0863d870"

# 2026-11-12 从证据不足改为已核未见课业的八上 10 点、九上 33 点。
# 原先已是第一类的 22 点，加上八上这 10 点，分类取值保持。
G8A_RECLASS = (
    "cne_j113", "cne_j115", "cne_j116", "cne_j117", "cne_j119", "cne_j120",
    "cne_j133", "cne_j135", "cne_j138", "cne_j141",
)
G9A_RECLASS = (
    "cne_j191", "cne_j194", "cne_j195", "cne_j196", "cne_j198", "cne_j199",
    "cne_j207", "cne_j212", "cne_j213", "cne_j214", "cne_j215", "cne_j216",
    "cne_j217", "cne_j218", "cne_j219", "cne_j228", "cne_j229", "cne_j230",
    "cne_j231", "cne_j232", "cne_j233", "cne_j234", "cne_j235", "cne_j236",
    "cne_j237", "cne_j238", "cne_j239", "cne_j240", "cne_j241", "cne_j242",
    "cne_j243", "cne_j244", "cne_j245",
)
BODY_CHECKED_KEPT = (
    "cne_j053", "cne_j054", "cne_j055", "cne_j056", "cne_j097",
    "cne_j134", "cne_j136",
    "cne_j156", "cne_j157", "cne_j172", "cne_j178", "cne_j180",
    "cne_j181", "cne_j182", "cne_j183", "cne_j185", "cne_j186", "cne_j225",
    "cne_j188", "cne_j201", "cne_j204", "cne_j206",
)

VOL_CHAPTER = {
    "七年级上册": (7, "上", "七年级上册 待核"),
    "七年级下册": (7, "下", "七年级下册 待核"),
    "八年级上册": (8, "上", "八年级上册 待核"),
    "八年级下册": (8, "下", "八年级下册 待核"),
    "九年级上册": (9, "上", "九年级上册 待核"),
}


def _load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def _sha(obj):
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_spec_covers_generator_unit_90():
    """生成器里每个 unit 90 都有分类，且重编号后的 id 与规格一致。"""
    assert len(P.BY_ID) == 65
    assert set(P.ALLOWED_STATUS) == {P.BODY_CHECKED_NO_LESSON, P.EVIDENCE_INSUFFICIENT}
    for forbidden in P.MORALITY_STATUS:
        assert forbidden not in P.ALLOWED_STATUS
    id_of = {}
    unit90 = []
    for i, spec in enumerate(TOPICS, start=1):
        tid = "cne_j%03d" % i
        id_of[spec["key"]] = tid
        topic = {"id": tid, "name": spec["name"], "chapter": "placeholder"}
        P.attach_pending(topic, spec)
        if spec["unit"] == 90:
            unit90.append(spec)
            assert topic["catalog_status"] in P.ALLOWED_STATUS
            assert topic["catalog_note"]
            assert "catalog_status" in topic and "catalog_note" in topic
        else:
            assert "catalog_status" not in topic
            assert "catalog_note" not in topic
    assert len(unit90) == 65
    assert {id_of[spec["key"]] for spec in unit90} == set(P.BY_ID)
    for spec in unit90:
        rec = P.BY_KEY[spec["key"]]
        assert id_of[spec["key"]] == rec["id"]
        assert spec["name"] == rec["name"]
        assert spec["unit"] == 90


def test_attach_keeps_been_gone_wording():
    spec = {"key": "gr_been", "unit": 90, "name": "been 与 gone"}
    topic = {"id": "cne_j180", "name": "been 与 gone"}
    P.attach_pending(topic, spec)
    assert topic["catalog_status"] == P.BODY_CHECKED_NO_LESSON
    assert "教材已教" in topic["catalog_note"]
    assert "单元归属未定" in topic["catalog_note"]
    assert "不是「书里没教」" in topic["catalog_note"]
    try:
        P.attach_pending({"id": "cne_j180", "name": "been 与 gone"}, {"key": "gr_been", "unit": 7, "name": "been 与 gone"})
    except SystemExit:
        pass
    else:
        raise AssertionError("已确认单元不应带待核分类")


def test_build_source_copies_classification():
    """静态检查：全新编译会抄上分类，且本脚本拒绝往已有 cne_j 的库里追加。"""
    src = open(BUILD_PATH, encoding="utf-8").read()
    assert "attach_pending(topic, spec)" in src
    assert "已经有 cne_j 知识点。enj_build.py 不能重复编译。" in src
    before = hashlib.sha256(open(TOPICS_PATH, "rb").read()).hexdigest()
    subprocess.check_call([sys.executable, "-c", "import enj_build"], cwd=os.path.join(ROOT, "scripts"))
    after = hashlib.sha256(open(TOPICS_PATH, "rb").read()).hexdigest()
    assert before == after, "导入 enj_build 不应写回 data/"


def test_data_marks_match_spec_and_leave_mounts():
    topics = _load("topics.json")
    by_id = {t["id"]: t for t in topics}
    core = []
    for tid, rec in sorted(P.BY_ID.items()):
        topic = by_id[tid]
        vol = P._volume(tid)
        grade, semester, chapter = VOL_CHAPTER[vol]
        assert topic["name"] == rec["name"]
        assert topic["grade"] == grade
        assert topic["semester"] == semester
        assert topic["chapter"] == chapter
        assert topic["catalog_status"] == rec["catalog_status"]
        assert topic["catalog_note"] == rec["catalog_note"]
        assert topic["catalog_status"] not in P.MORALITY_STATUS
        assert "第90单元" not in topic["chapter"]
        core.append({
            "id": topic["id"],
            "name": topic["name"],
            "description": topic["description"],
            "grade": topic["grade"],
            "semester": topic["semester"],
            "chapter": topic["chapter"],
            "domain": topic["domain"],
            "type": topic["type"],
        })
    assert _sha(core) == CORE_SHA
    extra = [
        t["id"] for t in topics
        if str(t.get("id", "")).startswith("cne_") and "catalog_status" in t and t["id"] not in P.BY_ID
    ]
    assert extra == []
    pending = [
        t["id"] for t in topics
        if str(t.get("id", "")).startswith("cne_j") and str(t.get("chapter", "")).endswith(" 待核")
    ]
    assert set(pending) == set(P.BY_ID)


def test_questions_and_edges_unchanged():
    ids = set(P.BY_ID)
    questions = [q for q in _load("questions.json") if q.get("topicId") in ids]
    assert len(questions) == 65 * 4
    assert _sha(questions) == QUESTION_SHA
    edges = [
        e for e in _load("dependencies.json")
        if e.get("topicId") in ids or e.get("prerequisiteId") in ids
    ]
    assert _sha(edges) == EDGE_SHA


def test_morality_catalog_status_unchanged():
    rows = [(t["id"], t.get("catalog_status")) for t in _load("topics.json") if str(t.get("id", "")).startswith("cnd_j")]
    assert rows
    assert _sha(rows) == MORALITY_SHA
    for tid, status in rows:
        assert status in P.MORALITY_STATUS, tid
        assert status not in P.ALLOWED_STATUS


def test_doc_matches_spec():
    text = open(DOC, encoding="utf-8").read()
    assert text == P.render_doc()
    for tid, rec in P.BY_ID.items():
        label = P.LABEL[rec["catalog_status"]]
        assert ("`%s`" % tid) in text
        assert label in text
    counts = P.count_by_volume()
    assert sum(bucket[P.BODY_CHECKED_NO_LESSON] for bucket in counts.values()) == 65
    assert sum(bucket[P.EVIDENCE_INSUFFICIENT] for bucket in counts.values()) == 0
    assert counts["七年级上册"] == {P.BODY_CHECKED_NO_LESSON: 4, P.EVIDENCE_INSUFFICIENT: 0}
    assert counts["七年级下册"] == {P.BODY_CHECKED_NO_LESSON: 1, P.EVIDENCE_INSUFFICIENT: 0}
    assert counts["八年级上册"] == {P.BODY_CHECKED_NO_LESSON: 12, P.EVIDENCE_INSUFFICIENT: 0}
    assert counts["八年级下册"] == {P.BODY_CHECKED_NO_LESSON: 11, P.EVIDENCE_INSUFFICIENT: 0}
    assert counts["九年级上册"] == {P.BODY_CHECKED_NO_LESSON: 37, P.EVIDENCE_INSUFFICIENT: 0}
    assert len(G8A_RECLASS) == 10
    assert len(G9A_RECLASS) == 33
    assert len(BODY_CHECKED_KEPT) == 22
    assert set(G8A_RECLASS).isdisjoint(G9A_RECLASS)
    assert set(BODY_CHECKED_KEPT).isdisjoint(G9A_RECLASS)
    assert set(BODY_CHECKED_KEPT).isdisjoint(G8A_RECLASS)
    for tid in G8A_RECLASS:
        rec = P.BY_ID[tid]
        assert rec["catalog_status"] == P.BODY_CHECKED_NO_LESSON
        assert "不改挂" in rec["catalog_note"]
        assert "g8a-evidence-20261112/notes.md" in rec["evidence"]
        assert P._volume(tid) == "八年级上册"
    for tid in BODY_CHECKED_KEPT:
        assert P.BY_ID[tid]["catalog_status"] == P.BODY_CHECKED_NO_LESSON
    for tid in G9A_RECLASS:
        rec = P.BY_ID[tid]
        assert rec["catalog_status"] == P.BODY_CHECKED_NO_LESSON
        assert "印刷页 1–80" in rec["catalog_note"] or "不改挂" in rec["catalog_note"]
        assert "g9a-evidence-20261112" in rec["evidence"]
        assert P._volume(tid) == "九年级上册"
    assert "cne_j253" in P.BY_ID["cne_j242"]["catalog_note"]
    assert "remember doing" in P.BY_ID["cne_j242"]["catalog_note"]
    assert "不改挂" in P.BY_ID["cne_j242"]["catalog_note"]
    assert "书页49发明介绍写作不是读材料产地介绍" in P.BY_ID["cne_j207"]["catalog_note"]
    assert "书页99产品听力不是阅读任务" in P.BY_ID["cne_j207"]["catalog_note"]
    assert "Changes in My Life 不是毕业回忆" in P.BY_ID["cne_j241"]["catalog_note"]
    assert all(row["catalog_status"] == P.BODY_CHECKED_NO_LESSON for row in P.BY_ID.values())


def main():
    test_spec_covers_generator_unit_90()
    test_attach_keeps_been_gone_wording()
    test_build_source_copies_classification()
    test_data_marks_match_spec_and_leave_mounts()
    test_questions_and_edges_unchanged()
    test_morality_catalog_status_unchanged()
    test_doc_matches_spec()
    print("ok 7")
    return 0


if __name__ == "__main__":
    sys.exit(main())
