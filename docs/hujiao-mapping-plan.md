# 沪教版映射层结构方案

对应 GitHub Issue #11。本文只定小学数学这一期的映射层怎么接进现有站点。知识点本体、先修边、题库继续共用；版本只改变年级册次归属、章节顺序和诊断的筛选范围。

已定、实施时保持不变的决定：

- 映射写在独立文件 `data/mappings/hujiao-math.json`。`data/topics.json` 不改。
- 三期：一期小学数学，并把档案、诊断、无映射提示整条链路跑通；二期初中数学（五四制册次重排）；三期物理与英语。
- 没有映射条目的知识点按「该版本暂未覆盖」呈现。册次位置留空，目录里不出现人教版的 `chapter`。

仓库里已有一份旧的贡献约定（`docs/edition-mappings.md`）和若干下划线文件名的对照表。那套约定是「审核后合并进 topic 的 `mappings` 字段」。本方案的运行时不走那条路。两套文件在一期并存，页面只读新文件。Issue #11 的正文本次没有从 GitHub 拉到（本机没有 `gh`），下文以本任务列出的决定为准。

撰写时读到的规模：`data/topics.json` 共 4221 条。其中小学数学正式点（id 以 `cnm_p` 开头、`external` 为 false）284 条，一至六年级分别是 48、44、51、41、52、48。

---

## 1. 现状盘点

### 1.1 `data/topics.json`

顶层是数组，一条知识点一个对象。数学点没有单独的 `subject` 字段时，诊断用 id 前缀判定（见 1.2 `subjectOf`）。抽到的两条：

| id | grade | semester | chapter |
|---|---|---|---|
| `cnm_p001` | `1` | `"上"` | `一年级上册 第1单元 5以内数的认识和加、减法` |
| `cnm_001` | `7` | `"上"` | `七上 第一章 有理数 1.1` |

和册次相关的字段：

- `grade`：整数。小学 1–6，初中 7–9，高中数学 10–14（10、11 为必修两册，12–14 为选择性必修三册，不是高三、高四）。全库 4221 条的 `grade` 都是整数。
- `semester`：字符串 `"上"` / `"下"` / `"全"`。全库计数为上 2922、下 1259、全 40。没有名为 `term` 的字段。小学数学 284 条只有 `"上"` 和 `"下"`。
- `chapter`：人教版归属，一条字符串，诊断按它拆册次。小学数学两种写法都有：
  - 单元：`X年级Y册 第N单元 单元名`，255 条。例如 `一年级上册 第1单元 5以内数的认识和加、减法`。
  - 综合与实践：`X年级Y册 综合与实践 活动名`，29 条。例如 `一年级上册 综合与实践 数学游戏`。
- 初中数学写成 `七上 第一章 有理数 1.1` 这种带小节号的短册名，和小学的「一年级上册」不是同一套格式。
- 正式点的必填字段由 `scripts/validate.py` 的 `CORE_FIELDS` 规定：`id`、`name`、`domain`、`grade`、`semester`、`chapter`、`type`、`description`、`mastery_criteria`、`diagnostic_question`、`external`。
- 可选字段 `mappings` 在 `validate.py` 的 `check_mappings` 里有校验，但当前 4221 条里没有任何一条带这个字段。

`grade` / `semester` 与 `chapter` 开头的册次在现有数据里是对齐的。整年级诊断看的是 `chapter` 拆出来的册（`gradeTargets`），学期进度过滤看的是 `grade` + `semester`（`filterByProgress`）。映射层要同时投影这两处，只改其中一处会筛错。

### 1.2 `diagnose/engine.js`：`parseChapter` 与学期过滤

文件头说明引擎是纯函数。浏览器里是 `window.DiagEngine`，Node 里 `require('../diagnose/engine.js')`。`buildGraph(topics, deps, questions)` 把 topic 对象原样放进 `graph.byId`，不复制、不改写 `grade` / `semester` / `chapter`。

`parseChapter(chapter)`（约第 562 行）按字符串拆册次，返回 `{volume, chapterNo, chapterName, section}`。和一期有关的分支：

- 小学与部分初中长册名：`/^([一二三四五六七八九])年级([上下全])册 (第\d+单元|预备单元\d) (.+)$/`。命中时 `volume` 为「一上」这种两字，`chapterNo` 为「第N单元」或「预备单元N」。
- 综合与实践：`/^([一二三四五六九])年级([上下])册 (综合与实践) (.+)$/`。八年级没有走这条（字符类里没有「八」）。
- 对不上时落到后面的 `^(\S+) (第\S+章) ...`，初中数学「七上 第一章 有理数 1.1」走这里。
- 再对不上则 `volume` 为空，整段原文放进 `chapterName`。

「预备单元」是人教版英语七年级 Starter 的章号（如 `七年级上册 预备单元1 Hello!`），不是上海预备年级。映射层不要复用这个词来表示五四制六年级。

`gradeTargets(graph, scope, subject)`（约第 649 行）把「三年级」「三上」「七上」等收成 volume 列表，再用 `parseChapter(t.chapter).volume` 过滤。`external === true` 的点排除。id 顺序与 `topics` 数组一致。它不读 `topic.grade`。

`filterByProgress(graph, ids, progress, curGrade)`（约第 732 行）：

- `progress` 不是 `'上'` 时原样返回，`deferred` 为空。
- `progress === '上'` 时，`semester === '下'` 且 `grade` 等于 `curGrade`（`curGrade == null` 时所有下册）放进 `deferred`，其余保留。
- `semester === '全'` 的点保留。
- 注释写明：只过滤被测目标池；沿先修边回溯不经过这里。

`gradeRank` 用 `grade * 2 + (semester === '下' ? 1 : 0)` 给学习路径排序。`chapterSummary` 再用 `parseChapter(t.chapter)` 按章汇总。

