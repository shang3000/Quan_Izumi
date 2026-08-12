import subprocess
import os


def extract_audio_ffmpeg(video_path, output_dir, bitrate="192k"):
    """
    使用 ffmpeg 从 MP4 中提取音频并保存为 MP3
    """
    # 1. 检查输入文件是否存在
    if not os.path.exists(video_path):
        print(f"错误：找不到文件 {video_path}")
        return

    # 2. 如果输出目录不存在，则自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"输出目录不存在，已自动创建: {output_dir}")

    # 3. 获取原文件名，并拼接输出路径
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{file_name}.mp3")

    # 4. 构建 ffmpeg 命令
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", bitrate,
        "-y",
        output_path
    ]

    # 5. 执行命令
    try:
        print(f"正在提取音频: {video_path} ...")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"成功！音频已保存至: {output_path}")
        else:
            print("转换失败，ffmpeg 报错信息如下：")
            print(result.stderr.decode('utf-8'))

    except FileNotFoundError:
        print("错误：系统找不到 ffmpeg 命令。请确保 ffmpeg 已正确安装并配置了环境变量。")
    except Exception as e:
        print(f"发生未知错误: {e}")


# --- 运行入口 ---
if __name__ == "__main__":
    # 固定的输出目录
    OUTPUT_DIR = r"D:\pycharm\Person-Practice\格式工厂\output"

    # 运行时输入 MP4 文件路径
    mp4_file = input("请输入 MP4 文件的完整路径: ").strip().strip('"')

    # 调用提取函数
    extract_audio_ffmpeg(mp4_file, OUTPUT_DIR)