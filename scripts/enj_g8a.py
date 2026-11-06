# -*- coding: utf-8 -*-
"""八年级上册。人教版 Go for it! 通行目录，单元名与册次待核。"""
from en_tx import V, P, G, F, R
from enj_g7a import PENDING


def q(prompt, answer, wrongs, expl):
    return ("c", prompt, answer, wrongs, expl)


P("ph_link", "辅音与元音连读", 7, "上", 90,
  "能判断辅音结尾的词和元音开头的词能否连读。" + PENDING, "link", [
    q("an apple 里，哪个音可以和后面的元音连读？", "n 和 a",
      ["a 和 n 拆开重读", "两个词都要停顿", "只连读 pple"],
      "an 以辅音 n 结尾，apple 以元音开头，n 可以连到后面。"),
    q("哪一个短语适合把前一个词的辅音连到后一个词？", "look at",
      ["big dog", "stop class", "good time"],
      "look 以辅音结尾，at 以元音开头。其余短语是辅音接辅音。"),
    q("not at all 连读时，主要连在哪里？", "t 和 a 之间",
      ["n 和 o 之间", "ll 后面再加一个词", "三个词各自停住"],
      "at 的 t 和 all 的 a 可以连读。"),
    q("哪一种情况通常可以连读？", "辅音结尾，后面单词以元音开头",
      ["两个单词都以辅音结尾", "句号后面必须连读", "每个音节都重读"],
      "连读常见于辅音加元音。"),
])

V("vo_vac", "假期地点", 8, "上", 1,
  "认读 vacation、beach、museum 和 mountain。",
  [("vacation", "假期"), ("beach", "海滩"), ("museum", "博物馆"), ("mountain", "山")], "vocab8")

G("gr_past8", "一般过去时叙述假期", 8, "上", 1,
  "能用一般过去时说出假期去了哪里、做了什么。", "past", [
    q("假期去了北京。哪一句正确？", "I went to Beijing on vacation.",
      ["I go to Beijing on vacation last month.", "I goed to Beijing on vacation.", "I went to Beijing on vacation tomorrow."],
      "went 是 go 的过去式，时间是已经过去的假期。"),
    q("她在海滩拍了照。哪一句正确？", "She took photos on the beach.",
      ["She takes photos on the beach yesterday.", "She taked photos on the beach.", "She took photos on the beach tomorrow."],
      "take 的过去式是 took。"),
    q("Where did you go on vacation? 这句在问什么？", "你假期去了哪里",
      ["你假期将去哪里", "你正在去哪里", "你通常在哪里度假"],
      "did 加过去的假期，问已经去过的地方。"),
    q("我们没有去爬山。哪一句正确？", "We didn't go to the mountains.",
      ["We didn't went to the mountains.", "We don't went to the mountains.", "We didn't goes to the mountains."],
      "didn't 后面用动词原形 go。"),
])

F("fu_vac", "谈论假期去向", 8, "上", 1,
  "能询问和回答假期去了哪里。", "func_plan", [
    q("想问同学假期去了哪里，哪一句合适？", "Where did you go on vacation?",
      ["Where did you went on vacation?", "Where do you go on vacation yesterday?", "Where did you go on vacation tomorrow?"],
      "Where did you go 用来询问过去的去向。"),
    q("你去了博物馆，应怎么回答？", "I went to the museum.",
      ["I go to the museum yesterday.", "I was go to the museum.", "I went the museum."],
      "went to 后面接地点。"),
    q("对方说 It was great. 这是在评价什么？", "那段经历很好",
      ["明天会很好", "他不喜欢任何地方", "他正在出发"],
      "was 说明已经发生的假期很好。"),
    q("想说食物不好吃，哪一句合适？", "The food was terrible.",
      ["The food is terrible yesterday.", "The food were terrible.", "The food was terrible tomorrow."],
      "food 作整体，用 was。"),
])

R("rw_vac", "读假期短文", 8, "上", 1,
  "读一篇假期短文，找出地点和活动。", "read_detail", [
    q("Gina went to the beach on vacation. She swam and took photos. The food was great. 她去了哪里？", "海滩",
      ["博物馆", "山上", "学校"], "went to the beach。"),
    q("Gina went to the beach on vacation. She swam and took photos. 她做了什么？", "游泳并拍照",
      ["只待在家里", "去爬山", "参观农场"], "swam and took photos。"),
    q("Tom stayed at home. He did not go to the museum. He read a book. 他去博物馆了吗？", "没有",
      ["去了", "和 Gina 一起去了", "短文没说"], "did not go to the museum。"),
    q("Tom stayed at home. He read a book. 哪一句和短文一致？", "Tom read a book at home.",
      ["Tom went to the beach.", "Tom took photos at the museum.", "Tom did not read."],
      "他待在家里看书。"),
])