进度的另外两个函数：`defaultProgress(date)` 按月份给 `'上'` / `'下'` / `'全'`；`termKey(date)` 返回「学年起始年-进度」，例如九月是 `2026-上`。这是「这学期学到哪」，和映射文件里的 `term` 不是同一个字段。

诊断页 `diagnose/app.js` 的用法：

- `loadData` 请求 `../data/topics.json`、`dependencies.json`、`cn-curriculum-standards.json`、`id-aliases.json`，再请求 `../data/questions/<学科>.json`。不请求 `data/mappings/`。
- `buildTree` 对每个非 external 点调用 `E.parseChapter(t.chapter)`，按 `volume` 再按章挂树。
- 册次顺序写死在 `VOLUMES`（第 21 行起）：一上到六下、七上到九下、九全，然后是高中各册。`fillList` 里 `volumeStage`：volume 首字为一至六则算小学 `'p'`。
- `gradeCard` 用 `E.gradeTargets` 得到整年级 id，再 `E.filterByProgress(..., prog.v, gradeNumOf(gradeSel))`。整章按钮用 `childGradeNum()` 当 `curGrade`（当前孩子档案年级，没有孩子则为 null）。
- 单点「选为目标」和 URL `target=` 不经过 `filterByProgress`（`app.js` 约第 261–263 行的注释）。
- `getProgress`：有当前孩子就读 `child.progress`，否则读本机 `cnmDiagnose.settings.v2` 里的 `progress`。结构是 `{v, term}`，`term` 要等于当天的 `termKey` 才算手动选择。
- 孩子档案在诊断页只用于当前孩子、保存记录和学习进度。`textbook` 字段没有被读取。

先修回溯在 `createSession` / `nextQuestion`：答错且确认题也错时沿 `graph.prereqs` 往前走。边来自 `data/dependencies.json`，与 `chapter` 无关。

### 1.3 孩子档案

存储在 `assets/children.js`。

- 键：`localStorage['cnmChildren.v1']`，形状 `{v: 1, current, children: [...]}`。
- 每个孩子：`{id, name, grade, textbook, createdAt}`，编辑或改进度时另有 `updatedAt`。进度是可选的 `progress: {v, term}`。
- `grade` 白名单 `GRADES`：一年级到九年级、高一、高二、高三。没有「预备年级」，也没有学制字段。
- `textbook` 白名单 `TEXTBOOKS`：人教版、北师大版、苏教版、沪教版、外研版、译林版、其他。缺省和非法值都落成人教版（`clean`）。
- 全孩子一份 `textbook`，不按学科。
- 校验在 `checkArchive`：年级、教材必须命中白名单。对象上多出来的字段目前不会被拒绝。`exportBackup` 导出的是 localStorage 原文，格式名 `cn-math-taxonomy.children`，`version: 1`。
- 档案页 `children/page.js` 用这两个白名单填 `#f-grade`、`#f-book`。`children/index.html` 的 `#book-note` 写明：当前按六三制编排，五四制和其他版本尚未支持对照筛选。
- `children.js` 文件头和 `docs/pwa.md`「孩子档案」一节仍写「不上传、没有云同步」。这句已经过时。`children/index.html` 写的是：不登录只在本机；登录后才上传。以页面和 `assets/sync.js` 为准。

云同步（`assets/sync.js`，登录后由 `assets/account.js` 挂上）：

- 六份数据集之一是 `children`，对应键 `cnmChildren.v1`。`api/lib.js` 的 `DATASETS` 注释写明服务端不解析内容。
- `api/schema.sql` 的 `sync_data` 把载荷放在 `payload TEXT`，主键 `(user_id, dataset)`。没有教材列。
- `mergeChildren` 按孩子 `id` 合并，冲突时用整份孩子对象做 `pickNewer`（比较 `updatedAt` 与 `createdAt`）。版本如果做在孩子对象上，会随整份档案走，不会按字段拼接。
- 未登录时 `sync.js` 在 `account.isLoggedIn()` 处直接返回，不挂钩、不上传。
- `localStorage.setItem` 被挂钩：写入 `cnmChildren.v1` 会 `notifyLocalChange`，防抖后推送。因此只要孩子对象里多了字段，登录用户会自动上传，不必新加接口。

诊断记录在另一个键 `cnmChildren.records.v1`，不存教材版本。

### 1.4 `explore/app.js` 的章节浏览

`load` 拉取 `topics.json`、`dependencies.json`、`id-aliases.json`、`cn-curriculum-standards.json`，用 `topicSubject` 滤出当前学科。不读映射文件。

`renderList`：

- 先 `passFilter`：学段 `'p'` 要求 `topic.grade <= 6`，`'j'` 要求 7–9，`'h'` 要求 `>= 10`；年级下拉的值要等于 `String(topic.grade)`。查询串 `?grade=` 在 `applyQuery` 里写入这个 `grade`（数学允许 1–9 和 10–14）。
- 通过的点按 `topic.grade + topic.semester` 分成册。册的顺序：`grade` 升序，`semester === '上'` 的排在前面。
- 册内用 `chapterOf(topic)` 分组。小学（以及匹配「N年级Y册 …」的长册名）去掉册前缀，留下「第N单元 …」或「综合与实践 …」。组的先后是知识点在 `topics` 数组里的出现顺序，没有单独的排序字段。
- 详情 `metaItem('章节', topic.chapter)` 显示人教版原文字符串。

`explore/index.html` 的 `#fGrade` 从一年级列到高中选必三，六年级是普通一项，没有预备年级。

### 1.5 `sw.js` 缓存与 data 加载

`VERSION` 现为 `'v42'`，缓存名 `cnm-pwa-` 加版本。注释要求：改了 `SHELL` 或 `DATA`，或数据结构不兼容，就把 `VERSION` 加一。

`DATA` 预缓存名单只有：

- `data/topics.json`
- `data/dependencies.json`
- `data/cn-curriculum-standards.json`
- `data/questions/index.json`
- `data/questions/math.json`
- `data/id-aliases.json`
- `data/english/days.json`

