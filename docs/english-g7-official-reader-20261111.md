# 七上、七下英语官方阅读器核对（2026-11-11）

在国家中小学智慧教育平台打开人教版2022课标修订电子教材，核目录、版权页和七上发音正文。没有下载教材 PDF，也没有改课标 `verbatim` 或 `standards.confidence`。稳定 id 不变。题目保持原技能，本轮未改写。

## 书号与目录

| 册次 | 书名 | ISBN | 平台 contentId |
| --- | --- | --- | --- |
| 七年级上册 | 义务教育教科书•英语 | 978-7-107-38254-3 | 33f98190-ed21-f303-9657-d29d792f27a9 |
| 七年级下册 | 义务教育教科书•英语 | 978-7-107-38255-0 | 5f12c902-f141-4ae2-9dcb-e2c504a7783b |

两册封面均为根据2022年版课程标准修订，人民教育出版社、课程教材研究所编著，主编刘道义、郑旺全，分册主编张献臣。版权页未见版次、印次或审核信息。

七上官方目录（书页）与 2026-11-06 资源页标题一致：Starter Hello! 1、Keep Tidy! 7、Welcome! 13；Unit 1 You and Me 19；Unit 2 We're Family! 27（Word stress (1)）；Unit 3 My School 35（Word stress (2)）；Unit 4 My Favourite Subject 43（Linking）；Unit 5 Fun Clubs 51（Incomplete plosion）；Unit 6 A Day in the Life 59（Sentence stress）；Unit 7 Happy Birthday! 67（Intonation）；附录 Pronunciation 92、Grammar 95。

七下官方目录（书页，2026-11-11 官方阅读器）：

| 单元 | 书页 | Section A | Section B | 发音 | 语法 |
| --- | --- | --- | --- | --- | --- |
| Unit 1 Animal Friends | 1 | Why do you like animals? Listening/Speaking 动物 | How are animals part of our lives? Reading 最喜欢的动物（大象）；Writing；Project: Design a zoo | Unstressed words | Wh- questions; Adjectives; Plurals |
| Unit 2 No Rules, No Order | 9 | What rules do we follow? 校规 | How can rules help us? | Sentence stress (1) | Imperatives; Modal verbs (can, have to, must) |
| Unit 3 Keep Fit | 17 | How often do you do sport or exercise? | How is exercise good for us? | Stress patterns | Possessive pronouns; Adverbs of frequency |
| Unit 4 Eat Well | 25 | What do we like to eat? Order food | How do we make healthy eating choices? | Intonation in alternative questions | Alternative questions; Countable and uncountable nouns |
| Unit 5 Here and Now | 33 | What are you doing right now? | | Sentence stress (2) | Present continuous tense (1) |
| Unit 6 Rain or Shine | 41 | What's the weather like? | | Rhythm | Present continuous tense (2) |
| Unit 7 A Day to Remember | 49 | What was your special day like? Speaking: Talk about a school trip | Reading/Writing: school trip diary / farm | Contractions in negative forms | Simple past tense (1) |
| Unit 8 Once upon a Time | 57 | What are your favourite stories? Speaking: Retell a story | Reading: The Ugly Duckling；Writing: ending for a story | Assimilation | Simple past tense (2) |

附录：Reading Plus 65，Listening Scripts 74，Pronunciation 83–87，Grammar 88，词表等。先前有一处把语法误记为书页86，已按阅读器目录和页脚更正为88。第7单元是校园旅行 / special day，不是怎么上学；第8单元是讲故事，不是上周末。生成器 `UNITS` 和七下课号已按此目录改写。

## 已改挂

| id | 名称 | 改挂章节 | 依据 |
| --- | --- | --- | --- |
| `cne_j001` | 单词重音 | 七年级上册 第2单元 We're Family! | Unit 2 书页29、Unit 3 书页37 均为 Word stress 练习；附录书页93 讲单词重音 |
| `cne_j098` | 辅音与元音连读 | 七年级上册 第4单元 My Favourite Subject | Unit 4 书页45 Linking；附录书页93 明确写辅音加元音、以及 r/re 加元音连读 |
| `cne_j107` | 不完全爆破 | 七年级上册 第5单元 Fun Clubs | Unit 5 书页53 用括号做发音练习，正文未点出规则名；附录书页94 明确讲解不完全爆破 |
| `cne_j002` | 句末升降调 | 七年级上册 第7单元 Happy Birthday! | Unit 7 书页69 有升调、降调记号练习；附录书页94 写明语调主要表现在语句末尾的降与升 |

