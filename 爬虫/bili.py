"""
B 站下载器（bili.py）

运行 → 粘贴 Cookie → 输入链接 → 选画质 → 下载

支持的输入：
    1. 单视频      BV 号 / 视频链接 / b23 短链
    2. UP主空间    https://space.bilibili.com/xxxx（一键全部投稿，从旧到新）
    3. 多链接批量  一行多个链接/BV号（空格、逗号分隔）
    4. CDN 直链    F12 复制的 upos-/bilivideo 直链

画质规则：
    单视频   菜单 = 该视频真实拥有的档位，选哪档下哪档，下完报告实得画质
    批量     菜单 = 画质上限，每条自动取不超过上限的实际最高档，逐条报告

Cookie：只存本次运行内存，绝不写盘。只贴 SESSDATA 值也行（自动补齐设备指纹）。
"""

import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import os
import re
import time
import queue
import random
import shutil
import hashlib
import argparse
import socket
import string
import threading
import subprocess
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:
    print('缺少 requests，请用项目虚拟环境运行本脚本')
    sys.exit(1)

# ============================================================
#  配置
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'downloads'
TEMP_ROOT = OUTPUT_DIR / '.temp'
ARCHIVE_FILE = BASE_DIR / 'downloaded_bilibili.txt'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

API_TIMEOUT = 30
API_RETRIES = 3
VIDEO_INTERVAL = 1.5     # 批量：两条视频之间的间隔
PAGE_INTERVAL = 3.0      # 空间翻页间隔（翻太快必触发风控）
CHUNK = 1 << 16
PROGRESS_STEP = 3.0

PROXY_PORTS = [7897, 7890, 7891, 10809]   # 兜底自救用的本机代理端口

QN_NAME = {
    127: '8K 超高清', 126: '杜比视界', 125: 'HDR 真彩',
    120: '4K 超清', 116: '1080P 60帧', 112: '1080P 高码率',
    100: '智能修复', 80: '1080P 高清', 74: '720P 60帧',
    64: '720P 高清', 32: '480P 清晰', 16: '360P 流畅', 6: '240P 极速',
}
BATCH_LADDER = [127, 120, 116, 112, 80, 74, 64, 32, 16]

MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

DEVICE_KEYS = ('buvid3', 'buvid4', 'b_nut', 'buvid_fp', 'LIVE_BUVID', 'b_lsid')


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
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', '_', str(name)).strip(' .')
    name = re.sub(r'\s+', ' ', name)
    return name[:max_len] or '未命名'


def parse_length(text):
    """'1:44' / '1:02:03' → 秒"""
    if not text:
        return 0
    text = str(text).strip()
    if text.isdigit():
        return int(text)
    try:
        nums = [int(p) for p in text.split(':')]
    except ValueError:
        return 0
    sec = 0
    for n in nums:
        sec = sec * 60 + n
    return sec


def has_ffmpeg():
    return shutil.which('ffmpeg') is not None


# ---------- 防粘贴输入 ----------

_PUMP = {'q': None, 'eof': False}


def _stdin_pump(q):
    """后台线程：持续把 stdin 的行放进队列"""
    try:
        for line in sys.stdin:
            q.put(line)
    except Exception:
        pass
    q.put(None)


def ask(prompt, settle=0.45):
    """
    防粘贴版 input()：
    - 粘贴的内容常自带换行（等于自动回车）或多行碎片
    - 这里持续吸收所有立刻到达的行，直到静默 settle 秒才返回
    - 自动丢弃空行，绝不让粘贴把流程"顶"过去
    """
    print(prompt, end='', flush=True)
    if _PUMP['q'] is None:
        _PUMP['q'] = queue.Queue()
        threading.Thread(target=_stdin_pump, args=(_PUMP['q'],), daemon=True).start()
    lines = []
    while True:
        if _PUMP['eof'] and _PUMP['q'].empty():
            break
        try:
            item = _PUMP['q'].get() if not lines else _PUMP['q'].get(timeout=settle)
        except queue.Empty:
            break
        if item is None:
            _PUMP['eof'] = True
            break
        lines.append(item.rstrip('\r\n'))
    if not lines:
        raise EOFError
    return '\n'.join(ln for ln in lines if ln.strip())


def detect_local_proxy():
    for port in PROXY_PORTS:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.3):
                return f'http://127.0.0.1:{port}'
        except OSError:
            continue
    return None