没有 `data/mappings/` 下的任何文件。安装时 `DATA` 用 `cache.add`，失败不阻止安装。

运行时 `fetch`：路径以 `.json` 结尾的请求走 `staleWhileRevalidate`（先缓存，同时后台更新），不要求该文件在 `DATA` 里。因此新加 `data/mappings/hujiao-math.json` 之后：

- 在线第一次打开会拉取并写入运行时缓存，下一次才稳定拿到新内容。
- 不放进 `DATA` 时，新安装后的第一次离线打开拿不到这个文件。
- 放进 `DATA` 时必须把 `VERSION` 从 `v42` 加到 `v43`，否则已安装的客户端不会因为名单变了而换缓存。

旧对照表（`hujiao_math.json` 等）今天没有任何页面 `fetch`，所以它们既不在预缓存里，也不会进运行时缓存。

### 1.6 `scripts/gen-kp-pages.mjs`

生成 `kp/<id>.html`、`kp/index.html`、`kp/<subject>.html`。读 `data/topics.json`、`dependencies.json`、`questions.json`。不读映射。

章节归属用在三处：

- `stageOf`：`grade` 1–6 写「小学」，7–9 写「初中」，10 及以上写「高中」。`grade` 无效时才回头看 `chapter` 字符串。
- `gradeLabel`：1–9 年级写成「三年级上学期」这种，学期来自 `semester`。
- 单页 `kp-info` 把 `chapter` 原文放进信息行。学科索引 `subjectPage` 按 `grade|semester` 分组，组内再按 `chapter` 原文分组，组顺序是年级升序再 `SEMESTER_ORDER`（上、下、全）。

`tests/test_kp_pages.js` 会真的跑这个脚本，检查页数、标题、先修链接、诊断深链。一期不改生成结果，这个测试保持现状即可。静态页继续写人教版册次。诊断深链进到 `/diagnose/?target=` 之后，册次才由诊断页按版本解释。

### 1.7 已经在仓库里、但页面不读的对照表

`data/mappings/` 现有五个文件，都是旧格式：`edition`、`label`、`status`、`entries` 为数组，条目里 `term` 为 `"上"` / `"下"` / `"全"`。`scripts/validate.py` 的 `check_mapping_files` 强制文件名以 `edition` 开头，`edition` 匹配 `^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$`。

| 文件 | status | 条数 | 说明 |
|---|---|---|---|
| `hujiao_math.example.json` | example | 6 | 占位，文件自己写明不能当目录 |
| `hujiao_math.json` | draft | 160 | 旧格式草稿。条目的 `grade` 只有 1–5，`term` 只有上/下。这 160 个 `topicId` 都是小学数学正式点，其中 6 个在人教版是六年级上册 |
| `sujiao_math.json` | draft | 277 | 苏教版 |
| `sd54_math.json` | draft | 12 | 山东五四制，青岛出版社，不是沪教版 |
| `yilin_english.json` | draft | 230 | 译林英语 |

`hujiao_math.json` 的 `source` 写明：新版（2022 课标，上海教育出版社）核对了一年级上下、二年级上下、三年级上；四、五年级用的是二期课改试用本旧目录；三年级下尚未上架的条目按旧目录并在 `note` 里标待补。没有 `contributor`。这份文件保持 draft，一期可以把它转成新格式当草稿数据，不能把它标成已复核。

`docs/edition-mappings.md` 还写着两条与本方案相反的约定：缺映射时仍显示人教版年级，并提示「该版本映射尚未补齐」；贡献文件审核后合并进 topic。实施时以本文为准。那份指南留着，用来约束尚未迁走的下划线文件。

相邻但一期只加提示、不改筛选的读取点：

- `children/history.js` 的 `chapterOf` 直接返回 `topics[id].chapter`，薄弱点按这个字符串分组。
- `finals/finals.js` 的 `gradesOf` / 排序读 `topic.grade` 与 `topic.semester`。
- `assets/home.js` 的年级卡按 `topic.grade` 计数，链到 `explore/?grade=`。

---

## 2. 映射文件格式细化

### 2.1 一期文件

路径固定为 `data/mappings/hujiao-math.json`。编码 UTF-8，无 BOM。顶层：

```json
{
  "version": "hujiao",
  "subject": "math",
  "stage": "primary",
  "label": "沪教版（上海教育出版社）数学 · 小学",
  "status": "draft",
  "source": "对照依据：教材全称、版次、目录来源、查证日期",
  "contributor": "填写人",
  "entries": {
    "cnm_p001": {
      "grade": 1,
      "term": 1,
      "unit": "单元名",
      "chapter": "节或课时名"
    }
  }
}
```

`entries` 的键就是 `topicId`。值里不再重复 `topicId`。键的书写顺序就是同一单元内的教学顺序，校验和页面都按这个顺序，不按 id 字母序重排。原始文本里同一个键出现两次算错误（`JSON.parse` 会静默留下后者）。

### 2.2 文件头

| 字段 | 必填 | 规则 |
|---|---|---|
| `version` | 是 | 版本标识。小写拼音，`^[a-z][a-z0-9]*$`，不含下划线、不含学科。沪教版固定 `hujiao` |
| `subject` | 是 | 学科 id，与诊断 `subjectOf` 一致。一期只能是 `math` |
| `stage` | 是 | `primary` / `junior` / `senior`。本文件必须是 `primary` |
| `source` | 是 | 非空字符串，最长 2000。写清教材全称、版次、目录来自哪一页或哪个公开目录、查证日期 |
| `contributor` | 是 | 非空字符串，最长 40。填写人的称呼。旧草稿没有署名时写「未署名（由 data/mappings/hujiao_math.json 转换）」，不编造人名 |
| `entries` | 是 | 对象。骨架提交允许 `{}`。`status` 为 `reviewed` 时至少一条 |
| `label` | 否 | 非空中文名，给人和校验日志看 |
| `status` | 否 | `draft` 或 `reviewed`。缺省当 `draft`。页面在 `draft` 时注明册次来自草稿 |
| `note` | 否 | 文件级说明，非空字符串 |