V("vo_habit", "运动习惯", 8, "上", 2,
  "认读 exercise、hardly、twice 和 Internet。",
  [("exercise", "锻炼"), ("hardly", "几乎不"), ("twice", "两次"), ("Internet", "互联网")], "vocab8")

G("gr_howoften", "How often 问频率", 8, "上", 2,
  "能用 How often 提问，并用 once、twice 或 hardly ever 回答。", "question", [
    q("想问对方多久锻炼一次，哪一句正确？", "How often do you exercise?",
      ["How often you exercise?", "How long do you exercise once?", "How far do you exercise?"],
      "How often 问频率，后面用助动词 do。"),
    q("我一周两次。哪一句正确？", "I exercise twice a week.",
      ["I exercise two time a week.", "I exercise twice week.", "I exercise a twice week."],
      "twice a week 表示一周两次。"),
    q("hardly ever 的意思是哪一个？", "几乎从不",
      ["每天", "一周三次", "只在昨天"], "hardly ever 表示频率非常低。"),
    q("She uses the Internet every day. 这句说明什么？", "她每天上网",
      ["她几乎不上网", "她一周上一次", "她昨天没上网"], "every day 是每天。"),
])

F("fu_habit", "谈论锻炼频率", 8, "上", 2,
  "能询问别人的习惯，并说出自己的频率。", "func_life", [
    q("医生问你多久运动一次，哪一句是这个问题？", "How often do you exercise?",
      ["How old do you exercise?", "What time is exercise yesterday?", "How many exercise are you?"],
      "How often 用来问习惯的频率。"),
    q("你几乎不喝牛奶，应怎么说？", "I hardly ever drink milk.",
      ["I hardly ever drank milk tomorrow.", "I hard ever drink milk.", "I hardly ever drinking milk."],
      "hardly ever 放在实义动词前面。"),
    q("对方回答 Three times a week. 这是在说什么？", "一周三次",
      ["三点钟", "三公里", "三个人"], "times a week 表示每周几次。"),
    q("想建议对方多运动，哪一句合适？", "You should exercise more.",
      ["You should exercises more.", "You should to exercise more.", "You should exercising more."],
      "should 后面用动词原形。"),
])

R("rw_habit", "读锻炼调查", 8, "上", 2,
  "读一段调查，找出谁运动得多。", "read_detail", [
    q("Jack exercises every day. Mary exercises twice a week. Peter hardly ever exercises. 谁每天锻炼？", "Jack",
      ["Mary", "Peter", "没有人"], "Jack exercises every day。"),
    q("Jack exercises every day. Mary exercises twice a week. Peter hardly ever exercises. 谁几乎不锻炼？", "Peter",
      ["Jack", "Mary", "三个人一样"], "Peter hardly ever exercises。"),
    q("Mary uses the Internet once a week. She reads books every night. 她多久上一次网？", "一周一次",
      ["每天", "几乎从不", "一周两次"], "once a week。"),
    q("Mary uses the Internet once a week. She reads books every night. 哪一句和短文一致？", "Mary reads every night.",
      ["Mary never reads.", "Mary uses the Internet every day.", "Mary hardly ever reads."],
      "reads books every night。"),
])

P("ph_plos", "不完全爆破", 7, "上", 90,
  "能识别两个爆破音相邻时，前一个音不完全爆破。" + PENDING, "plosion", [
    q("sit down 里，哪一个音常常不完全发出来？", "sit 里的 t",
      ["down 里的 n", "sit 里的 s", "down 里的 d"],
      "t 后面紧接爆破音 d，t 通常不完全爆破。"),
    q("哪一个短语有不完全爆破？", "good time",
      ["my apple", "to a park", "an old man"],
      "good 的 d 和 time 的 t 都是爆破音，相邻时前一个不完全爆破。"),
    q("big kite 里，不完全爆破发生在哪里？", "g 和 k 之间",
      ["b 和 i 之间", "k 和 i 之间", "词尾 e 后面"],
      "big 的 g 和 kite 的 k 是相邻爆破音。"),
    q("不完全爆破通常出现在什么时候？", "两个爆破音挨在一起",
      ["元音后面是句号", "单词只有一个音节", "句末用升调"],
      "前一个爆破音受后一个爆破音影响，常常听不全。"),
])

V("vo_person", "性格形容词", 8, "上", 3,
  "认读 outgoing、serious、loud 和 quiet。",
  [("outgoing", "外向的"), ("serious", "严肃的"), ("loud", "声音大的"), ("quiet", "安静的")], "vocab8")

