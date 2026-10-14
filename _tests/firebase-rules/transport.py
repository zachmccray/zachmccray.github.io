"""Drop actual RTDB WebSocket acknowledgements while enforcing the real rules.
Real Auth emulator/SDK/served UI; no replacement counter or transport implementation.
"""
import asyncio,json,runpy
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urlparse
G=runpy.run_path(str(Path(__file__).with_name('browser.py')),run_name='transport_helpers')
args=G['args'];rest=G['rest'];check=G['check'];checks=G['checks']
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path=G['shutil'].which('chromium'),args=['--no-sandbox'])
  for mode in ['like-lost-ack','like-opposite-before-retry','share-lost-ack']:
   rest('.settings/rules.json','PUT',json.loads((G['ROOT']/'_firebase/database.rules.json').read_text()))
   first='travel-southwestroadtrip2026';original={'count':4,'users':{'other':{'liked':True,'timestamp':1}},'note':'preserve'}
   rest('.json','PUT',{'likes':{first:original}})
   c=await b.new_context(viewport={'width':390,'height':844})
   await c.add_init_script("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{}})")
   await G['install_routes'](c)
   fault={'socket':None,'server':None,'rpc':None,'captured':False,'dropped':False,'attempts':0,'probes':[]};event=asyncio.Event();proof_ack=asyncio.Event()
   async def socket_route(ws):
    if urlparse(ws.url).hostname not in ('127.0.0.1','localhost'):
     await ws.close(code=1008,reason='No external test sockets');return
    server=ws.connect_to_server()
    async def outbound(message):
     try:
      d=json.loads(message).get('d',{});body=d.get('b',{})
      kind='shares' if mode=='share-lost-ack' else 'likes'
      if d.get('a')=='m' and body.get('p')=='/'+kind+'/'+first:
       if 'count' in body.get('d',{}):fault['attempts']+=1
       elif any(key.startswith('actions/') for key in body.get('d',{})):fault['probes'].append((ws,d['r']))
      if not fault['captured'] and d.get('a')=='m' and body.get('p')=='/'+kind+'/'+first and 'count' in body.get('d',{}):
       fault.update(socket=ws,server=server,rpc=d['r'],captured=True)
     except (ValueError,TypeError,KeyError):pass
     server.send(message)
    async def inbound(message):
     try:
      d=json.loads(message).get('d',{})
      if any(ws is socket and d.get('r')==rpc for socket,rpc in fault['probes']) and d.get('b',{}).get('s')=='ok':proof_ack.set()
      if ws is fault['socket'] and not fault['dropped'] and d.get('r')==fault['rpc'] and d.get('b',{}).get('s')=='ok':
       fault['dropped']=True;event.set()
       if mode!='like-opposite-before-retry':
        await ws.close(code=1001,reason='Test acknowledgement loss');server.close(code=1001,reason='Test reconnect')
       return
     except (ValueError,TypeError):pass
     ws.send(message)
    ws.on_message(lambda message:asyncio.create_task(outbound(message)));server.on_message(lambda message:asyncio.create_task(inbound(message)))
   await c.route_web_socket('**/*',socket_route)
   p=await c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
   await p.goto(args.url+'/travel.html',wait_until='networkidle')
   like=p.locator('.like-button').first
   await p.wait_for_function('!document.querySelector(".like-button").disabled')
   uid=await p.evaluate('firebase.auth().currentUser.uid')
   if mode=='share-lost-ack':await p.locator('.share-button').first.click()
   else:await like.click()
   await asyncio.wait_for(event.wait(),10)
   check(mode+': actual success ACK dropped after server commit',fault['dropped'])
   if mode=='like-opposite-before-retry':
    check(mode+': original remains pending',await like.is_disabled())
    p2=await c.new_page();await p2.goto(args.url+'/travel.html',wait_until='networkidle')
    await p2.wait_for_function('!document.querySelector(".like-button").disabled&&document.querySelector(".like-button").getAttribute("aria-pressed")==="true"')
    check(mode+': second tab uses same anonymous identity',await p2.evaluate('firebase.auth().currentUser.uid')==uid)
    await p2.locator('.like-button').first.click()
    await p2.wait_for_function('!document.querySelector(".like-button").disabled&&document.querySelector(".like-button").getAttribute("aria-pressed")==="false"')
    await fault['socket'].close(code=1001,reason='Retry after newer opposite intent');fault['server'].close(code=1001,reason='Test reconnect')
   if mode=='share-lost-ack':
    await asyncio.wait_for(proof_ack.wait(),15)
    check(mode+': SDK resend denied and immutable proof acknowledged',fault['attempts']>=2)
    await p.wait_for_function('document.querySelector(".share-count").textContent==="1"')
    # Let the replay denial and immutable proof acknowledgement finish.
    for _ in range(80):
     status=await p.locator('.travel-feedback').first.inner_text()
     if not await p.evaluate('document.querySelector(".share-button").disabled') and status=='Shared.':break
     await p.wait_for_timeout(100)
    record=rest('.json')['shares'][first]
    check(mode+': one share survives SDK resend',record['count']==1 and len(record['actions'][uid])==1)
    check(mode+': completed sharing stays usable',not await p.locator('.share-button').first.is_disabled())
   else:
    await p.wait_for_function('!document.querySelector(".like-button").disabled',timeout=20000)
    check(mode+': actual replay and proof acknowledgement',fault['attempts']>=2 and proof_ack.is_set())
    record=rest('.json')['likes'][first]
    expected=4 if mode=='like-opposite-before-retry' else 5
    check(mode+': exact count and latest state',record['count']==expected and await like.get_attribute('aria-pressed')==str(expected==5).lower())
    check(mode+': original other user untouched',record['users']['other']==original['users']['other'])
    if expected==4:check(mode+': no resurrected old action',len(record['actions'][uid])==2)
   check(mode+': no browser exception',not errors)
   await c.close()
  await b.close()
 (args.out/'transport-results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'method':'Actual anonymous Auth SDK + RTDB WebSockets; successful ACK dropped and socket closed; enforced proposed rules and real served client. Native share completion is controlled.'},indent=2))
 print('Transport checks passed:',len(checks))
asyncio.run(main())
