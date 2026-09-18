#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B 站直播录制器 —— 开播即录，手动终止即存

用法：
    python bilibili_live_record.py                      # 交互式（推荐）
    python bilibili_live_record.py <URL或房间号>         # 直接开录
    python bilibili_live_record.py 1467955 --qn 400     # 指定画质
    python bilibili_live_record.py 1467955 --wait       # 未开播时等待开播
    python bilibili_live_record.py 1467955 --list       # 只看房间信息，不录
    python bilibili_live_record.py --forget-cookie      # 清除本地 Cookie 缓存

流程（交互式）：
    输入直播间 → 显示房间信息 → 【输入登录 Cookie】→ 选择画质 → 录制 → Ctrl+C → 转 mp4

核心机制：
    1. 解析房间 → getRoomPlayInfo 拿真实流地址（FLV / HLS）
    2. ffmpeg -c copy 无损录制到 .flv（不转码，CPU 占用极低）
    3. Ctrl+C 终止 → ffmpeg 优雅收尾 → 无损转封装成 .mp4
    4. 中途断流会自动重取流续录（分片 part01/part02...），结束后合并
    5. 录制过程只显示一个计时时钟（已录时长 HH:MM:SS）

产物：
    downloads_bilibili_live/<主播名>/<日期_时间>_<标题>.mp4
    录制日志存同目录 .log；默认转 mp4 成功后删除 .flv（--keep-flv 可保留）

画质与 Cookie：
    未登录状态下 B 站**只下发主播自己推流的档位**（通常仅「原画」），
    请求蓝光/超清/高清会被服务端回落。
    在流程里输入登录 Cookie 即可解锁更多档位：
        · 输入方式：浏览器打开 live.bilibili.com 并登录 →
          F12 → Application → Cookies → 复制 SESSDATA 的值（粘值或整行都行）
        · Cookie 会缓存在同目录 .bili_cookie（已在 .gitignore 里，不会提交）
        · 也可用参数传入：--cookie "SESSDATA=xxx"，或环境变量 BILI_COOKIE
        · 不想每次问：--no-cookie
"""

import os
import re
import sys
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ 缺少 requests，请在项目虚拟环境里安装：pip install requests")
    sys.exit(1)

# ============================================================
#  配置区
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "downloads_bilibili_live"

# 登录 Cookie 本地缓存（已在 .gitignore 里忽略，不会误提交）
COOKIE_FILE = BASE_DIR / ".bili_cookie"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

API_ROOM_INIT = "https://api.live.bilibili.com/room/v1/Room/room_init"
API_ROOM_INFO = "https://api.live.bilibili.com/room/v1/Room/get_info"
API_ANCHOR = "https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room"
API_PLAY_INFO = "https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo"
API_NAV = "https://api.bilibili.com/x/web-interface/nav"   # 验证 Cookie 是否有效

# 画质编号 → 名称（B 站直播通用表）
QN_NAME = {
    30000: "杜比",
    20000: "4K",
    15000: "2K",
    10000: "原画",
    400: "蓝光",
    250: "超清",
    150: "高清",
    80: "流畅",
}

# 断流重连
MAX_RETRY = 20           # 最多重连次数
RETRY_WAIT = 3           # 每次重连前等待秒数
STALL_TIMEOUT = 20       # ffmpeg 网络读取超时（秒），超时即判为断流

# 开播轮询
WAIT_INTERVAL = 30       # 未开播时的轮询间隔（秒）

# 状态打印间隔
TICK = 1.0          # 时钟每秒走一格
REPORT_EVERY = 10   # 每 10 秒打印一行计时记录（新行打印，PyCharm 等控制台也可见）


# ============================================================
#  小工具
# ============================================================

def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def human_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def sanitize(name: str, max_len: int = 60) -> str:
    """清掉 Windows 文件名非法字符"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip(" .")
    name = re.sub(r"\s+", " ", name)
    return name[:max_len] or "未命名"


