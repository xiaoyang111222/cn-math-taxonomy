# -*- coding: utf-8 -*-
"""七年级下册，以及已经挂在七年级上册新版单元上的点。

才艺、作息改到七上 Unit 5、Unit 6。学校场所、家人外貌改到七上 Unit 3、Unit 2。
出行方式改到七上「待核」（unit 90），不写进 A Day in the Life。
其余点仍是七年级下册旧编号，本轮不改题目。
"""
from en_tx import V, P, G, F, R
from enj_g7a import PENDING


def q(prompt, answer, wrongs, expl):
    return ("c", prompt, answer, wrongs, expl)


V("vo_talent", "才艺与俱乐部", 7, "上", 5,
  "认读 guitar、chess、club 和 dance。",
  [("guitar", "吉他"), ("chess", "国际象棋"), ("club", "俱乐部"), ("dance", "跳舞")], "vocab7")

G("gr_can7", "情态动词 can", 7, "上", 5,
  "能用 can 和 can't 谈论能力。", "modal", [
    q("我会弹吉他。哪一句正确？", "I can play the guitar.",
      ["I can to play the guitar.", "I can plays the guitar.", "I can play guitar the."],
      "can 后面用动词原形；乐器前通常加 the。"),
    q("她不会下棋。哪一句正确？", "She can't play chess.",
      ["She can't plays chess.", "She can not to play chess.", "She doesn't can play chess."],
      "can't 后面用动词原形 play。"),
    q("Can you swim? 肯定简答是哪一句？", "Yes, I can.",
      ["Yes, I do.", "Yes, I can swim yes.", "Yes, I am."], "can 提问用 can 回答。"),
    q("他会跳舞吗？哪一句是正确的疑问句？", "Can he dance?",
      ["Does he can dance?", "Can he dances?", "Is he can dance?"], "can 直接提前，后面用原形。"),
])

F("fu_club", "谈论才能与俱乐部", 7, "上", 5,
  "能询问才能，并说明想加入哪个俱乐部。", "func_school", [
    q("想问对方会不会画画，哪一句合适？", "Can you draw?",
      ["Do you can draw?", "Can you draws?", "Are you can draw?"], "Can you draw 询问能力。"),
    q("想加入音乐俱乐部，哪一句合适？", "I want to join the music club.",
      ["I want join the music club.", "I want to join the music clubbing.", "I wants to join the music club."],
      "want to join 表示想加入。"),
    q("对方问 Can you play the piano? 你不会，应回答什么？", "No, I can't.",
      ["No, I don't.", "No, I am not.", "No, I can."], "can 的否定简答是 No, I can't。"),
    q("What club do you want to join? 这句在问什么？", "你想加入哪个俱乐部",
      ["你会不会游泳", "俱乐部在哪里", "吉他多少钱"], "what club 问哪一个俱乐部。"),
])

R("rw_ad", "读俱乐部广告", 7, "上", 5,
  "读一则俱乐部广告，找出需要的才能。", "read_detail", [
    q("Music Club. Can you sing or dance? Come and join us. Call Mr. Brown. 这个俱乐部需要什么才能？", "唱歌或跳舞",
      ["下棋", "踢足球", "画画"], "sing or dance 是唱歌或跳舞。"),
    q("Music Club. Can you sing or dance? Come and join us. Call Mr. Brown. 要联系谁？", "Mr. Brown",
      ["Mr. Green", "Gina", "Tom"], "Call Mr. Brown。"),
    q("We need students for the chess club. Can you play chess? 他们需要会什么的学生？", "会下国际象棋",
      ["会弹吉他", "会游泳", "会说英语"], "play chess 是下棋。"),
    q("We need students for the chess club. Can you play chess? 哪一句和广告一致？", "The club wants students who can play chess.",
      ["The club wants singers.", "Students must play the guitar.", "The club is only for teachers."],
      "广告要会下棋的学生。"),
])

V("vo_daily", "日常作息", 7, "上", 6,
  "认读 shower、exercise、quarter 和 homework。",
  [("shower", "淋浴"), ("exercise", "锻炼"), ("quarter", "一刻钟"), ("homework", "家庭作业")], "vocab7")

G("gr_clock", "时刻表达", 7, "上", 6,
  "能用 past、to 和数字读出时刻。", "question", [
    q("6:15 用哪一种说法？", "a quarter past six",
      ["a quarter to six", "six past a quarter", "half past six"], "15 分是 a quarter past。"),
    q("6:30 用哪一种说法？", "half past six",
      ["half to six", "six half", "a quarter past six"], "30 分是 half past。"),
    q("6:45 用哪一种说法？", "a quarter to seven",
      ["a quarter past seven", "seven to a quarter", "half to seven"], "差 15 分到 7 点是 a quarter to seven。"),
    q("What time do you get up? 这句在问什么？", "你几点起床",
      ["你在哪里起床", "你为什么起床", "你和谁起床"], "What time 问时刻。"),
])

G("gr_often", "频度副词", 7, "下", 2,
  "能按频率选用 always、usually、sometimes 和 never。", "present", [
    q("他每天都锻炼。哪一个词最合适？", "always",
      ["never", "sometimes", "seldom only once"], "每天都做用 always。"),
    q("她从不迟到。哪一句正确？", "She is never late.",
      ["She never is late.", "She is late never.", "She never late."],
      "be 动词放在 never 前面：is never。"),
    q("I usually do my homework at 7. usually 的意思是什么？", "通常",
      ["从不", "总是，一次不落", "只在周末"], "usually 是通常。"),
    q("频度从高到低，哪一组顺序正确？", "always, usually, sometimes, never",
      ["never, sometimes, usually, always", "usually, never, always, sometimes", "sometimes, always, never, usually"],
      "always 最高，never 最低。"),
])

