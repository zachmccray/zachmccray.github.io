"""Actual served Travel UI + Firebase 9.22.1 + enforced localhost RTDB rules.
Auth tokens are emulator fixtures; no production Firebase/auth/analytics traffic.
"""
import argparse, asyncio, json, shutil, subprocess, urllib.request
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:4340')
parser.add_argument('--sdk',type=Path,required=True,help='Installed firebase@9.22.1 package directory')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--fixtures',type=Path,help='Optional cached Inter.ttf/Font Awesome 6.5.0 files for previews')
args=parser.parse_args()
assert urlparse(args.url).hostname in ('127.0.0.1','localhost'), 'Locally served builds only'
args.out.mkdir(parents=True,exist_ok=True)
assert json.loads((args.sdk/'package.json').read_text())['version']=='9.22.1'
old_source=subprocess.check_output(['git','show','02839e0:assets/js/travel.js'],cwd=ROOT,text=True)
checks=[]; frames=[]; console=[]; errors=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)}); assert condition,name
def rest(location,method='GET',value=None):
    # Fixed localhost-only emulator endpoint; "owner" is its test bypass token.
    req=urllib.request.Request('http://127.0.0.1:9008/'+location+'?ns=demo-website-reliability',
        data=None if value is None else json.dumps(value).encode(),method=method,
        headers={'Authorization':'Bearer owner','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=5) as response:return json.load(response)
def seed(ids):
    likes={}
    for i,id in enumerate(ids):
        users={'other':{'liked':True,'timestamp':1}}
        if i%2:users['fixture-user']={'liked':True,'timestamp':2}
        likes[id]={'count':len(users),'users':users,'note':'fixture preserve'}
    return {'likes':likes}
def sent(phase,payload):
    try:
        data=json.loads(payload)
        if isinstance(data,dict) and data.get('t')=='d':
            request=data['d'];body=request.get('b',{})
            if request.get('a') in ('q','g','p','m'):
                frames.append({'phase':phase,'action':request['a'],'path':body.get('p')})
    except (ValueError,TypeError,KeyError):pass
async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for phase in ['provided-before','private-readonly-after']:
            rules='provided' if phase=='provided-before' else 'private-backend'
            rest('.settings/rules.json','PUT',json.loads((Path(__file__).parent/(rules+'.rules.json')).read_text()))
            for width in [390,1440]:
                ctx=await browser.new_context(viewport={'width':width,'height':900})
                await ctx.add_init_script("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('Dismissed','AbortError')}})")
                async def route(r):
                    url=urlparse(r.request.url);filename=url.path.rsplit('/',1)[-1]
                    if args.fixtures:
                        font=args.fixtures/filename
                        if filename in ('Inter.ttf','fa-solid-900.woff2','fa-regular-400.woff2','fa-brands-400.woff2') and font.exists():
                            await r.fulfill(path=str(font),content_type='font/ttf' if filename.endswith('.ttf') else 'font/woff2');return
                        if url.hostname=='fonts.googleapis.com':
                            await r.fulfill(content_type='text/css',body="@font-face{font-family:'Inter';font-weight:100 900;src:url('"+args.url+"/__test-font/Inter.ttf') format('truetype');font-display:swap}");return
                        if '/font-awesome/6.5.0/' in url.path and (args.fixtures/'fontawesome.css').exists():
                            await r.fulfill(path=str(args.fixtures/'fontawesome.css'),content_type='text/css');return
                    if filename=='firebase-app-compat.js':
                        await r.fulfill(content_type='text/javascript',body=(args.sdk/filename).read_text());return
                    if filename=='firebase-auth-compat.js':
                        await r.fulfill(content_type='text/javascript',body="firebase.auth=()=>({signInAnonymously:async()=>({user:{uid:'fixture-user'}})});");return
                    if filename=='firebase-database-compat.js':
                        source=(args.sdk/filename).read_text()+'''\nconst emulatorInitialize=firebase.initializeApp;
firebase.initializeApp=()=>{const app=emulatorInitialize({projectId:'demo-website-reliability',apiKey:'demo-only',databaseURL:'http://127.0.0.1:9008/?ns=demo-website-reliability'});app.database().useEmulator('127.0.0.1',9008,{mockUserToken:{sub:'fixture-user',user_id:'fixture-user'}});return app;};'''
                        await r.fulfill(content_type='text/javascript',body=source);return
                    if filename=='travel.js' and phase=='provided-before':
                        await r.fulfill(content_type='text/javascript',body=old_source);return
                    if '/assets/images/' in url.path:
                        await r.fulfill(content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"/>');return
                    if url.hostname not in ('127.0.0.1','localhost'):
                        await r.fulfill(content_type='text/javascript' if r.request.resource_type=='script' else 'text/css',body='');return
                    await r.continue_()
                await ctx.route('**/*',route)
                p=await ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
                p.on('console',lambda m:console.append({'phase':phase,'type':m.type,'text':m.text}) if 'permission_denied' in m.text.lower() else None)
                p.on('websocket',lambda ws:ws.on('framesent',lambda payload:sent(phase,payload)))
                # Get public IDs without invoking the runtime before seeding.
                html=await (await ctx.request.get(args.url+'/travel.html')).text()
                from html.parser import HTMLParser
                ids=[]
                class IDs(HTMLParser):
                    def handle_starttag(self,tag,attrs):
                        a=dict(attrs)
                        if 'like-button' in a.get('class','').split():ids.append(a['data-id'])
                IDs().feed(html)
                check(phase+': nine original Travel IDs',len(ids)==9)
                original=seed(ids);rest('.json','PUT',original)
                await p.goto(args.url+'/travel.html',wait_until='networkidle')
                await p.wait_for_function("Array.from(document.querySelectorAll('.like-count')).every(e=>Number(e.textContent)>=1)")
                await p.evaluate('document.fonts.ready')
                if phase=='provided-before':
                    button=p.locator('.like-button').first;await button.click()
                    await p.wait_for_function("document.querySelector('.travel-feedback').textContent.includes('Could not confirm')")
                    check(f'{width}: actual PR19 UI reproduces transaction failure',not await button.is_disabled())
                    check(f'{width}: rejected transaction preserves seeded data',rest('.json')==original)
                    await p.screenshot(path=str(args.out/f'before-travel-{width}.png'))
                else:
                    await p.wait_for_function("document.querySelectorAll('.like-button')[1].getAttribute('aria-pressed')==='true'")
                    await p.screenshot(path=str(args.out/f'private-travel-{width}.png'))
                    for i,card in enumerate(await p.locator('.travel-card').all()):
                        like=card.locator('.like-button')
                        check(f'{width}/{ids[i]}: readonly with current state/count',await like.is_disabled() and await like.get_attribute('aria-pressed')==str(bool(i%2)).lower() and await card.locator('.like-count').inner_text()==str(original['likes'][ids[i]]['count']))
                        await card.locator('.share-button').focus();await p.keyboard.press('Enter')
                        check(f'{width}/{ids[i]}: native cancellation normal',await card.locator('.travel-feedback').inner_text()=='Sharing canceled.' and not await card.locator('.share-button').is_disabled())
                    check(f'{width}: all fixture records unchanged',rest('.json')==original)
                    # One completed share still logs both original leaves with real SDK/rules.
                    await p.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{}})")
                    await p.locator('.share-button').first.click()
                    await p.wait_for_function("document.querySelector('.share-count').textContent==='1'")
                    shared=rest('.json')
                    check(f'{width}: actual atomic share increment/marker works',shared['likes']==original['likes'] and shared['shares'][ids[0]]['count']==1 and shared['shares'][ids[0]]['users']['fixture-user']['shared'] is True)
                await ctx.close()
        check('Real SDK records denied parent transaction',any('permission_denied' in m['text'].lower() for m in console))
        after=[f for f in frames if f['phase']=='private-readonly-after' and str(f['path']).startswith('/likes/')]
        check('Real SDK sends only count/own-marker reads for likes',len(after)==36 and all(f['action'] in ('q','g') and (f['path'].endswith('/count') or f['path'].endswith('/users/fixture-user')) for f in after))
        check('No browser exceptions',not errors)
        await browser.close()
    (args.out/'results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'requests':frames,'expected_permission_warnings':console,'errors':errors,'method':'Actual served Travel UI and Firebase 9.22.1 SDK; real local RTDB enforcement; auth tokens are emulator fixtures, not real Auth integration. No production traffic.'},indent=2))
    print('Enforced browser checks passed:',len(checks))
asyncio.run(main())
