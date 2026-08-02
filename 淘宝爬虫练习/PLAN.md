# 淘宝商品详情爬虫 — 三天练习计划

> **定位：练习项目，不是接单交付。**  
> 目标：熟悉 Scrapling 框架 + 淘宝反爬实战 + 完整爬虫链路。  
> 工具链：Python + Scrapling + Claude Code（VSCode）辅助编码。

---

## 需求速读

- **平台**：淘宝（tb），pdd.txt 只是示例格式
- **输入**：关键词（如"机械键盘"）
- **输出**：商品详情页原始报文（HTML/API 响应），按关键词分文件夹保存
- **量**：练习阶段 50-100 条即可，不用追求 500/天
- **格式**：原始数据，不做解析、不整理成表格

---

## 技术要求

| 项 | 说明 |
|---|------|
| Python | 3.10+ |
| 虚拟环境 | `D:/pycharm/Person-Practice/.venv/`（Scrapling v0.4.8 已装） |
| 框架 | Scrapling（`StealthyFetcher` + `DynamicFetcher`） |
| 数据存储 | 原始报文保存为 `.html` / `.json` 文件 |

---

## 目录结构（已创建）

```
淘宝爬虫练习/
├── PLAN.md              ← 你在这
├── day1/                Day 1 脚本
├── day2/                Day 2 脚本
├── day3/                Day 3 脚本
├── data/                原始报文数据
│   └── 关键词1/
│       ├── 商品ID_1.html
│       └── ...
└── notes.md             学习笔记（自己记录）
```

---

---

## ☀️ Day 1：破冰 — 让 Scrapling 摸到淘宝

**目标**：Scrapling 能稳定访问淘宝商品详情页，拿到非空响应。

### Step 1.1 — 看示例数据
- 打开 `pdd.txt`（群文件里那个 112.7K 的 txt）
- 理解"原始报文"是什么格式（大概率是页面 HTML 源码或 JSON 响应）
- 明确：客户要的就是这种原始形态，不是解析后的表格

### Step 1.2 — 浏览器分析淘宝页面
在 Chrome 里做：
1. 打开淘宝，随便搜一个词（如「手机壳」）
2. 观察搜索结果页 URL：`s.taobao.com/search?q=...`
3. 点进一个商品详情页，观察 URL：`item.taobao.com/item.htm?id=xxx`
4. F12 → Network 标签 → 刷新页面 → 看哪些 XHR 请求返回了商品数据
5. 记录：数据在 HTML 里还是异步接口里？

### Step 1.3 — 写第一个测试脚本

> 🤖 **把这个贴给 Claude Code：**

```
用 Scrapling 写一个 test_fetch.py，放在 D:/pycharm/Person-Practice/淘宝爬虫练习/day1/ 下。

功能：
1. 用 StealthyFetcher 访问一个淘宝商品详情页
2. 打印响应状态码和内容前 500 字符
3. 如果被拦截/跳转，打印出被拦截的迹象

要求：
- 用 D:/pycharm/Person-Practice/.venv/ 里的 Python（Scrapling 已装）
- 加 try/except 和详细日志
- 把响应内容保存到 data/ 目录

参考 URL：https://item.taobao.com/item.htm?id=123456789（随便一个淘宝商品 ID）
```

### Step 1.4 — 调通后记录反爬经验
- 打开 `notes.md`，记录：
  - 遇到了什么反爬？（403？验证码？跳登录？JS 挑战？）
  - 用了什么参数解决的？
  - StealthyFetcher 哪些参数有效、哪些没用？

**Day 1 成功标准**：脚本能跑通，拿到 ≥1 个商品详情页的非空原始数据。

---

---

## 🌤️ Day 2：打通链路 — 关键词 → 列表 → 详情

**目标**：输入一个关键词，自动跑完完整采集链路。

### Step 2.1 — 搜索页爬取

> 🤖 **贴给 Claude Code：**

