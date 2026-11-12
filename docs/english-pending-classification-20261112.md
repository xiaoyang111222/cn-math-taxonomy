# 初中英语待核点分类（2026-11-12）

65 个仍挂「N年级X册 待核」的初中英语知识点，按核对记录分成两类。
不删点，不改稳定 id、点名、题目、先修、学期、unit 90 和章节字符串，也不改挂到已确认单元。
2026-11-12 续核把八上 10 个点从证据不足改为已核未见对应课业；近义句和偶发句不改挂。
没有把「未命中」写成「教材不存在」或「书里没教」。

## 字段

沿用知识点上的 `catalog_status`。道法已确认点是 `official_toc`，道法待核桶是 `pending_official_lesson_list`。
这 65 点用另外两个值，都不是已确认挂载：

| 值 | 含义 |
| --- | --- |
| `body_checked_no_lesson` | 已核教材但未找到对应课业 |
| `evidence_insufficient` | 证据仍不足 |

`catalog_note` 是一句可追溯的理由。证据路径写在下面各表，不进前台。
explore 仍按 `chapter` 字符串分组；diagnose 的 `parseChapter` 仍把「N年级X册 待核」解析为未挂到具体单元。
本批不改界面。前台仍只显示「待核」，不显示这两类的新分组。

## 计数

| 册 | 已核教材但未找到对应课业 | 证据仍不足 | 合计 |
| --- | ---: | ---: | ---: |
| 七年级上册 | 4 | 0 | 4 |
| 七年级下册 | 1 | 0 | 1 |
| 八年级上册 | 12 | 0 | 12 |
| 八年级下册 | 11 | 0 | 11 |
| 九年级上册 | 4 | 33 | 37 |
| 合计 | 32 | 33 | 65 |

## 特殊说明

`cne_j180` been 与 gone 归入「已核教材但未找到对应课业」，理由是教材已教、单元归属未定。
语法附录书页108有 have/has been 与 have/has gone 的对比和西安例句。
第7单元语法栏是 already / yet / ever / never / just，第8单元是 for / since。
不改挂到第7或第8单元，也不写成书里没教。

`cne_j156`：第3单元书页24的 Why don't you talk to them? 是与父母沟通的对话。
第2单元建议是 should / could。Reading Plus 第1单元书页81的 Why not 是偶发句。
这些都不是「用 Why don't you 提建议」课业。

`cne_j157`：第3单元书页29是感谢信。第6单元书页59是读求助邮件，并要求写一封建议邮件，不是读建议信。

八年级上册 12 点现全部是「已核教材但未找到对应课业」。
2026-11-12 续核把 `cne_j113`、`cne_j115`、`cne_j116`、`cne_j117`、`cne_j119`、`cne_j120`、
`cne_j133`、`cne_j135`、`cne_j138`、`cne_j141` 从证据不足改入这一类。
依据是官方阅读器正文：第4单元书页31–40是动植物和最高级；书页37的小镇是人与自然例子；
第7单元书页70是未来城镇预测；书页62、65和听力书页99是看电影邀请；
第1单元书页8的 watch TV 是假期方式；第8单元书页74的生日聚会只是条件句角色扮演之一；
书页76–77是 How to Make a Better Conversation；书页79的正式邀请函仍属于 `cne_j136`。
这些近义句和偶发句都不改挂。`cne_j134`、`cne_j136` 的分类取值未改。

九年级上册仍有 33 点证据不足。研究笔记里没有该点书页或课文摘录的，不按官方文档概括句批量归入第一类，并写明缺什么。
语法附录里没有某个标题，只说明附录这几页没有，不能写成全书无此课。

## 分点