def progress_printer(label, total_bytes):
    state = {'t': time.time(), 'start': time.time(), 'last': -1}

    def update(done):
        now = time.time()
        if done == state['last']:
            return
        if now - state['t'] < PROGRESS_STEP and (total_bytes and done < total_bytes):
            return
        state['t'] = now
        state['last'] = done
        speed = done / max(now - state['start'], 0.001)
        if total_bytes:
            print(f'    ⬇ {label} {done / total_bytes * 100:5.1f}%  '
                  f'{human_size(done)}/{human_size(total_bytes)}  {human_size(speed)}/s',
                  flush=True)
        else:
            print(f'    ⬇ {label} {human_size(done)}  {human_size(speed)}/s', flush=True)

    return update


def extract_bvids(text):
    out = []
    for m in re.finditer(r'BV[0-9A-Za-z]{10}', text):
        if m.group(0) not in out:
            out.append(m.group(0))
    return out


def parse_mid(text):
    m = re.search(r'space\.bilibili\.com/(\d+)', text)
    return int(m.group(1)) if m else None


def is_short_link(text):
    return bool(re.match(r'https?://b23\.tv/\S+', text.strip()))


def is_cdn_url(text):
    return bool(re.search(r'(upos-|bilivideo\.com|akamaized\.net/mp4)', text))


def normalize_cookie(raw):
    """
    粘贴姿势归一：
    - 只贴 SESSDATA 的值 → 补 SESSDATA=
    - F12 的 Tab 分隔行 → 补成 k=v
    - 完整 Cookie 串 → 原样
    """
    raw = raw.strip().strip('"').strip("'").replace('\r', '')
    if not raw:
        return ''
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
#  下载器内核
# ============================================================

