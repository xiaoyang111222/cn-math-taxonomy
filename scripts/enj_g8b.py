# -*- coding: utf-8 -*-
"""八年级下册。人教版（根据2022年版课程标准修订），2026-11-11 官方阅读器已核。

正式单元 1–8 见 enj_build.UNITS。对不上官方课的点用 unit 90，章节为「八年级下册 待核」。
故事三点仍在七年级下册第8单元。家务四点在八年级上册第2单元 Home Sweet Home。
"""
from en_tx import V, P, G, F, R


def q(prompt, answer, wrongs, expl):
    return ("c", prompt, answer, wrongs, expl)


V("vo_health", "身体不适", 8, "下", 2,
  "认读 headache、stomachache、fever 和 cough。",
  [("headache", "头痛"), ("stomachache", "胃痛"), ("fever", "发烧"), ("cough", "咳嗽")], "vocab8")

G("gr_should8", "should 表示建议", 8, "下", 2,
  "能用 should 或 shouldn't 提出建议。", "modal", [
    q("你应该去看医生。哪一句正确？", "You should see a doctor.",
      ["You should to see a doctor.", "You should sees a doctor.", "You should seeing a doctor."],
      "should 后面用动词原形。"),
    q("你不该吃这么多。哪一句正确？", "You shouldn't eat so much.",
      ["You shouldn't to eat so much.", "You shouldn't eats so much.", "You don't should eat so much."],
      "shouldn't 后面用动词原形。"),
    q("她牙痛，哪一条建议合适？", "She should see a dentist.",
      ["She should sees a dentist.", "She should to see a dentist.", "She should seeing a dentist."],
      "should see。"),
    q("should 在这些句子里表示什么？", "建议",
      ["过去的事实", "正在进行", "已经完成"],
      "should 用来告诉别人宜做什么。"),
])

F("fu_health", "关心身体", 8, "下", 2,
  "能询问别人怎么了，并给出简单建议。", "func_life", [
    q("看到同学不舒服，哪一句合适？", "What's the matter?",
      ["What's the matter yesterday happened?", "What the matter is you?", "How the matter are you?"],
      "What's the matter 用来问出了什么问题。"),
    q("你头痛，应怎么说？", "I have a headache.",
      ["I have headache.", "I has a headache.", "I have an headache."],
      "have a headache。"),
    q("对方发烧了，你建议他躺下。哪一句合适？", "You should lie down and rest.",
      ["You should lies down and rest.", "You should to lie down and rest.", "You should lying down and rest."],
      "should lie。"),
    q("对方说 I have a cough. 你还想问持续多久，哪一句合适？", "How long have you had it?",
      ["How long did you had it tomorrow?", "How far have you had it?", "How often you have it yesterday now?"],
      "How long 问持续了多久。"),
])

R("rw_health", "读健康建议", 8, "下", 2,
  "读一段对话，找出症状和建议。", "read_detail", [
    q("Ben has a stomachache. The doctor says he should not eat cold food. 他怎么了？", "胃痛",
      ["头痛", "咳嗽", "牙疼"], "has a stomachache。"),
    q("Ben has a stomachache. The doctor says he should not eat cold food. 医生建议他怎样？", "别吃冷的食物",
      ["多吃冰淇淋", "去跑步", "不休息"], "should not eat cold food。"),
    q("Lisa has a fever and a cough. She should drink more water. 她应该做什么？", "多喝水",
      ["少喝水", "吃更多糖", "短文没说"], "should drink more water。"),
    q("Lisa has a fever and a cough. 哪一句和短文一致？", "Lisa has both a fever and a cough.",
      ["Lisa only has a headache.", "Lisa should not drink water.", "Ben has a fever in this sentence."],
      "fever and a cough 都有。"),
])

V("vo_vol", "志愿服务", 8, "下", 8,
  "认读 volunteer、lonely、sign 和 notice。",
  [("volunteer", "志愿者"), ("lonely", "孤独的"), ("sign", "标牌"), ("notice", "通知")], "vocab8")

G("gr_purpose", "不定式表示目的", 8, "下", 1,
  "能用 to 加动词原形说明做某事的目的。", "to_ing", [
    q("我去公园是为了做志愿者。哪一句正确？", "I went to the park to volunteer.",
      ["I went to the park for volunteer.", "I went to the park volunteering.", "I went to the park to volunteering."],
      "to volunteer 表示目的。"),
    q("她张贴通知是为了找帮手。哪一句正确？", "She put up a notice to find helpers.",
      ["She put up a notice find helpers.", "She put up a notice to found helpers.", "She put up a notice for find helpers."],
      "to find 表示目的。"),
    q("to do 放在句子后部，这里表示什么？", "目的",
      ["过去的时间", "比较的对象", "被动的动作"],
      "不定式可以说明为什么做这件事。"),
    q("他们筹款是为了帮助穷人。哪一句正确？", "They raise money to help the poor.",
      ["They raise money help the poor.", "They raise money to helping the poor.", "They raise money for to help the poor."],
      "to help 是目的。"),
])