### 七年级上册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j053` | 交通方式 | 已核教材但未找到对应课业 | 已核七上 Reading Plus 第3单元书页77和七上第6单元书页64，以及七下正文。浮动学校补充阅读、作息短文里的 walk to school，以及语法附录里的 at the bus stop、on the way to，都不是交通方式词汇课。在已核范围内未见可改挂课业。这不是「书里没教交通」。 | docs/english-g7-official-reader-20261111.md「正文续核」cne_j053–cne_j056 行；.english-g7-research/g7b-pending-body-check-20261111.md 结论中交通四点；截图 g7a-reading-plus-p077.png、g7a-u6-p064.png。g7a-pending-body-check-20261111.md 是核验清单，结论写在官方文档。 |
| `cne_j054` | How 问交通 | 已核教材但未找到对应课业 | 同一批已核页：书页77有 So how do I go to school?，但是浮动学校补充阅读里的句子，不是 how / how long / how far 的课业。书页64的步行句和介词例句也不构成 How 问交通课。在已核范围内未见可改挂课业。 | docs/english-g7-official-reader-20261111.md「正文续核」交通四点；.english-g7-research/g7b-pending-body-check-20261111.md；截图 g7a-reading-plus-p077.png、g7a-u6-p064.png。 |
| `cne_j055` | 谈论怎么上学 | 已核教材但未找到对应课业 | 书页77的讨论题问的是浮动学校的重要性和可能困难，官方文档写明这不是谈论自己怎么上学的口语课。书页64只是作息短文里的偶发句。在已核范围内未见可改挂课业。 | docs/english-g7-official-reader-20261111.md「正文续核」；.english-g7-research/g7b-pending-body-check-20261111.md「本册未见怎么上学或交通方式课」。 |
| `cne_j056` | 读上学方式 | 已核教材但未找到对应课业 | 书页77《My Floating School》是孟加拉浮动学校的补充阅读，不是读上学方式的课业。七下第7单元语法练习里的指路、坐错车只是一般过去时例句。在已核范围内未见可改挂课业。 | docs/english-g7-official-reader-20261111.md「正文续核」；.english-g7-research/g7b-pending-body-check-20261111.md；截图 g7a-reading-plus-p077.png。 |

### 七年级下册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j097` | 读周末日记 | 已核教材但未找到对应课业 | 已核七下第7单元 Section B 书页54：日记日期是 Friday 30 May，内容是学校农场秋游。Reading Plus 第7单元书页71是 Lisa 的日食日记。两篇都不是周末日记。在已核范围内未见可改挂的周末日记课业。 | docs/english-g7-official-reader-20261111.md「正文续核」cne_j097；.english-g7-research/g7b-pending-body-check-20261111.md；截图 g7b-u7-diary-p54-pdf63-20261111.png、g7b-reading-plus-u7-diary-p71-pdf80-20261111.png。 |

