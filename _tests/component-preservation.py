"""Compare approved component changes against a merged build without broad skips."""
import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--baseline-source', type=Path, required=True)
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
checks = []


def check(name, ok):
    checks.append({'check': name, 'passed': bool(ok)})
    assert ok, name


class Parts(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []; self.records = []; self.info = {}; self.stack = []
        self.active = None; self.info_id = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); classes = a.get('class', '').split()
        self.tags.append((tag, a))
        if 'blog-entry' in classes:
            self.active = {'data': [a.get('data-date'), a.get('data-year'), 'major' in classes],
                           'text': [], 'images': [], 'links': []}
            self.records.append(self.active)
            a['_record'] = True
        if 'photo-info' in classes:
            self.info_id = a['id']; self.info[self.info_id] = []
            a['_info'] = True
        if self.active:
            if tag == 'img': self.active['images'].append([a.get('src'), a.get('alt')])
            if tag == 'a': self.active['links'].append(a.get('href'))
        if tag not in {'img', 'br', 'hr', 'meta', 'link', 'input', 'source', 'wbr', 'area', 'embed'}:
            self.stack.append((tag, a))

    def handle_endtag(self, tag):
        if tag in {'img', 'br', 'hr', 'meta', 'link', 'input', 'source', 'wbr', 'area', 'embed'}:
            return
        while self.stack:
            t, a = self.stack.pop()
            if a.get('_record'): self.active = None
            if a.get('_info'): self.info_id = None
            if t == tag: break

    def handle_data(self, text):
        if self.active: self.active['text'].append(text)
        if self.info_id: self.info[self.info_id].append(text)


def main(text): return re.search(r'<main[^>]*>(.*?)</main>', text, re.S)[1]
def words(text): return ' '.join(text.split())
def loading_only(text):
    return re.sub(r'<img\b[^>]*>', lambda m: re.sub(r'\s(?:decoding="async"|loading="lazy")', '', m[0]), text)


routes = sorted(str(p.relative_to(args.baseline)) for p in args.baseline.rglob('*.html'))
check('Exactly the same 82 HTML routes', len(routes) == 82 and routes ==
      sorted(str(p.relative_to(args.site)) for p in args.site.rglob('*.html')))
for route in routes:
    before = (args.baseline/route).read_text(); after = (args.site/route).read_text()
    a = Parts(before); b = Parts(after)
    seo = lambda p: [(tag, attrs) for tag, attrs in p.tags if tag == 'meta' or
                     tag == 'link' and attrs.get('rel') == 'canonical']
    check(route+' exact meta/canonical fields', seo(a) == seo(b))
    for expression in [r'<title>.*?</title>', r'<script type="application/ld\+json">.*?</script>']:
        check(route+' exact title/structured data', re.findall(expression, before, re.S) == re.findall(expression, after, re.S))
    if route == 'blog.html':
        check('All 64 Blog records and original ordering', len(a.records) == len(b.records) == 64)
        for i, (old, new) in enumerate(zip(a.records, b.records)):
            check(f'Blog {i}: original dates/year/importance', old['data'] == new['data'])
            check(f'Blog {i}: exact original wording', words(' '.join(old['text'])) == words(' '.join(new['text'])))
            check(f'Blog {i}: original image references and alt text', old['images'] == new['images'])
            expected = old['links'] * (2 if old['data'][2] and old['images'] else 1)
            check(f'Blog {i}: only the approved major thumbnail link added', new['links'] == expected)
    elif route == 'photography.html':
        keys = ['href', 'data-gallery', 'data-title', 'data-description', 'data-alt', 'aria-describedby']
        gallery = lambda p: [[attrs.get(k) for k in keys] for tag, attrs in p.tags
                             if tag == 'a' and 'glightbox' in attrs.get('class', '').split()]
        check('All 30 Photography records/references/fields in original order', len(gallery(a)) == 30 and gallery(a) == gallery(b))
        check('All original photo metadata fragment IDs', list(a.info) == list(b.info))
        for id, old in a.info.items():
            check(id+' retains every original factual metadata token', not
                  (Counter(words(' '.join(old)).split()) - Counter(words(' '.join(b.info[id])).split())))
    else:
        check(route+' exact main content except native image loading attributes', loading_only(main(before)) == loading_only(main(after)))
old = json.loads((args.baseline/'assets/js/search-data.json').read_text())
new = json.loads((args.site/'assets/js/search-data.json').read_text())
check('All 80 existing native search identities/destinations', len(old) == len(new) == 80 and
      {k: {f: r[f] for f in ['doc', 'title', 'url', 'relUrl']} for k, r in old.items()} ==
      {k: {f: r[f] for f in ['doc', 'title', 'url', 'relUrl']} for k, r in new.items()})
check('All 79 non-Photography search records exactly unchanged',
      all(r == new[k] for k, r in old.items() if r['doc'] != 'Photography'))
for file in ['_data/photography.yml', '_data/coursework.yml', 'assets/js/travel-atomic-receipts-1.js',
             '_firebase/database.rules.json', '_firebase/maintenance.rules.json',
             'assets/js/search.js', 'assets/js/site-ui.js', 'assets/js/just-the-docs.js', '_config.yml']:
    check(file+' source byte-identical to merged baseline',
          (args.baseline_source/file).read_bytes() == (args.source/file).read_bytes())
for folder in ['_posts', '_travel']:
    for file in sorted((args.baseline_source/folder).glob('*.md')):
        after = args.source/folder/file.name
        check(str(after.relative_to(args.source))+' content/front matter preserved',
              loading_only(file.read_text()) == loading_only(after.read_text()))
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps({'passed': len(checks), 'checks': checks,
    'search_change': 'Only Photography snippet text reflects its updated hint and source metadata; all identities/destinations and 79 other records unchanged.'}, indent=2)+'\n')
print('Component preservation checks passed:', len(checks))