F("fu_time7", "谈论作息时间", 7, "上", 6,
  "能询问和说明每天几点做什么。", "func_school", [
    q("想问对方几点上学，哪一句合适？", "What time do you go to school?",
      ["What time does you go to school?", "What time do you goes to school?", "When time do you go to school?"],
      "you 用 What time do you。"),
    q("你六点半起床，应怎么说？", "I get up at half past six.",
      ["I get up in half past six.", "I gets up at half past six.", "I get up on half past six."],
      "在时刻前用 at，I get up。"),
    q("When do you usually exercise? 这句在问什么？", "你通常什么时候锻炼",
      ["你会不会锻炼", "锻炼在哪里", "锻炼多少钱"], "When 加 usually 问通常的时间。"),
    q("想说他通常晚上做作业，哪一句合适？", "He usually does his homework in the evening.",
      ["He usually do his homework in the evening.", "He usually does his homework on the evening.", "He usually does his homeworks in the evening."],
      "He does，homework 不可数，in the evening。"),
])

R("rw_day7", "读一天的安排", 7, "上", 6,
  "读一段作息短文，找出时间。", "read_detail", [
    q("Scott gets up at 6:00. He exercises at 6:30. He goes to school at 7:15. 他几点锻炼？", "6:30",
      ["6:00", "7:15", "8:00"], "exercises at 6:30。"),
    q("Scott gets up at 6:00. He exercises at 6:30. He goes to school at 7:15. 他几点上学？", "7:15",
      ["6:00", "6:30", "7:45"], "goes to school at 7:15。"),
    q("Mary usually does her homework at 7:00 in the evening. She never watches TV on school nights. 上学的晚上她看电视吗？", "从不看",
      ["总是看", "有时看", "只看半小时"], "never watches TV on school nights。"),
    q("Mary usually does her homework at 7:00 in the evening. 哪一句和短文一致？", "Mary usually does homework at seven in the evening.",
      ["Mary never does homework.", "Mary does homework at seven in the morning.", "Mary gets up at 7:00."],
      "at 7:00 in the evening 是晚上七点。"),
])

V("vo_trans7", "交通方式", 7, "上", 90,
  "认读 train、subway、bike 和 bus。" + PENDING,
  [("train", "火车"), ("subway", "地铁"), ("bike", "自行车"), ("bus", "公共汽车")], "vocab7")

G("gr_howfar", "How 问交通", 7, "上", 90,
  "能用 how、how long 和 how far 询问出行方式、时间和距离。" + PENDING, "question", [
    q("询问对方怎么去学校，哪一句正确？", "How do you get to school?",
      ["How does you get to school?", "How do you gets to school?", "How you get to school?"],
      "you 用 How do you get。"),
    q("路程大约 10 公里。哪一句正确？", "It is about ten kilometers.",
      ["It are about ten kilometers.", "It is about ten kilometer.", "It is about ten kilometers far."],
      "it is，kilometer 的复数是 kilometers。far 不和具体距离叠用。"),
    q("How long does it take? 这句在问什么？", "需要多长时间",
      ["有多远", "怎么去", "在哪里"], "how long 问时间长度。"),
    q("她步行上学。哪一句正确？", "She walks to school.",
      ["She goes to school by foot.", "She walk to school.", "She walks to school by foot."],
      "步行用 walks；by foot 不是标准说法，应说 on foot，且不再叠用 walks to。"),
])

F("fu_trans7", "谈论怎么上学", 7, "上", 90,
  "能说明自己怎么上学、花多长时间。" + PENDING, "func_life", [
    q("想说你乘地铁上学，哪一句合适？", "I take the subway to school.",
      ["I by the subway to school.", "I take the subway to school by.", "I takes the subway to school."],
      "I take the subway。"),
    q("想问学校有多远，哪一句合适？", "How far is it from your home to school?",
      ["How long is it from your home to school?", "How far it is from your home to school?", "How old is it from your home to school?"],
      "问距离用 How far。"),
    q("对方说 It takes me 20 minutes. 这句话的意思是什么？", "这花费我 20 分钟",
      ["学校有 20 公里", "我有 20 辆自行车", "我 20 岁"], "take 加时间表示花费时间。"),
    q("想说他骑自行车，哪一句合适？", "He rides his bike to school.",
      ["He ride his bike to school.", "He rides his bike by bike.", "He by bike to school."],
      "He rides his bike。不必再加 by bike。"),
])

R("rw_trans7", "读上学方式", 7, "上", 90,
  "读一段出行短文，找出方式和时间。" + PENDING, "read_detail", [
    q("Lisa lives 5 kilometers from school. She rides her bike. It takes her 15 minutes. 她怎么上学？", "骑自行车",
      ["乘地铁", "乘火车", "步行"], "rides her bike 是骑自行车。"),
    q("Lisa lives 5 kilometers from school. She rides her bike. It takes her 15 minutes. 大约要多久？", "15 分钟",
      ["5 分钟", "50 分钟", "15 公里"], "15 minutes 是时间，5 kilometers 是距离。"),
    q("Tom takes the bus. The bus ride takes about 20 minutes. Tom 乘什么？", "公共汽车",
      ["自行车", "火车", "地铁"], "takes the bus。"),
    q("Tom takes the bus. The bus ride takes about 20 minutes. 哪一句和短文一致？", "Tom's bus ride is about 20 minutes.",
      ["Tom walks for 20 minutes.", "Tom lives 20 kilometers away.", "Tom rides a bike."],
      "takes about 20 minutes 指乘车时间。"),
])

