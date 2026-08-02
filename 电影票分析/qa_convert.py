"""将PPT导出为PNG图片用于视觉QA"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pythoncom
import win32com.client

ppt_path = os.path.abspath('实验分析流程与技术原理.pptx')
output_dir = os.path.abspath('qa_images')
os.makedirs(output_dir, exist_ok=True)

pythoncom.CoInitialize()
powerpoint = win32com.client.Dispatch("PowerPoint.Application")
presentation = powerpoint.Presentations.Open(ppt_path, WithWindow=False)
slide_count = presentation.Slides.Count
print(f"PPT共 {slide_count} 页，开始导出...")

for i in range(1, slide_count + 1):
    slide = presentation.Slides(i)
    img_path = os.path.join(output_dir, f"slide_{i:02d}.png")
    slide.Export(img_path, "PNG", 1280, 720)
    print(f"  slide_{i:02d}.png 导出完成")

presentation.Close()
powerpoint.Quit()
pythoncom.CoUninitialize()
print(f"\n全部 {slide_count} 页导出到 {output_dir}")
