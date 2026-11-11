# -*- coding: utf-8 -*-
"""九年级上册已按 2026-11-11 官方阅读器 8 单元改挂，对不上的点挂「九年级上册 待核」。"""
from en_tx import V, P, G, F, R


def q(prompt, answer, wrongs, expl):
    return ("c", prompt, answer, wrongs, expl)


V("vo_learn", "学习方法", 9, "上", 3,
  "认读 pronunciation、expression、repeat 和 patient。",
  [("pronunciation", "发音"), ("expression", "表达方式"), ("repeat", "重复"), ("patient", "有耐心的")], "vocab9")

G("gr_by", "by 加动名词", 9, "上", 90,
  "能用 by 加动词的 -ing 形式说明做事方式。", "to_ing", [
    q("我靠读课文学英语。哪一句正确？", "I study English by reading the text.",
      ["I study English by read the text.", "I study English by to read the text.", "I study English with reading the text for by."],
      "by 后面用 reading。"),
    q("她靠听磁带提高发音。哪一句正确？", "She improves her pronunciation by listening to tapes.",
      ["She improves her pronunciation by listen to tapes.", "She improves her pronunciation by to listen to tapes.", "She improves her pronunciation by listened to tapes."],
      "by listening。"),
    q("by doing 表示什么？", "方式",
      ["过去的时间", "比较的对象", "被动的执行者一定是人"],
      "by 加动名词说明用什么方法。"),
    q("你可以靠小组合作来练习。哪一句正确？", "You can practice by working in a group.",
      ["You can practice by work in a group.", "You can practice by to work in a group.", "You can practice by worked in a group."],
      "by working。"),
])

F("fu_learn", "交流学习方法", 9, "上", 3,
  "能询问别人怎么学，并介绍自己的方法。", "func_school", [
    q("想问对方怎样学英语，哪一句合适？", "How do you study English?",
      ["How do you studies English?", "How are you study English?", "How you study English?"],
      "How do you study。"),
    q("你靠做笔记，应怎么说？", "I learn by taking notes.",
      ["I learn by take notes.", "I learn by to take notes.", "I learn with taking notes."],
      "by taking notes。"),
    q("What about reading aloud? 这句是在做什么？", "建议大声读",
      ["询问书的价格", "描述昨天的考试分数", "拒绝学习"],
      "What about 加动名词，用来提出一种方法。"),
    q("想说老师很有耐心，哪一句合适？", "The teacher is patient.",
      ["The teacher is patiently.", "The teacher are patient.", "The teacher is a patient to the book."],
      "is patient。"),
])

R("rw_learn", "读学习建议", 9, "上", 3,
  "读一段学习建议，找出方法和结果。", "read_detail", [
    q("Wei Fen studies English by reading aloud. She also learns new words by making word cards. 她怎样学英语？", "大声朗读",
      ["只靠看电视", "从不读书", "只在考试前睡觉"], "by reading aloud。"),
    q("Wei Fen studies English by reading aloud. She also learns new words by making word cards. 生词怎么记？", "做单词卡",
      ["把书扔掉", "只问一次", "不复习"], "by making word cards。"),
    q("Paul was not patient before. Now he studies by listening to tapes every night. 他现在每晚做什么？", "听磁带",
      ["写小说", "去博物馆", "不学习"], "listening to tapes every night。"),
    q("Paul was not patient before. Now he studies by listening to tapes. 哪一句和建议一致？", "Paul now learns by listening to tapes.",
      ["Paul still refuses to study.", "Wei Fen learns words only by sleeping.", "Paul has never listened to tapes."],
      "现在的方法是 listening to tapes。"),
])

V("vo_fest", "节日食物", 9, "上", 90,
  "认读 mooncake、lantern、stranger 和 relative。",
  [("mooncake", "月饼"), ("lantern", "灯笼"), ("stranger", "陌生人"), ("relative", "亲属")], "vocab9")

G("gr_that", "that 引导宾语从句", 9, "上", 3,
  "能用 that 连接看法和后面的陈述句，that 可以省略。", "clause_obj", [
    q("我认为月饼很好吃。哪一句正确？", "I think that mooncakes are delicious.",
      ["I think that mooncakes is delicious.", "I think mooncakes are delicious that.", "I think that are mooncakes delicious."],
      "that 后面用陈述语序，mooncakes 用 are。"),
    q("她相信故事是真的。哪一句正确？", "She believes that the story is true.",
      ["She believes that is the story true.", "She believes that the story true.", "She believes that the story are true."],
      "the story is true。"),
    q("that 引导的宾语从句用什么语序？", "陈述语序",
      ["疑问语序", "祈使语序", "倒装成 Are they"],
      "从句里主语在谓语前面。"),
    q("哪一句可以省略 that 后意思不变？", "I know that he likes lanterns.",
      ["I know that does he like lanterns.", "I know he likes lanterns that the end.", "That he likes lanterns I know are."],
      "I know he likes lanterns 可以省略 that。"),
])

G("gr_ifwhether", "if 与 whether 宾语从句", 9, "上", 3,
  "能用 if 或 whether 引导宾语从句，从句用陈述语序。", "clause_obj", [
    q("我不知道他会不会来。哪一句正确？", "I don't know if he will come.",
      ["I don't know if will he come.", "I don't know if he comes will.", "I don't know if does he come."],
      "if he will come，主语 he 在 will 前面。"),
    q("她在问是否要带灯笼。哪一句正确？", "She asks whether she should bring a lantern.",
      ["She asks whether should she bring a lantern.", "She asks whether does she bring a lantern.", "She asks whether she should brings a lantern."],
      "whether she should bring。"),
    q("宾语从句里，if 的意思是哪一个？", "是否",
      ["如果就一定会", "虽然", "以便"],
      "作宾语从句时，if 表示是否。"),
    q("哪一句的语序正确？", "I wonder whether the story is true.",
      ["I wonder whether is the story true.", "I wonder whether does the story true.", "I wonder whether the story true is it."],
      "whether the story is true。"),
])

