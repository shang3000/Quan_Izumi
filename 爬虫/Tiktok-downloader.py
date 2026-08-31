"""
TikTok 视频批量下载器（基于 yt-dlp）

支持的输入格式：
1. 单条视频链接
   https://www.tiktok.com/@用户名/video/7676299605516061960
   https://www.tiktok.com/@用户名/photo/1234567890        （图集）
2. 分享短链接（自动跟随重定向到正式链接）
   https://vm.tiktok.com/xxxxxx/
   https://vt.tiktok.com/xxxxxx/
3. 用户主页（批量下载 TA 的全部视频）
   https://www.tiktok.com/@用户名
4. 话题标签页（批量下载该标签下的视频）
   https://www.tiktok.com/tag/关键词
5. cURL 命令（从 Chrome DevTools 复制，自动提取里面的链接）

使用方法：
1. 直接运行：.venv/Scripts/python Tiktok-downloader.py
2. 把链接粘贴进去，回车开始下载
3. 单条视频链接：会先列出该视频所有可选画质（540p/720p/1080p…），
   输入编号选择后再下载；回车直接下最佳画质
4. 主页 / 话题：批量下载，按配置区画质上限执行
5. 视频保存到 downloads_tiktok/ 目录
6. 输入 q 退出

特点：
- 优先下载无水印版本（download_addr 是 TikTok 官方带水印的转码，
  脚本默认避开它，选 CDN 原始流；实在没有才回退到带水印版）
- 自动检测系统代理（Clash 7897/7890 等），也支持直连
- 自动识别 Cookie：优先 cookies.txt，其次浏览器；
  TikTok 不登录一般也能下，批量拉主页被限流时按提示导出即可
- 单条链接自动弹出画质选择菜单
- 自动跳过已下载的视频（断点续传）
- 单条失败不中断批量任务
- 失败自动重试

⚠️ 常见报错：
- "Login required" / 拉主页只拿到 0 条 → TikTok 对未登录的批量请求限流。
  解决：浏览器登录 TikTok 后导出 Cookie：
  1. 浏览器装扩展「Get cookies.txt LOCALLY」，打开 tiktok.com（保持登录）导出
  2. 把导出的 cookies.txt 放到本脚本同目录，重启脚本自动识别
- 一直转圈不出结果 → 检查 Clash 是否开启、节点是否可用
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import socket

try:
    import yt_dlp
except ImportError:
    print('未安装 yt-dlp，请先执行：')
    print('    .venv/Scripts/python -m pip install -U yt-dlp')
    sys.exit(1)

# 屏蔽 "Deprecated Feature: Support for Python version 3.10..." 提示：
# 虚拟环境是 Python 3.10，yt-dlp 每次实例化都会提醒一遍，且该提示无视 no_warnings
# 直接走 stderr。纯提醒、不影响功能，屏蔽之（真实 ERROR 不受影响）
yt_dlp.YoutubeDL.deprecated_feature = lambda self, message: None


# ============ 配置区 ============

# 下载目录：锚定到脚本所在目录（不管从哪里启动，文件都存在同一处）
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'downloads_tiktok')
MAX_HEIGHT = 1080                           # 批量任务（主页/话题）的画质上限（None = 不限制）
                                            # 单条链接不受此限，会弹出画质选择菜单
MAX_DURATION = None                         # 批量任务只下载短于该秒数的视频（None = 不限制）
                                            # 单条链接不受此限（既然手动指定了，就下）
AUDIO_ONLY = False                          # True = 只下载音频（mp3，需 ffmpeg）
MAX_RETRIES = 3                             # 外层重试次数
REQUEST_INTERVAL = 1                        # 批量任务每次请求间隔秒数（防限流）

# 常见本地代理端口（Clash / v2ray 等）
PROXY_PORTS = [7897, 7890, 7891, 10809, 1080]
PROXY_HOST = '127.0.0.1'


# ============ 代理检测 ============

def detect_proxy():
    """依次探测常见代理端口，返回可用的代理地址；探测不到返回 None（走直连）"""
    for port in PROXY_PORTS:
        try:
            with socket.create_connection((PROXY_HOST, port), timeout=1):
                proxy = f'http://{PROXY_HOST}:{port}'
                print(f'[代理] 检测到本地代理：{proxy}')
                return proxy
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


def get_proxy():
    """决定使用哪个代理：有本地代理用代理，否则测直连"""
    proxy = detect_proxy()
    if proxy:
        return proxy
    if can_direct_connect():
        print('[代理] 直连可用')
        return None
    print('[代理] ⚠️ 无代理且无法直连 TikTok，请先开启 Clash 等代理工具再运行')
    return None


# ============ 下载进度 ============

def make_progress_hook():
    """生成进度回调，显示下载百分比和速度"""
    state = {}

    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            done = d.get('downloaded_bytes', 0)
            if total:
                pct = done / total * 100
                speed = d.get('speed') or 0
                speed_str = f'{speed / 1024 / 1024:.2f} MB/s' if speed else '…'
                print(f"\r  下载中 {pct:5.1f}%  {speed_str}", end='', flush=True)
        elif d['status'] == 'finished':
            print('\r  下载完成，正在处理…                ')
        state['last'] = d['status']

    hook.state = state
    return hook


# ============ 核心选项 ============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIR, 'cookies_tiktok.txt')  # 手动导出的 Cookie 文件

# TikTok 登录态 Cookie 特征（有 sessionid = 已登录）
LOGIN_COOKIE_NAMES = {'sessionid'}

# TikTok 的视频是"混合流"（音视频合在一个 mp4 里，不像 YouTube 分离），
# 所以格式语法用 best[...]，不用 bestvideo+bestaudio。
# download_addr = TikTok 官方带水印转码流 → 默认避开；CDN 原始流（play_addr/
# bytevc1_xxx / h264_xxx 等）没有水印 → 优先选。
NO_WATERMARK = '[format_id!*=download_addr]'
FMT_BEST = f'best{NO_WATERMARK}/best'


def build_opts(proxy, cookie_browser=None, cookie_file=None):
    """构建 yt-dlp 选项；cookie_browser / cookie_file 用于携带登录 Cookie"""
    fmt = ('bestaudio/best' if AUDIO_ONLY
           else (f'best[height<={MAX_HEIGHT}]{NO_WATERMARK}/best[height<={MAX_HEIGHT}]/best'
                 if MAX_HEIGHT else FMT_BEST))

    opts = {
        # 画质：优先无水印、限定高度，失败降级到任意最佳
        'format': fmt,
        # 文件名：标题 [视频ID].扩展名，标题截断 60 字符避免文件名过长
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).60s [%(id)s].%(ext)s'),
        # 音频模式转 mp3
        'postprocessors': ([{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
                           if AUDIO_ONLY else []),
        # 重试（网络分片级别）
        'retries': 5,
        'fragment_retries': 10,
        # 批量任务中单条失败不中断
        'ignoreerrors': True,
        # 请求间隔：TikTok 对高频请求限流很凶，批量时放慢一点稳得多
        'sleep_interval_requests': REQUEST_INTERVAL,
        # 跳过已存在文件（断点续传）
        'overwrites': False,
        'continuedl': True,
        # 时长过滤：跳过超过 MAX_DURATION 秒的视频
        'match_filter': (yt_dlp.utils.match_filter_func(f'duration<{MAX_DURATION}')
                         if MAX_DURATION else None),
        # 进度显示
        'progress_hooks': [make_progress_hook()],
        # 代理
        'proxy': proxy,
        # 杂项
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    if cookie_file:
        # 用手动导出的 cookies.txt（最稳，新版 Chrome/Edge 加密读不了时的首选）
        opts['cookiefile'] = cookie_file
    elif cookie_browser:
        # 借用浏览器的 TikTok 登录 Cookie
        opts['cookiesfrombrowser'] = (cookie_browser,)
    return opts


import contextlib


@contextlib.contextmanager
def suppress_stderr():
    """临时屏蔽 stderr（探测浏览器 Cookie 时 yt-dlp 会刷一堆无害的 ERROR）"""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old = os.dup(2)
    os.dup2(devnull, 2)
    try:
        yield
    finally:
        os.dup2(old, 2)
        os.close(old)
        os.close(devnull)


def _try_cookie_opts(opts):
    """用给定 opts 实例化 yt-dlp，检查 cookiejar 里是否有 TikTok 登录态。成功返回 True"""
    ydl = None
    try:
        ydl = yt_dlp.YoutubeDL(opts)
        for c in ydl.cookiejar:  # cookiejar 是惰性加载，访问时才可能抛异常
            if 'tiktok' in (c.domain or '') and c.name in LOGIN_COOKIE_NAMES:
                return True
        return False
    except Exception:
        return False
    finally:
        if ydl is not None:
            try:
                ydl.close()
            except Exception:
                pass


def resolve_cookies(base_opts):
    """
    决定 Cookie 来源，优先级：
    1. 脚本同目录的 cookies_tiktok.txt（手动导出，最稳）
    2. 各浏览器的登录 Cookie（Firefox 成功率最高）
    返回 (cookie_browser, cookie_file)
    """
    # 方案 1：cookies_tiktok.txt（独立命名，跟 YouTube 的 cookies.txt 互不干扰）
    if os.path.exists(COOKIE_FILE):
        opts = dict(base_opts)
        opts['cookiefile'] = COOKIE_FILE
        with suppress_stderr():
            ok = _try_cookie_opts(opts)
        if ok:
            print('[Cookie] 已使用 cookies_tiktok.txt（含 TikTok 登录态）✓')
            return None, COOKIE_FILE
        print('[Cookie] ⚠️ 找到 cookies_tiktok.txt 但读取失败或无登录态，已忽略')

    # 方案 2：浏览器 Cookie（静默探测，失败不刷屏）
    # Firefox 排最前：新版 Chrome/Edge 的加密 (app-bound encryption) 大概率读取失败
    for browser in ('firefox', 'edge', 'chrome', 'brave'):
        opts = dict(base_opts)
        opts['cookiesfrombrowser'] = (browser,)
        with suppress_stderr():
            ok = _try_cookie_opts(opts)
        if ok:
            print(f'[Cookie] 已启用 {browser} 浏览器的 TikTok 登录 Cookie ✓')
            return browser, None

    # 都没有：不打扰用户 —— 无 Cookie 大多数情况也能下载，被限流了再说
    print('[Cookie] 未携带登录 Cookie（单条视频一般不影响，批量拉主页可能被限流）')
    return None, None


# ============ 输入解析 ============

def normalize_target(user_input):
    """
    把用户输入统一处理成 yt-dlp 能识别的目标：
    - cURL 命令 → 提取里面的 TikTok 链接
    - 去掉 URL 后面误粘贴的参数
    """
    text = user_input.strip()

    # cURL 命令：提取第一个 TikTok 链接
    if text.lower().startswith('curl '):
        m = re.search(r'https?://[^\s\'"]+', text)
        if m:
            return m.group(1).rstrip('\\')
        return text

    # 直接给的链接：只保留到路径部分，去掉跟踪参数（is_from_webapp 等）
    if 'tiktok.com' in text:
        m = re.search(r'(https?://[^\s\'"]+tiktok\.com/[^\s\'"?]+)', text)
        if m:
            return m.group(1)

    return text


def is_single_video(target):
    """判断目标是不是单条视频/图集链接（而非主页/话题页）"""
    if re.search(r'tiktok\.com/@[^/]+/(video|photo)/\d+', target):
        return True
    # 分享短链也当单条视频处理（重定向后就是单条）
    if re.search(r'(vm|vt)\.tiktok\.com/', target):
        return True
    return False


def choose_quality(info):
    """
    列出该视频所有可选画质，让用户挑选。
    返回 (画质描述, yt-dlp 格式字符串)；
    用户主动放弃返回 ('quit', None)；解析不出画质返回 (None, None)
    """
    # 从格式列表里收集"有画面"的分辨率 → 估算大小、宽高、有无无水印版本
    heights = {}
    for f in info.get('formats') or []:
        if not f.get('height') or f.get('vcodec') == 'none':
            continue
        h = f['height']
        size = f.get('filesize') or f.get('filesize_approx')
        clean = 'download_addr' not in (f.get('format_id') or '')  # 非水印流
        old = heights.get(h)
        if old is None:
            heights[h] = (size, f.get('width'), clean)
        else:
            old_size, old_w, old_clean = old
            if (clean and not old_clean) or \
               (clean == old_clean and size and (not old_size or size > old_size)):
                heights[h] = (max(size or 0, old_size or 0) or None, old_w,
                              clean or old_clean)
    if not heights:
        return None, None  # 解析不出画质列表，让调用方走默认格式

    sorted_h = sorted(heights)
    print('\n🎛  请选择画质：')
    print('   0. 最佳画质（回车默认，优先无水印）')
    for i, h in enumerate(sorted_h, 1):
        size, w, clean = heights[h]
        size_str = f'（约 {size / 1024 / 1024:.0f} MB）' if size else ''
        mark = '' if clean else ' ⚠️仅带水印'
        # 竖屏视频按短边（宽）标注画质：1080×1920 → 1080p 竖屏
        label = f'{min(w, h)}p 竖屏' if (w and w < h) else f'{h}p'
        print(f'   {i}. {label}{size_str}{mark}')
    print('   a. 仅音频 mp3   q. 放弃下载')

    while True:
        try:
            choice = input(f'   选择 [0-{len(sorted_h)}/a/q] > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'quit', None
        if choice in ('', '0'):
            return '最佳画质', FMT_BEST
        if choice == 'a':
            return '仅音频 mp3', 'bestaudio/best'
        if choice == 'q':
            return 'quit', None
        if choice.isdigit() and 1 <= int(choice) <= len(sorted_h):
            h = sorted_h[int(choice) - 1]
            w = heights[h][1]
            # 优先该高度的无水印流，没有再回退带水印版
            fmt = (f'best[height={h}]{NO_WATERMARK}/best[height<={h}]{NO_WATERMARK}'
                   f'/best[height<={h}]/best')
            # 竖屏按短边（宽）标注画质：1080×1920 → 1080p
            label = f'{min(w, h)}p' if (w and w < h) else f'{h}p'
            return label, fmt
        print('   输入无效，请重新选择')


def extract_info_quiet(target, opts, full=False):
    """解析目标信息。full=True 时解析完整格式列表（单条视频选画质需要）"""
    probe = dict(opts)
    probe.pop('match_filter', None)   # 预览/选画质阶段不做时长过滤
    if not full:
        probe['extract_flat'] = True
    with yt_dlp.YoutubeDL(probe) as ydl:
        return ydl.extract_info(target, download=False)


def report_extract_error(msg):
    """打印解析失败的分类提示"""
    print(f'❌ 获取视频信息失败：{msg[:200]}')
    if 'Login required' in msg or 'login' in msg.lower():
        print('   → TikTok 要求登录（未登录拉取被限制）！')
        print('     解决：浏览器登录 TikTok 后导出 Cookie：')
        print('        1. 浏览器装扩展「Get cookies.txt LOCALLY」')
        print('        2. 打开 tiktok.com（保持登录）→ 点扩展导出')
        print(f'        3. 重命名为 cookies_tiktok.txt 放到 {SCRIPT_DIR} → 重启脚本')
        return 'abort'
    elif 'HTTP Error 429' in msg or 'Too Many Requests' in msg:
        print('   → 请求太频繁被限流，稍等几分钟再试（批量任务可调大 REQUEST_INTERVAL）')
    elif 'not available' in msg.lower() or 'private' in msg.lower():
        print('   → 视频可能已删除 / 设为私密')
        return 'abort'
    else:
        print('   （常见原因：代理没开 / 链接无效 / 视频已删除）')
    return 'retry'


def cleanup_intermediates():
    """删除 yt-dlp 合并后残留的 .fNNN 中间分片文件"""
    import glob
    import time
    for _ in range(3):                      # 合并刚结束时文件可能还被占用，稍等重试
        leftovers = [p for p in glob.glob(os.path.join(DOWNLOAD_DIR, '*.*'))
                     if re.search(r'\.f\d+\.[a-z0-9]+$', p, re.IGNORECASE)]
        if not leftovers:
            return
        for path in leftovers:
            try:
                os.remove(path)
                print(f'  🧹 清理中间文件：{os.path.basename(path)}')
            except OSError:
                pass                        # 被占用，等下一轮
        time.sleep(0.5)


def report_saved_files(video_id):
    """按视频 ID 找到下载成品，打印完整路径，方便用户直接定位"""
    import glob
    # 文件名模板是 "标题 [视频ID].ext"，glob 的 [] 是特殊字符，必须转义
    pattern = os.path.join(DOWNLOAD_DIR, '*' + glob.escape(f'[{video_id}]') + '.*')
    saved = [p for p in glob.glob(pattern) if not re.search(r'\.f\d+\.', p)]
    for p in saved:
        size_mb = os.path.getsize(p) / 1024 / 1024
        print(f'💾 已保存：{p}（{size_mb:.1f} MB）')
    if not saved:
        print(f'💾 文件保存在：{DOWNLOAD_DIR}')


def run_download(target, opts):
    """
    执行下载。
    返回：'ok' 成功 / 'retry' 可重试的失败 / 'abort' 无需重试的失败（需登录等）
    """
    print(f'\n▶ 目标：{target}')
    print('=' * 60)

    # ---------- 分支一：单条视频 → 完整解析 + 画质选择菜单 ----------
    if is_single_video(target):
        try:
            # full=True：需要完整格式列表才能列出画质菜单
            info = extract_info_quiet(target, opts, full=True)
        except yt_dlp.utils.DownloadError as e:
            return report_extract_error(str(e))

        if not info:
            print('❌ 未解析到视频信息（链接可能已删除）')
            return 'abort'

        dur = info.get('duration')
        dur_str = f'{int(dur)}s' if dur else '?'
        print(f'  标题：{info.get("title", "?")}')
        print(f'  时长：{dur_str}   作者：{info.get("uploader", "?")}')

        quality, fmt = choose_quality(info)
        if quality == 'quit':
            print('↩ 已放弃，不下载')
            return 'ok'
        if not fmt:
            # 解析不出画质列表 → 走默认格式
            quality, fmt = '默认画质', opts.get('format', 'best')

        final_opts = dict(opts)
        final_opts['format'] = fmt
        final_opts.pop('match_filter', None)  # 手动指定的视频不做时长过滤
        if quality == '仅音频 mp3':
            final_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio',
                                             'preferredcodec': 'mp3'}]
        print(f'\n⬇ 开始下载（{quality}）…')
        try:
            with yt_dlp.YoutubeDL(final_opts) as ydl:
                ydl.download([target])
            cleanup_intermediates()
            print('✅ 下载完成！')
            report_saved_files(info.get('id', ''))
            return 'ok'
        except yt_dlp.utils.DownloadError as e:
            print(f'❌ 下载出错：{str(e)[:200]}')
            return 'retry'

    # ---------- 分支二：批量目标（主页/话题） → 预览 + 按上限下载 ----------
    try:
        info = extract_info_quiet(target, opts, full=False)
    except yt_dlp.utils.DownloadError as e:
        return report_extract_error(str(e))

    if info and 'entries' in info:
        entries = [e for e in info['entries'] if e]
        if not entries:
            print('❌ 一条视频都没拿到：多半是未登录被限流，按上方 Cookie 提示导出后重试')
            return 'abort'
        n_will_skip = sum(1 for e in entries
                          if MAX_DURATION and e.get('duration')
                          and e['duration'] > MAX_DURATION)
        print(f'共发现 {len(entries)} 条视频'
              + (f'（其中 {n_will_skip} 条超时长将被跳过）' if n_will_skip else '') + '：')
        for i, e in enumerate(entries[:10], 1):
            dur = e.get('duration')
            dur_str = f'{int(dur)}s' if dur else '?'
            skip = bool(MAX_DURATION and dur and dur > MAX_DURATION)
            print(f'  {i:>3}. [{dur_str}] {str(e.get("title", "?"))[:50]}'
                  + (' ⇣跳过' if skip else ''))
        if len(entries) > 10:
            print(f'  … 以及另外 {len(entries) - 10} 条')

    # ---------- 正式下载（应用时长过滤 + 画质上限） ----------
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([target])
        cleanup_intermediates()
        print('✅ 全部完成！')
        print(f'💾 文件保存在：{DOWNLOAD_DIR}')
        return 'ok'
    except yt_dlp.utils.DownloadError as e:
        print(f'❌ 下载出错：{str(e)[:200]}')
        return 'retry'


# ============ 主循环 ============

def main():
    print('=' * 60)
    print('   TikTok 视频批量下载器（yt-dlp 版）')
    print('=' * 60)
    print(f'保存目录：{os.path.abspath(DOWNLOAD_DIR)}')
    print(f'批量任务画质上限：{"仅音频 mp3" if AUDIO_ONLY else (f"{MAX_HEIGHT}p" if MAX_HEIGHT else "不限制")}'
          '（单条链接会弹画质菜单自选）')
    if MAX_DURATION:
        print(f'时长过滤：仅下载短于 {MAX_DURATION} 秒的视频（配置区 MAX_DURATION 可改）')
    print()
    print('支持的输入：')
    print('  1. 视频链接    https://www.tiktok.com/@用户名/video/xxxx')
    print('  2. 分享短链    https://vm.tiktok.com/xxxx/')
    print('  3. 用户主页    https://www.tiktok.com/@用户名')
    print('  4. 话题标签页  https://www.tiktok.com/tag/关键词')
    print('  5. cURL 命令   （从浏览器 DevTools 复制）')
    print('  输入 q 退出')
    print()

    proxy = get_proxy()
    cookie_browser, cookie_file = resolve_cookies(build_opts(proxy))
    opts = build_opts(proxy, cookie_browser, cookie_file)

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

        target = normalize_target(user_input)
        for attempt in range(1, MAX_RETRIES + 1):
            result = run_download(target, opts)
            if result in ('ok', 'abort'):
                break
            if attempt < MAX_RETRIES:
                print(f'… 第 {attempt} 次失败，重试（{attempt}/{MAX_RETRIES}）')
            else:
                print('❌ 重试次数用完，跳过该目标')

        print('=' * 60)


if __name__ == '__main__':
    main()
