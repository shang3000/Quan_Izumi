"""
TikTok 视频批量下载器（tikwm API + yt-dlp 双引擎）

支持的输入格式：
1. 单条视频链接
   https://www.tiktok.com/@用户名/video/7676299605516061960
   https://www.tiktok.com/@用户名/photo/1234567890        （图集）
2. 分享短链接（自动跟随重定向到正式链接）
   https://vm.tiktok.com/xxxxxx/
   https://vt.tiktok.com/xxxxxx/
3. 用户主页（批量下载 TA 的全部视频）
   https://www.tiktok.com/@用户名     或直接输入   @用户名
4. cURL 命令（从 Chrome DevTools 复制，自动提取里面的链接）

使用方法：
1. 直接运行：.venv/Scripts/python Tiktok-downloader.py
2. 把链接粘贴进去，回车开始下载
3. 单条视频：会列出可选版本（高清无水印 / 标准无水印 / 带水印 / 仅原声），
   回车默认下无水印版
4. 用户主页：先预览视频列表，可选全部下载 / 只下前 N 条 / 翻页
5. 视频/图片保存到 downloads_tiktok/ 目录
6. 输入 q 退出

双引擎说明：
- 主引擎 tikwm.com 公共 API：稳定、自带无水印直链，缺点是第三方服务
  （限频 1 次/秒，脚本已自动放慢节奏）
- 备用引擎 yt-dlp：tikwm 挂了或没收录时自动切换
  （yt-dlp 需要 curl_cffi 做浏览器伪装，venv 里已装好）

⚠️ 常见报错：
- tikwm 一直失败 → 第三方服务可能在抽风 / 你的 IP 被 TikTok 风控盯上，
  换个 Clash 节点再试
- 拉主页拿到 0 条 → 未登录被 TikTok 限流。浏览器登录 TikTok 后：
  1. 装扩展「Get cookies.txt LOCALLY」，打开 tiktok.com（保持登录）导出
  2. 重命名为 cookies_tiktok.txt 放到本脚本同目录，重启脚本
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import time
import socket

try:
    import requests
except ImportError:
    print('未安装 requests，请先执行：')
    print('    .venv/Scripts/python -m pip install requests')
    sys.exit(1)

# yt-dlp 是备用引擎，缺了不影响主流程
try:
    import yt_dlp
    yt_dlp.YoutubeDL.deprecated_feature = lambda self, message: None  # 屏蔽 Python 3.10 弃用提示
except ImportError:
    yt_dlp = None


# ============ 配置区 ============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, 'downloads_tiktok')
COOKIE_FILE = os.path.join(SCRIPT_DIR, 'cookies_tiktok.txt')   # yt-dlp 备用引擎的 Cookie

MAX_DURATION = None          # 批量任务只下载短于该秒数的视频（None = 不限制）
MAX_RETRIES = 3              # 外层重试次数
API_INTERVAL = 1.5           # tikwm 请求间隔秒数（免费接口限 1 次/秒，留点余量）
BATCH_QUALITY = 'play'       # 批量任务用的画质：'hdplay'=高清无水印 'play'=标准无水印 'wmplay'=带水印

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')

# 常见本地代理端口（Clash / v2ray 等）
PROXY_PORTS = [7897, 7890, 7891, 10809, 1080]
PROXY_HOST = '127.0.0.1'

TIKWM_BASE = 'https://www.tikwm.com/api'


# ============ 代理检测 ============

def detect_proxy():
    """依次探测常见代理端口，返回 requests 可用的 proxies dict；探测不到返回 None（走直连）"""
    for port in PROXY_PORTS:
        try:
            with socket.create_connection((PROXY_HOST, port), timeout=1):
                proxy = f'http://{PROXY_HOST}:{port}'
                print(f'[代理] 检测到本地代理：{proxy}')
                return {'http': proxy, 'https': proxy}
        except OSError:
            continue
    print('[代理] 未检测到本地代理，尝试直连…')
    return None


def can_direct_connect():
    """测试能否直连 TikTok"""
    try:
        with socket.create_connection(('www.tiktok.com', 443), timeout=5):
            return True
    except OSError:
        return False


def get_proxies():
    """决定代理配置：有本地代理用代理，否则测直连"""
    proxies = detect_proxy()
    if proxies:
        return proxies
    if can_direct_connect():
        print('[代理] 直连可用')
        return None
    print('[代理] ⚠️ 无代理且无法直连 TikTok，请先开启 Clash 等代理工具再运行')
    return None


# ============ 工具函数 ============

def sanitize_filename(name, max_len=60):
    """清理文件名非法字符并截断"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', ' ', str(name))
    name = re.sub(r'\s+', ' ', name).strip().strip('.')
    return name[:max_len] if name else 'untitled'