F("fu_fest", "谈论节日", 9, "上", 90,
  "能说出节日吃什么、做什么。", "func_life", [
    q("想说中秋节人们赏月，哪一句合适？", "People admire the moon on Mid-Autumn Festival.",
      ["People admires the moon on Mid-Autumn Festival.", "People admire the moon in Mid-Autumn Festival.", "People admire moon the on festival."],
      "on Mid-Autumn Festival，谓语用 admire。"),
    q("想问对方是否喜欢月饼，哪一句合适？", "Do you like mooncakes?",
      ["Do you like mooncake are?", "Are you like mooncakes?", "Do you likes mooncakes?"],
      "Do you like。"),
    q("I wonder if they will have a party. 这句在说什么？", "我想知道他们是否会聚会",
      ["我确定他们昨天聚过", "如果聚会就一定取消", "我不关心聚会"],
      "wonder if 表示想知道是否。"),
    q("亲属们聚在一起，哪一句合适？", "The relatives get together.",
      ["The relatives gets together.", "The relative get together as a plural verb error.", "The relatives are get together."],
      "relatives 用 get。"),
])

R("rw_fest", "读中秋短文", 9, "上", 90,
  "读一段节日短文，找出食物和活动。", "read_detail", [
    q("Li Mei thinks that mooncakes are delicious. Her family admires the moon at night. 她觉得月饼怎么样？", "很好吃",
      ["很难吃", "太咸", "短文没说"], "mooncakes are delicious。"),
    q("Li Mei thinks that mooncakes are delicious. Her family admires the moon at night. 晚上做什么？", "赏月",
      ["赛龙舟", "打扫卫生", "去医院"], "admires the moon。"),
    q("I don't know whether Tom will come. He is in another city. 确定 Tom 会来吗？", "不确定",
      ["确定会来", "他已经到了", "他不喜欢灯笼所以不来是写明的"],
      "don't know whether。"),
    q("Her family admires the moon at night. 哪一句和短文一致？", "The family watches the moon at night.",
      ["The family eats breakfast at night only.", "Tom has already arrived.", "Li Mei hates mooncakes."],
      "晚上赏月。"),
])

V("vo_polite", "公共场所", 9, "上", 90,
  "认读 restroom、stamp、postcard 和 politely。",
  [("restroom", "洗手间"), ("stamp", "邮票"), ("postcard", "明信片"), ("politely", "礼貌地")], "vocab9")

G("gr_whobj", "疑问词宾语从句", 9, "上", 4,
  "能把特殊疑问句改成陈述语序，放进宾语从句。", "clause_obj", [
    q("请问洗手间在哪里。哪一句正确？", "Could you tell me where the restroom is?",
      ["Could you tell me where is the restroom?", "Could you tell me where the restroom is it?", "Could you tell me where does the restroom?"],
      "where the restroom is，be 动词放在主语后面。"),
    q("我想知道银行在哪里。哪一句正确？", "I want to know where the bank is.",
      ["I want to know where is the bank.", "I want to know where the bank is there.", "I want to know the bank where is."],
      "where the bank is。"),
    q("她问我什么时候出发。哪一句正确？", "She asks me when we leave.",
      ["She asks me when do we leave.", "She asks me when we do leave tomorrow the question order.", "She asks me when leave we."],
      "when we leave，不用 do we。"),
    q("宾语从句为什么不用疑问语序？", "它是陈述的一部分，不是直接问句",
      ["因为不能用 where", "因为必须省略主语", "因为只能用过去时"],
      "嵌入后主语仍在谓语前面。"),
])

F("fu_polite", "礼貌问路", 9, "上", 90,
  "能礼貌地问路，并听懂直接问句和间接问句。", "func_view", [
    q("想礼貌地问邮局在哪里，哪一句合适？", "Could you please tell me where the post office is?",
      ["Could you please tell me where is the post office?", "Tell me where is the post office now.", "Could you please tell me where the post office?"],
      "礼貌请求加陈述语序。"),
    q("直接问句哪一句正确？", "Where is the restroom?",
      ["Where the restroom is?", "Where is restroom the?", "Where the restroom is it?"],
      "直接提问时 is 可以放在 where 后面。"),
    q("买一张邮票，哪一句合适？", "I need one stamp.",
      ["I need one stamps.", "I need a stamps.", "I need an stamp."],
      "one stamp。"),
    q("Excuse me, I wonder if you can help me. 说话人的态度是什么？", "礼貌",
      ["生气地命令", "已经结束对话", "在描述过去的错误"],
      "Excuse me 和 wonder if 都比较委婉。"),
])

R("rw_polite", "读问路对话", 9, "上", 90,
  "读一段问路对话，找出地点。", "read_detail", [
    q("A: Could you tell me where the restroom is? B: Go along the hall and turn left. 问路人要去哪里？", "洗手间",
      ["邮局", "银行", "博物馆"], "where the restroom is。"),
    q("A: Could you tell me where the restroom is? B: Go along the hall and turn left. 怎么走？", "沿走廊走，然后左转",
      ["右转上楼", "往回走", "坐电梯到三楼"], "along the hall and turn left。"),
    q("Mary asks where she can buy a stamp. The clerk says the shop is next to the library. 邮票在哪里买？", "图书馆旁边的商店",
      ["洗手间里", "邮局楼上没有商店", "家里"], "next to the library。"),
    q("The clerk says the shop is next to the library. 哪一句和对话一致？", "The stamp shop is beside the library.",
      ["The restroom is next to the library in this second text.", "Mary already has a stamp.", "The clerk tells her to turn right for the restroom."],
      "商店在图书馆旁边。"),
])

V("vo_change9", "今昔变化", 9, "上", 1,
  "认读 humorous、silent、score 和 background。",
  [("humorous", "幽默的"), ("silent", "沉默的"), ("score", "分数"), ("background", "背景")], "vocab9")

G("gr_used", "used to 表示过去习惯", 9, "上", 90,
  "能用 used to 加动词原形表示过去常常、现在不再如此。", "past", [
    q("我以前怕黑。哪一句正确？", "I used to be afraid of the dark.",
      ["I used to was afraid of the dark.", "I use to be afraid of the dark.", "I used to being afraid of the dark."],
      "used to be。"),
    q("她以前很沉默。哪一句正确？", "She used to be silent.",
      ["She used to silent.", "She used to is silent.", "She use to be silent."],
      "used to be silent。"),
    q("used to 表示什么？", "过去常常，现在通常已改变",
      ["正在做", "将来一定做", "从未做过"],
      "used to 把过去和现在作对比。"),
    q("你以前弹钢琴吗？哪一句正确？", "Did you use to play the piano?",
      ["Did you used to play the piano?", "Did you use to played the piano?", "Use you to play the piano?"],
      "疑问句里用 Did you use to。"),
])

