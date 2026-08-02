# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Python 学习与实践仓库，核心功能是**办公三件套生成器**（PPT + Word + Excel），使用 Python 脚本自动化生成办公文档。

## Environment

- **Python**: `.venv/Scripts/python.exe`
- **OS**: Windows 11（GBK 编码）
- **关键依赖**: python-pptx, python-docx, openpyxl, pywin32

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
| PPT | python-pptx | win32com 动画 | [PPT/AGENTS.md](PPT/AGENTS.md) |
| Word | python-docx | win32com 目录刷新 | [Word/AGENTS.md](Word/AGENTS.md) |
| Excel | openpyxl | win32com 透视表 | [Excel/AGENTS.md](Excel/AGENTS.md) |

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