def make_session(cookie: str | None = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Referer": "https://live.bilibili.com/",
        "Origin": "https://live.bilibili.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    if cookie:
        s.headers["Cookie"] = cookie
    # B 站国内直连，绕开系统代理（避免 Clash 规则干扰）
    s.trust_env = False
    return s


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


# ============================================================
#  登录 Cookie（解锁更高画质）
# ============================================================

def load_saved_cookie() -> str | None:
    """读取本地缓存的 Cookie"""
    try:
        if COOKIE_FILE.exists():
            txt = COOKIE_FILE.read_text(encoding="utf-8").strip()
            return txt or None
    except OSError:
        pass
    return None


def save_cookie(cookie: str) -> bool:
    try:
        COOKIE_FILE.write_text(cookie.strip(), encoding="utf-8")
        return True
    except OSError as exc:
        print(f"    ⚠️  Cookie 保存失败：{exc}")
        return False


def normalize_cookie(raw: str) -> str:
    """允许用户只粘贴 SESSDATA 的值，自动补成完整 Cookie"""
    raw = raw.strip().strip('"').strip("'")
    if not raw:
        return ""
    # 已经是 k=v; k=v 形式就原样用
    if "=" in raw and ";" in raw:
        return raw
    # 只给了值（很多人只会复制 SESSDATA 的值）
    if "=" in raw and raw.split("=", 1)[0].strip().lower() in ("sessdata", "bili_jct", "dedeuserid"):
        return raw
    return f"SESSDATA={raw}"


def verify_cookie(session: requests.Session) -> tuple[bool, str]:
    """验证 Cookie 是否有效，返回 (是否有效, 用户名或原因)"""
    try:
        r = session.get(API_NAV, timeout=10).json()
        d = r.get("data") or {}
        if d.get("isLogin"):
            return True, d.get("uname") or "已登录用户"
        return False, "Cookie 无效或已过期（isLogin=false）"
    except Exception as exc:
        return False, f"验证失败：{type(exc).__name__}"


def resolve_cookie(session: requests.Session, cli_cookie: str = "",
                   no_prompt: bool = False) -> str | None:
    """
    确定本次要用的登录 Cookie，优先级：
        ① 命令行 --cookie / 环境变量 BILI_COOKIE
        ② 本地缓存 .bili_cookie
        ③ 交互式询问（除非 --no-cookie）
    """
    # ① 显式传入
    if cli_cookie:
        cookie = normalize_cookie(cli_cookie)
        session.headers["Cookie"] = cookie
        ok, who = verify_cookie(session)
        if ok:
            print(f"\n🔑 使用传入的 Cookie，已登录：{who}")
            return cookie
        print(f"\n⚠️  传入的 Cookie 无效：{who} → 按未登录状态录制（仅原画）")
        del session.headers["Cookie"]
        return None

    if no_prompt:
        print("\n⏭  已按 --no-cookie 跳过登录，按未登录状态录制（仅原画）")
        return None

    # ② 本地缓存
    saved = load_saved_cookie()
    if saved:
        session.headers["Cookie"] = saved
        ok, who = verify_cookie(session)
        if ok:
            print(f"\n🔑 已自动读取本地 Cookie（{COOKIE_FILE.name}），登录用户：{who}")
            return saved
        print(f"\n⚠️  本地 Cookie 已失效：{who}")
        try:
            del session.headers["Cookie"]
        except KeyError:
            pass

    # ③ 交互询问
    return ask_cookie_interactive(session)


def ask_cookie_interactive(session: requests.Session) -> str | None:
    """交互式询问登录 Cookie —— 用来解锁蓝光/超清/高清画质。直接回车跳过。"""
    print("\n┌─ 登录 Cookie（可选，用来解锁更高画质）─────────")
    print("│ 未登录时 B 站只下发「原画」一档，蓝光/超清/高清会被回落。")
    print("│ 获取方式：浏览器打开 live.bilibili.com 并登录 →")
    print("│   F12 → Application（应用程序）→ Cookies → 复制 SESSDATA 的值")
    print("│ 也可以直接粘贴整行 Cookie，或只粘贴 SESSDATA 的值。")
    print("└───────────────────────────────────────────────")

    try:
        raw = input("Cookie（直接回车跳过）→ ").strip()
    except EOFError:
        return None

    if not raw:
        print("⏭  已跳过，将按未登录状态录制（仅原画）")
        return None

    cookie = normalize_cookie(raw)
    session.headers["Cookie"] = cookie
    ok, who = verify_cookie(session)

    if ok:
        print(f"    ✅ Cookie 有效，已登录：{who}")
        try:
            ans = input("    是否记住到本地 .bili_cookie（下次自动读取）？[Y/n] → ").strip().lower()
        except EOFError:
            ans = "n"
        if ans in ("", "y", "yes"):
            if save_cookie(cookie):
                print(f"    💾 已保存到 {COOKIE_FILE.name}（该文件已在 .gitignore 中，不会提交）")
    else:
        print(f"    ⚠️  {who}")
        print("    ⚠️  Cookie 不可用，本次按未登录状态录制（仅原画）")
        del session.headers["Cookie"]
        return None

    return cookie


# ============================================================
#  房间解析
# ============================================================

def parse_room_id(text: str, session: requests.Session) -> int:
    """从 URL / 短链 / 纯数字里解析房间号"""
    text = text.strip()

    # 纯数字
    if text.isdigit():
        return int(text)

    # b23.tv 短链 → 跟随跳转拿真实 URL
    if "b23.tv" in text:
        try:
            resp = session.get(text, allow_redirects=True, timeout=10)
            text = resp.url
        except Exception as exc:
            print(f"⚠️  短链解析失败：{exc}")

    # live.bilibili.com/12345 或 /blanc/12345
    m = re.search(r"live\.bilibili\.com/(?:blanc/|h5/)?(\d+)", text)
    if m:
        return int(m.group(1))

    # 兜底：从任意字符串里揪出最长数字串
    nums = re.findall(r"\d{2,}", text)
    if nums:
        return int(max(nums, key=len))

    raise ValueError(f"无法从「{text}」里解析出房间号")


def resolve_room(room_id: int, session: requests.Session) -> dict:
    """取真实 room_id + 主播 + 标题 + 直播状态"""
    info = {"input_id": room_id}

    r = session.get(API_ROOM_INIT, params={"id": room_id}, timeout=10).json()
    if r.get("code") != 0:
        raise RuntimeError(f"room_init 失败：{r.get('code')} {r.get('msg')}")
    d = r["data"]
    real_id = d.get("room_id") or room_id
    info["room_id"] = real_id
    info["short_id"] = d.get("short_id")
    info["live_status"] = d.get("live_status")   # 0 未开播 / 1 直播中 / 2 轮播
    info["live_time"] = d.get("live_time")

    try:
        a = session.get(API_ANCHOR, params={"roomid": real_id}, timeout=10).json()
        info["anchor"] = ((a.get("data") or {}).get("info") or {}).get("uname") or "未知主播"
    except Exception:
        info["anchor"] = "未知主播"

    try:
        g = session.get(API_ROOM_INFO, params={"room_id": real_id}, timeout=10).json()
        gd = g.get("data") or {}
        info["title"] = gd.get("title") or "无标题"
        info["area"] = f"{gd.get('parent_name') or ''} / {gd.get('area_name') or ''}".strip(" /") or "未知分区"
        info["online"] = gd.get("online")
        info["live_status"] = gd.get("live_status", info["live_status"])
    except Exception:
        info["title"] = "无标题"
        info["area"] = "未知分区"
        info["online"] = None

    return info


def print_room(info: dict) -> None:
    status = {0: "⚫ 未开播", 1: "🔴 直播中", 2: "🔁 轮播中"}.get(info.get("live_status"), "❓ 未知")
    print()
    print("┌─ 房间信息 ─────────────────────────────")
    print(f"│ 主播   : {info.get('anchor')}")
    print(f"│ 标题   : {info.get('title')}")
    print(f"│ 分区   : {info.get('area')}")
    print(f"│ 房间号 : {info.get('room_id')}"
          + (f"（短号 {info.get('short_id')}）" if info.get("short_id") else ""))
    if info.get("online"):
        print(f"│ 人气   : {info['online']}")
    print(f"│ 状态   : {status}")
    if info.get("live_time") and info.get("live_status") == 1:
        try:
            started = datetime.fromtimestamp(int(info["live_time"]))
            print(f"│ 开播于 : {started:%Y-%m-%d %H:%M:%S}"
                  f"（已播 {human_duration(time.time() - int(info['live_time']))}）")
        except Exception:
            pass
    print("└────────────────────────────────────────")


# ============================================================
#  取流
# ============================================================

def get_play_info(room_id: int, qn: int, session: requests.Session) -> dict | None:
    """调 getRoomPlayInfo，返回规范化后的流信息"""
    params = {
        "room_id": room_id,
        "protocol": "0,1",       # 0=http_stream(flv) 1=http_hls
        "format": "0,1,2",       # flv / ts / fmp4
        "codec": "0,1",          # avc / hevc
        "qn": qn,
        "platform": "web",
        "ptype": "8",
        "dolby": "5",
        "panorama": "1",
    }
    r = session.get(API_PLAY_INFO, params=params, timeout=10).json()
    d = r.get("data") or {}
    pi = d.get("playurl_info")
    if not pi:
        return None

    playurl = pi.get("playurl") or {}
    qn_desc = {x.get("qn"): x.get("desc") for x in (playurl.get("g_qn_desc") or [])}
    streams = []
    for st in playurl.get("stream") or []:
        for fmt in st.get("format", []):
            for cd in fmt.get("codec", []):
                for ui in (cd.get("url_info") or []):
                    url = ui.get("host", "") + cd.get("base_url", "") + "?" + ui.get("extra", "")
                    streams.append({
                        "protocol": st.get("protocol_name"),          # http_stream / http_hls
                        "format": fmt.get("format_name"),             # flv / ts / fmp4
                        "codec": cd.get("codec_name"),                # avc / hevc
                        "qn": cd.get("current_qn"),
                        "accept_qn": cd.get("accept_qn") or [],
                        "url": url,
                        "stream_ttl": ui.get("stream_ttl"),
                        "host": ui.get("host"),
                    })
    return {
        "live_status": d.get("live_status"),
        "streams": streams,
        "qn_desc": qn_desc,
        "accept_qn": sorted({q for s in streams for q in s["accept_qn"]}, reverse=True),
    }


def pick_stream(info: dict, prefer: str = "flv") -> dict | None:
    """从多路流里挑一路。优先 FLV(http_stream)，其次 HLS"""
    if not info or not info.get("streams"):
        return None
    for s in info["streams"]:
        if s["protocol"] == "http_stream" and s["format"] == prefer:
            return s
    for s in info["streams"]:
        if s["protocol"] == "http_stream":
            return s
    return info["streams"][0]


def choose_quality(info: dict, default_qn: int = 10000) -> int:
    """根据服务端实际提供的档位，让用户选画质"""
    avail = info.get("accept_qn") or []
    qn_desc = info.get("qn_desc") or {}

    if not avail:
        print("⚠️  服务端未返回可用画质，默认使用原画")
        return default_qn

    label = lambda q: f"{qn_desc.get(q) or QN_NAME.get(q, str(q))}（qn={q}）"  # noqa: E731

    # 只有一档 → 直接用它，不废话
    if len(avail) == 1:
        print(f"🎚  服务端仅提供：{label(avail[0])}，已自动选择")
        if avail[0] == 10000:
            print("    💡 想要蓝光/超清/高清？需要带登录 Cookie：--cookie \"SESSDATA=...\"")
        return avail[0]

    print("\n🎚  可选画质：")
    for i, q in enumerate(avail, 1):
        print(f"    [{i}] {label(q)}")
    print("    [回车] 默认第一档")

    raw = input("    请选择 → ").strip()
    if not raw:
        return avail[0]
    try:
        idx = int(raw)
        if 1 <= idx <= len(avail):
            return avail[idx - 1]
    except ValueError:
        pass
    print("    ⚠️  输入无效，使用第一档")
    return avail[0]


def wait_for_live(room_id: int, session: requests.Session) -> bool:
    """轮询等待开播，返回 True 表示已开播"""
    print(f"\n⏳ 等待开播中（每 {WAIT_INTERVAL} 秒检查一次，Ctrl+C 取消）…")
    try:
        while True:
            r = session.get(API_ROOM_INIT, params={"id": room_id}, timeout=10).json()
            st = ((r.get("data") or {}).get("live_status"))
            if st == 1:
                print("\n🔴 开播了！开始录制")
                return True
            now = datetime.now().strftime("%H:%M:%S")
            print(f"    [{now}] 还没开播…（每 {WAIT_INTERVAL} 秒检查一次）", flush=True)
            time.sleep(WAIT_INTERVAL)
    except KeyboardInterrupt:
        print("\n⏹  已取消等待")
        return False


# ============================================================
#  录制
# ============================================================

class Recorder:
    """封装一次 ffmpeg 录制，支持优雅终止"""

    def __init__(self, out_path: Path, log_path: Path):
        self.out_path = out_path
        self.log_path = log_path
        self.proc = None
        self.log_fp = None
        self.stopping = False
    def start(self, url: str, cookie: str | None = None) -> subprocess.Popen:
        headers = (f"Referer: https://live.bilibili.com/\r\n"
                   f"User-Agent: {UA}\r\n")
        # 登录态录高画质时，部分 CDN 节点会校验 Cookie，必须一并带上
        if cookie:
            headers += f"Cookie: {cookie}\r\n"
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-rw_timeout", str(STALL_TIMEOUT * 1_000_000),   # 读超时 → 断流判定
            "-headers", headers,
            "-i", url,
            "-c", "copy",          # 不转码，CPU 几乎为 0
            "-f", "flv",
            "-flush_packets", "1",  # 每个包立即落盘：进度更准，意外中断也少丢数据
            "-y", str(self.out_path),
        ]
        self.log_fp = open(self.log_path, "w", encoding="utf-8", errors="replace")
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=self.log_fp,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return self.proc

    def stop(self, timeout: float = 10.0) -> None:
        """给 ffmpeg 发 q 让它收尾（写文件尾），失败则强杀"""
        self.stopping = True
        if not self.proc or self.proc.poll() is not None:
            return
        try:
            self.proc.stdin.write(b"q")
            self.proc.stdin.flush()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

    def wait_with_clock(self, started_at: float, deadline: float | None = None) -> None:
        """
        边录边打印计时记录：每 REPORT_EVERY 秒新打一行「⏺ 已录 HH:MM:SS」。
        不用 \r 原地刷新 —— PyCharm Run 控制台等图形控制台对 \r 支持差，
        直接新行打印在所有环境（终端/PyCharm/重定向日志）下都可见。
        deadline 不为空时到点自动返回（配合 --max-seconds）
        """
        next_report = REPORT_EVERY
        while self.proc.poll() is None:
            if deadline is not None and time.time() >= deadline:
                return
            time.sleep(TICK)
            elapsed = time.time() - started_at
            if elapsed >= next_report:
                size = self.out_path.stat().st_size if self.out_path.exists() else 0
                print(f"    ⏺ 已录 {human_duration(elapsed)}  |  "
                      f"已写盘 {human_size(size)}", flush=True)
                next_report += REPORT_EVERY