F("fu_used", "比较过去和现在", 9, "上", 1,
  "能说出自己或别人过去什么样、现在什么样。", "func_view", [
    q("想说以前怕黑，现在不怕了，哪一句合适？", "I used to be afraid of the dark, but I am not now.",
      ["I used to be afraid of the dark, but I am not now yesterday.", "I use to be afraid of the dark, but now I am not.", "I used to afraid of the dark, but I am not now."],
      "used to be，but I am not now。"),
    q("他现在更幽默了。哪一句合适？", "He is more humorous than he used to be.",
      ["He is more humorous than he used to was.", "He is humorouser than he used to be.", "He is more humorouser than he use to be."],
      "than he used to be。"),
    q("What did you use to do after school? 这句在问什么？", "你过去放学后常常做什么",
      ["你现在正在做什么", "你明天放学做什么", "你的分数是多少"],
      "did you use to do 问过去的习惯。"),
    q("想说分数比以前高，哪一句合适？", "My score is higher than it used to be.",
      ["My score is higher than it used to was.", "My score is more high than it used to be.", "My score is highest than it used to be."],
      "higher than it used to be。"),
])

R("rw_used", "读变化短文", 9, "上", 1,
  "读一段变化，对比过去和现在。", "read_detail", [
    q("Andy used to be silent. Now he is humorous and talks a lot. 他以前怎么样？", "很沉默",
      ["很幽默", "很吵", "分数很高"], "used to be silent。"),
    q("Andy used to be silent. Now he is humorous and talks a lot. 他现在怎么样？", "幽默，话很多",
      ["仍然一言不发", "害怕说话", "短文没说现在"], "Now he is humorous。"),
    q("Tina used to hate tests. Her score is higher now. 分数怎样了？", "比以前高",
      ["比以前低", "没有变化", "短文没写分数"], "score is higher now。"),
    q("Tina used to hate tests. 哪一句和短文一致？", "Tina did not like tests before.",
      ["Tina still hates talking and is silent.", "Andy used to be humorous.", "Tina's score is lower now."],
      "used to hate tests。"),
])

V("vo_material", "材料", 9, "上", 90,
  "认读 cotton、steel、produce 和 widely。",
  [("cotton", "棉"), ("steel", "钢"), ("produce", "生产"), ("widely", "广泛地")], "vocab9")

G("gr_pass", "一般现在时被动语态", 9, "上", 5,
  "能用 am、is、are 加过去分词表示现在的被动。", "passive", [
    q("这件衬衫是棉做的。哪一句正确？", "This shirt is made of cotton.",
      ["This shirt is made from cotton as a visible cloth error.", "This shirt is make of cotton.", "This shirt made of cotton."],
      "is made of cotton。看得见的材料用 of。"),
    q("茶叶种在中国很多地方。哪一句正确？", "Tea is grown in many places in China.",
      ["Tea is grow in many places in China.", "Tea grows by people in many places as a passive form.", "Tea is grown by in China."],
      "is grown。"),
    q("一般现在时被动语态的结构是哪一个？", "am、is 或 are 加过去分词",
      ["do 加动词原形", "have 加动词 ing", "will 加过去式"],
      "be 的现在形式加 done。"),
    q("这些包是钢做的吗？哪一句正确？", "Are these bags made of steel?",
      ["Do these bags made of steel?", "Are these bags make of steel?", "Are these bags made from steel if the steel is still clearly steel?"],
      "Are ... made of。"),
])

F("fu_made", "询问由什么制成", 9, "上", 90,
  "能询问物品的材料和产地。", "func_life", [
    q("想问衬衫是什么做的，哪一句合适？", "What is the shirt made of?",
      ["What is the shirt made from of?", "What does the shirt made of?", "What is the shirt make of?"],
      "What is ... made of。"),
    q("它产于中国，应怎么说？", "It is produced in China.",
      ["It is produce in China.", "It produced in China.", "It is produced by China people the word order."],
      "is produced in China。"),
    q("Where is tea grown? 这句在问什么？", "茶叶种在哪里",
      ["谁喜欢喝茶", "茶多少钱", "茶是什么颜色"],
      "Where is ... grown 问产地。"),
    q("这种材料被广泛使用，哪一句合适？", "This material is widely used.",
      ["This material is widely use.", "This material widely is used.", "This material is wide used."],
      "is widely used。"),
])

R("rw_made", "读产品介绍", 9, "上", 90,
  "读一段介绍，找出材料和产地。", "read_detail", [
    q("The shirt is made of cotton. It is produced in China. 衬衫是什么做的？", "棉",
      ["钢", "玻璃", "纸"], "made of cotton。"),
    q("The shirt is made of cotton. It is produced in China. 在哪里生产？", "中国",
      ["法国", "日本", "短文没说"], "produced in China。"),
    q("These forks are made of steel. They are used widely in restaurants. 叉子是什么做的？", "钢",
      ["棉", "木头", "银子以外的金"], "made of steel。"),
    q("These forks are made of steel. 哪一句和介绍一致？", "The forks are steel products.",
      ["The forks are made of cotton.", "The shirt is made of steel.", "Tea is grown in the shirt factory."],
      "forks are made of steel。"),
])

V("vo_invent", "发明物", 9, "上", 5,
  "认读 inventor、mention、website 和 daily。",
  [("inventor", "发明家"), ("mention", "提到"), ("website", "网站"), ("daily", "每日的")], "vocab9")

G("gr_passpast", "一般过去时被动语态", 9, "上", 5,
  "能用 was 或 were 加过去分词表示过去的被动。", "passive", [
    q("电话是贝尔发明的。哪一句正确？", "The telephone was invented by Bell.",
      ["The telephone was invent by Bell.", "The telephone is invented by Bell in the past sentence.", "The telephone invented by Bell."],
      "was invented by。"),
    q("这些发明是什么时候被提到的？哪一句正确？", "When were the inventions mentioned?",
      ["When did the inventions mentioned?", "When were the inventions mention?", "When was the inventions mentioned?"],
      "复数 inventions 用 were mentioned。"),
    q("一般过去时被动语态的结构是哪一个？", "was 或 were 加过去分词",
      ["is 加动词 ing", "have 加过去分词", "did 加过去分词"],
      "过去的 be 加 done。"),
    q("网站是去年建立的。哪一句正确？", "The website was set up last year.",
      ["The website was set up next year.", "The website set up last year by nobody the active error.", "The website was set up last year by it."],
      "was set up last year。"),
])