V("vo_rule7", "校规词汇", 7, "下", 4,
  "认读 rule、hallway、fight 和 uniform。",
  [("rule", "规则"), ("hallway", "走廊"), ("fight", "打架"), ("uniform", "校服")], "vocab7")

G("gr_imp7", "祈使句", 7, "下", 4,
  "能用肯定和否定祈使句表达命令。", "sentence", [
    q("不要在课堂上吃东西。哪一句正确？", "Don't eat in class.",
      ["Not eat in class.", "Don't eating in class.", "Doesn't eat in class."],
      "否定祈使句用 Don't 加动词原形。"),
    q("请准时。哪一句正确？", "Please be on time.",
      ["Please is on time.", "Please to be on time.", "Please being on time."],
      "Please 后面用动词原形 be。"),
    q("哪一句是祈使句？", "Listen to the teacher.",
      ["She listens to the teacher.", "Does she listen to the teacher?", "She is listening to the teacher."],
      "以动词原形开头、省略主语的是祈使句。"),
    q("Don't run in the hallways. 这句的意思是什么？", "不要在走廊里跑",
      ["请在走廊里跑", "她不在走廊里跑", "走廊里没有规则"], "Don't run 是否定命令。"),
])

G("gr_must7", "must 与 have to", 7, "下", 4,
  "能用 must 和 have to 表示必须，用 can't 表示不准。", "modal", [
    q("我们在图书馆必须保持安静。哪一句正确？", "We must be quiet in the library.",
      ["We must are quiet in the library.", "We must to be quiet in the library.", "We must quiet in the library."],
      "must 后面用动词原形 be。"),
    q("他不得不早起。哪一句正确？", "He has to get up early.",
      ["He have to get up early.", "He has to gets up early.", "He must to get up early."],
      "He has to 加动词原形。"),
    q("上课不准听音乐。哪一句正确？", "We can't listen to music in class.",
      ["We can't to listen to music in class.", "We don't can listen to music in class.", "We can't listening to music in class."],
      "can't 后面用动词原形 listen。"),
    q("must 和 have to 都表示什么？", "必须",
      ["可能", "过去常常", "正在"], "两者都表示必须做。"),
])

F("fu_rule7", "说明规则", 7, "下", 4,
  "能说出学校里必须做和不能做的事。", "func_school", [
    q("想告诉新生不能在走廊打架，哪一句合适？", "Don't fight in the hallways.",
      ["Not fight in the hallways.", "Doesn't fight in the hallways.", "Fight don't in the hallways."],
      "规则用 Don't fight。"),
    q("想说学生必须穿校服，哪一句合适？", "Students must wear the school uniform.",
      ["Students must wears the school uniform.", "Students must to wear the school uniform.", "Students wear must the school uniform."],
      "must wear 是必须穿。"),
    q("Can we eat in the classroom? 老师要说不行，哪一句合适？", "No, you can't.",
      ["No, you don't.", "No, you aren't eat.", "Yes, you can't."], "拒绝用 No, you can't。"),
    q("We have to be on time. 这句话的意思是什么？", "我们必须准时",
      ["我们可以迟到", "我们正在准时", "准时是一条建议，可做可不做"], "have to 表示必须。"),
])

R("rw_rule7", "读校规", 7, "下", 4,
  "读几条校规，判断能做和不能做的事。", "read_detail", [
    q("Rules: Don't arrive late. Don't run in the hallways. We must wear uniforms. 可以迟到吗？", "不可以",
      ["可以", "只在星期一可以", "短文没说"], "Don't arrive late 是不要迟到。"),
    q("Rules: Don't arrive late. Don't run in the hallways. We must wear uniforms. 必须穿什么？", "校服",
      ["运动鞋", "帽子", "短裙"], "wear uniforms 是穿校服。"),
    q("Students can't eat in class. They can eat in the dining hall. 他们可以在哪里吃东西？", "餐厅",
      ["课堂上", "走廊里", "图书馆里"], "in the dining hall 是餐厅。"),
    q("Students can't eat in class. They can eat in the dining hall. 哪一句和短文一致？", "Students cannot eat in class.",
      ["Students can eat in class.", "Students must run in the hallways.", "Students arrive late every day."],
      "can't eat in class 就是课堂上不能吃。"),
])

V("vo_animal7", "动物", 7, "下", 5,
  "认读 tiger、elephant、panda 和 koala。",
  [("tiger", "老虎"), ("elephant", "大象"), ("panda", "熊猫"), ("koala", "树袋熊")], "vocab7")

G("gr_why7", "Why 与 because", 7, "下", 5,
  "能用 Why 提问，并用 because 回答。", "clause_adv", [
    q("为什么你喜欢熊猫？哪一句正确？", "Why do you like pandas?",
      ["Why you like pandas?", "Why does you like pandas?", "Why do you likes pandas?"],
      "you 用 Why do you like。"),
    q("因为它们很可爱。哪一句正确？", "Because they are cute.",
      ["Because they is cute.", "So they are cute.", "Why they are cute."],
      "they are cute，回答原因用 because。"),
    q("Why does she like koalas? 这句在问什么？", "她为什么喜欢树袋熊",
      ["她在哪里看树袋熊", "树袋熊吃什么", "她会不会画树袋熊"], "Why 问原因。"),
    q("哪一句是正确的？", "I like elephants because they are smart.",
      ["I like elephants because they is smart.", "I like elephants so they are smart.", "Because I like elephants they are smart."],
      "because they are smart。"),
])

