# 八上、八下英语官方阅读器核对（2026-11-11）

在国家中小学智慧教育平台打开人教版2022课标修订电子教材，核目录和版权页。没有下载教材 PDF，也没有改课标 `verbatim` 或 `standards.confidence`。稳定 id 不变。题目保持原技能，本轮未改写，也没有新增知识点。

## 书号与目录

| 册次 | 书名 | ISBN | 平台 contentId |
| --- | --- | --- | --- |
| 八年级上册 | （根据2022年版课程标准修订）义务教育教科书•英语 八年级上册 | 978-7-107-38944-3 | 5700edda-c4c1-11ea-29c4-8fe2c1ca7beb |
| 八年级下册 | （根据2022年版课程标准修订）义务教育教科书·英语八年级下册 | 阅读器未见印刷书号，未填写 | 467816b8-e76c-43fc-afc7-91638f97dba8 |

两册均为人民教育出版社、课程教材研究所编著，主编刘道义、郑旺全，分册主编张献臣。八上版权页未见版次、印次或审核信息；书号来自封底条码。八下封面印章有「国家教材委员会专家委员会审核通过 2024」。版权页未见版次、印次或审核年份。印刷书号：官方阅读器第 152–154 页底部和版权页底部（含 400% 放大）均未见书号或条码，未填写、未猜测。

八上官方 8 单元（`UNITS` 用字与现有 data chapter 一致）：

| 单元 | 书页 | 语法 / 发音（只记录，未建点） |
| --- | --- | --- |
| Unit 1 Happy Holiday | 1 | indefinite pronouns; review of the simple past tense; /iː/ /ɪ/ /i/ /e/ /æ/, rhythm |
| Unit 2 Home Sweet Home | 11 | Can/Could for polite requests and permission; sense groups and pauses |
| Unit 3 Same or Different? | 21 | comparatives with -(i)er and more; as … as; intonation |
| Unit 4 Amazing Plants and Animals | 31 | superlatives with -(i)est and most; sentence stress; noun suffixes |
| Unit 5 What a Delicious Meal! | 41 | exclamatory sentences; countable/uncountable nouns |
| Unit 6 Plan for Yourself | 51 | future with be going to; infinitives as objects; weak forms |
| Unit 7 When Tomorrow Comes | 61 | simple future (will) |
| Unit 8 Let's Communicate! | 71 | zero and first conditionals; pronunciation review（词尾辅音丛，不是 -s/-es） |

八上附录：Reading Plus 81，Listening Scripts 93，Pronunciation 102，Grammar 104，Vocabulary in Each Unit 111，A–Z 123，from Primary School 135，Irregular Verbs 136。

八下官方 8 单元。目录没有 Pronunciation 栏，附录也没有 Pronunciation。

| 单元 | 书页 | 语法（只记录，未建点） |
| --- | --- | --- |
| Unit 1 Time to Relax | 1 | Infinitives as adverbials and object complements |
| Unit 2 Stay Healthy | 11 | Modal verbs for advice (should, could); Reflexive pronouns |
| Unit 3 Growing Up | 21 | Conjunctions (although, until, so that) |
| Unit 4 The Wonders of Nature | 31 | Comparative and superlative adjectives/adverbs (review); Large numbers |
| Unit 5 Nature's Temper | 41 | Past continuous tense |
| Unit 6 Crossing Cultures | 51 | Conjunctions (so … that, unless, as soon as) |
| Unit 7 A Good Read | 61 | Present perfect (already, yet, never, ever, just) |
| Unit 8 Making a Difference | 71 | Present perfect (since, for) |

八下附录：Reading Plus 81，Listening Scripts 95，Grammar 105，Vocabulary in Each Unit 113，A–Z 125，from Primary School 136，Irregular Verbs 137。

生成器 `scripts/enj_build.py` 的八上、八下 `UNITS` 已改成上面 8+8，并加 `(8, 上, 90)`、`(8, 下, 90)` 待核。`chapter()` 对八年级 90 分别返回「八年级上册 待核」「八年级下册 待核」。九年级 `UNITS` 仍是旧版标题，本轮不改。

## 保留在官方单元

生成器的 grade、semester、unit 已改成官方课号，使 `chapter()` 与下表章节一致。这些点在数据里的 chapter 原本已经是官方标题，同步没有改它们的章节字符串，也没有改 name、description。`cne_j249`、`cne_j250` 不在 TOPICS，已挂 U1、U3，未改。`cne_j251` 反身代词不在 TOPICS，已挂 Stay Healthy，未改。