F("fu_invent", "询问发明时间", 9, "上", 5,
  "能询问某物是何时、被谁发明的。", "func_view", [
    q("想问拉链是何时发明的，哪一句合适？", "When was the zipper invented?",
      ["When was the zipper invent?", "When did the zipper invented?", "When was the zipper invented by time?"],
      "When was ... invented。"),
    q("它是偶然发明的，应怎么说？", "It was invented by accident.",
      ["It was invented by an accident person only.", "It invented by accident.", "It was invent by accident."],
      "was invented by accident。"),
    q("Who was it invented by? 这句在问什么？", "它是谁发明的",
      ["它现在卖多少钱", "它是什么颜色", "它明天会不会坏"],
      "Who ... by 问发明者。"),
    q("想说人们每天使用它，哪一句合适？", "People use it in daily life.",
      ["People uses it in daily life.", "People use it in daily life yesterday the tense.", "People are use it in daily life."],
      "use it in daily life。"),
])

R("rw_invent", "读发明介绍", 9, "上", 5,
  "读一段发明介绍，找出发明者和用途。", "read_detail", [
    q("The telephone was invented by Bell. It is used for talking to people far away. 谁发明了电话？", "贝尔",
      ["爱迪生", "一位学生", "短文没说"], "invented by Bell。"),
    q("The telephone was invented by Bell. It is used for talking to people far away. 电话用来做什么？", "和远处的人通话",
      ["煮茶叶", "印书", "搬山"], "talking to people far away。"),
    q("Potato chips were invented by accident. A cook made them in a restaurant. 怎么发明的？", "偶然",
      ["按计划研究了十年", "在网站上投票", "短文没说"], "by accident。"),
    q("Potato chips were invented by accident. 哪一句和介绍一致？", "Potato chips were an accidental invention.",
      ["Bell invented potato chips.", "The telephone was invented by a cook.", "Potato chips were invented on purpose in this text."],
      "by accident 就是偶然发明。"),
])

V("vo_teen", "青少年规则", 9, "上", 90,
  "认读 license、safety、society 和 choice。",
  [("license", "执照"), ("safety", "安全"), ("society", "社会"), ("choice", "选择")], "vocab9")

G("gr_allow", "be allowed to", 9, "上", 90,
  "能用 be allowed to 表示被允许做某事。", "passive", [
    q("青少年应该被允许选择自己的衣服。哪一句正确？", "Teenagers should be allowed to choose their own clothes.",
      ["Teenagers should be allowed choose their own clothes.", "Teenagers should be allowed to choosing their own clothes.", "Teenagers should allowed to choose their own clothes."],
      "be allowed to choose。"),
    q("我不被允许熬夜。哪一句正确？", "I am not allowed to stay up late.",
      ["I am not allowed stay up late.", "I am not allowed to staying up late.", "I not allowed to stay up late."],
      "am not allowed to stay。"),
    q("be allowed to 的意思是哪一个？", "被允许",
      ["不得不拒绝", "过去习惯", "正在允许别人"],
      "allowed 是被动，to 后面接动作。"),
    q("十六岁的学生被允许开车吗？哪一句是正确问句？", "Are sixteen-year-olds allowed to drive?",
      ["Do sixteen-year-olds allowed to drive?", "Are sixteen-year-olds allowed drive?", "Are sixteen-year-olds allow to drive?"],
      "Are ... allowed to drive。"),
])

F("fu_allow", "讨论是否允许", 9, "上", 90,
  "能对校规发表同意或不同意的看法。", "func_view", [
    q("你不同意十六岁开车，哪一句合适？", "I don't think sixteen-year-olds should be allowed to drive.",
      ["I don't think sixteen-year-olds should be allowed drive.", "I am not think they should be allowed to drive.", "I don't think they should allowed to drive."],
      "don't think ... should be allowed to drive。"),
    q("安全重要，哪一句合适？", "Safety is important.",
      ["Safety are important.", "Safety is importance.", "The safety is important than."],
      "Safety is important。"),
    q("想说这是他们自己的选择，哪一句合适？", "It is their own choice.",
      ["It is their own choices one.", "It are their own choice.", "It is they own choice."],
      "their own choice。"),
    q("I agree with the rule. 这句表示什么？", "同意这条规则",
      ["这条规则不存在", "我还没读规则", "我要求取消所有规则以外的同意"],
      "agree with 表示同意。"),
])

R("rw_allow", "读规则意见", 9, "上", 90,
  "读一段讨论，找出谁被允许做什么。", "read_detail", [
    q("Students are not allowed to use phones in class. They are allowed to use them after school. 课上可以用手机吗？", "不可以",
      ["可以", "只可以听歌", "短文没说"], "are not allowed to use phones in class。"),
    q("Students are not allowed to use phones in class. They are allowed to use them after school. 放学后呢？", "可以",
      ["不可以", "只能看不能碰", "必须上交"], "allowed to use them after school。"),
    q("Anna thinks sixteen-year-olds should be allowed to choose their clothes. Her father disagrees. 谁不同意？", "她的父亲",
      ["Anna", "老师已经同意开车", "两个人都同意"], "Her father disagrees。"),
    q("Her father disagrees. 哪一句和短文一致？", "Anna and her father do not have the same opinion.",
      ["Both of them disagree with choice.", "Students may use phones in class.", "Anna's father agrees with her."],
      "父亲不同意 Anna。"),
])

V("vo_owner", "物品主人", 9, "上", 90,
  "认读 whose、attend、valuable 和 picnic。",
  [("whose", "谁的"), ("attend", "参加"), ("valuable", "贵重的"), ("picnic", "野餐")], "vocab9")

G("gr_mustbe", "must 表示推测", 9, "上", 90,
  "能用 must 表示很有把握的肯定推测，用 can't 表示否定推测。", "modal", [
    q("吉他上面有 Carla 的名字，一定是她的。哪一句正确？", "The guitar must be Carla's.",
      ["The guitar must is Carla's.", "The guitar must be Carla.", "The guitar can be Carla's as a weak guess in this sure case."],
      "把握大时用 must be。"),
    q("他不可能在野餐，我看见他在图书馆。哪一句正确？", "He can't be at the picnic.",
      ["He must be at the picnic although I see him in the library.", "He can't is at the picnic.", "He must not to be at the picnic."],
      "有相反证据时用 can't be。"),
    q("must 在这里表示什么？", "很有把握的推测",
      ["过去的义务已经完成", "礼貌的请求", "正在进行的被动"],
      "must be 表示一定是。"),
    q("这本贵重的书是谁的？名字是 Tom。哪一句合适？", "It must belong to Tom.",
      ["It must belongs to Tom.", "It must belong Tom.", "It can't belong to Tom because the name is Tom."],
      "must belong to。"),
])

