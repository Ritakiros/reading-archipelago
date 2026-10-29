"""閱讀群島：Claude 以外的找書「連結版」測試。
用法：python3 tests/test_search_links.py [網址]   （不給網址就在本機開 http.server 測 index.html）
需要：pip install playwright && playwright install chromium
"""
import asyncio, os, sys, json, subprocess, time, urllib.parse
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.environ.get('SHOTS')  # 截圖資料夾（選用）
CAT = 'https://book.tpml.edu.tw/search?searchField='
FAILS = []

def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond: FAILS.append(msg)

def launch_args():
    exe = '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None
    return dict(executable_path=exe, args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])

async def search(pg, q):
    await pg.evaluate("()=>{const ix=document.getElementById('index');ix.hidden=false;ix.classList.remove('min')}")
    await pg.fill('#bookQ', q)
    await pg.press('#bookQ', 'Enter')
    await pg.wait_for_timeout(900)
    return await pg.evaluate("""()=>{const d=document.getElementById('detail');
      return {text:d.innerText, links:[...d.querySelectorAll('a')].map(a=>({t:a.innerText.trim(),h:a.href,tg:a.target,rel:a.rel})),
        picks:[...d.querySelectorAll('.bitem b')].map(b=>b.textContent.trim()), dim:document.querySelectorAll('#labels .dim').length}}""")

def tpml(field, q):
    return CAT + field + '&searchInput=' + urllib.parse.quote(q)

async def run(p, url, name, vp, mobile):
    print(f'[{name}] {vp["width"]}x{vp["height"]}')
    b = await p.chromium.launch(**launch_args())
    c = await b.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1,
                            locale='zh-TW', timezone_id='Asia/Taipei', color_scheme='light')
    await c.add_init_script("localStorage.setItem('ra-tour2','1')")
    pg = await c.new_page(); errs = []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(url, wait_until='networkidle', timeout=60000)
    await pg.wait_for_timeout(1500)

    # 1. 介紹文字不能宣稱會查各館館藏
    st = await pg.evaluate("""()=>({label:document.querySelector('#bookForm label').textContent,
        hint:document.getElementById('bookHint').textContent, tour:TOUR.map(x=>x.join(' ')).join(' ')})""")
    bad = ['有館藏的島', '航向有它的島', '查詢各館冊數', '查出哪幾館有']
    for k, v in st.items():
        check(not any(w in v for w in bad), f'{k} 沒有誤導字句：{v[:60]}')
    check('北市圖' in st['label'] + st['hint'], '找書區塊說明會連到北市圖館藏查詢')

    # 2. 書名 → 北市圖書名搜尋 + 博客來 + Google 圖書
    r = await search(pg, '小王子')
    if SHOTS: await pg.screenshot(path=f'{SHOTS}/{name}-小王子.png')
    main = [l for l in r['links'] if l['t'].startswith('到北市圖查「小王子」')]
    check(len(main) == 1, '有「到北市圖查「小王子」」按鈕')
    if main:
        check(main[0]['h'] == tpml('TI', '小王子'), '按鈕連到北市圖書名搜尋：' + main[0]['h'])
        check(main[0]['tg'] == '_blank' and 'noopener' in main[0]['rel'], '按鈕開新分頁並帶 noopener')
    bk = [l for l in r['links'] if '博客來' in l['t']]
    gg = [l for l in r['links'] if 'Google 圖書' in l['t']]
    check(bk and bk[0]['h'].startswith('https://search.books.com.tw/search/query/key/' + urllib.parse.quote('小王子')), '有博客來搜尋連結')
    check(gg and gg[0]['h'].startswith('https://www.google.com/search?tbm=bks&q=' + urllib.parse.quote('小王子')), '有 Google 圖書搜尋連結')
    check(all(l['tg'] == '_blank' and 'noopener' in l['rel'] for l in bk + gg), '備用連結開新分頁並帶 noopener')
    check('沒有找到館藏特色相近的島' not in r['text'] and '不能連到館藏系統' not in r['text'], '沒有像錯誤訊息的字句')
    check(r['picks'] == [], '沒有關鍵字時不推薦任何島')
    check(r['dim'] == 0, '沒有推薦時不把所有島變暗')

    # 3. ISBN（含連字號）
    r = await search(pg, '978-986-175-526-7')
    if SHOTS: await pg.screenshot(path=f'{SHOTS}/{name}-ISBN.png')
    main = [l for l in r['links'] if l['t'].startswith('到北市圖查')]
    check(bool(main) and main[0]['h'] == tpml('ISBN', '9789861755267'), 'ISBN 走 searchField=ISBN：' + (main[0]['h'] if main else '無'))
    r = await search(pg, '986175526X')
    main = [l for l in r['links'] if l['t'].startswith('到北市圖查')]
    check(bool(main) and 'searchField=ISBN' in main[0]['h'], '10 碼 ISBN（X 結尾）也走 ISBN')
    r = await search(pg, '12345678901')
    main = [l for l in r['links'] if l['t'].startswith('到北市圖查')]
    check(bool(main) and 'searchField=TI' in main[0]['h'], '11 位數字不算 ISBN')

    # 4. 關鍵字推薦：只比對完整關鍵字
    r = await search(pg, '天文學')
    if SHOTS: await pg.screenshot(path=f'{SHOTS}/{name}-天文學.png')
    check('士林分館' in r['picks'] or '東園分館' in r['picks'], '天文學 推薦天文館：' + json.dumps(r['picks'], ensure_ascii=False))
    check(not any(x in r['picks'] for x in ['道藩分館', '力行分館']), '天文學 不再推薦文學館')
    check(any(l['t'].startswith('到北市圖查「天文學」') for l in r['links']), '有推薦時仍有北市圖按鈕')
    r = await search(pg, '漫畫')
    check(r['picks'] == ['中崙分館'], '漫畫 → 中崙分館：' + json.dumps(r['picks'], ensure_ascii=False))
    r = await search(pg, '哈利波特')
    check(r['picks'] == [], '哈利波特 不推薦島')

    check(errs == [], '主控台沒有錯誤：' + json.dumps(errs, ensure_ascii=False))
    await b.close()

async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else None
    srv = None
    if not url:
        srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8799'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1); url = 'http://localhost:8799/'
    try:
        async with async_playwright() as p:
            await run(p, url, 'desktop', {'width': 1440, 'height': 900}, False)
            await run(p, url, 'mobile', {'width': 390, 'height': 844}, True)
    finally:
        if srv: srv.terminate()
    print('\n' + ('全部通過' if not FAILS else f'{len(FAILS)} 項失敗'))
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
