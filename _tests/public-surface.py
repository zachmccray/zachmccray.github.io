"""Reject leaked maintainer files and stale/duplicate Travel clients in any build.

Run against normal, localhost, and Pages-plugin builds. This is deliberately
independent of the baseline route count: a baseline with leaked docs must fail too.
"""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
checks = []


def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


internal = ('docs', '_firebase', '_tests', '_review', '.github', 'node_modules', 'vendor')
technical = ('README.md', 'Gemfile', 'Gemfile.lock', 'Gemfile.pages', 'pages-parity.yml')


def private_path(url):
    parts = unquote(urlsplit(url).path).strip('/').split('/')
    return parts[0] in internal or parts[-1] in technical


routes = sorted(str(p.relative_to(args.site)) for p in args.site.rglob('*.html'))
expected = json.loads((ROOT/'_tests/public-routes.json').read_text())
check('Exactly the 82 intentional public HTML routes', routes == expected and len(expected) == 82)
files = [str(p.relative_to(args.site)) for p in args.site.rglob('*') if p.is_file()]
check('No maintainer documents or test/rule/review files of any type published',
      not any(private_path('/'+p) for p in files))
client = '/assets/js/travel-atomic-receipts-1.js'
check('No obsolete Travel asset published', 'assets/js/travel.js' not in files)
asset = args.site/client.lstrip('/')
check('Served Travel asset bytes match the reviewed current source', asset.exists() and
      asset.read_bytes() == (ROOT/client.lstrip('/')).read_bytes())
published = {
    '/assets/css/custom-visual-media-1.css': 'assets/css/custom.css',
    '/assets/js/photography-portfolio-1.js': 'assets/js/photography.js',
    '/assets/js/image-carousel-1.js': 'assets/js/infinite-scroll.js',
    '/assets/js/blog-controls-2.js': 'assets/js/blog-controls.js',
}
for path, source in published.items():
    output = args.site/path.lstrip('/')
    check(path+' publishes the exact current source', output.exists() and
          output.read_bytes().strip() == (ROOT/source).read_bytes().strip())
for route in routes:
    html = (args.site/route).read_text()
    tags = Tags(html).tags
    links = [attrs.get('href', '') for tag, attrs in tags if tag == 'a']
    check(route+' has no internal sidebar or document links', not any(private_path(link) for link in links))
    scripts = [attrs for tag, attrs in tags if tag == 'script' and 'src' in attrs]
    styles = [a.get('href', '') for tag, a in tags if tag == 'link' and
              '/assets/css/custom' in a.get('href', '')]
    check(route+' loads exactly the versioned custom stylesheet', styles == ['/assets/css/custom-visual-media-1.css'])
    for name, needed in [('photography-portfolio-1', route == 'photography.html'),
                         ('blog-controls-2', route == 'blog.html'),
                         ('image-carousel-1', any('image-scroll-hyper' in a.get('class', '').split() for _, a in tags))]:
        matches = [s for s in scripts if s['src'] == '/assets/js/'+name+'.js']
        check(route+' scopes '+name+' once and deferred', len(matches) == int(needed) and all('defer' in s for s in matches))
    check(route+' does not load obsolete component assets', not any(urlsplit(s['src']).path in
          ['/assets/js/photography.js', '/assets/js/infinite-scroll.js', '/assets/js/blog-controls.js'] for s in scripts))
    travel = [s for s in scripts if re.search(r'/travel[^/]*\.js$', urlsplit(s['src']).path)]
    check(route+' loads exactly the intended Travel client on Travel only',
          ([s['src'] for s in travel] == [client] and 'defer' in travel[0])
          if route == 'travel.html' else not travel)
    check(route+' has one of each Firebase SDK on Travel only',
          sorted(urlsplit(s['src']).path.rsplit('/', 1)[-1] for s in scripts if 'firebase' in s['src']) ==
          (['firebase-app-compat.js', 'firebase-auth-compat.js', 'firebase-database-compat.js']
           if route == 'travel.html' else []))
search = json.loads((args.site/'assets/js/search-data.json').read_text())
check('Exactly 80 standard search entries with no maintainer results', len(search) == 80 and
      not any(private_path(r['url']) for r in search.values()))
course = [r for r in search.values() if r['doc'] == 'My Courses' and r['title'] != 'My Courses']
course_html = (args.site/'courses.html').read_text()
ids = [attrs['id'] for _, attrs in Tags(course_html).tags if 'id' in attrs]
check('All 45 unique course search fragments resolve exactly once', len(course) == 45 and
      len({r['url'] for r in course}) == 45 and
      all(urlsplit(r['url']).path == '/courses.html' and
          ids.count(urlsplit(r['url']).fragment) == 1 for r in course))
sitemap = args.site/'sitemap.xml'
if sitemap.exists():
    locations = [e.text for e in ElementTree.parse(sitemap).iter() if e.tag.endswith('}loc')]
    check('Sitemap contains no maintainer files', not any(private_path(url) for url in locations))
    check('Sitemap retains every intentional public route',
          set('/'+r.removesuffix('index.html') if r.endswith('index.html') else '/'+r for r in expected).issubset(
              {urlsplit(url).path for url in locations}))
else:
    check('No production sitemap is configured or published', True)
result = {'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
          'checks': checks, 'routes': routes, 'search_records': len(search),
          'sitemap': 'checked' if sitemap.exists() else 'absent',
          'travel_sha256': hashlib.sha256(asset.read_bytes()).hexdigest() if asset.exists() else None}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2)+'\n')
print('Public surface:', result['passed'], 'passed;', result['failed'], 'failed')
raise SystemExit(bool(result['failed']))