G("gr_comp8", "形容词比较级", 8, "上", 3,
  "能把形容词变成比较级，包括 -er 和 more。", "compare", [
    q("tall 的比较级是哪一个？", "taller",
      ["more tall", "tallest", "more taller"], "单音节词 tall 加 er。"),
    q("outgoing 的比较级是哪一个？", "more outgoing",
      ["outgoinger", "more outgoinger", "outgoingest"], "多音节词 outgoing 前面加 more。"),
    q("good 的比较级是哪一个？", "better",
      ["gooder", "more good", "best"], "good 的比较级是 better。"),
    q("哪一句使用了比较级？", "Tom is quieter than Sam.",
      ["Tom is quiet.", "Tom is the quietest boy.", "Tom is a quiet boy in Class 2."],
      "quieter 是 quiet 的比较级。"),
])

G("gr_than8", "用 than 比较", 8, "上", 3,
  "能用 than 比较两个人或两件事。", "compare", [
    q("她比她姐姐外向。哪一句正确？", "She is more outgoing than her sister.",
      ["She is more outgoinger than her sister.", "She is outgoing than her sister.", "She is more outgoing that her sister."],
      "more outgoing 后面用 than。"),
    q("我的头发比她的短。哪一句正确？", "My hair is shorter than hers.",
      ["My hair is more short than hers.", "My hair is shorter that hers.", "My hair is short than hers."],
      "shorter than 比较两者。"),
    q("哪一句是在比较两个人？", "Paul is taller than his brother.",
      ["Paul is tall.", "Paul is a student.", "Paul likes basketball."],
      "taller than 说明 Paul 更高。"),
    q("两者当中，谁更高，问法哪一句正确？", "Who is taller, Tom or Jack?",
      ["Who is tallest, Tom or Jack?", "Who is more taller, Tom or Jack?", "Who is the taller than Tom or Jack?"],
      "两个人用比较级 taller，不用最高级。"),
])

F("fu_cmp", "比较两人", 8, "上", 3,
  "能说出两个人的不同性格或外貌。", "func_life", [
    q("想说朋友比你更严肃，哪一句合适？", "My friend is more serious than me.",
      ["My friend is seriouser than me.", "My friend is more seriouser than me.", "My friend more serious than me."],
      "serious 的比较级是 more serious。"),
    q("对方问 Is Tara more outgoing than Tina? 你认为是，应回答什么？", "Yes, she is.",
      ["Yes, she does.", "Yes, she can.", "Yes, she more."],
      "问句用 is，肯定简答 Yes, she is。"),
    q("想说两个人都很安静，哪一句合适？", "They are both quiet.",
      ["They are both quieter than.", "They both is quiet.", "They are both more quiet than."],
      "both 表示两者都，这里不需要 than。"),
    q("哪一句在询问差别？", "How are you different from your sister?",
      ["How old is the classroom?", "What time is different yesterday?", "Where is than?"],
      "different from 用来问和别人有什么不同。"),
])

R("rw_cmp", "读人物比较", 8, "上", 3,
  "读一段比较，判断谁更高、谁更外向。", "read_detail", [
    q("Tara is taller than Tina. Tina is more outgoing than Tara. 谁更高？", "Tara",
      ["Tina", "两个人一样高", "短文没说"], "Tara is taller than Tina。"),
    q("Tara is taller than Tina. Tina is more outgoing than Tara. 谁更外向？", "Tina",
      ["Tara", "两个人一样外向", "老师"], "Tina is more outgoing。"),
    q("Paul is quieter than his brother. His brother is louder. 谁更安静？", "Paul",
      ["他的哥哥或弟弟", "两个人都大声", "短文没说"], "Paul is quieter。"),
    q("Paul is quieter than his brother. 哪一句和短文一致？", "Paul's brother is louder than Paul.",
      ["Paul is louder than his brother.", "Paul is more outgoing than his brother.", "They are the same."],
      "哥哥或弟弟更 loud，也就是没有 Paul 安静。"),
])

V("vo_town", "城镇设施", 8, "上", 4,
  "认读 theater、screen、seat 和 service。",
  [("theater", "剧院"), ("screen", "屏幕"), ("seat", "座位"), ("service", "服务")], "vocab8")

G("gr_super", "形容词最高级", 8, "上", 4,
  "能用最高级比较三个或三个以上的人或物。", "compare", [
    q("三个男孩中 Tom 最高。哪一句正确？", "Tom is the tallest of the three boys.",
      ["Tom is the taller of the three boys.", "Tom is tallest of the three boys.", "Tom is the most tall of the three boys."],
      "三者以上用 the tallest。"),
    q("popular 的最高级是哪一个？", "the most popular",
      ["the popularer", "the most popularer", "popularest"],
      "多音节词前面加 the most。"),
    q("good 的最高级是哪一个？", "best",
      ["goodest", "most good", "better"], "good 的最高级是 best。"),
    q("哪一句使用了最高级？", "This is the best theater in town.",
      ["This theater is better than that one.", "This theater is good.", "This is a theater."],
      "the best 是最高级。"),
])

