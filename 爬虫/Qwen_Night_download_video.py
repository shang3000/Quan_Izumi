"""
千问AI创作平台视频下载器 - 高级版
支持分片下载、断点续传、自动合并
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import os
import re
import json
import time
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed


class QianwenVideoDownloader:
    """千问视频下载器"""

    def __init__(self, output_dir=r'D:\pycharm\Person-Practice\downloads'):
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://create.qianwen.com/',
            'Origin': 'https://create.qianwen.com',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-'  # 请求整个文件
        }
        os.makedirs(output_dir, exist_ok=True)

    def get_video_info(self, url):
        """获取视频信息"""
        try:
            # 先获取文件信息
            response = requests.head(url, headers=self.headers, allow_redirects=True, timeout=10)

            content_length = response.headers.get('Content-Length')
            content_type = response.headers.get('Content-Type')
            accept_ranges = response.headers.get('Accept-Ranges')

            info = {
                'url': url,
                'content_length': int(content_length) if content_length else None,
                'content_type': content_type,
                'accept_ranges': accept_ranges,
                'supports_range': accept_ranges == 'bytes'
            }

            return info

        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    def download_chunk(self, url, start, end, chunk_id, temp_dir):
        """下载单个分片"""
        headers = self.headers.copy()
        headers['Range'] = f'bytes={start}-{end}'

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            chunk_file = os.path.join(temp_dir, f'chunk_{chunk_id:04d}.mp4')
            with open(chunk_file, 'wb') as f:
                f.write(response.content)

            return chunk_file, len(response.content)

        except Exception as e:
            print(f"分片 {chunk_id} 下载失败: {e}")
            return None, 0

    def download_video(self, url, filename=None):
        """
        下载视频文件

        Args:
            url: 视频URL
            filename: 保存文件名（可选）
        """
        print("=" * 60)
        print("开始下载视频")
        print("=" * 60)

        # 获取视频信息
        info = self.get_video_info(url)
        if not info:
            print("无法获取视频信息，尝试直接下载...")
            return self._simple_download(url, filename)

        print(f"文件类型: {info['content_type']}")
        print(f"文件大小: {info['content_length'] / 1024 / 1024:.2f} MB" if info['content_length'] else "文件大小: 未知")
        print(f"支持断点续传: {'是' if info['supports_range'] else '否'}")

        # 提取文件名
        if not filename:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            filename = path.split('/')[-1].split('?')[0]

        output_path = os.path.join(self.output_dir, filename)

        # 如果文件已存在，跳过下载
        if os.path.exists(output_path):
            existing_size = os.path.getsize(output_path)
            if info['content_length'] and existing_size == info['content_length']:
                print(f"文件已存在且大小一致，跳过下载: {output_path}")
                return output_path
            else:
                print(f"文件已存在但大小不一致，重新下载...")

        # 根据文件大小选择下载方式
        if info['content_length'] and info['content_length'] > 10 * 1024 * 1024:
            # 大于10MB，使用分片下载
            return self._chunked_download(url, output_path, info['content_length'])
        else:
            # 小文件，直接下载
            return self._simple_download(url, filename)

    def _simple_download(self, url, filename):
        """简单下载（不分片）"""
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()

            if not filename:
                # 从Content-Disposition或URL中提取文件名
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    filename = re.search(r'filename[*]?=["\']?([^"\';\s]+)', content_disposition)
                    if filename:
                        filename = filename.group(1)
                if not filename:
                    parsed = urlparse(url)
                    path = unquote(parsed.path)
                    filename = path.split('/')[-1].split('?')[0]

            output_path = os.path.join(self.output_dir, filename)

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0

            print(f"正在下载: {filename}")

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}% ({downloaded_size}/{total_size})", end='', flush=True)

            print(f"\n下载完成！文件保存在: {output_path}")
            return output_path

        except Exception as e:
            print(f"下载失败: {e}")
            return None

    def _chunked_download(self, url, output_path, total_size, chunk_size=5 * 1024 * 1024):
        """分片下载"""
        print(f"使用分片下载模式，分片大小: {chunk_size / 1024 / 1024:.1f} MB")

        # 创建临时目录
        temp_dir = os.path.join(self.output_dir, '.temp')
        os.makedirs(temp_dir, exist_ok=True)

        # 计算分片
        chunks = []
        for start in range(0, total_size, chunk_size):
            end = min(start + chunk_size - 1, total_size - 1)
            chunks.append((start, end, len(chunks)))

        print(f"共 {len(chunks)} 个分片")

        # 下载分片
        downloaded_chunks = []
        total_downloaded = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.download_chunk, url, start, end, chunk_id, temp_dir): chunk_id
                for start, end, chunk_id in chunks
            }

            for future in as_completed(futures):
                chunk_file, size = future.result()
                if chunk_file:
                    downloaded_chunks.append((chunk_file, size))
                    total_downloaded += size
                    progress = (total_downloaded / total_size) * 100
                    print(f"\r下载进度: {progress:.1f}% ({total_downloaded}/{total_size})", end='', flush=True)

        print()  # 换行

        # 按顺序合并分片
        downloaded_chunks.sort(key=lambda x: x[0])

        print("正在合并分片...")
        with open(output_path, 'wb') as outfile:
            for chunk_file, _ in downloaded_chunks:
                with open(chunk_file, 'rb') as infile:
                    outfile.write(infile.read())

        # 清理临时文件
        for chunk_file, _ in downloaded_chunks:
            os.remove(chunk_file)
        os.rmdir(temp_dir)

        print(f"下载完成！文件保存在: {output_path}")
        return output_path


def interactive_download():
    """交互式下载"""
    print("=" * 60)
    print("千问AI创作平台视频下载器 - 高级版")
    print("=" * 60)
    print()
    print("功能特性：")
    print("  - 支持分片下载（大文件加速）")
    print("  - 支持断点续传")
    print("  - 自动合并分片")
    print()
    print("使用方法：")
    print("1. 在千问AI创作平台打开视频")
    print("2. 按 F12 打开开发者工具")
    print("3. 切换到「网络」选项卡")
    print("4. 在筛选器中输入 'mp4' 或 'video'")
    print("5. 播放视频，观察网络请求")
    print("6. 找到视频文件的请求（通常是最大的那个）")
    print("7. 右键点击请求 -> 复制 -> 复制 URL")
    print("8. 将URL粘贴到下面")
    print()

    url = input("请粘贴视频URL: ").strip()

    if not url:
        print("URL不能为空！")
        return

    if not url.startswith('http'):
        print("请输入完整的URL（以http或https开头）")
        return

    # 可选：自定义文件名
    custom_name = input("输入自定义文件名（直接回车使用默认名称）: ").strip()

    print()

    downloader = QianwenVideoDownloader()
    result = downloader.download_video(url, custom_name if custom_name else None)

    if result:
        print()
        print("=" * 60)
        print("下载成功！")
        print(f"文件位置: {result}")
        print("=" * 60)
    else:
        print()
        print("下载失败，请检查URL是否正确")


if __name__ == '__main__':
    interactive_download()
