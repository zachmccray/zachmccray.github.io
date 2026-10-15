"""Pinned, licensed browser fixtures outside the checkout; no production assets."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--deps',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
font='https://raw.githubusercontent.com/google/fonts/94301472b4d809299b4775bc6502592b83dd6934/ofl/inter/'
target=a.out/'Inter.ttf'
subprocess.run(['curl','--fail','--silent','--show-error','--location',font+'Inter%5Bopsz,wght%5D.ttf','--output',str(target)],check=True)
assert hashlib.sha256(target.read_bytes()).hexdigest()=='29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031'
subprocess.run(['curl','--fail','--silent','--show-error','--location',font+'OFL.txt','--output',str(a.out/'Inter-OFL.txt')],check=True)
for src,dst in [('dist/js/glightbox.min.js','glightbox.js'),('dist/css/glightbox.min.css','glightbox.css'),('LICENSE.md','GLightbox-LICENSE.txt')]:
    shutil.copy2(a.deps/'glightbox'/src,a.out/dst)
(a.out/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.out.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2)+'\n')
print('Prepared Inter and real pinned GLightbox fixture files')
