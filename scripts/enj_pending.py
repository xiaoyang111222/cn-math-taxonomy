# -*- coding: utf-8 -*-
"""初中英语「N年级X册 待核」65 点的两类标记。

catalog_status 沿用道法已经使用的字段名，取值是另一对，不能和道法混用：

- body_checked_no_lesson：已核教材但未找到对应课业。已有该书点的正文、
  Reading Plus 或语法附录页码/课文，足以说明在已核范围内未见可改挂的课业。
  章节仍是「N年级X册 待核」。
- evidence_insufficient：证据仍不足。只核过目录、只有概括句、只看了少数页面，
  或记录对不上该点。不够支持上一类时用这个值。

这两个值都不是 official_toc，也不是 pending_official_lesson_list，更不是已确认挂载。
cne_j180 虽然归入 body_checked_no_lesson，catalog_note 必须写明教材已教、单元归属未定。

enj_build.py 在全新编译（库里还没有 cne_j）时调用 attach_pending。
当前库已有 cne_j，禁止对正式 data/ 运行 enj_build.py。
"""
from __future__ import annotations

BODY_CHECKED_NO_LESSON = "body_checked_no_lesson"
EVIDENCE_INSUFFICIENT = "evidence_insufficient"
ALLOWED_STATUS = (BODY_CHECKED_NO_LESSON, EVIDENCE_INSUFFICIENT)
# 道法取值。英语这 65 点禁止使用。
MORALITY_STATUS = ("official_toc", "pending_official_lesson_list")

LABEL = {
    BODY_CHECKED_NO_LESSON: "已核教材但未找到对应课业",
    EVIDENCE_INSUFFICIENT: "证据仍不足",
}

DOC_PATH = "docs/english-pending-classification-20261112.md"

# 九上 2026-11-12 续核写入这 33 点 catalog_note 的共同检查范围。
# 书页 5、22、35、46 用既有旧图，其余正文用同日新图。词表附录不纳入。
_G9A_SCOPE = (
    "已核第1–8单元正文印刷页 1–80（书页 5、22、35、46 用既有旧图 "
    ".english-g9-research/g9-u1-grammar-focus-p5-pdf14.png、"
    "g9-u3-sectionA-p22-pdf31.png、g9-u4-grammar-focus-p35-pdf44.png、"
    "g9-u5-sectionB-p46-pdf55.png，其余用 2026-11-12 新图 "
    ".english-g9-research/g9a-evidence-20261112/pNN_pdfXXX.png）、"
    "Reading Plus（含 83、85、88、91、93）、听力原文 94–103、语法附录 104–106"
    "（.english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png）。"
    "词表附录未纳入。"
)
_G9A_REVIEW = (
    ".english-g9-research/g9a-evidence-20261112/"
    "u1-u8-plus-appendix-pending-review-20261112.md"
)