F("fu_guess", "推测物品归属", 9, "上", 90,
  "能根据线索推测东西是谁的。", "func_view", [
    q("想问这是谁的书包，哪一句合适？", "Whose backpack is this?",
      ["Who's backpack is this owner?", "Whose backpack this is?", "Who backpack is this?"],
      "Whose backpack is this。"),
    q("你很确定是 Mary 的，应怎么说？", "It must be Mary's.",
      ["It must Mary's.", "It can be Mary's if we are completely sure.", "It must is Mary's."],
      "must be Mary's。"),
    q("CD 上是流行乐，Mary 喜欢流行乐。哪一句合适？", "It must belong to Mary.",
      ["It must belong Mary.", "It must belongs to Mary.", "It can't belong to Mary because she likes pop."],
      "must belong to Mary。"),
    q("想说他在参加野餐，所以不在这里，哪一句合适？", "He must be attending the picnic.",
      ["He must attending the picnic.", "He must be attend the picnic.", "He can be attending the picnic as a certain fact."],
      "must be attending。"),
])

R("rw_guess", "读推测短文", 9, "上", 90,
  "读一段推理，找出物品的主人。", "read_detail", [
    q("The notebook has Anna's name on it. It must be hers. 笔记本是谁的？", "Anna 的",
      ["Tom 的", "老师的", "无人认领"], "Anna's name，must be hers。"),
    q("The toy truck can't be Mary's. She does not like trucks. 玩具卡车是 Mary 的吗？", "不是",
      ["一定是", "可能是因为她喜欢", "短文没说"], "can't be Mary's。"),
    q("Somebody is attending a picnic. The volleyball must belong to that person. 排球和谁有关？", "正在参加野餐的那个人",
      ["Anna 的笔记本", "Mary 的卡车", "图书馆"], "belong to that person。"),
    q("The notebook has Anna's name on it. 哪一句和短文一致？", "Anna owns the notebook.",
      ["Mary owns the toy truck.", "The volleyball is Anna's notebook.", "The notebook has no name."],
      "名字在笔记本上。"),
])

V("vo_music", "音乐类型", 9, "上", 7,
  "认读 prefer、lyrics、Australian 和 electronic。",
  [("prefer", "更喜欢"), ("lyrics", "歌词"), ("Australian", "澳大利亚的"), ("electronic", "电子的")], "vocab9")

G("gr_attr", "定语从句", 9, "上", 7,
  "能用 that、who 或 which 修饰前面的人或物。", "clause_attr", [
    q("我喜欢能跟着跳舞的音乐。哪一句正确？", "I like music that I can dance to.",
      ["I like music who I can dance to.", "I like music that I can dance to it.", "I like music which I can dance."],
      "music 是物，用 that，dance to 的 to 保留。"),
    q("正在说话的那个人是我的老师。哪一句正确？", "The man who is talking is my teacher.",
      ["The man which is talking is my teacher.", "The man who talking is my teacher.", "The man who is talking he is my teacher."],
      "人用 who，从句里不再重复 he。"),
    q("这是我昨天买的书。哪一句正确？", "This is the book which I bought yesterday.",
      ["This is the book who I bought yesterday.", "This is the book which I bought it yesterday.", "This is the book which I buy yesterday."],
      "物可用 which，bought 是过去式，不重复 it。"),
    q("修饰人时，哪一个关系词最合适？", "who",
      ["what", "how", "whosever"],
      "who 指人。"),
])

F("fu_music", "说明喜欢的音乐", 9, "上", 7,
  "能说出自己喜欢什么音乐，并说明原因。", "func_life", [
    q("想说你更喜欢歌词清楚的歌，哪一句合适？", "I prefer songs that have clear lyrics.",
      ["I prefer songs who have clear lyrics.", "I prefer songs that they have clear lyrics.", "I prefer songs which has clear lyrics."],
      "songs that have。"),
    q("想问对方喜欢哪种音乐，哪一句合适？", "What kind of music do you like?",
      ["What kind of music do you like it?", "What kind of music you like?", "What kind of music are you like?"],
      "What kind of music do you like。"),
    q("我喜欢能跟着唱的音乐。哪一句合适？", "I like music that I can sing along with.",
      ["I like music that I can sing along.", "I like music who I can sing along with.", "I like music that can I sing along with."],
      "sing along with。"),
    q("He likes Australian singers. 这句说明什么？", "他喜欢澳大利亚歌手",
      ["他是澳大利亚人所以不唱歌", "他不喜欢歌手", "他只喜欢电子产品"],
      "Australian singers。"),
])

R("rw_music", "读音乐偏好", 9, "上", 7,
  "读一段偏好，找出谁喜欢什么音乐。", "read_detail", [
    q("Cindy likes music that she can dance to. She prefers songs with clear lyrics. 她喜欢什么样的音乐？", "可以跟着跳舞、歌词清楚的",
      ["没有歌词的", "只能安静听不能跳舞的古典", "短文没说"], "dance to，clear lyrics。"),
    q("Tony likes singers who write their own songs. He does not like electronic music. 他喜欢什么样的歌手？", "自己写歌的歌手",
      ["只播放电子音乐的人", "不写作的人", "短文没说"], "who write their own songs。"),
    q("Tony does not like electronic music. 他喜欢电子音乐吗？", "不喜欢",
      ["喜欢", "只在晚会上喜欢", "比 Cindy 更喜欢"], "does not like。"),
    q("Cindy likes music that she can dance to. 哪一句和短文一致？", "Cindy likes dance music.",
      ["Tony likes electronic music.", "Cindy hates clear lyrics.", "Tony likes singers who never write songs."],
      "能跟着跳舞的音乐。"),
])

# 以下四点是上一轮八年级改挂，本轮不改课号：社交习俗、说明该怎么做、读习俗说明
# 在八年级下册第6单元；be supposed to 挂「八年级下册 待核」。
V("vo_custom", "社交习俗", 8, "下", 6,
  "认读 bow、kiss、greet 和 manner。",
  [("bow", "鞠躬"), ("kiss", "亲吻"), ("greet", "问候"), ("manner", "礼仪")], "vocab9")

