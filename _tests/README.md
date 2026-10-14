# Core reliability regressions

These scripts are excluded from Jekyll output by the `_tests` directory name.
Use Node 18+ for isolated Firebase tests, and Python 3.10+ with Playwright for browser tests.
No script writes to production Firebase; browser checks intercept all third-party requests.

```sh
node --test _tests/firebase.test.cjs _tests/firebase-rules/trusted-updater.test.cjs
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
anchor offsets, all nine read-only Travel like controls and completed/canceled sharing.
Like mutations are intentionally release-blocked; these checks do not claim working likes. Neutral images and an
in-memory RTDB model are fixtures. Font/CDN rendering and real screen readers are
outside this portable functional test's scope. Pass `--chromium /path/to/chromium`
when using a system browser rather than Playwright's installed Chromium.

Save a baseline build from `gh-pages` outside the checkout before building this branch:

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

The in-memory fixture exercises client containment/errors and share atomicity, not
security rules. The frozen query fixture should change only alongside intentional
Coursework changes, not to make a regression disappear.

## Enforced Firebase tests

Read [the root cause and approval boundary](../docs/travel-like-reliability.md).
`firebase-rules/*.rules.json` are local emulator fixtures/candidates, **not rules to
publish**. Owner-supplied rules are reproduced without claiming deployed verification.
The trusted updater is a server-design prototype, not a browser or deployed backend.

Install pinned test-only dependencies outside the checkout (Node 20+; Java 21+):

```sh
mkdir -p /tmp/website-firebase-tests
cp _tests/firebase-rules/package.json /tmp/website-firebase-tests/
npm install --prefix /tmp/website-firebase-tests --no-audit --no-fund
export NODE_PATH=/tmp/website-firebase-tests/node_modules
export FIREBASE_EMULATORS_PATH=/tmp/website-firebase-tests/emulators
/tmp/website-firebase-tests/node_modules/.bin/firebase emulators:exec \
  --only database --project demo-website-reliability \
  --config _tests/firebase-rules/firebase.json \
  'node --test _tests/firebase-rules/emulator.test.cjs'
```

All service addresses are fixed to localhost and the demo project; no production
credentials are required. Official emulator download: `storage.googleapis.com`.
Tests use Firebase 9.22.1, matching the site's SDK, and rules-unit-testing 2.0.7.
They reproduce the denied parent transaction, public user-map reads, duplicate
increments under supplied rules, candidate private/coupled atomic transitions,
split/forged/other-user denials, 20 distinct users/ten same-user clients, historic
inconsistencies, a privileged transaction prototype and an actual offline queue/
optimistic-marker/reconnect check. No mock fallback exists.

For actual served-UI integration, start that emulator with `emulators:start` instead
of `emulators:exec`, then in another terminal:

```sh
python _tests/firebase-rules/browser.py --url http://localhost:4000 \
  --sdk /tmp/website-firebase-tests/node_modules/firebase --out /tmp/enforced-travel
```

This serves the real Firebase SDK and current Travel JS/UI against enforced emulator
rules; only authentication tokens, missing media and unrelated third-party requests
are fixtures. It also reproduces the previous PR19 UI failure from commit `02839e0`.
Keep that history available. Browser requests cannot reach production Firebase/auth
or analytics. Results show all nine original paths/current states, normal native
cancellation, unchanged records, real atomic sharing and the absence of parent reads
or like writes in the revised client. Endpoint/physical-device authentication is not
certified by emulator tokens. Pass `--fixtures /path/to/cached/fonts` optionally
for previews using `Inter.ttf`, `fontawesome.css` (6.5.0) and its three WOFF2 files.

In this cloud environment, SDK 9.22.1's Node WebSocket implementation applies
`HTTP_PROXY` even to loopback, ignoring `NO_PROXY`. Run **only the fixed-localhost test
process** with `env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy node ...`
inside `emulators:exec` if needed. Keep normal proxy configuration for downloads and
all nonlocal work. Never redirect these tests to a real Firebase project.