# (key, id, name, status, note, evidence)
# note 是写入知识点的 catalog_note。evidence 只进本文件和分类文档。
_ROWS = [
    (
        "vo_trans7", "cne_j053", "交通方式", BODY_CHECKED_NO_LESSON,
        "已核七上 Reading Plus 第3单元书页77和七上第6单元书页64，以及七下正文。"
        "浮动学校补充阅读、作息短文里的 walk to school，以及语法附录里的 at the bus stop、on the way to，"
        "都不是交通方式词汇课。在已核范围内未见可改挂课业。这不是「书里没教交通」。",
        "docs/english-g7-official-reader-20261111.md「正文续核」cne_j053–cne_j056 行；"
        ".english-g7-research/g7b-pending-body-check-20261111.md 结论中交通四点；"
        "截图 g7a-reading-plus-p077.png、g7a-u6-p064.png。"
        "g7a-pending-body-check-20261111.md 是核验清单，结论写在官方文档。",
    ),
    (
        "gr_howfar", "cne_j054", "How 问交通", BODY_CHECKED_NO_LESSON,
        "同一批已核页：书页77有 So how do I go to school?，但是浮动学校补充阅读里的句子，"
        "不是 how / how long / how far 的课业。书页64的步行句和介词例句也不构成 How 问交通课。"
        "在已核范围内未见可改挂课业。",
        "docs/english-g7-official-reader-20261111.md「正文续核」交通四点；"
        ".english-g7-research/g7b-pending-body-check-20261111.md；"
        "截图 g7a-reading-plus-p077.png、g7a-u6-p064.png。",
    ),
    (
        "fu_trans7", "cne_j055", "谈论怎么上学", BODY_CHECKED_NO_LESSON,
        "书页77的讨论题问的是浮动学校的重要性和可能困难，官方文档写明这不是谈论自己怎么上学的口语课。"
        "书页64只是作息短文里的偶发句。在已核范围内未见可改挂课业。",
        "docs/english-g7-official-reader-20261111.md「正文续核」；"
        ".english-g7-research/g7b-pending-body-check-20261111.md「本册未见怎么上学或交通方式课」。",
    ),
    (
        "rw_trans7", "cne_j056", "读上学方式", BODY_CHECKED_NO_LESSON,
        "书页77《My Floating School》是孟加拉浮动学校的补充阅读，不是读上学方式的课业。"
        "七下第7单元语法练习里的指路、坐错车只是一般过去时例句。在已核范围内未见可改挂课业。",
        "docs/english-g7-official-reader-20261111.md「正文续核」；"
        ".english-g7-research/g7b-pending-body-check-20261111.md；"
        "截图 g7a-reading-plus-p077.png。",
    ),
    (
        "rw_wknd", "cne_j097", "读周末日记", BODY_CHECKED_NO_LESSON,
        "已核七下第7单元 Section B 书页54：日记日期是 Friday 30 May，内容是学校农场秋游。"
        "Reading Plus 第7单元书页71是 Lisa 的日食日记。两篇都不是周末日记。"
        "在已核范围内未见可改挂的周末日记课业。",
        "docs/english-g7-official-reader-20261111.md「正文续核」cne_j097；"
        ".english-g7-research/g7b-pending-body-check-20261111.md；"
        "截图 g7b-u7-diary-p54-pdf63-20261111.png、g7b-reading-plus-u7-diary-p71-pdf80-20261111.png。",
    ),
    (
        "vo_town", "cne_j113", "城镇设施", BODY_CHECKED_NO_LESSON,
        "已核第4单元书页31–40，全程是动植物和最高级，不是城镇设施词表或设施课。"
        "书页37 1f 只是广东小镇树木与鸟的人与自然例子，不是城镇设施课，不改挂。"
        "第7单元书页70 Project 问未来城市或城镇会怎样、会不会有更多公园和博物馆，"
        "是将来预测，不是现在的设施课，不改挂。在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md A 节与第4单元书页31–40、书页37 1f、第7单元书页70；"
        "截图 g8a-u4-p31-pdf40-opener.png、g8a-u4-p37-pdf46-bees-tasks-town.png、"
        "g8a-u4-p40-pdf49-project-reflecting.png、g8a-u7-p70-pdf79-project-city-town.png、"
        "g8a-u7-p70-pdf79-project-town-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「影院 / 城镇设施 / 最好的地方」。",
    ),
    (
        "fu_best", "cne_j115", "谈论最好的地方", BODY_CHECKED_NO_LESSON,
        "第4单元书页31–40的最高级语法仍在动植物课，未见「谈论最好的地方」口语课。"
        "第7单元书页70也不是 best place 课。这些近义内容不改挂。在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md A 节书页31–40与书页70；"
        "截图 g8a-u4-p32-pdf41-sectionA.png、g8a-u4-p35-pdf44-grammar-superlatives.png、"
        "g8a-u7-p70-pdf79-project-town-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「影院 / 城镇设施 / 最好的地方」。",
    ),
    (
        "rw_best", "cne_j116", "读影院介绍", BODY_CHECKED_NO_LESSON,
        "影院出现在第7单元书页62 Section A 1b 听力填空：请人去看新科幻片，在 cinema 见面。"
        "书页65语法有 Shall we go to see the sci-fi film?，并有 theatre 见面。"
        "听力原文书页99是 Huaxia Cinema、网上订票、5:15 开映。"
        "这是 will/shall 将来预测课里的邀请听力，不是影院介绍课文，不改挂。"
        "在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md A 节书页62、65、99；"
        "截图 g8a-u7-p62-pdf71-1b-cinema-closeup.png、g8a-u7-p65-pdf74-3a-film-closeup.png、"
        "g8a-u7-p65-pdf74-3b-theatre-closeup.png、g8a-scripts-p99-pdf108-u7-cinema-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「影院 / 城镇设施 / 最好的地方」与书页62、99、65。",
    ),
    (
        "vo_show", "cne_j117", "电视节目", BODY_CHECKED_NO_LESSON,
        "第1单元书页8 Vocabulary in Use 2c 假期短文填空有 do nothing but relax, sleep, or watch TV，"
        "是假期方式，不是电视节目课，不改挂。第1单元主题是假期。在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md B 节与书页8；"
        "截图 g8a-u1-p8-pdf17-vocab-watch-tv.png、g8a-u1-p8-pdf17-2c-watch-tv-closeup.png、"
        "g8a-u1-p1-pdf10-opener.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。",
    ),
    (
        "fu_show", "cne_j119", "谈论想看的节目", BODY_CHECKED_NO_LESSON,
        "未见谈论想看的电视节目的听说课。第7单元看电影邀请不是本点，不改挂。"
        "在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md B 节；"
        "截图 g8a-u1-p2-pdf11-sectionA.png、g8a-u7-p62-pdf71-sectionA-cinema.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。",
    ),
    (
        "rw_show", "cne_j120", "读节目选择", BODY_CHECKED_NO_LESSON,
        "已核第1单元书页1–10，以及为其他点核过的第4、7、8单元正文，未见节目选择短文，不改挂。"
        "在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md B 节；"
        "截图 g8a-u1-p6-pdf15-sectionB-reading.png、g8a-u1-p8-pdf17-2c-watch-tv-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md「电视节目」。",
    ),
    (
        "vo_party", "cne_j133", "聚会活动", BODY_CHECKED_NO_LESSON,
        "第8单元是沟通与条件句。书页74 2e 情境1是同学请你参加周末生日聚会，"
        "用 If you can come, I’ll be very happy 等 if 句做角色扮演，只是三个情境之一，"
        "不是聚会活动课，不改挂。在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md C 节书页74；"
        "截图 g8a-u8-p74-pdf83-situations-party.png、g8a-u8-p74-pdf83-2e-party-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「聚会 / 邀请 / 建议」。",
    ),
    (
        "gr_invite", "cne_j134", "用 can 发出邀请", BODY_CHECKED_NO_LESSON,
        "已核语法附录书页104–110的 can/could：例句是家务、手机、搭车，没有 Can you come to my party?。"
        "第2单元的 Can/Could 是家务请求和许可，含 Can I go to the movies?，不是派对邀请。"
        "在这些已核页里未见可改挂的邀请课业。",
        ".english-g8-research/g8a-pending-body-check-20261111.md 语法附录与 U2 结论；"
        "截图 g8a-u2-p15-pdf24-grammar-cancould.png、g8a-grammar-p104-pdf113.png 起；"
        "docs/english-g8-official-reader-20261111.md 提到第2单元家务或许可，本点另有研究笔记的逐点依据。",
    ),
    (
        "fu_invite", "cne_j135", "接受或拒绝邀请", BODY_CHECKED_NO_LESSON,
        "书页74只有 if 句提示，没有印出的接受或拒绝邀请对话。"
        "第7单元听力原文书页99的 Oh, I’d love to! 是看电影邀请，不是本点课业，不改挂。"
        "书页79仍是请教授做沟通讲座的正式邀请函，已用于 cne_j136 的已核未见课业，不改挂。"
        "在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md C 节书页74、书页79与 A 节书页99；"
        "截图 g8a-u8-p74-pdf83-2e-party-closeup.png、g8a-u8-p79-pdf88-invitation-writing.png、"
        "g8a-scripts-p99-pdf108-u7-cinema-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「聚会 / 邀请 / 建议」与书页99。",
    ),
    (
        "rw_invite", "cne_j136", "读邀请函", BODY_CHECKED_NO_LESSON,
        "已核第8单元书页79：Read an invitation letter for an event。"
        "范文是请教授做沟通讲座的正式邀请，不是聚会邀请函。该页不能改挂为本点。",
        ".english-g8-research/g8a-pending-body-check-20261111.md 书页79；"
        "截图 g8a-u8-writing-invitation-p79-pdf88.png；"
        "docs/english-g8-official-reader-20261111.md「正文续核」对 cne_j136 的单独说明。",
    ),
    (
        "vo_advice", "cne_j138", "建议用词", BODY_CHECKED_NO_LESSON,
        "书页74 2e 的 Expressions 是 if 条件句提示，含 I think you should，不是建议用词汇总课，不改挂。"
        "if 条件句和用条件句给建议已挂在第8单元，不改挂。在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md C 节书页74；"
        "截图 g8a-u8-p74-pdf83-2e-party-closeup.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md"
        "「聚会 / 邀请 / 建议」。",
    ),
    (
        "rw_if", "cne_j141", "读聚会建议", BODY_CHECKED_NO_LESSON,
        "第8单元书页76–77 Section B 课文是 How to Make a Better Conversation，不是聚会建议短文，不改挂。"
        "在已核范围内未见可改挂课业。",
        ".english-g8-research/g8a-evidence-20261112/notes.md C 节书页76–77；"
        "截图 g8a-u8-p76-pdf85-sectionB-conversation-guide.png、g8a-u8-p77-pdf86-reading-tasks.png。"
        "既有转写 .english-g8-research/g8a-existing-screenshots-transcript-20261112.md "
        "写明书页76–78此前不在旧截图中；本次续核笔记已补书页76–78。",
    ),
    (
        "fu_advice8", "cne_j156", "用 Why don't you 提建议", BODY_CHECKED_NO_LESSON,
        "第3单元书页24的 Why don't you talk to them? 是与父母沟通的对话，不是以 Why don't you 提建议为课业。"
        "第3单元语法栏是 although / until / so that。第2单元建议用语是 should / could，笔记写明未见 Why don't you。"
        "Reading Plus 第1单元书页81的 Why not choose an outdoor hobby instead? 是偶发句。这些近义句不改挂。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j156；"
        ".english-g8-research/g8b-body-20261111/notes.md C 节书页24、B 节第2单元、G 节书页81；"
        "截图 u3-p024.png、u2-p013.png、reading-plus-p081.png。",
    ),
    (
        "rw_letter8", "cne_j157", "读建议信", BODY_CHECKED_NO_LESSON,
        "第3单元书页29的写作是 thank-you letter，不是建议信。"
        "第6单元书页59读的是 Tina 向 Yaming 求助的邮件（Home visit—Help needed!），"
        "写作要求是 Write an email to Tina to give some advice，这是写建议邮件，不是读建议信。不把近义邮件改挂。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j157；"
        ".english-g8-research/g8b-body-20261111/notes.md C 节书页29、D 节书页59；"
        "截图 u3-p029.png、u6-p059.png。",
    ),
    (
        "rw_cloze8", "cne_j172", "选词补全短文", BODY_CHECKED_NO_LESSON,
        "已核范围内未见名为 Cloze 或「选词补全」的课。"
        "所见是普通 Complete the passage with the words in the box，例如第2单元书页18、第6单元书页55。"
        "普通填空不改挂。这不是「书里没有填空练习」。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j172；"
        ".english-g8-research/g8b-body-20261111/notes.md 选词补全条。",
    ),
    (
        "vo_museum", "cne_j178", "场馆经历", BODY_CHECKED_NO_LESSON,
        "第7单元是读书。第8单元的博物馆出现在志愿讲解，不是参观场馆课。在已核范围内未见可改挂课业。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j178；"
        ".english-g8-research/g8b-body-20261111/notes.md E、F 节；截图 u7-p061.png、u8-p072.png。",
    ),
    (
        "gr_been", "cne_j180", "been 与 gone", BODY_CHECKED_NO_LESSON,
        "教材已教、单元归属未定。语法附录书页108写明 have/has been 表示曾经到过某地、"
        "have/has gone 表示已经去某地了，并有西安例句。第7单元语法栏只讲 already/yet/ever/never/just，"
        "第8单元语法栏只讲 for/since，单元正文未见这一组对比。不改挂到第7或第8单元。不是「书里没教」。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j180；"
        ".english-g8-research/g8b-body-20261111/notes.md H 节书页108；"
        "截图 grammar-p108.png、grammar-p108-close-been-gone.png。",
    ),
    (
        "fu_ever", "cne_j181", "询问去过哪里", BODY_CHECKED_NO_LESSON,
        "第8单元 Have you been to our animal shelter before? 是志愿语境里的一般疑问，不是询问去过哪里的课业。"
        "语法附录有 Where has Tom gone?，笔记写明未见 Where have you been? 作为课业。这两句都不改挂。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j181；"
        ".english-g8-research/g8b-body-20261111/notes.md F 节书页75与 H 节。",
    ),
    (
        "rw_museum", "cne_j182", "读场馆经历", BODY_CHECKED_NO_LESSON,
        "第7单元阅读是 The Secret Garden，写作是读书报告。Reading Plus 第8单元是 Unusual Volunteers，"
        "不是场馆参观阅读。在已核范围内未见可改挂课业。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j182；"
        ".english-g8-research/g8b-body-20261111/notes.md E 节书页66、书页69，G 节第8篇。",
    ),
    (
        "vo_own", "cne_j183", "旧物与回忆", BODY_CHECKED_NO_LESSON,
        "第8单元是志愿服务。第3单元丢失的吉他、第7单元花园的 painful memory 都不是旧物主题课。不把这些近义内容改挂。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j183；"
        ".english-g8-research/g8b-body-20261111/notes.md C 节书页23、E 节书页66、F 节。",
    ),
    (
        "fu_since", "cne_j185", "谈论拥有多久", BODY_CHECKED_NO_LESSON,
        "第8单元书页75有 How long have you had your favourite toy，是 for/since 的拥有例句，不是旧物课业。"
        "for/since 语法已留在第8单元。不把该例句改挂为本点。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j185；"
        ".english-g8-research/g8b-body-20261111/notes.md F 节书页75；截图 u8-p075.png。",
    ),
    (
        "rw_since", "cne_j186", "读旧物故事", BODY_CHECKED_NO_LESSON,
        "已核第3、7、8单元相关页和 Reading Plus，未见以旧物故事为课业的课文。"
        "第8单元书页80的项目是 Start a volunteer group。这不是「书里没有旧物」的判断，只说明已核范围里没有可改挂课业。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j186；"
        ".english-g8-research/g8b-body-20261111/notes.md 旧物条与书页80。",
    ),
    (
        "gr_by", "cne_j188", "by 加动名词", BODY_CHECKED_NO_LESSON,
        "笔记记第3单元出现 by reviewing / by doing，是学习方法用语，不是 by 加动名词的语法课。"
        "语法附录书页104–106没有这个标题。在这些已核页里未见可改挂课业。不是「教材没有 by doing」。",
        ".english-g9-research/g9-pending-body-check-20261111.md 核验结论的偶发用词；"
        "截图 g9-u3-sectionA-p22-pdf31.png（笔记未另写印刷页，页码来自该截图文件名）；"
        "语法附录截图 g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。"
        "docs/english-g9-official-reader-20261111.md「正文续核」只有概括句，不单独作为本点依据。",
    ),
    (
        "vo_fest", "cne_j191", "节日食物", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 mooncake、lantern、stranger、relative。"
        "Reading Plus 书页91的《春节序曲》在音乐会语境，不问节日食物，不见月饼或灯笼词表课。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 节日食物行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "fu_fest", "cne_j194", "谈论节日", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是说出节日吃什么、做什么，例如中秋赏月、喜欢月饼。"
        "书页91不问习俗。已核范围内未见谈论节日的听说课。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 谈论节日行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "rw_fest", "cne_j195", "读中秋短文", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段节日短文，找出食物和活动。未见中秋或月饼短文。"
        "书页91的音乐会补充阅读不是本点课文。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 读中秋短文行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "vo_polite", "cne_j196", "公共场所", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 restroom、stamp、postcard、politely。"
        "已见正文和听力未见公共场所词表课。"
        "书页35的机场巴士句是宾语从句合并题，不是本点，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 公共场所行；"
        "旧图 .english-g9-research/g9-u4-grammar-focus-p35-pdf44.png。",
    ),
    (
        "fu_polite", "cne_j198", "礼貌问路", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是礼貌问路并听懂直接问句和间接问句，例如 Could you please tell me where the post office is?。"
        "旧图书页35 4b 第5题 Pardon me, where can I get a bus to the airport? Could you please show me? "
        "是合并成宾语从句，已挂 cne_j197，不是问路功能课，不改挂。"
        "语法附录书页105的 Do you know where he lives? 同理。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 礼貌问路行；"
        "旧图 .english-g9-research/g9-u4-grammar-focus-p35-pdf44.png、"
        ".english-g9-research/g9-grammar-p105-pdf114.png。",
    ),
    (
        "rw_polite", "cne_j199", "读问路对话", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读问路对话并找出地点，例如 restroom、turn left、买邮票。"
        "已见页没有这类对话课文。听力原文 94–103 也没有问路脚本。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 读问路对话行；"
        "听力截图 .english-g9-research/g9a-evidence-20261112/p94_pdf103.png 至 p103_pdf112.png。",
    ),
    (
        "gr_used", "cne_j201", "used to 表示过去习惯", BODY_CHECKED_NO_LESSON,
        "笔记记第1单元 Grammar Focus 里 used to 作为时态填空出现，不是语法条目标题。"
        "语法附录书页104–106没有 used to。在这些已核页里未见可改挂课业。不是「教材没有 used to」。",
        ".english-g9-research/g9-pending-body-check-20261111.md 偶发用词与附录标题；"
        "截图 g9-u1-grammar-focus-p5-pdf14.png（页码来自文件名）；"
        "g9-grammar-p104-pdf113.png 至 p106。官方文档概括句不单独作为依据。",
    ),
    (
        "vo_material", "cne_j204", "材料", BODY_CHECKED_NO_LESSON,
        "笔记记第5单元发明课导入有 What material are these things made of，并写明不足以改挂。"
        "语法附录书页104–106没有 be made of/from。这句不是材料词汇课。"
        "笔记没有写下该句的印刷页，不把未在笔记里钉死的截图当成新的书页发现。",
        ".english-g9-research/g9-pending-body-check-20261111.md 偶发用词条；"
        "语法附录书页104–106。同目录有 g9-u5-sectionB-p46-pdf55.png，"
        "笔记没有把这句钉在该页，本文不引用为书页。",
    ),
    (
        "fu_made", "cne_j206", "询问由什么制成", BODY_CHECKED_NO_LESSON,
        "同一句 What material are these things made of 被记为发明课导入，不是询问由什么制成的课业。"
        "语法附录没有 be made of/from 标题。笔记未写该句印刷页。在已记录的范围内未见可改挂课业。",
        "同 cne_j204 的研究笔记结论与语法附录书页104–106。",
    ),
    (
        "rw_made", "cne_j207", "读产品介绍", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点按自身定义判断：读一段介绍，找出材料和产地。"
        "旧图书页46在 What material are these things made of? 之后接蔡伦造纸，"
        "是发明课导入和发明史阅读，已用于 cne_j204、cne_j206，并贴近已挂 cne_j211，不是读产品介绍并找出产地。"
        "书页47比较古代书写材料与蔡伦用纸，不是产地。"
        "书页49发明介绍写作不是读材料产地介绍：写作支架有 It was made of / from，没有产地或 produced in，不改挂。"
        "书页50是自己发明的海报。书页43是发明用途和被动语态。"
        "书页99产品听力不是阅读任务：Super See from Germany、Smart Cook from China 是发明展听力，"
        "made by the 3D printer 是由打印机做出，不是由某材料制成并标产地，不改挂。"
        "不因 made of/from 或 from China 改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.3节与读产品介绍行；"
        "旧图 .english-g9-research/g9-u5-sectionB-p46-pdf55.png；"
        "截图 .english-g9-research/g9a-evidence-20261112/p47_pdf056.png、"
        "p49_pdf058.png、p50_pdf059.png、p43_pdf052.png、p99_pdf108.png。",
    ),
    (
        "vo_teen", "cne_j212", "青少年规则", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 license、safety、society、choice。"
        "已见正文、Reading Plus 和听力未见青少年规则课。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 青少年规则行；"
        "语法附录旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "gr_allow", "cne_j213", "be allowed to", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是用 be allowed to 表示被允许做某事。"
        "八个单元语法栏和语法附录书页104–106的标题只有语态、宾语从句、关系从句，没有 be allowed to。"
        "已见的 allow 是用途或许可的零散句，不是该语法栏，不改挂。"
        "附录这几页没有该标题，不能写成全书没有。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " be allowed to 行；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png、"
        "g9-grammar-p105-pdf114.png、g9-grammar-p106-pdf115.png。",
    ),
    (
        "fu_allow", "cne_j214", "讨论是否允许", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是对校规表示同意或不同意，例如不同意十六岁开车。"
        "未见 should be allowed to drive 或 choose clothes 一类讨论校规的听说课。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 讨论是否允许行；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "rw_allow", "cne_j215", "读规则意见", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段讨论，找出谁被允许做什么。"
        "未见这类规则意见短文。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 读规则意见行；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "vo_owner", "cne_j216", "物品主人", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 whose、attend、valuable、picnic。"
        "语法附录书页106的 whose 是关系代词名单，并写明重点是 that、which、who，"
        "不是 Whose backpack is this? 课，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 物品主人行；"
        "旧图 .english-g9-research/g9-grammar-p106-pdf115.png。",
    ),
    (
        "gr_mustbe", "cne_j217", "must 表示推测", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是用 must 表示很有把握的肯定推测，用 can't 表示否定推测，例如 The guitar must be Carla's。"
        "八个单元语法栏和语法附录书页104–106未见该标题。"
        "书页58对话里的 must 是语境用法，不是推测语法栏，不以偶发 must 改挂。"
        "这只说明已核范围未见该课业，不是全书没有。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " must 表示推测行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p58_pdf067.png；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "fu_guess", "cne_j218", "推测物品归属", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是根据线索推测东西是谁的。"
        "未见该活动。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 推测物品归属行；"
        "旧图 .english-g9-research/g9-u4-grammar-focus-p35-pdf44.png、"
        ".english-g9-research/g9-grammar-p106-pdf115.png。",
    ),
    (
        "rw_guess", "cne_j219", "读推测短文", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段推理，找出物品的主人。"
        "书页35狐狸与葡萄是宾语从句选词，不是推测短文，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 读推测短文行；"
        "旧图 .english-g9-research/g9-u4-grammar-focus-p35-pdf44.png。",
    ),
    (
        "gr_supposed", "cne_j225", "be supposed to", BODY_CHECKED_NO_LESSON,
        "已核第6单元书页55语法栏，内容是 so … that、unless、as soon as。"
        "语法附录书页105–112未见 be supposed to。不因跨文化主题改挂。"
        "这是已核范围未见该课业，不是「全书不存在这个说法」。",
        "docs/english-g8-official-reader-20261111.md「八下正文续核」cne_j225；"
        ".english-g8-research/g8b-body-20261111/notes.md D 节与 H 节；截图 u6-p055.png、grammar-p105.png 起。",
    ),
    (
        "vo_emotion", "cne_j228", "情绪反应", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 friendship、king、pale、queen。"
        "音乐或人物阅读里若出现友谊等词，只是该课词汇，不是本点词表课，也不是电影情绪课，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 情绪反应行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "gr_make", "cne_j229", "make 加宾语加动词原形", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是 make somebody do 或 make somebody 加形容词，例如悲伤的电影让人哭。"
        "书页65关系从句填空里的 makes them all stop to listen、makes them smile 是偶发结构，不是 make 语法栏，不改挂。"
        "书页102的 Ms Gao made me the school photographer and reporter 是 make 加宾语加名词。"
        "第2单元书页16题头 What makes people admirable? 是讨论题，不是该语法教学。"
        "在已核范围内未见可改挂课业。这不是全书没有 make。",
        _G9A_REVIEW + " make 加宾语加动词原形行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p65_pdf074.png、"
        "p16_pdf025.png、p102_pdf111.png。",
    ),
    (
        "fu_feel9", "cne_j230", "表达电影感受", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是说出一部电影让自己有什么感受。"
        "书页91问 How did Chunjie Xuqu make the writer feel? 是音乐会补充阅读，不是表达电影感受。"
        "未见电影听说课。在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 表达电影感受行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "rw_movie", "cne_j231", "读观后感", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段观后感，找出电影给人的感受。"
        "未见以观后感为课业的短文。中国音乐会、残奥会和作曲家阅读都不是本点，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 读观后感行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p91_pdf100.png。",
    ),
    (
        "vo_unexp", "cne_j232", "意外事件", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 unexpected、backpack、block、burn。"
        "书页48的 an accident led to the invention of sticky notes 是便利贴发明故事，不是意外事件课，不改挂。"
        "Reading Plus 书页87 Braille 的 as a result of an accident 是发明家小传。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 意外事件行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p48_pdf057.png；"
        "既有 Reading Plus 图 .english-g9-research/g9-readingplus-u5-p87-pdf96.png。",
    ),
    (
        "gr_ppast", "cne_j233", "过去完成时", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是用 had 加过去分词，表示在过去某一动作之前已经发生的事。"
        "八个单元语法栏和语法附录书页104–106（表1只列一般现在、一般过去、一般将来的被动）未见 had 加过去分词专项。"
        "这只说明已核范围未见该课业，不是全书没有。在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 过去完成时行；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "fu_unexp", "cne_j234", "叙述意外经过", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是按先后顺序说出一件意外，例如闹钟没响。"
        "未见这类表达课。"
        "在已核范围内未见可改挂课业。不改挂。",
        _G9A_REVIEW + " 叙述意外经过行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p48_pdf057.png。",
    ),
    (
        "rw_unexp", "cne_j235", "读意外故事", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段意外，判断哪件事发生得更早。"
        "未见以该任务为课业的意外故事。便利贴发明、Braille 小传和书页35的狐狸故事都不是，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 读意外故事行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p48_pdf057.png；"
        "既有图 .english-g9-research/g9-readingplus-u5-p87-pdf96.png、"
        ".english-g9-research/g9-u4-grammar-focus-p35-pdf44.png。",
    ),
    (
        "vo_earth", "cne_j236", "环境保护", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 litter、bottom、coal、plastic。"
        "书页8塞罕坝短文是中国环境成就，用 bush、sandstorm、sandy、soil，不是本点词表课。"
        "听力书页94–95是沙地种树、沙尘暴变少，不是乱扔垃圾或煤、塑料的课，不改挂到第1单元。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.4节与环境保护行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p08_pdf017.png、"
        "p94_pdf103.png、p95_pdf104.png。",
    ),
    (
        "gr_review", "cne_j237", "时态选择", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是按时间状语在现在、过去、将来、进行和完成时之间选择。"
        "书页5只比较一般过去时和现在完成时，已是第1单元语法，不能自动等同本点，不改挂。"
        "这不是全书没有时态练习。在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 时态选择行；"
        "旧图 .english-g9-research/g9-u1-grammar-focus-p5-pdf14.png。",
    ),
    (
        "fu_earth", "cne_j238", "谈论环保做法", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是说出为保护环境可以做的事，例如不乱扔垃圾、少用煤。"
        "已见是种灌木防沙、环境变好（书页95），不是这些做法的听说课，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.4节与谈论环保做法行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p95_pdf104.png、p08_pdf017.png。",
    ),
    (
        "rw_earth", "cne_j239", "读环保倡议", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是读一段倡议，找出问题和做法，例如现在人们把塑料扔进河里。"
        "书页8塞罕坝是环境成就填空，不是该倡议课文，不改挂。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 读环保倡议行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p08_pdf017.png。",
    ),
    (
        "rw_cloze9", "cne_j240", "完形填空", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是根据上下文补全短文中的词。"
        "各单元 Vocabulary in Use 的 Complete the passage（书页8、48、78）是单元词汇练习，"
        "不是名为完形填空的独立课业，不因出现填空就改挂。"
        "这不是书里没有填空练习。在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 完形填空行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p08_pdf017.png、"
        "p48_pdf057.png、p78_pdf087.png。",
    ),
    (
        "vo_memory", "cne_j241", "毕业回忆", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是认读 survey、standard、graduate、ceremony。"
        "书页9 Changes in My Life 不是毕业回忆：短文写小学与初中、家和住处的变化，"
        "3c 是 Think back to when you were in primary school，不是毕业典礼，不改挂。"
        "第4单元是记忆方法。第8单元听力书页102–103是运动会，不是 graduation 或 ceremony 课。"
        "第2、第8单元里的 survey 是人物或赛事调查，不是本点词表课。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.5节与毕业回忆行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p09_pdf018.png、"
        "p102_pdf111.png、p103_pdf112.png。",
    ),
    (
        "gr_ger", "cne_j242", "动名词与不定式", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是区分动词后面接 to do 还是 doing，例如 remember doing 与 remember to do。"
        "书页15的 It is adj. (for/of sb) to do 不是 remember doing / to do，不改挂；该课已挂 cne_j253。"
        "书页15是 It was great of … to develop、It was difficult for … to do 这一语法栏。"
        "语法附录书页104–106无此标题。"
        "书页22的 I study by reviewing my notes 是 by 加动名词，已对照 cne_j188，也不是本点。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.1节与动名词与不定式行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p15_pdf024.png；"
        "旧图 .english-g9-research/g9-u3-sectionA-p22-pdf31.png、"
        "g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "gr_tag", "cne_j243", "反意疑问句", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是在陈述句后加上意思相反的简短问句。"
        "八个单元语法栏和语法附录书页104–106未见 question tag。"
        "八年级上册偶发反意疑问例句不能用来处理九上，也不改挂。"
        "这只说明已核范围未见该课业，不是全书没有。在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 反意疑问句行；"
        "旧图 .english-g9-research/g9-grammar-p104-pdf113.png 至 g9-grammar-p106-pdf115.png。",
    ),
    (
        "fu_memory", "cne_j244", "回忆学校生活", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是在毕业时回顾学校生活，例如记得第一次见面、典礼在星期五、明年毕业。"
        "书页9 Changes in My Life 是小学以来的生活变化，不是毕业时回顾学校生活，不改挂。"
        "书页102–103是运动会报名和接力，也不是。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 第3.5节与回忆学校生活行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p09_pdf018.png、"
        "p102_pdf111.png、p103_pdf112.png。",
    ),
    (
        "rw_write", "cne_j245", "书面表达要点", BODY_CHECKED_NO_LESSON,
        _G9A_SCOPE +
        "本点是选出涵盖全部要点、人称和时态都正确的句子。"
        "各单元 Writing（书页9、19、29、39、49、59、69、79）是单元写作任务，不是这种书面表达要点课，不改挂。"
        "书页49的发明介绍写作也不是本点。这不是书里没有写作。"
        "在已核范围内未见可改挂课业。",
        _G9A_REVIEW + " 书面表达要点行；"
        "截图 .english-g9-research/g9a-evidence-20261112/p09_pdf018.png、p49_pdf058.png。",
    ),
]


