# -*- coding: utf-8 -*-
"""七年级上册。人教版 Go for it!（根据 2022 年版课程标准修订）。

单元编号见 enj_build.UNITS：101–103 预备单元，1–7 正式单元，90 待核。
食物四点改挂生成器编号 (7, 下, 40)，对应已入库的「七年级下册 第4单元 Eat Well」，
题目不在本轮改写。
"""
from en_tx import V, P, G, F, R

# 资源页只有单元标题。未核到具体单元的语音项目不改挂到 Hello! 等标题下。
PENDING = (
    " 2026-11-06 人教社七上资源页没有把这项写进某个单元标题，"
    "公开教辅也未把它定为本册某一课的重点。暂不挂到具体单元，待核。"
)


def q(prompt, answer, wrongs, expl):
    return ("c", prompt, answer, wrongs, expl)


P("ph_stress", "单词重音", 7, "上", 90,
  "能判断常见单词的重音在第几个音节。" + PENDING, "stress", [
    q("teacher 的重音在第几个音节？", "第一个音节",
      ["第二个音节", "两个音节同样重", "没有重音"], "tea-cher 的重音在 tea。"),
    q("about 的重音在第几个音节？", "第二个音节",
      ["第一个音节", "两个音节同样重", "没有重音"], "a-bout 的重音在 bout。"),
    q("哪个单词的重音在第二个音节？", "begin",
      ["student", "China", "apple"], "be-gin 的重音在 gin，其余三个词的重音在第一个音节。"),
    q("computer 的重音在第几个音节？", "第二个音节",
      ["第一个音节", "第三个音节", "三个音节同样重"], "com-pu-ter 的重音在 pu。"),
])

P("ph_tone7", "句末升降调", 7, "上", 90,
  "能区分陈述句、特殊疑问句的降调和一般疑问句的升调。" + PENDING, "tone", [
    q("一般疑问句 Are you a student? 句末通常用什么语调？", "升调",
      ["降调", "先降后升", "每个词都重读"], "一般疑问句句末通常用升调。"),
    q("陈述句 My name is Gina. 句末通常用什么语调？", "降调",
      ["升调", "先升后降再升", "没有语调"], "陈述句句末通常用降调。"),
    q("特殊疑问句 Where is she? 句末通常用什么语调？", "降调",
      ["升调", "和一般疑问句相同的升调", "只在 where 上升"], "特殊疑问句句末通常用降调。"),
    q("哪一句朗读时句末通常用升调？", "Is he your friend?",
      ["He is my friend.", "Where is your friend?", "She is Gina."],
      "Is he your friend 是一般疑问句，句末用升调。"),
])

V("vo_name", "姓名与称呼", 7, "上", 101,
  "认读 name、friend、girl 和 boy。",
  [("name", "名字"), ("friend", "朋友"), ("girl", "女孩"), ("boy", "男孩")], "vocab7")

G("gr_be7", "be 动词 am、is、are", 7, "上", 1,
  "能按主语选用 am、is 或 are。", "be_have", [
    q("I ___ Gina. 横线处填哪一个？", "am",
      ["is", "are", "be"], "I 后面用 am。"),
    q("She ___ my friend. 横线处填哪一个？", "is",
      ["am", "are", "be"], "She 后面用 is。"),
    q("They ___ students. 横线处填哪一个？", "are",
      ["am", "is", "be"], "They 后面用 are。"),
    q("哪一句是正确的？", "He is a boy.",
      ["He am a boy.", "He are a boy.", "He be a boy."], "He 和 is 搭配。"),
])

F("fu_intro", "问候与自我介绍", 7, "上", 101,
  "能问候别人，并说出自己的名字。", "func_school", [
    q("初次见面，对方说 Nice to meet you. 你应回答什么？", "Nice to meet you, too.",
      ["Good night.", "See you yesterday.", "Nice to meeting you, too."], "回答 Nice to meet you 时加上 too。"),
    q("想告诉别人自己叫 Gina，哪一句合适？", "My name is Gina.",
      ["Your name is Gina.", "She name is Gina.", "My name are Gina."], "说自己的名字用 My name is。"),
    q("早上见面，哪一句是问候？", "Good morning.",
      ["Good mornings.", "Goodbye.", "Good afternoon."], "Good morning 用来问候早晨。"),
    q("对方问 What's your name? 你叫 Tom，应回答什么？", "My name is Tom.",
      ["His name is Tom.", "I name Tom.", "You are Tom?"], "询问你的名字时，用 My name is 回答。"),
])

