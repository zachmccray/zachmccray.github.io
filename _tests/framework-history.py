"""Native HTTP/cache and real Chromium BFCache, without production services.

A CSP and test-only HTML URL mapping keep fonts/libraries/SDK requests local.
Unlike routed browser fixtures, these contexts retain the browser HTTP cache.
"""
import argparse,asyncio,hashlib,json,mimetypes,re,shutil
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.async_api import async_playwright
p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        path=urlparse(self.path).path;kind='text/html';code=200
        if path=='/__native/empty.js':data=b'';kind='text/javascript'
        elif path=='/__native/inter.css':data=b'@font-face{font-family:Inter;font-weight:100 900;src:url(/__native/Inter.ttf) format("truetype");font-display:swap}';kind='text/css'
        elif path=='/__native/Inter.ttf':data=(a.assets/'Inter.ttf').read_bytes();kind='font/ttf'
        elif path.startswith('/assets/images/'):
            digest=hashlib.sha256(path.encode()).hexdigest();w,h=[(640,480),(480,800),(800,450)][int(digest[:2],16)%3]
            data=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#{digest[:6]}"/></svg>'.encode();kind='image/svg+xml'
        else:
            file=a.site/path.lstrip('/')
            if not file.is_file():data=b'Not found';code=404
            else:
                data=file.read_bytes();kind=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
                if kind=='text/html':
                    def local(m):
                        tag=m[0]
                        if m[1]=='link' and 'preconnect' in tag:return ''
                        url=m[2];replacement='/__native/inter.css' if 'fonts.googleapis.com' in url else '/__native/empty.js'
                        return tag.replace(url,replacement)
                    text=re.sub(r'<(script|link)\b[^>]*(?:src|href)="(https://[^"]+)"[^>]*>',local,data.decode())
                    data=text.encode()
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','max-age=3600')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'")
        self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port);checks=[];traces=[]
def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail});assert ok,(name,detail)
async def main():
    async with async_playwright() as pw:
        for cache in [False,True]:
            opts={'args':['--no-sandbox']}
            if shutil.which('chromium'):opts['executable_path']=shutil.which('chromium')
            else:opts['channel']='chromium'
            if cache:opts['ignore_default_args']=['--disable-back-forward-cache']
            b=await pw.chromium.launch(**opts);c=await b.new_context(viewport={'width':390,'height':900},reduced_motion='reduce')
            await c.add_init_script("window.__pageShows=[];addEventListener('pageshow',e=>__pageShows.push(e.persisted))")
            page=await c.new_page();await page.goto(base+'/blog.html',wait_until='networkidle');await page.evaluate('document.fonts.ready')
            await page.locator('#year-filter').select_option('2025');await page.locator('#sort-filter').select_option('title-asc')
            link=page.locator('.blog-entry:not([hidden]) a.event-thumb').nth(2);await link.scroll_into_view_if_needed();before=await page.evaluate('scrollY')
            await link.click();await page.wait_for_load_state('networkidle');await page.go_back(wait_until='commit');await page.wait_for_function('!!document.querySelector("#year-filter")');await page.wait_for_timeout(250)
            trace=await page.evaluate('({events:__pageShows,y:scrollY,year:document.querySelector("#year-filter").value,sort:document.querySelector("#sort-filter").value,type:performance.getEntriesByType("navigation")[0].type})');traces.append({'bfcache_enabled':cache,'before_scroll':before,**trace})
            check(f'BFCache={cache}: actual persisted/rebuilt lifecycle',trace['events'][-1] is cache,trace)
            check(f'BFCache={cache}: native controls restored',trace['year']=='2025' and trace['sort']=='title-asc')
            check(f'BFCache={cache}: restored controls match actual entries',await page.locator('.blog-entry:not([hidden])').evaluate_all('(es)=>es.length>0&&es.every(e=>e.dataset.year==="2025")'))
            check(f'BFCache={cache}: native cached-asset scroll preserved',abs(trace['y']-before)<3,trace)
            check(f'BFCache={cache}: default history model retained',await page.evaluate('history.scrollRestoration')=='auto')
            await page.go_forward(wait_until='commit');await page.wait_for_function('!!document.querySelector(".post-article")')
            check(f'BFCache={cache}: Forward retains article destination',await page.locator('.post-article').count()==1)
            await c.close();await b.close()
try:asyncio.run(main())
finally:(a.out/'results.json').write_text(json.dumps({'passed':sum(c['passed'] for c in checks),'checks':checks,'traces':traces,'method':'Native HTTP font/media assets, no Playwright request routing. Explicitly exercise Chromium cached rebuild and actual BFCache persisted=true. CSP and external script substitution prevent all production services. This does not write or override browser history.'},indent=2)+'\n');server.shutdown();server.server_close()
print('Native history checks passed:',len(checks))
