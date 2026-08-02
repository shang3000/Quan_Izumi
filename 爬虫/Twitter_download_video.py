"""下载 Twitter/X 视频

支持的输入格式：
1. 直接视频 URL（video-s.twimg.com 链接）
2. Twitter/X 帖子 URL（twitter.com 或 x.com）
3. Sotwe 镜像 URL（sotwe.com）
4. cURL 命令（从 Chrome DevTools 复制）

使用方法：
1. 在浏览器中打开 Twitter/X 视频帖子
2. F12 打开开发者工具 → Network → 筛选 mp4 或 video
3. 找到视频请求，复制 URL 或 cURL 命令
4. 粘贴到下方 URL 输入框，运行脚本
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import os
import re
import time
import json
from urllib.parse import urlparse, unquote


def extract_filename_from_url(url):
    """从 URL 中提取文件名"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    # 去掉可能的编码字符
    filename = re.sub(r'%[0-9a-fA-F]{2}', '_', filename)
    if '.' not in filename:
        filename = f'twitter_video_{int(time.time())}.mp4'
    return filename


def extract_tweet_id(url):
    """从 Twitter/Sotwe URL 中提取推文 ID"""
    # twitter.com/username/status/1234567890
    # x.com/username/status/1234567890
    # sotwe.com/username/1234567890
    patterns = [
        r'(?:twitter\.com|x\.com)/\w+/status/(\d+)',
        r'sotwe\.com/\w+/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_direct_video_url(url):
    """判断是否是直接视频链接"""
    video_domains = [
        'video-s.twimg.com',
        'video.twimg.com',
        'pbs.twimg.com',
    ]
    parsed = urlparse(url)
    return parsed.hostname in video_domains if parsed.hostname else False


def fetch_video_from_page(url, headers):
    """从页面中提取视频 URL"""
    print(f'[INFO] 正在解析页面: {url[:80]}...')

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        html = resp.text

        # 尝试多种模式提取视频 URL
        patterns = [
            # video-s.twimg.com 模式
            r'https?://video-s\.twimg\.com/ext_tw_video/\d+/[^"\'<>\s]+\.mp4[^"\'<>\s]*',
            # 通用 mp4 链接
            r'https?://[^"\'<>\s]+\.mp4[^"\'<>\s]*',
            # 嵌入的视频 URL（JSON 格式）
            r'"video_url"\s*:\s*"(https?://[^"]+)"',
            # data-url 属性
            r'data-url="(https?://[^"]+\.mp4[^"]*)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                # 过滤出视频链接
                for match in matches:
                    match = match.replace('\\/', '/').replace('&amp;', '&')
                    if 'twimg.com' in match or '.mp4' in match:
                        print(f'[INFO] 找到视频链接')
                        return match

        # 尝试从 meta 标签提取
        og_video = re.search(r'<meta[^>]+property="og:video"[^>]+content="([^"]+)"', html)
        if og_video:
            return og_video.group(1).replace('\\/', '/').replace('&amp;', '&')

        print('[WARN] 未在页面中找到视频链接')
        print('[HINT] 请尝试直接复制 Network 面板中的视频 URL')
        return None

    except requests.exceptions.RequestException as e:
        print(f'[ERROR] 页面请求失败: {e}')
        return None


def download_video(url, save_dir=None, filename=None, referer=None):
    """下载视频文件

    Args:
        url: 视频 URL
        save_dir: 保存目录，默认保存到项目根目录的 downloads/
        filename: 自定义文件名，不传则自动提取
        referer: Referer 头部
    """
    if not filename:
        filename = extract_filename_from_url(url)

    # 统一保存到项目根目录的 downloads/
    if save_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.join(project_root, 'downloads')

    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    print(f'[INFO] 开始下载: {filename}')
    print(f'[INFO] 保存到: {save_path}')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Ranges': 'bytes',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    if referer:
        headers['Referer'] = referer
    else:
        # 根据视频域名设置合适的 Referer
        parsed = urlparse(url)
        if 'twimg.com' in (parsed.hostname or ''):
            headers['Referer'] = 'https://twitter.com/'
        else:
            headers['Referer'] = f'{parsed.scheme}://{parsed.hostname}/'

    try:
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
                        bar_len = 30
                        filled = int(bar_len * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_len - filled)
                        print(f'\r[INFO] |{bar}| {pct:.1f}% ({downloaded:,}/{total_size:,} bytes)', end='')
                    else:
                        print(f'\r[INFO] 已下载: {downloaded:,} bytes', end='')

        file_size_mb = downloaded / (1024 * 1024)
        print(f'\n[DONE] 下载完成: {save_path} ({file_size_mb:.2f} MB)')
        return save_path

    except requests.exceptions.RequestException as e:
        print(f'\n[ERROR] 下载失败: {e}')
        if os.path.exists(save_path):
            os.remove(save_path)
        return None


def download_from_curl(curl_cmd, save_dir=None):
    """从 cURL 命令中提取 URL、Headers 并下载

    支持 Chrome DevTools Copy as cURL (bash) 格式
    """
    # 提取 URL
    url_match = re.search(r"['\"]?(https?://[^'\"]+)['\"]?", curl_cmd)
    if not url_match:
        print('[ERROR] 无法从 cURL 命令中提取 URL')
        return None
    url = url_match.group(1)
    print(f'[INFO] 提取到 URL: {url[:80]}...')

    # 提取所有 -H 头部
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }
    header_matches = re.findall(r"""-H\s+['"]([^'"]+)['"]""", curl_cmd)
    for h in header_matches:
        if ':' in h:
            key, value = h.split(':', 1)
            headers[key.strip()] = value.strip()

    # 提取 Cookie（-b 参数）
    cookie_match = re.search(r"""-b\s+['"]([^'"]+)['"]""", curl_cmd)
    if cookie_match:
        headers['Cookie'] = cookie_match.group(1)

    # 统一保存目录
    if save_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.join(project_root, 'downloads')
    os.makedirs(save_dir, exist_ok=True)

    # 从 URL 提取文件名
    filename = extract_filename_from_url(url)
    save_path = os.path.join(save_dir, filename)

    print(f'[INFO] 开始下载: {filename}')
    print(f'[INFO] 保存到: {save_path}')
    print(f'[INFO] 使用 {len(headers)} 个请求头')

    try:
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
                        bar_len = 30
                        filled = int(bar_len * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_len - filled)
                        print(f'\r[INFO] |{bar}| {pct:.1f}% ({downloaded:,}/{total_size:,} bytes)', end='')
                    else:
                        print(f'\r[INFO] 已下载: {downloaded:,} bytes', end='')

        file_size_mb = downloaded / (1024 * 1024)
        print(f'\n[DONE] 下载完成: {save_path} ({file_size_mb:.2f} MB)')
        return save_path

    except requests.exceptions.RequestException as e:
        print(f'\n[ERROR] 下载失败: {e}')
        if os.path.exists(save_path):
            os.remove(save_path)
        return None


def batch_download(urls, save_dir=None):
    """批量下载多个视频"""
    results = []
    for i, url in enumerate(urls, 1):
        print(f'\n===== [{i}/{len(urls)}] =====')
        result = download_url(url, save_dir=save_dir)
        results.append(result)
    return results


def download_url(url_or_curl, save_dir=None, filename=None):
    """智能下载入口 - 自动判断输入类型

    Args:
        url_or_curl: URL、cURL 命令或页面链接
        save_dir: 保存目录
        filename: 自定义文件名
    """
    url_or_curl = url_or_curl.strip()

    # 判断是否是 cURL 命令
    if url_or_curl.startswith('curl '):
        return download_from_curl(url_or_curl, save_dir=save_dir)

    # 判断是否是直接视频链接
    if is_direct_video_url(url_or_curl):
        return download_video(url_or_curl, save_dir=save_dir, filename=filename)

    # 判断是否是 Twitter/X/Sotwe 页面链接
    tweet_id = extract_tweet_id(url_or_curl)
    if tweet_id:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }
        video_url = fetch_video_from_page(url_or_curl, headers)
        if video_url:
            if not filename:
                filename = f'twitter_{tweet_id}.mp4'
            return download_video(video_url, save_dir=save_dir, filename=filename,
                                 referer=url_or_curl)
        else:
            print('[HINT] 无法从页面提取视频，请直接使用视频 URL 或 cURL 命令')
            return None

    # 尝试当作直接链接下载
    print('[INFO] 未识别的 URL 格式，尝试直接下载...')
    return download_video(url_or_curl, save_dir=save_dir, filename=filename)


if __name__ == '__main__':
    print('=' * 60)
    print('Twitter/X 视频下载器')
    print('=' * 60)
    print()
    print('支持的输入格式：')
    print('  1. 直接视频 URL（video-s.twimg.com）')
    print('  2. Twitter/X 帖子（twitter.com/.../status/ID）')
    print('  3. Sotwe 镜像（sotwe.com/.../ID）')
    print('  4. cURL 命令（从 DevTools 复制）')
    print()
    print('直接回车可退出程序')
    print()

    while True:
        print('-' * 60)
        url = input('请粘贴 URL 或 cURL 命令: ').strip()

        if not url:
            print('[INFO] 已退出')
            break

        print()
        download_url(url)
        print()