def _build():
    by_key = {}
    by_id = {}
    for key, tid, name, status, note, evidence in _ROWS:
        if status not in ALLOWED_STATUS:
            raise SystemExit("非法分类：%s" % key)
        if status in MORALITY_STATUS:
            raise SystemExit("英语待核点不能用道法目录状态：%s" % key)
        if not note or not evidence:
            raise SystemExit("缺少理由或证据：%s" % key)
        if tid in by_id or key in by_key:
            raise SystemExit("重复：%s" % tid)
        row = {
            "key": key,
            "id": tid,
            "name": name,
            "catalog_status": status,
            "catalog_note": note,
            "evidence": evidence,
        }
        by_key[key] = row
        by_id[tid] = row
    return by_key, by_id


BY_KEY, BY_ID = _build()


def attach_pending(topic, spec):
    """把规格里的分类抄到即将写入的知识点上。不写文件。

    unit 90 必须有分类。已确认单元不得带这条分类。
    """
    rec = BY_KEY.get(spec["key"])
    if spec.get("unit") == 90:
        if rec is None:
            raise SystemExit("unit 90 未分类：%s" % spec["key"])
        if topic.get("id") != rec["id"]:
            raise SystemExit(
                "待核 id 与规格不一致：%s 生成 %s，规格 %s"
                % (spec["key"], topic.get("id"), rec["id"])
            )
        if topic.get("name") != rec["name"] or spec.get("name") != rec["name"]:
            raise SystemExit("待核点名与规格不一致：%s" % spec["key"])
        topic["catalog_status"] = rec["catalog_status"]
        topic["catalog_note"] = rec["catalog_note"]
        return topic
    if rec is not None:
        raise SystemExit("非待核点带了待核分类：%s" % spec["key"])
    return topic


