"""
B 站视频爬虫（bili_spider.py）

功能：
    1. 给 UP 主空间链接 → 抓取 TA 的全部投稿视频，批量下载 mp4
    2. 给单个视频链接 / BV 号 → 下载单条
    3. 一行粘多个链接 → 多链接批量

交互流程：
    运行 → 粘贴 Cookie（一次，仅本次有效）→ 输入链接 → 选画质 → 下载

画质：
    单条视频  菜单列出该视频真实可用的档位，选哪档下哪档
    空间批量  菜单选画质上限，每条自动取不超过上限的实际最高档

稳定措施：
    wbi 签名 + w_webid、翻页限速、风控(-352/-412)自动重试、断点续传
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
VIDEO_INTERVAL = 1.5     # 批量：两条视频间隔
PAGE_INTERVAL = 3.0      # 空间翻页间隔（翻太快触发风控）
CHUNK = 1 << 16
PROGRESS_STEP = 3.0

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


def normalize_cookie(raw):
    """粘贴姿势归一：只贴 SESSDATA 值也能识别"""
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


# ---------- 防粘贴输入（粘贴自带换行不会顶跳流程） ----------

_PUMP = {'q': None, 'eof': False}


def _stdin_pump(q):
    try:
        for line in sys.stdin:
            q.put(line)
    except Exception:
        pass
    q.put(None)


def ask(prompt, settle=0.5):
    """读输入：吸收粘贴附带的多余行/空行，静默 settle 秒后返回。
    关键：若目前只收到空行，绝不立刻下结论——延长等待（2s）给晚到的粘贴留机会。
    """
    print(prompt, end='', flush=True)
    if _PUMP['q'] is None:
        _PUMP['q'] = queue.Queue()
        threading.Thread(target=_stdin_pump, args=(_PUMP['q'],), daemon=True).start()
    lines = []
    while True:
        if _PUMP['eof'] and _PUMP['q'].empty():
            break
        if not lines:
            item = _PUMP['q'].get()                     # 第一条：一直等到用户有动作
        elif all(not ln.strip() for ln in lines):
            try:
                item = _PUMP['q'].get(timeout=2.0)      # 只有空行 → 多等 2s，防粘贴后到
            except queue.Empty:
                break
        else:
            try:
                item = _PUMP['q'].get(timeout=settle)   # 已有内容 → 静默 settle 即收
            except queue.Empty:
                break
        if item is None:
            _PUMP['eof'] = True
            break
        lines.append(item.rstrip('\r\n'))
    if not lines:
        raise EOFError
    return '\n'.join(ln for ln in lines if ln.strip())


def read_clipboard():
    """读系统剪贴板（tkinter 优先，powershell 兜底），失败返回空串"""
    try:
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        t = r.clipboard_get()
        r.destroy()
        return t
    except Exception:
        pass
    try:
        return subprocess.run(
            ['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
            capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return ''


def looks_like_cookie(text):
    """剪贴板/输入内容是否像 B 站 Cookie"""
    if not text:
        return False
    if re.search(r'(?i)(sessdata|bili_jct|buvid3|dedeuserid)', text):
        return True
    return len(re.findall(r'[A-Za-z_][\w.-]*=[^;\s]+', text)) >= 2


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

    def set_cookie(self, cookie):
        """Cookie 解析进 cookie jar；缺设备指纹（buvid3）自动补齐"""
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
        if 'buvid3' in {c.name for c in self.session.cookies}:
            return
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
        if 'buvid3' not in {c.name for c in self.session.cookies}:
            self._visit_homepage()

    def login_name(self):
        try:
            r = self.session.get('https://api.bilibili.com/x/web-interface/nav',
                                 timeout=API_TIMEOUT).json()
            d = r.get('data') or {}
            return d.get('uname') if d.get('isLogin') else None
        except Exception:
            return None

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
        """抓全部投稿，按发布时间从旧到新排序；风控自动重试"""
        items, page = [], 1
        total = None
        w_webid = self._get_w_webid(mid)
        while True:
            r = self._space_page(mid, page, w_webid)
            for wait in (8, 15):
                if r.get('code') not in (-352, -412):
                    break
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
        items.sort(key=lambda x: x['created'])
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
        last = None
        for i, u in enumerate([url] + list(backup or [])):
            try:
                if i:
                    print(f'    ↻ 主节点连不上，换备用节点…', flush=True)
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
    """单条视频画质菜单（真实档位）。返回 ('video', stream)/('audio',None)/('quit',None)"""
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
              f'{s.get("width")}x{s.get("height")}  {size}')
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
    """批量画质上限菜单。返回 ('video', qn)/('audio',None)/('quit',None)"""
    print('\n🎛  请选择画质上限（本次批量统一使用）：')
    print('   ℹ️  每条视频实际档位不同，自动取「不超过上限的实际最高档」并逐条报告')
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
    bvid = info['bvid']
    play = bili.play_url(bvid, page['cid'])
    temp_dir = TEMP_ROOT / bvid
    temp_dir.mkdir(parents=True, exist_ok=True)
    if out_stem is None:
        out_stem = f"{sanitize(info['title'])} [{bvid}]"

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
    print('\n┌─ 登录 Cookie（解锁高画质 + 空间批量接口，仅本次运行有效）──')
    print('│ 获取：浏览器登录 bilibili.com → F12 → Application → Cookies')
    print('│      → 找到 SESSDATA，双击 Value 列复制（或整串 Cookie 都行）')
    print('└────────────────────────────────────────────────────')
    try:
        raw = ask('Cookie（回车 = 跳过，仍可下载单条视频）> ')
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not raw:
        # 控制台没收到有效输入 → 尝试从剪贴板自动读取（用户刚复制过 Cookie 的场景）
        cb = read_clipboard()
        if looks_like_cookie(cb):
            raw = cb.strip()
            print('    · 控制台没收到输入，已自动从剪贴板读取 Cookie')
        else:
            print('⏭  已跳过登录')
            return
    # 输入的是链接而不是 Cookie → 不当 Cookie 用，直接按链接处理
    if not looks_like_cookie(raw) and (parse_mid(raw) or extract_bvids(raw)):
        print('  💡 这看起来是链接不是 Cookie——已跳过登录，直接处理这个链接')
        handle_input(bili, raw.strip())
        return
    # 粘贴被拆成多行时自动拼合
    lines = [ln.strip() for ln in raw.split('\n') if ln.strip()]
    kv_lines = [ln for ln in lines if re.match(r'^[A-Za-z_][\w.-]*\s*=', ln)]
    if len(lines) > 1 and kv_lines:
        raw = '; '.join(kv_lines)
    elif kv_lines:
        raw = kv_lines[0] if len(kv_lines) == 1 else '; '.join(kv_lines)
    else:
        raw = ''.join(lines)
    bili.set_cookie(normalize_cookie(raw))
    names = sorted({k.split('=')[0].strip() for k in raw.split(';') if '=' in k})
    if names:
        print(f'    · 收到 {len(raw)} 字符，解析出 {len(names)} 项：{"、".join(names)}')
    who = bili.login_name()
    if who:
        print(f'    ✅ Cookie 有效，已登录：{who}（仅本次运行有效，不写入本地）')
    else:
        print('    ⚠️  Cookie 无效或已过期，本次按未登录下载')
        bili.set_cookie('')


# ============================================================
#  主流程
# ============================================================

def handle_input(bili, text):
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

    bvids = extract_bvids(text)
    if not bvids:
        print('  ❌ 没识别出 BV 号 / 空间链接。可输入：视频链接、BV号、UP主空间链接，或 q 退出')
        return True
    if len(bvids) > 1:
        run_multi_links(bili, bvids)
        return True
    run_single(bili, bvids[0])
    return True


def print_banner():
    print('=' * 62)
    print('  📺 B 站视频爬虫（bili_spider.py）')
    print('=' * 62)
    print(f'保存目录：{OUTPUT_DIR}')
    print()
    print('支持的输入：')
    print('  1. 单个视频     BV1xx411c7mD  /  https://www.bilibili.com/video/BV1xx411c7mD')
    print('  2. UP 主空间    https://space.bilibili.com/xxxx   ← 一键抓全部投稿（旧→新）')
    print('  3. 多链接批量   一行里用空格/逗号分隔多个链接或 BV 号')
    print('  命令：c = 重新设置 Cookie    q = 退出')
    print()


def main():
    parser = argparse.ArgumentParser(description='B 站视频爬虫')
    parser.add_argument('targets', nargs='*',
                        help='视频链接 / BV 号 / UP主空间链接（可多个）')
    parser.add_argument('--cookie', default=os.environ.get('BILI_COOKIE', ''),
                        help='登录 Cookie（也可用环境变量 BILI_COOKIE）')
    parser.add_argument('--no-cookie', action='store_true', help='跳过 Cookie 询问')
    args = parser.parse_args()

    if not has_ffmpeg():
        print('⚠️  未检测到 ffmpeg：dash 音视频无法合并（建议安装）')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    print_banner()
    bili = Bili()

    if args.cookie:
        bili.set_cookie(normalize_cookie(args.cookie))
        who = bili.login_name()
        if who:
            print(f'[Cookie] 已登录：{who}')
        else:
            print('[Cookie] ⚠️  命令行 Cookie 无效 → 改为询问')
            bili.set_cookie('')
            ask_cookie(bili)
    elif not args.no_cookie:
        ask_cookie(bili)
    print()

    for t in args.targets:
        handle_input(bili, t)

    while True:
        try:
            text = ask('📥 请输入链接 / BV 号 / UP主空间（q 退出）> ')
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break
        text = text.replace('\n', ' ').strip()
        if looks_like_cookie(text) and not parse_mid(text) and not extract_bvids(text):
            print('  💡 这看起来是 Cookie 不是链接——输入 c 重新设置 Cookie；请粘贴视频/空间链接')
            continue
        if not text:
            continue
        try:
            if not handle_input(bili, text):
                print('再见！')
                break
        except KeyboardInterrupt:
            print('\n↩ 已中断当前任务（程序继续运行）')
        except Exception as exc:
            print(f'❌ 发生未预期的错误（已拦截，程序继续运行）：{type(exc).__name__}: {exc}')
        print('=' * 62)


if __name__ == '__main__':
    main()
