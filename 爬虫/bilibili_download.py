"""
Bilibili 视频下载器（交互式，支持单条 / UP主空间批量 / 多链接批量）

交互设计参考 YouTube-downloader.py：
    运行 → 显示保存目录 → 处理登录 Cookie → 循环接收输入 → 每条都弹统一画质菜单

支持的输入：
    1. 单个视频：BV 号 / 视频链接（长短视频都一样）
       BV1xx411c7mD
       https://www.bilibili.com/video/BV1xx411c7mD
       https://b23.tv/xxxxxxx            （短链自动跟随跳转）
    2. UP 主空间批量：一次抓取 TA 的全部投稿
       https://space.bilibili.com/349594717
       https://space.bilibili.com/349594717/video
    3. 多链接批量：一行里放多个 BV / 链接（空格、逗号、分号分隔），
       或让脚本循环接收、逐个粘贴
    4. CDN 直链：F12 Network 里复制的 upos-/bilivideo 直链

画质菜单（单条 / 批量同一套操作）：
    0 或回车 = 最佳画质    数字 = 对应画质    a = 仅音频 mp3    q = 放弃本条
    单条视频会列出「该视频实际可用的画质 + 体积估算」；
    批量任务列出通用画质阶梯（1080P / 4K / …），服务端无该档时自动回落。

其他：
    - Cookie 只在本次运行内使用（输入→校验→内存里用，退出即丢弃），
      不写入本地文件（B 站 Cookie 会失效，存了反而可能用到过期的）
    - 批量任务带下载档案 downloaded_bilibili.txt，重跑时跳过已下载（断点续传）
    - 单条失败不中断批量；批量每条之间有间隔，降低触发风控的概率
    - 下载 dash 视频/音频流后自动用 ffmpeg 无损合并成 mp4

用法：
    python bilibili_download.py                    # 交互式（推荐）
    python bilibili_download.py BV1xx411c7mD       # 直接下这一条
    python bilibili_download.py --cookie "SESSDATA=xxx"
"""

import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import os
import re
import time
import json
import shutil
import hashlib
import argparse
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print('缺少 requests，请在项目虚拟环境里安装：')
    print('    D:/pycharm/Person-Practice/.venv/Scripts/python.exe -m pip install requests')
    sys.exit(1)


# ============================================================
#  配置区
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'downloads'                  # 下载产物（已在 .gitignore）
TEMP_ROOT = OUTPUT_DIR / '.temp'                     # dash 音视频临时文件
ARCHIVE_FILE = BASE_DIR / 'downloaded_bilibili.txt'  # 下载档案（断点续传）
COOKIE_FILE = BASE_DIR / '.bili_cookie'              # 与直播录制器共用登录态

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

REQUEST_INTERVAL = 1.2      # 批量任务中每条视频之间的间隔（秒），降低触发风控概率
SPACE_PAGE_INTERVAL = 3.0   # 空间投稿翻页间隔（秒）——翻太快必触发 -352 风控
API_TIMEOUT = 30            # API 读超时（15s 在 CDN 忙时会出现 Read timed out）
API_RETRIES = 3             # 瞬时网络错误（超时/连接中断）自动重试次数
CHUNK = 1 << 16
PROGRESS_INTERVAL = 3.0     # 下载进度每隔几秒打印一行（新行打印，PyCharm 控制台也能看见）

# 空目录 / 不留垃圾：这些都是音视频临时文件的前缀
TEMP_PREFIX = '.temp'

# 画质编号 → 名称（B 站 qn 映射）
QN_NAME = {
    127: '8K 超高清', 126: '杜比视界', 125: 'HDR 真彩',
    120: '4K 超清', 116: '1080P 60帧', 112: '1080P 高码率',
    100: '智能修复', 80: '1080P 高清', 74: '720P 60帧',
    64: '720P 高清', 32: '480P 清晰', 16: '360P 流畅', 6: '240P 极速',
}
# 批量任务的画质上限阶梯（从高到低；每条视频实际取「不超过上限的最高可用档」）
BATCH_LADDER = [127, 120, 116, 112, 80, 74, 64, 32, 16]

# wbi 签名用的混淆表（B 站前端固定常量）
MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


# ============================================================
#  小工具
# ============================================================

def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} PB'


def human_duration(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:d}:{s:02d}'