F("fu_help", "主动提供帮助", 8, "下", 8,
  "能提出帮忙，并说明能做什么。", "func_plan", [
    q("想说自己可以发食物，哪一句合适？", "I could give out food.",
      ["I could to give out food.", "I could giving out food.", "I could gave out food."],
      "could 后面用动词原形。"),
    q("想问对方想参加志愿活动吗，哪一句合适？", "Would you like to help?",
      ["Would you like helping out yesterday?", "Do you would like to help?", "Would you like help?"],
      "Would you like to help。"),
    q("孤独的老人需要什么，哪一句说得清楚？", "They need someone to talk to.",
      ["They need someone talk to.", "They need someone to talking to.", "They need someone for talk."],
      "someone to talk to。"),
    q("I'll help to clean up the park. 这句是在做什么？", "提出帮忙打扫公园",
      ["拒绝打扫", "询问公园在哪里", "比较两座公园"],
      "I'll help to 表示愿意帮忙。"),
])

R("rw_help", "读志愿活动", 8, "下", 8,
  "读一则通知，找出时间和需要做的事。", "read_detail", [
    q("We need volunteers to clean up the city park on Saturday. Please call Mr. Li. 需要志愿者做什么？", "打扫城市公园",
      ["建造医院", "卖票", "开车"], "clean up the city park。"),
    q("We need volunteers to clean up the city park on Saturday. 在星期几？", "星期六",
      ["星期日", "星期一", "星期五"], "on Saturday。"),
    q("Anna wants to help. She will give out notices after school. 她放学后做什么？", "发通知",
      ["打扫自己的房间", "去看病", "待在家里"], "give out notices。"),
    q("Anna wants to help. She will give out notices after school. 哪一句和短文一致？", "Anna will hand out notices after school.",
      ["Anna will not help.", "The park clean-up is on Monday.", "Mr. Li will give out food at the hospital."],
      "give out notices after school。"),
])

V("vo_chore", "家务", 8, "上", 2,
  "认读 chore、rubbish、fold 和 sweep。",
  [("chore", "家务"), ("rubbish", "垃圾"), ("fold", "折叠"), ("sweep", "清扫")], "vocab8")

G("gr_could", "could 表示请求", 8, "上", 2,
  "能用 Could you please 礼貌地提出请求。", "modal", [
    q("请你打扫房间，好吗？哪一句正确？", "Could you please clean your room?",
      ["Could you please to clean your room?", "Could you please cleaning your room?", "Could you please cleaned your room?"],
      "Could you please 后面用动词原形。"),
    q("同意请求，哪一句合适？", "Yes, sure.",
      ["Yes, I could please.", "No, here you are not doing.", "Yes, I couldn't do it gladly."],
      "Yes, sure 表示同意。"),
    q("你不想出去倒垃圾。哪一句正确？", "I don't want to take out the rubbish.",
      ["I don't want take out the rubbish.", "I don't want to taking out the rubbish.", "I doesn't want to take out the rubbish."],
      "want to take。"),
    q("Could you please 比 Can you 怎样？", "更礼貌",
      ["只能用于过去", "后面必须加 ing", "不能用来请求"],
      "could 使请求更委婉。"),
])

F("fu_chore", "礼貌提出请求", 8, "上", 2,
  "能请求别人做家务，并礼貌应答。", "func_life", [
    q("想请弟弟叠衣服，哪一句合适？", "Could you please fold the clothes?",
      ["Could you please folds the clothes?", "Could you please to fold the clothes?", "Do you could fold the clothes?"],
      "Could you please fold。"),
    q("你正在做作业，不能扫地，应怎么说？", "Sorry, I am doing my homework.",
      ["Sorry, I do my homework now yesterday.", "Sorry, I doing my homework.", "Sorry, I am do my homework."],
      "am doing 表示正在做。"),
    q("Could I go out for dinner? 这句是在做什么？", "请求允许外出吃饭",
      ["命令别人做饭", "描述昨天的晚饭", "比较两家餐馆"],
      "Could I 用来请求允许。"),
    q("同意弟弟借用自行车，哪一句合适？", "Yes, you can. But please return it later.",
      ["Yes, you could please return yesterday.", "No, you can take it and never say.", "Yes, you can returns it."],
      "同意后可以补上一句请稍后归还。"),
])