def build_filename(title, video_id, ext):
    """构造 '标题 [视频ID].ext' 形式的文件名"""
    return os.path.join(DOWNLOAD_DIR,
                        f'{sanitize_filename(title)} [{video_id}].{ext}')


def fix_url(u):
    """把 tikwm 返回的链接补全协议（可能是 //xxx 或 /xxx 开头）"""
    if not u:
        return u
    if u.startswith('//'):
        return 'https:' + u
    if u.startswith('/'):
        return 'https://www.tikwm.com' + u
    return u


def download_file(url, path, proxies):
    """流式下载文件，带进度显示；成功返回 True"""
    headers = {'User-Agent': UA, 'Referer': 'https://www.tiktok.com/'}
    try:
        with requests.get(url, headers=headers, proxies=proxies,
                          timeout=60, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length') or 0)
            done = 0
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done / total * 100
                        print(f'\r  下载中 {pct:5.1f}%  {done / 1024 / 1024:.1f} MB',
                              end='', flush=True)
        print()
        # 校验：mp4 至少要有 ftyp 头，太小说明下到了错误页
        if os.path.getsize(path) < 10240:
            os.remove(path)
            print('  ⚠️ 文件异常（小于 10KB），已丢弃')
            return False
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f'💾 已保存：{path}（{size_mb:.1f} MB）')
        return True
    except requests.RequestException as e:
        print(f'\n  ⚠️ 下载中断：{str(e)[:120]}')
        if os.path.exists(path):
            os.remove(path)   # 删掉半截文件，保证重试能重来
        return False


# ============ tikwm 主引擎 ============

def tikwm_get(path, params, proxies):
    """请求 tikwm API，返回 data 部分；失败抛 RuntimeError"""
    try:
        r = requests.get(TIKWM_BASE + path, params=params,
                         proxies=proxies, timeout=30,
                         headers={'User-Agent': UA})
        r.raise_for_status()
        j = r.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f'tikwm 请求失败：{str(e)[:120]}')
    if j.get('code') != 0:
        raise RuntimeError(f'tikwm 返回错误：{str(j.get("msg"))[:120]}')
    return j.get('data') or {}


def tikwm_video_info(url, proxies):
    """解析单条视频/图集信息"""
    data = tikwm_get('/', {'url': url, 'hd': 1}, proxies)
    if not data.get('id'):
        raise RuntimeError('tikwm 未返回视频数据（链接可能无效或已删除）')
    return data


def resolve_short_url(url, proxies):
    """把 vm.tiktok.com / vt.tiktok.com 短链解析成正式链接"""
    if not re.search(r'(vm|vt)\.tiktok\.com/', url):
        return url
    try:
        r = requests.get(url, proxies=proxies, timeout=20,
                         headers={'User-Agent': UA}, allow_redirects=True)
        return r.url
    except requests.RequestException:
        return url


# ============ 单视频流程 ============