class Bili:

    def __init__(self, cookie=''):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': UA,
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        self.proxy = None
        self._mixin = None
        self._mixin_at = 0
        if cookie:
            self.set_cookie(cookie)
        else:
            self._visit_homepage()

    def _visit_homepage(self):
        try:
            self.session.get('https://www.bilibili.com/', timeout=API_TIMEOUT)
        except requests.RequestException:
            pass

    # ---------- Cookie ----------

    def set_cookie(self, cookie):
        """
        Cookie 解析进 cookie jar（和真实浏览器一致）。
        只贴 SESSDATA 时必须保住/补齐设备指纹（buvid3），否则空间接口必被风控。
        """
        device_old = {c.name: c.value for c in self.session.cookies
                      if c.name in DEVICE_KEYS}
        self.session.headers.pop('Cookie', None)
        self.session.cookies.clear()
        if cookie:
            for kv in cookie.split(';'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    self.session.cookies.set(k.strip(), v.strip(), domain='.bilibili.com')
        if 'buvid3' not in {c.name for c in self.session.cookies}:
            self._ensure_device_cookies()
        have = {c.name for c in self.session.cookies}
        for k, v in device_old.items():
            if k not in have:
                self.session.cookies.set(k, v, domain='.bilibili.com')

    def _ensure_device_cookies(self):
        """确保 jar 里有设备指纹 buvid3 —— 空间接口没有它直接 -412/-352"""
        if 'buvid3' in {c.name for c in self.session.cookies}:
            return
        # 方式一：B 站指纹接口直接领（最稳）
        try:
            r = self.session.get('https://api.bilibili.com/x/frontend/finger/spi',
                                 timeout=API_TIMEOUT).json()
            d = r.get('data') or {}
            if d.get('b_3'):
                self.session.cookies.set('buvid3', d['b_3'], domain='.bilibili.com')
            if d.get('b_4'):
                self.session.cookies.set('buvid4', d['b_4'], domain='.bilibili.com')
        except Exception:
            pass
        # 方式二：访问主站碰 Set-Cookie 兜底
        if 'buvid3' not in {c.name for c in self.session.cookies}:
            self._visit_homepage()

    def login_name(self):
        """返回登录用户名；未登录/无效返回 None"""
        try:
            r = self.session.get('https://api.bilibili.com/x/web-interface/nav',
                                 timeout=API_TIMEOUT).json()
            d = r.get('data') or {}
            return d.get('uname') if d.get('isLogin') else None
        except Exception:
            return None

    def use_proxy(self, proxy):
        self.proxy = proxy
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
        else:
            self.session.proxies = {}

    # ---------- wbi 签名 ----------

    def _mixin_key(self):
        if self._mixin and time.time() - self._mixin_at < 3600:
            return self._mixin
        d = self.session.get('https://api.bilibili.com/x/web-interface/nav',
                             timeout=API_TIMEOUT).json().get('data') or {}
        wbi = d.get('wbi_img') or {}
        img = wbi.get('img_url', '').rsplit('/', 1)[-1].split('.')[0]
        sub = wbi.get('sub_url', '').rsplit('/', 1)[-1].split('.')[0]
        if not img or not sub:
            raise RuntimeError('无法获取 wbi 密钥（nav 接口异常）')
        raw = img + sub
        self._mixin = ''.join(raw[i] for i in MIXIN_TAB)[:32]
        self._mixin_at = time.time()
        return self._mixin

    def _sign(self, params):
        p = dict(params)
        p['wts'] = str(int(time.time()))
        p.setdefault('dm_img_list', '[]')
        p.setdefault('dm_img_str', ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=8)))
        p.setdefault('dm_cover_img_str', ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=8)))
        p.setdefault('dm_img_inter', '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}')
        p = dict(sorted(p.items()))
        clean = {k: re.sub(r"[!'()*]", '', str(v)) for k, v in p.items()}
        query = urllib.parse.urlencode(clean)
        p['w_rid'] = hashlib.md5((query + self._mixin_key()).encode()).hexdigest()
        return p

    def _get_json(self, url, *, params=None, headers=None):
        """GET JSON，网络抖动自动重试"""
        last = None
        for attempt in range(1, API_RETRIES + 1):
            try:
                r = self.session.get(url, params=params, headers=headers,
                                     timeout=API_TIMEOUT)
                return r.json()
            except (requests.Timeout, requests.ConnectionError) as exc:
                last = exc
                if attempt < API_RETRIES:
                    wait = 3 * attempt
                    print(f'    ⚠️  网络抖动（{type(exc).__name__}），{wait}s 后重试…',
                          flush=True)
                    time.sleep(wait)
        raise last

    # ---------- 空间投稿 ----------

    def _get_w_webid(self, mid):
        """从空间页 HTML 提取 w_webid（空间接口反爬字段，缺了 -352）"""
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

    def _space_page(self, mid, page, w_webid):
        return self._get_json(
            'https://api.bilibili.com/x/space/wbi/arc/search',
            params=self._sign({'mid': str(mid), 'order': 'pubdate', 'pn': str(page),
                               'ps': '30', 'platform': 'web', 'web_location': '1550101',
                               'w_webid': w_webid}),
            headers={'Referer': f'https://space.bilibili.com/{mid}/video'})

    def space_videos(self, mid):
        """
        抓 UP 主全部投稿，按发布时间「从旧到新」排序返回。
        风控自救：-352/-412 → 等 8s 换 w_webid → 等 15s → 借本机代理换 IP
        """
        items, page = [], 1
        total = None
        w_webid = self._get_w_webid(mid)
        while True:
            r = self._space_page(mid, page, w_webid)
            for wait, use_proxy in ((8, False), (15, False), (10, True)):
                if r.get('code') not in (-352, -412):
                    break
                if use_proxy:
                    if self.proxy:
                        break
                    clash = detect_local_proxy()
                    if not clash:
                        break
                    self.use_proxy(clash)
                    print(f'    🛡 自动改走本机代理 {clash} 换 IP…', flush=True)
                print(f'    ⚠️  空间接口被风控（{r.get("code")}），'
                      f'等待 {wait}s 后重试…', flush=True)
                time.sleep(wait)
                w_webid = self._get_w_webid(mid)
                r = self._space_page(mid, page, w_webid)
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
                items.append({'bvid': v.get('bvid'),
                              'title': v.get('title') or '无标题',
                              'duration': parse_length(v.get('length')),
                              'created': v.get('created') or 0})
            print(f'    · 已抓取 {len(items)}/{total} 条…', flush=True)
            if len(vlist) < 30:
                break
            page += 1
            time.sleep(PAGE_INTERVAL)
        items.sort(key=lambda x: x['created'])    # 接口最新在前 → 反转成从旧到新
        return items

    def uploader_name(self, mid):
        try:
            r = self._get_json('https://api.bilibili.com/x/space/wbi/acc/info',
                               params=self._sign({'mid': str(mid)}))
            if r.get('code') == 0:
                return (r.get('data') or {}).get('name')
        except Exception:
            pass
        return None

    # ---------- 视频信息 / 取流 ----------

    def video_info(self, bvid):
        r = self._get_json('https://api.bilibili.com/x/web-interface/view',
                           params={'bvid': bvid})
        if r.get('code') != 0:
            raise RuntimeError(f"{r.get('code')} {r.get('message') or '获取视频信息失败'}")
        d = r['data']
        return {'bvid': bvid,
                'title': d.get('title') or '无标题',
                'owner': ((d.get('owner') or {}).get('name')) or '未知UP',
                'duration': d.get('duration') or 0,
                'pages': [{'cid': p.get('cid'), 'part': p.get('part') or f'P{i+1}',
                           'duration': p.get('duration') or 0}
                          for i, p in enumerate(d.get('pages') or [])]}

    def play_url(self, bvid, cid, qn=127):
        params = {'bvid': bvid, 'cid': cid, 'qn': qn, 'fnval': 16, 'fnver': 0,
                  'fourk': 1, 'platform': 'pc', 'otype': 'json', 'high_quality': 1}
        r = self._get_json('https://api.bilibili.com/x/player/playurl', params=params)
        if r.get('code') != 0:
            raise RuntimeError(f"{r.get('code')} {r.get('message') or '取流失败'}")
        d = r.get('data') or {}
        if d.get('dash'):
            dash = d['dash']
            return {'format': 'dash',
                    'video': [{'qn': v.get('id'),
                               'bandwidth': v.get('bandwidth') or 0,
                               'codecs': v.get('codecs') or '',
                               'width': v.get('width') or 0,
                               'height': v.get('height') or 0,
                               'fps': v.get('frameRate'),
                               'url': v.get('baseUrl') or v.get('base_url'),
                               'backup': v.get('backupUrl') or v.get('backup_url') or []}
                              for v in (dash.get('video') or [])],
                    'audio': [{'bandwidth': a.get('bandwidth') or 0,
                               'codecs': a.get('codecs') or '',
                               'url': a.get('baseUrl') or a.get('base_url'),
                               'backup': a.get('backupUrl') or a.get('backup_url') or []}
                              for a in (dash.get('audio') or [])]}
        if d.get('durl'):
            return {'format': 'durl',
                    'quality': d.get('quality'),
                    'segments': [{'url': x.get('url'),
                                  'backup': x.get('backup_url') or []}
                                 for x in d['durl']]}
        raise RuntimeError('接口未返回可用流（可能需要登录 Cookie）')

    # ---------- 下载 ----------

    def fetch(self, url, out_path, label, backup=None):
        """下载单个流；主节点失败自动换备用 CDN"""
        last = None
        for i, u in enumerate([url] + list(backup or [])):
            try:
                if i:
                    print(f'    ↻ 主节点连不上（{type(last).__name__}），换备用节点…',
                          flush=True)
                return self._fetch_one(u, out_path, label)
            except Exception as exc:
                last = exc
        raise last if last else RuntimeError('下载失败')

    def _fetch_one(self, url, out_path, label):
        headers = {'Referer': 'https://www.bilibili.com/',
                   'Origin': 'https://www.bilibili.com'}
        host = re.sub(r'^https?://', '', url).split('/')[0]
        print(f'    ⬇ {label}：连接 {host} …', flush=True)
        with self.session.get(url, headers=headers, stream=True,
                              timeout=(10, 30)) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get('Content-Length') or 0)
            m = re.match(r'bytes \d+-\d+/(\d+)',
                         resp.headers.get('Content-Range') or '')
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
#  画质选择
# ============================================================