人教版不建映射文件。档案里的 `renjiao` 表示「用 topic 自己的 `grade` / `semester` / `chapter`」。文件头禁止写成 `renjiao`、`hujiao_math`、`pep`。

### 2.3 条目

| 字段 | 必填 | 规则 |
|---|---|---|
| `grade` | 是 | 整数 1–5。表示沪教版小学一至五年级。禁止 6 及以上，禁止字符串 |
| `term` | 是 | 整数 `1` 或 `2`。`1` 是第一学期（上册），`2` 是第二学期（下册） |
| `unit` | 是 | 非空字符串。章节浏览的分组标题，用教材上的单元名 |
| `chapter` | 否 | 非空字符串。节或课时。没有单独节名就省略 |
| `note` | 否 | 非空字符串。拆开、合并、与人教版取舍不同时写在这里。不拿它当章节标题 |

不使用 `"上"` / `"下"` / `"全"`。旧文件里的 `"上"` 转到新文件时写成 `1`，`"下"` 写成 `2`。投影到现有引擎时再临时变成 `semester`：`1 → "上"`，`2 → "下"`。这个中文只活在内存里，不写回 `topics.json`，也不写进映射文件。

小学沪教版没有「全一册」。`term` 不设 `0`、`3` 或「全」。

`unit`、`chapter`、`note` 里禁止出现「示例」「占位」。那是 `hujiao_math.example.json` 的写法，不能进运行时文件。

一条知识点至多一个落点。教材里重复出现时，条目记第一次教学的位置，`note` 写后续复习册。图谱里没有的沪教课文不新建 id，写在文件级 `note`，不进 `entries`。

### 2.4 多学科、多学段怎么拆文件

一个文件只描述一个版本、一个学科、一个学段。

| 文件 | 头字段 | 何时 |
|---|---|---|
| `data/mappings/hujiao-math.json` | `version=hujiao`，`subject=math`，`stage=primary` | 一期 |
| `data/mappings/hujiao-math-junior.json` | `stage=junior` | 二期，一期不创建、页面不请求 |
| `data/mappings/hujiao-physics.json` | `subject=physics`，`stage` 按该科实际学段 | 三期 |
| `data/mappings/hujiao-english.json` | `subject=english` | 三期 |

文件名是 `{version}-{subject}.json`。学段不是 `primary` 时加 `-{stage}`，所以小学文件可以保持任务指定的 `hujiao-math.json`。文件名的 subject、stage 必须和文件头一致。`entries` 的 id 必须属于该学科的正式知识点（数学是 `cnm_` 且 `external` 为 false；物理 `cnp_`，英语 `cne_`，规则与 `validate.py` 的 `topic_subject` 相同）。

同一 `topicId` 不能同时出现在 `hujiao-math.json` 和 `hujiao-math-junior.json`。

版本标识命名：`hujiao`（沪教，上海教育出版社）、以后可有 `sujiao`、`beishida`、`yilin`、`waiyan`、`sd54`。标识是版本，不是「版本_学科」。旧键 `hujiao_math` 只存在于旧文件和 `validate.py` 的 `EDITION_KEY_RE`，不写入孩子档案，不作为 `fetch` 的文件名。

### 2.5 和旧文件的关系

`hujiao_math.json`、`hujiao_math.example.json` 以及其他下划线文件原样留下，继续走 `check_mapping_files` 的旧规则。新加载器只请求连字符文件名，不请求 `hujiao_math.json`。

把草稿转进新文件时：`term` 上/下改成 1/2，数组改成以 `topicId` 为键的对象，`source` 原文保留，并加上「由草稿转换，status 仍为 draft」。`hujiao_math.json` 本身不动，避免一次提交里两套数据各改一遍。

`scripts/validate.py` 若不作区分，会把 `hujiao-math.json` 判为非法：文件名不以 `edition` 开头，且没有 `edition` 字段。一期第一步就要把连字符文件分流到新校验，下划线文件仍走旧校验。

---

## 3. 站点切换逻辑

### 3.1 版本存在哪里

孩子对象增加可选字段 `editions`，按学科存版本标识：

```json
{ "id": "c1", "name": "小满", "grade": "三年级", "textbook": "沪教版", "editions": { "math": "hujiao" }, "createdAt": "..." }
```

- 键是学科 id。一期只写 `math`。值只允许 `renjiao` 或 `hujiao`。
- 缺省：没有 `editions`，或没有 `editions.math` 时，仅当旧字段 `textbook === "沪教版"` 时把数学读成 `hujiao`，其余（含北师大版、苏教版、其他、人教版）把数学读成 `renjiao`。
- `textbook` 保留，备份校验和旧页面还认它。它继续是备注，不决定数学册次。北师大版等没有映射文件，一期不把它们变成「已选版本」。那些档案的数学仍走 `renjiao`，界面说明数学册次按人教版，备注里的版本名不代表册次已经对照过。
- `assets/children.js` 的 `update` 用 `Object.assign` 合并 `clean()` 的结果。`clean()` 必须带上 `editions`，否则编辑昵称不会更新数学版本；只改昵称时也不能把已有 `editions` 丢掉。`add` 写新对象时一并写入。
- 写入 `editions` 时照旧更新 `updatedAt`，云端整份合并才分得出新旧。
- `checkArchive` 在对象自己带 `editions` 时检查形状。不带这个字段的旧备份继续合法。不把未知字段整表拒绝，避免旧备份里将来别的附加字段导入失败。

未登录、或诊断选择「不保存到档案」：

