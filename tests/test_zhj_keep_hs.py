# -*- coding: utf-8 -*-
"""初中语文重建时只删 cnc_j 自己的边，保留高中指向初中的跨段边。不写 data/。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from zhj_build import strip_junior_deps  # noqa: E402


def test_keeps_senior_and_primary_edges():
    edges = [
        {"topicId": "cnc_j001", "prerequisiteId": "cnc_p469", "strength": "hard", "reason": "初中边"},
        {"topicId": "cnc_j002", "prerequisiteId": "cnc_j001", "strength": "soft", "reason": "初中内部"},
        {"topicId": "cnc_h077", "prerequisiteId": "cnc_j013", "strength": "hard", "reason": "高中论语"},
        {"topicId": "cnc_h016", "prerequisiteId": "cnc_p056", "strength": "hard", "reason": "高中到小学"},
        {"topicId": "cnc_p010", "prerequisiteId": "cnc_p001", "strength": "hard", "reason": "小学"},
    ]
    out = strip_junior_deps(edges)
    topics = [e["topicId"] for e in out]
    assert "cnc_j001" not in topics
    assert "cnc_j002" not in topics
    assert "cnc_h077" in topics
    assert "cnc_h016" in topics
    assert "cnc_p010" in topics
    kept = {(e["topicId"], e["prerequisiteId"]) for e in out}
    assert ("cnc_h077", "cnc_j013") in kept
    assert ("cnc_h016", "cnc_p056") in kept


if __name__ == "__main__":
    test_keeps_senior_and_primary_edges()
    print("ok")