F("fu_best", "谈论最好的地方", 8, "上", 4,
  "能询问和回答某个地方是不是最好的。", "func_life", [
    q("想问哪家影院最舒服，哪一句合适？", "Which theater has the most comfortable seats?",
      ["Which theater has the comfortablest seats?", "Which theater has more comfortable seats of all?", "Which theater has the most comfortable seatest?"],
      "comfortable 的最高级是 the most comfortable。"),
    q("你认为屏幕最大，应怎么说？", "It has the biggest screen.",
      ["It has the most big screen.", "It has the bigger screen of all the town.", "It has biggest screen."],
      "big 的最高级是 the biggest。"),
    q("What's the best movie theater? 这句在问什么？", "最好的电影院是哪一家",
      ["电影院在哪里", "票价是多少", "你昨天看了什么"],
      "the best 问三者以上当中最好的。"),
    q("想说服务最差，哪一句合适？", "It has the worst service.",
      ["It has the most bad service.", "It has the worse service of all.", "It has the baddest service."],
      "bad 的最高级是 worst。"),
])

R("rw_best", "读影院介绍", 8, "上", 4,
  "读一段城镇介绍，找出最好的设施。", "read_detail", [
    q("Town Cinema has the biggest screen. It has the most comfortable seats. 最大的屏幕在哪里？", "Town Cinema",
      ["学校", "家里", "短文没说"], "Town Cinema has the biggest screen。"),
    q("Town Cinema has the biggest screen. It has the most comfortable seats. 座位怎么样？", "最舒服",
      ["最少", "比别家更差", "短文没说"], "the most comfortable seats。"),
    q("Movie World is the cheapest, but the service is the worst. 最便宜的是哪一家？", "Movie World",
      ["Town Cinema", "两家一样", "短文没说"], "Movie World is the cheapest。"),
    q("Movie World is the cheapest, but the service is the worst. 哪一句和短文一致？", "Movie World has the worst service.",
      ["Movie World has the best service.", "Town Cinema is the cheapest.", "The seats are the worst."],
      "便宜，但是服务最差。"),
])

V("vo_show", "电视节目", 8, "上", 5,
  "认读 sitcom、news、educational 和 cartoon。",
  [("sitcom", "情景喜剧"), ("news", "新闻"), ("educational", "有教育意义的"), ("cartoon", "动画片")], "vocab8")

G("gr_to", "不定式作宾语", 8, "上", 5,
  "能在 want、plan、hope 和 expect 后面使用 to 加动词原形。", "to_ing", [
    q("我想看新闻。哪一句正确？", "I want to watch the news.",
      ["I want watch the news.", "I want watching the news.", "I want to watching the news."],
      "want 后面用 to watch。"),
    q("她计划学习医学。哪一句正确？", "She plans to study medicine.",
      ["She plans study medicine.", "She plans studying medicine.", "She plan to study medicine."],
      "plan 加 s，后面用 to study。"),
    q("hope 后面应接哪一种形式？", "to 加动词原形",
      ["动词加 ing 必须接在 hope 后", "动词过去式", "名词复数"],
      "hope to do something。"),
    q("他们期望明天到达。哪一句正确？", "They expect to arrive tomorrow.",
      ["They expect arriving tomorrow.", "They expect arrive tomorrow.", "They expect to arrived tomorrow."],
      "expect to arrive。"),
])

F("fu_show", "谈论想看的节目", 8, "上", 5,
  "能说出想看什么节目，并询问对方的看法。", "func_plan", [
    q("想约对方看情景喜剧，哪一句合适？", "Do you want to watch a sitcom?",
      ["Do you want watch a sitcom?", "Do you want to watching a sitcom?", "Are you want to watch a sitcom?"],
      "Do you want to watch。"),
    q("你觉得新闻有教育意义，应怎么说？", "I think the news is educational.",
      ["I think the news are educational.", "I think the news is education.", "I am think the news is educational."],
      "news 作节目名，这里用 is educational。"),
    q("What do you think of talk shows? 这句在问什么？", "你觉得谈话节目怎么样",
      ["谈话节目在几点", "你想成为主持人吗", "谈话节目是谁的"],
      "What do you think of 用来问评价。"),
    q("你不能忍受这个节目，哪一句合适？", "I can't stand it.",
      ["I can't stand watch it.", "I can't stands it.", "I am can't stand it."],
      "can't stand 后面可以直接接 it。"),
])

