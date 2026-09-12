"""
YouTube 短视频批量下载器（基于 yt-dlp）

支持的输入格式：
1. 单条视频 / Shorts 链接
   https://www.youtube.com/watch?v=xxxx
   https://www.youtube.com/shorts/xxxx
   https://youtu.be/xxxx
2. 频道的全部 Shorts
   https://www.youtube.com/@频道名/shorts
3. 播放列表
   https://www.youtube.com/playlist?list=xxxx
4. 关键字搜索（自动下载搜索结果）
   search:猫咪搞笑 20        ← 下载前 20 条
   search:猫咪搞笑           ← 默认下载前 10 条

使用方法：
1. 直接运行：python YouTube-downloader.py
2. 把链接或搜索词粘贴进去，回车开始下载
3. 单条视频链接：先显示视频信息，再弹画质菜单（列出该视频实际可用的画质）
4. 频道/播放列表/搜索：先列出视频预览，再弹同一套画质菜单（通用画质阶梯）
5. 画质菜单统一操作：回车/0 = 最佳画质；数字 = 选对应画质；
   a = 仅音频 mp3；q = 放弃下载
6. 视频保存到 downloads_youtube/ 目录
7. 输入 q 退出

特点：
- 自动检测系统代理（Clash 7897/7890 等），也支持直连
- 自动识别 Cookie：优先 cookies.txt，其次浏览器（Firefox 成功率最高）；
  没有 Cookie 一般也能下载，被机器人验证拦截时按提示导出即可
- 单条/批量任务共用同一套画质选择菜单（回车=最佳画质，a=仅音频 mp3）
- 自动跳过已下载的视频（断点续传）
- 单条失败不中断批量任务
- 失败自动重试（yt-dlp 内置 + 外层重试）
- 软封禁熔断：连续多条 "Video unavailable" 时自动停止批量任务并给出提示
  （批量下载几百条后节点 IP 被 YouTube 限流，所有视频都会报 unavailable）
- 熔断后续爬：换 Clash 节点 → 回一个回车 → 按下载档案秒跳已完成的视频，从断点继续

⚠️ 机器人验证（"Sign in to confirm you're not a bot"）：
这是代理出口 IP 被 YouTube 标记导致的。先换个 Clash 节点；
还不行就导出登录 Cookie：
1. 浏览器装扩展「Get cookies.txt LOCALLY」，打开 youtube.com（保持登录）导出
2. 把导出的 cookies.txt 放到本脚本同目录，重启脚本自动识别
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
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
                            'downloads_youtube')
MAX_HEIGHT = 720                            # 画质菜单解析失败时的兜底上限（None = 不限制）
                                            # 正常流程以下载前弹出的统一画质菜单为准
MAX_DURATION = 180                          # 批量任务只下载短于该秒数的视频（None = 不限制）
                                            # 单条链接不受此限（既然手动指定了，就下）
AUDIO_ONLY = False                          # True = 只下载音频（mp3）
MAX_RETRIES = 3                             # 外层重试次数
UNAVAILABLE_BREAK = 8                       # 批量下载中连续多少条 "Video unavailable" 就熔断停止
                                            # （连续大量不可用 = 当前节点 IP 被 YouTube 软封禁，
                                            #   继续挨个试只会刷屏浪费时间）
REQUEST_INTERVAL = 0.5                      # 每次请求间隔（秒），降低触发限流的概率；0 = 关闭

# 下载档案：记录已成功下载的视频 ID。重跑同一频道/列表时，
# 已下载的条目在「解析之前」就被跳过 → 熔断后换节点回车续爬时秒级断点续传
ARCHIVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'downloaded_youtube.txt')

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
    """测试能否直连 YouTube"""
    try:
        with socket.create_connection(('www.youtube.com', 443), timeout=5):
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
    print('[代理] ⚠️ 无代理且无法直连 YouTube，请先开启 Clash 等代理工具再运行')
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
            print('\r  下载完成，正在合并/处理…          ')
        state['last'] = d['status']

    hook.state = state
    return hook


# ============ 核心选项 ============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIR, 'cookies.txt')  # 手动导出的 Cookie 文件

# YouTube 登录态 Cookie 特征（有任意一个 = 已登录）
LOGIN_COOKIE_NAMES = {'SID', 'SAPISID', 'LOGIN_INFO'}

# 客户端伪装策略：
# - tv_embedded：能拿到完整画质列表（144p~2160p），画质选择菜单全靠它
# - android：兜底。只发一个 360p 混合格式（YouTube 的 SABR 限制），
#   但部分网络环境下 tv_embedded 失败时它还能用
# ⚠️ 两者不能写进同一个 player_client 列表：android 会污染格式列表导致只剩 360p
PRIMARY_CLIENTS = ['tv_embedded']
FALLBACK_CLIENTS = ['android']


def build_opts(proxy, cookie_browser=None, cookie_file=None, player_clients=None):
    """构建 yt-dlp 选项；cookie_browser / cookie_file 用于携带登录 Cookie"""
    if player_clients is None:
        player_clients = PRIMARY_CLIENTS
    fmt = ('bestaudio/best' if AUDIO_ONLY else fmt_for_height(MAX_HEIGHT))

    opts = {
        # 画质：优先限定高度的视频+音频合并，失败降级到最佳
        'format': fmt,
        # 文件名：标题 [视频ID].扩展名，标题截断 60 字符避免文件名过长
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).60s [%(id)s].%(ext)s'),
        # 合并容器
        'merge_output_format': 'mp4',
        # 音频模式转 mp3
        'postprocessors': ([{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
                           if AUDIO_ONLY else []),
        # 重试（网络分片级别）
        'retries': 5,
        'fragment_retries': 10,
        # 批量任务中单条失败不中断
        'ignoreerrors': True,
        # 不下载直播流
        'live_from_start': False,
        # 跳过已存在文件（断点续传）
        'overwrites': False,
        'continuedl': True,
        # 下载档案：记录已下载 ID，重跑时跳过（配合熔断续爬实现秒级断点）
        'download_archive': ARCHIVE_FILE,
        # 时长过滤：跳过超过 MAX_DURATION 秒的长视频
        'match_filter': (yt_dlp.utils.match_filter_func(f'duration<{MAX_DURATION}')
                         if MAX_DURATION else None),
        # 进度显示
        'progress_hooks': [make_progress_hook()],
        # 代理
        'proxy': proxy,
        # 客户端伪装（见顶部 PRIMARY_CLIENTS / FALLBACK_CLIENTS 说明）
        'extractor_args': {'youtube': {'player_client': list(player_clients)}},
        # 请求间隔：降低连续请求被 YouTube 限流的概率
        'sleep_interval_requests': (REQUEST_INTERVAL if REQUEST_INTERVAL > 0 else None),
        # 杂项
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    if cookie_file:
        # 用手动导出的 cookies.txt（最稳，新版 Chrome/Edge 加密读不了时的首选）
        opts['cookiefile'] = cookie_file
    elif cookie_browser:
        # 借用浏览器的 YouTube 登录 Cookie，绕过 bot 验证
        opts['cookiesfrombrowser'] = (cookie_browser,)
    return opts


import contextlib
import re
import sys


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


class FloodGuard:
    """
    软封禁熔断器（自定义 yt-dlp logger）。

    现象：批量下载约 300 条后，当前代理节点 IP 被 YouTube 限流，
    之后每条视频的解析都返回 "Video unavailable"（封禁的伪装形式），
    yt-dlp 在 ignoreerrors 下会把剩下几百条挨个试一遍 → ERROR 刷屏。

    对策：
    - 统计连续 "Video unavailable" 条数（每当有视频下载成功就清零）
    - 达到阈值直接抛 DownloadCancelled 熔断整个批量任务
    - bot 验证拦截更是直接熔断（继续试毫无意义）
    """

    def __init__(self, limit):
        self.limit = limit
        self.streak = 0          # 连续不可用计数
        self.shown = 0           # 已完整打印的错误条数（前几条照常显示，后面静默）

    def reset(self, d=None):
        """下载成功回调：清零连续计数"""
        if d is None or d.get('status') == 'finished':
            self.streak = 0

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        msg = str(msg)
        # bot 验证：节点被标记，立即熔断
        if 'Sign in to confirm' in msg or 'not a bot' in msg:
            raise yt_dlp.utils.DownloadCancelled(
                'YouTube 机器人验证拦截，批量任务已熔断')
        if 'Video unavailable' in msg or 'Private video' in msg:
            self.streak += 1
            if self.shown < 3:
                print(f'  [跳过] {msg}')
                self.shown += 1
            elif self.streak == self.limit:
                print(f'  … 连续 {self.streak} 条视频不可用，熔断停止本次批量任务')
            if self.streak >= self.limit:
                raise yt_dlp.utils.DownloadCancelled(
                    f'连续 {self.streak} 条视频 unavailable（疑似节点 IP 被软封禁）')
        else:
            print(f'  [错误] {msg}')


def _try_cookie_opts(opts):
    """用给定 opts 实例化 yt-dlp 并检查是否有 YouTube 登录态。成功返回 True"""
    ydl = None
    try:
        ydl = yt_dlp.YoutubeDL(opts)
        names = {c.name for c in ydl.cookiejar}  # cookiejar 是惰性加载，访问时才可能抛异常
        return bool(names & LOGIN_COOKIE_NAMES)
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
    1. 脚本同目录的 cookies.txt（手动导出，最稳）
    2. 各浏览器的登录 Cookie（Firefox 成功率最高）
    返回 (cookie_browser, cookie_file)
    """
    # 方案 1：cookies.txt
    if os.path.exists(COOKIE_FILE):
        opts = dict(base_opts)
        opts['cookiefile'] = COOKIE_FILE
        with suppress_stderr():
            ok = _try_cookie_opts(opts)
        if ok:
            print('[Cookie] 已使用 cookies.txt（含 YouTube 登录态）✓')
            return None, COOKIE_FILE
        print('[Cookie] ⚠️ 找到 cookies.txt 但读取失败或无登录态，已忽略')

    # 方案 2：浏览器 Cookie（静默探测，失败不刷屏）
    # Firefox 排最前：新版 Chrome/Edge 的加密 (app-bound encryption) 大概率读取失败
    for browser in ('firefox', 'edge', 'chrome', 'brave'):
        opts = dict(base_opts)
        opts['cookiesfrombrowser'] = (browser,)
        with suppress_stderr():
            ok = _try_cookie_opts(opts)
        if ok:
            print(f'[Cookie] 已启用 {browser} 浏览器的 YouTube 登录 Cookie ✓')
            return browser, None

    # 都没有：不打扰用户 —— 无 Cookie 大多数情况也能下载，被拦截了再说
    print('[Cookie] 未携带登录 Cookie（一般不影响，被机器人验证拦截时再导出）')
    return None, None