G("gr_supposed", "be supposed to", 8, "下", 90,
  "能用 be supposed to 表示按习俗或规则应该做的事。", "modal", [
    q("你应该握手。哪一句正确？", "You are supposed to shake hands.",
      ["You are supposed shake hands.", "You are supposed to shaking hands.", "You supposed to shake hands."],
      "are supposed to shake。"),
    q("在那里不应该大声说话。哪一句正确？", "You are not supposed to talk loudly there.",
      ["You are not supposed talk loudly there.", "You are not supposed to talking loudly there.", "You not supposed to talk loudly there."],
      "are not supposed to talk。"),
    q("be supposed to 的意思接近哪一个？", "应该",
      ["曾经", "已经被允许离开", "正在鞠躬"],
      "它表示按规矩应当。"),
    q("第一次见面他们应该鞠躬吗？哪一句正确？", "Are they supposed to bow when they meet for the first time?",
      ["Do they supposed to bow when they meet for the first time?", "Are they supposed bow when they meet?", "Are they suppose to bow when they meet?"],
      "Are they supposed to bow。"),
])

F("fu_custom", "说明该怎么做", 8, "下", 6,
  "能介绍一个地方见面时该怎么打招呼。", "func_view", [
    q("在中国，朋友见面常常握手。哪一句合适？", "In China, people are supposed to shake hands.",
      ["In China, people are supposed shake hands.", "In China, people supposed to shake hands.", "In China, people are supposed to shaking hands."],
      "are supposed to shake hands。"),
    q("想问在日本该怎么问候，哪一句合适？", "How are people supposed to greet in Japan?",
      ["How do people supposed to greet in Japan?", "How are people supposed greet in Japan?", "How people are supposed to greet in Japan?"],
      "How are people supposed to greet。"),
    q("迟到是不礼貌的，哪一句合适？", "It is impolite to be late.",
      ["It is impolite be late.", "It is impolite to being late.", "It is impolite to late."],
      "impolite to be late。"),
    q("We kissed when we met. 这句是在说什么？", "见面时我们亲吻了",
      ["我们拒绝问候", "我们正在学习鞠躬的单词", "我们没有见面"],
      "kissed when we met。"),
])

R("rw_custom", "读习俗说明", 8, "下", 6,
  "读一段习俗说明，找出该做和不该做的事。", "read_detail", [
    q("In this country, you are supposed to bow when you meet someone. You are not supposed to kiss. 见面应该做什么？", "鞠躬",
      ["亲吻", "握手以外没有写鞠躬", "什么都不做"], "supposed to bow。"),
    q("In this country, you are supposed to bow when you meet someone. You are not supposed to kiss. 应该亲吻吗？", "不应该",
      ["应该", "只对陌生人亲吻", "短文没说"], "not supposed to kiss。"),
    q("Being on time is important. It is impolite to be late for a meeting. 开会迟到怎样？", "不礼貌",
      ["被鼓励", "没有关系", "是一种问候"], "impolite to be late。"),
    q("You are supposed to bow. 哪一句和说明一致？", "Bowing is the expected greeting.",
      ["Kissing is required.", "Being late is polite.", "People should not bow."],
      "应该鞠躬。"),
])

V("vo_emotion", "情绪反应", 9, "上", 90,
  "认读 friendship、king、pale 和 queen。",
  [("friendship", "友谊"), ("king", "国王"), ("pale", "苍白的"), ("queen", "王后")], "vocab9")

G("gr_make", "make 加宾语加动词原形", 9, "上", 90,
  "能用 make somebody do 或 make somebody 加形容词。", "to_ing", [
    q("悲伤的电影让我哭。哪一句正确？", "Sad movies make me cry.",
      ["Sad movies make me to cry.", "Sad movies make me crying.", "Sad movies make me cried."],
      "make me cry，cry 用原形。"),
    q("这个消息让他高兴。哪一句正确？", "The news made him happy.",
      ["The news made him happily.", "The news made him to happy.", "The news made he happy."],
      "made him happy，happy 是形容词。"),
    q("make somebody do 里的 do 用什么形式？", "动词原形",
      ["to 加动词", "动词 ing", "过去式"],
      "make 后面的动词不带 to。"),
    q("国王的决定让王后很苍白。哪一句正确？", "The king's decision made the queen pale.",
      ["The king's decision made the queen to pale.", "The king's decision made the queen palely.", "The king's decision made the queen pales."],
      "made the queen pale。"),
])

F("fu_feel9", "表达电影感受", 9, "上", 90,
  "能说出一部电影让自己有什么感受。", "func_view", [
    q("想说这部电影让你想哭，哪一句合适？", "The movie makes me want to cry.",
      ["The movie makes me to want to cry.", "The movie makes me wanting to cry.", "The movie makes me want cry."],
      "makes me want to cry。"),
    q("想问这部电影怎么样，哪一句合适？", "What do you think of the movie?",
      ["What do you think the movie of?", "How do you think of the movie is?", "What are you think of the movie?"],
      "What do you think of。"),
    q("友谊让她快乐，哪一句合适？", "Friendship makes her happy.",
      ["Friendship makes her happily.", "Friendship make her happy.", "Friendship makes she happy."],
      "makes her happy。"),
    q("The king looks pale. 这句说明什么？", "国王看上去脸色苍白",
      ["国王很高兴", "王后在笑", "电影还没开始"],
      "looks pale。"),
])

R("rw_movie", "读观后感", 9, "上", 90,
  "读一段观后感，找出电影给人的感受。", "read_detail", [
    q("The sad movie made Amy cry. It also made her think about friendship. 电影让 Amy 怎样了？", "哭了，并想到友谊",
      ["睡着了", "离开了电影院而且没有哭", "开始笑个不停"], "made Amy cry，think about friendship。"),
    q("The sad movie made Amy cry. 她哭是因为什么？", "这部悲伤的电影",
      ["一个笑话", "国王请她吃饭", "短文没说原因"], "sad movie made Amy cry。"),
    q("The story of the king and the queen made Ben sleepy. He did not cry. Ben 哭了吗？", "没有",
      ["哭了", "和 Amy 一起哭", "短文没说"], "did not cry。"),
    q("The story made Ben sleepy. 哪一句和观后感一致？", "Ben felt sleepy because of the story.",
      ["Ben cried a lot.", "Amy did not think about friendship.", "The queen made Amy sleepy in the first text."],
      "made Ben sleepy。"),
])

V("vo_unexp", "意外事件", 9, "上", 90,
  "认读 unexpected、backpack、block 和 burn。",
  [("unexpected", "出乎意料的"), ("backpack", "背包"), ("block", "街区"), ("burn", "燃烧")], "vocab9")