官方课序是连读（第4单元）早于句末升降调（第7单元）。已删除与之相反的硬先修 `cne_j098`←`cne_j002`。不完全爆破对连读的硬先修与官方课序一致，保留。

## 七下课序（本轮）

生成器 `scripts/enj_build.py` 的七下 `UNITS` 已改成官方 1–8，并加 `(7, 下, 90)` 待核。`chapter()` 对七下 90 返回「七年级下册 待核」。八上及以后仍是旧版 Go for it! 课名，本轮不改。

| id | 名称 | 本轮处理 |
| --- | --- | --- |
| `cne_j093`、`cne_j096`、`cne_j097` | 周末活动、谈论上周末、读周末日记 | 改挂「七年级下册 待核」。官方第8单元是讲故事（Retell a story / The Ugly Duckling / Simple past tense (2)），目录无「上周末」同名课，不按旧版 What did you do last weekend 挂在第8单元。 |
| `cne_j094`、`cne_j095` | Did 提问、不规则动词过去式 | 仍挂「七年级下册 第8单元 Once upon a Time」（Grammar: Simple past tense (2)）。 |
| `cne_j163`、`cne_j166`、`cne_j167` | 故事用词、复述故事、读神话故事 | 仍挂第8单元。故事阅读题仍用旧课文例子（愚公移山用词），题目未改。 |
| `cne_j072` | 感叹句 | 数据已是「八年级上册 第5单元 What a Delicious Meal!」。只改生成器为 `(8, 上, 5)`，不用 `chapter()` 覆盖（八上 `UNITS` 仍是旧课名）。 |
| `cne_j164` | unless | 数据已是「八年级下册 第6单元 Crossing Cultures」。故事三点改挂七下第8单元，`gr_unless` 保持 `(8, 下, 6)`，不用 `chapter()` 覆盖。 |

原先已挂官方七下课名的点（动物、校规、Keep Fit、Eat Well、Here and Now、Rain or Shine、A Day to Remember 等）chapter 不变。

