"""Compare generated routes, content, SEO, native search, and resource budgets."""
import argparse, json, re
from html.parser import HTMLParser
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--site',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--local-url',help='Normalize this local build origin to the baseline production origin')
a=parser.parse_args(); checks=[]
def check(name,ok):
    checks.append({'check':name,'passed':bool(ok)}); assert ok,name
class Tags(HTMLParser):
    def __init__(self,text):super().__init__();self.tags=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
def seo(text):
    tags=Tags(text)
    return ([x for x in tags.tags if x[0]=='meta' or x[0]=='link' and x[1].get('rel')=='canonical'], re.findall(r'<title>.*?</title>|<script type="application/ld\+json">.*?</script>',text,re.S))
def main(text):return re.search(r'<main[^>]*>(.*?)</main>',text,re.S)[1]
routes=lambda root:sorted(str(p.relative_to(root)) for p in root.rglob('*.html'))
r=routes(a.baseline); check('All 82 HTML routes preserved',len(r)==82 and r==routes(a.site))
for name in r:
    before=(a.baseline/name).read_text();after=(a.site/name).read_text()
    if a.local_url: after=after.replace(a.local_url.rstrip('/'), 'https://zachmccray.github.io')
    check(name+' SEO unchanged',seo(before)==seo(after))
    expected=main(before).replace('npm/glightbox/dist/','npm/glightbox@3.3.1/dist/')
    check(name+' exact main content unchanged except dependency pin',expected==main(after))
    scripts=[attrs for tag,attrs in Tags(after).tags if tag=='script' and 'src' in attrs]
    check(name+' theme script deferred',all('defer' in s for s in scripts if s['src'].endswith('/just-the-docs.js')))
    check(name+' no eager Lunr script',not any(s['src'].endswith('/lunr.min.js') for s in scripts))
    icons=[attrs for tag,attrs in Tags(after).tags if tag=='link' and 'font-awesome' in attrs.get('href','')]
    check(name+' icons only on Travel',len(icons)==(1 if name=='travel.html' else 0))
    check(name+' direct same Inter request',len([attrs for tag,attrs in Tags(after).tags if tag=='link' and 'fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap' in attrs.get('href','')])==1)
    check(name+' no unused Firebase/Blog scripts',sum('firebase' in s['src'] for s in scripts)==(3 if name=='travel.html' else 0) and sum(s['src'].endswith(('/blog-controls.js', '/blog-controls-2.js')) for s in scripts)==(1 if name=='blog.html' else 0))
search='assets/js/search-data.json'
before=json.loads((a.baseline/search).read_text());after=json.loads((a.site/search).read_text())
check('All 80 standard search records byte-equivalent',before==after and len(after)==80)
course=[record for record in after.values() if record['doc']=='My Courses' and record['title']!='My Courses']
check('All 45 unique stable course destinations preserved',len(course)==45 and len(set(record['url'] for record in course))==45 and all('#course-' in record['url'] for record in course))
# Guard the intentionally small upstream fork: remove only initSearch and attribution.
native_scroll='''      // scroll search input into view, workaround for iOS Safari
      window.scroll(0, -1);
      setTimeout(function(){ window.scroll(0, 0); }, 0);'''
strip=lambda s:re.sub(r'/\* Just the Docs 9a7e403.*?\*/\n','', (s[:s.index('function initSearch()')]+s[s.index('function searchLoaded'):]).replace(native_scroll, '      // The search input is in the persistent header; retain article position.').replace('    currentSearchIndex++;\n\n', '').replace('    currentSearchIndex++;\n    currentInput', '    currentInput'),flags=re.S)
check('Native theme runtime unchanged except initialization, batching guard and obsolete forced scroll',strip((a.baseline/'assets/js/just-the-docs.js').read_text())==strip((a.site/'assets/js/just-the-docs.js').read_text()))
for path in a.baseline.rglob('*'):
    if path.is_file() and '/assets/images/' in str(path):check(str(path.relative_to(a.baseline))+' image asset preserved',path.read_bytes()==(a.site/path.relative_to(a.baseline)).read_bytes())
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps({'passed':len(checks),'checks':checks,'routes':r},indent=2));print('Preservation checks passed:',len(checks))