R("rw_show", "读节目选择", 8, "上", 5,
  "读一段对话，找出谁想看什么。", "read_detail", [
    q("Lisa wants to watch a cartoon. Tom plans to watch the news. 谁想看动画片？", "Lisa",
      ["Tom", "两个人都想看新闻", "老师"], "Lisa wants to watch a cartoon。"),
    q("Lisa wants to watch a cartoon. Tom plans to watch the news. Tom 打算看什么？", "新闻",
      ["动画片", "情景喜剧", "体育比赛"], "plans to watch the news。"),
    q("Gina hopes to watch an educational sitcom. She does not like scary shows. 她喜欢恐怖节目吗？", "不喜欢",
      ["喜欢", "只在周末看", "短文没说"], "does not like scary shows。"),
    q("Gina hopes to watch an educational sitcom. 哪一句和短文一致？", "Gina hopes to watch a sitcom.",
      ["Gina wants to watch the news.", "Gina likes scary shows.", "Gina plans to watch a cartoon."],
      "hopes to watch an educational sitcom。"),
])

V("vo_job8", "职业打算", 8, "上", 6,
  "认读 scientist、engineer、pilot 和 college。",
  [("scientist", "科学家"), ("engineer", "工程师"), ("pilot", "飞行员"), ("college", "大学")], "vocab8")

G("gr_going8", "be going to 表示打算", 8, "上", 6,
  "能用 be going to 说出已经决定的打算。", "future", [
    q("我打算学计算机。哪一句正确？", "I am going to study computer science.",
      ["I am going study computer science.", "I going to study computer science.", "I am go to study computer science."],
      "am going to 后面用动词原形。"),
    q("她打算当工程师。哪一句正确？", "She is going to be an engineer.",
      ["She is going to be a engineer.", "She are going to be an engineer.", "She is going to is an engineer."],
      "engineer 以元音开头，用 an。be 用原形。"),
    q("他们不打算上大学。哪一句正确？", "They are not going to go to college.",
      ["They are not going to goes to college.", "They not going to go to college.", "They are not go to college."],
      "否定是 be not going to。"),
    q("be going to 在这里主要表示什么？", "已经决定的打算",
      ["过去的习惯", "正在进行的动作", "对过去的推测"],
      "be going to 用来谈打算。"),
])

F("fu_dream", "谈论将来打算", 8, "上", 6,
  "能询问别人长大后想做什么，并说出自己的打算。", "func_plan", [
    q("想问对方长大后打算做什么，哪一句合适？", "What are you going to be when you grow up?",
      ["What are you going to be when you grew up?", "What do you going to be when you grow up?", "What are you going be when you grow up?"],
      "are you going to be。"),
    q("你打算当飞行员，应怎么说？", "I am going to be a pilot.",
      ["I am going to be an pilot.", "I am going to am a pilot.", "I going to be a pilot."],
      "pilot 以辅音音素开头，用 a。"),
    q("How are you going to do that? 这句在问什么？", "你打算怎样做到",
      ["你现在在做什么", "你去年做了什么", "你要去哪里度假"],
      "How are you going to 问实现打算的方式。"),
    q("想说打算多练习，哪一句合适？", "I am going to practice every day.",
      ["I am going to practicing every day.", "I am going practice every day.", "I am going to practiced every day."],
      "going to practice。"),
])

R("rw_dream", "读计划短文", 8, "上", 6,
  "读一段计划，找出职业和行动。", "read_detail", [
    q("Ken is going to be a scientist. He is going to study hard. 他打算成为什么？", "科学家",
      ["飞行员", "工程师", "医生"], "be a scientist。"),
    q("Ken is going to be a scientist. He is going to study hard. 他打算怎么做？", "努力学习",
      ["每天游泳", "去当飞行员", "不上学"], "study hard。"),
    q("Lucy is going to college. She is not going to be a pilot. 她打算当飞行员吗？", "不打算",
      ["打算", "已经是飞行员", "短文没说"], "is not going to be a pilot。"),
    q("Lucy is going to college. 哪一句和短文一致？", "Lucy is going to go to college.",
      ["Lucy is going to be a pilot.", "Lucy was a scientist.", "Lucy is not going to college."],
      "is going to college。"),
])

V("vo_future", "未来生活", 8, "上", 7,
  "认读 robot、pollution、prediction 和 future。",
  [("robot", "机器人"), ("pollution", "污染"), ("prediction", "预测"), ("future", "将来")], "vocab8")

