# 七上、七下英语官方阅读器核对（2026-11-11）

在国家中小学智慧教育平台打开人教版2022课标修订电子教材，核目录、版权页和七上发音正文。没有下载教材 PDF，也没有改课标 `verbatim` 或 `standards.confidence`。稳定 id 不变。题目保持原技能，本轮未改写。

## 书号与目录

| 册次 | 书名 | ISBN | 平台 contentId |
| --- | --- | --- | --- |
| 七年级上册 | 义务教育教科书•英语 | 978-7-107-38254-3 | 33f98190-ed21-f303-9657-d29d792f27a9 |
| 七年级下册 | 义务教育教科书•英语 | 978-7-107-38255-0 | 5f12c902-f141-4ae2-9dcb-e2c504a7783b |

两册封面均为根据2022年版课程标准修订，人民教育出版社、课程教材研究所编著，主编刘道义、郑旺全，分册主编张献臣。版权页未见版次、印次或审核信息。

七上官方目录（书页）与 2026-11-06 资源页标题一致：Starter Hello! 1、Keep Tidy! 7、Welcome! 13；Unit 1 You and Me 19；Unit 2 We're Family! 27（Word stress (1)）；Unit 3 My School 35（Word stress (2)）；Unit 4 My Favourite Subject 43（Linking）；Unit 5 Fun Clubs 51（Incomplete plosion）；Unit 6 A Day in the Life 59（Sentence stress）；Unit 7 Happy Birthday! 67（Intonation）；附录 Pronunciation 92、Grammar 95。

七下官方目录（书页）：Unit 1 Animal Friends 1（Unstressed words）；Unit 2 No Rules, No Order 9（Sentence stress (1)）；Unit 3 Keep Fit 17（Stress patterns）；Unit 4 Eat Well 25（Intonation in alternative questions）；Unit 5 Here and Now 33（Sentence stress (2)）；Unit 6 Rain or Shine 41（Rhythm）；Unit 7 A Day to Remember 49（校园旅行，不是怎么上学）；Unit 8 Once upon a Time 57（Assimilation）；附录 Pronunciation 83。生成器里七下 UNITS 除已占位的 Eat Well 外，仍是旧版 Go for it! 标题，本轮不改写。

## 已改挂

| id | 名称 | 改挂章节 | 依据 |
| --- | --- | --- | --- |
| `cne_j001` | 单词重音 | 七年级上册 第2单元 We're Family! | Unit 2 书页29、Unit 3 书页37 均为 Word stress 练习；附录书页93 讲单词重音 |
| `cne_j098` | 辅音与元音连读 | 七年级上册 第4单元 My Favourite Subject | Unit 4 书页45 Linking；附录书页93 明确写辅音加元音、以及 r/re 加元音连读 |
| `cne_j107` | 不完全爆破 | 七年级上册 第5单元 Fun Clubs | Unit 5 书页53 用括号做发音练习，正文未点出规则名；附录书页94 明确讲解不完全爆破 |
| `cne_j002` | 句末升降调 | 七年级上册 第7单元 Happy Birthday! | Unit 7 书页69 有升调、降调记号练习；附录书页94 写明语调主要表现在语句末尾的降与升 |

官方课序是连读（第4单元）早于句末升降调（第7单元）。已删除与之相反的硬先修 `cne_j098`←`cne_j002`。不完全爆破对连读的硬先修与官方课序一致，保留。

## 仍待核

| id | 名称 | 结论 |
| --- | --- | --- |
| `cne_j010` | 词尾 s 的读音 | Unit 6 书页61 与附录发音页（书页92–94）只有 /s/、/z/ 等音素和句子重音，没有词尾 -s/-es 读 /s/、/z/ 或 /ɪz/ 的规则。七下官方目录无同名课，七下附录发音页尚未读。仍挂「七年级上册 待核」，不改挂到第6单元，不删除。 |
| `cne_j053`–`cne_j056` | 交通方式、How 问交通、谈论怎么上学、读上学方式 | 七上、七下 2022 课标修订官方目录均无同名课。七下第7单元是校园旅行，不是怎么上学。不按旧版七下 How do you get to school 改挂，不删除。 |

截图保存在仓库未跟踪目录 `.english-g7-research/`，不纳入本提交。

## 本轮未做

- 没有推送、没有部署。
- 没有重写七下及以后的单元目录。
- 没有改题目，也没有升格课标原文标记。
