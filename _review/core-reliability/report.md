# Performance and core reliability review

Branch: `perf/core-reliability`, based on latest merged `gh-pages` `19973eb`.
One PR for local review; production remains unmodified and the PR must stay unmerged.

**Release blocked: Travel like mutations are paused.** The owner-supplied rules deny
PR #19's parent transaction, expose all user records through root `.read: true`, and
permit unsafe independent counter writes. The revised client reads only counts and
its own marker. This removes the incompatible/private-data-reading operation; it
does **not** complete the like/unlike fix. See the [concrete rules/backend options,
security, hosting/cost and approval requirements](../../docs/travel-like-reliability.md).
No production rules, service, billing or records changed.

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
- Likes now display existing state/count read-only and never read the user map or
  attempt a parent transaction. Authentication/count/own-read failures report SDK
  categories without private data. Invalid counts are not reset. Shares retain atomic
  marker/increment logging independent of completed native/clipboard actions, and
  voluntary native cancellation remains normal feedback. No production data changed.
- Font Awesome loads on Travel only. Inter's original four weights/display=swap move
  directly to the head with preconnect. Pin the audited theme SHA and tested GLightbox
  3.3.1; no dependency upgrade, global typography reset or image changes.

Audit findings addressed: **A1/A2/A3, B4/B6/B7, A6**. B1 remains release-blocked
until the approved private-like write path is implemented and deployed.

## Comparable performance evidence

Recorded on `02839e0`; all eight other production files remain byte-identical in
this revision, so homepage performance was not remeasured.
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

## Validation of this revision

- Production and localhost Jekyll builds succeed; 580 preservation checks each,
  all **82 HTML routes**, content, links, assets, IDs, SEO and standard search data.
  Existing upstream Sass warnings remain.
- Actual Jekyll-served browser: **557** checks, 135 course queries and 90 destination
  clicks, native loading/error/retry/cache/keyboard/history, 12 widths and eight
  orientations. Nine like controls are explicitly tested as read-only, not passed
  off as successful like/unlike interactions. No browser exceptions.
- **Eight enforced RTDB scenarios**, using Firebase 9.22.1 and emulator 4.11.2:
  supplied-rule parent denial/public reads/duplicate increments; private coupled
  atomic like/unlike, fixed-intent retries, forbidden split/forged/other-user writes,
  20 distinct/ten same-user clients, malformed and historical inconsistent records,
  trusted transaction prototype, offline queue/optimistic state/reconnect. Expected
  denial warnings are recorded in [firebase-enforced.log](firebase-enforced.log).
  This tests local copies of owner-supplied/candidate rules, not deployed rules.
- **51 actual Firebase SDK/browser checks** at 390/1440 against enforced rules:
  reproduce the original PR19 UI failure; verify all nine counts/own states and
  no parent reads/like writes; native cancellation and actual atomic share logging;
  seeded records remain unchanged. Auth uses emulator tokens. Results:
  [firebase-browser-results.json](firebase-browser-results.json).
- **13 isolated scenarios** cover client containment, error categories, SDK/auth/read
  failures, corrupt/history preservation, share atomicity/queued logging/cancellation,
  and the server-side design prototype. These supplement the enforced tests.
- Retained Blog: **110**; Travel IDs/sharing/navigation: **88** (old mocked mutation
  expectations now assert paused controls/no writes); carousel/navigation: **64**.
- **36** controlled visual comparisons on twelve unrelated pages at 390/820/1440:
  main-content geometry, typography and pixels unchanged. Shared chrome and native
  select/video paint masked consistently; Travel's intentional paused feedback is
  assessed separately. Eight other production files are unchanged from reviewed
  `02839e0`, including search, CSS, navigation and Photography.

Earlier gallery/UI/performance evidence remains in `validation.json` under
`prior_suites`; it is not claimed as rerun. Linux Chromium, synthetic missing media,
no physical devices/other engines/screen-reader/real-zoom certification. The SDK's
Node loopback proxy issue was resolved only for fixed-localhost test processes.
The official emulator artifact SHA-256 matches the Firebase CLI manifest.

Evidence: [validation.json](validation.json). Portable commands:
[testing README](../../_tests/README.md).

## Before/after screenshots

[Homepage desktop](homepage-desktop.png) · [Homepage mobile](homepage-mobile.png) ·
[Mobile keyboard focus exit](mobile-keyboard.png) ·
[Mobile search failure](search-failure-390.png) · [Desktop search failure](search-failure-1440.png).

