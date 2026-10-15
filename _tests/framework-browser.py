"""Real DOM/axe/native navigation checks, portable across three Playwright engines."""
import argparse,asyncio,json,os,shutil
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from framework_helpers import Site,context,ready

p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--deps',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
site=Site(a.site);checks=[];scans=[];all_errors=[];version=None;last_action='launch';failure=None
WIDTHS=[320,375,390,430,600,601,768,820,1024,1280,1440,1920]
ORIENTATIONS=[(375,812),(812,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820)]
PAGES=['/','/academics.html','/courses.html','/blog.html','/2025/10/07/japan.html','/2024/08/24/alvvays-concert.html','/travel.html','/travel/washington/','/travel/japan/','/photography.html','/volunteering.html','/hobbies.html','/media.html']
def check(name,ok,detail=None):
    global last_action
    last_action=name
    checks.append({'check':name,'passed':bool(ok),'detail':detail});assert ok,(name,detail)
async def scan(page,name):
    global last_action
    last_action='axe: '+name
    if os.getenv('GITHUB_ACTIONS'):
        print('::notice title=Framework progress::'+a.browser+'; '+last_action,flush=True)
    await page.add_script_tag(path=str(a.deps/'axe-core/axe.min.js'))
    result=await asyncio.wait_for(page.evaluate('''async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations,incomplete:r.incomplete,passes:r.passes.length}}'''),timeout=60)
    scans.append({'scenario':name,**result});check(name+' axe scan has no violations',not result['violations'],[(v['id'],[n['target'] for n in v['nodes']]) for v in result['violations']])
async def visit(browser,path,width=390,height=900,mode=None,javascript=True):
    c,page,errors,requests=await context(browser,site,a.assets,a.deps,width,height,mode,javascript)
    if javascript:await c.add_init_script("window.__layoutShifts=[];if('PerformanceObserver' in window){try{new PerformanceObserver(es=>__layoutShifts.push(...es.getEntries().filter(e=>!e.hadRecentInput).map(e=>e.value))).observe({type:'layout-shift',buffered:true})}catch(_){}}")
    response=await page.goto(site.base+path,wait_until='networkidle');check(path+' successful response',response.status==200);await ready(page)
    return c,page,errors,requests
async def close(c,errors):
    all_errors.extend(errors);await c.close()