R("rw_chore", "读家务对话", 8, "上", 2,
  "读一段对话，找出谁要做什么。", "read_detail", [
    q("Mom: Could you please sweep the floor? Peter: Sure. 妈妈请 Peter 做什么？", "扫地",
      ["倒垃圾", "叠衣服", "洗碗"], "sweep the floor。"),
    q("Mom: Could you please sweep the floor? Peter: Sure. Peter 同意了吗？", "同意了",
      ["拒绝了", "还没回答", "让妈妈去做"], "Sure 表示同意。"),
    q("Lucy has to fold the clothes and take out the rubbish. She will not wash the car. 她要洗车吗？", "不要",
      ["要", "只洗车", "短文没说"], "will not wash the car。"),
    q("Lucy has to fold the clothes and take out the rubbish. 哪一句和短文一致？", "Lucy will fold the clothes.",
      ["Lucy will wash the car.", "Peter will not sweep the floor.", "Lucy does not take out the rubbish."],
      "fold the clothes 是她要做的。"),
])

V("vo_mood", "情绪与压力", 8, "下", 3,
  "认读 pressure、argue、nervous 和 proper。",
  [("pressure", "压力"), ("argue", "争吵"), ("nervous", "紧张的"), ("proper", "合适的")], "vocab8")

G("gr_although", "although 引导让步", 8, "下", 3,
  "能用 although 连接相反的两层意思，并且不和 but 同时使用。", "clause_adv", [
    q("虽然他很累，但是他做完了作业。哪一句正确？", "Although he was tired, he finished his homework.",
      ["Although he was tired, but he finished his homework.", "Although he was tired, so he finished his homework.", "Although he is tired, he finished his homework yesterday without a tense."],
      "although 和 but 不同时用。"),
    q("虽然她紧张，她还是上了台。哪一句正确？", "Although she was nervous, she went on the stage.",
      ["Although she was nervous, but she went on the stage.", "Although she nervous, she went on the stage.", "Although she was nervous, she goes on the stage yesterday."],
      "Although 后面直接接结果，不加 but。"),
    q("although 的意思接近哪一个？", "虽然",
      ["因为", "所以", "除非"],
      "although 表示让步。"),
    q("哪一句使用正确？", "Although they argue, they still love each other.",
      ["Although they argue, but they still love each other.", "Although they argue, so they still love each other.", "But although they argue, they still love."],
      "保留 although，去掉 but。"),
])

F("fu_advice8", "用 Why don't you 提建议", 8, "下", 90,
  "能用 Why don't you 或 Why not 建议别人怎么做。", "func_plan", [
    q("建议对方和父母谈谈，哪一句合适？", "Why don't you talk to your parents?",
      ["Why don't you to talk to your parents?", "Why not you talk to your parents?", "Why don't you talking to your parents?"],
      "Why don't you 后面用动词原形。"),
    q("Why not write him a letter? 这句是在做什么？", "建议写信",
      ["询问信的价格", "描述已经写完的信", "拒绝写信"],
      "Why not 加动词原形，用来提建议。"),
    q("你觉得对方该先冷静，哪一句合适？", "You should calm down first.",
      ["You should to calm down first.", "You should calms down first.", "You should calming down first."],
      "should calm。"),
    q("想说压力太大，哪一句合适？", "I have too much pressure.",
      ["I have too many pressure.", "I have too much pressures.", "I has too much pressure."],
      "pressure 这里不可数，用 too much。"),
])

R("rw_letter8", "读建议信", 8, "下", 90,
  "读一封短信，找出问题和建议。", "read_detail", [
    q("Dear Linda, I argued with my parents. I feel nervous. What should I do? 写信人怎么了？", "和父母吵了架，感到紧张",
      ["考试得了满分", "去公园做志愿", "身体发烧"], "argued with my parents，feel nervous。"),
    q("Linda says: Why don't you talk to them? Although you are upset, they love you. Linda 建议什么？", "和他们谈谈",
      ["不要再说话", "离开家", "和他们继续吵"], "Why don't you talk to them。"),
    q("Although you are upset, they love you. 这句还说明什么？", "虽然你不高兴，他们仍然爱你",
      ["他们不爱你", "你并不心烦", "Linda 很紧张"], "Although 表示让步，爱这个事实还在。"),
    q("Linda says: Why don't you talk to them? 哪一句和回信一致？", "Linda advises a talk with the parents.",
      ["Linda tells the writer to argue again.", "The writer is not nervous.", "The parents do not love the writer."],
      "建议是 talk to them。"),
])

V("vo_storm", "暴风雨", 8, "下", 5,
  "认读 rainstorm、alarm、flashlight 和 wind。",
  [("rainstorm", "暴风雨"), ("alarm", "闹钟"), ("flashlight", "手电筒"), ("wind", "风")], "vocab8")

G("gr_pasting", "过去进行时", 8, "下", 5,
  "能用 was 或 were 加动词的 -ing 形式，描述过去某时正在做的事。", "pastcont", [
    q("昨晚八点我正在读书。哪一句正确？", "I was reading at eight last night.",
      ["I was read at eight last night.", "I were reading at eight last night.", "I reading at eight last night."],
      "I 后面用 was reading。"),
    q("他们当时正在睡觉。哪一句正确？", "They were sleeping at that time.",
      ["They was sleeping at that time.", "They were sleep at that time.", "They sleeping at that time."],
      "They 后面用 were sleeping。"),
    q("过去进行时的结构是哪一个？", "was 或 were 加动词 ing",
      ["did 加动词原形", "have 加过去分词", "will 加动词原形"],
      "was 或 were 加 doing。"),
    q("她那时没在看电视。哪一句正确？", "She wasn't watching TV then.",
      ["She wasn't watch TV then.", "She weren't watching TV then.", "She not watching TV then."],
      "wasn't watching。"),
])

