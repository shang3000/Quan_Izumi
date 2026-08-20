"""
mhxiaoshen 漫画图片下载器（mhxiaoshen.vip 专用）

⚠️ 独立程序，与原 manhua_download.py 互不干扰。

为什么单独写：
- 该站点图片列表直接内嵌在章节页 HTML 的 data-src 属性中（无需探测）
- 图片 CDN (cdn.mmba.stream 等) 有严格 Referer 防盗链，不带 Referer 直接 403
- 图片 URL 为 /files/分类/漫画/角色/章节/编号.webp 结构，目录级编号，无规律可枚举

支持的输入格式：
1. 章节页面 URL（推荐）
   例如：https://mhxiaoshen.vip/小巳-南宫仙儿-16.html
   程序会自动从页面 data-src 提取完整图片列表
2. 单张图片 URL（自动反推同章节其他图片）
   例如：https://cdn.mmba.stream/files/AI国漫/神墓/南宫仙儿/016/001.webp
3. cURL 命令（从 Chrome DevTools 复制）

使用方法：
1. 打开漫画章节页面，复制页面 URL
2. 粘贴到下方输入框，回车开始下载
3. 图片保存到 downloads_mhxiaoshen/ 目录下的子文件夹中

特点：
- 自动检测系统代理（127.0.0.1:7897）
- 自动带正确 Referer（从输入的页面 URL 提取）
- 从 data-src / src / JSON 多策略提取图片
- 多线程并发下载 + 失败自动重试 + 断点续传
- 文件名保留原始编号（001.webp）
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import time
import json
import random
import urllib.request
import urllib.error
from urllib.parse import urlparse, urljoin, urlunparse, unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# ============ 配置区 ============

SITE_DOMAINS = ['mhxiaoshen.vip']                     # 站点域名（用于生成 Referer）
CDN_DOMAINS = [                                       # 图片 CDN 域名（按优先级）
    'cdn.mmba.stream',
    'cdn.nmbxa.stream',
    'cdn.mnba.stream',
    'mmba.stream',
    'nmbxa.stream',
    'mnba.stream',
]
DEFAULT_REFERER = 'https://mhxiaoshen.vip/'           # 默认 Referer
DEFAULT_PROXY = 'http://127.0.0.1:7897'               # Clash 默认代理
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
PROBE_DELAY = 0.3                                      # 顺序探测时每次请求间隔（秒）
PROBE_TIMEOUT = 15                                     # 顺序探测超时时间（秒）
PROBE_MAX_RETRIES = 2                                  # 探测失败时重试次数
MAX_WORKERS = 4                                        # 并发下载数
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
)
IMAGE_EXTS = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.avif'}

# 页面中可能存放图片列表的 JSON 字段名
IMAGE_ARRAY_KEYS = [
    'images', 'imageList', 'image_list', 'pages', 'files', 'pics', 'picture',
    'chapterImages', 'chapter_images', 'data', 'imageData', 'chapter', 'photos',
]


# ============ 工具函数 ============

def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))


def get_default_download_dir():
    """独立下载目录，与原程序 downloads/ 互不干扰"""
    return os.path.join(get_project_root(), 'downloads_mhxiaoshen')


def detect_proxy():
    """检测系统代理是否可用"""
    for port in [7897, 7890, 10808, 10809, 8080]:
        proxy_url = f'http://127.0.0.1:{port}'
        try:
            parsed = urlparse(proxy_url)
            import socket
            with socket.create_connection((parsed.hostname, parsed.port), timeout=1):
                return proxy_url
        except Exception:
            continue
    return None


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    if not name:
        return 'untitled'
    name = unquote(name).strip()
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('._')
    return name or 'untitled'


def is_image_url(url):
    """判断 URL 是否是图片链接"""
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    return ext in IMAGE_EXTS


def is_cdn_url(url):
    """判断是否是本站 CDN 图片链接"""
    url_lower = url.lower()
    return any(d in url_lower for d in CDN_DOMAINS)


def build_headers(referer=None):
    """构建页面请求头"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    if referer:
        headers['Referer'] = referer
    return headers


