# Word 制作配置

## 技术栈

- **静态生成**：python-docx
- **动态增强**：win32com（目录刷新、水印、批注等）

## 页面设置

- **A4 纸**：21 × 29.7 cm
- 上下边距：2.54 cm，左右边距：3.18 cm
- 横向页面：`section.orientation = WD_ORIENT.LANDSCAPE`
- 页面宽度：`section.page_width = Cm(21)`
- 页面高度：`section.page_height = Cm(29.7)`

## 默认字体

- 正文字体：`Microsoft YaHei`（微软雅黑）
- 正文字号：12pt
- 标题用彩色，正文用深色 `#2B2D42`
- **中文字体两步设置（缺一不可）**：
  ```python
  run.font.name = 'Microsoft YaHei'          # 西文字体
  run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')  # 东亚字体
  ```

## 文件输出

- 输出目录：`D:/pycharm/Person-Practice/Word/`
- 虚拟环境：`D:/pycharm/Person-Practice/.venv/Scripts/python.exe`
- print 不要用 emoji（Windows GBK 编码报错）

## python-docx vs win32com

| 功能 | python-docx | win32com |
|------|-------------|----------|
| 段落、文字排版 | ✅ | ✅ |
| 表格（创建、合并、底色） | ✅ | ✅ |
| 页眉页脚、页码 | ✅ | ✅ |
| 分节、分栏、横向 | ✅ | ✅ |
| 样式、字体、颜色 | ✅ | ✅ |
| 有序/无序列表 | ✅ | ✅ |
| **目录刷新** | ❌ 只能插入域代码 | ✅ |
| **水印** | ❌ | ✅ |
| **批注/修订** | ❌ | ✅ |
| **邮件合并** | ❌ | ✅ |

- 基础文档 → python-docx 够用
- 目录自动更新 → 需要 win32com

## Helper 函数

```python
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

def set_cell_bg(cell, color_hex):
    """设置单元格背景色"""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_paragraph_spacing(para, before=0, after=0, line=None):
    """设置段落间距"""
    pf = para.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if line:
        pf.line_spacing = Pt(line)

def add_colored_heading(doc, text, level=1, color=None):
    """添加彩色标题"""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = color
    return heading

def add_horizontal_line(doc, color="81D8D1"):
    """添加水平分隔线"""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:bottom w:val="single" w:sz="12" w:space="1" w:color="{color}"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)
    return p
```

## 表格样式技巧

- 表头：白色文字 + 主色背景（如蒂芙尼蓝 `81D8D1`）
- 数据行交替色：奇数行白色、偶数行浅奶黄 `FDF9EC`
- 合并单元格：先 `cell.merge(other_cell)`，再设置内容和样式
- 水平对齐：`p.alignment = WD_ALIGN_PARAGRAPH.CENTER`
- 垂直对齐：`cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER`

## 踩坑记录

### 合并单元格行索引
- 合并行的行数不变，但访问时要注意索引
- 数据行从 `rows[1]` 开始（`rows[0]` 是合并的表头）

### 目录域代码
- python-docx 只能插入 TOC 域代码，不能刷新
- 需要在 Word 中右键 → 更新域，或用 win32com 刷新