G("gr_will", "will 表示将来", 8, "上", 7,
  "能用 will 预测将来或表达临时决定。", "future", [
    q("人们将会有机器人。哪一句正确？", "People will have robots.",
      ["People will has robots.", "People will to have robots.", "People will having robots."],
      "will 后面用动词原形 have。"),
    q("将会有更少的污染。哪一句正确？", "There will be less pollution.",
      ["There will have less pollution.", "There will be less pollution yesterday.", "There will to be less pollution."],
      "There will be 表示将会有。"),
    q("我来帮你。这是临时决定，哪一句合适？", "I will help you.",
      ["I will helped you.", "I will to help you.", "I helping you tomorrow now."],
      "临时决定常用 will。"),
    q("will 的否定式是哪一个？", "will not",
      ["willn't doed", "do will not", "not will to"],
      "will not 可以缩写成 won't。"),
])

F("fu_predict", "预测未来", 8, "上", 7,
  "能询问别人对未来的看法，并作出预测。", "func_plan", [
    q("想问一百年后会有什么，哪一句合适？", "What will the world be like in 100 years?",
      ["What will the world be like 100 years ago?", "What is the world be like in 100 years?", "What will the world like in 100 years?"],
      "in 100 years 表示一百年之后，用 will。"),
    q("你预测孩子会在家里上课，应怎么说？", "Kids will study at home.",
      ["Kids will studies at home.", "Kids will study at home yesterday.", "Kids will to study at home."],
      "will study。"),
    q("Do you think there will be more trees? 认为会有，应回答什么？", "Yes, I think so.",
      ["Yes, I think not so.", "Yes, there was.", "No, I think so there will."],
      "同意这个预测可以说 Yes, I think so。"),
    q("想说自己不同意，哪一句合适？", "No, I don't think so.",
      ["No, I am not think so.", "No, I doesn't think so.", "No, I don't thinks so."],
      "I don't think so 表示不这么认为。"),
])

R("rw_future", "读未来预测", 8, "上", 7,
  "读一段预测，判断将会发生什么。", "read_detail", [
    q("In 50 years, people will have robots at home. There will be less pollution. 家里将会有什么？", "机器人",
      ["更多污染", "纸质书", "马车"], "will have robots at home。"),
    q("In 50 years, people will have robots at home. There will be less pollution. 污染会怎样？", "更少",
      ["更多", "和现在完全一样", "短文没说"], "less pollution。"),
    q("Joe thinks cities will be more crowded. He will live on a space station. 他将住在哪里？", "太空站",
      ["海底", "乡下", "学校宿舍"], "live on a space station。"),
    q("Joe thinks cities will be more crowded. 哪一句和短文一致？", "Joe thinks cities will be more crowded.",
      ["Joe thinks there will be no cities.", "Joe will live on a farm.", "People will not have robots."],
      "cities will be more crowded。"),
])

V("vo_cook", "烹饪用词", 8, "上", 8,
  "认读 yogurt、honey、spoon 和 blender。",
  [("yogurt", "酸奶"), ("honey", "蜂蜜"), ("spoon", "勺子"), ("blender", "搅拌器")], "vocab8")

G("gr_seq", "顺序词 first、next、then", 8, "上", 8,
  "能用顺序词和祈使句说明步骤。", "sentence", [
    q("先把香蕉剥开。哪一句正确？", "First, peel the bananas.",
      ["First, peeling the bananas.", "First, to peel the bananas.", "First, peeled the bananas."],
      "说明步骤用祈使句，动词用原形。"),
    q("然后加入蜂蜜。哪一句正确？", "Then add the honey.",
      ["Then adding the honey.", "Then to add the honey.", "Then added the honey yesterday."],
      "Then 后面接动词原形。"),
    q("哪一个词用来连接下一个步骤？", "Next",
      ["Yesterday", "Because", "Although"],
      "Next 表示接下来。"),
    q("最后把奶昔倒进杯子。哪一句正确？", "Finally, pour the milk shake into a glass.",
      ["Finally, pours the milk shake into a glass.", "Finally, pouring the milk shake into a glass.", "Finally, to pour the milk shake into a glass."],
      "祈使句用 pour，不加 s。"),
])

F("fu_recipe", "说明做法", 8, "上", 8,
  "能询问食物怎么做，并按顺序回答。", "func_life", [
    q("想问香蕉奶昔怎么做，哪一句合适？", "How do you make a banana milk shake?",
      ["How do you makes a banana milk shake?", "How are you make a banana milk shake?", "How did you make a banana milk shake tomorrow?"],
      "How do you make。"),
    q("需要两勺蜂蜜，应怎么说？", "We need two spoons of honey.",
      ["We need two spoon of honey.", "We need two spoons of honeys.", "We need two spoon honey."],
      "two spoons of honey。"),
    q("How much yogurt do we need? 这句在问什么？", "需要多少酸奶",
      ["酸奶怎么拼", "酸奶在哪里卖", "谁喜欢酸奶"],
      "How much 问不可数名词的量。"),
    q("让对方打开搅拌器，哪一句合适？", "Turn on the blender.",
      ["Turns on the blender.", "Turning on the blender.", "To turn on the blender."],
      "祈使句用动词原形。"),
])

