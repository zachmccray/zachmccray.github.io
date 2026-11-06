"""Approved editorial interactions on served builds, not isolated index mocks.

Uses the real theme/search/controllers and pinned GLightbox. Only external
services and absent photographs are fixtures. Never writes to production.
"""
import argparse, asyncio, hashlib, json, re, shutil
from pathlib import Path
from playwright.async_api import async_playwright
from framework_helpers import Site, context, ready

p=argparse.ArgumentParser()
for name in ('site','baseline','assets','deps','fixtures','out'):
    p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
p.add_argument('--only',choices=['text','carousel','screenshots'])
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
site=Site(a.site);before=Site(a.baseline);fixtures=Site(a.fixtures)
checks=[];errors=[];scans=[];shots=[];typography=[]
WIDTHS=[320,375,390,430,600,601,768,820,1024,1280,1440,1920]
ORIENTATIONS=[(375,812),(812,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820)]

def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail})
    assert ok,(name,detail)

async def visit(browser,path,width=1440,height=900,server=site,motion='reduce',touch=False,mode=None,javascript=True):
    c,page,pe,requests=await context(browser,server,a.assets,a.deps,width,height,mode,javascript,touch)
    await page.emulate_media(reduced_motion=motion)
    await page.goto(server.base+path,wait_until='networkidle')
    if javascript:await ready(page)
    return c,page,pe,requests

async def close(c,pe):errors.extend(pe);await c.close()

async def axe(page,name):
    await page.add_script_tag(path=str(a.deps/'axe-core/axe.min.js'))
    r=await page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations,incomplete:r.incomplete}}")
    scans.append({'name':name,**r});check(name+': axe zero violations',not r['violations'],r['violations'])