```
在 D:/pycharm/Person-Practice/淘宝爬虫练习/day2/ 写 search_products.py。

功能：
1. 输入：一个关键词（如"机械键盘"）
2. 用 Scrapling 的 DynamicFetcher（Playwright）访问淘宝搜索结果页
3. 等待页面加载完成后，提取搜索结果中的商品信息：
   - 商品 ID
   - 商品标题
   - 详情页 URL
4. 把结果保存为 search_result.json

注意：
- 搜索页 URL 格式：https://s.taobao.com/search?q={关键词}
- 可能需要滚动加载更多结果
- 提取 20 个商品即可，不用翻页太深
```

### Step 2.2 — 详情页串行爬取

> 🤖 **贴给 Claude Code：**

```
在 D:/pycharm/Person-Practice/淘宝爬虫练习/day2/ 写 fetch_details.py。

功能：
1. 读取 search_result.json 中的商品详情页 URL 列表
2. 逐个访问商品详情页，获取原始报文（HTML 源码）
3. 保存到 data/{关键词}/ 目录下，文件名用商品ID
4. 每次请求间隔 3-8 秒随机延迟
5. 实现简单的错误处理和重试（最多重试 3 次）

参考：使用 Day1 中验证过的 StealthyFetcher 配置
```

### Step 2.3 — 串联脚本

> 🤖 **贴给 Claude Code：**

```
写一个 run_day2.py，放在 day2/ 目录下，串联 Step 2.1 和 2.2：
1. 用户输入关键词
2. 自动调用 search_products.py → 得到商品列表
3. 自动调用 fetch_details.py → 爬取每个详情页
4. 打印进度和统计：成功/失败/跳过
```

### Step 2.4 — 如果搜索页被反爬
备选方案：不爬搜索页，直接手动收集一批商品 ID，跳过 Step 2.1。

**Day 2 成功标准**：输入一个关键词，脚本自动输出 10-20 个原始报文文件。

---

---

## ⛅ Day 3：批量稳定 — 跑起来 + 复盘

**目标**：脚本可无人值守跑完一批关键词。

### Step 3.1 — 多关键词批量

> 🤖 **贴给 Claude Code：**

```
在 D:/pycharm/Person-Practice/淘宝爬虫练习/day3/ 写 batch_spider.py。

功能：
1. 从 keywords.txt 读取关键词列表（每行一个）
2. 对每个关键词，跑完 Day 2 的完整链路
3. 数据按关键词分文件夹保存
4. 每个关键词之间间隔 30-60 秒
5. 实现断点续传：如果中途断了，重新运行能跳过已完成的
6. 最终打印总统计：成功 X 条 / 失败 X 条
```

### Step 3.2 — 测试运行
- 准备 3-5 个不同品类的关键词
- 每个关键词目标 20-30 条
- 观察稳定性

### Step 3.3 — 学习复盘

打开 `notes.md`，写一份总结（给未来的自己看）：

```
## Scrapling 使用总结

### 好的
- StealthyFetcher 哪些场景管用？
- DynamicFetcher（Playwright）在什么时候必需？
- 与之前用过的 requests/Selenium 比好在哪？

### 坑
- 淘宝反爬踩了哪些坑？
- 哪些问题 Scrapling 也救不了？

### 下次接单参考
- 爬淘宝商品详情页，合理报价应该是多少？
- 长期维护的话，每月固定成本有哪些？
```

---

---

## 🚨 常见坑预警

| 坑 | 现象 | 排查方向 |
|---|------|---------|
| 搜索页空白/跳登录 | 搜索页返回空或跳到 login.taobao.com | 需要 Cookie，DynamicFetcher 登录 |
| 详情页反爬 | 返回滑块验证码页面 | 降低频率、加代理、换 UA |
| 数据在异步接口里 | HTML 里找不到商品信息 | F12 Network 找 XHR 接口，直接请求 API |
| IP 被封 | 所有请求 403 | 代理池（练习阶段不用管，换个网络/等待） |

---

## 📋 进度检查清单

- [ ] Day 1：Scrapling 能访问淘宝详情页
- [ ] Day 2：关键词 → 搜索结果 → 详情页 完整链路
- [ ] Day 3：多关键词批量运行 + 复盘笔记

---

*规划写完，代码交给 Claude Code。我在 WorkBuddy 这边随时 review 👀*