### 八年级上册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j113` | 城镇设施 | 已核教材但未找到对应课业 | 已核第4单元书页31–40，全程是动植物和最高级，不是城镇设施词表或设施课。书页37 1f 只是广东小镇树木与鸟的人与自然例子，不是城镇设施课，不改挂。第7单元书页70 Project 问未来城市或城镇会怎样、会不会有更多公园和博物馆，是将来预测，不是现在的设施课，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md A 节与第4单元书页31–40、书页37 1f、第7单元书页70；截图 g8a-u4-p31-pdf40-opener.png、g8a-u4-p37-pdf46-bees-tasks-town.png、g8a-u4-p40-pdf49-project-reflecting.png、g8a-u7-p70-pdf79-project-city-town.png、g8a-u7-p70-pdf79-project-town-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「影院 / 城镇设施 / 最好的地方」。 |
| `cne_j115` | 谈论最好的地方 | 已核教材但未找到对应课业 | 第4单元书页31–40的最高级语法仍在动植物课，未见「谈论最好的地方」口语课。第7单元书页70也不是 best place 课。这些近义内容不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md A 节书页31–40与书页70；截图 g8a-u4-p32-pdf41-sectionA.png、g8a-u4-p35-pdf44-grammar-superlatives.png、g8a-u7-p70-pdf79-project-town-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「影院 / 城镇设施 / 最好的地方」。 |
| `cne_j116` | 读影院介绍 | 已核教材但未找到对应课业 | 影院出现在第7单元书页62 Section A 1b 听力填空：请人去看新科幻片，在 cinema 见面。书页65语法有 Shall we go to see the sci-fi film?，并有 theatre 见面。听力原文书页99是 Huaxia Cinema、网上订票、5:15 开映。这是 will/shall 将来预测课里的邀请听力，不是影院介绍课文，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md A 节书页62、65、99；截图 g8a-u7-p62-pdf71-1b-cinema-closeup.png、g8a-u7-p65-pdf74-3a-film-closeup.png、g8a-u7-p65-pdf74-3b-theatre-closeup.png、g8a-scripts-p99-pdf108-u7-cinema-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「影院 / 城镇设施 / 最好的地方」与书页62、99、65。 |
| `cne_j117` | 电视节目 | 已核教材但未找到对应课业 | 第1单元书页8 Vocabulary in Use 2c 假期短文填空有 do nothing but relax, sleep, or watch TV，是假期方式，不是电视节目课，不改挂。第1单元主题是假期。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md B 节与书页8；截图 g8a-u1-p8-pdf17-vocab-watch-tv.png、g8a-u1-p8-pdf17-2c-watch-tv-closeup.png、g8a-u1-p1-pdf10-opener.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。 |
| `cne_j119` | 谈论想看的节目 | 已核教材但未找到对应课业 | 未见谈论想看的电视节目的听说课。第7单元看电影邀请不是本点，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md B 节；截图 g8a-u1-p2-pdf11-sectionA.png、g8a-u7-p62-pdf71-sectionA-cinema.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。 |
| `cne_j120` | 读节目选择 | 已核教材但未找到对应课业 | 已核第1单元书页1–10，以及为其他点核过的第4、7、8单元正文，未见节目选择短文，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md B 节；截图 g8a-u1-p6-pdf15-sectionB-reading.png、g8a-u1-p8-pdf17-2c-watch-tv-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。 |
| `cne_j133` | 聚会活动 | 已核教材但未找到对应课业 | 第8单元是沟通与条件句。书页74 2e 情境1是同学请你参加周末生日聚会，用 If you can come, I’ll be very happy 等 if 句做角色扮演，只是三个情境之一，不是聚会活动课，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md C 节书页74；截图 g8a-u8-p74-pdf83-situations-party.png、g8a-u8-p74-pdf83-2e-party-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「聚会 / 邀请 / 建议」。 |
| `cne_j134` | 用 can 发出邀请 | 已核教材但未找到对应课业 | 已核语法附录书页104–110的 can/could：例句是家务、手机、搭车，没有 Can you come to my party?。第2单元的 Can/Could 是家务请求和许可，含 Can I go to the movies?，不是派对邀请。在这些已核页里未见可改挂的邀请课业。 | .english-g8-research/g8a-pending-body-check-20261111.md 语法附录与 U2 结论；截图 g8a-u2-p15-pdf24-grammar-cancould.png、g8a-grammar-p104-pdf113.png 起；docs/english-g8-official-reader-20261111.md 提到第2单元家务或许可，本点另有研究笔记的逐点依据。 |
| `cne_j135` | 接受或拒绝邀请 | 已核教材但未找到对应课业 | 书页74只有 if 句提示，没有印出的接受或拒绝邀请对话。第7单元听力原文书页99的 Oh, I’d love to! 是看电影邀请，不是本点课业，不改挂。书页79仍是请教授做沟通讲座的正式邀请函，已用于 cne_j136 的已核未见课业，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md C 节书页74、书页79与 A 节书页99；截图 g8a-u8-p74-pdf83-2e-party-closeup.png、g8a-u8-p79-pdf88-invitation-writing.png、g8a-scripts-p99-pdf108-u7-cinema-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「聚会 / 邀请 / 建议」与书页99。 |
| `cne_j136` | 读邀请函 | 已核教材但未找到对应课业 | 已核第8单元书页79：Read an invitation letter for an event。范文是请教授做沟通讲座的正式邀请，不是聚会邀请函。该页不能改挂为本点。 | .english-g8-research/g8a-pending-body-check-20261111.md 书页79；截图 g8a-u8-writing-invitation-p79-pdf88.png；docs/english-g8-official-reader-20261111.md「正文续核」对 cne_j136 的单独说明。 |
| `cne_j138` | 建议用词 | 已核教材但未找到对应课业 | 书页74 2e 的 Expressions 是 if 条件句提示，含 I think you should，不是建议用词汇总课，不改挂。if 条件句和用条件句给建议已挂在第8单元，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md C 节书页74；截图 g8a-u8-p74-pdf83-2e-party-closeup.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「聚会 / 邀请 / 建议」。 |
| `cne_j141` | 读聚会建议 | 已核教材但未找到对应课业 | 第8单元书页76–77 Section B 课文是 How to Make a Better Conversation，不是聚会建议短文，不改挂。在已核范围内未见可改挂课业。 | .english-g8-research/g8a-evidence-20261112/notes.md C 节书页76–77；截图 g8a-u8-p76-pdf85-sectionB-conversation-guide.png、g8a-u8-p77-pdf86-reading-tasks.png。既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md 写明书页76–78此前不在旧截图中；本次续核笔记已补书页76–78。 |