G("gr_desc", "描述性形容词", 7, "下", 5,
  "能用形容词描述动物，并注意 be 动词。", "present", [
    q("熊猫是黑白相间的。哪一句正确？", "Pandas are black and white.",
      ["Pandas is black and white.", "Pandas are black white.", "Panda are black and white."],
      "复数 pandas 用 are。"),
    q("这只大象很友好。哪一句正确？", "The elephant is friendly.",
      ["The elephant are friendly.", "The elephant is friend.", "The elephant is friendlyly."],
      "单数用 is，形容词是 friendly。"),
    q("kind 的意思是哪一个？", "和蔼的",
      ["可怕的", "懒惰的", "来自南方的"], "kind 可以表示和蔼。"),
    q("哪一句表示「老虎有点吓人」？", "Tigers are kind of scary.",
      ["Tigers are a kind of scary.", "Tigers is kind of scary.", "Tigers are kind scary of."],
      "kind of 表示有点，放在形容词前。"),
])

F("fu_zoo", "谈论动物", 7, "下", 5,
  "能询问来自哪里、喜欢什么动物并说明原因。", "func_life", [
    q("想问对方为什么喜欢大象，哪一句合适？", "Why do you like elephants?",
      ["Why are you like elephants?", "Why do you likes elephants?", "What do you like elephants?"],
      "Why do you like 问原因。"),
    q("想说熊猫来自中国，哪一句合适？", "Pandas are from China.",
      ["Pandas is from China.", "Pandas are from the China.", "Panda are from China."],
      "复数用 are from。"),
    q("Where are lions from? 这句在问什么？", "狮子来自哪里",
      ["狮子为什么可爱", "狮子在吃什么", "狮子多少钱"], "Where ... from 问来源。"),
    q("想说树袋熊很懒，哪一句合适？", "Koalas are very lazy.",
      ["Koalas is very lazy.", "Koalas are very lazily.", "Koalas very are lazy."],
      "are 加形容词 lazy。"),
])

R("rw_zoo7", "读动物介绍", 7, "下", 5,
  "读一段动物介绍，找出产地和特点。", "read_detail", [
    q("Pandas are from China. They are black and white. They are kind of shy. 熊猫来自哪里？", "中国",
      ["澳大利亚", "南非", "印度"], "from China。"),
    q("Pandas are from China. They are black and white. They are kind of shy. 它们的性格怎样？", "有点害羞",
      ["非常吓人", "很懒", "很友好而且短文说它们爱打架"], "kind of shy 是有点害羞。"),
    q("Koalas are from Australia. They sleep all day. People think they are lazy. 树袋熊来自哪里？", "澳大利亚",
      ["中国", "美国", "英国"], "from Australia。"),
    q("Koalas are from Australia. They sleep all day. 哪一句和短文一致？", "Koalas sleep during the day.",
      ["Koalas are from China.", "Koalas never sleep.", "Koalas are black and white."],
      "sleep all day 是白天都在睡。"),
])

V("vo_now", "正在进行的活动", 7, "下", 6,
  "认读 newspaper、soup、movie 和 just。",
  [("newspaper", "报纸"), ("soup", "汤"), ("movie", "电影"), ("just", "正好；只是")], "vocab7")

G("gr_ing7", "现在进行时的构成", 7, "下", 6,
  "能用 am、is、are 加动词 -ing 描述正在做的事。", "continuous", [
    q("他正在看电视。哪一句正确？", "He is watching TV.",
      ["He watching TV.", "He is watch TV.", "He are watching TV."],
      "现在进行时是 is 加 watching。"),
    q("他们正在吃晚饭。哪一句正确？", "They are eating dinner.",
      ["They are eat dinner.", "They is eating dinner.", "They eating dinner."],
      "They are eating。"),
    q("她正在读书吗？哪一句正确？", "Is she reading a book?",
      ["Does she reading a book?", "Is she read a book?", "Does she reads a book now?"],
      "把 is 提前，reading 保留。"),
    q("swim 的 -ing 形式是哪一个？", "swimming",
      ["swiming", "swimminging", "swim"], "重读闭音节、末尾单辅音要双写再加 ing。"),
])

F("fu_now", "询问正在做什么", 7, "下", 6,
  "能打电话询问对方正在做什么。", "func_life", [
    q("想问对方正在做什么，哪一句合适？", "What are you doing?",
      ["What do you doing?", "What are you do?", "What is you doing?"],
      "What are you doing。"),
    q("你正在喝汤，应回答什么？", "I am drinking soup.",
      ["I drinking soup.", "I am drink soup.", "I is drinking soup."],
      "I am drinking。"),
    q("Is Mary talking on the phone? 她正在读报，应回答什么？", "No, she is reading a newspaper.",
      ["Yes, she is reading a newspaper.", "No, she reading a newspaper.", "No, she does read a newspaper."],
      "否定正在打电话，并说明她在读报。"),
    q("Let's go to the movies. 对方正在做作业，哪一句能说明去不了？", "I am doing my homework.",
      ["I do my homework every day.", "I am do my homework.", "I does my homework."],
      "现在正在做用 am doing。"),
])

R("rw_now7", "读正在发生的事", 7, "下", 6,
  "读一段现在进行时短文，找出每个人正在做什么。", "read_detail", [
    q("It is Sunday morning. Tom is reading a newspaper. His mother is making soup. Tom 正在做什么？", "读报纸",
      ["做汤", "看电影", "打电话"], "is reading a newspaper。"),
    q("It is Sunday morning. Tom is reading a newspaper. His mother is making soup. 妈妈正在做什么？", "做汤",
      ["读报纸", "看电视", "写作业"], "is making soup。"),
    q("Gina is talking on the phone. She is not watching the movie. Gina 在看电影吗？", "没有",
      ["在看", "和 Tom 一起看", "短文没说"], "is not watching the movie。"),
    q("Gina is talking on the phone. She is not watching the movie. 哪一句和短文一致？", "Gina is using the phone.",
      ["Gina is watching a movie.", "Gina is making soup.", "Gina is reading a newspaper."],
      "talking on the phone 就是在打电话。"),
])