def sanitize(name, max_len=60):
    """清理成合法文件名"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', '_', str(name)).strip(' .')
    name = re.sub(r'\s+', ' ', name)
    return name[:max_len] or '未命名'


def has_ffmpeg():
    return shutil.which('ffmpeg') is not None


def progress_printer(label, total_bytes):
    """
    进度打印器 —— 每 PROGRESS_INTERVAL 秒打一行新记录。
    ⚠️ 不用 \\r 原地刷新：PyCharm Run 控制台对 \\r 支持差，会把整行吞掉。
    """
    state = {'t': time.time(), 'start': time.time(), 'last': -1}

    def update(done):
        now = time.time()
        if done == state['last']:
            return                      # 同一进度不重复打印（收尾时会再调一次）
        if now - state['t'] < PROGRESS_INTERVAL and (total_bytes and done < total_bytes):
            return
        state['t'] = now
        state['last'] = done
        speed = done / max(now - state['start'], 0.001)
        if total_bytes:
            pct = done / total_bytes * 100
            print(f'    ⬇ {label} {pct:5.1f}%  {human_size(done)}/{human_size(total_bytes)}'
                  f'  {human_size(speed)}/s', flush=True)
        else:
            print(f'    ⬇ {label} {human_size(done)}  {human_size(speed)}/s', flush=True)

    return update


# ============================================================
#  Cookie
# ============================================================

def load_saved_cookie():
    try:
        txt = COOKIE_FILE.read_text(encoding='utf-8').strip()
        return txt or None
    except OSError:
        return None


def save_cookie(cookie):
    try:
        COOKIE_FILE.write_text(cookie.strip(), encoding='utf-8')
        return True
    except OSError as exc:
        print(f'    ⚠️  Cookie 保存失败：{exc}')
        return False


def normalize_cookie(raw):
    """
    把各种姿势的粘贴归一成 SESSDATA=xxx：
    - 只贴 SESSDATA 的值            → 自动补 SESSDATA=
    - F12 整行复制（名字和值用 Tab 分隔）→ SESSDATA⇥值 转成 SESSDATA=值
    - 完整 Cookie 串（含分号）       → 原样保留
    """
    raw = raw.strip().strip('"').strip("'").replace('\r', '')
    if not raw:
        return ''
    # F12 → Application 里复制整行，名字和值之间是 Tab
    if '\t' in raw:
        parts = [x.strip() for x in raw.split('\t') if x.strip()]
        if len(parts) == 2 and '=' not in raw:
            raw = f'{parts[0]}={parts[1]}'
        else:
            raw = ''.join(parts)
    if '=' in raw and ';' in raw:
        return raw
    key = raw.split('=', 1)[0].strip().lower() if '=' in raw else ''
    if key in ('sessdata', 'bili_jct', 'dedeuserid', 'buvid3'):
        return raw
    return f'SESSDATA={raw}'


# ============================================================
#  下载器
# ============================================================

class BiliDownloader:
    """B 站视频下载器（requests + ffmpeg 内核）"""

    def __init__(self, cookie=None, proxy=None):
        self.cookie = cookie or None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': UA,
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        if proxy:
            # 被风控（-352/-412）时走本地代理换 IP，例如 Clash: http://127.0.0.1:7897
            self.session.proxies = {'http': proxy, 'https': proxy}
            print(f'🛡 已启用代理：{proxy}')
        self._mixin = None
        self._mixin_at = 0
        if self.cookie:
            # 已登录：设备指纹（buvid3 等）用 Cookie 里自带的那套，不再去主站另领，
            # 避免「匿名 buvid3 + 登录 Cookie」混在一起被风控判定为异常
            self.set_cookie(self.cookie)
        else:
            # 未登录才去主站领 buvid3 设备 Cookie（缺了会被风控 412）
            try:
                self.session.get('https://www.bilibili.com/', timeout=API_TIMEOUT)
            except requests.RequestException:
                pass

    def set_cookie(self, cookie):
        """Cookie 解析进 cookie jar（真实浏览器就是这么带的，比拼裸 Cookie 头稳）"""
        self.cookie = cookie or None
        self.session.headers.pop('Cookie', None)
        self.session.cookies.clear()
        if cookie:
            for kv in cookie.split(';'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    self.session.cookies.set(k.strip(), v.strip(), domain='.bilibili.com')

    # ---------- 登录态 ----------

    def _get_json_retry(self, url, *, params=None, headers=None, tries=API_RETRIES):
        """
        GET JSON，带瞬时错误重试。
        只对超时 / 连接中断这类「网络抖动」重试；接口返回错误码不重试。
        """
        last = None
        for attempt in range(1, tries + 1):
            try:
                r = self.session.get(url, params=params, headers=headers,
                                     timeout=API_TIMEOUT)
                return r.json()
            except (requests.Timeout, requests.ConnectionError) as exc:
                last = exc
                if attempt < tries:
                    wait = 3 * attempt
                    print(f'    ⚠️  网络抖动（{type(exc).__name__}），{wait}s 后重试'
                          f'（第 {attempt}/{tries - 1} 次）…', flush=True)
                    time.sleep(wait)
        raise last

    def login_check(self):
        """返回 (是否登录, 用户名或失败原因)"""
        try:
            r = self.session.get('https://api.bilibili.com/x/web-interface/nav',
                                 timeout=API_TIMEOUT).json()
            d = r.get('data') or {}
            if d.get('isLogin'):
                return True, d.get('uname') or '已登录用户'
            return False, '未登录（Cookie 无效或已过期）'
        except Exception as exc:
            return False, f'校验失败：{type(exc).__name__}'

    # ---------- wbi 签名（空间接口必需） ----------

    def _mixin_key(self):
        """取 wbi 混淆密钥，缓存 1 小时（密钥每天轮换）"""
        if self._mixin and time.time() - self._mixin_at < 3600:
            return self._mixin
        d = self.session.get('https://api.bilibili.com/x/web-interface/nav',
                             timeout=API_TIMEOUT).json().get('data') or {}
        img = (d.get('wbi_img') or {}).get('img_url', '').rsplit('/', 1)[-1].split('.')[0]
        sub = (d.get('wbi_img') or {}).get('sub_url', '').rsplit('/', 1)[-1].split('.')[0]
        if not img or not sub:
            raise RuntimeError('无法获取 wbi 密钥（nav 接口异常）')
        raw = img + sub
        self._mixin = ''.join(raw[i] for i in MIXIN_TAB)[:32]
        self._mixin_at = time.time()
        return self._mixin

    def _sign(self, params):
        """给参数加 wts + dm 反爬字段 + w_rid 签名"""
        import random
        import string
        p = dict(params)
        p['wts'] = str(int(time.time()))
        # dm_* 是 B 站前端的「行为验证」字段，缺了空间接口会 412 或返回空列表
        p.setdefault('dm_img_list', '[]')
        p.setdefault('dm_img_str', ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)))
        p.setdefault('dm_cover_img_str', ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)))
        p.setdefault('dm_img_inter', '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}')
        p = dict(sorted(p.items()))
        # 值里不能带 !'()* 这些字符
        clean = {k: re.sub(r"[!'()*]", '', str(v)) for k, v in p.items()}
        query = urllib.parse.urlencode(clean)
        p['w_rid'] = hashlib.md5((query + self._mixin_key()).encode()).hexdigest()
        return p

    # ---------- 视频信息 ----------

    def get_video_info(self, bvid):
        r = self.session.get('https://api.bilibili.com/x/web-interface/view',
                             params={'bvid': bvid}, timeout=API_TIMEOUT).json()
        if r.get('code') != 0:
            raise RuntimeError(f"{r.get('code')} {r.get('message') or '获取视频信息失败'}")
        d = r['data']
        return {
            'bvid': bvid,
            'title': d.get('title') or '无标题',
            'owner': ((d.get('owner') or {}).get('name')) or '未知UP',
            'duration': d.get('duration') or 0,
            'pic': d.get('pic'),
            'pages': [{'cid': p.get('cid'), 'part': p.get('part') or f"P{i+1}",
                       'duration': p.get('duration') or 0}
                      for i, p in enumerate(d.get('pages') or [])],
        }

    def get_w_webid(self, mid):
        """
        从 UP 主空间页 HTML 里挖 w_webid。
        空间投稿接口现在除了 wbi 签名还要求带 w_webid（B 站加的反爬），
        缺了会返回 -352「风控校验失败」。拿不到时返回空串（靠重试碰运气）。
        """
        try:
            r = self.session.get(f'https://space.bilibili.com/{mid}/video',
                                 headers={'Referer': 'https://www.bilibili.com/'},
                                 timeout=API_TIMEOUT)
            m = (re.search(r'"w_webid":"([^"]+)"', r.text)
                 or re.search(r'w_webid["\']?\s*[:=]\s*["\']([^"\']+)', r.text))
            if m:
                return m.group(1)
        except requests.RequestException:
            pass
        return ''

    def get_space_videos(self, mid, limit=None, quiet=False):
        """
        抓 UP 主全部投稿（wbi 签名 + 分页）。返回 [{bvid,title,duration,pages}]
        limit 不为空时最多抓这么多条
        """
        items, page = [], 1
        total = None
        w_webid = self.get_w_webid(mid)         # 空间页反爬字段，缺了会 -352
        while True:
            params = self._sign({
                'mid': str(mid), 'order': 'pubdate', 'pn': str(page), 'ps': '30',
                'platform': 'web', 'web_location': '1550101', 'w_webid': w_webid,
            })
            r = self._get_json_retry('https://api.bilibili.com/x/space/wbi/arc/search',
                                     params=params,
                                     headers={'Referer': f'https://space.bilibili.com/{mid}/video'})
            # 风控自救：-352=校验失败 / -412=IP 被封。逐级加码重试：
            # ① 等 8s 换 w_webid ② 等 15s 再换 ③ 自动接本机代理换 IP 最后一把
            for wait, use_proxy in ((8, False), (15, False), (10, True)):
                if r.get('code') not in (-352, -412):
                    break
                if use_proxy:
                    if self.session.proxies:
                        break                         # 已经在代理上了，再试也没用
                    clash = detect_clash_proxy()
                    if not clash:
                        break                         # 没有代理可用
                    self.session.proxies = {'http': clash, 'https': clash}
                    print(f'    🛡 自动改走本机代理 {clash} 换 IP…', flush=True)
                print(f'    ⚠️  空间接口被风控（{r.get("code")}），等待 {wait}s 后重试…', flush=True)
                time.sleep(wait)
                w_webid = self.get_w_webid(mid)
                r = self._get_json_retry('https://api.bilibili.com/x/space/wbi/arc/search',
                                         params=self._sign({
                                             'mid': str(mid), 'order': 'pubdate',
                                             'pn': str(page), 'ps': '30',
                                             'platform': 'web', 'web_location': '1550101',
                                             'w_webid': w_webid,
                                         }),
                                         headers={'Referer': f'https://space.bilibili.com/{mid}/video'})
            if r.get('code') != 0:
                raise RuntimeError(f"空间接口返回 {r.get('code')} "
                                   f"{r.get('message') or ''}".strip())
            d = r.get('data') or {}
            vlist = ((d.get('list') or {}).get('vlist')) or []
            if total is None:
                total = ((d.get('page') or {}).get('count')) or len(vlist)
            if not vlist:
                break
            for v in vlist:
                items.append({
                    'bvid': v.get('bvid'),
                    'title': v.get('title') or '无标题',
                    'duration': parse_length(v.get('length')),
                    'created': v.get('created'),
                })
            if not quiet:
                print(f'    · 已抓取 {len(items)}/{total} 条…', flush=True)
            if len(vlist) < 30:
                break
            if limit and len(items) >= limit:
                break
            page += 1
            time.sleep(SPACE_PAGE_INTERVAL)
        # 接口默认最新在前 → 反转成由旧到新（从 UP 主最早的视频开始下）
        items.sort(key=lambda x: x.get('created') or 0)
        if limit:
            items = items[:limit]
        return items

    def get_uploader_name(self, mid):
        try:
            r = self.session.get('https://api.bilibili.com/x/space/wbi/acc/info',
                                 params=self._sign({'mid': str(mid)}),
                                 timeout=API_TIMEOUT).json()
            if r.get('code') == 0:
                return (r.get('data') or {}).get('name')
        except Exception:
            pass
        return None

    # ---------- 取流 ----------

    def get_play_url(self, bvid, cid, qn=127):
        """返回 dash（视频/音频分离）或 durl（未登录降级）信息"""
        params = {'bvid': bvid, 'cid': cid, 'qn': qn, 'fnval': 16, 'fnver': 0,
                  'fourk': 1, 'platform': 'pc', 'otype': 'json', 'high_quality': 1}
        r = self.session.get('https://api.bilibili.com/x/player/playurl',
                             params=params, timeout=API_TIMEOUT).json()
        if r.get('code') != 0:
            raise RuntimeError(f"{r.get('code')} {r.get('message') or '取流失败'}")
        d = r.get('data') or {}

        if d.get('dash'):
            dash = d['dash']
            videos = [{
                'qn': v.get('id'), 'bandwidth': v.get('bandwidth') or 0,
                'codecs': v.get('codecs') or '', 'width': v.get('width') or 0,
                'height': v.get('height') or 0, 'frame_rate': v.get('frameRate'),
                'url': v.get('baseUrl') or (v.get('base_url')),
                'backup': v.get('backupUrl') or v.get('backup_url') or [],
            } for v in (dash.get('video') or [])]
            audios = [{
                'bandwidth': a.get('bandwidth') or 0, 'codecs': a.get('codecs') or '',
                'url': a.get('baseUrl') or (a.get('base_url')),
                'backup': a.get('backupUrl') or a.get('backup_url') or [],
            } for a in (dash.get('audio') or [])]
            return {'format': 'dash', 'duration': dash.get('duration') or 0,
                    'video_streams': videos, 'audio_streams': audios,
                    'quality': d.get('quality')}

        if d.get('durl'):
            return {'format': 'durl', 'duration': (d.get('timelength') or 0) // 1000,
                    'segments': [{'url': x.get('url'), 'backup': x.get('backup_url') or [],
                                  'size': x.get('size') or 0} for x in d['durl']],
                    'quality': d.get('quality')}

        raise RuntimeError('接口未返回可用流（可能需要登录 Cookie）')

    # ---------- 下载 ----------

    def fetch(self, url, out_path, label, backup=None):
        """下载单个流，失败自动尝试备用 CDN 地址"""
        urls = [url] + list(backup or [])
        last = None
        for i, u in enumerate(urls):
            try:
                if i:
                    print(f'    ↻ 主节点连不上（{type(last).__name__}），换备用节点（{i}）…',
                          flush=True)
                return self._fetch_one(u, out_path, label)
            except Exception as exc:
                last = exc
        raise last if last else RuntimeError('下载失败')

    def _fetch_one(self, url, out_path, label):
        headers = {'Referer': 'https://www.bilibili.com/', 'Origin': 'https://www.bilibili.com'}
        host = re.sub(r'^https?://', '', url).split('/')[0]
        print(f'    ⬇ {label}：连接 {host} …', flush=True)
        with self.session.get(url, headers=headers, stream=True, timeout=(10, 30)) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get('Content-Length') or 0)
            m = re.match(r'bytes \d+-\d+/(\d+)', resp.headers.get('Content-Range') or '')
            if m:
                total = int(m.group(1))
            update = progress_printer(label, total)
            done = 0
            tmp = out_path.with_suffix(out_path.suffix + '.part')
            with open(tmp, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=CHUNK):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        update(done)
            update(total or done)
            tmp.replace(out_path)
        return out_path


# ============================================================
#  解析输入
# ============================================================

def parse_length(text):
    """把 "1:44" / "10:05" / "1:02:03" 解析成秒"""
    if not text:
        return 0
    text = str(text).strip()
    if text.isdigit():
        return int(text)
    parts = text.split(':')
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    sec = 0
    for n in nums:
        sec = sec * 60 + n
    return sec


def parse_mid(text):
    m = re.search(r'space\.bilibili\.com/(\d+)', text)
    return int(m.group(1)) if m else None


def extract_bvids(text):
    """从任意文本里抽出所有 BV 号（去重保序）"""
    out = []
    for m in re.finditer(r'BV[0-9A-Za-z]{10}', text):
        if m.group(0) not in out:
            out.append(m.group(0))
    return out


def is_cdn_url(text):
    return bool(re.search(r'(upos-|bilivideo\.com|akamaized\.net/mp4)', text))


def is_short_link(text):
    return bool(re.match(r'https?://b23\.tv/\S+', text.strip()))


def expand_short_link(session, url):
    try:
        r = session.get(url, allow_redirects=True, timeout=API_TIMEOUT)
        return r.url
    except requests.RequestException as exc:
        print(f'    ⚠️  短链展开失败：{exc}')
        return url


# ============================================================
#  画质菜单
# ============================================================

def group_streams(video_streams, duration):
    """
    把 dash 视频流按画质档位归并：
    同一档有 avc/hevc/av01 多个编码，优先留 avc（兼容性最好），
    并估算该档体积（码率 × 时长 / 8）
    """
    best = {}
    for s in video_streams:
        qn = s.get('qn')
        old = best.get(qn)
        prefer_new = False
        if old is None:
            prefer_new = True
        else:
            old_avc = str(old.get('codecs', '')).startswith('avc')
            new_avc = str(s.get('codecs', '')).startswith('avc')
            if new_avc and not old_avc:
                prefer_new = True
            elif new_avc == old_avc and s.get('bandwidth', 0) > old.get('bandwidth', 0):
                prefer_new = True
        if prefer_new:
            best[qn] = s
    rows = []
    for qn, s in best.items():
        est = (s.get('bandwidth') or 0) * max(duration or 0, 1) / 8
        rows.append((qn, s, est))
    rows.sort(key=lambda x: x[0], reverse=True)
    return rows


def choose_quality_single(play_info, duration):
    """
    单条视频：列出该视频真实可用的画质。
    返回 ('video', stream) / ('audio', None) / ('quit', None) / (None, None)
    """
    if play_info['format'] == 'durl':
        print('\n🎛  该视频只有渐进式（durl）流，无法选画质，将直接下载')
        return 'video', None

    rows = group_streams(play_info.get('video_streams') or [], duration)
    if not rows:
        return None, None

    print('\n🎛  请选择画质：')
    print(f'   0. 最佳画质（{QN_NAME.get(rows[0][0], str(rows[0][0]))}，回车默认）')
    for i, (qn, s, est) in enumerate(rows, 1):
        name = QN_NAME.get(qn, f'qn={qn}')
        fps = ''
        try:                                    # frameRate 可能是 '30.000' 这种字符串
            fr = float(s.get('frame_rate') or 0)
            fps = f' {int(fr)}fps' if fr >= 50 else ''
        except (TypeError, ValueError):
            pass
        size = f'（约 {human_size(est)}）' if est else ''
        print(f'   {i}. {name}{fps}  {s.get("width")}x{s.get("height")} '
              f'{s.get("codecs")}  {(s.get("bandwidth") or 0)//1000}kbps {size}')
    print('   a. 仅音频 mp3   q. 放弃这条')

    while True:
        try:
            c = input(f'   选择 [0-{len(rows)}/a/q] > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'quit', None
        if c in ('', '0'):
            return 'video', rows[0][1]
        if c == 'a':
            return 'audio', None
        if c == 'q':
            return 'quit', None
        if c.isdigit() and 1 <= int(c) <= len(rows):
            return 'video', rows[int(c) - 1][1]
        print('   输入无效，请重新选择')


def choose_quality_batch():
    """批量任务：画质上限菜单。返回 ('video', qn) / ('audio', None) / ('quit', None)"""
    print('\n🎛  请选择画质上限（批量任务统一使用）：')
    print('   ℹ️  每个视频实际拥有的档位不同（有的最高 1080P，有的只有 720P），')
    print('      会自动取「不超过上限的实际最高档」，下载时逐条报告实得画质。')
    print('   0. 不设上限（每条视频都取它自己的最高档，回车默认）')
    for i, qn in enumerate(BATCH_LADDER, 1):
        print(f'   {i}. {QN_NAME.get(qn, qn)}')
    print('   a. 仅音频 mp3   q. 放弃本次批量')
    print('   💡 未登录时最高只能到 1080P（多数账号 480P），更高档位需要登录 Cookie')
    while True:
        try:
            c = input(f'   选择 [0-{len(BATCH_LADDER)}/a/q] > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'quit', None
        if c in ('', '0'):
            return 'video', BATCH_LADDER[0]
        if c == 'a':
            return 'audio', None
        if c == 'q':
            return 'quit', None
        if c.isdigit() and 1 <= int(c) <= len(BATCH_LADDER):
            return 'video', BATCH_LADDER[int(c) - 1]
        print('   输入无效，请重新选择')


def pick_streams(play_info, qn=None, want_stream=None):
    """
    从取流结果里挑出要下载的流。
    pick_streams(play, qn=120)        → 批量：挑不超过 120 的最高档
    pick_streams(play, want_stream=v) → 单条：已选定具体流对象
    返回 (video_stream, audio_stream)
    """
    if play_info['format'] == 'durl':
        return None, None

    if want_stream is not None:
        v = want_stream
    else:
        videos = play_info.get('video_streams') or []
        if not videos:
            return None, None
        limit = qn if qn else 999
        ok = [s for s in videos if (s.get('qn') or 0) <= limit]
        pool = ok or videos
        top_qn = max((s.get('qn') or 0) for s in pool)
        pool = [s for s in pool if (s.get('qn') or 0) == top_qn]
        avc = [s for s in pool if str(s.get('codecs', '')).startswith('avc')]
        pool = avc or pool
        v = max(pool, key=lambda s: s.get('bandwidth') or 0)

    audios = play_info.get('audio_streams') or []
    a = None
    if audios:
        mp4a = [x for x in audios if 'mp4a' in str(x.get('codecs', ''))]
        a = max(mp4a or audios, key=lambda x: x.get('bandwidth') or 0)
    return v, a


# ============================================================
#  下载档案（断点续传）
# ============================================================

def archive_load():
    try:
        return {ln.strip() for ln in ARCHIVE_FILE.read_text(encoding='utf-8').splitlines() if ln.strip()}
    except OSError:
        return set()


def archive_add(bvid):
    try:
        with open(ARCHIVE_FILE, 'a', encoding='utf-8') as f:
            f.write(bvid + '\n')
    except OSError:
        pass


# ============================================================
#  下载流程
# ============================================================

def merge_av(video_path, audio_path, out_path):
    """dash 音视频无损合并成 mp4"""
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-i', str(video_path), '-i', str(audio_path),
           '-c', 'copy', '-movflags', '+faststart', str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=1800)
    return r.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0


def to_mp3(src_path, out_path):
    """仅音频模式：转成 mp3"""
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-i', str(src_path), '-vn', '-c:a', 'libmp3lame', '-q:a', '2', str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=1800)
    if r.returncode != 0 or not out_path.exists():
        print(f'    ⚠️  mp3 转码失败，保留原始音频流：{src_path.name}')
        return src_path
    return out_path


def download_one(d, info, page, quality, qn=None, want_stream=None,
                 audio_only=False, out_stem=None):
    """
    下载单个视频的单个分P。
    quality: 'video' / 'audio'；want_stream 为单条流程选定的具体流
    返回产物路径，失败抛异常
    """
    bvid = info['bvid']
    cid = page['cid']
    play = d.get_play_url(bvid, cid, qn=qn or 127)
    v, a = pick_streams(play, qn=qn, want_stream=want_stream)

    temp_dir = TEMP_ROOT / bvid
    temp_dir.mkdir(parents=True, exist_ok=True)

    if out_stem is None:
        out_stem = f"{sanitize(info['title'])} [{bvid}]"

    # 渐进式 durl：直接下，未登录也能用
    if play['format'] == 'durl':
        seg = (play.get('segments') or [None])[0]
        if not seg:
            raise RuntimeError('没有可用分片')
        got = play.get('quality')
        print(f'    🎞 实得画质：{QN_NAME.get(got, got or "?")}', flush=True)
        out = OUTPUT_DIR / f'{out_stem}.mp4'
        d.fetch(seg['url'], out, '本片', seg.get('backup'))
        if audio_only and has_ffmpeg():
            out = to_mp3(out, OUTPUT_DIR / f'{out_stem}.mp3')
        return out

    if v is None:
        raise RuntimeError('未取到视频流')

    # 实得画质报告（单条模式：报告的是你刚选中的那一档；批量模式：报告实际落档）
    if v is not None:
        got_qn = v.get('qn') or 0
        got_name = QN_NAME.get(got_qn, f'qn={got_qn}')
        if want_stream is not None:
            print(f'    🎞 本次下载画质：{got_name}（{v.get("width")}x{v.get("height")}）', flush=True)
        else:
            msg = f'    🎞 实得画质：{got_name}（{v.get("width")}x{v.get("height")}）'
            if qn and qn < 127 and got_qn < qn:
                msg += f'　· 该视频最高就这档，未到所选上限 {QN_NAME.get(qn, qn)}'
            print(msg, flush=True)

    if audio_only:
        if not a:
            raise RuntimeError('未取到音频流')
        src = temp_dir / 'audio.m4s'
        d.fetch(a['url'], src, '音频', a.get('backup'))
        out = OUTPUT_DIR / f'{out_stem}.mp3'
        if has_ffmpeg():
            out = to_mp3(src, out)
        else:
            out = OUTPUT_DIR / f'{out_stem}.m4a'
            shutil.move(str(src), str(out))
        shutil.rmtree(temp_dir, ignore_errors=True)
        return out

    vpath = temp_dir / 'video.m4s'
    d.fetch(v['url'], vpath, '视频', v.get('backup'))

    apath = None
    if a:
        apath = temp_dir / 'audio.m4s'
        d.fetch(a['url'], apath, '音频', a.get('backup'))

    out = OUTPUT_DIR / f'{out_stem}.mp4'
    if apath and has_ffmpeg():
        print('    🔗 合并音视频…', flush=True)
        if not merge_av(vpath, apath, out):
            print('    ⚠️  合并失败，仅保留视频流')
            shutil.move(str(vpath), str(out))
    else:
        if a and not has_ffmpeg():
            print('    ⚠️  未找到 ffmpeg，只保存视频画面（无声音）')
        shutil.move(str(vpath), str(out))

    shutil.rmtree(temp_dir, ignore_errors=True)
    return out


def report_saved(path):
    if path and path.exists():
        print(f'💾 已保存：{path}（{human_size(path.stat().st_size)}）')


# ---------- 单条流程 ----------

def run_single(d, bvid, no_cookie_hint=True):
    print(f'\n{"=" * 62}')
    print(f'  🔍 解析视频 {bvid}')
    info = d.get_video_info(bvid)
    print(f'  标题：{info["title"]}')
    print(f'  UP主：{info["owner"]}    时长：{human_duration(info["duration"])}'
          f'    分P：{len(info["pages"])}')

    # 分P 菜单
    pages = info['pages']
    if len(pages) > 1:
        print('\n📑 该视频有多个分P：')
        for i, p in enumerate(pages, 1):
            print(f'   {i}. {p["part"]}（{human_duration(p["duration"])}）')
        print('   a. 全部分P   q. 放弃')
        while True:
            try:
                c = input(f'   选择 [1-{len(pages)}/a/q] > ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if c == 'q':
                print('↩ 已放弃')
                return
            if c == 'a':
                selected = pages
                break
            if c.isdigit() and 1 <= int(c) <= len(pages):
                selected = [pages[int(c) - 1]]
                break
            print('   输入无效，请重新选择')
    else:
        selected = pages

    # 用第一个分P探画质（同视频各P画质档位一般一致）
    probe = d.get_play_url(bvid, selected[0]['cid'], qn=127)
    quality, want = choose_quality_single(probe, info['duration'])
    if quality == 'quit':
        print('↩ 已放弃')
        return
    if quality is None:
        print('   ⚠️  未解析到画质列表，使用最佳画质')
        quality, want = 'video', None

    audio_only = quality == 'audio'
    multi = len(selected) > 1
    for page in selected:
        stem = f"{sanitize(info['title'])} [{bvid}]"
        if multi:
            stem += f" P{selected.index(page) + 1}_{sanitize(page['part'], 30)}"
        print(f'\n⬇ 开始下载（{"仅音频 mp3" if audio_only else "视频"}）…')
        try:
            out = download_one(d, info, page, quality,
                               qn=(want or {}).get('qn') if False else None,
                               want_stream=want, audio_only=audio_only, out_stem=stem)
        except Exception as exc:
            print(f'   ❌ 下载失败：{type(exc).__name__}: {exc}')
            if no_cookie_hint and not d.cookie:
                print('      💡 部分画质/视频需要登录 Cookie，可输入 c 命令补充 Cookie 后重试')
            continue
        report_saved(out)
        if multi and len(selected) > 1:
            print(f'   （进度 {selected.index(page) + 1}/{len(selected)}）')
    archive_add(bvid)


# ---------- 批量流程 ----------

def run_batch(d, items, title):
    """
    items: [{'bvid','title','duration'}]（空间抓取的直接可用）
    单条失败不中断；已下载的按档案跳过
    """
    archive = archive_load()
    todo = [x for x in items if x['bvid'] not in archive]
    skipped = len(items) - len(todo)
    print(f'\n📦 {title}：共 {len(items)} 条'
          + (f'，其中 {skipped} 条此前已下载（跳过）' if skipped else ''))
    for i, x in enumerate(todo[:10], 1):
        print(f'   {i:>3}. [{human_duration(x.get("duration"))}] {x["title"][:44]}')
    if len(todo) > 10:
        print(f'   … 以及另外 {len(todo) - 10} 条')

    if not todo:
        print('✅ 没有需要下载的内容')
        return

    quality, qn = choose_quality_batch()
    if quality == 'quit':
        print('↩ 已放弃本次批量')
        return
    audio_only = quality == 'audio'

    print(f'\n⬇ 开始批量下载（{"仅音频 mp3" if audio_only else "画质上限：" + QN_NAME.get(qn, str(qn))}，逐条取实际最高档）…')
    ok = fail = 0
    failed_items = []
    for i, x in enumerate(todo, 1):
        print(f'\n[{i}/{len(todo)}] {x["title"][:50]}')
        try:
            info = d.get_video_info(x['bvid'])
            pages = info['pages']
            if len(pages) > 1:
                print(f'   ℹ️  该视频有 {len(pages)} 个分P，批量模式只下第 1P')
            page = pages[0]
            stem = f"{sanitize(info['title'])} [{info['bvid']}]"
            out = download_one(d, info, page, quality, qn=qn, audio_only=audio_only,
                               out_stem=stem)
            report_saved(out)
            archive_add(info['bvid'])
            ok += 1
        except KeyboardInterrupt:
            print('\n↩ 已中断本次批量（已下载的内容不受影响）')
            break
        except Exception as exc:
            failed_items.append(x)
            print(f'   ❌ 失败：{type(exc).__name__}: {exc}')
            if not d.cookie:
                print('      💡 这类失败常因登录态缺失，可输入 c 命令补充 Cookie')
        time.sleep(REQUEST_INTERVAL)

    # ---- 失败补抓：瞬时网络错误（超时等）最后统一再试一遍 ----
    if failed_items:
        print(f'\n🔁 有 {len(failed_items)} 条失败，稍候自动重试一轮…')
        time.sleep(3)
        retried_ok = 0
        still_failed = []
        for j, x in enumerate(failed_items, 1):
            print(f'\n[重试 {j}/{len(failed_items)}] {x["title"][:50]}')
            try:
                info = d.get_video_info(x['bvid'])
                page = info['pages'][0]
                stem = f"{sanitize(info['title'])} [{info['bvid']}]"
                out = download_one(d, info, page, quality, qn=qn, audio_only=audio_only,
                                   out_stem=stem)
                report_saved(out)
                archive_add(info['bvid'])
                retried_ok += 1
            except KeyboardInterrupt:
                print('\n↩ 已中断重试（已下载的内容不受影响）')
                break
            except Exception as exc:
                still_failed.append((x, exc))
                print(f'   ❌ 仍失败：{type(exc).__name__}: {exc}')
            time.sleep(REQUEST_INTERVAL)
        ok += retried_ok
        fail = len(still_failed)
        if still_failed:
            print('\n📝 重试后仍失败的条目（下次运行会按档案自动补下）:')
            for x, exc in still_failed:
                print(f'   · [{x["bvid"]}] {x["title"][:40]} — {type(exc).__name__}')

    print(f'\n{"=" * 62}')
    print(f'📊 批量结束：成功 {ok} 条，失败 {fail} 条')
    print(f'💾 文件保存在：{OUTPUT_DIR}')


def run_space_batch(d, mid):
    print(f'\n🔍 正在抓取 UP 主空间投稿（mid={mid}）…')
    name = d.get_uploader_name(mid)
    try:
        items = d.get_space_videos(mid)
    except Exception as exc:
        print(f'❌ 抓取失败：{type(exc).__name__}: {exc}')
        if '-412' in str(exc):
            print('   🚫 当前 IP 已被 B 站临时拉黑（请求太频繁），继续重试只会延长封禁！')
            print('   ✅ 解法：退出程序 → 开着 Clash → 运行时加代理参数换个 IP：')
            print('      python bilibili_download.py --proxy http://127.0.0.1:7897')
            print('   （或者什么都不做，等 10~30 分钟封禁自动解除）')
        elif '-352' in str(exc):
            print('   💡 空间接口被风控：请稍等几分钟再试，或加 --proxy 走 Clash 换 IP')
        elif not d.cookie:
            print('   💡 空间接口需要登录 Cookie 才稳：按 c 补充 Cookie 后重试')
        print('   （临时替代方案：把视频链接逐条粘进来，一样能批量下载）')
        return
    if not items:
        print('❌ 没抓到任何投稿（可能账号异常 / 被风控）')
        if not d.cookie:
            print('   💡 补个登录 Cookie 再试：输入 c')
        return
    title = f'{name} 的投稿' if name else f'mid={mid} 的投稿'
    run_batch(d, items, title)


# ============================================================
#  Cookie 环节
# ============================================================

def ask_cookie(d):
    print('\n┌─ 登录 Cookie（可选，用来解锁更高画质 + 空间批量接口）──')
    print('│ 未登录：画质最高 480P 左右，UP主空间列表接口容易被风控拦截。')
    print('│ 获取方式：浏览器打开 bilibili.com 并登录 →')
    print('│   F12 → Application（应用程序）→ Cookies →')
    print('│   复制 SESSDATA 的值（可直接只粘贴值，会自动补成 SESSDATA=xxx）')
    print('└────────────────────────────────────────────────────')
    try:
        raw = input('Cookie（回车 = 跳过，仍可下载单条视频）> ').strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not raw:
        print('⏭  已跳过登录，按未登录状态下载')
        return None
    cookie = normalize_cookie(raw)
    d.set_cookie(cookie)
    ok, who = d.login_check()
    if ok:
        print(f'    ✅ Cookie 有效，已登录：{who}（仅本次运行有效，不写入本地）')
        return cookie
    print(f'    ⚠️  {who}')
    print('    ⚠️  Cookie 不可用，本次按未登录状态下载（画质与批量都会受限）')
    d.set_cookie(None)
    return None


def resolve_cookie(d, cli_cookie='', no_prompt=False):
    """优先级：命令行 → 本地缓存 → 交互询问"""
    if cli_cookie:
        cookie = normalize_cookie(cli_cookie)
        d.set_cookie(cookie)
        ok, who = d.login_check()
        if ok:
            print(f'[Cookie] 使用命令行传入的 Cookie，已登录：{who}')
            return cookie
        print(f'[Cookie] ⚠️  命令行 Cookie 无效：{who} → 改为询问')
        d.set_cookie(None)

    if no_prompt:
        print('[Cookie] 已按 --no-cookie 跳过登录（画质与批量受限）')
        return None

    # 不读写本地 Cookie 文件：Cookie 只在本次运行内使用，退出即丢弃
    return ask_cookie(d)


# ============================================================
#  主流程
# ============================================================

def handle_input(d, text):
    """
    处理一次用户输入。返回 True 继续循环，False 退出程序。
    支持：q 退出 / c 重设 Cookie / 空间链接 / 多链接 / 单条 / CDN 直链
    """
    text = text.strip()
    if text.lower() in ('q', 'quit', 'exit'):
        return False
    if text.lower() == 'c':
        ask_cookie(d)
        return True

    # UP 主空间
    mid = parse_mid(text)
    if mid:
        run_space_batch(d, mid)
        return True

    # 短链展开
    if is_short_link(text):
        print('  ↪ 展开短链…')
        text = expand_short_link(d.session, text)

    # CDN 直链
    if is_cdn_url(text) and not extract_bvids(text):
        name = f"cdn_{datetime.now():%Y%m%d_%H%M%S}"
        out = OUTPUT_DIR / f'{name}.mp4'
        try:
            d.fetch(text, out, '直链')
            report_saved(out)
        except Exception as exc:
            print(f'  ❌ 下载失败：{type(exc).__name__}: {exc}')
        return True

    # 抽取 BV 号（一行多个 = 多链接批量）
    bvids = extract_bvids(text)
    if not bvids:
        print('  ❌ 没识别出 BV 号 / 空间链接。可输入 BV 号、视频链接、UP主空间链接，'
              '或 q 退出')
        return True

    if len(bvids) > 1:
        items = []
        for bv in bvids:
            try:
                info = d.get_video_info(bv)
                items.append({'bvid': bv, 'title': info['title'],
                              'duration': info['duration']})
            except Exception as exc:
                print(f'  ⚠️  跳过 {bv}：{exc}')
            time.sleep(0.3)
        if items:
            run_batch(d, items, f'多链接批量（{len(items)} 条）')
        return True

    run_single(d, bvids[0])
    return True


def print_banner():
    print('=' * 62)
    print('  📺 B 站视频下载器')
    print('=' * 62)
    print(f'保存目录：{OUTPUT_DIR}')
    print()
    print('支持的输入：')
    print('  1. 单个视频     BV1xx411c7mD  /  https://www.bilibili.com/video/BV1xx411c7mD')
    print('  2. UP 主空间    https://space.bilibili.com/349594717   ← 一键抓全部投稿')
    print('  3. 多链接批量   一行里用空格/逗号分隔多个链接或 BV 号')
    print('  4. CDN 直链     F12 Network 里复制的 upos-/bilivideo 直链')
    print('  命令：c = 重新设置 Cookie（解锁高画质 / 空间批量）    q = 退出')
    print()
    print('每条视频下载前都会弹画质菜单：回车 = 最佳，数字 = 选档，a = 仅音频 mp3')
    print()


def detect_clash_proxy():
    """自动探测本机常见代理端口（Clash 等），活着就借它换 IP 绕风控"""
    import socket
    for port in (7897, 7890, 7899, 10809):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.3):
                return f'http://127.0.0.1:{port}'
        except OSError:
            continue
    return None


def main():
    parser = argparse.ArgumentParser(
        description='B 站视频下载器（单条 / UP主空间批量 / 多链接批量）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例：\n'
               '  python bilibili_download.py\n'
               '  python bilibili_download.py BV1xx411c7mD\n'
               '  python bilibili_download.py https://space.bilibili.com/349594717\n')
    parser.add_argument('targets', nargs='*', help='视频链接 / BV 号 / UP主空间链接（可多个）')
    parser.add_argument('--cookie', default=os.environ.get('BILI_COOKIE', ''),
                        help='登录 Cookie（也可用环境变量 BILI_COOKIE）')
    parser.add_argument('--no-cookie', action='store_true', help='跳过 Cookie 询问，按未登录下载')
    parser.add_argument('--proxy', default=os.environ.get('BILI_PROXY', ''),
                        help='HTTP 代理（如 http://127.0.0.1:7897），遇到 -352/-412 风控时用它换 IP')
    parser.add_argument('--no-proxy', action='store_true', help='禁用自动代理探测，强制直连')
    args = parser.parse_args()

    if not has_ffmpeg():
        print('⚠️  未检测到 ffmpeg：dash 音视频无法合并、mp3 无法转码（建议先装 ffmpeg）')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    print_banner()
    # 默认直连（家宽 IP 最干净）；只有 --proxy 手动指定才在启动时挂代理。
    # 直连途中被风控的话，抓取流程会自动接本机 Clash 换 IP 重试。
    d = BiliDownloader(proxy=args.proxy or None)
    resolve_cookie(d, args.cookie, args.no_cookie)
    print()

    # 命令行直接给了目标：先处理掉
    for t in args.targets:
        handle_input(d, t)

    while True:
        try:
            text = input('📥 请输入链接 / BV 号 / UP主空间（q 退出）> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break
        if not text:
            continue
        try:
            if not handle_input(d, text):
                print('再见！')
                break
        except KeyboardInterrupt:
            print('\n↩ 已中断当前任务（程序继续运行）')
        except Exception as exc:
            print(f'❌ 发生未预期的错误（已拦截，程序继续运行）：{type(exc).__name__}: {exc}')
        print('=' * 62)


if __name__ == '__main__':
    main()