R("rw_recipe", "读食谱", 8, "上", 8,
  "读一份食谱，找出材料和顺序。", "read_detail", [
    q("First, peel two bananas. Next, put them into the blender. Then add honey. 第一步做什么？", "剥香蕉",
      ["加蜂蜜", "打开杯子", "倒奶昔"], "First, peel two bananas。"),
    q("First, peel two bananas. Next, put them into the blender. 香蕉放进哪里？", "搅拌器",
      ["杯子", "勺子", "冰箱"], "into the blender。"),
    q("We need one spoon of honey and a cup of yogurt. 蜂蜜要多少？", "一勺",
      ["一杯", "两勺", "不要蜂蜜"], "one spoon of honey。"),
    q("Finally, pour the milk shake into a glass. 哪一句和食谱一致？", "The last step is to pour it into a glass.",
      ["The first step is to pour it into a glass.", "We do not use yogurt.", "We peel the honey."],
      "Finally 是最后一步。"),
])

V("vo_party", "聚会活动", 8, "上", 9,
  "认读 invitation、preparation、concert 和 available。",
  [("invitation", "邀请"), ("preparation", "准备"), ("concert", "音乐会"), ("available", "有空的")], "vocab8")

G("gr_invite", "用 can 发出邀请", 8, "上", 9,
  "能用 Can you 邀请别人，并用情态动词回答。", "modal", [
    q("邀请对方来聚会，哪一句正确？", "Can you come to my party?",
      ["Can you to come to my party?", "Do you can come to my party?", "Can you coming to my party?"],
      "Can you 后面用动词原形。"),
    q("你很乐意去，哪一句正确？", "Sure, I would love to.",
      ["Sure, I would love.", "Sure, I would love coming.", "Sure, I will love to went."],
      "would love to 后面省略了 come。"),
    q("那天你得去看医生，哪一句正确？", "I have to see the doctor.",
      ["I have to seeing the doctor.", "I has to see the doctor.", "I have see the doctor."],
      "have to 后面用动词原形。"),
    q("Can you come to the concert? 这句主要是在做什么？", "发出邀请",
      ["询问票价", "描述过去", "比较两场音乐会"],
      "Can you come 常用来邀请。"),
])

F("fu_invite", "接受或拒绝邀请", 8, "上", 9,
  "能接受邀请，或说明为什么不能去。", "func_plan", [
    q("对方邀请你星期六来，你能来，应怎么说？", "Sure. I am available on Saturday.",
      ["Sure. I was available on Saturday tomorrow.", "Sure. I am available in Saturday.", "Sure. I available on Saturday."],
      "on Saturday，并且要有 am。"),
    q("你不能去，因为要准备考试。哪一句合适？", "Sorry, I have to prepare for a test.",
      ["Sorry, I have to preparing for a test.", "Sorry, I has to prepare for a test.", "Sorry, I have prepare for a test."],
      "have to prepare。"),
    q("想问对方星期二是否有空，哪一句合适？", "Are you available on Tuesday?",
      ["Do you available on Tuesday?", "Are you available in Tuesday?", "Are you available at Tuesday?"],
      "星期前用 on，available 前面用 are。"),
    q("对方说 I might have to meet my friend. 这是什么意思？", "他可能得去见朋友",
      ["他一定能来", "他昨天见了朋友", "他不想有朋友"],
      "might have to 表示可能不得不。"),
])

R("rw_invite", "读邀请函", 8, "上", 9,
  "读一封邀请，找出时间、地点和谁不能来。", "read_detail", [
    q("Please come to my party on Sunday at 7. It is at my house. 聚会在星期几？", "星期日",
      ["星期六", "星期一", "星期五"], "on Sunday。"),
    q("Please come to my party on Sunday at 7. It is at my house. 在哪里举行？", "在我家里",
      ["在学校", "在音乐会", "在医院"], "at my house。"),
    q("Anna can come. Jeff has to prepare for a test, so he cannot come. 谁不能来？", "Jeff",
      ["Anna", "两个人都能来", "短文没说"], "Jeff cannot come。"),
    q("Anna can come. Jeff has to prepare for a test. 哪一句和邀请函一致？", "Jeff is not available because of a test.",
      ["Anna cannot come.", "The party is on Monday.", "Jeff will come to the party."],
      "Jeff 要准备考试，不能来。"),
])

