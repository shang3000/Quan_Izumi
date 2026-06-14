# PPT 制作配置

## 技术栈

- **静态生成**：python-pptx
- **动态动画**：win32com（PowerPoint COM 自动化）
- **不要用 MckEngine** — 设计语言固定，不适合自定义配色

## 画布尺寸

- **标准 16:9**：10 × 5.625 英寸（25.4 × 14.2875 cm）
- **宽屏 16:9**：13.333 × 7.5 英寸（MckEngine 默认）
- 安全边距：0.2~0.3 英寸
- 所有元素 `top + height ≤ 画布高度`，`left + width ≤ 画布宽度`

## 排版约束

- 每页内容不要塞太满，留出呼吸空间
- 文字框高度预留足够空间，避免溢出截断
- 圆角矩形底部不要贴画布底
- 多列布局列间距保持 0.3 英寸

## 文件输出

- 输出目录：`D:/pycharm/Person-Practice/PPT/`
- 虚拟环境：`D:/pycharm/Person-Practice/.venv/Scripts/python.exe`
- print 不要用 emoji（Windows GBK 编码报错）

## Helper 函数

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_SHAPE

def set_bg(s, c):
    """设置页面背景色"""
    f = s.background.fill; f.solid(); f.fore_color.rgb = c

def rect(s, l, t, w, h, c):
    """添加圆角矩形"""
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = c; sh.line.fill.background()
    return sh

def txt(s, l, t, w, h, text, sz=14, c=DARK, b=False, a=PP_ALIGN.LEFT):
    """添加文本框"""
    tb = s.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text
    p.font.size = Pt(sz); p.font.color.rgb = c; p.font.bold = b
    p.font.name = 'Microsoft YaHei'; p.alignment = a
    return tb
```

## 设计原则

- **大面积用主色** — 用户要看到颜色的冲击力，不是只在小圆点上
- **两种主色要交融** — 如石榴裙红做色块 + 明月珰珠光做底色
- **对称布局配色互换** — 左右对比时，布局一致但颜色相反
- **每页不留大面积空白** — 用色块、卡片、分隔线填满

## 制作流程

1. **内容 & 主题** → 定大纲、受众、页数
2. **静态排版** → python-pptx 从零写，每个 shape 颜色/坐标/大小直接控制
3. **动态动画** → win32com 添加（可选）

## 动画制作（win32com）

- **脚本**：`PPT/add_animations.py`
- **原理**：打开静态 PPT → 逐页逐 shape 添加动画 → 另存为新文件
- **动画方案**：第一个形状 ON_CLICK，后续 AFTER_PREVIOUS（0.1s 延迟）
- **淡入时长**：0.5s
- **页面切换**：PP_FADE（1.0s）
- **注意**：需要 PowerPoint 已安装
- **输出**：原文件名加 `_动画` 后缀

## 踩坑记录

### MckEngine 颜色改不动
- `from module import *` 在 import 时复制值，后续改模块属性不生效
- Theme 颜色 vs 内联颜色 — MckEngine shape 引用 theme 色，只改内联看不到变化
- **结论：想完全控制颜色就不要用 MckEngine，从零写**

### Theme 颜色修改
- PPT 有两层颜色：theme 层（`ppt/theme/theme1.xml`）和内联层（`srgbClr`）
- 要改 theme 需要 zip 解压 → 改 theme1.xml → 重新打包

---

## 配色方案

### 明月珰 × 石榴裙（东方美学）

| 色名 | 色值 | 用途 |
|------|------|------|
| 石榴裙 | `#C41E3A` | 正红，大面积色块、表头、重点 |
| 深石榴 | `#8B1528` | 石榴裙暗色，装饰圆 |
| 明月珰 | `#F5F0E8` | 珠光暖白，页面背景 |
| 深珠光 | `#E8E0D4` | 珠光暗色 |
| 金色 | `#C9963A` | 琉璃金，装饰分隔线 |
| 黛色 | `#2B2D42` | 正文深色 |
| 次要文字 | `#7A7C8E` | 灰色说明文字 |
| 浅珠光线 | `#D0C8BC` | 分隔线 |

