"""
theCrag.com 全球攀岩数据爬虫 v2
修复：parent_url、认证cookie、grade/type分布提取
"""
import os, sys, re, json, csv, asyncio, signal, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ══════════════════════════════════════════════════════════════════
#  Paths & Config
# ══════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'theCrag' / 'data'
AREAS_CSV = DATA_DIR / 'areas_v2.csv'
ROUTES_CSV = DATA_DIR / 'routes_v2.csv'
CHECKPOINT = DATA_DIR / 'checkpoint_v2.json'

BASE_URL = 'https://www.thecrag.com'
SEEDS = [
    '/en/climbing/africa',
    '/en/climbing/antarctica',
    '/en/climbing/asia',
    '/en/climbing/arctic-region',
    '/en/climbing/central-america',
    '/en/climbing/europe',
    '/en/climbing/middle-east',
    '/en/climbing/north-america',
    '/en/climbing/oceania',
    '/en/climbing/south-america',
]

# Cookie for authentication
COOKIE = '_ga=GA1.1.984821572.1784549563; cf_clearance=h9V7pHALjVlKdqSVKuWVGCUHVz4yLZFQsRE25ZR_zwI-1784630129-1.2.1.1-gu.iq6YmSaR1GPIlCSKWnVM5pB3bOaKlQYzqS0PPr_.hOvLdhkLEcZwxQ9fYBRdxuu5C8C4rSZfIQ0VP2OlyGYxy7njtjnplefKZeVE6dNpk8NqsfrUPtt0cgOcMZ.o626F9urq35ZplM2kLW0H5xe_HFzxkjnbYn0.D_ZHk18POHXRHQMHLMX.Deo.PCUVpJm4pIWq5ni_pTfI13pFlur5_UGFR61umzoPy7WgjiZcRuMWLX0W7rLOjTglASlNnmqCmoxPjqi4WDG78OQfKFw2v5QlcbtQjCYfVNg_Ld9yuVw4ZBXCO61.iSL5XTg_2XocLG2oVAGatenwzO_b6j1szHc0oB4WVm4esJBZS7LDWMiz3AL3mDwv_EhMrdHqQ_NSflblOO7TZ.4oO5NUpAYV_d7UzV0yMq2j86D2_ZhbwZMQNGPGoZhLMv4SVLuKI; _ga_E4F0QR29VH=GS2.1.s1784630128$o2$g1$t1784630141$j47$l0$h0'

# Max items to crawl (None = unlimited)
MAX_ITEMS = 100

AREA_FIELDS = [
    'area_name', 'latitude', 'longitude', 'total_routes',
    'grade_distribution', 'type_distribution', 'bbox',
    'depth', 'is_leaf', 'parent_url', 'hierarchy', 'url',
]
ROUTE_FIELDS = [
    'name', 'grade', 'type', 'bolts', 'length', 'pitches',
    'first_ascent', 'route_setter', 'url', 'area_url',
]

EXCLUDE = ['with-grade', 'with-gear-style', 'route/', 'article/', 'image/',
           'forum/', 'user/', 'climber/', 'login', 'signup', 'about', 'contact']


def ensure_csv(path, fields):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(fields)


def append_csv(path, row, fields):
    with open(path, 'a', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=fields, extrasaction='ignore').writerow(row)


# ══════════════════════════════════════════════════════════════════
#  Checkpoint
# ══════════════════════════════════════════════════════════════════
def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'visited': [], 'queue': [], 'area_count': 0, 'route_count': 0}


def save_checkpoint(visited, queue, area_count, route_count):
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump({
            'visited': list(visited),
            'queue': list(queue),
            'area_count': area_count,
            'route_count': route_count,
        }, f)


# ══════════════════════════════════════════════════════════════════
#  URL → Hierarchy chain
# ══════════════════════════════════════════════════════════════════
def url_to_slug(url):
    """提取 /en/climbing/ 后面的部分"""
    path = url.replace(BASE_URL + '/en/climbing/', '')
    return path


def parent_url_from_url(url):
    """从 URL 推断父级 URL"""
    path = url.replace(BASE_URL + '/en/climbing/', '')
    parts = path.split('/')

    # 如果是 /en/climbing/xxx/area/id 格式，父级是 /en/climbing/xxx
    if 'area' in parts:
        idx = parts.index('area')
        if idx > 0:
            return BASE_URL + '/en/climbing/' + '/'.join(parts[:idx])

    # 否则去掉最后一段
    if len(parts) > 1:
        return BASE_URL + '/en/climbing/' + '/'.join(parts[:-1])

    return ''