def group_streams(video_streams, duration):
    """同档位归并（优先 avc 编码），返回 [(qn, stream, 估算体积)] 从高到低"""
    best = {}
    for s in video_streams:
        qn = s.get('qn')
        old = best.get(qn)
        if old is None:
            best[qn] = s
            continue
        old_avc = str(old.get('codecs', '')).startswith('avc')
        new_avc = str(s.get('codecs', '')).startswith('avc')
        if (new_avc and not old_avc) or (new_avc == old_avc
                                         and s.get('bandwidth', 0) > old.get('bandwidth', 0)):
            best[qn] = s
    rows = [(qn, s, (s.get('bandwidth') or 0) * max(duration or 0, 1) / 8)
            for qn, s in best.items()]
    rows.sort(key=lambda x: x[0], reverse=True)
    return rows


def menu_single(play, duration):
    """单视频：列出真实可用档位。返回 ('video', stream) / ('audio', None) / ('quit', None)"""
    if play['format'] == 'durl':
        print('\n🎛  该视频只有渐进式流，无法选画质，将直接下载')
        return 'video', None

    rows = group_streams(play.get('video') or [], duration)
    if not rows:
        return None, None

    print('\n🎛  请选择画质（以下为该视频实际可用的档位）：')
    print(f'   0. 最佳画质（{QN_NAME.get(rows[0][0], rows[0][0])}，回车默认）')
    for i, (qn, s, est) in enumerate(rows, 1):
        fps = ''
        try:
            fr = float(s.get('fps') or 0)
            fps = f' {int(fr)}fps' if fr >= 50 else ''
        except (TypeError, ValueError):
            pass
        size = f'（约 {human_size(est)}）' if est else ''
        print(f'   {i}. {QN_NAME.get(qn, f"qn={qn}")}{fps}  '
              f'{s.get("width")}x{s.get("height")} {s.get("codecs")}  {size}')
    print('   a. 仅音频 mp3   q. 放弃这条')

    while True:
        try:
            c = ask(f'   选择 [0-{len(rows)}/a/q] > ').split('\n')[0].strip().lower()
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