| 章节 | id |
| --- | --- |
| 八年级上册 第1单元 Happy Holiday | `cne_j099` 假期地点、`cne_j100` 一般过去时叙述假期、`cne_j101` 谈论假期去向、`cne_j102` 读假期短文 |
| 八年级上册 第2单元 Home Sweet Home | `cne_j137` 意群停顿、`cne_j150` 家务、`cne_j151` could 表示请求、`cne_j152` 礼貌提出请求、`cne_j153` 读家务对话 |
| 八年级上册 第3单元 Same or Different? | `cne_j108` 性格形容词、`cne_j109` 形容词比较级、`cne_j110` 用 than 比较、`cne_j111` 比较两人、`cne_j112` 读人物比较 |
| 八年级上册 第4单元 Amazing Plants and Animals | `cne_j114` 形容词最高级 |
| 八年级上册 第5单元 What a Delicious Meal! | `cne_j072` 感叹句、`cne_j129` 烹饪用词、`cne_j130` 顺序词 first、next、then、`cne_j131` 说明做法、`cne_j132` 读食谱 |
| 八年级上册 第6单元 Plan for Yourself | `cne_j118` 不定式作宾语、`cne_j121` 职业打算、`cne_j122` be going to 表示打算、`cne_j123` 谈论将来打算、`cne_j124` 读计划短文 |
| 八年级上册 第7单元 When Tomorrow Comes | `cne_j125` 未来生活、`cne_j126` will 表示将来、`cne_j127` 预测未来、`cne_j128` 读未来预测 |
| 八年级上册 第8单元 Let's Communicate! | `cne_j139` if 条件状语从句、`cne_j140` 用条件句给建议 |
| 八年级下册 第1单元 Time to Relax | `cne_j147` 不定式表示目的 |
| 八年级下册 第2单元 Stay Healthy | `cne_j142` 身体不适、`cne_j143` should 表示建议、`cne_j144` 关心身体、`cne_j145` 读健康建议 |
| 八年级下册 第3单元 Growing Up | `cne_j154` 情绪与压力、`cne_j155` although 引导让步、`cne_j165` so that 表示目的 |
| 八年级下册 第4单元 The Wonders of Nature | `cne_j168` 地理名称、`cne_j169` 比较级与最高级的选用、`cne_j170` 陈述地理事实、`cne_j171` 读地理短文 |
| 八年级下册 第5单元 Nature's Temper | `cne_j158` 暴风雨、`cne_j159` 过去进行时、`cne_j160` when 与 while、`cne_j161` 描述当时的动作、`cne_j162` 读暴风雨故事 |
| 八年级下册 第6单元 Crossing Cultures | `cne_j224` 社交习俗、`cne_j164` unless 表示除非、`cne_j226` 说明该怎么做、`cne_j227` 读习俗说明 |
| 八年级下册 第7单元 A Good Read | `cne_j173` 书籍与阅读、`cne_j174` 现在完成时、`cne_j175` already 与 yet、`cne_j176` 谈论读过的书、`cne_j177` 读阅读记录、`cne_j179` ever 与 never |
| 八年级下册 第8单元 Making a Difference | `cne_j146` 志愿服务、`cne_j148` 主动提供帮助、`cne_j149` 读志愿活动、`cne_j184` for 与 since |

原先挂错册次或课号、本轮只改生成器的点：`cne_j150`–`cne_j153` 家务四点从八年级下册改到上册第2单元；`cne_j129`–`cne_j132` 烹饪四点从第8单元改到第5单元；`cne_j118` 不定式作宾语从第5单元改到第6单元；`cne_j165` so that 从下册第6单元改到第3单元（官方 U3 写明 so that）。`cne_j224`、`cne_j226`、`cne_j227` 原来在九年级生成器里是 `(9, 全, 10)`，本轮只把这三点改成 `(8, 下, 6)`。九年级其余点不动。`cne_j072`、`cne_j164` 的 `chapter()` 与数据一致，不再用单独名单躲开旧课名。

## 改挂待核

目录无同名课不是删除。对不上官方课的点改为 unit 90，不删点、不改题目。