Travel failure → safe read-only containment (actual SDK/emulator, cached Inter/icons, neutral media):
[Mobile before](travel-like-before-390.png) · [Mobile read-only](travel-like-readonly-390.png) ·
[Desktop before](travel-like-before-1440.png) · [Desktop read-only](travel-like-readonly-1440.png).

Homepage presentation stays intact. The menu now dismisses when Tab reaches main
content, and search failure has readable, keyboard-accessible feedback.

## Limits and remaining work

The supplied rules explain the permission failure and the privacy warning; they have
not been remotely verified. A private atomic multi-path update is possible with
coupled validation rules, but does not identify historical phantom markers.
The recommended trusted endpoint preserves known-undercount protection without
client access to other users. The exact candidate rules/prototype are local test
fixtures, not deployment configuration. Owner approval and staging/production
verification remain required. See [decision details](../../docs/travel-like-reliability.md).

Historic overcounts/attribution are not repaired or certified. Exactly-once share
transport delivery remains unverified; current numeric-only share write rules remain
an abuse limitation. No durable ledger, migration, production write test or backend
is silently introduced.

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

Production changes in this revision: **`assets/js/travel.js` only**. The eight other
production files from PR #19 are unchanged. Testing, investigation and review files
are below; `_tests`/`_review` do not ship in the Jekyll output.

Revision from `02839e0`:

- `_review/core-reliability/firebase-browser-results.json`
- `_review/core-reliability/firebase-enforced.log`
- `_review/core-reliability/report.md`
- `_review/core-reliability/travel-like-before-1440.png`
- `_review/core-reliability/travel-like-before-390.png`
- `_review/core-reliability/travel-like-readonly-1440.png`
- `_review/core-reliability/travel-like-readonly-390.png`
- `_review/core-reliability/validation.json`
- `_tests/.gitignore`
- `_tests/README.md`
- `_tests/browser.py`
- `_tests/firebase-fixture.js`
- `_tests/firebase-rules/browser.py`
- `_tests/firebase-rules/emulator.test.cjs`
- `_tests/firebase-rules/firebase.json`
- `_tests/firebase-rules/package.json`
- `_tests/firebase-rules/private-backend.rules.json`
- `_tests/firebase-rules/private-coupled.rules.json`
- `_tests/firebase-rules/provided.rules.json`
- `_tests/firebase-rules/trusted-updater.cjs`
- `_tests/firebase-rules/trusted-updater.test.cjs`
- `_tests/firebase.test.cjs`
- `assets/js/travel.js`
- `docs/core-reliability.md`
- `docs/modernization-roadmap.md`
- `docs/travel-like-reliability.md`

Complete PR against `gh-pages`:

- `_config.yml`
- `_includes/head.html`
- `_includes/head_custom.html`
- `_review/core-reliability/firebase-browser-results.json`
- `_review/core-reliability/firebase-enforced.log`
- `_review/core-reliability/homepage-desktop.png`
- `_review/core-reliability/homepage-mobile.png`
- `_review/core-reliability/mobile-keyboard.png`
- `_review/core-reliability/performance-results.json`
- `_review/core-reliability/report.md`
- `_review/core-reliability/search-failure-1440.png`
- `_review/core-reliability/search-failure-390.png`
- `_review/core-reliability/travel-like-before-1440.png`
- `_review/core-reliability/travel-like-before-390.png`
- `_review/core-reliability/travel-like-readonly-1440.png`
- `_review/core-reliability/travel-like-readonly-390.png`
- `_review/core-reliability/validation.json`
- `_tests/.gitignore`
- `_tests/README.md`
- `_tests/browser.py`
- `_tests/course-queries.json`
- `_tests/firebase-fixture.js`
- `_tests/firebase-rules/browser.py`
- `_tests/firebase-rules/emulator.test.cjs`
- `_tests/firebase-rules/firebase.json`
- `_tests/firebase-rules/package.json`
- `_tests/firebase-rules/private-backend.rules.json`
- `_tests/firebase-rules/private-coupled.rules.json`
- `_tests/firebase-rules/provided.rules.json`
- `_tests/firebase-rules/trusted-updater.cjs`
- `_tests/firebase-rules/trusted-updater.test.cjs`
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
- `docs/travel-like-reliability.md`
- `photography.md`

## Rollback

Before merge, close/discard this branch; production is untouched. After an approved
merge, revert its merge commit in a separately reviewed PR and rebuild Pages. No
migration or data reset needs reversal. If reverting only performance work, restore
head/runtime/controller/site-ui/font integration together and keep likes paused; a complete revert would restore the old split-write defect. Session entries are
ignored by the old runtime and need no purge. Do not merge automatically.