### 八年级下册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j156` | 用 Why don't you 提建议 | 已核教材但未找到对应课业 | 第3单元书页24的 Why don't you talk to them? 是与父母沟通的对话，不是以 Why don't you 提建议为课业。第3单元语法栏是 although / until / so that。第2单元建议用语是 should / could，笔记写明未见 Why don't you。Reading Plus 第1单元书页81的 Why not choose an outdoor hobby instead? 是偶发句。这些近义句不改挂。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j156；.english-g8-research/g8b-body-20261111/notes.md C 节书页24、B 节第2单元、G 节书页81；截图 u3-p024.png、u2-p013.png、reading-plus-p081.png。 |
| `cne_j157` | 读建议信 | 已核教材但未找到对应课业 | 第3单元书页29的写作是 thank-you letter，不是建议信。第6单元书页59读的是 Tina 向 Yaming 求助的邮件（Home visit—Help needed!），写作要求是 Write an email to Tina to give some advice，这是写建议邮件，不是读建议信。不把近义邮件改挂。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j157；.english-g8-research/g8b-body-20261111/notes.md C 节书页29、D 节书页59；截图 u3-p029.png、u6-p059.png。 |
| `cne_j172` | 选词补全短文 | 已核教材但未找到对应课业 | 已核范围内未见名为 Cloze 或「选词补全」的课。所见是普通 Complete the passage with the words in the box，例如第2单元书页18、第6单元书页55。普通填空不改挂。这不是「书里没有填空练习」。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j172；.english-g8-research/g8b-body-20261111/notes.md 选词补全条。 |
| `cne_j178` | 场馆经历 | 已核教材但未找到对应课业 | 第7单元是读书。第8单元的博物馆出现在志愿讲解，不是参观场馆课。在已核范围内未见可改挂课业。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j178；.english-g8-research/g8b-body-20261111/notes.md E、F 节；截图 u7-p061.png、u8-p072.png。 |
| `cne_j180` | been 与 gone | 已核教材但未找到对应课业 | 教材已教、单元归属未定。语法附录书页108写明 have/has been 表示曾经到过某地、have/has gone 表示已经去某地了，并有西安例句。第7单元语法栏只讲 already/yet/ever/never/just，第8单元语法栏只讲 for/since，单元正文未见这一组对比。不改挂到第7或第8单元。不是「书里没教」。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j180；.english-g8-research/g8b-body-20261111/notes.md H 节书页108；截图 grammar-p108.png、grammar-p108-close-been-gone.png。 |
| `cne_j181` | 询问去过哪里 | 已核教材但未找到对应课业 | 第8单元 Have you been to our animal shelter before? 是志愿语境里的一般疑问，不是询问去过哪里的课业。语法附录有 Where has Tom gone?，笔记写明未见 Where have you been? 作为课业。这两句都不改挂。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j181；.english-g8-research/g8b-body-20261111/notes.md F 节书页75与 H 节。 |
| `cne_j182` | 读场馆经历 | 已核教材但未找到对应课业 | 第7单元阅读是 The Secret Garden，写作是读书报告。Reading Plus 第8单元是 Unusual Volunteers，不是场馆参观阅读。在已核范围内未见可改挂课业。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j182；.english-g8-research/g8b-body-20261111/notes.md E 节书页66、书页69，G 节第8篇。 |
| `cne_j183` | 旧物与回忆 | 已核教材但未找到对应课业 | 第8单元是志愿服务。第3单元丢失的吉他、第7单元花园的 painful memory 都不是旧物主题课。不把这些近义内容改挂。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j183；.english-g8-research/g8b-body-20261111/notes.md C 节书页23、E 节书页66、F 节。 |
| `cne_j185` | 谈论拥有多久 | 已核教材但未找到对应课业 | 第8单元书页75有 How long have you had your favourite toy，是 for/since 的拥有例句，不是旧物课业。for/since 语法已留在第8单元。不把该例句改挂为本点。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j185；.english-g8-research/g8b-body-20261111/notes.md F 节书页75；截图 u8-p075.png。 |
| `cne_j186` | 读旧物故事 | 已核教材但未找到对应课业 | 已核第3、7、8单元相关页和 Reading Plus，未见以旧物故事为课业的课文。第8单元书页80的项目是 Start a volunteer group。这不是「书里没有旧物」的判断，只说明已核范围里没有可改挂课业。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j186；.english-g8-research/g8b-body-20261111/notes.md 旧物条与书页80。 |