def menu_batch():
    """批量：选画质上限。返回 ('video', qn) / ('audio', None) / ('quit', None)"""
    print('\n🎛  请选择画质上限（批量任务统一使用）：')
    print('   ℹ️  每条视频实际档位不同，会自动取「不超过上限的实际最高档」，')
    print('      下载时逐条报告实得画质。')
    print('   0. 不设上限（每条取自己的最高档，回车默认）')
    for i, qn in enumerate(BATCH_LADDER, 1):
        print(f'   {i}. {QN_NAME.get(qn, qn)}')
    print('   a. 仅音频 mp3   q. 放弃本次批量')
    while True:
        try:
            c = ask(f'   选择 [0-{len(BATCH_LADDER)}/a/q] > ').split('\n')[0].strip().lower()
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


def pick_stream(play, qn=None, want=None):
    """挑要下载的视频/音频流。want=单条模式选定流；qn=批量模式上限"""
    if play['format'] == 'durl':
        return None, None
    v = want
    if v is None:
        videos = play.get('video') or []
        if not videos:
            return None, None
        pool = [s for s in videos if (s.get('qn') or 0) <= (qn or 999)] or videos
        top = max(s.get('qn') or 0 for s in pool)
        pool = [s for s in pool if (s.get('qn') or 0) == top]
        avc = [s for s in pool if str(s.get('codecs', '')).startswith('avc')]
        v = max(avc or pool, key=lambda s: s.get('bandwidth') or 0)
    audios = play.get('audio') or []
    mp4a = [x for x in audios if 'mp4a' in str(x.get('codecs', ''))]
    a = max(mp4a or audios, key=lambda x: x.get('bandwidth') or 0) if audios else None
    return v, a


# ============================================================
#  下载档案（断点续传）
# ============================================================

def archive_load():
    try:
        return {ln.strip() for ln in
                ARCHIVE_FILE.read_text(encoding='utf-8').splitlines() if ln.strip()}
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
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-i', str(video_path), '-i', str(audio_path),
           '-c', 'copy', '-movflags', '+faststart', str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=1800)
    return r.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0


def to_mp3(src_path, out_path):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-i', str(src_path), '-vn', '-c:a', 'libmp3lame', '-q:a', '2', str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=1800)
    if r.returncode != 0 or not out_path.exists():
        return src_path
    return out_path


def report_saved(path):
    if path and path.exists():
        print(f'💾 已保存：{path}（{human_size(path.stat().st_size)}）', flush=True)


def quality_report(stream, qn_cap=None):
    got = (stream or {}).get('qn') or 0
    name = QN_NAME.get(got, f'qn={got}')
    msg = (f'    🎞 实得画质：{name}'
           f'（{(stream or {}).get("width")}x{(stream or {}).get("height")}）')
    if qn_cap and qn_cap < 127 and got < qn_cap:
        msg += f'　· 该视频最高就这档，未到上限 {QN_NAME.get(qn_cap, qn_cap)}'
    print(msg, flush=True)