R("rw_intro", "读自我介绍", 7, "上", 1,
  "读一段自我介绍，找出姓名和身份。", "read_detail", [
    q("Hello. My name is Gina. I am 12. I am a student. 她叫什么？", "Gina",
      ["Alice", "Tom", "Jack"], "短文写 My name is Gina。"),
    q("Hello. My name is Gina. I am 12. I am a student. 她是做什么的？", "学生",
      ["老师", "医生", "司机"], "I am a student 是学生。"),
    q("Hi. I am Jack. I am a boy. My friend is Gina. Jack 的朋友是谁？", "Gina",
      ["Tom", "Alice", "Mike"], "短文写 My friend is Gina。"),
    q("Hi. I am Jack. I am a boy. My friend is Gina. 哪一句和短文一致？", "Jack is a boy.",
      ["Jack is a girl.", "Gina is Jack.", "Jack is 12."], "短文只说 Jack is a boy，没有说他 12 岁。"),
])

V("vo_family7", "家庭成员", 7, "上", 2,
  "认读 family、parent、sister 和 brother。",
  [("family", "家庭"), ("parent", "父或母"), ("sister", "姐姐或妹妹"), ("brother", "哥哥或弟弟")], "vocab7")

G("gr_this7", "指示代词 this、that、these、those", 7, "上", 103,
  "能用 this、that 指单数，用 these、those 指复数，并回答 What's this 和 What are these。", "noun_pron", [
    q("近处一只兔子，哪一句正确？", "This is a rabbit.",
      ["These are a rabbit.", "This are a rabbit.", "These is a rabbit."], "近处单数用 This is。"),
    q("远处那些是树，哪一句正确？", "Those are trees.",
      ["That are trees.", "Those is trees.", "This are trees."], "远处复数用 Those are。"),
    q("What are these? 这些是胡萝卜，应回答什么？", "They are carrots.",
      ["It is carrots.", "This are carrots.", "They is carrots."], "these 用 They are 回答。"),
    q("What's that? 远处是一只鹅，哪一句正确？", "It's a goose.",
      ["They're a goose.", "This are a goose.", "Those are a goose."], "that 指单数，用 It's。"),
])

G("gr_plural7", "名词复数", 7, "上", 103,
  "能把院子、农场里的常见名词变成复数，包括 sheep 和 goose。", "noun_pron", [
    q("tomato 的复数是哪一个？", "tomatoes",
      ["tomatos", "tomatoies", "tomato"], "以 o 结尾的 tomato 加 es。"),
    q("sheep 的复数是哪一个？", "sheep",
      ["sheeps", "sheepes", "sheepies"], "sheep 单复数同形。"),
    q("goose 的复数是哪一个？", "geese",
      ["gooses", "geeses", "goose"], "goose 的复数是 geese。"),
    q("哪一句的名词复数是正确的？", "I see two rabbits.",
      ["I see two rabbit.", "I see two rabites.", "I see two rabbites."], "two 后面用 rabbits。"),
])

P("ph_s", "词尾 s 的读音", 7, "上", 90,
  "能分辨词尾 -s、-es 读 /s/、/z/ 还是 /ɪz/。" + PENDING, "esound", [
    q("books 词尾 s 的读音和哪一个同类？", "maps",
      ["pens", "bags", "buses"], "books 和 maps 的词尾都读 /s/。"),
    q("bags 词尾 s 的读音和哪一个同类？", "pens",
      ["books", "maps", "buses"], "bags 和 pens 的词尾都读 /z/。"),
    q("哪个单词的词尾读 /ɪz/？", "buses",
      ["books", "bags", "maps"], "buses 的 -es 读 /ɪz/。"),
    q("boxes 的词尾和哪个词的读音相同？", "watches",
      ["cats", "dogs", "birds"], "boxes 和 watches 的词尾都读 /ɪz/。"),
])

F("fu_family7", "介绍家人", 7, "上", 2,
  "能向别人介绍自己的家人。", "func_school", [
    q("想把姐姐介绍给同学，哪一句合适？", "This is my sister.",
      ["These are my sister.", "She is my parent?", "I am your sister."], "介绍一个人用 This is。"),
    q("对方问 Who is he? 他是你的弟弟，应回答什么？", "He is my brother.",
      ["She is my brother.", "He are my brother.", "This are my brother."], "弟弟是 he，用 is。"),
    q("These are my parents. 说话人在介绍谁？", "父母",
      ["同学", "老师", "朋友的书"], "parents 是父母。"),
    q("哪一句能用来介绍照片里的一家人？", "This is my family.",
      ["This is my schoolbag.", "These are my pens.", "This are my family."], "family 是家庭。"),
])