G("gr_ppast", "过去完成时", 9, "上", 90,
  "能用 had 加过去分词，表示在过去某一动作之前已经发生的事。", "pastperf", [
    q("我到达之前，火车已经离开了。哪一句正确？", "The train had left when I arrived.",
      ["The train has left when I arrived.", "The train had left when I arrive.", "The train left when I had arrived as the earlier event."],
      "先离开用 had left，后到达用 arrived。"),
    q("到我起床时，哥哥已经走了。哪一句正确？", "By the time I got up, my brother had left.",
      ["By the time I got up, my brother has left.", "By the time I got up, my brother had leave.", "By the time I get up, my brother had left."],
      "had left 发生在 got up 之前。"),
    q("过去完成时的结构是哪一个？", "had 加过去分词",
      ["have 加动词 ing", "was 加动词 ing", "would 加动词原形"],
      "had done。"),
    q("她发现背包烧了，那是在她回来之前发生的。哪一句正确？", "She found that her backpack had burned.",
      ["She found that her backpack has burned.", "She found that her backpack had burn.", "She had found that her backpack burned first after she found it."],
      "burned 发生在 found 之前，用 had burned。"),
])

F("fu_unexp", "叙述意外经过", 9, "上", 90,
  "能按先后顺序说出一件意外。", "func_view", [
    q("想说你迟到是因为闹钟没响，哪一句合适？", "I was late because my alarm had not gone off.",
      ["I was late because my alarm has not gone off.", "I was late because my alarm had not went off.", "I was late because my alarm did not had gone off."],
      "had not gone off 在迟到之前。"),
    q("想说这完全出乎意料，哪一句合适？", "It was totally unexpected.",
      ["It was totally unexpectedness.", "It were totally unexpected.", "It was total unexpected."],
      "was totally unexpected。"),
    q("By the time I reached the airport, the plane had taken off. 飞机何时起飞？", "在我到达机场之前",
      ["在我到达之后", "和我同时", "第二天"],
      "had taken off 早于 reached。"),
    q("背包忘在家里了，哪一句合适？", "I had left my backpack at home.",
      ["I have left my backpack at home before I noticed yesterday.", "I had leave my backpack at home.", "I left my backpack at home after I found it missing first."],
      "had left 表示发现之前已经忘了。"),
])

R("rw_unexp", "读意外故事", 9, "上", 90,
  "读一段意外，判断哪件事发生得更早。", "read_detail", [
    q("By the time Carl woke up, the bus had already left. He had forgotten to set the alarm. 哪件事更早？", "他忘记设闹钟，公共汽车也先离开了",
      ["他先醒来然后车才离开", "车还在等他", "闹钟先响了"], "had forgotten，had already left，然后才 woke up。"),
    q("By the time Carl woke up, the bus had already left. 他醒来时车还在吗？", "已经离开了",
      ["还在门口", "还没来", "短文没说"], "had already left。"),
    q("When Nina got home, she found the kitchen had burned. The fire was unexpected. 她到家时发现什么？", "厨房已经烧过了",
      ["厨房正在新建", "火还没开始", "背包在燃烧但厨房没事"], "kitchen had burned。"),
    q("The fire was unexpected. 哪一句和故事一致？", "Nina did not expect the fire.",
      ["Carl caught the bus.", "The kitchen burned after Nina arrived.", "Carl had set the alarm."],
      "unexpected 说明她没有料到。"),
])

V("vo_earth", "环境保护", 9, "上", 90,
  "认读 litter、bottom、coal 和 plastic。",
  [("litter", "垃圾"), ("bottom", "底部"), ("coal", "煤"), ("plastic", "塑料")], "vocab9")

G("gr_review", "时态选择", 9, "上", 90,
  "能根据时间状语在现在、过去、将来、进行和完成时之间选择。", "tense", [
    q("我通常步行上学。哪一句正确？", "I usually walk to school.",
      ["I usually walked to school every present day.", "I am usually walk to school.", "I have walk to school every day."],
      "usually 说明习惯，用一般现在时 walk。"),
    q("昨天我步行上学了。哪一句正确？", "I walked to school yesterday.",
      ["I walk to school yesterday.", "I have walked to school yesterday.", "I was walk to school yesterday."],
      "yesterday 用 walked。"),
    q("现在我正在步行上学。哪一句正确？", "I am walking to school now.",
      ["I walk to school now as a finished past action.", "I have walked to school now in this ongoing sentence.", "I am walk to school now."],
      "now 而且动作正在进行，用 am walking。"),
    q("到上月底，他们已经种了一千棵树。哪一句正确？", "They had planted one thousand trees by the end of last month.",
      ["They have planted one thousand trees by the end of last month.", "They planted one thousand trees by the end of next month.", "They had plant one thousand trees by the end of last month."],
      "by the end of last month 是过去的截止时间，用 had planted。"),
])

F("fu_earth", "谈论环保做法", 9, "上", 90,
  "能说出为保护环境可以做的事。", "func_view", [
    q("想说不该乱扔垃圾，哪一句合适？", "We should not throw litter on the ground.",
      ["We should not to throw litter on the ground.", "We should not throwing litter on the ground.", "We not should throw litter on the ground."],
      "should not throw。"),
    q("想说塑料对海洋有害，哪一句合适？", "Plastic is bad for the ocean.",
      ["Plastic are bad for the ocean.", "Plastic is badly for the ocean.", "Plastic is bad to the ocean bottom word."],
      "is bad for。"),
    q("我们可以少用煤。哪一句合适？", "We can use less coal.",
      ["We can use less coals as a countable pile.", "We can to use less coal.", "We can using less coal."],
      "can use less coal。"),
    q("The river was clean before. Now there is litter at the bottom. 这句在对比什么？", "以前干净，现在底部有垃圾",
      ["河一直很干净", "垃圾已经全部清除", "煤变成了塑料"],
      "was clean 和 now there is litter。"),
])

R("rw_earth", "读环保倡议", 9, "上", 90,
  "读一段倡议，找出问题和做法。", "read_detail", [
    q("Last year the river was clean. Now people throw plastic into it. 现在人们把什么扔进河里？", "塑料",
      ["煤块做成的船", "树", "短文没说"], "throw plastic into it。"),
    q("Last year the river was clean. Now people throw plastic into it. 去年河怎么样？", "干净",
      ["充满垃圾", "干涸", "短文没说"], "was clean。"),
    q("We should pick up litter and use less plastic. 倡议要我们做什么？", "捡垃圾并少用塑料",
      ["多烧煤", "把垃圾留在底部", "关闭所有河流"], "pick up litter and use less plastic。"),
    q("We should pick up litter. 哪一句和倡议一致？", "People are asked to collect litter.",
      ["People should throw more plastic.", "The river was dirty last year.", "Coal is the only topic."],
      "pick up litter。"),
])