G("gr_whenwhile", "when 与 while", 8, "下", 5,
  "能用 when 连接一个短暂动作，用 while 连接一段正在进行的动作。", "pastcont", [
    q("暴风雨来的时候，我正在读。哪一句正确？", "I was reading when the rainstorm came.",
      ["I was reading when the rainstorm was come.", "I read when the rainstorm was coming at that long time only.", "I was read when the rainstorm came."],
      "came 是短动作，用 when；阅读用过去进行时。"),
    q("我睡觉的时候，弟弟在看电视。哪一句正确？", "While I was sleeping, my brother was watching TV.",
      ["While I slept a short knock, my brother was watching TV.", "While I was sleep, my brother was watching TV.", "While I was sleeping, my brother watched TV for a long time in the same pattern."],
      "两段同时持续的动作都可以用过去进行时，while 连接其中一段。"),
    q("when the rainstorm came 里的 came 表示什么？", "突然发生的短动作",
      ["一段很长的习惯", "将来的计划", "现在的状态"],
      "came 是暴风雨到来的那一下。"),
    q("哪一句里 while 用得合适？", "While Mary was calling, the bell rang.",
      ["While the bell rang for one second, Mary was calling all night without while.", "While Mary called once, the bell was ringing for hours in this beginner pattern.", "While the bell rang, Mary was call."],
      "while 后面接 was calling 这段较长的动作。"),
])

F("fu_storm", "描述当时的动作", 8, "下", 5,
  "能询问过去某一时刻正在做什么。", "func_life", [
    q("想问暴风雨来时对方在做什么，哪一句合适？", "What were you doing when the rainstorm came?",
      ["What were you do when the rainstorm came?", "What did you doing when the rainstorm came?", "What were you doing when the rainstorm comes?"],
      "were you doing，when 从句用 came。"),
    q("当时你正在洗澡，应怎么说？", "I was taking a shower.",
      ["I was take a shower.", "I were taking a shower.", "I taking a shower."],
      "was taking。"),
    q("While the wind was blowing, I felt scared. 这句说明什么？", "刮风的那段时间里我感到害怕",
      ["风还没开始", "我明天会害怕", "我没有感到害怕"],
      "while 说明害怕发生在刮风期间。"),
    q("闹钟没响，哪一句合适？", "My alarm did not go off.",
      ["My alarm did not went off.", "My alarm was not go off.", "My alarm not went off."],
      "did not go off。"),
])

R("rw_storm", "读暴风雨故事", 8, "下", 5,
  "读一段故事，找出暴风雨来时人们正在做什么。", "read_detail", [
    q("When the rainstorm came, Ben was reading. His sister was sleeping. 暴风雨来时 Ben 在做什么？", "在读书",
      ["在睡觉", "在洗澡", "在扫地"], "Ben was reading。"),
    q("When the rainstorm came, Ben was reading. His sister was sleeping. 妹妹在做什么？", "在睡觉",
      ["在读书", "在看新闻", "在做饭"], "was sleeping。"),
    q("While the wind was blowing, the lights went out. Mom was making dinner. 灯灭的时候妈妈在做什么？", "在做晚饭",
      ["在睡觉", "在读报", "在公园"], "Mom was making dinner。"),
    q("While the wind was blowing, the lights went out. 哪一句和短文一致？", "The lights went out while the wind was blowing.",
      ["The lights went out before there was any wind.", "Ben was sleeping when the rainstorm came.", "Mom was reading in the park."],
      "刮风期间灯灭了。"),
])

V("vo_story", "故事用词", 7, "下", 8,
  "认读 emperor、stupid、stone 和 weak。",
  [("emperor", "皇帝"), ("stupid", "愚蠢的"), ("stone", "石头"), ("weak", "虚弱的")], "vocab8")

G("gr_unless", "unless 表示除非", 8, "下", 6,
  "能用 unless 表示如果不，从句用一般现在时。", "clause_adv", [
    q("除非你赶快，否则会迟到。哪一句正确？", "You will be late unless you hurry.",
      ["You will be late unless you will hurry.", "You will be late unless you hurried yesterday.", "You are late unless you will hurry tomorrow."],
      "unless 从句用 hurry，主句用 will be。"),
    q("unless 的意思接近哪一个？", "如果不",
      ["因为", "虽然", "以便"],
      "unless 等于 if not。"),
    q("如果他不帮忙，我们就搬不动石头。哪一句正确？", "We cannot move the stone unless he helps.",
      ["We cannot move the stone unless he will help.", "We cannot move the stone unless he help.", "We could not move the stone unless he helps tomorrow in the past."],
      "unless he helps。"),
    q("哪一句和 If you do not try, you will not win. 最接近？", "You will not win unless you try.",
      ["You will not win unless you will try.", "You will win unless you try.", "Unless you try, you will win."],
      "unless you try 就是 if you do not try。"),
])

