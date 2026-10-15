"""Paired Travel lab with native local HTTP fonts/assets and real controllers.

Only external font URLs in served test HTML are mapped to pinned local fixtures.
Production sources are never rewritten. This is not production Web Vitals.
"""
import argparse,asyncio,hashlib,json,mimetypes,shutil,statistics
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse,unquote
from playwright.async_api import async_playwright
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--site',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=7);a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        path=unquote(urlparse(self.path).path);kind='text/html';code=200
        if path=='/__vendor/inter.css':data=b'@font-face{font-family:Inter;font-weight:100 900;src:url(/__vendor/Inter.ttf) format("truetype");font-display:swap}';kind='text/css'
        elif path.startswith('/__vendor/'):
            filename=path.rsplit('/',1)[-1];filename='fontawesome.css' if filename=='all.min.css' else filename
            file=a.assets/filename;data=file.read_bytes();kind=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        elif path.startswith('/assets/images/'):
            digest=hashlib.sha256(path.encode()).hexdigest();w,h=[(640,480),(480,800),(800,450)][int(digest[:2],16)%3]
            data=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#{digest[:6]}"/></svg>'.encode();kind='image/svg+xml'
        else:
            file=self.server.folder/path.lstrip('/')
            if not file.is_file():data=b'Not found';code=404
            else:
                data=file.read_bytes();kind=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
                if kind=='text/html':
                    text=data.decode().replace('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css','/__vendor/fa/css/all.min.css')
                    text=text.replace('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap','/__vendor/inter.css')
                    assert 'https://fonts.googleapis.com/css2' not in text
                    data=text.encode()
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','max-age=3600');self.end_headers();self.wfile.write(data)
servers={}
for phase,folder in [('before',a.baseline),('after',a.site)]:
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.folder=folder
    Thread(target=server.serve_forever,daemon=True).start();servers[phase]=server
root=Path(__file__).resolve().parent.parent
mock=(root/'_tests/firebase-fixture.js').read_text()+'\nwindow.__fixture=firebaseFixture();window.firebase=__fixture.firebase;'
rows=[]
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for cpu in [1,4]:
            for sample in range(a.samples):
                for phase in (['before','after'] if sample%2==0 else ['after','before']):
                    c=await b.new_context(viewport={'width':390,'height':844});await c.add_init_script(mock)
                    await c.add_init_script("window.__cls=[];new PerformanceObserver(es=>__cls.push(...es.getEntries().filter(e=>!e.hadRecentInput).map(e=>e.value))).observe({type:'layout-shift',buffered:true})")
                    async def route(r):
                        if urlparse(r.request.url).hostname in ('localhost','127.0.0.1'):await r.continue_()
                        else:await r.fulfill(body='',content_type='text/javascript' if r.request.resource_type=='script' else 'text/css')
                    await c.route('**/*',route);page=await c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    cdp=await c.new_cdp_session(page);await cdp.send('Performance.enable');await cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
                    url=f'http://127.0.0.1:{servers[phase].server_port}/travel.html'
                    await page.goto(url,wait_until='networkidle');await page.evaluate('document.fonts.ready');await page.wait_for_function('Array.from(document.querySelectorAll(".like-button")).every(b=>!b.disabled)');await page.wait_for_timeout(120)
                    resources=await page.evaluate('performance.getEntriesByType("resource").map(r=>({url:r.name,bytes:r.transferSize,type:r.initiatorType}))')
                    icon=[r for r in resources if '/__vendor/fa/' in r['url']]
                    navigation=await page.evaluate('performance.getEntriesByType("navigation")[0].transferSize')
                    metrics={r['name']:r['value'] for r in (await cdp.send('Performance.getMetrics'))['metrics']}
                    values={'phase':phase,'cpu':cpu,'sample':sample,'icon_requests':len(icon),'icon_transfer_bytes':sum(r['bytes'] for r in icon),'icon_resources':icon,'document_transfer_bytes':navigation,'all_local_transfer_bytes':navigation+sum(r['bytes'] for r in resources if '127.0.0.1' in r['url']),'requests':len(resources)+1,'script_ms':metrics['ScriptDuration']*1000,'layout_ms':metrics['LayoutDuration']*1000,'style_ms':metrics['RecalcStyleDuration']*1000,'dom_nodes':(await cdp.send('Memory.getDOMCounters'))['nodes'],'js_heap_bytes':metrics['JSHeapUsedSize'],'fixture_cls':await page.evaluate('__cls.reduce((a,b)=>a+b,0)'),'fcp_ms':await page.evaluate('performance.getEntriesByName("first-contentful-paint")[0]?.startTime'),'errors':errors}
                    assert not errors,errors
                    if phase=='after':assert not icon and await page.locator('svg.travel-action-icon').count()==18
                    else:assert len(icon)==3,icon
                    rows.append(values);await c.close()
                print('Measured',cpu,'× sample',sample+1,flush=True)
        await b.close()
    medians=[]
    for cpu in [1,4]:
        for phase in ['before','after']:
            selected=[r for r in rows if r['cpu']==cpu and r['phase']==phase]
            medians.append({'cpu':cpu,'phase':phase,**{k:statistics.median(r[k] for r in selected) for k in ['icon_requests','icon_transfer_bytes','requests','document_transfer_bytes','all_local_transfer_bytes','script_ms','layout_ms','style_ms','dom_nodes','js_heap_bytes','fixture_cls','fcp_ms']}})
    a.out.write_text(json.dumps({'samples':rows,'medians':medians,'method':'Seven alternating fresh Chromium contexts per phase at 1×/4× CPU; actual generated Travel HTML/controller/styles. HTTP fixture server rewrites only external font links to equivalent local pinned files, supplies Inter TTF and synthetic media. Firebase fixture, SDK/analytics blocked. Transfer figures include local HTTP headers; Inter TTF differs from production WOFF subsets. No production CDN latency, real photographs, deployed Firebase timing or Core Web Vitals claims.'},indent=2)+'\n')
try:asyncio.run(main())
finally:
    for server in servers.values():server.shutdown();server.server_close()
print('Framework performance comparison complete')
