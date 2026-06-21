"""下载千问空间中的视频文件

使用方法：
1. 打开千问空间，播放视频
2. F12 打开开发者工具 → 网络 → 筛选 video/mp4 或 zip
3. 找到 mp4 请求，右键 → 复制 cURL
4. 粘贴到下面的 curl_cmd 变量，或者直接用 video_url 变量

注意：URL 是临时签名链接，会过期，拿到后尽快下载
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import os
import time
from urllib.parse import urlparse, parse_qs


def extract_filename_from_url(url):
    """从 URL 中提取文件名"""
    parsed = urlparse(url)
    # 去掉查询参数，取路径最后一段
    path = parsed.path
    filename = os.path.basename(path)
    # 如果文件名太长或没有扩展名，自动生成
    if '.' not in filename:
        filename = f'qianwen_video_{int(time.time())}.mp4'
    return filename


def download_video(url, save_dir=None, filename=None):
    """下载视频文件

    Args:
        url: 视频 URL
        save_dir: 保存目录
        filename: 自定义文件名，不传则自动提取
    """
    if not filename:
        filename = extract_filename_from_url(url)

    # 统一保存到项目根目录的 downloads/，不受工作目录影响
    if save_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.join(project_root, 'downloads')

    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    print(f'[INFO] 开始下载: {filename}')
    print(f'[INFO] 保存到: {save_path}')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.qianwen.com/',
        'Origin': 'https://www.qianwen.com',
    }

    try:
        # stream=True 懒加载，大文件不会一次性读入内存
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()

        total_size = int(resp.headers.get('Content-Length', 0))
        downloaded = 0

        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        print(f'\r[INFO] 下载进度: {pct:.1f}% ({downloaded}/{total_size} bytes)', end='')
                    else:
                        print(f'\r[INFO] 已下载: {downloaded} bytes', end='')

        print(f'\n[DONE] 下载完成: {save_path} ({downloaded} bytes)')
        return save_path

    except requests.exceptions.RequestException as e:
        print(f'\n[ERROR] 下载失败: {e}')
        return None


def download_from_curl(curl_cmd):
    """从 cURL 命令中提取 URL 并下载

    在 Chrome DevTools 中右键请求 → Copy → Copy as cURL
    粘贴到这里即可
    """
    import re
    # 提取 URL（单引号或双引号包裹的 http/https 链接）
    match = re.search(r"['\"]?(https?://[^'\"]+)['\"]?", curl_cmd)
    if match:
        url = match.group(1)
        print(f'[INFO] 提取到 URL: {url[:80]}...')
        return download_video(url)
    else:
        print('[ERROR] 无法从 cURL 命令中提取 URL')
        return None


def batch_download(urls, save_dir=None):
    """批量下载多个视频"""
    results = []
    for i, url in enumerate(urls, 1):
        print(f'\n===== [{i}/{len(urls)}] =====')
        result = download_video(url, save_dir=save_dir)
        results.append(result)
    return results


if __name__ == '__main__':
    # ============================================================
    # 方式一：直接粘贴视频 URL（从开发者工具 Network 面板获取）
    # ============================================================
    video_url = (
        'https://ai-studio-resource.cn-zhangjiakou.oss.aliyuncs.com/d/qwen/58c1c97f23d3741be390415339c4c7d6/1777359438548-e20bc49baa3f4fa1b3976371cf844230.mp4?Expires=1783344356&OSSAccessKeyId=LTAI5tB1ULAmj55yDBf6XJ9T&Signature=kVRErUIfANYpL7vDflttlQQqukA%3D'
    )

    download_video(video_url)

    # ============================================================
    # 方式二：粘贴 cURL 命令（Chrome DevTools → Copy as cURL）
    # ============================================================
    # curl_cmd = """curl 'https://ai-studio-resource...' -H '...' """
    # download_from_curl(curl_cmd)

    # ============================================================
    # 方式三：批量下载（多个视频 URL）
    # ============================================================
    # urls = [
    #     'https://...',
    #     'https://...',
    # ]
    # batch_download(urls)
