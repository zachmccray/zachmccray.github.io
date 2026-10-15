"""Build the real Liquid photo include with controlled optional/long metadata.

Run outside the checkout. All fixture facts/dimensions are synthetic test inputs.
The real _data/photography.yml is never edited.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
args = parser.parse_args()
source = args.source.resolve()
assert not args.root.resolve().is_relative_to(source)
args.root.mkdir(parents=True, exist_ok=True)
copy = args.root/'source'
shutil.copytree(source, copy, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git', '_review', '__pycache__', '.jekyll-cache'))
settings = {'body': 'Sony a7R III (fixture)', 'shutter_speed': '1/800s',
            'aperture': 'f/4', 'iso': 100, 'focal_length': '35mm'}
records = []
for i in range(110):
    camera = {name: value for bit, (name, value) in enumerate(settings.items()) if i % 32 & (1 << bit)}
    record = {'id': 'fixture-photo-'+str(i), 'src': '/assets/images/__fixture__/photo-'+str(i)+'.svg',
              'href': '/assets/images/__fixture__/photo-'+str(i)+'.svg', 'gallery': 'gallery1',
              'title': 'Fixture photograph '+str(i), 'alt': 'Controlled image fixture '+str(i)}
    if i % 3:
        record.update({'label': 'Fixture label '+str(i), 'date': 'Fixture date', 'location': 'Fixture location'})
    if i % 4:
        record['description'] = 'Controlled metadata example.'
    if i == 31:
        record['title'] += ' — '+('long label ' * 14)
        record['description'] = 'Long controlled description, not factual photo content. ' * 90
        record['location'] = 'Long controlled location ' * 15
    if camera: record['camera'] = camera
    records.append(record)
# JSON is valid YAML; no additional parser dependency is required.
(copy/'_data/photography.yml').write_text(json.dumps(records, indent=2)+'\n')
(args.root/'photo-fixtures.json').write_text(json.dumps(records, indent=2)+'\n')
# Exercise the real Liquid no-image branches without editing production posts.
empty_media = []
for importance in ('major', 'minor'):
    for post in sorted((copy/'_posts').glob('*.md')):
        text = post.read_text()
        if 'importance: '+importance in text and re.search(r'^image:', text, re.M):
            post.write_text(re.sub(r'^image:.*\n', '', text, count=1, flags=re.M))
            empty_media.append(str(post.relative_to(copy)))
            break
(args.root/'blog-fixtures.json').write_text(json.dumps(empty_media, indent=2)+'\n')
subprocess.run(['bundle', 'exec', 'jekyll', 'build', '--source', str(copy), '--destination',
                str(args.root/'site'), '--disable-disk-cache'], check=True,
               cwd=source, env={**os.environ, 'JEKYLL_ENV': 'production'})
print('Built real photo include with 110 synthetic records / all 32 camera combinations')