G("gr_sothat", "so that 表示目的", 8, "下", 3,
  "能用 so that 说明目的，从句里常用 can 或 could。", "clause_adv", [
    q("他早起是为了赶上公共汽车。哪一句正确？", "He got up early so that he could catch the bus.",
      ["He got up early so that he catch the bus.", "He got up early to that he could catch the bus.", "He got up early so that he can caught the bus."],
      "so that he could catch。"),
    q("so that 在这句里表示什么？", "目的",
      ["让步", "比较", "被动"],
      "so that 说明希望达到的结果。"),
    q("她留了便条，以便父母能看见。哪一句正确？", "She left a note so that her parents could see it.",
      ["She left a note so that her parents can saw it.", "She left a note for that her parents could see it.", "She left a note so that her parents see it yesterday."],
      "could see。"),
    q("哪一个短语可以引导目的从句？", "so that",
      ["as tall as", "more than", "ever since"],
      "so that 后面接一个完整的目的从句。"),
])

F("fu_story", "复述故事", 7, "下", 8,
  "能用简单过去时讲出故事里的人物和结果。", "func_life", [
    q("故事开头，哪一句合适？", "Once upon a time, there was an old man.",
      ["Once upon a time, there is an old man yesterday.", "Once upon a time, there were an old man.", "Once upon a time, there was a old man."],
      "there was an old man。"),
    q("老人一直试着移山。哪一句合适？", "The old man kept trying to move the mountain.",
      ["The old man kept try to move the mountain.", "The old man kept to trying move the mountain.", "The old man kept trying move the mountain."],
      "kept trying to move。"),
    q("别人觉得这很愚蠢，应怎么说？", "Other people thought it was stupid.",
      ["Other people thought it is stupid yesterday.", "Other people think it was stupid now past.", "Other people thought it were stupid."],
      "thought it was stupid。"),
    q("想说他没有放弃，哪一句合适？", "He did not give up.",
      ["He did not gave up.", "He did not giving up.", "He not gave up."],
      "did not give up。"),
])

R("rw_story", "读神话故事", 7, "下", 8,
  "读一段故事，找出人物做了什么。", "read_detail", [
    q("An old man tried to move the mountains. His family kept working every day. 老人想做什么？", "移走大山",
      ["建造宫殿", "寻找皇帝", "离开村庄"], "move the mountains。"),
    q("An old man tried to move the mountains. His family kept working every day. 家人怎样？", "每天继续干活",
      ["马上放弃", "只看不干", "搬走了"], "kept working every day。"),
    q("A god thought the man was weak, but he sent two gods to help. 谁来帮忙？", "两位神",
      ["皇帝", "邻居", "没有人"], "two gods to help。"),
    q("A god thought the man was weak, but he sent two gods to help. 哪一句和故事一致？", "The gods came to help the man.",
      ["The man gave up at once.", "The family never worked.", "The god refused to help."],
      "sent two gods to help。"),
])

V("vo_geo", "地理名称", 8, "下", 4,
  "认读 desert、ocean、ancient 和 protect。",
  [("desert", "沙漠"), ("ocean", "海洋"), ("ancient", "古代的"), ("protect", "保护")], "vocab8")

G("gr_high", "比较级与最高级的选用", 8, "下", 4,
  "能根据是两者还是三者以上，选用比较级或最高级。", "compare", [
    q("珠穆朗玛峰是世界上最高的山。哪一句正确？", "Qomolangma is the highest mountain in the world.",
      ["Qomolangma is the higher mountain in the world.", "Qomolangma is highest mountain in the world.", "Qomolangma is the most high mountain in the world."],
      "在世界上所有山中用 the highest。"),
    q("这条河比那条长。哪一句正确？", "This river is longer than that one.",
      ["This river is the longest than that one.", "This river is more long than that one.", "This river is longer that that one."],
      "两者用 longer than。"),
    q("三者以上用哪一种形式？", "最高级",
      ["只用不加 the 的原级", "只用比较级加 than", "动词过去式"],
      "三者以上用最高级。"),
    q("哪一句是两者比较？", "The Pacific Ocean is larger than the Atlantic Ocean.",
      ["The Pacific Ocean is the largest ocean in the world.", "The Pacific Ocean is large.", "Oceans are blue."],
      "larger than 比较两个大洋。"),
])

