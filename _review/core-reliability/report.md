# Performance and core reliability review

Branch: `perf/core-reliability`, based on latest merged `gh-pages` `19973eb`.
One PR for local review; production remains unmodified and the PR must stay unmerged.

## Implementation

- Native Just the Docs search loads Lunr/data on demand, replays early/pasted input,
  provides loading/error/keyboard retry, and restores session indexes only against
  the exact retrieved data and matching builder/Lunr versions. Corrupt/disabled/stale
  storage falls back to the native builder. All 80 standard records and 45 course
  destination anchors remain unchanged; no generator override or placeholder indexing.
- The pinned theme exposes no lifecycle hook. Its 53-line head and runtime have a
  guarded integration: deferred scripts, initialization delegation, no forced page
  scroll, and cancellation of native result batches only when the query changes.
  Full-result tests verify all 18 EECS 101 matches after real typing/focus return;
  associations alone would miss an interrupted batch. Native ranking, snippets,
  highlighting, result URLs and Arrow/Enter/Escape handlers remain in use.
- Accessible suggestions use the native list as a listbox inside a named region;
  retry stays an ordinary button outside it. Tab exits suggestions, arrow keys choose
  a result, and Enter follows its unchanged URL. Error-button Escape works in one
  press. Mobile retry uses the original event path so replacing feedback does not
  dismiss the menu. Retry text computes to Inter 15px/24px with a 44px minimum target
  and the established 3px purple focus outline; input remains 16px.
- Likes use one post-level transaction with a fixed retry intent. User marker/count
  change together; other users and unknown fields remain intact. Invalid schema and
  known legacy marker undercounts abort without rewriting data or decrementing
  existing contributions. Shares use one atomic increment/marker update per completed
  action, with independent logging so a queued write does not hold sharing disabled.
  Native sharing uses the existing article title. No production records/rules changed.
- Font Awesome loads on Travel only. Inter's original four weights/display=swap move
  directly to the head with preconnect. Pin the audited theme SHA and tested GLightbox
  3.3.1; no dependency upgrade, global typography reset or image changes.

Audit findings addressed: **A1/A2/A3, B1/B4/B6/B7, A6**.

## Comparable performance evidence

Seven fresh contexts per phase/rate, alternating order; Chromium 154, 390×844,
actual compiled JS and standard 80-record JSON from local HTTP. Native functions
are timed with a transparent test-only Proxy. No simultaneous browser regressions
ran during this measurement.

| 4× CPU median | Baseline | Revision |
| --- | ---: | ---: |
| Index build on initial page load | 183.7ms | 0ms |
| Cold native build | 183.7ms (startup) | 178.6ms (first use) |
| Session native Index.load | — | 20.5ms |
| Initial total script duration | 217.8ms | 19.6ms |
| Initial local HTTP transferred bytes, including headers | 290,869 | 215,241 |
| Initial requests, including controlled externals | 12 | 10 |
| Laboratory FCP | 300ms | 244ms |

Initial local transfer drops by 75,628 bytes.
The earlier audit's 182ms construction is reproduced at 183.7ms;
its new range is 142.7–192.3ms.
Cold first use still pays construction/network cost; this moves work to visitors
using search rather than promising instant first-use search. Session Index.load
excludes storage/JSON parsing, UI rendering and network time.

The separately removed Font Awesome stylesheet is 102,526 decoded bytes (21,865
estimated gzip), omitted on 81/82 routes. This CDN payload is excluded from the local
HTTP totals above. Synthetic font/media transfers are also excluded. Google font
WOFF2 payloads/cache headers and live production were inaccessible, so no actual
font-byte or production Core Web Vitals claims are made. FCP ranges and all 28 raw
samples are in [performance-results.json](performance-results.json).

## Validation

- Production and actual localhost Jekyll serve/build succeeded. Existing upstream
  Sass deprecation warnings remain. 580 preservation checks per build; all **82 HTML
  routes**, main content, public links/assets, IDs and SEO retained. Local origin is
  normalized only when comparing canonical/social/share URLs against production.
- Real Jekyll-served browser suite: **554 checks**, 135 course queries, 90 code/title
  destination clicks across all 45 headings, keyboard retry/loading/error/network/
  malformed data/missing library, corrupt/disabled/stale cache, fresh changed numeric
  IDs, full native batching, Tab/arrow/Escape, Back/Forward and 20 responsive profiles.
- Baseline/candidate actual serve: early query gives **0 → 18 results** without another
  keystroke. Controlled 503 gives **silent failure → readable retry feedback**.
- Additional retained search/keyboard: **335 checks**, including all 23 other section
  destinations. UI: **262**; navigation: **130**; Blog sorting/filtering/optional legacy
  lightbox: **110**; Travel sharing/IDs/URLs: **88**; carousel/navigation: **64**.