V("vo_weather7", "天气", 7, "下", 7,
  "认读 rain、windy、cloudy 和 sunny。",
  [("rain", "雨；下雨"), ("windy", "有风的"), ("cloudy", "多云的"), ("sunny", "晴朗的")], "vocab7")

G("gr_excl", "感叹句", 7, "下", 7,
  "能用 What 和 How 构成感叹句。", "sentence", [
    q("多么冷的一天。哪一句正确？", "What a cold day it is!",
      ["What cold day it is!", "How a cold day it is!", "What a cold day is it?"],
      "可数单数名词前用 What a，主语 it 在 is 前面。"),
    q("天气真好。哪一句正确？", "How nice the weather is!",
      ["What nice the weather is!", "How a nice the weather is!", "How nice is the weather!"],
      "How 后面接形容词，语序仍是陈述语序。"),
    q("What a sunny day! 这句在感叹什么？", "多么晴朗的一天",
      ["请在晴天出门", "今天是星期几", "太阳在哪里"], "What a sunny day 是感叹晴天。"),
    q("哪一句是感叹句？", "How windy it is!",
      ["It is windy.", "Is it windy?", "It is not windy."], "How 加形容词加陈述语序是感叹句。"),
])

F("fu_weather7", "谈论天气", 7, "下", 7,
  "能询问天气，并描述正在下雨或出太阳。", "func_life", [
    q("想问北京的天气，哪一句合适？", "How is the weather in Beijing?",
      ["What is the weather in Beijing?", "How is the weather in Beijing is?", "What weather is it in Beijing does?"],
      "How is the weather in Beijing 是常见问法。"),
    q("北京正在下雨，应怎么说？", "It is raining in Beijing.",
      ["It is rain in Beijing.", "It raining in Beijing.", "Beijing is raining."],
      "正在下雨用 It is raining。"),
    q("对方说 It is sunny. 你觉得天气很好，哪一句合适？", "What a fine day!",
      ["What fine day!", "How a fine day!", "What a fine day it are!"],
      "What a fine day。"),
    q("How is the weather? 也可以说成哪一句？", "What's the weather like?",
      ["What's the weather is like?", "How the weather is?", "What does the weather like?"],
      "What's the weather like 和 How is the weather 同义。"),
])

R("rw_weather7", "读天气消息", 7, "下", 7,
  "读一段天气短文，找出各地天气。", "read_detail", [
    q("It is sunny in Shanghai. It is raining in Beijing. It is windy in Guangzhou. 北京的天气怎样？", "正在下雨",
      ["晴朗", "有风", "多云"], "raining in Beijing。"),
    q("It is sunny in Shanghai. It is raining in Beijing. It is windy in Guangzhou. 哪里有风？", "广州",
      ["上海", "北京", "三地都有风"], "windy in Guangzhou。"),
    q("What a cold day in Harbin! People are wearing sweaters. 哈尔滨的人穿着什么？", "毛衣",
      ["短裙", "校服", "短袜"], "wearing sweaters。"),
    q("What a cold day in Harbin! People are wearing sweaters. 哪一句和短文一致？", "It is cold in Harbin.",
      ["It is hot in Harbin.", "People are wearing skirts.", "It is raining in Harbin."],
      "a cold day 说明很冷。短文没有说下雨。"),
])

V("vo_place", "学校场所", 7, "上", 3,
  "认读 hall、building、dining hall 和 reading corner。",
  [("hall", "礼堂"), ("building", "建筑物"), ("dining hall", "餐厅"), ("reading corner", "阅读角")], "vocab7")

G("gr_there7", "There be 句型", 7, "上", 3,
  "能用 There is 和 There are 描述学校里有什么。", "there_prep", [
    q("学校里有一座礼堂。哪一句正确？", "There is a hall in the school.",
      ["There are a hall in the school.", "There have a hall in the school.", "There is hall in the school."],
      "单数用 There is a hall。"),
    q("教学楼前面有两棵树。哪一句正确？", "There are two trees in front of the building.",
      ["There is two trees in front of the building.", "There are two tree in front of the building.", "There have two trees in front of the building."],
      "复数用 There are，trees 用复数。"),
    q("Is there a dining hall in your school? 肯定回答是哪一句？", "Yes, there is.",
      ["Yes, there are.", "Yes, it is.", "Yes, there has."], "Is there 用 Yes, there is 回答。"),
    q("哪一句是正确的否定句？", "There isn't a reading corner in this building.",
      ["There aren't a reading corner in this building.", "There not a reading corner in this building.", "There isn't any reading corner are in this building."],
      "单数否定用 There isn't a。"),
])

F("fu_way7", "询问学校场所", 7, "上", 3,
  "能询问学校里有没有某处，并用 across from、next to 说明位置。", "func_life", [
    q("想问学校里有没有餐厅，哪一句合适？", "Is there a dining hall in your school?",
      ["Are there a dining hall in your school?", "Is there dining hall in your school?", "Does there a dining hall in your school?"],
      "Is there a dining hall。"),
    q("餐厅在教学楼对面，应怎么说？", "The dining hall is across from the building.",
      ["The dining hall is across to the building.", "The dining hall across from the building.", "The dining hall is across from building the."],
      "across from 表示在对面。"),
    q("Where is the reading corner? 这句在问什么？", "阅读角在哪里",
      ["阅读角多少钱", "阅读角是谁的", "阅读角几点开门，这句没问时间"], "Where 问位置。"),
    q("想说礼堂在餐厅旁边，哪一句合适？", "The hall is next to the dining hall.",
      ["The hall is next the dining hall.", "The hall next to the dining hall.", "The hall are next to the dining hall."],
      "next to 表示在旁边。"),
])