F("fu_fact", "陈述地理事实", 8, "下", 4,
  "能用事实句说出地理事物有多大、多高。", "func_view", [
    q("想说这片沙漠很大，哪一句合适？", "This desert is very large.",
      ["This desert is very larger.", "This desert is the larger.", "This desert are very large."],
      "陈述事实、不比较时用原级 large。"),
    q("想问世界上最高的山是哪座，哪一句合适？", "What is the highest mountain in the world?",
      ["What is the higher mountain in the world?", "What is highest mountain in the world?", "What is the most high mountain in the world?"],
      "the highest。"),
    q("想说我们应该保护海洋，哪一句合适？", "We should protect the ocean.",
      ["We should to protect the ocean.", "We should protects the ocean.", "We should protecting the ocean."],
      "should protect。"),
    q("It is 8,848.86 meters high. 这句在说什么？", "它的高度",
      ["它的年龄", "它的人口", "它的票价"],
      "meters high 表示高度。"),
])

R("rw_fact", "读地理短文", 8, "下", 4,
  "读一段地理短文，找出最高或最长的事物。", "read_detail", [
    q("Qomolangma is the highest mountain in the world. It is higher than any other mountain. 它是什么？", "世界上最高的山",
      ["一条河", "一片沙漠", "一个海洋"], "the highest mountain。"),
    q("The Nile is the longest river in the world. The Amazon is shorter than the Nile. 哪条河更短？", "亚马孙河",
      ["尼罗河", "两样长", "珠穆朗玛峰"], "The Amazon is shorter。"),
    q("The Sahara is a great desert. We should protect the animals there. 我们应该做什么？", "保护那里的动物",
      ["离开所有沙漠", "把河移走", "短文没说"], "protect the animals there。"),
    q("The Nile is the longest river in the world. 哪一句和短文一致？", "No river in this text is longer than the Nile.",
      ["The Amazon is longer than the Nile.", "Qomolangma is a river.", "The Sahara is an ocean."],
      "Nile 是文中最长的河。"),
])

R("rw_cloze8", "选词补全短文", 8, "下", 90,
  "能根据上下文选择意思和语法都通顺的词。", "read_cloze", [
    q("Tom ___ to the library yesterday. He read an old book about the ocean. 横线处选哪一个？", "went",
      ["goes", "going", "will go"], "yesterday 要用过去式 went。"),
    q("The Sahara is one of ___ deserts in the world. 横线处选哪一个？", "the biggest",
      ["bigger", "big", "the bigger"], "one of 后面用 the 加最高级。"),
    q("Mary was reading ___ the rainstorm came. 横线处选哪一个？", "when",
      ["but", "unless", "so that"], "一个短动作到来，用 when。"),
    q("We should ___ the animals in the desert. They are in danger. 横线处选哪一个？", "protect",
      ["protected", "protecting", "to protect"], "should 后面用动词原形 protect。"),
])

V("vo_book", "书籍与阅读", 8, "下", 7,
  "认读 treasure、island、classic 和 page。",
  [("treasure", "宝藏"), ("island", "岛"), ("classic", "名著"), ("page", "页")], "vocab8")

G("gr_pp", "现在完成时", 8, "下", 7,
  "能用 have 或 has 加过去分词，表示到现在为止已经发生的事。", "perfect", [
    q("我已经读完了这本书。哪一句正确？", "I have already read this book.",
      ["I have already readed this book.", "I has already read this book.", "I have already reading this book."],
      "have read，read 的过去分词与原形同形。"),
    q("她已经看过这部电影。哪一句正确？", "She has already seen the film.",
      ["She has already saw the film.", "She have already seen the film.", "She has already see the film."],
      "has seen。"),
    q("现在完成时的结构是哪一个？", "have 或 has 加过去分词",
      ["was 加动词 ing", "will 加动词原形", "did 加动词原形"],
      "have 或 has 加 done。"),
    q("他们还没有找到宝藏。哪一句正确？", "They have not found the treasure yet.",
      ["They have not find the treasure yet.", "They has not found the treasure yet.", "They have not founded the treasure yet."],
      "have not found。"),
])

G("gr_yet", "already 与 yet", 8, "下", 7,
  "能在肯定句中用 already，在疑问句和否定句中用 yet。", "perfect", [
    q("我已经做完作业了。哪一句正确？", "I have already finished my homework.",
      ["I have yet finished my homework.", "I already have finished my homework yesterday.", "I have finished already my homework yet."],
      "肯定句用 already。"),
    q("你读过《金银岛》了吗？哪一句正确？", "Have you read Treasure Island yet?",
      ["Have you read Treasure Island already yet?", "Did you have read Treasure Island yet?", "Have you readed Treasure Island yet?"],
      "疑问句用 yet，放在句末。"),
    q("他还没回来。哪一句正确？", "He has not come back yet.",
      ["He has not come back already.", "He has not came back yet.", "He not has come back yet."],
      "否定句用 yet。"),
    q("already 常用于哪一种句子？", "肯定句",
      ["只用于过去进行时", "只用于 if 从句", "只用于最高级"],
      "already 常放在肯定的现在完成时里。"),
])

