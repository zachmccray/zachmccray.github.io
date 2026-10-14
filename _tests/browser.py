"""Real DOM/search/browser checks against a build or an actual Jekyll server.
Only external media/SDKs are fixtures; search engine/UI/data are served unchanged.
"""
import argparse, asyncio, json, mimetypes, shutil
from functools import partial
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--site', type=Path)
parser.add_argument('--url', help='Existing localhost Jekyll server instead of --site')
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--chromium', default=shutil.which('chromium'))
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
checks = []; errors = []; destinations = []
def check(name, condition, detail=None):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
    assert condition, (name, detail)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = None
if args.url:
    assert urlparse(args.url).hostname in ('localhost', '127.0.0.1'), 'Local testing only'
    base = args.url.rstrip('/')
else:
    assert args.site, '--site or --url required'
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(args.site)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
fixture = (ROOT/'_tests/firebase-fixture.js').read_text() + '''
window.__fixture=firebaseFixture();window.firebase=__fixture.firebase;
window.__shared=[];window.__copied=[];
Object.defineProperty(navigator,'share',{configurable:true,value:async data=>__shared.push(data)});
Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async url=>__copied.push(url)}});
'''
neutral_image = '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#bbc4cd"/></svg>'
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(**({'executable_path': args.chromium} if args.chromium else {}), args=['--no-sandbox'])
        async def context(width=1440, height=900, mode=None):
            ctx = await browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
            await ctx.add_init_script(fixture)
            requests = []; faults = mode or {}; event = asyncio.Event()
            async def route(r):
                url = urlparse(r.request.url); requests.append(r.request.url)
                if url.path.endswith('/search-data.json') and faults.get('data'):
                    if faults['data']=='delay': await event.wait()
                    elif faults['data']=='503': await r.fulfill(status=503, body='fixture unavailable'); return
                    elif faults['data']=='invalid': await r.fulfill(body='{invalid'); return
                    elif faults['data']=='network': await r.abort(); return
                if url.path.endswith('/lunr.min.js') and faults.get('library'):
                    await r.abort(); return
                if '/assets/images/' in url.path:
                    await r.fulfill(content_type='image/svg+xml', body=neutral_image); return
                if url.hostname not in ('localhost', '127.0.0.1'):
                    # No real analytics, authentication, database or third-party traffic.
                    await r.fulfill(content_type='text/javascript' if r.request.resource_type=='script' else 'text/css', body=''); return
                await r.continue_()
            await ctx.route('**/*', route)
            page = await ctx.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
            return ctx, page, faults, event, requests
        # Genuine async interaction while the data request is still outstanding.
        for width,failure in [(w,f) for w in [390,1440] for f in ['delay', '503', 'invalid', 'network', 'library']]:
            c,p,mode,event,requests = await context(width=width,mode={'library':True} if failure=='library' else {'data':failure})
            await p.goto(base+'/', wait_until='domcontentloaded')
            await p.wait_for_timeout(150)
            if width<800: await p.locator('#menu-button').click()
            check(f'{failure}: no eager data/library request', not any('/search-data.json' in u or '/lunr.min.js' in u for u in requests))
            await p.locator('#search-input').fill('EECS 101')
            if failure=='delay':
                await p.wait_for_function('document.querySelector("#search-results").getAttribute("aria-busy")==="true"')
                check('Pending query has visible loading status', 'Loading search' in await p.locator('#search-results').inner_text())
                await p.screenshot(path=str(args.out/'search-loading.png')); event.set()
            else:
                await p.get_by_role('button', name='Retry search').wait_for()
                check(f'{failure}: visible error and editable preserved query', await p.locator('#search-input').input_value()=='EECS 101' and not await p.locator('#search-input').is_disabled())
                await p.screenshot(path=str(args.out/'search-error.png'))
                check(f'{width}/{failure}: retry outside the options list', await p.get_by_role('listbox').count()==0)
                await p.get_by_role('button', name='Retry search').focus(); await p.keyboard.press('Escape')
                check(f'{width}/{failure}: one Escape dismisses error from retry button', not await p.evaluate('document.documentElement.classList.contains("search-active")') and await p.locator('#search-input').input_value()=='')
                await p.locator('#search-input').fill('EECS 101')
                mode.clear(); await p.get_by_role('button', name='Retry search').focus(); await p.keyboard.press('Enter')
            result = p.locator('#search-results a[href="/courses.html#course-eecs101"]')
            await result.wait_for(state='visible')
            check(f'{width}/{failure}: genuine options list', await p.get_by_role('listbox').count()==1 and await p.locator('#search-input').get_attribute('aria-controls')=='search-results-listbox')
            check(f'{failure}: query replay and correct first result', await p.locator('.search-result').first.get_attribute('href')=='/courses.html#course-eecs101')
            await result.click(); await p.wait_for_url('**/courses.html#course-eecs101')
            await p.wait_for_function('document.activeElement.id==="course-eecs101"')
            check(f'{failure}: actual click reaches course', await p.locator('#course-eecs101').is_visible())
            await c.close()
        # Real key events must not cancel the native 100ms batches on a duplicate
        # input/keyup or an unchanged focus return. Assert the complete result set.
        for width in [390,1440]:
            c,p,_,_,_=await context(width=width)
            await p.goto(base+'/');
            if width<800: await p.locator('#menu-button').click()
            await p.locator('#search-input').fill('EECS 101')
            await p.locator('#search-results a[href="/courses.html#course-eecs101"]').wait_for(state='visible')
            await p.locator('#search-input').fill('')
            await p.locator('#search-input').press_sequentially('EECS 101')
            await p.locator('#search-input').evaluate('(e)=>e.blur()')
            await p.locator('#search-input').focus()
            await p.get_by_role('listbox').wait_for(state='visible')
            await p.wait_for_function('document.querySelectorAll("#search-results .search-result").length===18')
            check(f'{width}: all 18 native results survive duplicate events/focus return', await p.get_by_role('option').count()==18)
            await p.keyboard.press('Tab')
            check(f'{width}: Tab exits suggestions', not await p.evaluate('document.activeElement.classList.contains("search-result")'))
            await c.close()
        # Cache rejection must fall back to the native builder, not stale destinations.
        for poison in ['{broken', json.dumps({'version':'old','data':'obsolete','index':{}}), 'blocked-storage']:
            c,p,_,_,_ = await context()
            if poison=='blocked-storage':
                await c.add_init_script("Object.defineProperty(window,'sessionStorage',{get(){throw new Error('fixture disabled storage')}})")
            else:
                await p.goto(base+'/'); await p.evaluate('(x)=>sessionStorage.setItem("site-search-index-v1",x)', poison)
            await p.goto(base+'/'); await p.locator('#search-input').fill('ECON 144')
            await p.locator('#search-results a[href="/courses.html#course-econ144"]').wait_for(state='visible')
            check(f'{poison}: search survives unusable cache', True); await c.close()
        # Seed a real session index, then exercise both corruption and changed IDs.
        c,p,_,_,_=await context()
        await p.goto(base+'/'); await p.locator('#search-input').fill('EECS 101')
        await p.locator('#search-results a[href="/courses.html#course-eecs101"]').wait_for(state='visible')
        await p.wait_for_function('sessionStorage.getItem("site-search-index-v1")!==null')
        await p.evaluate("let saved=JSON.parse(sessionStorage.getItem('site-search-index-v1'));saved.index={version:'2.3.9',fields:['title','content','relUrl'],fieldVectors:[]};sessionStorage.setItem('site-search-index-v1',JSON.stringify(saved))")
        await p.goto(base+'/'); await p.locator('#search-input').fill('EECS-101')
        await p.locator('#search-results a[href="/courses.html#course-eecs101"]').wait_for(state='visible')
        await p.wait_for_function('JSON.parse(sessionStorage.getItem("site-search-index-v1")).index.fieldVectors.length>0')
        check('Matching-data corrupt index rebuilds and repairs the session entry', True)
        docs=json.loads(await (await c.request.get(base+'/assets/js/search-data.json')).text())
        changed={str(i):row for i,row in enumerate(reversed(list(docs.values())))}
        await c.route('**/assets/js/search-data.json', lambda r: r.fulfill(content_type='application/json',body=json.dumps(changed)))
        await p.goto(base+'/'); await p.locator('#search-input').fill('ECON 144')
        await p.locator('#search-results a[href="/courses.html#course-econ144"]').wait_for(state='visible')
        check('Fresh changed data invalidates a valid cache and preserves numeric-ID association', await p.locator('.search-result').first.get_attribute('href')=='/courses.html#course-econ144')
        await c.close()
        c,p,_,_,_=await context()
        await p.goto(base+'/')
        queries=json.loads((ROOT/'_tests/course-queries.json').read_text())
        async def query(value):
            if not await p.locator('#search-input').is_visible(): await p.locator('#menu-button').click()
            await p.locator('#search-input').fill(value)
        for item in queries:
            await query(item['query'])
            title=unescape(item['expected_title'])
            link=p.locator('#search-results a.search-result').filter(has=p.locator('.search-result-section', has_text=title)).first
            # Exact title association, including descriptions whose terms overlap.
            await link.wait_for(state='visible'); href=await link.get_attribute('href')
            rank=await p.locator('.search-result').evaluate_all('(es,h)=>es.findIndex(e=>e.getAttribute("href")===h)+1', href)
            check(item['query']+' association', rank>0)
            if item['kind']=='code': check(item['query']+' rank', rank==1)
            if item['kind'] in ('code','title'):
                await link.click(); await p.wait_for_url('**'+href)
                anchor=href.split('#')[1]
                await p.wait_for_function('(id)=>document.activeElement.id===id', arg=anchor)
                actual=(await p.locator('#'+anchor).inner_text()).replace('\n',' ').strip()
                check(item['query']+' click destination', actual==title)
                destinations.append({'query':item['query'],'url':href})
        check('All 45 course sections reached by code and title', len(destinations)==90 and len(set(d['url'] for d in destinations))==45)
        await c.close()
        profiles=[(w,900) for w in [320,375,390,430,600,601,768,820,1024,1280,1440,1920]]+[(375,812),(812,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820)]
        for width,height in profiles:
            c,p,_,_,_=await context(width,height); await p.goto(base+'/hobbies.html',wait_until='networkidle')
            await p.keyboard.press('Tab'); check(f'{width}x{height} first Tab', await p.locator('.skip-to-main').evaluate('(e)=>e===document.activeElement'))
            await p.keyboard.press('Enter'); check(f'{width}x{height} main focus', await p.evaluate('document.activeElement.id==="main-content"'))
            if width<800:
                await p.locator('#menu-button').focus(); await p.keyboard.press('Enter')
                await p.locator('#site-nav a.nav-list-link').last.focus(); await p.keyboard.press('Tab')
                check(f'{width}x{height} focus exit dismisses menu', await p.locator('#menu-button').get_attribute('aria-expanded')=='false')
                check(f'{width}x{height} focused content is unobscured', await p.evaluate('''()=>{const e=document.activeElement,r=e.getBoundingClientRect();return !e.closest('.side-bar')&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'''))
                await p.locator('#menu-button').click()
            await p.locator('#search-input').fill('Calculus I')
            await p.locator('#search-results a[href="/courses.html#course-math125"]').wait_for(state='visible')
            await p.locator('#search-input').press('ArrowDown'); await p.wait_for_timeout(20)
            check(f'{width}x{height} accessible active result', bool(await p.locator('#search-input').get_attribute('aria-activedescendant')))
            await p.locator('#search-input').press('Escape'); check(f'{width}x{height} Escape dismisses search', await p.locator('#search-input').get_attribute('aria-expanded')=='false')
            await p.locator('#search-input').fill('EECS 101'); await p.locator('#search-results a[href="/courses.html#course-eecs101"]').click()
            await p.wait_for_url('**/courses.html#course-eecs101'); await p.wait_for_function('document.activeElement.id==="course-eecs101"')
            box=await p.locator('#course-eecs101').bounding_box(); check(f'{width}x{height} anchor clear of header', box['y']>=51)
            await p.go_back(wait_until='networkidle'); check(f'{width}x{height} Back', '/hobbies.html' in p.url)
            await p.go_forward(wait_until='networkidle'); check(f'{width}x{height} Forward', p.url.endswith('#course-eecs101'))
            check(f'{width}x{height} no horizontal overflow', await p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            await c.close()
        c,p,_,_,_=await context(); await p.goto(base+'/travel.html',wait_until='networkidle')
        for card in await p.locator('.travel-card').all():
            like=card.locator('.like-button');await like.focus();await p.keyboard.press('Space')
            await p.wait_for_function('(id)=>document.querySelector(`.like-button[data-id="${id}"]`).getAttribute("aria-pressed")==="true"&&!document.querySelector(`.like-button[data-id="${id}"]`).disabled',arg=await like.get_attribute('data-id'))
            check('Native one-click like/count',await card.locator('.like-count').inner_text()=='1')
            await p.keyboard.press('Space')
            await p.wait_for_function('(id)=>document.querySelector(`.like-button[data-id="${id}"]`).getAttribute("aria-pressed")==="false"&&!document.querySelector(`.like-button[data-id="${id}"]`).disabled',arg=await like.get_attribute('data-id'))
            check('Native one-click unlike/count',await card.locator('.like-count').inner_text()=='0')
            await card.locator('.share-button').click()
            await p.wait_for_function('(id)=>document.querySelector(`.share-button[data-id="${id}"]`).closest(".travel-card").querySelector(".share-count").textContent==="1"', arg=await like.get_attribute('data-id'))
            check('Native share correct article title', (await p.evaluate('__shared.at(-1).title'))==(await card.locator('.travel-card-title').inner_text()))
        reads=await p.evaluate('__fixture.reads.filter(p=>p.startsWith("likes/"))')
        check('Like reads restricted to own marker/count for all nine articles', all(x.endswith('/count') or x.endswith('/users/fixture-user') or x.endswith('/receipts/fixture-user') for x in reads))
        check('No parent transactions',not await p.evaluate('__fixture.operations.some(x=>x.type==="transaction")'))
        await p.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('Dismissed','AbortError')}})")
        await p.locator('.share-button').first.click()
        check('Canceled native share is normal feedback', await p.locator('.travel-feedback').first.inner_text()=='Sharing canceled.' and not await p.locator('.share-button').first.is_disabled())
        await c.close(); await browser.close()
    check('No browser exceptions', not errors, errors)
    (args.out/'browser-results.json').write_text(json.dumps({'checks':checks,'passed':len(checks),'course_queries':len(queries),'destinations':destinations,'profiles':profiles,'errors':errors,'method':'Actual local HTTP HTML/JS/standard search JSON. SDK, network failure and missing media fixtures only; no mocked search functions.'},indent=2))
    print('Browser checks passed:',len(checks))
try: asyncio.run(main())
finally:
    if server: server.shutdown(); server.server_close()