R("rw_way7", "读学校位置", 7, "上", 3,
  "读一段学校位置说明，找出场所在哪里。", "read_detail", [
    q("Our hall is in front of the building. The dining hall is across from the hall. The reading corner is next to the library. 礼堂在哪里？", "在教学楼前面",
      ["在餐厅里面", "在图书馆对面", "在阅读角里面"], "in front of the building。"),
    q("Our hall is in front of the building. The dining hall is across from the hall. The reading corner is next to the library. 餐厅在礼堂的哪一边？", "在对面",
      ["在前面", "在里面", "在楼上"], "across from the hall。"),
    q("Our hall is in front of the building. The dining hall is across from the hall. The reading corner is next to the library. 阅读角在哪里？", "在图书馆旁边",
      ["在礼堂里面", "在餐厅对面", "在教学楼后面"], "next to the library。"),
    q("Our hall is in front of the building. The dining hall is across from the hall. The reading corner is next to the library. 哪一句和短文一致？", "The dining hall is across from the hall.",
      ["The hall is across from the building.", "The reading corner is in the hall.", "The library is in front of the hall."],
      "餐厅在礼堂对面。礼堂在教学楼前面，不是在对面。"),
])

V("vo_look", "外貌", 7, "上", 2,
  "认读描述家人外貌时用到的 handsome、tall、short 和 hair。",
  [("handsome", "英俊的"), ("tall", "高的"), ("short", "矮的"), ("hair", "头发")], "vocab7")

G("gr_look", "描述外貌", 7, "上", 2,
  "能用 be 和 have 描述家人的高矮和头发。", "present", [
    q("他很英俊。哪一句正确？", "He is handsome.",
      ["He has handsome.", "He is a handsome.", "He wears handsome."], "英俊用 be 加形容词。"),
    q("她留着长发。哪一句正确？", "She has long hair.",
      ["She is long hair.", "She has long hairs.", "She is has long hair."],
      "有某种头发用 has，hair 通常不可数。"),
    q("我爷爷又高又英俊。哪一句正确？", "My grandfather is tall and handsome.",
      ["My grandfather has tall and handsome.", "My grandfather is tall and handsome hair.", "My grandfather are tall and handsome."],
      "高和英俊都用 is，不用 has。"),
    q("What does he look like? 这句在问什么？", "他长什么样",
      ["他喜欢什么", "他看起来在看书", "他来自哪里"], "look like 问外貌，不是问喜好。"),
])

F("fu_look", "询问长什么样", 7, "上", 2,
  "能询问和描述家人的外貌。", "func_life", [
    q("想问你哥哥长什么样，哪一句合适？", "What does your brother look like?",
      ["What does your brother like?", "What is your brother look like?", "How does your brother look like?"],
      "问外貌用 What does ... look like。What does he like 是问喜好。"),
    q("她个子矮，应怎么说？", "She is short.",
      ["She has short.", "She is a short.", "She wears short."], "矮用 is short。"),
    q("He has short grey hair. 这句话的意思是什么？", "他留着花白的短发",
      ["他很高", "他很英俊所以头发长", "他戴着帽子"], "short grey hair 是花白短发。"),
    q("想说那个男孩又高又英俊，哪一句合适？", "The boy is tall and handsome.",
      ["The boy has tall and handsome.", "The boy is tall and handsome hair.", "The boy are tall and handsome."],
      "is 加两个形容词。"),
])

R("rw_look", "读人物外貌", 7, "上", 2,
  "读一段家人外貌描述，找出人物特征。", "read_detail", [
    q("This is my family. My grandfather is tall and handsome. He has short grey hair. My sister is short. She has long brown hair. 爷爷高吗？", "高",
      ["矮", "和姐姐一样矮", "短文没说"], "My grandfather is tall。"),
    q("This is my family. My grandfather is tall and handsome. He has short grey hair. My sister is short. She has long brown hair. 姐姐的头发是什么样的？", "长的棕色头发",
      ["花白短发", "短的黑发", "没有头发"], "long brown hair。"),
    q("This is my family. My grandfather is tall and handsome. He has short grey hair. My sister is short. She has long brown hair. 爷爷的头发是什么样的？", "花白的短发",
      ["棕色长发", "金色卷发", "短文没说"], "short grey hair。"),
    q("This is my family. My grandfather is tall and handsome. He has short grey hair. My sister is short. She has long brown hair. 哪一句和短文一致？", "My sister is short.",
      ["My sister is tall.", "Grandfather has long hair.", "My sister is handsome in this text."],
      "姐姐个子矮。爷爷高，而且头发短。"),
])

V("vo_noodle", "点餐食物", 7, "下", 10,
  "认读 noodle、mutton、cabbage 和 dumpling。",
  [("noodle", "面条"), ("mutton", "羊肉"), ("cabbage", "卷心菜"), ("dumpling", "饺子")], "vocab7")

G("gr_would7", "would like", 7, "下", 10,
  "能用 would like 点餐，并区分 some 和 any。", "modal", [
    q("我想要一碗牛肉面。哪一句正确？", "I would like a bowl of beef noodles.",
      ["I would like a bowl of beef noodle.", "I would like to a bowl of beef noodles.", "I like would a bowl of beef noodles."],
      "would like 后面直接加名词；noodles 常用复数。"),
    q("你想要什么？哪一句正确？", "What would you like?",
      ["What would you like to?", "What do you would like?", "What would you like it?"],
      "What would you like。"),
    q("疑问句里用 any 还是 some？哪一句正确？", "Would you like some dumplings?",
      ["Would you like any dumplings?", "Would you like some dumpling?", "Do you would like some dumplings?"],
      "would like 的问句表示邀请，仍常用 some。"),
    q("She would like mutton cabbage dumplings. 她想要什么馅的饺子？", "羊肉白菜",
      ["牛肉", "只有卷心菜、没有肉", "鱼肉"], "mutton cabbage 是羊肉白菜。"),
])

