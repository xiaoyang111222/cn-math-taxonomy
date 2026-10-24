# 题库说明（data/questions.json）

给每个正式知识点建的小题库，供 `diagnose/` 诊断工具按「每个知识点最多 2 题」的规则出题。现在共 **828** 个知识点（小学 242 + 初中 315 + 高中必修 143 + 高中选择性必修 128），**3459** 题。三个学段一样出题。**题目与答案全部由 AI 生成，没有教师审核**；正确性靠下面的自动核验和独立复核尽量保证，但不等于权威答案。高中题只有自动核验，没有盲解。

下面「统计」「核验方法」里标成第五轮的数字只计当时的 1407 道初中题。全库和小学见文末「小学题（2026-10-19）」。

## 格式

`data/questions.json` 是一个 JSON 数组，每题一个对象：

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | `<topicId>_q<N>`，如 `cnm_221_q2`；`_q1` 由 `topics.json` 的 `diagnostic_question` 迁移而来（题干以原题文字开头，必要时在后面追加答案格式说明） |
| `topicId` | 是 | 知识点 id，必须是正式知识点 |
| `difficulty` | 是 | `basic`（直接套定义 / 一步计算）、`standard`（课本例题水平，2–3 步）、`advanced`（综合、多步或易错点） |
| `type` | 是 | `numeric` 数值题、`choice` 选择题、`short` 短答题、`self` 开放题（必须自评） |
| `prompt` | 是 | 中文题干，自包含（几何条件用文字、长度、角度、坐标写全，不看图也能读懂条件）。单位写在题干里，答案不带单位。需要看形状时另有可选的 `figure` |
| `answer` | 是 | 字符串。numeric：一个数（整数 / 小数 / 分数 `a/b` / 负数），多个答案用全角「，」分隔；choice：正确选项字母；short：标准短答案；self：参考答案 |
| `choices` | choice 必填 | `[{"key":"A","text":"…"}, …]`，3–4 个选项，key 依次为 A、B、C、D，选项文字互不相同。选项可以另有 `figure`（内联 SVG） |
| `figure` | 否 | 题干配图，内联 SVG 字符串（只含 `viewBox`，用 `currentColor`，不引用外网）。诊断页和知识图谱样题会画在题干下面 |
| `hideChoiceText` | 否 | 仅选择题，且为 `true`。每个选项都有 `figure` 时，页面只显示图形、不显示选项名称（名称仍留在 `text` 里，用来判分和显示参考答案）。用于「下面哪一个是长方体」这类题，避免名称直接泄题 |
| `accept` | 否 | short（也可用于 numeric）的等价答案列表 |
| `explanation` | 是 | 1–3 句中文解析，答题后显示 |
| `verify` | 否 | 一个 Python 表达式字符串，用于机器核验 `answer`（见下） |
| `unordered` | 否 | numeric 且多个答案顺序无关时为 `true`（如方程的两个根）；没有这个字段的多答案题按顺序比较 |
| `fixed_from_source` | 否 | 迁移 `diagnostic_question` 时补充了条件（原题有歧义）才有，写明原因。目前 3 题：`cnm_061_q1`、`cnm_070_q1`、`cnm_253_q1` |

`topics.json` 里的 `diagnostic_question` 原样保留（兼容；题库缺失时诊断工具回退到它）。

## 统计（第五轮，只计初中 1407 题）

- 当时总数 **1407** 题，覆盖全部 315 个初中知识点；每个知识点 4 题（168 个）或 5 题（147 个），最少 4、最多 5、平均 4.47。这些题后来没有改写。
- 按 type：numeric 903，choice 475，short 23，self 6；**numeric + choice 占 97.9%**。
- 按 difficulty：basic 591，standard 537，advanced 279。每个知识点都含 basic 和 standard，并且除 q1 之外至少还有一道 basic（诊断时「第二题优先出 basic」要用）。
- choice 的正确选项分布：A 124，B 126，C 126，D 99；101 题 3 个选项，374 题 4 个选项。

## 核验方法

### 1. 自动核验：`python3 scripts/verify_questions.py`

numeric 和 choice 题可以带 `verify` 表达式，脚本在**受限环境**里求值（Python `ast` 白名单：四则运算、`**`、`//`、`%`、比较、列表 / 元组 / 推导式、下标；只能调用 `Fraction sqrt pi sin cos … comb perm gcd lcm sum min max sorted range ceil floor mean median pvariance …`，外加 `solve2`（解二元一次方程组，精确分数）、`roots2`（一元二次方程实根）；没有 import、属性访问、赋值，单次求值 2 秒超时），再与 `answer` 比较：

