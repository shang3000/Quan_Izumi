# Excel 制作配置

## 技术栈

- **静态生成**：openpyxl
- **动态增强**：win32com（数据透视表、透视图）

## 默认样式

- 正文字体：`Microsoft YaHei`
- 正文字号：11pt
- 表头：白色文字 `FFFFFF` + 主色背景（蒂芙尼蓝 `81D8D1`）
- 数据行交替色：奇数行白色、偶数行浅奶黄 `FDF9EC`
- 边框：浅灰色细线 `D0C8BC`
- 对齐：居中对齐 + 自动换行

## 文件输出

- 输出目录：`D:/pycharm/Person-Practice/Excel/`
- 虚拟环境：`D:/pycharm/Person-Practice/.venv/Scripts/python.exe`
- print 不要用 emoji（Windows GBK 编码报错）

## openpyxl vs win32com

| 功能 | openpyxl | win32com |
|------|----------|----------|
| 单元格格式（字体/颜色/对齐） | ✅ | ✅ |
| 数字格式（千分位/百分比/日期） | ✅ | ✅ |
| 公式（SUM/VLOOKUP/COUNTIF） | ✅ | ✅ |
| 图表（柱状/折线/饼图） | ✅ | ✅ |
| 条件格式（数据条/色阶/规则） | ✅ | ✅ |
| 数据验证（下拉选择） | ✅ | ✅ |
| 冻结窗格 | ✅ | ✅ |
| 自动筛选 | ✅ | ✅ |
| 打印设置（横向/重复行） | ✅ | ✅ |
| **数据透视表** | ❌ | ✅ |
| **透视图** | ❌ | ✅ |

- 基础表格 → openpyxl 够用
- 数据透视表/透视图 → 必须 win32com

## openpyxl Helper 函数

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# 预制样式
header_font = Font(name="Microsoft YaHei", bold=True, color="FFFFFF", size=12)
header_fill = PatternFill(start_color="81D8D1", end_color="81D8D1", fill_type="solid")
normal_font = Font(name="Microsoft YaHei", color="2B2D42", size=11)
center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin_border = Border(
    left=Side(style="thin", color="D0C8BC"),
    right=Side(style="thin", color="D0C8BC"),
    top=Side(style="thin", color="D0C8BC"),
    bottom=Side(style="thin", color="D0C8BC"),
)

def style_header_row(ws, row, cols):
    """设置表头行样式"""
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

def style_data_rows(ws, start_row, end_row, cols):
    """数据行交替色"""
    for r in range(start_row, end_row + 1):
        for c in range(1, cols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = normal_font
            cell.alignment = center_align
            cell.border = thin_border
            if (r - start_row) % 2 == 1:
                cell.fill = PatternFill(start_color="FDF9EC", end_color="FDF9EC", fill_type="solid")
```

## win32com 透视表关键代码

```python
import win32com.client

# 常量（避免 constants 拿不到的问题）
xlDatabase = 1
xlRowField = 4
xlSum = -4157
xlColumnClustered = 51

# 创建透视缓存
pivot_cache = wb.PivotCaches().Create(
    SourceType=xlDatabase,
    SourceData="Sheet1!A1:F100"
)

# 创建透视表
pivot_table = pivot_cache.CreatePivotTable(
    TableDestination=ws.Range("A3"),
    TableName="汇总表"
)

# 行字段（用列索引，避免中文编码问题）
pivot_table.PivotFields(2).Orientation = xlRowField

# 值字段（求和）
pivot_table.AddDataField(pivot_table.PivotFields(6), "金额合计", xlSum)

# 透视图
chart_obj = ws.ChartObjects().Add(Left=250, Top=10, Width=400, Height=300)
chart = chart_obj.Chart
chart.ChartType = xlColumnClustered
chart.SetSourceData(Source=pivot_table.TableRange1)
```

## 踩坑记录

### win32com 中文字段名编码失败
- `PivotFields("中文名")` 在 COM 调用时可能编码失败
- **解决方法**：用列索引 `PivotFields(2)` 代替字段名
- 字段顺序 = 数据源列顺序（1=第1列，2=第2列...）
- 中文 Sheet 名同样问题，用 `Sheets(1)` 代替 `Sheets("名称")`

### win32com 常量获取失败
- `from win32com.client import constants as xl` 有时拿不到常量
- **解决方法**：直接用数字常量
  - `xlDatabase = 1`
  - `xlRowField = 4`
  - `xlColumnField = 3`
  - `xlSum = -4157`
  - `xlCenter = -4108`
  - `xlColumnClustered = 51`

### openpyxl 无法创建透视表
- openpyxl 有 `TableDefinition` 类，但没有高层 API
- 手写 XML 极其复杂，不现实
- 透视表功能必须用 win32com