F("fu_order", "点餐用语", 7, "下", 10,
  "能在餐馆点餐并询问种类。", "func_life", [
    q("服务员问 May I take your order? 你想要面条，哪一句合适？", "I'd like beef noodles, please.",
      ["I like beef noodles every day.", "I would like to beef noodles.", "I'd like beef noodle, please."],
      "点餐用 I'd like，noodles 用复数。"),
    q("想问有哪些种类的饺子，哪一句合适？", "What kind of dumplings would you like?",
      ["What kind of dumplings would you like to?", "What kind dumplings you like?", "How kind of dumplings would you like?"],
      "What kind of 问哪一种。"),
    q("Are there any vegetables in the soup? 这句在问什么？", "汤里有蔬菜吗",
      ["汤多少钱", "你想要汤吗", "汤是谁做的"], "Are there any 问是否有。"),
    q("A large bowl, please. 这句话的意思是什么？", "请来一大碗",
      ["请来一小碗", "不要碗", "碗在桌子底下"], "large bowl 是大碗。"),
])

R("rw_order", "读点餐对话", 7, "下", 10,
  "读一段点餐对话，找出食物和碗的大小。", "read_detail", [
    q("Waiter: What would you like? Tom: I'd like a large bowl of mutton noodles. Tom 要什么面？", "羊肉面",
      ["牛肉面", "白菜面", "鸡蛋面"], "mutton noodles 是羊肉面。"),
    q("Waiter: What would you like? Tom: I'd like a large bowl of mutton noodles. 他要多大的碗？", "大碗",
      ["小碗", "中碗", "不要碗"], "a large bowl。"),
    q("Gina would like some cabbage dumplings. She would not like any meat. Gina 要肉吗？", "不要",
      ["要羊肉", "要牛肉", "短文没说"], "would not like any meat。"),
    q("Gina would like some cabbage dumplings. 哪一句和短文一致？", "Gina wants cabbage dumplings.",
      ["Gina wants mutton dumplings.", "Gina wants a bowl of soup only.", "Gina does not want dumplings."],
      "cabbage dumplings 是白菜饺子。"),
])

V("vo_trip7", "旅行活动", 7, "下", 11,
  "认读 museum、farm、fire 和 flower。",
  [("museum", "博物馆"), ("farm", "农场"), ("fire", "火；火灾"), ("flower", "花")], "vocab7")

G("gr_was7", "was 与 were", 7, "下", 11,
  "能用 was 和 were 谈论过去。", "past", [
    q("昨天的郊游很棒。哪一句正确？", "The school trip was great.",
      ["The school trip were great.", "The school trip is great yesterday.", "The school trip was greated."],
      "单数过去式用 was，不和 yesterday 一起用 is。"),
    q("农民们当时很友好。哪一句正确？", "The farmers were friendly.",
      ["The farmers was friendly.", "The farmers were friend.", "The farmers are friendly yesterday."],
      "复数过去式用 were。"),
    q("Was the weather good? 否定回答是哪一句？", "No, it wasn't.",
      ["No, it weren't.", "No, it didn't.", "No, it isn't."], "weather 用 it wasn't。"),
    q("Were there any cows? 肯定回答是哪一句？", "Yes, there were.",
      ["Yes, there was.", "Yes, there are.", "Yes, they were cows yes."], "Were there 用 Yes, there were。"),
])

G("gr_ed", "规则动词过去式", 7, "下", 11,
  "能写出规则动词的过去式。", "past", [
    q("play 的过去式是哪一个？", "played",
      ["plaied", "playd", "playing"], "一般直接加 ed。"),
    q("stop 的过去式是哪一个？", "stopped",
      ["stoped", "stopping", "stops"], "重读闭音节末尾辅音双写再加 ed。"),
    q("study 的过去式是哪一个？", "studied",
      ["studyed", "studed", "studies"], "辅音加 y，变 i 再加 ed。"),
    q("昨天我们参观了博物馆。哪一句正确？", "We visited a museum yesterday.",
      ["We visit a museum yesterday.", "We visited a museum yesterdayed.", "We visiting a museum yesterday."],
      "yesterday 和过去式 visited 一起用。"),
])

P("ph_ed", "过去式 ed 的读音", 7, "下", 11,
  "能分辨 -ed 读 /t/、/d/ 还是 /ɪd/。", "edsound", [
    q("哪个单词的 -ed 读 /ɪd/？", "visited",
      ["played", "stopped", "cleaned"], "visited 的 -ed 在 /t/ 后读 /ɪd/。"),
    q("stopped 的 -ed 和哪个词同类？", "watched",
      ["played", "lived", "needed"], "stopped 和 watched 的 -ed 都读 /t/。"),
    q("played 的 -ed 和哪个词同类？", "cleaned",
      ["stopped", "watched", "visited"], "played 和 cleaned 的 -ed 都读 /d/。"),
    q("needed 的词尾读什么？", "/ɪd/",
      ["/t/", "/d/", "不发音"], "needed 以 /d/ 结尾，-ed 读 /ɪd/。"),
])

