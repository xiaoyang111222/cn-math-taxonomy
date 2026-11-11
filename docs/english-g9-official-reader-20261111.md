# 九上英语官方阅读器核对（2026-11-11）

在国家中小学智慧教育平台打开人教版2022课标修订电子教材，核目录和版权页。观察日期 2026-11-11。平台筛选初中 / 英语 / 人教版 / 九年级，只出现一张人民教育出版社卡片，没有九下，也没有旧版卡片。没有下载教材 PDF，也没有改课标 `verbatim` 或 `standards.confidence`。稳定 id 不变。题目保持原技能，本轮未改写，也没有新增知识点。阅读器第 10 页始终没有渲染出正文，只核了目录（PDF 第 5–8 页）和版权页，没有发明课文内容。

## 书号与目录

| 册次 | 书名 | ISBN | 平台 contentId |
| --- | --- | --- | --- |
| 九年级上册 | （根据2022年版课程标准修订）义务教育教科书•英语 九年级上册 | 阅读器未见印刷书号，未填写 | 7055a895-2dbd-8b3d-4988-6c357fe5dae1 |

详情页：https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=7055a895-2dbd-8b3d-4988-6c357fe5dae1&catalogType=tchMaterial&subCatalog=tchMaterial

人民教育出版社、课程教材研究所编著。主编刘道义、郑旺全，分册主编张献臣。版次、印次、审核信息未见。印刷书号：阅读器未见印刷书号，未填写。PDF 第 142 页是橙色封面风格的末页，不是条码封底；400% 放大底部和右缘，以及版权页 PDF 第 3 页底部，均未见 ISBN、CIP 或条码。没有从非官方网站填书号。

官方目录只有九上 8 单元，没有九下，也没有发音栏。`UNITS` 标题与目录截图逐字一致。

| 单元 | 书页 | 主题 | 语法（只记录，未建点） | 词汇（只记录，未建点） |
| --- | --- | --- | --- | --- |
| Unit 1 The Changing World | 1 | changes | Compare simple past tense and present perfect tense | Compound words; Words related to changes |
| Unit 2 Inspiring People | 11 | admire / inspiring people | It is / was ... (of / for sb) to do ...; It is / was ... that ... | Suffixes (-ist, -er, -ian); Words related to professions |
| Unit 3 Smart Learning | 21 | how we learn | Object clauses with that, if, and whether | Collocations related to learning |
| Unit 4 Our Memory | 31 | memory（记忆力、记忆方法，不是毕业回忆） | Object clauses with question words | Words related to memory |
| Unit 5 Power of Ideas | 41 | inventions | Passive voice in the simple present and past tenses | Words related to inventions |
| Unit 6 Beyond Earth | 51 | space exploration | Passive voice in the simple future tense | Compound words; Words related to space exploration |
| Unit 7 Feel the Rhythm | 61 | music | Relative clauses with that, which, and who | Words related to music |
| Unit 8 More than a Game | 71 | sports events / Olympics | Subject-verb agreement | Words related to sports events |

目录里和改挂有关的课文行：U1 Section A「What changes have taken place around you?」，口语 Talk about big changes in the last 10 years；Section B「What changes influence us?」，阅读 A report on changes brought by a railway，写作 Write about changes in your life since primary school；*Project: Compare then and now。U5 阅读 An informative text about the invention of paper。

附录：*Reading Plus 81，Listening Scripts 94，Grammar 104，Vocabulary in Each Unit 107，Vocabulary A-Z 117，Vocabulary from Primary School 126，Irregular Verbs 127。本目录没有 Pronunciation 附录，也没有发音栏。

生成器 `scripts/enj_build.py` 的九年级 `UNITS` 已改为上面 8 个九上标题，并加 `(9, 上, 90)` 待核。没有九下，也没有 `(9, 全, …)`。`chapter()` 对 `(9, 上, 90)` 返回「九年级上册 待核」；1–8 仍走「九年级上册 第N单元 标题」。九年级学期校验改为必须是「上」，`(9, 全, …)` 不能通过。

## 数据原先的过渡状态

