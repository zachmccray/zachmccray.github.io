# Core reliability regressions

These scripts are excluded from Jekyll output by the `_tests` directory name.
The site also explicitly excludes `docs/`, `_firebase/`, `_tests/`, `_review/`,
`.github/`, dependency directories and root build files. Do not rely on Markdown
having no front matter: GitHub Pages automatically adds publication plugins.
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
They also reenact the pre-PR19 client from `19973eb` under current private rules,
reproducing its exact stale-client error. The current phase verifies the browser
requests one `travel-atomic-receipts-1.js` and receives the exact reviewed bytes.
Pass `--fixtures /path/to/cached/fonts` for previews using Inter.ttf, Font Awesome
6.5.0 CSS and its three WOFF2 files. Missing media remains synthetic/controlled.
Emulator tests establish local behavior, not remote rules, physical devices or quotas.

SDK 9.22.1's Node WebSocket implementation applies HTTP_PROXY to loopback even with
NO_PROXY. In this cloud, run **only the fixed-localhost Node test process** inside
`emulators:exec` with:
`env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy node --test ...`.
Keep the normal proxy for downloads/nonlocal work. Never use a real project for these
scripts, and never treat an optimistic cache/value event as commit confirmation.

## GitHub Pages publication parity and deployed checks

The previous checks only built the normal Jekyll profile, missing Pages' automatic
`jekyll-optional-front-matter`, `jekyll-default-layout` and title generation.
The pinned test-only profile adds these plus README/relative-link processing.
Sitemap generation is an additional probe; this does **not** enable a production
sitemap. This profile uses the repository's Jekyll 4.4.1 and pinned remote theme,
not the entire GitHub Pages legacy dependency stack. Its before-fix search index
was verified against the actual production index (all 84 records exactly equal).

```sh
BUNDLE_GEMFILE=_tests/Gemfile.pages bundle install
JEKYLL_ENV=production BUNDLE_GEMFILE=_tests/Gemfile.pages bundle exec jekyll build \
  --disable-disk-cache --config _config.yml,_tests/pages-parity.yml \
  --destination /tmp/pages-site
python _tests/public-surface.py --site /tmp/pages-site --out /tmp/pages-surface.json
```

Run `public-surface.py` against normal and localhost builds too. It rejects any
route beyond the frozen 82-route manifest, all maintainer output (including raw
Markdown), internal links/search/sitemap entries, stale or duplicate Travel scripts,
incorrect served script bytes and broken course-search fragments. Update the route
manifest only for intentional public content additions. The PR workflow runs normal,
Pages-plugin and localhost profiles and content/search/SEO preservation comparisons.

After the owner merges and the successful Pages deployment completes:

```sh
python _tests/verify-deployed.py --out /tmp/deployed-surface.json
```

This performs read-only HTTPS checks of all 82 routes, every internal `docs/` URL
and its generated HTML counterpart, representative private paths, all sidebar
links, search records, course fragments, sitemap and exact current Travel bytes.
It never authenticates or executes Firebase. Before this hotfix, its expected
failures demonstrate the production leak and absence of the new asset. It cannot
pass before the hotfix is deployed. The owner should then reload an ordinary
browser tab and verify one-click like/unlike; also use a fresh/private context.
Already-open pages and cached HTML can retain an old reference until reloaded or
expired (observed Pages cache lifetime: 600 seconds). The distinct script pathname
prevents updated HTML from reusing the obsolete asset. Keep database rules private;
no rules publication, resets or data migrations accompany this hotfix.

## Photography, Timeline and bounded carousels

Keep a build/source archive of merged `8bd2daa` outside the checkout. For this
intentional visual change use the component-aware preservation check below;
`preservation.py` remains strict for normal/Pages/localhost parity of one revision.
Neither script relaxes route, course-anchor, SEO or Firebase preservation.

```sh
python _tests/component-preservation.py --baseline /tmp/site-baseline \
  --baseline-source /tmp/source-baseline --site /tmp/site-candidate \
  --out /tmp/component-preservation.json
python _tests/prepare-visual-fixtures.py --root /tmp/visual-metadata-fixtures
python _tests/visual-media.py --site /tmp/site-candidate \
  --fixtures /tmp/cached-visual-assets --metadata-fixtures /tmp/visual-metadata-fixtures \
  --out /tmp/visual-media
python _tests/carousel-behavior.py --site /tmp/site-candidate --out /tmp/carousel-behavior
python _tests/carousel-performance.py --baseline /tmp/site-baseline \
  --site /tmp/site-candidate --out /tmp/carousel-performance
```