# ══════════════════════════════════════════════════════════════════
#  Page parser
# ══════════════════════════════════════════════════════════════════
def parse_area(html, url, depth, parent=''):
    from scrapling.parser import Selector
    sel = Selector(html)

    title = sel.css('title::text').get('').strip()
    area_name = title.split(',')[0].strip() if title else ''

    lat = sel.css('meta[property="place:location:latitude"]::attr(content)').get('')
    lng = sel.css('meta[property="place:location:longitude"]::attr(content)').get('')

    body_text = ' '.join(sel.css('body *::text').getall())
    m = re.search(r'([\d,]+)\s*route', body_text, re.I)
    total_routes = m.group(1).replace(',', '') if m else '0'

    # BBox
    bbox = ''
    for script in sel.css('script::text').getall():
        bm = re.search(
            r'bbox:\s*\[\s*\[([-\d.]+),([-\d.]+)\]\s*,\s*\[([-\d.]+),([-\d.]+)\]\s*\]', script)
        if bm:
            bbox = ','.join(bm.groups())
            break

    # Grade distribution — 从链接提取
    gd = {}
    for link in sel.css('a[href*="/with-grade/"]'):
        txt = (link.css('::text').get('') or '').strip()
        gm = re.search(r'(\d+\.\d+[a-d]?)', txt)
        if gm:
            gd[gm.group(1)] = gd.get(gm.group(1), 0) + 1

    # Type distribution
    td_raw = {}
    TYPE_KEYWORDS = {
        'sport': 'Sport', 'trad': 'Trad', 'boulder': 'Bouldering',
        'ice': 'Ice', 'mixed': 'Mixed', 'snow': 'Snow',
        'aid': 'Aid', 'via-ferrata': 'Via Ferrata', 'alpine': 'Alpine',
    }
    for link in sel.css('a[href*="/with-gear-style/"]'):
        h = link.attrib.get('href', '').lower()
        for kw, label in TYPE_KEYWORDS.items():
            if kw in h:
                td_raw[label] = td_raw.get(label, 0) + 1
                break
    td_total = sum(td_raw.values()) or 1
    td = {}
    for label, cnt in td_raw.items():
        td[label] = {'count': cnt, 'pct': f'{cnt / td_total * 100:.1f}%'}

    # Routes from div.route
    routes = []
    for rdiv in sel.css('div.route'):
        tick_json = rdiv.attrib.get('data-route-tick', '')
        rt = {}
        if tick_json:
            try:
                rt = json.loads(tick_json)
            except (json.JSONDecodeError, TypeError):
                pass

        grade = ''
        if rt.get('gradeAtom', {}).get('grade'):
            grade = rt['gradeAtom']['grade']
        else:
            grade_el = rdiv.css('span.r-grade span')
            if grade_el:
                grade = (grade_el[0].css('::text').get('') or '').strip()
            if not grade:
                grade_el = rdiv.css('span.r-grade')
                grade = (grade_el.css('::text').get('') or '').strip() if grade_el else ''

        name = rt.get('name', '')
        if not name:
            name_el = rdiv.css('span.name')
            name = ''.join(name_el.css('::text').getall()).strip() if name_el else ''
        name = re.sub(r'^[★\s]+', '', name).strip()

        rl = rdiv.css('a[href*="/route/"]')
        href = ''
        if rl:
            href = rl[0].attrib.get('href', '')
            if not href.startswith('http'):
                href = BASE_URL + href
            if not name:
                name = ''.join(rl[0].css('::text').getall()).strip()
                name = re.sub(r'^[★\s]+', '', name).strip()

        if not href or not grade:
            continue

        rtype = rt.get('styleStub', '')
        if not rtype:
            for tag_span in rdiv.css('span.tags'):
                cls = tag_span.attrib.get('class', '').lower()
                for kw, label in TYPE_KEYWORDS.items():
                    if kw in cls:
                        rtype = label
                        break
                if rtype:
                    break

        bolts = str(rt.get('bolts', '')) if rt.get('bolts') is not None else ''

        length = ''
        dh = rt.get('displayHeight', [])
        if dh and len(dh) >= 2:
            length = f'{dh[0]}{dh[1]}'
        elif dh and len(dh) == 1:
            length = str(dh[0])
        if not length:
            attr_span = rdiv.css('span.attr')
            if attr_span:
                attr_text = (attr_span.css('::text').get('') or '').strip()
                if attr_text:
                    length = attr_text.split(',')[0].strip()

        pitches = str(rt.get('pitches', '')) if rt.get('pitches') else ''

        first_ascent = ''
        fa_who = rdiv.css('span.fa__who')
        if fa_who:
            first_ascent = fa_who[0].css('::text').get('').strip() if fa_who else ''
        if not first_ascent:
            desc_el = rdiv.css('div.markdown.desc.brief')
            if desc_el:
                desc_text = ' '.join(desc_el.css('::text').getall()).strip()
                fa_m = re.search(r'(?:FA|First\s*Ascent)[:\s]+([^\n]+)', desc_text, re.I)
                if fa_m:
                    first_ascent = fa_m.group(1).strip()

        route_setter = ''

        routes.append({
            'name': name, 'grade': grade, 'type': rtype,
            'bolts': bolts, 'length': length, 'pitches': pitches,
            'first_ascent': first_ascent, 'route_setter': route_setter,
            'url': href,
        })

    # Sub-area links
    subs = []
    seen = set()
    for a in sel.css('a'):
        href = a.attrib.get('href', '')
        text = ''.join(a.css('::text').getall()).strip()
        if '/area/' not in href or not text or len(text) >= 100:
            continue
        if any(p in href.lower() for p in EXCLUDE):
            continue
        if not href.startswith('http'):
            href = BASE_URL + href
        if '/en/' not in href:
            continue
        if href not in seen:
            seen.add(href)
            subs.append(href)

    is_leaf = '1' if routes and not subs else '0'

    return {
        'area_name': area_name,
        'latitude': lat,
        'longitude': lng,
        'total_routes': total_routes,
        'grade_distribution': json.dumps(gd, ensure_ascii=False),
        'type_distribution': json.dumps(td, ensure_ascii=False),
        'bbox': bbox,
        'depth': depth,
        'is_leaf': is_leaf,
        'parent_url': parent,
        'url': url,
        'sub_areas': subs,
        'routes': routes,
    }