- 没有当前孩子时，数学版本存在 `localStorage['cnmEdition.v1']`，形状 `{ "math": "renjiao" }`，缺省 `renjiao`。
- 这个键不在 `sync.js` 的 `DATASETS` 里，不上传。
- 有当前孩子时，诊断和图谱读 `child.editions` 的解读结果，不用这把客机键。
- 新建孩子时，若客机键里数学已是 `hujiao`，把它抄进新孩子的 `editions.math`。
- 登录用户：`editions` 在 `cnmChildren.v1` 里，随现有推送上云。`api/worker.js` 的 `syncPut` 不解析 payload，不必改表。
- 两台设备各改同一个孩子时，较新的整份孩子对象胜出。一期不做 `editions` 字段级合并。

档案页 `children/page.js` 在原「教材版本」下方加「数学册次」，选项只有人教版（`renjiao`）和沪教版（`hujiao`）。`#book-note` 改成说明：数学的诊断和章节目录看「数学册次」；上面的教材版本仍是备注；沪教版六年级（预备年级）这一期没有册次。

### 3.2 诊断：目标池受版本影响，先修回溯不受

新增一张内存里的落点表，不改 `graph.byId` 里的 topic 对象：

```text
placement[id] = { grade, semester, unit, chapter, volume, order }
```

`semester` 由 `term` 投影（1 → `"上"`，2 → `"下"`）。`volume` 直接生成「三上」这种诊断已有的册键，不把沪教单元名送进 `parseChapter`。沪教单元名对不上 `parseChapter` 的正则，硬拆会得到空 `volume`，整册诊断会漏点。`order` 是该条目在 `entries` 里的序号。

人教版（`renjiao`）不建这张表，`gradeTargets`、`buildTree`、`filterByProgress` 保持今天的路径。

沪教版目标池（整年级、整册、整章，以及 `gradeCard` 里那次 `filterByProgress`）：

- 只保留 `placement` 里有的 id。
- 册次用 `placement.volume`，不用 `parseChapter(topic.chapter)`。
- 学期进度仍调用现有 `filterByProgress` 的规则，但年级和学期改读落点：进度为「上」时，去掉「当前所选年级、落点学期为下」的点。实现上给 `filterByProgress` 增加可选的取值函数，缺省仍读 `topic.grade` / `topic.semester`，人教版测试不用改期望。
- 所选年级为六年级时，池为空。文案说明沪教版六年级是初中预备年级，小学映射未收录。不把人教版六上、六下填进这个池。
- `chapterSummary` 在沪教筛查会话里按 `placement.unit` 分组，顺序用 `order`。

先修回溯不看版本。`createSession`、`nextQuestion`、`graph.prereqs` 仍用 `dependencies.json` 的边。理由和现在的学习进度相同：先修边表示知识先后，筛选只决定「这一册要不要作为被测目标」。沪教把某个先修放到另一册，或者这一期还没标册次，回溯仍然要测到那个点，否则缺口会在册次边界上断开。被回溯到的点如果没有落点，题还在原题库里出，界面上的册次写成「该版本暂未覆盖」。

用户在 URL 里写了 `target=`，或在「暂未覆盖」组里点名「选为目标」，与今天的单点诊断一样，不因为缺映射而拒绝出题。拒绝的是把这些点算进某一沪教册。

学习路径的边不变。有落点的点，同一层内按落点 `grade`、`term` 排；没有落点的点不插入人教年级序列，只保持拓扑序，并标「该版本暂未覆盖」。`gradeRank` 继续只服务人教版路径。

### 3.3 章节浏览按版本排序

`explore/app.js` 在 `load` 之外再请求 `../data/mappings/hujiao-math.json`（仅当数学版本为 `hujiao`）。请求失败时目录不退回人教册次，整表显示加载失败，请刷新。

版本来源与诊断相同：当前孩子的数学版本，否则 `cnmEdition.v1`。图谱页提供与档案一致的数学册次切换；切到沪教且存在当前孩子时，写回该孩子的 `editions.math` 并更新 `updatedAt`。

沪教模式下 `renderList`：

- `passFilter` 的学段和年级比较落点 `grade`，不再比较 `topic.grade`。`?grade=3` 表示沪教三年级。人教版三年级、被标到沪教四年级的点，出现在四年级。人教版六年级、被标到沪教四或五年级的点，出现在那个落点年级。
- 册按落点 `grade` 升序、`term` 1 在前。
- 册内按 `unit` 分组。单元顺序是该 `unit` 字符串在文件中第一次出现的位置。单元内按 `order`。
- 六年级筛选项保留，列表为空，并显示预备年级说明。
- 详情的「章节」显示 `unit`，有 `chapter` 时再接节名。

人教模式的 `renderList`、`chapterOf`、`?grade=` 行为不变。

首页 `assets/home.js` 的年级卡仍按 `topic.grade` 计数。一期不改首页。从首页进入图谱后，沪教模式再按落点重排。首页数字因此仍是人教版各年级的点数，这是一期的已知限制。

### 3.4 无映射知识点怎么呈现

同一句话用在诊断册章树、图谱目录、答题页标签、结果页、`children/history.js` 的章节分组：

> 该版本暂未覆盖

具体放置：

- 不进入沪教的年级、册、单元。
- 目录底部单独一组，标题就是这句话。组内只有知识点名称，不显示 `topic.chapter`、`grade`、`semester`。
- 点进详情后，章节一行仍是这句话。描述、先修、题库保持原样，这些不属于册次。
- `status === "draft"` 时，在册次标题旁加「册次依据为草稿」。
- 历史页在数学版本为沪教时，薄弱点分组用落点单元名；没有落点的归入「该版本暂未覆盖」，组标题不再使用人教 `chapter`。

`finals/finals.js` 一期仍按 `topic.grade` 组卷。期末页加一句「期末范围仍按人教版年级」。不把人教年级的名单标成沪教册次。接入落点留到一期链路稳定之后，不塞进上面的诊断改动里。

静态知识点页一期不改，信息行仍是人教版 `chapter`。这些页是预先生成的，没有孩子档案。不在 HTML 里假装已经换成沪教章节。