def _volume(tid):
    """与数据里的章节对应。只覆盖这 65 个 id。"""
    table = {
        "cne_j053": "七年级上册",
        "cne_j054": "七年级上册",
        "cne_j055": "七年级上册",
        "cne_j056": "七年级上册",
        "cne_j097": "七年级下册",
    }
    if tid in table:
        return table[tid]
    n = int(tid[5:])
    if tid in {
        "cne_j113", "cne_j115", "cne_j116", "cne_j117", "cne_j119", "cne_j120",
        "cne_j133", "cne_j134", "cne_j135", "cne_j136", "cne_j138", "cne_j141",
    }:
        return "八年级上册"
    if tid in {
        "cne_j156", "cne_j157", "cne_j172", "cne_j178", "cne_j180", "cne_j181",
        "cne_j182", "cne_j183", "cne_j185", "cne_j186", "cne_j225",
    }:
        return "八年级下册"
    if n >= 188:
        return "九年级上册"
    raise SystemExit("未分册：%s" % tid)


def count_by_volume():
    volumes = ["七年级上册", "七年级下册", "八年级上册", "八年级下册", "九年级上册"]
    out = {v: {BODY_CHECKED_NO_LESSON: 0, EVIDENCE_INSUFFICIENT: 0} for v in volumes}
    for row in BY_ID.values():
        out[_volume(row["id"])][row["catalog_status"]] += 1
    return out