P("ph_pause", "意群停顿", 8, "上", 10,
  "能按意群停顿，不把一个意思从中间拆开。", "pause", [
    q("I went to the park with my father. 哪一种停顿更好？", "I went to the park / with my father.",
      ["I went to / the park with my father.", "I / went to the park with my father only after every word", "went to the / park"],
      "to the park 是一个意群，不宜在 to 后面断开。"),
    q("哪一个位置不适合停顿？", "把 look at 拆成 look / at",
      ["句号后面", "逗号后面", "一个完整意群结束的地方"],
      "look at 通常连在一起，不从中间拆开。"),
    q("If it rains, I will stay at home. 逗号处可以怎样处理？", "可以停顿",
      ["必须连读过去", "必须重读逗号", "不能换气"],
      "逗号常常是意群的边界。"),
    q("按意群朗读是为了什么？", "让意思更清楚",
      ["让每个字母都重读", "取消所有停顿", "只在单词中间停"],
      "意群停顿帮助听的人理解句子。"),
])

V("vo_advice", "建议用词", 8, "上", 10,
  "认读 advice、organize、upset 和 careless。",
  [("advice", "建议"), ("organize", "组织"), ("upset", "心烦的"), ("careless", "粗心的")], "vocab8")

G("gr_if", "if 条件状语从句", 8, "上", 10,
  "能用 if 引导条件从句，主句用 will，if 从句用一般现在时。", "clause_adv", [
    q("如果明天下雨，我就待在家里。哪一句正确？", "If it rains tomorrow, I will stay at home.",
      ["If it will rain tomorrow, I will stay at home.", "If it rains tomorrow, I stayed at home.", "If it rain tomorrow, I will stay at home."],
      "if 从句用 rains，主句用 will stay。"),
    q("如果你去聚会，你会玩得很开心。哪一句正确？", "If you go to the party, you will have a great time.",
      ["If you will go to the party, you have a great time.", "If you go to the party, you had a great time.", "If you went to the party, you will have a great time tomorrow."],
      "从句 go，主句 will have。"),
    q("if 条件从句表示将来时，动词常用哪一种时态？", "一般现在时",
      ["过去完成时", "will 加动词", "过去进行时"],
      "条件从句里通常不用 will。"),
    q("如果他来，请告诉我。哪一句正确？", "If he comes, please tell me.",
      ["If he will come, please tell me.", "If he come, please tell me.", "If he comes, please told me."],
      "he 后面用 comes，祈使句用 tell。"),
])

F("fu_if", "用条件句给建议", 8, "上", 10,
  "能用 if 提醒对方某种做法会带来什么结果。", "func_plan", [
    q("想劝对方别吃太多，否则会不舒服，哪一句合适？", "If you eat too much, you will feel sick.",
      ["If you will eat too much, you feel sick.", "If you eat too much, you felt sick tomorrow.", "If you eats too much, you will feel sick."],
      "if you eat，主句 will feel。"),
    q("想说组织好聚会就会成功，哪一句合适？", "If you organize it well, the party will be great.",
      ["If you will organize it well, the party is great yesterday.", "If you organize it well, the party was great tomorrow.", "If you organizes it well, the party will be great."],
      "organize 用原形，主句用 will be。"),
    q("What will happen if they have the party today? 这句在问什么？", "如果今天开聚会会发生什么",
      ["他们昨天开了什么聚会", "聚会在哪个教室", "谁没有受到邀请"],
      "What will happen if 询问可能的结果。"),
    q("朋友很心烦，你想建议他离开吵闹的聚会。哪一句合适？", "If you leave now, you will feel better.",
      ["If you will leave now, you feel better.", "If you leave now, you felt better.", "If you leaving now, you will feel better."],
      "leave 用一般现在时，结果用 will feel。"),
])

R("rw_if", "读聚会建议", 8, "上", 10,
  "读一段建议，找出条件和结果。", "read_detail", [
    q("If you wear jeans, the teacher will not let you in. If you take a bus, you will be late. 穿牛仔裤会怎样？", "老师不让进",
      ["会很早到", "会得到礼物", "短文没说"], "will not let you in。"),
    q("If you wear jeans, the teacher will not let you in. If you take a bus, you will be late. 坐公交会怎样？", "会迟到",
      ["会很安静", "老师会表扬", "不会迟到"], "you will be late。"),
    q("If we organize the games well, everyone will have fun. 大家会玩得开心的条件是什么？", "把游戏组织好",
      ["穿牛仔裤", "迟到", "不准备"], "If we organize the games well。"),
    q("If we organize the games well, everyone will have fun. 哪一句和短文一致？", "Good organization will help everyone have fun.",
      ["Everyone will have fun if nobody organizes the games.", "The teacher will let jeans in.", "Taking a bus will make them early."],
      "组织好，大家就会玩得开心。"),
])
