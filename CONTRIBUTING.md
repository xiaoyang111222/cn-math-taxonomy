# 贡献指南 / Contributing

**English summary**

- This repo publishes Chinese K-12 knowledge-graph data (topics, prerequisite edges, question bank, curriculum-standard and textbook-edition mappings) and the scripts behind it. Corrections and source checks are welcome; site and diagnostic-tool code lives in a private repo and is not accepted here.
- Before a PR, run `npm test` (python3 and node only, no `npm install`); success ends with `VERIFICATION PASSED`, WARNING lines do not block.
- If you edit `data/questions.json`, also run `python3 scripts/split_questions.py` and commit the changes under `data/questions/`.
- Cite a primary source (with date) for catalog, mapping and standards changes; mark anything unverified as pending; disclose AI assistance and how you checked it.
- Contributions are licensed under CC BY-NC 4.0, and you agree the maintainer may include them in commercial licenses (section 8). Commercial licensing: 499749204@qq.com.
- Single maintainer, review is best-effort with no response-time guarantee.

本仓库只有一位维护者，审核是尽力而为。下面的约定是为了让你的修改容易被核对、容易被合并。

## 1. 先看这里：去哪提

| 你想做的事 | 去哪 |
| --- | --- |
| 某道题的题干、答案、选项、难度有误 | [题目纠错](https://github.com/xiaoyang111222/cn-math-taxonomy/issues/new/choose) 模板（带题目 ID，如 `cnm_221_q3`） |
| 改进想法，或先修边/映射/课标的核对建议（改动较大，想先商量） | 「功能建议」模板，模块选对应的数据方向 |
| 数据怎么用、字段什么意思、想交流 | [Discussions](https://github.com/xiaoyang111222/cn-math-taxonomy/discussions) |
| 商业使用授权 | X 私信 [@hassanyehiaa](https://x.com/hassanyehiaa) 或邮箱 499749204@qq.com；Issue 里可以说明用途，报价与合同细节请走私信或邮件 |
| 直接改数据或文档 | 提 PR，规则见第 4、5 节 |

- 小改动（订正一两道题、补一条来源、改一条先修边）直接提 PR 即可。
- 大改动（多道题、一册以上、整个学科的映射）请先开 Issue 说一声，免得白做。

## 2. 欢迎的贡献

- **题目纠错与补 `verify`**
  - 改错题干、答案、选项、解析。
  - `verify_questions.py` 目前报告 528 道题无法自动核验（选择题 499、短答 23、开放题 6）。选项是数或可计算式子的，可以补 `verify` 表达式。
  - 选项是纯文字的选择题没法用表达式验算，不必在这类题上花力气。
- **先修边的增删**：补漏边、删多余边，或把 hard/soft 判断改对。
- **教材版本映射核对**：`data/mappings/` 下的条目对照教材目录页核一遍，格式见 [docs/edition-mappings.md](docs/edition-mappings.md)。
- **课标条目核对**
  - `data/cn-curriculum-standards.json` 里 `verbatim: false`、`page_or_ref` 写「待核」的条目，对照课标原文核对。
  - 以及 `standards` 为空的知识点（`validate.py` 会打印 WARNING，目前有 `cnm_130`、`cnm_192`）。
- **题目重写**：可以，但有条件。
  - 一次只动一个学科的一册；
  - PR 里写明改写依据（哪里不好、改成什么、为什么）；
  - 数值类题附验算或 `verify`。

## 3. 几条必知约定

字段细节不在这里重复，以 `scripts/validate.py` 的报错为准。必须知道的是：

- **ID 不改名。** 知识点 id 一旦发布就稳定（`cnm_221`、`cnm_p001` 等）；确需合并或改名，在 `data/id-aliases.json` 里留别名。
- **题目 ID 是 `<知识点 id>_q<N>`**，如 `cnm_221_q3`。
- **先修边方向**：`{"topicId": "A", "prerequisiteId": "B"}` 表示 A 依赖 B。
  - 只保留直接先修；
  - 不允许跨学科边（`validate.py` 会拒绝），物理用到的数学写在 `mathLinks`。
- **`data/questions.json` 是题库源数据**，网站读的是由它生成的 `data/questions/<学科>.json`（见第 4 节）。

字段说明在这几处，不要在别处另写一份：

- README「仓库结构」下的「topics.json 字段」「dependencies.json 字段」；
- 题库字段：[docs/questions.md](docs/questions.md)「格式」；
- 版本映射：[docs/edition-mappings.md](docs/edition-mappings.md)（运行时以 [docs/hujiao-mapping-plan.md](docs/hujiao-mapping-plan.md) 为准）；
- 课标映射：[docs/standards-mapping.md](docs/standards-mapping.md)。

## 4. 提 PR 前

基本流程：

1. Fork 本仓库，从 `main` 拉一个分支；
2. 只改你要改的数据或文档（改题库时留意下面的 `split_questions.py`）；
3. 跑下面的 `npm test`，通过后提交；
4. 提 PR，按模板写清改了什么、依据是什么。

环境：python3 和 node（CI 用 Node 22）。没有 npm 依赖，**不需要 `npm install`**。

```bash
npm test
```

- 这一条已经包含 `scripts/validate.py`、图示检查和题目答案核验，不用再单独跑它们。
- 成功的标志是**最后一行**为 `VERIFICATION PASSED`。
- 过程中打印的 `WARNING`（例如个别知识点的 `standards` 为空）不阻塞，只看最后一行和退出码。
- `npm test` 不会改动工作树。

另外两条容易漏：

- **改了 `data/questions.json` 的，必须再跑**

  ```bash
  python3 scripts/split_questions.py
  ```

  并把 `data/questions/` 的变化一起提交；`--check` 可以只核对不写。目前 CI 和 `npm test` 都不检查两边是否一致，漏了就会出现「CI 绿，但网站读到的还是旧题」。
- **不要单独运行** `python3 scripts/verify_questions.py` 而不带 `--report`：它会改写已被 git 跟踪的 `data/verification_report.json`，让你的 PR 带上无关改动。需要看报告请用 `npm test`，或加 `--report /tmp/xxx.json`。

提交前 `git status` 看一眼，确认只有你想改的文件。

## 5. PR 规矩

**一个 PR 只做一件事。**

- 一个 PR 超过约 50 道题或涉及一册以上，请先开 Issue 商量。
- PR 描述里写明学科、册次、涉及的知识点或题目 ID。

PR 描述示例（改题）：

```text
（示例）某学科某册，cnm_221_q3：答案应为 12 而非 21。
推导：36 ÷ 3 = 12，已补 verify，已跑 split_questions.py。npm test 通过。
```

**依据分三档，按你改的内容给：**

1. **题干、答案、选项、解析有误**：给出推导，或可复算的 `verify` 表达式即可，不要求课标页码。
2. **教材目录、版本映射、课标条目**：给一手来源加**查证日期**。
   - 一手来源：出版社或国家中小学智慧教育平台的目录页、课标 PDF 的页码。
   - 不要凭记忆填，不要整页复制教材或课标原文。
   - 「来源怎么记」可参考 `docs/` 里各学科的 `*-catalog-*.md`、`*-official-reader-*.md`、`standards-verify-*.md`。
3. **先修边**：一句中文理由，并说明是 hard 还是 soft。
   - hard：不会 B 基本无法学 A；
   - soft：会 B 对学 A 明显有帮助，但不是硬门槛（详见 README「dependencies.json 字段」）。

**查不到就标待核，不要自创标记。** 仓库现有的待核标记是：

- 映射文件：`status: draft`，并在 `note` 里写 `provisional：…待复核`；
- 知识点目录：`catalog_status`；
- 课标条目：`verbatim: false`，`page_or_ref` 写「待核」；
- 题目答案存疑：在 PR 里说明，不要悄悄改成你认为对的。

**AI 辅助要声明。**

- 本仓库的题目本来就由 AI 生成，所以不禁止 AI 辅助；
- 但**不收未经逐条核对的批量数据**；
- 用了 AI 来起草、改写或批量处理的，请在 PR 里写明，并说明你怎么核对的（逐题手算 / 写了验算脚本 / 对照了某页教材）。

**源数据与生成脚本。**

- 部分学科的题目或知识点由 `scripts/*_build.py` 和 `data/_qbatches/` 下的批次文件生成，只改 json 会在下次重建时被覆盖。
- 你改的学科如果有生成脚本或批次文件，请在 PR 里说明，维护者合并时负责回写。

**CHANGELOG 由维护者记**，请不要改 `CHANGELOG.md`：多个 PR 同改文件顶部必然冲突，而且它只记数据变更。

## 6. 不收什么

- **网站和诊断工具的代码**：站点源码在私有仓维护，本仓不收这类 PR。站点功能建议可以提，由维护者转到私有仓，不保证响应。
- **授权询价**：请发邮件或 X 私信；Issue 和 PR 里的报价、合同类讨论不处理。
- **未经逐条核对的批量数据**：包括大批量机器生成、批量抓取的内容（见第 5 节）。
- **整页复制的教材、课标、第三方题库原文**：只收转述、目录信息和你自己出的题，并注明来源。

关于脚本：

- `scripts/` 下的构建脚本按现状提供，不保证在其他环境能复现，也不提供使用支持；
- 数据格式方面的问题（字段含义、怎么引用数据）照常回答，请到 Discussions 提问。

## 7. 审核与合并

- CI（与 `npm test` 相同的步骤）必须是绿的。
- 首次贡献者的工作流需要维护者在 GitHub 上手动批准后才会运行，请耐心等待。
- 维护者会对数据改动做抽查复核，可能追问来源或要求补依据。
- 这是单人维护的项目，审核尽力而为，不保证响应时间。
- 合并后维护者视情况在 `CHANGELOG.md` 记录；纯文档、CI 类改动不记。

## 8. 授权

提交贡献（包括 PR、Issue 中给出的修改文本），即表示你同意：

1. 你的贡献按本仓库的许可证 **CC BY-NC 4.0** 授权；
2. 你同意维护者将你的贡献纳入本项目的商业授权范围，即维护者可以在单独的商业授权中，连同你的贡献一起向第三方授权本项目数据。

你同时保证贡献内容是你自己写的，或其来源允许这样使用。不同意第 2 条的，请在 PR 中明说，相应内容将不被合并。
