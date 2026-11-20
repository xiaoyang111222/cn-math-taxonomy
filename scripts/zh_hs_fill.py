# -*- coding: utf-8 -*-
"""把每课 4 道选择题登记成知识点；先修 = 课文记录里的 pre + zh_hs_edges.EXTRA 补充边。"""
from zh_hs_lib import C, T
from zh_hs_rows import ROWS
from zh_hs_edges import EXTRA

_DIFFS = ("basic", "basic", "standard", "challenge")


def _extra_by_key():
    keys = [r["key"] for r in ROWS]
    index = {k: i for i, k in enumerate(keys)}
    out, seen = {}, set()
    for key, ref, reason in EXTRA:
        if key not in index:
            raise SystemExit("补边的后学 key 不存在：%s" % key)
        if ref[:2] not in ("J:", "P:"):
            if ref not in index or index[ref] >= index[key]:
                raise SystemExit("补边的先修不存在或不在它前面：%s <- %s" % (key, ref))
        if (key, ref) in seen:
            raise SystemExit("补边重复：%s <- %s" % (key, ref))
        if not reason.strip():
            raise SystemExit("补边缺少理由：%s <- %s" % (key, ref))
        seen.add((key, ref))
        out.setdefault(key, []).append((ref, reason))
    return out


_EXTRA = _extra_by_key()

for _r in ROWS:
    _qs = [C(d, q[0], q[1], q[2], q[3]) for d, q in zip(_DIFFS, _r["qs"])]
    _have = {e[0] for e in _r["pre"]}
    _more = [e for e in _EXTRA.get(_r["key"], []) if e[0] not in _have]
    if len(_more) != len(_EXTRA.get(_r["key"], [])):
        raise SystemExit("%s 的补边与课文记录里的先修重复" % _r["key"])
    T(_r["key"], _r["domain"], "conceptual", _r["desc"], _r["mastery"], [_r["std"]], list(_r["pre"]) + _more, _qs)