## 仍待核

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j010` | 词尾 s 的读音 | 七上 Unit 6 书页61 与附录书页92–94 只有 /s/、/z/ 等音素和句子重音。七下附录发音页（书页83–87；语法从书页88起）第85页是字母 s 读 /s/、/z/，第86页是 ds /dz/、ts /ts/ 辅音组合，都不是词尾 -s/-es 规则，也未见 /ɪz/。Unit 1 有 “Notice the pronunciation of – (e) s.” 的练习提示和复数例词，不是规则说明，不据此改挂第1单元。七下官方目录无同名课。仍挂「七年级上册 待核」，不删除。 |
| `cne_j053`–`cne_j056` | 交通方式、How 问交通、谈论怎么上学、读上学方式 | 七上、七下 2022 课标修订官方目录均无同名课。七下第7单元是校园旅行，不是怎么上学。不按旧版七下 How do you get to school 改挂，不删除。本章未改它们的 chapter。 |
| `cne_j093`、`cne_j096`、`cne_j097` | 周末活动、谈论上周末、读周末日记 | 官方七下目录无「上周末」同名课。挂「七年级下册 待核」，不删除。 |

截图保存在仓库未跟踪目录 `.english-g7-research/`，不纳入本提交。


## 七下附录发音页（2026-11-11 续核）

官方阅读器目录为 Pronunciation 书页83、Grammar 书页88。书页86、87 仍是发音页（页脚写 Pronunciation）。对应阅读器 PDF 页大约是 92–96，语法从 PDF 97 / 书页88 起。没有下载教材。

- 书页83–84：字母及字母组合在重读、非重读音节中的读音归类。
- 书页85：辅音字母读音归类。s 作 /s/（salt, skate, artist）和 /z/（noise, always, yours），是字母读音，不是词尾后缀规则。
- 书页86：辅音字母组合读音归类，含 ds /dz/（beds, cards, sounds）、ts /ts/（bats, hats, habits）；随后「朗读基本知识」从弱读（Unstressed Words）开始。
- 书页87：弱读续、音的同化（Assimilation）、节奏（Rhythm）。

全书页83–87 未见复数、第三人称或其它词尾 -s/-es 读 /s/、/z/、/ɪz/ 的规则。

## 本轮未做

- 没有推送、没有部署。
- 没有重写八年级及以后的 `UNITS` 标题。
- 没有改题目，也没有升格课标原文标记。
- 没有新增语音/语法知识点。官方发音行 Unstressed words、Stress patterns、Rhythm、Assimilation、Contractions in negative forms、Sentence stress (1)(2)、Intonation in alternative questions 先记下，本轮不建点。
- 已核七下附录发音页（书页83–87），词尾 s 仍待核：附录没有 -s/-es 规则，也不把 Unit 1 的练习提示改挂为正式课。

## 正文续核（2026-11-11 晚）

在已按官方目录改挂之后，续核七上、七下官方阅读器的课文正文、Reading Plus 和语法附录。本轮 PDF.js 页码 = 印刷书页 + 9。没有下载教材。上面「仍待核」表是目录阶段结论，以下为正文续核后的当前挂接。

### 已按正文改挂

| id | 名称 | 当前挂接 | 依据 |
| --- | --- | --- | --- |
| `cne_j010` | 词尾 s 的读音 | 七年级下册 第1单元 Animal Friends（semester 由上改为下） | 七下语法附录书页88「名词复数」给出名词复数词尾 -s/-es 读 /s/、/z/、/ɪz/ 的规则及读音表。本册第1单元官方语法含 Plurals，Unit 1 另有 “Notice the pronunciation of – (e) s.” 的练习提示。七上语法附录书页95–105 没有这条复数词尾规则：书页95只写可数名词有复数形式，书页96「名词所有格」和书页103第三人称单数动词虽有同类读音，但都不是名词复数词尾规则，不据此改挂七上。七上发音页（书页92–94）和七下发音页（书页83–87）仍没有这条规则。点名和题目未改。`gr_plural7` 名词复数仍挂七上预备单元3 Welcome!，硬先修未改。 |
| `cne_j093`、`cne_j096` | 周末活动、谈论上周末 | 七年级下册 第7单元 A Day to Remember | 第7单元 Section A 书页50 有 “Did you do any of these activities last weekend?” 以及 “How was Peter’s weekend?” / “How was Teng Fei’s weekend?” 的上周末活动听说练习。第8单元仍是讲故事，不按旧版挂第8单元。点名和题目未改。 |

### 正文后仍待核

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j097` | 读周末日记 | 仍「七年级下册 待核」。第7单元 Section B 书页54 日记日期是 Friday 30 May，内容是学校农场秋游，不是周末日记。Reading Plus 第7单元是日食日记，也不是周末日记。不删除。 |
| `cne_j053`–`cne_j056` | 交通方式、How 问交通、谈论怎么上学、读上学方式 | 仍「七年级上册 待核」。七下正文未见独立的交通方式或怎么上学课。七上 Reading Plus Unit 3 书页77「My Floating School」是孟加拉浮动学校的补充阅读，虽有 “So how do I go to school?” 以及船既是校车又是教室，但不是交通方式词汇课，也不是谈论自己怎么上学的口语课，讨论题问的是浮动学校的重要性和可能困难；不足以改挂第3单元。七上第6单元书页64 “I walk to school. It’s only a 10-minute walk” 是作息短文里的偶发句。语法附录中的 at the bus stop、on the way to 只是介词例句。不按旧版 How do you get to school 改挂，不删除。 |

本轮未改题目、课标 `verbatim` 和 `standards.confidence`，未升 `sw.js`（仍为 v16）。硬先修未改。因词尾 s 改到七下，软先修「介绍家人」不再依赖「词尾 s 的读音」，改为依赖七上「名词复数」；并增加「动物」对「词尾 s 的读音」的软先修。未推送、未部署。截图仍在未跟踪目录 `.english-g7-research/`。
