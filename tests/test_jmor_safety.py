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
    full = [
        {"grade": 7, "semester": "上"},
        {"grade": 7, "semester": "下"},
        {"grade": 8, "semester": "上"},
        {"grade": 8, "semester": "下"},
        {"grade": 9, "semester": "上"},
    ]
    full_text = B.coverage_text(full)
    assert "已有七上至九上，已按官方阅读器目录改挂，九下未建点，不是六册全覆盖" in full_text
    assert "这不是四册全覆盖" in full_text


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
    """真实入库点：每点 4 题、题号唯一、verify 与正确选项一致、官方目录或待核桶、inferred、verbatim false。"""
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


# 八下道法课名锚点。来源是智慧教育平台官方阅读器目录，14 课。
# 每课可对应多个知识点；点数随再生变化，这里不写死当前的 24。
G8B_OFFICIAL_LESSONS = {
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


VOLUME_ISBN = {
    (7, "上"): "978-7-107-38238-3",
    (7, "下"): "978-7-107-38239-0",
    (8, "上"): "978-7-107-39650-2",
    (8, "下"): "978-7-107-40548-8",
    (9, "上"): "978-7-107-41303-2",
}


def _assert_pending_inferred(topic):
    """已确认点 catalog 为 official_toc；待核桶为 pending。课标置信度都是 inferred。"""
    chapter = topic.get("chapter") or ""
    if chapter.endswith(" 待核"):
        assert topic.get("catalog_status") == L.CATALOG_STATUS, topic["id"]
        assert "第90单元" not in chapter, topic["id"]
    else:
        assert topic.get("catalog_status") == L.OFFICIAL_CATALOG_STATUS, topic["id"]
        isbn = VOLUME_ISBN[(topic["grade"], topic["semester"])]
        assert isbn in (topic.get("standards") or [{}])[0].get("note", ""), topic["id"]
    assert topic["standards"][0]["confidence"] == "inferred", topic["id"]


# 九上官方阅读器目录的 10 课。不是课文正文逐字核对。
G9A_OFFICIAL_LESSONS = {
    "百年大党风华正茂",
    "坚持以人民为中心",
    "党是领导一切的",
    "新的历史方位",
    "新时代的思想旗帜",
    "中国腾飞谱新篇",
    "擘画宏伟蓝图",
    "实现高质量发展",
    "凝聚团结伟力",
    "实现伟大梦想",
}


def test_g9a_official_toc_not_g9b():
    """九上 10 课按官方目录，九下不建点；七至八年级已确认点也是 official_toc。"""
    rows = [
        t for t in _data("topics.json")
        if str(t.get("id", "")).startswith("cnd_j") and t.get("grade") == 9
    ]
    assert rows, "没有九年级道法点"
    assert all(t.get("semester") == "上" for t in rows)
    lessons = {t.get("lesson") for t in rows}
    assert lessons == G9A_OFFICIAL_LESSONS, sorted(lessons ^ G9A_OFFICIAL_LESSONS)
    assert all(t.get("catalog_status") == "official_toc" for t in rows)
    blob = "\n".join((t.get("lesson") or "") + "\n" + (t.get("frames") or "") + "\n" + (t.get("name") or "") for t in rows)
    assert "恢弘" not in blob
    assert "书写恢宏史诗" in blob
    assert "“两步走”战略" in blob
    assert any(t.get("lesson") == "实现高质量发展" and "推动高质量发展" in (t.get("frames") or "") for t in rows)
    assert any(t.get("lesson") == "实现伟大梦想" for t in rows)
    assert all("单元思考与行动" not in (t.get("lesson") or "") for t in rows)
    assert all("978-7-107-41303-2" in (t.get("standards") or [{}])[0].get("note", "") for t in rows)
    assert all(t["standards"][0]["confidence"] == "inferred" for t in rows)
    older = [
        t for t in _data("topics.json")
        if str(t.get("id", "")).startswith("cnd_j") and t.get("grade") in (7, 8)
    ]
    assert older and all(t.get("catalog_status") == L.OFFICIAL_CATALOG_STATUS for t in older)


def test_g8b_public_catalog_lessons():
    """八下 cnd_j 的课名集合等于官方目录 14 课。

    集合来自智慧教育平台官方阅读器目录。不要求每课一点：一课可有多点，
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
    assert lessons == G8B_OFFICIAL_LESSONS, sorted(lessons ^ G8B_OFFICIAL_LESSONS)
    assert len(rows) >= len(G8B_OFFICIAL_LESSONS)
    for topic in rows:
        _assert_pending_inferred(topic)


G7A_OFFICIAL_LESSONS = {
    "开启初中生活", "正确认识自我", "梦想始于当下", "幸福和睦的家庭",
    "和谐的师生关系", "友谊之树常青", "在集体中成长", "生命可贵",
    "守护生命安全", "保持身心健康", "确立人生目标", "端正人生态度", "实现人生价值",
}
G7B_OFFICIAL_LESSONS = {
    "青春正当时", "做情绪情感的主人", "人贵自尊", "自信给人力量", "人生当自强",
    "传承核心思想理念", "弘扬中华人文精神", "践行中华传统美德",
    "法律为我们护航", "走近民法典", "远离违法犯罪",
}
G8A_OFFICIAL_LESSONS = {
    "丰富的社会生活", "在社会中健康成长", "共建网络美好家园", "遵守社会规则",
    "社会生活讲道德", "提升法治素养", "追求自由平等", "维护公平正义",
    "积极奉献社会", "国家利益至上", "军强才能国安", "树立总体国家安全观",
}
UNBUILT_OFFICIAL_FRAMES = set()
BUILT_OFFICIAL_FRAMES = {
    "cnd_j107": "在奉献中成就精彩人生",
    "cnd_j108": "认识民法典",
    "cnd_j109": "友善待人",
    "cnd_j110": "国家行政机关的性质和职权",
}
WRAPPED_G8B_FRAMES = {
    "中国共产党领导的多党合作和政治协商制度",
    "公有制为主体、多种所有制经济共同发展",
    "按劳分配为主体、多种分配方式并存",
}


def _junior_rows(grade=None, semester=None):
    rows = [t for t in _data("topics.json") if str(t.get("id", "")).startswith("cnd_j")]
    if grade is not None:
        rows = [t for t in rows if t.get("grade") == grade]
    if semester is not None:
        rows = [t for t in rows if t.get("semester") == semester]
    return rows


def test_g78_official_toc_lessons_and_unbuilt_frames():
    """七至八年级已确认点挂官方课名；四个原空框已由新点覆盖；不建单元思考与行动。"""
    g7a = _junior_rows(7, "上")
    g7b = _junior_rows(7, "下")
    g8a = _junior_rows(8, "上")
    g8b = _junior_rows(8, "下")
    assert {t.get("lesson") for t in g7a} == G7A_OFFICIAL_LESSONS
    assert {t.get("lesson") for t in g7b} == G7B_OFFICIAL_LESSONS
    assert {t.get("lesson") for t in g8a} == G8A_OFFICIAL_LESSONS
    assert {t.get("lesson") for t in g8b} == G8B_OFFICIAL_LESSONS
    all_g78 = g7a + g7b + g8a + g8b
    assert all(t.get("catalog_status") == "official_toc" for t in all_g78)
    assert all("单元思考与行动" not in ((t.get("lesson") or "") + (t.get("frames") or "") + (t.get("chapter") or "") + (t.get("name") or "")) for t in all_g78)
    frame_blob = "\n".join(t.get("frames") or "" for t in all_g78)
    for missing in UNBUILT_OFFICIAL_FRAMES:
        assert missing not in frame_blob, missing
    for wrapped in WRAPPED_G8B_FRAMES:
        assert any(wrapped in (t.get("frames") or "") for t in g8b), wrapped
    j025 = next(t for t in g7a if t["id"] == "cnd_j025")
    assert j025["frames"] == "在劳动中创造人生价值"
    j040 = next(t for t in g7b if t["id"] == "cnd_j040")
    assert j040["frames"] == "保护人身权；保障财产权"
    assert "认识民法典" in (j040.get("standards") or [{}])[0].get("note", "")
    j077 = next(t for t in g8b if t["id"] == "cnd_j077")
    assert j077["frames"] == "依法行政，建设法治政府"
    assert next(t for t in g7a if t["id"] == "cnd_j107")["frames"] == BUILT_OFFICIAL_FRAMES["cnd_j107"]
    assert next(t for t in g7b if t["id"] == "cnd_j108")["frames"] == BUILT_OFFICIAL_FRAMES["cnd_j108"]
    assert next(t for t in g8a if t["id"] == "cnd_j109")["frames"] == BUILT_OFFICIAL_FRAMES["cnd_j109"]
    assert next(t for t in g8b if t["id"] == "cnd_j110")["frames"] == BUILT_OFFICIAL_FRAMES["cnd_j110"]
    assert len(g7a) == 26
    assert len(g7b) == 19
    assert len(g8a) == 19
    assert len(g8b) == 25
    j078 = next(t for t in g8b if t["id"] == "cnd_j078")
    j079 = next(t for t in g8b if t["id"] == "cnd_j079")
    assert j078["frames"] == "中央军事委员会的领导体制和职权"
    assert j079["frames"] == "中央军事委员会的性质和产生"
    assert all(VOLUME_ISBN[(t["grade"], t["semester"])] in (t.get("standards") or [{}])[0].get("note", "") for t in all_g78)


def test_pending_unit_hook():
    """unit 90 章节为「N年级X册 待核」，不要拼成第90单元。"""
    saved_units = dict(L.UNITS)
    saved_cur = dict(L._CUR)
    try:
        L.vol(7, "上")
        L.unit(90, "待核")
        assert L.chapter(7, "上", 90) == "七年级上册 待核"
        L.vol(8, "下")
        L.unit(90, "待核")
        assert L.chapter(8, "下", 90) == "八年级下册 待核"
        assert "第90单元" not in L.chapter(7, "上", 90)
        assert "第90单元" not in L.chapter(8, "下", 90)
        L.vol(7, "上")
        try:
            L.unit(90, "少年有梦")
        except SystemExit:
            pass
        else:
            raise AssertionError("unit 90 标题必须是待核")
    finally:
        L.UNITS.clear()
        L.UNITS.update(saved_units)
        L._CUR.clear()
        L._CUR.update(saved_cur)


def test_grade9_xia_and_quan_rejected():
    saved_cur = dict(L._CUR)
    try:
        L.vol(9, "下")
        try:
            L.unit(1, "不应写入")
        except SystemExit:
            pass
        else:
            raise AssertionError("九下应当拒绝")
        assert (9, "下", 1) not in L.UNITS
        L.vol(9, "全")
        try:
            L.unit(1, "不应写入")
        except SystemExit:
            pass
        else:
            raise AssertionError("九全应当拒绝")
        assert (9, "全", 1) not in L.UNITS
    finally:
        L._CUR.clear()
        L._CUR.update(saved_cur)


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
    test_g9a_official_toc_not_g9b()
    test_g78_official_toc_lessons_and_unbuilt_frames()
    test_pending_unit_hook()
    test_grade9_xia_and_quan_rejected()
    test_independent_root_allowed()
    print("test_jmor_safety ok")
