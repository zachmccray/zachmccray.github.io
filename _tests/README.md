# Core reliability regressions

These scripts are excluded from Jekyll output by the `_tests` directory name.
Use Node 18+ for isolated Firebase tests, and Python 3.10+ with Playwright for browser tests.
No script writes to production Firebase; browser checks intercept all third-party requests.

```sh
node --test _tests/firebase.test.cjs
python -m pip install -r _tests/requirements.txt
python -m playwright install chromium
JEKYLL_ENV=production bundle exec jekyll build --destination /tmp/site-candidate
python _tests/browser.py --site /tmp/site-candidate --out /tmp/browser-results
# Or use a running Jekyll server; this exercises real locally served search.
python _tests/browser.py --url http://localhost:4000 --out /tmp/served-results
```

`browser.py` runs native search loading/error/retry interactions, disabled/corrupt/stale
cache cases, all 135 frozen course queries and 90 code/title destination clicks, 12
widths/eight orientation profiles, mobile/desktop keyboard retry and Escape,
complete batched results after real typing/focus return, menu focus exit,
keyboard selection, history,
anchor offsets, and all nine Travel like/unlike/share controls. Neutral images and an
in-memory RTDB model are fixtures. Font/CDN rendering and real screen readers are
outside this portable functional test's scope. Pass `--chromium /path/to/chromium`
when using a system browser rather than Playwright's installed Chromium.

Save a baseline build from `gh-pages` in another worktree before building this branch:

```sh
python _tests/preservation.py --baseline /tmp/site-baseline --site /tmp/site-candidate --out /tmp/preservation.json
python _tests/performance.py --baseline /tmp/site-baseline --site /tmp/site-candidate --out /tmp/performance.json
```

`preservation.py --local-url http://localhost:4000` can compare a local build to
the production baseline, normalizing that origin only (canonical/social/share URLs
are expected to use localhost in local development).

Performance checks alternate seven fresh contexts per phase at 1×/4× CPU throttling.
They report local HTTP transferred bytes/request counts, script duration, native
index construction, session restoration and laboratory paint timing. They are not
production Core Web Vitals. `--fixtures /path/to/fixtures` optionally supplies the
same `Inter.ttf` and `fontawesome.css` in both phases for controlled font comparisons;
those fixture font bytes are never treated as production WOFF2 transfer savings.

The RTDB fixture exercises atomic semantics and errors, not deployed security rules.
Confirm parent transaction permissions locally before merging; see
`docs/core-reliability.md`. The frozen query fixture should change only alongside
intentional Coursework content/search changes, not to make a regression disappear.