| id | 名称 | 改挂章节 | 依据 |
| --- | --- | --- | --- |
| `cne_j113` | 城镇设施 | 八年级上册 待核 | 旧版影院单元。官方 U4 是动植物，不是 theater/screen/seat |
| `cne_j115` | 谈论最好的地方 | 八年级上册 待核 | 同上 |
| `cne_j116` | 读影院介绍 | 八年级上册 待核 | 同上。形容词最高级仍留在 U4 |
| `cne_j133` | 聚会活动 | 八年级上册 待核 | 旧版聚会/邀请。官方 U8 是沟通与条件句 |
| `cne_j134` | 用 can 发出邀请 | 八年级上册 待核 | 描写是派对邀请，不只是「写邀请函」 |
| `cne_j135` | 接受或拒绝邀请 | 八年级上册 待核 | 同上 |
| `cne_j136` | 读邀请函 | 八年级上册 待核 | 同上 |
| `cne_j138` | 建议用词 | 八年级上册 待核 | 同上 |
| `cne_j141` | 读聚会建议 | 八年级上册 待核 | 同上。if 条件句和用条件句给建议仍留在 U8 |
| `cne_j117` | 电视节目 | 八年级上册 待核 | 旧版电视节目。数据曾误挂在八下 U1 Time to Relax，已改回八上待核，grade/semester 同步为八年级上册 |
| `cne_j119` | 谈论想看的节目 | 八年级上册 待核 | 同上 |
| `cne_j120` | 读节目选择 | 八年级上册 待核 | 同上。不定式表示目的仍留在八下 U1 |
| `cne_j156` | 用 Why don't you 提建议 | 八年级下册 待核 | 官方 U3 写作是感谢信，语法是连词 |
| `cne_j157` | 读建议信 | 八年级下册 待核 | 同上 |
| `cne_j172` | 选词补全短文 | 八年级下册 待核 | 目录无此课 |
| `cne_j225` | be supposed to | 八年级下册 待核 | 官方 U6 语法是连词，未写 be supposed to。数据已在八下，不改回九年级。生成器从 `(9, 全, 10)` 改为 `(8, 下, 90)` |
| `cne_j178` | 场馆经历 | 八年级下册 待核 | 旧版博物馆单元。官方 U7 是读书 |
| `cne_j180` | been 与 gone | 八年级下册 待核 | 同上 |
| `cne_j181` | 询问去过哪里 | 八年级下册 待核 | 同上 |
| `cne_j182` | 读场馆经历 | 八年级下册 待核 | 同上。already、yet、ever、never 与书籍类仍留在 U7 |
| `cne_j183` | 旧物与回忆 | 八年级下册 待核 | 旧版旧物/自行车单元。官方 U8 是志愿服务 |
| `cne_j185` | 谈论拥有多久 | 八年级下册 待核 | 同上 |
| `cne_j186` | 读旧物故事 | 八年级下册 待核 | 同上。志愿服务和 for/since 仍留在 U8 |

软边理由写的是知识点名称，不是旧版单元课名，本轮没有改 `dependencies.json`，也没有改硬边。

