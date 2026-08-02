"""
thecrag.com Global Climbing Data Scraper
========================================
Uses Scrapling for Cloudflare bypass + concurrent crawling.

Usage:
    python scraper.py              # Run (auto-resumes from checkpoint)
    python scraper.py --reset      # Clear checkpoint and start fresh
    python scraper.py --export     # Export collected data to clean CSV/JSON
    python scraper.py --status     # Show current progress

Output:
    data/areas.csv       - Area data: name, lat/lng, routes, grade/type distribution, bbox, is_leaf
    data/routes.csv      - Route data: name, grade, type, bolts, length, pitches, first_ascent, url
    data/checkpoint.json - Resume state (auto-managed)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import asyncio
import csv
import json
import os
import re
import time
import signal
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AREAS_CSV = os.path.join(DATA_DIR, 'areas.csv')
ROUTES_CSV = os.path.join(DATA_DIR, 'routes.csv')
CHECKPOINT = os.path.join(DATA_DIR, 'checkpoint.json')
EXPORT_DIR = os.path.join(BASE_DIR, 'export')

BASE_URL = 'https://www.thecrag.com'
PROXY = 'http://127.0.0.1:7897'

# ── URL filter ─────────────────────────────────────────────────────
EXCLUDE = [
    'locate', 'topos', 'ascents', 'maps', 'photos', 'forum',
    'contributors', 'guidebooks', 'webcovers', 'climbers',
    'signup', 'login', 'processmap', 'routes', 'favorites',
    'guide', 'weather', 'accommodation', 'areas/of-area-type',
    '/route/', '/climber/', '/article/',
]

# ── Seed URLs (all continents) ─────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════
#  CSV helpers
# ══════════════════════════════════════════════════════════════════
AREA_FIELDS = [
    'area_name', 'latitude', 'longitude', 'total_routes',
    'grade_distribution', 'type_distribution', 'bbox', 'depth', 'is_leaf', 'url',
]
ROUTE_FIELDS = [
    'name', 'grade', 'type', 'bolts', 'length', 'pitches',
    'first_ascent', 'route_setter', 'url', 'area_url',
]


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
    return {'visited': [], 'queue': []}


def save_checkpoint(visited, queue):
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump({'visited': list(visited), 'queue': list(queue)}, f)


# ══════════════════════════════════════════════════════════════════
#  Page parser (Scrapling Response → dict)
# ══════════════════════════════════════════════════════════════════
def parse_area(html, url, depth):
    """Parse area page HTML string into structured dict."""
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

    # Grade distribution
    gd = {}
    for link in sel.css('a[href*="/with-grade/"]'):
        txt = (link.css('::text').get('') or '').strip()
        gm = re.search(r'(\d+\.\d+[a-d]?)', txt)
        if gm:
            gd[gm.group(1)] = gd.get(gm.group(1), 0) + 1

    # Type distribution \u2014 count all gear styles
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
    # Convert to {count, pct} format
    td_total = sum(td_raw.values()) or 1
    td = {}
    for label, cnt in td_raw.items():
        td[label] = {'count': cnt, 'pct': f'{cnt / td_total * 100:.1f}%'}

    # \u2500\u2500 Routes from div.route (use data-route-tick JSON) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    routes = []
    for rdiv in sel.css('div.route'):
        # Primary source: data-route-tick JSON attribute (most reliable)
        tick_json = rdiv.attrib.get('data-route-tick', '')
        rt = {}
        if tick_json:
            try:
                rt = json.loads(tick_json)
            except (json.JSONDecodeError, TypeError):
                pass

        # Grade from JSON or HTML
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

        # Name from JSON or HTML
        name = rt.get('name', '')
        if not name:
            name_el = rdiv.css('span.name')
            name = ''.join(name_el.css('::text').getall()).strip() if name_el else ''
        name = re.sub(r'^[\u2605\s]+', '', name).strip()

        # Route URL
        rl = rdiv.css('a[href*="/route/"]')
        href = ''
        if rl:
            href = rl[0].attrib.get('href', '')
            if not href.startswith('http'):
                href = BASE_URL + href
            if not name:
                name = ''.join(rl[0].css('::text').getall()).strip()
                name = re.sub(r'^[\u2605\s]+', '', name).strip()

        if not href or not grade:
            continue

        # Route type from JSON styleStub or HTML tags
        rtype = rt.get('styleStub', '')
        if not rtype:
            TYPE_MAP = {v.lower(): v for v in TYPE_KEYWORDS.values()}
            for tag_span in rdiv.css('span.tags'):
                cls = tag_span.attrib.get('class', '').lower()
                for kw, label in TYPE_KEYWORDS.items():
                    if kw in cls:
                        rtype = label
                        break
                if rtype:
                    break

        # Bolts from JSON
        bolts = str(rt.get('bolts', '')) if rt.get('bolts') is not None else ''

        # Length from JSON displayHeight or HTML span.attr
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

        # Pitches from JSON
        pitches = str(rt.get('pitches', '')) if rt.get('pitches') else ''

        # First ascent from dedicated span elements or description
        first_ascent = ''
        fa_who = rdiv.css('span.fa__who')
        if fa_who:
            # Get direct text only, avoid nested duplicates
            first_ascent = fa_who[0].css('::text').get('').strip() if fa_who else ''
        if not first_ascent:
            desc_el = rdiv.css('div.markdown.desc.brief')
            if desc_el:
                desc_text = ' '.join(desc_el.css('::text').getall()).strip()
                fa_m = re.search(r'(?:FA|First\s*Ascent)[:\s]+([^\n]+)', desc_text, re.I)
                if fa_m:
                    first_ascent = fa_m.group(1).strip()

        # Route setter (rarely available on area pages)
        route_setter = ''

        routes.append({
            'name': name,
            'grade': grade,
            'type': rtype,
            'bolts': bolts,
            'length': length,
            'pitches': pitches,
            'first_ascent': first_ascent,
            'route_setter': route_setter,
            'url': href,
        })

    # \u2500\u2500 Sub-area links \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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

    # Leaf node = has routes and no sub-areas (smallest area unit)
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
        'url': url,
        'sub_areas': subs,
        'routes': routes,
    }


# ══════════════════════════════════════════════════════════════════
#  Async crawler
# ══════════════════════════════════════════════════════════════════
async def crawl():
    from scrapling.fetchers import AsyncStealthySession
    import time

    os.makedirs(DATA_DIR, exist_ok=True)
    ensure_csv(AREAS_CSV, AREA_FIELDS)
    ensure_csv(ROUTES_CSV, ROUTE_FIELDS)

    ckpt = load_checkpoint()
    visited = set(ckpt['visited'])
    queue = list(ckpt['queue'])

    if not queue:
        queue = [(BASE_URL + s, 0) for s in SEEDS]

    area_count = sum(1 for _ in csv.DictReader(open(AREAS_CSV, 'r', encoding='utf-8'))) if os.path.exists(AREAS_CSV) and os.path.getsize(AREAS_CSV) > 0 else 0
    route_count = sum(1 for _ in csv.DictReader(open(ROUTES_CSV, 'r', encoding='utf-8'))) if os.path.exists(ROUTES_CSV) and os.path.getsize(ROUTES_CSV) > 0 else 0

    # 进度追踪
    start_time = time.time()
    total_processed = len(visited)
    print(f'=== theCrag Global Scraper ===')
    print(f'Checkpoint: {len(visited)} visited, {len(queue)} queued')
    print(f'Files: {AREAS_CSV}, {ROUTES_CSV}')

    # Graceful shutdown
    running = True
    def on_signal(sig, frame):
        nonlocal running
        print('\n[Shutting down gracefully...]')
        running = False
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    session = AsyncStealthySession(
        headless=True,
        solve_cloudflare=True,
    )

    batch_size = 5  # Smaller batches
    save_every = 10
    processed_since_save = 0
    batch_delay = 3  # Seconds between batches

    try:
        async with session:
            while queue and running:
                # Take a batch
                batch = []
                while queue and len(batch) < batch_size:
                    url, depth = queue.pop(0)
                    if url not in visited:
                        batch.append((url, depth))

                if not batch:
                    break

                print(f'  Batch: {len(batch)} URLs')
                for u, d in batch:
                    print(f'    {u.replace(BASE_URL, "")}')

                # Fetch all in batch concurrently
                async def fetch_one(url, depth):
                    try:
                        page = await session.fetch(url, timeout=60000)
                        html = str(page.html_content) if hasattr(page, 'html_content') else ''
                        short = url.replace(BASE_URL, '')
                        if not html or len(html) < 500:
                            return None
                        if 'Just a moment' in html:
                            return None
                        result = parse_area(html, url, depth)
                        return result
                    except Exception as e:
                        return None

                tasks = [fetch_one(u, d) for u, d in batch]
                results = await asyncio.gather(*tasks)
                print(f'  Results: {sum(1 for r in results if r is not None)} valid, {sum(1 for r in results if r is None)} null')

                for (url, depth), result in zip(batch, results):
                    visited.add(url)
                    if result is None:
                        continue

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

                    # Queue sub-areas (go deeper)
                    for sub_url in result['sub_areas']:
                        if sub_url not in visited:
                            queue.append((sub_url, depth + 1))

                    short = url.replace(BASE_URL, '')
                    leaf_mark = ' *' if result['is_leaf'] == '1' else ''
                    total_processed += 1
                    elapsed = time.time() - start_time
                    speed = total_processed / elapsed if elapsed > 0 else 0
                    eta_min = (len(queue) + len(visited)) / speed / 60 if speed > 0 else 0
                    print(f'[{area_count}A {route_count}R q={len(queue)}] d={depth} {result["area_name"][:40]} routes={len(result["routes"])} sub={len(result["sub_areas"])}{leaf_mark}')
                    print(f'  Progress: {total_processed} processed, {speed:.1f} pages/sec, ETA: {eta_min:.1f} min')

                    processed_since_save += 1

                # Save checkpoint periodically
                if processed_since_save >= save_every:
                    save_checkpoint(visited, queue)
                    processed_since_save = 0
                    print(f'  >> Checkpoint saved')

                # Delay between batches to avoid rate limiting
                await asyncio.sleep(batch_delay)

    except Exception as e:
        print(f'\n[Error] {e}')
        import traceback
        traceback.print_exc()
    finally:
        save_checkpoint(visited, queue)
        print(f'\n=== Stats ===')
        print(f'Areas: {area_count}, Routes: {route_count}, Queue: {len(queue)}')
        print(f'Checkpoint saved. Re-run to resume.')


# ══════════════════════════════════════════════════════════════════
#  Export
# ══════════════════════════════════════════════════════════════════
def export_data():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    JSON_FIELDS = {'grade_distribution', 'type_distribution'}

    for src, dst_name in [(AREAS_CSV, 'areas.csv'), (ROUTES_CSV, 'routes.csv')]:
        if not os.path.exists(src):
            print(f'Skip {src} (not found)')
            continue
        with open(src, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        # Deduplicate by URL
        seen = set()
        unique = []
        for r in rows:
            key = r.get('url', '')
            if key and key not in seen:
                seen.add(key)
                # Parse JSON string fields for proper JSON output
                for jf in JSON_FIELDS:
                    if jf in r and r[jf]:
                        try:
                            r[jf] = json.loads(r[jf])
                        except (json.JSONDecodeError, TypeError):
                            pass
                unique.append(r)

        dst = os.path.join(EXPORT_DIR, dst_name)
        if unique:
            with open(dst, 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=unique[0].keys())
                w.writeheader()
                w.writerows(unique)

        # Also JSON
        dst_json = os.path.join(EXPORT_DIR, dst_name.replace('.csv', '.json'))
        with open(dst_json, 'w', encoding='utf-8') as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

        print(f'{dst_name}: {len(unique)} rows -> {dst}, {dst_json}')


def show_status():
    ckpt = load_checkpoint()
    visited = len(ckpt['visited'])
    queued = len(ckpt['queue'])

    area_n = 0
    route_n = 0
    if os.path.exists(AREAS_CSV) and os.path.getsize(AREAS_CSV) > 0:
        with open(AREAS_CSV, 'r', encoding='utf-8') as f:
            area_n = sum(1 for _ in f) - 1
    if os.path.exists(ROUTES_CSV) and os.path.getsize(ROUTES_CSV) > 0:
        with open(ROUTES_CSV, 'r', encoding='utf-8') as f:
            route_n = sum(1 for _ in f) - 1

    print(f'Visited: {visited}, Queued: {queued}')
    print(f'Areas CSV: {area_n} rows')
    print(f'Routes CSV: {route_n} rows')


# ══════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='thecrag.com Global Scraper')
    parser.add_argument('--reset', action='store_true', help='Clear checkpoint and start fresh')
    parser.add_argument('--export', action='store_true', help='Export data to clean CSV/JSON')
    parser.add_argument('--status', action='store_true', help='Show current progress')
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.export:
        export_data()
    elif args.reset:
        for f in [AREAS_CSV, ROUTES_CSV, CHECKPOINT]:
            if os.path.exists(f):
                os.remove(f)
        print('Reset complete.')
    else:
        asyncio.run(crawl())
