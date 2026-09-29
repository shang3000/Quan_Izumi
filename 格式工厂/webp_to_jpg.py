import os

from PIL import Image


def webp_to_jpg(src_path, output_dir, quality=95):
    """
    使用 Pillow 将 WebP 图片转换为 JPG
    支持：单个 .webp 文件，或包含多个 .webp 的文件夹（批量）
    注意：JPG 不支持透明通道，透明部分会自动填充为白色
    """
    # 1. 检查输入是否存在
    if not os.path.exists(src_path):
        print(f"错误：找不到路径 {src_path}")
        return

    # 2. 收集所有待转换的 .webp 文件
    if os.path.isdir(src_path):
        webp_files = [
            os.path.join(src_path, f) for f in os.listdir(src_path)
            if f.lower().endswith(".webp")
        ]
        if not webp_files:
            print(f"错误：文件夹 {src_path} 里没有找到 .webp 文件")
            return
        print(f"共找到 {len(webp_files)} 个 .webp 文件，开始批量转换…")
    elif src_path.lower().endswith(".webp"):
        webp_files = [src_path]
    else:
        print("错误：请输入 .webp 文件或包含 .webp 的文件夹路径")
        return

    # 3. 输出目录自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"输出目录不存在，已自动创建: {output_dir}")

    # 4. 逐张转换
    ok, fail = 0, 0
    for src in webp_files:
        file_name = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(output_dir, f"{file_name}.jpg")
        try:
            print(f"正在转换: {os.path.basename(src)} ...")
            img = Image.open(src)

            # JPG 不支持透明：透明背景铺白底
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")

            img.save(dst, "JPEG", quality=quality)
            print(f"成功！已保存至: {dst}")
            ok += 1
        except Exception as e:
            print(f"转换失败（{os.path.basename(src)}）: {e}")
            fail += 1

    print(f"\n完成！成功 {ok} 张，失败 {fail} 张（输出目录：{output_dir}）")


# --- 运行入口 ---
if __name__ == "__main__":
    # 固定的输出目录
    OUTPUT_DIR = r"D:\pycharm\Person-Practice\格式工厂\output"

    # 运行时输入 WebP 文件路径（或整个文件夹路径 → 批量转换）
    src = input("请输入 WebP 文件 / 文件夹的完整路径: ").strip().strip('"')

    webp_to_jpg(src, OUTPUT_DIR)

    input("\n按回车键退出…")