def build_image_headers(referer):
    """构建图片请求头（必须带 Referer，否则 403）"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': referer or DEFAULT_REFERER,
    }
    return headers


def extract_referer_from_url(url):
    """从输入 URL 自动提取站内 Referer"""
    parsed = urlparse(url)
    if parsed.netloc and any(d in parsed.netloc for d in SITE_DOMAINS):
        return f'{parsed.scheme}://{parsed.netloc}/'
    return DEFAULT_REFERER


def http_get(url, headers=None, proxies=None, timeout=DEFAULT_TIMEOUT, stream=False):
    """统一的 HTTP GET 请求"""
    if HAS_REQUESTS:
        session = requests.Session()
        if headers:
            session.headers.update(headers)
        resp = session.get(url, proxies=proxies, timeout=timeout, stream=stream)
        resp.raise_for_status()
        return resp
    else:
        req_headers = dict(headers) if headers else {}
        if req_headers.get('Accept-Encoding', '').startswith('gzip'):
            req_headers['Accept-Encoding'] = 'identity'
        req = urllib.request.Request(url, headers=req_headers)
        if proxies:
            handler = urllib.request.ProxyHandler({'http': proxies, 'https': proxies})
            opener = urllib.request.build_opener(handler)
        else:
            opener = urllib.request.build_opener()
        resp = opener.open(req, timeout=timeout)
        if stream:
            return resp
        return resp.read()


def normalize_url(base_url, url):
    """将相对 URL 转为绝对 URL"""
    if not url:
        return None
    url = url.strip()
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return urljoin(base_url, url)


def encode_url(url):
    """将 URL 中的非 ASCII 字符（如中文路径）编码为百分号形式

    站点图片 URL 含原始中文（如 /files/AI国漫/神墓/南宫仙儿/...），
    直接请求会触发 ascii 编码错误。先 unquote 再 quote 做规范化。
    """
    if not url:
        return url
    try:
        parsed = urlparse(url)
        path = quote(unquote(parsed.path), safe="/%:@&=+$,;~*'()!")
        query = quote(unquote(parsed.query), safe="=?&%")
        return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, query, parsed.fragment))
    except Exception:
        return url


def extract_title_from_html(html, url=None):
    """从 HTML 中提取标题"""
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
        title = re.sub(r'[-_|\s]*漫画小生.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'[-_|\s]*免费.*$', '', title)
        if title:
            return title
    if url:
        parsed = urlparse(url)
        path = unquote(os.path.basename(parsed.path))
        name = os.path.splitext(path)[0]
        if name:
            return name
    return None


# ============ 图片提取 ============

def extract_images_with_bs4(html, base_url):
    """使用 BeautifulSoup 提取图片 URL（优先 data-src 懒加载属性）"""
    images = []
    if not HAS_BS4:
        return images
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(['img', 'amp-img', 'picture', 'source']):
        for attr in ['data-src', 'data-original', 'src', 'data-url']:
            url = tag.get(attr)
            if url:
                url = normalize_url(base_url, url)
                if url and is_image_url(url):
                    images.append(url)
                break
    return images


def extract_images_with_regex(html, base_url):
    """使用正则提取图片 URL"""
    images = []
    pattern = re.compile(
        r'https?://[^\s"\'<>]+\.(?:webp|jpg|jpeg|png|gif|bmp|avif)(?:\?[^\s"\'<>]*)?',
        re.IGNORECASE
    )
    for url in pattern.findall(html):
        url = normalize_url(base_url, url)
        if url:
            images.append(url)
    return images


def extract_json_image_arrays(html, base_url):
    """从页面脚本中的 JSON 数组提取图片 URL"""
    images = []

    # 模式1: var xxx = [...]
    array_pattern = re.compile(
        r'(?:var|let|const|window\.)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(\[[^\]]*\])',
        re.DOTALL
    )
    for match in array_pattern.finditer(html):
        var_name, array_str = match.group(1), match.group(2)
        if any(key.lower() in var_name.lower() for key in IMAGE_ARRAY_KEYS):
            try:
                data = json.loads(array_str)
                images.extend(_flatten_image_list(data, base_url))
            except json.JSONDecodeError:
                pass

    # 模式2: 对象中的 images 等字段
    obj_pattern = re.compile(
        r'"(' + '|'.join(IMAGE_ARRAY_KEYS) + r')"\s*:\s*(\[[^\]]*\])',
        re.IGNORECASE | re.DOTALL
    )
    for match in obj_pattern.finditer(html):
        try:
            data = json.loads(match.group(2))
            images.extend(_flatten_image_list(data, base_url))
        except json.JSONDecodeError:
            pass

    return images


def _flatten_image_list(data, base_url):
    """将嵌套数据结构展平为图片 URL 列表"""
    images = []
    if isinstance(data, list):
        for item in data:
            images.extend(_flatten_image_list(item, base_url))
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith('http') and is_image_url(value):
                url = normalize_url(base_url, value)
                if url:
                    images.append(url)
            else:
                images.extend(_flatten_image_list(value, base_url))
    elif isinstance(data, str) and data.startswith('http') and is_image_url(data):
        url = normalize_url(base_url, data)
        if url:
            images.append(url)
    return images


def extract_images_from_page(url, html):
    """从页面 HTML 中提取所有图片 URL（多策略）"""
    all_images = []

    # 策略1: BeautifulSoup（data-src 优先）
    all_images.extend(extract_images_with_bs4(html, url))

    # 策略2: 正则
    all_images.extend(extract_images_with_regex(html, url))

    # 策略3: JSON 数组
    all_images.extend(extract_json_image_arrays(html, url))

    # 去重并保持顺序
    seen = set()
    unique_images = []
    for img in all_images:
        if img and img not in seen:
            seen.add(img)
            unique_images.append(img)

    # 优先保留本站 CDN 图片，过滤掉站点封面/图标/广告图
    cdn_images = [img for img in unique_images if is_cdn_url(img)]
    if cdn_images:
        return cdn_images

    # 兜底：返回所有图片
    return [img for img in unique_images if is_image_url(img)]


def infer_image_sequence(image_url):
    """
    从单张图片 URL 反推同章节其他图片（本站 /files/分类/漫画/角色/章节/编号.webp 结构）

    章节页的图片全部集中在同一目录：/016/001.webp -> /016/002.webp -> ...
    只探测当前章节目录，避免误伤其他章节。
    """
    parsed = urlparse(image_url)
    path = unquote(parsed.path)
    parts = [p for p in path.split('/') if p]

    # 需要至少 /files/xx/xx/xx/章节/编号.ext
    if len(parts) < 2:
        return []

    base = parts[-1]            # 001.webp
    match = re.search(r'^(\d+)(\.\w+)$', base)
    if not match:
        return []

    ext = match.group(2)
    num_len = len(match.group(1))      # 001 -> 3, 1 -> 1
    base_url = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts[:-1])}/"

    candidates = []
    max_num = 10 ** num_len
    for i in range(1, max_num):
        candidates.append(f"{base_url}{i:0{num_len}d}{ext}")
    return candidates


# ============ 下载 ============

def download_image(url, save_path, headers, proxies, retries=MAX_RETRIES):
    """下载单张图片（带内容校验）"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    url = encode_url(url)  # 中文路径 -> 百分号编码

    for attempt in range(retries):
        try:
            if HAS_REQUESTS:
                resp = requests.get(url, headers=headers, proxies=proxies,
                                    timeout=DEFAULT_TIMEOUT, stream=True)
                resp.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                req = urllib.request.Request(url, headers=headers)
                if proxies:
                    handler = urllib.request.ProxyHandler({'http': proxies, 'https': proxies})
                    opener = urllib.request.build_opener(handler)
                else:
                    opener = urllib.request.build_opener()
                with opener.open(req, timeout=DEFAULT_TIMEOUT) as resp:
                    with open(save_path, 'wb') as f:
                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            file_size = os.path.getsize(save_path)
            # 内容校验：防 403 页面/占位图伪装成功
            if file_size < 100:
                os.remove(save_path)
                raise ValueError('下载内容过小，疑似非图片')
            return True, file_size
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
            # 清理残留
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception:
                    pass
            return False, str(e)
    return False, 'unknown error'