---

## 4. 五四制预留

上海义务教育是小学五年、初中四年。六年级是初中预备年级，用初中教材，不是六三制的小学六年级。站点今天全部按六三制切学段，预备年级的正式册名不在本仓库里（`hujiao_math.json` 的 `source` 只写到小学一至五年级的草稿）。下面只预留结构，不填预备年级目录。

### 4.1 一期就要守住的边界

- `stage: "primary"` 的条目 `grade` 只能是 1–5。校验直接拒绝 6。这样预备年级的内容不会因为写成 `grade: 6` 而被 `explore/app.js` 的 `passFilter`（`grade <= 6` 算小学）、`diagnose/app.js` 的 `volumeStage`（首字「六」算 `'p'`）、`gen-kp-pages.mjs` 的 `stageOf`（1–6 算小学）收进小学。
- 人教版六年级的点，只有已经对照到沪教一至五年级时才进入一期文件。应放在预备年级的点保持无映射，呈现为「该版本暂未覆盖」。现有草稿里有 6 个人教六年级上册的点被标进 1–5 年级，转换时可以保留，因为落点年级合法；不要为了「六年级对六年级」把它们改回 6。
- 档案年级字符串仍用现有白名单里的「六年级」，不新增「预备年级」选项。改 `GRADES` 会让旧备份在 `checkArchive` 里失败。一期只在文案里说明：沪教版的六年级是预备年级，小学册次未收录。
- 诊断在沪教模式选六年级时走空态，不调用人教版 `gradeTargets('六年级')`。
- 加载函数的参数留 `stage`。一期调用处写死 `primary`，只 `fetch` `hujiao-math.json`。
- 落点对象带 `stage: "primary"`，二期的初中落点用 `"junior"`，合并时能发现同一 id 跨学段重复。

### 4.2 留到二期再处理的坑

- 年级编号撞车。若二期把预备年级写成 `grade: 6`，现有学段判断会把它显示成小学。二期要在沪教模式下把落点 `stage === "junior"` 且 `grade === 6` 的点放进初中，并给册标题用「六年级（预备）」一类文字。人教模式的六年级仍是小学六上、六下。这一期不去改 `passFilter`、`volumeStage`、`stageOf` 的全局数字界限，避免人教版六年级被一起搬走。
- `filterByProgress` 的 `curGrade`。档案年级「六年级」今天会去比对 `topic.grade === 6` 的下册，那是人教六下。二期必须只比对预备年级落点里 `term === 2` 的点。
- 册次重排跨度更大。人教七至九年级的点会散落到预备年级和七至九年级，顺序与「七上 第一章」无关。二期目录继续用映射的 `unit`，不调用 `parseChapter`。
- 初中文件用 `data/mappings/hujiao-math-junior.json`，`grade` 允许 6–9，`term` 仍是 1 或 2。与小学文件 id 互斥。
- `sd54_math.json` 是青岛出版社的山东五四制草稿，只有 12 条，不能当成沪教初中的底稿，也不能共用 `hujiao` 这个版本标识。
- 沪教初中有、图谱没有的章节仍然不新建知识点。缺口写在该文件的 `note`。
- 是否把档案展示从「六年级」改成「六年级（预备）」只影响沪教版数学的文案，存储值保持「六年级」。二期再改 `children/page.js` 的显示。一期不动白名单。
- 高中不在沪教五四制这一期内。`grade` 10–14 的高中编号继续只属于人教 A 版，小学和初中映射文件都拒绝这些数字。

预备年级各册的官方目录名称，本仓库没有核对记录，二期动笔前另行查证。此处不写册名。

---

## 5. 校验与测试

### 5.1 一致性要查什么

新文件 `data/mappings/hujiao-math.json`：

- 顶层是对象，必填字段齐全，类型符合第 2 节。未知字段报错。
- `version`、`subject`、`stage` 与文件名一致。
- 原始文本无重复键。
- 每个 `topicId` 在 `topics.json` 中存在，`external` 为 false，学科为数学。
- `grade` 是整数 1–5，`term` 是整数 1 或 2，`unit` 非空。出现的 `chapter`、`note` 为非空字符串。
- 条目字段只有 `grade`、`term`、`unit`、`chapter`、`note`。
- `unit` / `chapter` / `note` 不含「示例」「占位」。
- `topics.json` 中仍然没有任何 `mappings` 字段。这条用来守住「不把对照写回主数据」。
- 旧的五个下划线文件仍能通过现有 `check_mapping_files`。新校验不要放宽旧规则。

覆盖率只打印、不设最低线，避免为了凑满而填写未核对的行。口径：

- 分母：id 匹配 `^cnm_p\d+$` 且 `external` 为 false 的知识点。撰写时是 284，测试里每次从 `topics.json` 数，不把 284 写死。
- 分子：分母中的 id 出现在 `entries` 里的个数。
- 另打印：分母里人教 `grade === 6` 的点数、其中已有落点的点数、`entries` 条数。人教六年级共 48 个点，多数在一期会留在分母里却不进分子，覆盖率低于 100% 是预期。
- 分子大于分母（条目指向了初中或高中 id）时失败，不只打印。

投影函数用小型夹具测，不把整份草稿当断言：

- 有条目的点：对外的 `grade` / `term` / `unit` 来自映射；`topics` 里原对象的 `grade`、`semester`、`chapter` 仍是人教值。
- 无条目的点：`covered === false`。把它放进沪教三年级池时，池里没有它。
- `term: 2` 且进度为「上」、当前年级等于落点年级时，该点在 `deferred`，不在目标 id 里。进度为「下」时保留。
- 人教路径不传取值函数时，`filterByProgress` 仍按 `topic.semester` 排除下册。现有 `tests/test_engine.js` 的人教用例保持通过。
- 先修：目标点有落点、先修点没有落点时，`graph.prereqs` 仍包含该先修 id。展示名用的册次函数返回「该版本暂未覆盖」，返回值里没有人教 `chapter` 原文。
- 排序：同一 `grade`+`term` 下，单元顺序等于文件中首次出现的顺序，而不是 id 排序。

