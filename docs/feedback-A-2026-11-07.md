# 反馈 A：Issue 34 / PR 40（2026-11-07）

基线 `bf44fd9`。只读抓取证据在 `/workspace/grok-build-logs/feedback-20261107/`（`issue34-raw.json`、`issue34-comments.json`、`pr40-raw.json`、`pr40.diff`、`pr40-files.json`、`pr40-commits.json`、评论/reviews 空数组、`repro-summary.json`、`postfix-hist7a.json`）。`gh *comment*` 被本机策略拦截，改用 GitHub REST 只读 GET。未 clone、未 push、未部署。

## 两边主张（待核，已独立复现）

- **Issue 34**（DoviCapet）：「历史题答 3 题就结束了，没有到 40 题的量」。
- **仓库主评论**（xiaoyang111222，2026-11-04）：认为是自适应预期——每点 4 题、默认连续 3 题才掌握，整科不会出满 40。
- **PR 40**（TheGeekyM）：筛查沿全部先修推断掌握；历史七上几乎全是 soft，末点答对就把整册标掌握。主张筛查只沿 **hard** 传播；target 不变；不做「填满 40 题」。

## 固定序列（历史 / 七年级上册 / 筛查）

引擎：`gradeTargets(G, '七上', 'history')`，`mode: 'screen'`，`confirm: 3`，`limit: 40`，`seed: 'repro'`。册内 21 点。先修：hard 4、soft 18、孤立 1（`cnh_j001`）。栈从拓扑最末点 `cnh_j021`（第 4 单元「从考古发现看中华文明的起源与形成」）问起。每点题库 4 题，`needConfirm=3`。

四条 hard 边（方向 A←B 表示学 A 需要 B）：

| 边 | 理由（数据原文） |
| --- | --- |
| `cnh_j009`←`cnh_j006` | 秦统一建立在战国变法图强上 |
| `cnh_j011`←`cnh_j010` | 西汉建立承接秦末起义 |
| `cnh_j012`←`cnh_j011` | 汉武帝巩固大一统建立在文景之治上 |
| `cnh_j014`←`cnh_j012` | 丝绸之路以通西域、巩固统一为前提 |

`cnh_j021` 只有 soft 先修 `cnh_j020`。末点掌握沿 **全部边** 可到全部 21 点；沿 **hard** 只能到它自己。

## 逐步表：基线 vs 修复后（全对）

### 基线 `bf44fd9`（修复前）

| 步 | 已答 | 点 | 结果 | 判定 | 新推断掌握 | 未知剩余 | 下一候选 |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | 1 | `cnh_j021` | correct | pending | 0 | 21 | `cnh_j021` |
| 2 | 2 | `cnh_j021` | correct | pending | 0 | 21 | `cnh_j021` |
| 3 | 3 | `cnh_j021` | correct | mastered/direct | 20（`cnh_j001`–`cnh_j020`） | 0 | null |

停止原因：`no_unknown_in_scope`（不是题量上限）。`limitReached=false`，`asked=3`，`unique=1`，`mastered=21`，`untested=0`。这是 **soft 推断过度**，不是合理自适应结束：第 4 单元活动课 3 题全对，不能证明第 1 单元「远古时期的人类活动」。

主评论把 3 题当成「单点确认题数」，与用户「到 40 题」的筛查预期不符。单点 target 对 `cnh_j021` 全对同样 3 题结束（文档原规则，本次不改）。

### 修复后（筛查只沿 hard 推断）

| 步 | 已答 | 点 | 结果 | 判定 | 新推断掌握 | 未知剩余 | 下一候选 |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| 1–2 | 1–2 | `cnh_j021` | correct | pending | 0 | 21 | `cnh_j021` |
| 3 | 3 | `cnh_j021` | correct | mastered/direct | **0** | 20 | `cnh_j020` |
| 4–6 | 4–6 | `cnh_j020` | correct×3 | mastered/direct | 0 | 19 | `cnh_j019` |
| … | … | 沿栈 `j019`…`j015` 各 3 题 | correct | 直接掌握 | 0 | … | … |
| 24 | 24 | `cnh_j014` 第 3 题 | correct | mastered/direct | `cnh_j012`,`cnh_j011`,`cnh_j010`（hard 链） | 跳过这 3 点 | `cnh_j013` |
| … | … | `cnh_j009` 第 3 题 | correct | mastered/direct | `cnh_j006` | 跳过 j006 | `cnh_j008` |
| 40 | 40 | `cnh_j004` 第 1 题 | correct | pending | 0 | 4 | 上限停止 |

停止原因：`limit`（40）。`unique=14`，`mastered=17`（13 直接满额 + 4 条 hard 推断），`untested=4`（`cnh_j004` 未满额 + 未问到的 `cnh_j001`–`cnh_j003`）。推断点均可从某个直接掌握点沿 hard 到达。`cnh_j021` 掌握后 `cnh_j001` 仍为 unknown。

直接问到的 14 点：`cnh_j021`–`cnh_j013`、`cnh_j009`、`cnh_j008`、`cnh_j007`、`cnh_j005`、`cnh_j004`。

