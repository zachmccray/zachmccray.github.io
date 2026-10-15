"""Native wheel/touch, boundary pixels, readiness and repeated-use carousel checks.

Actual built CSS/controller; synthetic photographs, never production requests.
"""
import argparse, asyncio, json, shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--site',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail});assert ok,(name,detail)

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for n in [1,2,5,12,150,180]:
            ctx=await browser.new_context(viewport={'width':390,'height':844},has_touch=True,reduced_motion='reduce')
            async def route(r):
                u=urlparse(r.request.url)
                if u.path=='/':
                    items=''.join(f'<div class="image-scroll-item" id="photo-{i}"><img src="/image-{i}.svg" alt="Fixture {i}"></div>' for i in range(n))
                    html=f'''<!doctype html><link rel="stylesheet" href="/assets/css/custom-visual-media-1.css"><style>body{{margin:0}}main{{width:calc(100% - 32px);margin:80px auto}}h2{{font-size:20px}}</style><main><h2>Controlled gallery</h2><div class="image-scroll-hyper"><div class="image-scroll-track">{items}</div></div></main><script defer src="/assets/js/image-carousel-1.js"></script>'''
                    await r.fulfill(body=html,content_type='text/html');return
                if u.path.startswith('/image-'):
                    i=int(u.path[7:-4]);w,h=[(640,480),(480,800),(800,450),(300,1400),(1600,100)][i%5]
                    if 'slow' in u.query:await asyncio.sleep(.4)
                    if 'missing' in u.query:await r.fulfill(status=404);return
                    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#{i%256:02x}7585"/><circle cx="{w//2}" cy="{h//2}" r="{min(w,h)//3}" fill="#dde4e9"/></svg>'
                    await r.fulfill(content_type='image/svg+xml',body=svg);return
                p=args.site/u.path.lstrip('/')
                if p.is_file():await r.fulfill(path=str(p));return
                await r.fulfill(status=404)
            await ctx.route('**/*',route)
            page=await ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            await page.goto('http://carousel.test/',wait_until='networkidle');await page.wait_for_timeout(250)
            strip=page.locator('.image-scroll-hyper');track=page.locator('.image-scroll-track')
            check(f'{n}: bounded image nodes',await track.locator('img').count()<=3*n)
            check(f'{n}: source order retained',await track.locator(':scope > :not([data-carousel-clone])').evaluate_all('(es)=>es.every((e,i)=>e.id==="photo-"+i)'))
            check(f'{n}: natural source ratios',await track.locator(':scope > :not([data-carousel-clone]) img').evaluate_all('(es)=>es.every(e=>{const r=e.getBoundingClientRect();return Math.abs(r.width/r.height-e.naturalWidth/e.naturalHeight)<.02})'))
            check(f'{n}: first photo centered after readiness',await page.locator('#photo-0').evaluate('(e)=>{const a=e.getBoundingClientRect(),b=e.closest(".image-scroll-hyper").getBoundingClientRect();return Math.abs(a.left+a.width/2-b.left-b.width/2)<1}'))
            if n==1:
                check('one photo: controls hidden when unnecessary',await page.locator('.carousel-controls').is_hidden())
            if n==2:
                check('two photos: finite without clones',not await strip.evaluate('(e)=>e.classList.contains("is-looping")') and await track.locator('img').count()==2)
                await page.get_by_role('button',name='Next photo').click();await page.wait_for_timeout(250)
                check('two photos: finite end disables next',await page.get_by_role('button',name='Next photo').is_disabled())
                await page.get_by_role('button',name='Previous photo').click();await page.wait_for_timeout(250)
                check('two photos: finite start disables previous',await page.get_by_role('button',name='Previous photo').is_disabled())
            if n>=5:
                # Contact prevents wrapping. Capture identical viewport pixels before
                # and after idle normalization, without reconstructing its math.
                await strip.dispatch_event('pointerdown',{'pointerId':7,'pointerType':'touch'})
                await strip.evaluate('(e)=>e.scrollLeft=0');await page.wait_for_timeout(250)
                check(f'{n}: held pointer defers correction',await strip.evaluate('(e)=>e.scrollLeft')==0)
                before=await strip.screenshot()
                await page.locator('body').dispatch_event('pointerup',{'pointerId':7,'pointerType':'touch'})
                await page.wait_for_timeout(350)
                check(f'{n}: release outside strip restores continuity',await strip.evaluate('(e)=>e.scrollLeft')>0)
                # Integer scroll positions can round fractional image geometry
                # by at most one pixel; compare visible identities and geometry.
                check(f'{n}: invisible left-boundary normalization',before==await strip.screenshot())
                await strip.dispatch_event('pointerdown',{'pointerId':8,'pointerType':'touch'})
                await strip.evaluate('(e)=>e.scrollLeft=e.scrollWidth');await page.wait_for_timeout(250)
                before=await strip.screenshot()
                before_geo=await track.locator('img').evaluate_all('(es)=>es.map(e=>({src:e.src,x:e.getBoundingClientRect().x,w:e.getBoundingClientRect().width})).filter(e=>e.x+e.w>16&&e.x<374)')
                await page.locator('body').dispatch_event('pointercancel',{'pointerId':8,'pointerType':'touch'});await page.wait_for_timeout(350)
                after_geo=await track.locator('img').evaluate_all('(es)=>es.map(e=>({src:e.src,x:e.getBoundingClientRect().x,w:e.getBoundingClientRect().width})).filter(e=>e.x+e.w>16&&e.x<374)')
                check(f'{n}: right-boundary content continuity (subpixel rounding only)',len(before_geo)==len(after_geo) and all(a['src']==b['src'] and abs(a['x']-b['x'])<1 for a,b in zip(before_geo,after_geo)),{'before':before_geo,'after':after_geo})
                await strip.focus();await page.keyboard.press('Home');await page.wait_for_timeout(250)
                await page.keyboard.press('ArrowRight');await page.wait_for_timeout(250)
                chosen=await page.locator('.carousel-position').inner_text()
                await page.set_viewport_size({'width':820,'height':390});await page.wait_for_timeout(350)
                check(f'{n}: chosen photo survives orientation change',await page.locator('.carousel-position').inner_text()==chosen)
                await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(350)
                await strip.hover();start=await strip.evaluate('(e)=>e.scrollLeft');await page.mouse.wheel(170,0);await page.wait_for_timeout(350)
                check(f'{n}: actual horizontal wheel scrolls natively',abs(await strip.evaluate('(e)=>e.scrollLeft')-start)>50)
                # Chromium input dispatch reaches the browser's native touch scroll.
                await strip.focus();await page.keyboard.press('Home');await page.wait_for_timeout(250)
                cdp=await ctx.new_cdp_session(page);box=await strip.bounding_box();x=box['x']+box['width']*.8;y=box['y']+box['height']/2
                start=await strip.evaluate('(e)=>e.scrollLeft')
                await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                for j in range(1,9):
                    await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-j*18,'y':y}]});await page.wait_for_timeout(20)
                await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_timeout(450)
                check(f'{n}: native touch swipe changes position',abs(await strip.evaluate('(e)=>e.scrollLeft')-start)>40)
                before_count=await track.locator('img').count()
                for _ in range(20):await page.evaluate('ImageCarousels.init()')
                await page.wait_for_timeout(250)
                check(f'{n}: reinitializing keeps one control set and bounded nodes',await page.locator('.carousel-controls').count()==1 and await track.locator('img').count()==before_count)
            if n==12:
                # Real late/error resource events, with changing original geometry.
                await page.keyboard.press('Home');await page.wait_for_timeout(250)
                await page.keyboard.press('ArrowRight');await page.wait_for_timeout(250)
                await page.keyboard.press('ArrowRight');await page.wait_for_timeout(250)
                selected=await page.locator('.carousel-position').inner_text()
                await page.locator('#photo-0 img').evaluate('(e)=>e.src+="?slow"');await page.wait_for_timeout(800)
                check('late resource dimensions retain selected photo',await page.locator('.carousel-position').inner_text()==selected)
                await page.locator('#photo-1 img').evaluate('(e)=>e.src+="?missing"');await page.wait_for_timeout(600)
                check('failed image has reserved fallback',await page.locator('#photo-1').evaluate('(e)=>e.classList.contains("is-unavailable")&&e.getBoundingClientRect().width===180'))
                check('failed image does not reset current photo',await page.locator('.carousel-position').inner_text()==selected)
            check(f'{n}: no document overflow',await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            await ctx.close()
        check('No JavaScript exceptions',not errors,errors);await browser.close()

try:asyncio.run(main())
finally:(args.out/'results.json').write_text(json.dumps({'passed':sum(x['passed'] for x in checks),'checks':checks,'errors':errors,'limits':'Chromium emulated touch input and native wheel; no physical device inertia certification.'},indent=2)+'\n')
print('Carousel behavior checks passed:',len(checks))