def normalize_target(user_input):
    """
    把用户输入统一处理成 yt-dlp 能识别的目标：
    - search:关键词 [数量] → ytsearchN:关键词
    - 其他 URL 原样返回
    """
    text = user_input.strip()
    if text.lower().startswith('search:'):
        rest = text[7:].strip()
        parts = rest.rsplit(None, 1)
        if len(parts) == 2 and parts[1].isdigit():
            keyword, count = parts[0], int(parts[1])
        else:
            keyword, count = rest, 10
        return f'ytsearch{count}:{keyword}'
    return text


def is_single_video(target):
    """判断目标是不是单条视频链接（而非搜索/频道/播放列表）"""
    if target.startswith('ytsearch'):
        return False
    if 'list=' in target:          # 播放列表
        return False
    if '/@' in target or '/channel/' in target or '/c/' in target:
        return False               # 频道页
    return any(k in target for k in ('watch?v=', '/shorts/', 'youtu.be/'))


def fmt_for_height(h):
    """
    按画质数值生成格式串（横竖屏通吃）。
    ⚠️ Shorts 是竖屏：720p 竖屏的实际分辨率是 720×1280（宽=720，高=1280），
    如果按 height<=720 过滤，竖屏 720p（高 1280）根本匹配不上，只会选到 360p！
    所以：
    1) 先按宽度精确匹配（竖屏的短边 = 画质数值）
    2) 再按高度精确匹配（横屏的高度 = 画质数值）
    3) 都没有（该视频没这个画质）→ 不限画质，选最佳
    """
    return (f'bestvideo[width={h}]+bestaudio/'
            f'bestvideo[height={h}]+bestaudio/'
            f'bestvideo+bestaudio/best')


