"""Exact content/SEO/source preservation with declared editorial UI additions."""
import argparse, json, re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from search_contract import expected_destinations

p = argparse.ArgumentParser()
for name in ('baseline', 'baseline-source', 'site', 'out'):
    p.add_argument('--'+name, type=Path, required=True)
a = p.parse_args(); source = Path(__file__).resolve().parent.parent; checks = []

def check(name, ok):
    checks.append({'check': name, 'passed': bool(ok)})

class Content(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.stack=[]; self.words=[]; self.links=[]; self.media=[]; self.ids=[]; self.seo=[]; self.lang=[]; self.feed(html)
    def handle_starttag(self, tag, attrs):
        d=dict(attrs); classes=d.get('class','').split()
        ignore=any(x[1] for x in self.stack) or bool(set(classes)&{'section-nav','photo-summary','gallery-hint'}) or tag in ('script','style')
        if 'id' in d:self.ids.append(d['id'])
        if tag=='meta' or tag=='link' and d.get('rel')=='canonical':self.seo.append((tag,d))
        in_main=tag=='main' or any(x[0]=='main' for x in self.stack)
        if in_main and not ignore:
            if tag=='a':self.links.append(d.get('href'))
            if tag in ('img','source','video'):self.media.append((tag,d))
            if 'lang' in d:self.lang.append(d['lang'])
        if tag not in ('img','source','br','hr','input','meta','link','wbr','area','embed'):
            self.stack.append((tag,ignore))
    def handle_endtag(self, tag):
        if tag in ('img','source','br','hr','input','meta','link','wbr','area','embed'):return
        while self.stack:
            current=self.stack.pop()
            if current[0]==tag:break
    def handle_data(self, text):
        if any(x[0]=='main' for x in self.stack) and not any(x[1] for x in self.stack):self.words.extend(text.split())

routes=lambda root:sorted(str(f.relative_to(root)) for f in root.rglob('*.html'))
check('Exactly the 82 baseline routes',len(routes(a.baseline))==82 and routes(a.baseline)==routes(a.site))
for route in routes(a.baseline):
    before=(a.baseline/route).read_text();after=(a.site/route).read_text();x=Content(before);y=Content(after)
    check(route+': exact meaningful wording/order', x.words==y.words)
    check(route+': exact existing functional links/order', x.links==y.links)
    check(route+': exact media attributes and language samples',x.media==y.media and x.lang==y.lang)
    check(route+': all old fragment IDs retained once',not (Counter(x.ids)-Counter(y.ids)) and len(y.ids)==len(set(y.ids)))
    check(route+': unchanged SEO',x.seo==y.seo and re.findall(r'<title>.*?</title>|<script type="application/ld\+json">.*?</script>',before,re.S)==re.findall(r'<title>.*?</title>|<script type="application/ld\+json">.*?</script>',after,re.S))
old=json.loads((a.baseline/'assets/js/search-data.json').read_text());new=json.loads((a.site/'assets/js/search-data.json').read_text())
check('All exact intended standard search identities',expected_destinations(new))
check('All non-Photography search snippets byte-identical', [r for r in old.values() if r['doc']!='Photography']==[r for r in new.values() if r['doc']!='Photography'])
protected=['_config.yml','Gemfile','Gemfile.lock','assets/js/search.js','assets/js/site-ui.js','assets/js/just-the-docs.js','assets/js/blog-controls.js','assets/js/travel-atomic-receipts-1.js','_includes/course-list.md','courses.md','index.md','academics.md']
for folder in ('_data','_posts','_firebase'):
    protected += [str(f.relative_to(a.baseline_source)) for f in (a.baseline_source/folder).rglob('*') if f.is_file()]
for name in protected:check(name+': source byte-identical',(a.baseline_source/name).read_bytes()==(source/name).read_bytes())
for file in (a.baseline_source/'_travel').glob('*.md'):
    text=(source/'_travel'/file.name).read_text().replace('\nsection_navigation: false # Copied placeholder outline; enable when authored.','')
    check(file.name+': only curated navigation opt-out added',text==file.read_text())
result={'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
print('Editorial preservation:',result['passed'],'passed;',len(result['failed']),'failed')
raise SystemExit(bool(result['failed']))