档案与同步：

- 无 `editions` 的旧备份能导入。
- `textbook` 为沪教版且没有 `editions.math` 时，读函数返回 `hujiao`。`textbook` 为苏教版时返回 `renjiao`。
- `editions.math` 为 `hujiao` 时，即使 `textbook` 仍是人教版，读函数也返回 `hujiao`（备注和数学册次可以不同）。
- `editions.math` 写成 `hujiao_math` 或 `beishida` 时 `checkArchive` 失败。
- `mergeChildren` 在本地孩子较新且带 `editions`、云端同 id 较旧且不带该字段时，合并结果保留 `editions`。

### 5.2 新增测试文件与 `npm test`

新增：

- `tests/test_hujiao_mapping.js`：第 5.1 节的文件格式、topicId、覆盖率打印、主数据不含 `mappings`。文件还不存在时失败并提示先提交骨架，避免页面先去 `fetch` 一个 404。骨架阶段 `entries` 允许 `{}`，覆盖率打印 0。
- `tests/test_edition_view.js`：落点投影、目标池、进度过滤、先修 id 仍在、无映射文案。纯函数，不启浏览器。被测函数放在新文件 `assets/edition.js`（浏览器挂 `window.CnmEdition`，Node 用 `module.exports`），诊断和图谱都调用它，避免两处各写一份筛选。

接入方式：

- `package.json` 的 `scripts.test` 在 `python3 scripts/validate.py` 之前加上  
  `node tests/test_hujiao_mapping.js && node tests/test_edition_view.js &&`。
- `.github/workflows/ci.yml` 为这两条 `node tests/...` 各加一个步骤。`tests/test_ci_workflow.js` 的「CI 与 npm test 覆盖全部无浏览器依赖的 Node 测试」会扫描 `tests/test_*.js`（排除 `*_browser.js`），缺任何一边都会失败。两处名单放在同一次提交。
- `scripts/validate.py`：文件名含连字符的走新校验函数；`hujiao_math.json` 这类继续走 `check_mapping_files`。校验结束时的「教材版本对照」打印行同时给出新文件条数。
- `tests/test_children.js`、`tests/test_sync.js` 在原文件里加第 5.1 节的档案用例，不再新开文件。这两个文件已经在 `npm test` 和 CI 里。

不把 `tests/test_children_browser.js` 放进 `npm test`。那份测试需要本机 Chrome，现有 CI 明确排除 `*_browser.js`。

`python3 scripts/validate.py` 在新文件落地后必须仍打印 `VALIDATION PASSED`。只跑新测试不够，因为旧分流写错时是 `validate.py` 先失败。

---

## 6. 一期实施步骤

每步可以单独提交。前一步的测试在后一步开始前是绿的。所有步骤都不修改 `data/topics.json`、`data/dependencies.json` 和题库。

### 步骤 1 · 校验分流与空骨架

工作量：半天。

- 改 `scripts/validate.py`：连字符映射文件走新规则，下划线文件走原 `check_mapping_files`。
- 新增 `data/mappings/hujiao-math.json`，文件头按第 2 节填，`status` 为 `draft`，`entries` 为 `{}`，`source` 写「骨架，条目尚未迁入」。`contributor` 用提交者的称呼；若沿用旧草稿且查不到署名，用第 2.2 节的「未署名」句子。
- 新增 `tests/test_hujiao_mapping.js`。
- 改 `package.json` 的 `test` 脚本和 `.github/workflows/ci.yml`。

验收：`node tests/test_hujiao_mapping.js`、`node tests/test_ci_workflow.js`、`python3 scripts/validate.py` 通过。`git diff -- data/topics.json` 为空。五个旧映射文件的条数不变。

### 步骤 2 · 落点投影

工作量：一天。

- 新增 `assets/edition.js`：读入映射对象（调用方负责 `fetch`），生成 `placement`，提供「某 id 的册次文案」「按年级册次收集目标 id」「按进度再滤一层」「单元排序」。
- 新增 `tests/test_edition_view.js`，并把它写进 `package.json` 与 `ci.yml`。
- `filterByProgress` 若增加可选取值函数，缺省行为与现在一致，`tests/test_engine.js` 不改断言。

验收：`node tests/test_edition_view.js` 通过。投影不写回 topic 对象（测试里对原对象做深比较）。

### 步骤 3 · 档案按学科记住数学版本

工作量：一天。

- 改 `assets/children.js`：`editions` 的读写与 `checkArchive`。解读函数放在这里或 `assets/edition.js`，诊断和图谱共用，避免「沪教版备注」的兼容规则写两遍。
- 改 `children/page.js`、`children/index.html`：增加数学册次，改 `#book-note`。
- 无孩子时的 `cnmEdition.v1` 由诊断页和图谱页读写；新建孩子时从该键抄初始值。
- 在 `tests/test_children.js`、`tests/test_sync.js` 加第 5.1 节的用例。

验收：旧备份 JSON（无 `editions`）仍能通过 `checkArchive`。登录路径不改 `api/`。手动看档案页：只改数学册次时 `textbook` 备注可以保持不动，刷新后 `editions.math` 仍在。

### 步骤 4 · 诊断目标池

工作量：一天。

- 改 `diagnose/index.html`：在 `engine.js` 之后引入 `../assets/edition.js`。
- 改 `diagnose/app.js` 的 `loadData`：数学版本为 `hujiao` 时请求 `../data/mappings/hujiao-math.json`。
- `buildTree`、`gradeCard`、整章按钮在沪教模式下走落点表。六年级空态用第 4 节的文案。
- 答题页、结果页的章节标签走册次文案函数。
- `sw.js` 的 `SHELL` 加入 `assets/edition.js`，`VERSION` 加一。这一步页面已经会请求脚本；缓存名单与脚本同时提交，避免离线缺文件。映射 JSON 的预缓存放在步骤 7，届时再加一版，两步的缓存版本不要挤在同一个未发布的中间号上。

