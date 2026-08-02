# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 学习与实践仓库，核心功能是**办公三件套生成器**（PPT + Word + Excel），使用 Python 脚本自动化生成办公文档。

## Environment

- **Python**: `.venv/Scripts/python.exe`
- **OS**: Windows 11（GBK 编码）

### 已安装依赖

#### 办公三件套核心
- python-pptx 1.0.2 — PPT 生成
- python-docx 1.2.0 — Word 生成
- openpyxl 3.1.5 — Excel 生成
- pywin32 312 — Office COM 自动化（动画、目录刷新、透视表）

#### 爬虫相关
- scrapling 0.4.8 — Cloudflare 绕过（AsyncStealthySession）
- requests 2.34.2 — HTTP 请求
- beautifulsoup4 4.13.5 — HTML 解析
- lxml 6.1.1 — XML/HTML 解析
- playwright 1.59.0 — 浏览器自动化
- cloudscraper 1.2.71 — Cloudflare 绕过
- curl_cffi 0.15.0 — 模拟浏览器 TLS 指纹

#### 数据分析
- pandas 2.3.3 — 数据处理
- numpy 2.2.6 — 数值计算
- matplotlib 3.10.9 — 数据可视化
- scipy 1.15.3 — 科学计算
- scikit-learn 1.7.2 — 机器学习

#### 其他工具
- rich 15.0.0 — 终端富文本输出
- Pillow 12.2.0 — 图像处理
- pdfplumber 0.11.10 — PDF 解析
- msoffcrypto-tool 6.0.0 — Office 文件加密/解密
- DrissionPage 4.1.1.4 — 浏览器自动化（另一种方案）

## Running Scripts

```bash
# 办公三件套
.venv/Scripts/python.exe PPT/make_ppt.py
.venv/Scripts/python.exe Word/make_word.py
.venv/Scripts/python.exe Excel/make_excel.py

# 挑战杯
.venv/Scripts/python.exe 挑战杯/convert_to_ppt.py
.venv/Scripts/python.exe 挑战杯/convert_to_word.py
```

## Architecture

### 办公三件套（核心）

| 组件 | 静态生成 | 动态增强 | 详细配置 |
|------|----------|----------|----------|
| PPT | python-pptx | win32com 动画 | [PPT/CLAUDE.md](PPT/CLAUDE.md) |
| Word | python-docx | win32com 目录刷新 | [Word/CLAUDE.md](Word/CLAUDE.md) |
| Excel | openpyxl | win32com 透视表 | [Excel/CLAUDE.md](Excel/CLAUDE.md) |

**设计模式**: 每个组件采用「静态生成 + 动态增强」两阶段流程：
1. python-pptx/docx/openpyxl 生成基础文件
2. win32com 打开文件添加高级功能（动画、目录刷新、透视表）

### 其他模块

- `挑战杯/` — 竞赛材料生成（PPT + Word），复用办公三件套的技术栈
- `课程源码/` — Python 学习笔记（函数、OOP、SQL、可视化等）
- `爬虫/` — 网络爬虫练习
- `综合案例/` — 数据分析案例

## Critical Constraints

1. **print 不要用 emoji** — Windows GBK 编码会报错
2. **三件套都用 CLI 脚本** — `python make_xxx.py` 模式
3. **win32com 需要安装 Office** — 动态增强功能依赖本地 Office
4. **Python 脚本开头加编码设置** — 解决 Windows 中文乱码问题：
   ```python
   import sys
   sys.stdout.reconfigure(encoding='utf-8')
   ```

## Design Principles（三件套通用）

- **大面积用主色** — 用户要看到颜色的冲击力
- **两种主色要交融** — 不是分开放
- **对称布局配色互换** — 布局一致但颜色相反
- **不留大面积空白** — 用色块、卡片、分隔线填满

## Common Pitfalls

- **MckEngine 颜色改不动** — `from module import *` 在 import 时复制值，后续改模块属性不生效
- **win32com 中文字段名编码失败** — 用列索引 `PivotFields(2)` 代替字段名
- **python-docx 中文字体两步设置** — 必须同时设置 `font.name` 和 `rFonts.set(qn('w:eastAsia'), name)`
- **Windows 中文乱码** — 先修根因（加编码设置），不要绕过问题写一堆 workaround

## 爬虫开发经验（theCrag 项目教训）

### 必须先验证再全量跑
- 探索页面结构后，**先爬 5-10 页测试数据质量**，确认字段提取正确再跑全量
- 不要假设选择器正确，必须看到实际数据验证

### 遇到问题要解决，不是跳过
- 发现大量 404 页面时，必须先排查原因（为什么是404？）
- theCrag 的404是因为深层页面需要登录认证，不是页面不存在
- 正确做法：用浏览器登录提取 cookie，爬虫带上 cookie 访问
- 错误做法：跳过 404 页面 → 导致 72% 数据缺失

### 认证页面处理流程
1. 发现大量 404 → 检查 URL 模式（是否都是深层页面）
2. 检查响应头（是否有 302 重定向到登录页）
3. 用浏览器手动登录，提取 cookie
4. 爬虫请求时带上 cookie
5. 验证数据完整性

### 层级数据爬取
- 爬取层级结构时，必须同时记录父子关系，便于后续生成完整链路
- URL 路径可以辅助生成层级链路，但需要处理中间层级缺失的情况
- 导出时必须包含层级路径字段（如 "亚洲 -> 中国 -> 北京 -> 白河"）

### 数据质量检查清单
- [ ] 字段提取率是否合理（低于 50% 要排查原因）
- [ ] 是否有异常值（如 "Error 404" 作为名称）
- [ ] 层级链路是否完整
- [ ] 数值字段是否合理（经纬度范围、线路数量等）
- [ ] 导出前去重、清理无效数据
