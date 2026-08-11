# 淘宝商品数据爬虫 — 分步实战计划 v2

> **定位**：练习项目，不商用、不大规模采集。  
> **目标**：能稳定绕过淘宝登录态反爬，拿到商品的结构化数据。  
> **原则**：一步步来，每步有明确产出和验证标准，跑通了再进下一步。

---

## 一、总目标（明确）

| 项 | 说明 |
|---|---|
| **输入** | 淘宝商品 ID，或一个搜索关键词 |
| **输出** | 结构化 JSON：标题、价格、原价、销量、SKU 列表、主图 URL、店铺名、评论数 |
| **量级** | 练习阶段单个关键词 20 条，批量 3-5 个关键词 × 20 条 |
| **存储** | `data/{关键词}/{item_id}.json` |
| **不强求** | 不解析评论正文、不翻深页、不逆向 sign 加密 |

---

## 二、技术栈与环境

| 项 | 版本/路径 |
|---|---|
| Python | 3.10+ |
| 虚拟环境 | `D:/pycharm/Person-Practice/.venv/`（已就绪） |
| 爬虫框架 | Scrapling 0.4.8（`DynamicFetcher` 为主） |
| 浏览器内核 | Playwright（已装，Chromium） |
| 视频合并 | ffmpeg 8.1.2（已装，备用） |
| 辅助编码 | Claude Code / WorkBuddy（vibe coding，人工把关） |

---

## 三、反爬绕过策略（核心）

淘宝反爬强在三点：**登录态校验**、**数据在异步接口**、**滑块/行为风控**。对应绕法：

| 反爬点 | 绕过手段 |
|---|---|
| 登录态校验 | Playwright 有头浏览器**手动扫码登录**一次，Cookie 持久化到 `taobao_cookie.json`，后续请求复用 |
| 数据在异步接口 | 优先用 DynamicFetcher 等待页面 JS 渲染完，直接从 **渲染后 DOM** 提取；DOM 拿不到的字段，fallback 到 H5 mtop 接口带 Cookie 请求 |
| 浏览器指纹检测 | Scrapling 的 DynamicFetcher 自带反检测（stealth）；必要时注入脚本伪装 `navigator.webdriver` |
| 行为风控 | 单线程串行，每个商品随机延时 5-10s；每 20 个休息 2 分钟；随机滚动模拟人类 |
| 滑块验证码 | 检测到滑块立即**暂停 + 告警**，人工处理后再继续（练习阶段不接打码平台） |
| Cookie 过期 | 每次启动校验登录态，失效则提示重新扫码 |
| IP 频率 | 练习阶段不买代理，被封就换网络/等几小时；记录现象 |

**关键判断**：练习阶段不逆向 `x-sign`/`x-mini-wua` 等加密签名（门槛高、维护成本大）。靠**登录态 Cookie + 浏览器渲染**拿数据，够用。

---

## 四、分步计划

### 🔍 Step 0 — 侦察：搞清楚数据在哪（半天）

**目标**：手动分析一个商品详情页，确定每个字段从哪拿。

**做法**：
1. Chrome 打开任意淘宝商品详情页（先登录）
2. F12 → Network 筛选 XHR/Fetch，刷新页面
3. 找到返回商品数据的接口（通常是 `h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/...`）
4. 记录：标题/价格/销量/SKU 分别在哪个接口的哪个字段
5. 同时看渲染后 DOM 里有没有这些字段（`document.querySelector` 试一下）

**产出**：`day0/recon.md`（侦察笔记）
- 数据主要在哪个接口
- 各字段的选择器或接口路径
- 是否需要登录才能看到完整数据

**成功标准**：能说清"标题从哪拿、价格从哪拿、销量从哪拿"。

---

### 🔑 Step 1 — 登录态 Cookie 获取（半天）

**目标**：拿到一个可复用的登录态 Cookie 文件。

**做法**：

> 🤖 **贴给 AI：**
> ```
> 用 Playwright 写 D:/pycharm/Person-Practice/淘宝爬虫练习/day1/get_cookie.py
> 
> 功能：
> 1. 启动有头 Chromium，打开 https://login.taobao.com
> 2. 等待用户手动扫码登录（input 阻塞，登录后回车继续）
> 3. 登录成功后，把 context.cookies() 保存到 day1/taobao_cookie.json
> 4. 再用保存的 Cookie 访问 https://i.taobao.com/my_taobao.htm，确认能拿到登录态页面
> 5. 打印 Cookie 数量和关键字段（_tb_token_ 等），确认有效
> 
> 用 D:/pycharm/Person-Practice/.venv/ 的 Python
> ```

**产出**：`day1/taobao_cookie.json` + `day1/get_cookie.py`

**成功标准**：用 Cookie 访问"我的淘宝"返回登录态内容（非跳登录页）。

---

### 📦 Step 2 — 单个详情页采集（1 天）

**目标**：给定一个商品 ID，拿到完整结构化 JSON。

**做法**：

> 🤖 **贴给 AI：**
> ```
> 用 Scrapling DynamicFetcher 写 D:/pycharm/Person-Practice/淘宝爬虫练习/day2/fetch_one.py
> 
> 功能：
> 1. 读取 day1/taobao_cookie.json 注入浏览器
> 2. 访问 https://item.taobao.com/item.htm?id={商品ID}（或 H5 端 m.tb.cn 短链）
> 3. 等待页面渲染完成（等价格元素出现）
> 4. 提取字段：标题、价格、原价、销量、SKU列表、主图URL、店铺名、评论数
> 5. 检测反爬：是否跳登录？是否出滑块？响应是否为空？
> 6. 保存到 data/test/{item_id}.json
> 7. 详细日志：每步打印状态
> 
> 参考 day0/recon.md 里的字段定位
> ```