R("rw_cloze9", "完形填空", 9, "上", 90,
  "能根据上下文补全短文中的词。", "read_cloze", [
    q("The city ___ dirty ten years ago. People have planted trees since then. 横线处选哪一个？", "was",
      ["is", "were", "has"], "ten years ago 用 was。city 是单数。"),
    q("We ___ not supposed to throw plastic into the river. 横线处选哪一个？", "are",
      ["is", "be", "were yesterday now"], "we 后面用 are supposed。"),
    q("By the time the students arrived, the volunteers ___ already cleaned the park. 横线处选哪一个？", "had",
      ["have", "has", "did"], "arrived 之前已经打扫，用 had cleaned。"),
    q("Music that we can dance ___ makes the trip fun. 横线处选哪一个？", "to",
      ["who", "for to", "which it"], "dance to music，关系词后保留 to。"),
])

V("vo_memory", "毕业回忆", 9, "上", 90,
  "认读 survey、standard、graduate 和 ceremony。",
  [("survey", "调查"), ("standard", "标准"), ("graduate", "毕业"), ("ceremony", "典礼")], "vocab9")

G("gr_ger", "动名词与不定式", 9, "上", 90,
  "能区分动词后面接 to do 还是 doing。", "to_ing", [
    q("我记得见过你们。哪一句正确？", "I remember meeting all of you.",
      ["I remember to meeting all of you.", "I remember meet all of you.", "I remember meeting to all of you."],
      "remember meeting 表示记得做过。"),
    q("记得锁门。这是还没做的事。哪一句正确？", "Remember to lock the door.",
      ["Remember locking the door for a future action.", "Remember to locking the door.", "Remember lock the door."],
      "remember to lock 表示记得要去做。"),
    q("她喜欢唱歌。哪一句正确？", "She enjoys singing.",
      ["She enjoys to sing.", "She enjoys sing.", "She enjoys to singing."],
      "enjoy 后面用 singing。"),
    q("他决定离开。哪一句正确？", "He decided to leave.",
      ["He decided leaving.", "He decided leave.", "He decided to leaving."],
      "decide 后面用 to leave。"),
])

G("gr_tag", "反意疑问句", 9, "上", 90,
  "能在陈述句后加上意思相反的简短问句。", "sentence", [
    q("她是学生，不是吗？哪一句正确？", "She is a student, isn't she?",
      ["She is a student, isn't he?", "She is a student, is she?", "She is a student, doesn't she?"],
      "前面是肯定的 is，后面用 isn't she。"),
    q("你喜欢苹果，不是吗？哪一句正确？", "You like apples, don't you?",
      ["You like apples, aren't you?", "You like apples, do you?", "You like apples, doesn't you?"],
      "like 是实义动词，用 don't you。"),
    q("他昨天没来，对吗？哪一句正确？", "He didn't come yesterday, did he?",
      ["He didn't come yesterday, didn't he?", "He didn't come yesterday, was he?", "He didn't come yesterday, does he?"],
      "前面是否定，后面用肯定的 did he。"),
    q("反意疑问句的后半部分通常怎样？", "和前半部分肯定否定相反",
      ["必须再重复整个句子", "只能用名词作主语", "不能使用 be 动词"],
      "前肯后否，前否后肯。"),
])

F("fu_memory", "回忆学校生活", 9, "上", 90,
  "能在毕业时回顾学校生活。", "func_school", [
    q("想说你记得第一次见面，哪一句合适？", "I remember meeting you on the first day.",
      ["I remember to meet you on the first day already done.", "I remember meet you on the first day.", "I remember meeting you tomorrow."],
      "记得已经发生的事用 remember meeting。"),
    q("典礼在星期五。想向同学确认，哪一句合适？", "The ceremony is on Friday, isn't it?",
      ["The ceremony is on Friday, isn't he?", "The ceremony is on Friday, is it?", "The ceremony is on Friday, doesn't it?"],
      "isn't it。"),
    q("我们明年毕业。哪一句合适？", "We will graduate next year.",
      ["We will graduate last year.", "We graduated next year.", "We are graduate next year."],
      "will graduate next year。"),
    q("想说调查已经做完，哪一句合适？", "We have already done the survey.",
      ["We have yet done the survey.", "We did already the survey tomorrow.", "We have already do the survey."],
      "have already done。"),
])

R("rw_write", "书面表达要点", 9, "上", 90,
  "能选出涵盖全部要点、人称和时态都正确的句子。", "write_point", [
    q("要点：你上周末去了公园，和同学放了风筝，天气晴朗。哪一句符合全部要点？",
      "Last weekend I went to the park with my classmates and flew a kite. It was sunny.",
      ["Next weekend I will go to the park alone.",
       "Last weekend I went to the park. It was rainy, and I did not fly a kite.",
       "I go to the park every weekend and fly a kite."],
      "过去的时间、同学、放风筝、晴天都要出现。"),
    q("要点：用现在完成时说明你已经在这所学校学习了三年，并且仍然喜欢英语。哪一句符合？",
      "I have studied at this school for three years, and I still like English.",
      ["I studied at this school for three years, but I have left it.",
       "I have studied at this school since three years, and I liked English only before.",
       "I study at this school tomorrow for three years."],
      "have studied for three years，并且 still like。"),
    q("要点：写信建议朋友少扔塑料，并说明河底已经有垃圾。哪一句符合？",
      "You should throw less plastic because there is already litter at the bottom of the river.",
      ["You should throw more plastic into the river.",
       "There was no litter, so do nothing.",
       "I threw plastic yesterday and I will not give advice."],
      "建议少扔，并提到河底已有垃圾。"),
    q("要点：毕业典礼在周五，你记得第一次见到老师。用正确的反意疑问句向同学确认日期。哪一句符合？",
      "I remember meeting the teacher, and the ceremony is on Friday, isn't it?",
      ["I remember to meet the teacher next Friday, is it?",
       "The ceremony was on Friday, wasn't he?",
       "I remember meeting the teacher, but I do not know any date."],
      "记得做过用 meeting，确认星期五用 isn't it。"),
])