- numeric：结果与 `answer` 逐项比较；整数 / 分数结果**精确比较**，浮点结果容差 1e-9；多个答案按 `unordered` 决定是否顺序无关；
- choice：结果与**正确选项的内容**比较（选项是数时按数值比较，否则要求文字完全相同），同时要求没有第二个选项与它相同（防双解）。

脚本会同时做格式检查，输出 `auto_verified`（有 verify 且通过）、`mismatch`、`unverifiable`，明细写入 `data/verification_report.json`。第五轮当时（只计初中；全库数字见文末）：

| 项 | 数量 |
|---|---|
| numeric + choice 题 | 1378 |
| **auto_verified**（有 verify 且通过） | **875**（占 numeric + choice 的 63.5%） |
| **mismatch** | **0** |
| unverifiable（无 verify） | 532：choice 464（选项是文字 / 式子，没法用表达式算）、numeric 39（推理型）、short 23、self 6 |

自动核验的局限：`verify` 是出题者自己写的，可能和答案「同源」（算法写错一样会错）；个别题的 verify 只是把常数列出来（出题者在备注里标注过 `cnm_248_q4`、`cnm_093_q5`），这类题的保证主要来自第二遍独立复核。

### 2. 独立第二遍复核：`scripts/second_pass.py`

由**没看到答案**的独立解题者（Claude 子任务）重新解题，再逐题与题库比对：

- 把 numeric / choice / short 题去掉 `answer`、`explanation`、`verify`、`accept`，只留题干和选项，分块给解题者（`second_pass.py prepare`）；解题者只能读自己的那一块，我核对过他们的工具调用记录，没有读过题库或其它文件；
- **A 轮（全量）**：19 个解题者，1401 道题（numeric 903、choice 475、short 23），一次性作答；
- **B 轮（风险题，更仔细）**：16 个解题者，752 道题——所有没有 `verify` 的 numeric / choice / short 题加上全部 `advanced` 题；要求分小批逐题推理、非平凡的计算用 Python 精确算、每题写出推导（`work_b_NN.json`）；
- 解题者的原始答案、推导和存疑备注保留在 `data/_second_pass/`（`ans_NN.json`、`ans_b_NN.json`、`work_b_NN.json`、`notes_NN.json`、`mismatches*.json`），题干分块文件（`blind_*.json`）可随时用 `second_pass.py prepare` 重新生成；
- `second_pass.py compare` 比对：choice 比字母，numeric 比数值（有序 / 无序），short 规范化后比 `answer` + `accept`；不一致的逐条裁决。

结果（详见 `data/verification_report.json` 的 `second_pass` 与 `data/second_pass_log.json`）：

- A 轮 3 处不一致（`cnm_090_q3`、`cnm_213_q4`、`cnm_311_q4`），我用精确计算逐条裁决，**3 处都是解题者算错，题库答案正确**；B 轮 0 处不一致。
- **发现并修正答案错误：0 处**。发现并修正的其它问题 5 处：4 处题干含糊（解题者提示后改写）、1 处解析写错。例：
  - `cnm_133_q2`「到线段 AB 两个端点距离相等的点，一定在：」只在平面内成立 → 补「在同一平面内」；
  - `cnm_053_q3` 题干写「图中……」却没有图 → 删去「图中」；
  - `cnm_306_q2` 样本方差除以 n 还是 n−1 有口径之分 → 写明「各数据与平均数之差的平方的平均数」；
  - `cnm_151_q3` 解析把正确选项 C 写成「没提干净」→ 由「解析里选项字母与答案矛盾」的扫描发现并改正。
- 解题者另外标出 16 条「存疑」，逐条看过：除上面 4 处外，题干条件已足以唯一确定答案，不改。
- 报告里 `mismatch = 0`，`second_pass_mismatch = []`。
- 出题阶段每位出题者交稿前自己跑过 `verify_questions.py --file`（要求 mismatch = 0，格式错误 = 0）；这一步里被他们自己改掉的问题没有留下记录，所以不计入上面的「修正」数字。

### 3. 格式校验：`python3 scripts/validate.py`

题 id 唯一且与 topicId 一致；topicId 存在且不是外部节点；`difficulty` / `type` 合法；choice 有 3–4 个选项、key 依次为 A–D 且不重复、answer 是某个 key、选项文字不重复；numeric 的 answer 能解析成数（含分数、负数、多值）；必填字段非空；没有未知字段；每个正式知识点 ≥ 3 题且含 basic 与 standard；q1 存在且题干以 `diagnostic_question` 开头（或带 `fixed_from_source`）；numeric + choice 占比 ≥ 60%。打印题量统计。