def probe_file(path: Path) -> dict:
    """用 ffprobe 验证产物可用性"""
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "format=duration,size,format_name:stream=codec_type,codec_name,width,height",
           "-of", "json", str(path)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=30)
        return json.loads(out.stdout or "{}")
    except Exception:
        return {}


def remux_to_mp4(src: Path, dst: Path) -> bool:
    """无损转封装 flv → mp4（不重新编码）"""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning",
           "-i", str(src), "-c", "copy", "-bsf:a", "aac_adtstoasc",
           "-movflags", "+faststart", "-y", str(dst)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
        return r.returncode == 0 and dst.exists() and dst.stat().st_size > 0
    except Exception as exc:
        print(f"    ⚠️  转封装异常：{exc}")
        return False


def concat_parts(parts: list[Path], dst: Path) -> bool:
    """把多个断流分片无损拼成一个 flv"""
    list_file = dst.with_suffix(".concat.txt")
    with open(list_file, "w", encoding="utf-8") as fp:
        for p in parts:
            fp.write(f"file '{p.as_posix()}'\n")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning",
           "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c", "copy", "-fflags", "+genpts", "-y", str(dst)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
        ok = r.returncode == 0 and dst.exists() and dst.stat().st_size > 0
    except Exception as exc:
        print(f"    ⚠️  合并异常：{exc}")
        ok = False
    finally:
        list_file.unlink(missing_ok=True)
    return ok