async def main():
    global version
    async with async_playwright() as pw:
        engine=getattr(pw,a.browser);options={'args':['--no-sandbox']} if a.browser=='chromium' else {}
        if a.browser=='chromium' and shutil.which('chromium'):options['executable_path']=shutil.which('chromium')
        b=await engine.launch(**options);version=b.version
        # Full-page static and dynamic axe snapshots, using real component code.
        for width in [390,1440]:
            c,page,errors,requests=await visit(b,'/',width)
            for path in PAGES:
                await page.goto(site.base+path,wait_until='networkidle');await ready(page)
                check(f'{path}/{width}: exactly one visible H1',await page.locator('main h1:visible').count()==1)
                check(f'{path}/{width}: no overflow',await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                expected='/academics.html' if path=='/courses.html' else '/travel.html' if path.startswith('/travel/') else '/blog.html' if path.startswith('/20') else path
                active=page.locator('#site-nav a[aria-current]')
                check(f'{path}/{width}: exact/parent section indicator',await active.count()==1 and await active.get_attribute('href')==expected and await active.get_attribute('aria-current')==('location' if path!=expected else 'page'))
                await scan(page,f'{path}/{width}')
            await page.goto(site.base+'/courses.html',wait_until='networkidle');await ready(page)
            if width<800:await page.locator('#menu-button').click()
            await page.locator('#search-input').fill('EECS 101');await page.locator('.search-result').first.wait_for();await page.wait_for_timeout(400)
            await scan(page,f'search results/{width}')
            await page.screenshot(path=str(a.out/f'search-{width}.png'))
            if width<800:
                check('Search uses full header width and hides competing navigation',await page.locator('#search-results').evaluate('(e)=>e.getBoundingClientRect().width')>=width-2 and not await page.locator('#site-nav').is_visible())
            await page.locator('#search-input').focus();await page.keyboard.press('Tab')
            check(f'search/{width}: Tab reaches scrollable results and keeps popup open',await page.locator('#search-results').evaluate('(e)=>document.activeElement===e') and await page.locator('#search-results').is_visible())
            check(f'search/{width}: visible results focus',await page.locator('#search-results').evaluate('(e)=>getComputedStyle(e).outlineStyle')=='solid')
            before=await page.evaluate('scrollY');await page.keyboard.press('PageDown');await page.wait_for_timeout(80)
            check(f'search/{width}: keyboard scroll does not move article',abs(await page.evaluate('scrollY')-before)<2)
            await page.keyboard.press('Escape')
            check(f'search/{width}: Escape returns to input',await page.locator('#search-input').evaluate('(e)=>e===document.activeElement'))
            if width<800:await page.keyboard.press('Escape')
            # Exercise the real search links/keyboard selection in every engine,
            # complementing the exhaustive 45-course Chromium regression suite.
            for query,anchor in [('EECS 101','course-eecs101'),('ECON 144','course-econ144'),('Calculus I','course-math125')]:
                await page.goto(site.base+'/hobbies.html',wait_until='networkidle');await ready(page)
                if width<800:await page.locator('#menu-button').click()
                await page.locator('#search-input').fill(query)
                result=page.locator('#search-results a[href="/courses.html#'+anchor+'"]');await result.wait_for(state='visible')
                if query=='EECS 101':
                    await page.locator('#search-input').press('ArrowDown');await page.locator('#search-input').press('Enter')
                else:await result.click()
                await page.wait_for_url('**/courses.html#'+anchor);await page.wait_for_function('(id)=>document.activeElement.id===id',arg=anchor)
                check(f'search/{width}/{query}: actual result opens and focuses correct course',await page.locator('#'+anchor).evaluate('(e)=>e.tagName==="H2"&&e===document.activeElement'))
                rect=await page.locator('#'+anchor).bounding_box()
                check(f'search/{width}/{query}: destination clears sticky header',rect['y']>=40 and rect['y']<900,rect)
            await page.goto(site.base+'/photography.html',wait_until='networkidle');await ready(page)
            first=page.locator('a.glightbox').first;await first.focus();await page.keyboard.press('Enter');await page.locator('.gslide.current').wait_for();await ready(page)
            check(f'lightbox/{width}: inactive slides are inert and hidden',await page.locator('.gslide:not(.current)').evaluate_all('(es)=>es.every(e=>e.inert&&e.getAttribute("aria-hidden")==="true")'))
            await scan(page,f'lightbox/{width}')
            await page.screenshot(path=str(a.out/f'viewer-{width}.png'))
            check(f'lightbox/{width}: field labels have no duplicated punctuation',await page.locator('.gslide.current dt').evaluate_all('(es)=>es.every(e=>getComputedStyle(e,"::after").content==="none")'))
            await page.locator('.gslide.current .gslide-description').focus();await page.keyboard.press('ArrowRight');await page.wait_for_timeout(180)
            check(f'lightbox/{width}: focus never remains in hidden slide',await page.evaluate('!document.activeElement.closest("[inert]")') and await page.locator('.gslide.current').get_attribute('aria-hidden')=='false')
            await page.keyboard.press('Escape');await page.wait_for_function('!document.querySelector(".glightbox-container")')
            check(f'lightbox/{width}: original focus restored',await first.evaluate('(e)=>document.activeElement===e'))
            check(f'page/{width}: no new JS exceptions',not errors,errors);await close(c,errors)
        # Small viewport and zoom-equivalent reflow. These are CSS viewports,
        # explicitly not browser-chrome zoom or physical-device certification.
        for width,height in [(w,900) for w in WIDTHS]+ORIENTATIONS+[(640,450),(320,225)]:
            c,page,errors,requests=await visit(b,'/courses.html',width,height)
            await page.goto(site.base+'/courses.html#course-eecs101',wait_until='networkidle');await ready(page)
            rect=await page.locator('#course-eecs101').bounding_box()
            check(f'{width}x{height}: direct course anchor below header',rect['y']>=40 and rect['y']<height,rect)
            check(f'{width}x{height}: no horizontal overflow',await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            if width<800:
                await page.locator('#menu-button').click();await page.locator('#search-input').fill('Calculus I');await page.locator('.search-result').first.wait_for()
                check(f'{width}x{height}: search panel fits visible viewport',await page.locator('#search-results').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1}'))
                await page.keyboard.press('Escape');await page.keyboard.press('Escape')
            await close(c,errors)
        # Traverse existing navigation rather than replacing it with goto calls.
        c,page,errors,requests=await visit(b,'/')
        for path in ['/academics.html','/blog.html','/hobbies.html','/media.html','/photography.html','/travel.html','/volunteering.html','/']:
            await page.locator('#menu-button').click();await page.locator('#site-nav a[href="'+path+'"]').click();await page.wait_for_url(site.base+path)
            check('Primary navigation reaches '+path,urlparse(page.url).path==path)
        await page.locator('#menu-button').click();await page.locator('#site-nav a[href="/academics.html"]').click();await page.locator('main a[href="/courses.html"]').click();await page.wait_for_url('**/courses.html')
        check('Academics → Courses → parent indicator',await page.locator('#site-nav a[aria-current="location"]').get_attribute('href')=='/academics.html')
        await page.go_back(wait_until='networkidle');check('Native Back returns to Academics',urlparse(page.url).path=='/academics.html')
        await page.go_forward(wait_until='networkidle');check('Native Forward returns to Courses',urlparse(page.url).path=='/courses.html')
        await page.reload(wait_until='networkidle');check('Refresh preserves section context',await page.locator('#site-nav a[aria-current="location"]').count()==1)
        await page.goto(site.base+'/blog.html',wait_until='networkidle');await ready(page)
        await page.locator('#year-filter').select_option('2025');await page.locator('#sort-filter').select_option('title-asc')
        thumb=page.locator('.blog-entry:not([hidden]) a.event-thumb').nth(2)
        await thumb.scroll_into_view_if_needed();saved_box=await thumb.bounding_box()
        await thumb.click();await page.wait_for_load_state('networkidle')
        check('Blog article has its parent-section indicator',await page.locator('#site-nav a[aria-current="location"]').get_attribute('href')=='/blog.html')
        await page.go_back(wait_until='networkidle');await ready(page)
        check('Back restores selected Blog controls',await page.locator('#year-filter').input_value()=='2025' and await page.locator('#sort-filter').input_value()=='title-asc')
        check('Back applies restored Blog filter and title order',await page.locator('.blog-entry:not([hidden])').evaluate_all('''es=>es.length>0&&es.every((e,i)=>e.dataset.year==='2025'&&(!i||e.querySelector('.event-title').textContent.trim().toLowerCase().localeCompare(es[i-1].querySelector('.event-title').textContent.trim().toLowerCase())>=0))'''))
        returned_box=await page.locator('.blog-entry:not([hidden]) a.event-thumb').nth(2).bounding_box()
        # Routing disables HTTP cache: font reflow can change absolute scrollY.
        # Preserve the same visible item/region, without overriding native history.
        check('Back preserves filtered Timeline context and native scroll restoration',0<=returned_box['y']<=900 and abs(returned_box['y']-saved_box['y'])<135 and await page.evaluate('history.scrollRestoration')=='auto',{'before':saved_box,'after':returned_box})
        await page.go_forward(wait_until='networkidle');check('Blog Forward opens the same article',await page.locator('.post-article').count()==1)
        await page.goto(site.base+'/travel.html',wait_until='networkidle');await ready(page)
        cover=page.locator('.travel-cover').nth(5);await cover.scroll_into_view_if_needed();saved_scroll=await page.evaluate('scrollY')
        await cover.click();await page.wait_for_load_state('networkidle');await page.go_back(wait_until='networkidle');await ready(page)
        check('Travel Back preserves index scroll',abs(await page.evaluate('scrollY')-saved_scroll)<3)
        await close(c,errors)
        # Isolated service failures, with no real Firebase/authentication requests.
        for mode,path in [('no-theme','/hobbies.html'),('no-gallery','/photography.html'),('no-font','/hobbies.html'),('missing','/photography.html'),('search-failure','/courses.html')]:
            c,page,errors,requests=await visit(b,path,mode=mode)
            if mode=='no-theme':
                await page.locator('#menu-button').click()
                check('Theme failure: native menu still usable',await page.locator('#site-nav a:visible').count()==8)
                check('Theme failure: search failure is explicit',await page.locator('#search-input').is_disabled() and await page.locator('#search-input').get_attribute('placeholder')=='Search unavailable')
                await page.keyboard.press('Escape');check('Theme failure: Escape restores menu focus',await page.locator('#menu-button').evaluate('(e)=>e===document.activeElement'))
            elif mode=='no-gallery':
                check('Library failure: all 30 native metadata disclosures and original links',await page.locator('details.photo-fallback-details').count()==30 and await page.locator('a.glightbox').count()==30)
                summary=page.locator('summary').first;await summary.focus();await page.keyboard.press('Enter')
                check('Library failure: keyboard opens full original metadata',await page.locator('details[open] .photo-fallback-content').first.is_visible() and 'Sunrise reflecting on the river.' in await page.locator('details[open]').first.inner_text())
                check('Library failure: metadata IDs remain unique',await page.locator('[id]').evaluate_all('(es)=>new Set(es.map(e=>e.id)).size===es.length'))
                check('Library failure: metadata stays inside its photo column',await page.locator('details[open] dd').evaluate_all('(es)=>es.every(e=>{const r=e.getBoundingClientRect(),p=e.closest(".photo-tile").getBoundingClientRect();return r.left>=p.left&&r.right<=p.right+1})'))
                await scan(page,'Unavailable gallery library')
            elif mode=='no-font':check('Font failure: readable page still fits',await page.evaluate('document.documentElement.scrollWidth<=innerWidth') and await page.locator('main h1').is_visible())
            elif mode=='missing':
                await page.locator('a.glightbox').first.click();await page.locator('.gslide.current .photo-viewer-error').wait_for();await page.locator('.gnext').click();await page.wait_for_timeout(150)
                check('Missing media: current failed slide remains accessible',await page.locator('.gslide.current').get_attribute('aria-hidden')=='false' and await page.locator('.gloader').is_hidden())
                await page.keyboard.press('Escape');await page.wait_for_function('!document.querySelector(".glightbox-container")')
            else:
                await page.locator('#menu-button').click();await page.locator('#search-input').fill('EECS 101');await page.locator('.search-retry').wait_for()
                await scan(page,'Search failed with retry')
            check(mode+': no JS exceptions',not errors,errors);await close(c,errors)
        c,page,errors,requests=await visit(b,'/travel.html')
        check('Travel: no external icon dependency requested',not any('font-awesome' in u or 'fa-solid-900' in u or 'fa-regular-400' in u for u in requests))
        check('Travel: every action has a visible named icon',await page.locator('button svg.travel-action-icon').count()==18 and await page.locator('.travel-action-icon').evaluate_all('(es)=>es.every(e=>{const r=e.getBoundingClientRect();return r.width===18&&r.height===18})'))
        button=page.locator('.like-button').first;await page.wait_for_function('!document.querySelector(".like-button").disabled');await button.click();await page.wait_for_function('document.querySelector(".like-button").getAttribute("aria-pressed")==="true"')
        check('Like feedback: shape as well as color indicates pressed state',await button.locator('.heart-solid').evaluate('(e)=>getComputedStyle(e).display')!='none' and await button.locator('.heart-outline').evaluate('(e)=>getComputedStyle(e).display')=='none')
        await page.locator('.travel-card').first.screenshot(path=str(a.out/'travel-liked.png'))
        await button.click();await page.wait_for_function('document.querySelector(".like-button").getAttribute("aria-pressed")==="false"');await close(c,errors)
        c,page,errors,requests=await visit(b,'/',javascript=False)
        check('No JavaScript: all eight navigation links remain reachable',await page.locator('#site-nav a:visible').count()==8 and not await page.locator('#menu-button').is_visible())
        check('No JavaScript: unavailable search hidden',not await page.locator('.search').is_visible())
        await page.locator('#site-nav a[href="/academics.html"]').click();await page.wait_for_url('**/academics.html');check('No JavaScript: real navigation works',await page.locator('main h1').inner_text()=='Academics');await close(c,errors)
        check('No framework JavaScript exceptions',not all_errors,all_errors)
        await b.close()

try:asyncio.run(asyncio.wait_for(main(),timeout=600))
except Exception as error:
    failure=f'{a.browser}; last action: {last_action}; {type(error).__name__}: {error}'
    if os.getenv('GITHUB_ACTIONS'):
        # Keep the failing assertion available through GitHub's annotations API,
        # even in environments unable to fetch the artifact-storage host.
        message=failure[:6000].replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::error title=Framework browser failure::'+message,flush=True)
    raise
finally:
    (a.out/'results.json').write_text(json.dumps({'browser':a.browser,'version':version,'passed':sum(c['passed'] for c in checks),'checks':checks,'axe':scans,'errors':all_errors,'failure':failure,'limits':'Local generated site; real component/axe code. Controlled image/font/library assets; Firebase fixture only. Reflow viewports simulate 200%/400% equivalence, not browser-chrome zoom. No physical device or screen-reader certification.'},indent=2)+'\n');site.close()
print('Framework checks passed:',a.browser,len(checks))
if os.getenv('GITHUB_ACTIONS'):
    print(f'::notice title=Framework browser passed::{a.browser} {version}: {len(checks)} assertions; {len(scans)} axe scans; '
          f'{sum(len(s["violations"]) for s in scans)} violations; {sum(len(s["incomplete"]) for s in scans)} incomplete rule instances requiring manual review.',flush=True)