F("fu_book", "谈论读过的书", 8, "下", 7,
  "能询问别人是否已经读过某本书。", "func_plan", [
    q("想问对方是否已经读过这本名著，哪一句合适？", "Have you read this classic yet?",
      ["Did you have read this classic yet?", "Have you read this classic yesterday?", "Have you readed this classic yet?"],
      "Have you read ... yet。"),
    q("你刚读完，应怎么说？", "Yes, I have already finished it.",
      ["Yes, I have yet finished it.", "Yes, I already finished it tomorrow.", "Yes, I has already finished it."],
      "Yes, I have already finished it。"),
    q("还没读到第 20 页，哪一句合适？", "I have not reached page 20 yet.",
      ["I have not reach page 20 yet.", "I has not reached page 20 yet.", "I did not have reached page 20 yet."],
      "have not reached ... yet。"),
    q("What book have you read? 这句在问什么？", "你读过什么书",
      ["你正在写什么书", "你明天要买什么书", "这本书多少页"],
      "have you read 问到目前为止读过的书。"),
])

R("rw_book", "读阅读记录", 8, "下", 7,
  "读一段阅读记录，判断谁已经读完。", "read_detail", [
    q("Amy has already read Treasure Island. Pete has not finished it yet. 谁已经读完了？", "Amy",
      ["Pete", "两个人都读完了", "没有人"], "Amy has already read。"),
    q("Amy has already read Treasure Island. Pete has not finished it yet. Pete 读完了吗？", "还没有",
      ["已经读完", "读了两遍", "短文没说"], "has not finished it yet。"),
    q("The book is a classic. It is about a boy and treasure on an island. 这本书讲什么？", "岛上的宝藏和一个男孩",
      ["一座现代城市", "如何做饭", "一场暴风雨"], "treasure on an island。"),
    q("Pete has not finished it yet. 哪一句和记录一致？", "Pete is still reading the book.",
      ["Pete has already finished the book.", "Amy has not started.", "The book is not about an island."],
      "not finished yet 说明还没读完。"),
])

V("vo_museum", "场馆经历", 8, "下", 90,
  "认读 camera、progress、unusual 和 collect。",
  [("camera", "照相机"), ("progress", "进步"), ("unusual", "不寻常的"), ("collect", "收集")], "vocab8")

G("gr_ever", "ever 与 never", 8, "下", 7,
  "能用 ever 询问是否曾经做过，用 never 表示从未做过。", "perfect", [
    q("你曾经去过博物馆吗？哪一句正确？", "Have you ever been to a museum?",
      ["Have you never been to a museum as a yes-no with ever?", "Did you ever been to a museum?", "Have you ever went to a museum?"],
      "Have you ever been。"),
    q("我从未坐过地铁。哪一句正确？", "I have never taken the subway.",
      ["I have never took the subway.", "I have ever taken the subway to mean never.", "I has never taken the subway."],
      "have never taken。"),
    q("ever 常出现在哪一种句子里？", "疑问句",
      ["只出现在最高级前", "只出现在祈使句", "只和 yesterday 连用"],
      "Have you ever 用来问经历。"),
    q("她从未用过这台相机。哪一句正确？", "She has never used this camera.",
      ["She has never use this camera.", "She have never used this camera.", "She has ever used this camera to mean not."],
      "has never used。"),
])

G("gr_been", "been 与 gone", 8, "下", 90,
  "能区分 has been to（去过并已回来）和 has gone to（去了尚未回来）。", "perfect", [
    q("她现在不在这里，去了图书馆。哪一句正确？", "She has gone to the library.",
      ["She has been to the library and is still there now.", "She has went to the library.", "She has gone the library."],
      "人不在这里，用 has gone to。"),
    q("他去过上海，上周已经回来了。哪一句正确？", "He has been to Shanghai.",
      ["He has gone to Shanghai and is back home now.", "He has been in Shanghai for a finished trip last week without been.", "He has went to Shanghai."],
      "去过并回来了，用 has been to。"),
    q("Has she gone to the museum? 若回答 Yes，她现在在哪里？", "在博物馆，还没回来",
      ["在家里", "已经回来了", "从未去过"],
      "gone 表示人还在那里。"),
    q("哪一句表示去过那个地方而且人已经回来？", "They have been to the science museum.",
      ["They have gone to the science museum.", "They have went to the science museum.", "They have been the science museum."],
      "have been to 表示经历，人已回来。"),
])

