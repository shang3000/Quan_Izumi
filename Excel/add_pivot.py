"""Excel 数据透视表 - win32com 实现"""
import os
import random
import win32com.client

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(OUTPUT_DIR, "openpyxl_全功能展示.xlsx")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openpyxl_全功能展示_透视表.xlsx")

# Excel 常量
xlDatabase = 1
xlRowField = 4
xlColumnField = 3
xlDataField = 4  # 注意：xlDataField 也是 4
xlSum = -4157
xlColumnClustered = 51


def main():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(SOURCE_FILE)

        # ========================================
        # 创建透视表数据源
        # ========================================
        ws_data = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
        ws_data.Name = "透视数据"

        headers = ["日期", "部门", "产品", "数量", "单价", "金额"]
        for i, h in enumerate(headers, 1):
            cell = ws_data.Cells(1, i)
            cell.Value = h
            cell.Font.Bold = True
            cell.Interior.Color = 0x00D881
            cell.Font.Color = 0xFFFFFF

        random.seed(42)
        departments = ["技术部", "产品部", "设计部", "市场部"]
        products = ["笔记本电脑", "显示器", "键盘", "鼠标", "耳机"]
        months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]

        row = 2
        for month in months:
            for _ in range(4):
                ws_data.Cells(row, 1).Value = month
                ws_data.Cells(row, 2).Value = random.choice(departments)
                ws_data.Cells(row, 3).Value = random.choice(products)
                ws_data.Cells(row, 4).Value = random.randint(5, 50)
                ws_data.Cells(row, 5).Value = random.randint(100, 8000)
                ws_data.Cells(row, 5).NumberFormat = "#,##0"
                ws_data.Cells(row, 6).Value = ws_data.Cells(row, 4).Value * ws_data.Cells(row, 5).Value
                ws_data.Cells(row, 6).NumberFormat = "#,##0"
                if row % 2 == 0:
                    for c in range(1, 7):
                        ws_data.Cells(row, c).Interior.Color = 0xECF9FD
                row += 1

        data_end_row = row - 1

        # ========================================
        # 透视表1：按部门汇总
        # ========================================
        ws_pivot1 = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
        ws_pivot1.Name = "按部门透视"

        pivot_cache = wb.PivotCaches().Create(
            SourceType=xlDatabase,
            SourceData=f"透视数据!A1:F{data_end_row}"
        )

        pivot_table = pivot_cache.CreatePivotTable(
            TableDestination=ws_pivot1.Range("A3"),
            TableName="部门汇总"
        )

        # 行字段：部门（第2列）
        pivot_table.PivotFields(2).Orientation = xlRowField

        # 值字段：金额（第6列）求和
        pivot_table.AddDataField(pivot_table.PivotFields(6), "金额合计", xlSum)

        # 值字段：数量（第4列）求和
        pivot_table.AddDataField(pivot_table.PivotFields(4), "数量合计", xlSum)

        # 标题
        ws_pivot1.Cells(1, 1).Value = "按部门汇总"
        ws_pivot1.Cells(1, 1).Font.Size = 16
        ws_pivot1.Cells(1, 1).Font.Bold = True

        # 添加透视图
        chart_obj = ws_pivot1.ChartObjects().Add(250, 10, 400, 300)
        chart = chart_obj.Chart
        chart.ChartType = xlColumnClustered
        chart.SetSourceData(Source=pivot_table.TableRange1)
        chart.HasTitle = True
        chart.ChartTitle.Text = "各部门销售金额"

        # ========================================
        # 透视表2：按产品汇总（简化版）
        # ========================================
        ws_pivot2 = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
        ws_pivot2.Name = "产品透视"

        pivot_cache2 = wb.PivotCaches().Create(
            SourceType=xlDatabase,
            SourceData=f"透视数据!A1:F{data_end_row}"
        )

        pivot_table2 = pivot_cache2.CreatePivotTable(
            TableDestination=ws_pivot2.Range("A3"),
            TableName="产品汇总"
        )

        # 行字段：产品（第3列）
        pivot_table2.PivotFields(3).Orientation = xlRowField

        # 值字段：金额（第6列）
        pivot_table2.AddDataField(pivot_table2.PivotFields(6), "金额合计", xlSum)

        # 值字段：数量（第4列）
        pivot_table2.AddDataField(pivot_table2.PivotFields(4), "数量合计", xlSum)

        ws_pivot2.Cells(1, 1).Value = "按产品汇总"
        ws_pivot2.Cells(1, 1).Font.Size = 16
        ws_pivot2.Cells(1, 1).Font.Bold = True

        # ========================================
        # 透视表3：按月份汇总
        # ========================================
        ws_pivot3 = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
        ws_pivot3.Name = "月份透视"

        pivot_cache3 = wb.PivotCaches().Create(
            SourceType=xlDatabase,
            SourceData=f"透视数据!A1:F{data_end_row}"
        )

        pivot_table3 = pivot_cache3.CreatePivotTable(
            TableDestination=ws_pivot3.Range("A3"),
            TableName="月份汇总"
        )

        # 行字段：日期（第1列）
        pivot_table3.PivotFields(1).Orientation = xlRowField

        # 值字段：金额（第6列）
        pivot_table3.AddDataField(pivot_table3.PivotFields(6), "金额合计", xlSum)

        ws_pivot3.Cells(1, 1).Value = "按月份汇总"
        ws_pivot3.Cells(1, 1).Font.Size = 16
        ws_pivot3.Cells(1, 1).Font.Bold = True

        # ========================================
        # 保存
        # ========================================
        wb.SaveAs(OUTPUT_FILE)
        wb.Close()
        print(f"Excel with pivot tables saved: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        excel.Quit()


if __name__ == "__main__":
    main()
