# 反馈 C（2026-11-07）

本地阶段 C。基线是 A/B 之后的 `43c1ea089ad3551c8c2afae8ec316f8d95a1e9ad`（`main` 比 `origin/main` 超前这 2 个提交）。开始时工作区只有未跟踪的 `grok-phases/`，本阶段没有读、没有改、没有提交该目录。只读材料在 `/workspace/grok-build-logs/feedback-20261107/` 的 `pr-37`、`pr-38`、`pr-39`、`pr-41` 与 `issue-36`、`issue-29`。这些正文和 diff 都当作待核主张，没有整份套用。没有 push、没有部署、没有 PR、没有 reset/rebase/amend。

本阶段做了 C1，并做了 C2 里能用现有题库断言的题目 ID 模板修正。首页题库异步、诊断页报错链接、教材版本筛选没有改。

## 未改的约束（本阶段前后对过）

| 项 | 结果 |
| --- | --- |
| 带图题目 | `check_figures.py` 打印 443。另一次只读统计：初中物理（年级 7–9）50，高中物理 106，物理合计 156。`data/questions.json` 的 sha256 在测试前后都是 `bf4a7dfb8e28d038a4a9d7b55b921e89d4135bec47d67e2a7653ff33ae4ec3eb` |
| 初中语文知识点 | `cnc_j*` 189。`data/topics.json` 的 sha256 前后都是 `7815211d5ca24f05e9d54d219da31c135b362ef296ba48bcb78f6eb2309f1f1d` |
| 课标 `verbatim: true` | 0（false 629，缺字段 157，条目 786）。`data/cn-curriculum-standards.json` 不在本阶段的 git 改动里 |
| `sw.js` | `VERSION = 'v9'` 未改。sha256 前后都是 `b374a6a7817344a24044868488354c9ff6b5e74839d975df36fc336125fafe35` |
| 初中道法 | 没有新增知识点，也没有改 `scripts/mor_*.py` |
| 七上英语与 9 个待核点 | 没有改英语数据 |

`data/verification_report.json` 的 sha256 前后都是 `ec823bed73beeea9d95f9b892819245e1b6b562d840bff3e01ef2ba3ba29b362`。

## PR 37：采纳，并加宽检查范围

主张：仓库没有 GitHub Actions；`npm test` 是 `echo` 后 `exit 1`。工作流应跑 `validate.py`、只报告的 `STRICT_STANDARDS=1`、`verify_questions.py`，以及不需要浏览器的 Node 测试。

代码核对：开始时确实没有 `.github/workflows/`。`package.json` 的 `test` 确实是占位失败。`tests/` 里已有 `test_engine.js`、`test_blindspots.js`、`test_children.js`、`test_children_browser.js`。`validate.py` 和 `check_figures.py` 不写文件。`verify_questions.py` 默认把报告写到 `data/verification_report.json`，而且报告含 `generated_at`，每次运行都会改这个文件。

采纳：

- 新增 `.github/workflows/ci.yml`。`contents: read`。没有 wrangler、部署或 push。`actions/checkout@v4`、`actions/setup-python@v5`（`3.x`）、`actions/setup-node@v4`（`22`）。
- 强制步骤：`validate.py`、`verify_questions.py`、`check_figures.py`，以及全部非浏览器 Node 测试（含本阶段新增的两个）。
- `STRICT_STANDARDS=1` 的 `validate.py` 使用 `continue-on-error: true`。本地这次它以退出码 1 结束，不是通过。
- `npm test` 是上述强制步骤的并集。原有四个测试文件都还在，没有用某一份 PR 的脚本覆盖掉另一个。`test_children_browser.js` 仍不进入 `npm test` 或 CI，因为它要本机 Chrome。

相对 PR 37 正文，有意不同的地方：