### 九年级上册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j188` | by 加动名词 | 已核教材但未找到对应课业 | 笔记记第3单元出现 by reviewing / by doing，是学习方法用语，不是 by 加动名词的语法课。语法附录书页104–106没有这个标题。在这些已核页里未见可改挂课业。不是「教材没有 by doing」。 | .english-g9-research/g9-pending-body-check-20261111.md 核验结论的偶发用词；截图 g9-u3-sectionA-p22-pdf31.png（笔记未另写印刷页，页码来自该截图文件名）；语法附录截图 g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。docs/english-g9-official-reader-20261111.md「正文续核」只有概括句，不单独作为本点依据。 |
| `cne_j191` | 节日食物 | 证据仍不足 | 目录阶段写旧版节日单元、官方目录无此课。正文笔记只列了 8 条 Reading Plus 标题和语法附录三个标题，并有一句「37点均未达到改挂标准」。没有节日食物的课文页摘录。不足以排除对应课业。 | .english-g9-research/g9-pending-body-check-20261111.md 核验结论（概括）；docs/english-g9-official-reader-20261111.md 前半是目录，后半「正文续核」不能批量认定。缺：节日食物课文页。 |
| `cne_j194` | 谈论节日 | 证据仍不足 | 与节日食物同一记录范围：没有谈论节日的听说页摘录。Reading Plus 标题清单不能代替该点的课文。 | 同 cne_j191。缺：谈论节日的活动页。 |
| `cne_j195` | 读中秋短文 | 证据仍不足 | 没有中秋短文的书页摘录。目录无此课加上 37 点概括句，达不到已核到能排除对应课业。 | 同 cne_j191。缺：中秋短文页。 |
| `cne_j196` | 公共场所 | 证据仍不足 | 目录阶段写旧版问路、官方第4单元是 memory。正文笔记没有公共场所或 restroom 课的书页摘录。 | 同九上概括结论。缺：公共场所课文页。 |
| `cne_j198` | 礼貌问路 | 证据仍不足 | 没有礼貌问路活动的书页摘录。不能用第4单元「记忆方法」的单元主题代替本点。 | 同九上概括结论。缺：问路表达的课文页。 |
| `cne_j199` | 读问路对话 | 证据仍不足 | 没有问路对话课文的书页摘录。 | 同九上概括结论。缺：问路对话页。 |
| `cne_j201` | used to 表示过去习惯 | 已核教材但未找到对应课业 | 笔记记第1单元 Grammar Focus 里 used to 作为时态填空出现，不是语法条目标题。语法附录书页104–106没有 used to。在这些已核页里未见可改挂课业。不是「教材没有 used to」。 | .english-g9-research/g9-pending-body-check-20261111.md 偶发用词与附录标题；截图 g9-u1-grammar-focus-p5-pdf14.png（页码来自文件名）；g9-grammar-p104-pdf113.png 至 p106。官方文档概括句不单独作为依据。 |
| `cne_j204` | 材料 | 已核教材但未找到对应课业 | 笔记记第5单元发明课导入有 What material are these things made of，并写明不足以改挂。语法附录书页104–106没有 be made of/from。这句不是材料词汇课。笔记没有写下该句的印刷页，不把未在笔记里钉死的截图当成新的书页发现。 | .english-g9-research/g9-pending-body-check-20261111.md 偶发用词条；语法附录书页104–106。同目录有 g9-u5-sectionB-p46-pdf55.png，笔记没有把这句钉在该页，本文不引用为书页。 |
| `cne_j206` | 询问由什么制成 | 已核教材但未找到对应课业 | 同一句 What material are these things made of 被记为发明课导入，不是询问由什么制成的课业。语法附录没有 be made of/from 标题。笔记未写该句印刷页。在已记录的范围内未见可改挂课业。 | 同 cne_j204 的研究笔记结论与语法附录书页104–106。 |
| `cne_j207` | 读产品介绍 | 证据仍不足 | 发明课导入里的材料问句对不上「读产品介绍」。笔记没有产品介绍课文的书页摘录。 | cne_j204 的那句引文不能用于本点。缺：产品介绍课文页。 |
| `cne_j212` | 青少年规则 | 证据仍不足 | 目录无此课。正文笔记没有青少年规则课文页。37 点概括句不能排除对应课业。 | 同九上概括结论。缺：青少年规则课文页。 |
| `cne_j213` | be allowed to | 证据仍不足 | 语法附录书页104–106的标题只有语态、宾语从句、关系从句，笔记写明没有 be allowed to。没有该点的单元语法栏页摘录。附录未见标题，还不足以排除全书里的课业。 | .english-g9-research/g9-pending-body-check-20261111.md 附录否定清单；截图 g9-grammar-p104-pdf113.png 至 p106。缺：单元正文里的 be allowed to 页。 |
| `cne_j214` | 讨论是否允许 | 证据仍不足 | 没有讨论是否允许的听说页摘录。 | 同九上概括结论。缺：该活动页。 |
| `cne_j215` | 读规则意见 | 证据仍不足 | 没有规则意见课文的书页摘录。 | 同九上概括结论。缺：规则意见短文页。 |
| `cne_j216` | 物品主人 | 证据仍不足 | 目录无物品归属课。正文笔记没有 whose 或 belongs to 的课文页摘录。 | 同九上概括结论。缺：物品主人课文页。 |
| `cne_j217` | must 表示推测 | 证据仍不足 | 语法附录书页104–106未见 must 表示推测。没有单元语法栏页摘录。附录否定不足以排除全书课业。 | 同 cne_j213 的附录范围。缺：单元正文页。 |
| `cne_j218` | 推测物品归属 | 证据仍不足 | 没有推测物品归属的活动页摘录。 | 同九上概括结论。缺：该活动页。 |
| `cne_j219` | 读推测短文 | 证据仍不足 | 没有推测短文的书页摘录。 | 同九上概括结论。缺：推测短文页。 |

