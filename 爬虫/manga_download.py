"""
漫画图片批量下载器

支持的输入格式：
1. 漫画章节页面 URL（推荐）
   例如：https://www.mkiaoshen.vip/19-xxx-01-1_-1-3.html
2. 单张图片 URL（程序会自动推断同章节其他图片）
   例如：https://cdn.mnba.stream/comics/19/xxx/001.webp
3. 任意包含漫画图片的网页 URL
4. cURL 命令（从 Chrome DevTools 复制）

使用方法：
1. 打开漫画章节页面
2. 复制页面 URL 或任意一张图片 URL
3. 粘贴到下方输入框，回车开始下载
4. 图片会保存到项目 downloads/ 目录下的子文件夹中

特点：
- 自动检测系统代理（127.0.0.1:7897）
- 自动从页面中提取所有漫画图片
- 支持单张图片 URL 反推整章
- 多线程并发下载
- 失败自动重试
- 支持断点续传
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import time
import json
import gzip
import random
import shutil
import urllib.request
from urllib.parse import urlparse, urljoin, unquote
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

DEFAULT_PROXY = 'http://127.0.0.1:7897'  # Clash 默认代理地址
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
MAX_WORKERS = 3  # 并发下载数（该站点对并发敏感，默认 conservative）
PROBE_DELAY = 0.3  # 顺序探测时每次请求间隔（秒）
PROBE_TIMEOUT = 15  # 顺序探测超时时间（秒）
PROBE_MAX_RETRIES = 2  # 探测失败时重试次数
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
)

# 常见漫画图片域名/路径特征
MANGA_IMAGE_PATTERNS = [
    r'https?://[^\s"\'<>]+\.(?:webp|jpg|jpeg|png|gif|bmp)(?:\?[^\s"\'<>]*)?',
]

# 页面中可能存放图片列表的 JSON 字段名
IMAGE_ARRAY_KEYS = [
    'images', 'imageList', 'image_list', 'pages', 'files', 'pics', 'picture',
    'chapterImages', 'chapter_images', 'data', 'imageData', 'chapter', 'photos',
]


# ============ 工具函数 ============

def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))


def get_default_download_dir():
    """默认下载目录"""
    return os.path.join(get_project_root(), 'downloads')


def detect_proxy():
    """检测系统代理是否可用"""
    # 检测常见代理端口
    proxy_ports = [7897, 7890, 10808, 10809, 8080]
    for port in proxy_ports:
        proxy_url = f'http://127.0.0.1:{port}'
        if _check_proxy(proxy_url):
            return proxy_url
    return None


def _check_proxy(proxy_url):
    """测试代理是否可用（简单连接测试）"""
    try:
        parsed = urlparse(proxy_url)
        host, port = parsed.hostname, parsed.port
        import socket
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def build_headers(referer=None):
    """构建请求头"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    if referer:
        headers['Referer'] = referer
    return headers