def choose_quality(info=None):
    """
    统一的画质选择菜单（单条链接 / 批量任务共用同一套）。
    - 传入 info（单条视频）：列出该视频实际可用的画质（含大小估算）
    - 不传 info（批量任务）：列出通用画质阶梯
    统一操作：回车/0 = 最佳画质；数字 = 对应画质；a = 仅音频 mp3；q = 放弃。
    返回 (画质描述, yt-dlp 格式字符串)；
    用户主动放弃返回 ('quit', None)；解析不出画质返回 (None, None)
    """
    if info is not None:
        # 从格式列表里收集"有画面"的分辨率 → 估算大小、宽高
        heights = {}
        for f in info.get('formats') or []:
            if not f.get('height') or f.get('vcodec') == 'none':
                continue
            h = f['height']
            size = f.get('filesize') or f.get('filesize_approx')
            old = heights.get(h)
            if old is None or (size and (not old[0] or size > old[0])):
                heights[h] = (size, f.get('width'))
    else:
        # 批量任务：通用画质阶梯（不逐条解析格式，速度快）
        heights = {h: (None, None) for h in (360, 480, 720, 1080, 1440, 2160)}
    if not heights:
        return None, None  # 解析不出画质列表，让调用方走默认格式

    sorted_h = sorted(heights)
    print('\n🎛  请选择画质：')
    print('   0. 最佳画质（回车默认）')
    for i, h in enumerate(sorted_h, 1):
        size, w = heights[h]
        size_str = f'（约 {size / 1024 / 1024:.0f} MB）' if size else ''
        # 竖屏视频（Shorts）按短边（宽）标注画质：1080×1920 → 1080p 竖屏
        label = f'{min(w, h)}p 竖屏' if (w and w < h) else f'{h}p'
        print(f'   {i}. {label}{size_str}')
    print('   a. 仅音频 mp3   q. 放弃下载')

    while True:
        try:
            choice = input(f'   选择 [0-{len(sorted_h)}/a/q] > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'quit', None
        if choice in ('', '0'):
            return '最佳画质', 'bestvideo+bestaudio/best'
        if choice == 'a':
            return '仅音频 mp3', 'bestaudio/best'
        if choice == 'q':
            return 'quit', None
        if choice.isdigit() and 1 <= int(choice) <= len(sorted_h):
            h = sorted_h[int(choice) - 1]
            w = heights[h][1]
            # 竖屏按短边（宽）标注画质：1080×1920 → 1080p
            label_h = min(w, h) if (w and w < h) else h
            return f'{label_h}p', fmt_for_height(label_h)
        print('   输入无效，请重新选择')


def extract_with_fallback(target, opts_list, full=False):
    """
    依次尝试 opts_list 里的客户端配置解析目标。
    full=True 时解析完整格式列表（单条视频选画质需要）；否则只取列表级元数据（快）。
    返回 (info, 成功使用的opts)；全部失败抛最后一个 DownloadError
    """
    last_err = None
    for o in opts_list:
        probe = dict(o)
        probe.pop('match_filter', None)   # 预览/选画质阶段不做时长过滤
        if not full:
            probe['extract_flat'] = True
        try:
            with yt_dlp.YoutubeDL(probe) as ydl:
                return ydl.extract_info(target, download=False), o
        except yt_dlp.utils.DownloadError as e:
            last_err = e
    raise last_err


def report_extract_error(msg):
    """打印解析失败的分类提示"""
    print(f'❌ 获取视频信息失败：{msg[:200]}')
    if 'Sign in to confirm' in msg or 'not a bot' in msg:
        print('   → YouTube 机器人验证拦截（当前节点 IP 被标记）！')
        print('     解决：① 先换个 Clash 节点再试；② 或导出登录 Cookie：')
        print('        浏览器装扩展「Get cookies.txt LOCALLY」→ 打开 youtube.com（保持登录）')
        print(f'        → 点导出 → 把 cookies.txt 放到 {SCRIPT_DIR} → 重启脚本')
        return 'abort'
    elif 'HTTP Error 429' in msg:
        print('   → 请求太频繁被限流，稍等几分钟再试')
    else:
        print('   （常见原因：代理没开 / 链接无效）')
    return 'retry'


def cleanup_intermediates():
    """删除 yt-dlp 音视频合并后残留的 .fNNN 中间分片文件"""
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


def run_download(target, opts, fallback_opts):
    """
    执行下载。
    返回：'ok' 成功 / 'retry' 可重试的失败 / 'abort' 无需重试的失败（bot 验证等）
    """
    print(f'\n▶ 目标：{target}')
    print('=' * 60)

    # ---------- 分支一：单条视频 → 完整解析 + 画质选择菜单 ----------
    if is_single_video(target):
        try:
            # full=True：需要完整格式列表才能列出画质菜单
            info, used_opts = extract_with_fallback(
                target, [opts, fallback_opts], full=True)
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
            # 解析不出画质列表（如 android 兜底客户端只有混合格式）→ 走默认格式
            quality, fmt = '默认画质', used_opts.get('format', 'best')

        final_opts = dict(used_opts)
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

    # ---------- 分支二：批量目标（频道/列表/搜索） → 预览 + 按上限下载 ----------
    try:
        info, used_opts = extract_with_fallback(
            target, [opts, fallback_opts], full=False)
    except yt_dlp.utils.DownloadError as e:
        return report_extract_error(str(e))

    if info and 'entries' in info:
        entries = [e for e in info['entries'] if e]
        n_will_skip = sum(1 for e in entries
                          if MAX_DURATION and e.get('duration')
                          and e['duration'] > MAX_DURATION)
        print(f'共发现 {len(entries)} 条视频'
              + (f'（其中 {n_will_skip} 条超时长将被跳过）' if n_will_skip else '') + '：')
        for i, e in enumerate(entries[:10], 1):
            dur = e.get('duration')
            dur_str = f'{int(dur)}s' if dur else '?'
            skip = bool(MAX_DURATION and dur and dur > MAX_DURATION)
            print(f'  {i:>3}. [{dur_str}] {e.get("title", "?")[:50]}'
                  + (' ⇣跳过' if skip else ''))
        if len(entries) > 10:
            print(f'  … 以及另外 {len(entries) - 10} 条')

    # ---------- 选画质（与单条视频同一套菜单） ----------
    quality, fmt = choose_quality()
    if quality == 'quit':
        print('↩ 已放弃，不下载')
        return 'ok'
    if not fmt:
        # 解析不出画质列表 → 走默认格式（配置区 MAX_HEIGHT 兜底）
        quality, fmt = '默认画质', used_opts.get('format', 'best')

    final_opts = dict(used_opts)
    final_opts['format'] = fmt
    if quality == '仅音频 mp3':
        final_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio',
                                         'preferredcodec': 'mp3'}]
    base_hooks = list(final_opts.get('progress_hooks') or [])
    print(f'\n⬇ 开始批量下载（{quality}）…')

    # ---------- 正式下载（应用时长过滤 + 画质上限） ----------
    # 熔断后续传循环：换节点 → 回车 → 用下载档案秒跳已下载的，从断点继续
    while True:
        # 软封禁熔断器：连续大量 unavailable 时停止批量，不再刷屏硬扛
        guard = FloodGuard(UNAVAILABLE_BREAK)
        final_opts['logger'] = guard
        final_opts['progress_hooks'] = base_hooks + [guard.reset]
        try:
            with yt_dlp.YoutubeDL(final_opts) as ydl:
                ydl.download([target])
            cleanup_intermediates()
            print('✅ 全部完成！')
            print(f'💾 文件保存在：{DOWNLOAD_DIR}')
            return 'ok'
        except yt_dlp.utils.DownloadCancelled as e:
            print(f'⛔ 熔断：{e}')
            print('   大概率是当前节点 IP 被 YouTube 限流。请先在 Clash 切换节点')
            print('   （或等十几分钟让限流解除；导出 cookies.txt 登录态会更稳）。')
            try:
                choice = input('   ↵ 回车 = 已换节点，继续下载剩余视频 | s = 跳过该目标 | q = 退出程序 > ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return 'abort'
            if choice == 'q':
                print('再见！')
                return 'exit'
            if choice == 's':
                return 'abort'
            print('↩ 继续下载剩余视频…（已下载的部分按档案秒级跳过）\n')
        except yt_dlp.utils.DownloadError as e:
            print(f'❌ 下载出错：{str(e)[:200]}')
            return 'retry'


# ============ 主循环 ============

def main():
    print('=' * 60)
    print('   YouTube 短视频批量下载器（yt-dlp 版）')
    print('=' * 60)
    print(f'保存目录：{os.path.abspath(DOWNLOAD_DIR)}')
    print('下载前会弹统一画质菜单：回车 = 最佳画质，也可选 360p~4K 或仅音频 mp3')
    if MAX_DURATION:
        print(f'时长过滤：仅下载短于 {MAX_DURATION} 秒的视频（配置区 MAX_DURATION 可改）')
    print()
    print('支持的输入：')
    print('  1. 视频链接    https://www.youtube.com/shorts/xxxx')
    print('  2. 频道 Shorts  https://www.youtube.com/@频道名/shorts')
    print('  3. 播放列表    https://www.youtube.com/playlist?list=xxxx')
    print('  4. 关键字搜索  search:猫咪搞笑 20')
    print('  输入 q 退出')
    print()

    proxy = get_proxy()
    cookie_browser, cookie_file = resolve_cookies(build_opts(proxy))
    opts = build_opts(proxy, cookie_browser, cookie_file, PRIMARY_CLIENTS)
    fallback_opts = build_opts(proxy, cookie_browser, cookie_file, FALLBACK_CLIENTS)

    while True:
        try:
            user_input = input('📥 请输入链接或搜索词 > ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break

        if not user_input:
            continue
        if user_input.lower() in ('q', 'quit', 'exit'):
            print('再见！')
            break

        target = normalize_target(user_input)
        result = None
        try:
            for attempt in range(1, MAX_RETRIES + 1):
                result = run_download(target, opts, fallback_opts)
                if result in ('ok', 'abort', 'exit'):
                    break
                if attempt < MAX_RETRIES:
                    print(f'… 第 {attempt} 次失败，重试（{attempt}/{MAX_RETRIES}）')
                else:
                    print('❌ 重试次数用完，跳过该目标')
        except KeyboardInterrupt:
            print('\n↩ 已中断当前任务（程序继续运行）')
        except Exception as e:
            print(f'❌ 发生未预期的错误（已拦截，程序继续运行）：{type(e).__name__}: {e}')

        if result == 'exit':
            break

        print('=' * 60)


if __name__ == '__main__':
    main()