# ══════════════════════════════════════════════════════════════════
#  Async crawler
# ══════════════════════════════════════════════════════════════════
async def crawl():
    from scrapling.fetchers import AsyncStealthySession

    os.makedirs(DATA_DIR, exist_ok=True)
    ensure_csv(AREAS_CSV, AREA_FIELDS)
    ensure_csv(ROUTES_CSV, ROUTE_FIELDS)

    ckpt = load_checkpoint()
    visited = set(ckpt['visited'])
    queue = list(ckpt['queue'])
    area_count = ckpt.get('area_count', 0)
    route_count = ckpt.get('route_count', 0)

    if not queue:
        queue = [(BASE_URL + s, 0, '') for s in SEEDS]

    start_time = time.time()
    total_processed = len(visited)

    print(f'=== theCrag Scraper v2 ===')
    print(f'Checkpoint: {len(visited)} visited, {len(queue)} queued')
    print(f'Max items: {MAX_ITEMS}')
    print(f'Files: {AREAS_CSV}, {ROUTES_CSV}')

    running = True
    def on_signal(sig, frame):
        nonlocal running
        print('\n[Shutting down gracefully...]')
        running = False
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    # Parse cookie string into dict
    cookie_dict = {}
    for item in COOKIE.split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            cookie_dict[k.strip()] = v.strip()

    session = AsyncStealthySession(
        headless=True,
        solve_cloudflare=True,
    )

    batch_size = 5
    save_every = 10
    processed_since_save = 0
    batch_delay = 3

    try:
        async with session:
            while queue and running:
                # Check max items
                if MAX_ITEMS and total_processed >= MAX_ITEMS:
                    print(f'\n[Max items reached: {MAX_ITEMS}]')
                    break

                batch = []
                while queue and len(batch) < batch_size:
                    item = queue.pop(0)
                    url, depth, parent = item[0], item[1], item[2] if len(item) > 2 else ''
                    if url not in visited:
                        batch.append((url, depth, parent))

                if not batch:
                    break

                print(f'\n  Batch: {len(batch)} URLs')

                async def fetch_one(url, depth, parent):
                    try:
                        page = await session.fetch(url, timeout=60000)
                        html = str(page.html_content) if hasattr(page, 'html_content') else ''
                        if not html or len(html) < 500:
                            return None
                        if 'Just a moment' in html:
                            return None
                        result = parse_area(html, url, depth, parent)
                        return result
                    except Exception as e:
                        return None

                tasks = [fetch_one(u, d, p) for u, d, p in batch]
                results = await asyncio.gather(*tasks)
                valid = sum(1 for r in results if r is not None)
                print(f'  Results: {valid} valid, {len(results) - valid} null')

                for (url, depth, parent), result in zip(batch, results):
                    visited.add(url)
                    total_processed += 1
                    if result is None:
                        continue

                    # Build hierarchy from parent chain
                    # We'll compute this in export step using parent_url links

                    area_count += 1
                    append_csv(AREAS_CSV, {k: result.get(k, '') for k in AREA_FIELDS}, AREA_FIELDS)

                    for r in result['routes']:
                        route_count += 1
                        append_csv(ROUTES_CSV, {
                            'name': r['name'], 'grade': r['grade'],
                            'type': r['type'], 'bolts': r['bolts'],
                            'length': r['length'], 'pitches': r['pitches'],
                            'first_ascent': r['first_ascent'],
                            'route_setter': r['route_setter'],
                            'url': r['url'], 'area_url': url,
                        }, ROUTE_FIELDS)

                    for sub_url in result['sub_areas']:
                        if sub_url not in visited:
                            queue.append((sub_url, depth + 1, url))

                    elapsed = time.time() - start_time
                    speed = total_processed / elapsed if elapsed > 0 else 0
                    remaining = len(queue)
                    eta_min = remaining / speed / 60 if speed > 0 else 0
                    leaf_mark = ' *' if result['is_leaf'] == '1' else ''
                    print(f'[{total_processed}/{MAX_ITEMS or "?"}] {result["area_name"][:40]} routes={len(result["routes"])} sub={len(result["sub_areas"])}{leaf_mark} ETA={eta_min:.1f}m')

                    processed_since_save += 1

                if processed_since_save >= save_every:
                    save_checkpoint(visited, queue, area_count, route_count)
                    processed_since_save = 0
                    print(f'  >> Checkpoint saved')

                await asyncio.sleep(batch_delay)

    except Exception as e:
        print(f'\n[Error] {e}')
        import traceback
        traceback.print_exc()
    finally:
        save_checkpoint(visited, queue, area_count, route_count)
        print(f'\n=== Stats ===')
        print(f'Areas: {area_count}, Routes: {route_count}, Queue: {len(queue)}')
        print(f'Checkpoint saved. Re-run to resume.')