F("fu_ever", "询问去过哪里", 8, "下", 90,
  "能询问别人的经历，并说出自己去过哪里。", "func_plan", [
    q("想问对方是否去过游乐园，哪一句合适？", "Have you ever been to an amusement park?",
      ["Have you ever gone to an amusement park and come back in the same word?", "Did you ever been to an amusement park?", "Have you ever be to an amusement park?"],
      "Have you ever been to。"),
    q("你去过，而且是去年去的，应怎么说？", "Yes, I have. I went there last year.",
      ["Yes, I have gone there and I am back.", "Yes, I went there next year.", "Yes, I have never been there last year."],
      "先说 have，再用 went 补过去的时间。"),
    q("Me neither. 用在什么时候？", "对方说从未做过，你也没有",
      ["对方说去过，你也去过", "你正在出发", "你拒绝邀请"],
      "Neither 表示也不。"),
    q("想说这是不寻常的经历，哪一句合适？", "It was an unusual experience.",
      ["It was an unusual experiences.", "It were an unusual experience.", "It was a unusual experience."],
      "an unusual experience。"),
])

R("rw_museum", "读场馆经历", 8, "下", 90,
  "读一段经历，区分去过和正在那里。", "read_detail", [
    q("Kate has been to the science museum. She took photos there last month. 她现在还在馆里吗？", "不在，她已经回来了",
      ["还在馆里", "从未去过", "短文没说她去过"], "has been to，并且上个月拍了照。"),
    q("Leo has gone to the film museum. He is not at home. Leo 在哪里？", "在电影博物馆",
      ["在家里", "在科学博物馆", "在学校"], "has gone，人不在家。"),
    q("Kate has never been to a space museum. 她去过太空博物馆吗？", "没有",
      ["去过", "和 Leo 一起去了", "上周去了"], "never been。"),
    q("Leo has gone to the film museum. 哪一句和短文一致？", "Leo is away at the film museum.",
      ["Leo has come back home.", "Kate is at the film museum now.", "Kate has been to a space museum."],
      "gone 说明他还没回来。"),
])

V("vo_own", "旧物与回忆", 8, "下", 90,
  "认读 scarf、soft、yard 和 honest。",
  [("scarf", "围巾"), ("soft", "柔软的"), ("yard", "院子"), ("honest", "诚实的")], "vocab8")

G("gr_since", "for 与 since", 8, "下", 8,
  "能用 for 加一段时间，用 since 加过去的起点。", "perfect", [
    q("这辆自行车我买了三年了。哪一句正确？", "I have had this bike for three years.",
      ["I have had this bike since three years.", "I have bought this bike for three years.", "I have had this bike for three years ago."],
      "for three years 是一段时间。have had 可以和 for 连用。"),
    q("从 2019 年起我就住在这里。哪一句正确？", "I have lived here since 2019.",
      ["I have lived here for 2019.", "I have lived here since three years.", "I lived here since 2019 and I do not live here now."],
      "since 2019 是起点。"),
    q("for 后面通常接什么？", "一段时间",
      ["一个过去的年份", "一个星期几的名称单独作起点", "一个最高级"],
      "for three years、for two hours 都是一段时间。"),
    q("他从星期一就病了，到现在还病着。哪一句正确？", "He has been ill since Monday.",
      ["He has been ill for Monday.", "He was ill since Monday and he is well now in this sentence.", "He has been ill since three days."],
      "since Monday 表示从星期一开始一直到现在。"),
])

F("fu_since", "谈论拥有多久", 8, "下", 90,
  "能询问一件物品拥有了多久，并回答。", "func_plan", [
    q("想问对方拥有这条围巾多久了，哪一句合适？", "How long have you had this scarf?",
      ["How long have you bought this scarf?", "How long did you have this scarf next year?", "How long have you has this scarf?"],
      "延续到现在用 have you had，不用 have you bought。"),
    q("你拥有两年了，应怎么说？", "I have had it for two years.",
      ["I have had it since two years.", "I have bought it for two years.", "I had it for two years and I sold it."],
      "for two years。"),
    q("Since when have you lived in this yard? 这句在问什么？", "你从何时起住在这个院子里",
      ["院子有多大", "你昨天住不住", "院子软不软"],
      "Since when 问起始时间。"),
    q("想说玩具熊又软又旧，哪一句合适？", "The bear is soft and old.",
      ["The bear is soft and old for since.", "The bear are soft and old.", "The bear is a old soft."],
      "is soft and old。"),
])

R("rw_since", "读旧物故事", 8, "下", 90,
  "读一段回忆，找出拥有的时间和原因。", "read_detail", [
    q("I have had this scarf for three years. My grandma made it. 围巾是谁做的？", "奶奶",
      ["妈妈", "同学", "售货员"], "My grandma made it。"),
    q("I have had this scarf for three years. 拥有多久了？", "三年",
      ["三个月", "从昨天开始", "短文没说"], "for three years。"),
    q("Jeff has owned the bike since he was ten. He still rides it. 他现在还骑这辆车吗？", "还骑",
      ["已经卖掉了", "从未拥有", "只在十岁前骑"], "still rides it。"),
    q("Jeff has owned the bike since he was ten. 哪一句和短文一致？", "Jeff got the bike when he was ten and still has it.",
      ["Jeff has had the bike for ten days only.", "Jeff sold the bike.", "The scarf is three days old."],
      "since he was ten，而且 still rides。"),
])
