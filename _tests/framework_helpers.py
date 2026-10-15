"""Shared local-only browser fixtures; never connect visitors to production services."""
import asyncio
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

class Site:
    def __init__(self,folder):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(folder)))
        Thread(target=self.server.serve_forever,daemon=True).start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def close(self):
        self.server.shutdown();self.server.server_close()

async def context(browser,site,assets,deps,width=1440,height=900,mode=None,javascript=True):
    ctx=await browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce',java_script_enabled=javascript)
    mock=(ROOT/'_tests/firebase-fixture.js').read_text()+'''\nwindow.__fixture=firebaseFixture();window.firebase=__fixture.firebase;
    Object.defineProperty(navigator,'share',{configurable:true,value:undefined});
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{}}});'''
    if javascript:await ctx.add_init_script(mock)
    requests=[]
    async def route(r):
        u=urlparse(r.request.url);name=u.path.rsplit('/',1)[-1];requests.append(r.request.url)
        if mode=='no-theme' and name=='just-the-docs.js':await r.abort();return
        if mode=='no-gallery' and 'glightbox@' in r.request.url:await r.abort();return
        if mode=='no-font' and u.hostname in ('fonts.googleapis.com','fonts.gstatic.com'):await r.abort();return
        if mode=='no-icons' and ('font-awesome' in r.request.url or name.startswith('fa-')):await r.abort();return
        if mode=='search-failure' and name=='search-data.json':await r.fulfill(status=503);return
        if '/assets/images/' in u.path:
            if mode=='missing':await r.fulfill(status=404,body='Controlled missing image');return
            h=hashlib.sha256(u.path.encode()).digest();w,ht=[(640,480),(480,800),(800,450)][h[0]%3]
            await r.fulfill(content_type='image/svg+xml',body=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{ht}"><rect width="100%" height="100%" fill="#{h.hex()[:6]}"/><path d="M0 {ht} L{w//2} {ht//3} L{w} {ht}" fill="#dde4e9"/></svg>');return
        if 'glightbox@' in r.request.url:
            p=(assets/('glightbox.css' if name.endswith('.css') else 'glightbox.js')) if assets else deps/'glightbox/dist'/('css/glightbox.min.css' if name.endswith('.css') else 'js/glightbox.min.js')
            await r.fulfill(path=str(p),content_type='text/css' if name.endswith('.css') else 'text/javascript');return
        if u.hostname=='fonts.googleapis.com':
            if assets:await r.fulfill(content_type='text/css',body="@font-face{font-family:Inter;font-weight:100 900;src:url('"+site.base+"/__fixture/Inter.ttf') format('truetype')}\n");return
            await r.fulfill(body='',content_type='text/css');return
        if name=='Inter.ttf' and assets:
            if mode=='slow-font':await asyncio.sleep(.8)
            await r.fulfill(path=str(assets/name),content_type='font/ttf');return
        if 'font-awesome' in r.request.url and name.endswith('.css') and assets:await r.fulfill(path=str(assets/'fontawesome.css'),content_type='text/css');return
        if name.startswith('fa-') and assets and (assets/name).exists():await r.fulfill(path=str(assets/name),content_type='font/woff2',headers={'Access-Control-Allow-Origin':'*'});return
        if u.hostname not in ('127.0.0.1','localhost'):
            await r.fulfill(body='',content_type='text/javascript' if r.request.resource_type=='script' else 'text/css');return
        await r.continue_()
    await ctx.route('**/*',route)
    p=await ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    return ctx,p,errors,requests

async def ready(page):
    await asyncio.wait_for(page.evaluate('document.fonts.ready'),timeout=20)
    await page.wait_for_timeout(230)