Visual assets are `Inter.ttf`, `glightbox.js` and `glightbox.css` (GLightbox 3.3.1,
the site's pinned jsDelivr version). Supply these cached files with their upstream
licenses; the review manifest records their hashes. They are browser-test fixtures,
not new production dependencies. Image SVGs are generated locally. The real
Liquid fixture build uses 110 labeled synthetic photo records, every one of the
32 optional camera-field combinations, long/absent metadata, and one major/one
minor post without an image. Original data/posts are never edited. `--source`
can build the same controlled records using the baseline include for previews.

`visual-media.py` exercises actual served controllers, GLightbox, native links and
sorting/filtering at twelve widths and eight orientations; 30/60/110-photo
portrait/landscape/mixed galleries, keyboard/touch/modal focus, failed originals
and both real Liquid no-image branches. `--only gallery|timeline|carousels|fixtures`
supports focused reruns. External analytics, auth and production databases are
blocked. Use the separately enforced Firebase suites for permission guarantees.

`carousel-behavior.py` checks actual wheel input and Chromium touch input, finite
one/two-photo sets, source order/ratios, bounded copies, held-pointer release,
equivalent boundary content (allowing <1px fractional rounding), resize selection,
late/error events and idempotent refresh for 1/2/5/12/150/180 images. It does not
certify physical iOS/Android inertia or substitute for owner visual acceptance.

The performance lab runs seven alternating fresh contexts per phase/count at 1×
and 4× CPU. It uses actual baseline/current CSS/JS with native local HTTP/cache,
not route-mocked timing. Report DOM/images, initialization callback work including
layout, CDP layout/script time, image resources/transfers, repeated scroll/resize
tasks, post-GC DOM and JS heap. Do not claim sixfold network/decoded-memory savings:
browsers reuse duplicate URLs, unique transfers can be unchanged, and this does
not measure decoded-image/GPU memory. Small-set overhead may rise because controls,
readiness and resize preservation are now implemented. This is a shared-cloud lab,
not production Core Web Vitals or a physical-device benchmark.

The publication workflow now also asserts exact compiled versioned component bytes,
single scoped/deferred scripts and one current custom stylesheet on every page.
No workflow/config/Firebase deployment changes are needed for this PR.

## Framework hardening and accessibility

Use the merged PR #21 source/build as the baseline. `framework-preservation.py`
checks all 82 routes, exact SEO, functional links/media/IDs, all 80 byte-identical
search records and protected post/Travel/course/photo/Firebase sources. Its only
main-content exceptions are the declared Photography entry-point name and inline
Travel action icons; it also freezes the Blog comparator logic. Keep the strict
normal/Pages/localhost `preservation.py` comparison too.

```sh
mkdir -p /tmp/framework-tools
cp _tests/accessibility/package*.json /tmp/framework-tools/
npm ci --prefix /tmp/framework-tools --no-audit --no-fund
python _tests/prepare-framework-assets.py --deps /tmp/framework-tools/node_modules \
  --out /tmp/framework-browser-assets
python _tests/framework-preservation.py --baseline /tmp/site-baseline \
  --baseline-source /tmp/source-baseline --site /tmp/site-candidate \
  --out /tmp/framework-preservation.json
python -m playwright install --with-deps chromium firefox webkit
python _tests/framework-browser.py --site /tmp/site-candidate \
  --assets /tmp/framework-browser-assets --deps /tmp/framework-tools/node_modules \
  --browser chromium --out /tmp/framework-chromium
# Repeat the last command with --browser firefox and --browser webkit.
python _tests/framework-history.py --site /tmp/site-candidate \
  --assets /tmp/framework-browser-assets --out /tmp/framework-native-history
```

axe-core 4.11.0 and GLightbox 3.3.1 are test-only, lockfile-pinned dependencies.
The asset helper downloads Inter from a pinned Google Fonts revision, verifies
its SHA-256 and retains its license; it copies GLightbox from the verified npm
package. Nothing is added to the production JavaScript dependency graph. The
framework workflow runs all three Linux engines and the publication profile.
Browser downloads may be unavailable in restricted local cloud networks; record
that limitation and use the CI results rather than claiming local engine coverage.

`framework-browser.py` runs full-page axe snapshots at desktop/mobile widths,
search/failed-search/open-viewer/library-fallback scans, keyboard focus/scroll,
direct anchors, twelve widths/eight orientations, primary navigation, native
Back/Forward/refresh, restored Blog state, missing fonts/media/libraries/theme,
SVG action feedback and no-JavaScript navigation. All production services are
blocked and Firebase is only an in-memory UI fixture here; keep the enforced
SDK/rules/transport suites separately. Axe findings and incomplete/manual-review
items are saved, not treated as a WCAG certification. 640×450 and 320×225 CSS
viewports cover 200%/400% reflow equivalence for a 1280×900 window; they do not
claim actual browser-chrome zoom or physical-device testing.

The routed tests disable HTTP caching and may see font reflow when returning.
They assert the same visible Timeline context rather than exact scroll pixels.
`framework-history.py` complements them with native HTTP/cached fonts and actual
Chromium BFCache (persisted=true) and reconstructed-page (persisted=false) paths,
verifying exact native scroll offsets. It uses full Chromium in CI, since the
headless shell need not support BFCache. Test-only HTML URL mapping plus a
self-only CSP prevent production SDK/analytics/font requests. No global history
state or scroll-restoration override is shipped.

For the icon delivery comparison, supply the baseline's cached Font Awesome 6.5.0
CSS plus regular/solid WOFF2 files alongside Inter.ttf:

```sh
python _tests/framework-performance.py --baseline /tmp/site-baseline \
  --site /tmp/site-candidate --assets /tmp/cached-visual-assets \
  --out /tmp/framework-performance.json
```

This lab alternates seven fresh contexts per phase at 1×/4× CPU, serving real
component code and font files over local HTTP. Only external font URLs in the
test HTML are mapped locally; SDK/analytics are blocked and media are synthetic.
Report browser transfer bytes including the document, requests, JS/layout/style
work, DOM/heap and laboratory paint/layout shifts. Inter TTF fixture bytes differ
from production WOFF subsets; this is not CDN latency, production Firebase timing,
real-photo performance or production Core Web Vitals. Report the added inline SVG
and DOM costs as well as the removed stylesheet/font requests.

The framework suite waits for font/layout readiness before measuring actual search
click destinations, with an explicit delayed-font case. Its JavaScript-disabled
fixture uses completed network loading and native layout checks instead of awaiting
a page-level FontFaceSet Promise (which does not resolve there in Firefox).
Font/axe/whole-run time limits prevent unbounded CI stalls. Failure annotations and
a compact final engine/version/assertion/axe summary are readable through GitHub's
checks API even when the artifact-storage download host is blocked; the raw scans
and screenshots remain attached to the Actions run. Only five progress notices are
emitted per step, leaving room for the final summary within GitHub's annotation cap.
