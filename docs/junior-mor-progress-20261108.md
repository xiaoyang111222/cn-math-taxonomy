# 初中道德与法治阶段记录（2026-11-08）

记录性质：2026-11-08 续跑的真实阶段快照。范围只记本阶段已核对的事实。未写上线或 push。

## 七上本阶段

- 现行计数：25 点，100 题，3 soft，0 hard。
- 原 9 点及 36 题逐对象未变。
- 第 1–13 课有可测概念覆盖。这不是教材每框每项的完全穷尽。
- 0 hard 不记为缺陷。本册多数生活能力可独立成立，不强造硬边。

## 来源与核验状态

- 来源：教师之家 3505；dzskb `tbbczqdfsc`。
- 官方人教社只核四单元。
- catalog：`pending_official_lesson_list`。
- 课标：`inferred`；verbatim 为 false；页码待核。

## 本阶段检查

- `npm test` 本阶段 exit 0。
- 生成安全检查通过。
- 非 `cnd_j` 全对象未变。
- 原课标未变。
- 初中语文 189 未变。
- 初中物理 50/368 未变。
- 三册（七上、七下、八上）生成双跑四份 data SHA256 相同。

## 累计（七上 + 七下 + 八上）

- 61 点，244 题，5 soft，0 hard。编号到 `cnd_j061`。
- 首批 9 点、36 题对象未改。
- 0 hard：生活判断可以独立题面成立，不强造掌握推断，也不把「没有硬边」记成缺陷。
- 相对首批 3 soft，新增 2 soft。这两条是有概念关联的学习推荐，不是课次链。

## 七下本阶段

- 已测试：18 点，72 题。共 11 课：青春正当时、做情绪情感的主人、人贵自尊、自信给人力量、人要自强、传承核心思想理念、弘扬中华人文精神、践行中华传统美德、法律为我们护航、走近民法典、远离违法犯罪。
- 这 11 课有可测概念覆盖。这不是教材每框每项的完全穷尽。
- 课名、框名据公开目录转述。来源：教师之家 https://www.renjiaoshe.com/jiaocai/3506.html ；dzskb https://www.dzskb.com/tbbczqdfxc.html 。此前误写的 3505 一带已改为 3506。
- 官方逐课未核。页码待核。源核实不等于教材原文。catalog：`pending_official_lesson_list`。
- 第十课首框「认识民法典」与「读懂民法典」异文仍待核，不作确定框名。其他已知框保留为保护人身权、保障财产权。未编页码。
- 法律引用仍用已核官方 URL。这些 URL 核对的是法律公开表述，不是教材原文。
- 七上原 9 点及题未改。点名与 ID 未改。
- 三册阶段 `npm test` exit 0。非 `cnd_j` 全对象未变。原课标条目一致。初中语文 189、初中物理 50/368、`verbatim: true` 为 0，均未变。`sw.js` 本地 v13。未 push、未 deploy。

## 八上本阶段

- 已测：18 点，72 题，12 课。可测概念覆盖，不是每框穷尽。
- 来源：教师之家 3507 公开目录。官方逐课待核。catalog：`pending_official_lesson_list`。课标 `inferred`，verbatim 为 false，页码待核。
- `npm test` exit 0。日志：`/workspace/grok-build-logs/jh-mor-20261108/continuation/g8a-npm-test.log`。
- 未 push、未 deploy。

## 待续

- 下一册八下：`scripts/jmor_g8b.py`，从 `cnd_j062` 开始。计划：`/workspace/grok-build-prompts/jmor-g8b-plan.txt`。未测，未生成。
- 九上课名异文、九下目录待核。没有建点。