R("rw_family7", "读家庭介绍", 7, "上", 2,
  "读一段家庭介绍，找出人物关系。", "read_detail", [
    q("This is my family. These are my parents. This is my sister, Gina. 说话人的姐姐是谁？", "Gina",
      ["Tom", "Alice", "Jack"], "This is my sister, Gina 说明姐姐是 Gina。"),
    q("This is my family. These are my parents. This is my sister, Gina. 哪一句和短文一致？", "Gina is the speaker's sister.",
      ["Gina is the speaker's brother.", "The speaker has no parents.", "Gina is a parent."],
      "短文说 This is my sister, Gina。"),
    q("I have a brother. His name is Tom. I have no sister. 说话人有姐姐吗？", "没有",
      ["有一个", "有两个", "短文没说"], "I have no sister 是没有姐姐或妹妹。"),
    q("I have a brother. His name is Tom. I have no sister. Tom 是谁？", "说话人的弟弟或哥哥",
      ["说话人的姐姐", "说话人的父母", "说话人的老师"], "His name is Tom 指 brother。"),
])

V("vo_school7", "学习用品", 7, "上", 102,
  "认读书包里的 key、cap、pencil 和 ruler。",
  [("key", "钥匙"), ("cap", "帽子"), ("pencil", "铅笔"), ("ruler", "尺子")], "vocab7")

G("gr_poss7", "形容词性物主代词", 7, "上", 1,
  "能选用 my、your、his、her 修饰名词，用来谈论你和我。", "noun_pron", [
    q("这是她的名字。哪一句正确？", "This is her name.",
      ["This is she name.", "This is hers name.", "This is her a name."], "her 后面直接加名词。"),
    q("___ friend is Tom. 朋友是男生 Tom 的，横线处填哪一个？", "His",
      ["He", "Him", "Her"], "Tom 是男性，形容词性物主代词用 His。"),
    q("I 的形容词性物主代词是哪一个？", "my",
      ["me", "mine", "myself"], "I 对应 my，不能用 myself。"),
    q("哪一句是正确的？", "Your book is here.",
      ["You book is here.", "Your is book here.", "Yours book is here."],
      "your 修饰 book，名词性物主代词 yours 后面不再加名词。"),
])

G("gr_yesno", "be 动词一般疑问句", 7, "上", 1,
  "能把含 be 动词的句子改成一般疑问句，并用来确认同学是谁。", "be_have", [
    q("She is your classmate. 改成一般疑问句，哪一句正确？", "Is she your classmate?",
      ["Does she is your classmate?", "Is she your classmate.", "Are she your classmate?"],
      "be 动词提到句首，she 仍用 is。"),
    q("Are you Tom? 肯定简答是哪一句？", "Yes, I am.",
      ["Yes, I are.", "Yes, I'm.", "Yes, I is."], "简答 Yes, I am 不能缩写 am。"),
    q("Is he your friend? 否定简答是哪一句？", "No, he isn't.",
      ["No, he aren't.", "No, he not.", "No, he doesn't."], "he 和 is 对应，否定用 isn't。"),
    q("哪一句是一般疑问句？", "Are they your classmates?",
      ["They are your classmates.", "Your classmates are they.", "What they are?"],
      "Are they 把 are 放在句首。"),
])

F("fu_lost", "确认物品是谁的", 7, "上", 102,
  "能询问帽子、钥匙是不是对方的，并说明是谁的。", "func_school", [
    q("想问这顶帽子是不是对方的，哪一句合适？", "Is this your cap?",
      ["This is your cap.", "Are this your cap?", "What your cap?"], "询问用 Is this your cap。"),
    q("对方问 Is this your key? 是你的，应回答什么？", "Yes, it is.",
      ["Yes, it are.", "No, it is mine.", "Yes, I am."], "物品用 it，肯定是 Yes, it is。"),
    q("想说这把钥匙是他的，哪一句合适？", "This is his key.",
      ["This is he key.", "This is him key.", "This are his key."], "his 修饰 key。"),
    q("Whose cap is this? 这句在问什么？", "这顶帽子是谁的",
      ["帽子在哪里", "帽子多少钱", "帽子是什么颜色"], "Whose 问所属。"),
])