def build_image_headers(referer):
    """构建图片请求头"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': referer,
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    return headers


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    if not name:
        return 'untitled'
    name = unquote(name).strip()
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('._')
    return name or 'untitled'


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
        # urllib 不会自动解 gzip，如果 Accept-Encoding 包含 gzip，需要手动处理
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


def test_url_access(url, headers=None, proxies=None, timeout=10, retries=0):
    """测试 URL 是否可访问，返回状态码和 Content-Type

    Args:
        retries: 连接失败时的重试次数，每次重试间隔递增
    """
    last_error = ''
    for attempt in range(retries + 1):
        try:
            resp = http_get(url, headers=headers, proxies=proxies, timeout=timeout)
            if HAS_REQUESTS:
                return resp.status_code, resp.headers.get('Content-Type', '')
            else:
                return resp.getcode(), resp.headers.get('Content-Type', '')
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                sleep_time = 0.5 * (attempt + 1)
                time.sleep(sleep_time)
                continue
            return 0, last_error
    return 0, last_error


# ============ URL 解析与图片提取 ============

def is_image_url(url):
    """判断 URL 是否是图片链接"""
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    return ext in {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.avif'}


def is_manga_cdn_url(url):
    """判断是否是常见漫画 CDN 图片链接"""
    cdn_domains = [
        'cdn.mnba.stream',
        'mnba.stream',
        'comic',
        'manga',
        'img',
        'image',
        'pic',
    ]
    url_lower = url.lower()
    return any(d in url_lower for d in cdn_domains)


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


def extract_title_from_html(html, url=None):
    """从 HTML 中提取标题"""
    # 尝试 title 标签
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
        # 去掉常见后缀
        title = re.sub(r'[-_|\s]*漫画小生.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'[-_|\s]*免费.*$', '', title)
        if title:
            return title
    # 从 URL 路径提取
    if url:
        parsed = urlparse(url)
        path = unquote(os.path.basename(parsed.path))
        name = os.path.splitext(path)[0]
        if name:
            return name
    return None


def extract_images_with_bs4(html, base_url):
    """使用 BeautifulSoup 提取图片 URL"""
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
    """使用正则表达式提取图片 URL"""
    images = []
    for pattern in MANGA_IMAGE_PATTERNS:
        matches = re.findall(pattern, html)
        for url in matches:
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

    # 模式3: 更宽松的 JSON 数组（包含 http 字符串的数组）
    generic_array = re.compile(
        r'\[\s*"(https?://[^"]+(?:webp|jpg|jpeg|png|gif|bmp)[^"]*)"(?:\s*,\s*"(https?://[^"]+(?:webp|jpg|jpeg|png|gif|bmp)[^"]*)")*\s*\]',
        re.IGNORECASE | re.DOTALL
    )
    for match in generic_array.finditer(html):
        for group in match.groups():
            if group:
                url = normalize_url(base_url, group)
                if url:
                    images.append(url)

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

    # 策略1: BeautifulSoup
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

    # 优先保留漫画 CDN 图片，过滤掉小图标/广告图
    manga_images = [img for img in unique_images if is_manga_cdn_url(img)]
    if manga_images:
        return manga_images

    # 如果全是 webp/jpg 等图片，也返回
    return [img for img in unique_images if is_image_url(img)]


def infer_image_sequence(image_url):
    """
    从单张图片 URL 推断整章图片序列
    例如：https://cdn.mnba.stream/comics/19/name/009.webp
    会生成 001.webp ~ 999.webp 的候选 URL
    """
    parsed = urlparse(image_url)
    path = unquote(parsed.path)
    base = os.path.basename(path)  # 009.webp
    dir_path = os.path.dirname(path)  # /comics/19/name

    # 提取文件名中的数字部分
    match = re.search(r'(\d+)(\.\w+)$', base)
    if not match:
        return []

    ext = match.group(2)
    num_len = len(match.group(1))

    base_url = f"{parsed.scheme}://{parsed.netloc}{dir_path}/"
    candidates = []
    for i in range(1, 1000):
        filename = f"{i:0{num_len}d}{ext}"
        candidates.append(f"{base_url}{filename}")
    return candidates


# ============ 下载相关 ============

def download_image(url, save_path, headers, proxies, retries=MAX_RETRIES):
    """下载单张图片"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    for attempt in range(retries):
        try:
            if HAS_REQUESTS:
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=DEFAULT_TIMEOUT, stream=True)
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
            return True, file_size
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
            return False, str(e)
    return False, 'unknown error'


def download_with_progress(args):
    """供多线程调用的下载任务"""
    idx, url, save_path, headers, proxies = args
    success, result = download_image(url, save_path, headers, proxies)
    return idx, url, save_path, success, result


def download_images(urls, save_dir, referer=None, proxies=None, max_workers=MAX_WORKERS):
    """批量下载图片

    文件名保留 URL 中的原始编号（如 009.webp），不会因缺图而重新编号。
    """
    if not urls:
        print('[WARN] 没有可下载的图片')
        return []

    os.makedirs(save_dir, exist_ok=True)
    headers = build_image_headers(referer or 'https://www.mkiaoshen.vip/')

    # 准备任务
    tasks = []
    for i, url in enumerate(urls, 1):
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower() or '.webp'
        # 尝试从 URL 中提取原始文件名（如 009.webp），保留原始编号
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


