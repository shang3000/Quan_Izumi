"""
Bilibili 视频下载器

使用方法：
1. 打开 B 站视频页面，F12 → Network → 找到视频请求 → 复制 Cookie 头
2. 运行脚本，粘贴 Cookie 和视频 URL
3. 自动获取 dash 格式视频流并下载

支持：
- dash 格式（视频+音频分离，1080P+）
- durl 格式（未登录降级方案）
- 自动合并视频+音频（需要 ffmpeg）
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import os
import re
import json
import subprocess
import shutil
from urllib.parse import urlparse


class BilibiliDownloader:
    """Bilibili 视频下载器"""

    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
        })

    def set_cookie(self, cookie_str):
        """设置 Cookie 字符串

        从浏览器 F12 → Network → 任意请求 → Headers → Cookie 复制
        """
        if cookie_str:
            self.session.headers['Cookie'] = cookie_str
            print(f'  Cookie 已设置（长度 {len(cookie_str)} 字符）')

    def is_cdn_url(self, url):
        """判断是否为 B 站 CDN 直链（upos/bilivideo 等）"""
        return bool(re.search(r'(upos-sz-estghw|bilivideo|upos-sz-mirror)\.com', url))

    def extract_bvid(self, url_or_bvid):
        """从 URL 或 BV 号中提取 bvid"""
        if re.match(r'^BV[\w]+$', url_or_bvid):
            return url_or_bvid
        match = re.search(r'(BV[\w]+)', url_or_bvid)
        if match:
            return match.group(1)
        return None

    def get_video_info(self, bvid):
        """获取视频信息"""
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data['code'] != 0:
            raise Exception(f"API 错误: {data.get('message', '未知错误')}")
        info = data['data']
        return {
            'bvid': bvid,
            'aid': info['aid'],
            'title': info['title'],
            'desc': info['desc'],
            'duration': info['duration'],
            'owner': info['owner']['name'],
            'pages': [
                {'cid': p['cid'], 'part': p['part'], 'duration': p['duration']}
                for p in info['pages']
            ],
        }

    def get_play_url(self, bvid, cid, qn=80):
        """获取视频播放地址

        fnval=16 请求 dash 格式（需要登录态 Cookie）
        无 Cookie 会降级为 durl 格式（480P/720P）
        """
        url = 'https://api.bilibili.com/x/player/playurl'
        params = {
            'bvid': bvid,
            'cid': cid,
            'qn': qn,
            'fnval': 16,
            'fourk': 1,
            'platform': 'pc',
        }
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data['code'] != 0:
            raise Exception(f"获取播放地址失败: {data.get('message', '未知错误')}")

        play_data = data['data']

        # dash 格式（视频+音频分离，画质更高）
        if 'dash' in play_data and play_data['dash']:
            dash = play_data['dash']
            result = {
                'format': 'dash',
                'duration': dash.get('duration', 0),
                'video_streams': [],
                'audio_streams': [],
            }
            for v in dash.get('video', []):
                result['video_streams'].append({
                    'id': v['id'],
                    'bandwidth': v['bandwidth'],
                    'codecs': v['codecs'],
                    'width': v.get('width', 0),
                    'height': v.get('height', 0),
                    'url': v['baseUrl'],
                    'backup_urls': v.get('backupUrl', []),
                })
            for a in dash.get('audio', []):
                result['audio_streams'].append({
                    'id': a['id'],
                    'bandwidth': a['bandwidth'],
                    'codecs': a['codecs'],
                    'url': a['baseUrl'],
                    'backup_urls': a.get('backupUrl', []),
                })
            result['video_streams'].sort(key=lambda x: x['id'], reverse=True)
            result['audio_streams'].sort(key=lambda x: x['bandwidth'], reverse=True)
            return result

        # durl 格式（未登录降级）
        elif 'durl' in play_data and play_data['durl']:
            result = {
                'format': 'durl',
                'duration': play_data.get('timelength', 0) // 1000,
                'segments': [],
            }
            for d in play_data['durl']:
                result['segments'].append({
                    'order': d['order'],
                    'url': d['url'],
                    'backup_urls': d.get('backup_url', []),
                    'size': d.get('size', 0),
                })
            return result

        else:
            raise Exception('无法获取播放地址')

    def _download_stream(self, url, output_path):
        """下载单个流"""
        # 先探测总大小
        total_size = 0
        try:
            head = self.session.head(url, timeout=10, allow_redirects=True)
            total_size = int(head.headers.get('Content-Length', 0))
        except Exception:
            pass

        resp = self.session.get(url, stream=True, timeout=30)
        resp.raise_for_status()

        # 从 Content-Range 获取真实总大小
        cr = resp.headers.get('Content-Range', '')
        if cr:
            m = re.match(r'bytes \d+-\d+/(\d+)', cr)
            if m:
                total_size = int(m.group(1))
        if total_size == 0:
            total_size = int(resp.headers.get('Content-Length', 0))

        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        bar = '█' * int(pct // 2) + '░' * (50 - int(pct // 2))
                        mb_done = downloaded / 1024 / 1024
                        mb_total = total_size / 1024 / 1024
                        print(f'\r  [{bar}] {pct:.1f}%  {mb_done:.1f}/{mb_total:.1f} MB', end='')
        print()
        return output_path

    def _merge_video_audio(self, video_path, audio_path, output_path):
        """合并视频和音频"""
        cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path,
               '-c:v', 'copy', '-c:a', 'copy', output_path]
        print('  正在合并视频和音频...')
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                print(f'  ffmpeg 失败，使用纯视频流')
                shutil.copy2(video_path, output_path)
            else:
                print(f'  合并完成')
        except FileNotFoundError:
            print('  未找到 ffmpeg，使用纯视频流（无音频）')
            shutil.copy2(video_path, output_path)

    def select_quality(self, play_info):
        """选择画质"""
        if play_info['format'] == 'durl':
            print('\n  渐进式格式（未登录），直接下载')
            return None, None

        vs = play_info['video_streams']
        aus = play_info['audio_streams']

        print('\n  可用画质：')
        for i, v in enumerate(vs):
            label = f'{v["height"]}P' if v['height'] else v['codecs']
            print(f'    [{i + 1}] {label} ({v["codecs"]})  {v["bandwidth"] // 1000}kbps')

        if len(vs) == 1:
            chosen_v = vs[0]
        else:
            choice = input(f'\n  选择画质 [1-{len(vs)}]，回车默认最高: ').strip()
            idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(vs) else 0
            chosen_v = vs[idx]

        chosen_a = aus[0] if aus else None
        label = f'{chosen_v["height"]}P' if chosen_v['height'] else chosen_v['codecs']
        print(f'  已选择: {label}')
        return chosen_v, chosen_a

    def download(self, url_or_bvid, quality=80, filename=None):
        """下载视频

        支持两种输入：
        1. BV 号或 B 站页面 URL → 通过 API 获取播放地址
        2. CDN 直链（upos/bilivideo）→ 直接下载
        """
        # 直接是 CDN 链接，直接下载
        if self.is_cdn_url(url_or_bvid):
            return self._download_cdn(url_or_bvid, filename)

        # BV 号或 B 站页面 URL
        bvid = self.extract_bvid(url_or_bvid)
        if not bvid:
            print('[ERROR] 无法提取 BV 号')
            return None

        print(f'\n{"=" * 60}')
        print(f'  BV 号: {bvid}')
        print(f'{"=" * 60}')

        print('\n[1/4] 获取视频信息...')
        info = self.get_video_info(bvid)
        print(f'  标题: {info["title"]}')
        print(f'  UP主: {info["owner"]}')
        print(f'  时长: {info["duration"] // 60}分{info["duration"] % 60}秒')
        print(f'  分P数: {len(info["pages"])}')

        if len(info['pages']) > 1:
            print('\n  分P列表：')
            for i, p in enumerate(info['pages']):
                print(f'    [{i + 1}] {p["part"]} ({p["duration"] // 60}分{p["duration"] % 60}秒)')
            choice = input(f'\n  选择分P [1-{len(info["pages"])}]，回车默认第1P: ').strip()
            idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(info['pages']) else 0
            page = info['pages'][idx]
        else:
            page = info['pages'][0]

        cid = page['cid']
        print(f'\n  分P: {page["part"]} (cid={cid})')

        print('\n[2/4] 获取播放地址...')
        play_info = self.get_play_url(bvid, cid, qn=quality)
        print(f'  格式: {play_info["format"].upper()}')
        if play_info['format'] == 'dash':
            print(f'  视频流: {len(play_info["video_streams"])} 个')
            print(f'  音频流: {len(play_info["audio_streams"])} 个')

        chosen_v, chosen_a = self.select_quality(play_info)

        safe_title = re.sub(r'[\\/:*?"<>|]', '_', info['title'])
        if len(info['pages']) > 1:
            safe_part = re.sub(r'[\\/:*?"<>|]', '_', page['part'])
            default_name = f'{safe_title}_{safe_part}'
        else:
            default_name = safe_title
        if filename:
            default_name = filename

        print(f'\n[3/4] 下载中...')

        temp_dir = os.path.join(self.output_dir, '.temp_' + bvid)
        os.makedirs(temp_dir, exist_ok=True)

        if play_info['format'] == 'durl':
            output_path = os.path.join(self.output_dir, f'{default_name}.mp4')
            self._download_stream(play_info['segments'][0]['url'], output_path)
            self._cleanup(temp_dir)
        else:
            video_path = os.path.join(temp_dir, 'video.m4s')
            audio_path = os.path.join(temp_dir, 'audio.m4s')

            print('\n  --- 视频流 ---')
            self._download_stream(chosen_v['url'], video_path)

            if chosen_a:
                print('\n  --- 音频流 ---')
                self._download_stream(chosen_a['url'], audio_path)

            print('\n[4/4] 合并...')
            output_path = os.path.join(self.output_dir, f'{default_name}.mp4')
            if chosen_a and os.path.exists(audio_path):
                self._merge_video_audio(video_path, audio_path, output_path)
            else:
                shutil.copy2(video_path, output_path)
            self._cleanup(temp_dir)

        print(f'\n  完成! {output_path}')
        return output_path

    def _cleanup(self, temp_dir):
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass

    def _download_cdn(self, url, filename=None):
        """直接从 CDN 链接下载"""
        # 从 URL 提取文件名
        if not filename:
            parsed = urlparse(url)
            path = parsed.path
            # 取路径最后一段，去掉扩展名前的参数
            basename = os.path.basename(path)
            basename = basename.split('?')[0]
            if '.' in basename:
                filename = basename.rsplit('.', 1)[0]
            else:
                filename = f'bilibili_{int(__import__("time").time())}'

        # 清理文件名中的特殊字符
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', filename)
        output_path = os.path.join(self.output_dir, f'{safe_name}.mp4')

        print(f'\n  CDN 直链下载')
        print(f'  文件名: {safe_name}.mp4')
        print(f'  下载中...')

        self._download_stream(url, output_path)

        print(f'\n  完成! {output_path}')
        return output_path


def main():
    print('=' * 60)
    print('  Bilibili 视频下载器')
    print('=' * 60)
    print()
    print('  支持两种输入方式：')
    print('  1. BV 号 / B 站页面 URL')
    print('  2. CDN 直链（F12 Network 中的视频请求 URL）')
    print()
    print('  获取 Cookie（可选，提高画质）：')
    print('  F12 → Network → 任意请求 → Headers → Cookie')
    print()

    cookie = input('请粘贴 Cookie（回车跳过）: ').strip()
    url = input('请粘贴链接: ').strip()

    if not url:
        print('链接不能为空！')
        return

    downloader = BilibiliDownloader()
    if cookie:
        downloader.set_cookie(cookie)
    result = downloader.download(url, quality=0)

    if result:
        print(f'\n  已保存到: {result}')
    else:
        print('\n  下载失败')


if __name__ == '__main__':
    main()