async def text_pages(browser):
    for width,height in [(w,900) for w in WIDTHS]+ORIENTATIONS+[(640,450),(320,225)]:
        c,page,pe,_=await visit(browser,'/hobbies.html',width,height)
        for route,count in [('/hobbies.html',4),('/media.html',4),('/volunteering.html',3),('/travel/southwestroadtrip2026/',8)]:
            await page.goto(site.base+route,wait_until='networkidle');await ready(page)
            label=f'{route}/{width}x{height}'
            nav=page.locator('.section-nav')
            check(label+': actual heading targets',await nav.locator('a').count()==count and await nav.locator('a').evaluate_all('(es)=>es.every(a=>document.querySelectorAll("[id]").length===new Set(Array.from(document.querySelectorAll("[id]"),e=>e.id)).size&&!!document.getElementById(decodeURIComponent(a.hash.slice(1))))'))
            check(label+': navigation left aligns with H1',abs((await nav.bounding_box())['x']-(await page.locator('main h1').bounding_box())['x'])<1)
            check(label+': no horizontal overflow',await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check(label+': navigation targets at least 24px high',await nav.locator('a').evaluate_all('(es)=>es.every(e=>e.getBoundingClientRect().height>=24)'))
            check(label+': one visible H1',await page.locator('main h1:visible').count()==1)
            if route=='/hobbies.html':
                check(label+': five disclosures and 18 source items',await page.locator('.support-button').count()==5 and await page.locator('.support-panel li').count()==18)
                check(label+': all language samples visible',await page.locator('main p[lang]:visible').count()==3)
                if height>=900:check(label+': compact four-link navigation',(await nav.bounding_box())['height']<=68)
            if width in (390,1440) and height==900:
                await axe(page,label)
                typography.append({'page':route,'width':width,'roles':await page.locator('main h1,main h2,main p,main .section-nav a').evaluate_all('(es)=>es.slice(0,12).map(e=>{const s=getComputedStyle(e);return {tag:e.tagName,role:e.className,text:e.textContent.trim().slice(0,60),font:s.fontSize,lineHeight:s.lineHeight,color:s.color,marginTop:s.marginTop,marginBottom:s.marginBottom}})')})
        await close(c,pe)
    c,page,pe,_=await visit(browser,'/hobbies.html',390)
    for button in await page.locator('.support-button').all():
        await button.focus();await page.keyboard.press('Enter')
        check('Keyboard opens '+await button.inner_text(),await button.get_attribute('aria-expanded')=='true')
        await page.keyboard.press(' ');check('Space closes supporting list',await button.get_attribute('aria-expanded')=='false')
    await page.get_by_role('button',name='Expand supporting lists',exact=True).click()
    check('Expand-all reveals every original list',await page.locator('.support-panel[hidden]').count()==0)
    await page.get_by_role('button',name='Collapse supporting lists',exact=True).click()
    ids=await page.locator('[data-support-heading]').evaluate_all('(es)=>es.map(e=>e.id)')
    for id in ids:
        await page.goto(site.base+'/hobbies.html#'+id,wait_until='networkidle');await ready(page)
        check('Direct fragment exposes '+id,await page.locator('#'+id+' button').get_attribute('aria-expanded')=='true')
        check('Direct fragment clears sticky header', (await page.locator('#'+id).bounding_box())['y']>=40)
        await page.reload(wait_until='networkidle');await ready(page)
        check('Refresh exposes '+id,await page.locator('#'+id+' button').get_attribute('aria-expanded')=='true')
    for query,hash in [('YAS-62','music'),('Royal Conservatory','music'),('Piano','music'),('Spanish','language'),('Pickleball','outdoor'),('Hiking','outdoor'),('Mile High Freedom Band','music'),('Foreign Languages','language'),('Sand Volleyball','outdoor'),('Mixology','other'),('Skiing','outdoor'),('Japanese','language'),('Mandarin','language')]:
        await page.goto(site.base+'/hobbies.html',wait_until='networkidle');await ready(page)
        await page.locator('#menu-button').click();await page.locator('#search-input').fill(query)
        result=page.locator('#search-results a[href="/hobbies.html#'+hash+'"]');await result.wait_for();await result.click()
        await page.wait_for_url('**/hobbies.html#'+hash);await ready(page)
        check('Real standard search reaches '+query,await page.locator('#'+hash).is_visible())
        check('Search focuses the correct group for '+query,await page.locator('#'+hash).evaluate('(e)=>e===document.activeElement'))
        if hash=='music':check('Search exposes matching equipment/books',await page.locator('.support-panel[hidden]').count()==0)
    await page.goto(site.base+'/hobbies.html#saxophone-details',wait_until='networkidle');await ready(page)
    await page.locator('.section-nav a[href="#language"]').click();await page.wait_for_url('**#language')
    await page.go_back();await ready(page);check('Fragment Back restores visible supporting heading',page.url.endswith('#saxophone-details') and await page.locator('#saxophone-details button').get_attribute('aria-expanded')=='true')
    await page.go_forward();await ready(page);check('Fragment Forward keeps native history',page.url.endswith('#language') and await page.evaluate('history.scrollRestoration')=='auto')
    await close(c,pe)
    for path in ['/2025/10/07/japan.html','/travel/washington/','/travel/japan/']:
        c,page,pe,_=await visit(browser,path,390)
        check(path+': no empty or copied-outline navigation',await page.locator('.section-nav').count()==0);await close(c,pe)
    for javascript in [True,False]:
        c,page,pe,_=await visit(browser,'/2025/10/07/japan.html',390,server=fixtures,javascript=javascript)
        check('Future long article: native compact expansion',await page.locator('.section-nav details').count()==1)
        await page.locator('.section-nav summary').click();await page.locator('.section-nav a[href="#fixture-hidden-section"]').click()
        check('Future article: hidden heading opens via fragment',await page.locator('#fixture-hidden-section').is_visible())
        check('Future article: no duplicate IDs',await page.locator('[id]').evaluate_all('(es)=>es.length===new Set(es.map(e=>e.id)).size'))
        await close(c,pe)
    c,page,pe,_=await visit(browser,'/hobbies.html',390,javascript=False)
    check('No JS: all supporting content visible',await page.locator('.support-panel li:visible').count()==18)
    check('No JS: native four-link navigation remains',await page.locator('.section-nav a').count()==4)
    await close(c,pe)

async def carousel(browser):
    for motion in ['reduce','no-preference']:
        c,page,pe,requests=await visit(browser,'/volunteering.html',390,motion=motion)
        strip=page.locator('.image-scroll-hyper').first
        controls=page.locator('.carousel-controls').first
        next=controls.get_by_role('button',name='Next photo',exact=True)
        status=controls.locator('.carousel-position')
        await strip.scroll_into_view_if_needed()
        check(motion+': no eager carousel GLightbox request',not any('glightbox@' in u for u in requests))
        check(motion+': bare 44px controls',await next.evaluate('(e)=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&s.borderTopWidth==="0px"&&s.backgroundColor==="rgba(0, 0, 0, 0)"}'))
        await next.click();await page.wait_for_timeout(800)
        check(motion+': one arrow click advances once','Photo 2 ' in await status.inner_text())
        await strip.focus();await page.keyboard.press('Home');await page.wait_for_timeout(800)
        # Actual rapid pointer clicks must use the intended destination, not the
        # still-moving center of a smooth scroll.
        rect=await next.bounding_box()
        for _ in range(3):await page.mouse.click(rect['x']+22,rect['y']+22,delay=20)
        await page.wait_for_timeout(1000)
        check(motion+': rapid commands advance three slots','Photo 4 ' in await status.inner_text(),await status.inner_text())
        rect=await next.bounding_box();await page.mouse.move(rect['x']+22,rect['y']+22)
        hold_start=await strip.evaluate('(e)=>e.scrollLeft')
        await page.evaluate('''()=>{const native=requestAnimationFrame;window.__holdFrames=0;window.requestAnimationFrame=f=>native(t=>{__holdFrames++;f(t)})}''')
        await page.mouse.down();await page.wait_for_timeout(1050)
        during=await strip.evaluate('(e)=>e.scrollLeft');await page.mouse.up();await page.wait_for_timeout(260)
        stopped=await strip.evaluate('(e)=>e.scrollLeft');await page.wait_for_timeout(300)
        check(motion+': hold moves and release stops',abs(stopped-await strip.evaluate('(e)=>e.scrollLeft'))<1 and abs(during-hold_start)>4)
        idle_frames=await page.evaluate('__holdFrames');await page.wait_for_timeout(250)
        check(motion+': no idle hold animation callbacks',await page.evaluate('__holdFrames')==idle_frames)
        for cancel in ['pointercancel','lostpointercapture','blur']:
            await next.focus();await page.keyboard.down('Space');await page.wait_for_timeout(700)
            if cancel=='blur':await strip.focus()
            else:await next.dispatch_event(cancel)
            canceled=await strip.evaluate('(e)=>e.scrollLeft')
            await page.keyboard.up('Space');await page.wait_for_timeout(260)
            stop=await strip.evaluate('(e)=>e.scrollLeft');await page.wait_for_timeout(300)
            check(motion+': '+cancel+' stops motion',abs(stop-await strip.evaluate('(e)=>e.scrollLeft'))<1)
            check(motion+': '+cancel+' release adds no command',abs(stop-canceled)<1)
        await next.focus();await page.keyboard.down('Space');await page.wait_for_timeout(700);await page.keyboard.up('Space');await page.wait_for_timeout(240)
        check(motion+': keyboard hold stops on release',await next.evaluate('(e)=>e===document.activeElement'))
        # Open a stable source slot using the region keyboard interface.
        await strip.focus();await page.keyboard.press('Home');await page.wait_for_timeout(800)
        originals=await strip.locator('.image-scroll-track > :not([data-carousel-clone]) img').count()
        await page.keyboard.press('Enter');await page.get_by_role('dialog').wait_for();await ready(page)
        check(motion+': exactly original slide count',await page.locator('.gslide').count()==originals)
        check(motion+': opening keeps inactive slides inert',await page.locator('.gslide:not(.current)').evaluate_all('(es)=>es.every(e=>e.inert)'))
        await page.keyboard.press('Tab');check(motion+': focus remains in viewer',await page.evaluate('!!document.activeElement.closest(".glightbox-container")'))
        await page.keyboard.press('ArrowRight');await page.wait_for_timeout(450)
        check(motion+': keyboard next displays second original',await page.locator('.gslide.current img').get_attribute('src')==await strip.locator('.image-scroll-track > :not([data-carousel-clone]) img').nth(1).get_attribute('src') or (await page.locator('.gslide.current img').get_attribute('src')).endswith(await strip.locator('.image-scroll-track > :not([data-carousel-clone]) img').nth(1).get_attribute('src')))
        await page.keyboard.press('Escape');await page.wait_for_function('!document.querySelector(".glightbox-container")')
        check(motion+': focus returns to stable strip',await strip.evaluate('(e)=>e===document.activeElement'))
        check(motion+': one lazy JS and CSS fetch',sum('glightbox@' in u and u.endswith('.js') for u in requests)==1 and sum('glightbox@' in u and u.endswith('.css') for u in requests)==1)
        check(motion+': copies have no interactive keyboard stops',await page.locator('[data-carousel-clone]').evaluate_all('(es)=>es.every(e=>e.inert&&e.getAttribute("aria-hidden")==="true"&&Array.from(e.querySelectorAll("a,button,[tabindex]")).every(n=>n.tabIndex===-1))'))
        # Home centers the first original and leaves a genuine prefix-buffer
        # neighbor visible. Click its pixels, not an inert element locator.
        await strip.focus();await page.keyboard.press('Home');await page.wait_for_timeout(800)
        # A wide first photograph can fill the entire centered viewport. Move
        # within the valid first-original range, then let native scrolling rest.
        await strip.evaluate('''e=>{const first=e.querySelector('.image-scroll-track > :not([data-carousel-clone])'),r=first.getBoundingClientRect(),c=e.getBoundingClientRect();e.scrollLeft+=r.left-c.left-e.clientWidth/2+12}''')
        await page.wait_for_timeout(300)
        hit=await strip.evaluate('''e=>{const r=e.getBoundingClientRect();for(const n of e.querySelectorAll('[data-carousel-clone]')){const b=n.getBoundingClientRect(),l=Math.max(b.left,r.left),right=Math.min(b.right,r.right);if(right-l>12)return {x:(l+right)/2,y:r.top+r.height/2,index:Number(n.dataset.carouselIndex)}}return null}''')
        check(motion+': a cloned neighbor is visibly available',bool(hit))
        await page.mouse.click(hit['x'],hit['y']);await page.get_by_role('dialog').wait_for();await ready(page)
        source_url=await strip.locator('.image-scroll-track > :not([data-carousel-clone]) img').nth(hit['index']).get_attribute('src')
        check(motion+': clicking cloned pixels opens corresponding original',(await page.locator('.gslide.current img').get_attribute('src')).endswith(source_url))
        check(motion+': clone opening has no duplicate viewer slides',await page.locator('.gslide').count()==originals)
        await page.keyboard.press('Escape');await page.wait_for_function('!document.querySelector(".glightbox-container")')
        check(motion+': warm enlargement reuses library',sum('glightbox@' in u and u.endswith('.js') for u in requests)==1)
        await strip.scroll_into_view_if_needed();box=await strip.bounding_box()
        await page.mouse.move(box['x']+box['width']*.6,box['y']+box['height']/2)
        await page.mouse.down();await page.mouse.move(box['x']+box['width']*.3,box['y']+box['height']/2,steps=8);await page.mouse.up();await page.wait_for_timeout(300)
        check(motion+': horizontal drag does not enlarge',await page.locator('.glightbox-container').count()==0)
        await close(c,pe)
    c,page,pe,_=await visit(browser,'/volunteering.html',390,touch=True)
    strip=page.locator('.image-scroll-hyper').first
    await strip.scroll_into_view_if_needed();await page.wait_for_timeout(250)
    box=await strip.bounding_box();await page.touchscreen.tap(box['x']+box['width']/2,box['y']+box['height']/2)
    await page.get_by_role('dialog').wait_for();check('Native touch tap enlarges immediately',await page.locator('.gslide.current').count()==1)
    await page.locator('.gclose').tap();await page.wait_for_function('!document.querySelector(".glightbox-container")');await close(c,pe)
    c,page,pe,_=await visit(browser,'/volunteering.html',390,mode='no-gallery')
    strip=page.locator('.image-scroll-hyper').first;await strip.focus();await page.keyboard.press('Enter')
    fallback=page.locator('.carousel-viewer-status a').first;await fallback.wait_for()
    check('Viewer download failure retains original URL',await fallback.get_attribute('href')==await strip.locator('.image-scroll-track > :not([data-carousel-clone]) a').first.get_attribute('href'))
    async def recover(route):
        name='glightbox.css' if '.css' in route.request.url else 'glightbox.js'
        await route.fulfill(path=str(a.assets/name),content_type='text/css' if name.endswith('.css') else 'text/javascript')
    await c.route(re.compile('.*glightbox@.*'),recover)
    await strip.focus();await page.keyboard.press('Enter');await page.get_by_role('dialog').wait_for()
    check('Viewer download can recover on retry',await page.locator('.gslide.current').count()==1)
    await close(c,pe)
    for cancel_open in [True,False]:
        c,page,pe,_=await visit(browser,'/volunteering.html',390)
        gate=asyncio.Event()
        async def delayed(route):
            await gate.wait()
            name='glightbox.css' if '.css' in route.request.url else 'glightbox.js'
            await route.fulfill(path=str(a.assets/name),content_type='text/css' if name.endswith('.css') else 'text/javascript')
        await c.route(re.compile('.*glightbox@.*'),delayed)
        first=page.locator('.image-scroll-hyper').first;second=page.locator('.image-scroll-hyper').nth(1)
        await first.focus();await page.keyboard.press('Enter')
        await page.locator('.carousel-viewer-status').first.get_by_text('Loading image viewer…').wait_for()
        if cancel_open:
            await page.keyboard.press('Tab')
            check('Tab cancels pending viewer feedback immediately',await page.locator('.carousel-viewer-status').first.inner_text()=='')
        else:
            await second.focus();await page.keyboard.press('Enter')
            check('New strip intent clears first pending feedback',await page.locator('.carousel-viewer-status').first.inner_text()=='')
        gate.set();await page.wait_for_timeout(900)
        if cancel_open:check('Late library does not steal focus/open canceled viewer',await page.locator('.glightbox-container').count()==0)
        else:
            await page.get_by_role('dialog').wait_for()
            check('Latest strip owns the delayed viewer',await page.get_by_role('dialog').get_attribute('aria-label')==await second.get_attribute('aria-label'))
            check('Delayed viewer contains only second originals',await page.locator('.gslide').count()==await second.locator('.image-scroll-track > :not([data-carousel-clone])').count())
        await close(c,pe)
    c,page,pe,_=await visit(browser,'/volunteering.html',390)
    fail_css=asyncio.Event()
    async def partial_load(route):
        if '.css' in route.request.url:
            await fail_css.wait();await route.fulfill(status=503,body='Controlled stylesheet failure')
        else:await route.fulfill(path=str(a.assets/'glightbox.js'),content_type='text/javascript')
    await c.route(re.compile('.*glightbox@.*'),partial_load)
    strip=page.locator('.image-scroll-hyper').first;await strip.focus();await page.keyboard.press('Enter')
    await page.wait_for_function('typeof GLightbox==="function"');fail_css.set()
    await page.locator('.carousel-viewer-status a').first.wait_for()
    check('CSS-only viewer failure leaves a working original link',await page.locator('.glightbox-container').count()==0)
    await c.route(re.compile('.*glightbox@.*'),recover)
    await strip.focus();await page.keyboard.press('Enter');await page.get_by_role('dialog').wait_for()
    check('Retry restores stylesheet even if JS was already installed',await page.get_by_role('dialog').evaluate('(e)=>getComputedStyle(e).position')=='fixed')
    await close(c,pe)

async def screenshots(browser):
    out=a.out/'screenshots';out.mkdir(exist_ok=True)
    paths=[('carousels','/volunteering.html'),('blog','/blog.html'),('photography','/photography.html'),('travel','/travel.html'),('hobbies','/hobbies.html'),('media','/media.html'),('volunteering','/volunteering.html'),('article-short','/2025/10/07/japan.html'),('article-days','/travel/southwestroadtrip2026/')]
    for width in [390,1440]:
        for phase,server in [('before',before),('after',site)]:
            for name,path in paths:
                c,page,pe,_=await visit(browser,path,width,1100,server)
                # Match scroll positions/content region across comparisons.
                if name=='carousels':await page.locator('.image-scroll-hyper').first.scroll_into_view_if_needed()
                if name=='photography':await page.locator('a.glightbox').first.focus()
                filename=f'{name}-{phase}-{width}.png';await page.screenshot(path=str(out/filename))
                shots.append(filename)
                if name=='carousels' and phase=='after':
                    await page.locator('.image-scroll-hyper').first.focus();await page.keyboard.press('Enter');await page.get_by_role('dialog').wait_for();await ready(page)
                    filename=f'carousel-viewer-{width}.png';await page.screenshot(path=str(out/filename));shots.append(filename)
                await close(c,pe)

async def main():
    async with async_playwright() as pw:
        options={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']} if a.browser=='chromium' else {}
        browser=await getattr(pw,a.browser).launch(**options)
        if not a.only or a.only=='text':await text_pages(browser)
        if not a.only or a.only=='carousel':await carousel(browser)
        if not a.only or a.only=='screenshots':await screenshots(browser)
        check('No new page exceptions',not errors,errors)
        await browser.close()

try:asyncio.run(main())
finally:
    (a.out/'results.json').write_text(json.dumps({'browser':a.browser,'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks,'axe':scans,'typography':typography,'errors':errors,'screenshots':shots,'limitations':'Synthetic geometry/media; Chromium/Firefox/WebKit where installed, no physical devices or screen-reader certification.'},indent=2)+'\n')
    for s in [site,before,fixtures]:s.close()
print('Editorial browser checks passed:',len(checks))
