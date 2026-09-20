import subprocess
import os
import sys


def convert_av1_to_h264(input_path, output_dir=None, crf=23, preset="medium", audio_bitrate="128k"):
    """
    将 AV1 编码的 MP4 转换为 H.264 编码的 MP4
    
    Args:
        input_path: 输入文件或目录路径
        output_dir: 输出目录（默认为输入文件同级目录下的 output_h264 文件夹）
        crf: 质量参数（18-28，数值越低质量越高）
        preset: 压缩预设（ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow）
        audio_bitrate: 音频比特率
    """
    
    # 1. 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"错误：找不到路径 {input_path}")
        return False
    
    # 2. 获取要处理的文件列表
    files_to_convert = []
    
    if os.path.isfile(input_path):
        # 单个文件
        if input_path.lower().endswith('.mp4'):
            files_to_convert.append(input_path)
        else:
            print(f"错误：{input_path} 不是 MP4 文件")
            return False
    elif os.path.isdir(input_path):
        # 目录：查找所有 MP4 文件
        for file in os.listdir(input_path):
            if file.lower().endswith('.mp4'):
                files_to_convert.append(os.path.join(input_path, file))
        if not files_to_convert:
            print(f"在目录 {input_path} 中未找到 MP4 文件")
            return False
    else:
        print(f"错误：{input_path} 既不是文件也不是目录")
        return False
    
    # 3. 设置输出目录
    if output_dir is None:
        if os.path.isfile(input_path):
            # 单个文件：输出到同级目录的 output_h264 文件夹
            output_dir = os.path.join(os.path.dirname(input_path), "output_h264")
        else:
            # 目录：输出到该目录下的 output_h264 文件夹
            output_dir = os.path.join(input_path, "output_h264")
    
    # 4. 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录: {output_dir}")
    
    # 5. 转换每个文件
    success_count = 0
    total_count = len(files_to_convert)
    
    for i, video_path in enumerate(files_to_convert, 1):
        file_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{file_name}_h264.mp4")
        
        print(f"\n[{i}/{total_count}] 正在转换: {os.path.basename(video_path)}")
        print(f"  输出到: {output_path}")
        
        # 构建 ffmpeg 命令
        command = [
            "ffmpeg",
            "-i", video_path,
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-y",  # 覆盖已存在的文件
            output_path
        ]
        
        try:
            # 执行转换
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                print(f"  ✓ 转换成功!")
                success_count += 1
            else:
                print(f"  ✗ 转换失败!")
                print(f"  错误信息: {result.stderr[:200]}...")  # 只显示前200个字符
                
        except FileNotFoundError:
            print("错误：系统找不到 ffmpeg 命令。请确保 ffmpeg 已正确安装并配置了环境变量。")
            return False
        except Exception as e:
            print(f"发生未知错误: {e}")
            return False
    
    # 6. 输出总结
    print(f"\n{'='*50}")
    print(f"转换完成！成功: {success_count}/{total_count}")
    print(f"输出目录: {output_dir}")
    
    return success_count == total_count


def main():
    """主函数：处理命令行参数或交互式输入"""
    
    print("="*60)
    print("  AV1 → H.264 视频格式转换工具")
    print("  解决 ComfyUI 等软件不支持 AV1 编码的问题")
    print("="*60)
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 交互式输入
        print("\n使用说明：")
        print("1. 输入单个 MP4 文件路径进行转换")
        print("2. 输入目录路径批量转换目录下所有 MP4 文件")
        print("3. 直接按回车使用默认路径（当前脚本所在目录）")
        
        input_path = input("\n请输入文件或目录路径: ").strip().strip('"')
        
        if not input_path:
            # 使用默认路径：脚本所在目录
            input_path = os.path.dirname(os.path.abspath(__file__))
            print(f"使用默认路径: {input_path}")
        
        # 询问输出目录
        output_dir = input("输出目录（留空使用默认）: ").strip().strip('"')
        if not output_dir:
            output_dir = None
    
    # 执行转换
    print(f"\n开始转换...")
    print(f"输入路径: {input_path}")
    
    success = convert_av1_to_h264(input_path, output_dir)
    
    if success:
        print("\n🎉 所有文件转换完成！现在可以在 ComfyUI 中使用这些文件了。")
    else:
        print("\n❌ 部分文件转换失败，请检查错误信息。")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()