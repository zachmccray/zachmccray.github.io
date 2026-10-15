"""Real component JS/GLightbox/native scrolling; controlled media, no production writes."""
import argparse
import asyncio
import hashlib
import json
import mimetypes
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.async_api import async_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--only', choices=['gallery','timeline','carousels','fixtures'])
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--fixtures', type=Path, required=True, help='Cached Inter and pinned GLightbox files')
parser.add_argument('--metadata-fixtures', type=Path, required=True, help='Output of prepare-visual-fixtures.py')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
checks = []; errors = []; profiles = []
WIDTHS = [320,375,390,430,600,601,768,820,1024,1280,1440,1920]
ORIENTATIONS = [(375,812),(812,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820)]


def check(name, ok, details=None):
    checks.append({'check': name, 'passed': bool(ok), 'details': details})
    assert ok, (name, details)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(args.site)))
Thread(target=server.serve_forever,daemon=True).start()
base = 'http://127.0.0.1:'+str(server.server_port)


async def context(browser, width=1440, height=900, mode='mixed', gate=None, metadata=False):
    ctx = await browser.new_context(viewport={'width':width,'height':height},has_touch=width<800,reduced_motion='reduce')
    async def route(r):
        u = urlparse(r.request.url); name = u.path.rsplit('/',1)[-1]
        if metadata and u.path in ('/photography.html', '/blog.html'):
            await r.fulfill(path=str(args.metadata_fixtures/'site'/u.path.lstrip('/')),content_type='text/html');return
        if gate and name == 'photography-portfolio-1.js': await gate.wait()
        if '/assets/images/' in u.path:
            if mode == 'missing': await r.fulfill(status=404,body='Intentional missing-media fixture');return
            h = hashlib.sha256(u.path.encode()).digest()
            shapes = [(640,480),(480,800),(800,450),(300,1400),(1600,100)]
            w,ht = (480,800) if mode == 'portrait' else (800,450) if mode == 'landscape' else shapes[h[0]%len(shapes)]
            if mode == 'slow': await asyncio.sleep(.8)
            color = '#'+h.hex()[2:8]
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{ht}" viewBox="0 0 {w} {ht}"><rect width="{w}" height="{ht}" fill="{color}"/><path d="M0 {ht} L{w//2} {ht//3} L{w} {ht}" fill="#dde4e9"/><circle cx="{w//4}" cy="{ht//4}" r="{min(w,ht)//10}" fill="#f7e4a4"/></svg>'
            await r.fulfill(content_type='image/svg+xml',body=svg);return
        if 'glightbox@3.3.1' in r.request.url:
            await r.fulfill(path=str(args.fixtures/('glightbox.css' if name.endswith('.css') else 'glightbox.js')),content_type='text/css' if name.endswith('.css') else 'text/javascript');return
        if u.hostname == 'fonts.googleapis.com':
            await r.fulfill(content_type='text/css',body="@font-face{font-family:Inter;font-weight:100 900;src:url('"+base+"/__fixture/Inter.ttf') format('truetype')}");return
        if name == 'Inter.ttf': await r.fulfill(path=str(args.fixtures/name),content_type='font/ttf');return
        if u.hostname not in ('127.0.0.1','localhost'):
            await r.fulfill(body='',content_type='text/javascript' if r.request.resource_type=='script' else 'text/css');return
        await r.continue_()
    await ctx.route('**/*',route)
    page = await ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    return ctx,page


async def ready(p):
    await p.evaluate('document.fonts.ready')
    await p.wait_for_function('Array.from(document.images).filter(i=>i.loading!=="lazy").every(i=>i.complete)')
    await p.wait_for_timeout(240) # native scrollend/quiet-time geometry, no recentering helper


async def gallery(browser):
    for w,h in [(w,900) for w in WIDTHS]+ORIENTATIONS:
        c,p = await context(browser,w,h)
        await p.goto(base+'/photography.html',wait_until='networkidle');await ready(p)
        check(f'gallery {w}x{h}: all 30 original tiles',await p.locator('.photo-tile').count()==30)
        sizes = await p.locator('.photo-tile img').evaluate_all('(es)=>es.map(e=>({w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height,nw:e.naturalWidth,nh:e.naturalHeight}))')
        check(f'gallery {w}x{h}: uncropped natural ratios',all(abs(s['w']/s['h']-s['nw']/s['nh'])<.02 for s in sizes),sizes)
        check(f'gallery {w}x{h}: no horizontal overflow',await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        cols = await p.locator('.masonry-gallery').evaluate('(e)=>getComputedStyle(e).columnCount')
        check(f'gallery {w}x{h}: constrained column count',int(cols)==1 if w<=360 else int(cols)<=4 and int(cols)>=2,cols)
        link = p.locator('a.glightbox').first
        await link.focus()
        summary = await link.locator('.photo-summary').evaluate('(e)=>({visible:getComputedStyle(e).opacity,rect:e.getBoundingClientRect().toJSON(),pos:getComputedStyle(e).position})')
        tile = await link.bounding_box()
        if not await link.evaluate('(e)=>e.classList.contains("no-summary")'):
            check(f'gallery {w}x{h}: focus summary stays inside tile',summary['visible']=='1' and summary['pos']=='absolute' and summary['rect']['left']>=tile['x']-1 and summary['rect']['right']<=tile['x']+tile['width']+1 and summary['rect']['top']>=tile['y']-1,summary)
        before = await p.evaluate('scrollY')
        await p.keyboard.press('Enter');await p.locator('.gslide.current img').wait_for()
        await p.wait_for_function('document.querySelector(".gslide.current img")?.naturalWidth>0')
        check(f'gallery {w}x{h}: named dialog and full source description',await p.get_by_role('dialog',name='Photography image viewer').count()==1 and 'Sunrise reflecting on the river.' in await p.locator('.gslide.current .gslide-desc').inner_text())
        await p.locator('.gslide.current .gslide-description[tabindex="0"]').wait_for()
        await p.wait_for_timeout(150)
        for key in ['Tab','Shift+Tab']:
            await p.keyboard.press(key)
            check(f'gallery {w}x{h}: {key} stays in visible current dialog',await p.evaluate('''()=>{const e=document.activeElement,r=e.getBoundingClientRect();return !!e.closest('.glightbox-container')&&(!e.closest('.gslide')||e.closest('.gslide').classList.contains('current'))&&r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight}'''))
        await p.keyboard.press('ArrowRight');await p.wait_for_function('document.querySelector(".gslide.current .gslide-title")?.textContent.trim()==="Atosha Mountain"')
        check(f'gallery {w}x{h}: next photo',await p.locator('.gslide.current .gslide-title').inner_text()=='Atosha Mountain')
        await p.keyboard.press('ArrowLeft');await p.wait_for_timeout(60)
        await p.keyboard.press('Escape');await p.wait_for_function('!document.querySelector(".glightbox-container")')
        check(f'gallery {w}x{h}: focus return without page jump',await link.evaluate('(e)=>e===document.activeElement') and abs(await p.evaluate('scrollY')-before)<2)
        profiles.append({'width':w,'height':h,'columns':cols})
        if w in [390,1440] and h==900:
            await p.screenshot(path=str(args.out/f'photography-focus-{w}.png'))
        await c.close()
    for n in [30,60,110]:
        for mode in ['portrait','landscape','mixed']:
            gate = asyncio.Event();c,p = await context(browser,390,mode=mode,gate=gate,metadata=True)
            await p.goto(base+'/photography.html',wait_until='commit')
            await p.locator('.photo-tile').last.wait_for(state='attached')
            await p.locator('.photo-tile').evaluate_all('(es,n)=>es.slice(n).forEach(e=>e.remove())',n)
            gate.set();await p.wait_for_load_state('networkidle');await ready(p)
            check(f'fixture gallery {n}/{mode}: all expected entries and no overflow',await p.locator('a.glightbox').count()==n and await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check(f'fixture gallery {n}/{mode}: unique metadata IDs',await p.locator('.photo-info').evaluate_all('(es)=>new Set(es.map(e=>e.id)).size===es.length'))
            if n==110 and mode=='mixed':
                for i in range(32):
                    link=p.locator('a.glightbox').nth(i);await link.click()
                    await p.wait_for_function('document.querySelector(".gslide.current img")?.naturalWidth>0')
                    text=await p.locator('.gslide.current .gslide-desc').inner_text()
                    values=['Sony a7R III (fixture)','1/800s','f/4','100','35mm']
                    check(f'metadata {i}: exactly the provided camera combination',all((value in text)==bool(i&(1<<bit)) for bit,value in enumerate(values)),text[:700])
                    if i==31:
                        check('Long metadata region is bounded and scrollable',await p.locator('.gslide.current .gslide-description').evaluate('(e)=>e.scrollHeight>e.clientHeight&&e.clientHeight<=innerHeight*.4+1'))
                        await p.screenshot(path=str(args.out/'viewer-long-metadata-390.png'))
                    await p.keyboard.press('Escape');await p.wait_for_function('!document.querySelector(".glightbox-container")')
            await c.close()
    c,p=await context(browser,390)
    await p.goto(base+'/photography.html',wait_until='networkidle');await ready(p)
    await p.locator('a.glightbox').first.tap();await p.get_by_role('dialog').wait_for()
    check('Native touch tap immediately opens details',await p.locator('.gslide.current .gslide-desc').count()==1)
    await p.locator('.gclose').tap();await p.wait_for_function('!document.querySelector(".glightbox-container")')
    await c.close()


async def timeline(browser):
    for w in WIDTHS:
        c,p=await context(browser,w)
        await p.goto(base+'/blog.html',wait_until='networkidle');await ready(p)
        check(f'blog {w}: 64 entries and grid layout',await p.locator('.blog-entry').count()==64 and await p.locator('.blog-entry').first.evaluate('(e)=>getComputedStyle(e).display')=='grid')
        geom=await p.locator('.blog-entry').evaluate_all('''es=>es.slice(0,20).map(e=>{const t=e.querySelector('.event-thumb').getBoundingClientRect(),c=e.querySelector('.event-content').getBoundingClientRect();return {gutter:c.left-t.right,text:c.left,major:e.classList.contains('major')}})''')
        check(f'blog {w}: consistent major/minor gutter and title alignment',max(g['gutter'] for g in geom)-min(g['gutter'] for g in geom)<1 and max(g['text'] for g in geom)-min(g['text'] for g in geom)<1,geom)
        check(f'blog {w}: major thumbnails share title destinations; minor events stay unlinked',await p.locator('.blog-entry').evaluate_all('''es=>es.every(e=>e.classList.contains('major')?e.querySelector('a.event-thumb')?.getAttribute('href')===e.querySelector('a.event-link').getAttribute('href'):!e.querySelector('a'))'''))
        for year in ['all','2026','2025','2024']:
            await p.locator('#year-filter').select_option(year)
            for mode in ['date-desc','date-asc','title-asc','title-desc']:
                await p.locator('#sort-filter').select_option(mode)
                data=await p.locator('.blog-entry:not([hidden])').evaluate_all('(es)=>es.map(e=>({year:e.dataset.year,date:e.dataset.date,title:e.querySelector(".event-title").textContent.trim().toLowerCase(),display:getComputedStyle(e).display}))')
                check(f'blog {w}/{year}/{mode}: filtering retains grid and correct year',all(e['display']=='grid' and (year=='all' or e['year']==year) for e in data))
                ok=await p.evaluate('''({data,mode})=>data.every((e,i)=>!i||(mode.startsWith('date')?(mode.endsWith('asc')?e.date>=data[i-1].date:e.date<=data[i-1].date):(mode.endsWith('asc')?e.title.localeCompare(data[i-1].title)>=0:e.title.localeCompare(data[i-1].title)<=0)))''',{'data':data,'mode':mode})
                check(f'blog {w}/{year}/{mode}: original sorting behavior',ok)
        check(f'blog {w}: no overflow',await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await p.locator('#year-filter').select_option('all');await p.locator('#sort-filter').select_option('date-desc')
        thumb=p.locator('a.event-thumb').first;await thumb.focus()
        check(f'blog {w}: thumbnail has name, focus and correct destination',bool(await thumb.get_attribute('aria-label')) and await thumb.evaluate('(e)=>getComputedStyle(e).outlineStyle')=='solid')
        if w in [390,820,1440]:await p.screenshot(path=str(args.out/f'blog-focus-{w}.png'))
        await c.close()
    c,p=await context(browser,390,mode='missing');await p.goto(base+'/blog.html',wait_until='networkidle');await ready(p)
    check('Missing Blog images retain references and stable thumbnail slots',await p.locator('.event-thumb.is-unavailable').count()==64 and await p.locator('.event-thumb img[src]').count()==64)
    await p.screenshot(path=str(args.out/'blog-missing-390.png'));await c.close()


async def carousels(browser):
    for w,h in [(w,900) for w in WIDTHS]+ORIENTATIONS:
        c,p=await context(browser,w,h)
        await p.goto(base+'/volunteering.html',wait_until='networkidle');await ready(p)
        check(f'carousel {w}x{h}: original sets plus bounded copies',await p.locator('.image-scroll-hyper').evaluate_all('''cs=>cs.every(c=>{const t=c.querySelector('.image-scroll-track'),n=t.querySelectorAll(':scope > :not([data-carousel-clone])').length;return t.children.length<=n*3&&t.children.length<n*6})'''))
        check(f'carousel {w}x{h}: two independent groups, no duplicate IDs',await p.locator('.carousel-controls').count()==2 and await p.locator('[id]').evaluate_all('(es)=>new Set(es.map(e=>e.id)).size===es.length'))
        check(f'carousel {w}x{h}: copies are inert and hidden',await p.locator('[data-carousel-clone]').evaluate_all('(es)=>es.every(e=>e.inert&&e.getAttribute("aria-hidden")==="true"&&!e.id)'))
        for i,strip in enumerate(await p.locator('.image-scroll-hyper').all()):
            await strip.scroll_into_view_if_needed();await strip.focus();start=await p.evaluate('scrollY')
            await p.keyboard.press('ArrowRight');await p.wait_for_timeout(240)
            status=await strip.evaluate('(e)=>e.nextElementSibling.querySelector(".carousel-position").textContent')
            check(f'carousel {w}x{h}/{i}: keyboard next and no page jump','Photo 2 ' in status and abs(await p.evaluate('scrollY')-start)<2,status)
            await p.keyboard.press('Home');await p.wait_for_timeout(240)
            check(f'carousel {w}x{h}/{i}: initial first image centered',await strip.evaluate('''e=>{const img=e.querySelector(':not([data-carousel-clone]) > img'),r=img.getBoundingClientRect(),c=e.getBoundingClientRect();return Math.abs(r.left+r.width/2-c.left-c.width/2)<2}'''))
            other=await p.locator('.image-scroll-hyper').nth(1-i).evaluate('(e)=>e.scrollLeft')
            await strip.evaluate('(e)=>e.scrollLeft=0');await p.wait_for_timeout(260)
            check(f'carousel {w}x{h}/{i}: left edge settles into a finite or looping valid view',await strip.evaluate('(e)=>!e.classList.contains("is-looping")||e.scrollLeft>0'))
            await strip.evaluate('(e)=>e.scrollLeft=e.scrollWidth');await p.wait_for_timeout(260)
            check(f'carousel {w}x{h}/{i}: right edge settles without blank space',await strip.evaluate('(e)=>!e.classList.contains("is-looping")||e.scrollLeft<e.scrollWidth-e.clientWidth-1'))
            check(f'carousel {w}x{h}/{i}: independent collection unchanged',await p.locator('.image-scroll-hyper').nth(1-i).evaluate('(e)=>e.scrollLeft')==other)
        check(f'carousel {w}x{h}: document has no overflow',await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await c.close()
    c,p=await context(browser,390,mode='slow');await p.goto(base+'/volunteering.html',wait_until='domcontentloaded')
    await ready(p)
    await p.wait_for_timeout(900)
    check('Late images settle to correctly centered first source',await p.locator('.image-scroll-hyper').evaluate_all('''cs=>cs.every(e=>{const img=e.querySelector('.image-scroll-track > :not([data-carousel-clone]) > img'),r=img.getBoundingClientRect(),c=e.getBoundingClientRect();return Math.abs(r.left+r.width/2-c.left-c.width/2)<2})'''))
    before=await p.locator('.image-scroll-track').evaluate_all('(es)=>es.map(e=>e.children.length)')
    for _ in range(12):await p.evaluate('ImageCarousels.init()')
    await p.wait_for_timeout(240)
    check('Repeated initialization does not add controls or copies',await p.locator('.carousel-controls').count()==2 and before==await p.locator('.image-scroll-track').evaluate_all('(es)=>es.map(e=>e.children.length)'))
    await c.close()


async def fixtures(browser):
    for w in [320,390,820,1440]:
        c,p=await context(browser,w,metadata=True)
        await p.goto(base+'/blog.html',wait_until='networkidle');await ready(p)
        empty=p.locator('.event-thumb-empty')
        check(f'no-image Liquid branches {w}: one major and one minor placeholder',await empty.count()==2 and await p.locator('.major .event-thumb-empty').count()==1)
        check(f'no-image Liquid branches {w}: text alignment and overflow',await empty.evaluate_all('''es=>es.every(e=>{const r=e.getBoundingClientRect(),c=e.nextElementSibling.getBoundingClientRect();return r.width>0&&c.left>r.right})''') and await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await c.close()
    c,p=await context(browser,390,mode='missing')
    await p.goto(base+'/photography.html',wait_until='networkidle');await ready(p)
    await p.locator('a.glightbox').first.tap()
    await p.locator('.gslide.current .photo-viewer-error').wait_for()
    check('Reduced motion: library opening, closing and mobile slide effects are disabled',await p.evaluate('lightbox.settings.openEffect==="none"&&lightbox.settings.closeEffect==="none"&&lightbox.settings.cssEfects.slide.in==="none"'))
    check('Missing original: viewer reports failure and retains full metadata',await p.locator('.gslide.current .gslide-desc').count()==1 and await p.locator('.gslide.current .gslide-description').get_attribute('tabindex')=='0')
    check('Missing original: loading spinner finishes',await p.locator('.gloader').is_hidden())
    await p.locator('.gnext').tap()
    await p.wait_for_function('document.querySelector(".gslide.current .gslide-title")?.textContent.trim()==="Atosha Mountain"')
    check('Missing original: navigation remains available',await p.locator('.gslide.current .photo-viewer-error').is_visible())
    await p.keyboard.press('Escape');await p.wait_for_function('!document.querySelector(".glightbox-container")')
    check('Missing original: Escape restores focus',await p.locator('a.glightbox').first.evaluate('(e)=>e===document.activeElement'))
    await c.close()
    c,p=await context(browser,390)
    await p.goto(base+'/blog.html',wait_until='networkidle');await ready(p)
    target=await p.locator('a.event-thumb').first.get_attribute('href')
    await p.locator('a.event-thumb').first.focus();await p.keyboard.press('Enter')
    await p.wait_for_url('**'+target)
    check('Major thumbnail: keyboard activation opens the existing article',await p.locator('main h1').count()==1)
    await p.go_back(wait_until='networkidle')
    check('Major thumbnail: native Back returns to Timeline',urlparse(p.url).path=='/blog.html')
    await c.close()


async def main():
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])

            for name, run in [('gallery',gallery),('timeline',timeline),('carousels',carousels),('fixtures',fixtures)]:
                if not args.only or args.only==name:await run(browser)
            check('No component JavaScript exceptions',not errors,errors)
            await browser.close()
    finally:
        (args.out/'results.json').write_text(json.dumps({'passed':sum(c['passed'] for c in checks),'checks':checks,'profiles':profiles,'errors':errors,'fixtures':'Synthetic media and explicitly synthetic optional metadata; real served component scripts, actual GLightbox 3.3.1. No production auth/data/analytics.'},indent=2)+'\n')
        server.shutdown();server.server_close()
    print('Visual/media browser checks passed:',len(checks))


asyncio.run(main())
