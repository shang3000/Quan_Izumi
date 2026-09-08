"""
网站反爬机制探测 & 接单可行性评估工具

用途：
    接单前快速测试目标网站的反爬强度，输出评估报告，帮你判断
    这单能不能接、用什么技术方案、要不要加价。

使用方法：
    python anti_crawl_test.py [URL]
    不带参数运行则进入交互模式，粘贴网址回车即可。

探测项目（共约 10-15 个请求，很快）：
    1. 裸请求（无 UA）        → 是否直接拦截
    2. 浏览器 UA 伪装请求     → 是否 UA 黑名单
    3. WAF 指纹识别           → Cloudflare / 阿里云 WAF / 安全狗 / 云锁 / 宝塔 / 360
    4. JS 挑战 / 浏览器校验    → Just a moment / Checking your browser
    5. 验证码识别              → 极验 / 数美 / 同盾 / 滑块 / 图形码
    6. Cookie 挑战            → 首次 Set-Cookie 二次放行
    7. SPA 动态渲染检测        → 是否需要无头浏览器
    8. 频率限制测试            → 快速连发 8 个请求看封不封
    9. Referer 防盗链检测      → 图片资源是否有盗链保护
   10. robots.txt 情况        → 仅供参考

输出：
    - 各项探测明细（✔ 通过 / ⚠ 触发反爬）
    - 综合评分（0-100，越高越难爬）
    - 反爬等级：⭐简单 / ⭐⭐中等 / ⭐⭐⭐困难 / 💀地狱级
    - 接单建议：能不能接、技术方案、谈判要点

注意：
    - 本工具只做只读 GET 请求，不提交任何表单，不破解任何东西
    - 频率测试只发 8 个请求，对目标站点压力极小
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ============ 配置区 ============

DEFAULT_TIMEOUT = 15          # 单请求超时（秒）
FREQ_TEST_COUNT = 8           # 频率测试请求数
FREQ_TEST_INTERVAL = 0.15     # 频率测试间隔（秒），模拟快速翻页
PROBE_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

# ============ 工具函数 ============


def http_get(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """统一 GET 入口，返回 (status_code, response_headers, body_text, error)
    requests 可用则用 requests，否则退回 urllib。"""
    hdrs = {
        'User-Agent': PROBE_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    if headers:
        hdrs.update(headers)

    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
            return r.status_code, dict(r.headers), r.text, None
        except requests.RequestException as e:
            return 0, {}, '', str(e)
    else:
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                for enc in ('utf-8', 'gbk', 'latin-1'):
                    try:
                        return resp.status, dict(resp.headers), body.decode(enc), None
                    except UnicodeDecodeError:
                        continue
                return resp.status, dict(resp.headers), body.decode('utf-8', errors='replace'), None
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode('utf-8', errors='replace')
            except Exception:
                body = ''
            return e.code, dict(e.headers or {}), body, None
        except Exception as e:
            return 0, {}, '', str(e)


def norm_headers(h):
    """header 字典统一转小写键。"""
    return {k.lower(): v for k, v in h.items()}


def body_contains_any(body, keywords):
    low = (body or '').lower()
    return [kw for kw in keywords if kw.lower() in low]


# ============ 探测项目 ============


def probe_1_bare_request(url):
    """裸请求（无伪装 UA）。"""
    print('\n[1/8] 裸请求测试（无浏览器 UA）...')
    status, headers, body, err = http_get(url, headers={'User-Agent': 'python-requests/2.31.0'})
    result = {'name': '裸请求拦截', 'score': 0, 'detail': f'HTTP {status}', 'hit': False}

    if err:
        result['detail'] = f'连接失败：{err[:80]}'
        result['score'] = 15
        result['hit'] = True
    elif status == 200:
        result['detail'] = f'HTTP 200，无 UA 也能正常访问（未拦截脚本 UA）'
    elif status in (403, 412, 418):
        result['detail'] = f'HTTP {status}，裸请求被直接拦截'
        result['score'] = 15
        result['hit'] = True
    elif status == 429:
        result['detail'] = 'HTTP 429，触发频率限制'
        result['score'] = 15
        result['hit'] = True
    elif status in (503, 521):
        result['detail'] = f'HTTP {status}，疑似被 WAF 挡在门外'
        result['score'] = 12
        result['hit'] = True
    else:
        result['detail'] = f'HTTP {status}，状态异常但非典型拦截'

    mark(result)
    return result, status, headers, body, err


def probe_2_browser_ua(url):
    """浏览器 UA 伪装请求。"""
    print('[2/8] 浏览器 UA 伪装请求...')
    status, headers, body, err = http_get(url)
    result = {'name': 'UA 黑名单', 'score': 0, 'detail': f'HTTP {status}', 'hit': False}

    if err:
        result['detail'] = f'连接失败：{err[:80]}'
        result['score'] = 20
        result['hit'] = True
    elif status == 200:
        result['detail'] = 'HTTP 200，伪装 UA 即可正常访问'
    elif status in (403, 412, 418, 429, 503, 521):
        result['detail'] = f'HTTP {status}，换浏览器 UA 仍被拦截（IP 级/WAF 级封锁）'
        result['score'] = 20
        result['hit'] = True

    mark(result)
    return result, status, headers, body


def probe_3_waf(url, status, headers, body):
    """WAF 指纹识别。"""
    print('[3/8] WAF 指纹识别...')
    h = norm_headers(headers)
    body = body or ''
    result = {'name': 'WAF 防火墙', 'score': 0, 'detail': '未发现已知 WAF', 'hit': False}
    found = []

    if h.get('server', '').lower() == 'cloudflare' or 'cf-ray' in h:
        found.append('Cloudflare')
    if 'aliyunwaf' in body.lower() or 'errors.aliyun.com' in body:
        found.append('阿里云 WAF')
    if 'safedog' in body.lower() or '安全狗' in body:
        found.append('安全狗')
    if 'yunsuo' in body.lower() or '云锁' in body:
        found.append('云锁')
    if 'www.bt.cn' in body or 'btwaf' in body.lower():
        found.append('宝塔防火墙')
    if '360wzws' in body.lower() or '360网站卫士' in body or 'wzws-cid' in h:
        found.append('360 网站卫士')
    if 'lewwwaf' in body.lower() or 'ns.fwapp.net' in body:
        found.append('腾讯云 WAF')
    if 'f5 big-ip' in h.get('server', '').lower():
        found.append('F5 BIG-IP')
    if h.get('server', '').lower().startswith('waf'):
        found.append('未知 WAF（server: waf）')

    if found:
        result['detail'] = '发现：' + '、'.join(found)
        # Cloudflare 全套挑战加更多分
        if 'Cloudflare' in found and ('just a moment' in body.lower() or 'challenge-platform' in body.lower()):
            result['score'] = 25
        else:
            result['score'] = 12
        result['hit'] = True

    mark(result)
    return result


def probe_4_js_challenge(status, body):
    """JS 挑战 / 浏览器校验。"""
    print('[4/8] JS 挑战 / 浏览器校验检测...')
    body = body or ''
    result = {'name': 'JS 挑战', 'score': 0, 'detail': '未发现 JS 挑战', 'hit': False}

    sigs = body_contains_any(body, [
        'just a moment', 'checking your browser', 'enable javascript',
        '请开启 javascript', 'cdn-cgi/challenge-platform', '__cf_chl',
        'cf_chl_opt', '浏览器验证', 'browser check', 'ddos-guard',
    ])
    if sigs:
        result['detail'] = f'发现 JS 挑战特征：{", ".join(sigs[:3])}'
        result['score'] = 20
        result['hit'] = True
    mark(result)
    return result


def probe_5_captcha(body):
    """验证码检测（只在表单区域和脚本/样式引用里找，避免大页面 JS 关键字误报）。"""
    print('[5/8] 验证码 / 人机验证检测...')
    body = body or ''
    result = {'name': '验证码', 'score': 0, 'detail': '未发现验证码组件', 'hit': False}

    # 只提取 form 表单区域 + script/link 引用路径 + input 元素，正文/大段 JS 内容不参与匹配
    forms = ' '.join(re.findall(r'<form[^>]*>.*?</form>', body, re.S | re.I))
    scripts = ' '.join(re.findall(r'(?:src|href|data-src|class|id)\s*=\s*"[^"]*"', body, re.I))
    inputs = ' '.join(re.findall(r'<input[^>]*>', body, re.I))
    scope = forms + ' ' + scripts + ' ' + inputs

    vendor = []
    def has(kws, where=None):
        target = (where if where is not None else scope).lower()
        return any(kw.lower() in target for kw in kws)

    if has(['geetest', '极验']):
        vendor.append('极验 Geetest')
    if has(['shumei', '数美']):
        vendor.append('数美科技')
    if has(['tongdun', '同盾']):
        vendor.append('同盾')
    if has(['aliyun captcha', 'aliyuncaptcha', 'captcha2.aliyun']):
        vendor.append('阿里云验证码')
    if has(['tcaptcha', 'tencent captcha']):
        vendor.append('腾讯验证码')
    if has(['recaptcha']):
        vendor.append('reCAPTCHA')
    if has(['slider']):
        vendor.append('滑块验证')
    if not vendor and (has(['captcha']) or '验证码' in scope):
        vendor.append('疑似验证码（通用特征）')

    if vendor:
        result['detail'] = '发现：' + '、'.join(vendor)
        # 商用滑块/行为验证比普通图形码难得多
        hard_vendors = {'极验 Geetest', '数美科技', '同盾', '阿里云验证码', '腾讯验证码', 'reCAPTCHA'}
        result['score'] = 22 if hard_vendors & set(vendor) else 10
        result['hit'] = True
    mark(result)
    return result


def probe_6_cookie_challenge(url, status, headers):
    """Cookie 挑战：首次响应给 Cookie，带上再请求才放行。"""
    print('[6/8] Cookie 挑战检测...')
    result = {'name': 'Cookie 挑战', 'score': 0, 'detail': '未发现 Cookie 挑战', 'hit': False}
    h = norm_headers(headers)

    set_cookies = h.get('set-cookie', '')
    if set_cookies and status in (403, 412, 202, 503):
        # 带上 cookie 重试一次
        cookie_str = '; '.join(
            part.split(';')[0] for part in set_cookies.split(', ') if '=' in part
        )
        status2, _, body2, _ = http_get(url, headers={'Cookie': cookie_str})
        if status2 == 200:
            result['detail'] = f'首次 HTTP {status} 发放 Cookie，带 Cookie 重试即 200（cookie challenge）'
            result['score'] = 8
            result['hit'] = True
        else:
            result['detail'] = f'首次 HTTP {status} 发放 Cookie，但带上后仍 {status2}（不止 cookie 那么简单）'
            result['score'] = 12
            result['hit'] = True
    mark(result)
    return result


def probe_7_spa(body):
    """SPA 动态渲染检测：HTML 是否只有空壳。"""
    print('[7/8] SPA 动态渲染检测...')
    body = body or ''
    result = {'name': 'SPA 动态渲染', 'score': 0, 'detail': '静态 HTML 内容完整', 'hit': False}

    text_len = len(re.sub(r'<[^>]+>|\s', '', body))  # 去掉标签后的纯文本量
    # 兼容 <div id="app"> 和 Vue 构建产物的 <div id=app>（无引号）
    is_spa_shell = bool(re.search(r'<div[^>]*id\s*=\s*["\']?(?:app|root|__nuxt)\b', body, re.I))
    has_next_data = '__NEXT_DATA__' in body  # Next.js SSR 自带数据，不算难

    if is_spa_shell and text_len < 500 and not has_next_data:
        framework = []
        if 'vue' in body.lower() or '/js/app.' in body:
            framework.append('Vue')
        if 'react' in body.lower():
            framework.append('React')
        result['detail'] = (
            f'页面是空壳（纯文本仅 {text_len} 字符'
            + (f'，{"+".join(framework)}' if framework else '')
            + '），数据靠 JS 加载 → 需无头浏览器或逆向 XHR 接口'
            + '（注意：此类站点的反爬常在数据接口上，建议手动看一眼 XHR）'
        )
        result['score'] = 15
        result['hit'] = True
    elif text_len < 200:
        result['detail'] = f'页面纯文本量极少（{text_len} 字符），内容可疑'
        result['score'] = 8
        result['hit'] = True
    else:
        result['detail'] = f'HTML 含 {text_len} 字符纯文本，服务端渲染，requests 可直接解析'
    mark(result)
    return result


def probe_8_frequency(url):
    """频率限制测试：快速连发请求。"""
    print(f'[8/8] 频率限制测试（快速连发 {FREQ_TEST_COUNT} 个请求）...')
    result = {'name': '频率限制', 'score': 0, 'detail': '', 'hit': False}
    codes = []
    for i in range(FREQ_TEST_COUNT):
        status, _, _, _ = http_get(url)
        codes.append(status)
        if i < FREQ_TEST_COUNT - 1:
            time.sleep(FREQ_TEST_INTERVAL)

    blocked = sum(1 for c in codes if c in (403, 412, 418, 429))
    if blocked == 0:
        result['detail'] = f'状态码序列 {codes}，快速请求未触发限制'
    elif blocked < FREQ_TEST_COUNT:
        result['detail'] = f'状态码序列 {codes}，请求 {blocked} 次后被限流'
        result['score'] = 10
        result['hit'] = True
    else:
        result['detail'] = f'状态码序列 {codes}，全部被拦截（封锁非常敏感）'
        result['score'] = 18
        result['hit'] = True
    mark(result)
    return result


def probe_referer_hotlink(url, body):
    """附加项：图片 Referer 防盗链检测。"""
    print('\n[附加] Referer 防盗链检测...')
    result = {'name': '防盗链', 'score': 0, 'detail': '未发现图片资源或无防盗链', 'hit': False}

    m = re.search(r'<img[^>]+src="(https?://[^"]+\.(?:jpg|jpeg|png|webp|gif))"', body or '', re.I)
    if not m:
        mark(result)
        return result

    img_url = m.group(1)
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    s1, _, _, _ = http_get(img_url, headers={'Referer': origin})
    s2, _, _, _ = http_get(img_url, headers={'Referer': 'https://www.google.com/'})

    if s1 == 200 and s2 in (403, 412):
        result['detail'] = f'图片带本站 Referer 返回 {s1}，外站 Referer 返回 {s2} → 有防盗链（下载时带 Referer 即可绕过）'
        result['score'] = 3
        result['hit'] = True
    else:
        result['detail'] = f'图片无 Referer 校验（{s1}/{s2}）'
    mark(result)
    return result


def probe_robots(url):
    """附加项：robots.txt。"""
    print('[附加] robots.txt 检查...')
    parsed = urlparse(url)
    robots_url = f'{parsed.scheme}://{parsed.netloc}/robots.txt'
    status, _, body, _ = http_get(robots_url)
    if status == 200 and 'user-agent' in (body or '').lower():
        disallow_count = (body or '').lower().count('disallow:')
        print(f'    ℹ  存在 robots.txt（{disallow_count} 条 Disallow），爬取时注意遵守')
    else:
        print(f'    ℹ  无 robots.txt（HTTP {status}）')


def mark(result):
    icon = '⚠' if result['hit'] else '✔'
    print(f'    {icon} {result["detail"]}')


# ============ 综合评估 ============


def judge(score, results):
    """根据总分给出等级和接单建议。"""
    if score <= 10:
        level = '⭐ 简单'
        advice = [
            '✅ 放心接单，requests 直接干，半天到一天能出活',
            '技术方案：requests + BeautifulSoup，普通 headers 伪装即可',
            '报价参考：按普通爬虫单报，没必要加价',
        ]
    elif score <= 35:
        level = '⭐⭐ 中等'
        advice = [
            '✅ 可以接单，有一些反爬但都有成熟解法',
            '技术方案：requests + Session Cookie 管理 + 随机 UA，必要时分析 XHR 接口',
            '报价参考：比普通单略高一点，预留调试时间',
        ]
    elif score <= 60:
        level = '⭐⭐⭐ 困难'
        advice = [
            '⚠️ 谨慎接单，有硬反爬，工作量不小',
            '技术方案：Playwright / DrissionPage 无头浏览器，可能要处理 cookie 池、代理 IP 池',
            '报价参考：至少按普通单的 2 倍报价，写清"反爬导致的价格浮动"条款',
            '谈单要点：跟客户说明站点有防护，稳定性无法 100% 保证',
        ]
    else:
        level = '💀 地狱级'
        advice = [
            '❌ 不建议接单（除非加价很多且客户接受不稳定）',
            '原因：多重反爬叠加，需要逆向 JS / 打码平台 / 住宅代理池，维护成本极高',
            '如果客户坚持：按项目制高价报，且明确"站点改版即失效，不含长期维护"',
        ]
    return level, advice


def main():
    print('=' * 62)
    print('     网站反爬机制探测 & 接单可行性评估工具')
    print('=' * 62)

    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input('请输入目标网站 URL：').strip().strip('"').strip("'")
        if not url:
            print('未输入 URL，退出。')
            return

    if not url.startswith('http'):
        url = 'https://' + url

    print(f'\n目标：{url}')
    print(f'引擎：{"requests" if HAS_REQUESTS else "urllib（建议 pip install requests）"}')
    print(f'说明：整个探测约发送 {FREQ_TEST_COUNT + 6} 个 GET 请求，全部只读，请放心')

    # ---- 主探测 ----
    r1, s1, h1, b1, err1 = probe_1_bare_request(url)
    if err1 and 'proxy' in str(err1).lower():
        print('\n检测到网络需要代理，可先开启 Clash 再运行本工具。')

    r2, s2, h2, b2 = probe_2_browser_ua(url)

    # 后续探测基于浏览器 UA 那次的结果；如果连它都失败，就用裸请求的结果
    base_status, base_headers, base_body = s2, h2, b2
    if base_status == 0:
        base_status, base_headers, base_body = s1, h1, b1

    r3 = probe_3_waf(url, base_status, base_headers, base_body)
    r4 = probe_4_js_challenge(base_status, base_body)
    r5 = probe_5_captcha(base_body)
    r6 = probe_6_cookie_challenge(url, base_status, base_headers)
    r7 = probe_7_spa(base_body)
    r8 = probe_8_frequency(url)
    r9 = probe_referer_hotlink(url, base_body)
    probe_robots(url)

    # ---- 汇总 ----
    results = [r1, r2, r3, r4, r5, r6, r7, r8, r9]
    total = sum(r['score'] for r in results)
    level, advice = judge(total, results)

    print('\n' + '=' * 62)
    print('                    评 估 报 告')
    print('=' * 62)
    print(f'综合评分：{total} / 100')
    print(f'反爬等级：{level}')
    print('-' * 62)
    print('触发的反爬信号：')
    hits = [r for r in results if r['hit']]
    if hits:
        for r in hits:
            print(f'  ⚠ {r["name"]}（+{r["score"]} 分）')
    else:
        print('  （无 —— 站点基本裸奔）')
    print('-' * 62)
    print('接单建议：')
    for line in advice:
        print(f'  {line}')
    print('=' * 62)


if __name__ == '__main__':
    main()