R("rw_notice", "读物品归属", 7, "上", 102,
  "读一段课桌说明，找出物品是谁的、在哪里。", "read_detail", [
    q("This is my desk. The pencil is mine. The cap is his. The key is in the bag. 铅笔是谁的？", "说话人自己",
      ["他", "老师", "短文没说"], "The pencil is mine 是说话人自己的。"),
    q("This is my desk. The pencil is mine. The cap is his. The key is in the bag. 帽子是谁的？", "他",
      ["说话人自己", "老师", "Mary"], "The cap is his。"),
    q("This is my desk. The pencil is mine. The cap is his. The key is in the bag. 钥匙在哪里？", "在包里",
      ["在帽子上", "在铅笔盒外的地上", "在书桌上，短文没这么写"], "The key is in the bag。"),
    q("This is my desk. The pencil is mine. The cap is his. The key is in the bag. 哪一句和短文一致？", "The key is in the bag.",
      ["The cap is mine.", "The pencil is his.", "The desk is his."], "钥匙在包里，帽子是他的，铅笔是我的。"),
])

V("vo_room7", "房间与家具", 7, "上", 102,
  "认读 room、bed、table 和 chair。",
  [("room", "房间"), ("bed", "床"), ("table", "桌子"), ("chair", "椅子")], "vocab7")

G("gr_prep7", "方位介词", 7, "上", 3,
  "能用 in front of、behind、across from 和 next to 表示学校里场所的位置。", "there_prep", [
    q("礼堂在教学楼前面。哪一句正确？", "The hall is in front of the building.",
      ["The hall is in the front building.", "The hall are in front of the building.", "The hall is front the building."],
      "在……前面用 in front of。"),
    q("教学楼在礼堂对面。哪一句正确？", "The building is across from the hall.",
      ["The building is across to the hall.", "The building across from the hall.", "The building is across from hall the."],
      "在对面用 across from。"),
    q("Where is the hall? 这句在问什么？", "礼堂在哪里",
      ["礼堂是什么颜色", "礼堂多少钱", "礼堂是谁的"], "Where 问地点。"),
    q("餐厅在教学楼旁边。哪一句正确？", "The dining hall is next to the building.",
      ["The dining hall is next the building.", "The dining hall next to the building.", "The dining hall are next to the building."],
      "在旁边用 next to。"),
])

F("fu_where7", "询问位置", 7, "上", 102,
  "能询问东西在哪里，并说明位置。", "func_life", [
    q("找不到书包，哪一句用来询问？", "Where is my schoolbag?",
      ["What is my schoolbag?", "Where are my schoolbag?", "Who is my schoolbag?"],
      "单数物品用 Where is。"),
    q("书包在椅子下面，应回答什么？", "It is under the chair.",
      ["It are under the chair.", "It is the under chair.", "They is under the chair."],
      "单数用 It is under。"),
    q("对方说 Where are my books? 书在桌子上，应回答什么？", "They are on the table.",
      ["It is on the table.", "They is on the table.", "They are in the table."],
      "books 用 they are，在桌面上用 on。"),
    q("哪一句是在请对方看床底下？", "Look under the bed.",
      ["Look the bed under.", "Look on name.", "See you under."], "Look under the bed 是看床底下。"),
])

R("rw_room7", "读房间描述", 7, "上", 102,
  "读一段房间描述，找出物品位置。", "read_detail", [
    q("This is my room. The book is on the table. The bag is under the chair. 书在哪里？", "在桌子上",
      ["在椅子下面", "在书包里", "在床上"], "The book is on the table。"),
    q("This is my room. The book is on the table. The bag is under the chair. 包在哪里？", "在椅子下面",
      ["在桌子上", "在床上", "在书里面"], "The bag is under the chair。"),
    q("The keys are in the schoolbag. The schoolbag is on the bed. 钥匙在哪里？", "在书包里",
      ["在床底下", "在桌子上", "在椅子上"], "The keys are in the schoolbag。"),
    q("The keys are in the schoolbag. The schoolbag is on the bed. 哪一句和短文一致？", "The schoolbag is on the bed.",
      ["The keys are on the bed.", "The schoolbag is under the bed.", "The keys are under the chair."],
      "书包在床上，钥匙在书包里，不是直接在床上。"),
])

V("vo_ball", "球类运动", 7, "上", 5,
  "认读社团活动里的 basketball、soccer、tennis 和 volleyball。",
  [("basketball", "篮球"), ("soccer", "足球"), ("tennis", "网球"), ("volleyball", "排球")], "vocab7")