def run_single_tikwm(target, proxies):
    """tikwm 引擎处理单条视频。返回 'ok' / 'retry' / 'abort'"""
    try:
        info = tikwm_video_info(target, proxies)
    except RuntimeError as e:
        print(f'❌ {e}')
        if '无效' in str(e) or '删除' in str(e):
            return 'abort'
        return 'retry'

    vid = info.get('id', '')
    title = info.get('title') or 'tiktok_video'
    author = (info.get('author') or {}).get('nickname', '?')
    dur = info.get('duration')
    print(f'  标题：{title}')
    print(f'  时长：{int(dur)}s   作者：{author}')

    # ---- 图集：images 非空 ----
    images = info.get('images') or []
    if images:
        print(f'\n🖼  这是图集，共 {len(images)} 张图片')
        try:
            choice = input('   回车下载全部图片，q 放弃 > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'ok'
        if choice == 'q':
            print('↩ 已放弃')
            return 'ok'
        ok = 0
        for i, img in enumerate(images, 1):
            img = fix_url(img)
            path = build_filename(f'{title} #{i:02d}', vid, 'jpg')
            if os.path.exists(path):
                print(f'  ⇣ 第 {i} 张已存在，跳过')
                ok += 1
                continue
            print(f'  ⬇ 第 {i}/{len(images)} 张…')
            if download_file(img, path, proxies):
                ok += 1
            time.sleep(API_INTERVAL)
        print(f'✅ 完成：{ok}/{len(images)} 张' if ok else '❌ 全部失败')
        return 'ok' if ok else 'retry'

    # ---- 视频：列出版本菜单 ----
    hd_url = fix_url(info.get('hdplay'))
    play_url = fix_url(info.get('play'))
    wm_url = fix_url(info.get('wmplay'))
    music_url = fix_url(info.get('music'))

    def mb(v):
        return f'（约 {v / 1024 / 1024:.1f} MB）' if v else ''

    print('\n🎛  请选择版本：')
    print(f'   0. 标准无水印（回车默认）{mb(info.get("size"))}')
    if hd_url:
        print(f'   1. 高清无水印 1080p{mb(info.get("hd_size"))}')
    if wm_url:
        print(f'   2. 带水印原版{mb(info.get("wm_size"))}')
    print('   3. 仅原声 mp3   q. 放弃下载')

    while True:
        try:
            choice = input('   选择 > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'ok'
        if choice in ('', '0'):
            url, ext = play_url, 'mp4'
            label = '标准无水印'
            break
        if choice == '1' and hd_url:
            url, ext = hd_url, 'mp4'
            label = '高清无水印'
            break
        if choice == '2' and wm_url:
            url, ext = wm_url, 'mp4'
            label = '带水印原版'
            break
        if choice == '3' and music_url:
            url, ext = music_url, 'mp3'
            label = '原声 mp3'
            break
        if choice == 'q':
            print('↩ 已放弃，不下载')
            return 'ok'
        print('   输入无效，请重新选择')

    path = build_filename(title, vid, ext)
    if os.path.exists(path):
        print(f'⇣ 文件已存在，跳过：{os.path.basename(path)}')
        return 'ok'

    print(f'\n⬇ 开始下载（{label}）…')
    return 'ok' if download_file(url, path, proxies) else 'retry'


# ============ 用户主页批量流程 ============

def run_user_page_tikwm(unique_id, proxies):
    """tikwm 引擎批量下载用户主页视频。返回 'ok' / 'retry' / 'abort'"""
    cursor = 0
    all_videos = []
    print(f'\n▶ 用户主页：@{unique_id}（分页拉取，每页 33 条）')

    # ---- 先拉第一页预览 ----
    try:
        data = tikwm_get('/user/posts',
                         {'unique_id': unique_id, 'count': 33, 'cursor': 0},
                         proxies)
    except RuntimeError as e:
        print(f'❌ {e}')
        return 'retry'
    videos = data.get('videos') or []
    if not videos:
        print('❌ 一条视频都没拿到（用户不存在 / 未登录被限流 / 该用户无私发视频）')
        return 'abort'

    all_videos.extend(videos)
    _preview_videos(videos)

    while True:
        try:
            choice = input('\n📥 回车=下载以上全部  数字N=只下前N条  '
                           'm=再拉一页  q=放弃 > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'ok'

        if choice == 'q':
            print('↩ 已放弃')
            return 'ok'

        if choice == 'm':
            if not data.get('hasMore'):
                print('   没有更多了')
                continue
            cursor = data.get('cursor') or (cursor + 33)
            try:
                data = tikwm_get('/user/posts',
                                 {'unique_id': unique_id, 'count': 33,
                                  'cursor': cursor}, proxies)
            except RuntimeError as e:
                print(f'❌ {e}')
                continue
            videos = data.get('videos') or []
            if not videos:
                print('   没有更多了')
                continue
            all_videos.extend(videos)
            _preview_videos(videos, start=len(all_videos) - len(videos) + 1)
            continue

        # 回车 = 全部；数字 = 前 N 条
        if choice.isdigit() and int(choice) > 0:
            targets = all_videos[:int(choice)]
        else:
            targets = all_videos
        break

    # ---- 批量下载 ----
    # 过滤超时长视频
    if MAX_DURATION:
        n_before = len(targets)
        targets = [v for v in targets
                   if not v.get('duration') or v['duration'] <= MAX_DURATION]
        if len(targets) < n_before:
            print(f'⏭ 已按时长过滤（<{MAX_DURATION}s），跳过 {n_before - len(targets)} 条')

    print(f'\n⬇ 开始批量下载，共 {len(targets)} 条（画质：{ {"play": "标准无水印", "hdplay": "高清无水印", "wmplay": "带水印"}[BATCH_QUALITY] }）')
    ok = fail = skip = 0
    for i, v in enumerate(targets, 1):
        vid = v.get('video_id') or v.get('id', '')
        title = v.get('title') or 'tiktok_video'
        url = fix_url(v.get(BATCH_QUALITY) or v.get('play'))
        path = build_filename(title, vid, 'mp4')
        print(f'\n[{i}/{len(targets)}] {sanitize_filename(title, 40)}')
        if not url:
            print('  ⚠️ 无下载链接，跳过')
            fail += 1
            continue
        if os.path.exists(path):
            print('  ⇣ 已存在，跳过')
            skip += 1
            continue
        if download_file(url, path, proxies):
            ok += 1
        else:
            fail += 1
        time.sleep(API_INTERVAL)

    print(f'\n✅ 批量完成：成功 {ok}，跳过 {skip}，失败 {fail}')
    print(f'💾 文件保存在：{DOWNLOAD_DIR}')
    return 'ok' if fail == 0 else ('ok' if ok else 'retry')


def _preview_videos(videos, start=1):
    """预览视频列表（前 10 条）"""
    print(f'共拉到 {len(videos)} 条：')
    for i, v in enumerate(videos[:10], start):
        dur = v.get('duration')
        dur_str = f'{int(dur)}s' if dur else '?'
        print(f'  {i:>3}. [{dur_str}] {sanitize_filename(v.get("title", "?"), 40)}')
    if len(videos) > 10:
        print(f'  … 以及另外 {len(videos) - 10} 条')


# ============ yt-dlp 备用引擎 ============

def run_ytdlp(target, proxies):
    """yt-dlp 备用引擎：单视频 / 主页都直接交给它。返回 'ok' / 'retry'"""
    if yt_dlp is None:
        print('❌ yt-dlp 未安装（备用引擎不可用）')
        return 'retry'

    proxy = proxies['http'] if proxies else None
    opts = {
        'format': 'best[format_id!*=download_addr]/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).60s [%(id)s].%(ext)s'),
        'retries': 5,
        'fragment_retries': 10,
        'ignoreerrors': True,
        'sleep_interval_requests': 1,
        'overwrites': False,
        'continuedl': True,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'proxy': proxy,
        'extractor_args': {'tiktok': {
            'api_hostname': ['api16-normal-c-useast1a.tiktokv.com'],
        }},
    }
    if os.path.exists(COOKIE_FILE):
        opts['cookiefile'] = COOKIE_FILE

    print('… 尝试备用引擎 yt-dlp…')
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ret = ydl.download([target])
        if ret == 0:
            print(f'✅ 下载完成！文件保存在：{DOWNLOAD_DIR}')
            return 'ok'
        return 'retry'
    except yt_dlp.utils.DownloadError as e:
        print(f'❌ yt-dlp 也失败了：{str(e)[:150]}')
        return 'retry'


# ============ 输入解析 ============

def normalize_target(user_input, proxies):
    """
    把用户输入统一处理。
    返回 (kind, target)：kind ∈ {'video', 'user', 'unknown'}
    """
    text = user_input.strip()

    # cURL 命令：提取第一个 TikTok 链接
    if text.lower().startswith('curl '):
        m = re.search(r'https?://[^\s\'"]+', text)
        if m:
            text = m.group(1).rstrip('\\')
        else:
            return 'unknown', text

    # 裸 @用户名 → 主页
    if re.fullmatch(r'@[\w\.\-]+', text):
        return 'user', text[1:]

    # 链接：去掉误粘贴的跟踪参数
    m = re.search(r'(https?://[^\s\'"]*tiktok\.com/[^\s\'"?]+)', text)
    if m:
        text = m.group(1)
    elif re.match(r'https?://(vm|vt)\.tiktok\.com/\S+', text):
        pass
    else:
        return 'unknown', text

    # 短链 → 跟随重定向拿正式链接
    text = resolve_short_url(text, proxies)

    # 主页链接（没有 /video/ /photo/）→ 用户模式
    if 'tiktok.com/@' in text and not re.search(r'/(video|photo)/\d+', text):
        m = re.search(r'@([\w\.\-]+)', text)
        if m:
            return 'user', m.group(1)

    return 'video', text


# ============ 主流程 ============

def run_download(kind, target, proxies):
    """
    执行下载，双引擎策略：tikwm 失败自动切 yt-dlp。
    返回 'ok' / 'retry' / 'abort'
    """
    print(f'\n▶ 目标：{target if kind != "user" else "@" + target}')
    print('=' * 60)

    # tikwm 主引擎
    if kind == 'user':
        result = run_user_page_tikwm(target, proxies)
    else:
        result = run_single_tikwm(target, proxies)

    # tikwm 失败 → yt-dlp 备用引擎
    if result == 'retry' and yt_dlp:
        ydl_target = target if kind == 'video' else f'https://www.tiktok.com/@{target}'
        result = run_ytdlp(ydl_target, proxies)

    return result


def main():
    print('=' * 60)
    print('   TikTok 视频批量下载器（tikwm + yt-dlp 双引擎）')
    print('=' * 60)
    print(f'保存目录：{os.path.abspath(DOWNLOAD_DIR)}')
    if MAX_DURATION:
        print(f'时长过滤：批量任务仅下载短于 {MAX_DURATION} 秒的视频（配置区 MAX_DURATION 可改）')
    print()
    print('支持的输入：')
    print('  1. 视频链接    https://www.tiktok.com/@用户名/video/xxxx')
    print('  2. 分享短链    https://vm.tiktok.com/xxxx/')
    print('  3. 用户主页    https://www.tiktok.com/@用户名  或  @用户名')
    print('  4. cURL 命令   （从浏览器 DevTools 复制）')
    print('  输入 q 退出')
    print()

    proxies = get_proxies()

    while True:
        try:
            user_input = input('📥 请输入链接 > ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break

        if not user_input:
            continue
        if user_input.lower() in ('q', 'quit', 'exit'):
            print('再见！')
            break

        kind, target = normalize_target(user_input, proxies)
        if kind == 'unknown':
            print('⚠️ 看不懂这个输入，请粘贴 TikTok 链接、@用户名 或 cURL 命令')
            continue

        for attempt in range(1, MAX_RETRIES + 1):
            result = run_download(kind, target, proxies)
            if result in ('ok', 'abort'):
                break
            if attempt < MAX_RETRIES:
                wait = attempt * 5
                print(f'… 第 {attempt} 次失败，{wait}s 后重试（{attempt}/{MAX_RETRIES}）')
                time.sleep(wait)
            else:
                print('❌ 重试次数用完，跳过该目标')

        print('=' * 60)


if __name__ == '__main__':
    main()