def download_with_progress(args):
    idx, url, save_path, headers, proxies = args
    success, result = download_image(url, save_path, headers, proxies)
    return idx, url, save_path, success, result


def download_images(urls, save_dir, referer=None, proxies=None, max_workers=MAX_WORKERS):
    """批量下载图片，文件名保留原始编号"""
    if not urls:
        print('[WARN] 没有可下载的图片')
        return []

    os.makedirs(save_dir, exist_ok=True)
    headers = build_image_headers(referer or DEFAULT_REFERER)

    # 准备任务
    tasks = []
    for i, url in enumerate(urls, 1):
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower() or '.webp'
        original_name = os.path.basename(unquote(parsed.path))
        if original_name and re.search(r'\d+', original_name):
            save_name = original_name
        else:
            save_name = f"{i:03d}{ext}"
        save_path = os.path.join(save_dir, save_name)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            print(f'[SKIP] 已存在: {save_name}')
            continue
        tasks.append((i, url, save_path, headers, proxies))

    if not tasks:
        print('[INFO] 所有图片都已存在，无需下载')
        return []

    print(f'[INFO] 开始下载 {len(tasks)} 张图片，保存到: {save_dir}')
    print(f'[INFO] 并发数: {max_workers}')
    print()

    results = []
    success_count = 0
    fail_count = 0
    total = len(tasks)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_with_progress, task): task for task in tasks}
        for future in as_completed(futures):
            idx, url, save_path, success, result = future.result()
            filename = os.path.basename(save_path)
            if success:
                success_count += 1
                size_mb = result / (1024 * 1024)
                print(f'[{idx}/{total}] ✅ {filename} ({size_mb:.2f} MB)')
            else:
                fail_count += 1
                print(f'[{idx}/{total}] ❌ {filename} - {result}')
            results.append((idx, url, save_path, success, result))

    print()
    print(f'[DONE] 下载完成: 成功 {success_count} 张，失败 {fail_count} 张')
    return results


