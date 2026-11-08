#!/usr/bin/env python3
"""初中道法入库安全：缺模块不得删已有 cnd_j，排序不得改 id。"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import jmor_build as B  # noqa: E402
import jmor_lib as L  # noqa: E402


def test_lost_ids_are_rejected():
    lost = B.lost_junior_ids({"cnd_j001", "cnd_j099"}, ["cnd_j001", "cnd_j002"])
    assert lost == ["cnd_j099"], lost
    assert B.lost_junior_ids({"cnd_j001"}, ["cnd_j001", "cnd_j002"]) == []


def test_sort_keeps_ids():
    rows = [
        {"id": "cnd_j010", "grade": 7, "semester": "上", "unit": 1},
        {"id": "cnd_j002", "grade": 7, "semester": "上", "unit": 1},
    ]
    B.sort_topics(rows)
    assert [r["id"] for r in rows] == ["cnd_j002", "cnd_j010"]


def test_coverage_does_not_claim_four_books():
    rows = [{"grade": 7, "semester": "上"}] * 4
    text = B.coverage_text(rows)
    assert "4 个知识点" in text
    assert "七上" in text
    assert "这不是四册全覆盖" in text
    assert "七下" not in text and "八上" not in text


def test_missing_module_does_not_write():
    tmp = tempfile.mkdtemp(prefix="jmor-safety-")
    real_root = B.ROOT
    saved = list(L.TOPICS)
    try:
        data = {
            "topics.json": [{"id": "cnd_j001", "name": "甲"}, {"id": "cnd_j099", "name": "乙"}, {"id": "cnd_p001", "name": "小学"}],
            "dependencies.json": [],
            "questions.json": [{"id": "cnd_j099_q1", "topicId": "cnd_j099"}],
            "cn-curriculum-standards.json": {"items": [], "morality": {"note": "小学保留"}},
        }
        for name, obj in data.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False)
        snap = {name: open(os.path.join(tmp, name), "rb").read() for name in data}
        os.makedirs(os.path.join(tmp, "data"))
        for name in data:
            shutil.move(os.path.join(tmp, name), os.path.join(tmp, "data", name))
        snap_paths = {name: open(os.path.join(tmp, "data", name), "rb").read() for name in data}
        assert snap_paths  # files moved
        B.ROOT = tmp
        # 模拟缺模块：待生成 id 不含已入库的 cnd_j099。
        L.TOPICS[:] = [t for t in saved if t["id"] != "cnd_j099"]
        rc = B.main()
        assert rc == 1, rc
        for name, blob in snap_paths.items():
            got = open(os.path.join(tmp, "data", name), "rb").read()
            assert got == blob, name
        del snap
    finally:
        L.TOPICS[:] = saved
        B.ROOT = real_root
        shutil.rmtree(tmp)


def _data(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def test_real_new_points_shape():
    """真实入库点：每点 4 题、题号唯一、verify 与正确选项一致、待核、inferred、verbatim false。"""
    topics = [t for t in _data("topics.json") if str(t.get("id", "")).startswith("cnd_j")]
    assert topics, "没有真实初中点"
    questions = [q for q in _data("questions.json") if str(q.get("topicId", "")).startswith("cnd_j")]
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "题号重复"
    by_topic = {}
    for q in questions:
        by_topic.setdefault(q["topicId"], []).append(q)
    for topic in topics:
        _assert_pending_inferred(topic)
        group = by_topic.get(topic["id"], [])
        assert len(group) == 4, (topic["id"], len(group))
        numbers = []
        for q in group:
            tail = q["id"].split("_q", 1)[1]
            assert tail.isdigit(), q["id"]
            numbers.append(int(tail))
            chosen = next(c["text"] for c in q["choices"] if c["key"] == q["answer"])
            assert json.loads(q["verify"]) == chosen, q["id"]
        assert len(set(numbers)) == 4, topic["id"]
    items = [it for it in _data("cn-curriculum-standards.json").get("items", []) if str(it.get("id", "")).startswith("cds-2022:4.")]
    assert items, "没有第四学段课标"
    assert all(it.get("verbatim") is False for it in items)


# 八下道法课名锚点。来源是公开目录转述，不是官方逐课核实。
# 每课可对应多个知识点；点数随再生变化，这里不写死当前的 24。
G8B_PUBLIC_CATALOG_LESSONS = {
    "治国安邦的总章程",
    "维护宪法权威",
    "公民的基本权利和义务",
    "依法行使权利和履行义务",
    "我国的政治制度",
    "我国的基本经济制度",
    "国家权力机关",
    "中华人民共和国主席",
    "国家行政机关",
    "中央军事委员会",
    "国家监察机关",
    "国家司法机关",
    "坚持全面依法治国",
    "以法治推进国家治理现代化",
}


def _assert_pending_inferred(topic):
    """与真实入库形状相同：catalog 待核，课标置信度为 inferred。"""
    assert topic.get("catalog_status") == L.CATALOG_STATUS, topic["id"]
    assert topic["standards"][0]["confidence"] == "inferred", topic["id"]


def test_g8b_public_catalog_lessons():
    """八下 cnd_j 的课名集合等于公开目录 14 课。

    集合来自公开目录，不是官方逐课核实。不要求每课一点：一课可有多点，
    因此不断言知识点总数（当前计数不必写死）。
    """
    rows = [
        t for t in _data("topics.json")
        if str(t.get("id", "")).startswith("cnd_j")
        and t.get("grade") == 8
        and t.get("semester") == "下"
    ]
    assert rows, "没有八下道法点"
    lessons = {t.get("lesson") for t in rows}
    assert lessons == G8B_PUBLIC_CATALOG_LESSONS, sorted(lessons ^ G8B_PUBLIC_CATALOG_LESSONS)
    assert len(rows) >= len(G8B_PUBLIC_CATALOG_LESSONS)
    for topic in rows:
        _assert_pending_inferred(topic)


def test_independent_root_allowed():
    incoming = {src for src, _dst, _strength, _reason in L.EDGES}
    roots = [t for t in L.TOPICS if t["key"] not in incoming]
    assert roots, "本批应允许没有先修的独立根"
    stored = {t["id"]: t for t in _data("topics.json") if str(t.get("id", "")).startswith("cnd_j")}
    for spec in roots:
        assert spec.get("root_reason"), spec["id"]
        assert stored[spec["id"]].get("root_reason"), spec["id"]


if __name__ == "__main__":
    test_lost_ids_are_rejected()
    test_sort_keeps_ids()
    test_coverage_does_not_claim_four_books()
    test_missing_module_does_not_write()
    test_real_new_points_shape()
    test_g8b_public_catalog_lessons()
    test_independent_root_allowed()
    print("test_jmor_safety ok")