## 局限

- **没有教师审核**；独立复核的解题者与出题者是同一模型家族，如果对某个知识点有共同的误解，这种错误两边都不会暴露。「0 处答案错误」说明没有发现分歧，不是「保证无错」。
- 约 36% 的 numeric + choice 题没有 `verify`，主要是选项为文字 / 式子的选择题，它们只靠独立复核保证。
- 题干纯文字，不能画图：几何题用文字描述条件，没有图形题、作图题、证明题（证明思路类用 choice 或 `self`）。
- **选择题干扰项**只对应「典型错误」的猜测，没有真实学生数据校准；难度标注（basic / standard / advanced）是出题者的主观判断，同一难度内也没有区分度数据。
- 每个知识点只有 4–5 题：重测几次后会重复（诊断工具会优先出没出过的题，出完才重复）；也不足以支撑严肃的测评。
- numeric 答案限于有理数（含小数），含根号、π 的答案只能做成选择题；short 题（23 道）和 self 题（6 道）靠规范化精确匹配或自评，等价写法可能被判成「需自评」。
- 初中批次文件合并后已删除。小学批次留在 `data/_qbatches/primary_g1.json` … `primary_g6.json`。要改题直接改 `data/questions.json`（小学题若从批次重编，需按 `scripts/build_primary.py` 的说明先恢复含 `cnm_ext_*` 的依赖再编译），再跑 `verify_questions.py` 和 `validate.py`。

## 小学题（2026-10-19）

每个小学正式知识点 4 题，共 **864** 题，id 形如 `cnm_p001_q1`。字段与初中题相同。q1 的题干等于该知识点 `diagnostic_question.question`；q1 和 q2 都是 basic，另外两道是 standard。没有 short、self、advanced。

| 项 | 小学 864 题 | 全库 2271 题 |
|---|---|---|
| type | numeric 644，choice 220（合计 100%） | numeric 1547，choice 695，short 23，self 6（numeric + choice 占 98.7%） |
| difficulty | basic 433，standard 431 | basic 1024，standard 968，advanced 279 |
| 每知识点 | 正好 4 题；每个点都有 basic 和 standard | 最少 4，最多 5，平均 4.28（4 题 × 384，5 题 × 147） |
| auto_verified | 864（每道 numeric / choice 都有 `verify` 且通过） | **1739** |
| mismatch | 0 | **0** |
| unverifiable | 0 | 532（choice 464、numeric 39、short 23、self 6，都是原来的初中题） |

低年级题用小学生说法，避免还没学过的符号（例如一年级不用字母方程）。numeric 的 `verify` 用 `scripts/verify_questions.py` 同一套受限求值。

独立复核记为 C 轮，写在 `data/second_pass_log.json`，名称是「C：小学题独立复核（primary_recheck，只读题干和选项，不读 answer / verify / explanation）」：`scripts/primary_recheck.py` 只根据题干和选项重算，864 题不一致 **0**。这一轮不是另请一位没看过出题脚本的人逐题手解，而是另一段不读取 `answer` / `verify` / `explanation` 的程序重算；和初中 A/B 轮的盲解不是同一做法。A/B 轮的记录没有改。`second_pass_mismatch` 仍是空数组。

小学题同样没有教师审核。二年级下册等册次目录若以后改了，对应题目的情境不一定要改，但章节归属要跟着教材重核。

## 高中必修题（2026-10-20）

每个人教 A 版（2019）必修知识点 4 题，共 **572** 题，id 形如 `cnm_h001_q1`。字段与小学、初中题相同。q1 的题干等于该知识点 `diagnostic_question.question`；q1 和 q2 都是 basic，另外两道是 standard。没有 short、self、advanced。诊断题的 `answer` 是数值，或正确选项的**文字**（不是 A/B/C/D：选项字母按知识点序号轮换）。

| 项 | 高中 572 题 | 全库 2843 题 |
|---|---|---|
| type | numeric 362，choice 210（合计 100%） | numeric 1909，choice 905，short 23，self 6（numeric + choice 占 99.0%） |
| difficulty | basic 286，standard 286 | basic 1310，standard 1254，advanced 279 |
| 每知识点 | 正好 4 题；每个点都有 basic 和 standard | 最少 4，最多 5，平均 4.22（4 题 × 527，5 题 × 147） |
| auto_verified | 572 | **2311** |
| mismatch | 0 | **0** |
| unverifiable | 0 | 532（仍是原来没有 verify 的初中题） |