## 其他对照（同一引擎、固定 seed）

| 序列 | 基线 asked / unique / mastered / untested / 停止 | 硬传播候选（修复） |
| --- | --- | --- |
| 历史七上 全对 confirm=3 limit=40 | 3 / 1 / 21 / 0 / 范围清空 | 40 / 14 / 17 / 4 / 上限 |
| 历史七上 全对 confirm=1 | 1 / 1 / 21 / 0 / 范围清空 | confirm=1 limit=1000：17 / 17 / 21 / 0 / 问完 |
| 历史七上 首题错再对 | 40 / 20 / 0 / 1 / 上限（不稳，不推断） | 同左（此序列不触发掌握推断） |
| 历史七上 全错 | 40 / 20 / 0 / 1 / 上限 | 同左 |
| 历史七上 混合（仅 `cnh_j020` 错） | 基线 3 题已把 j020 推断掉，问不到 | 继续出题；j021 掌握不覆盖 j020；推断仍只走 hard |
| 语文七上 全对 confirm=3 | 3 / 1 / 29 / 0 / 范围清空（册内 hard=0） | 40 / 14 / 13 / 16 / 上限 |
| 英语七上 全对 confirm=3 | 21 / 7 / 62 / 0 | 未作为本阶段必改数据；同类 soft 链 |
| 数学七上 全对 confirm=3 | 40 / 14 / 59 / 2 / 上限 | 40 / 14 / 55 / 6 / 上限 |
| 物理八上 全对 confirm=3 | 27 / 9 / 28 / 0 / 问完 | 33 / 11 / 28 / 0 / 问完（hard 与全边闭包接近） |

合理自适应结束：数学/物理上，hard 先修成立时答对末端可跳过真门槛。soft 时间线（史前→夏商→秦汉→魏晋）不能当掌握证明。hard 本身仍是 AI 标注、未教师审核，只保证「不沿 soft 跳册」，不保证推断点真会。

跨册：筛查七上答案 id 均在七上；不问卷内以外。target 模式对 `cnh_j021` 仍 3 题推断全部祖先（文档原规则）。

## 修复

`diagnose/engine.js`：新增 `hardAncestorSet`（独立 `_hardAnc` / `_hardVisiting` 缓存，环检测与 `ancestorSet` 相同）。`applyAnswer` 在连续答对满额时：`s.mode === 'screen'` 用 hard 祖先，否则仍用全部祖先。不改选题、回溯、题量上限、target、数据。未做「填满 40 题」：全对历史现在碰到上限并留下未测，这是诚实结果，不是失败。

## 测试（均实际执行）

| 命令 | 结果 |
| --- | --- |
| `python3 scripts/validate.py` | VALIDATION PASSED。3297 点；语文 `cnc_j` 189；题库 13335 |
| `python3 scripts/check_figures.py` | 通过。443 题带图；初中物理带图 **50** |
| `node tests/test_engine.js` | **107 passed, 0 failed**（原 96 + 本阶段 11） |
| `node tests/test_children.js` | 38 passed, 0 failed |
| `node tests/test_blindspots.js` | 8 passed |

新回归（不能只靠题数变多）：手造 soft-only、hard-soft 混合、多跳 soft 切断 hard 链、推断不覆盖直接判定、target 仍全祖先、历史七上全对 confirm=3 不是 3 题整册掌握且 `cnh_j001` 不被末点推断、首题错→不稳、混合 `cnh_j020` 错、跨册过滤、confirm=1 真实数据推断点均可沿 hard 到达。

未跑：整库生成脚本。未改 `data/*`、`sw.js`（仍 v9）、课标 `verbatim true=0`、七上英语、道法。

## 与 PR 40 异同

**同：** 根因判断一致（筛查 `ancestorSet` 沿 soft 过度推断）；最小修复同为筛查改走 `hardAncestorSet`；target 不变；不做填满上限。

**异：**

- 未 cherry-pick。PR 底提交 `cf73951`，当前基线 `bf44fd9`（含七上英语、课标核对、初中语文等），直接合会脏。
- 未改 `package.json` / 未新增 `package-lock.json`。
- CHANGELOG 写在 2026-11-07，插在现行「七上英语目录」之前；PR 写 2026-11-06 且插在当时的「新增初中语文」前。
- 测试：PR 以 confirm=1 且 `direct.length > 3` 为主；本阶段用 confirm=3 复现用户 3 题路径，并断言推断集合 ⊆ hard 闭包、末点掌握后远古点仍 unknown。
- README 措辞独立改写，未复制 PR 全文。

## 限制

- 用户未给出具体年级/册/种子；按筛查默认（历史七上、confirm=3、limit=40）复现，与「3 题 / 40 题」字面相符。若用户走的是单点诊断，3 题结束仍是文档行为。
- 默认 40 题仍可能留未测；全对历史七上修后 4 个未测。这是上限，不是新的提前结束。
- 英语七上、语文七上有同类 soft 链，修筛查规则后一并改变；未改边数据。
- hard 边未教师审核；「只沿 hard」是数据已有的强度语义，不是掌握的证明。