# ============ 主流程 ============

def fetch_page(url, proxies=None):
    """获取章节页面内容"""
    headers = build_headers()
    print(f'[INFO] 正在获取页面: {url}')
    try:
        resp = http_get(url, headers=headers, proxies=proxies, timeout=DEFAULT_TIMEOUT)
        if HAS_REQUESTS:
            html = resp.text
        else:
            html = resp.decode('utf-8', errors='ignore')
        print(f'[INFO] 页面获取成功，大小: {len(html):,} 字符')
        return html
    except Exception as e:
        print(f'[ERROR] 页面获取失败: {e}')
        return None


def parse_curl(curl_cmd):
    """从 cURL 命令中提取 URL 和 headers"""
    url_match = re.search(r"['\"]?(https?://[^'\"]+)['\"]?", curl_cmd)
    if not url_match:
        return None, {}
    url = url_match.group(1)

    headers = build_headers()
    header_matches = re.findall(r"""-H\s+['\"]([^'\"]+)['\"]""", curl_cmd)
    for h in header_matches:
        if ':' in h:
            key, value = h.split(':', 1)
            headers[key.strip()] = value.strip()

    cookie_match = re.search(r"""-b\s+['\"]([^'\"]+)['\"]""", curl_cmd)
    if cookie_match:
        headers['Cookie'] = cookie_match.group(1)

    return url, headers