F("fu_trip7", "谈论一次旅行", 7, "下", 11,
  "能询问旅行怎么样，并说出做了什么。", "func_plan", [
    q("想问对方的郊游怎么样，哪一句合适？", "How was your school trip?",
      ["How is your school trip yesterday?", "How were your school trip?", "What was your school trip like did?"],
      "How was your school trip。"),
    q("郊游很有趣，应怎么说？", "It was interesting.",
      ["It were interesting.", "It was interest.", "It is interesting yesterday."],
      "It was interesting。"),
    q("Did you see any cows? 你看到了，应回答什么？", "Yes, I did.",
      ["Yes, I do.", "Yes, I saw.", "Yes, I was."], "Did 提问用 did 简答。"),
    q("想说我们给奶牛挤了奶，哪一句合适？", "We milked a cow.",
      ["We milk a cow yesterday.", "We milked a cow yesterdayed.", "We milking a cow."],
      "milked 是过去式。"),
])

R("rw_diary", "读旅行日记", 7, "下", 11,
  "读一篇旅行日记，找出活动和感受。", "read_detail", [
    q("June 5th. The trip was great. We visited a farm. We milked a cow and saw many flowers. 他们去了哪里？", "农场",
      ["博物馆", "消防站", "学校"], "visited a farm。"),
    q("June 5th. The trip was great. We visited a farm. We milked a cow and saw many flowers. 旅行感觉怎样？", "很棒",
      ["很糟糕", "一般", "短文没说"], "was great。"),
    q("The weather was bad. It rained. We did not take any photos. 他们拍照了吗？", "没有",
      ["拍了很多", "只拍了花", "短文没说"], "did not take any photos。"),
    q("The weather was bad. It rained. 哪一句和日记一致？", "It rained and the weather was bad.",
      ["The weather was great.", "They took many photos.", "They milked a cow in this text."],
      "天气不好并且下了雨。这段没有写挤奶。"),
])

V("vo_wknd", "周末活动", 7, "下", 12,
  "认读 lake、beach、badminton 和 visitor。",
  [("lake", "湖"), ("beach", "海滩"), ("badminton", "羽毛球"), ("visitor", "游客")], "vocab7")

G("gr_did7", "Did 提问", 7, "下", 12,
  "能用 Did 询问过去的事，动词用原形。", "past", [
    q("你上周打羽毛球了吗？哪一句正确？", "Did you play badminton last weekend?",
      ["Did you played badminton last weekend?", "Do you played badminton last weekend?", "Did you played badminton last weekend now?"],
      "Did 后面用动词原形 play。"),
    q("Did he go to the beach? 否定回答是哪一句？", "No, he didn't.",
      ["No, he didn't went.", "No, he doesn't.", "No, he wasn't go."],
      "简答 No, he didn't，不再加动词。"),
    q("她没有去湖边。哪一句正确？", "She didn't go to the lake.",
      ["She didn't went to the lake.", "She doesn't went to the lake.", "She didn't goes to the lake."],
      "didn't 后面用原形 go。"),
    q("What did you do last weekend? 这句在问什么？", "上周末你做了什么",
      ["上周末你将做什么", "你周末通常做什么", "你正在做什么"], "did 加过去时间问已经做的事。"),
])

G("gr_irr7", "不规则动词过去式", 7, "下", 12,
  "能写出 go、see、have、do 和 read 的过去式。", "past", [
    q("go 的过去式是哪一个？", "went",
      ["goed", "goes", "going"], "go 的过去式是 went。"),
    q("see 的过去式是哪一个？", "saw",
      ["seed", "seen", "sawed"], "see 的过去式是 saw。"),
    q("read 的过去式和原形拼写一样。哪一句正确？", "I read an interesting book last night.",
      ["I readed an interesting book last night.", "I reads an interesting book last night.", "I reading an interesting book last night."],
      "read 的过去式仍拼作 read，不写成 readed。"),
    q("我们过得很愉快。哪一句正确？", "We had a good time.",
      ["We haved a good time.", "We has a good time yesterday.", "We had a good time yesterdayed."],
      "have 的过去式是 had。"),
])

F("fu_wknd", "谈论上周末", 7, "下", 12,
  "能询问和叙述上周末做的事。", "func_plan", [
    q("想问对方上周末做了什么，哪一句合适？", "What did you do last weekend?",
      ["What did you did last weekend?", "What do you do last weekend?", "What did you last weekend?"],
      "What did you do。"),
    q("你去了海滩，应怎么说？", "I went to the beach.",
      ["I goed to the beach.", "I go to the beach last weekend.", "I went to the beach yesterday now."],
      "went 是 go 的过去式。"),
    q("Who did you go with? 这句在问什么？", "你和谁一起去的",
      ["你去了哪里", "你怎么去的", "你星期几去的"], "Who ... with 问同伴。"),
    q("想说访客们打了羽毛球，哪一句合适？", "The visitors played badminton.",
      ["The visitors play badminton last Sunday.", "The visitors played badminton yesterdayed.", "The visitors plaied badminton."],
      "played 是 play 的过去式。"),
])

R("rw_wknd", "读周末日记", 7, "下", 12,
  "读一篇周末日记，找出活动和同伴。", "read_detail", [
    q("On Saturday morning I went to the lake with my father. We went fishing. 星期六上午他和谁去的？", "他的爸爸",
      ["他的妈妈", "同学", "游客"], "with my father。"),
    q("On Saturday morning I went to the lake with my father. We went fishing. 他们做了什么？", "钓鱼",
      ["打羽毛球", "去海滩", "参观农场"], "went fishing。"),
    q("On Sunday Lisa stayed at home and read a book. She did not play badminton. 她打羽毛球了吗？", "没有",
      ["打了", "和爸爸打了", "短文没说"], "did not play badminton。"),
    q("On Sunday Lisa stayed at home and read a book. 哪一句和日记一致？", "Lisa read at home on Sunday.",
      ["Lisa went to the lake on Sunday.", "Lisa played badminton.", "Lisa did not read."],
      "stayed at home and read a book。"),
])