- 答案报告改为 `--report /tmp/cn-math-taxonomy-verification-report.json`。CI 的临时目录和本地都不会改仓库里的 `data/verification_report.json`。PR 里的默认路径在本机跑会留下时间戳 diff。
- 加上 `check_figures.py`。PR 37 没有检查图。
- `tests/test_ci_workflow.js` 也放进工作流。它按目录断言：每个 `tests/test_*.js`（除 `*_browser.js`）都必须同时出现在 CI 和 `npm test` 里，避免以后只改一边。
- 不提交空的 `package-lock.json`。项目没有依赖，`npm test` 也没有生成这个文件。

## PR 39：只采纳模板里的 ID 格式

主张：纠错模板示例是 `q_cnm_221_3` / `q_cnm_xxx_n`，题库实际是 `cnm_221_q3` 这种「知识点 id + `_q` + 题号」。另外要在诊断页参考答案下加「报错」链接，URL 只带题目 ID。

代码核对：`.github/ISSUE_TEMPLATE/question-fix.yml` 确是旧示例。`data/questions.json` 13339 道题的 `id` 全部匹配 `^<topicId>_q<数字>$`，其中 `cnm_221_q3` 和 `cnm_p001_q1` 都在。`diagnose/app.js` 的 `feedbackBlock` 只渲染参考答案和解析，没有报错链接。

采纳：模板的题目 ID 说明和 placeholder 改成真实格式。`tests/test_question_ids.js` 对全部题目做格式断言，并检查模板不再出现 `q_cnm_`，举例的两道题在题库里，题目 ID 栏没有答案或档案字段。

不采纳诊断页链接，留到后续。原因：链接要处理编码、缺 ID 时不渲染、GitHub 未登录时的回退，还要保证 URL 里没有学生答案、解析、会话和孩子档案。这些都还没有在本仓库里用测试跑过。只改模板不会把作答带到 GitHub。

## PR 38：本阶段不改代码

主张：首页不要等 `questions.json` 才渲染；题库失败只让题目计数变成「—」，不要整页失败。

代码核对（当前 `main`，不是 PR 的旧基线）：

- `assets/home.js` 约 220–229 行把 topics、dependencies、questions、standards 放在同一个 `Promise.all` 里。任一 HTTP 失败会走到 `fail()`，年级卡出不来。题目计数只用过滤后的长度。
- 学科在启动时从 `location.search` 读一次（约第 9–10 行）。页面内没有切科。`subjectOfId` 已覆盖 `cne_`、`cnp_`、`cnc_`、`cns_`、`cnd_`、`cnh_`、`cng_`、`cnb_`、`cnk_`，其余当数学。PR 38 的测试夹具只写了数学和英语，直接套上会漏掉后来的学科。
- 诊断 `diagnose/app.js` 的 `loadData`（约 279–297 行）先等图谱文件，再单独取题库；失败或非 2xx 时 `questions = null`，回退到知识点上的 `diagnostic_question`。`init`（约 1713 行）在 `await loadData()` 之后才 `startSession`。首题已经在这个屏障后面，没有重试，失败也不单独提示。
- 图谱 `explore/app.js` 的 `load()` 成功后才 `loadQuestions()`（约 1353 行）。题库失败被吃掉，样题退回文字。没有进行中的请求去重，因为每次打开页面只走一次。
- `sw.js` 对 `.json` 使用 `staleWhileRevalidate`（约 105–124 行）：有缓存就立刻返回旧文件，并在后台更新。页面看不到第二次响应。`VERSION` 已是 `v9`。PR 若按旧基线把版本从 v8 改到 v9，会和现在的 v9 冲突；本阶段也不该为了没改的数据去加版本。

不在本阶段实现。异步拆分有价值，但和首题屏障、失败重试、并发去重、缓存和切科竞态绑在一起。没有这些断言之前改 `home.js`，容易让迟到的题库响应盖住另一学科的计数。

## PR 41、Issue 36、Issue 29：不启用对照，也不改筛选

PR 41 要在图谱详情里展示「其他教材版本（待核）」，并把四份对照放进 `sw.js` 的 `DATA`、把版本改成 v9，还改 `scripts/deploy-cf.sh`。