- Photography: **1,512** collage checks (portrait, landscape, mixed, very tall/wide,
  30/60/120 photos, long metadata, hover/keyboard/touch/GLightbox/fallback), **100**
  gallery responsive checks, **1,017** actual Liquid optional-camera checks. Gallery
  source/behavior is unchanged apart from the dependency pin.
- Firebase: **12 isolated scenarios**: atomicity, rejected child/parent writes, lost
  acknowledgements, fixed-intent retry, 20 concurrent users, repeated/mixed same-user
  intents, pending network/resume, auth/read failures, invalid and legacy partial
  states, repeated atomic shares and responsive queued logging. No production tests.
- **39** controlled visual pairs at 390/820/1440: approved main-content geometry,
  typography and pixels unchanged. Navigation/search chrome excluded from that
  comparison; native select/video paint masked consistently, with DOM/styles and
  interactions checked separately. Screenshots use identical cached Inter/libraries
  and neutral missing-media fixtures. Dimensions describe fixtures only.
- All twelve widths: 320, 375, 390, 430, 600, 601, 768, 820, 1024, 1280, 1440, 1920.
  Eight portrait/landscape profiles retained. No new horizontal overflow or healthy-
  flow page exceptions; injected transport errors are expected fixture failures.

Evidence: [validation.json](validation.json). Portable checks and commands:
[testing README](../../_tests/README.md).

## Before/after screenshots

[Homepage desktop](homepage-desktop.png) · [Homepage mobile](homepage-mobile.png) ·
[Mobile keyboard focus exit](mobile-keyboard.png) ·
[Mobile search failure](search-failure-390.png) · [Desktop search failure](search-failure-1440.png).

Homepage presentation stays intact. The menu now dismisses when Tab reaches main
content, and search failure has readable, keyboard-accessible feedback.

## Limits and remaining work

**Verify deployed Firebase permissions during local review before merging.** Rules
are not in the repository; likes require read/write at `likes/<post-id>` including
its user map. Child-only rules can deny the parent transaction. The client fails
closed without a split-write fallback; no production rules changes are made. Do not
broaden public reads solely for this implementation. If that access is intentionally
restricted, a separately authorized rules/backend design is needed. Parent user-map
size/contention also matters at high future like volume.

Legacy drift is not repaired or migrated; known undercounts fail closed. Complete
historical attribution cannot be inferred from aggregate counts. Share logging is
atomic per scheduled update, but exactly-once transport delivery across reconnects
is not certified without a durable event ledger; no such model/backend is added.

Linux Chromium is available; physical iOS/Android, Safari, Firefox, Edge, real screen
readers and genuine 200% browser zoom remain unverified. Public website/CDN access
was blocked in this cloud. No full WCAG conformance or live performance certification.

Image dimensions/lazy priority changes are deferred because no actual referenced
photograph dimensions are available; never write fixture dimensions into source or
blindly lazy-load above-fold photos. Next: Photography overlay summary, Timeline
rhythm/gutters/major thumbnail link, carousel copies/readiness/geometry/controls,
then actual R2 metadata and selective discovery/editorial readiness work. Broader
SEO/dark mode remain separate. See [updated roadmap](../../docs/modernization-roadmap.md).

## Exact changed files

- `_config.yml`
- `_includes/head.html`
- `_includes/head_custom.html`
- `_review/core-reliability/homepage-desktop.png`
- `_review/core-reliability/homepage-mobile.png`
- `_review/core-reliability/mobile-keyboard.png`
- `_review/core-reliability/performance-results.json`
- `_review/core-reliability/report.md`
- `_review/core-reliability/search-failure-1440.png`
- `_review/core-reliability/search-failure-390.png`
- `_review/core-reliability/validation.json`
- `_tests/.gitignore`
- `_tests/README.md`
- `_tests/browser.py`
- `_tests/course-queries.json`
- `_tests/firebase-fixture.js`
- `_tests/firebase.test.cjs`
- `_tests/performance.py`
- `_tests/preservation.py`
- `_tests/requirements.txt`
- `assets/css/custom.css`
- `assets/js/just-the-docs.js`
- `assets/js/search.js`
- `assets/js/site-ui.js`
- `assets/js/travel.js`
- `docs/core-reliability.md`
- `docs/just-the-docs-license.txt`
- `docs/modernization-roadmap.md`
- `photography.md`

## Rollback

Before merge, close/discard this branch; production is untouched. After an approved
merge, revert its merge commit in a separately reviewed PR and rebuild Pages. No
migration or data reset needs reversal. If reverting only performance work, restore
head/runtime/controller/site-ui/font integration together and retain the safe counter
fix; a complete revert would restore the old split-write defect. Session entries are
ignored by the old runtime and need no purge. Do not merge automatically.