G("gr_have", "have 与 has", 7, "上", 2,
  "能按主语选用 have 或 has，用来说明家人有什么。", "be_have", [
    q("I ___ a brother. 横线处填哪一个？", "have",
      ["has", "am", "is"], "I 后面用 have。"),
    q("She ___ a red hat. 横线处填哪一个？", "has",
      ["have", "are", "haves"], "She 后面用 has。"),
    q("They ___ two sons. 横线处填哪一个？", "have",
      ["has", "haves", "is"], "They 后面用 have。"),
    q("哪一句是正确的？", "He has a ping-pong bat.",
      ["He have a ping-pong bat.", "He haves a ping-pong bat.", "He have bat a."], "He 用 has。"),
])

G("gr_do", "do 与 does", 7, "上", 2,
  "能用 do 或 does 构成一般现在时的疑问句和否定句，用来谈家人的活动。", "present", [
    q("___ you play chess? 横线处填哪一个？", "Do",
      ["Does", "Are", "Is"], "you 用 Do。"),
    q("___ she have a piano? 横线处填哪一个？", "Does",
      ["Do", "Is", "Has"], "she 用 Does，后面动词用原形 have。"),
    q("他不踢足球。哪一句正确？", "He doesn't play football.",
      ["He don't play football.", "He doesn't plays football.", "He not play football."],
      "doesn't 后面用动词原形 play。"),
    q("Do they read every evening? 肯定简答是哪一句？", "Yes, they do.",
      ["Yes, they have.", "Yes, they does.", "Yes, they are."], "Do 提问用 do 回答。"),
])

F("fu_ball", "谈论社团运动", 7, "上", 5,
  "能询问会不会某项运动，并说想加入体育社团。", "func_school", [
    q("想问对方会不会打篮球，哪一句合适？", "Can you play basketball?",
      ["Are you play basketball?", "Do you can play basketball?", "Can you plays basketball?"],
      "能力用 Can you play。"),
    q("对方问 Can you play tennis? 你会，应回答什么？", "Yes, I can.",
      ["Yes, I can to.", "Yes, I am.", "Yes, I does."], "Can you 的肯定简答是 Yes, I can。"),
    q("想说你想加入体育社团，哪一句合适？", "I want to join the sports club.",
      ["I want join the sports club.", "I wants to join the sports club.", "I want to joining the sports club."],
      "want to 后面用动词原形 join。"),
    q("Let's play soccer. 这句是在做什么？", "建议去踢足球",
      ["询问足球的价格", "说自己没有足球", "介绍一个姐姐"], "Let's 用来提出建议。"),
])

R("rw_ball", "读体育社团短文", 7, "上", 5,
  "读一段体育社团短文，找出谁会什么、哪天活动。", "read_detail", [
    q("The sports club meets on Friday. Tom can play basketball. He cannot play tennis. His sister can play tennis. Tom 会打网球吗？", "不会",
      ["会", "只在星期五会，短文没这么说", "短文没说"], "He cannot play tennis。"),
    q("The sports club meets on Friday. Tom can play basketball. He cannot play tennis. His sister can play tennis. 谁会打网球？", "Tom 的姐姐或妹妹",
      ["Tom", "老师", "短文没说"], "His sister can play tennis。"),
    q("The sports club meets on Friday. Tom can play basketball. He cannot play tennis. His sister can play tennis. 社团在星期几活动？", "星期五",
      ["星期一", "每天", "星期日"], "meets on Friday。"),
    q("The sports club meets on Friday. Tom can play basketball. He cannot play tennis. His sister can play tennis. 哪一句和短文一致？", "Tom can play basketball.",
      ["Tom can play tennis.", "The club meets on Monday.", "His sister cannot play tennis."],
      "Tom can play basketball，他不会网球。"),
])

V("vo_food7", "食物", 7, "下", 40,
  "认读 banana、hamburger、salad 和 ice-cream。",
  [("banana", "香蕉"), ("hamburger", "汉堡包"), ("salad", "沙拉"), ("ice-cream", "冰激凌")], "vocab7")

G("gr_count", "可数与不可数名词", 7, "下", 40,
  "能区分可数名词和不可数名词，并选用 a、an 或 some。", "noun_pron", [
    q("banana 是可数名词。哪一句正确？", "I like bananas.",
      ["I like a bananaes.", "I like bananaes.", "I like an bananas."], "可数名词复数是 bananas。"),
    q("milk 是不可数名词。哪一句正确？", "I like milk.",
      ["I like a milk.", "I like milks.", "I like an milk."], "不可数名词不加 a，也不加 s。"),
    q("想要一些沙拉，哪一句正确？", "I want some salad.",
      ["I want a salades.", "I want some salads the count.", "I want an salad."],
      "salad 在这里作不可数食物，用 some salad。"),
    q("哪一个是不可数名词？", "milk",
      ["banana", "hamburger", "apple"], "milk 不可数；香蕉、汉堡和苹果可数。"),
])

