"""Actual served Travel UI + Firebase 9.22.1 + enforced localhost RTDB rules.
Auth tokens are emulator fixtures; no production Firebase/auth/analytics traffic.
"""
import argparse, asyncio, json, re, shutil, subprocess, urllib.request
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
stale_source=subprocess.check_output(['git','show','19973eb:assets/js/travel.js'],cwd=ROOT,text=True)
checks=[]; frames=[]; console=[]; errors=[]; anonymous_uids=[]
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
async def install_routes(ctx,phase="private-atomic-after"):
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
                        if filename in ('firebase-app-compat.js','firebase-auth-compat.js'):
                            await r.fulfill(content_type='text/javascript',body=(args.sdk/filename).read_text());return
                        if filename=='firebase-database-compat.js':
                            source=(args.sdk/filename).read_text()+'''\nconst emulatorInitialize=firebase.initializeApp;
    firebase.initializeApp=()=>{const app=emulatorInitialize({projectId:'demo-website-reliability',apiKey:'demo-only',databaseURL:'http://127.0.0.1:9008/?ns=demo-website-reliability'});app.auth().useEmulator('http://127.0.0.1:9098',{disableWarnings:true});app.database().useEmulator('127.0.0.1',9008);return app;};'''
                            await r.fulfill(content_type='text/javascript',body=source);return
                        if filename=='travel-atomic-receipts-1.js' and phase=='provided-before':
                            await r.fulfill(content_type='text/javascript',body=old_source);return
                        if filename=='travel-atomic-receipts-1.js' and phase=='stale-private-before':
                            # Reenact an old client under current rules, not a claim
                            # that Playwright interception reproduces HTTP caching.
                            await r.fulfill(content_type='text/javascript',body=stale_source);return
                        if '/assets/images/' in url.path:
                            await r.fulfill(content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"/>');return
                        if url.hostname not in ('127.0.0.1','localhost'):
                            await r.fulfill(content_type='text/javascript' if r.request.resource_type=='script' else 'text/css',body='');return
                        await r.continue_()
                    await ctx.route('**/*',route)

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for phase in ['provided-before','stale-private-before','private-atomic-after']:
            rule_path=Path(__file__).parent/'provided.rules.json' if phase=='provided-before' else ROOT/'_firebase/database.rules.json'
            rest('.settings/rules.json','PUT',json.loads(rule_path.read_text()))
            for width in [390,1440]:
                rest('.settings/rules.json','PUT',json.loads(rule_path.read_text()))
                ctx=await browser.new_context(viewport={'width':width,'height':900})
                await ctx.add_init_script("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('Dismissed','AbortError')}})")
                await install_routes(ctx,phase)
                p=await ctx.new_page();responses=[];p.on('response',lambda r:responses.append(r));p.on('pageerror',lambda e:errors.append(str(e)))
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
                await p.wait_for_function("Array.from(document.querySelectorAll('.like-count')).every(e=>Number(e.textContent)>=1)&&Array.from(document.querySelectorAll('.like-button')).every(e=>!e.disabled)")
                await p.evaluate('document.fonts.ready')
                if phase!='private-atomic-after':
                    button=p.locator('.like-button').first;await button.click()
                    message='Could not confirm' if phase=='provided-before' else 'Could not update the like. Please try again.'
                    await p.wait_for_function('(message)=>document.querySelector(".travel-feedback").textContent.includes(message)',arg=message)
                    check(f'{width}/{phase}: actual old client reproduces the expected failure',not await button.is_disabled())
                    check(f'{width}: rejected transaction preserves seeded data',rest('.json')==original)
                    await p.screenshot(path=str(args.out/f'{phase}-travel-{width}.png'))
                else:
                    travel_responses=[r for r in responses if '/assets/js/travel' in r.url]
                    check(f'{width}: exactly one current Travel asset requested',len(travel_responses)==1 and urlparse(travel_responses[0].url).path=='/assets/js/travel-atomic-receipts-1.js')
                    check(f'{width}: browser executed the reviewed Travel source',await travel_responses[0].body()==(ROOT/'assets/js/travel-atomic-receipts-1.js').read_bytes())
                    uid=await p.evaluate('firebase.auth().currentUser.uid');anonymous_uids.append(uid)
                    check(f'{width}: anonymous sign-in is invisible',await p.evaluate("firebase.auth().currentUser.isAnonymous") and await p.locator('input[type=email],input[type=password],iframe[src*=captcha]').count()==0)
                    # Fixture own state is initially absent for the actual anonymous UID.
                    for i,card in enumerate(await p.locator('.travel-card').all()):
                        like=card.locator('.like-button')
                        await like.focus();await p.keyboard.press('Space')
                        await p.wait_for_function('(id)=>document.querySelector(`.like-button[data-id="${id}"]`).getAttribute("aria-pressed")==="true"&&!document.querySelector(`.like-button[data-id="${id}"]`).disabled',arg=ids[i])
                        check(f'{width}/{ids[i]}: one-click like',await card.locator('.like-count').inner_text()==str(original['likes'][ids[i]]['count']+1))
                        if i==0:await p.screenshot(path=str(args.out/f'private-travel-{width}.png'))
                        await p.keyboard.press('Space')
                        await p.wait_for_function('(id)=>document.querySelector(`.like-button[data-id="${id}"]`).getAttribute("aria-pressed")==="false"&&!document.querySelector(`.like-button[data-id="${id}"]`).disabled',arg=ids[i])
                        check(f'{width}/{ids[i]}: one-click unlike',await card.locator('.like-count').inner_text()==str(original['likes'][ids[i]]['count']))
                        await card.locator('.share-button').focus();await p.keyboard.press('Enter')
                        check(f'{width}/{ids[i]}: native cancellation normal',await card.locator('.travel-feedback').inner_text()=='Sharing canceled.' and not await card.locator('.share-button').is_disabled())
                    stored=rest('.json')
                    check(f'{width}: original counts and user markers retained',all(stored['likes'][id]['count']==original['likes'][id]['count'] and stored['likes'][id]['users']==original['likes'][id]['users'] for id in ids))
                    # Same anonymous identity returns after navigation with no login or new setup.
                    await p.reload(wait_until='networkidle');await p.wait_for_function('firebase.auth().currentUser!==null')
                    check(f'{width}: automatic anonymous identity persists',await p.evaluate('firebase.auth().currentUser.uid')==uid)
                    await p.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{}})")
                    await p.locator('.share-button').first.click()
                    await p.wait_for_function("document.querySelector('.share-count').textContent==='1'")
                    for _ in range(50):
                        shared=rest('.json')
                        if shared.get('shares',{}).get(ids[0],{}).get('count')==1:break
                        await p.wait_for_timeout(100)
                    check(f'{width}: actual atomic share increment/marker',shared['shares'][ids[0]]['count']==1 and shared['shares'][ids[0]]['users'][uid]['shared'] is True)
                    # Real clipboard fallback also works when database rules reject analytics.
                    await ctx.grant_permissions(['clipboard-read','clipboard-write'])
                    await p.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:undefined})")
                    denied={'rules':{'.read':False,'.write':False}}
                    rest('.settings/rules.json','PUT',denied)
                    await p.locator('.share-button').first.click()
                    await p.wait_for_function("document.querySelector('.travel-feedback').textContent.includes('could not be confirmed')")
                    check(f'{width}: clipboard survives analytics denial',await p.evaluate('navigator.clipboard.readText()')==re.search(r"sharePost\('([^']+)'",await p.locator('.share-button').first.get_attribute('onclick')).group(1) and not await p.locator('.share-button').first.is_disabled())
                await ctx.close()
        check('Real SDK records denied parent transaction',any('permission_denied' in m['text'].lower() for m in console))
        after=[f for f in frames if f['phase']=='private-atomic-after' and f['action'] in ('q','g') and str(f['path']).startswith('/likes/')]
        check('Real SDK reads only count or own user/receipt paths',all(f['path'].endswith('/count') or any(f['path'].endswith('/users/'+uid) or f['path'].endswith('/receipts/'+uid) for uid in anonymous_uids) for f in after))
        check('No browser exceptions',not errors)
        await browser.close()
    (args.out/'results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'requests':frames,'expected_permission_warnings':console,'errors':errors,'method':'Actual served Travel UI and Firebase 9.22.1 SDK; real local RTDB enforcement; real automatic Anonymous Authentication uses the Auth emulator; no credentials or login UI. No production traffic.'},indent=2))
    print('Enforced browser checks passed:',len(checks))
if __name__=='__main__':asyncio.run(main())
