# App 第一期：PWA、孩子档案与统计钩子

## PWA

- `manifest.webmanifest`：名称、`display: standalone`、主题色 `#0f6e62`、图标和三个快捷入口（诊断、知识图谱、孩子档案）。路径都是相对写法，站点放在域名根目录或子目录都能用。`start_url` 带 `?source=pwa`。
- 图标在 `assets/icons/`，由 `python3 scripts/make_pwa_icons.py` 用站点 logo 和配色（`#0f6e62`、`#dff3ef`）生成：`icon-192.png`、`icon-512.png`（带圆角）、`icon-maskable-512.png`（安全区内）、`apple-touch-icon.png`（180，不透明，给 iOS）。
- `sw.js`（必须在站点根目录，才能管整个站点）：
  - 安装时预缓存页面、脚本、样式、图标、`data/*.json` 和知识图谱用到的 `data/mappings/` 对照表（约 6 MB，其中题库 3.7 MB）。壳必须齐全才算安装成功，数据缓存失败不挡安装。
  - 页面和脚本：网络优先（5 秒超时），断网用缓存，所以发布后在线用户直接拿到新版。
  - 数据、图标、manifest：先用缓存，同时后台更新（下一次打开拿到新数据）。
  - 改了缓存清单，或数据结构有不兼容的变化，把 `sw.js` 里的 `VERSION` 加一，旧缓存会在激活时删掉。
  - 新增页面或脚本时，要把它加进 `sw.js` 的 `SHELL` 列表才会离线可用。
- 每个页面的 `<head>` 有 manifest、apple-touch-icon、theme-color；页尾加载 `assets/stats-config.js`、`assets/stats.js`、`assets/pwa.js`。service worker 只在 https 或 localhost 下注册。
- 部署：`scripts/deploy-cf.sh` 已把 `sw.js`、`manifest.webmanifest`、`children/` 打进部署包。

### 添加到桌面的提示（`assets/pwa.js`）

| 环境 | 行为 |
|---|---|
| 安卓 / 桌面 Chrome、Edge | 捕获 `beforeinstallprompt`，约 1 秒后在页面底部出现提示条，点「添加」调用系统安装框 |
| iOS Safari（含 iPad） | 没有安装接口。提示条按钮是「怎么添加」，打开图文引导：分享 → 添加到主屏幕 → 添加。iOS 上的 Chrome、微信等内置浏览器不显示（它们的步骤不同） |
| 已从桌面图标打开（`display-mode: standalone`、`navigator.standalone`） | 不显示任何提示 |

点「暂不」、看完引导点「知道了」、或点过「添加」后，`localStorage` 的 `cnmPwa.dismissed.v1` 记下时间，之后不再自动弹出；页脚会有一个「添加到桌面」链接，想装的人仍能找到。收到 `appinstalled` 后写 `cnmPwa.installed.v1`，入口也不再显示。要重新看到提示，清掉这两个键。

## 孩子档案

- 数据都在本机 `localStorage`，不上传，没有账号和云同步。清除浏览器数据或换设备不会保留。
- `cnmChildren.v1`：`{ current, children: [{ id, name, grade, textbook, createdAt }] }`，最多 8 个，昵称不能重名。
- `cnmChildren.records.v1`：`{ [childId]: [记录] }`，普通档案保留最近 40 条；备份合并后超过 40 条的档案会保留完整历史，之后保存或移动记录也不会按 40 条截断。一条记录是一次诊断（`key = 学科|seed|目标`），含学科、范围名称、已答题数、薄弱 / 不稳 / 已掌握 / 未测数量、各自的知识点 id 和根因 id。同一次诊断反复打开结果页、更正答案，只更新这一条。
- 教材版本是档案里的备注：图谱的知识点和章节按人教版编排，目前不按版本筛选内容。
- 诊断页：开始页、答题页、结果页都有当前孩子切换（也可选「不保存到档案」）。结果页自动保存到当前孩子；换成另一个孩子，会把这条记录一并挪过去。演示模式（`demo=1`）不保存。
- `children/history.html`：按学科筛选；「现在还薄弱的知识点」把某个孩子所有记录合起来，同一知识点以最近一次结果为准，根因排最前，每项链到知识图谱，并可「再测一次」；下面是逐条诊断记录，可展开、可删除。

### 档案备份与跨浏览器恢复

档案管理页的「导出全部档案」会下载一个带导出时间的 `children-backup-*.json` 文件，包含所有孩子的资料、当前孩子选择和各学科的全部已存诊断记录。没有档案时按钮不可用；读取或解析失败会显示错误，不会生成空备份。导出不修改本机数据，不发送档案数据到服务器。

备份格式：

```json
{
  "format": "cn-math-taxonomy.children",
  "version": 1,
  "exportedAt": "2026-10-28T00:00:00.000Z",
  "profiles": {
    "v": 1,
    "current": "child-id",
    "children": [{ "id": "child-id", "name": "小满", "grade": "三年级", "textbook": "人教版", "createdAt": "2026-10-01T00:00:00.000Z" }]
  },
  "records": { "child-id": [] }
}
```

`profiles` 和 `records` 分别保留 `cnmChildren.v1`、`cnmChildren.records.v1` 的完整内容，包括孩子 ID、创建时间、记录时间、学科、范围和掌握状态等字段。历史记录的知识点名称与薄弱点汇总可由知识点 ID 和记录重新计算，不另存一份。未完成的诊断会话、诊断设置、已见题目和访问统计不属于档案备份。

