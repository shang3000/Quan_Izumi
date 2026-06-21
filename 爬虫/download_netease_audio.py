"""下载网易云音乐音频文件

使用方法：
1. 打开网易云音乐网页版，播放歌曲
2. F12 打开开发者工具 → 网络 → 筛选 m4a / mp3 / application/octet-stream
3. 找到音频请求，右键 → 复制 URL 或 cURL
4. 粘贴到下面的 audio_url 变量，运行脚本

注意：网易云的音频 URL 是临时签名链接，会过期，拿到后尽快下载
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import os
import time
import re
from urllib.parse import urlparse


def extract_filename_from_url(url):
    """从 URL 中提取文件名"""
    parsed = urlparse(url)
    path = parsed.path
    filename = os.path.basename(path)
    # 去掉可能的编码字符
    filename = re.sub(r'%[0-9a-fA-F]{2}', '_', filename)
    if '.' not in filename:
        filename = f'netease_audio_{int(time.time())}.m4a'
    return filename


def download_audio(url, save_dir=None, filename=None):
    """下载音频文件

    Args:
        url: 音频 URL（从网易云 Network 面板获取）
        save_dir: 保存目录，不传则保存到项目根目录的 downloads/
        filename: 自定义文件名，不传则自动提取
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
        'Referer': 'https://music.163.com/',
        'Origin': 'https://music.163.com',
    }

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
                        print(f'\r[INFO] 下载进度: {pct:.1f}% ({downloaded}/{total_size} bytes)', end='')
                    else:
                        print(f'\r[INFO] 已下载: {downloaded} bytes', end='')

        print(f'\n[DONE] 下载完成: {save_path} ({downloaded:,} bytes)')
        return save_path

    except requests.exceptions.RequestException as e:
        print(f'\n[ERROR] 下载失败: {e}')
        return None


def download_from_curl(curl_cmd, save_dir=None):
    """从 cURL 命令中提取 URL、Headers、Cookie 并下载

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
                        print(f'\r[INFO] 下载进度: {pct:.1f}% ({downloaded}/{total_size} bytes)', end='')
                    else:
                        print(f'\r[INFO] 已下载: {downloaded} bytes', end='')

        print(f'\n[DONE] 下载完成: {save_path} ({downloaded:,} bytes)')
        return save_path

    except requests.exceptions.RequestException as e:
        print(f'\n[ERROR] 下载失败: {e}')
        return None


def batch_download(urls, save_dir=None):
    """批量下载多个音频"""
    results = []
    for i, url in enumerate(urls, 1):
        print(f'\n===== [{i}/{len(urls)}] =====')
        result = download_audio(url, save_dir=save_dir)
        results.append(result)
    return results


if __name__ == '__main__':
    # ============================================================
    # 方式一：粘贴 cURL 命令（推荐，包含完整 Cookie 和 Headers）
    # Chrome DevTools → 右键请求 → Copy → Copy as cURL (bash)
    # ============================================================
    curl_cmd = """curl 'https://m704.music.126.net/20260621222836/bba748bcef272b88262e52d971299980/jdyyaac/obj/w5rDlsOJwrLDjj7CmsOj/45265666803/8070/3927/8a0c/878582d5901763c1bbd62863d2d2511f.m4a?vuutv=3kx3TJH/r/V5nWczfpT/BBT3kCJlLnwT9LeeR5wniqA3ocpVlnbUIlQKaEd2X5RiT1Lors7B5/FxMfUElr9VNjYFYRoDmDyWPNFmxpg9adg=&authSecret=0000019eea7e748809e00a32ca3e0006&cdntag=bWFyaz1vc193ZWIscXVhbGl0eV9leGhpZ2g' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6' \
  -H 'Connection: keep-alive' \
  -H 'Range: bytes=0-' \
  -H 'Referer: https://music.163.com/' \
  -H 'Sec-Fetch-Dest: audio' \
  -H 'Sec-Fetch-Mode: no-cors' \
  -H 'Sec-Fetch-Site: cross-site' \
  -H 'Sec-Fetch-Storage-Access: active' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0' \
  -H 'sec-ch-ua: "Microsoft Edge";v="149", "Chromium";v="149", "Not)A;Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"'"""

    if curl_cmd:
        download_from_curl(curl_cmd)
    else:
        # ============================================================
        # 方式二：直接粘贴音频 URL（临时链接，可能过期）
        # ============================================================
        audio_url = (
            'https://m804.music.126.net/20260621222151/e5d23a6fd7e9a61eb975b45920ea51a7/'
            'jdyyaac/obj/w5rDlsOJwrLDjj7CmsOj/4525666803/8070/3927/8a0c/'
            '878582d5901763c1bbd62863d2d2511f.m4a'
            '?uwtv=Akmk60zGyLwZEF9sL1MLuEuSK5fJI1TLi7DhRSf9BXYSRy29FFvkaV7UjPxfVqrXB1b9'
            '+1CtQttXSnWLkIYbNfCDRVUcUCLLqmkVrmyE0uk='
            '&authSecret=0000019eea7847ca15f20a3b236b160d'
            '&cdnTag=bWFyaz1vc193ZWIsc1VhbGI0eV9leGhpZ2g'
        )
        download_audio(audio_url)
