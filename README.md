# Person-Practice 🐍

> 个人 Python 练习仓库 —— 从爬虫到数据分析，从自动化到小游戏，边学边玩边沉淀。

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Personal_Use-8BAF56)](LICENSE)

---

## 写在前面

这个仓库记录了我学习 Python 的点点滴滴。  
代码可能不完美，但每一行都经过我的理解与调试 —— 早期一行行手敲，现在更多是 vibe coding（AI 辅助 + 人工把关）。如果你也在学 Python，希望这里能给你一些灵感 💡

**仓库定位**：个人练习 + 小工具集合，不是生产级项目。  
**使用原则**：请遵守相关法律法规和平台规则，爬虫类脚本仅供学习交流。

---

## 仓库地图 🗺️

| 目录 | 内容 | 亮点 |
|------|------|------|
| [`爬虫/`](爬虫/) | 视频/音乐/漫画下载器、网页数据采集 | B站、Twitter/X、网易云、漫画站批量下载 |
| [`淘宝爬虫练习/`](淘宝爬虫练习/) | 淘宝商品详情爬虫练习 | 基于 Scrapling 的三天学习计划 |
| [`theCrag/`](theCrag/) | 全球攀岩数据爬虫 | 异步爬取 + 断点续传 + CSV 导出 |
| [`电影票分析/`](电影票分析/) | 影院 K-means 聚类分析 | 数据分析完整链路 + 可视化报告 |
| [`Excel/`](Excel/) | openpyxl 办公自动化 | Excel 全功能展示 + 透视表生成 |
| [`Word/`](Word/) | python-docx 办公自动化 | Word 全功能展示 + 申报书排版 |
| [`PPT/`](PPT/) | pptxgenjs / python-pptx 生成 PPT | Dify Agent、PyCharm 团队协作等主题 |
| [`游戏/`](游戏/) | Pygame 小游戏 | 砖块破坏者 |
| [`图表/`](图表/) | pyecharts 可视化 | 动态柱形图、折线图 |
| [`习思想期末复习/`](习思想期末复习/) | 期末复习辅助脚本 | 知识点整理 + 刷题题库 HTML |
| [`课程源码/`](课程源码/) | Python 基础到进阶 | 语法、函数、面向对象、SQL、PySpark |
| [`综合案例/`](综合案例/) | 数据分析综合案例 | 每日销售额可视化 |
| [`进阶/`](进阶/) | SQL、Spark、面向对象进阶 | 练习代码 |
| [`练习/`](练习/) | 零散练习和小实验 | Excel 数据处理练习 |
| [`自动化脚本/`](自动化脚本/) | 待补充的自动化脚本目录 | - |

---

## 重点项目介绍 ⭐

### 1. 爬虫小工具集合 [`爬虫/`](爬虫/)

一套"拿到链接就能下"的小工具，支持多种输入格式：

- **`manga_download.py`** — 漫画图片批量下载器
  - 支持章节 URL / 单张图片 URL / cURL 命令
  - 自动检测系统代理、多线程并发、失败重试、断点续传
- **`bilibili_download.py`** — B站视频下载器
  - 支持 dash/durl 格式，自动合并音视频（需 ffmpeg）
- **`Twitter_download_video.py`** — Twitter/X 视频下载器
  - 支持视频 URL / 帖子 URL / Sotwe 镜像 / cURL
- **`Wangyi_download_music.py`** — 网易云音乐音频下载器
  - 通过浏览器开发者工具获取临时签名链接下载

### 2. 淘宝爬虫练习 [`淘宝爬虫练习/`](淘宝爬虫练习/)

为期三天的 Scrapling 爬虫实战练习计划，目标是跑通「关键词 → 搜索页 → 商品详情页」的完整链路。详见 [`PLAN.md`](淘宝爬虫练习/PLAN.md)。

### 3. theCrag 全球攀岩数据爬虫 [`theCrag/`](theCrag/)

从 [theCrag.com](https://www.thecrag.com) 采集全球攀岩区域和路线数据：

- 异步爬取，支持断点续传
- 输出 `areas_v2.csv` 和 `routes_v2.csv`
- 已修复 parent_url、认证 cookie、grade/type 分布提取

### 4. 电影票数据分析 [`电影票分析/`](电影票分析/)

一次完整的数据分析练习：

- 数据清洗 + K-means 聚类
- PCA 降维可视化
- 生成 HTML 报告和 PPT

### 5. Office 自动化三件套

| 目录 | 技术 | 产出 |
|------|------|------|
| [`Excel/`](Excel/) | `openpyxl` | 全功能展示 Excel + 透视表 |
| [`Word/`](Word/) | `python-docx` | 全功能展示 Word + 已排版申报书 |
| [`PPT/`](PPT/) | `python-pptx` / `pptxgenjs` | Dify Agent、PyCharm 团队协作等主题 PPT |

### 6. Pygame 小游戏 [`游戏/`](游戏/)

- **`brick_breaker.py`** — 竖屏砖块破坏者，带连锁变色和分裂小球机制 🎮

### 7. 学习资料沉淀

- [`experiments.html`](experiments.html) — Python 数据分析实验手册
- [`习思想期末复习/刷题题库.html`](习思想期末复习/刷题题库.html) — 期末复习题库
- [`课程源码/`](课程源码/) — 从基础语法到 PySpark 的完整学习代码

---

## 技术栈 🛠️

- **编程语言**：Python 3.10+
- **爬虫**：requests、Scrapling、urllib、asyncio、BeautifulSoup
- **数据分析**：pandas、numpy、matplotlib、scikit-learn
- **办公自动化**：openpyxl、python-docx、python-pptx
- **PPT 生成**：pptxgenjs（Node.js）
- **可视化**：pyecharts、matplotlib
- **游戏开发**：pygame
- **大数据入门**：PySpark

---

## 快速开始 🚀

1. 克隆仓库

```bash
git clone https://github.com/<your-username>/Person-Practice.git
cd Person-Practice
```

2. 创建虚拟环境（推荐）

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. 各子项目依赖不同，进入对应目录后按需安装

```bash
# 例如运行爬虫项目
cd 爬虫
pip install requests
python manhua_download.py
```

> 小提示：部分脚本需要 ffmpeg（视频合并）、浏览器开发者工具抓取的 Cookie/URL 等，详见各脚本头部注释。

---

## 免责声明 ⚠️

1. 本仓库所有代码仅供**学习交流**使用。
2. 爬虫类脚本请严格遵守目标网站的 `robots.txt` 和相关法律法规，**禁止用于商业用途或大规模数据采集**。
3. 下载的音视频、图片等版权归原权利人所有，请勿传播或商用。
4. 因使用本仓库代码造成的任何后果，由使用者自行承担。

---

*Last updated: 2026-08-02*
