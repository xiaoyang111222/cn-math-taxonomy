# 反馈兼容：cnc_p124_q3/q4 同 ID 题干改写（2026-11-07）

本地阶段。基线是 A/B/C1 的 `283a7a1`（相对 `origin/main` 超前 3）。没有 push、没有部署。未读未提交 `grok-phases/`。

## 发现

B 提交 `43c1ea0` 把知识点拆成：

- `cnc_p124`：语气（口语交际）
- `cnc_p494`：日积月累《赋得古原草送别》

但 **`cnc_p124_q3` / `cnc_p124_q4` 仍用原题号**，题干从古诗改成语气。核对存储后：

| 路径 | 存什么 | 有无题干/归属快照 |
| --- | --- | --- |
| 诊断 session（localStorage） | `answers[].id` + `qid` + `result`（及可选 `text`） | **无** prompt；恢复时用现行题库按 qid 取题干 |
| 孩子档案记录 | 知识点级 weak/shaky/mastered | **无**逐题快照 |
| 盲区账本 | 知识点级 status + wrongs | **无**题干 |
| 备份 JSON | 上述记录原样 | 同上 |

因此旧浏览器里「答对/答错了古诗 q3/q4」会在恢复或盲区合并时，被当成「答了现在的语气题」。也不能把整份旧 `cnc_p124` 结论迁到 `cnc_p494`：旧记录里可能混有仍有效的 q1/q2 语气作答。

## 修复（最小保守排除）

新增 `assets/stem-compat.js`（`window.StemCompat` / `require`）：

- 仅处理这一对 retired id：`cnc_p124_q3`、`cnc_p124_q4`。
- 作答带现行语气 `prompt` 快照才算新题；无快照或仍是旧诗句 → 排除，标需重测。
- 孩子记录 / 盲区：无 `stemRev = tone-2026-11-07` 的 `cnc_p124` 从掌握/薄弱/不稳视图拿掉，标 `retest`；**不改存储原文**，备份仍可还原旧字节。
- 诊断：恢复会话时过滤；结果页提示「有旧作答未计入」；导出里排除项单独列出，不显示成现行语气题干。
- 引擎 `replay`/`applyAnswer` 支持按 `qid` pin，避免过滤后错位套题。

页面在 `children.js` / `blindspots.js` / `diagnose/app.js` 之前加载该脚本。`sw.js` **v9→v10**，SHELL 加入 `assets/stem-compat.js`。首页盲区标签对 `retest` 显示「需重测」。

**明确不声称：** 全量历史题干兼容；其他同 ID 改写；把旧混合结果改记到 `cnc_p494`。

## 测试（本机实测）

```text
node tests/test_stem_compat.js
```

5 passed：夹具↔RETIRED/CURRENT；git 原文一致；旧 session 排除后不成掌握；孩子记录视图需重测且备份原字节；盲区旧弱项/旧错题不计入语气，新 stamped 可信。

一并跑过原有 `test_engine.js`（107）、`test_children.js`（38）、`test_blindspots.js`（8）。完整 `npm test` 见提交说明。
