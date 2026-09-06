# -*- coding: utf-8 -*-
"""测试超出视频上限时的兜底格式写法"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yt_dlp
yt_dlp.YoutubeDL.deprecated_feature = lambda self, message: None

URL = 'https://www.youtube.com/watch?v=eoakaJmz6vE'

with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True,
                       'extractor_args': {'youtube': {'player_client': ['tv_embedded']}}}) as ydl:
    info = ydl.extract_info(URL, download=False)
    fmts = info['formats']
    ctx = {'formats': fmts, 'id': info['id'], 'title': info.get('title'),
           'url': URL, 'webpage_url': URL}
    tests = [
        'best[height<=2160]',
        'bestvideo[height<=2160]+bestaudio',
        'bestvideo+bestaudio/best',
        # 候选完整写法A：精确宽度/高度 + 高度上限兜底
        'bestvideo[width=2160]+bestaudio/bestvideo[height=2160]+bestaudio/best[height<=2160]/best',
        # 候选完整写法B：精确匹配 + "小于等于"竖屏宽度兜底 + 高度兜底
        'bestvideo[width=2160]+bestaudio/bestvideo[height=2160]+bestaudio/'
        'bestvideo[width<=2160][height<=3840]+bestaudio/'
        'best[height<=2160]/best',
        # 候选完整写法C：精确匹配 + 综合尺寸上限兜底（w*h 面积）
        'bestvideo[width=2160]+bestaudio/bestvideo[height=2160]+bestaudio/'
        'bestvideo[width<=2160][height<=2160]+bestaudio/'
        'best[height<=2160]/best',
    ]
    for fmt in tests:
        try:
            picked = list(ydl.build_format_selector(fmt)(ctx))
            desc = ' + '.join(f'{f.get("width")}x{f.get("height")}' for f in picked)
            print(f'OK   {desc:<28} <- {fmt[:60]}')
        except Exception as e:
            print(f'FAIL {str(e)[:30]:<28} <- {fmt[:60]}')