G("gr_like7", "like 的句型", 7, "上", 4,
  "能用 like 的肯定句、否定句和疑问句谈论对学科的喜好。", "present", [
    q("她喜欢历史。哪一句正确？", "She likes history.",
      ["She like history.", "She likes histories.", "She like a history."], "She 后面动词加 s。"),
    q("我不喜欢地理。哪一句正确？", "I don't like geography.",
      ["I doesn't like geography.", "I don't likes geography.", "I not like geography."],
      "I 的否定用 don't，后面动词用原形。"),
    q("___ she like science? 横线处填哪一个？", "Does",
      ["Do", "Is", "Are"], "she 用 Does，like 用原形。"),
    q("Do you like P.E.? 否定回答是哪一句？", "No, I don't.",
      ["No, I doesn't.", "No, I'm not.", "No, I don't like."], "Do you 的否定简答是 No, I don't。"),
])

F("fu_food7", "谈论食物", 7, "下", 40,
  "能询问和表达对食物的喜好。", "func_life", [
    q("想问对方喜不喜欢沙拉，哪一句合适？", "Do you like salad?",
      ["Are you like salad?", "Does you like salad?", "Do you likes salad?"], "you 用 Do you like。"),
    q("你喜欢香蕉，应怎么说？", "I like bananas.",
      ["I likes bananas.", "I like bananaes.", "I am like bananas."], "I like 加可数名词复数。"),
    q("对方说 I don't like hamburgers. 这句话的意思是什么？", "我不喜欢汉堡",
      ["我有汉堡", "我正在吃汉堡", "汉堡在桌子上"], "don't like 表示不喜欢。"),
    q("想建议一起吃冰激凌，哪一句合适？", "Let's have some ice-cream.",
      ["Let's has some ice-cream.", "Let have an ice-cream the.", "Let's having ice-cream."],
      "Let's 后面用动词原形 have。"),
])

R("rw_food7", "读饮食短文", 7, "下", 40,
  "读一段饮食短文，找出人物的喜好。", "read_detail", [
    q("Gina likes bananas and milk. She doesn't like hamburgers. Gina 喜欢汉堡吗？", "不喜欢",
      ["喜欢", "只在学校喜欢", "短文没说"], "She doesn't like hamburgers。"),
    q("Gina likes bananas and milk. She doesn't like hamburgers. 她喜欢喝什么？", "牛奶",
      ["沙拉", "汉堡", "茶"], "likes milk 是喜欢牛奶。"),
    q("Tom likes salad. He doesn't like ice-cream. His sister likes ice-cream. 谁喜欢冰激凌？", "Tom 的姐姐或妹妹",
      ["Tom", "Gina", "Tom 的爸爸"], "His sister likes ice-cream。"),
    q("Tom likes salad. He doesn't like ice-cream. 哪一句和短文一致？", "Tom likes salad.",
      ["Tom likes ice-cream.", "Tom doesn't like salad.", "Tom has no sister in this text and he likes hamburgers."],
      "第一句就是 Tom likes salad。干扰项里后半句短文没有说到汉堡。"),
])

V("vo_clothes7", "生日聚会", 7, "上", 7,
  "认读 birthday、party、cake 和 balloon。",
  [("birthday", "生日"), ("party", "聚会"), ("cake", "蛋糕"), ("balloon", "气球")], "vocab7")

G("gr_much", "How much 问价格", 7, "上", 7,
  "能用 How much 询问生日蛋糕、气球的价格。", "question", [
    q("询问这个生日蛋糕多少钱，哪一句正确？", "How much is this cake?",
      ["How much are this cake?", "How many is this cake?", "How much this cake is?"],
      "蛋糕是单数，用 How much is。"),
    q("这些气球 6 美元。哪一句正确？", "The balloons are 6 dollars.",
      ["The balloons is 6 dollars.", "The balloons are 6 dollar.", "The balloons have 6 dollar."],
      "复数用 are，美元复数用 dollars。"),
    q("How much are the balloons? 这句在问什么？", "这些气球多少钱",
      ["气球是什么颜色", "气球在哪里", "你有几个气球"], "How much 问价格。"),
    q("蛋糕 15 美元。哪一句正确？", "The cake is fifteen dollars.",
      ["The cake are fifteen dollars.", "The cake is fifteen dollar.", "The cakes is fifteen dollars."],
      "一个蛋糕用 is，dollars 用复数。"),
])