### 雪青 × 紫罗兰

| 色名 | 色值 | RGB |
|------|------|-----|
| 紫罗兰 | `#7356B1` | 115, 86, 177 |
| 深紫罗兰 | `#5A4090` | — |
| 雪青 | `#BDB5D7` | 189, 181, 215 |
| 薰衣草 | `#9B7EC8` | — |
| 浅雪青 | `#D8D2E8` | — |

### 玉色 × 碧山

| 色名 | 色值 | RGB |
|------|------|-----|
| 碧山 | `#8BAF56` | 139, 175, 86 |
| 深碧 | `#6B8F3C` | — |
| 玉色 | `#FAF8F4` | 250, 248, 244 |
| 浅碧 | `#E8F0E0` | — |
| 嫩绿 | `#A8C878` | — |

### 秋波蓝 × 若竹

| 色名 | 色值 | RGB |
|------|------|-----|
| 秋波蓝 | `#A5CCDC` | 165, 204, 220 |
| 深秋蓝 | `#7AAFC4` | — |
| 若竹 | `#84BB9F` | 132, 187, 159 |
| 深竹 | `#6A9E82` | — |
| 薄荷 | `#B8D8CC` | — |

### 碧落 × 绀宇

| 色名 | 色值 | RGB |
|------|------|-----|
| 绀宇 | `#003C75` | 0, 60, 117 |
| 碧落 | `#AFD0F2` | 175, 208, 242 |
| 深蓝 | `#002855` | — |
| 浅蓝 | `#D4E6F6` | — |
| 湖蓝 | `#5BA0D0` | — |

### 十样锦 × 烟墨色

| 色名 | 色值 | RGB |
|------|------|-----|
| 烟墨色 | `#5D4F57` | 93, 79, 87 |
| 十样锦 | `#FAC7B7` | 250, 199, 183 |
| 深墨 | `#453A40` | — |
| 浅粉 | `#FDE8E0` | — |
| 藕荷 | `#D4A89C` | — |

### 奶酪色 × 蒂芙尼蓝

| 色名 | 色值 | RGB |
|------|------|-----|
| 蒂芙尼蓝 | `#81D8D1` | 129, 216, 209 |
| 深蒂蓝 | `#5CBDB4` | — |
| 奶酪色 | `#FBF7D8` | 251, 247, 216 |
| 浅奶酪 | `#FDF9EC` | — |
| 薄荷绿 | `#A8E0D8` | — |

### 雾灰色 × 普鲁士蓝

| 色名 | 色值 | RGB |
|------|------|-----|
| 普鲁士蓝 | `#013054` | 1, 48, 84 |
| 深蓝 | `#001E38` | — |
| 雾灰色 | `#E3DAD6` | 227, 218, 214 |
| 浅灰 | `#EDE8E4` | — |
| 钢蓝 | `#4A7A9C` | — |

### 桃夭 × 桔梗色

| 色名 | 色值 | RGB |
|------|------|-----|
| 桔梗色 | `#6966B6` | 105, 102, 182 |
| 深桔梗 | `#504D94` | — |
| 桃夭 | `#F8CED7` | 248, 206, 215 |
| 浅桃 | `#FDE4EA` | — |
| 紫丁香 | `#9090CC` | — |

### 女贞黄 × 鹤顶红

| 色名 | 色值 | RGB |
|------|------|-----|
| 鹤顶红 | `#D44636` | 212, 70, 54 |
| 深红 | `#B03028` | — |
| 女贞黄 | `#FBEEAF` | 251, 238, 175 |
| 浅黄 | `#FDF5E0` | — |
| 橙金 | `#E8A060` | — |

### 浅卡其色 × 凡戴克棕

| 色名 | 色值 | RGB |
|------|------|-----|
| 凡戴克棕 | `#4B2C23` | 75, 44, 35 |
| 深棕 | `#35201A` | — |
| 浅卡其色 | `#D6C3B2` | 214, 195, 178 |
| 浅米 | `#E8DDD2` | — |
| 焦糖 | `#A07858` | — |