**产出**：`day2/fetch_one.py` + `data/test/{item_id}.json`

**成功标准**：1 个商品，关键字段（标题/价格/销量/SKU）非空。

**反爬降级处理**：
- 跳登录 → Cookie 失效，回到 Step 1
- 出滑块 → 打印警告，暂停 60s，人工处理后继续
- 空响应 → 重试 3 次，仍失败则记录跳过

---

### 🔗 Step 3 — 关键词 → 搜索 → 详情链路（1 天）

**目标**：输入一个关键词，自动采集 20 个商品详情。

**做法**：

> 🤖 **贴给 AI：**
> ```
> 在 day3/ 下写两个脚本：
> 
> search_products.py：
> 1. DynamicFetcher + Cookie 访问 https://s.taobao.com/search?q={关键词}
> 2. 等搜索结果渲染完，提取前 20 个商品的 ID、标题、详情页 URL
> 3. 保存 day3/search_result_{关键词}.json
> 
> fetch_batch.py：
> 1. 读取 search_result.json
> 2. 逐个调用 Step 2 的采集逻辑（串行，每个间隔 random 5-10s）
> 3. 保存到 data/{关键词}/{item_id}.json
> 4. 每采集 5 个打印进度
> 5. 失败的记录到 day3/failed.json，最后统一重试一次
> ```

**产出**：`day3/search_products.py` + `day3/fetch_batch.py` + `data/{关键词}/` 下 20 个 JSON

**成功标准**：1 个关键词 → ≥15 个商品完整 JSON（允许少量失败）。

---

### 🏭 Step 4 — 批量稳定 + 复盘（1 天）

**目标**：多关键词无人值守跑完，带断点续传。

**做法**：

> 🤖 **贴给 AI：**
> ```
> 在 day4/ 下写 batch.py：
> 1. 从 keywords.txt 读关键词列表（每行一个）
> 2. 对每个关键词跑 Step 3 完整链路
> 3. 关键词之间间隔 60-120s
> 4. 断点续传：记录已完成的 item_id 到 day4/done.json，重跑时跳过
> 5. Cookie 失效检测：访问失败且判定为登录态问题 → 暂停 + 提示重新扫码
> 6. 最终打印统计：成功 X / 失败 X / 跳过 X
> ```

**产出**：`day4/batch.py` + 多关键词数据 + `day4/stats.txt`

**复盘**：在 `notes.md` 写总结
- Scrapling DynamicFetcher 对淘宝效果如何？
- 哪些字段 DOM 能直接拿、哪些必须走接口？
- 反爬踩了哪些坑？
- 长期跑的话成本在哪（Cookie 维护？代理？）

**成功标准**：3-5 个关键词 × 20 条，无人值守跑完，成功率 ≥70%。

---

## 五、目录结构

```
淘宝爬虫练习/
├── PLAN.md                 ← 本文件
├── notes.md                ← 复盘笔记（Step 4 写）
├── day0/
│   └── recon.md            ← 侦察笔记
├── day1/
│   ├── get_cookie.py
│   └── taobao_cookie.json  ← 登录态（已在 .gitignore，勿提交）
├── day2/
│   └── fetch_one.py
├── day3/
│   ├── search_products.py
│   └── fetch_batch.py
├── day4/
│   ├── batch.py
│   ├── done.json           ← 断点续传记录
│   └── stats.txt
├── keywords.txt            ← 关键词列表
└── data/
    ├── test/
    └── {关键词}/
        └── {item_id}.json
```

---

## 六、常见坑预警 🚨

| 坑 | 现象 | 排查方向 |
|---|---|---|
| 搜索页跳登录 | 返回空或跳 login.taobao.com | Cookie 没注入或已过期，回 Step 1 |
| 详情页数据空 | 渲染后 DOM 里没价格/销量 | 数据在异步接口，看 recon.md 走 mtop 接口 |
| 出滑块 | 页面卡在验证码 | 立即降速，暂停等人工；别硬刚 |
| Cookie 频繁失效 | 几小时就掉登录 | 淘宝风控感知到自动化，降频 + 换 IP |
| DynamicFetcher 超时 | 页面没渲染完 | 增加等待时间，用 `wait` 参数等关键元素 |
| IP 被 403 | 所有请求失败 | 换网络/等几小时；练习阶段不买代理 |

---

## 七、进度检查清单

- [ ] Step 0：侦察笔记 recon.md，搞清字段来源
- [ ] Step 1：taobao_cookie.json 可用，能访问登录态页面
- [ ] Step 2：单个商品完整 JSON，关键字段非空
- [ ] Step 3：1 个关键词 → 15+ 个商品 JSON
- [ ] Step 4：3-5 关键词无人值守跑完，复盘 notes.md

---

## 八、重要提醒 ⚠️

1. `taobao_cookie.json` 含登录态，**已在 .gitignore，绝不能提交到 GitHub**
2. 采集到的数据仅供学习，**不传播、不商用**
3. 控制频率，别给淘宝服务器添麻烦
4. 遇到风控就停，**练习项目不值得硬刚反爬**

---

*v2 计划制定于 2026-08-02*