# ══════════════════════════════════════════════════════════════════
#  Build hierarchy chains from parent_url links
# ══════════════════════════════════════════════════════════════════
def build_hierarchy():
    """Build hierarchy chains from parent_url references."""
    if not os.path.exists(AREAS_CSV):
        print('No areas CSV found')
        return

    with open(AREAS_CSV, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # Build url→name map
    url_to_name = {r['url']: r['area_name'] for r in rows}
    url_to_parent = {r['url']: r.get('parent_url', '') for r in rows}

    # Build chain for each area
    for r in rows:
        chain = []
        url = r['url']
        visited_urls = set()

        while url and url not in visited_urls:
            visited_urls.add(url)
            name = url_to_name.get(url, '')
            if name:
                chain.append(name)
            url = url_to_parent.get(url, '')

        chain.reverse()
        r['hierarchy'] = ' -> '.join(chain) if chain else r['area_name']

    # Write back
    with open(AREAS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    total = len(rows)
    with_chain = sum(1 for r in rows if '->' in r['hierarchy'])
    print(f'Hierarchy built: {with_chain}/{total} areas have multi-level chains')

    # Export
    EXPORT_DIR = PROJECT_ROOT / 'theCrag' / 'export'
    os.makedirs(EXPORT_DIR, exist_ok=True)

    with open(EXPORT_DIR / 'areas_v2.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(EXPORT_DIR / 'areas_v2.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    # Routes
    if os.path.exists(ROUTES_CSV):
        import shutil
        shutil.copy2(ROUTES_CSV, EXPORT_DIR / 'routes_v2.csv')
        with open(ROUTES_CSV, 'r', encoding='utf-8') as f:
            routes = list(csv.DictReader(f))
        with open(EXPORT_DIR / 'routes_v2.json', 'w', encoding='utf-8') as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)

    print(f'Exported to {EXPORT_DIR}')


# ══════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='theCrag Scraper v2')
    parser.add_argument('--crawl', action='store_true', help='Start/resume crawling')
    parser.add_argument('--hierarchy', action='store_true', help='Build hierarchy chains from crawled data')
    parser.add_argument('--status', action='store_true', help='Show current progress')
    parser.add_argument('--reset', action='store_true', help='Reset checkpoint')
    parser.add_argument('--max', type=int, default=100, help='Max items to crawl (default: 100)')
    args = parser.parse_args()

    MAX_ITEMS = args.max

    if args.reset:
        if os.path.exists(CHECKPOINT):
            os.remove(CHECKPOINT)
        print('Reset complete.')

    if args.status:
        ckpt = load_checkpoint()
        print(f'Visited: {len(ckpt["visited"])}, Queued: {len(ckpt["queue"])}')
        if os.path.exists(AREAS_CSV):
            area_n = sum(1 for _ in csv.DictReader(open(AREAS_CSV, 'r', encoding='utf-8')))
            print(f'Areas CSV: {area_n} rows')
        if os.path.exists(ROUTES_CSV):
            route_n = sum(1 for _ in csv.DictReader(open(ROUTES_CSV, 'r', encoding='utf-8')))
            print(f'Routes CSV: {route_n} rows')

    if args.hierarchy:
        build_hierarchy()

    if args.crawl:
        asyncio.run(crawl())