def main_process(input_str, save_dir=None, proxies=None, max_workers=MAX_WORKERS):
    """主处理函数"""
    input_str = input_str.strip()
    if not input_str:
        return

    # cURL 命令模式
    if input_str.lower().startswith('curl '):
        url, headers = parse_curl(input_str)
        if not url:
            print('[ERROR] 无法从 cURL 命令中提取 URL')
            return
    else:
        url = input_str

    # 自动检测代理
    if proxies is None:
        detected = detect_proxy()
        if detected:
            proxies = {'http': detected, 'https': detected}
            print(f'[INFO] 已自动检测到代理: {detected}')
        else:
            proxies = {}
            print('[INFO] 未检测到代理，将直连')
    elif isinstance(proxies, str):
        proxies = {'http': proxies, 'https': proxies}
    else:
        proxies = proxies or {}

    # 默认保存目录
    if not save_dir:
        save_dir = get_default_download_dir()

    # 自动提取站内 Referer（关键：CDN 防盗链）
    referer = extract_referer_from_url(url)

    # 情况1: 直接图片 URL -> 尝试反推整章
    if is_image_url(url):
        print('[INFO] 检测到图片 URL，尝试反推同章节图片...')
        image_urls = infer_image_sequence(url)
        if image_urls:
            print(f'[INFO] 已生成 {len(image_urls)} 个候选 URL（探测中）')
            print(f'[INFO] 探测间隔: {PROBE_DELAY}s，超时: {PROBE_TIMEOUT}s，重试: {PROBE_MAX_RETRIES} 次')
            # 顺序探测有效图片
            valid_urls = []
            consecutive_failures = 0
            headers = build_image_headers(referer)
            for i, cand in enumerate(image_urls, 1):
                if consecutive_failures >= 8:
                    print(f'[INFO] 连续 {consecutive_failures} 次失败，停止探测')
                    break
                # 单次探测（失败自动重试 PROBE_MAX_RETRIES 次，间隔递增）
                found = False
                miss_reason = 'unknown'
                for attempt in range(PROBE_MAX_RETRIES + 1):
                    try:
                        if HAS_REQUESTS:
                            resp = requests.get(cand, headers=headers, proxies=proxies,
                                                timeout=PROBE_TIMEOUT, stream=True)
                            status = resp.status_code
                            ctype = resp.headers.get('Content-Type', '')
                            resp.close()
                            if status == 200 and 'image' in ctype:
                                found = True
                                break
                            miss_reason = f'status={status}'
                        else:
                            req = urllib.request.Request(cand, headers=headers)
                            with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as r:
                                ctype = r.headers.get('Content-Type', '')
                                if 'image' in ctype:
                                    found = True
                                    break
                                miss_reason = f'type={ctype[:20]}'
                    except urllib.error.HTTPError as e:
                        miss_reason = f'status={e.code}'
                    except Exception as e:
                        miss_reason = f'err={str(e)[:40]}'
                    if attempt < PROBE_MAX_RETRIES:
                        time.sleep(0.5 * (attempt + 1))   # 重试间隔递增
                if found:
                    valid_urls.append(cand)
                    consecutive_failures = 0
                    print(f'[FOUND] {os.path.basename(cand)}')
                else:
                    consecutive_failures += 1
                    print(f'[MISS] {os.path.basename(cand)} ({miss_reason})')
                time.sleep(PROBE_DELAY)

            print()
            print(f'[INFO] 探测结束，共找到 {len(valid_urls)} 张图片')

            # 章节号目录作为文件夹名
            path_parts = [p for p in unquote(urlparse(url).path).split('/') if p]
            if len(path_parts) >= 2 and path_parts[-2].isdigit():
                folder_name = f'{path_parts[-2]}_{path_parts[-1]}'
            else:
                folder_name = sanitize_filename(path_parts[-2] if len(path_parts) >= 2 else path_parts[-1])
            final_save_dir = os.path.join(save_dir, folder_name)

            if valid_urls:
                download_images(valid_urls, final_save_dir, referer=referer,
                                proxies=proxies, max_workers=max_workers)
            else:
                print('[WARN] 未能探测到有效图片')
        return

    # 情况2: 页面 URL -> 提取图片（推荐路径）
    html = fetch_page(url, proxies=proxies)
    if html is None:
        return

    title = extract_title_from_html(html, url)
    folder_name = sanitize_filename(title) if title else f'manga_{int(time.time())}'
    final_save_dir = os.path.join(save_dir, folder_name)

    image_urls = extract_images_from_page(url, html)

    if image_urls:
        print(f'[INFO] 从页面中提取到 {len(image_urls)} 张图片')
        print(f'[INFO] Referer: {referer}')
        download_images(image_urls, final_save_dir, referer=referer,
                        proxies=proxies, max_workers=max_workers)
    else:
        print('[WARN] 未从页面中提取到图片')
        print('[HINT] 你可以复制任意一张图片 URL，程序会尝试反推整章')
        print('[HINT] 或检查页面是否需要登录/刷新后重试')


if __name__ == '__main__':
    print('=' * 60)
    print('mhxiaoshen 漫画图片下载器')
    print('=' * 60)
    print()
    print('支持的输入：')
    print('  1. 章节页面 URL（推荐，直接提取全部图片）')
    print('  2. 单张图片 URL（自动反推整章）')
    print('  3. cURL 命令')
    print()
    print('直接回车可退出程序')
    print()

    while True:
        print('-' * 60)
        user_input = input('请粘贴 URL 或 cURL 命令: ').strip()

        if not user_input:
            print('[INFO] 已退出')
            break

        print()
        try:
            main_process(user_input)
        except Exception as e:
            print(f'[ERROR] 程序异常: {e}')
        print()