F("fu_shop7", "为聚会询价", 7, "上", 7,
  "能为生日聚会询问价格，并决定买或不买。", "func_life", [
    q("在商店想问蛋糕的价格，哪一句合适？", "How much is the cake?",
      ["How many is the cake?", "What much is the cake?", "How much the cake is?"],
      "单数物品用 How much is。"),
    q("店员说 It is 20 dollars. 你决定买下，哪一句合适？", "I'll take it.",
      ["I take them are.", "I'll taking it.", "I am take it."], "I'll take it 表示我买下它。"),
    q("想要一些气球，哪一句合适？", "I want some balloons.",
      ["I want a balloons.", "I want some balloones.", "I wants some balloons."], "some 加复数 balloons。"),
    q("Can I help you? 店员这句是在做什么？", "询问你需要什么帮助",
      ["询问你的生日", "说蛋糕很贵", "介绍自己的家人"], "Can I help you 是商店里的招呼。"),
])

R("rw_shop7", "读聚会购物", 7, "上", 7,
  "读一段为聚会买东西的对话，找出价格和决定。", "read_detail", [
    q("Girl: How much is this cake? Clerk: It is 20 dollars. Girl: I'll take it. 蛋糕多少钱？", "20 美元",
      ["6 美元", "15 美元", "8 美元"], "It is 20 dollars。"),
    q("Girl: How much is this cake? Clerk: It is 20 dollars. Girl: I'll take it. 她买了吗？", "买了",
      ["没买", "只问了颜色", "店员不卖"], "I'll take it 表示买下。"),
    q("Boy: How much are the balloons? Clerk: They are 6 dollars. Boy: They are too dear. I will not take them. 按男孩的话，气球贵不贵？", "他认为太贵",
      ["他认为很便宜", "他马上买下", "短文没谈价格"], "too dear 是太贵，他不买。"),
    q("选词填空：The cake is 20 ___. I will take it. 哪个词使句子完整？", "dollars",
      ["dollar", "much", "party"], "20 后面用复数 dollars。"),
])

V("vo_date", "月份与序数词", 7, "上", 7,
  "认读 January、February、March 和 April。",
  [("January", "一月"), ("February", "二月"), ("March", "三月"), ("April", "四月")], "vocab7")

G("gr_when7", "When 问日期", 7, "上", 7,
  "能用 When 询问日期，并用月份加序数词回答。", "question", [
    q("询问生日是哪一天，哪一句正确？", "When is your birthday?",
      ["When your birthday is?", "What is your birthday?", "When are your birthday?"],
      "When is your birthday 问日期。"),
    q("生日是 5 月 2 日。哪一句正确？", "My birthday is on May 2nd.",
      ["My birthday is on May two.", "My birthday is in May 2nd.", "My birthday are on May 2nd."],
      "具体日期用 on，序数词用 2nd。"),
    q("第一个月是哪一个？", "January",
      ["February", "March", "April"], "January 是一月。"),
    q("third 对应的基数词是哪一个？", "three",
      ["thirdly", "thirty", "thirteen"], "third 是第三，基数词是 three。"),
])

F("fu_bday7", "谈论生日", 7, "上", 7,
  "能询问和说明生日、年龄。", "func_school", [
    q("想问对方的生日，哪一句合适？", "When is your birthday?",
      ["Where is your birthday?", "When are your birthday?", "How much is your birthday?"],
      "问日期用 When is your birthday。"),
    q("你的生日是 9 月 5 日，应回答什么？", "It is on September 5th.",
      ["It is in September 5.", "It is on September five.", "It are on September 5th."],
      "具体日子用 on 加序数词。"),
    q("How old are you? 这句在问什么？", "你多大",
      ["你的生日是哪天", "你叫什么", "你来自哪里"], "How old 问年龄。"),
    q("想说 Alice 十二岁，哪一句合适？", "Alice is twelve.",
      ["Alice are twelve.", "Alice is twelfth.", "Alice has twelve."], "年龄用基数词 twelve，不是序数词 twelfth。"),
])