只读统计，四份正式对照全是 `draft`，示例文件是 `example`：

| 文件 | status | 条目 |
| --- | --- | --- |
| `sujiao_math.json` | draft | 277 |
| `hujiao_math.json` | draft | 160 |
| `yilin_english.json` | draft | 230 |
| `sd54_math.json` | draft | 12 |
| `hujiao_math.example.json` | example | 6 |

`docs/edition-mappings.md` 仍写明前端不读这些文件。图谱年级筛选是 `explore/index.html` 的 `#fGrade`（一至九年级）。孩子档案的教材版本白名单在 `assets/children.js` 的 `TEXTBOOKS`（人教版、北师大版、苏教版、沪教版、外研版、译林版、其他）。`children/index.html` 的 `#book-note` 只说章节按人教版编排，没有区分六三制和五四制。

不采纳 PR 41。draft 不能当成已核位置显示。待核提示也不能说成筛选已经按版本工作。PR 基于旧的 v8 去改 `sw.js`，现在已经是 v9，不能套用。部署脚本本阶段不动。

Issue 36 要求档案增加青岛版、鲁教版、鲁科版（五四制），并增加学制字段。Issue 29 要求鲁教版；评论里有人说自己做了青岛版 App，另一人说不是青岛的用不了。这些评论没有在本仓库核对教材。不把出版社名称加进白名单：加了名字、年级仍按人教六三制，档案卡会更像已经支持。

不扩初中道法，不做学制迁移。

### 后续可执行的版本方案（本阶段不实施）

1. 提示只改文案，不改选项值，也不要写「已支持五四制筛选」。`#book-note`、`#fGrade` 旁、诊断开始页 `renderStart` 里「按册、章浏览」那句，各加一句：年级和册次按人教版六三制；五四制小学五年、初中从六年级起，不能按这里的年级对照，请按知识点查。用 Node 读这三个字符串做断言。改完在浏览器里看档案页、图谱页、诊断开始页。不改 `sw.js`，因此不加缓存版本。
2. 仍不把 `data/mappings/*.json` 读进页面，直到某份文件的 `status` 成为 `reviewed`。UI 只消费 `reviewed`。没有 reviewed 条目时，版本筛选控件不出现。缺映射时仍显示人教版年级，并写「该版本映射尚未补齐」（`docs/edition-mappings.md` 已有这句约定）。
3. 档案以后再加可选字段 `schoolSystem`：`63` 或 `54`，与 `textbook` 分开。旧备份没有这个字段时 `clean()` 必须仍能读。不要用一个下拉框同时表示学制、出版社和版次。
4. 对照条目在 `reviewed` 时才要求 `schoolSystem` 和版次年。`draft` 可以继续缺这两项。`validate.py` 按 status 分支。一次 PR 只核一册，不改 `topics.json` 的 `grade`。
5. 出版社、版次年、册次对照是数据，不是代码开关。Issue 29/36 里的青岛版、鲁教版、鲁科版，要有可引用的目录来源写进该文件的 `source` 之后才能进白名单。

## 测试命令和实际结果

本地环境：Node `v24.22.1`，Python `3.13.5`。工作流文件里写的是 Node 22 和 Python `3.x`。本机没有执行 `actions/setup-node` 或 `actions/setup-python`，也没有触发 GitHub Actions。不能把下面的通过说成 GitHub CI 已绿。

2026-11-07T15:03:41+08:00 至 15:04:01+08:00，在仓库根目录：

```text
npm test
```

退出码 0。摘要：