换浏览器时，在原浏览器点「导出全部档案」，到新浏览器的档案页选择「导入备份文件」。文件只在浏览器里读取，不上传；支持上述版本 1 的 JSON 备份，最大 10 MB（支持 UTF-8 BOM）。选择文件后显示预览，点击「确认合并导入」才会保存，取消不会写入任何数据。

合并规则：

- 相同孩子 ID：合并诊断历史，保留本机昵称、年级、教材版本和创建时间；已有的当前孩子选择保持不变。空浏览器恢复备份中的当前孩子选择。
- 同名但不同 ID：保留两份档案，导入档案改名为「昵称（导入）」等，仍保留原 ID。重复导入按 ID 匹配，不会新增副本。
- 诊断记录按 `key` 去重，按 `savedAt` 与 `updatedAt` 中较晚的时间选择较新结果；时间相同保留本机记录。只存在于一边的记录全部保留，不因合并超过 40 条而截断。
- 合并后超过 8 个孩子时停止导入，不删除现有档案。错误格式、未知版本、重复 ID/记录 key、无归属记录、非法字段和损坏的本机数据都不会被当成空数据导入。未知知识点 ID 保留，历史页可回退显示 ID。
- 预览后本机档案有变化时，先重新预览再确认。确认时先写记录再写档案；第二步失败会恢复原始记录，恢复失败会单独提示，不报告成功。浏览器存储配额或权限不足时需要先处理存储问题。

JSON 文件包含昵称和学习记录，请自行保管。未完成诊断的进度和诊断设置仍不在备份范围内。

备份恢复逻辑测试：`node tests/test_children.js`（无第三方依赖）。

浏览器迁移测试：`node tests/test_children_browser.js`（Node 22+、本机 Chrome/Chromium，可用 `CHROME` 指定路径）。使用隔离的浏览器存储实际下载并导入备份，验证恢复后的历史与薄弱点、重复导入、冲突合并、过期预览、配额失败回滚和移动端布局；不访问真实用户档案，测试文件和截图写入系统临时目录。

## 统计

**仓库里原来没有任何统计方案**（页面不加载统计脚本，也没有自建采集）。没有编造账号，这里只留出可配置的钩子，默认全空，页面不发任何统计请求。

配置在 `assets/stats-config.js`：

```js
window.CNM_STATS = {
  cloudflareToken: '',  // Cloudflare Web Analytics 的 token；填了才加载它的信标脚本
  endpoint: '',         // 自建采集地址；填了就用 sendBeacon 把事件 POST 过去
  onEvent: null         // 可选回调，每个事件调用一次
};
```

`assets/stats.js` 提供 `window.cnmTrack(name, props)`，每个事件的内容是：

```json
{ "event": "pageview", "source": "pwa", "path": "/diagnose/", "ts": "2026-10-22T12:00:00.000Z" }
```

- `source`：`pwa` 表示从桌面图标打开（`display-mode: standalone` 或 iOS `navigator.standalone`），`web` 表示普通网页访问。`manifest.webmanifest` 的 `start_url` 另外带了 `?source=pwa`，用 URL 参数统计的也能区分入口。
- 事件：`pageview`、`pwa_launch`（standalone 下一次会话的第一次打开）、`appinstalled`、`return_visit`（本机和上次不在同一天；带 `days_since_first`、`visit_days`）、`install_hint_shown`、`install_prompt_accepted` / `install_prompt_dismissed`、`ios_guide_opened`、`install_hint_closed`、`child_added`。
- 不收集孩子昵称、年级、答题内容等任何个人信息；事件里只有事件名、来源、页面路径（不含查询参数）和时间。回访用本机 `localStorage` 的 `cnmStats.v1`（首次和最近一次访问日期）判断，没有用户标识。
- 同一个 `window` 上还会派发 `cnm:track` 事件，可以不改代码、在别处监听。

怎么接：
1. **只要访问量**：在 Cloudflare 后台创建 Web Analytics 站点，把 token 填进 `cloudflareToken`。它只统计页面访问，不支持自定义事件，所以 `appinstalled` 等事件不会出现在里面。
2. **要区分 PWA 和安装 / 回访**：自己起一个接收端（例如一个 Cloudflare Worker 写入 D1 / Analytics Engine），把地址填进 `endpoint`。请求体是上面那段 JSON（`text/plain`，避免 CORS 预检），接收端按 `event`、`source` 汇总即可。
3. 用其他统计服务：在 `onEvent` 里转发，或监听 `cnm:track`。

填了 `cloudflareToken` 之后，页面会请求 `static.cloudflareinsights.com`；`scripts/screenshot.js` 里「没有外网请求」的检查在那种配置下会失败，属预期。

## 本地验证

```bash
python3 -m http.server 8000   # localhost 下 service worker 也能注册
```

打开 http://localhost:8000/ ，DevTools → Application 里看 Manifest 和 Service Workers；勾选 Offline 后刷新，知识图谱、诊断、档案都应能打开。安卓提示要在 https（或 localhost）并满足 Chrome 的可安装条件才会触发；iOS 的引导需要用 Safari 或 iPhone UA 查看。
