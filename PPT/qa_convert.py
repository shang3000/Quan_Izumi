"""Convert PPT to images for visual QA using win32com"""
import os
import pythoncom
import win32com.client

pythoncom.CoInitialize()

ppt_path = os.path.abspath(r"D:\pycharm\Person-Practice\PPT\Claude_Code_CLI_使用指南.pptx")
output_dir = os.path.abspath(r"D:\pycharm\Person-Practice\PPT\qa_images")
os.makedirs(output_dir, exist_ok=True)

powerpoint = win32com.client.Dispatch("PowerPoint.Application")
powerpoint.Visible = True

presentation = powerpoint.Presentations.Open(ppt_path, WithWindow=False)
slide_count = presentation.Slides.Count

for i in range(1, slide_count + 1):
    slide = presentation.Slides(i)
    img_path = os.path.join(output_dir, f"slide_{i:02d}.png")
    slide.Export(img_path, "PNG", 1280, 720)
    print(f"Exported slide {i}/{slide_count}: {img_path}")

presentation.Close()
powerpoint.Quit()
pythoncom.CoUninitialize()
print(f"\nDone! Exported {slide_count} slides to {output_dir}")