def record_live(room: dict, qn: int, session: requests.Session,
                keep_flv: bool = False, no_remux: bool = False,
                max_seconds: int = 0, cookie: str | None = None) -> Path | None:
    """
    主录制流程：取流 → 录制 → 断流重连 → 终止 → 合并 → 转 mp4
    返回最终产物路径
    """
    anchor_dir = OUTPUT_DIR / sanitize(room.get("anchor") or "未知主播", 30)
    anchor_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{stamp}_{sanitize(room.get('title') or '直播')}"
    parts: list[Path] = []

    print(f"\n📁 输出目录：{anchor_dir}")
    print("🎬 开始录制（随时按 Ctrl+C 停止并保存）\n")

    stopped_by_user = False
    retry = 0
    current: Recorder | None = None
    part_index = 0

    try:
        while True:
            # 1) 取流
            info = None
            for attempt in range(3):
                info = get_play_info(room["room_id"], qn, session)
                if info and info.get("streams"):
                    break
                print(f"    ⚠️  取流失败（第 {attempt + 1} 次），2 秒后重试…")
                time.sleep(2)
            if not info or not info.get("streams"):
                # 直播可能已结束
                st = session.get(API_ROOM_INIT, params={"id": room["room_id"]}, timeout=10).json()
                if ((st.get("data") or {}).get("live_status")) != 1:
                    print("\n📴 直播已结束，收尾中…")
                    break
                retry += 1
                if retry > MAX_RETRY:
                    print("\n❌ 连续取流失败次数过多，停止录制")
                    break
                time.sleep(RETRY_WAIT)
                continue

            stream = pick_stream(info)
            got_qn = stream.get("qn")
            qn_label = QN_NAME.get(got_qn, str(got_qn))

            part_index += 1
            if part_index == 1:
                part_path = anchor_dir / f"{base_name}.flv"
            else:
                part_path = anchor_dir / f"{base_name}.part{part_index:02d}.flv"

            if part_index == 1:
                print(f"🎚  画质：{qn_label}（qn={got_qn}） | 协议：{stream['protocol']} | 编码：{stream['codec']}")
            else:
                print(f"\n🔌 第 {part_index} 段开始（断流重连 {retry}/{MAX_RETRY}）：{qn_label}")

            # 2) 录制
            current = Recorder(part_path, part_path.with_suffix(".log"))
            started = time.time()
            current.start(stream["url"], cookie=cookie)

            aborted = False
            try:
                if max_seconds:
                    current.wait_with_clock(started, deadline=started + max_seconds)
                    if current.proc.poll() is None:
                        print("\n⏹  达到设定时长，停止录制")
                        current.stop()
                        aborted = True
                else:
                    current.wait_with_clock(started)
            except KeyboardInterrupt:
                # 关键：这里不能直接 break，否则已录好的分片会被丢掉
                print("\n\n⏹  收到停止信号，正在保存（请稍候）…")
                current.stop()
                aborted = True

            exit_code = current.proc.poll() if current.proc else None

            # 3) 收集本段产物
            if part_path.exists() and part_path.stat().st_size > 0:
                parts.append(part_path)
                print(f"\n    ✅ 本段完成：{human_size(part_path.stat().st_size)}"
                      f"（ffmpeg 退出码 {exit_code}）")
            else:
                print(f"\n    ⚠️  本段无有效数据（退出码 {exit_code}）")
                part_path.unlink(missing_ok=True)

            if aborted:
                stopped_by_user = True
                break

            # 直播是否还在？
            try:
                st = session.get(API_ROOM_INIT, params={"id": room["room_id"]}, timeout=10).json()
                if ((st.get("data") or {}).get("live_status")) != 1:
                    print("📴 直播已结束，收尾中…")
                    break
            except Exception:
                pass

            retry += 1
            if retry > MAX_RETRY:
                print(f"❌ 断流重连已达上限（{MAX_RETRY} 次），停止录制约")
                break
            print(f"    🔄 {RETRY_WAIT} 秒后重连…（第 {retry} 次）")
            time.sleep(RETRY_WAIT)

    except KeyboardInterrupt:
        print("\n\n⏹  收到停止信号，正在保存（请稍候）…")
        if current:
            current.stop()
            # 兜底：把正在录的这一段也收进来
            p = current.out_path
            if p.exists() and p.stat().st_size > 0 and p not in parts:
                parts.append(p)
        stopped_by_user = True
    finally:
        if current and current.log_fp:
            current.log_fp.close()

    # ---- 收尾 ----
    if not parts:
        print("\n❌ 没有录到任何内容")
        return None

    def drop_empty_log(p: Path) -> None:
        """ffmpeg 没报任何警告时，日志是空文件，直接删掉"""
        log = p.with_suffix(".log")
        try:
            if log.exists() and log.stat().st_size == 0:
                log.unlink()
        except OSError:
            pass

    print("\n" + "─" * 50)
    print("🧩 正在收尾…")

    # 多分片先合并
    if len(parts) > 1:
        merged = anchor_dir / f"{base_name}.flv"
        if merged.exists() and merged not in parts:
            merged.unlink()
        print(f"    合并 {len(parts)} 个分片…")
        if concat_parts(parts, merged):
            for p in parts:
                if p != merged:
                    p.unlink(missing_ok=True)
                    drop_empty_log(p)
            parts = [merged]
            print("    ✅ 合并完成")
        else:
            print("    ⚠️  合并失败，保留分片文件")

    src = parts[0]
    final = src

    # 转 mp4
    if not no_remux:
        mp4 = src.with_suffix(".mp4")
        print("    无损转封装为 mp4…")
        if remux_to_mp4(src, mp4):
            final = mp4
            print("    ✅ 转封装完成")
            if not keep_flv:
                src.unlink(missing_ok=True)
                drop_empty_log(src)
        else:
            print("    ⚠️  转封装失败，保留 .flv（文件本身可正常播放）")
    else:
        drop_empty_log(src)

    # 验证产物
    meta = probe_file(final)
    fmt = meta.get("format") or {}
    dur = float(fmt.get("duration") or 0)
    streams = meta.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)

    print("\n" + "═" * 50)
    print("🎉 录制完成")
    print(f"   文件   : {final}")
    print(f"   大小   : {human_size(final.stat().st_size)}")
    if dur:
        print(f"   时长   : {human_duration(dur)}")
    if v:
        print(f"   画面   : {v.get('width')}x{v.get('height')} / {v.get('codec_name')}")
    print(f"   停止方式: {'手动终止' if stopped_by_user else '直播结束或自动停止'}")
    print("═" * 50)
    return final


