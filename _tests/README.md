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
anchor offsets, all nine one-click Travel like/unlike controls, completed/canceled
sharing and absence of parent transactions/other-user reads. Neutral images and an
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

Read [the complete rules/deployment guide](../_firebase/README.md).
`_firebase/database.rules.json` is the proposed production policy; no command below
publishes it. Older `firebase-rules/private-*.rules.json` and trusted-updater files
are historical investigation fixtures. The current suite tests the actual client
helpers against the proposed rules and retains owner-supplied rules for cutover checks.

Install test-only dependencies outside the checkout (Node 20+; Java 21+):

```sh
mkdir -p /tmp/website-firebase-tests
cp _tests/firebase-rules/package.json /tmp/website-firebase-tests/
npm install --prefix /tmp/website-firebase-tests --no-audit --no-fund
export NODE_PATH=/tmp/website-firebase-tests/node_modules
export FIREBASE_EMULATORS_PATH=/tmp/website-firebase-tests/emulators
/tmp/website-firebase-tests/node_modules/.bin/firebase emulators:exec \
  --only database,auth --project demo-website-reliability \
  --config _tests/firebase-rules/firebase.json \
  'node --test _tests/firebase-rules/option-a.test.cjs'
```

All services are fixed to loopback/demo project; no production credentials. The SDK
is 9.22.1, matching the site; rules-unit-testing 2.0.7 and firebase-tools 14.26.0 are
pinned. The official RTDB emulator download uses `storage.googleapis.com`. The suite
has no mock fallback: ownership/privacy, like/unlike/no-op intents, immutable proofs,
forged/split/cross-user/delete/multi-proof writes, same/distinct-user contention,
new/legacy malformed counts, under/overcounts, offline/newer opposite intents,
share repetitions/replays, old/new client compatibility, in-flight cutover and private
maintenance rollback. `firebase.test.cjs` supplements it with isolated UI/error cases.

For actual SDK/UI/Anonymous Authentication and network-loss testing, start the same
emulators with `emulators:start` in a persistent session, then run in another terminal:

```sh
python _tests/firebase-rules/browser.py --url http://localhost:4000 \
  --sdk /tmp/website-firebase-tests/node_modules/firebase --out /tmp/enforced-travel
python _tests/firebase-rules/transport.py --url http://localhost:4000 \
  --sdk /tmp/website-firebase-tests/node_modules/firebase --out /tmp/enforced-transport
```

The browser uses real automatic Anonymous Auth and Database SDKs with both emulators.
It verifies all nine click/keyboard like/unlike controls, retained counts/markers,
no account/verification UI, persistent anonymous identity, cancellation and actual
clipboard success even when analytics is denied. `transport.py` drops actual successful
WebSocket ACKs, closes the connection, asserts SDK resends/proof acknowledgements and
tests an intervening opposite action in a second tab. Real rules always enforce
writes. Native-share completion/cancellation is controlled because headless Linux
cannot certify the platform dialog. Production Firebase/analytics requests are blocked.

These checks reproduce old PR19 failures from commit `02839e0`; retain that history.
Pass `--fixtures /path/to/cached/fonts` for previews using Inter.ttf, Font Awesome
6.5.0 CSS and its three WOFF2 files. Missing media remains synthetic/controlled.
Emulator tests establish local behavior, not remote rules, physical devices or quotas.

SDK 9.22.1's Node WebSocket implementation applies HTTP_PROXY to loopback even with
NO_PROXY. In this cloud, run **only the fixed-localhost Node test process** inside
`emulators:exec` with:
`env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy node --test ...`.
Keep the normal proxy for downloads/nonlocal work. Never use a real project for these
scripts, and never treat an optimistic cache/value event as commit confirmation.
