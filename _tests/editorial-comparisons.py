"""Controlled unrelated-page pixels, reversible Travel CSS and payload budgets."""
import argparse,asyncio,gzip,hashlib,json,re,shutil
from pathlib import Path
from playwright.async_api import async_playwright
from framework_helpers import Site,context,ready

p=argparse.ArgumentParser()
for n in ('baseline','site','assets','deps','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sites=[Site(a.baseline),Site(a.site)];checks=[];styles=[];payload=[];heights=[]
def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
async def shot(browser,index,path,width,undo=False):
    c,page,errors,requests=await context(browser,sites[index],a.assets,a.deps,width,1100)
    if undo:
        css=(a.site/'assets/css/custom-editorial-1.css').read_text()
        css,count=re.subn(r'/\* Travel refinements:.*?(?=/\* The normal instructions)', '',css,flags=re.S)
        check('Travel has exactly one removable styling block',count==1)
        await c.route('**/assets/css/custom-editorial-1.css',lambda r:r.fulfill(body=css,content_type='text/css'))
    await page.goto(sites[index].base+path,wait_until='networkidle');await ready(page)
    data=await page.screenshot()
    if path=='/travel.html':
        values=await page.locator('.travel-card,.travel-date,.travel-card-content > p,.travel-actions,.travel-cover').evaluate_all('(es)=>es.slice(0,14).map(e=>{const s=getComputedStyle(e);return {role:e.className,tag:e.tagName,border:s.borderColor,padding:s.padding,margin:s.margin,fontSize:s.fontSize,lineHeight:s.lineHeight,color:s.color,gap:s.gap,aspectRatio:s.aspectRatio}})')
        styles.append({'phase':'before' if index==0 else 'reversed' if undo else 'after','width':width,'properties':values})
    if path in ('/hobbies.html','/blog.html','/photography.html'):
        height=await page.locator('main').evaluate('(e)=>e.getBoundingClientRect().height')
        heights.append({'page':path,'phase':'before' if index==0 else 'after','width':width,'main_height':height})
    check(path+'/'+str(width)+': no exceptions',not errors,errors)
    await c.close();return hashlib.sha256(data).hexdigest()
async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for width in [390,1440]:
            for path in ['/','/academics.html','/courses.html','/2025/10/07/japan.html','/travel/washington/']:
                x=await shot(browser,0,path,width);y=await shot(browser,1,path,width)
                check(path+'/'+str(width)+': unrelated pixels identical',x==y,{'before':x,'after':y})
            x=await shot(browser,0,'/travel.html',width)
            await shot(browser,1,'/travel.html',width)
            y=await shot(browser,1,'/travel.html',width,undo=True)
            check('Travel/'+str(width)+': reversing scoped block restores exact baseline pixels',x==y,{'before':x,'reversed':y})
            for path in ['/hobbies.html','/blog.html','/photography.html']:
                for index in [0,1]:await shot(browser,index,path,width)
        await browser.close()
asyncio.run(main())
for old,new in [('assets/css/custom-hardening-1.css','assets/css/custom-editorial-1.css'),('assets/js/image-carousel-2.js','assets/js/image-carousel-3.js'),('assets/js/photography-portfolio-2.js','assets/js/photography-portfolio-3.js'),(None,'assets/js/image-viewer-1.js'),(None,'assets/js/section-navigation-1.js')]:
    row={'before':old,'after':new}
    for label,file,root in [('before',old,a.baseline),('after',new,a.site)]:
        data=(root/file).read_bytes() if file else b''
        row[label+'_raw_bytes']=len(data);row[label+'_gzip_bytes']=len(gzip.compress(data,mtime=0)) if data else 0
    payload.append(row)
for s in sites:s.close()
result={'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks,'travel_computed_styles':styles,'payloads':payload,'layout_heights':heights,'limits':'Chromium local synthetic media and pinned Inter, not real-photo performance or production Web Vitals. gzip is computed artifact size, not a measured CDN response.'}
(a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print('Controlled comparisons:',result['passed'],'passed;',len(result['failed']),'failed')
raise SystemExit(bool(result['failed']))