### 八年级下册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j225` | be supposed to | 已核教材但未找到对应课业 | 已核第6单元书页55语法栏，内容是 so … that、unless、as soon as。语法附录书页105–112未见 be supposed to。不因跨文化主题改挂。这是已核范围未见该课业，不是「全书不存在这个说法」。 | docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j225；.english-g8-research/g8b-body-20261111/notes.md D 节与 H 节；截图 u6-p055.png、grammar-p105.png 起。 |

### 九年级上册

| id | 点名 | 分类 | 理由 | 证据 |
| --- | --- | --- | --- | --- |
| `cne_j228` | 情绪反应 | 证据仍不足 | 目录无电影课。正文笔记没有情绪或电影感受的课文页摘录。 | 同九上概括结论。缺：情绪反应课文页。 |
| `cne_j229` | make 加宾语加动词原形 | 证据仍不足 | 语法附录书页104–106未见 make sb do。没有单元语法栏页摘录。附录否定不足以排除全书课业。 | 同 cne_j213 的附录范围。缺：单元正文页。 |
| `cne_j230` | 表达电影感受 | 证据仍不足 | 没有表达电影感受的听说页摘录。 | 同九上概括结论。缺：该活动页。 |
| `cne_j231` | 读观后感 | 证据仍不足 | 没有观后感课文的书页摘录。 | 同九上概括结论。缺：观后感页。 |
| `cne_j232` | 意外事件 | 证据仍不足 | 目录无意外课。正文笔记没有意外事件课文页。 | 同九上概括结论。缺：意外课文页。 |
| `cne_j233` | 过去完成时 | 证据仍不足 | 语法附录书页104–106未见过去完成时。没有单元语法栏页摘录。附录否定不足以排除全书课业。 | 同 cne_j213 的附录范围。缺：单元正文页。 |
| `cne_j234` | 叙述意外经过 | 证据仍不足 | 没有叙述意外经过的表达页摘录。 | 同九上概括结论。缺：该活动页。 |
| `cne_j235` | 读意外故事 | 证据仍不足 | 没有意外故事课文的书页摘录。 | 同九上概括结论。缺：意外故事页。 |
| `cne_j236` | 环境保护 | 证据仍不足 | 目录无环保课。正文笔记没有环境保护课文页。 | 同九上概括结论。缺：环保课文页。 |
| `cne_j237` | 时态选择 | 证据仍不足 | 没有以时态选择为课业的书页摘录。语法附录的三个标题也不含这项。某课里偶尔选时态，笔记未逐页记录，不能当成已排除。 | 同九上概括结论与附录书页104–106。缺：时态选择课的正文页。 |
| `cne_j238` | 谈论环保做法 | 证据仍不足 | 没有谈论环保做法的听说页摘录。 | 同九上概括结论。缺：该活动页。 |
| `cne_j239` | 读环保倡议 | 证据仍不足 | 没有环保倡议课文的书页摘录。 | 同九上概括结论。缺：环保倡议页。 |
| `cne_j240` | 完形填空 | 证据仍不足 | 清单写练习里出现完形不等于要改挂。结论没有摘录名为完形填空的书页，只有 37 点概括句。 | .english-g9-research/g9-pending-body-check-20261111.md 清单与概括结论。缺：完形栏目的书页摘录。 |
| `cne_j241` | 毕业回忆 | 证据仍不足 | 目录和正文续核概括句说第4单元 Our Memory 是记忆方法，不是毕业主题。没有毕业回忆课文的书页摘录。概括句不能排除对应课业。 | docs/english-g9-official-reader-20261111.md「正文续核」一句；.english-g9-research/g9-pending-body-check-20261111.md 清单已写 U4 不是毕业回忆，正文结论未摘录书页。未转写截图 g9-u4-grammar-focus-p35-pdf44.png。缺：毕业回忆课文页。 |
| `cne_j242` | 动名词与不定式 | 证据仍不足 | 语法附录书页104–106未见动名词与不定式。没有单元语法栏页摘录。附录否定不足以排除全书课业。 | 同 cne_j213 的附录范围。缺：单元正文页。 |
| `cne_j243` | 反意疑问句 | 证据仍不足 | 语法附录书页104–106未见反意疑问句。没有单元语法栏页摘录。八年级上册发音附录里的 party 反意疑问例句是另一册的偶发句，不能用来排除九上，也不能改挂。 | 同 cne_j213 的附录范围。缺：九上单元正文页。 |
| `cne_j244` | 回忆学校生活 | 证据仍不足 | 没有回忆学校生活的活动页摘录。第4单元「记忆方法」的概括不能代替本点。 | 同 cne_j241。缺：学校生活回忆的课文页。 |
| `cne_j245` | 书面表达要点 | 证据仍不足 | 目录无单独的书面表达要点课。笔记没有该课的书页摘录。单元里的写作练习不等于这个点。 | .english-g9-research/g9-pending-body-check-20261111.md 清单与概括结论。缺：书面表达要点课的书页。 |

## 材料范围

只使用仓库里已有的文档和研究笔记：
`docs/english-g7-official-reader-20261111.md`、`docs/english-g8-official-reader-20261111.md`、
`docs/english-g9-official-reader-20261111.md`，以及未跟踪目录
`.english-g7-research/`、`.english-g8-research/`、`.english-g9-research/` 里的核对笔记。
八上这 10 点以 `.english-g8-research/g8a-evidence-20261112/notes.md` 和同目录截图为准，
并对照 `.english-g8-research/g8a-existing-screenshots-transcript-20261112.md` 里已转写的对应节。
九上官方文档前半是目录阶段（当时第10页未渲染正文），后半「正文续核」只有概括，不作为九上 33 个证据不足点的批量依据。
八下以「八下正文续核」逐点表和研究笔记 `g8b-body-20261111/notes.md` 为准。

书页只引用上述笔记已经转写的句子。写入本文件时没有另开阅读器，也没有下载教材。