def render_doc():
    """分类文档正文。测试用它锁定 docs/ 里的文件，避免规格和文档分叉。"""
    lines = []
    a = lines.append
    a("# 初中英语待核点分类（2026-11-12）")
    a("")
    a("65 个仍挂「N年级X册 待核」的初中英语知识点，按核对记录分成两类。")
    a("不删点，不改稳定 id、点名、题目、先修、学期、unit 90 和章节字符串，也不改挂到已确认单元。")
    a("2026-11-12 续核把八上 10 个点从证据不足改为已核未见对应课业；近义句和偶发句不改挂。")
    a("同日续核再把九上 33 个点改为已核未见对应课业。65 点现全部是这一类，证据不足为 0。")
    a("没有把「未命中」写成「教材不存在」「全书没有」或「教材都没教」。")
    a("")
    a("## 字段")
    a("")
    a("沿用知识点上的 `catalog_status`。道法已确认点是 `official_toc`，道法待核桶是 `pending_official_lesson_list`。")
    a("这 65 点用另外两个值，都不是已确认挂载：")
    a("")
    a("| 值 | 含义 |")
    a("| --- | --- |")
    a("| `body_checked_no_lesson` | 已核教材但未找到对应课业 |")
    a("| `evidence_insufficient` | 证据仍不足 |")
    a("")
    a("`catalog_note` 是一句可追溯的理由。证据路径写在下面各表，不进前台。")
    a("explore 仍按 `chapter` 字符串分组；diagnose 的 `parseChapter` 仍把「N年级X册 待核」解析为未挂到具体单元。")
    a("本批不改界面。前台仍只显示「待核」，不显示这两类的新分组。")
    a("")
    a("## 计数")
    a("")
    a("| 册 | 已核教材但未找到对应课业 | 证据仍不足 | 合计 |")
    a("| --- | ---: | ---: | ---: |")
    totals = {BODY_CHECKED_NO_LESSON: 0, EVIDENCE_INSUFFICIENT: 0}
    for vol, bucket in count_by_volume().items():
        n1 = bucket[BODY_CHECKED_NO_LESSON]
        n2 = bucket[EVIDENCE_INSUFFICIENT]
        totals[BODY_CHECKED_NO_LESSON] += n1
        totals[EVIDENCE_INSUFFICIENT] += n2
        a("| %s | %d | %d | %d |" % (vol, n1, n2, n1 + n2))
    a("| 合计 | %d | %d | %d |" % (
        totals[BODY_CHECKED_NO_LESSON],
        totals[EVIDENCE_INSUFFICIENT],
        sum(totals.values()),
    ))
    a("")
    a("## 特殊说明")
    a("")
    a("`cne_j180` been 与 gone 归入「已核教材但未找到对应课业」，理由是教材已教、单元归属未定。")
    a("语法附录书页108有 have/has been 与 have/has gone 的对比和西安例句。")
    a("第7单元语法栏是 already / yet / ever / never / just，第8单元是 for / since。")
    a("不改挂到第7或第8单元，也不写成书里没教。")
    a("")
    a("`cne_j156`：第3单元书页24的 Why don't you talk to them? 是与父母沟通的对话。")
    a("第2单元建议是 should / could。Reading Plus 第1单元书页81的 Why not 是偶发句。")
    a("这些都不是「用 Why don't you 提建议」课业。")
    a("")
    a("`cne_j157`：第3单元书页29是感谢信。第6单元书页59是读求助邮件，并要求写一封建议邮件，不是读建议信。")
    a("")
    a("八年级上册 12 点现全部是「已核教材但未找到对应课业」。")
    a("2026-11-12 续核把 `cne_j113`、`cne_j115`、`cne_j116`、`cne_j117`、`cne_j119`、`cne_j120`、")
    a("`cne_j133`、`cne_j135`、`cne_j138`、`cne_j141` 从证据不足改入这一类。")
    a("依据是官方阅读器正文：第4单元书页31–40是动植物和最高级；书页37的小镇是人与自然例子；")
    a("第7单元书页70是未来城镇预测；书页62、65和听力书页99是看电影邀请；")
    a("第1单元书页8的 watch TV 是假期方式；第8单元书页74的生日聚会只是条件句角色扮演之一；")
    a("书页76–77是 How to Make a Better Conversation；书页79的正式邀请函仍属于 `cne_j136`。")
    a("这些近义句和偶发句都不改挂。`cne_j134`、`cne_j136` 的分类取值未改。")
    a("")
    a("九年级上册 37 点现全部是「已核教材但未找到对应课业」。")
    a("2026-11-12 续核把 `cne_j191`、`cne_j194`、`cne_j195`、`cne_j196`、`cne_j198`、`cne_j199`、")
    a("`cne_j207`、`cne_j212`、`cne_j213`、`cne_j214`、`cne_j215`、`cne_j216`、`cne_j217`、`cne_j218`、`cne_j219`、")
    a("`cne_j228`、`cne_j229`、`cne_j230`、`cne_j231`、`cne_j232`、`cne_j233`、`cne_j234`、`cne_j235`、")
    a("`cne_j236`、`cne_j237`、`cne_j238`、`cne_j239`、`cne_j240`、`cne_j241`、`cne_j242`、`cne_j243`、")
    a("`cne_j244`、`cne_j245` 从证据不足改入这一类。")
    a("检查范围是第1–8单元正文印刷页 1–80（书页 5、22、35、46 用既有旧图，其余用 2026-11-12 新图）、")
    a("Reading Plus（含 83、85、88、91、93）、听力原文 94–103、语法附录 104–106。")
    a("词表附录（Vocabulary in Each Unit 107 起、A–Z、小学词汇、不规则动词）未纳入。")
    a("改挂按各点自身的阅读、听说或语法任务判断，不要求课文标题同名。零散例句和近义活动不改挂。")
    a("书页 15 的 It is adj. (for/of sb) to do 已挂 `cne_j253`，不是 remember doing / to do，不改挂 `cne_j242`。")
    a("书页 49 的发明介绍写作不是读材料产地介绍，书页 99 的产品听力不是阅读任务，不改挂 `cne_j207`。")
    a("书页 9 的 Changes in My Life 不是毕业回忆，不改挂 `cne_j241`。")
    a("`cne_j188`、`cne_j201`、`cne_j204`、`cne_j206` 的分类取值和理由未改。")
    a("这 33 点的结论是在已核范围内未见可改挂课业，不是「教材都没教」。")
    a("语法附录里没有某个标题，只说明附录这几页没有，不能写成全书无此课。")
    a("")
    a("## 分点")
    a("")
    current = None
    for row in sorted(BY_ID.values(), key=lambda r: r["id"]):
        vol = _volume(row["id"])
        if vol != current:
            if current is not None:
                a("")
            current = vol
            a("### %s" % vol)
            a("")
            a("| id | 点名 | 分类 | 理由 | 证据 |")
            a("| --- | --- | --- | --- | --- |")
        note = row["catalog_note"].replace("|", "\\|")
        evidence = row["evidence"].replace("|", "\\|")
        a("| `%s` | %s | %s | %s | %s |" % (
            row["id"], row["name"], LABEL[row["catalog_status"]], note, evidence,
        ))
    a("")
    a("## 材料范围")
    a("")
    a("只使用仓库里已有的文档和研究笔记：")
    a("`docs/english-g7-official-reader-20261111.md`、`docs/english-g8-official-reader-20261111.md`、")
    a("`docs/english-g9-official-reader-20261111.md`，以及未跟踪目录")
    a("`.english-g7-research/`、`.english-g8-research/`、`.english-g9-research/` 里的核对笔记。")
    a("八上这 10 点以 `.english-g8-research/g8a-evidence-20261112/notes.md` 和同目录截图为准，")
    a("并对照 `.english-g8-research/g8a-existing-screenshots-transcript-20261112.md` 里已转写的对应节。")
    a("九上这 33 点以 `.english-g9-research/g9a-evidence-20261112/u1-u8-plus-appendix-pending-review-20261112.md`")
    a("和同目录截图、既有旧图为准。检查范围是第1–8单元正文印刷页 1–80")
    a("（书页 5 用 `.english-g9-research/g9-u1-grammar-focus-p5-pdf14.png`，")
    a("书页 22 用 `g9-u3-sectionA-p22-pdf31.png`，书页 35 用 `g9-u4-grammar-focus-p35-pdf44.png`，")
    a("书页 46 用 `g9-u5-sectionB-p46-pdf55.png`，其余正文用 2026-11-12 新图）、")
    a("Reading Plus（含 83、85、88、91、93；先前已有 81、82、84、86、87、89、90、92）、")
    a("听力原文 94–103、语法附录 104–106（`g9-grammar-p104-pdf113.png` 至 `g9-grammar-p106-pdf115.png`）。")
    a("词表附录未纳入。九上官方文档前半是目录阶段（当时第10页未渲染正文），后半「正文续核」只有概括，不作为这 33 点的批量依据。")
    a("先前已是第一类的九上 4 点理由未改。")
    a("八下以「八下正文续核」逐点表和研究笔记 `g8b-body-20261111/notes.md` 为准。")
    a("")
    a("书页只引用上述笔记已经转写的句子。写入本文件时没有另开阅读器，也没有下载教材。")
    a("")
    return "\n".join(lines) + "\n"