R("rw_cal7", "读生日安排", 7, "上", 7,
  "读一则生日安排，找出日期和活动。", "read_detail", [
    q("Tom's birthday is on September 21st. His party is on that day. The family dinner is on October 2nd. Tom 的生日是哪一天？", "9 月 21 日",
      ["10 月 2 日", "9 月 2 日", "10 月 21 日"], "September 21st 是 9 月 21 日。"),
    q("Tom's birthday is on September 21st. His party is on that day. The family dinner is on October 2nd. 家庭晚餐在哪一天？", "10 月 2 日",
      ["9 月 21 日", "10 月 21 日", "11 月 2 日"], "October 2nd 是 10 月 2 日。"),
    q("Tom's birthday is on September 21st. His party is on that day. The family dinner is on October 2nd. 聚会和生日是不是同一天？", "是",
      ["不是", "聚会在十月", "短文没说聚会"], "His party is on that day，that day 指生日。"),
    q("Tom's birthday is on September 21st. His party is on that day. The family dinner is on October 2nd. 哪一句和短文一致？", "The party is on September 21st.",
      ["The dinner is on September 21st.", "Tom's birthday is on October 2nd.", "There is no party."],
      "聚会在生日当天，也就是 9 月 21 日。"),
])

V("vo_subj", "学科词汇", 7, "上", 4,
  "认读 subject、science、history 和 geography。",
  [("subject", "学科"), ("science", "科学"), ("history", "历史"), ("geography", "地理")], "vocab7")

G("gr_because", "because 说明原因", 7, "上", 4,
  "能用 because 回答 why，说明原因。", "clause_adv", [
    q("Why do you like science? 哪一句适合作为回答？", "Because it is interesting.",
      ["Because it are interesting.", "So it is interesting.", "Why it is interesting."],
      "回答 why 用 because，it 用 is。"),
    q("哪一句正确？", "I like history because it is fun.",
      ["I like history because it are fun.", "I like history so it is fun.", "Because I like history it is fun."],
      "because 连接原因，it is fun。"),
    q("Because he likes P.E. 这半句是在做什么？", "说明原因",
      ["询问时间", "询问价格", "发出命令"], "because 用来说明原因。"),
    q("她喜欢地理，因为它有用。哪一句正确？", "She likes geography because it is useful.",
      ["She like geography because it is useful.", "She likes geography because it are useful.", "She likes geography so it is useful."],
      "She likes，because 从句里 it is。"),
])

F("fu_subj", "谈论最喜欢的学科", 7, "上", 4,
  "能说出最喜欢的学科并说明原因。", "func_school", [
    q("想问对方最喜欢的学科，哪一句合适？", "What's your favorite subject?",
      ["What's your favorite subjects?", "What your favorite subject is?", "How much is your favorite subject?"],
      "What's your favorite subject 问最喜欢的一门学科。"),
    q("你最喜欢科学，应回答什么？", "My favorite subject is science.",
      ["My favorite subject are science.", "I favorite science.", "Science is my favorite subject are."],
      "subject 是单数，用 is。"),
    q("想问为什么喜欢历史，哪一句合适？", "Why do you like history?",
      ["Why does you like history?", "Why do you likes history?", "Because do you like history?"],
      "you 用 Why do you like。"),
    q("Friday 下午有地理课。想告诉同学，哪一句合适？", "We have geography on Friday afternoon.",
      ["We has geography on Friday afternoon.", "We have geography in Friday afternoon.", "We have geography on Friday the afternoon is."],
      "在星期几的下午用 on Friday afternoon，we have。"),
])

R("rw_subj", "读课程介绍", 7, "上", 4,
  "读一段课程介绍，找出喜欢的学科和原因。", "read_detail", [
    q("My favorite subject is science. I have it on Monday. I like it because it is interesting. 最喜欢的学科是什么？", "科学",
      ["历史", "地理", "体育"], "favorite subject is science。"),
    q("My favorite subject is science. I have it on Monday. I like it because it is interesting. 为什么喜欢？", "因为它有趣",
      ["因为它很难", "因为在星期五", "因为老师很严格，短文没有写别的原因"], "because it is interesting。"),
    q("Jack's favorite subject is history. He thinks it is useful. He doesn't like geography. Jack 喜欢地理吗？", "不喜欢",
      ["喜欢", "只在星期一喜欢", "短文没说"], "He doesn't like geography。"),
    q("Jack's favorite subject is history. He thinks it is useful. 哪一句和短文一致？", "Jack likes history.",
      ["Jack likes geography.", "Jack's favorite subject is science.", "History is not useful for Jack."],
      "favorite subject is history，而且他认为有用。"),
])