可计算的题（计算、化简、求值、解的个数或端点）带 `verify`。不等式的解集如果是区间，改成选择题，或改成问整数解的个数、最小整数解。方差题在题干里写明除以 n，并用 `pvariance`。百分位数题在题干里写了人教教材的位置规则（排序后按 n×p% 取位；不是整数就取下一位，是整数就取相邻两项的平均），并标待核。含 √2、√3/2 这类不能化成简单分数的值做成选择题，或改成平方后的有理数。

`second_pass_log.json` 的 D 轮写明：高中必修题由 `scripts/hs_build.py` 用同一条 `verify` 表达式求出答案再写入，然后 `verify_questions.py` 再比对一次。mismatch 为 0 只说明格式和表达式一致，**不是另一遍独立解题**。没有做初中 A/B 轮那种盲解。概念题的选项文字与 verify 返回的字符串相同。批次在 `data/_qbatches/high.json`。

立体几何的判定、性质是选择题，不要求学生写出证明。高中题同样没有教师审核。

## 高中选择性必修题（2026-10-20）

每个人教 A 版（2019）选择性必修知识点 4 题，共 **512** 题，id 从 `cnm_h144_q1` 起。字段与必修题相同。q1、q2 是 basic，q3、q4 是 standard。

**2026-10 补 advanced**：选择性必修第一册第一章（`cnm_h144`–`cnm_h164`，21 个知识点）每点追加一道 `advanced`（id 形如 `cnm_h144_q5`），共 **21** 题，该章合计 533 题。题目是多步计算（先求坐标或模，再代入公式），答案仍由 `verify` 求值后写入。生成脚本 `scripts/hs_adv1.py` 会拒绝把 `isqrt` 用在非完全平方数上——`isqrt(2)` 得 1 而不是根号 2，这类写法会让答案在毫无提示的情况下算错。题干自包含：不写「同一 / 上题 / 该函数」这类指着别的题的说法，也不问「本知识点 / 课标是否要求」。

| 项 | 选择性必修 533 题 | 全库 3355 题 |
|---|---|---|
| type | numeric 340，choice 172 | numeric 2251，choice 1075，short 23，self 6 |
| difficulty | basic 256，standard 256，advanced 21 | basic 1566，standard 1510，advanced 279 |
| 每知识点 | 正好 4 题 | 最少 4，最多 5 |
| auto_verified | 533 | **2823** |
| mismatch | 0 | **0** |
| unverifiable | 0 | 532（仍是原来没有 verify 的初中题） |

E 轮和 D 轮一样：`scripts/hs_sel_build.py` 用同一条 `verify` 写出答案，再由 `verify_questions.py` 比对，**不是盲解**。批次在 `data/_qbatches/high_sel.json`。

## 高中英语题（2026-10-21）

每个人教版（2019）高中英语知识点 4 题，共 **1036** 题，id 从 `cne_h001_q1` 起。全部是选择题。q1 的题干等于该知识点 `diagnostic_question.question`，答案是正确选项的文字（不是 A/B/C/D）。q1 和 q2 是 basic，q3 和 q4 是 standard。题干自包含：不以「同一 / 上题 / 该题 / 同上」开头，也不出现「本知识点 / 课标 / 是否要求」。短文是新写的，不抄教材原文。没有听力、口语。

小学英语 788 题、初中英语 980 题此前已经入库。全库现在 **6159** 题（数学 3355 + 英语 2804）。`verify_questions.py`：auto_verified **5627**，mismatch **0**，unverifiable **532**（仍是原来没有 verify 的初中数学题）。高中英语的 `verify` 返回正确选项的文字，和出题用的是同一条逻辑，**不是盲解**。生成脚本在 `scripts/enh_b1.py` 到 `enh_s4.py`，由 `scripts/enh_build.py` 写入 `questions.json`。

## 2026-10 英语新版教材

按新版人教 PEP 和 Go for it! 新增 23 个知识点（小学 `cne_p198`–`cne_p208`，初中 `cne_j246`–`cne_j257`），每个 4 道选择题，共 92 题，干扰项是常见错误形式或近形词。全库现在 **6355** 题（数学 3459 + 英语 2896）。`verify_questions.py`：auto_verified **5823**，mismatch **0**，unverifiable **532**（没有变）。