| 步骤 | 结果 |
| --- | --- |
| `node tests/test_ci_workflow.js` | 17 passed |
| `node tests/test_engine.js` | 107 passed, 0 failed |
| `node tests/test_blindspots.js` | 8 passed |
| `node tests/test_children.js` | 38 passed, 0 failed |
| `node tests/test_question_ids.js` | 4 passed |
| `python3 scripts/validate.py` | `VALIDATION PASSED`。正式知识点 standards 为空 2 个：`cnm_130`、`cnm_192`（非严格模式下是 WARNING） |
| `python3 scripts/check_figures.py` | `图示检查通过：443 道题带图` |
| `python3 scripts/verify_questions.py --report /tmp/cn-math-taxonomy-verification-report.json` | 题目 13339；numeric+choice 13310；auto_verified 12772；mismatch 0；unverifiable 567（choice 499，numeric 39，self 6，short 23）；format_errors 0；`VERIFICATION PASSED` |

Node 把 `NO_COLOR` 被 `FORCE_COLOR` 盖住的提示打到 stderr。测试本身没有失败。

严格模式单独跑，不在 `npm test` 里，因为它现在就应该失败：

```text
STRICT_STANDARDS=1 python3 scripts/validate.py
```

退出码 1。唯一错误：`STRICT_STANDARDS=1：2 个正式知识点的 standards 为空`（仍是 `cnm_130`、`cnm_192`）。工作流里这一步是 `continue-on-error`。这不是本阶段要填的课标空项，也没有把 `verbatim` 改成 true。

幂等：同一命令再写 `/tmp/c1-verify-2.json`，退出码 0。两份报告去掉 `generated_at` 后相等。范围只是题库答案核验的报告，没有重跑构建脚本，没有改 `data/`、`sw.js`。

没有跑 `node tests/test_children_browser.js`（要本机 Chrome）。没有打开网页点诊断或图谱。

## 后续步骤（给续跑 C2 的人）

不要套用 PR 38/39/41 的 diff。当前首页、诊断和 `sw.js` 都已经比那些 PR 的基线新。

1. 诊断首题屏障保持住：`init` 必须继续 `await loadData()` 之后才出题。题库失败时的 `questions = null` 回退可以保留，但要有测试证明失败不会抛到整页「数据加载失败」，并且不会把学生答案写进任何请求。若要加重试，最多 2 次、同一 URL、进行中的 Promise 只留一个。测试用假 `fetch`：第一次失败、第二次成功；两个调用者共享同一次请求。
2. 首页拆题库时，先写 `tests/test_home.js`，用 `vm` 和可控的 `fetch`，覆盖现在的全部科目前缀，而不是只覆盖数学和英语。断言：topics/dependencies/standards 到达后年级卡和知识点计数已出现，`n-questions` 为「…」；题库 404、网络拒绝、非数组时计数为「—」且 `#load-error` 仍隐藏；topics 无效时仍走 `fail()`，并且不再请求 `questions.json`。学科只在启动时读一次。不要在同一次改动里加页内切科。
3. 若以后页内切科或重试会重叠，加代数：晚到的数学响应不能写英语计数。测试先发数学、再切英语、最后让数学的 Promise 成功。
4. 缓存：`.json` 仍是 stale-while-revalidate。页面只消费第一次响应，所以刚更新的题库要等下一次访问才出现。不要为这个现象改 `VERSION`，除非 `SHELL` 或 `DATA` 变了。不要把 `data/mappings/` 加进 `DATA`。
5. 诊断报错链接再做时：只在 `feedbackBlock` 里、答案已经显示之后出现。查询参数只有 `template`、`title`、`question_id`，值用 `encodeURIComponent`。`question_id` 只放 `q.id`。没有 id 就不渲染链接。`target="_blank"`，`rel="noopener noreferrer"`，带已有的 `no-print`。不要预填问题描述、建议修正、参考答案、学生答案、孩子昵称或会话。测试要断言一条含 `&`、`#` 和空格的 id 能原样解码回来，并且 href 里没有这些答案字段。本机若没有浏览器，要在记录里写明链接点击没有人工点过。
6. 新的 Node 测试文件放进 `npm test` 和 `ci.yml`。`tests/test_ci_workflow.js` 会在漏掉时失败。不要用 `git add .`。不要提交 `grok-phases/`。