`data/topics.json` 里一部分九年级点的 chapter 已经是官方九上标题，semester 已是上。另有 29 个点仍是「九年级全册 第N单元 …」，semester 为全。这是早先「九上已出、九下未出」的过渡。本轮不按旧课号 1–14 去套新标题。按官方目录核过之后，对不上的点改挂「九年级上册 待核」；那 29 个旧全册点的 semester 从全改为上，章节改为「九年级上册 待核」。不发明九下，也不写「九年级下册 待核」。

保留点的 name、description、chapter 与生成器算出的官方标题已经一致，同步没有改这些字段。待核点只改了 chapter，原先 semester 为全的同时改为上。

## 保留在官方单元

生成器的 grade、semester、unit 已改成官方课号，使 `chapter()` 与下表章节一致。这些点在数据里的 chapter 原本已经是官方标题。

| 章节 | id |
| --- | --- |
| 九年级上册 第1单元 The Changing World | `cne_j200` 今昔变化、`cne_j202` 比较过去和现在、`cne_j203` 读变化短文 |
| 九年级上册 第3单元 Smart Learning | `cne_j187` 学习方法、`cne_j189` 交流学习方法、`cne_j190` 读学习建议、`cne_j192` that 引导宾语从句、`cne_j193` if 与 whether 宾语从句 |
| 九年级上册 第4单元 Our Memory | `cne_j197` 疑问词宾语从句 |
| 九年级上册 第5单元 Power of Ideas | `cne_j205` 一般现在时被动语态、`cne_j208` 发明物、`cne_j209` 一般过去时被动语态、`cne_j210` 询问发明时间、`cne_j211` 读发明介绍 |
| 九年级上册 第7单元 Feel the Rhythm | `cne_j220` 音乐类型、`cne_j221` 定语从句、`cne_j222` 说明喜欢的音乐、`cne_j223` 读音乐偏好 |

U1 的比较过去和现在、读变化短文留在本单元：官方 *Project 是 Compare then and now，写作和口语也是 changes，阅读是变化报告。U3 的 that、if、whether 宾语从句对应官方语法 Object clauses with that, if, and whether。U4 只留疑问词宾语从句，对应 Object clauses with question words；问路主题点改挂待核。U5 的一般现在时与一般过去时被动、发明物、询问发明时间、读发明介绍对应官方 inventions 和造纸发明阅读。U7 的定语从句对应 Relative clauses with that, which, and who。

不在 TOPICS、已挂官方课、本轮未改：

| id | 名称 | 章节 |
| --- | --- | --- |
| `cne_j252` | 一般过去时与现在完成时 | 九年级上册 第1单元 The Changing World |
| `cne_j253` | It is ... (for sb) to do | 九年级上册 第2单元 Inspiring People |
| `cne_j254` | 一般将来时的被动语态 | 九年级上册 第6单元 Beyond Earth |
| `cne_j255` | 太空探索词汇 | 九年级上册 第6单元 Beyond Earth |
| `cne_j256` | 主谓一致 | 九年级上册 第8单元 More than a Game |
| `cne_j257` | 体育赛事词汇 | 九年级上册 第8单元 More than a Game |

U2、U6、U8 在 TOPICS 里没有应保留的旧点，只有上面这些 246 以后的点。

改完后九年级英语各章点数（含不在 TOPICS 的 `cne_j252`–`cne_j257`）：第1单元 4，第2单元 1，第3单元 5，第4单元 1，第5单元 5，第6单元 2，第7单元 4，第8单元 2，待核 37。合计 61，全部 semester 为上。

## 改挂待核

目录无同名课不是删除。对不上官方课的点改为 unit 90，章节「九年级上册 待核」，不删点、不改题目。原先 semester 为全的点改为上。