def probe_sequential_images(base_image_url, proxies=None):
    """
    通过顺序探测获取整章图片 URL
    当只有单张图片 URL 时使用

    说明：
    - 每次探测之间加入随机延迟，模拟正常浏览节奏，避免被 CDN 限流
    - 对 status=0（连接失败）自动重试，减少偶发网络抖动导致的误判
    """
    candidates = infer_image_sequence(base_image_url)
    if not candidates:
        return []

    print(f'[INFO] 正在从单张图片反推章节图片序列...')
    print(f'[INFO] 基础 URL: {base_image_url}')
    print(f'[INFO] 探测间隔: {PROBE_DELAY}s，超时: {PROBE_TIMEOUT}s，重试: {PROBE_MAX_RETRIES} 次')
    print()

    valid_urls = []
    consecutive_failures = 0
    max_consecutive_failures = 5

    headers = build_image_headers('https://www.mkiaoshen.vip/')

    for i, url in enumerate(candidates, 1):
        if consecutive_failures >= max_consecutive_failures:
            print(f'[INFO] 连续 {max_consecutive_failures} 次失败，停止探测')
            break

        # 请求前随机延迟，模拟人类浏览（范围 0.5 * delay ~ 1.5 * delay）
        jitter = PROBE_DELAY * (0.5 + random.random())
        time.sleep(jitter)

        status, content_type = test_url_access(
            url, headers=headers, proxies=proxies,
            timeout=PROBE_TIMEOUT, retries=PROBE_MAX_RETRIES
        )

        if status == 200 and ('image' in content_type or 'webp' in content_type or 'octet' in content_type):
            valid_urls.append(url)
            consecutive_failures = 0
            print(f'[FOUND] 第 {i:03d} 张')
        elif status == 404 or status == 403:
            # 真正的 404/403 才认为是页面不存在
            consecutive_failures += 1
            print(f'[MISS] 第 {i:03d} 张不存在 (status={status})')
        else:
            # 连接错误也计入连续失败
            consecutive_failures += 1
            print(f'[MISS] 第 {i:03d} 张探测失败 (status={status}, type={content_type[:30]})')

    print()
    print(f'[INFO] 探测结束，共找到 {len(valid_urls)} 张图片')
    return valid_urls


# ============ 主流程 ============

def fetch_page(url, proxies=None):
    """获取页面内容"""
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

    # 提示当前 HTTP 后端
    if not HAS_REQUESTS:
        print('[INFO] 当前使用 urllib 作为 HTTP 后端（建议安装 requests 以获得更好体验）')

    # 如果提供了 cURL 命令
    if input_str.lower().startswith('curl '):
        url, _ = parse_curl(input_str)
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

    # 设置默认保存目录
    if not save_dir:
        save_dir = get_default_download_dir()

    # 情况1: 直接图片 URL -> 尝试反推整章
    if is_image_url(url):
        print('[INFO] 检测到图片 URL，尝试反推整章图片...')
        image_urls = probe_sequential_images(url, proxies=proxies)
        if image_urls:
            # 用 URL 路径作为文件夹名
            parsed = urlparse(url)
            path_parts = [p for p in unquote(parsed.path).split('/') if p]
            folder_name = sanitize_filename(path_parts[-2] if len(path_parts) >= 2 else path_parts[-1])
            final_save_dir = os.path.join(save_dir, folder_name)
            download_images(image_urls, final_save_dir, referer='https://www.mkiaoshen.vip/', proxies=proxies, max_workers=max_workers)
        else:
            print('[WARN] 未能反推章节图片，将只下载当前图片')
            parsed = urlparse(url)
            folder_name = sanitize_filename(os.path.splitext(os.path.basename(unquote(parsed.path)))[0])
            final_save_dir = os.path.join(save_dir, folder_name)
            download_images([url], final_save_dir, referer='https://www.mkiaoshen.vip/', proxies=proxies, max_workers=1)
        return

    # 情况2: 页面 URL -> 提取图片
    html = fetch_page(url, proxies=proxies)
    if html is None:
        return

    # 提取标题作为文件夹名
    title = extract_title_from_html(html, url)
    folder_name = sanitize_filename(title) if title else f"manga_{int(time.time())}"
    final_save_dir = os.path.join(save_dir, folder_name)

    image_urls = extract_images_from_page(url, html)

    if image_urls:
        print(f'[INFO] 从页面中提取到 {len(image_urls)} 张图片')
        download_images(image_urls, final_save_dir, referer=url, proxies=proxies, max_workers=max_workers)
    else:
        print('[WARN] 未从页面中提取到图片')
        print('[HINT] 你可以复制任意一张图片 URL，程序会尝试反推整章')


if __name__ == '__main__':
    print('=' * 60)
    print('漫画图片批量下载器')
    print('=' * 60)
    print()
    print('支持的输入：')
    print('  1. 漫画章节页面 URL（推荐）')
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
