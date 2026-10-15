"""Comparable local carousel lab: actual baseline/current CSS+JS, native HTTP media.

SVGs are controlled fixtures, not production photo/decoded-memory measurements.
Callbacks include their synchronous layout work; CDP reports layout/heap separately.
"""
import argparse
import asyncio
import json
import mimetypes
import shutil
import statistics
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--site',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--repetitions',type=int,default=7)
args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
cases=[1,2,5,12,150,180]
rows=[]
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urlparse(self.path);q=parse_qs(u.query);phase=q.get('phase',['after'])[0]
        site=args.site if phase=='after' else args.baseline
        code=200;kind='text/html'
        if u.path=='/':
            n=int(q.get('n',['150'])[0]);images=''.join(f'<div class="image-scroll-item" id="source-{i}"><img src="/image-{i}.svg" alt="Fixture {i}"></div>' for i in range(n))
            data=f'''<!doctype html><html><head><link rel="stylesheet" href="/style.css?phase={phase}"></head><body><main class="main-content"><h2>Controlled photo strip</h2><div class="image-scroll-hyper" id="fixture-carousel"><div class="image-scroll-track">{images}</div></div></main><script src="/app.js?phase={phase}"></script></body></html>'''.encode()
        elif u.path=='/style.css':
            data=(site/'assets/css/just-the-docs-default.css').read_bytes()+(site/'assets/css/custom.css').read_bytes()+b'\nbody{margin:0} .main-content{width:min(784px,calc(100vw - 32px));margin:80px auto;}'
            kind='text/css'
        elif u.path=='/app.js':
            data=(site/'assets/js/infinite-scroll.js').read_bytes();kind='text/javascript'
        elif u.path.startswith('/image-'):
            i=int(u.path.removeprefix('/image-').removesuffix('.svg'))
            w,h=[(640,480),(480,800),(800,450)][i%3]
            data=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#{i%256:02x}7088"/><path d="M0 {h} L{w//2} {h//3} L{w} {h}" fill="#dde4e9"/></svg>'.encode();kind='image/svg+xml'
        else:code=404;data=b'Not found'
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','max-age=3600' if code==200 and u.path.startswith('/image-') else 'no-store')
        self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(server.server_port)
instrument='''window.__work={active:true,callbacks:[]};
const record=fn=>function(...args){const start=performance.now();try{return fn.apply(this,args)}finally{if(__work.active)__work.callbacks.push(performance.now()-start)}};
const add=EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener=function(type,fn,...args){return add.call(this,type,type==='DOMContentLoaded'&&typeof fn==='function'?record(fn):fn,...args)};
const raf=requestAnimationFrame;window.requestAnimationFrame=fn=>raf(record(fn));
const RO=ResizeObserver;window.ResizeObserver=class extends RO{constructor(fn){super(record(fn))}};'''
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for cpu in [1,4]:
            for n in cases:
                for repetition in range(args.repetitions):
                    for phase in (['before','after'] if repetition%2==0 else ['after','before']):
                        c=await b.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce')
                        await c.add_init_script(instrument);p=await c.new_page();cdp=await c.new_cdp_session(p)
                        await cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu});await cdp.send('Performance.enable')
                        await p.goto(base+f'/?phase={phase}&n={n}',wait_until='networkidle')
                        await p.wait_for_function('(n)=>Array.from(document.querySelectorAll("[id^=source-] img")).slice(0,n).every(i=>i.complete&&i.naturalWidth>0)',arg=n)
                        await p.wait_for_timeout(240)
                        values=await p.evaluate('''()=>{__work.active=false;const c=document.querySelector('.image-scroll-hyper');const resources=performance.getEntriesByType('resource').filter(e=>e.initiatorType==='img');return {images:c.querySelectorAll('img').length,init_callback_ms:__work.callbacks.reduce((a,b)=>a+b,0),callback_samples:__work.callbacks.length,unique_image_resources:new Set(resources.map(e=>e.name)).size,image_transfer_bytes:resources.reduce((s,e)=>s+e.transferSize,0),is_looping:c.classList.contains('is-looping')}}''')
                        metrics={x['name']:x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
                        dom=await cdp.send('Memory.getDOMCounters')
                        values.update({'phase':phase,'source_images':n,'cpu':cpu,'repetition':repetition,'layout_ms':metrics['LayoutDuration']*1000,'script_ms':metrics['ScriptDuration']*1000,'dom_nodes':dom['nodes'],'heap_used_bytes':metrics['JSHeapUsedSize']})
                        # Measure repeated scroll/resize and retention with the real app.
                        start=metrics['TaskDuration'];count=values['images']
                        await p.evaluate('''async()=>{const c=document.querySelector('.image-scroll-hyper');for(let i=0;i<24;i++){c.scrollLeft+=(i%2?1:-1)*123;await new Promise(requestAnimationFrame)} }''')
                        for width in [390,820,1440,390,1440]:
                            await p.set_viewport_size({'width':width,'height':900});await p.wait_for_timeout(200)
                        metrics2={x['name']:x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
                        values['repeat_scroll_resize_task_ms']=(metrics2['TaskDuration']-start)*1000
                        values['final_images']=await p.locator('.image-scroll-hyper img').count()
                        await cdp.send('HeapProfiler.collectGarbage')
                        values['retained_dom_nodes']=(await cdp.send('Memory.getDOMCounters'))['nodes']
                        if phase=='after':
                            assert values['images']<=n*3 and values['images']<n*6
                            assert values['final_images']<=n*3
                            assert await p.locator('.carousel-controls').count()==1
                        else:assert count==n*6
                        rows.append(values);await c.close()
                print('Measured',cpu,'× CPU,',n,'source images',flush=True)
        await b.close()
    summaries=[]
    for cpu in [1,4]:
        for n in cases:
            summary={'cpu':cpu,'source_images':n}
            for phase in ['before','after']:
                samples=[r for r in rows if r['phase']==phase and r['cpu']==cpu and r['source_images']==n]
                summary[phase]={k:statistics.median(r[k] for r in samples) for k in ['images','init_callback_ms','layout_ms','script_ms','unique_image_resources','image_transfer_bytes','dom_nodes','heap_used_bytes','repeat_scroll_resize_task_ms','retained_dom_nodes']}
            summaries.append(summary)
    (args.out/'performance.json').write_text(json.dumps({'samples':rows,'medians':summaries,'method':'Seven alternating fresh Chromium contexts per phase/count at 1× and 4× CPU. Actual source CSS/JS; native HTTP requests/cache with mixed SVG images. Callback time includes synchronous layout; CDP layout/script durations reported separately. Repeated task time includes 24 scroll frames and five resizes. DOM/JS heap are renderer measurements, not decoded image/GPU memory or Core Web Vitals.'},indent=2)+'\n')
    print('Carousel performance lab complete')
try:asyncio.run(main())
finally:server.shutdown();server.server_close()