| id | 名称 | 依据 |
| --- | --- | --- |
| `cne_j201` | used to 表示过去习惯 | 数据曾挂在 U1 The Changing World。官方 U1 语法是比较一般过去时与现在完成时，不是 used to |
| `cne_j188` | by 加动名词 | 数据曾挂在 U3 Smart Learning。官方 U3 语法是宾语从句，不是 by doing |
| `cne_j196` | 公共场所 | 旧版问路、公共场所。官方 U4 是 memory（记忆力），不是 restroom |
| `cne_j198` | 礼貌问路 | 同上。疑问词宾语从句仍留在 U4 |
| `cne_j199` | 读问路对话 | 同上 |
| `cne_j204` | 材料 | 旧版「由什么制成」。官方 U5 是 inventions |
| `cne_j206` | 询问由什么制成 | 同上。一般现在时被动和发明类点仍留在 U5 |
| `cne_j207` | 读产品介绍 | 同上 |
| `cne_j191` | 节日食物 | 旧版节日单元，官方目录无此课。原先是九年级全册第2单元 |
| `cne_j194` | 谈论节日 | 同上 |
| `cne_j195` | 读中秋短文 | 同上 |
| `cne_j212` | 青少年规则 | 旧版 be allowed to、青少年规则，官方目录无此课 |
| `cne_j213` | be allowed to | 同上 |
| `cne_j214` | 讨论是否允许 | 同上 |
| `cne_j215` | 读规则意见 | 同上 |
| `cne_j216` | 物品主人 | 旧版物品归属、推测。目录没有 belongings / things around the house |
| `cne_j217` | must 表示推测 | 同上 |
| `cne_j218` | 推测物品归属 | 同上 |
| `cne_j219` | 读推测短文 | 同上 |
| `cne_j228` | 情绪反应 | 旧版电影、make sb do，官方目录无此课 |
| `cne_j229` | make 加宾语加动词原形 | 同上 |
| `cne_j230` | 表达电影感受 | 同上 |
| `cne_j231` | 读观后感 | 同上 |
| `cne_j232` | 意外事件 | 旧版意外、过去完成时，官方目录无此课 |
| `cne_j233` | 过去完成时 | 同上 |
| `cne_j234` | 叙述意外经过 | 同上 |
| `cne_j235` | 读意外故事 | 同上 |
| `cne_j236` | 环境保护 | 旧版环保，官方目录无此课 |
| `cne_j237` | 时态选择 | 同上 |
| `cne_j238` | 谈论环保做法 | 同上 |
| `cne_j239` | 读环保倡议 | 同上 |
| `cne_j240` | 完形填空 | 目录没有完形填空 |
| `cne_j241` | 毕业回忆 | 旧版第14单元毕业回忆。Our Memory 是记忆力主题，不是「I remember meeting all of you in Grade 7」 |
| `cne_j242` | 动名词与不定式 | 官方目录没有这一语法栏 |
| `cne_j243` | 反意疑问句 | 官方目录没有这一语法栏 |
| `cne_j244` | 回忆学校生活 | 同上，不是 U4 的记忆方法 |
| `cne_j245` | 书面表达要点 | 官方目录没有单独的书面表达要点课 |

其中 `cne_j191`、`cne_j194`、`cne_j195`、`cne_j212`–`cne_j219`、`cne_j228`–`cne_j245` 这 29 个点原先是「九年级全册」，本轮改为九上待核。另外 8 个（`cne_j188`、`cne_j196`、`cne_j198`、`cne_j199`、`cne_j201`、`cne_j204`、`cne_j206`、`cne_j207`）数据里已经是九上，但挂在对不上的官方单元上，本轮只改章节为待核。

软边和硬边理由里没有旧版九年级课名，本轮没有改 `dependencies.json`。

## 仍留在原处