def download_one(bili, info, page, *, want=None, qn=None, audio_only=False,
                 out_stem=None):
    """下载一条视频的一个分P，返回产物路径"""
    bvid = info['bvid']
    play = bili.play_url(bvid, page['cid'])
    temp_dir = TEMP_ROOT / bvid
    temp_dir.mkdir(parents=True, exist_ok=True)
    if out_stem is None:
        out_stem = f"{sanitize(info['title'])} [{bvid}]"

    # ---- 渐进式 durl（未登录降级）----
    if play['format'] == 'durl':
        seg = (play.get('segments') or [None])[0]
        if not seg:
            raise RuntimeError('没有可用分片')
        got = play.get('quality')
        print(f'    🎞 实得画质：{QN_NAME.get(got, got or "?")}', flush=True)
        out = OUTPUT_DIR / f'{out_stem}.mp4'
        bili.fetch(seg['url'], out, '本片', seg.get('backup'))
        if audio_only and has_ffmpeg():
            out = to_mp3(out, OUTPUT_DIR / f'{out_stem}.mp3')
        return out

    v, a = pick_stream(play, qn=qn, want=want)
    if v is None:
        raise RuntimeError('未取到视频流')
    quality_report(v, qn_cap=None if want is not None else qn)

    # ---- 仅音频 ----
    if audio_only:
        if not a:
            raise RuntimeError('未取到音频流')
        src = temp_dir / 'audio.m4s'
        bili.fetch(a['url'], src, '音频', a.get('backup'))
        if has_ffmpeg():
            out = to_mp3(src, OUTPUT_DIR / f'{out_stem}.mp3')
        else:
            out = OUTPUT_DIR / f'{out_stem}.m4a'
            shutil.move(str(src), str(out))
        shutil.rmtree(temp_dir, ignore_errors=True)
        return out

    # ---- 视频 + 音频 → ffmpeg 合并 ----
    vpath = temp_dir / 'video.m4s'
    bili.fetch(v['url'], vpath, '视频', v.get('backup'))
    apath = None
    if a:
        apath = temp_dir / 'audio.m4s'
        bili.fetch(a['url'], apath, '音频', a.get('backup'))
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


# ---------- 单条 ----------

def run_single(bili, bvid):
    print(f'\n{"=" * 62}')
    print(f'  🔍 解析视频 {bvid}')
    info = bili.video_info(bvid)
    print(f'  标题：{info["title"]}')
    print(f'  UP主：{info["owner"]}    时长：{human_duration(info["duration"])}'
          f'    分P：{len(info["pages"])}')

    pages = info['pages']
    if len(pages) > 1:
        print('\n📑 该视频有多个分P：')
        for i, p in enumerate(pages, 1):
            print(f'   {i}. {p["part"]}（{human_duration(p["duration"])}）')
        print('   a. 全部分P   q. 放弃')
        while True:
            try:
                c = ask(f'   选择 [1-{len(pages)}/a/q] > ').split('\n')[0].strip().lower()
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

    probe = bili.play_url(bvid, selected[0]['cid'])
    quality, want = menu_single(probe, info['duration'])
    if quality == 'quit':
        print('↩ 已放弃')
        return
    if quality is None:
        print('   ⚠️  未解析到画质列表，按最佳画质下载')
        quality, want = 'video', None
    audio_only = quality == 'audio'

    multi = len(selected) > 1
    for idx, page in enumerate(selected, 1):
        stem = f"{sanitize(info['title'])} [{bvid}]"
        if multi:
            stem += f" P{idx}_{sanitize(page['part'], 30)}"
        print(f'\n⬇ 开始下载（{"仅音频 mp3" if audio_only else "视频"}）…')
        try:
            out = download_one(bili, info, page, want=want, audio_only=audio_only,
                               out_stem=stem)
        except Exception as exc:
            print(f'   ❌ 下载失败：{type(exc).__name__}: {exc}')
            if not bili.session.cookies:
                print('      💡 部分画质/视频需要登录 Cookie，可输入 c 补充后重试')
            continue
        report_saved(out)
        if multi:
            print(f'   （进度 {idx}/{len(selected)}）')
    archive_add(bvid)


# ---------- 批量 ----------