验收：人教模式用现有 `tests/test_engine.js` 锁住筛选。沪教模式用 `test_edition_view.js` 的夹具锁住池子。浏览器里看诊断页：数学选沪教、年级选三上，列表里的单元名来自映射；无映射的点只出现在底部「该版本暂未覆盖」，行内没有人教 `chapter`。点一个有落点的目标并答错到回溯后，先修点仍会出现。

### 步骤 5 · 图谱目录

工作量：一天。

- 改 `explore/index.html`、`explore/app.js`：引入 `assets/edition.js`，按第 3.3 节分组排序，详情改章节行。
- `SHELL` 已含 `explore/app.js`。若 `index.html` 新增脚本标签，把该脚本路径补进 `SHELL`，`VERSION` 与步骤 4 的发布安排对齐：同一次上线只保留最终的版本号，开发中的连续加一在合并前收成一次。

验收：`?grade=3` 在沪教模式下只列出落点年级为 3 的点。人教模式下列表与改动前一致（抽查一年级上册第 1 单元仍是 `chapterOf` 去掉册前缀后的原文）。搜索知识点名称能在「暂未覆盖」组里找到无映射的点。

### 步骤 6 · 历史页与期末提示

工作量：半天。

- 改 `children/history.js`：沪教数学的薄弱点分组用落点单元名，无落点一组「该版本暂未覆盖」。
- 改 `finals/index.html` 或 `finals/finals.js`：加第 3.4 节那句期末说明。不改 `gradesOf` 的取年级逻辑。
- `children/history.js` 已在 `SHELL`。若脚本依赖 `assets/edition.js`，确认历史页引入了它。

验收：一个无映射 id 出现在薄弱列表时，分组标题是「该版本暂未覆盖」。人教模式历史页仍按 `topics[id].chapter` 分组。

### 步骤 7 · 映射文件进预缓存

工作量：半天。

- `sw.js` 的 `DATA` 加入 `data/mappings/hujiao-math.json`。
- `VERSION` 加一（相对步骤 4–6 合并后的号；当前仓库是 `v42`，若中间步骤已加过，则在那个号上继续加）。
- 确认页面请求的路径与 `DATA` 里的相对路径在站点根目录下是同一个 URL。

验收：本地用 `python3 -m http.server` 打开站点，安装 service worker 后，缓存中有该 JSON。DevTools 勾选 Offline 再进诊断，沪教册次仍能读到（骨架阶段是空表，空态文案正常，而不是请求失败）。

### 步骤 8 · 迁入小学草稿

工作量：一天。

- 把 `data/mappings/hujiao_math.json` 的 160 条转成新结构，写入 `hujiao-math.json` 的 `entries`。`term` 上 → `1`，下 → `2`。`unit`、`chapter`、`note` 原样搬。键顺序与旧数组顺序一致。
- `source` 保留旧文，并写明转换日期与「status 为 draft，三下与四、五年级的依据见原文，未另作复核」。
- 不改 `hujiao_math.json`。
- `tests/test_hujiao_mapping.js` 增加三条抽样：`cnm_p001` 的 `grade`/`term` 与旧文件一致（旧 `term` 已按上表转换）；全部落点 `grade` 在 1–5；条数等于旧文件条数 160。160 可以写成与旧文件长度比较，避免两处数字以后分叉。

验收：`node tests/test_hujiao_mapping.js` 与 `python3 scripts/validate.py` 通过。覆盖率打印约 160/284。抽一个旧文件里人教六年级、落点在 1–5 的 id，确认新文件 `grade` 不是 6。`topics.json` 的 diff 仍为空。

草稿里的目录争议（三年级下未上架、四五年级旧版）不在这一步重核。重核是后续数据提交，按册替换 `entries` 里对应的键，并把 `source` 里已复核的册次写清楚。`status` 保持 `draft`，直到另一人按教材对过并改成 `reviewed`。

### 步骤 9 · 让旧说明指向本文

工作量：半天。

- 改 `docs/edition-mappings.md` 开头：运行时映射以本文为准；该文继续只约束下划线贡献文件，不再写「缺映射时显示人教版年级」。
- `docs/pwa.md` 里「教材版本只是备注」「档案不上传」两处与代码不符。这一步只改「教材版本」那句，改成数学册次看 `editions.math`，并指向本文。云同步那句涉及面更大，不在一期顺手改写，避免把 PWA 说明整节重写进这个提交。

验收：仓库内搜索「该版本映射尚未补齐」，不再作为现行行为出现。下划线文件的校验说明仍在。

### 工作量合计

| 步骤 | 内容 | 粗估 |
|---|---|---|
| 1 | 校验分流与空骨架 | 半天 |
| 2 | 落点投影与单测 | 一天 |
| 3 | 档案按学科存版本 | 一天 |
| 4 | 诊断目标池与无映射分组 | 一天 |
| 5 | 图谱按落点排序 | 一天 |
| 6 | 历史页与期末提示 | 半天 |
| 7 | service worker 预缓存 | 半天 |
| 8 | 160 条草稿迁入 | 一天 |
| 9 | 旧文档改指向 | 半天 |

合计约六天半。步骤 8 可以紧跟步骤 1，让后面的浏览器验收一开始就有单元名；它不依赖 2–7 的代码，只依赖新文件格式。步骤 4 和 5 都依赖步骤 2 和 3。

一期不做的事：不改 `gen-kp-pages.mjs` 的输出；不改首页年级卡的计数；不让期末计划按沪教册次抽题；不创建 `hujiao-math-junior.json`；不读取 `hujiao_math.json` 作为运行时数据；不把对照写进 topic 的 `mappings`。