# ============================================================
#  主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="B 站直播录制器 —— 开播即录，手动终止即存",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python bilibili_live_record.py https://live.bilibili.com/1467955\n"
               "  python bilibili_live_record.py 1467955 --wait\n"
               "  python bilibili_live_record.py 1467955 --qn 400 --cookie \"SESSDATA=xxx\"\n"
    )
    parser.add_argument("target", nargs="?", help="直播间 URL 或房间号；不给则交互式输入")
    parser.add_argument("--qn", type=int, default=0, help="画质编号（10000 原画 / 400 蓝光 / 250 超清 / 150 高清）")
    parser.add_argument("--cookie", default=os.environ.get("BILI_COOKIE", ""),
                        help="登录 Cookie，用于解锁更高画质（也可用环境变量 BILI_COOKIE）")
    parser.add_argument("--no-cookie", action="store_true",
                        help="不再询问 Cookie，直接按未登录状态录制（适合脚本化调用）")
    parser.add_argument("--forget-cookie", action="store_true",
                        help="删除本地缓存的 .bili_cookie 后退出")
    parser.add_argument("--wait", action="store_true", help="未开播时等待开播")
    parser.add_argument("--list", action="store_true", help="只显示房间信息，不录制")
    parser.add_argument("--keep-flv", action="store_true", help="转 mp4 后保留 .flv 原文件")
    parser.add_argument("--no-remux", action="store_true", help="只录 flv，不做 mp4 转封装")
    parser.add_argument("--max-seconds", type=int, default=0, help="最长录制秒数（0 = 不限，靠 Ctrl+C 终止）")
    args = parser.parse_args()

    if os.name == "nt":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 50)
    print("  🎥 B 站直播录制器")
    print("=" * 50)

    if args.forget_cookie:
        if COOKIE_FILE.exists():
            COOKIE_FILE.unlink()
            print(f"🗑  已删除本地 Cookie 缓存：{COOKIE_FILE}")
        else:
            print("ℹ️  本地没有 Cookie 缓存")
        return

    if not check_ffmpeg():
        print("❌ 未检测到 ffmpeg / ffprobe，请先安装并加入 PATH")
        print("   （本项目需要 ffmpeg 才能无损录制）")
        sys.exit(1)

    session = make_session()

    # 输入
    target = args.target
    if not target:
        print("\n支持：直播 URL / 房间号 / b23.tv 短链")
        target = input("请输入直播间 → ").strip()
        if not target:
            print("❌ 未输入内容")
            sys.exit(1)

    try:
        room_id = parse_room_id(target, session)
    except ValueError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    print(f"\n🔍 解析房间 {room_id} …")
    try:
        room = resolve_room(room_id, session)
    except Exception as exc:
        print(f"❌ 房间信息获取失败：{exc}")
        sys.exit(1)

    print_room(room)

    # ---- 登录 Cookie 环节（解锁更高画质）----
    cookie = resolve_cookie(session, args.cookie, args.no_cookie)

    if args.list:
        info = get_play_info(room["room_id"], args.qn or 10000, session)
        if info:
            desc = info.get("qn_desc") or {}
            print("\n🎚  服务端可用画质：")
            for q in info.get("accept_qn") or []:
                print(f"    · {desc.get(q) or QN_NAME.get(q, q)}（qn={q}）")
            # 同类流可能有多个 CDN 节点，按 协议/格式/编码 去重展示
            seen = {}
            for s in info["streams"]:
                key = (s["protocol"], s["format"], s["codec"], s["qn"])
                seen[key] = seen.get(key, 0) + 1
            print("    ── 可用流 ──")
            for (proto, fmt, codec, q), cnt in seen.items():
                extra = f"（{cnt} 个 CDN 节点）" if cnt > 1 else ""
                print(f"    · {proto} / {fmt} / {codec} qn={q}{extra}")
            if not cookie and (info.get("accept_qn") or []) == [10000]:
                print("    💡 只有原画档：未登录状态下 B 站只下发主播推流档位")
                print("       （重跑不加 --no-cookie 即可在流程里输入 Cookie 解锁更多档位）")
        else:
            print("\n⚫ 当前无可用流（未开播）")
        return

    # 未开播
    if room.get("live_status") != 1:
        if args.wait:
            if not wait_for_live(room["room_id"], session):
                return
            room = resolve_room(room["room_id"], session)
            print_room(room)
        else:
            print("\n⚫ 主播当前未开播。")
            print("   · 想等开播自动录：加 --wait 参数")
            print("   · 想现在就录：等他开播后再跑一次")
            return

    # ---- 画质 ----
    if args.qn:
        qn = args.qn
        print(f"\n🎚  指定画质：{QN_NAME.get(qn, qn)}（qn={qn}）")
    else:
        probe = get_play_info(room["room_id"], 10000, session)
        if not probe:
            print("❌ 取流失败，主播可能刚下播")
            return
        avail = probe.get("accept_qn") or []
        if cookie and len(avail) > 1:
            print(f"\n🎉 登录后可用画质增加，共 {len(avail)} 档")
        qn = choose_quality(probe, 10000)

    try:
        record_live(room, qn, session,
                    keep_flv=args.keep_flv, no_remux=args.no_remux,
                    max_seconds=args.max_seconds, cookie=cookie)
    except Exception as exc:
        print(f"\n❌ 录制过程出错：{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