def run_batch(bili, items, title):
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

    quality, qn = menu_batch()
    if quality == 'quit':
        print('↩ 已放弃本次批量')
        return
    audio_only = quality == 'audio'

    print(f'\n⬇ 开始批量下载（{"仅音频 mp3" if audio_only else "画质上限：" + QN_NAME.get(qn, str(qn))}）…')
    ok = fail = 0
    failed_items = []
    for i, x in enumerate(todo, 1):
        print(f'\n[{i}/{len(todo)}] {x["title"][:50]}')
        try:
            info = bili.video_info(x['bvid'])
            pages = info['pages']
            if len(pages) > 1:
                print(f'   ℹ️  该视频有 {len(pages)} 个分P，批量模式只下第 1P')
            stem = f"{sanitize(info['title'])} [{info['bvid']}]"
            out = download_one(bili, info, pages[0], qn=qn, audio_only=audio_only,
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
        time.sleep(VIDEO_INTERVAL)

    if failed_items:
        print(f'\n🔁 有 {len(failed_items)} 条失败，稍候自动重试一轮…')
        time.sleep(3)
        for j, x in enumerate(failed_items, 1):
            print(f'\n[重试 {j}/{len(failed_items)}] {x["title"][:50]}')
            try:
                info = bili.video_info(x['bvid'])
                stem = f"{sanitize(info['title'])} [{info['bvid']}]"
                out = download_one(bili, info, info['pages'][0], qn=qn,
                                   audio_only=audio_only, out_stem=stem)
                report_saved(out)
                archive_add(info['bvid'])
                ok += 1
            except KeyboardInterrupt:
                print('\n↩ 已中断重试')
                break
            except Exception as exc:
                fail += 1
                print(f'   ❌ 仍失败：{type(exc).__name__}: {exc}')
            time.sleep(VIDEO_INTERVAL)

    print(f'\n{"=" * 62}')
    print(f'📊 批量结束：成功 {ok} 条，失败 {fail} 条')
    print(f'💾 文件保存在：{OUTPUT_DIR}')


def run_space_batch(bili, mid):
    print(f'\n🔍 正在抓取 UP 主空间投稿（mid={mid}）…')
    name = bili.uploader_name(mid)
    try:
        items = bili.space_videos(mid)
    except Exception as exc:
        print(f'❌ 抓取失败：{type(exc).__name__}: {exc}')
        if '-412' in str(exc):
            print('   🚫 当前 IP 被 B 站临时封禁（请求太频繁），一般 10~30 分钟自动解除')
            print('   💡 下次运行前歇一会儿；或换网络（手机热点）后再试')
        elif '-352' in str(exc):
            print('   💡 空间接口被风控：歇几分钟再试；确认已粘贴登录 Cookie')
        elif not bili.session.cookies:
            print('   💡 空间接口需要登录 Cookie 才稳：输入 c 补充后重试')
        print('   （临时替代：把视频链接逐条粘进来，一样能批量下载）')
        return
    if not items:
        print('❌ 没抓到任何投稿（可能账号异常 / 被风控）')
        return
    run_batch(bili, items, f'{name or f"mid={mid}"} 的投稿（按从旧到新排序）')


# ---------- 多链接批量 ----------

def run_multi_links(bili, bvids):
    items = []
    for bv in bvids:
        try:
            info = bili.video_info(bv)
            items.append({'bvid': bv, 'title': info['title'],
                          'duration': info['duration']})
        except Exception as exc:
            print(f'  ⚠️  跳过 {bv}：{exc}')
        time.sleep(0.3)
    if items:
        run_batch(bili, items, f'多链接批量（{len(items)} 条）')


# ============================================================
#  Cookie 环节
# ============================================================

def ask_cookie(bili):
    print('\n┌─ 登录 Cookie（可选：解锁高画质 + 空间批量接口）──', flush=True)
    print('│ 未登录：画质最高 480P 左右，空间列表接口容易被风控拦截。', flush=True)
    print('│ 获取：浏览器登录 bilibili.com → F12 → Application → Cookies', flush=True)
    print('│      → 复制 SESSDATA 的值（或整串 Cookie 粘进来都行）', flush=True)
    print('└────────────────────────────────────────────────────', flush=True)
    try:
        raw = ask('Cookie（回车 = 跳过，仍可下载单条视频）> ')
    except (EOFError, KeyboardInterrupt):
        print(flush=True)
        return
    if not raw:
        print('⏭  已跳过登录', flush=True)
        return
    # 粘贴可能被拆成多行：含 = 的行当作 Cookie 项；都不含 = 则拼成一整段值
    lines = [ln.strip() for ln in raw.split('\n') if ln.strip()]
    kv_lines = [ln for ln in lines if re.match(r'^[A-Za-z_][\w.-]*\s*=', ln)]
    if len(lines) > 1 and kv_lines:
        raw = '; '.join(kv_lines)
    elif kv_lines:
        raw = kv_lines[0] if len(kv_lines) == 1 else '; '.join(kv_lines)
    else:
        raw = ''.join(lines)
    # 回执：粘贴时控制台经常不回显，主动打印收到的东西让用户核对
    print(f'    · 收到输入：共 {len(raw)} 字符', flush=True)
    print(f'    · 开头：「{raw[:30]}」', flush=True)
    print(f'    · 结尾：「{raw[-20:]}」', flush=True)
    bili.set_cookie(normalize_cookie(raw))
    cookie_names = sorted({k.split('=')[0].strip() for k in raw.split(';') if '=' in k})
    if cookie_names:
        print(f'    · 解析出 {len(cookie_names)} 个 Cookie 项：'
              f'{"、".join(cookie_names)}', flush=True)
    who = bili.login_name()
    if who:
        print(f'    ✅ Cookie 有效，已登录：{who}（仅本次运行有效，不写入本地）',
              flush=True)
    else:
        print('    ⚠️  Cookie 无效或已过期，本次按未登录下载', flush=True)
        print('    💡 检查上面「开头/结尾」是否完整；建议只复制 SESSDATA 的值粘贴',
              flush=True)
        bili.set_cookie('')


# ============================================================
#  主流程
# ============================================================

def handle_input(bili, text):
    """处理一次输入。返回 True 继续循环，False 退出"""
    text = text.strip()
    if text.lower() in ('q', 'quit', 'exit'):
        return False
    if text.lower() == 'c':
        ask_cookie(bili)
        return True

    mid = parse_mid(text)
    if mid:
        run_space_batch(bili, mid)
        return True

    if is_short_link(text):
        print('  ↪ 展开短链…')
        try:
            text = bili.session.get(text, allow_redirects=True,
                                    timeout=API_TIMEOUT).url
        except requests.RequestException as exc:
            print(f'  ⚠️  短链展开失败：{exc}')

    if is_cdn_url(text) and not extract_bvids(text):
        out = OUTPUT_DIR / f"cdn_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        try:
            bili.fetch(text, out, '直链')
            report_saved(out)
        except Exception as exc:
            print(f'  ❌ 下载失败：{type(exc).__name__}: {exc}')
        return True

    bvids = extract_bvids(text)
    if not bvids:
        print('  ❌ 没识别出 BV 号 / 空间链接。可输入 BV 号、视频链接、UP主空间链接，或 q 退出')
        return True
    if len(bvids) > 1:
        run_multi_links(bili, bvids)
        return True
    run_single(bili, bvids[0])
    return True


def print_banner():
    print('=' * 62)
    print('  📺 B 站下载器（bili.py）')
    print('=' * 62)
    print(f'保存目录：{OUTPUT_DIR}')
    print()
    print('支持的输入：')
    print('  1. 单个视频     BV1xx411c7mD  /  https://www.bilibili.com/video/BV1xx411c7mD')
    print('  2. UP 主空间    https://space.bilibili.com/349594717   ← 一键抓全部投稿（旧→新）')
    print('  3. 多链接批量   一行里用空格/逗号分隔多个链接或 BV 号')
    print('  4. CDN 直链     F12 Network 里复制的 upos-/bilivideo 直链')
    print('  命令：c = 重新设置 Cookie    q = 退出')
    print()
    print('画质菜单：回车 = 最佳，数字 = 选档，a = 仅音频 mp3')
    print()


def main():
    parser = argparse.ArgumentParser(
        description='B 站下载器（单条 / UP主空间批量 / 多链接批量）')
    parser.add_argument('targets', nargs='*',
                        help='视频链接 / BV 号 / UP主空间链接（可多个）')
    parser.add_argument('--cookie', default=os.environ.get('BILI_COOKIE', ''),
                        help='登录 Cookie（也可用环境变量 BILI_COOKIE）')
    parser.add_argument('--no-cookie', action='store_true', help='跳过 Cookie 询问')
    args = parser.parse_args()

    if not has_ffmpeg():
        print('⚠️  未检测到 ffmpeg：dash 音视频无法合并、mp3 无法转码')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    print_banner()
    bili = Bili()

    # Cookie：命令行 > 交互询问（只存内存，绝不写盘）
    if args.cookie:
        bili.set_cookie(normalize_cookie(args.cookie))
        who = bili.login_name()
        if who:
            print(f'[Cookie] 已登录：{who}', flush=True)
        else:
            print('[Cookie] ⚠️  命令行 Cookie 无效 → 改为询问', flush=True)
            bili.set_cookie('')
            ask_cookie(bili)
    elif not args.no_cookie:
        ask_cookie(bili)
    print(flush=True)

    for t in args.targets:
        handle_input(bili, t)

    while True:
        try:
            text = ask('📥 请输入链接 / BV 号 / UP主空间（q 退出）> ')
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break
        text = text.replace('\n', ' ').strip()
        if 'SESSDATA' in text or (text.count('=') >= 3 and 'BV' not in text
                                  and 'space.bilibili.com' not in text):
            print('  💡 这看起来是 Cookie 不是链接——输入 c 可重新设置 Cookie；请粘贴视频/空间链接')
            continue
        try:
            if not handle_input(bili, text):
                print('再见！')
                break
        except KeyboardInterrupt:
            print('\n↩ 已中断当前任务（程序继续运行）')
        except Exception as exc:
            print(f'❌ 发生未预期的错误（已拦截，程序继续运行）：'
                  f'{type(exc).__name__}: {exc}')
        print('=' * 62)


if __name__ == '__main__':
    main()
