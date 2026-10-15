"""Read-only post-deployment checks. Never runs JS or authenticates to Firebase."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='https://zachmccray.github.io')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
origin = args.url.rstrip('/')
assert urlsplit(origin).scheme == 'https' and not urlsplit(origin).username
routes = json.loads((ROOT/'_tests/public-routes.json').read_text())
client = '/assets/js/travel-atomic-receipts-1.js'
private = ['/'+str(p.relative_to(ROOT)) for p in (ROOT/'docs').rglob('*') if p.is_file()]
private += [p.removesuffix('.md')+'.html' for p in private if p.endswith('.md')]
private += ['/_firebase/database.rules.json', '/_tests/README.md',
            '/_review/core-reliability/report.md', '/README.md', '/Gemfile', '/Gemfile.lock']
paths = ['/'+r.removesuffix('index.html') if r.endswith('index.html') else '/'+r for r in routes]
paths += private+[client, '/assets/js/search-data.json', '/sitemap.xml']


def fetch(path):
    # curl uses the platform's normal verified TLS/proxy configuration.
    r = subprocess.run(['curl', '--silent', '--show-error', '--location', '--max-time', '20',
                        '--write-out', '\n%{http_code}', origin+path], capture_output=True)
    assert r.returncode == 0, (path, r.stderr.decode())
    body, status = r.stdout.rsplit(b'\n', 1)
    return path, (int(status), body)


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    responses = dict(pool.map(fetch, paths))
checks = []


def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})


check('All 82 public routes return HTTP 200', all(responses[p][0] == 200 for p in paths[:82]))
check('All maintainer document/rule/test/review URLs return HTTP 404',
      all(responses[p][0] == 404 for p in private))
check('Current versioned Travel asset returns the exact reviewed source',
      responses[client] == (200, (ROOT/client.lstrip('/')).read_bytes()))


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.tags = []; self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


for path in paths[:82]:
    tags = Tags(responses[path][1].decode()).tags
    travel = [a['src'] for tag, a in tags if tag == 'script' and '/assets/js/travel' in a.get('src', '')]
    check(path+' loads the intended single Travel client on Travel only',
          travel == ([client] if path == '/travel.html' else []))
    check(path+' contains no internal navigation',
          not any(urlsplit(a.get('href', '')).path.startswith('/docs/') for tag, a in tags if tag == 'a'))
search = json.loads(responses['/assets/js/search-data.json'][1])
check('Exactly 80 search entries and no internal documents', len(search) == 80 and
      not any(urlsplit(r['url']).path.startswith('/docs/') for r in search.values()))
course = [r for r in search.values() if r['doc'] == 'My Courses' and r['title'] != 'My Courses']
ids = [a['id'] for _, a in Tags(responses['/courses.html'][1].decode()).tags if 'id' in a]
check('All 45 unique course destinations resolve', len(course) == 45 and
      len({r['url'] for r in course}) == 45 and
      all(ids.count(urlsplit(r['url']).fragment) == 1 for r in course))
status, body = responses['/sitemap.xml']
check('Sitemap absent or contains no internal document URLs',
      status == 404 or status == 200 and b'/docs/' not in body)
result = {'origin': origin, 'passed': sum(c['passed'] for c in checks),
          'failed': sum(not c['passed'] for c in checks), 'checks': checks,
          'responses': {p: {'status': s, 'sha256': hashlib.sha256(b).hexdigest()}
                        for p, (s, b) in responses.items()},
          'limitation': 'Read-only HTTP checks; no Firebase authentication, likes, shares or JS execution.'}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2)+'\n')
print('Deployed surface:', result['passed'], 'passed;', result['failed'], 'failed')
raise SystemExit(bool(result['failed']))