这些主题官方九年级目录没有。现有七年级、八年级待核点和已改挂的八年级点一律不改到九年级。

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j010` | 词尾 s 的读音 | 仍「七年级上册 待核」。九上没有词尾 -s/-es 读 /s/ /z/ /ɪz/。U2 的后缀 -ist、-er、-ian 是词汇，不是这个发音点。不据此改挂，不删除 |
| `cne_j053`–`cne_j056` | 交通方式、How 问交通、谈论怎么上学、读上学方式 | 仍「七年级上册 待核」。九年级目录没有交通课 |
| `cne_j093`、`cne_j096`、`cne_j097` | 周末活动、谈论上周末、读周末日记 | 仍「七年级下册 待核」 |
| `cne_j113`、`cne_j115`、`cne_j116` | 城镇设施、谈论最好的地方、读影院介绍 | 仍「八年级上册 待核」。目录没有 theater / the best place |
| `cne_j133`–`cne_j136`、`cne_j138`、`cne_j141` | 聚会、邀请、建议用词、读聚会建议 | 仍「八年级上册 待核」。目录没有 party / invitation / Can you come |
| `cne_j117`、`cne_j119`、`cne_j120` | 电视节目、谈论想看的节目、读节目选择 | 仍「八年级上册 待核」。目录没有 TV shows |
| `cne_j156`、`cne_j157` | 用 Why don't you 提建议、读建议信 | 仍「八年级下册 待核」 |
| `cne_j172` | 选词补全短文 | 仍「八年级下册 待核」 |
| `cne_j225` | be supposed to | 仍「八年级下册 待核」。目录没有 be supposed to。生成器里这四条八年级课号本轮不改 |
| `cne_j178`、`cne_j180`–`cne_j182` | 场馆经历、been 与 gone、询问去过哪里、读场馆经历 | 仍「八年级下册 待核」。目录没有 museum / been vs gone |
| `cne_j183`、`cne_j185`、`cne_j186` | 旧物与回忆、谈论拥有多久、读旧物故事 | 仍「八年级下册 待核」。目录没有 belongings / things around the house 这一旧版课 |
| `cne_j224`、`cne_j226`、`cne_j227` | 社交习俗、说明该怎么做、读习俗说明 | 仍「八年级下册 第6单元 Crossing Cultures」 |

上面八年级待核一共 23 个点，加上 `cne_j224`、`cne_j226`、`cne_j227`，都没有改挂到九年级。七上、七下、八上、八下的 `UNITS` 本轮不重开。

## 官方语法和词汇（未建点）

上表语法、词汇只写入本文，没有新建 V/G/F/R 点。已经存在、且不在 TOPICS 里的 `cne_j252`–`cne_j257` 覆盖了 U1 的一般过去时与现在完成时、U2 的 It is ... (for sb) to do、U6 的一般将来时被动和太空探索词汇、U8 的主谓一致和体育赛事词汇，本轮未改。U2 的 It is / was ... that ...、of sb 这一变体，以及后缀 -ist、-er、-ian，都没有另建点。没有把词尾 -s/-es 补成新点。

## 本轮未做

- 没有推送、没有部署。
- 没有发明 ISBN，没有发明九下，也没有写「九年级下册 待核」。
- 没有改题目，`questions.json` 未写。没有升格课标原文标记，没有改 confidence、verbatim。`verbatim` 没有设为 true。
- 没有新增知识点，没有删点。`sw.js` 仍是 `v14`。
- 没有改七年级、八年级生成器，没有改 README、诊断页的「九全」选项、`validate.py`。`tests/test_engine.js` 里原先要求英语「九全」仍有知识点；数据改为全部九上之后，该断言改为检查「九上」，并确认英语「九全」现在没有点。诊断页的九全选项本身没改。物理九全测试未动。
- 截图和笔记在仓库未跟踪目录 `.english-g9-research/`，不纳入本提交。

## 正文续核（2026-11-11 晚）

在已按官方目录改挂之后，续核九上官方阅读器正文、Reading Plus 和语法附录。平台目录只有九上，不设九下。本轮 PDF.js 页码 = 印刷书页 + 9。阅读器未见印刷书号，仍不填写 ISBN。没有下载教材。

- 九年级上册 37 个待核点正文后仍全部挂「九年级上册 待核」，没有可改挂的独立课。used to、by doing 只作为功能或时态练习出现，不是语法条目标题。语法附录只有动词的语态、宾语从句、关系从句。第4单元 Our Memory 是记忆方法，不是毕业主题。
- 七年级相关点的当前挂接见 `docs/english-g7-official-reader-20261111.md` 正文续核节。本文件目录阶段的七年级行不再作为当前挂接。

本轮未改九上这些点的生成器挂接，未改题目，未升 `sw.js`。未推送、未部署。截图和笔记在未跟踪目录 `.english-g9-research/`。
