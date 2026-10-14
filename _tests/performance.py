"""Comparable local laboratory measurement; never a production Web Vitals report."""
import argparse, json, mimetypes, shutil, statistics, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--site',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=7);p.add_argument('--chromium',default=shutil.which('chromium'));p.add_argument('--fixtures',type=Path)
a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
servers=[];bases={}
for name,folder in [('before',a.baseline),('after',a.site)]:
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(folder)))
 threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server);bases[name]=f'http://127.0.0.1:{server.server_port}'
instrument='''(()=>{let value;window.__build=[];window.__restore=[];
Object.defineProperty(window,'lunr',{configurable:true,get:()=>value,set:fn=>{
const load=fn.Index.load;fn.Index.load=function(...args){const start=performance.now(),result=load.apply(this,args);__restore.push(performance.now()-start);return result};
value=new Proxy(fn,{apply(target,self,args){const start=performance.now(),result=Reflect.apply(target,self,args);__build.push(performance.now()-start);return result}});
}})})();'''
runs=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(**({'executable_path':a.chromium} if a.chromium else {}),args=['--no-sandbox'])
  for rate in [1,4]:
   for sample in range(a.samples):
    # Alternate order to reduce systematic warming/order bias.
    for phase in (['before','after'] if sample%2==0 else ['after','before']):
     c=b.new_context(viewport={'width':390,'height':844});c.add_init_script(instrument);requests=[];responses={};transfers={}
     def route(r):
      u=urlparse(r.request.url);requests.append(r.request.url);fixtures=a.fixtures
      if '/assets/images/' in u.path:
       r.fulfill(content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#bbc4cd"/></svg>');return
      if u.path=='/__fixture-font.ttf' and fixtures:
       r.fulfill(path=str(fixtures/'Inter.ttf'),content_type='font/ttf');return
      if u.hostname not in ('127.0.0.1','localhost'):
       if u.hostname=='fonts.googleapis.com' and fixtures:
        r.fulfill(content_type='text/css',body=f'@font-face{{font-family:Inter;font-style:normal;font-weight:100 900;src:url({bases[phase]}/__fixture-font.ttf) format("truetype");font-display:swap}}');return
       if 'font-awesome' in r.request.url and fixtures:
        r.fulfill(path=str(fixtures/'fontawesome.css'),content_type='text/css');return
       r.fulfill(content_type='text/javascript' if r.request.resource_type=='script' else 'text/css',body='');return
      r.continue_()
     c.route('**/*',route);page=c.new_page();cdp=c.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Performance.enable');cdp.send('Emulation.setCPUThrottlingRate',{'rate':rate})
     cdp.on('Network.responseReceived',lambda e:responses.update({e['requestId']:e['response']['url']}))
     cdp.on('Network.loadingFinished',lambda e:transfers.update({e['requestId']:e['encodedDataLength']}))
     page.goto(bases[phase]+'/',wait_until='networkidle')
     startup=page.evaluate('({build:__build,restore:__restore,paint:performance.getEntriesByName("first-contentful-paint").map(e=>e.startTime)})')
     script_ms=next(m['value']*1000 for m in cdp.send('Performance.getMetrics')['metrics'] if m['name']=='ScriptDuration')
     initial_requests=requests.copy();local_encoded=sum(size for key,size in transfers.items() if responses.get(key,'').startswith(bases[phase]) and '/assets/images/' not in responses.get(key,'') and '/__fixture-font' not in responses.get(key,''))
     page.locator('#menu-button').click();page.locator('#search-input').press_sequentially('EECS 101');page.locator('#search-results a[href="/courses.html#course-eecs101"]').wait_for(state='visible')
     cold=page.evaluate('__build')
     warm=None
     if phase=='after':
      page.wait_for_function('sessionStorage.getItem("site-search-index-v1")!==null')
      page.goto(bases[phase]+'/academics.html',wait_until='networkidle');page.locator('#menu-button').click();page.locator('#search-input').fill('EECS-101');page.locator('#search-results a[href="/courses.html#course-eecs101"]').wait_for(state='visible');warm=page.evaluate('__restore[0]')
     runs.append({'phase':phase,'cpu':rate,'sample':sample,'initial_build_ms':startup['build'][0] if startup['build'] else 0,'cold_build_ms':cold[0] if cold else None,'session_restore_ms':warm,'initial_script_duration_ms':script_ms,'fcp_ms':startup['paint'][0] if startup['paint'] else None,'initial_requests':initial_requests,'initial_local_http_encoded_bytes':local_encoded,'initial_request_count':len(initial_requests)})
     print(phase,rate,sample,'initial',runs[-1]['initial_build_ms'],'restore',warm,flush=True);c.close()
  b.close()
 summary=[]
 for rate in [1,4]:
  for phase in ['before','after']:
   selected=[r for r in runs if r['cpu']==rate and r['phase']==phase];item={'phase':phase,'cpu':rate}
   for field in ['initial_build_ms','cold_build_ms','session_restore_ms','initial_script_duration_ms','fcp_ms','initial_local_http_encoded_bytes','initial_request_count']:
    values=[r[field] for r in selected if r[field] is not None]
    item[field]={'median':statistics.median(values),'range':[min(values),max(values)]} if values else None
   summary.append(item)
 a.out.write_text(json.dumps({'summary':summary,'runs':runs,'method':'Seven fresh Chromium contexts per phase/rate; alternating order. Actual built theme/Lunr/native search JSON from uncompressed local HTTP. Transparent Proxy times native construction and Index.load calls. CDP encodedDataLength measures local HTTP traffic including headers, excluding synthetic font/media. Third-party SDKs/analytics blocked; optional cached real Inter TTF/Font Awesome CSS are controlled fixtures. No production Web Vitals, real CDN font-byte claims, or global runtime patches shipped.','fixtures':str(a.fixtures) if a.fixtures else None,'browser':b.version},indent=2))
finally:
 for server in servers:server.shutdown();server.server_close()
