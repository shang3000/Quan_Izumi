# Person-Practice 项目配置

## 项目概览

办公三件套生成器：PPT + Word + Excel，统一配色体系，CLI 脚本驱动。

| 组件 | 静态生成 | 动态增强 | 详细配置 |
|------|----------|----------|----------|
| PPT | python-pptx | win32com 动画 | [PPT/CLAUDE.md](PPT/CLAUDE.md) |
| Word | python-docx | win32com 目录刷新 | [Word/CLAUDE.md](Word/CLAUDE.md) |
| Excel | openpyxl | win32com 透视表 | [Excel/CLAUDE.md](Excel/CLAUDE.md) |

## 共享配置

- **虚拟环境**：`D:/pycharm/Person-Practice/.venv/Scripts/python.exe`
- **print 不要用 emoji**（Windows GBK 编码报错）
- **三件套都用 CLI 脚本**：`python make_xxx.py`

## 设计原则（三件套通用）

- **大面积用主色** — 用户要看到颜色的冲击力
- **两种主色要交融** — 不是分开放
- **对称布局配色互换** — 布局一致但颜色相反
- **不留大面积空白** — 用色块、卡片、分隔线填满