## 仍待核

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j010` | 词尾 s 的读音 | 仍「七年级上册 待核」。八上、八下目录和八下附录都没有词尾 -s/-es 读 /s/ /z/ /ɪz/ 的规则。八上 U8 的 pronunciation review 是词尾辅音丛，不是 -s/-es。八下 Unit 2 词尾、Unit 7 形容词后缀都是词汇。不据此改挂，不删除。 |
| `cne_j053`–`cne_j056` | 交通方式、How 问交通、谈论怎么上学、读上学方式 | 仍「七年级上册 待核」。八年级目录无同名课。不删除。本章未改它们的 chapter。 |
| `cne_j093`、`cne_j096`、`cne_j097` | 周末活动、谈论上周末、读周末日记 | 仍「七年级下册 待核」。八下 U1 是课余爱好（free time），不是 last weekend。八上 U1 是假期经历，也不是上周末。不删除。 |

## 官方语法和发音（未建点）

上表语法、发音只写入本文，没有新建 V/G/F/R 点。其中包括八上的不定代词、as … as、感叹句以外的可数与不可数名词复习、弱读、句子重音、名词后缀，以及八下的 until、so … that、as soon as、大数字、just、反身代词的目录位置（`cne_j251` 已在 Stay Healthy，未改）。八下没有发音栏，也没有把词尾 -s/-es 补成新点。

## 本轮未做

- 没有推送、没有部署。
- 没有改九年级 `UNITS` 标题，也没有改九年级其余点的册次。
- 没有改题目，`questions.json` 未写。没有升格课标原文标记，没有改 confidence、verbatim。
- 没有新增知识点。`sw.js` 仍是 `v14`。
- 截图保存在仓库未跟踪目录 `.english-g8-research/`，不纳入本提交。

## 正文续核（2026-11-11 晚）

在已按官方目录改挂之后，续核八上官方阅读器正文、Reading Plus 和语法附录。上面「仍待核」表是目录阶段结论。八上、八下 PDF.js 页码 = 印刷书页 + 9。没有下载教材。八下仍未见印刷书号，未填写、未猜测。

- 八年级上册 12 个待核点正文后仍全部挂「八年级上册 待核」，没有可改挂的独立课。第8单元写作是正式的校园演讲邀请信，不是聚会邀请，`cne_j136` 读邀请函不改挂。Can/Could 出现在第2单元家务或许可语境，不是本批聚会邀请点的依据。影院、电视节目在正文中也没有独立课。
- 八年级下册 11 个待核点已于同晚稍后用新路径打开官方阅读器正文（从目录逐页翻入第1单元，不使用页码跳转；此前两次跳到语法附录书页105后画布一直转圈）。正文后仍全部挂「八年级下册 待核」，没有可改挂的独立课，不删除。详见下一节。
- 七年级相关点的当前挂接已改到 `docs/english-g7-official-reader-20261111.md` 的正文续核节：`cne_j010` 现挂七下第1单元，`cne_j093`、`cne_j096` 现挂七下第7单元；`cne_j097` 与交通四点仍待核。本文件目录阶段的七年级行不再作为当前挂接。同晚复核七上交通四点与七下「读周末日记」既有正文截图，结论不变，仍待核。

本轮未改八上、八下这些点的生成器挂接，未改题目，未升 `sw.js`。未推送、未部署。八下正文截图在未跟踪目录 `.english-g8-research/g8b-body-20261111/`。

## 八下正文续核（2026-11-11 晚，第二次打开阅读器）

官方在页阅读器已渲染第1单元书页1。会话为用户***6 老师。未用全屏授课，未下载教材。

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j156` | 用 Why don't you 提建议 | 仍「八年级下册 待核」。第3单元书页24 对话有 “Why don’t you talk to them?”，是与父母沟通的范文，不是以 Why don’t you 提建议为课业。第3单元语法栏是 although / until / so that。第2单元建议用语是 should / could，未见 Why don’t you。Reading Plus 第1单元书页81 有偶发 “Why not choose an outdoor hobby instead?”，不足改挂。 |
| `cne_j157` | 读建议信 | 仍「八年级下册 待核」。第3单元书页29 写作明确是 thank-you letter。第6单元书页59 读的是 Tina 向 Yaming 求助的邮件（Home visit—Help needed!），写作要求 “Write an email to Tina to give some advice”，不是读建议信。 |
| `cne_j172` | 选词补全短文 | 仍「八年级下册 待核」。未见名为 Cloze 或「选词补全」的课，只有普通 “Complete the passage with the words in the box”。 |
| `cne_j225` | be supposed to | 仍「八年级下册 待核」。第6单元语法栏（书页55）是 so … that、unless、as soon as，语法附录未见 be supposed to。不因跨文化主题改挂。 |
| `cne_j178` | 场馆经历 | 仍「八年级下册 待核」。第7单元是读书。第8单元博物馆出现在志愿讲解语境，不是参观场馆课。 |
| `cne_j180` | been 与 gone | 仍「八年级下册 待核」。语法附录书页108 明确写 have (has) been 表示「曾经到过某地」、have (has) gone 表示「已经去某地了」，并有西安例句。第7单元语法栏只讲 already / yet / ever / never / just，第8单元语法栏只讲 for / since，单元正文未见这一组对比。因没有对应的单元课业，不改挂到第7或第8单元。不删除。 |
| `cne_j181` | 询问去过哪里 | 仍「八年级下册 待核」。第8单元有 “Have you been to our animal shelter before?”，是是否去过的一般疑问，志愿语境。语法附录有 “Where has Tom gone?”，未见 “Where have you been?” 作为课业。 |
| `cne_j182` | 读场馆经历 | 仍「八年级下册 待核」。第7单元阅读是 The Secret Garden，写作是读书报告。Reading Plus 第8单元是 Unusual Volunteers，不是场馆参观阅读。 |
| `cne_j183` | 旧物与回忆 | 仍「八年级下册 待核」。第8单元是志愿服务。第3单元丢失的吉他、第7单元花园的 painful memory 都不是旧物主题课。 |
| `cne_j185` | 谈论拥有多久 | 仍「八年级下册 待核」。第8单元书页75 采访练习有 “How long have you had your favourite toy / ...?”，是 for / since 的拥有例句，不是旧物课业。for / since 语法已留在第8单元。 |
| `cne_j186` | 读旧物故事 | 仍「八年级下册 待核」。未见以旧物故事为课业的课文。 |

## 待核分类（2026-11-12）

八上 12 点与八下 11 点的两类标记见 [english-pending-classification-20261112.md](english-pending-classification-20261112.md)。八下逐点表仍是正文依据。章节仍是「待核」。`cne_j180` 不改挂到第7或第8单元。

2026-11-12 续核八上 `cne_j113`、`cne_j115`、`cne_j116`、`cne_j117`、`cne_j119`、`cne_j120`、`cne_j133`、`cne_j135`、`cne_j138`、`cne_j141`：已核教材正文但仍未见对应课业，章节仍是「八年级上册 待核」，近义句和偶发句不改挂。详见 [english-pending-classification-20261112.md](english-pending-classification-20261112.md)。
