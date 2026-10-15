"""Strong merged-baseline preservation with explicit framework-only exceptions."""
import argparse,json,re
from html.parser import HTMLParser
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--site',type=Path,required=True);p.add_argument('--baseline-source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent.parent;checks=[]
def check(name,ok):
    checks.append({'check':name,'passed':bool(ok)});assert ok,name
class Tags(HTMLParser):
    def __init__(self,text):super().__init__();self.tags=[];self.feed(text)
    def handle_starttag(self,t,attrs):self.tags.append((t,dict(attrs)))
def main(s):return re.search(r'<main[^>]*>(.*?)</main>',s,re.S)[1]
def normalize(s):return re.sub(r'\s+',' ',s).strip()
expected=json.loads((root/'_tests/public-routes.json').read_text())
check('All 82 intended routes, no additions',sorted(str(p.relative_to(a.site)) for p in a.site.rglob('*.html'))==expected)
for route in expected:
    before=(a.baseline/route).read_text();after=(a.site/route).read_text();x=Tags(before).tags;y=Tags(after).tags
    seo=lambda ts:[(t,d) for t,d in ts if t=='meta' or t=='link' and d.get('rel')=='canonical']
    check(route+' unchanged SEO/canonical metadata',seo(x)==seo(y))
    for regex in [r'<title>.*?</title>',r'<script type="application/ld\+json">.*?</script>']:
        check(route+' unchanged document title/structured data',re.findall(regex,before,re.S)==re.findall(regex,after,re.S))
    links=lambda ts:[d.get('href') for t,d in ts if t=='a']
    media=lambda ts:[d for t,d in ts if t in ('img','video','source')]
    check(route+' all functional links unchanged',links(x)==links(y))
    check(route+' all media references/attributes unchanged',media(x)==media(y))
    oldids=[d['id'] for _,d in x if 'id' in d];newids=[d['id'] for _,d in y if 'id' in d]
    check(route+' every existing ID retained exactly once',all(newids.count(id)==oldids.count(id) for id in oldids))
    allowed={'site-ui-script'}|({'travel-action-symbols','travel-heart-outline','travel-heart-solid','travel-share'} if route=='travel.html' else set())
    check(route+' only intended new IDs, none duplicated',set(newids)-set(oldids)==allowed and len(newids)==len(set(newids)))
    old=main(before);new=main(after).replace('photography-portfolio-2.js','photography-portfolio-1.js')
    if route=='travel.html':
        new=re.sub(r'<!-- Font Awesome.*?-->','',new,flags=re.S)
        new=re.sub(r'<svg[^>]*id="travel-action-symbols".*?</svg>','',new,flags=re.S)
        new=re.sub(r'<svg class="travel-action-icon"[^>]*>.*?</svg>',lambda m:'<i class="fa-regular fa-heart" aria-hidden="true"></i>' if 'heart-outline' in m[0] else '<i class="fa-solid fa-share-nodes" aria-hidden="true"></i>',new,flags=re.S)
    check(route+' exact content/structure except declared icon/entry-point changes',normalize(old)==normalize(new))
old=(a.baseline/'assets/js/search-data.json').read_text();new=(a.site/'assets/js/search-data.json').read_text()
check('All 80 search records byte-identical',old==new and len(json.loads(new))==80)
old_controls=(a.baseline_source/'assets/js/blog-controls.js').read_text();new_controls=(root/'assets/js/blog-controls.js').read_text()
pattern=r'visibleEntries.sort\((.*?)\n    \}\);'
check('Blog comparators unchanged; only history lifecycle corrected',len(re.findall(pattern,old_controls,re.S))==1 and re.findall(pattern,old_controls,re.S)==re.findall(pattern,new_controls,re.S))
protected=['_config.yml','Gemfile','Gemfile.lock','assets/js/search.js','assets/js/just-the-docs.js','assets/js/travel-atomic-receipts-1.js','_includes/course-list.md']
for folder in ['_data','_posts','_travel','_layouts','_firebase']:
    protected.extend(str(f.relative_to(a.baseline_source)) for f in (a.baseline_source/folder).rglob('*') if f.is_file())
for name in protected:check(name+' source byte-identical',(a.baseline_source/name).read_bytes()==(root/name).read_bytes())
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2)+'\n');print('Framework preservation checks passed:',len(checks))
